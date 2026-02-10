"""Holding and trade API endpoints."""
from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...models.portfolio import Holding, Portfolio, PortfolioTrade
from ...schemas.portfolio import HoldingCreate, HoldingResponse
from ...schemas.trade import PortfolioTradeCreate, PortfolioTradeResponse
from ...services.quote_service import AkshareQuoteProvider, QuoteFetchError, QuoteService, StooqQuoteProvider

router = APIRouter()
settings = get_settings()
trade_quote_service = QuoteService(cache_ttl_seconds=settings.CACHE_QUOTE_TTL)
# Keep trade-time symbol verification responsive by avoiding slower provider chains.
trade_quote_service.providers = [StooqQuoteProvider(timeout_seconds=4), AkshareQuoteProvider()]


def _get_portfolio_or_404(db: Session, portfolio_id: int) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


def _refresh_holding_snapshot(holding: Holding, price: float) -> None:
    holding.current_price = price
    holding.market_value = holding.quantity * price
    holding.unrealized_pnl = (price - holding.average_cost) * holding.quantity


def _is_supported_symbol_format(symbol: str) -> bool:
    normalized = str(symbol or "").strip().upper()
    if not normalized:
        return False
    if re.fullmatch(r"\d{6}", normalized):
        return True
    if re.fullmatch(r"\d{6}\.(SS|SZ|BJ)", normalized):
        return True
    if re.fullmatch(r"(SH|SZ|BJ)\d{6}", normalized):
        return True
    # Common US equity formats (e.g. AAPL, BRK.B)
    if re.fullmatch(r"[A-Z]{1,5}(\.[A-Z]{1,2})?", normalized):
        return True
    return False


def _validate_buy_symbol(symbol: str) -> None:
    if not _is_supported_symbol_format(symbol):
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported symbol format: {symbol}")

    try:
        trade_quote_service.get_quote(symbol, refresh=False)
    except QuoteFetchError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot verify symbol from quote source: {symbol}. Please check symbol code and retry.",
        ) from exc


def _refresh_portfolio_value(db: Session, portfolio: Portfolio) -> None:
    # SessionLocal is configured with autoflush=False, so force a flush before querying
    # aggregates to avoid stale current_value when holdings were added/deleted in-session.
    db.flush()
    total_holdings_value = (
        db.query(func.coalesce(func.sum(Holding.market_value), 0.0))
        .filter(Holding.portfolio_id == portfolio.id)
        .scalar()
        or 0.0
    )
    portfolio.current_value = portfolio.cash_balance + total_holdings_value


def _merge_duplicate_symbol_holdings(db: Session, portfolio_id: int, symbol: str) -> Holding | None:
    """Collapse duplicate holdings of the same symbol into one row."""
    rows = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio_id, Holding.symbol == symbol)
        .order_by(Holding.id.asc())
        .all()
    )
    if not rows:
        return None

    primary = rows[0]
    for duplicate in rows[1:]:
        total_qty = primary.quantity + duplicate.quantity
        if total_qty <= 1e-8:
            db.delete(duplicate)
            continue

        total_cost = (primary.quantity * primary.average_cost) + (duplicate.quantity * duplicate.average_cost)
        total_market_value = float(primary.market_value or 0.0) + float(duplicate.market_value or 0.0)
        primary.quantity = total_qty
        primary.average_cost = total_cost / total_qty
        merged_price = (total_market_value / total_qty) if total_qty > 0 else primary.average_cost
        _refresh_holding_snapshot(primary, merged_price)
        db.delete(duplicate)

    if primary.current_price <= 0:
        _refresh_holding_snapshot(primary, primary.average_cost)
    return primary


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=201)
async def add_holding(
    portfolio_id: int,
    holding: HoldingCreate,
    db: Session = Depends(get_db),
):
    """Add a holding directly (legacy endpoint kept for compatibility)."""
    portfolio = _get_portfolio_or_404(db, portfolio_id)
    symbol = holding.symbol.strip().upper()
    cost = holding.quantity * holding.average_cost
    if portfolio.cash_balance < cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient cash balance. Available: ${portfolio.cash_balance:.2f}",
        )

    db_holding = _merge_duplicate_symbol_holdings(db, portfolio_id, symbol)
    if db_holding:
        old_total_cost = db_holding.quantity * db_holding.average_cost
        old_market_value = float(db_holding.market_value or 0.0)
        new_quantity = db_holding.quantity + holding.quantity
        new_total_cost = old_total_cost + cost
        db_holding.quantity = new_quantity
        db_holding.average_cost = new_total_cost / new_quantity
        merged_market_value = old_market_value + cost
        merged_price = merged_market_value / new_quantity
        _refresh_holding_snapshot(db_holding, merged_price)
    else:
        db_holding = Holding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=holding.quantity,
            average_cost=holding.average_cost,
            current_price=holding.average_cost,
            market_value=cost,
            unrealized_pnl=0.0,
        )
        db.add(db_holding)

    portfolio.cash_balance -= cost
    _refresh_portfolio_value(db, portfolio)
    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=204)
