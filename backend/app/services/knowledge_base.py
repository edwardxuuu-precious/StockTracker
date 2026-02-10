"""Knowledge base ingestion and retrieval utilities."""
from __future__ import annotations

import json
import re
import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ..models.knowledge_base import KnowledgeChunk, KnowledgeDocument

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "data" / "kb"


@dataclass(frozen=True)
class SearchHit:
    score: float
    chunk: KnowledgeChunk
    document: KnowledgeDocument
    vector_score: float = 0.0
    fts_score: float = 0.0
    overlap_score: float = 0.0
    freshness_score: float = 0.0
    confidence: str = "low"
    reference_id: str = ""
    governance_flags: tuple[str, ...] = ()
    snippet: str = ""


@dataclass(frozen=True)
class GovernancePolicy:
    name: str
    min_score: float
    max_per_document: int
    allow_fallback: bool


_GOVERNANCE_POLICIES: dict[str, GovernancePolicy] = {
    "strict": GovernancePolicy(
        name="strict",
        min_score=0.16,
        max_per_document=1,
        allow_fallback=False,
    ),
    "balanced": GovernancePolicy(
        name="balanced",
        min_score=0.08,
        max_per_document=2,
        allow_fallback=True,
    ),
    "recall": GovernancePolicy(
        name="recall",
        min_score=0.03,
        max_per_document=4,
        allow_fallback=True,
    ),
}


def resolve_governance_policy(profile: str | None) -> GovernancePolicy:
    key = (profile or "balanced").strip().lower()
    return _GOVERNANCE_POLICIES.get(key, _GOVERNANCE_POLICIES["balanced"])


