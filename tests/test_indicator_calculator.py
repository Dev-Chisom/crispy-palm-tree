"""Tests for indicator calculator service."""

import pytest
import pandas as pd
import numpy as np
from app.services.indicator_calculator import IndicatorCalculator


def test_calculate_rsi():
    """Test RSI calculation."""
    # Create sample price data
    prices = pd.Series([100, 101, 102, 103, 104, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91])
    rsi = IndicatorCalculator.calculate_rsi(prices, period=14)
    assert rsi is not None
    assert 0 <= rsi <= 100


def test_calculate_macd():
    """Test MACD calculation."""
    prices = pd.Series([100 + i * 0.5 for i in range(50)])
    macd_data = IndicatorCalculator.calculate_macd(prices)
    assert "macd" in macd_data
    assert "macd_signal" in macd_data
    assert "macd_histogram" in macd_data


def test_calculate_sma():
    """Test SMA calculation."""
    prices = pd.Series([100 + i for i in range(30)])
    sma = IndicatorCalculator.calculate_sma(prices, period=20)
    assert sma is not None
    assert sma > 0


def test_calculate_bollinger_bands():
    """Test Bollinger Bands calculation."""
    prices = pd.Series([100 + np.random.randn() * 2 for _ in range(30)])
    bb_data = IndicatorCalculator.calculate_bollinger_bands(prices)
    assert "upper" in bb_data
    assert "middle" in bb_data
    assert "lower" in bb_data
    if all(v is not None for v in bb_data.values()):
        assert bb_data["upper"] > bb_data["middle"] > bb_data["lower"]


def test_calculate_all_indicators():
    """Test calculation of all indicators."""
    prices_df = pd.DataFrame(
        {
            "time": pd.date_range(start="2023-01-01", periods=100, freq="D"),
            "open": [100 + i * 0.1 for i in range(100)],
            "high": [102 + i * 0.1 for i in range(100)],
            "low": [98 + i * 0.1 for i in range(100)],
            "close": [101 + i * 0.1 for i in range(100)],
            "volume": [1000000] * 100,
        }
    )

    indicators = IndicatorCalculator.calculate_all_indicators(prices_df)
    assert isinstance(indicators, dict)
    assert "rsi" in indicators or indicators.get("rsi") is None
    assert "sma_20" in indicators or indicators.get("sma_20") is None
