"""Deploy with health checks and rollback using docker compose.

Example:
  python backend/scripts/deploy_with_rollback.py --env staging --project-name stocktracker-staging
  python backend/scripts/deploy_with_rollback.py --env prod --rollback-on-failure --dry-run
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / ".runtime"


@dataclass
class StepResult:
    step: str
    status: str
    details: str
    command: str | None = None
    stdout_tail: str | None = None
    stderr_tail: str | None = None


def _tail(value: str, lines: int = 25) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    parts = text.splitlines()
    if len(parts) <= lines:
        return "\n".join(parts)
    return "\n".join(parts[-lines:])


def _run(cmd: list[str], *, cwd: Path, dry_run: bool = False, timeout_seconds: int = 1800) -> StepResult:
    if dry_run:
        return StepResult(
            step="command",
            status="pass",
            details="dry-run",
            command=" ".join(cmd),
        )
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        status = "pass" if completed.returncode == 0 else "fail"
        return StepResult(
            step="command",
            status=status,
            details=f"exit_code={completed.returncode}",
            command=" ".join(cmd),
            stdout_tail=_tail(completed.stdout),
            stderr_tail=_tail(completed.stderr),
        )
    except Exception as exc:  # pragma: no cover
        return StepResult(
            step="command",
            status="fail",
            details=str(exc),
            command=" ".join(cmd),
        )


def _compose_cmd(project_name: str, compose_files: list[Path], extra: list[str]) -> list[str]:
    cmd = ["docker", "compose", "-p", project_name]
    for file_path in compose_files:
        cmd.extend(["-f", str(file_path)])
    cmd.extend(extra)
    return cmd


def _backup_database(env_name: str, stamp: str, *, dry_run: bool) -> tuple[Path | None, StepResult]:
    db_path = PROJECT_ROOT / "backend" / "stocktracker.db"
    if not db_path.exists():
        return None, StepResult(
            step="backup-db",
            status="pass",
            details="database file not found, skip backup",
        )
    backup_dir = RUNTIME_DIR / "deploy_backups" / env_name / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "stocktracker.db"
    if not dry_run:
        shutil.copy2(db_path, backup_path)
    return backup_path, StepResult(
        step="backup-db",
        status="pass",
        details=f"backup created at {backup_path}" if not dry_run else f"dry-run backup path {backup_path}",
    )


def _restore_database(backup_path: Path | None, *, dry_run: bool) -> StepResult:
    if backup_path is None or not backup_path.exists():
        return StepResult(step="restore-db", status="pass", details="no backup db to restore")
    db_path = PROJECT_ROOT / "backend" / "stocktracker.db"
    if not dry_run:
        shutil.copy2(backup_path, db_path)
    return StepResult(step="restore-db", status="pass", details=f"restored from {backup_path}")


def _http_ok(url: str, timeout_seconds: float = 3.0) -> bool:
    try:
        with urlopen(url, timeout=timeout_seconds) as resp:
            code = int(resp.getcode() or 0)
            return 200 <= code < 500
    except (HTTPError, URLError, TimeoutError):
        return False


def _snapshot_images(
    *,
    project_name: str,
    env_name: str,
    compose_files: list[Path],
    dry_run: bool,
) -> tuple[dict[str, str], list[StepResult]]:
    results: list[StepResult] = []
    if dry_run:
        return {}, [StepResult(step="snapshot-images", status="pass", details="dry-run skip snapshot")]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    service_repos = {
        "backend": "stocktracker-backend",
        "scheduler": "stocktracker-backend",
        "frontend": "stocktracker-frontend",
    }
    rollback_tags: dict[str, str] = {}
    for service, repo in service_repos.items():
        ps_cmd = _compose_cmd(project_name, compose_files, ["ps", "-q", service])
        ps_result = _run(ps_cmd, cwd=PROJECT_ROOT, dry_run=False, timeout_seconds=60)
        ps_result.step = f"snapshot-{service}-ps"
        results.append(ps_result)
        if ps_result.status != "pass":
            continue
        container_id = (ps_result.stdout_tail or "").strip()
        if not container_id:
            continue

        inspect_result = _run(
            ["docker", "inspect", "-f", "{{.Image}}", container_id],
            cwd=PROJECT_ROOT,
            dry_run=False,
            timeout_seconds=60,
        )
        inspect_result.step = f"snapshot-{service}-inspect"
        results.append(inspect_result)
        if inspect_result.status != "pass":
            continue
        image_id = (inspect_result.stdout_tail or "").strip()
        if not image_id:
            continue

        tag = f"{repo}:rollback-{env_name}-{stamp}"
        tag_result = _run(["docker", "tag", image_id, tag], cwd=PROJECT_ROOT, dry_run=False, timeout_seconds=60)
        tag_result.step = f"snapshot-{service}-tag"
        results.append(tag_result)
        if tag_result.status == "pass":
            rollback_tags[service] = tag
    if not rollback_tags:
        results.append(StepResult(step="snapshot-images", status="pass", details="no running containers to snapshot"))
    else:
        results.append(
            StepResult(
                step="snapshot-images",
                status="pass",
                details=f"created rollback tags for: {', '.join(sorted(rollback_tags.keys()))}",
            )
        )
    return rollback_tags, results


def _write_rollback_override(tags: dict[str, str], env_name: str, stamp: str) -> Path | None:
    if not tags:
        return None
    runtime_dir = RUNTIME_DIR / "deploy_backups" / env_name / stamp
    runtime_dir.mkdir(parents=True, exist_ok=True)
    path = runtime_dir / "rollback.override.yml"
    lines = ["services:"]
    for service in ("backend", "scheduler", "frontend"):
        tag = tags.get(service)
        if service == "scheduler" and not tag:
            tag = tags.get("backend")
        if not tag:
            continue
        lines.append(f"  {service}:")
        lines.append(f"    image: {tag}")
        lines.append("    build: null")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _wait_for_health(
    *,
    project_name: str,
    compose_files: list[Path],
    backend_url: str,
    frontend_url: str,
    timeout_seconds: int,
    interval_seconds: int,
    dry_run: bool,
    force_fail: bool = False,
) -> StepResult:
    if force_fail:
        return StepResult(step="health-check", status="fail", details="forced failure for drill")
    if dry_run:
        return StepResult(step="health-check", status="pass", details="dry-run")
    start = time.time()
    while (time.time() - start) < timeout_seconds:
        backend_ok = _http_ok(backend_url)
        frontend_ok = _http_ok(frontend_url)

        service_ok = True
        for service in ("backend", "scheduler", "frontend"):
            ps = _run(_compose_cmd(project_name, compose_files, ["ps", "-q", service]), cwd=PROJECT_ROOT, dry_run=False)
            if ps.status != "pass":
                service_ok = False
                break
            container_id = (ps.stdout_tail or "").strip()
            if not container_id:
                service_ok = False
                break
            inspect = _run(
                ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
                cwd=PROJECT_ROOT,
                dry_run=False,
                timeout_seconds=60,
            )
            if inspect.status != "pass" or (inspect.stdout_tail or "").strip().lower() != "true":
                service_ok = False
                break

        if backend_ok and frontend_ok and service_ok:
            return StepResult(
                step="health-check",
                status="pass",
                details=f"backend={backend_url} frontend={frontend_url}",
            )
        time.sleep(interval_seconds)
    return StepResult(
        step="health-check",
        status="fail",
        details=f"health check timeout after {timeout_seconds}s",
    )


def _step_from_command(step: str, result: StepResult) -> StepResult:
    result.step = step
    return result


def deploy(args: argparse.Namespace) -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    compose_files = [PROJECT_ROOT / "docker-compose.yml"]
    steps: list[StepResult] = []

    backup_path, backup_result = _backup_database(args.env, stamp, dry_run=args.dry_run)
    steps.append(backup_result)

    rollback_tags, snapshot_results = _snapshot_images(
        project_name=args.project_name,
        env_name=args.env,
        compose_files=compose_files,
        dry_run=args.dry_run,
    )
    steps.extend(snapshot_results)

    deploy_cmd = _compose_cmd(args.project_name, compose_files, ["up", "-d", "--build", "--remove-orphans"])
    steps.append(_step_from_command("deploy-up", _run(deploy_cmd, cwd=PROJECT_ROOT, dry_run=args.dry_run)))

    health = _wait_for_health(
        project_name=args.project_name,
        compose_files=compose_files,
        backend_url=args.backend_health_url,
        frontend_url=args.frontend_health_url,
        timeout_seconds=args.health_timeout_seconds,
        interval_seconds=args.health_interval_seconds,
        dry_run=args.dry_run,
        force_fail=args.simulate_initial_health_failure,
    )
    steps.append(health)

    deployed_ok = all(item.status == "pass" for item in steps if item.step in {"deploy-up", "health-check"})
    rollback_attempted = False
    rollback_success = False

    if (not deployed_ok) and args.rollback_on_failure:
        rollback_attempted = True
        override_path = _write_rollback_override(rollback_tags, args.env, stamp)
        if override_path is None:
            if args.dry_run:
                # Keep rollback drill reproducible in dry-run even without running containers.
                rollback_cmd = _compose_cmd(
                    args.project_name,
                    compose_files,
                    ["up", "-d", "--no-build", "--remove-orphans"],
                )
                steps.append(_step_from_command("rollback-up", _run(rollback_cmd, cwd=PROJECT_ROOT, dry_run=True)))
                steps.append(_restore_database(backup_path, dry_run=args.dry_run))
                rollback_health = _wait_for_health(
                    project_name=args.project_name,
                    compose_files=compose_files,
                    backend_url=args.backend_health_url,
                    frontend_url=args.frontend_health_url,
                    timeout_seconds=args.health_timeout_seconds,
                    interval_seconds=args.health_interval_seconds,
                    dry_run=args.dry_run,
                    force_fail=False,
                )
                rollback_health.step = "rollback-health"
                steps.append(rollback_health)
                rollback_success = rollback_health.status == "pass"
            else:
                steps.append(
                    StepResult(
                        step="rollback",
                        status="fail",
                        details="rollback requested but no rollback image snapshot available",
                    )
                )
        else:
            rollback_cmd = _compose_cmd(
                args.project_name,
                compose_files + [override_path],
                ["up", "-d", "--no-build", "--force-recreate", "--remove-orphans"],
            )
            steps.append(_step_from_command("rollback-up", _run(rollback_cmd, cwd=PROJECT_ROOT, dry_run=args.dry_run)))
            steps.append(_restore_database(backup_path, dry_run=args.dry_run))
            rollback_health = _wait_for_health(
                project_name=args.project_name,
                compose_files=compose_files + [override_path],
                backend_url=args.backend_health_url,
                frontend_url=args.frontend_health_url,
                timeout_seconds=args.health_timeout_seconds,
                interval_seconds=args.health_interval_seconds,
                dry_run=args.dry_run,
                force_fail=False,
            )
            rollback_health.step = "rollback-health"
            steps.append(rollback_health)
            rollback_success = rollback_health.status == "pass"

    passed = deployed_ok or rollback_success
    report = {
        "env": args.env,
        "project_name": args.project_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "simulate_initial_health_failure": bool(args.simulate_initial_health_failure),
        "deployed_ok": deployed_ok,
        "rollback_attempted": rollback_attempted,
        "rollback_success": rollback_success,
        "passed": passed,
        "steps": [asdict(item) for item in steps],
    }

    output_path = Path(args.output) if args.output else (RUNTIME_DIR / f"deploy_report_{args.env}_{stamp}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[deploy] env={args.env} passed={passed} report={output_path}")
    for item in steps:
        print(f"  - {item.step}: {item.status} ({item.details})")

    return 0 if passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy with health checks and rollback.")
    parser.add_argument("--env", choices=["staging", "prod"], required=True)
    parser.add_argument("--project-name", default="")
    parser.add_argument("--rollback-on-failure", action="store_true")
    parser.add_argument("--backend-health-url", default="http://localhost:8001/openapi.json")
    parser.add_argument("--frontend-health-url", default="http://localhost:5173/")
    parser.add_argument("--health-timeout-seconds", type=int, default=150)
    parser.add_argument("--health-interval-seconds", type=int, default=5)
    parser.add_argument(
        "--simulate-initial-health-failure",
        action="store_true",
        help="Force first health check to fail (for rollback drill automation).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    if not args.project_name:
        args.project_name = f"stocktracker-{args.env}"
    return args


def main() -> int:
    return deploy(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
