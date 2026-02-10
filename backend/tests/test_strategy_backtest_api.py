"""API tests for strategy and backtest skeleton flow."""
import pytest


def _create_strategy(client):
    response = client.post(
        "/api/v1/strategies/",
        json={
            "name": "MA Crossover",
            "description": "moving average strategy",
            "strategy_type": "moving_average",
            "parameters": {
                "short_window": 2,
                "long_window": 3,
                "allocation_per_trade": 0.3,
                "commission_rate": 0.001,
            },
        },
    )
    assert response.status_code == 201
    return response.json()


def test_strategy_crud_baseline(client):
    created = _create_strategy(client)
    strategy_id = created["id"]
    assert created["strategy_type"] == "moving_average"

    listing = client.get("/api/v1/strategies/")
    assert listing.status_code == 200
    items = listing.json()
    assert any(item["id"] == strategy_id for item in items)

    fetched = client.get(f"/api/v1/strategies/{strategy_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "MA Crossover"

    updated = client.put(
        f"/api/v1/strategies/{strategy_id}",
        json={"name": "MA Crossover v2", "parameters": {"short_window": 3, "long_window": 9}},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "MA Crossover v2"
    assert updated.json()["parameters"]["short_window"] == 3


def test_backtest_execution_and_query_flow(client):
    strategy = _create_strategy(client)
    strategy_id = strategy["id"]

    from app.database import SessionLocal
    from app.models.market_data import Bar1d, Instrument
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        for symbol in ("AAPL", "MSFT"):
            instrument = Instrument(symbol=symbol, market="US", name=f"{symbol} Inc")
            db.add(instrument)
            db.flush()
            for day in range(1, 6):
                db.add(
                    Bar1d(
                        instrument_id=instrument.id,
                        ts=datetime(2025, 1, day, tzinfo=timezone.utc),
                        open=100.0 + day,
                        high=101.0 + day,
                        low=99.0 + day,
                        close=100.5 + day,
                        volume=1000 + day,
                        source="akshare",
                    )
                )
        db.commit()
    finally:
        db.close()

    run = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-05",
            "initial_capital": 100000,
            "parameters": {"allocation_per_trade": 0.35, "market": "US", "interval": "1d"},
        },
    )
    assert run.status_code == 201
    payload = run.json()
    assert payload["status"] == "completed"
    assert payload["trade_count"] > 0
    assert payload["total_return"] is not None
    assert payload["sharpe_ratio"] is not None
    assert payload["max_drawdown"] is not None

    detail = client.get(f"/api/v1/backtests/{payload['id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["trades"]) > 0
    assert "equity_curve" in (detail_body["results"] or {})

    trades = client.get(f"/api/v1/backtests/{payload['id']}/trades")
    assert trades.status_code == 200
    trade_rows = trades.json()
    assert len(trade_rows) > 0
    assert all(item["is_simulated"] is False for item in trade_rows)


def test_backtest_validation_and_not_found(client):
    strategy = _create_strategy(client)

    bad_date = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy["id"],
            "symbols": ["AAPL"],
            "start_date": "2025-04-01",
            "end_date": "2025-03-01",
            "initial_capital": 50000,
            "parameters": {},
        },
    )
    assert bad_date.status_code == 400

    not_found_strategy = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": 99999,
            "symbols": ["AAPL"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "initial_capital": 50000,
            "parameters": {},
        },
    )
    assert not_found_strategy.status_code == 404
