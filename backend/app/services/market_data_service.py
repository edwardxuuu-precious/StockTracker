"""Market data ingestion service with pluggable providers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Protocol

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..models.market_data import Bar1d, Bar1m, DataSourceMeta, IngestionLog, Instrument


@dataclass(frozen=True)
class BarRecord:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int | None
    source: str


class MarketDataProvider(Protocol):
    name: str

    def supports(self, market: str, interval: str) -> bool: ...

    def fetch_history(
        self,
        symbol: str,
        start: datetime | None,
        end: datetime | None,
        interval: str,
    ) -> list[BarRecord]: ...


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def _normalize_market(market: str) -> str:
    return str(market or "").strip().upper()


def get_or_create_instrument(
    db: Session,
    symbol: str,
    market: str,
) -> Instrument:
    symbol = _normalize_symbol(symbol)
    market = _normalize_market(market)
    instrument = (
        db.query(Instrument)
        .filter(Instrument.symbol == symbol, Instrument.market == market)
        .first()
    )
    if instrument:
        return instrument

    instrument = Instrument(symbol=symbol, market=market)
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


def _upsert_bars(
    db: Session,
    model,
    instrument_id: int,
    bars: Iterable[BarRecord],
) -> int:
    payload = []
    for item in bars:
        payload.append(
            {
                "instrument_id": instrument_id,
                "ts": item.ts,
                "open": float(item.open),
                "high": float(item.high),
                "low": float(item.low),
                "close": float(item.close),
                "volume": int(item.volume) if item.volume is not None else None,
                "source": item.source,
                "created_at": _utcnow(),
            }
        )

    if not payload:
        return 0

    # SQLite has a default limit of 999 variables per statement
    # Each bar record has 9 fields, so batch size is limited to ~100 bars
    BATCH_SIZE = 100
    total_affected = 0

    for batch_start in range(0, len(payload), BATCH_SIZE):
        batch = payload[batch_start : batch_start + BATCH_SIZE]

        stmt = sqlite_insert(model).values(batch)
        update_cols = {
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["instrument_id", "ts", "source"],
            set_=update_cols,
        )
        result = db.execute(stmt)
        total_affected += result.rowcount or len(batch)

    return total_affected


def _record_ingestion_meta(
    db: Session,
    source: str,
    market: str,
    symbol: str,
    interval: str,
    last_success_ts: datetime | None,
    error: str | None,
) -> None:
    meta = (
        db.query(DataSourceMeta)
        .filter(
            DataSourceMeta.source == source,
            DataSourceMeta.market == market,
            DataSourceMeta.symbol == symbol,
            DataSourceMeta.interval == interval,
        )
        .first()
    )
    if not meta:
        meta = DataSourceMeta(
            source=source,
            market=market,
            symbol=symbol,
            interval=interval,
        )
        db.add(meta)

    if last_success_ts is not None:
        meta.last_success_ts = last_success_ts
    meta.last_error = error


class MarketDataService:
    def __init__(self, providers: list[MarketDataProvider]) -> None:
        self.providers = providers

    def _pick_provider(self, market: str, interval: str, provider_name: str | None) -> MarketDataProvider:
        market = _normalize_market(market)
        if provider_name:
            for provider in self.providers:
                if provider.name == provider_name and provider.supports(market, interval):
                    return provider
            raise ValueError(f"Provider {provider_name} not available for {market} {interval}")

        for provider in self.providers:
            if provider.supports(market, interval):
                return provider
        raise ValueError(f"No provider available for {market} {interval}")

    def ingest_history(
        self,
        db: Session,
        symbol: str,
        market: str,
        interval: str,
        start: datetime | None,
        end: datetime | None,
        provider_name: str | None = None,
    ) -> int:
        symbol = _normalize_symbol(symbol)
        market = _normalize_market(market)
        interval = str(interval or "").strip().lower()

        provider = self._pick_provider(market, interval, provider_name)
        instrument = get_or_create_instrument(db, symbol, market)

        meta = (
            db.query(DataSourceMeta)
            .filter(
                DataSourceMeta.source == provider.name,
                DataSourceMeta.market == market,
                DataSourceMeta.symbol == symbol,
                DataSourceMeta.interval == interval,
            )
            .first()
        )

        effective_start = start or (meta.last_success_ts if meta else None)
        effective_end = end or _utcnow()

        log = IngestionLog(
            source=provider.name,
            market=market,
            symbol=symbol,
            interval=interval,
            start_ts=effective_start,
            end_ts=effective_end,
            status="running",
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        try:
            bars = provider.fetch_history(symbol, effective_start, effective_end, interval)
            if interval == "1m":
                affected = _upsert_bars(db, Bar1m, instrument.id, bars)
            else:
                affected = _upsert_bars(db, Bar1d, instrument.id, bars)
            log.status = "completed"
            log.message = f"ingested {affected} bars"
            last_ts = bars[-1].ts if bars else (meta.last_success_ts if meta else None)
            _record_ingestion_meta(db, provider.name, market, symbol, interval, last_ts, None)
            db.commit()
            return affected
        except Exception as exc:
            log.status = "failed"
            log.message = str(exc)
            _record_ingestion_meta(db, provider.name, market, symbol, interval, None, str(exc))
            db.commit()
            raise