def ensure_kb_schema(engine: Engine) -> None:
    """Ensure FTS table exists for knowledge base chunks."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunks_fts "
                "USING fts5(content, chunk_id UNINDEXED)"
            )
        )


def _stable_hash_token(token: str) -> int:
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest, 16)


def _embed_text(text_value: str, dim: int = 256) -> list[float]:
    vector = np.zeros(dim, dtype=np.float32)
    tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", text_value.lower())
    for token in tokens:
        idx = _stable_hash_token(token) % dim
        vector[idx] += 1.0
    norm = float(np.linalg.norm(vector))
    if norm > 1e-8:
        vector = vector / norm
    return vector.tolist()


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return float(dot)


def _sanitize_fts_query(query: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", query or "")
    return re.sub(r"\s+", " ", normalized).strip()


def _extract_query_terms(query: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{2,}", (query or "").lower())
    seen: set[str] = set()
    deduped: list[str] = []
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        deduped.append(term)
    return deduped


def _term_overlap_score(query_terms: list[str], content: str) -> float:
    if not query_terms:
        return 0.0
    lowered = (content or "").lower()
    matched = 0
    for term in query_terms:
        if term and term in lowered:
            matched += 1
    return matched / float(len(query_terms))


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _freshness_score(
    created_at: datetime | None,
    latest_created_at: datetime | None,
    *,
    half_life_days: int = 180,
) -> float:
    created_at = _to_utc(created_at)
    latest_created_at = _to_utc(latest_created_at)
    if half_life_days <= 0:
        half_life_days = 180
    if created_at is None or latest_created_at is None:
        return 0.0
    delta_days = max((latest_created_at - created_at).total_seconds() / 86400.0, 0.0)
    # Smooth decay by age. Newer evidence gets a mild boost, not dominance.
    return 1.0 / (1.0 + delta_days / float(half_life_days))


def _normalize_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        item = (value or "").strip().lower()
        if item:
            normalized.append(item)
    return normalized


def _source_blob(document: KnowledgeDocument) -> str:
    meta_text = ""
    if document.meta is not None:
        try:
            meta_text = json.dumps(document.meta, ensure_ascii=False)
        except Exception:
            meta_text = str(document.meta)
    parts = [
        document.source_name or "",
        document.source_type or "",
        document.title or "",
        document.storage_path or "",
        meta_text,
    ]
    return " ".join(parts).lower()


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _confidence_label(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"


def _build_snippet(content: str, query_terms: list[str], max_chars: int = 240) -> str:
    text_value = re.sub(r"\s+", " ", content or "").strip()
    if not text_value:
        return ""
    if len(text_value) <= max_chars:
        return text_value
    lowered = text_value.lower()
    anchor = -1
    for term in query_terms:
        pos = lowered.find(term)
        if pos >= 0:
            anchor = pos
            break
    if anchor < 0:
        return text_value[:max_chars].strip()
    half = max_chars // 2
    start = max(anchor - half, 0)
    end = min(start + max_chars, len(text_value))
    if end - start < max_chars:
        start = max(end - max_chars, 0)
    return text_value[start:end].strip()


def _govern_hits(
    ranked_hits: list[SearchHit],
    top_k: int,
    *,
    min_score: float = 0.08,
    max_per_document: int = 2,
    allow_fallback: bool = True,
) -> list[SearchHit]:
    selected: list[SearchHit] = []
    deferred: list[SearchHit] = []
    per_doc: dict[int, int] = {}

    for hit in ranked_hits:
        flags: list[str] = []
        if hit.score < min_score:
            flags.append("low_score")
        if per_doc.get(hit.document.id, 0) >= max_per_document:
            flags.append("duplicate_document")
        if hit.overlap_score < 0.05:
            flags.append("weak_term_overlap")

        governed = replace(
            hit,
            governance_flags=tuple(flags),
            confidence=_confidence_label(hit.score),
        )
        hard_blocked = "low_score" in flags or "duplicate_document" in flags
        if hard_blocked:
            deferred.append(governed)
            continue

        selected.append(governed)
        per_doc[hit.document.id] = per_doc.get(hit.document.id, 0) + 1
        if len(selected) >= top_k:
            return selected

    if not allow_fallback:
        return selected

    # Fallback when strict governance would return too few citations.
    for item in deferred:
        if len(selected) >= top_k:
            break
        flags = list(item.governance_flags)
        if "fallback_selected" not in flags:
            flags.append("fallback_selected")
        selected.append(
            replace(
                item,
                governance_flags=tuple(flags),
                confidence=_confidence_label(max(item.score, 0.01)),
            )
        )
    return selected


def _chunk_text(text_value: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    if not text_value:
        return []
    chunks: list[str] = []
    cursor = 0
    length = len(text_value)
    while cursor < length:
        end = min(cursor + chunk_size, length)
        chunk = text_value[cursor:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        cursor = max(0, end - overlap)
    return chunks


def _load_text_from_file(path: Path, source_type: str) -> str:
    source_type = source_type.lower()
    if source_type == "pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"pypdf import failed: {exc}") from exc
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()
    if source_type == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False, indent=2)
    return path.read_text(encoding="utf-8")


def ingest_document(
    db: Session,
    *,
    source_name: str,
    source_type: str,
    content: str,
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
    storage_path: str | None = None,
    embedding_dim: int = 256,
) -> tuple[KnowledgeDocument, int]:
    if not content or not content.strip():
        raise ValueError("Empty content; cannot ingest.")
    document = KnowledgeDocument(
        source_name=source_name,
        source_type=source_type,
        title=title,
        storage_path=storage_path,
        meta=metadata or {},
    )
    db.add(document)
    db.flush()

    chunks = _chunk_text(content)
    if not chunks:
        raise ValueError("No chunks generated from content.")
    chunk_count = 0
    for index, chunk in enumerate(chunks):
        embedding = _embed_text(chunk, dim=embedding_dim)
        item = KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk,
            token_count=len(chunk.split()),
            embedding=embedding,
            embedding_dim=embedding_dim,
        )
        db.add(item)
        db.flush()
        db.execute(
            text("INSERT INTO kb_chunks_fts(rowid, content, chunk_id) VALUES (:rowid, :content, :chunk_id)"),
            {"rowid": item.id, "content": chunk, "chunk_id": item.id},
        )
        chunk_count += 1

    db.commit()
    db.refresh(document)
    return document, chunk_count


def ingest_file(
    db: Session,
    *,
    file_path: Path,
    source_type: str,
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
    embedding_dim: int = 256,
) -> tuple[KnowledgeDocument, int]:
    content = _load_text_from_file(file_path, source_type)
    return ingest_document(
        db,
        source_name=file_path.name,
        source_type=source_type,
        content=content,
        title=title,
        metadata=metadata,
        storage_path=str(file_path),
        embedding_dim=embedding_dim,
    )


def search_knowledge_base(
    db: Session,
    query: str,
    top_k: int = 5,
    mode: str = "hybrid",
    *,
    min_score: float = 0.08,
    max_per_document: int = 2,
    allow_fallback: bool = True,
    allowed_source_types: list[str] | None = None,
    blocked_source_keywords: list[str] | None = None,
    preferred_source_types: list[str] | None = None,
    recency_half_life_days: int = 180,
) -> list[SearchHit]:
    sanitized = _sanitize_fts_query(query)
    query_terms = _extract_query_terms(query)
    allowed_types = set(_normalize_list(allowed_source_types))
    blocked_keywords = _normalize_list(blocked_source_keywords)
    preferred_types = set(_normalize_list(preferred_source_types))
    fts_candidates: dict[int, float] = {}

    if mode in {"fts", "hybrid"} and sanitized:
        rows = db.execute(
            text(
                "SELECT chunk_id, bm25(kb_chunks_fts) AS score "
                "FROM kb_chunks_fts WHERE kb_chunks_fts MATCH :q "
                "ORDER BY score LIMIT :limit"
            ),
            {"q": sanitized, "limit": max(top_k * 5, 25)},
        ).fetchall()
        for chunk_id, score in rows:
            fts_score = _clamp01(1.0 / (1.0 + float(score)))
            fts_candidates[int(chunk_id)] = max(fts_score, 0.0)

    candidate_ids = set(fts_candidates.keys())
    if mode in {"vector", "hybrid"}:
        rows = (
            db.query(KnowledgeChunk.id)
            .order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.id.desc())
            .limit(max(top_k * 40, 200))
            .all()
        )
        candidate_ids.update({int(row[0]) for row in rows})

    if not candidate_ids:
        return []

    query_embedding = _embed_text(query)
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(candidate_ids)).all()
    docs_map = {
        doc.id: doc
        for doc in db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.id.in_({chunk.document_id for chunk in chunks}))
        .all()
    }
    latest_doc_ts = None
    if docs_map:
        latest_doc_ts = max((_to_utc(doc.created_at) for doc in docs_map.values() if doc.created_at), default=None)

    hits: list[SearchHit] = []
    for chunk in chunks:
        document = docs_map[chunk.document_id]
        source_type = (document.source_type or "").strip().lower()
        if allowed_types and source_type not in allowed_types:
            continue
        if blocked_keywords:
            source_text = _source_blob(document)
            if any(keyword in source_text for keyword in blocked_keywords):
                continue

        vector_score = _clamp01(_cosine(query_embedding, chunk.embedding or []))
        fts_score = fts_candidates.get(chunk.id, 0.0)
        overlap_score = _clamp01(_term_overlap_score(query_terms, chunk.content or ""))
        freshness = _clamp01(
            _freshness_score(
                document.created_at,
                latest_doc_ts,
                half_life_days=recency_half_life_days,
            )
        )
        source_boost = 1.0 if source_type in preferred_types else 0.0
        if mode == "fts":
            final_score = 0.73 * fts_score + 0.25 * overlap_score + 0.02 * source_boost
        elif mode == "vector":
            final_score = 0.78 * vector_score + 0.2 * overlap_score + 0.02 * source_boost
        else:
            final_score = (
                0.49 * vector_score
                + 0.3 * fts_score
                + 0.15 * overlap_score
                + 0.05 * freshness
                + 0.01 * source_boost
            )
        hits.append(
            SearchHit(
                score=_clamp01(final_score),
                chunk=chunk,
                document=document,
                vector_score=vector_score,
                fts_score=fts_score,
                overlap_score=overlap_score,
                freshness_score=freshness,
                confidence=_confidence_label(final_score),
                reference_id=f"doc:{chunk.document_id}:chunk:{chunk.id}",
                governance_flags=(),
                snippet=_build_snippet(chunk.content or "", query_terms),
            )
        )

    hits.sort(key=lambda item: item.score, reverse=True)
    governed = _govern_hits(
        hits,
        top_k=top_k,
        min_score=min_score,
        max_per_document=max_per_document,
        allow_fallback=allow_fallback,
    )
    return governed[:top_k]
