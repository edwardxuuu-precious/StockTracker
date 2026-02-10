"""Pydantic schemas for strategy version APIs."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrategyVersionResponse(BaseModel):
    id: int
    strategy_id: int
    version_no: int
    name: str
    description: str | None = None
    strategy_type: str
    parameters: dict[str, Any] | None = None
    code: str | None = None
    note: str | None = None
    created_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyVersionCreate(BaseModel):
    note: str | None = Field(default=None, max_length=255)
    created_by: str = Field(default="manual", max_length=50)


class StrategyVersionCompareRequest(BaseModel):
    version_ids: list[int] = Field(..., min_length=2, max_length=10)


class StrategyVersionCompareItem(BaseModel):
    version: StrategyVersionResponse
    backtest_count: int
    best_total_return: float | None = None
    best_sharpe_ratio: float | None = None
    latest_completed_at: datetime | None = None


class StrategyVersionCompareResponse(BaseModel):
    items: list[StrategyVersionCompareItem]
