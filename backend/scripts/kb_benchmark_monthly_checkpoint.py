"""Build monthly KB governance checkpoint from monitor/review/change evidence.

Examples:
  python backend/scripts/kb_benchmark_monthly_checkpoint.py --profile prod --month 2026-02
  python backend/scripts/kb_benchmark_monthly_checkpoint.py --profile staging
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HISTORY_DIR = PROJECT_ROOT / ".runtime" / "kb_benchmark_history"
DEFAULT_REVIEW_DIR = PROJECT_ROOT / ".runtime" / "kb_benchmark_reviews"
DEFAULT_CHANGES_DIR = PROJECT_ROOT / "docs" / "Ops" / "KB_Threshold_Changes"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".runtime" / "kb_monthly_checkpoints"


def _month_bounds(month_text: str | None) -> tuple[datetime, datetime, str]:
    now = datetime.now(timezone.utc)
    if not month_text:
        month_text = now.strftime("%Y-%m")
    parsed = datetime.strptime(month_text, "%Y-%m").replace(tzinfo=timezone.utc)
    if parsed.month == 12:
        nxt = parsed.replace(year=parsed.year + 1, month=1, day=1)
    else:
        nxt = parsed.replace(month=parsed.month + 1, day=1)
    start = parsed.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = nxt.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end, start.strftime("%Y-%m")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _parse_dt(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _in_window(dt: datetime | None, start: datetime, end: datetime) -> bool:
    return dt is not None and start <= dt < end


def _load_json_files(directory: Path, pattern: str) -> list[tuple[Path, dict[str, Any]]]:
    items: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(directory.glob(pattern)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            items.append((path, payload))
    return items


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _parse_threshold_change(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    date_match = re.search(r"\|\s*Date \(UTC\)\s*\|\s*`([^`]+)`\s*\|", text)
    scope_match = re.search(r"\|\s*Environment Scope\s*\|\s*`([^`]+)`\s*\|", text)
    change_id_match = re.search(r"\|\s*Change ID\s*\|\s*`([^`]+)`\s*\|", text)
    decision_match = re.search(r"-\s*Decision:\s*\n\s*-\s*`([^`]+)`", text, flags=re.MULTILINE)
    if not date_match or not scope_match:
        return None
    date_text = date_match.group(1).strip()
    date_dt = _parse_dt(f"{date_text}T00:00:00+00:00")
    return {
        "path": str(path),
        "change_id": (change_id_match.group(1).strip() if change_id_match else path.stem),
        "date_utc": date_text,
        "date_dt": date_dt,
        "scope": scope_match.group(1).strip().lower(),
        "decision": decision_match.group(1).strip() if decision_match else "",
    }


def _decision_counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = (value or "unknown").strip().lower() or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def run_checkpoint(args: argparse.Namespace) -> int:
    start, end, month_text = _month_bounds(args.month)
    profile = str(args.profile).strip().lower()

    history_root = Path(args.history_dir)
    if not history_root.is_absolute():
        history_root = PROJECT_ROOT / history_root
    review_root = Path(args.review_dir)
    if not review_root.is_absolute():
        review_root = PROJECT_ROOT / review_root
    changes_dir = Path(args.changes_dir)
    if not changes_dir.is_absolute():
        changes_dir = PROJECT_ROOT / changes_dir
    output_root = Path(args.output_dir)
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root

    monitor_dir = history_root / profile
    review_dir = review_root / profile

    monitor_items = _load_json_files(monitor_dir, "monitor_*.json") if monitor_dir.exists() else []
    review_items = _load_json_files(review_dir, "review_*.json") if review_dir.exists() else []

    month_monitors: list[dict[str, Any]] = []
    for path, payload in monitor_items:
        dt = _parse_dt(str(payload.get("generated_at_utc") or ""))
        if not _in_window(dt, start, end):
            continue
        metric = payload.get("current_metrics") or {}
        month_monitors.append(
            {
                "path": str(path),
                "generated_at_utc": str(payload.get("generated_at_utc") or ""),
                "precision": _safe_float(metric.get("avg_precision_at_k"), 0.0),
                "recall": _safe_float(metric.get("avg_keyword_recall"), 0.0),
                "passed": bool(payload.get("passed")),
                "alert_count": len(payload.get("alerts") or []),
            }
        )

    month_reviews: list[dict[str, Any]] = []
    for path, payload in review_items:
        dt = _parse_dt(str(payload.get("generated_at_utc") or ""))
        if not _in_window(dt, start, end):
            continue
        decision = payload.get("decision") or {}
        month_reviews.append(
            {
                "path": str(path),
                "generated_at_utc": str(payload.get("generated_at_utc") or ""),
                "points": int((payload.get("summary") or {}).get("count", 0)),
                "decision": str(decision.get("decision") or "unknown"),
                "rationale": str(decision.get("rationale") or ""),
                "recommended_thresholds": decision.get("recommended_thresholds"),
            }
        )

    changes: list[dict[str, Any]] = []
    if changes_dir.exists():
        for file_path in sorted(changes_dir.glob("*.md")):
            parsed = _parse_threshold_change(file_path)
            if not parsed:
                continue
            if not _in_window(parsed.get("date_dt"), start, end):
                continue
            scope = str(parsed.get("scope") or "")
            if scope not in {profile, "both", "all"}:
                continue
            changes.append(
                {
                    "path": str(file_path),
                    "change_id": parsed.get("change_id"),
                    "date_utc": parsed.get("date_utc"),
                    "decision": parsed.get("decision"),
                }
            )

    precisions = [float(item["precision"]) for item in month_monitors]
    recalls = [float(item["recall"]) for item in month_monitors]
    failed = sum(1 for item in month_monitors if not bool(item["passed"]))
    alerts = sum(int(item["alert_count"]) for item in month_monitors)
    review_decisions = _decision_counts([str(item["decision"]) for item in month_reviews])

    latest_review_decision = month_reviews[-1]["decision"] if month_reviews else "insufficient_data"
    if failed > 0:
        governance_status = "attention_required"
    elif latest_review_decision == "investigate_before_change":
        governance_status = "attention_required"
    elif latest_review_decision == "consider_tighten":
        governance_status = "candidate_for_threshold_change"
    elif month_monitors:
        governance_status = "stable"
    else:
        governance_status = "insufficient_data"

    report = {
        "profile": profile,
        "month": month_text,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "monitor_points": len(month_monitors),
            "review_points": len(month_reviews),
            "threshold_change_records": len(changes),
            "avg_precision": round(_avg(precisions), 4),
            "avg_recall": round(_avg(recalls), 4),
            "failed_monitor_points": failed,
            "total_alerts": alerts,
            "review_decisions": review_decisions,
            "governance_status": governance_status,
            "latest_review_decision": latest_review_decision,
        },
        "monitors": month_monitors,
        "reviews": month_reviews,
        "threshold_changes": changes,
    }

    out_dir = output_root / profile
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if str(args.output).strip() else out_dir / f"monthly_{month_text}.json"
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[kb-monthly] profile={profile} month={month_text} "
        f"status={governance_status} report={output_path}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build monthly KB governance checkpoint.")
    parser.add_argument("--profile", choices=["staging", "prod"], default="prod")
    parser.add_argument("--month", default="", help="Month in YYYY-MM format. Default: current UTC month.")
    parser.add_argument("--history-dir", default=str(DEFAULT_HISTORY_DIR))
    parser.add_argument("--review-dir", default=str(DEFAULT_REVIEW_DIR))
    parser.add_argument("--changes-dir", default=str(DEFAULT_CHANGES_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> int:
    return run_checkpoint(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
