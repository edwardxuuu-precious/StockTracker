"""Knowledge base persistence models."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeDocument(Base):
    """Source document stored in the knowledge base."""

    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(256), nullable=False)
    source_type = Column(String(32), nullable=False)
    title = Column(String(256))
    storage_path = Column(String(512))
    meta = Column("metadata", JSON)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    """Chunked text from a knowledge document."""

    __tablename__ = "kb_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding = Column(JSON)
    embedding_dim = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")
