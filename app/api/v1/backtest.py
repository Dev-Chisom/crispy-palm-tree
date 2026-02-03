"""Backtesting API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models.stock import Stock
from app.schemas.common import SuccessResponse, Meta
from app.services.backtest import BacktestService

router = APIRouter()


@router.get("/{symbol}/backtest", response_model=SuccessResponse)
def get_backtest_performance(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date (default: 1 year ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: today)"),
    db: Session = Depends(get_db),
):
    """
    Get backtest performance metrics for a stock.

    Simulates following AI signals and calculates:
    - Total return
    - Win rate
    - Drawdown
    - Volatility
    - Sharpe ratio
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Default to 1 year if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    try:
        performance = BacktestService.calculate_signal_performance(
            stock_id=stock.id,
            start_date=start_date,
            end_date=end_date,
            db=db,
        )

        return SuccessResponse(
            data=performance,
            meta=Meta(timestamp=datetime.utcnow()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating backtest: {str(e)}")


@router.post("/run", response_model=SuccessResponse)
def run_backtest(
    symbol: str = Body(..., description="Stock symbol"),
    start_date: date = Body(..., description="Start date"),
    end_date: date = Body(..., description="End date"),
    benchmark_return: Optional[float] = Body(None, description="Benchmark return percentage for comparison"),
    db: Session = Depends(get_db),
):
    """
    Run a backtest for a specific date range.

    Optionally compare against a benchmark (e.g., S&P 500 return).
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    try:
        if benchmark_return is not None:
            result = BacktestService.compare_to_benchmark(
                stock_id=stock.id,
                start_date=start_date,
                end_date=end_date,
                benchmark_return=benchmark_return,
                db=db,
            )
        else:
            result = BacktestService.calculate_signal_performance(
                stock_id=stock.id,
                start_date=start_date,
                end_date=end_date,
                db=db,
            )

        return SuccessResponse(
            data=result,
            meta=Meta(timestamp=datetime.utcnow()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")
