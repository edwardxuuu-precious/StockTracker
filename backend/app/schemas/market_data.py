"""Schemas for local market data APIs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InstrumentResponse(BaseModel):
    id: int
    symbol: str
    market: str
    name: str | None = None
    exchange: str | None = None
    currency: str | None = None
    is_active: bool


class BarResponse(BaseModel):
    symbol: str
    market: str
    interval: Literal["1m", "1d"]
    ts: datetime = Field(..., description="UTC timestamp")
    open: float
    high: float
    low: float
    close: float
    volume: int | None = None
    source: str


class BarQuery(BaseModel):
    symbol: str
    market: str = "CN"
    interval: Literal["1m", "1d"] = "1m"
    start: datetime | None = None
    end: datetime | None = None
    limit: int = Field(default=2000, ge=1, le=200000)


class DataSourceMetaResponse(BaseModel):
    source: str
    market: str
    symbol: str
    interval: str
    last_success_ts: datetime | None = None
    last_error: str | None = None
    updated_at: datetime | None = None


class IngestionLogResponse(BaseModel):
    id: int
    source: str
    market: str
    symbol: str | None = None
    interval: str
    start_ts: datetime | None = None
    end_ts: datetime | None = None
    status: str
    message: str | None = None
    created_at: datetime | None = None


class DataHealthResponse(BaseModel):
    symbol: str
    market: str
    interval: Literal["1m", "1d"]
    total_bars: int
    first_bar_ts: datetime | None = None
    last_bar_ts: datetime | None = None
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    gap_estimate: int
    last_ingest: DataSourceMetaResponse | None = None


class IngestionRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=1)
    market: str = "CN"
    interval: Literal["1m", "1d"] = "1m"
    start: datetime | None = None
    end: datetime | None = None
    provider: str | None = None


class IngestionResult(BaseModel):
    symbol: str
    market: str
    interval: str
    ingested: int
    status: str
    message: str | None = None


class IngestionBatchResponse(BaseModel):
    results: list[IngestionResult]
