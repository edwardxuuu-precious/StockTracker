"""Manual market data ingestion CLI."""
from __future__ import annotations

import argparse
from datetime import datetime

from app.database import SessionLocal
from app.services.market_data_providers import AkshareMarketDataProvider, UsYFinanceMarketDataProvider
from app.services.market_data_service import MarketDataService


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest market data into local store")
    parser.add_argument("--symbol", required=True, help="Ticker symbol, e.g. 600519 or AAPL")
    parser.add_argument("--market", default="CN", help="Market code, e.g. CN/US")
    parser.add_argument("--interval", default="1m", choices=["1m", "1d"], help="Bar interval")
    parser.add_argument("--start", help="Start datetime (ISO format)")
    parser.add_argument("--end", help="End datetime (ISO format)")
    parser.add_argument("--provider", help="Provider name override")

    args = parser.parse_args()
    start = _parse_datetime(args.start)
    end = _parse_datetime(args.end)

    service = MarketDataService(
        providers=[AkshareMarketDataProvider(), UsYFinanceMarketDataProvider()]
    )

    with SessionLocal() as db:
        count = service.ingest_history(
            db=db,
            symbol=args.symbol,
            market=args.market,
            interval=args.interval,
            start=start,
            end=end,
            provider_name=args.provider,
        )

    print(f"[OK] Ingested {count} bars for {args.symbol} ({args.market}, {args.interval})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
