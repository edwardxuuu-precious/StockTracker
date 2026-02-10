"""Stock data cache and price alert models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class StockCache(Base):
    """Stock data cache model for reducing API calls."""

    __tablename__ = "stock_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)  # 'quote', 'history', 'info'
    data = Column(JSON, nullable=False)
    source = Column(String(20), nullable=False)  # 'yfinance', 'akshare', 'tushare'
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


class PriceAlert(Base):
    """Price alert model for notifying users of price changes."""

    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    condition = Column(String(20), nullable=False)  # 'above', 'below', 'change_pct'
    target_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
