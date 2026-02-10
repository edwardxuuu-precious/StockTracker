"""Pytest fixtures for backend API tests."""
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class TestTradeQuoteProvider:
    """Deterministic quote provider for trade symbol validation in tests."""

    name = "test-trade-provider"

    def supports(self, symbol: str) -> bool:
        return True

    def fetch_quote(self, symbol: str) -> dict:
        normalized = str(symbol or "").strip().upper()
        if normalized.startswith("INVALID"):
            raise RuntimeError(f"stooq returned no data for {normalized}")
        return {
            "symbol": normalized,
            "name": normalized,
            "price": 100.0,
            "change": 0.0,
            "change_pct": 0.0,
            "volume": 1000.0,
            "market_cap": None,
            "source": "test",
        }


@pytest.fixture(autouse=True)
def mock_trade_quote_service():
    """Avoid external network in trade tests while preserving validation behavior."""
    from app.api.v1 import holding as holding_api

    service = holding_api.trade_quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    service.providers = [TestTradeQuoteProvider()]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        yield
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create an isolated FastAPI TestClient backed by a temporary SQLite DB."""
    db_path = tmp_path / "stocktracker_test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    from app.config import get_settings

    get_settings.cache_clear()

    import app.database as database

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    database.engine = engine
    database.SessionLocal = testing_session

    # Ensure models are loaded into metadata before table creation.
    import app.models.portfolio  # noqa: F401
    import app.models.strategy  # noqa: F401
    import app.models.backtest  # noqa: F401
    import app.models.market_data  # noqa: F401
    import app.models.knowledge_base  # noqa: F401
    import app.models.strategy_version  # noqa: F401

    database.Base.metadata.create_all(bind=engine)

    from app.main import app

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[database.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    database.Base.metadata.drop_all(bind=engine)
