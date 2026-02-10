"""Pydantic schemas for strategy operations."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StrategyBase(BaseModel):
    """Base strategy fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: str = Field(..., min_length=1, max_length=50)
    parameters: dict = Field(default_factory=dict)


class StrategyCreate(StrategyBase):
    """Schema for creating a strategy."""

    code: Optional[str] = None
    created_from_chat: bool = False


class StrategyUpdate(BaseModel):
    """Schema for partial strategy update."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    parameters: Optional[dict] = None
    code: Optional[str] = None


class StrategyResponse(StrategyBase):
    """Schema returned by strategy APIs."""

    id: int
    code: Optional[str]
    created_from_chat: bool
    latest_version_no: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
