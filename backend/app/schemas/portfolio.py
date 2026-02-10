"""Pydantic schemas for portfolio operations."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HoldingBase(BaseModel):
    """Base schema for holdings."""
    symbol: str = Field(..., max_length=20)
    quantity: float = Field(..., gt=0)
    average_cost: float = Field(..., gt=0)


class HoldingCreate(HoldingBase):
    """Schema for creating a holding."""
    pass


class HoldingResponse(HoldingBase):
    """Schema for holding response."""
    id: int
    portfolio_id: int
    current_price: float
    market_value: float
    unrealized_pnl: float
    purchase_date: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PortfolioBase(BaseModel):
    """Base schema for portfolios."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    initial_capital: float = Field(..., gt=0)


class PortfolioCreate(PortfolioBase):
    """Schema for creating a portfolio."""
    holdings: List[HoldingCreate] = []


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response."""
    id: int
    current_value: float
    cash_balance: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    holdings: List[HoldingResponse] = []

    model_config = ConfigDict(from_attributes=True)
