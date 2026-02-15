"""Tests for agent report telemetry metrics endpoint."""

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


def _prepare_backtest_id(client) -> int:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _seed_us_daily_bars("AAPL", 1, db)
        db.commit()
    finally:
        db.close()

    generated = client.post(
        "/api/v1/agent/strategy/generate",
        json={"prompt": "create MA strategy", "name": "Agent MA Metrics"},
    )
    assert generated.status_code == 200
    strategy_id = generated.json()["strategy"]["id"]

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
            "max_trials": 2,
            "top_k": 1,
            "parameter_grid": {"short_window": [3], "long_window": [8]},
        },
    )
    assert tuned.status_code == 200
    return int(tuned.json()["best_trial"]["backtest_id"])


def test_agent_report_metrics_endpoint_empty(client):
    from app.services.agent_report_observability import clear_agent_report_metrics

    clear_agent_report_metrics()
    response = client.get("/api/v1/telemetry/agent-report-metrics?window=20")
    assert response.status_code == 200
    body = response.json()
    assert body["window"] == 20
    assert body["total"] == 0
    assert body["success_rate"] is None
    assert body["fallback_ratio"] is None
    assert body["timeout_rate"] is None


def test_agent_report_metrics_endpoint_aggregates_success_and_fallback(client, monkeypatch):
    from app.api.v1 import agent as agent_api
    from app.services.agent_report_observability import clear_agent_report_metrics
    from app.services.llm_service import LLMUnavailableError

    clear_agent_report_metrics()
    backtest_id = _prepare_backtest_id(client)

    def _llm_success(*args, **kwargs):
        return (
            "## AI Insights\nAll good",
            {
                "provider": "deepseek",
                "latency_ms": 10.0,
                "retry_count": 0,
                "timeout_seconds": 90.0,
                "error_type": None,
            },
        )

    monkeypatch.setattr(agent_api, "build_ai_backtest_insights", _llm_success)
    first = client.post(
        f"/api/v1/agent/backtests/{backtest_id}/report",
        json={"question": "optimize returns", "top_k_sources": 2},
    )
    assert first.status_code == 200
    assert first.json()["fallback_used"] is False

    def _llm_timeout(*args, **kwargs):
        raise LLMUnavailableError(
            "Request timed out",
            metadata={
                "provider": "deepseek",
                "latency_ms": 12.0,
                "retry_count": 2,
                "timeout_seconds": 90.0,
                "error_type": "timeout",
            },
        )

    monkeypatch.setattr(agent_api, "build_ai_backtest_insights", _llm_timeout)
    second = client.post(
        f"/api/v1/agent/backtests/{backtest_id}/report",
        json={"question": "reduce drawdown", "top_k_sources": 2},
    )
    assert second.status_code == 200
    assert second.json()["fallback_used"] is True

    metrics = client.get("/api/v1/telemetry/agent-report-metrics?window=10")
    assert metrics.status_code == 200
    body = metrics.json()
    assert body["window"] == 10
    assert body["total"] == 2
    assert body["success_rate"] == 1.0
    assert body["fallback_ratio"] == 0.5
    assert body["timeout_rate"] == 0.5
    assert body["p95_latency_ms"] is not None
    assert body["llm_p95_latency_ms"] == 12.0
