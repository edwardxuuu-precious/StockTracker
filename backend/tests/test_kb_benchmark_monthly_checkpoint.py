"""Tests for monthly KB governance checkpoint script."""
from __future__ import annotations

from argparse import Namespace
import importlib.util
import json
from pathlib import Path
import sys


def _load_monthly():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "kb_benchmark_monthly_checkpoint.py"
    spec = importlib.util.spec_from_file_location("kb_benchmark_monthly_checkpoint", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_threshold_change_extracts_fields(tmp_path):
    mod = _load_monthly()
    file_path = tmp_path / "KB-TC-20260209-01.md"
    file_path.write_text(
        "\n".join(
            [
                "| Change ID | `KB-TC-20260209-01` |",
                "| Date (UTC) | `2026-02-09` |",
                "| Environment Scope | `prod` |",
                "- Decision:",
                "  - `Go (No threshold value change)`",
            ]
        ),
        encoding="utf-8",
    )
    parsed = mod._parse_threshold_change(file_path)
    assert parsed is not None
    assert parsed["change_id"] == "KB-TC-20260209-01"
    assert parsed["scope"] == "prod"
    assert "Go" in parsed["decision"]


def test_run_checkpoint_builds_monthly_summary(tmp_path):
    mod = _load_monthly()
    history_dir = tmp_path / "history" / "prod"
    review_dir = tmp_path / "reviews" / "prod"
    changes_dir = tmp_path / "changes"
    output = tmp_path / "monthly.json"
    history_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    changes_dir.mkdir(parents=True, exist_ok=True)

    monitor = {
        "generated_at_utc": "2026-02-09T11:11:37+00:00",
        "current_metrics": {"avg_precision_at_k": 0.625, "avg_keyword_recall": 1.0},
        "alerts": [],
        "passed": True,
    }
    (history_dir / "monitor_20260209T111137Z.json").write_text(json.dumps(monitor), encoding="utf-8")
    review = {
        "generated_at_utc": "2026-02-09T11:21:45+00:00",
        "summary": {"count": 4},
        "decision": {"decision": "keep_thresholds", "rationale": "stable"},
    }
    (review_dir / "review_20260209T112145Z.json").write_text(json.dumps(review), encoding="utf-8")
    change = "\n".join(
        [
            "| Change ID | `KB-TC-20260209-01` |",
            "| Date (UTC) | `2026-02-09` |",
            "| Environment Scope | `prod` |",
            "- Decision:",
            "  - `Go (No threshold value change)`",
        ]
    )
    (changes_dir / "KB-TC-20260209-01.md").write_text(change, encoding="utf-8")

    args = Namespace(
        profile="prod",
        month="2026-02",
        history_dir=str(tmp_path / "history"),
        review_dir=str(tmp_path / "reviews"),
        changes_dir=str(changes_dir),
        output_dir=str(tmp_path / "out"),
        output=str(output),
    )
    code = mod.run_checkpoint(args)
    assert code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["monitor_points"] == 1
    assert payload["summary"]["review_points"] == 1
    assert payload["summary"]["threshold_change_records"] == 1
    assert payload["summary"]["governance_status"] == "stable"
