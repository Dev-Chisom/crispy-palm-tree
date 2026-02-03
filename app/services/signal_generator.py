"""Signal generation service with rule-based multi-factor scoring."""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from app.models.signal import SignalType, RiskLevel, HoldingPeriod
from app.services.indicator_calculator import IndicatorCalculator
import pandas as pd


class SignalGenerator:
    """Service for generating trading signals using rule-based analysis."""

    # Weight distribution
    TECHNICAL_WEIGHT = 0.40
    FUNDAMENTAL_WEIGHT = 0.30
    TREND_WEIGHT = 0.20
    VOLATILITY_WEIGHT = 0.10

    @staticmethod
    def calculate_technical_score(indicators: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """
        Calculate technical analysis score (0-100).

        Args:
            indicators: Dictionary of technical indicators
            current_price: Current stock price

        Returns:
            Dictionary with score and details
        """
        score = 50  # Start neutral
        factors = []
        signals = []

        rsi = indicators.get("rsi")
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        macd_histogram = indicators.get("macd_histogram")
        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")
        sma_200 = indicators.get("sma_200")
        bb_upper = indicators.get("bollinger_upper")
        bb_lower = indicators.get("bollinger_lower")
        volume_avg = indicators.get("volume_avg")
        current_volume = indicators.get("current_volume")

        # RSI analysis
        if rsi is not None:
            if rsi < 30:
                score += 15
                factors.append("RSI oversold (bullish)")
                signals.append("BUY")
            elif rsi > 70:
                score -= 15
                factors.append("RSI overbought (bearish)")
                signals.append("SELL")
            elif 30 <= rsi <= 45:
                score += 5
                factors.append("RSI in neutral-bullish zone")
            elif 55 <= rsi <= 70:
                score -= 5
                factors.append("RSI in neutral-bearish zone")

        # MACD analysis
        if macd is not None and macd_signal is not None:
            if macd > macd_signal and macd_histogram and macd_histogram > 0:
                score += 10
                factors.append("Bullish MACD crossover")
                signals.append("BUY")
            elif macd < macd_signal and macd_histogram and macd_histogram < 0:
                score -= 10
                factors.append("Bearish MACD crossover")
                signals.append("SELL")

        # Moving averages analysis
        bullish_ma_count = 0
        if sma_20 and current_price > sma_20:
            score += 5
            bullish_ma_count += 1
            factors.append("Price above SMA 20")
        if sma_50 and current_price > sma_50:
            score += 8
            bullish_ma_count += 1
            factors.append("Price above SMA 50")
        if sma_200 and current_price > sma_200:
            score += 10
            bullish_ma_count += 1
            factors.append("Price above SMA 200")

        if bullish_ma_count == 0:
            score -= 10
            factors.append("Price below all key moving averages")

        # Bollinger Bands analysis
        if bb_lower and bb_upper:
            if current_price <= bb_lower:
                score += 10
                factors.append("Price near lower Bollinger Band (potential bounce)")
            elif current_price >= bb_upper:
                score -= 10
                factors.append("Price near upper Bollinger Band (potential pullback)")

        # Volume analysis
        if current_volume and volume_avg:
            volume_ratio = current_volume / volume_avg
            if volume_ratio > 1.5:
                # High volume confirms trend
                if "BUY" in signals:
                    score += 5
                elif "SELL" in signals:
                    score -= 5
                factors.append(f"Volume {volume_ratio:.2f}x average (confirms trend)")

        # Normalize score to 0-100
        score = max(0, min(100, score))

        return {
            "score": score,
            "factors": factors,
            "signals": signals,
            "rsi": rsi,
            "trend": "bullish" if score > 50 else "bearish" if score < 50 else "neutral",
        }

    @staticmethod
    def calculate_fundamental_score(fundamentals: Dict[str, Any], sector_pe: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate fundamental analysis score (0-100).

        Args:
            fundamentals: Dictionary of fundamental metrics
            sector_pe: Sector average P/E ratio for comparison

        Returns:
            Dictionary with score and details
        """
        score = 50  # Start neutral
        factors = []

        pe_ratio = fundamentals.get("pe_ratio")
        earnings_growth = fundamentals.get("earnings_growth")
        revenue = fundamentals.get("revenue")
        debt_ratio = fundamentals.get("debt_ratio")

        # P/E ratio analysis
        if pe_ratio is not None:
            if sector_pe:
                if pe_ratio < sector_pe * 0.8:
                    score += 10
                    factors.append(f"P/E ratio ({pe_ratio:.2f}) below sector average ({sector_pe:.2f})")
                elif pe_ratio > sector_pe * 1.2:
                    score -= 10
                    factors.append(f"P/E ratio ({pe_ratio:.2f}) above sector average ({sector_pe:.2f})")
            else:
                # General P/E assessment
                if 10 <= pe_ratio <= 25:
                    score += 5
                    factors.append(f"Reasonable P/E ratio ({pe_ratio:.2f})")
                elif pe_ratio > 30:
                    score -= 10
                    factors.append(f"High P/E ratio ({pe_ratio:.2f})")

        # Earnings growth analysis
        if earnings_growth is not None:
            if earnings_growth > 20:
                score += 15
                factors.append(f"Strong earnings growth ({earnings_growth:.2f}%)")
            elif earnings_growth > 10:
                score += 8
                factors.append(f"Positive earnings growth ({earnings_growth:.2f}%)")
            elif earnings_growth > 0:
                score += 3
                factors.append(f"Modest earnings growth ({earnings_growth:.2f}%)")
            elif earnings_growth < -10:
                score -= 15
                factors.append(f"Negative earnings growth ({earnings_growth:.2f}%)")
            else:
                score -= 5
                factors.append(f"Declining earnings growth ({earnings_growth:.2f}%)")

        # Revenue analysis (if available)
        if revenue is not None:
            factors.append(f"Revenue data available")

        # Debt ratio analysis
        if debt_ratio is not None:
            if debt_ratio < 30:
                score += 5
                factors.append(f"Low debt ratio ({debt_ratio:.2f}%)")
            elif debt_ratio > 70:
                score -= 10
                factors.append(f"High debt ratio ({debt_ratio:.2f}%)")

        # Normalize score to 0-100
        score = max(0, min(100, score))

        return {
            "score": score,
            "factors": factors,
            "pe_ratio": pe_ratio,
            "earnings_growth": earnings_growth,
        }

    @staticmethod
    def calculate_trend_score(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate trend analysis score (0-100).

        Args:
            prices_df: DataFrame with price data

        Returns:
            Dictionary with score and details
        """
        if prices_df.empty or len(prices_df) < 5:
            return {"score": 50, "factors": ["Insufficient data for trend analysis"]}

        close_prices = prices_df["close"].values
        score = 50
        factors = []

        # Short-term trend (5-20 days)
        if len(close_prices) >= 20:
            short_term_change = ((close_prices[-1] - close_prices[-20]) / close_prices[-20]) * 100
            if short_term_change > 5:
                score += 8
                factors.append(f"Strong short-term uptrend ({short_term_change:.2f}%)")
            elif short_term_change > 2:
                score += 4
                factors.append(f"Positive short-term trend ({short_term_change:.2f}%)")
            elif short_term_change < -5:
                score -= 8
                factors.append(f"Strong short-term downtrend ({short_term_change:.2f}%)")
            elif short_term_change < -2:
                score -= 4
                factors.append(f"Negative short-term trend ({short_term_change:.2f}%)")

        # Medium-term trend (20-50 days)
        if len(close_prices) >= 50:
            medium_term_change = ((close_prices[-1] - close_prices[-50]) / close_prices[-50]) * 100
            if medium_term_change > 10:
                score += 10
                factors.append(f"Strong medium-term uptrend ({medium_term_change:.2f}%)")
            elif medium_term_change > 5:
                score += 5
                factors.append(f"Positive medium-term trend ({medium_term_change:.2f}%)")
            elif medium_term_change < -10:
                score -= 10
                factors.append(f"Strong medium-term downtrend ({medium_term_change:.2f}%)")
            elif medium_term_change < -5:
                score -= 5
                factors.append(f"Negative medium-term trend ({medium_term_change:.2f}%)")

        # Long-term trend (50-200 days)
        if len(close_prices) >= 200:
            long_term_change = ((close_prices[-1] - close_prices[-200]) / close_prices[-200]) * 100
            if long_term_change > 20:
                score += 12
                factors.append(f"Strong long-term uptrend ({long_term_change:.2f}%)")
            elif long_term_change > 10:
                score += 6
                factors.append(f"Positive long-term trend ({long_term_change:.2f}%)")
            elif long_term_change < -20:
                score -= 12
                factors.append(f"Strong long-term downtrend ({long_term_change:.2f}%)")
            elif long_term_change < -10:
                score -= 6
                factors.append(f"Negative long-term trend ({long_term_change:.2f}%)")

        # Normalize score to 0-100
        score = max(0, min(100, score))

        return {"score": score, "factors": factors}

    @staticmethod
    def calculate_volatility_score(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate volatility and risk score (0-100).

        Args:
            prices_df: DataFrame with price data

        Returns:
            Dictionary with score and details
        """
        if prices_df.empty or len(prices_df) < 20:
            return {"score": 50, "factors": ["Insufficient data for volatility analysis"]}

        close_prices = prices_df["close"]
        score = 50
        factors = []

        # Calculate historical volatility (standard deviation of returns)
        returns = close_prices.pct_change().dropna()
        if len(returns) > 0:
            volatility = returns.std() * 100  # Convert to percentage
            annualized_vol = volatility * (252 ** 0.5)  # Annualized

            if annualized_vol < 15:
                score += 10  # Low volatility is good
                factors.append(f"Low volatility ({annualized_vol:.2f}%)")
            elif annualized_vol > 40:
                score -= 15  # High volatility increases risk
                factors.append(f"High volatility ({annualized_vol:.2f}%)")
            else:
                factors.append(f"Moderate volatility ({annualized_vol:.2f}%)")

        # Calculate maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        if max_drawdown > -20:
            score += 5
            factors.append(f"Controlled drawdown ({max_drawdown:.2f}%)")
        elif max_drawdown < -50:
            score -= 10
            factors.append(f"Significant drawdown ({max_drawdown:.2f}%)")

        # Normalize score to 0-100
        score = max(0, min(100, score))

        return {"score": score, "factors": factors, "volatility": annualized_vol if len(returns) > 0 else None}

    @staticmethod
    def generate_signal(
        indicators: Dict[str, Any],
        fundamentals: Dict[str, Any],
        prices_df: pd.DataFrame,
        sector_pe: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate trading signal using multi-factor analysis.

        Args:
            indicators: Technical indicators
            fundamentals: Fundamental metrics
            prices_df: Price DataFrame
            sector_pe: Sector average P/E ratio

        Returns:
            Dictionary with signal type, confidence, risk level, holding period, and explanation
        """
        if prices_df.empty:
            return {
                "signal_type": SignalType.NO_SIGNAL,
                "confidence_score": 0,
                "risk_level": RiskLevel.HIGH,
                "holding_period": HoldingPeriod.SHORT,
                "explanation": {
                    "summary": "Insufficient data to generate signal",
                    "factors": {},
                    "triggers": [],
                    "risks": ["Insufficient price data"],
                    "invalidation_conditions": [],
                },
            }

        current_price = prices_df["close"].iloc[-1]
        current_volume = prices_df["volume"].iloc[-1] if "volume" in prices_df.columns else None

        # Add current volume to indicators
        indicators_with_volume = indicators.copy()
        indicators_with_volume["current_volume"] = current_volume

        # Calculate component scores
        technical_result = SignalGenerator.calculate_technical_score(indicators_with_volume, current_price)
        fundamental_result = SignalGenerator.calculate_fundamental_score(fundamentals, sector_pe)
        trend_result = SignalGenerator.calculate_trend_score(prices_df)
        volatility_result = SignalGenerator.calculate_volatility_score(prices_df)

        # Calculate weighted composite score
        composite_score = (
            technical_result["score"] * SignalGenerator.TECHNICAL_WEIGHT
            + fundamental_result["score"] * SignalGenerator.FUNDAMENTAL_WEIGHT
            + trend_result["score"] * SignalGenerator.TREND_WEIGHT
            + volatility_result["score"] * SignalGenerator.VOLATILITY_WEIGHT
        )

        # Determine signal type
        if composite_score > 60:
            signal_type = SignalType.BUY
        elif composite_score < 40:
            signal_type = SignalType.SELL
        elif 40 <= composite_score <= 60:
            signal_type = SignalType.HOLD
        else:
            signal_type = SignalType.NO_SIGNAL

        # Calculate confidence score
        # Base confidence from composite score
        confidence = abs(composite_score - 50) * 2  # Convert to 0-100 scale

        # Adjust for data quality
        data_quality_factor = 1.0
        if not indicators or not fundamentals:
            data_quality_factor *= 0.7  # Reduce confidence if data is missing

        # Adjust for signal agreement
        agreement_factor = 1.0
        buy_signals = sum(1 for s in technical_result.get("signals", []) if s == "BUY")
        sell_signals = sum(1 for s in technical_result.get("signals", []) if s == "SELL")

        if signal_type == SignalType.BUY and buy_signals > sell_signals:
            agreement_factor = 1.1
        elif signal_type == SignalType.SELL and sell_signals > buy_signals:
            agreement_factor = 1.1
        elif signal_type == SignalType.HOLD and buy_signals == sell_signals:
            agreement_factor = 1.0
        else:
            agreement_factor = 0.9  # Mixed signals reduce confidence

        confidence = min(100, confidence * data_quality_factor * agreement_factor)

        # Determine risk level
        volatility = volatility_result.get("volatility", 30)
        if volatility < 20 and fundamental_result.get("debt_ratio", 50) < 40:
            risk_level = RiskLevel.LOW
        elif volatility > 40 or fundamental_result.get("debt_ratio", 50) > 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.MEDIUM

        # Determine holding period
        if volatility > 35 or trend_result["score"] < 40:
            holding_period = HoldingPeriod.SHORT
        elif volatility < 20 and trend_result["score"] > 60 and fundamental_result["score"] > 60:
            holding_period = HoldingPeriod.LONG
        else:
            holding_period = HoldingPeriod.MEDIUM

        # Generate explanation (will be enhanced by ExplanationGenerator)
        explanation = {
            "summary": f"{signal_type.value} signal with {confidence:.1f}% confidence",
            "factors": {
                "technical": {
                    "score": technical_result["score"],
                    "rsi": technical_result.get("rsi"),
                    "trend": technical_result.get("trend"),
                },
                "fundamental": {
                    "score": fundamental_result["score"],
                    "pe_ratio": fundamental_result.get("pe_ratio"),
                    "earnings_growth": fundamental_result.get("earnings_growth"),
                },
                "trend": {"score": trend_result["score"]},
                "volatility": {"score": volatility_result["score"]},
            },
            "triggers": technical_result.get("factors", [])[:3],
            "risks": volatility_result.get("factors", [])[:2],
            "invalidation_conditions": [],
        }

        return {
            "signal_type": signal_type,
            "confidence_score": round(confidence, 2),
            "risk_level": risk_level,
            "holding_period": holding_period,
            "explanation": explanation,
            "composite_score": round(composite_score, 2),
        }
