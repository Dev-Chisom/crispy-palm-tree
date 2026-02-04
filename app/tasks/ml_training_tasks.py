"""Automated ML training Celery tasks."""

import os
from datetime import datetime
from celery.schedules import crontab
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.stock import Stock

# Optional ML imports
try:
    from app.ml.training import train_lstm_model, train_classifier_model
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    train_lstm_model = None
    train_classifier_model = None


@celery_app.task(name="train_lstm_for_stock", bind=True, max_retries=3)
def train_lstm_for_stock(self, stock_id: int, sequence_length: int = 60, epochs: int = 50):
    """
    Train LSTM model for a specific stock.
    
    Args:
        stock_id: Stock ID to train model for
        sequence_length: LSTM sequence length
        epochs: Number of training epochs
        
    Returns:
        Training results dictionary
    """
    try:
        db = SessionLocal()
        try:
            stock = db.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                return {"status": "error", "message": f"Stock {stock_id} not found"}
            
            # Check if stock has sufficient price data
            from app.models.price import StockPrice
            price_count = db.query(StockPrice).filter(StockPrice.stock_id == stock_id).count()
            if price_count < 100:
                return {
                    "status": "skipped",
                    "message": f"Insufficient price data: {price_count} records (need 100+)",
                    "stock_id": stock_id,
                    "stock_symbol": stock.symbol,
                }
            
            # Train model
            if not ML_AVAILABLE or train_lstm_model is None:
                return {
                    "status": "error",
                    "message": "ML training not available. TensorFlow is not installed.",
                    "stock_id": stock_id,
                }
            
            result = train_lstm_model(
                stock_id=stock_id,
                sequence_length=sequence_length,
                epochs=epochs,
                model_save_path=f"models/lstm_{stock.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
            )
            
            return {
                "status": "success",
                "stock_id": stock_id,
                "stock_symbol": stock.symbol,
                "model_path": result["model_path"],
                "final_loss": result["final_loss"],
                "final_val_loss": result.get("final_val_loss"),
                "epochs": epochs,
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()
    except Exception as e:
        # Retry on failure
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@celery_app.task(name="train_classifier_model_task", bind=True, max_retries=3)
def train_classifier_model_task(self, stock_ids: list = None, epochs: int = 100):
    """
    Train signal classifier model for all stocks or specified stocks.
    
    Args:
        stock_ids: List of stock IDs (None = all stocks with sufficient data)
        epochs: Number of training epochs
        
    Returns:
        Training results dictionary
    """
    try:
        db = SessionLocal()
        try:
            # Check if we have sufficient signal history
            from app.models.signal import SignalHistory
            signal_count = db.query(SignalHistory).count()
            if signal_count < 100:
                return {
                    "status": "skipped",
                    "message": f"Insufficient signal history: {signal_count} records (need 100+)",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Train model
            if not ML_AVAILABLE or train_classifier_model is None:
                return {
                    "status": "error",
                    "message": "ML training not available. TensorFlow is not installed.",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            result = train_classifier_model(
                stock_ids=stock_ids,
                epochs=epochs,
                model_save_path=f"models/classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
            )
            
            return {
                "status": "success",
                "model_path": result["model_path"],
                "training_samples": result["training_samples"],
                "final_accuracy": result["final_accuracy"],
                "final_val_accuracy": result.get("final_val_accuracy"),
                "epochs": epochs,
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()
    except Exception as e:
        # Retry on failure
        raise self.retry(exc=e, countdown=600)  # Retry after 10 minutes


@celery_app.task(name="train_lstm_for_all_stocks")
def train_lstm_for_all_stocks(sequence_length: int = 60, epochs: int = 50):
    """
    Train LSTM models for all active stocks with sufficient data.
    Runs weekly on Sunday at 2 AM UTC.
    
    Args:
        sequence_length: LSTM sequence length
        epochs: Number of training epochs
        
    Returns:
        Summary of training results
    """
    db = SessionLocal()
    try:
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        results = []
        
        for stock in stocks:
            try:
                result = train_lstm_for_stock.delay(stock.id, sequence_length, epochs)
                results.append({
                    "stock_id": stock.id,
                    "stock_symbol": stock.symbol,
                    "task_id": result.id,
                })
            except Exception as e:
                results.append({
                    "stock_id": stock.id,
                    "stock_symbol": stock.symbol,
                    "error": str(e),
                })
        
        return {
            "status": "success",
            "stocks_queued": len(stocks),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="retrain_classifier_model")
def retrain_classifier_model(epochs: int = 100):
    """
    Retrain the signal classifier model with latest data.
    Runs weekly on Sunday at 3 AM UTC.
    
    Args:
        epochs: Number of training epochs
        
    Returns:
        Training results
    """
    try:
        result = train_classifier_model_task.delay(stock_ids=None, epochs=epochs)
        return {
            "status": "queued",
            "task_id": result.id,
            "message": "Classifier training task queued",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
