"""Strategy version snapshot model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class StrategyVersion(Base):
    """Immutable strategy snapshot for version tracking."""

    __tablename__ = "strategy_versions"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=True)
    code = Column(Text, nullable=True)
    note = Column(String(255), nullable=True)
    created_by = Column(String(50), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    strategy = relationship("Strategy", back_populates="versions")
