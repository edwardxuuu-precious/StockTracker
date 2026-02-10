"""Tests for KB benchmark monitor script."""
from __future__ import annotations

from argparse import Namespace
import importlib.util
import json
from pathlib import Path
import sys


def _load_monitor():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "kb_benchmark_monitor.py"
    spec = importlib.util.spec_from_file_location("kb_benchmark_monitor", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _args(**overrides):
    defaults = {
        "profile": "prod",
        "mode": "auto",
        "policy": "",
        "cases": "",
        "min_precision": None,
        "min_recall": None,
        "history_dir": "",
        "retain_count": 3,
        "drift_lookback": 4,
        "min_history": 2,
        "max_precision_drop": 0.1,
        "max_recall_drop": 0.1,
        "alert_webhook": "",
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_resolve_config_reads_policy(tmp_path):
    monitor = _load_monitor()
    policy = tmp_path / "kb_policy.json"
    policy.write_text(
        json.dumps(
            {
                "prod": {
                    "mode": "required",
                    "cases": "backend/config/kb_benchmark_cases.kb004.json",
                    "min_precision": 0.55,
                    "min_recall": 0.8,
                }
            }
        ),
        encoding="utf-8",
    )
    config = monitor._resolve_config(_args(policy=str(policy)))
    assert config.mode == "required"
    assert str(config.cases_path).replace("\\", "/").endswith("backend/config/kb_benchmark_cases.kb004.json")
    assert config.min_precision == 0.55
    assert config.min_recall == 0.8


def test_evaluate_drift_triggers_blocking_alerts():
    monitor = _load_monitor()
    alerts = monitor._evaluate_drift(
        current_precision=0.4,
        current_recall=0.5,
        history=[{"precision": 0.8, "recall": 0.85}, {"precision": 0.78, "recall": 0.82}],
        min_history=2,
        max_precision_drop=0.1,
        max_recall_drop=0.1,
        blocking=True,
    )
    assert any(item["code"] == "precision_drift" for item in alerts)
    assert any(item["code"] == "recall_drift" for item in alerts)
    assert all(item["blocking"] is True for item in alerts)


def test_run_monitor_writes_history_and_retention(tmp_path):
    monitor = _load_monitor()
    history_root = tmp_path / "history"
    profile_dir = history_root / "prod"
    profile_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(3):
        (profile_dir / f"benchmark_2024010{idx}T000000Z.json").write_text(
            json.dumps({"avg_precision_at_k": 0.7, "avg_keyword_recall": 0.8}),
            encoding="utf-8",
        )
        (profile_dir / f"monitor_2024010{idx}T000000Z.json").write_text(
            json.dumps({"passed": True}),
            encoding="utf-8",
        )

    def _fake_run_benchmark(config):
        return (
            0,
            json.dumps({"avg_precision_at_k": 0.71, "avg_keyword_recall": 0.81, "cases": 1}),
            "",
            {"avg_precision_at_k": 0.71, "avg_keyword_recall": 0.81, "cases": 1},
        )

    monitor._run_benchmark = _fake_run_benchmark
    args = _args(
        history_dir=str(history_root),
        mode="required",
        policy=str(tmp_path / "no_policy.json"),
        cases="backend/config/kb_benchmark_cases.sample.json",
        min_precision=0.5,
        min_recall=0.5,
        retain_count=2,
    )
    code = monitor.run_monitor(args)
    assert code == 0
    assert len(list(profile_dir.glob("benchmark_*.json"))) == 2
    assert len(list(profile_dir.glob("monitor_*.json"))) == 2
