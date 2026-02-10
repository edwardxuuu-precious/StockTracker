"""Pydantic schemas for backtest operations."""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BacktestCreate(BaseModel):
    """Input payload for launching a backtest."""

    strategy_id: int = Field(..., gt=0)
    strategy_version_id: Optional[int] = Field(default=None, gt=0)
    portfolio_id: Optional[int] = Field(default=None, gt=0)
    symbols: list[str] = Field(..., min_length=1, max_length=20)
    start_date: date
    end_date: date
    initial_capital: float = Field(..., gt=0)
    parameters: dict[str, Any] = Field(default_factory=dict)


class BacktestTradeResponse(BaseModel):
    """Simulated trade record from a backtest run."""

    id: int
    symbol: str
    action: str
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    pnl: float
    is_simulated: bool

    model_config = ConfigDict(from_attributes=True)


class BacktestResponse(BaseModel):
    """Summary response for a backtest."""

    id: int
    strategy_id: int
    strategy_version_id: Optional[int]
    portfolio_id: Optional[int]
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: float
    final_value: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    parameters: Optional[dict[str, Any]]
    status: str
    results: Optional[dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class BacktestDetailResponse(BacktestResponse):
    """Detailed backtest response including trade list."""

    trades: list[BacktestTradeResponse] = Field(default_factory=list)
