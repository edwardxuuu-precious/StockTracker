"""Release gate runner for dev/staging/prod promotion checks.

Examples:
  python backend/scripts/release_gate.py --profile dev
  python backend/scripts/release_gate.py --profile staging --docker-build
  python backend/scripts/release_gate.py --profile prod --allow-dirty-git
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

DEFAULT_SECRET_KEY = "your-secret-key-change-this-in-production"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KB_CASES = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_cases.sample.json"
DEFAULT_KB_CASES_PROD = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_cases.prod.json"
DEFAULT_KB_POLICY = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_policy.json"
DEFAULT_KB_MIN_PRECISION = 0.45
DEFAULT_KB_MIN_RECALL = 0.45


@dataclass
class CheckResult:
    name: str
    status: str
    duration_seconds: float
    details: str
    command: str | None = None
    cwd: str | None = None
    stdout_tail: str | None = None
    stderr_tail: str | None = None


@dataclass(frozen=True)
class KBBenchmarkConfig:
    mode: str
    cases_path: Path
    min_precision: float
    min_recall: float
    policy_path: Path | None = None


def _tail_text(value: str, lines: int = 30) -> str:
    parts = (value or "").strip().splitlines()
    if len(parts) <= lines:
        return "\n".join(parts)
    return "\n".join(parts[-lines:])


def _tool_name(name: str) -> str:
    if os.name == "nt" and name.lower() == "npm":
        return "npm.cmd"
    return name


def _run_command(name: str, cmd: list[str], cwd: Path, timeout_seconds: int = 1800) -> CheckResult:
    started = time.time()
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
        elapsed = round(time.time() - started, 3)
        status = "pass" if completed.returncode == 0 else "fail"
        details = f"exit_code={completed.returncode}"
        return CheckResult(
            name=name,
            status=status,
            duration_seconds=elapsed,
            details=details,
            command=" ".join(cmd),
            cwd=str(cwd),
            stdout_tail=_tail_text(completed.stdout),
            stderr_tail=_tail_text(completed.stderr),
        )
    except FileNotFoundError as exc:
        elapsed = round(time.time() - started, 3)
        return CheckResult(
            name=name,
            status="fail",
            duration_seconds=elapsed,
            details=f"command not found: {exc}",
            command=" ".join(cmd),
            cwd=str(cwd),
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.time() - started, 3)
        return CheckResult(
            name=name,
            status="fail",
            duration_seconds=elapsed,
            details=f"timeout after {timeout_seconds}s",
            command=" ".join(cmd),
            cwd=str(cwd),
            stdout_tail=_tail_text((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
            stderr_tail=_tail_text((exc.stderr or "") if isinstance(exc.stderr, str) else ""),
        )


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _effective_env() -> dict[str, str]:
    env_file = _parse_env_file(PROJECT_ROOT / "backend" / ".env")
    merged = dict(env_file)
    merged.update({key: value for key, value in os.environ.items()})
    return merged


def _check_env_policy(profile: str, env: dict[str, str]) -> CheckResult:
    started = time.time()
    issues: list[str] = []

    allow_sim = str(env.get("ALLOW_SIM_BACKTEST", "false")).strip().lower()
    if allow_sim in {"1", "true", "yes", "on"}:
        issues.append("ALLOW_SIM_BACKTEST must be false")

    if profile in {"staging", "prod"}:
        secret = str(env.get("SECRET_KEY", "")).strip()
        if not secret:
            issues.append("SECRET_KEY must be set")
        elif secret in {"your-secret-key-change-this", DEFAULT_SECRET_KEY}:
            issues.append("SECRET_KEY must not use insecure default value")

    if profile == "prod":
        app_env = str(env.get("APP_ENV", "")).strip().lower()
        if app_env in {"", "development", "dev", "local", "test", "testing"}:
            issues.append("APP_ENV must be production-like for prod gate")

    elapsed = round(time.time() - started, 3)
    if issues:
        return CheckResult(
            name="env-policy",
            status="fail",
            duration_seconds=elapsed,
            details="; ".join(issues),
        )
    return CheckResult(
        name="env-policy",
        status="pass",
        duration_seconds=elapsed,
        details=f"{profile} env policy checks passed",
    )


def _check_required_files() -> CheckResult:
    started = time.time()
    required = [
        PROJECT_ROOT / "backend" / "config" / "ingestion_jobs.json",
        PROJECT_ROOT / "docker-compose.yml",
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml",
    ]
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.exists()]
    elapsed = round(time.time() - started, 3)
    if missing:
        return CheckResult(
            name="required-files",
            status="fail",
            duration_seconds=elapsed,
            details=f"missing required files: {', '.join(missing)}",
        )
    return CheckResult(
        name="required-files",
        status="pass",
        duration_seconds=elapsed,
        details="all required files exist",
    )


def _check_git_clean(allow_dirty: bool) -> CheckResult:
    started = time.time()
    if allow_dirty:
        return CheckResult(
            name="git-clean",
            status="pass",
            duration_seconds=round(time.time() - started, 3),
            details="dirty working tree allowed by flag",
        )
    result = _run_command(
        name="git-clean",
        cmd=["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        timeout_seconds=30,
    )
    if result.status == "fail":
        return result
    dirty = (result.stdout_tail or "").strip()
    if dirty:
        result.status = "fail"
        result.details = "working tree is not clean"
    else:
        result.details = "working tree is clean"
    return result


def _default_output_path(profile: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return PROJECT_ROOT / ".runtime" / f"release_gate_{profile}_{stamp}.json"


def _resolve_kb_benchmark_mode(profile: str, mode: str) -> str:
    normalized = (mode or "auto").strip().lower()
    if normalized != "auto":
        return normalized
    if profile == "prod":
        return "required"
    if profile == "staging":
        return "optional"
    return "off"


def _resolve_policy_path(raw_path: str | None) -> Path | None:
    path_value = (raw_path or "").strip()
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _load_kb_policy(policy_path: Path | None, profile: str) -> dict[str, Any]:
    if policy_path is None or not policy_path.exists():
        return {}
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    item = payload.get(profile)
    if not isinstance(item, dict):
        return {}
    return item


def _resolve_kb_benchmark_config(profile: str, args: argparse.Namespace) -> KBBenchmarkConfig:
    policy_path = _resolve_policy_path(getattr(args, "kb_policy", str(DEFAULT_KB_POLICY)))
    policy = _load_kb_policy(policy_path, profile)

    raw_mode = str(getattr(args, "kb_benchmark_mode", "auto") or "auto").strip().lower()
    if raw_mode == "auto" and str(policy.get("mode", "")).strip().lower() in {"off", "optional", "required"}:
        mode = str(policy.get("mode", "")).strip().lower()
    else:
        mode = _resolve_kb_benchmark_mode(profile, raw_mode)

    raw_cases = str(getattr(args, "kb_cases", "") or "").strip()
    if raw_cases:
        cases_path = Path(raw_cases)
    elif str(policy.get("cases", "")).strip():
        cases_path = Path(str(policy.get("cases", "")).strip())
    else:
        cases_path = DEFAULT_KB_CASES

    if not cases_path.is_absolute():
        cases_path = PROJECT_ROOT / cases_path

    if (
        profile == "prod"
        and cases_path.resolve() == DEFAULT_KB_CASES.resolve()
        and DEFAULT_KB_CASES_PROD.exists()
    ):
        cases_path = DEFAULT_KB_CASES_PROD

    min_precision = (
        float(args.kb_min_precision)
        if args.kb_min_precision is not None
        else float(policy.get("min_precision", DEFAULT_KB_MIN_PRECISION))
    )
    min_recall = (
        float(args.kb_min_recall)
        if args.kb_min_recall is not None
        else float(policy.get("min_recall", DEFAULT_KB_MIN_RECALL))
    )

    return KBBenchmarkConfig(
        mode=mode,
        cases_path=cases_path,
        min_precision=min_precision,
        min_recall=min_recall,
        policy_path=policy_path if policy_path and policy_path.exists() else None,
    )


def _check_kb_benchmark(profile: str, args: argparse.Namespace) -> CheckResult:
    started = time.time()
    config = _resolve_kb_benchmark_config(profile, args)
    mode = config.mode
    if mode == "off":
        details = "skipped (mode=off)"
        if config.policy_path is not None:
            details = f"{details}; policy={config.policy_path}"
        return CheckResult(
            name="kb-benchmark",
            status="pass",
            duration_seconds=round(time.time() - started, 3),
            details=details,
        )

    cases_path = config.cases_path
    if not cases_path.exists():
        elapsed = round(time.time() - started, 3)
        if mode == "optional":
            return CheckResult(
                name="kb-benchmark",
                status="pass",
                duration_seconds=elapsed,
                details=f"optional check skipped, cases file missing: {cases_path}; policy={config.policy_path}",
            )
        return CheckResult(
            name="kb-benchmark",
            status="fail",
            duration_seconds=elapsed,
            details=f"required cases file missing: {cases_path}; policy={config.policy_path}",
        )

    cmd = [
        sys.executable,
        "backend/scripts/kb_benchmark.py",
        "--cases",
        str(cases_path),
        "--reset-db",
        "--min-precision",
        str(config.min_precision),
        "--min-recall",
        str(config.min_recall),
    ]
    result = _run_command(
        name="kb-benchmark",
        cmd=cmd,
        cwd=PROJECT_ROOT,
    )
    if result.status == "pass":
        result.details = (
            f"mode={mode} passed; cases={cases_path}; thresholds: "
            f"precision>={config.min_precision}, recall>={config.min_recall}; policy={config.policy_path}"
        )
        return result

    if mode == "optional":
        result.status = "pass"
        result.details = (
            f"mode={mode} non-blocking failure: {result.details}; "
            f"cases={cases_path}; thresholds: precision>={config.min_precision}, recall>={config.min_recall}; "
            f"policy={config.policy_path}"
        )
        return result

    result.details = (
        f"mode={mode} failed: {result.details}; "
        f"cases={cases_path}; thresholds: precision>={config.min_precision}, recall>={config.min_recall}; "
        f"policy={config.policy_path}"
    )
    return result


def _build_checks(profile: str, args: argparse.Namespace) -> list[CheckResult]:
    results: list[CheckResult] = []
    env = _effective_env()

    results.append(_check_required_files())
    results.append(_check_env_policy(profile, env))
    results.append(_check_git_clean(args.allow_dirty_git))

    if args.skip_tests:
        results.append(
            CheckResult(
                name="backend-tests",
                status="pass",
                duration_seconds=0.0,
                details="skipped by flag",
            )
        )
    else:
        results.append(
            _run_command(
                name="backend-tests",
                cmd=[sys.executable, "-m", "pytest", "backend/tests", "-q"],
                cwd=PROJECT_ROOT,
            )
        )
    results.append(_check_kb_benchmark(profile, args))

    if args.skip_frontend:
        results.append(
            CheckResult(
                name="frontend-checks",
                status="pass",
                duration_seconds=0.0,
                details="skipped by flag",
            )
        )
    else:
        npm = _tool_name("npm")
        results.append(_run_command("frontend-lint", [npm, "run", "lint"], PROJECT_ROOT / "frontend"))
        results.append(_run_command("frontend-unit", [npm, "run", "test:unit"], PROJECT_ROOT / "frontend"))
        results.append(_run_command("frontend-build", [npm, "run", "build"], PROJECT_ROOT / "frontend"))

    run_docker_checks = (profile in {"staging", "prod"}) and (not args.skip_docker)
    if not run_docker_checks:
        results.append(
            CheckResult(
                name="docker-checks",
                status="pass",
                duration_seconds=0.0,
                details="skipped by profile/flag",
            )
        )
    else:
        results.append(
            _run_command(
                name="docker-compose-config",
                cmd=["docker", "compose", "config", "-q"],
                cwd=PROJECT_ROOT,
            )
        )
        if args.docker_build:
            results.append(
                _run_command(
                    name="docker-compose-build",
                    cmd=["docker", "compose", "build", "backend", "frontend", "scheduler"],
                    cwd=PROJECT_ROOT,
                    timeout_seconds=3600,
                )
            )
        else:
            results.append(
                CheckResult(
                    name="docker-compose-build",
                    status="pass",
                    duration_seconds=0.0,
                    details="skipped (use --docker-build to enable image build)",
                )
            )

    return results


def run_release_gate(args: argparse.Namespace) -> int:
    profile = args.profile.strip().lower()
    started = time.time()
    checks = _build_checks(profile, args)
    passed = all(item.status == "pass" for item in checks)
    elapsed = round(time.time() - started, 3)

    summary: dict[str, Any] = {
        "profile": profile,
        "passed": passed,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": elapsed,
        "checks": [asdict(item) for item in checks],
    }

    output_path = Path(args.output) if args.output else _default_output_path(profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[release-gate] profile={profile} passed={passed} duration={elapsed}s")
    print(f"[release-gate] report={output_path}")
    for item in checks:
        print(f"  - {item.name}: {item.status} ({item.details})")

    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0 if passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run release gate checks for environment promotion.")
    parser.add_argument("--profile", choices=["dev", "staging", "prod"], default="dev")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--skip-docker", action="store_true")
    parser.add_argument("--docker-build", action="store_true")
    parser.add_argument("--allow-dirty-git", action="store_true")
    parser.add_argument(
        "--kb-benchmark-mode",
        choices=["auto", "off", "optional", "required"],
        default="auto",
        help="KB benchmark mode. auto uses policy file first, then built-in profile mapping.",
    )
    parser.add_argument(
        "--kb-policy",
        default=str(DEFAULT_KB_POLICY),
        help="Path to KB benchmark policy JSON (profile-specific mode/cases/thresholds).",
    )
    parser.add_argument(
        "--kb-cases",
        default="",
        help=(
            "Path to KB benchmark cases JSON file. "
            "If empty, value is resolved from policy file or built-in defaults."
        ),
    )
    parser.add_argument(
        "--kb-min-precision",
        type=float,
        default=None,
        help="Minimum average precision@k. If omitted, use policy/default value.",
    )
    parser.add_argument(
        "--kb-min-recall",
        type=float,
        default=None,
        help="Minimum average keyword recall. If omitted, use policy/default value.",
    )
    parser.add_argument("--output", default="", help="Output JSON report path")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_release_gate(args)


if __name__ == "__main__":
    raise SystemExit(main())
