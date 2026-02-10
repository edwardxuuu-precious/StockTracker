"""Pydantic schemas for portfolio trade operations."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PortfolioTradeCreate(BaseModel):
    """Schema for creating a buy/sell trade."""

    symbol: str = Field(..., min_length=1, max_length=20)
    action: Literal["BUY", "SELL"]
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    commission: float = Field(0.0, ge=0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class PortfolioTradeResponse(BaseModel):
    """Schema for portfolio trade response."""

    id: int
    portfolio_id: int
    symbol: str
    action: str
    quantity: float
    price: float
    commission: float
    amount: float
    realized_pnl: float
    trade_time: datetime

    model_config = ConfigDict(from_attributes=True)
