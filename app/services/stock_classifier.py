"""Service for classifying stocks as Growth, Dividend, or Hybrid."""

from typing import Dict, Any, Optional
from app.models.stock import StockType


class StockClassifier:
    """Service for classifying stocks based on fundamental characteristics."""

    @staticmethod
    def classify_stock(
        dividend_yield: Optional[float],
        earnings_growth: Optional[float],
        pe_ratio: Optional[float],
        dividend_payout_ratio: Optional[float],
    ) -> StockType:
        """
        Classify a stock as GROWTH, DIVIDEND, or HYBRID.

        Args:
            dividend_yield: Dividend yield percentage
            earnings_growth: Earnings growth percentage
            pe_ratio: Price-to-earnings ratio
            dividend_payout_ratio: Dividend payout ratio percentage

        Returns:
            StockType enum
        """
        has_dividend = dividend_yield and dividend_yield > 0.5  # At least 0.5% yield
        has_growth = earnings_growth and earnings_growth > 10  # At least 10% growth
        high_pe = pe_ratio and pe_ratio > 25  # High P/E suggests growth expectations
        high_payout = dividend_payout_ratio and dividend_payout_ratio > 50  # High payout suggests dividend focus

        # Dividend stock: High yield, low growth, high payout ratio
        if has_dividend and (not has_growth or earnings_growth < 5) and (high_payout or dividend_yield > 3):
            return StockType.DIVIDEND

        # Growth stock: High growth, high P/E, low or no dividend
        if has_growth and (high_pe or not has_dividend or dividend_yield < 1):
            return StockType.GROWTH

        # Hybrid: Has both dividend and growth characteristics
        if has_dividend and has_growth:
            return StockType.HYBRID

        # Default classification based on primary characteristic
        if has_dividend:
            return StockType.DIVIDEND
        elif has_growth:
            return StockType.GROWTH
        else:
            # Default to HYBRID if unclear
            return StockType.HYBRID

    @staticmethod
    def get_investor_recommendation(stock_type: StockType, signal_type: str) -> Dict[str, Any]:
        """
        Get investor-specific recommendations based on stock type.

        Args:
            stock_type: StockType enum
            signal_type: BUY, HOLD, SELL, NO_SIGNAL

        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            StockType.GROWTH: {
                "best_for": ["Growth investors", "Long-term wealth building", "Capital appreciation seekers"],
                "strategy": "Focus on capital gains and reinvestment",
                "time_horizon": "Long-term (5+ years)",
            },
            StockType.DIVIDEND: {
                "best_for": ["Income investors", "Retirement portfolios", "Passive income seekers"],
                "strategy": "Focus on regular dividend income",
                "time_horizon": "Long-term (steady income)",
            },
            StockType.HYBRID: {
                "best_for": ["Balanced investors", "Total return seekers", "Diversified portfolios"],
                "strategy": "Combination of growth and income",
                "time_horizon": "Medium to long-term",
            },
        }

        base_recommendation = recommendations.get(stock_type, recommendations[StockType.HYBRID])

        # Add signal-specific guidance
        if signal_type == "BUY":
            base_recommendation["action"] = f"Consider adding to {stock_type.value.lower()} portfolio"
        elif signal_type == "HOLD":
            base_recommendation["action"] = "Maintain position if aligned with investment goals"
        elif signal_type == "SELL":
            base_recommendation["action"] = "Consider reducing position or taking profits"
        else:
            base_recommendation["action"] = "Wait for clearer signals"

        return base_recommendation
