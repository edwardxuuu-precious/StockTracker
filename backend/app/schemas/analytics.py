"""Pydantic schemas for portfolio analytics responses."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PortfolioSummaryResponse(BaseModel):
    """Top-level analytics metrics for a portfolio."""

    portfolio_id: int
    portfolio_name: str
    initial_capital: float
    cash_balance: float
    holdings_market_value: float
    current_value: float
    total_return: float
    total_return_pct: float
    realized_pnl: float
    unrealized_pnl: float
    active_holdings: int
    total_trades: int


class AllocationItemResponse(BaseModel):
    """Single holding allocation item."""

    symbol: str
    quantity: float
    current_price: float
    market_value: float
    weight_pct: float
    unrealized_pnl: float


class TrendPointResponse(BaseModel):
    """Cumulative realized PnL point used by line chart."""

    timestamp: datetime
    label: str
    trade_realized_pnl: float
    cumulative_realized_pnl: float


class MonthlyPnlItemResponse(BaseModel):
    """Monthly realized PnL bar-chart data."""

    month: str
    realized_pnl: float
    trade_count: int


class PortfolioAnalyticsResponse(BaseModel):
    """Aggregated analytics payload for analysis dashboard."""

    summary: PortfolioSummaryResponse
    allocation: list[AllocationItemResponse]
    trend: list[TrendPointResponse]
    monthly_realized_pnl: list[MonthlyPnlItemResponse]


class ExportResponse(BaseModel):
    """Metadata for CSV export endpoint."""

    report: Literal["summary", "holdings", "trades"]
    filename: str
