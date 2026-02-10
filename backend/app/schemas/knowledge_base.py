"""Pydantic schemas for knowledge base operations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocumentResponse(BaseModel):
    id: int
    source_name: str
    source_type: str
    title: str | None = None
    storage_path: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, alias="meta")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class KnowledgeChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeIngestResponse(BaseModel):
    document: KnowledgeDocumentResponse
    chunk_count: int


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    mode: Literal["fts", "vector", "hybrid"] = "hybrid"
    policy_profile: Literal["strict", "balanced", "recall"] | None = None
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    max_per_document: int | None = Field(default=None, ge=1, le=20)
    allow_fallback: bool | None = None
    allowed_source_types: list[str] | None = None
    blocked_source_keywords: list[str] | None = None


class KnowledgeSearchHit(BaseModel):
    score: float
    chunk: KnowledgeChunkResponse
    document: KnowledgeDocumentResponse
    vector_score: float | None = None
    fts_score: float | None = None
    overlap_score: float | None = None
    freshness_score: float | None = None
    confidence: str | None = None
    reference_id: str | None = None
    governance_flags: list[str] = Field(default_factory=list)
    snippet: str | None = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    hits: list[KnowledgeSearchHit]
