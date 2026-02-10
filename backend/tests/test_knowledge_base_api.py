"""API tests for knowledge base ingestion and retrieval."""
from datetime import datetime, timezone


def _seed_us_daily_bars(symbol: str, start_day: int, db):
    from app.models.market_data import Bar1d, Instrument

    instrument = Instrument(symbol=symbol, market="US", name=symbol)
    db.add(instrument)
    db.flush()
    for day in range(start_day, start_day + 8):
        db.add(
            Bar1d(
                instrument_id=instrument.id,
                ts=datetime(2025, 1, day, tzinfo=timezone.utc),
                open=100.0 + day,
                high=101.0 + day,
                low=99.0 + day,
                close=100.5 + day,
                volume=1000 + day,
                source="test",
            )
        )


def test_kb_ingest_file_and_search(client):
    response = client.post(
        "/api/v1/kb/ingest",
        files={"file": ("kb-note.txt", b"drawdown control and risk management with stop loss", "text/plain")},
        data={"source_type": "txt", "title": "KB Note"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chunk_count"] >= 1
    assert body["document"]["source_type"] == "txt"

    for mode in ("fts", "vector", "hybrid"):
        search = client.post("/api/v1/kb/search", json={"query": "drawdown control", "top_k": 3, "mode": mode})
        assert search.status_code == 200
        hits = search.json()["hits"]
        assert len(hits) >= 1
        assert hits[0]["document"]["id"] == body["document"]["id"]
        assert isinstance(hits[0]["reference_id"], str)
        assert hits[0]["confidence"] in {"low", "medium", "high"}
        assert isinstance(hits[0]["governance_flags"], list)
        assert isinstance(hits[0]["snippet"], str)

    docs = client.get("/api/v1/kb/documents")
    assert docs.status_code == 200
    assert any(item["id"] == body["document"]["id"] for item in docs.json())


def test_agent_report_with_kb_citations(client):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _seed_us_daily_bars("AAPL", 1, db)
        db.commit()
    finally:
        db.close()

    ingested = client.post(
        "/api/v1/kb/ingest-text",
        data={
            "source_name": "playbook.txt",
            "source_type": "txt",
            "content": (
                "To reduce drawdown, lower allocation_per_trade, avoid overtrading, "
                "and prioritize strategies with stable risk-adjusted returns."
            ),
        },
    )
    assert ingested.status_code == 200

    generated = client.post(
        "/api/v1/agent/strategy/generate",
        json={"prompt": "build a moving average strategy with 5 and 20 windows", "name": "Agent MA"},
    )
    assert generated.status_code == 200
    strategy_id = generated.json()["strategy"]["id"]

    tuned = client.post(
        "/api/v1/agent/strategy/tune",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-08",
            "initial_capital": 100000,
            "market": "US",
            "interval": "1d",
            "max_trials": 3,
            "top_k": 2,
            "parameter_grid": {"short_window": [3, 5], "long_window": [8, 12]},
        },
    )
    assert tuned.status_code == 200
    backtest_id = tuned.json()["best_trial"]["backtest_id"]

    report = client.post(
        f"/api/v1/agent/backtests/{backtest_id}/report",
        json={"question": "how to reduce drawdown", "top_k_sources": 2},
    )
    assert report.status_code == 200
    citations = report.json()["citations"]
    assert len(citations) >= 1
    assert citations[0]["confidence"] in {"low", "medium", "high"}
    assert isinstance(citations[0]["governance_flags"], list)
    assert isinstance(citations[0]["reference_id"], str)

    # request-level citation filters should override defaults
    filtered = client.post(
        f"/api/v1/agent/backtests/{backtest_id}/report",
        json={
            "question": "how to reduce drawdown",
            "top_k_sources": 2,
            "allowed_source_types": ["pdf"],
            "allow_citation_fallback": False,
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["citations"] == []

    strict_profile = client.post(
        f"/api/v1/agent/backtests/{backtest_id}/report",
        json={
            "question": "how to reduce drawdown",
            "top_k_sources": 3,
            "citation_policy_profile": "strict",
        },
    )
    assert strict_profile.status_code == 200
    strict_citations = strict_profile.json()["citations"]
    assert all("fallback_selected" not in item["governance_flags"] for item in strict_citations)


def test_kb_governance_limits_doc_concentration(client):
    # one large document with many matching chunks
    long_content = ("riskcontrol " * 2500) + " end"
    ingested_large = client.post(
        "/api/v1/kb/ingest-text",
        data={
            "source_name": "large.txt",
            "source_type": "txt",
            "content": long_content,
            "title": "Large",
        },
    )
    assert ingested_large.status_code == 200

    # additional matching documents for diversity
    for idx in range(1, 4):
        resp = client.post(
            "/api/v1/kb/ingest-text",
            data={
                "source_name": f"small-{idx}.txt",
                "source_type": "txt",
                "content": f"riskcontrol mitigation note {idx}",
                "title": f"Small {idx}",
            },
        )
        assert resp.status_code == 200

    search = client.post(
        "/api/v1/kb/search",
        json={"query": "riskcontrol", "top_k": 5, "mode": "hybrid"},
    )
    assert search.status_code == 200
    hits = search.json()["hits"]
    assert len(hits) == 5

    counts: dict[int, int] = {}
    for hit in hits:
        doc_id = int(hit["document"]["id"])
        counts[doc_id] = counts.get(doc_id, 0) + 1
    assert max(counts.values()) <= 2

    strict_search = client.post(
        "/api/v1/kb/search",
        json={"query": "riskcontrol", "top_k": 5, "mode": "hybrid", "policy_profile": "strict"},
    )
    assert strict_search.status_code == 200
    strict_hits = strict_search.json()["hits"]
    strict_counts: dict[int, int] = {}
    for hit in strict_hits:
        doc_id = int(hit["document"]["id"])
        strict_counts[doc_id] = strict_counts.get(doc_id, 0) + 1
    if strict_counts:
        assert max(strict_counts.values()) <= 1


def test_kb_search_source_allow_and_block_filters(client):
    ingested_txt = client.post(
        "/api/v1/kb/ingest-text",
        data={
            "source_name": "blocked-playbook.txt",
            "source_type": "txt",
            "content": "riskcontrol guide text document",
        },
    )
    assert ingested_txt.status_code == 200

    ingested_json = client.post(
        "/api/v1/kb/ingest-text",
        data={
            "source_name": "research-note.json",
            "source_type": "json",
            "content": "{\"topic\":\"riskcontrol guidelines\"}",
        },
    )
    assert ingested_json.status_code == 200

    search = client.post(
        "/api/v1/kb/search",
        json={
            "query": "riskcontrol",
            "top_k": 5,
            "mode": "hybrid",
            "allowed_source_types": ["json"],
            "blocked_source_keywords": ["blocked"],
        },
    )
    assert search.status_code == 200
    hits = search.json()["hits"]
    assert len(hits) >= 1
    assert all(hit["document"]["source_type"] == "json" for hit in hits)
    assert all("blocked" not in hit["document"]["source_name"].lower() for hit in hits)


def test_kb_search_can_disable_fallback(client):
    ingested = client.post(
        "/api/v1/kb/ingest-text",
        data={
            "source_name": "plain-note.txt",
            "source_type": "txt",
            "content": "alpha beta gamma delta",
        },
    )
    assert ingested.status_code == 200

    strict = client.post(
        "/api/v1/kb/search",
        json={
            "query": "zzzzzzzzzz yyyyyyyyyy",
            "top_k": 3,
            "mode": "vector",
            "min_score": 0.95,
            "allow_fallback": False,
        },
    )
    assert strict.status_code == 200
    assert strict.json()["hits"] == []

    relaxed = client.post(
        "/api/v1/kb/search",
        json={
            "query": "zzzzzzzzzz yyyyyyyyyy",
            "top_k": 3,
            "mode": "vector",
            "min_score": 0.95,
            "allow_fallback": True,
        },
    )
    assert relaxed.status_code == 200
    hits = relaxed.json()["hits"]
    assert len(hits) >= 1
    assert any("fallback_selected" in hit["governance_flags"] for hit in hits)


def test_kb_search_handles_punctuation_query(client):
    ingested = client.post(
        "/api/v1/kb/ingest-text",
        data={
            "source_name": "punctuation.txt",
            "source_type": "txt",
            "content": "risk adjusted return and drawdown control guidance",
        },
    )
    assert ingested.status_code == 200

    search = client.post(
        "/api/v1/kb/search",
        json={
            "query": "how to improve risk-adjusted returns?",
            "top_k": 3,
            "mode": "fts",
        },
    )
    assert search.status_code == 200
