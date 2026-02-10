"""Market data persistence models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Instrument(Base):
    """Tradable instrument metadata."""

    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), nullable=False, index=True)
    market = Column(String(16), nullable=False, index=True)  # CN / US / ...
    name = Column(String(128))
    exchange = Column(String(32))
    currency = Column(String(8))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    bars_1m = relationship("Bar1m", back_populates="instrument", cascade="all, delete-orphan")
    bars_1d = relationship("Bar1d", back_populates="instrument", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("symbol", "market", name="uq_instrument_symbol_market"),
    )


class Bar1m(Base):
    """One-minute bar data stored locally."""

    __tablename__ = "bars_1m"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger)
    source = Column(String(32), nullable=False, default="local")
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    instrument = relationship("Instrument", back_populates="bars_1m")

    __table_args__ = (
        UniqueConstraint("instrument_id", "ts", "source", name="uq_bar1m_instrument_ts_source"),
        Index("ix_bar1m_instrument_ts", "instrument_id", "ts"),
    )


class Bar1d(Base):
    """One-day bar data stored locally."""

    __tablename__ = "bars_1d"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger)
    source = Column(String(32), nullable=False, default="local")
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    instrument = relationship("Instrument", back_populates="bars_1d")

    __table_args__ = (
        UniqueConstraint("instrument_id", "ts", "source", name="uq_bar1d_instrument_ts_source"),
        Index("ix_bar1d_instrument_ts", "instrument_id", "ts"),
    )


class IngestionLog(Base):
    """Track data ingestion attempts for observability and replay."""

    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(32), nullable=False)
    market = Column(String(16), nullable=False)
    symbol = Column(String(32))
    interval = Column(String(8), nullable=False)
    start_ts = Column(DateTime)
    end_ts = Column(DateTime)
    status = Column(String(16), default="pending", nullable=False)
    message = Column(String(512))
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class DataSourceMeta(Base):
    """Track latest ingestion checkpoint per source/market/symbol."""

    __tablename__ = "data_source_meta"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(32), nullable=False)
    market = Column(String(16), nullable=False)
    symbol = Column(String(32), nullable=False)
    interval = Column(String(8), nullable=False)
    last_success_ts = Column(DateTime)
    last_error = Column(String(512))
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "market", "symbol", "interval", name="uq_source_symbol_interval"),
    )
