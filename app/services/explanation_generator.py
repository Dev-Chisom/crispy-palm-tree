"""Explanation generator service for creating human-readable signal explanations."""

from typing import Dict, Any, List
from app.models.signal import SignalType, RiskLevel, HoldingPeriod


class ExplanationGenerator:
    """Service for generating detailed explanations for trading signals."""

    @staticmethod
    def generate_explanation(
        signal_type: SignalType,
        confidence_score: float,
        risk_level: RiskLevel,
        holding_period: HoldingPeriod,
        technical_data: Dict[str, Any],
        fundamental_data: Dict[str, Any],
        trend_data: Dict[str, Any],
        volatility_data: Dict[str, Any],
        current_price: float,
        indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a signal.

        Args:
            signal_type: Type of signal (BUY/HOLD/SELL/NO_SIGNAL)
            confidence_score: Confidence score (0-100)
            risk_level: Risk level (LOW/MEDIUM/HIGH)
            holding_period: Recommended holding period
            technical_data: Technical analysis results
            fundamental_data: Fundamental analysis results
            trend_data: Trend analysis results
            volatility_data: Volatility analysis results
            current_price: Current stock price
            indicators: Technical indicators

        Returns:
            Dictionary with complete explanation
        """
        # Generate summary
        summary = ExplanationGenerator._generate_summary(
            signal_type, confidence_score, technical_data, fundamental_data, indicators
        )

        # Generate triggers
        triggers = ExplanationGenerator._generate_triggers(
            signal_type, technical_data, fundamental_data, trend_data, indicators
        )

        # Generate risks
        risks = ExplanationGenerator._generate_risks(risk_level, volatility_data, fundamental_data)

        # Generate invalidation conditions
        invalidation_conditions = ExplanationGenerator._generate_invalidation_conditions(
            signal_type, indicators, current_price
        )

        return {
            "summary": summary,
            "factors": {
                "technical": {
                    "score": technical_data.get("score", 50),
                    "rsi": indicators.get("rsi"),
                    "trend": technical_data.get("trend", "neutral"),
                    "momentum": ExplanationGenerator._assess_momentum(technical_data, trend_data),
                },
                "fundamental": {
                    "score": fundamental_data.get("score", 50),
                    "earnings_growth": fundamental_data.get("earnings_growth"),
                    "pe_ratio": fundamental_data.get("pe_ratio"),
                    "sector_pe": fundamental_data.get("sector_pe"),
                },
                "trend": {
                    "score": trend_data.get("score", 50),
                    "short_term": trend_data.get("short_term", "neutral"),
                    "long_term": trend_data.get("long_term", "neutral"),
                },
                "volatility": {
                    "score": volatility_data.get("score", 50),
                    "volatility": volatility_data.get("volatility"),
                },
            },
            "triggers": triggers,
            "risks": risks,
            "invalidation_conditions": invalidation_conditions,
            "holding_period": holding_period.value,
            "risk_level": risk_level.value,
        }

    @staticmethod
    def _generate_summary(
        signal_type: SignalType,
        confidence_score: float,
        technical_data: Dict[str, Any],
        fundamental_data: Dict[str, Any],
        indicators: Dict[str, Any],
    ) -> str:
        """Generate signal summary."""
        rsi = indicators.get("rsi")
        earnings_growth = fundamental_data.get("earnings_growth")
        pe_ratio = fundamental_data.get("pe_ratio")

        parts = [f"{signal_type.value} -"]

        if signal_type == SignalType.BUY:
            parts.append("Strong upward momentum")
            if rsi:
                parts.append(f"with RSI at {rsi:.1f}")
            if earnings_growth and earnings_growth > 0:
                parts.append(f"positive earnings growth of {earnings_growth:.1f}%")
            if technical_data.get("trend") == "bullish":
                parts.append("and price above key moving averages")
        elif signal_type == SignalType.SELL:
            parts.append("Negative momentum")
            if rsi and rsi > 70:
                parts.append(f"with RSI overbought at {rsi:.1f}")
            if earnings_growth and earnings_growth < 0:
                parts.append(f"negative earnings growth of {earnings_growth:.1f}%")
            if technical_data.get("trend") == "bearish":
                parts.append("and price below key moving averages")
        elif signal_type == SignalType.HOLD:
            parts.append("Mixed signals")
            parts.append("with neutral momentum")
        else:
            parts.append("Insufficient data or conflicting signals")

        parts.append(f"(Confidence: {confidence_score:.1f}%)")

        return " ".join(parts) + "."

    @staticmethod
    def _generate_triggers(
        signal_type: SignalType,
        technical_data: Dict[str, Any],
        fundamental_data: Dict[str, Any],
        trend_data: Dict[str, Any],
        indicators: Dict[str, Any],
    ) -> List[str]:
        """Generate trigger list."""
        triggers = []

        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 30:
                triggers.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:
                triggers.append(f"RSI overbought ({rsi:.1f})")

        macd_histogram = indicators.get("macd_histogram")
        if macd_histogram:
            if macd_histogram > 0:
                triggers.append("Bullish MACD crossover")
            elif macd_histogram < 0:
                triggers.append("Bearish MACD crossover")

        sma_50 = indicators.get("sma_50")
        current_price = indicators.get("current_price")
        if sma_50 and current_price:
            if current_price > sma_50:
                triggers.append("Price above 50-day SMA")
            else:
                triggers.append("Price below 50-day SMA")

        earnings_growth = fundamental_data.get("earnings_growth")
        if earnings_growth:
            if earnings_growth > 10:
                triggers.append(f"Positive earnings growth ({earnings_growth:.1f}%)")
            elif earnings_growth < -10:
                triggers.append(f"Negative earnings growth ({earnings_growth:.1f}%)")

        # Add trend triggers
        trend_factors = trend_data.get("factors", [])
        if trend_factors:
            triggers.extend(trend_factors[:2])

        return triggers[:5]  # Limit to top 5 triggers

    @staticmethod
    def _generate_risks(risk_level: RiskLevel, volatility_data: Dict[str, Any], fundamental_data: Dict[str, Any]) -> List[str]:
        """Generate risk list."""
        risks = []

        if risk_level == RiskLevel.HIGH:
            risks.append("High volatility and risk level")

        volatility = volatility_data.get("volatility")
        if volatility and volatility > 40:
            risks.append(f"High market volatility ({volatility:.1f}%)")

        debt_ratio = fundamental_data.get("debt_ratio")
        if debt_ratio and debt_ratio > 70:
            risks.append(f"High debt ratio ({debt_ratio:.1f}%)")

        if risk_level == RiskLevel.MEDIUM:
            risks.append("Moderate market volatility may increase")

        # Generic risks
        risks.append("Market conditions can change rapidly")
        risks.append("Past performance does not guarantee future results")

        return risks[:4]  # Limit to top 4 risks

    @staticmethod
    def _generate_invalidation_conditions(
        signal_type: SignalType, indicators: Dict[str, Any], current_price: float
    ) -> List[str]:
        """Generate invalidation conditions."""
        conditions = []

        if signal_type == SignalType.BUY:
            sma_50 = indicators.get("sma_50")
            if sma_50:
                conditions.append(f"Price breaks below ${sma_50:.2f} support (50-day SMA)")

            rsi = indicators.get("rsi")
            if rsi:
                conditions.append(f"RSI exceeds 70 (overbought)")

            bb_lower = indicators.get("bollinger_lower")
            if bb_lower:
                conditions.append(f"Price breaks below ${bb_lower:.2f} (lower Bollinger Band)")

        elif signal_type == SignalType.SELL:
            sma_50 = indicators.get("sma_50")
            if sma_50:
                conditions.append(f"Price breaks above ${sma_50:.2f} resistance (50-day SMA)")

            rsi = indicators.get("rsi")
            if rsi:
                conditions.append(f"RSI falls below 30 (oversold)")

            bb_upper = indicators.get("bollinger_upper")
            if bb_upper:
                conditions.append(f"Price breaks above ${bb_upper:.2f} (upper Bollinger Band)")

        else:
            conditions.append("Signal may change with new data")

        return conditions[:3]  # Limit to top 3 conditions

    @staticmethod
    def _assess_momentum(technical_data: Dict[str, Any], trend_data: Dict[str, Any]) -> str:
        """Assess overall momentum."""
        technical_score = technical_data.get("score", 50)
        trend_score = trend_data.get("score", 50)

        avg_score = (technical_score + trend_score) / 2

        if avg_score > 65:
            return "strong"
        elif avg_score > 55:
            return "moderate"
        elif avg_score < 35:
            return "weak"
        else:
            return "neutral"
