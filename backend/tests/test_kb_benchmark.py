"""Regression tests for KB benchmark corpus seeding and runner."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def _load_kb_benchmark():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "kb_benchmark.py"
    spec = importlib.util.spec_from_file_location("kb_benchmark", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_seed_corpus_supports_manifest_and_file_docs(tmp_path):
    bench = _load_kb_benchmark()
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "corpus_pack.json").write_text(
        json.dumps(
            [
                {
                    "source_name": "manifest-doc.pdf",
                    "source_type": "pdf",
                    "title": "Manifest Doc",
                    "content": "manifest seeded content for benchmark",
                }
            ]
        ),
        encoding="utf-8",
    )
    (corpus / "extra_doc.txt").write_text("extra txt seeded content", encoding="utf-8")
    (corpus / "extra_doc.json").write_text(json.dumps({"k": "v", "topic": "json seeded"}), encoding="utf-8")

    db_path = tmp_path / "bench.sqlite3"
    engine, session_factory = bench._build_db_session(f"sqlite:///{db_path.as_posix()}")
    db = session_factory()
    try:
        inserted = bench._seed_corpus_if_needed(db, corpus)
        count = db.query(bench.KnowledgeDocument).count()
    finally:
        db.close()
        engine.dispose()

    assert inserted == 3
    assert count == 3


def test_run_benchmark_with_manifest_corpus(tmp_path):
    bench = _load_kb_benchmark()
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "corpus_pack.json").write_text(
        json.dumps(
            [
                {
                    "source_name": "policy-note.txt",
                    "source_type": "txt",
                    "title": "Policy Note",
                    "content": "profile policy precision recall thresholds for release gate",
                }
            ]
        ),
        encoding="utf-8",
    )
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            [
                {
                    "query": "release gate policy precision recall",
                    "expected_keywords": ["policy", "precision", "recall"],
                    "top_k": 3,
                    "mode": "hybrid",
                    "policy_profile": "balanced",
                }
            ]
        ),
        encoding="utf-8",
    )

    code = bench.run_benchmark(
        cases_path=cases,
        min_precision=0.3,
        min_recall=0.5,
        database_url=f"sqlite:///{(tmp_path / 'runner.sqlite3').as_posix()}",
        corpus_dir=corpus,
        reset_db=True,
    )

    assert code == 0
