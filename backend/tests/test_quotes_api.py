"""API tests for quote endpoints and cache behavior."""

from app.api.v1 import quotes as quotes_api


class FakeQuoteProvider:
    """Deterministic provider used for quote API tests."""

    name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def supports(self, symbol: str) -> bool:
        return True

    def fetch_quote(self, symbol: str) -> dict:
        self.calls += 1
        price = 100.0 + self.calls
        return {
            "symbol": symbol,
            "name": f"{symbol} Corp",
            "price": price,
            "change": 1.5,
            "change_pct": 1.5,
            "volume": 12345.0,
            "market_cap": 987654321.0,
        }


class AlwaysFailProvider:
    """Provider that always fails to verify fallback chain behavior."""

    name = "always-fail"

    def supports(self, symbol: str) -> bool:
        return True

    def fetch_quote(self, symbol: str) -> dict:
        raise RuntimeError("intentional provider failure")


class OneShotThenFailProvider:
    """Provider that succeeds once and fails afterwards."""

    name = "one-shot"

    def __init__(self) -> None:
        self.calls = 0

    def supports(self, symbol: str) -> bool:
        return True

    def fetch_quote(self, symbol: str) -> dict:
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("provider unavailable after first fetch")
        return {
            "symbol": symbol,
            "name": f"{symbol} Corp",
            "price": 123.45,
            "change": 0.0,
            "change_pct": 0.0,
            "volume": 1000.0,
            "market_cap": None,
        }


class SelectiveFailProvider:
    """Provider that fails for selected symbols to test partial batch success."""

    name = "selective-fail"

    def supports(self, symbol: str) -> bool:
        return True

    def fetch_quote(self, symbol: str) -> dict:
        if symbol == "MSFT":
            raise RuntimeError("simulated symbol-specific failure")
        return {
            "symbol": symbol,
            "name": f"{symbol} Corp",
            "price": 222.22,
            "change": 0.0,
            "change_pct": 0.0,
            "volume": 1000.0,
            "market_cap": None,
        }


def test_single_quote_cache_hit_and_stats(client):
    service = quotes_api.quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    provider = FakeQuoteProvider()
    service.providers = [provider]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        first = client.get("/api/v1/quotes/AAPL")
        assert first.status_code == 200
        first_data = first.json()
        assert first_data["symbol"] == "AAPL"
        assert first_data["cache_hit"] is False
        assert first_data["source"] == "fake"
        assert provider.calls == 1

        second = client.get("/api/v1/quotes/AAPL")
        assert second.status_code == 200
        second_data = second.json()
        assert second_data["cache_hit"] is True
        assert second_data["price"] == first_data["price"]
        assert provider.calls == 1

        stats = client.get("/api/v1/quotes/stats")
        assert stats.status_code == 200
        stats_data = stats.json()
        assert stats_data["cache_hits"] == 1
        assert stats_data["cache_misses"] == 1
        assert stats_data["cache_size"] == 1
        assert stats_data["hit_rate"] == 0.5
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()


def test_quote_refresh_bypasses_cache(client):
    service = quotes_api.quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    provider = FakeQuoteProvider()
    service.providers = [provider]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        first = client.get("/api/v1/quotes/MSFT")
        assert first.status_code == 200
        first_data = first.json()
        assert first_data["cache_hit"] is False
        assert provider.calls == 1

        refreshed = client.get("/api/v1/quotes/MSFT?refresh=true")
        assert refreshed.status_code == 200
        refreshed_data = refreshed.json()
        assert refreshed_data["cache_hit"] is False
        assert refreshed_data["price"] > first_data["price"]
        assert provider.calls == 2

        after_refresh = client.get("/api/v1/quotes/MSFT")
        assert after_refresh.status_code == 200
        after_refresh_data = after_refresh.json()
        assert after_refresh_data["cache_hit"] is True
        assert after_refresh_data["price"] == refreshed_data["price"]
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()


def test_quote_provider_fallback_uses_next_provider(client):
    service = quotes_api.quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    failing = AlwaysFailProvider()
    provider = FakeQuoteProvider()
    service.providers = [failing, provider]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        response = client.get("/api/v1/quotes/AAPL")
        assert response.status_code == 200
        payload = response.json()
        assert payload["symbol"] == "AAPL"
        assert payload["source"] == "fake"
        assert payload["cache_hit"] is False
        assert provider.calls == 1
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()


def test_batch_quotes_with_partial_cache(client):
    service = quotes_api.quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    provider = FakeQuoteProvider()
    service.providers = [provider]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        warmup = client.get("/api/v1/quotes/AAPL")
        assert warmup.status_code == 200
        assert provider.calls == 1

        batch = client.get("/api/v1/quotes/batch?symbols=AAPL,MSFT,GOOGL")
        assert batch.status_code == 200
        items = batch.json()
        assert [item["symbol"] for item in items] == ["AAPL", "MSFT", "GOOGL"]

        by_symbol = {item["symbol"]: item for item in items}
        assert by_symbol["AAPL"]["cache_hit"] is True
        assert by_symbol["MSFT"]["cache_hit"] is False
        assert by_symbol["GOOGL"]["cache_hit"] is False
        assert provider.calls == 3
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()


def test_refresh_uses_cached_quote_when_provider_temporarily_fails(client):
    service = quotes_api.quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    provider = OneShotThenFailProvider()
    service.providers = [provider]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        first = client.get("/api/v1/quotes/AAPL")
        assert first.status_code == 200
        first_data = first.json()
        assert first_data["cache_hit"] is False
        assert first_data["price"] == 123.45

        refreshed = client.get("/api/v1/quotes/AAPL?refresh=true")
        assert refreshed.status_code == 200
        refreshed_data = refreshed.json()
        assert refreshed_data["cache_hit"] is True
        assert refreshed_data["price"] == first_data["price"]
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()


def test_batch_quotes_returns_partial_success_instead_of_failing_all(client):
    service = quotes_api.quote_service
    original_providers = service.providers
    original_ttl = service.cache_ttl_seconds
    provider = SelectiveFailProvider()
    service.providers = [provider]
    service.cache_ttl_seconds = 60
    service.cache.clear()

    try:
        response = client.get("/api/v1/quotes/batch?symbols=AAPL,MSFT")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["symbol"] == "AAPL"
        assert payload[0]["cache_hit"] is False
    finally:
        service.providers = original_providers
        service.cache_ttl_seconds = original_ttl
        service.cache.clear()
