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
                "short_window": 4,
                "long_window": 12,
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

    run = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "initial_capital": 100000,
            "parameters": {"allocation_per_trade": 0.35},
        },
    )
    assert run.status_code == 201
    result = run.json()
    backtest_id = result["id"]
    assert result["status"] == "completed"
    assert result["trade_count"] >= 1
    assert result["final_value"] > 0
    assert result["sharpe_ratio"] == pytest.approx(float(result["sharpe_ratio"]))
    assert "equity_curve" in (result.get("results") or {})

    detail = client.get(f"/api/v1/backtests/{backtest_id}")
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["id"] == backtest_id
    assert len(detail_data["trades"]) == result["trade_count"]
    if detail_data["trades"]:
        assert detail_data["trades"][0]["action"] in {"BUY", "SELL"}
        assert detail_data["trades"][0]["is_simulated"] is True

    trades = client.get(f"/api/v1/backtests/{backtest_id}/trades")
    assert trades.status_code == 200
    assert len(trades.json()) == result["trade_count"]

    listing = client.get("/api/v1/backtests/")
    assert listing.status_code == 200
    assert any(item["id"] == backtest_id for item in listing.json())


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
    assert "start_date" in bad_date.json()["detail"]

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
    assert "Strategy not found" in not_found_strategy.json()["detail"]
