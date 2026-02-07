"""Quote API endpoints."""
from fastapi import APIRouter, HTTPException, Query

from ...config import get_settings
from ...schemas.quote import QuoteResponse, QuoteStatsResponse
from ...services.quote_service import QuoteFetchError, QuoteService

router = APIRouter()

settings = get_settings()
quote_service = QuoteService(cache_ttl_seconds=settings.CACHE_QUOTE_TTL)


@router.get("/batch", response_model=list[QuoteResponse])
async def get_batch_quotes(
    symbols: str = Query(..., description="Comma-separated symbols, e.g. AAPL,MSFT,600519"),
    refresh: bool = Query(False, description="Bypass cache and fetch latest quotes"),
):
    parsed_symbols = [item.strip() for item in symbols.split(",") if item.strip()]
    if not parsed_symbols:
        raise HTTPException(status_code=400, detail="At least one symbol is required")
    try:
        return quote_service.get_batch_quotes(parsed_symbols, refresh=refresh)
    except QuoteFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/stats", response_model=QuoteStatsResponse)
async def get_quote_stats():
    return quote_service.get_stats()


@router.get("/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    refresh: bool = Query(False, description="Bypass cache and fetch latest quote"),
):
    try:
        return quote_service.get_quote(symbol, refresh=refresh)
    except QuoteFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
