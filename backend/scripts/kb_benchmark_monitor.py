"""Run KB benchmark periodically, archive trend history, and detect drift.

Examples:
  python backend/scripts/kb_benchmark_monitor.py --profile prod
  python backend/scripts/kb_benchmark_monitor.py --profile staging --mode optional
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_policy.json"
DEFAULT_HISTORY_DIR = PROJECT_ROOT / ".runtime" / "kb_benchmark_history"
DEFAULT_KB_CASES = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_cases.sample.json"
DEFAULT_KB_CASES_PROD = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_cases.prod.json"


@dataclass(frozen=True)
class MonitorConfig:
    profile: str
    mode: str
    cases_path: Path
    min_precision: float
    min_recall: float
    policy_path: Path | None


def _tail(text: str, lines: int = 40) -> str:
    parts = (text or "").strip().splitlines()
    if len(parts) <= lines:
        return "\n".join(parts)
    return "\n".join(parts[-lines:])


def _extract_json_from_text(text: str) -> dict[str, Any]:
    payload = (text or "").strip()
    if not payload:
        return {}
    if payload.startswith("{") and payload.endswith("}"):
        return json.loads(payload)
    start = payload.find("{")
    end = payload.rfind("}")
    if start < 0 or end < 0 or end <= start:
        return {}
    try:
        return json.loads(payload[start : end + 1])
    except Exception:
        return {}


def _resolve_mode(profile: str, raw_mode: str) -> str:
    mode = (raw_mode or "auto").strip().lower()
    if mode != "auto":
        return mode
    if profile == "prod":
        return "required"
    if profile == "staging":
        return "optional"
    return "off"


def _load_policy(path: Path | None, profile: str) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    item = payload.get(profile)
    if not isinstance(item, dict):
        return {}
    return item


def _resolve_config(args: argparse.Namespace) -> MonitorConfig:
    profile = str(args.profile).strip().lower()
    policy_path = Path(args.policy) if str(args.policy).strip() else DEFAULT_POLICY_PATH
    if not policy_path.is_absolute():
        policy_path = PROJECT_ROOT / policy_path
    policy = _load_policy(policy_path, profile)

    raw_mode = str(args.mode or "auto").strip().lower()
    if raw_mode == "auto" and str(policy.get("mode", "")).strip().lower() in {"off", "optional", "required"}:
        mode = str(policy.get("mode")).strip().lower()
    else:
        mode = _resolve_mode(profile, raw_mode)

    if str(args.cases).strip():
        cases_path = Path(args.cases)
    elif str(policy.get("cases", "")).strip():
        cases_path = Path(str(policy.get("cases")))
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
        float(args.min_precision)
        if args.min_precision is not None
        else float(policy.get("min_precision", 0.45))
    )
    min_recall = (
        float(args.min_recall)
        if args.min_recall is not None
        else float(policy.get("min_recall", 0.45))
    )
    return MonitorConfig(
        profile=profile,
        mode=mode,
        cases_path=cases_path,
        min_precision=min_precision,
        min_recall=min_recall,
        policy_path=policy_path if policy_path.exists() else None,
    )


def _run_benchmark(config: MonitorConfig) -> tuple[int, str, str, dict[str, Any]]:
    cmd = [
        sys.executable,
        "backend/scripts/kb_benchmark.py",
        "--cases",
        str(config.cases_path),
        "--reset-db",
        "--min-precision",
        str(config.min_precision),
        "--min-recall",
        str(config.min_recall),
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload = _extract_json_from_text(completed.stdout)
    return completed.returncode, completed.stdout, completed.stderr, payload


def _history_files(directory: Path, pattern: str) -> list[Path]:
    return sorted(directory.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)


def _load_recent_metrics(directory: Path, lookback: int) -> list[dict[str, float]]:
    history: list[dict[str, float]] = []
    for file_path in _history_files(directory, "benchmark_*.json"):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            history.append(
                {
                    "precision": float(payload.get("avg_precision_at_k", 0.0)),
                    "recall": float(payload.get("avg_keyword_recall", 0.0)),
                }
            )
        except Exception:
            continue
        if len(history) >= lookback:
            break
    return history


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _evaluate_drift(
    *,
    current_precision: float,
    current_recall: float,
    history: list[dict[str, float]],
    min_history: int,
    max_precision_drop: float,
    max_recall_drop: float,
    blocking: bool,
) -> list[dict[str, Any]]:
    if len(history) < max(min_history, 1):
        return []

    baseline_precision = _avg([item["precision"] for item in history])
    baseline_recall = _avg([item["recall"] for item in history])
    alerts: list[dict[str, Any]] = []

    precision_drop = baseline_precision - current_precision
    if precision_drop > max_precision_drop:
        alerts.append(
            {
                "code": "precision_drift",
                "blocking": blocking,
                "severity": "error" if blocking else "warning",
                "message": (
                    f"precision drop {precision_drop:.4f} exceeds limit {max_precision_drop:.4f} "
                    f"(baseline={baseline_precision:.4f}, current={current_precision:.4f})"
                ),
                "baseline": round(baseline_precision, 4),
                "current": round(current_precision, 4),
            }
        )

    recall_drop = baseline_recall - current_recall
    if recall_drop > max_recall_drop:
        alerts.append(
            {
                "code": "recall_drift",
                "blocking": blocking,
                "severity": "error" if blocking else "warning",
                "message": (
                    f"recall drop {recall_drop:.4f} exceeds limit {max_recall_drop:.4f} "
                    f"(baseline={baseline_recall:.4f}, current={current_recall:.4f})"
                ),
                "baseline": round(baseline_recall, 4),
                "current": round(current_recall, 4),
            }
        )
    return alerts


def _apply_retention(directory: Path, keep_count: int) -> list[str]:
    removed: list[str] = []
    keep = max(int(keep_count), 1)
    for pattern in ("benchmark_*.json", "monitor_*.json"):
        for stale in _history_files(directory, pattern)[keep:]:
            stale.unlink(missing_ok=True)
            removed.append(str(stale))
    return removed


def _post_alert(webhook: str, payload: dict[str, Any]) -> bool:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(webhook, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=5):
            return True
    except Exception:
        return False


def run_monitor(args: argparse.Namespace) -> int:
    config = _resolve_config(args)
    history_root = Path(args.history_dir)
    if not history_root.is_absolute():
        history_root = PROJECT_ROOT / history_root
    history_dir = history_root / config.profile
    history_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    benchmark_path = history_dir / f"benchmark_{stamp}.json"
    monitor_path = history_dir / f"monitor_{stamp}.json"
    webhook = str(args.alert_webhook or "").strip()
    if not webhook:
        webhook = str(os.environ.get("KB_BENCHMARK_ALERT_WEBHOOK", "")).strip()

    alerts: list[dict[str, Any]] = []
    benchmark_exit = 0
    benchmark_stdout = ""
    benchmark_stderr = ""
    benchmark_payload: dict[str, Any] = {}
    if config.mode == "off":
        benchmark_payload = {
            "cases_file": str(config.cases_path),
            "cases": 0,
            "avg_precision_at_k": 0.0,
            "avg_keyword_recall": 0.0,
            "seeded_documents": 0,
            "mode": "off",
            "details": "benchmark skipped by mode",
        }
    else:
        benchmark_exit, benchmark_stdout, benchmark_stderr, benchmark_payload = _run_benchmark(config)
        if not benchmark_payload:
            benchmark_payload = {
                "cases_file": str(config.cases_path),
                "cases": 0,
                "avg_precision_at_k": 0.0,
                "avg_keyword_recall": 0.0,
                "seeded_documents": 0,
                "mode": config.mode,
                "details": "benchmark output parse failed",
            }

    benchmark_record = dict(benchmark_payload)
    benchmark_record.update(
        {
            "profile": config.profile,
            "mode": config.mode,
            "thresholds": {
                "min_precision": config.min_precision,
                "min_recall": config.min_recall,
            },
            "policy_path": str(config.policy_path) if config.policy_path else None,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "exit_code": int(benchmark_exit),
        }
    )
    benchmark_path.write_text(json.dumps(benchmark_record, ensure_ascii=False, indent=2), encoding="utf-8")

    current_precision = float(benchmark_record.get("avg_precision_at_k", 0.0))
    current_recall = float(benchmark_record.get("avg_keyword_recall", 0.0))
    blocking = config.mode == "required"
    if benchmark_exit != 0:
        alerts.append(
            {
                "code": "benchmark_threshold_failure",
                "blocking": blocking,
                "severity": "error" if blocking else "warning",
                "message": (
                    f"benchmark exit code={benchmark_exit} "
                    f"(precision>={config.min_precision}, recall>={config.min_recall})"
                ),
            }
        )

    history = _load_recent_metrics(history_dir, max(int(args.drift_lookback), 1) + 1)
    if history:
        # Exclude current point which has already been written.
        history = history[1:]
    alerts.extend(
        _evaluate_drift(
            current_precision=current_precision,
            current_recall=current_recall,
            history=history,
            min_history=int(args.min_history),
            max_precision_drop=float(args.max_precision_drop),
            max_recall_drop=float(args.max_recall_drop),
            blocking=blocking,
        )
    )

    removed: list[str] = []
    passed = not any(bool(item.get("blocking")) for item in alerts)
    monitor_report = {
        "profile": config.profile,
        "mode": config.mode,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_path": str(benchmark_path),
        "monitor_path": str(monitor_path),
        "policy_path": str(config.policy_path) if config.policy_path else None,
        "cases_path": str(config.cases_path),
        "thresholds": {"min_precision": config.min_precision, "min_recall": config.min_recall},
        "current_metrics": {
            "avg_precision_at_k": round(current_precision, 4),
            "avg_keyword_recall": round(current_recall, 4),
        },
        "history_points_used": len(history),
        "drift_rules": {
            "min_history": int(args.min_history),
            "drift_lookback": int(args.drift_lookback),
            "max_precision_drop": float(args.max_precision_drop),
            "max_recall_drop": float(args.max_recall_drop),
        },
        "alerts": alerts,
        "retention_deleted": [],
        "passed": passed,
        "benchmark_stdout_tail": _tail(benchmark_stdout),
        "benchmark_stderr_tail": _tail(benchmark_stderr),
    }
    monitor_path.write_text(json.dumps(monitor_report, ensure_ascii=False, indent=2), encoding="utf-8")
    removed = _apply_retention(history_dir, int(args.retain_count))
    if removed:
        monitor_report["retention_deleted"] = removed
        monitor_path.write_text(json.dumps(monitor_report, ensure_ascii=False, indent=2), encoding="utf-8")

    if alerts and webhook:
        monitor_report["alert_webhook_sent"] = _post_alert(
            webhook,
            {
                "event": "kb_benchmark_monitor_alert",
                "profile": config.profile,
                "passed": passed,
                "alerts": alerts,
                "monitor_report": str(monitor_path),
            },
        )
        monitor_path.write_text(json.dumps(monitor_report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[kb-monitor] profile={config.profile} passed={passed} report={monitor_path}")
    return 0 if passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KB benchmark drift monitor.")
    parser.add_argument("--profile", choices=["dev", "staging", "prod"], default="prod")
    parser.add_argument("--mode", choices=["auto", "off", "optional", "required"], default="auto")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY_PATH))
    parser.add_argument("--cases", default="")
    parser.add_argument("--min-precision", dest="min_precision", type=float, default=None)
    parser.add_argument("--min-recall", dest="min_recall", type=float, default=None)
    parser.add_argument("--history-dir", default=str(DEFAULT_HISTORY_DIR))
    parser.add_argument("--retain-count", type=int, default=120)
    parser.add_argument("--drift-lookback", type=int, default=8)
    parser.add_argument("--min-history", type=int, default=3)
    parser.add_argument("--max-precision-drop", type=float, default=0.08)
    parser.add_argument("--max-recall-drop", type=float, default=0.05)
    parser.add_argument("--alert-webhook", default="")
    return parser.parse_args()


def main() -> int:
    return run_monitor(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
