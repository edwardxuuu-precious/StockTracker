"""Portfolio analytics and CSV export endpoints."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.portfolio import Holding, Portfolio, PortfolioTrade
from ...schemas.analytics import (
    AllocationItemResponse,
    MonthlyPnlItemResponse,
    PortfolioAnalyticsResponse,
    PortfolioSummaryResponse,
    TrendPointResponse,
)

router = APIRouter()


def _get_portfolio_or_404(db: Session, portfolio_id: int) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


def _build_summary(
    db: Session,
    portfolio: Portfolio,
    holdings: list[Holding],
    trades: list[PortfolioTrade],
) -> PortfolioSummaryResponse:
    holdings_value = sum(float(holding.market_value or 0.0) for holding in holdings)
    current_value = float(portfolio.cash_balance or 0.0) + holdings_value
    total_return = current_value - float(portfolio.initial_capital or 0.0)
    total_return_pct = (
        (total_return / float(portfolio.initial_capital) * 100.0)
        if float(portfolio.initial_capital or 0.0) > 0
        else 0.0
    )
    realized_pnl = (
        db.query(func.coalesce(func.sum(PortfolioTrade.realized_pnl), 0.0))
        .filter(PortfolioTrade.portfolio_id == portfolio.id)
        .scalar()
        or 0.0
    )
    unrealized_pnl = sum(float(holding.unrealized_pnl or 0.0) for holding in holdings)

    return PortfolioSummaryResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        initial_capital=float(portfolio.initial_capital or 0.0),
        cash_balance=float(portfolio.cash_balance or 0.0),
        holdings_market_value=float(holdings_value),
        current_value=float(current_value),
        total_return=float(total_return),
        total_return_pct=float(total_return_pct),
        realized_pnl=float(realized_pnl),
        unrealized_pnl=float(unrealized_pnl),
        active_holdings=len(holdings),
        total_trades=len(trades),
    )


def _format_trade_time(value: datetime) -> str:
    """Return a human-friendly and machine-parseable UTC timestamp."""
    if value.tzinfo is None:
        utc_value = value.replace(tzinfo=timezone.utc)
    else:
        utc_value = value.astimezone(timezone.utc)
    return utc_value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _build_allocation(holdings: list[Holding]) -> list[AllocationItemResponse]:
    total_value = sum(float(holding.market_value or 0.0) for holding in holdings)
    if total_value <= 0:
        total_value = 0.0

    items: list[AllocationItemResponse] = []
    for holding in sorted(holdings, key=lambda item: float(item.market_value or 0.0), reverse=True):
        market_value = float(holding.market_value or 0.0)
        weight_pct = (market_value / total_value * 100.0) if total_value > 0 else 0.0
        items.append(
            AllocationItemResponse(
                symbol=holding.symbol,
                quantity=float(holding.quantity or 0.0),
                current_price=float(holding.current_price or 0.0),
                market_value=market_value,
                weight_pct=float(weight_pct),
                unrealized_pnl=float(holding.unrealized_pnl or 0.0),
            )
        )
    return items


def _build_trend(portfolio: Portfolio, trades: list[PortfolioTrade]) -> list[TrendPointResponse]:
    running = 0.0
    points: list[TrendPointResponse] = []
    created_at = portfolio.created_at or datetime.utcnow()

    points.append(
        TrendPointResponse(
            timestamp=created_at,
            label="初始",
            trade_realized_pnl=0.0,
            cumulative_realized_pnl=0.0,
        )
    )

    ordered = sorted(trades, key=lambda item: (item.trade_time, item.id))
    for trade in ordered:
        delta = float(trade.realized_pnl or 0.0)
        running += delta
        points.append(
            TrendPointResponse(
                timestamp=trade.trade_time,
                label=f"{trade.symbol} {trade.action}",
                trade_realized_pnl=delta,
                cumulative_realized_pnl=float(running),
            )
        )
    return points


def _build_monthly_realized_pnl(trades: list[PortfolioTrade]) -> list[MonthlyPnlItemResponse]:
    grouped: dict[str, dict[str, float | int]] = {}
    for trade in trades:
        month = trade.trade_time.strftime("%Y-%m")
        bucket = grouped.setdefault(month, {"realized_pnl": 0.0, "trade_count": 0})
        bucket["realized_pnl"] = float(bucket["realized_pnl"]) + float(trade.realized_pnl or 0.0)
        bucket["trade_count"] = int(bucket["trade_count"]) + 1

    items: list[MonthlyPnlItemResponse] = []
    for month in sorted(grouped.keys()):
        bucket = grouped[month]
        items.append(
            MonthlyPnlItemResponse(
                month=month,
                realized_pnl=float(bucket["realized_pnl"]),
                trade_count=int(bucket["trade_count"]),
            )
        )
    return items


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = _get_portfolio_or_404(db, portfolio_id)
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio_id)
        .order_by(Holding.market_value.desc(), Holding.id.desc())
        .all()
    )
    trades = (
        db.query(PortfolioTrade)
        .filter(PortfolioTrade.portfolio_id == portfolio_id)
        .order_by(PortfolioTrade.trade_time.asc(), PortfolioTrade.id.asc())
        .all()
    )

    return PortfolioAnalyticsResponse(
        summary=_build_summary(db, portfolio, holdings, trades),
        allocation=_build_allocation(holdings),
        trend=_build_trend(portfolio, trades),
        monthly_realized_pnl=_build_monthly_realized_pnl(trades),
    )


def _csv_for_summary(summary: PortfolioSummaryResponse, exported_at: datetime) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "portfolio_id",
            "portfolio_name",
            "initial_capital",
            "cash_balance",
            "holdings_market_value",
            "current_value",
            "total_return",
            "total_return_pct",
            "realized_pnl",
            "unrealized_pnl",
            "active_holdings",
            "total_trades",
            "exported_at",
        ]
    )
    writer.writerow(
        [
            summary.portfolio_id,
            summary.portfolio_name,
            f"{summary.initial_capital:.2f}",
            f"{summary.cash_balance:.2f}",
            f"{summary.holdings_market_value:.2f}",
            f"{summary.current_value:.2f}",
            f"{summary.total_return:.2f}",
            f"{summary.total_return_pct:.4f}",
            f"{summary.realized_pnl:.2f}",
            f"{summary.unrealized_pnl:.2f}",
            summary.active_holdings,
            summary.total_trades,
            _format_trade_time(exported_at),
        ]
    )
    return buffer.getvalue()


def _csv_for_holdings(holdings: list[AllocationItemResponse], exported_at: datetime) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "symbol",
            "quantity",
            "current_price",
            "market_value",
            "weight_pct",
            "unrealized_pnl",
            "exported_at",
        ]
    )
    for item in holdings:
        writer.writerow(
            [
                item.symbol,
                f"{item.quantity:.6f}",
                f"{item.current_price:.4f}",
                f"{item.market_value:.2f}",
                f"{item.weight_pct:.4f}",
                f"{item.unrealized_pnl:.2f}",
                _format_trade_time(exported_at),
            ]
        )
    return buffer.getvalue()


def _csv_for_trades(trades: list[PortfolioTrade]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "trade_time",
            "symbol",
            "action",
            "quantity",
            "price",
            "commission",
            "amount",
            "realized_pnl",
        ]
    )
    for trade in trades:
        writer.writerow(
            [
                _format_trade_time(trade.trade_time),
                trade.symbol,
                trade.action,
                f"{float(trade.quantity or 0.0):.6f}",
                f"{float(trade.price or 0.0):.4f}",
                f"{float(trade.commission or 0.0):.4f}",
                f"{float(trade.amount or 0.0):.2f}",
                f"{float(trade.realized_pnl or 0.0):.2f}",
            ]
        )
    return buffer.getvalue()


@router.get("/portfolios/{portfolio_id}/export")
async def export_portfolio_analytics_csv(
    portfolio_id: int,
    report_type: Literal["summary", "holdings", "trades"] | None = Query(None, alias="report_type"),
    report: Literal["summary", "holdings", "trades"] | None = Query(None, alias="report"),
    db: Session = Depends(get_db),
):
    portfolio = _get_portfolio_or_404(db, portfolio_id)
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio_id)
        .order_by(Holding.market_value.desc(), Holding.id.desc())
        .all()
    )
    trades = (
        db.query(PortfolioTrade)
        .filter(PortfolioTrade.portfolio_id == portfolio_id)
        .order_by(PortfolioTrade.trade_time.desc(), PortfolioTrade.id.desc())
        .all()
    )
    summary = _build_summary(db, portfolio, holdings, trades)
    exported_at = datetime.now(timezone.utc)

    effective_report_type = report_type or report or "summary"
    if report_type and report and report_type != report:
        raise HTTPException(
            status_code=400,
            detail="Conflicting query params: report and report_type must match when both are provided.",
        )

    if effective_report_type == "summary":
        csv_content = _csv_for_summary(summary, exported_at)
    elif effective_report_type == "holdings":
        csv_content = _csv_for_holdings(_build_allocation(holdings), exported_at)
    else:
        csv_content = _csv_for_trades(trades)

    filename = f"portfolio_{portfolio_id}_{effective_report_type}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_content, media_type="text/csv; charset=utf-8", headers=headers)
