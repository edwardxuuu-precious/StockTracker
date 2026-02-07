"""Strategy API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.strategy import Strategy
from ...schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate

router = APIRouter()


@router.get("/", response_model=list[StrategyResponse])
async def list_strategies(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List saved strategies."""
    return (
        db.query(Strategy)
        .order_by(Strategy.created_at.desc(), Strategy.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get one strategy by ID."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


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
    db.commit()
    db.refresh(strategy)
    return strategy


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

    db.commit()
    db.refresh(strategy)
    return strategy
