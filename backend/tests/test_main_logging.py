"""Regression tests for request logging resilience."""


def test_request_logging_survives_stdout_failure(client, monkeypatch):
    """Middleware logging must not break API responses when stdout is unavailable."""

    def _broken_print(*args, **kwargs):
        raise BrokenPipeError("simulated closed stdout")

    monkeypatch.setattr("builtins.print", _broken_print)

    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "StockTracker API is running"
