"""Backtest and trade database models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Backtest(Base):
    """Backtest model for storing backtest configurations and results."""

    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    strategy_version_id = Column(Integer, ForeignKey("strategy_versions.id"), nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    symbols = Column(JSON, nullable=False)  # List of symbols tested
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_value = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    trade_count = Column(Integer, default=0)
    parameters = Column(JSON, nullable=True)  # Backtest configuration
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    results = Column(JSON, nullable=True)  # Detailed results
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    portfolio = relationship("Portfolio", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")


class Trade(Base):
    """Trade model for storing trade records from backtests and live trading."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    pnl = Column(Float, default=0.0)
    is_simulated = Column(Boolean, default=True)

    # Relationships
    backtest = relationship("Backtest", back_populates="trades")
