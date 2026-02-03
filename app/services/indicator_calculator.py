"""Technical indicator calculator service."""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from datetime import date


class IndicatorCalculator:
    """Service for calculating technical indicators."""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: Series of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi.iloc[-1])
        except Exception:
            return None

    @staticmethod
    def calculate_macd(
        prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, Optional[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: Series of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Dictionary with macd, macd_signal, and macd_histogram
        """
        if len(prices) < slow + signal:
            return {"macd": None, "macd_signal": None, "macd_histogram": None}

        try:
            ema_fast = prices.ewm(span=fast, adjust=False).mean()
            ema_slow = prices.ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line

            return {
                "macd": float(macd_line.iloc[-1]),
                "macd_signal": float(signal_line.iloc[-1]),
                "macd_histogram": float(histogram.iloc[-1]),
            }
        except Exception:
            return {"macd": None, "macd_signal": None, "macd_histogram": None}

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average.

        Args:
            prices: Series of closing prices
            period: SMA period

        Returns:
            SMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        try:
            return float(prices.rolling(window=period).mean().iloc[-1])
        except Exception:
            return None

    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> Optional[float]:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: Series of closing prices
            period: EMA period

        Returns:
            EMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        try:
            return float(prices.ewm(span=period, adjust=False).mean().iloc[-1])
        except Exception:
            return None

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> Dict[str, Optional[float]]:
        """
        Calculate Bollinger Bands.

        Args:
            prices: Series of closing prices
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Dictionary with upper, middle, and lower bands
        """
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}

        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()

            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)

            return {
                "upper": float(upper.iloc[-1]),
                "middle": float(sma.iloc[-1]),
                "lower": float(lower.iloc[-1]),
            }
        except Exception:
            return {"upper": None, "middle": None, "lower": None}

    @staticmethod
    def calculate_volume_average(volumes: pd.Series, period: int = 20) -> Optional[float]:
        """
        Calculate average volume.

        Args:
            volumes: Series of volume data
            period: Period for average

        Returns:
            Average volume or None if insufficient data
        """
        if len(volumes) < period:
            return None

        try:
            return float(volumes.rolling(window=period).mean().iloc[-1])
        except Exception:
            return None

    @staticmethod
    def calculate_all_indicators(
        prices_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Calculate all technical indicators from a price DataFrame.

        Args:
            prices_df: DataFrame with columns: time, open, high, low, close, volume

        Returns:
            Dictionary with all calculated indicators
        """
        if prices_df.empty or "close" not in prices_df.columns:
            return {}

        close_prices = prices_df["close"]
        volumes = prices_df["volume"] if "volume" in prices_df.columns else pd.Series()

        indicators = {
            "rsi": IndicatorCalculator.calculate_rsi(close_prices),
            "sma_20": IndicatorCalculator.calculate_sma(close_prices, 20),
            "sma_50": IndicatorCalculator.calculate_sma(close_prices, 50),
            "sma_200": IndicatorCalculator.calculate_sma(close_prices, 200),
            "ema_12": IndicatorCalculator.calculate_ema(close_prices, 12),
            "ema_26": IndicatorCalculator.calculate_ema(close_prices, 26),
        }

        # MACD
        macd_data = IndicatorCalculator.calculate_macd(close_prices)
        indicators.update(macd_data)

        # Bollinger Bands
        bb_data = IndicatorCalculator.calculate_bollinger_bands(close_prices)
        indicators["bollinger_upper"] = bb_data["upper"]
        indicators["bollinger_middle"] = bb_data["middle"]
        indicators["bollinger_lower"] = bb_data["lower"]

        # Volume average
        if not volumes.empty:
            indicators["volume_avg"] = IndicatorCalculator.calculate_volume_average(volumes)

        return indicators
