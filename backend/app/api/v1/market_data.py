"""Local market data API endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.market_data import Bar1d, Bar1m, DataSourceMeta, IngestionLog, Instrument
from ...schemas.market_data import (
    BarResponse,
    DataHealthResponse,
    DataSourceMetaResponse,
    IngestionBatchResponse,
    IngestionRequest,
    IngestionLogResponse,
    InstrumentResponse,
)
from ...services.market_data_providers import AkshareMarketDataProvider, UsYFinanceMarketDataProvider
from ...services.market_data_service import MarketDataService

router = APIRouter()
market_data_service = MarketDataService(
    providers=[AkshareMarketDataProvider(), UsYFinanceMarketDataProvider()],
)


def _get_instrument(db: Session, symbol: str, market: str) -> Instrument:
    instrument = (
        db.query(Instrument)
        .filter(Instrument.symbol == symbol.upper(), Instrument.market == market.upper())
        .first()
    )
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found in local store")
    return instrument


def _get_bar_model(interval: str):
    return Bar1m if interval == "1m" else Bar1d


def _estimate_gap(total_bars: int, start: datetime | None, end: datetime | None, interval: str) -> int:
    if not start or not end:
        return 0
    if end < start:
        return 0
    seconds = 60 if interval == "1m" else 86400
    expected = int((end - start).total_seconds() // seconds) + 1
    if expected <= 0:
        return 0
    return max(expected - total_bars, 0)


@router.get("/instruments", response_model=list[InstrumentResponse])
async def list_instruments(
    market: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    query = db.query(Instrument)
    if market:
        query = query.filter(Instrument.market == market.upper())
    return query.order_by(Instrument.symbol.asc()).limit(limit).all()


@router.get("/bars", response_model=list[BarResponse])
async def get_bars(
    symbol: str = Query(..., description="Ticker symbol, e.g. 600519 or AAPL"),
    market: str = Query("CN", description="Market code, e.g. CN/US"),
    interval: Literal["1m", "1d"] = Query("1m"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=2000, ge=1, le=200000),
    db: Session = Depends(get_db),
):
    instrument = _get_instrument(db, symbol, market)
    model = _get_bar_model(interval)

    query = db.query(model).filter(model.instrument_id == instrument.id)
    if start:
        query = query.filter(model.ts >= start)
    if end:
        query = query.filter(model.ts <= end)

    rows = (
        query.order_by(model.ts.asc())
        .limit(limit)
        .all()
    )

    return [
        BarResponse(
            symbol=instrument.symbol,
            market=instrument.market,
            interval=interval,
            ts=row.ts,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=int(row.volume) if row.volume is not None else None,
            source=row.source,
        )
        for row in rows
    ]


@router.get("/status", response_model=DataHealthResponse)
async def get_data_status(
    symbol: str = Query(..., description="Ticker symbol, e.g. 600519 or AAPL"),
    market: str = Query("CN", description="Market code, e.g. CN/US"),
    interval: Literal["1m", "1d"] = Query("1m"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    instrument = _get_instrument(db, symbol, market)
    model = _get_bar_model(interval)

    query = db.query(
        func.count(model.id),
        func.min(model.ts),
        func.max(model.ts),
    ).filter(model.instrument_id == instrument.id)

    if start:
        query = query.filter(model.ts >= start)
    if end:
        query = query.filter(model.ts <= end)

    total_bars, first_ts, last_ts = query.one()
    total_bars = int(total_bars or 0)

    meta = (
        db.query(DataSourceMeta)
        .filter(
            DataSourceMeta.market == instrument.market,
            DataSourceMeta.symbol == instrument.symbol,
            DataSourceMeta.interval == interval,
        )
        .order_by(DataSourceMeta.updated_at.desc())
        .first()
    )

    gap_estimate = _estimate_gap(total_bars, start or first_ts, end or last_ts, interval)

    return DataHealthResponse(
        symbol=instrument.symbol,
        market=instrument.market,
        interval=interval,
        total_bars=total_bars,
        first_bar_ts=first_ts,
        last_bar_ts=last_ts,
        requested_start=start or first_ts,
        requested_end=end or last_ts,
        gap_estimate=gap_estimate,
        last_ingest=(
            DataSourceMetaResponse(
                source=meta.source,
                market=meta.market,
                symbol=meta.symbol,
                interval=meta.interval,
                last_success_ts=meta.last_success_ts,
                last_error=meta.last_error,
                updated_at=meta.updated_at,
            )
            if meta
            else None
        ),
    )


@router.get("/ingestions", response_model=list[IngestionLogResponse])
async def list_ingestions(
    market: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    interval: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(IngestionLog)
    if market:
        query = query.filter(IngestionLog.market == market.upper())
    if symbol:
        query = query.filter(IngestionLog.symbol == symbol.upper())
    if interval:
        query = query.filter(IngestionLog.interval == interval.lower())

    rows = (
        query.order_by(IngestionLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        IngestionLogResponse(
            id=row.id,
            source=row.source,
            market=row.market,
            symbol=row.symbol,
            interval=row.interval,
            start_ts=row.start_ts,
            end_ts=row.end_ts,
            status=row.status,
            message=row.message,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/ingest", response_model=IngestionBatchResponse)
async def ingest_market_data(payload: IngestionRequest, db: Session = Depends(get_db)):
    results = []
    for symbol in payload.symbols:
        try:
            ingested = market_data_service.ingest_history(
                db=db,
                symbol=symbol,
                market=payload.market,
                interval=payload.interval,
                start=payload.start,
                end=payload.end,
                provider_name=payload.provider,
            )
            results.append(
                {
                    "symbol": symbol.upper(),
                    "market": payload.market.upper(),
                    "interval": payload.interval,
                    "ingested": ingested,
                    "status": "completed",
                    "message": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "symbol": symbol.upper(),
                    "market": payload.market.upper(),
                    "interval": payload.interval,
                    "ingested": 0,
                    "status": "failed",
                    "message": str(exc),
                }
            )
    return {"results": results}
