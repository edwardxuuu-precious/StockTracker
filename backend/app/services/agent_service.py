"""Deterministic agent helpers for strategy generation, tuning, and reporting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
import re
from typing import Any

from ..models.backtest import Backtest, Trade
from ..services.knowledge_base import search_knowledge_base


@dataclass(frozen=True)
class GeneratedStrategy:
    strategy_type: str
    parameters: dict[str, Any]
    rationale: str
    code: str


def _extract_numbers(text: str) -> list[float]:
    values = re.findall(r"-?\d+(?:\.\d+)?", text or "")
    return [float(item) for item in values]


def _infer_strategy_type(prompt: str) -> str:
    lower = (prompt or "").lower()
    if "rsi" in lower:
        return "rsi"
    if "momentum" in lower or "动量" in lower:
        return "momentum"
    return "moving_average"


def _generate_default_parameters(strategy_type: str, prompt: str) -> dict[str, Any]:
    numbers = _extract_numbers(prompt)
    if strategy_type == "rsi":
        period = int(numbers[0]) if len(numbers) >= 1 else 14
        buy = float(numbers[1]) if len(numbers) >= 2 else 30.0
        sell = float(numbers[2]) if len(numbers) >= 3 else 70.0
        return {
            "rsi_period": max(2, period),
            "rsi_buy": max(1.0, min(50.0, buy)),
            "rsi_sell": max(50.0, min(99.0, sell)),
            "allocation_per_trade": 0.25,
            "commission_rate": 0.001,
        }
    if strategy_type == "momentum":
        period = int(numbers[0]) if len(numbers) >= 1 else 10
        threshold = float(numbers[1]) if len(numbers) >= 2 else 0.015
        return {
            "momentum_period": max(2, period),
            "momentum_threshold": max(0.001, min(0.2, threshold)),
            "allocation_per_trade": 0.25,
            "commission_rate": 0.001,
        }
    short_window = int(numbers[0]) if len(numbers) >= 1 else 5
    long_window = int(numbers[1]) if len(numbers) >= 2 else 20
    if long_window <= short_window:
        long_window = short_window + 5
    return {
        "short_window": max(2, short_window),
        "long_window": max(3, long_window),
        "allocation_per_trade": 0.25,
        "commission_rate": 0.001,
    }


def _template_code(strategy_type: str, parameters: dict[str, Any]) -> str:
    if strategy_type == "rsi":
        return (
            "from __future__ import annotations\n\n"
            "def signal(prices: list[float], params: dict) -> str:\n"
            "    period = int(params.get('rsi_period', 14))\n"
            "    buy = float(params.get('rsi_buy', 30))\n"
            "    sell = float(params.get('rsi_sell', 70))\n"
            "    if len(prices) <= period:\n"
            "        return 'HOLD'\n"
            "    window = prices[-(period+1):]\n"
            "    gains = []\n"
            "    losses = []\n"
            "    for i in range(1, len(window)):\n"
            "        delta = window[i] - window[i-1]\n"
            "        gains.append(max(delta, 0.0))\n"
            "        losses.append(max(-delta, 0.0))\n"
            "    avg_gain = sum(gains) / len(gains)\n"
            "    avg_loss = sum(losses) / len(losses)\n"
            "    if avg_loss <= 1e-12:\n"
            "        rsi = 100.0\n"
            "    else:\n"
            "        rs = avg_gain / avg_loss\n"
            "        rsi = 100.0 - (100.0 / (1.0 + rs))\n"
            "    if rsi <= buy:\n"
            "        return 'BUY'\n"
            "    if rsi >= sell:\n"
            "        return 'SELL'\n"
            "    return 'HOLD'\n"
        )
    if strategy_type == "momentum":
        return (
            "from __future__ import annotations\n\n"
            "def signal(prices: list[float], params: dict) -> str:\n"
            "    period = int(params.get('momentum_period', 10))\n"
            "    threshold = float(params.get('momentum_threshold', 0.015))\n"
            "    if len(prices) <= period:\n"
            "        return 'HOLD'\n"
            "    now = prices[-1]\n"
            "    prev = prices[-(period+1)]\n"
            "    change = (now - prev) / prev if prev > 0 else 0.0\n"
            "    if change >= threshold:\n"
            "        return 'BUY'\n"
            "    if change <= -threshold:\n"
            "        return 'SELL'\n"
            "    return 'HOLD'\n"
        )
    return (
        "from __future__ import annotations\n\n"
        "def signal(prices: list[float], params: dict) -> str:\n"
        "    short = int(params.get('short_window', 5))\n"
        "    long = int(params.get('long_window', 20))\n"
        "    if len(prices) < max(short, long):\n"
        "        return 'HOLD'\n"
        "    short_ma = sum(prices[-short:]) / short\n"
        "    long_ma = sum(prices[-long:]) / long\n"
        "    if short_ma > long_ma:\n"
        "        return 'BUY'\n"
        "    if short_ma < long_ma:\n"
        "        return 'SELL'\n"
        "    return 'HOLD'\n"
    )


def generate_strategy_from_prompt(prompt: str) -> GeneratedStrategy:
    strategy_type = _infer_strategy_type(prompt)
    params = _generate_default_parameters(strategy_type, prompt)
    rationale = (
        f"Detected {strategy_type} from prompt. "
        "Parameters were initialized from explicit numbers and bounded defaults."
    )
    return GeneratedStrategy(
        strategy_type=strategy_type,
        parameters=params,
        rationale=rationale,
        code=_template_code(strategy_type, params),
    )


def build_trial_parameters(
    strategy_type: str,
    base_parameters: dict[str, Any],
    parameter_grid: dict[str, list[float | int]],
    max_trials: int,
) -> list[dict[str, Any]]:
    defaults: dict[str, list[float | int]]
    if strategy_type == "rsi":
        defaults = {
            "rsi_period": [10, 14, 20],
            "rsi_buy": [25, 30, 35],
            "rsi_sell": [65, 70, 75],
        }
    elif strategy_type == "momentum":
        defaults = {
            "momentum_period": [5, 10, 20],
            "momentum_threshold": [0.01, 0.015, 0.02],
        }
    else:
        defaults = {
            "short_window": [3, 5, 8],
            "long_window": [15, 20, 30],
        }

    merged = {**defaults, **(parameter_grid or {})}
    keys = list(merged.keys())
    value_lists = [merged[key] for key in keys if merged[key]]
    if not keys or not value_lists:
        return [dict(base_parameters)]

    trials: list[dict[str, Any]] = []
    for values in product(*value_lists):
        candidate = dict(base_parameters)
        for key, value in zip(keys, values):
            candidate[key] = value
        trials.append(candidate)
        if len(trials) >= max_trials:
            break
    return trials


def trial_objective_value(item, objective: str) -> float:
    if objective == "sharpe_ratio":
        return float(item["sharpe_ratio"])
    if objective == "win_rate":
        return float(item["win_rate"])
    if objective == "min_drawdown":
        return -float(item["max_drawdown"])
    return float(item["total_return"])


def build_quantitative_recommendations(backtest: Backtest) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    ret = float(backtest.total_return or 0.0)
    dd = float(backtest.max_drawdown or 0.0)
    sharpe = float(backtest.sharpe_ratio or 0.0)

    if dd > 20:
        results.append(
            {
                "kind": "risk",
                "summary": "Control drawdown",
                "details": "Max drawdown exceeds 20%. Reduce allocation_per_trade and tighten stop rules.",
            }
        )
    if sharpe < 0.8:
        results.append(
            {
                "kind": "quality",
                "summary": "Improve risk-adjusted return",
                "details": "Sharpe ratio is below 0.8. Re-tune signal thresholds and trade frequency.",
            }
        )
    if ret <= 0:
        results.append(
            {
                "kind": "return",
                "summary": "Retune for positive return",
                "details": "Current total return is non-positive. Expand search grid and validate data window.",
            }
        )
    if not results:
        results.append(
            {
                "kind": "stability",
                "summary": "Run robustness checks",
                "details": "Current metrics are healthy. Validate stability across additional time windows.",
            }
        )
    return results


def build_qualitative_recommendations(backtest: Backtest) -> list[dict[str, str]]:
    results = [
        {
            "kind": "process",
            "summary": "Version every material parameter change",
            "details": "Keep strategy snapshots aligned with backtest IDs to preserve reproducibility.",
        },
        {
            "kind": "data",
            "summary": "Monitor data gaps before rerun",
            "details": "Run data health checks before backtests to avoid sparse windows skewing metrics.",
        },
    ]
    if int(backtest.trade_count or 0) <= 2:
        results.append(
            {
                "kind": "coverage",
                "summary": "Increase sample of trades",
                "details": "Trade count is low. Expand backtest window or symbol universe for better significance.",
            }
        )
    return results


def build_report_markdown(backtest: Backtest, trades: list[Trade], recommendations: list[dict[str, str]]) -> str:
    lines = [
        f"# Backtest Report #{backtest.id}",
        "",
        f"- Status: {backtest.status}",
        f"- Total Return: {float(backtest.total_return or 0.0):.4f}%",
        f"- Sharpe Ratio: {float(backtest.sharpe_ratio or 0.0):.4f}",
        f"- Max Drawdown: {float(backtest.max_drawdown or 0.0):.4f}%",
        f"- Win Rate: {float(backtest.win_rate or 0.0):.4f}%",
        f"- Trade Count: {int(backtest.trade_count or 0)}",
        "",
        "## Recommendations",
    ]
    for item in recommendations:
        lines.append(f"- [{item['kind']}] {item['summary']}: {item['details']}")
    lines.append("")
    lines.append("## Recent Trades")
    for trade in trades[:10]:
        lines.append(
            f"- {trade.timestamp}: {trade.symbol} {trade.action} "
            f"qty={trade.quantity:.2f} price={trade.price:.2f} pnl={trade.pnl:.2f}"
        )
    return "\n".join(lines)


def kb_citations(
    db,
    query: str,
    top_k: int,
    *,
    min_score: float = 0.08,
    max_per_document: int = 2,
    allow_fallback: bool = True,
    allowed_source_types: list[str] | None = None,
    blocked_source_keywords: list[str] | None = None,
    preferred_source_types: list[str] | None = None,
    recency_half_life_days: int = 180,
) -> list[dict[str, Any]]:
    hits = search_knowledge_base(
        db,
        query,
        top_k=top_k,
        mode="hybrid",
        min_score=min_score,
        max_per_document=max_per_document,
        allow_fallback=allow_fallback,
        allowed_source_types=allowed_source_types,
        blocked_source_keywords=blocked_source_keywords,
        preferred_source_types=preferred_source_types,
        recency_half_life_days=recency_half_life_days,
    )
    output: list[dict[str, Any]] = []
    for hit in hits:
        output.append(
            {
                "document_id": hit.document.id,
                "source_name": hit.document.source_name,
                "chunk_id": hit.chunk.id,
                "score": float(hit.score),
                "confidence": hit.confidence,
                "reference_id": hit.reference_id,
                "governance_flags": list(hit.governance_flags),
                "snippet": hit.snippet or (hit.chunk.content or "")[:240],
            }
        )
    return output


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
