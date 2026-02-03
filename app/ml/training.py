"""Training pipelines for ML models."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.stock import Stock
from app.models.price import StockPrice
from app.models.signal import SignalHistory, SignalType
from app.models.technical_indicator import TechnicalIndicator
from app.models.fundamental import Fundamental
from app.ml.models import LSTMForecaster, SignalClassifier


def prepare_training_data_for_lstm(
    stock_id: int,
    lookback_days: int = 365,
    db: Session = None
) -> pd.DataFrame:
    """
    Prepare price data for LSTM training.

    Args:
        stock_id: Stock ID
        lookback_days: Number of days to look back
        db: Database session

    Returns:
        DataFrame with OHLCV data
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        prices = (
            db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock_id,
                StockPrice.time >= start_date,
                StockPrice.time <= end_date
            )
            .order_by(StockPrice.time.asc())
            .all()
        )

        if len(prices) < 100:
            raise ValueError(f"Insufficient data: {len(prices)} records")

        df = pd.DataFrame([
            {
                'time': p.time,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume,
            }
            for p in prices
        ])

        return df
    finally:
        if should_close:
            db.close()


def prepare_training_data_for_classifier(
    stock_ids: List[int] = None,
    min_history_days: int = 30,
    db: Session = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare training data for signal classifier.

    Args:
        stock_ids: List of stock IDs (None = all stocks)
        min_history_days: Minimum days of history required
        db: Database session

    Returns:
        Tuple of (X features, y labels one-hot encoded)
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # Get all signal history with sufficient data
        query = db.query(SignalHistory).join(Stock)
        if stock_ids:
            query = query.filter(SignalHistory.stock_id.in_(stock_ids))

        signals = query.order_by(SignalHistory.created_at.asc()).all()

        X_features = []
        y_labels = []

        for signal in signals:
            # Get indicators at signal time
            signal_date = signal.created_at.date()
            indicator = (
                db.query(TechnicalIndicator)
                .filter(
                    TechnicalIndicator.stock_id == signal.stock_id,
                    TechnicalIndicator.date <= signal_date
                )
                .order_by(TechnicalIndicator.date.desc())
                .first()
            )

            fundamental = (
                db.query(Fundamental)
                .filter(
                    Fundamental.stock_id == signal.stock_id,
                    Fundamental.date <= signal_date
                )
                .order_by(Fundamental.date.desc())
                .first()
            )

            # Get price data for trend calculation
            prices = (
                db.query(StockPrice)
                .filter(
                    StockPrice.stock_id == signal.stock_id,
                    StockPrice.time <= signal.created_at
                )
                .order_by(StockPrice.time.desc())
                .limit(200)
                .all()
            )

            if not indicator or len(prices) < 20:
                continue

            # Prepare features
            indicators_dict = {
                'rsi': indicator.rsi,
                'macd': indicator.macd,
                'macd_histogram': indicator.macd_histogram,
                'sma_20': indicator.sma_20,
                'sma_50': indicator.sma_50,
                'sma_200': indicator.sma_200,
                'bollinger_upper': indicator.bollinger_upper,
                'bollinger_lower': indicator.bollinger_lower,
            }

            fundamentals_dict = {}
            if fundamental:
                fundamentals_dict = {
                    'pe_ratio': fundamental.pe_ratio,
                    'earnings_growth': fundamental.earnings_growth,
                    'debt_ratio': fundamental.debt_ratio,
                }

            # Calculate price features
            prices_df = pd.DataFrame([
                {'close': p.close, 'volume': p.volume}
                for p in reversed(prices)
            ])

            if len(prices_df) < 20:
                continue

            # Calculate trends
            short_term = 0
            medium_term = 0
            if len(prices_df) >= 20:
                short_term = ((prices_df['close'].iloc[-1] - prices_df['close'].iloc[-20]) / prices_df['close'].iloc[-20]) * 100
            if len(prices_df) >= 50:
                medium_term = ((prices_df['close'].iloc[-1] - prices_df['close'].iloc[-50]) / prices_df['close'].iloc[-50]) * 100

            volatility = prices_df['close'].pct_change().std() * 100 if len(prices_df) > 1 else 20
            volume_avg = prices_df['volume'].mean()
            current_volume = prices_df['volume'].iloc[-1]
            volume_ratio = current_volume / volume_avg if volume_avg > 0 else 1

            price_features = {
                'short_term_trend': short_term,
                'medium_term_trend': medium_term,
                'volatility': volatility,
                'volume_ratio': volume_ratio,
            }

            # Create feature vector
            classifier = SignalClassifier()
            features = classifier.prepare_features(indicators_dict, fundamentals_dict, price_features)
            X_features.append(features[0])

            # Create label (one-hot: BUY=[1,0,0], HOLD=[0,1,0], SELL=[0,0,1])
            signal_map = {'BUY': [1, 0, 0], 'HOLD': [0, 1, 0], 'SELL': [0, 0, 1]}
            label = signal_map.get(signal.signal_type.value, [0, 1, 0])
            y_labels.append(label)

        if len(X_features) == 0:
            raise ValueError("No training data prepared")

        return np.array(X_features), np.array(y_labels)
    finally:
        if should_close:
            db.close()


def train_lstm_model(
    stock_id: int,
    sequence_length: int = 60,
    epochs: int = 50,
    model_save_path: str = None
) -> Dict[str, Any]:
    """
    Train LSTM model for a specific stock.

    Args:
        stock_id: Stock ID
        sequence_length: LSTM sequence length
        epochs: Training epochs
        model_save_path: Path to save model

    Returns:
        Training results
    """
    db = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise ValueError(f"Stock {stock_id} not found")

        # Prepare data
        prices_df = prepare_training_data_for_lstm(stock_id, lookback_days=365, db=db)

        # Train model
        forecaster = LSTMForecaster(sequence_length=sequence_length)
        forecaster.build_model()
        history = forecaster.train(prices_df, epochs=epochs, verbose=0)

        # Save model
        if model_save_path is None:
            model_save_path = f"models/lstm_{stock.symbol}_{datetime.now().strftime('%Y%m%d')}.h5"
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
        forecaster.save(model_save_path)

        return {
            'stock_id': stock_id,
            'stock_symbol': stock.symbol,
            'model_path': model_save_path,
            'final_loss': history['loss'][-1],
            'final_val_loss': history['val_loss'][-1] if 'val_loss' in history else None,
            'epochs': epochs,
        }
    finally:
        db.close()


def train_classifier_model(
    stock_ids: List[int] = None,
    epochs: int = 100,
    model_save_path: str = None
) -> Dict[str, Any]:
    """
    Train signal classifier model.

    Args:
        stock_ids: List of stock IDs (None = all stocks)
        epochs: Training epochs
        model_save_path: Path to save model

    Returns:
        Training results
    """
    db = SessionLocal()
    try:
        # Prepare data
        X, y = prepare_training_data_for_classifier(stock_ids=stock_ids, db=db)

        # Train model
        classifier = SignalClassifier()
        history = classifier.train(X, y, epochs=epochs, verbose=0)

        # Save model
        if model_save_path is None:
            model_save_path = f"models/classifier_{datetime.now().strftime('%Y%m%d')}.h5"
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
        classifier.save(model_save_path)

        return {
            'model_path': model_save_path,
            'training_samples': len(X),
            'final_accuracy': history['accuracy'][-1],
            'final_val_accuracy': history['val_accuracy'][-1] if 'val_accuracy' in history else None,
            'epochs': epochs,
        }
    finally:
        db.close()
