"""Build weekly KB benchmark trend review and threshold decision suggestions.

Examples:
  python backend/scripts/kb_benchmark_review.py --profile prod --lookback 4
  python backend/scripts/kb_benchmark_review.py --profile staging --lookback 6
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HISTORY_DIR = PROJECT_ROOT / ".runtime" / "kb_benchmark_history"
DEFAULT_REVIEW_DIR = PROJECT_ROOT / ".runtime" / "kb_benchmark_reviews"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _history_files(profile_dir: Path, pattern: str) -> list[Path]:
    return sorted(profile_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)


def _load_points(profile_dir: Path, lookback: int) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for file_path in _history_files(profile_dir, "monitor_*.json"):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        current = payload.get("current_metrics") or {}
        thresholds = payload.get("thresholds") or {}
        alerts = payload.get("alerts") or []
        points.append(
            {
                "timestamp_utc": str(payload.get("generated_at_utc") or ""),
                "precision": _to_float(current.get("avg_precision_at_k"), 0.0),
                "recall": _to_float(current.get("avg_keyword_recall"), 0.0),
                "threshold_precision": _to_float(thresholds.get("min_precision"), 0.0),
                "threshold_recall": _to_float(thresholds.get("min_recall"), 0.0),
                "passed": bool(payload.get("passed")),
                "alert_count": len(alerts),
                "blocking_alert_count": sum(1 for item in alerts if bool(item.get("blocking"))),
                "monitor_path": str(file_path),
                "benchmark_path": str(payload.get("benchmark_path") or ""),
            }
        )
        if len(points) >= max(int(lookback), 1):
            break
    points.reverse()
    return points


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _recommend(points: list[dict[str, Any]]) -> dict[str, Any]:
    if not points:
        return {
            "decision": "insufficient_data",
            "rationale": "no monitor history found",
            "recommended_thresholds": None,
        }

    latest = points[-1]
    threshold_precision = _to_float(latest.get("threshold_precision"), 0.0)
    threshold_recall = _to_float(latest.get("threshold_recall"), 0.0)
    avg_precision = _avg([_to_float(item["precision"]) for item in points])
    avg_recall = _avg([_to_float(item["recall"]) for item in points])
    blocking_points = sum(1 for item in points if int(item["blocking_alert_count"]) > 0)
    failed_points = sum(1 for item in points if not bool(item["passed"]))

    if failed_points > 0 or blocking_points > 0:
        return {
            "decision": "investigate_before_change",
            "rationale": (
                f"failed_points={failed_points}, blocking_alert_points={blocking_points}; "
                "keep thresholds unchanged and investigate data quality/retrieval regressions first"
            ),
            "recommended_thresholds": {
                "min_precision": threshold_precision,
                "min_recall": threshold_recall,
            },
        }

    if (
        len(points) >= 4
        and avg_precision >= threshold_precision + 0.10
        and avg_recall >= threshold_recall + 0.10
    ):
        return {
            "decision": "consider_tighten",
            "rationale": (
                "multi-cycle metrics stay materially above thresholds; "
                "consider small tighten step with acceptance evidence"
            ),
            "recommended_thresholds": {
                "min_precision": round(min(threshold_precision + 0.03, 0.95), 2),
                "min_recall": round(min(threshold_recall + 0.03, 0.98), 2),
            },
        }

    return {
        "decision": "keep_thresholds",
        "rationale": "current multi-cycle margin is healthy but not enough for mandatory tighten",
        "recommended_thresholds": {
            "min_precision": threshold_precision,
            "min_recall": threshold_recall,
        },
    }


def _build_summary(profile: str, points: list[dict[str, Any]], lookback: int) -> dict[str, Any]:
    if not points:
        return {
            "profile": profile,
            "points": [],
            "lookback": lookback,
            "summary": {
                "count": 0,
                "avg_precision": 0.0,
                "avg_recall": 0.0,
                "delta_precision_first_to_last": 0.0,
                "delta_recall_first_to_last": 0.0,
                "failed_points": 0,
                "blocking_alert_points": 0,
            },
            "decision": _recommend(points),
        }

    first = points[0]
    last = points[-1]
    precisions = [_to_float(item["precision"]) for item in points]
    recalls = [_to_float(item["recall"]) for item in points]
    summary = {
        "count": len(points),
        "avg_precision": round(_avg(precisions), 4),
        "avg_recall": round(_avg(recalls), 4),
        "min_precision": round(min(precisions), 4),
        "min_recall": round(min(recalls), 4),
        "max_precision": round(max(precisions), 4),
        "max_recall": round(max(recalls), 4),
        "delta_precision_first_to_last": round(_to_float(last["precision"]) - _to_float(first["precision"]), 4),
        "delta_recall_first_to_last": round(_to_float(last["recall"]) - _to_float(first["recall"]), 4),
        "failed_points": sum(1 for item in points if not bool(item["passed"])),
        "blocking_alert_points": sum(1 for item in points if int(item["blocking_alert_count"]) > 0),
        "latest_thresholds": {
            "min_precision": _to_float(last["threshold_precision"]),
            "min_recall": _to_float(last["threshold_recall"]),
        },
    }
    return {
        "profile": profile,
        "lookback": lookback,
        "points": points,
        "summary": summary,
        "decision": _recommend(points),
    }


def run_review(args: argparse.Namespace) -> int:
    profile = str(args.profile).strip().lower()
    lookback = max(int(args.lookback), 1)
    history_root = Path(args.history_dir)
    if not history_root.is_absolute():
        history_root = PROJECT_ROOT / history_root
    profile_dir = history_root / profile
    profile_dir.mkdir(parents=True, exist_ok=True)

    points = _load_points(profile_dir, lookback=lookback)
    report = _build_summary(profile=profile, points=points, lookback=lookback)
    report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

    review_root = Path(args.output_dir)
    if not review_root.is_absolute():
        review_root = PROJECT_ROOT / review_root
    out_dir = review_root / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(args.output) if str(args.output).strip() else out_dir / f"review_{stamp}.json"
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    decision = str((report.get("decision") or {}).get("decision") or "unknown")
    print(f"[kb-review] profile={profile} points={len(points)} decision={decision} report={output}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review KB benchmark trend and suggest threshold decisions.")
    parser.add_argument("--profile", choices=["dev", "staging", "prod"], default="prod")
    parser.add_argument("--history-dir", default=str(DEFAULT_HISTORY_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_REVIEW_DIR))
    parser.add_argument("--lookback", type=int, default=4)
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> int:
    return run_review(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
