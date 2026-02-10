"""Unit tests for ingestion scheduler helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def test_load_jobs_reads_config(tmp_path):
    from run_scheduler import load_jobs

    config = tmp_path / "jobs.json"
    config.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "name": "demo",
                        "market": "CN",
                        "symbols": ["600519"],
                        "interval": "1m",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    jobs = load_jobs(config)
    assert len(jobs) == 1
    assert jobs[0]["name"] == "demo"


def test_run_job_normalizes_inputs_and_parses_dates():
    from run_scheduler import run_job

    calls = []

    class FakeService:
        def ingest_history(self, **kwargs):
            calls.append(kwargs)
            return 123

    summary = run_job(
        db=None,
        service=FakeService(),
        job={
            "market": "cn",
            "symbols": ["600519", " 000001 "],
            "interval": "1M",
            "provider": "akshare",
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-01-01T01:00:00Z",
        },
    )

    assert len(calls) == 2
    first = calls[0]
    assert first["market"] == "CN"
    assert first["interval"] == "1m"
    assert first["symbol"] == "600519"
    assert first["provider_name"] == "akshare"
    assert first["start"] == datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert first["end"] == datetime(2025, 1, 1, 1, 0, tzinfo=timezone.utc)
    assert summary["attempted"] == 2
    assert summary["succeeded"] == 2
    assert summary["failed"] == 0


def test_default_config_points_to_backend_config():
    from run_scheduler import DEFAULT_CONFIG

    assert str(DEFAULT_CONFIG).replace("\\", "/").endswith("/backend/config/ingestion_jobs.json")


def test_run_job_executes_and_idempotent(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base
    from app.models.market_data import Bar1d, IngestionLog
    from app.services.market_data_service import BarRecord, MarketDataService
    from run_scheduler import run_job

    class DummyProvider:
        name = "dummy"

        def supports(self, market: str, interval: str) -> bool:
            return market.upper() == "US" and interval == "1d"

        def fetch_history(self, symbol, start, end, interval):
            return [
                BarRecord(
                    ts=datetime(2025, 1, 2, tzinfo=timezone.utc),
                    open=100.0,
                    high=101.0,
                    low=99.0,
                    close=100.5,
                    volume=1000,
                    source=self.name,
                )
            ]

    db_path = tmp_path / "scheduler_test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure metadata includes all tables referenced by the service.
    import app.models.market_data  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        service = MarketDataService(providers=[DummyProvider()])
        job = {
            "name": "acceptance-us-daily",
            "market": "US",
            "symbols": ["AAPL"],
            "interval": "1d",
            "provider": "dummy",
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-01-03T00:00:00Z",
        }

        first = run_job(db=db, service=service, job=job)
        second = run_job(db=db, service=service, job=job)

        assert db.query(Bar1d).count() == 1
        assert db.query(IngestionLog).count() >= 2
        assert first["failed"] == 0
        assert second["failed"] == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_scheduler_main_writes_heartbeat_when_no_jobs(tmp_path, monkeypatch):
    from app.config import get_settings
    from run_scheduler import main

    heartbeat = tmp_path / "heartbeat.json"
    missing_jobs = tmp_path / "missing_jobs.json"
    db_path = tmp_path / "scheduler_main.db"

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("INGESTION_JOBS_PATH", str(missing_jobs))
    monkeypatch.setenv("SCHEDULER_HEARTBEAT_PATH", str(heartbeat))
    get_settings.cache_clear()

    main()

    payload = json.loads(heartbeat.read_text(encoding="utf-8"))
    assert payload["status"] == "idle_no_jobs"
    assert payload["jobs"] == 0


def test_cleanup_reports_keeps_latest(tmp_path):
    from run_scheduler import _cleanup_reports

    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    for idx in range(5):
        path = reports / f"cycle_2024010{idx}T000000Z.json"
        path.write_text("{}", encoding="utf-8")

    _cleanup_reports(reports, keep_count=2)

    left = sorted(Path(reports).glob("cycle_*.json"))
    assert len(left) == 2
