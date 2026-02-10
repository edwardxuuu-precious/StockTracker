"""Portfolio, holding, and portfolio-trade database models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Portfolio(Base):
    """Portfolio model for storing stock portfolios."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    initial_capital = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("PortfolioTrade", back_populates="portfolio", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="portfolio")


class Holding(Base):
    """Holding model for individual stock positions in a portfolio."""

    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")


class PortfolioTrade(Base):
    """Trade record for live portfolio buy/sell operations."""

    __tablename__ = "portfolio_trades"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    amount = Column(Float, nullable=False)  # quantity * price
    realized_pnl = Column(Float, default=0.0)
    trade_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
