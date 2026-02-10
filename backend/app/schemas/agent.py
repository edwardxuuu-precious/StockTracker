"""Schemas for strategy agent operations."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .strategy import StrategyResponse


class AgentGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    name: str | None = None
    save_strategy: bool = True


class AgentGenerateResponse(BaseModel):
    detected_strategy_type: str
    parameters: dict[str, Any]
    rationale: str
    code: str
    strategy: StrategyResponse | None = None


class AgentTuneRequest(BaseModel):
    strategy_id: int = Field(..., gt=0)
    strategy_version_id: int | None = Field(default=None, gt=0)
    symbols: list[str] = Field(..., min_length=1, max_length=20)
    start_date: date
    end_date: date
    initial_capital: float = Field(..., gt=0)
    market: str | None = None
    interval: str = "1d"
    objective: str = Field(default="total_return")
    top_k: int = Field(default=5, ge=1, le=20)
    max_trials: int = Field(default=30, ge=1, le=200)
    parameter_grid: dict[str, list[float | int]] = Field(default_factory=dict)
    persist_best_version: bool = False


class AgentTuneTrial(BaseModel):
    trial_no: int
    parameters: dict[str, Any]
    backtest_id: int
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float


class AgentTuneResponse(BaseModel):
    objective: str
    best_trial: AgentTuneTrial
    top_trials: list[AgentTuneTrial]
    created_version_id: int | None = None


class AgentReportRequest(BaseModel):
    question: str | None = None
    top_k_sources: int = Field(default=3, ge=1, le=10)
    citation_policy_profile: Literal["strict", "balanced", "recall"] | None = None
    min_citation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    allow_citation_fallback: bool | None = None
    allowed_source_types: list[str] | None = None
    blocked_source_keywords: list[str] | None = None


class AgentRecommendation(BaseModel):
    kind: str
    summary: str
    details: str


class AgentCitation(BaseModel):
    document_id: int
    source_name: str
    chunk_id: int
    score: float
    confidence: str = "low"
    reference_id: str | None = None
    governance_flags: list[str] = Field(default_factory=list)
    snippet: str


class AgentReportResponse(BaseModel):
    backtest_id: int
    generated_at: datetime
    markdown: str
    quantitative_recommendations: list[AgentRecommendation]
    qualitative_recommendations: list[AgentRecommendation]
    citations: list[AgentCitation]


class AgentHealthResponse(BaseModel):
    ok: bool
    llm_required: bool
    provider: str
    model: str
    base_url: str
    configured: bool
    reachable: bool | None = None
    detail: str
    checked_at: datetime
