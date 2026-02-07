"""Pydantic schemas for quote API responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QuoteResponse(BaseModel):
    """Normalized quote payload returned by quote endpoints."""

    symbol: str
    name: Optional[str] = None
    price: float
    change: float
    change_pct: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    source: str
    fetched_at: datetime
    cache_hit: bool = False


class QuoteStatsResponse(BaseModel):
    """In-memory quote cache metrics for observability."""

    cache_hits: int
    cache_misses: int
    cache_expired: int
    total_requests: int
    hit_rate: float
    cache_size: int
    ttl_seconds: int
