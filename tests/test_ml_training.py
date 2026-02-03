"""Tests for ML training functionality."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
from app.models.stock import Stock, Market, AssetType
from app.models.price import StockPrice
from app.models.signal import SignalHistory, SignalType
from app.ml.training import (
    prepare_training_data_for_lstm,
    prepare_training_data_for_classifier,
    train_lstm_model,
    train_classifier_model,
)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_stock_with_prices(db_session):
    """Create a stock with price data."""
    stock = Stock(
        symbol="TEST",
        name="Test Stock",
        market=Market.US,
        asset_type=AssetType.STOCK,
        currency="USD",
        is_active=True,
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    
    # Add price data (200 days)
    base_date = datetime.utcnow() - timedelta(days=200)
    prices = []
    for i in range(200):
        date = base_date + timedelta(days=i)
        price = StockPrice(
            stock_id=stock.id,
            time=date,
            open=100.0 + i * 0.1,
            high=101.0 + i * 0.1,
            low=99.0 + i * 0.1,
            close=100.5 + i * 0.1,
            volume=1000000,
        )
        prices.append(price)
    
    db_session.add_all(prices)
    db_session.commit()
    
    return stock


def test_prepare_training_data_for_lstm(sample_stock_with_prices):
    """Test preparing LSTM training data."""
    db = SessionLocal()
    try:
        prices_df = prepare_training_data_for_lstm(
            stock_id=sample_stock_with_prices.id,
            lookback_days=365,
            db=db,
        )
        
        assert isinstance(prices_df, pd.DataFrame)
        assert len(prices_df) >= 100
        assert "open" in prices_df.columns
        assert "high" in prices_df.columns
        assert "low" in prices_df.columns
        assert "close" in prices_df.columns
        assert "volume" in prices_df.columns
    finally:
        db.close()


def test_prepare_training_data_for_lstm_insufficient_data(db_session):
    """Test LSTM data preparation with insufficient data."""
    stock = Stock(
        symbol="INSUFFICIENT",
        name="Insufficient Data",
        market=Market.US,
        asset_type=AssetType.STOCK,
        currency="USD",
        is_active=True,
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    
    db = SessionLocal()
    try:
        with pytest.raises(ValueError, match="Insufficient data"):
            prepare_training_data_for_lstm(stock_id=stock.id, db=db)
    finally:
        db.close()


def test_prepare_training_data_for_classifier_insufficient_data(db_session):
    """Test classifier data preparation with insufficient signal history."""
    db = SessionLocal()
    try:
        with pytest.raises(ValueError, match="No training data prepared"):
            prepare_training_data_for_classifier(db=db)
    finally:
        db.close()


@pytest.mark.skip(reason="Requires TensorFlow and trained models")
def test_train_lstm_model(sample_stock_with_prices):
    """Test training LSTM model."""
    result = train_lstm_model(
        stock_id=sample_stock_with_prices.id,
        sequence_length=60,
        epochs=5,  # Small for testing
    )
    
    assert result["status"] == "success"
    assert "model_path" in result
    assert "final_loss" in result


@pytest.mark.skip(reason="Requires TensorFlow and trained models")
def test_train_classifier_model(sample_stock_with_prices):
    """Test training classifier model."""
    # This would need signal history to work
    # For now, just test the function exists
    assert callable(train_classifier_model)
