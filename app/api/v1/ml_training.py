"""ML model training API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.stock import Stock
from app.schemas.common import SuccessResponse, Meta
# Optional ML training imports
try:
    from app.ml.training import train_lstm_model, train_classifier_model
    ML_TRAINING_AVAILABLE = True
except ImportError:
    ML_TRAINING_AVAILABLE = False
    def train_lstm_model(*args, **kwargs):
        raise HTTPException(status_code=503, detail="ML training not available. Install TensorFlow: pip install tensorflow")
    def train_classifier_model(*args, **kwargs):
        raise HTTPException(status_code=503, detail="ML training not available. Install TensorFlow: pip install tensorflow")

router = APIRouter()


@router.post("/lstm/train", response_model=SuccessResponse)
def train_lstm(
    symbol: str = Body(..., description="Stock symbol"),
    sequence_length: int = Body(60, description="LSTM sequence length"),
    epochs: int = Body(50, description="Training epochs"),
    db: Session = Depends(get_db),
):
    """
    Train LSTM model for price forecasting.

    Requires sufficient historical data (at least 100+ days).
    """
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    if not ML_TRAINING_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML training not available. Install TensorFlow: pip install tensorflow")
    
    try:
        result = train_lstm_model(
            stock_id=stock.id,
            sequence_length=sequence_length,
            epochs=epochs
        )

        return SuccessResponse(
            data=result,
            meta=Meta(timestamp=datetime.utcnow()),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/classifier/train", response_model=SuccessResponse)
def train_classifier(
    stock_symbols: Optional[List[str]] = Body(None, description="Stock symbols to train on (None = all)"),
    epochs: int = Body(100, description="Training epochs"),
    db: Session = Depends(get_db),
):
    """
    Train signal classifier model.

    Uses historical signal data to learn BUY/HOLD/SELL patterns.
    """
    stock_ids = None
    if stock_symbols:
        stocks = db.query(Stock).filter(Stock.symbol.in_([s.upper() for s in stock_symbols])).all()
        stock_ids = [s.id for s in stocks]
        if not stock_ids:
            raise HTTPException(status_code=404, detail="No stocks found")

    if not ML_TRAINING_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML training not available. Install TensorFlow: pip install tensorflow")
    
    try:
        result = train_classifier_model(
            stock_ids=stock_ids,
            epochs=epochs
        )

        return SuccessResponse(
            data=result,
            meta=Meta(timestamp=datetime.utcnow()),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")
