"""Backtest API endpoints and lightweight simulation engine."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
import statistics
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.backtest import Backtest, Trade
from ...models.portfolio import Portfolio
from ...models.strategy import Strategy
from ...schemas.backtest import (
    BacktestCreate,
    BacktestDetailResponse,
    BacktestResponse,
    BacktestTradeResponse,
)

router = APIRouter()


def _normalize_symbols(symbols: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        value = str(symbol or "").strip().upper()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    if not normalized:
        raise HTTPException(status_code=400, detail="At least one valid symbol is required")
    return normalized


def _daterange(start: date, end: date) -> list[date]:
    days: list[date] = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _series_for_symbol(symbol: str, days: list[date]) -> list[float]:
    """Generate deterministic pseudo-market prices for repeatable tests."""
    seed = sum(ord(ch) for ch in symbol)
    base = 40.0 + float(seed % 160)
    phase = (seed % 31) / 10.0
    series: list[float] = []
    for index, _ in enumerate(days):
        trend = 0.0009 * index
        cycle = math.sin(index / 5.0 + phase) * 0.03
        micro = math.sin(index * 1.7 + phase * 0.7) * 0.004
        price = base * (1.0 + trend + cycle + micro)
        series.append(max(1.0, round(price, 4)))
    return series


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _calc_rsi(prices: list[float], period: int) -> float:
    if len(prices) <= period:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    window = prices[-(period + 1) :]
    for idx in range(1, len(window)):
        delta = window[idx] - window[idx - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))
    avg_gain = _mean(gains)
    avg_loss = _mean(losses)
    if avg_loss <= 1e-12:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _signal_for_strategy(
    strategy_type: str,
    history: list[float],
    parameters: dict[str, Any],
) -> str:
    strategy = (strategy_type or "").strip().lower()
    price = history[-1]

    if strategy == "rsi":
        period = int(parameters.get("rsi_period", 14))
        buy_threshold = float(parameters.get("rsi_buy", 30))
        sell_threshold = float(parameters.get("rsi_sell", 70))
        rsi = _calc_rsi(history, max(2, period))
        if rsi <= buy_threshold:
            return "BUY"
        if rsi >= sell_threshold:
            return "SELL"
        return "HOLD"

    if strategy == "momentum":
        period = int(parameters.get("momentum_period", 10))
        threshold = float(parameters.get("momentum_threshold", 0.015))
        if len(history) <= period:
            return "HOLD"
        past_price = history[-(period + 1)]
        change = (price - past_price) / past_price if past_price > 0 else 0.0
        if change >= threshold:
            return "BUY"
        if change <= -threshold:
            return "SELL"
        return "HOLD"

    # Default: moving-average crossover.
    short_window = int(parameters.get("short_window", 5))
    long_window = int(parameters.get("long_window", 20))
    if len(history) < max(short_window, long_window):
        return "HOLD"
    short_ma = _mean(history[-short_window:])
    long_ma = _mean(history[-long_window:])
    if short_ma > long_ma * 1.0001:
        return "BUY"
    if short_ma < long_ma * 0.9999:
        return "SELL"
    return "HOLD"


def _run_backtest_simulation(
    strategy: Strategy,
    symbols: list[str],
    start_date: date,
    end_date: date,
    initial_capital: float,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    days = _daterange(start_date, end_date)
    if len(days) < 3:
        raise HTTPException(status_code=400, detail="Backtest period must include at least 3 days")

    price_map = {symbol: _series_for_symbol(symbol, days) for symbol in symbols}
    cash = float(initial_capital)
    allocation = float(parameters.get("allocation_per_trade", 0.25))
    allocation = min(max(allocation, 0.05), 0.95)
    commission_rate = float(parameters.get("commission_rate", 0.001))
    commission_rate = min(max(commission_rate, 0.0), 0.02)

    positions: dict[str, float] = {symbol: 0.0 for symbol in symbols}
    average_cost: dict[str, float] = {symbol: 0.0 for symbol in symbols}
    trade_events: list[dict[str, Any]] = []
    closed_trade_pnls: list[float] = []
    equity_curve: list[dict[str, Any]] = []

    for day_idx, trade_day in enumerate(days):
        for symbol in symbols:
            history = price_map[symbol][: day_idx + 1]
            price = history[-1]
            signal = _signal_for_strategy(strategy.strategy_type, history, parameters)
            quantity = positions[symbol]

            if signal == "BUY" and quantity <= 1e-8:
                budget = cash * allocation
                unit_cost = price * (1.0 + commission_rate)
                buy_qty = math.floor(budget / unit_cost)
                if buy_qty >= 1:
                    notional = buy_qty * price
                    commission = notional * commission_rate
                    cash -= notional + commission
                    positions[symbol] = float(buy_qty)
                    average_cost[symbol] = float(price)
                    trade_events.append(
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": float(buy_qty),
                            "price": float(price),
                            "commission": float(commission),
                            "timestamp": datetime.combine(trade_day, datetime.min.time(), tzinfo=timezone.utc),
                            "pnl": 0.0,
                            "is_simulated": True,
                        }
                    )

            elif signal == "SELL" and quantity > 1e-8:
                notional = quantity * price
                commission = notional * commission_rate
                pnl = notional - commission - quantity * average_cost[symbol]
                cash += notional - commission
                positions[symbol] = 0.0
                average_cost[symbol] = 0.0
                closed_trade_pnls.append(float(pnl))
                trade_events.append(
                    {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": float(quantity),
                        "price": float(price),
                        "commission": float(commission),
                        "timestamp": datetime.combine(trade_day, datetime.min.time(), tzinfo=timezone.utc),
                        "pnl": float(pnl),
                        "is_simulated": True,
                    }
                )

        equity = cash + sum(
            positions[symbol] * price_map[symbol][day_idx] for symbol in symbols
        )
        equity_curve.append({"date": trade_day.isoformat(), "value": round(float(equity), 4)})

    # Force close all remaining positions on the final day for stable realized metrics.
    close_day = days[-1]
    for symbol in symbols:
        quantity = positions[symbol]
        if quantity <= 1e-8:
            continue
        price = price_map[symbol][-1]
        notional = quantity * price
        commission = notional * commission_rate
        pnl = notional - commission - quantity * average_cost[symbol]
        cash += notional - commission
        positions[symbol] = 0.0
        average_cost[symbol] = 0.0
        closed_trade_pnls.append(float(pnl))
        trade_events.append(
            {
                "symbol": symbol,
                "action": "SELL",
                "quantity": float(quantity),
                "price": float(price),
                "commission": float(commission),
                "timestamp": datetime.combine(close_day, datetime.max.time(), tzinfo=timezone.utc),
                "pnl": float(pnl),
                "is_simulated": True,
            }
        )

    final_value = float(cash)
    total_return_pct = ((final_value - initial_capital) / initial_capital * 100.0) if initial_capital > 0 else 0.0

    daily_values = [float(point["value"]) for point in equity_curve]
    daily_returns = [
        (daily_values[idx] / daily_values[idx - 1] - 1.0)
        for idx in range(1, len(daily_values))
        if daily_values[idx - 1] > 0
    ]
    if len(daily_returns) > 1:
        std = statistics.stdev(daily_returns)
        sharpe = (statistics.mean(daily_returns) / std) * math.sqrt(252) if std > 1e-12 else 0.0
    else:
        sharpe = 0.0

    peak = daily_values[0]
    max_drawdown = 0.0
    for value in daily_values:
        peak = max(peak, value)
        drawdown = (value - peak) / peak if peak > 0 else 0.0
        max_drawdown = min(max_drawdown, drawdown)

    win_count = len([pnl for pnl in closed_trade_pnls if pnl > 0])
    win_rate = (win_count / len(closed_trade_pnls) * 100.0) if closed_trade_pnls else 0.0

    return {
        "final_value": round(final_value, 4),
        "total_return": round(total_return_pct, 4),
        "sharpe_ratio": round(float(sharpe), 4),
        "max_drawdown": round(abs(float(max_drawdown)) * 100.0, 4),
        "win_rate": round(float(win_rate), 4),
        "trade_count": len(trade_events),
        "trades": trade_events,
        "results": {
            "equity_curve": equity_curve,
            "closed_trade_pnls": [round(float(item), 4) for item in closed_trade_pnls],
            "symbols": symbols,
            "days": len(days),
            "strategy_type": strategy.strategy_type,
            "parameters_used": parameters,
        },
    }


def _get_backtest_or_404(db: Session, backtest_id: int) -> Backtest:
    item = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return item


@router.post("/", response_model=BacktestResponse, status_code=201)
async def run_backtest(payload: BacktestCreate, db: Session = Depends(get_db)):
    """Create and run a backtest synchronously."""
    if payload.start_date > payload.end_date:
        raise HTTPException(status_code=400, detail="start_date must be earlier than or equal to end_date")

    strategy = db.query(Strategy).filter(Strategy.id == payload.strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if payload.portfolio_id is not None:
        portfolio = db.query(Portfolio).filter(Portfolio.id == payload.portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

    symbols = _normalize_symbols(payload.symbols)
    merged_parameters = dict(strategy.parameters or {})
    merged_parameters.update(payload.parameters or {})

    backtest = Backtest(
        strategy_id=strategy.id,
        portfolio_id=payload.portfolio_id,
        symbols=symbols,
        start_date=payload.start_date,
        end_date=payload.end_date,
        initial_capital=payload.initial_capital,
        parameters=merged_parameters,
        status="running",
    )
    db.add(backtest)
    db.commit()
    db.refresh(backtest)

    try:
        simulation = _run_backtest_simulation(
            strategy=strategy,
            symbols=symbols,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            parameters=merged_parameters,
        )
        backtest.final_value = simulation["final_value"]
        backtest.total_return = simulation["total_return"]
        backtest.sharpe_ratio = simulation["sharpe_ratio"]
        backtest.max_drawdown = simulation["max_drawdown"]
        backtest.win_rate = simulation["win_rate"]
        backtest.trade_count = simulation["trade_count"]
        backtest.results = simulation["results"]
        backtest.status = "completed"
        backtest.completed_at = datetime.now(timezone.utc)

        for item in simulation["trades"]:
            db.add(
                Trade(
                    backtest_id=backtest.id,
                    portfolio_id=payload.portfolio_id,
                    symbol=item["symbol"],
                    action=item["action"],
                    quantity=item["quantity"],
                    price=item["price"],
                    commission=item["commission"],
                    timestamp=item["timestamp"],
                    pnl=item["pnl"],
                    is_simulated=True,
                )
            )
        db.commit()
    except HTTPException:
        backtest.status = "failed"
        backtest.results = {"error": "validation failed during simulation"}
        backtest.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise
    except Exception as exc:
        backtest.status = "failed"
        backtest.results = {"error": str(exc)}
        backtest.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail="Backtest execution failed") from exc

    db.refresh(backtest)
    return backtest


@router.get("/", response_model=list[BacktestResponse])
async def list_backtests(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List backtests sorted by latest created."""
    query = db.query(Backtest)
    if status:
        query = query.filter(Backtest.status == status)
    return query.order_by(Backtest.created_at.desc(), Backtest.id.desc()).limit(limit).all()


@router.get("/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """Get one backtest with full trade records."""
    backtest = _get_backtest_or_404(db, backtest_id)
    trades = (
        db.query(Trade)
        .filter(Trade.backtest_id == backtest_id)
        .order_by(Trade.timestamp.asc(), Trade.id.asc())
        .all()
    )
    return BacktestDetailResponse(
        **BacktestResponse.model_validate(backtest).model_dump(),
        trades=[BacktestTradeResponse.model_validate(item) for item in trades],
    )


@router.get("/{backtest_id}/trades", response_model=list[BacktestTradeResponse])
async def get_backtest_trades(backtest_id: int, db: Session = Depends(get_db)):
    """List trades generated by one backtest."""
    _get_backtest_or_404(db, backtest_id)
    return (
        db.query(Trade)
        .filter(Trade.backtest_id == backtest_id)
        .order_by(Trade.timestamp.asc(), Trade.id.asc())
        .all()
    )
