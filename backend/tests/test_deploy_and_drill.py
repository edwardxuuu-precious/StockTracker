"""Regression tests for deploy rollback drill helpers."""
from __future__ import annotations

from argparse import Namespace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def _load_module(name: str, rel_path: str):
    script_path = Path(__file__).resolve().parents[1] / rel_path
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_wait_for_health_force_fail_short_circuit():
    deploy = _load_module("deploy_with_rollback", "scripts/deploy_with_rollback.py")
    result = deploy._wait_for_health(
        project_name="stocktracker-test",
        compose_files=[Path("docker-compose.yml")],
        backend_url="http://localhost:8001/openapi.json",
        frontend_url="http://localhost:5173/",
        timeout_seconds=1,
        interval_seconds=1,
        dry_run=True,
        force_fail=True,
    )
    assert result.status == "fail"
    assert "forced failure" in result.details


def test_deploy_dry_run_simulated_failure_executes_rollback(tmp_path):
    deploy = _load_module("deploy_with_rollback", "scripts/deploy_with_rollback.py")
    output = tmp_path / "deploy_report.json"
    args = Namespace(
        env="staging",
        project_name="stocktracker-staging-test",
        rollback_on_failure=True,
        backend_health_url="http://localhost:8001/openapi.json",
        frontend_health_url="http://localhost:5173/",
        health_timeout_seconds=5,
        health_interval_seconds=1,
        simulate_initial_health_failure=True,
        dry_run=True,
        output=str(output),
    )
    code = deploy.deploy(args)
    assert code == 0
    payload = deploy.json.loads(output.read_text(encoding="utf-8"))
    assert payload["simulate_initial_health_failure"] is True
    assert payload["rollback_attempted"] is True
    assert payload["rollback_success"] is True
    assert payload["passed"] is True


def test_rollback_drill_retention_keeps_latest(tmp_path):
    drill = _load_module("rollback_drill", "scripts/rollback_drill.py")
    target = tmp_path / "drills"
    target.mkdir(parents=True, exist_ok=True)
    for idx in range(4):
        (target / f"deploy_report_staging_2024010{idx}.json").write_text("{}", encoding="utf-8")
        (target / f"rollback_drill_summary_staging_2024010{idx}.json").write_text("{}", encoding="utf-8")

    removed = drill._apply_retention(target, keep_count=2)

    assert len(removed) == 4
    assert len(list(target.glob("deploy_report_*.json"))) == 2
    assert len(list(target.glob("rollback_drill_summary_*.json"))) == 2


def test_rollback_drill_run_applies_retention_after_summary_write(tmp_path, monkeypatch):
    drill = _load_module("rollback_drill", "scripts/rollback_drill.py")
    target = tmp_path / "drills"
    target.mkdir(parents=True, exist_ok=True)
    for idx in range(2):
        (target / f"deploy_report_staging_2024010{idx}.json").write_text("{}", encoding="utf-8")
        (target / f"rollback_drill_summary_staging_2024010{idx}.json").write_text("{}", encoding="utf-8")

    def _fake_run(cmd, cwd, capture_output, text, encoding, errors, check):
        out_path = Path(cmd[cmd.index("--output") + 1])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "rollback_attempted": True,
            "rollback_success": True,
            "passed": True,
        }
        out_path.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(drill.subprocess, "run", _fake_run)
    args = Namespace(
        env="staging",
        project_name="",
        output_dir=str(target),
        retain_count=2,
        live=False,
        backend_health_url="http://localhost:8001/openapi.json",
        frontend_health_url="http://localhost:5173/",
        health_timeout_seconds=120,
        health_interval_seconds=5,
    )

    code = drill.run_drill(args)
    assert code == 0
    assert len(list(target.glob("deploy_report_*.json"))) == 2
    assert len(list(target.glob("rollback_drill_summary_*.json"))) == 2
