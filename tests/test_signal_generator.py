"""Tests for signal generator service."""

import pytest
import pandas as pd
from app.services.signal_generator import SignalGenerator
from app.models.signal import SignalType, RiskLevel, HoldingPeriod


def test_calculate_technical_score():
    """Test technical score calculation."""
    indicators = {
        "rsi": 35,
        "macd": 0.5,
        "macd_signal": 0.3,
        "macd_histogram": 0.2,
        "sma_20": 100,
        "sma_50": 95,
        "sma_200": 90,
        "bollinger_upper": 110,
        "bollinger_lower": 90,
    }
    current_price = 105

    result = SignalGenerator.calculate_technical_score(indicators, current_price)
    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert "factors" in result


def test_generate_signal():
    """Test signal generation."""
    indicators = {
        "rsi": 45,
        "macd": 0.5,
        "macd_signal": 0.3,
        "macd_histogram": 0.2,
        "sma_20": 100,
        "sma_50": 95,
        "sma_200": 90,
        "bollinger_upper": 110,
        "bollinger_lower": 90,
        "volume_avg": 1000000,
        "current_volume": 1200000,
    }

    fundamentals = {
        "pe_ratio": 20,
        "earnings_growth": 15,
        "debt_ratio": 30,
    }

    # Create sample price data
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    prices_df = pd.DataFrame(
        {
            "time": dates,
            "open": [100 + i * 0.1 for i in range(100)],
            "high": [102 + i * 0.1 for i in range(100)],
            "low": [98 + i * 0.1 for i in range(100)],
            "close": [101 + i * 0.1 for i in range(100)],
            "volume": [1000000] * 100,
        }
    )

    result = SignalGenerator.generate_signal(
        indicators=indicators,
        fundamentals=fundamentals,
        prices_df=prices_df,
    )

    assert "signal_type" in result
    assert result["signal_type"] in [SignalType.BUY, SignalType.HOLD, SignalType.SELL, SignalType.NO_SIGNAL]
    assert "confidence_score" in result
    assert 0 <= result["confidence_score"] <= 100
    assert "risk_level" in result
    assert result["risk_level"] in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
    assert "holding_period" in result
    assert result["holding_period"] in [HoldingPeriod.SHORT, HoldingPeriod.MEDIUM, HoldingPeriod.LONG]
    assert "explanation" in result
