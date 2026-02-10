"""Tests for release gate helper logic."""
from __future__ import annotations

from argparse import Namespace
import importlib.util
from pathlib import Path
import sys


def _load_release_gate():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "release_gate.py"
    spec = importlib.util.spec_from_file_location("release_gate", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _args(**overrides):
    defaults = {
        "kb_benchmark_mode": "auto",
        "kb_policy": "",
        "kb_cases": "",
        "kb_min_precision": None,
        "kb_min_recall": None,
        "agent_health_mode": "auto",
        "agent_health_url": "",
        "agent_health_probe": True,
        "agent_health_timeout_seconds": 10.0,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_kb_benchmark_mode_auto_resolution():
    gate = _load_release_gate()
    assert gate._resolve_kb_benchmark_mode("dev", "auto") == "off"
    assert gate._resolve_kb_benchmark_mode("staging", "auto") == "optional"
    assert gate._resolve_kb_benchmark_mode("prod", "auto") == "required"
    assert gate._resolve_kb_benchmark_mode("prod", "off") == "off"


def test_kb_benchmark_optional_missing_cases_is_non_blocking(tmp_path):
    gate = _load_release_gate()
    missing = tmp_path / "missing_cases.json"
    result = gate._check_kb_benchmark(
        "staging",
        _args(kb_benchmark_mode="optional", kb_cases=str(missing)),
    )
    assert result.status == "pass"
    assert "optional check skipped" in result.details


def test_kb_benchmark_required_missing_cases_blocks(tmp_path):
    gate = _load_release_gate()
    missing = tmp_path / "missing_cases.json"
    result = gate._check_kb_benchmark(
        "prod",
        _args(kb_benchmark_mode="required", kb_cases=str(missing)),
    )
    assert result.status == "fail"
    assert "required cases file missing" in result.details


def test_kb_policy_resolution_applies_profile_values(tmp_path):
    gate = _load_release_gate()
    policy = tmp_path / "kb_policy.json"
    policy.write_text(
        gate.json.dumps(
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
    config = gate._resolve_kb_benchmark_config(
        "prod",
        _args(kb_policy=str(policy)),
    )
    assert config.mode == "required"
    assert str(config.cases_path).replace("\\", "/").endswith("backend/config/kb_benchmark_cases.kb004.json")
    assert config.min_precision == 0.55
    assert config.min_recall == 0.8


def test_agent_health_mode_auto_resolution():
    gate = _load_release_gate()
    assert gate._resolve_agent_health_mode("dev", "auto") == "off"
    assert gate._resolve_agent_health_mode("staging", "auto") == "optional"
    assert gate._resolve_agent_health_mode("prod", "auto") == "required"
    assert gate._resolve_agent_health_mode("prod", "off") == "off"


def test_agent_health_optional_missing_url_is_non_blocking():
    gate = _load_release_gate()
    result = gate._check_agent_health(
        "staging",
        _args(agent_health_mode="optional", agent_health_url=""),
    )
    assert result.status == "pass"
    assert "optional check skipped" in result.details


def test_agent_health_required_missing_url_blocks():
    gate = _load_release_gate()
    result = gate._check_agent_health(
        "prod",
        _args(agent_health_mode="required", agent_health_url=""),
    )
    assert result.status == "fail"
    assert "required base URL missing" in result.details


def test_agent_health_optional_command_failure_is_non_blocking(monkeypatch):
    gate = _load_release_gate()

    def _fake_run(*_args, **_kwargs):
        return gate.CheckResult(
            name="agent-health",
            status="fail",
            duration_seconds=0.1,
            details="exit_code=1",
        )

    monkeypatch.setattr(gate, "_run_command", _fake_run)
    result = gate._check_agent_health(
        "staging",
        _args(agent_health_mode="optional", agent_health_url="http://localhost:8000"),
    )
    assert result.status == "pass"
    assert "non-blocking failure" in result.details


def test_agent_health_required_command_failure_blocks(monkeypatch):
    gate = _load_release_gate()

    def _fake_run(*_args, **_kwargs):
        return gate.CheckResult(
            name="agent-health",
            status="fail",
            duration_seconds=0.1,
            details="exit_code=1",
        )

    monkeypatch.setattr(gate, "_run_command", _fake_run)
    result = gate._check_agent_health(
        "prod",
        _args(agent_health_mode="required", agent_health_url="http://localhost:8000"),
    )
    assert result.status == "fail"
    assert "mode=required failed" in result.details
