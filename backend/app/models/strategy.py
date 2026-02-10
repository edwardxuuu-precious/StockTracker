"""Strategy database models."""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Strategy(Base):
    """Strategy model for storing trading strategies."""

    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String(50), nullable=False)  # 'moving_average', 'rsi', 'custom', etc.
    parameters = Column(JSON, nullable=True)  # Strategy-specific parameters
    code = Column(Text, nullable=True)  # Python code for custom strategies
    created_from_chat = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    backtests = relationship("Backtest", back_populates="strategy")
    versions = relationship("StrategyVersion", back_populates="strategy", cascade="all, delete-orphan")
