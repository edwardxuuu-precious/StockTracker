"""Tests for market data provider adapters."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd


def test_us_yfinance_provider_parses_history(monkeypatch):
    from app.services.market_data_providers import UsYFinanceMarketDataProvider

    index = pd.to_datetime(
        [
            "2025-01-02 14:30:00+00:00",
            "2025-01-02 14:31:00+00:00",
        ]
    )
    frame = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [101.0, 102.0],
            "Low": [99.5, 100.5],
            "Close": [100.5, 101.5],
            "Volume": [1000, 1200],
        },
        index=index,
    )

    fake_yf = SimpleNamespace(download=lambda **kwargs: frame)
    monkeypatch.setitem(__import__("sys").modules, "yfinance", fake_yf)

    provider = UsYFinanceMarketDataProvider()
    rows = provider.fetch_history(
        symbol="AAPL",
        start=datetime(2025, 1, 2, 14, 30, tzinfo=timezone.utc),
        end=datetime(2025, 1, 2, 14, 31, tzinfo=timezone.utc),
        interval="1m",
    )
    assert len(rows) == 2
    assert rows[0].source == "yfinance"
    assert rows[0].close == 100.5
    assert rows[1].volume == 1200
