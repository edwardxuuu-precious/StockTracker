"""Knowledge base API endpoints."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...models.knowledge_base import KnowledgeDocument
from ...schemas.knowledge_base import (
    KnowledgeDocumentResponse,
    KnowledgeIngestResponse,
    KnowledgeSearchHit,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from ...services.knowledge_base import (
    STORAGE_DIR,
    ensure_kb_schema,
    ingest_document,
    ingest_file,
    resolve_governance_policy,
    search_knowledge_base,
)

router = APIRouter()


def _infer_source_type(filename: str, explicit: str | None) -> str:
    if explicit:
        return explicit.lower()
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix in {"pdf", "txt", "json"}:
        return suffix
    raise HTTPException(status_code=400, detail="Unsupported file type; use pdf/txt/json")


@router.post("/ingest", response_model=KnowledgeIngestResponse)
async def ingest_kb_file(
    file: UploadFile = File(...),
    source_type: str | None = Form(default=None),
    title: str | None = Form(default=None),
    metadata: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    source_type = _infer_source_type(file.filename or "upload", source_type)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload").name
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    storage_path = STORAGE_DIR / f"{ts}_{safe_name}"
    content = await file.read()
    storage_path.write_bytes(content)
    ensure_kb_schema(db.get_bind())

    meta: dict | None = None
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {exc}") from exc

    try:
        document, chunk_count = ingest_file(
            db,
            file_path=storage_path,
            source_type=source_type,
            title=title,
            metadata=meta,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeIngestResponse(
        document=KnowledgeDocumentResponse.model_validate(document),
        chunk_count=chunk_count,
    )


@router.post("/ingest-text", response_model=KnowledgeIngestResponse)
async def ingest_kb_text(
    source_name: str = Form(...),
    source_type: str = Form("txt"),
    content: str = Form(...),
    title: str | None = Form(default=None),
    metadata: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    meta: dict | None = None
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {exc}") from exc

    ensure_kb_schema(db.get_bind())

    try:
        document, chunk_count = ingest_document(
            db,
            source_name=source_name,
            source_type=source_type,
            content=content,
            title=title,
            metadata=meta,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeIngestResponse(
        document=KnowledgeDocumentResponse.model_validate(document),
        chunk_count=chunk_count,
    )


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_kb(payload: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    ensure_kb_schema(db.get_bind())
    settings = get_settings()
    policy = resolve_governance_policy(payload.policy_profile or settings.KB_POLICY_PROFILE)
    print(f"[DEBUG] KB search: query={payload.query!r}, mode={payload.mode}, top_k={payload.top_k}, policy={policy.name}, min_score={policy.min_score}")
    hits = search_knowledge_base(
        db,
        payload.query,
        payload.top_k,
        payload.mode,
        min_score=payload.min_score if payload.min_score is not None else policy.min_score,
        max_per_document=(
            payload.max_per_document
            if payload.max_per_document is not None
            else policy.max_per_document
        ),
        allow_fallback=(
            payload.allow_fallback
            if payload.allow_fallback is not None
            else policy.allow_fallback
        ),
        allowed_source_types=(
            payload.allowed_source_types
            if payload.allowed_source_types is not None
            else settings.KB_ALLOWED_SOURCE_TYPES
        ),
        blocked_source_keywords=(
            payload.blocked_source_keywords
            if payload.blocked_source_keywords is not None
            else settings.KB_BLOCKED_SOURCE_KEYWORDS
        ),
        preferred_source_types=settings.KB_PREFERRED_SOURCE_TYPES,
        recency_half_life_days=settings.KB_RECENCY_HALF_LIFE_DAYS,
    )
    print(f"[DEBUG] KB search returned {len(hits)} hits")
    return KnowledgeSearchResponse(
        query=payload.query,
        hits=[
            KnowledgeSearchHit(
                score=hit.score,
                chunk=hit.chunk,
                document=hit.document,
                vector_score=hit.vector_score,
                fts_score=hit.fts_score,
                overlap_score=hit.overlap_score,
                freshness_score=hit.freshness_score,
                confidence=hit.confidence,
                reference_id=hit.reference_id,
                governance_flags=list(hit.governance_flags),
                snippet=hit.snippet,
            )
            for hit in hits
        ],
    )


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_documents(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    return db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).limit(limit).all()
