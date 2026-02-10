"""Market data providers for CN and US markets."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import io
import math
import csv
from zoneinfo import ZoneInfo

from .market_data_service import BarRecord


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value)
    # Handle "Z" suffix from ISO8601 values.
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _to_utc(ts: datetime, assume_tz: str | None = None) -> datetime:
    if ts.tzinfo is not None:
        return ts.astimezone(timezone.utc)
    if assume_tz:
        return ts.replace(tzinfo=ZoneInfo(assume_tz)).astimezone(timezone.utc)
    return ts.replace(tzinfo=timezone.utc)


def _pick_column(frame, candidates: list[str]) -> str:
    for name in candidates:
        if name in frame.columns:
            return name
    raise KeyError(f"Missing columns: {candidates}")


@dataclass
class AkshareMarketDataProvider:
    name: str = "akshare"

    def supports(self, market: str, interval: str) -> bool:
        return market.upper() == "CN" and interval in {"1m", "1d"}

    def fetch_history(
        self,
        symbol: str,
        start: datetime | None,
        end: datetime | None,
        interval: str,
    ) -> list[BarRecord]:
        try:
            import akshare  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"akshare import failed: {exc}") from exc

        interval = interval.lower()
        if interval == "1d":
            data = akshare.stock_zh_a_hist(symbol=symbol, period="daily", adjust="")  # type: ignore[attr-defined]
            time_col = _pick_column(data, ["日期", "date", "时间"])
        else:
            kwargs = {
                "symbol": symbol,
                "period": "1",
                "start_date": start.strftime("%Y-%m-%d %H:%M:%S") if start else None,
                "end_date": end.strftime("%Y-%m-%d %H:%M:%S") if end else None,
                "adjust": "",
            }
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            if not hasattr(akshare, "stock_zh_a_hist_min_em"):
                raise RuntimeError("akshare missing stock_zh_a_hist_min_em")
            data = akshare.stock_zh_a_hist_min_em(**kwargs)  # type: ignore[attr-defined]
            time_col = _pick_column(data, ["时间", "date", "日期"])

        if data is None or data.empty:
            return []

        open_col = _pick_column(data, ["开盘", "open", "开"])
        high_col = _pick_column(data, ["最高", "high", "高"])
        low_col = _pick_column(data, ["最低", "low", "低"])
        close_col = _pick_column(data, ["收盘", "close", "收"])
        volume_col = _pick_column(data, ["成交量", "volume", "量"])

        records: list[BarRecord] = []
        for _, row in data.iterrows():
            ts = _to_utc(_to_datetime(row[time_col]), assume_tz="Asia/Shanghai")
            records.append(
                BarRecord(
                    ts=ts,
                    open=float(row[open_col]),
                    high=float(row[high_col]),
                    low=float(row[low_col]),
                    close=float(row[close_col]),
                    volume=int(row[volume_col]) if row[volume_col] is not None else None,
                    source=self.name,
                )
            )

        if start:
            records = [item for item in records if item.ts >= _to_utc(start, assume_tz="Asia/Shanghai")]
        if end:
            records = [item for item in records if item.ts <= _to_utc(end, assume_tz="Asia/Shanghai")]
        return records


@dataclass
class UsYFinanceMarketDataProvider:
    """US market provider based on yfinance free data."""

    name: str = "yfinance"

    def supports(self, market: str, interval: str) -> bool:
        return market.upper() == "US" and interval in {"1m", "1d"}

    def fetch_history(
        self,
        symbol: str,
        start: datetime | None,
        end: datetime | None,
        interval: str,
    ) -> list[BarRecord]:
        try:
            import pandas as pd
            import yfinance as yf  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"yfinance dependencies import failed: {exc}") from exc

        yf_interval = "1m" if interval == "1m" else "1d"
        try:
            history = yf.download(
                tickers=symbol,
                start=start,
                end=end,
                interval=yf_interval,
                auto_adjust=False,
                progress=False,
                prepost=False,
                group_by="column",
                threads=False,
            )
        except Exception:
            history = None

        if history is None or history.empty:
            # Fallback for daily bars when yfinance is rate-limited.
            if interval == "1d":
                fallback = self._fetch_stooq_daily(symbol, start, end)
                if fallback:
                    return fallback
            return []

        frame = history.copy()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [str(col[0]) for col in frame.columns]

        required = ["Open", "High", "Low", "Close"]
        missing = [col for col in required if col not in frame.columns]
        if missing:
            raise RuntimeError(f"yfinance missing columns: {missing}")

        volume_col = "Volume" if "Volume" in frame.columns else None
        records: list[BarRecord] = []
        for idx, row in frame.iterrows():
            ts = _to_datetime(idx)
            ts = _to_utc(ts, assume_tz="America/New_York")
            volume_value = None
            if volume_col:
                raw = row[volume_col]
                if raw is not None and not (isinstance(raw, float) and math.isnan(raw)):
                    try:
                        volume_value = int(raw)
                    except Exception:
                        volume_value = None
            records.append(
                BarRecord(
                    ts=ts,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=volume_value,
                    source=self.name,
                )
            )

        if start:
            records = [item for item in records if item.ts >= _to_utc(start, assume_tz="America/New_York")]
        if end:
            records = [item for item in records if item.ts <= _to_utc(end, assume_tz="America/New_York")]
        return records

    def _fetch_stooq_daily(
        self,
        symbol: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[BarRecord]:
        try:
            import requests
        except Exception:
            return []

        url = "https://stooq.com/q/d/l/"
        params = {"s": f"{symbol.lower()}.us", "i": "d"}
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code != 200:
                return []
            text = resp.text or ""
        except Exception:
            return []

        if "No data" in text or "Exceeded the daily hits limit" in text:
            return []

        reader = csv.DictReader(io.StringIO(text))
        records: list[BarRecord] = []
        for row in reader:
            date_text = row.get("Date")
            open_text = row.get("Open")
            high_text = row.get("High")
            low_text = row.get("Low")
            close_text = row.get("Close")
            if not date_text or not open_text or not high_text or not low_text or not close_text:
                continue
            try:
                ts = datetime.fromisoformat(date_text)
                ts = _to_utc(ts, assume_tz="America/New_York")
                volume_value = row.get("Volume")
                volume = int(float(volume_value)) if volume_value not in (None, "", "0") else None
                item = BarRecord(
                    ts=ts,
                    open=float(open_text),
                    high=float(high_text),
                    low=float(low_text),
                    close=float(close_text),
                    volume=volume,
                    source=f"{self.name}-stooq",
                )
            except Exception:
                continue
            records.append(item)

        records.sort(key=lambda x: x.ts)
        if start:
            records = [item for item in records if item.ts >= _to_utc(start, assume_tz="America/New_York")]
        if end:
            records = [item for item in records if item.ts <= _to_utc(end, assume_tz="America/New_York")]
        return records
