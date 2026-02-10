"""Tests for KB benchmark weekly review script."""
from __future__ import annotations

from argparse import Namespace
import importlib.util
import json
from pathlib import Path
import sys


def _load_review():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "kb_benchmark_review.py"
    spec = importlib.util.spec_from_file_location("kb_benchmark_review", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_recommend_keep_thresholds_when_margin_not_enough():
    review = _load_review()
    points = [
        {"precision": 0.62, "recall": 0.84, "threshold_precision": 0.55, "threshold_recall": 0.8, "passed": True, "blocking_alert_count": 0},
        {"precision": 0.63, "recall": 0.85, "threshold_precision": 0.55, "threshold_recall": 0.8, "passed": True, "blocking_alert_count": 0},
        {"precision": 0.62, "recall": 0.84, "threshold_precision": 0.55, "threshold_recall": 0.8, "passed": True, "blocking_alert_count": 0},
        {"precision": 0.63, "recall": 0.85, "threshold_precision": 0.55, "threshold_recall": 0.8, "passed": True, "blocking_alert_count": 0},
    ]
    decision = review._recommend(points)
    assert decision["decision"] == "keep_thresholds"


def test_recommend_investigate_when_failed_points_exist():
    review = _load_review()
    points = [
        {"precision": 0.62, "recall": 0.84, "threshold_precision": 0.55, "threshold_recall": 0.8, "passed": True, "blocking_alert_count": 0},
        {"precision": 0.40, "recall": 0.60, "threshold_precision": 0.55, "threshold_recall": 0.8, "passed": False, "blocking_alert_count": 1},
    ]
    decision = review._recommend(points)
    assert decision["decision"] == "investigate_before_change"


def test_run_review_writes_json_report(tmp_path):
    review = _load_review()
    history_root = tmp_path / "history"
    profile_dir = history_root / "prod"
    profile_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(4):
        payload = {
            "generated_at_utc": f"2026-02-0{idx+1}T00:00:00+00:00",
            "current_metrics": {"avg_precision_at_k": 0.62 + idx * 0.005, "avg_keyword_recall": 0.9},
            "thresholds": {"min_precision": 0.55, "min_recall": 0.8},
            "alerts": [],
            "passed": True,
            "benchmark_path": str(profile_dir / f"benchmark_0{idx}.json"),
        }
        (profile_dir / f"monitor_2026020{idx+1}T000000Z.json").write_text(json.dumps(payload), encoding="utf-8")
    out = tmp_path / "review.json"
    args = Namespace(
        profile="prod",
        history_dir=str(history_root),
        output_dir=str(tmp_path / "reviews"),
        lookback=4,
        output=str(out),
    )

    code = review.run_review(args)
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["count"] == 4
    assert payload["decision"]["decision"] in {"keep_thresholds", "consider_tighten"}
