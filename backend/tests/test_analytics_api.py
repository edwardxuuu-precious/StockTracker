"""API tests for portfolio analytics dashboard and CSV export."""
import csv
from io import StringIO
import re

import pytest


def _seed_portfolio_with_trades(client):
    create_resp = client.post(
        "/api/v1/portfolios/",
        json={
            "name": "Analytics Portfolio",
            "description": "analytics seed",
            "initial_capital": 100000,
            "holdings": [],
        },
    )
    assert create_resp.status_code == 201
    portfolio_id = create_resp.json()["id"]

    for payload in [
        {"symbol": "AAPL", "action": "BUY", "quantity": 100, "price": 150, "commission": 0},
        {"symbol": "MSFT", "action": "BUY", "quantity": 50, "price": 300, "commission": 0},
        {"symbol": "AAPL", "action": "SELL", "quantity": 50, "price": 160, "commission": 0},
    ]:
        trade_resp = client.post(f"/api/v1/portfolios/{portfolio_id}/trades", json=payload)
        assert trade_resp.status_code == 201

    return portfolio_id


def test_portfolio_analytics_summary_and_charts(client):
    portfolio_id = _seed_portfolio_with_trades(client)

    response = client.get(f"/api/v1/analytics/portfolios/{portfolio_id}")
    assert response.status_code == 200
    payload = response.json()

    summary = payload["summary"]
    assert summary["portfolio_id"] == portfolio_id
    assert summary["initial_capital"] == pytest.approx(100000.0)
    assert summary["cash_balance"] == pytest.approx(78000.0)
    assert summary["holdings_market_value"] == pytest.approx(23000.0)
    assert summary["current_value"] == pytest.approx(101000.0)
    assert summary["total_return"] == pytest.approx(1000.0)
    assert summary["total_return_pct"] == pytest.approx(1.0)
    assert summary["realized_pnl"] == pytest.approx(500.0)
    assert summary["unrealized_pnl"] == pytest.approx(500.0)
    assert summary["active_holdings"] == 2
    assert summary["total_trades"] == 3

    allocation = payload["allocation"]
    assert len(allocation) == 2
    allocation_by_symbol = {item["symbol"]: item for item in allocation}
    assert allocation_by_symbol["MSFT"]["market_value"] == pytest.approx(15000.0)
    assert allocation_by_symbol["MSFT"]["weight_pct"] == pytest.approx(65.2173, abs=1e-3)
    assert allocation_by_symbol["AAPL"]["market_value"] == pytest.approx(8000.0)
    assert allocation_by_symbol["AAPL"]["unrealized_pnl"] == pytest.approx(500.0)

    trend = payload["trend"]
    assert len(trend) == 4
    assert trend[0]["label"] == "初始"
    assert trend[-1]["label"] == "AAPL SELL"
    assert trend[-1]["cumulative_realized_pnl"] == pytest.approx(500.0)

    monthly = payload["monthly_realized_pnl"]
    assert len(monthly) == 1
    assert monthly[0]["realized_pnl"] == pytest.approx(500.0)
    assert monthly[0]["trade_count"] == 3


def test_portfolio_analytics_export_csv(client):
    portfolio_id = _seed_portfolio_with_trades(client)

    summary_resp = client.get(f"/api/v1/analytics/portfolios/{portfolio_id}/export?report=summary")
    assert summary_resp.status_code == 200
    assert "text/csv" in summary_resp.headers["content-type"]
    assert "portfolio_id,portfolio_name,initial_capital" in summary_resp.text
    assert ",101000.00,1000.00,1.0000,500.00,500.00,2,3" in summary_resp.text
    assert "exported_at" in summary_resp.text
    summary_rows = list(csv.DictReader(StringIO(summary_resp.text)))
    assert summary_rows
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", summary_rows[0]["exported_at"])

    holdings_resp = client.get(f"/api/v1/analytics/portfolios/{portfolio_id}/export?report=holdings")
    assert holdings_resp.status_code == 200
    assert "symbol,quantity,current_price,market_value,weight_pct,unrealized_pnl" in holdings_resp.text
    assert "MSFT,50.000000,300.0000,15000.00" in holdings_resp.text
    assert "AAPL,50.000000,160.0000,8000.00" in holdings_resp.text
    assert "exported_at" in holdings_resp.text
    holding_rows = list(csv.DictReader(StringIO(holdings_resp.text)))
    assert holding_rows
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", holding_rows[0]["exported_at"])

    trades_resp = client.get(f"/api/v1/analytics/portfolios/{portfolio_id}/export?report=trades")
    assert trades_resp.status_code == 200
    assert "trade_time,symbol,action,quantity,price,commission,amount,realized_pnl" in trades_resp.text
    assert ",AAPL,SELL,50.000000,160.0000,0.0000,8000.00,500.00" in trades_resp.text

    rows = list(csv.DictReader(StringIO(trades_resp.text)))
    assert rows
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", rows[0]["trade_time"])
