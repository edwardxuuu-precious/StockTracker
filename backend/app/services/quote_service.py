"""Quote fetching with provider fallback and in-memory TTL cache."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import io
import math
import re
import threading
import time
from typing import Any, Protocol
import urllib.parse
import urllib.request


def _normalize_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def _is_cn_symbol(symbol: str) -> bool:
    sym = _normalize_symbol(symbol)
    if re.fullmatch(r"\d{6}", sym):
        return True
    if re.fullmatch(r"\d{6}\.(SS|SZ|BJ)", sym):
        return True
    if re.fullmatch(r"(SH|SZ|BJ)\d{6}", sym):
        return True
    return False


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


class QuoteFetchError(Exception):
    """Raised when no provider can return a valid quote."""


class QuoteProvider(Protocol):
    """Provider protocol for quote adapters."""

    name: str

    def supports(self, symbol: str) -> bool:
        ...

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        ...


class YFinanceQuoteProvider:
    """Quote provider backed by yfinance."""

    name = "yfinance"

    def __init__(self) -> None:
        self._import_error: Exception | None = None
        self._yf = None
        try:
            import yfinance  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            self._import_error = exc
        else:
            self._yf = yfinance

    def supports(self, symbol: str) -> bool:
        return True

    def _to_ticker_symbol(self, symbol: str) -> str:
        sym = _normalize_symbol(symbol)
        if re.fullmatch(r"\d{6}", sym):
            if sym.startswith(("5", "6", "9")):
                return f"{sym}.SS"
            if sym.startswith(("4", "8")):
                return f"{sym}.BJ"
            return f"{sym}.SZ"
        if re.fullmatch(r"(SH|SS)\d{6}", sym):
            return f"{sym[-6:]}.SS"
        if re.fullmatch(r"SZ\d{6}", sym):
            return f"{sym[-6:]}.SZ"
        if re.fullmatch(r"BJ\d{6}", sym):
            return f"{sym[-6:]}.BJ"
        return sym

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        if self._yf is None:
            raise QuoteFetchError(f"yfinance import failed: {self._import_error}")

        ticker_symbol = self._to_ticker_symbol(symbol)
        ticker = self._yf.Ticker(ticker_symbol)

        price = None
        previous_close = None
        volume = None
        market_cap = None
        name = None

        fast_info = getattr(ticker, "fast_info", {}) or {}
        if isinstance(fast_info, dict):
            price = _to_float(
                fast_info.get("last_price")
                or fast_info.get("regular_market_price")
                or fast_info.get("lastPrice")
            )
            previous_close = _to_float(
                fast_info.get("previous_close")
                or fast_info.get("regular_market_previous_close")
                or fast_info.get("previousClose")
            )
            volume = _to_float(
                fast_info.get("last_volume")
                or fast_info.get("regular_market_volume")
                or fast_info.get("volume")
            )
            market_cap = _to_float(fast_info.get("market_cap") or fast_info.get("marketCap"))

        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            info = {}
        if isinstance(info, dict):
            name = info.get("longName") or info.get("shortName")
            if price is None:
                price = _to_float(
                    info.get("regularMarketPrice")
                    or info.get("currentPrice")
                    or info.get("ask")
                )
            if previous_close is None:
                previous_close = _to_float(
                    info.get("regularMarketPreviousClose") or info.get("previousClose")
                )
            if volume is None:
                volume = _to_float(info.get("regularMarketVolume") or info.get("volume"))
            if market_cap is None:
                market_cap = _to_float(info.get("marketCap"))

        if price is None:
            history = ticker.history(period="2d", interval="1d")
            if history is None or history.empty:
                raise QuoteFetchError("yfinance returned empty history")
            close_values = history["Close"].dropna().tolist()
            if not close_values:
                raise QuoteFetchError("yfinance returned empty close prices")
            price = float(close_values[-1])
            if previous_close is None and len(close_values) >= 2:
                previous_close = float(close_values[-2])
            if volume is None and "Volume" in history:
                vol_values = history["Volume"].dropna().tolist()
                if vol_values:
                    volume = _to_float(vol_values[-1])

        if price is None or price <= 0:
            raise QuoteFetchError("yfinance returned invalid price")

        if previous_close is None or previous_close <= 0:
            previous_close = price
        change = price - previous_close
        change_pct = (change / previous_close * 100) if previous_close else 0.0

        return {
            "symbol": _normalize_symbol(symbol),
            "name": name,
            "price": float(price),
            "change": float(change),
            "change_pct": float(change_pct),
            "volume": volume,
            "market_cap": market_cap,
            "source": self.name,
            "fetched_at": datetime.now(timezone.utc),
        }


class AkshareQuoteProvider:
    """Quote provider backed by akshare for A-share symbols."""

    name = "akshare"

    def __init__(self) -> None:
        self._import_error: Exception | None = None
        self._ak = None
        try:
            import akshare  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            self._import_error = exc
        else:
            self._ak = akshare

    def supports(self, symbol: str) -> bool:
        return _is_cn_symbol(symbol)

    def _to_cn_symbol(self, symbol: str) -> str:
        sym = _normalize_symbol(symbol)
        if re.fullmatch(r"\d{6}", sym):
            return sym
        if re.fullmatch(r"(SH|SS|SZ|BJ)\d{6}", sym):
            return sym[-6:]
        if re.fullmatch(r"\d{6}\.(SS|SZ|BJ)", sym):
            return sym[:6]
        return sym

    def _extract_spot_quote(self, symbol: str) -> dict[str, Any]:
        data_frame = self._ak.stock_zh_a_spot_em()
        if data_frame is None or data_frame.empty:
            raise QuoteFetchError("akshare returned empty A-share spot data")

        symbol_col = "代码" if "代码" in data_frame.columns else None
        if symbol_col is None:
            raise QuoteFetchError("akshare spot schema missing 代码 column")

        row = data_frame.loc[data_frame[symbol_col].astype(str) == symbol]
        if row.empty:
            raise QuoteFetchError(f"akshare cannot find symbol {symbol}")

        record = row.iloc[0]
        price = _to_float(record.get("最新价"))
        if price is None or price <= 0:
            raise QuoteFetchError("akshare returned invalid latest price")

        change = _to_float(record.get("涨跌额")) or 0.0
        change_pct = _to_float(record.get("涨跌幅")) or 0.0
        volume = _to_float(record.get("成交量"))
        market_cap = _to_float(record.get("总市值"))
        name = record.get("名称")

        return {
            "symbol": _normalize_symbol(symbol),
            "name": str(name) if name else None,
            "price": float(price),
            "change": float(change),
            "change_pct": float(change_pct),
            "volume": volume,
            "market_cap": market_cap,
            "source": self.name,
            "fetched_at": datetime.now(timezone.utc),
        }

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        if self._ak is None:
            raise QuoteFetchError(f"akshare import failed: {self._import_error}")

        cn_symbol = self._to_cn_symbol(symbol)
        if not re.fullmatch(r"\d{6}", cn_symbol):
            raise QuoteFetchError(f"akshare unsupported symbol format: {symbol}")

        return self._extract_spot_quote(cn_symbol)


class StooqQuoteProvider:
    """Quote provider backed by stooq CSV endpoint for non-CN symbols."""

    name = "stooq"

    _symbol_pattern = re.compile(r"^[A-Z][A-Z0-9\.\-]{0,14}$")

    def __init__(self, timeout_seconds: int = 15) -> None:
        self.timeout_seconds = max(1, int(timeout_seconds))

    def supports(self, symbol: str) -> bool:
        sym = _normalize_symbol(symbol)
        return bool(sym) and not _is_cn_symbol(sym) and bool(self._symbol_pattern.fullmatch(sym))

    def _to_stooq_symbol(self, symbol: str) -> str:
        sym = _normalize_symbol(symbol)
        if sym.endswith(".US"):
            return sym.lower()
        return f"{sym.lower()}.us"

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        stooq_symbol = self._to_stooq_symbol(symbol)
        query = urllib.parse.urlencode({"s": stooq_symbol, "f": "sd2t2ohlcv", "h": "e", "e": "csv"})
        url = f"https://stooq.com/q/l/?{query}"

        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            raise QuoteFetchError(f"stooq request failed: {exc}") from exc

        rows = list(csv.DictReader(io.StringIO(payload)))
        if not rows:
            raise QuoteFetchError("stooq returned empty payload")

        row = rows[0]
        close_price = _to_float(row.get("Close"))
        if close_price is None or close_price <= 0:
            raise QuoteFetchError("stooq returned invalid close price")

        volume = _to_float(row.get("Volume"))

        return {
            "symbol": _normalize_symbol(symbol),
            "name": _normalize_symbol(symbol),
            "price": float(close_price),
            "change": 0.0,
            "change_pct": 0.0,
            "volume": volume,
            "market_cap": None,
            "source": self.name,
            "fetched_at": datetime.now(timezone.utc),
        }


@dataclass
class CachedQuote:
    value: dict[str, Any]
    expires_at: float


class QuoteCache:
    """Simple thread-safe in-memory cache with counters."""

    def __init__(self) -> None:
        self._store: dict[str, CachedQuote] = {}
        self._lock = threading.Lock()
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_expired = 0

    def get(self, symbol: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            cached = self._store.get(symbol)
            if cached is None:
                self.cache_misses += 1
                return None
            if cached.expires_at <= now:
                self.cache_misses += 1
                self.cache_expired += 1
                del self._store[symbol]
                return None
            self.cache_hits += 1
            return dict(cached.value)

    def get_any(self, symbol: str) -> tuple[dict[str, Any], bool] | None:
        """Return cached value without mutating hit/miss counters.

        Returns a tuple of (value, is_expired). Expired entries are kept so the
        latest known price can be used as a resilience fallback.
        """
        now = time.time()
        with self._lock:
            cached = self._store.get(symbol)
            if cached is None:
                return None
            return dict(cached.value), cached.expires_at <= now

    def set(self, symbol: str, value: dict[str, Any], ttl_seconds: int) -> None:
        expires_at = time.time() + max(1, int(ttl_seconds))
        with self._lock:
            self._store[symbol] = CachedQuote(value=dict(value), expires_at=expires_at)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            self.cache_expired = 0

    def size(self) -> int:
        with self._lock:
            return len(self._store)


class QuoteService:
    """Facade used by API endpoints."""

    def __init__(self, cache_ttl_seconds: int) -> None:
        self.cache_ttl_seconds = max(1, int(cache_ttl_seconds))
        self.cache = QuoteCache()
        self.providers: list[QuoteProvider] = [
            YFinanceQuoteProvider(),
            StooqQuoteProvider(),
            AkshareQuoteProvider(),
        ]

    def _provider_chain(self, symbol: str) -> list[QuoteProvider]:
        prefer_akshare = _is_cn_symbol(symbol)
        order = ["akshare", "yfinance", "stooq"] if prefer_akshare else ["yfinance", "stooq", "akshare"]
        ranked: list[QuoteProvider] = []
        for name in order:
            ranked.extend(
                provider
                for provider in self.providers
                if provider.name == name and provider.supports(symbol)
            )
        ranked.extend(
            provider
            for provider in self.providers
            if provider.name not in order and provider.supports(symbol)
        )
        return ranked

    def _fetch_from_providers(self, symbol: str) -> dict[str, Any]:
        errors: list[str] = []
        for provider in self._provider_chain(symbol):
            try:
                quote = provider.fetch_quote(symbol)
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                continue
            normalized = dict(quote)
            normalized["symbol"] = symbol
            normalized["source"] = provider.name
            fetched_at = normalized.get("fetched_at")
            if not isinstance(fetched_at, datetime):
                normalized["fetched_at"] = datetime.now(timezone.utc)
            price = _to_float(normalized.get("price"))
            if price is None or price <= 0:
                errors.append(f"{provider.name}: invalid price")
                continue
            normalized["price"] = float(price)
            normalized["change"] = float(_to_float(normalized.get("change")) or 0.0)
            normalized["change_pct"] = float(_to_float(normalized.get("change_pct")) or 0.0)
            normalized["volume"] = _to_float(normalized.get("volume"))
            normalized["market_cap"] = _to_float(normalized.get("market_cap"))
            return normalized
        if errors:
            raise QuoteFetchError("; ".join(errors))
        raise QuoteFetchError("No available quote provider")

    def get_quote(self, symbol: str, refresh: bool = False) -> dict[str, Any]:
        normalized_symbol = _normalize_symbol(symbol)
        if not normalized_symbol:
            raise QuoteFetchError("symbol cannot be empty")

        if not refresh:
            cached = self.cache.get(normalized_symbol)
            if cached is not None:
                cached["cache_hit"] = True
                return cached

        try:
            quote = self._fetch_from_providers(normalized_symbol)
        except QuoteFetchError:
            # Resilience path: if provider refresh fails, keep the latest known
            # cached quote so portfolio pages remain usable.
            fallback = self.cache.get_any(normalized_symbol)
            if fallback is None:
                raise
            quote, _ = fallback
            quote["cache_hit"] = True
            return dict(quote)
        quote["cache_hit"] = False
        self.cache.set(normalized_symbol, quote, self.cache_ttl_seconds)
        return dict(quote)

    def get_batch_quotes(self, symbols: list[str], refresh: bool = False) -> list[dict[str, Any]]:
        deduped: list[str] = []
        seen: set[str] = set()
        for symbol in symbols:
            normalized = _normalize_symbol(symbol)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        quotes: list[dict[str, Any]] = []
        errors: list[str] = []
        for symbol in deduped:
            try:
                quotes.append(self.get_quote(symbol, refresh=refresh))
            except QuoteFetchError as exc:
                errors.append(f"{symbol}: {exc}")

        if quotes:
            return quotes

        if errors:
            raise QuoteFetchError("; ".join(errors))
        return []

    def get_stats(self) -> dict[str, Any]:
        total = self.cache.cache_hits + self.cache.cache_misses
        hit_rate = (self.cache.cache_hits / total) if total else 0.0
        return {
            "cache_hits": self.cache.cache_hits,
            "cache_misses": self.cache.cache_misses,
            "cache_expired": self.cache.cache_expired,
            "total_requests": total,
            "hit_rate": round(hit_rate, 4),
            "cache_size": self.cache.size(),
            "ttl_seconds": self.cache_ttl_seconds,
        }