async def remove_holding(
    portfolio_id: int,
    holding_id: int,
    db: Session = Depends(get_db),
):
    """Remove a holding directly (legacy endpoint kept for compatibility)."""
    portfolio = _get_portfolio_or_404(db, portfolio_id)

    holding = (
        db.query(Holding)
        .filter(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
        .first()
    )
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    portfolio.cash_balance += holding.market_value
    db.delete(holding)
    _refresh_portfolio_value(db, portfolio)
    db.commit()
    return None


@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    portfolio_id: int,
    holding_id: int,
    holding_update: HoldingCreate,
    db: Session = Depends(get_db),
):
    """Update holding quantity/cost directly (legacy endpoint kept for compatibility)."""
    portfolio = _get_portfolio_or_404(db, portfolio_id)
    symbol = holding_update.symbol.strip().upper()

    db_holding = (
        db.query(Holding)
        .filter(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
        .first()
    )
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    old_cost = db_holding.quantity * db_holding.average_cost
    new_cost = holding_update.quantity * holding_update.average_cost
    cash_diff = new_cost - old_cost

    if cash_diff > 0 and portfolio.cash_balance < cash_diff:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient cash balance. Available: ${portfolio.cash_balance:.2f}, Required: ${cash_diff:.2f}",
        )

    duplicate_symbol_holding = (
        db.query(Holding)
        .filter(
            Holding.portfolio_id == portfolio_id,
            Holding.symbol == symbol,
            Holding.id != holding_id,
        )
        .first()
    )

    if duplicate_symbol_holding:
        old_duplicate_cost = duplicate_symbol_holding.quantity * duplicate_symbol_holding.average_cost
        old_duplicate_market_value = float(duplicate_symbol_holding.market_value or 0.0)
        merged_quantity = duplicate_symbol_holding.quantity + holding_update.quantity
        merged_total_cost = old_duplicate_cost + new_cost
        duplicate_symbol_holding.quantity = merged_quantity
        duplicate_symbol_holding.average_cost = merged_total_cost / merged_quantity
        merged_market_value = old_duplicate_market_value + new_cost
        merged_price = merged_market_value / merged_quantity
        _refresh_holding_snapshot(duplicate_symbol_holding, merged_price)
        db.delete(db_holding)
        result_holding = duplicate_symbol_holding
    else:
        db_holding.symbol = symbol
        db_holding.quantity = holding_update.quantity
        db_holding.average_cost = holding_update.average_cost
        _refresh_holding_snapshot(db_holding, holding_update.average_cost)
        result_holding = db_holding

    portfolio.cash_balance -= cash_diff
    _refresh_portfolio_value(db, portfolio)
    db.commit()
    db.refresh(result_holding)
    return result_holding


@router.post("/{portfolio_id}/trades", response_model=PortfolioTradeResponse, status_code=201)
async def execute_trade(
    portfolio_id: int,
    trade: PortfolioTradeCreate,
    db: Session = Depends(get_db),
):
    """Execute BUY/SELL trade with weighted-average cost accounting."""
    portfolio = _get_portfolio_or_404(db, portfolio_id)
    symbol = trade.symbol.strip().upper()
    amount = trade.quantity * trade.price
    realized_pnl = 0.0

    holding = _merge_duplicate_symbol_holdings(db, portfolio_id, symbol)

    if trade.action == "BUY":
        _validate_buy_symbol(symbol)
        total_cost = amount + trade.commission
        if portfolio.cash_balance < total_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient cash balance. Available: ${portfolio.cash_balance:.2f}, Required: ${total_cost:.2f}",
            )

        if holding:
            old_total_cost = holding.quantity * holding.average_cost
            new_quantity = holding.quantity + trade.quantity
            new_total_cost = old_total_cost + amount + trade.commission
            holding.quantity = new_quantity
            holding.average_cost = new_total_cost / new_quantity
            _refresh_holding_snapshot(holding, trade.price)
        else:
            average_cost = (amount + trade.commission) / trade.quantity
            holding = Holding(
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=trade.quantity,
                average_cost=average_cost,
            )
            _refresh_holding_snapshot(holding, trade.price)
            db.add(holding)

        portfolio.cash_balance -= total_cost

    else:  # SELL
        if not holding:
            raise HTTPException(status_code=400, detail=f"No holdings found for symbol {symbol}")
        if holding.quantity < trade.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient holding quantity. Current: {holding.quantity}, Requested: {trade.quantity}",
            )

        net_proceeds = amount - trade.commission
        if net_proceeds < 0:
            raise HTTPException(status_code=400, detail="Commission cannot exceed trade proceeds")

        realized_pnl = (trade.price - holding.average_cost) * trade.quantity - trade.commission
        portfolio.cash_balance += net_proceeds

        remaining_qty = holding.quantity - trade.quantity
        if remaining_qty <= 1e-8:
            db.delete(holding)
        else:
            holding.quantity = remaining_qty
            _refresh_holding_snapshot(holding, trade.price)

    db_trade = PortfolioTrade(
        portfolio_id=portfolio_id,
        symbol=symbol,
        action=trade.action,
        quantity=trade.quantity,
        price=trade.price,
        commission=trade.commission,
        amount=amount,
        realized_pnl=realized_pnl,
        trade_time=datetime.now(timezone.utc),
    )
    db.add(db_trade)

    _refresh_portfolio_value(db, portfolio)
    db.commit()
    db.refresh(db_trade)
    return db_trade


@router.get("/{portfolio_id}/trades", response_model=list[PortfolioTradeResponse])
async def list_portfolio_trades(
    portfolio_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List latest portfolio trade records (newest first)."""
    _get_portfolio_or_404(db, portfolio_id)
    return (
        db.query(PortfolioTrade)
        .filter(PortfolioTrade.portfolio_id == portfolio_id)
        .order_by(PortfolioTrade.trade_time.desc(), PortfolioTrade.id.desc())
        .limit(limit)
        .all()
    )
