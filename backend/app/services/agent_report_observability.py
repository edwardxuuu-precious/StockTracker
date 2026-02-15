"""In-memory observability store for agent report calls."""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from math import ceil
from threading import Lock
from typing import Any

_MAX_EVENTS = 1000
_events: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_lock = Lock()


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, ceil(0.95 * len(ordered)))
    return float(ordered[rank - 1])


def clear_agent_report_metrics() -> None:
    """Reset in-memory metrics. Used by tests."""
    with _lock:
        _events.clear()


def record_agent_report_event(
    *,
    success: bool,
    fallback_used: bool,
    timeout_hit: bool,
    report_latency_ms: float,
    llm_provider: str,
    llm_latency_ms: float | None,
    llm_retry_count: int,
    llm_timeout_seconds: float | None,
    llm_error_type: str | None,
) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "success": bool(success),
        "fallback_used": bool(fallback_used),
        "timeout_hit": bool(timeout_hit),
        "report_latency_ms": float(report_latency_ms),
        "llm_provider": llm_provider,
        "llm_latency_ms": None if llm_latency_ms is None else float(llm_latency_ms),
        "llm_retry_count": int(llm_retry_count),
        "llm_timeout_seconds": None if llm_timeout_seconds is None else float(llm_timeout_seconds),
        "llm_error_type": llm_error_type,
    }
    with _lock:
        _events.append(event)


def get_agent_report_metrics(window: int = 200) -> dict[str, Any]:
    """Return aggregate metrics over the latest `window` events."""
    with _lock:
        data = list(_events)[-max(1, int(window)) :]

    total = len(data)
    if total == 0:
        return {
            "window": int(window),
            "total": 0,
            "success_rate": None,
            "p95_latency_ms": None,
            "fallback_ratio": None,
            "timeout_rate": None,
            "llm_p95_latency_ms": None,
        }

    success_count = sum(1 for item in data if item["success"])
    fallback_count = sum(1 for item in data if item["fallback_used"])
    timeout_count = sum(1 for item in data if item["timeout_hit"])

    report_latencies = [float(item["report_latency_ms"]) for item in data]
    llm_latencies = [float(item["llm_latency_ms"]) for item in data if item["llm_latency_ms"] is not None]

    return {
        "window": int(window),
        "total": total,
        "success_rate": round(success_count / total, 6),
        "p95_latency_ms": _p95(report_latencies),
        "fallback_ratio": round(fallback_count / total, 6),
        "timeout_rate": round(timeout_count / total, 6),
        "llm_p95_latency_ms": _p95(llm_latencies),
    }
