"""Run a reproducible rollback drill and keep archived reports.

Example:
  python backend/scripts/rollback_drill.py --env staging
  python backend/scripts/rollback_drill.py --env prod --retain-count 36
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / ".runtime"
DEFAULT_DRILL_DIR = RUNTIME_DIR / "rollback_drills"


def _tail(value: str, lines: int = 40) -> str:
    parts = (value or "").strip().splitlines()
    if len(parts) <= lines:
        return "\n".join(parts)
    return "\n".join(parts[-lines:])


def _apply_retention(directory: Path, keep_count: int) -> list[str]:
    deleted: list[str] = []
    for pattern in ("deploy_report_*.json", "rollback_drill_summary_*.json"):
        files = sorted(
            directory.glob(pattern),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for stale in files[keep_count:]:
            stale.unlink(missing_ok=True)
            deleted.append(str(stale))
    return deleted


def _build_deploy_command(args: argparse.Namespace, deploy_report_path: Path) -> list[str]:
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "backend" / "scripts" / "deploy_with_rollback.py"),
        "--env",
        args.env,
        "--project-name",
        args.project_name or f"stocktracker-{args.env}-drill",
        "--rollback-on-failure",
        "--simulate-initial-health-failure",
        "--health-timeout-seconds",
        str(args.health_timeout_seconds),
        "--health-interval-seconds",
        str(args.health_interval_seconds),
        "--backend-health-url",
        args.backend_health_url,
        "--frontend-health-url",
        args.frontend_health_url,
        "--output",
        str(deploy_report_path),
    ]
    if not args.live:
        cmd.append("--dry-run")
    return cmd


def run_drill(args: argparse.Namespace) -> int:
    drill_dir = Path(args.output_dir)
    if not drill_dir.is_absolute():
        drill_dir = PROJECT_ROOT / drill_dir
    drill_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    deploy_report_path = drill_dir / f"deploy_report_{args.env}_{stamp}.json"
    summary_path = drill_dir / f"rollback_drill_summary_{args.env}_{stamp}.json"

    command = _build_deploy_command(args, deploy_report_path)
    completed = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    deploy_report: dict = {}
    if deploy_report_path.exists():
        deploy_report = json.loads(deploy_report_path.read_text(encoding="utf-8"))

    drill_passed = (
        completed.returncode == 0
        and bool(deploy_report)
        and bool(deploy_report.get("rollback_attempted"))
        and bool(deploy_report.get("rollback_success"))
        and bool(deploy_report.get("passed"))
    )

    keep_count = max(int(args.retain_count), 1)
    summary = {
        "env": args.env,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "live_mode": bool(args.live),
        "passed": drill_passed,
        "deploy_command": " ".join(command),
        "deploy_exit_code": completed.returncode,
        "deploy_report_path": str(deploy_report_path),
        "deploy_report_exists": bool(deploy_report),
        "rollback_attempted": bool(deploy_report.get("rollback_attempted")),
        "rollback_success": bool(deploy_report.get("rollback_success")),
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
        "retention_deleted": [],
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    removed = _apply_retention(drill_dir, keep_count)
    if removed:
        summary["retention_deleted"] = removed
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[rollback-drill] env={args.env} passed={drill_passed} report={summary_path}")
    return 0 if drill_passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rollback drill and archive reports.")
    parser.add_argument("--env", choices=["staging", "prod"], default="staging")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_DRILL_DIR))
    parser.add_argument("--retain-count", type=int, default=24)
    parser.add_argument("--live", action="store_true", help="Run against live docker stack (no --dry-run).")
    parser.add_argument("--backend-health-url", default="http://localhost:8001/openapi.json")
    parser.add_argument("--frontend-health-url", default="http://localhost:5173/")
    parser.add_argument("--health-timeout-seconds", type=int, default=120)
    parser.add_argument("--health-interval-seconds", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    return run_drill(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
