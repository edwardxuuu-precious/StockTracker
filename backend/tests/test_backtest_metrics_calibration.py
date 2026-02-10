"""Calibration tests for backtest performance metrics across regimes/markets."""
from __future__ import annotations

from datetime import datetime, timezone
import math


def _create_strategy(client):
    response = client.post(
        "/api/v1/strategies/",
        json={
            "name": "Calibration MA",
            "description": "metric calibration strategy",
            "strategy_type": "moving_average",
            "parameters": {
                "short_window": 2,
                "long_window": 3,
                "allocation_per_trade": 0.3,
                "commission_rate": 0.001,
                "interval": "1d",
            },
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _seed_1d_bars(db, *, symbol: str, market: str, closes: list[float], start_day: int = 1):
    from app.models.market_data import Bar1d, Instrument

    instrument = Instrument(symbol=symbol, market=market, name=symbol)
    db.add(instrument)
    db.flush()
    for idx, close in enumerate(closes, start=start_day):
        db.add(
            Bar1d(
                instrument_id=instrument.id,
                ts=datetime(2025, 1, idx, tzinfo=timezone.utc),
                open=float(close),
                high=float(close) * 1.01,
                low=float(close) * 0.99,
                close=float(close),
                volume=1000 + idx,
                source="test",
            )
        )


def test_metric_function_regime_calibration():
    from app.api.v1.backtest import _compute_performance_metrics

    bull = _compute_performance_metrics(
        initial_capital=100.0,
        final_value=115.0,
        equity_values=[100.0, 105.0, 110.0, 115.0],
        closed_trade_pnls=[5.0, 10.0],
        interval="1d",
    )
    assert bull["total_return"] == 15.0
    assert bull["max_drawdown"] == 0.0
    assert bull["win_rate"] == 100.0
    assert bull["sharpe_ratio"] > 0.0

    bear = _compute_performance_metrics(
        initial_capital=100.0,
        final_value=85.0,
        equity_values=[100.0, 95.0, 90.0, 85.0],
        closed_trade_pnls=[-5.0, -10.0],
        interval="1d",
    )
    assert bear["total_return"] == -15.0
    assert bear["max_drawdown"] == 15.0
    assert bear["win_rate"] == 0.0
    assert bear["sharpe_ratio"] < 0.0

    flat = _compute_performance_metrics(
        initial_capital=100.0,
        final_value=100.0,
        equity_values=[100.0, 100.0, 100.0],
        closed_trade_pnls=[],
        interval="1d",
    )
    assert flat["total_return"] == 0.0
    assert flat["max_drawdown"] == 0.0
    assert flat["win_rate"] == 0.0
    assert flat["sharpe_ratio"] == 0.0

    choppy = _compute_performance_metrics(
        initial_capital=100.0,
        final_value=90.0,
        equity_values=[100.0, 110.0, 90.0, 115.0, 85.0, 90.0],
        closed_trade_pnls=[8.0, -10.0, 12.0, -20.0],
        interval="1d",
    )
    assert choppy["max_drawdown"] > 20.0
    assert choppy["win_rate"] == 50.0
    assert math.isfinite(choppy["sharpe_ratio"])


def test_backtest_final_value_matches_equity_curve_terminal_point(client):
    from app.database import SessionLocal

    strategy_id = _create_strategy(client)

    db = SessionLocal()
    try:
        _seed_1d_bars(
            db,
            symbol="AAPL",
            market="US",
            closes=[100, 101, 102, 103, 104, 105, 106, 107],
        )
        db.commit()
    finally:
        db.close()

    run = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-08",
            "initial_capital": 100000,
            "parameters": {"market": "US", "interval": "1d"},
        },
    )
    assert run.status_code == 201
    body = run.json()
    assert body["status"] == "completed"
    equity_curve = (body.get("results") or {}).get("equity_curve") or []
    assert len(equity_curve) > 0
    terminal = float(equity_curve[-1]["value"])
    assert abs(float(body["final_value"]) - terminal) < 0.01
    expected_return = (float(body["final_value"]) / 100000.0 - 1.0) * 100.0
    assert abs(float(body["total_return"]) - expected_return) < 0.05


def test_backtest_metrics_across_us_cn_market_regimes(client):
    from app.database import SessionLocal

    strategy_id = _create_strategy(client)

    db = SessionLocal()
    try:
        _seed_1d_bars(
            db,
            symbol="AAPL",
            market="US",
            closes=[100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        )
        _seed_1d_bars(
            db,
            symbol="600519",
            market="CN",
            closes=[50, 49, 51, 48, 52, 47, 53, 46, 54, 45],
        )
        db.commit()
    finally:
        db.close()

    bull = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
            "initial_capital": 100000,
            "parameters": {"market": "US", "interval": "1d"},
        },
    )
    assert bull.status_code == 201
    bull_body = bull.json()
    assert bull_body["status"] == "completed"

    choppy = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy_id,
            "symbols": ["600519"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
            "initial_capital": 100000,
            "parameters": {"market": "CN", "interval": "1d"},
        },
    )
    assert choppy.status_code == 201
    choppy_body = choppy.json()
    assert choppy_body["status"] == "completed"

    mixed = client.post(
        "/api/v1/backtests/",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL", "600519"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
            "initial_capital": 100000,
            "parameters": {"markets": {"AAPL": "US", "600519": "CN"}, "interval": "1d"},
        },
    )
    assert mixed.status_code == 201
    mixed_body = mixed.json()
    assert mixed_body["status"] == "completed"
    assert mixed_body["trade_count"] > 0

    # Choppy regime should induce denser trading and weaker risk-adjusted performance.
    assert int(choppy_body["trade_count"]) > int(bull_body["trade_count"])
    assert float(choppy_body["max_drawdown"]) >= float(bull_body["max_drawdown"])
    assert float(choppy_body["sharpe_ratio"]) <= float(bull_body["sharpe_ratio"])
