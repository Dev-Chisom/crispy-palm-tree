"""ML-enhanced signal generation service."""

from typing import Dict, Any, Optional
import pandas as pd
from app.models.signal import SignalType, RiskLevel, HoldingPeriod
# Optional ML imports - only import if TensorFlow is available
try:
    from app.ml.models import LSTMForecaster, SignalClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    LSTMForecaster = None
    SignalClassifier = None
from app.services.signal_generator import SignalGenerator
from app.services.indicator_calculator import IndicatorCalculator
import os


class MLSignalGenerator:
    """
    ML-enhanced signal generator with layered approach:
    1. Baseline: Rule-based signals (fallback)
    2. ML Layer: LSTM forecasting + Classification model
    3. Hybrid: Combine both for final signal
    """

    def __init__(
        self,
        use_lstm: bool = True,
        use_classifier: bool = True,
        fallback_to_rules: bool = True
    ):
        """
        Initialize ML signal generator.

        Args:
            use_lstm: Use LSTM for price forecasting
            use_classifier: Use classifier for signal prediction
            fallback_to_rules: Fallback to rule-based if ML fails
        """
        if not ML_AVAILABLE:
            # ML not available, force fallback to rules
            use_lstm = False
            use_classifier = False
            fallback_to_rules = True
        
        self.use_lstm = use_lstm and ML_AVAILABLE
        self.use_classifier = use_classifier and ML_AVAILABLE
        self.fallback_to_rules = fallback_to_rules
        self.lstm_models = {}  # Cache loaded models
        self.classifier = None

    def _load_lstm_model(self, symbol: str, model_path: str = None) -> Optional[LSTMForecaster]:
        """Load LSTM model for a stock."""
        if symbol in self.lstm_models:
            return self.lstm_models[symbol]

        if model_path is None:
            # Try to find model
            model_dir = "models"
            if not os.path.exists(model_dir):
                return None
            model_files = [f for f in os.listdir(model_dir) if f.startswith(f"lstm_{symbol}") and f.endswith(".h5")]
            if not model_files:
                return None
            model_path = os.path.join(model_dir, sorted(model_files)[-1])  # Use latest

        if not os.path.exists(model_path):
            return None

        try:
            forecaster = LSTMForecaster()
            forecaster.load(model_path)
            self.lstm_models[symbol] = forecaster
            return forecaster
        except Exception:
            return None

    def _load_classifier(self, model_path: str = None) -> Optional[SignalClassifier]:
        """Load signal classifier model."""
        if self.classifier is not None:
            return self.classifier

        if model_path is None:
            model_dir = "models"
            if not os.path.exists(model_dir):
                return None
            model_files = [f for f in os.listdir(model_dir) if f.startswith("classifier_") and f.endswith(".h5")]
            if not model_files:
                return None
            model_path = os.path.join(model_dir, sorted(model_files)[-1])

        if not os.path.exists(model_path):
            return None

        try:
            classifier = SignalClassifier()
            classifier.load(model_path)
            self.classifier = classifier
            return classifier
        except Exception:
            return None

    def generate_signal_with_ml(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        fundamentals: Dict[str, Any],
        prices_df: pd.DataFrame,
        sector_pe: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate signal using ML models with rule-based fallback.

        Args:
            symbol: Stock symbol
            indicators: Technical indicators
            fundamentals: Fundamental metrics
            prices_df: Price DataFrame
            sector_pe: Sector average P/E

        Returns:
            Signal dictionary with ML predictions
        """
        ml_confidence = 0
        ml_signal_type = None
        price_forecast = None
        ml_used = False

        # Try LSTM forecasting
        if self.use_lstm:
            lstm_model = self._load_lstm_model(symbol)
            if lstm_model:
                try:
                    # Forecast next 5 days
                    forecast = lstm_model.predict(prices_df, steps=5)
                    price_forecast = float(forecast[-1])  # Use 5-day forecast
                    current_price = prices_df["close"].iloc[-1]
                    
                    # Calculate forecast trend
                    forecast_change = ((price_forecast - current_price) / current_price) * 100
                    
                    if forecast_change > 3:
                        ml_signal_type = SignalType.BUY
                        ml_confidence = min(85, 50 + abs(forecast_change) * 2)
                    elif forecast_change < -3:
                        ml_signal_type = SignalType.SELL
                        ml_confidence = min(85, 50 + abs(forecast_change) * 2)
                    else:
                        ml_signal_type = SignalType.HOLD
                        ml_confidence = 60
                    
                    ml_used = True
                except Exception:
                    pass

        # Try classifier
        if self.use_classifier and ml_signal_type is None:
            classifier = self._load_classifier()
            if classifier:
                try:
                    # Prepare price features
                    current_price = prices_df["close"].iloc[-1]
                    short_term = 0
                    medium_term = 0
                    if len(prices_df) >= 20:
                        short_term = ((prices_df["close"].iloc[-1] - prices_df["close"].iloc[-20]) / prices_df["close"].iloc[-20]) * 100
                    if len(prices_df) >= 50:
                        medium_term = ((prices_df["close"].iloc[-1] - prices_df["close"].iloc[-50]) / prices_df["close"].iloc[-50]) * 100
                    
                    volatility = prices_df["close"].pct_change().std() * 100 if len(prices_df) > 1 else 20
                    volume_avg = prices_df["volume"].mean() if "volume" in prices_df.columns else 1
                    current_volume = prices_df["volume"].iloc[-1] if "volume" in prices_df.columns else 1
                    volume_ratio = current_volume / volume_avg if volume_avg > 0 else 1

                    price_features = {
                        'short_term_trend': short_term,
                        'medium_term_trend': medium_term,
                        'volatility': volatility,
                        'volume_ratio': volume_ratio,
                    }

                    signal_str, confidence = classifier.predict(indicators, fundamentals, price_features)
                    ml_signal_type = SignalType[signal_str]
                    ml_confidence = confidence
                    ml_used = True
                except Exception:
                    pass

        # Get rule-based signal as baseline/fallback
        rule_based_result = SignalGenerator.generate_signal(
            indicators=indicators,
            fundamentals=fundamentals,
            prices_df=prices_df,
            sector_pe=sector_pe,
        )

        # Hybrid approach: Combine ML and rule-based
        if ml_used and ml_signal_type:
            # Weight ML prediction (60%) with rule-based (40%)
            ml_weight = 0.6
            rule_weight = 0.4

            # Convert to scores
            ml_score = ml_confidence if ml_signal_type == SignalType.BUY else (100 - ml_confidence) if ml_signal_type == SignalType.SELL else 50
            rule_score = rule_based_result.get("composite_score", 50)

            hybrid_score = (ml_score * ml_weight) + (rule_score * rule_weight)

            # Determine final signal
            if hybrid_score > 60:
                final_signal = SignalType.BUY
            elif hybrid_score < 40:
                final_signal = SignalType.SELL
            elif 40 <= hybrid_score <= 60:
                final_signal = SignalType.HOLD
            else:
                final_signal = SignalType.NO_SIGNAL

            # Calculate final confidence
            final_confidence = abs(hybrid_score - 50) * 2
            final_confidence = min(100, final_confidence)

            # Use risk level and holding period from rule-based (can be enhanced)
            risk_level = rule_based_result["risk_level"]
            holding_period = rule_based_result["holding_period"]

            explanation = rule_based_result["explanation"].copy()
            explanation["ml_prediction"] = {
                "signal": ml_signal_type.value,
                "confidence": ml_confidence,
                "price_forecast": price_forecast,
                "method": "LSTM" if price_forecast else "Classifier"
            }
            explanation["hybrid_approach"] = True
            explanation["ml_weight"] = ml_weight
            explanation["rule_weight"] = rule_weight

        else:
            # Fallback to rule-based
            final_signal = rule_based_result["signal_type"]
            final_confidence = rule_based_result["confidence_score"]
            risk_level = rule_based_result["risk_level"]
            holding_period = rule_based_result["holding_period"]
            explanation = rule_based_result["explanation"]
            explanation["ml_prediction"] = None
            explanation["hybrid_approach"] = False

        return {
            "signal_type": final_signal,
            "confidence_score": round(final_confidence, 2),
            "risk_level": risk_level,
            "holding_period": holding_period,
            "explanation": explanation,
            "ml_used": ml_used,
            "price_forecast": price_forecast,
        }
