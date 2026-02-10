"""Evaluate knowledge-base retrieval quality against a reproducible corpus.

Usage:
  python backend/scripts/kb_benchmark.py --cases backend/config/kb_benchmark_cases.sample.json
  python backend/scripts/kb_benchmark.py --cases backend/config/kb_benchmark_cases.prod.json --reset-db
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.database import Base  # noqa: E402
import app.models.knowledge_base  # noqa: F401, E402
from app.models.knowledge_base import KnowledgeDocument  # noqa: E402
from app.services.knowledge_base import (  # noqa: E402
    ensure_kb_schema,
    ingest_document,
    ingest_file,
    resolve_governance_policy,
    search_knowledge_base,
)

DEFAULT_BENCHMARK_DB = PROJECT_ROOT / ".runtime" / "kb_benchmark.sqlite3"
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "backend" / "config" / "kb_benchmark_corpus"
CORPUS_MANIFEST_FILE = "corpus_pack.json"


def _lower_text_for_hit(hit) -> str:
    parts = [
        hit.document.source_name or "",
        hit.document.title or "",
        hit.document.source_type or "",
        hit.snippet or "",
    ]
    return " ".join(parts).lower()


def _seed_manifest_documents_if_needed(db, manifest_path: Path) -> int:
    if not manifest_path.exists():
        return 0
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Corpus manifest must be a JSON array.")

    inserted = 0
    for item in payload:
        if not isinstance(item, dict):
            continue
        source_name = str(item.get("source_name") or "").strip()
        source_type = str(item.get("source_type") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        title = str(item.get("title") or "").strip() or None
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        if not source_name or source_type not in {"pdf", "txt", "json"} or not content:
            continue
        exists = (
            db.query(KnowledgeDocument.id)
            .filter(KnowledgeDocument.source_name == source_name)
            .first()
        )
        if exists:
            continue
        ingest_document(
            db,
            source_name=source_name,
            source_type=source_type,
            content=content,
            title=title,
            metadata=metadata,
        )
        inserted += 1
    return inserted


def _seed_file_documents_if_needed(db, corpus_dir: Path) -> int:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [
            *corpus_dir.glob("*.txt"),
            *corpus_dir.glob("*.json"),
            *corpus_dir.glob("*.pdf"),
        ]
    )
    inserted = 0
    for path in files:
        if path.name == CORPUS_MANIFEST_FILE:
            continue
        suffix = path.suffix.lower()
        source_type = "txt"
        if suffix == ".json":
            source_type = "json"
        elif suffix == ".pdf":
            source_type = "pdf"
        source_name = f"benchmark::{path.name}"
        exists = (
            db.query(KnowledgeDocument.id)
            .filter(KnowledgeDocument.source_name == source_name)
            .first()
        )
        if exists:
            continue
        document, _ = ingest_file(
            db,
            file_path=path,
            source_type=source_type,
            title=path.stem.replace("_", " "),
            metadata={"benchmark_corpus": True, "path": str(path), "source_name": source_name},
        )
        document.source_name = source_name
        db.add(document)
        db.commit()
        inserted += 1
    return inserted


def _seed_corpus_if_needed(db, corpus_dir: Path) -> int:
    manifest_inserted = _seed_manifest_documents_if_needed(db, corpus_dir / CORPUS_MANIFEST_FILE)
    file_inserted = _seed_file_documents_if_needed(db, corpus_dir)
    return manifest_inserted + file_inserted


def _evaluate_case(db, case: dict[str, Any], settings) -> dict[str, Any]:
    query = str(case.get("query") or "").strip()
    if not query:
        raise ValueError("Each case must include a non-empty 'query'.")

    expected_keywords = [str(item).strip().lower() for item in case.get("expected_keywords", []) if str(item).strip()]
    top_k = int(case.get("top_k", 5))
    mode = str(case.get("mode", "hybrid")).strip().lower()
    policy_profile = str(case.get("policy_profile") or settings.KB_POLICY_PROFILE).strip().lower()
    policy = resolve_governance_policy(policy_profile)

    hits = search_knowledge_base(
        db,
        query=query,
        top_k=top_k,
        mode=mode,
        min_score=policy.min_score,
        max_per_document=policy.max_per_document,
        allow_fallback=policy.allow_fallback,
        allowed_source_types=settings.KB_ALLOWED_SOURCE_TYPES,
        blocked_source_keywords=settings.KB_BLOCKED_SOURCE_KEYWORDS,
        preferred_source_types=settings.KB_PREFERRED_SOURCE_TYPES,
        recency_half_life_days=settings.KB_RECENCY_HALF_LIFE_DAYS,
    )
    if not hits:
        return {
            "query": query,
            "policy_profile": policy.name,
            "top_k": top_k,
            "hits": 0,
            "matched_hits": 0,
            "matched_keywords": [],
            "precision_at_k": 0.0,
            "keyword_recall": 0.0,
        }

    matched_hits = 0
    matched_keywords: set[str] = set()
    for hit in hits:
        text_blob = _lower_text_for_hit(hit)
        matched_now = False
        for keyword in expected_keywords:
            if keyword and keyword in text_blob:
                matched_now = True
                matched_keywords.add(keyword)
        if matched_now:
            matched_hits += 1

    precision = matched_hits / float(len(hits)) if hits else 0.0
    recall = (
        len(matched_keywords) / float(len(expected_keywords))
        if expected_keywords
        else (1.0 if hits else 0.0)
    )
    return {
        "query": query,
        "policy_profile": policy.name,
        "top_k": top_k,
        "hits": len(hits),
        "matched_hits": matched_hits,
        "matched_keywords": sorted(matched_keywords),
        "precision_at_k": round(precision, 4),
        "keyword_recall": round(recall, 4),
    }


def _build_db_session(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
    ensure_kb_schema(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session_factory


def run_benchmark(
    *,
    cases_path: Path,
    min_precision: float | None = None,
    min_recall: float | None = None,
    database_url: str,
    corpus_dir: Path,
    reset_db: bool = False,
) -> int:
    if reset_db and database_url.startswith("sqlite:///"):
        sqlite_path = Path(database_url.removeprefix("sqlite:///"))
        if sqlite_path.exists():
            sqlite_path.unlink()
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark cases file must be a non-empty JSON array.")

    settings = get_settings()
    engine, session_factory = _build_db_session(database_url)
    db = session_factory()
    try:
        inserted = _seed_corpus_if_needed(db, corpus_dir=corpus_dir)
        results = [_evaluate_case(db, case, settings) for case in cases]
    finally:
        db.close()
        engine.dispose()

    avg_precision = sum(item["precision_at_k"] for item in results) / len(results)
    avg_recall = sum(item["keyword_recall"] for item in results) / len(results)
    summary = {
        "cases_file": str(cases_path),
        "database_url": database_url,
        "corpus_dir": str(corpus_dir),
        "seeded_documents": inserted,
        "cases": len(results),
        "avg_precision_at_k": round(avg_precision, 4),
        "avg_keyword_recall": round(avg_recall, 4),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if min_precision is not None and avg_precision < min_precision:
        return 2
    if min_recall is not None and avg_recall < min_recall:
        return 3
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Knowledge-base retrieval benchmark runner.")
    parser.add_argument(
        "--cases",
        required=True,
        help="Path to JSON benchmark cases.",
    )
    parser.add_argument("--min-precision", type=float, default=None, help="Fail if average precision@k is lower.")
    parser.add_argument("--min-recall", type=float, default=None, help="Fail if average keyword recall is lower.")
    parser.add_argument(
        "--database-url",
        default=f"sqlite:///{DEFAULT_BENCHMARK_DB}",
        help="Database URL for benchmark execution.",
    )
    parser.add_argument(
        "--corpus-dir",
        default=str(DEFAULT_CORPUS_DIR),
        help="Directory containing benchmark corpus text files.",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset benchmark SQLite DB before loading corpus.",
    )
    args = parser.parse_args()

    return run_benchmark(
        cases_path=Path(args.cases),
        min_precision=args.min_precision,
        min_recall=args.min_recall,
        database_url=args.database_url,
        corpus_dir=Path(args.corpus_dir),
        reset_db=args.reset_db,
    )


if __name__ == "__main__":
    raise SystemExit(main())
