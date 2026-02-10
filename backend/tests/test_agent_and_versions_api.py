"""API tests for agent endpoints and strategy versions."""
from datetime import datetime, timezone


def _seed_us_daily_bars(symbol: str, start_day: int, db):
    from app.models.market_data import Bar1d, Instrument

    instrument = Instrument(symbol=symbol, market="US", name=symbol)
    db.add(instrument)
    db.flush()
    for day in range(start_day, start_day + 8):
        db.add(
            Bar1d(
                instrument_id=instrument.id,
                ts=datetime(2025, 1, day, tzinfo=timezone.utc),
                open=100.0 + day,
                high=101.0 + day,
                low=99.0 + day,
                close=100.5 + day,
                volume=1000 + day,
                source="test",
            )
        )


def test_strategy_version_endpoints(client):
    created = client.post(
        "/api/v1/strategies/",
        json={
            "name": "Version Test",
            "description": "for versioning",
            "strategy_type": "moving_average",
            "parameters": {"short_window": 5, "long_window": 20},
        },
    )
    assert created.status_code == 201
    strategy_id = created.json()["id"]

    versions = client.get(f"/api/v1/strategies/{strategy_id}/versions")
    assert versions.status_code == 200
    assert len(versions.json()) >= 1

    snapshot = client.post(
        f"/api/v1/strategies/{strategy_id}/versions",
        json={"note": "manual snapshot", "created_by": "test"},
    )
    assert snapshot.status_code == 201

    versions = client.get(f"/api/v1/strategies/{strategy_id}/versions")
    assert len(versions.json()) >= 2


def test_agent_generate_tune_and_report(client):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _seed_us_daily_bars("AAPL", 1, db)
        db.commit()
    finally:
        db.close()

    generated = client.post(
        "/api/v1/agent/strategy/generate",
        json={"prompt": "请生成一个均线策略，短线5长线20", "name": "Agent MA"},
    )
    assert generated.status_code == 200
    strategy = generated.json()["strategy"]
    assert strategy is not None
    strategy_id = strategy["id"]

    tuned = client.post(
        "/api/v1/agent/strategy/tune",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-08",
            "initial_capital": 100000,
            "market": "US",
            "interval": "1d",
            "max_trials": 3,
            "top_k": 2,
            "parameter_grid": {"short_window": [3, 5], "long_window": [8, 12]},
        },
    )
    assert tuned.status_code == 200
    body = tuned.json()
    assert body["best_trial"]["backtest_id"] > 0
    assert len(body["top_trials"]) >= 1

    report = client.post(
        f"/api/v1/agent/backtests/{body['best_trial']['backtest_id']}/report",
        json={"question": "如何降低回撤", "top_k_sources": 2},
    )
    assert report.status_code == 200
    report_body = report.json()
    assert report_body["backtest_id"] == body["best_trial"]["backtest_id"]
    assert "Recommendations" in report_body["markdown"]


def test_agent_health_config_only_optional_mode(client):
    health = client.get("/api/v1/agent/health")
    assert health.status_code == 200
    body = health.json()
    assert body["ok"] is True
    assert body["llm_required"] is False
    assert body["reachable"] is None


def test_agent_health_strict_mode_without_key_returns_503(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("AGENT_REQUIRE_LLM", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    get_settings.cache_clear()
    try:
        health = client.get("/api/v1/agent/health")
        assert health.status_code == 503
        body = health.json()
        assert body["ok"] is False
        assert body["llm_required"] is True
        assert body["configured"] is False
    finally:
        get_settings.cache_clear()


def test_agent_health_probe_success(client, monkeypatch):
    from app.api.v1 import agent as agent_api
    from app.config import get_settings

    monkeypatch.setenv("AGENT_REQUIRE_LLM", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(agent_api, "probe_llm_connection", lambda: (True, "reachable"))
    try:
        health = client.get("/api/v1/agent/health?probe=true")
        assert health.status_code == 200
        body = health.json()
        assert body["ok"] is True
        assert body["reachable"] is True
        assert body["detail"] == "reachable"
    finally:
        get_settings.cache_clear()
