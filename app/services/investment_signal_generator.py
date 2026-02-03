"""Investment-focused signal generator for long-term investing with dividend focus.

This service generates BUY/HOLD/SELL signals optimized for:
- Long-term investing (not short-term trading)
- Dividend-paying stocks
- Investment timing (when to buy, how long to hold, when to sell)
- Fundamental analysis over technical analysis
"""

from typing import Dict, Any, Optional
from datetime import datetime
from app.models.signal import SignalType, RiskLevel, HoldingPeriod
from app.services.indicator_calculator import IndicatorCalculator
import pandas as pd


class InvestmentSignalGenerator:
    """
    Investment-focused signal generator.
    
    Optimized for long-term investing with emphasis on:
    - Dividend yield and stability
    - Fundamental strength
    - Long-term value
    - Investment entry/exit timing
    """
    
    # Weight distribution for INVESTING (not trading)
    FUNDAMENTAL_WEIGHT = 0.50  # Higher weight on fundamentals
    DIVIDEND_WEIGHT = 0.25     # Significant weight on dividends
    TREND_WEIGHT = 0.15        # Long-term trends
    TECHNICAL_WEIGHT = 0.10    # Lower weight on technical (entry timing only)
    
    @staticmethod
    def calculate_dividend_score(fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate dividend-focused score for investment decisions.
        
        Args:
            fundamentals: Dictionary with dividend metrics
        
        Returns:
            Dictionary with dividend score and analysis
        """
        score = 50  # Start neutral
        factors = []
        
        dividend_yield = fundamentals.get("dividend_yield")
        dividend_per_share = fundamentals.get("dividend_per_share")
        dividend_payout_ratio = fundamentals.get("dividend_payout_ratio")
        earnings_growth = fundamentals.get("earnings_growth")
        
        # Dividend yield analysis (higher is better for income investors)
        if dividend_yield is not None:
            if dividend_yield > 5:
                score += 15
                factors.append(f"High dividend yield ({dividend_yield:.2f}%) - excellent for income")
            elif dividend_yield > 3:
                score += 10
                factors.append(f"Good dividend yield ({dividend_yield:.2f}%) - solid income stream")
            elif dividend_yield > 2:
                score += 5
                factors.append(f"Moderate dividend yield ({dividend_yield:.2f}%) - decent income")
            elif dividend_yield > 0:
                score += 2
                factors.append(f"Low dividend yield ({dividend_yield:.2f}%) - minimal income")
            else:
                score -= 5
                factors.append("No dividend - growth stock, no income")
        
        # Dividend sustainability (payout ratio)
        if dividend_payout_ratio is not None:
            if 30 <= dividend_payout_ratio <= 70:
                score += 10
                factors.append(f"Sustainable payout ratio ({dividend_payout_ratio:.2f}%) - healthy balance")
            elif dividend_payout_ratio < 30:
                score += 5
                factors.append(f"Low payout ratio ({dividend_payout_ratio:.2f}%) - room for dividend growth")
            elif dividend_payout_ratio > 90:
                score -= 10
                factors.append(f"High payout ratio ({dividend_payout_ratio:.2f}%) - dividend may be at risk")
            elif dividend_payout_ratio > 100:
                score -= 15
                factors.append(f"Payout ratio > 100% ({dividend_payout_ratio:.2f}%) - unsustainable")
        
        # Dividend growth potential
        if earnings_growth is not None and dividend_yield and dividend_yield > 0:
            if earnings_growth > 10:
                score += 8
                factors.append(f"Strong earnings growth ({earnings_growth:.2f}%) - dividend may increase")
            elif earnings_growth > 5:
                score += 4
                factors.append(f"Positive earnings growth ({earnings_growth:.2f}%) - dividend stability")
            elif earnings_growth < 0:
                score -= 8
                factors.append(f"Negative earnings growth ({earnings_growth:.2f}%) - dividend may be cut")
        
        # Dividend per share
        if dividend_per_share is not None and dividend_per_share > 0:
            factors.append(f"Annual dividend: ${dividend_per_share:.2f} per share")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "factors": factors,
            "dividend_yield": dividend_yield,
            "dividend_per_share": dividend_per_share,
            "dividend_payout_ratio": dividend_payout_ratio,
            "is_dividend_stock": dividend_yield and dividend_yield > 2,
        }
    
    @staticmethod
    def calculate_fundamental_score_investing(fundamentals: Dict[str, Any], sector_pe: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate fundamental score optimized for long-term investing.
        
        Args:
            fundamentals: Fundamental metrics
            sector_pe: Sector average P/E
        
        Returns:
            Dictionary with fundamental score
        """
        score = 50
        factors = []
        
        pe_ratio = fundamentals.get("pe_ratio")
        earnings_growth = fundamentals.get("earnings_growth")
        debt_ratio = fundamentals.get("debt_ratio")
        revenue = fundamentals.get("revenue")
        eps = fundamentals.get("eps")
        
        # P/E ratio analysis (for value investing)
        if pe_ratio is not None:
            if sector_pe:
                if pe_ratio < sector_pe * 0.7:
                    score += 12
                    factors.append(f"Undervalued: P/E ({pe_ratio:.2f}) well below sector ({sector_pe:.2f})")
                elif pe_ratio < sector_pe * 0.9:
                    score += 6
                    factors.append(f"Fairly valued: P/E ({pe_ratio:.2f}) below sector ({sector_pe:.2f})")
                elif pe_ratio > sector_pe * 1.3:
                    score -= 10
                    factors.append(f"Overvalued: P/E ({pe_ratio:.2f}) above sector ({sector_pe:.2f})")
            else:
                # General P/E assessment
                if 10 <= pe_ratio <= 20:
                    score += 8
                    factors.append(f"Reasonable P/E ratio ({pe_ratio:.2f}) - good value")
                elif pe_ratio < 10:
                    score += 5
                    factors.append(f"Low P/E ratio ({pe_ratio:.2f}) - potential value play")
                elif pe_ratio > 30:
                    score -= 8
                    factors.append(f"High P/E ratio ({pe_ratio:.2f}) - premium valuation")
        
        # Earnings growth (critical for long-term investing)
        if earnings_growth is not None:
            if earnings_growth > 20:
                score += 15
                factors.append(f"Strong earnings growth ({earnings_growth:.2f}%) - excellent long-term potential")
            elif earnings_growth > 10:
                score += 10
                factors.append(f"Good earnings growth ({earnings_growth:.2f}%) - solid growth")
            elif earnings_growth > 5:
                score += 5
                factors.append(f"Moderate earnings growth ({earnings_growth:.2f}%) - steady growth")
            elif earnings_growth < -10:
                score -= 15
                factors.append(f"Declining earnings ({earnings_growth:.2f}%) - concerning for long-term")
        
        # Financial health (debt ratio)
        if debt_ratio is not None:
            if debt_ratio < 30:
                score += 8
                factors.append(f"Low debt ratio ({debt_ratio:.2f}%) - strong financial health")
            elif debt_ratio < 50:
                score += 4
                factors.append(f"Moderate debt ratio ({debt_ratio:.2f}%) - manageable debt")
            elif debt_ratio > 70:
                score -= 12
                factors.append(f"High debt ratio ({debt_ratio:.2f}%) - financial risk")
        
        # Revenue and EPS (business strength)
        if revenue is not None and revenue > 0:
            factors.append(f"Revenue data available - business operational")
        if eps is not None and eps > 0:
            score += 3
            factors.append(f"Positive EPS (${eps:.2f}) - profitable company")
        elif eps is not None and eps < 0:
            score -= 10
            factors.append(f"Negative EPS (${eps:.2f}) - company losing money")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "factors": factors,
            "pe_ratio": pe_ratio,
            "earnings_growth": earnings_growth,
            "debt_ratio": debt_ratio,
        }
    
    @staticmethod
    def calculate_long_term_trend_score(prices_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate long-term trend score for investing (not trading).
        
        Focuses on 6-month to 2-year trends, not daily volatility.
        
        Args:
            prices_df: Price DataFrame
        
        Returns:
            Dictionary with long-term trend score
        """
        if prices_df.empty or len(prices_df) < 60:
            return {"score": 50, "factors": ["Insufficient data for long-term trend"]}
        
        close_prices = prices_df["close"].values
        score = 50
        factors = []
        
        # Long-term trend (6 months = ~126 trading days)
        if len(close_prices) >= 126:
            long_term_change = ((close_prices[-1] - close_prices[-126]) / close_prices[-126]) * 100
            if long_term_change > 30:
                score += 15
                factors.append(f"Strong long-term uptrend ({long_term_change:.2f}% over 6 months)")
            elif long_term_change > 15:
                score += 10
                factors.append(f"Positive long-term trend ({long_term_change:.2f}% over 6 months)")
            elif long_term_change > 5:
                score += 5
                factors.append(f"Modest long-term growth ({long_term_change:.2f}% over 6 months)")
            elif long_term_change < -30:
                score -= 15
                factors.append(f"Significant long-term decline ({long_term_change:.2f}% over 6 months)")
            elif long_term_change < -15:
                score -= 10
                factors.append(f"Long-term downtrend ({long_term_change:.2f}% over 6 months)")
        
        # Medium-term trend (3 months = ~63 trading days)
        if len(close_prices) >= 63:
            medium_term_change = ((close_prices[-1] - close_prices[-63]) / close_prices[-63]) * 100
            if medium_term_change > 20:
                score += 8
                factors.append(f"Strong recent momentum ({medium_term_change:.2f}% over 3 months)")
            elif medium_term_change < -20:
                score -= 8
                factors.append(f"Recent weakness ({medium_term_change:.2f}% over 3 months)")
        
        # Price stability (low volatility is good for long-term investing)
        if len(close_prices) >= 60:
            returns = pd.Series(close_prices).pct_change().dropna()
            volatility = returns.std() * 100
            if volatility < 20:
                score += 5
                factors.append(f"Low volatility ({volatility:.2f}%) - stable for long-term holding")
            elif volatility > 40:
                score -= 5
                factors.append(f"High volatility ({volatility:.2f}%) - more risk for long-term")
        
        score = max(0, min(100, score))
        
        return {"score": score, "factors": factors}
    
    @staticmethod
    def calculate_entry_timing_score(indicators: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """
        Calculate entry timing score (when to buy).
        
        Uses technical analysis ONLY for entry timing, not for investment decision.
        Helps identify good entry points for long-term positions.
        
        Args:
            indicators: Technical indicators
            current_price: Current stock price
        
        Returns:
            Dictionary with entry timing score
        """
        score = 50
        factors = []
        
        rsi = indicators.get("rsi")
        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")
        sma_200 = indicators.get("sma_200")
        
        # RSI for entry timing (oversold = good entry)
        if rsi is not None:
            if rsi < 35:
                score += 10
                factors.append(f"RSI oversold ({rsi:.1f}) - potential good entry point")
            elif rsi > 65:
                score -= 5
                factors.append(f"RSI overbought ({rsi:.1f}) - consider waiting for better entry")
        
        # Moving averages for entry timing
        if sma_200 and current_price:
            if current_price < sma_200 * 0.9:
                score += 8
                factors.append(f"Price below 200-day SMA - potential value entry")
            elif current_price > sma_200 * 1.1:
                score -= 5
                factors.append(f"Price above 200-day SMA - may be overextended")
        
        if sma_50 and current_price:
            if current_price < sma_50 * 0.95:
                score += 5
                factors.append(f"Price below 50-day SMA - short-term pullback, good entry")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "factors": factors,
            "entry_timing": "GOOD" if score > 55 else "FAIR" if score > 45 else "WAIT",
        }
    
    @staticmethod
    def generate_investment_signal(
        indicators: Dict[str, Any],
        fundamentals: Dict[str, Any],
        prices_df: pd.DataFrame,
        sector_pe: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate investment signal optimized for long-term investing.
        
        Focuses on:
        - Dividend yield and sustainability
        - Fundamental strength
        - Long-term value
        - Investment entry/exit timing
        
        Args:
            indicators: Technical indicators (for entry timing only)
            fundamentals: Fundamental metrics
            prices_df: Price DataFrame
            sector_pe: Sector average P/E
        
        Returns:
            Dictionary with investment signal
        """
        if prices_df.empty:
            return {
                "signal_type": SignalType.NO_SIGNAL,
                "confidence_score": 0,
                "risk_level": RiskLevel.HIGH,
                "holding_period": HoldingPeriod.MEDIUM,
                "explanation": {
                    "summary": "Insufficient data to generate investment signal",
                    "factors": {},
                    "triggers": [],
                    "risks": ["Insufficient price data"],
                    "invalidation_conditions": [],
                },
            }
        
        current_price = prices_df["close"].iloc[-1]
        
        # Calculate component scores
        dividend_result = InvestmentSignalGenerator.calculate_dividend_score(fundamentals)
        fundamental_result = InvestmentSignalGenerator.calculate_fundamental_score_investing(fundamentals, sector_pe)
        trend_result = InvestmentSignalGenerator.calculate_long_term_trend_score(prices_df)
        entry_timing_result = InvestmentSignalGenerator.calculate_entry_timing_score(indicators, current_price)
        
        # Calculate weighted composite score (investment-focused)
        composite_score = (
            fundamental_result["score"] * InvestmentSignalGenerator.FUNDAMENTAL_WEIGHT
            + dividend_result["score"] * InvestmentSignalGenerator.DIVIDEND_WEIGHT
            + trend_result["score"] * InvestmentSignalGenerator.TREND_WEIGHT
            + entry_timing_result["score"] * InvestmentSignalGenerator.TECHNICAL_WEIGHT
        )
        
        # Determine signal type (investment-focused thresholds)
        if composite_score > 65:
            signal_type = SignalType.BUY
        elif composite_score < 35:
            signal_type = SignalType.SELL
        elif 35 <= composite_score <= 65:
            signal_type = SignalType.HOLD
        else:
            signal_type = SignalType.NO_SIGNAL
        
        # Calculate confidence
        confidence = abs(composite_score - 50) * 2
        confidence = min(100, confidence)
        
        # Adjust confidence based on data quality
        if not fundamentals or not dividend_result.get("dividend_yield"):
            confidence *= 0.8  # Lower confidence if missing dividend data
        
        # Determine risk level (for investing)
        debt_ratio = fundamental_result.get("debt_ratio", 50)
        dividend_payout = dividend_result.get("dividend_payout_ratio")
        
        if debt_ratio < 40 and dividend_payout and 30 <= dividend_payout <= 70:
            risk_level = RiskLevel.LOW
        elif debt_ratio > 70 or (dividend_payout and dividend_payout > 90):
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.MEDIUM
        
        # Determine holding period (for investing, favor LONG-term)
        dividend_yield = dividend_result.get("dividend_yield", 0)
        earnings_growth = fundamental_result.get("earnings_growth", 0)
        
        if dividend_yield > 3 and earnings_growth > 5 and fundamental_result["score"] > 60:
            holding_period = HoldingPeriod.LONG  # Strong dividend + growth = long-term hold
        elif dividend_yield > 2 or (earnings_growth > 10 and fundamental_result["score"] > 55):
            holding_period = HoldingPeriod.LONG  # Good fundamentals = long-term
        elif fundamental_result["score"] < 40:
            holding_period = HoldingPeriod.SHORT  # Poor fundamentals = short-term only
        else:
            holding_period = HoldingPeriod.MEDIUM
        
        # Generate investment-focused explanation
        explanation = {
            "summary": f"{signal_type.value} signal for long-term investing with {confidence:.1f}% confidence",
            "investment_focus": True,
            "factors": {
                "fundamental": {
                    "score": fundamental_result["score"],
                    "pe_ratio": fundamental_result.get("pe_ratio"),
                    "earnings_growth": fundamental_result.get("earnings_growth"),
                    "debt_ratio": fundamental_result.get("debt_ratio"),
                },
                "dividend": {
                    "score": dividend_result["score"],
                    "dividend_yield": dividend_result.get("dividend_yield"),
                    "dividend_per_share": dividend_result.get("dividend_per_share"),
                    "dividend_payout_ratio": dividend_result.get("dividend_payout_ratio"),
                    "is_dividend_stock": dividend_result.get("is_dividend_stock", False),
                },
                "long_term_trend": {
                    "score": trend_result["score"],
                },
                "entry_timing": {
                    "score": entry_timing_result["score"],
                    "timing": entry_timing_result.get("entry_timing", "FAIR"),
                },
            },
            "triggers": (
                fundamental_result.get("factors", [])[:2] +
                dividend_result.get("factors", [])[:2] +
                trend_result.get("factors", [])[:1]
            ),
            "risks": [
                f"Debt ratio: {debt_ratio:.1f}%",
                f"Dividend payout: {dividend_result.get('dividend_payout_ratio', 'N/A')}%",
            ],
            "investment_guidance": {
                "when_to_buy": entry_timing_result.get("entry_timing", "FAIR"),
                "how_long_to_hold": holding_period.value,
                "when_to_sell": "Consider selling if fundamentals deteriorate or dividend is cut",
            },
        }
        
        return {
            "signal_type": signal_type,
            "confidence_score": round(confidence, 2),
            "risk_level": risk_level,
            "holding_period": holding_period,
            "explanation": explanation,
            "composite_score": round(composite_score, 2),
            "dividend_yield": dividend_result.get("dividend_yield"),
            "is_dividend_stock": dividend_result.get("is_dividend_stock", False),
        }
