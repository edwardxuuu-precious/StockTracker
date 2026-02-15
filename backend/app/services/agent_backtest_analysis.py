"""Agent helpers for tuning analysis, citations, and report content."""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import product
from typing import Any

from ..models.backtest import Backtest, Trade
from ..services.knowledge_base import search_knowledge_base
from .llm_service import chat_text_with_metadata


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
    elif strategy_type == "moving_average":
        defaults = {
            "short_window": [3, 5, 8],
            "long_window": [15, 20, 30],
        }
    else:
        defaults = {}

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


def build_ai_backtest_insights(
    backtest: Backtest,
    trades: list[Trade],
    question: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Generate additional report insights with LLM and return call metadata."""
    user_prompt = (
        "You are reviewing a strategy backtest. "
        "Give concise, practical advice in markdown.\n\n"
        f"Backtest metrics:\n"
        f"- total_return: {float(backtest.total_return or 0.0):.4f}%\n"
        f"- sharpe_ratio: {float(backtest.sharpe_ratio or 0.0):.4f}\n"
        f"- max_drawdown: {float(backtest.max_drawdown or 0.0):.4f}%\n"
        f"- win_rate: {float(backtest.win_rate or 0.0):.4f}%\n"
        f"- trade_count: {int(backtest.trade_count or 0)}\n"
        f"- latest_trades: {[{'symbol': t.symbol, 'action': t.action, 'pnl': round(float(t.pnl), 4)} for t in trades[:10]]}\n"
        f"- user_focus: {question or 'general optimization'}\n\n"
        "Output sections:\n"
        "## AI Insights\n"
        "## Optimization Ideas\n"
        "## Risk Notes\n"
    )
    return chat_text_with_metadata(
        system_prompt="You are a senior quant analyst. Be concrete and non-promotional.",
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=800,
    )


def build_fallback_ai_backtest_insights(
    backtest: Backtest,
    trades: list[Trade],
    recommendations: list[dict[str, str]],
    *,
    reason: str | None = None,
) -> str:
    """Build deterministic fallback text when LLM insights are unavailable."""
    lines = [
        "## AI Insights (Fallback)",
        "LLM insights are temporarily unavailable. The system generated a deterministic report from backtest metrics.",
        "",
        "## Optimization Ideas",
    ]
    for item in recommendations[:4]:
        lines.append(f"- {item['summary']}: {item['details']}")

    lines.extend(
        [
            "",
            "## Risk Notes",
            f"- Max drawdown: {float(backtest.max_drawdown or 0.0):.4f}%",
            f"- Sharpe ratio: {float(backtest.sharpe_ratio or 0.0):.4f}",
            f"- Trade count: {int(backtest.trade_count or 0)}",
            f"- Recent trades reviewed: {min(len(trades), 10)}",
        ]
    )
    if reason:
        lines.append(f"- Fallback reason: {reason}")
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
