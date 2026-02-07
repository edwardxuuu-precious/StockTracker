"""Portfolio API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate
from ...models.portfolio import Portfolio, Holding

router = APIRouter()

# Portfolio endpoints


@router.get("/", response_model=List[PortfolioResponse])
async def list_portfolios(db: Session = Depends(get_db)):
    """List all portfolios."""
    portfolios = db.query(Portfolio).all()
    return portfolios


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Get a specific portfolio by ID."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.post("/", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio."""
    # Create portfolio
    db_portfolio = Portfolio(
        name=portfolio.name,
        description=portfolio.description,
        initial_capital=portfolio.initial_capital,
        cash_balance=portfolio.initial_capital,
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)

    # Create holdings if provided
    for holding in portfolio.holdings:
        cost = holding.quantity * holding.average_cost
        db_holding = Holding(
            portfolio_id=db_portfolio.id,
            symbol=holding.symbol,
            quantity=holding.quantity,
            average_cost=holding.average_cost,
            market_value=cost,
            current_price=holding.average_cost,
        )
        db.add(db_holding)
        # Deduct from cash balance
        db_portfolio.cash_balance -= cost

    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """Update a portfolio."""
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Update fields
    if portfolio_update.name is not None:
        db_portfolio.name = portfolio_update.name
    if portfolio_update.description is not None:
        db_portfolio.description = portfolio_update.description
    if portfolio_update.is_active is not None:
        db_portfolio.is_active = portfolio_update.is_active

    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


@router.delete("/{portfolio_id}", status_code=204)
async def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Delete a portfolio."""
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.delete(db_portfolio)
    db.commit()
    return None
