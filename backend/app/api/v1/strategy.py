"""Strategy API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.backtest import Backtest
from ...models.strategy import Strategy
from ...models.strategy_version import StrategyVersion
from ...schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate
from ...schemas.strategy_version import (
    StrategyVersionCompareItem,
    StrategyVersionCompareRequest,
    StrategyVersionCompareResponse,
    StrategyVersionCreate,
    StrategyVersionResponse,
)

router = APIRouter()


def _next_version_no(db: Session, strategy_id: int) -> int:
    value = (
        db.query(func.max(StrategyVersion.version_no))
        .filter(StrategyVersion.strategy_id == strategy_id)
        .scalar()
    )
    return int(value or 0) + 1


def _create_snapshot(
    db: Session,
    strategy: Strategy,
    *,
    created_by: str = "system",
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
        note=note,
        created_by=created_by,
    )
    db.add(version)
    db.flush()
    return version


def _to_strategy_response(db: Session, strategy: Strategy) -> StrategyResponse:
    latest_version = (
        db.query(func.max(StrategyVersion.version_no))
        .filter(StrategyVersion.strategy_id == strategy.id)
        .scalar()
    )
    payload = StrategyResponse.model_validate(strategy).model_dump()
    payload["latest_version_no"] = int(latest_version) if latest_version is not None else None
    return StrategyResponse(**payload)


@router.get("/", response_model=list[StrategyResponse])
async def list_strategies(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List saved strategies."""
    items = (
        db.query(Strategy)
        .order_by(Strategy.created_at.desc(), Strategy.id.desc())
        .limit(limit)
        .all()
    )
    return [_to_strategy_response(db, item) for item in items]


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get one strategy by ID."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return _to_strategy_response(db, strategy)


@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(payload: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new strategy."""
    strategy = Strategy(
        name=payload.name.strip(),
        description=(payload.description or "").strip() or None,
        strategy_type=payload.strategy_type.strip().lower(),
        parameters=payload.parameters or {},
        code=payload.code,
        created_from_chat=payload.created_from_chat,
    )
    db.add(strategy)
    db.flush()
    _create_snapshot(db, strategy, created_by="create", note="initial version")
    db.commit()
    db.refresh(strategy)
    return _to_strategy_response(db, strategy)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    payload: StrategyUpdate,
    db: Session = Depends(get_db),
):
    """Update a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if payload.name is not None:
        strategy.name = payload.name.strip()
    if payload.description is not None:
        strategy.description = payload.description.strip() or None
    if payload.strategy_type is not None:
        strategy.strategy_type = payload.strategy_type.strip().lower()
    if payload.parameters is not None:
        strategy.parameters = payload.parameters
    if payload.code is not None:
        strategy.code = payload.code

    _create_snapshot(db, strategy, created_by="update", note="updated from API")
    db.commit()
    db.refresh(strategy)
    return _to_strategy_response(db, strategy)


@router.get("/{strategy_id}/versions", response_model=list[StrategyVersionResponse])
async def list_strategy_versions(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return (
        db.query(StrategyVersion)
        .filter(StrategyVersion.strategy_id == strategy_id)
        .order_by(StrategyVersion.version_no.desc())
        .all()
    )


@router.post("/{strategy_id}/versions", response_model=StrategyVersionResponse, status_code=201)
async def create_strategy_version(
    strategy_id: int,
    payload: StrategyVersionCreate,
    db: Session = Depends(get_db),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    version = _create_snapshot(db, strategy, created_by=payload.created_by, note=payload.note)
    db.commit()
    db.refresh(version)
    return version


@router.post("/versions/compare", response_model=StrategyVersionCompareResponse)
async def compare_strategy_versions(
    payload: StrategyVersionCompareRequest,
    db: Session = Depends(get_db),
):
    versions = (
        db.query(StrategyVersion)
        .filter(StrategyVersion.id.in_(payload.version_ids))
        .all()
    )
    found_ids = {item.id for item in versions}
    missing = [item for item in payload.version_ids if item not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"Version IDs not found: {missing}")

    items: list[StrategyVersionCompareItem] = []
    for version in versions:
        # Backtest records may or may not be explicitly linked by strategy_version_id.
        rows = (
            db.query(Backtest)
            .filter(Backtest.strategy_version_id == version.id, Backtest.status == "completed")
            .all()
        )
        best_total = max((float(item.total_return or 0.0) for item in rows), default=None)
        best_sharpe = max((float(item.sharpe_ratio or 0.0) for item in rows), default=None)
        latest = max((item.completed_at for item in rows if item.completed_at), default=None)
        items.append(
            StrategyVersionCompareItem(
                version=StrategyVersionResponse.model_validate(version),
                backtest_count=len(rows),
                best_total_return=best_total,
                best_sharpe_ratio=best_sharpe,
                latest_completed_at=latest,
            )
        )
    items.sort(key=lambda item: item.version.version_no, reverse=True)
    return StrategyVersionCompareResponse(items=items)
