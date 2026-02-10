"""API tests for local market data queries."""
from datetime import datetime, timezone


def test_market_data_bars_query(client):
    from app.database import SessionLocal
    from app.models.market_data import Bar1m, Instrument

    db = SessionLocal()
    try:
        instrument = Instrument(symbol="600519", market="CN", name="Test CN")
        db.add(instrument)
        db.flush()

        ts = datetime(2025, 1, 2, 9, 31, tzinfo=timezone.utc)
        db.add(
            Bar1m(
                instrument_id=instrument.id,
                ts=ts,
                open=100.0,
                high=101.0,
                low=99.5,
                close=100.5,
                volume=12345,
                source="akshare",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/market-data/bars",
        params={"symbol": "600519", "market": "CN", "interval": "1m"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["symbol"] == "600519"
    assert item["market"] == "CN"
    assert item["interval"] == "1m"
    assert item["open"] == 100.0
    assert item["close"] == 100.5


def test_market_data_instruments_list(client):
    from app.database import SessionLocal
    from app.models.market_data import Instrument

    db = SessionLocal()
    try:
        db.add(Instrument(symbol="AAPL", market="US", name="Apple"))
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/market-data/instruments", params={"market": "US"})
    assert response.status_code == 200
    data = response.json()
    assert any(item["symbol"] == "AAPL" for item in data)


def test_market_data_status_and_ingestions(client):
    from app.database import SessionLocal
    from app.models.market_data import Bar1m, DataSourceMeta, IngestionLog, Instrument

    db = SessionLocal()
    try:
        instrument = Instrument(symbol="600001", market="CN", name="Test CN")
        db.add(instrument)
        db.flush()

        ts1 = datetime(2025, 1, 2, 1, 0, tzinfo=timezone.utc)
        ts2 = datetime(2025, 1, 2, 1, 1, tzinfo=timezone.utc)
        ts3 = datetime(2025, 1, 2, 1, 3, tzinfo=timezone.utc)
        db.add_all(
            [
                Bar1m(
                    instrument_id=instrument.id,
                    ts=ts1,
                    open=10.0,
                    high=10.5,
                    low=9.8,
                    close=10.2,
                    volume=100,
                    source="akshare",
                ),
                Bar1m(
                    instrument_id=instrument.id,
                    ts=ts2,
                    open=10.2,
                    high=10.6,
                    low=10.1,
                    close=10.4,
                    volume=120,
                    source="akshare",
                ),
                Bar1m(
                    instrument_id=instrument.id,
                    ts=ts3,
                    open=10.4,
                    high=10.7,
                    low=10.3,
                    close=10.6,
                    volume=140,
                    source="akshare",
                ),
            ]
        )

        db.add(
            DataSourceMeta(
                source="akshare",
                market="CN",
                symbol="600001",
                interval="1m",
                last_success_ts=ts3,
            )
        )
        db.add(
            IngestionLog(
                source="akshare",
                market="CN",
                symbol="600001",
                interval="1m",
                start_ts=ts1,
                end_ts=ts3,
                status="completed",
                message="ingested 3 bars",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/market-data/status",
        params={
            "symbol": "600001",
            "market": "CN",
            "interval": "1m",
            "start": "2025-01-02T01:00:00Z",
            "end": "2025-01-02T01:03:00Z",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_bars"] == 3
    assert payload["gap_estimate"] == 1
    assert payload["last_ingest"]["source"] == "akshare"

    response = client.get(
        "/api/v1/market-data/ingestions",
        params={"symbol": "600001", "market": "CN", "interval": "1m"},
    )
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["status"] == "completed"


def test_market_data_ingest_endpoint(client):
    from app.api.v1 import market_data as market_data_api
    from app.services.market_data_service import BarRecord, MarketDataService

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
                    low=99.5,
                    close=100.8,
                    volume=1234,
                    source=self.name,
                )
            ]

    original_service = market_data_api.market_data_service
    market_data_api.market_data_service = MarketDataService(providers=[DummyProvider()])
    try:
        response = client.post(
            "/api/v1/market-data/ingest",
            json={
                "symbols": ["AAPL"],
                "market": "US",
                "interval": "1d",
                "start": "2025-01-01T00:00:00Z",
                "end": "2025-01-03T00:00:00Z",
                "provider": "dummy",
            },
        )
        assert response.status_code == 200
        body = response.json()["results"]
        assert len(body) == 1
        assert body[0]["status"] == "completed"
        assert body[0]["ingested"] >= 1

        logs = client.get(
            "/api/v1/market-data/ingestions",
            params={"symbol": "AAPL", "market": "US", "interval": "1d"},
        )
        assert logs.status_code == 200
        assert any(item["status"] == "completed" for item in logs.json())
    finally:
        market_data_api.market_data_service = original_service
