"""Backtest API endpoints and local-data backtest engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
import math
import statistics
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.backtest import Backtest, Trade
from ...models.market_data import Bar1d, Bar1m, Instrument
from ...models.portfolio import Portfolio
from ...models.strategy import Strategy
from ...models.strategy_version import StrategyVersion
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


@dataclass(frozen=True)
class BarPoint:
    ts: datetime
    close: float


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


def _resolve_market_for_symbol(symbol: str, parameters: dict[str, Any]) -> str | None:
    markets = parameters.get("markets")
    if isinstance(markets, dict):
        key = symbol.upper()
        market = markets.get(key) or markets.get(key.lower())
        if market:
            return str(market).strip().upper()
    market = parameters.get("market")
    if market:
        return str(market).strip().upper()
    return None


def _resolve_instrument(db: Session, symbol: str, market: str | None) -> Instrument:
    symbol = symbol.upper()
    query = db.query(Instrument).filter(Instrument.symbol == symbol)
    if market:
        query = query.filter(Instrument.market == market.upper())
    items = query.all()
    if not items:
        raise HTTPException(status_code=404, detail=f"Instrument not found for {symbol}")
    if len(items) > 1:
        raise HTTPException(
            status_code=400,
            detail=f"Multiple markets found for {symbol}; specify market.",
        )
    return items[0]


def _get_bar_model(interval: str):
    return Bar1m if interval == "1m" else Bar1d


def _load_local_bars(
    db: Session,
    symbol: str,
    market: str | None,
    interval: str,
    start_dt: datetime | None,
    end_dt: datetime | None,
) -> tuple[list[BarPoint], str]:
    instrument = _resolve_instrument(db, symbol, market)
    model = _get_bar_model(interval)
    query = db.query(model.ts, model.close).filter(model.instrument_id == instrument.id)
    if start_dt:
        query = query.filter(model.ts >= start_dt)
    if end_dt:
        query = query.filter(model.ts <= end_dt)
    rows = query.order_by(model.ts.asc()).all()
    if not rows:
        raise HTTPException(
            status_code=400,
            detail=f"No local bars available for {instrument.symbol} {instrument.market}",
        )
    bars = [BarPoint(ts=row[0], close=float(row[1])) for row in rows]
    return bars, instrument.market


def _annualization_factor(interval: str) -> float:
    if interval == "1m":
        return 252.0 * 390.0
    return 252.0


def _compute_performance_metrics(
    *,
    initial_capital: float,
    final_value: float,
    equity_values: list[float],
    closed_trade_pnls: list[float],
    interval: str,
) -> dict[str, float]:
    total_return_pct = ((final_value - initial_capital) / initial_capital * 100.0) if initial_capital > 0 else 0.0

    period_returns = [
        (equity_values[idx] / equity_values[idx - 1] - 1.0)
        for idx in range(1, len(equity_values))
        if equity_values[idx - 1] > 0
    ]
    if len(period_returns) > 1:
        std = statistics.stdev(period_returns)
        factor = _annualization_factor(interval)
        sharpe = (statistics.mean(period_returns) / std) * math.sqrt(factor) if std > 1e-12 else 0.0
    else:
        sharpe = 0.0

    peak = equity_values[0] if equity_values else 0.0
    max_drawdown = 0.0
    for value in equity_values:
        peak = max(peak, value)
        drawdown = (value - peak) / peak if peak > 0 else 0.0
        max_drawdown = min(max_drawdown, drawdown)

    win_count = len([pnl for pnl in closed_trade_pnls if pnl > 0])
    win_rate = (win_count / len(closed_trade_pnls) * 100.0) if closed_trade_pnls else 0.0

    return {
        "total_return": round(float(total_return_pct), 4),
        "sharpe_ratio": round(float(sharpe), 4),
        "max_drawdown": round(abs(float(max_drawdown)) * 100.0, 4),
        "win_rate": round(float(win_rate), 4),
    }


def _run_backtest_local(
    strategy: Strategy,
    symbols: list[str],
    bars_by_symbol: dict[str, list[BarPoint]],
    initial_capital: float,
    parameters: dict[str, Any],
    interval: str,
) -> dict[str, Any]:
    timeline = sorted({item.ts for bars in bars_by_symbol.values() for item in bars})
    if len(timeline) < 3:
        raise HTTPException(status_code=400, detail="Backtest period must include at least 3 bars")

    cash = float(initial_capital)
    allocation = float(parameters.get("allocation_per_trade", 0.25))
    allocation = min(max(allocation, 0.05), 0.95)
    commission_rate = float(parameters.get("commission_rate", 0.001))
    commission_rate = min(max(commission_rate, 0.0), 0.02)

    positions: dict[str, float] = {symbol: 0.0 for symbol in symbols}
    average_cost: dict[str, float] = {symbol: 0.0 for symbol in symbols}
    indices: dict[str, int] = {symbol: 0 for symbol in symbols}
    history: dict[str, list[float]] = {symbol: [] for symbol in symbols}
    last_price: dict[str, float | None] = {symbol: None for symbol in symbols}
    trade_events: list[dict[str, Any]] = []
    closed_trade_pnls: list[float] = []
    equity_curve: list[dict[str, Any]] = []

    for ts in timeline:
        for symbol in symbols:
            bars = bars_by_symbol[symbol]
            idx = indices[symbol]
            updated = False
            while idx < len(bars) and bars[idx].ts == ts:
                price = bars[idx].close
                history[symbol].append(price)
                last_price[symbol] = price
                idx += 1
                updated = True
            indices[symbol] = idx
            if not updated:
                continue

            price = last_price[symbol]
            if price is None:
                continue
            signal = _signal_for_strategy(strategy.strategy_type, history[symbol], parameters)
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
                            "timestamp": ts,
                            "pnl": 0.0,
                            "is_simulated": False,
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
                            "timestamp": ts,
                            "pnl": float(pnl),
                            "is_simulated": False,
                        }
                    )

        equity = cash + sum(
            positions[symbol] * (last_price[symbol] or 0.0) for symbol in symbols
        )
        equity_curve.append({"timestamp": ts.isoformat(), "value": round(float(equity), 4)})

    # Force close all remaining positions on the final day for stable realized metrics.
    close_ts = timeline[-1]
    for symbol in symbols:
        quantity = positions[symbol]
        if quantity <= 1e-8:
            continue
        price = last_price[symbol] or 0.0
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
                "timestamp": close_ts,
                "pnl": float(pnl),
                "is_simulated": False,
            }
        )

    final_value = float(cash)
    if equity_curve:
        # Keep equity curve terminal value consistent with forced liquidation costs.
        equity_curve[-1]["value"] = round(final_value, 4)
    equity_values = [float(point["value"]) for point in equity_curve]
    metrics = _compute_performance_metrics(
        initial_capital=initial_capital,
        final_value=final_value,
        equity_values=equity_values,
        closed_trade_pnls=closed_trade_pnls,
        interval=interval,
    )

    return {
        "final_value": round(final_value, 4),
        "total_return": metrics["total_return"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "max_drawdown": metrics["max_drawdown"],
        "win_rate": metrics["win_rate"],
        "trade_count": len(trade_events),
        "trades": trade_events,
        "results": {
            "equity_curve": equity_curve,
            "closed_trade_pnls": [round(float(item), 4) for item in closed_trade_pnls],
            "symbols": symbols,
            "bars": len(timeline),
            "strategy_type": strategy.strategy_type,
            "parameters_used": parameters,
            "interval": interval,
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

    strategy_version = None
    if payload.strategy_version_id is not None:
        strategy_version = (
            db.query(StrategyVersion)
            .filter(StrategyVersion.id == payload.strategy_version_id)
            .first()
        )
        if not strategy_version:
            raise HTTPException(status_code=404, detail="Strategy version not found")
        if strategy_version.strategy_id != strategy.id:
            raise HTTPException(status_code=400, detail="strategy_version_id does not belong to strategy_id")

    if payload.portfolio_id is not None:
        portfolio = db.query(Portfolio).filter(Portfolio.id == payload.portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

    symbols = _normalize_symbols(payload.symbols)
    base_parameters = strategy_version.parameters if strategy_version else strategy.parameters
    merged_parameters = dict(base_parameters or {})
    merged_parameters.update(payload.parameters or {})
    interval = str(merged_parameters.get("interval", "1d")).strip().lower()
    if interval not in {"1m", "1d"}:
        raise HTTPException(status_code=400, detail="interval must be 1m or 1d")

    start_dt = datetime.combine(payload.start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(payload.end_date, time.max, tzinfo=timezone.utc)

    bars_by_symbol: dict[str, list[BarPoint]] = {}
    markets_used: dict[str, str] = {}
    for symbol in symbols:
        market = _resolve_market_for_symbol(symbol, merged_parameters)
        bars, resolved_market = _load_local_bars(db, symbol, market, interval, start_dt, end_dt)
        bars_by_symbol[symbol] = bars
        markets_used[symbol] = resolved_market

    backtest = Backtest(
        strategy_id=strategy.id,
        strategy_version_id=payload.strategy_version_id,
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
        simulation = _run_backtest_local(
            strategy=strategy,
            symbols=symbols,
            bars_by_symbol=bars_by_symbol,
            initial_capital=payload.initial_capital,
            parameters=merged_parameters,
            interval=interval,
        )
        backtest.final_value = simulation["final_value"]
        backtest.total_return = simulation["total_return"]
        backtest.sharpe_ratio = simulation["sharpe_ratio"]
        backtest.max_drawdown = simulation["max_drawdown"]
        backtest.win_rate = simulation["win_rate"]
        backtest.trade_count = simulation["trade_count"]
        backtest.results = simulation["results"]
        backtest.results["strategy_version_id"] = payload.strategy_version_id
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
                    is_simulated=False,
                )
            )
        db.commit()
    except HTTPException:
        backtest.status = "failed"
        backtest.results = {"error": "validation failed during local-data backtest"}
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
