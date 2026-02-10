"""Agent APIs for strategy generation, tuning, and reporting."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...models.backtest import Backtest, Trade
from ...models.strategy import Strategy
from ...models.strategy_version import StrategyVersion
from ...schemas.agent import (
    AgentCitation,
    AgentGenerateRequest,
    AgentGenerateResponse,
    AgentHealthResponse,
    AgentRecommendation,
    AgentReportRequest,
    AgentReportResponse,
    AgentTuneRequest,
    AgentTuneResponse,
    AgentTuneTrial,
)
from ...schemas.backtest import BacktestCreate
from ...schemas.strategy import StrategyResponse
from ...services.llm_service import (
    LLMUnavailableError,
    llm_runtime_info,
    probe_llm_connection,
)
from ...services.agent_service import (
    build_ai_backtest_insights,
    build_qualitative_recommendations,
    build_quantitative_recommendations,
    build_report_markdown,
    build_trial_parameters,
    generate_strategy_from_prompt,
    kb_citations,
    now_utc,
    trial_objective_value,
)
from ...services.knowledge_base import resolve_governance_policy
from .backtest import run_backtest

router = APIRouter()


def _next_version_no(db: Session, strategy_id: int) -> int:
    value = (
        db.query(StrategyVersion.version_no)
        .filter(StrategyVersion.strategy_id == strategy_id)
        .order_by(StrategyVersion.version_no.desc())
        .first()
    )
    return int(value[0]) + 1 if value else 1


def _snapshot_strategy(
    db: Session,
    strategy: Strategy,
    *,
    created_by: str,
    note: str | None = None,
) -> StrategyVersion:
    version = StrategyVersion(
        strategy_id=strategy.id,
        version_no=_next_version_no(db, strategy.id),
        name=strategy.name,
        description=strategy.description,
        strategy_type=strategy.strategy_type,
        parameters=strategy.parameters or {},
        code=strategy.code,
        created_by=created_by,
        note=note,
    )
    db.add(version)
    db.flush()
    return version


@router.get("/health", response_model=AgentHealthResponse)
async def agent_health(probe: bool = Query(default=False)):
    """Expose LLM readiness for agent flows.

    probe=false: config-only check
    probe=true: perform a real lightweight provider call
    """
    settings = get_settings()
    info = llm_runtime_info()
    llm_required = bool(settings.AGENT_REQUIRE_LLM)

    reachable: bool | None = None
    detail = "llm config is present" if info["configured"] else "llm config is missing"
    if probe:
        reachable, detail = probe_llm_connection()

    ok = bool(info["configured"])
    if probe and reachable is not None:
        ok = ok and bool(reachable)
    if not llm_required:
        ok = True

    payload = AgentHealthResponse(
        ok=ok,
        llm_required=llm_required,
        provider=str(info["provider"]),
        model=str(info["model"]),
        base_url=str(info["base_url"]),
        configured=bool(info["configured"]),
        reachable=reachable,
        detail=detail,
        checked_at=now_utc(),
    )
    return JSONResponse(
        status_code=200 if payload.ok else 503,
        content=payload.model_dump(mode="json"),
    )


@router.post("/strategy/generate", response_model=AgentGenerateResponse)
async def generate_strategy(payload: AgentGenerateRequest, db: Session = Depends(get_db)):
    try:
        generated = generate_strategy_from_prompt(payload.prompt)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    strategy_response: StrategyResponse | None = None

    if payload.save_strategy:
        strategy = Strategy(
            name=(payload.name or f"Agent {generated.strategy_type} strategy").strip(),
            description=f"Generated from prompt: {payload.prompt[:120]}",
            strategy_type=generated.strategy_type,
            parameters=generated.parameters,
            code=generated.code,
            created_from_chat=True,
        )
        db.add(strategy)
        db.flush()
        _snapshot_strategy(db, strategy, created_by="agent", note="generated from prompt")
        db.commit()
        db.refresh(strategy)
        strategy_response = StrategyResponse.model_validate(strategy)

    return AgentGenerateResponse(
        detected_strategy_type=generated.strategy_type,
        parameters=generated.parameters,
        rationale=generated.rationale,
        code=generated.code,
        strategy=strategy_response,
    )


@router.post("/strategy/tune", response_model=AgentTuneResponse)
async def tune_strategy(payload: AgentTuneRequest, db: Session = Depends(get_db)):
    if payload.start_date > payload.end_date:
        raise HTTPException(status_code=400, detail="start_date must be earlier than or equal to end_date")

    strategy = db.query(Strategy).filter(Strategy.id == payload.strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    base_parameters = dict(strategy.parameters or {})
    if payload.strategy_version_id is not None:
        version = db.query(StrategyVersion).filter(StrategyVersion.id == payload.strategy_version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="Strategy version not found")
        if version.strategy_id != strategy.id:
            raise HTTPException(status_code=400, detail="strategy_version_id does not belong to strategy_id")
        base_parameters = dict(version.parameters or {})

    base_parameters.setdefault("interval", payload.interval)
    if payload.market:
        base_parameters.setdefault("market", payload.market.upper())

    trials = build_trial_parameters(
        strategy_type=strategy.strategy_type,
        base_parameters=base_parameters,
        parameter_grid=payload.parameter_grid,
        max_trials=payload.max_trials,
    )
    if not trials:
        raise HTTPException(status_code=400, detail="No parameter trials generated")

    trial_results: list[dict] = []
    for idx, params in enumerate(trials, start=1):
        backtest = await run_backtest(
            BacktestCreate(
                strategy_id=payload.strategy_id,
                strategy_version_id=payload.strategy_version_id,
                portfolio_id=None,
                symbols=payload.symbols,
                start_date=payload.start_date,
                end_date=payload.end_date,
                initial_capital=payload.initial_capital,
                parameters=params,
            ),
            db=db,
        )
        trial_results.append(
            {
                "trial_no": idx,
                "parameters": params,
                "backtest_id": backtest.id,
                "total_return": float(backtest.total_return or 0.0),
                "sharpe_ratio": float(backtest.sharpe_ratio or 0.0),
                "max_drawdown": float(backtest.max_drawdown or 0.0),
                "win_rate": float(backtest.win_rate or 0.0),
            }
        )

    trial_results.sort(key=lambda item: trial_objective_value(item, payload.objective), reverse=True)
    top_items = trial_results[: payload.top_k]
    best_item = top_items[0]

    created_version_id = None
    if payload.persist_best_version:
        strategy.parameters = dict(best_item["parameters"])
        snapshot = _snapshot_strategy(db, strategy, created_by="agent", note="best params from tune")
        db.commit()
        created_version_id = snapshot.id

    return AgentTuneResponse(
        objective=payload.objective,
        best_trial=AgentTuneTrial(**best_item),
        top_trials=[AgentTuneTrial(**item) for item in top_items],
        created_version_id=created_version_id,
    )


@router.post("/backtests/{backtest_id}/report", response_model=AgentReportResponse)
async def build_backtest_report(
    backtest_id: int,
    payload: AgentReportRequest,
    db: Session = Depends(get_db),
):
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    trades = (
        db.query(Trade)
        .filter(Trade.backtest_id == backtest_id)
        .order_by(Trade.timestamp.desc(), Trade.id.desc())
        .limit(20)
        .all()
    )

    quant = build_quantitative_recommendations(backtest)
    qual = build_qualitative_recommendations(backtest)
    all_recs = quant + qual

    kb_query = payload.question or f"strategy {backtest.strategy_id} backtest improvement"
    settings = get_settings()
    citation_policy = resolve_governance_policy(
        payload.citation_policy_profile or settings.KB_POLICY_PROFILE
    )
    citations_raw = kb_citations(
        db,
        kb_query,
        top_k=payload.top_k_sources,
        min_score=(
            payload.min_citation_score
            if payload.min_citation_score is not None
            else citation_policy.min_score
        ),
        max_per_document=citation_policy.max_per_document,
        allow_fallback=(
            payload.allow_citation_fallback
            if payload.allow_citation_fallback is not None
            else citation_policy.allow_fallback
        ),
        allowed_source_types=(
            payload.allowed_source_types
            if payload.allowed_source_types is not None
            else settings.KB_ALLOWED_SOURCE_TYPES
        ),
        blocked_source_keywords=(
            payload.blocked_source_keywords
            if payload.blocked_source_keywords is not None
            else settings.KB_BLOCKED_SOURCE_KEYWORDS
        ),
        preferred_source_types=settings.KB_PREFERRED_SOURCE_TYPES,
        recency_half_life_days=settings.KB_RECENCY_HALF_LIFE_DAYS,
    )
    citations = [AgentCitation(**item) for item in citations_raw]

    markdown = build_report_markdown(backtest, trades, all_recs)
    try:
        ai_insights = build_ai_backtest_insights(backtest, trades, payload.question)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if ai_insights:
        markdown += f"\n\n{ai_insights}\n"
    if citations:
        markdown += "\n\n## Evidence\n"
        for item in citations:
            flags = ",".join(item.governance_flags) if item.governance_flags else "ok"
            markdown += (
                f"- [{item.source_name}#{item.chunk_id}] "
                f"score={item.score:.4f} confidence={item.confidence} flags={flags} {item.snippet}\n"
            )

    return AgentReportResponse(
        backtest_id=backtest.id,
        generated_at=now_utc(),
        markdown=markdown,
        quantitative_recommendations=[AgentRecommendation(**item) for item in quant],
        qualitative_recommendations=[AgentRecommendation(**item) for item in qual],
        citations=citations,
    )
