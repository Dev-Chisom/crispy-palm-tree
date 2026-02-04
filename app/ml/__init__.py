"""ML models for signal generation."""

# Optional imports - only import if TensorFlow is available
try:
    from app.ml.models import LSTMForecaster, SignalClassifier
    from app.ml.training import train_lstm_model, train_classifier_model
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    LSTMForecaster = None
    SignalClassifier = None
    train_lstm_model = None
    train_classifier_model = None

__all__ = [
    "LSTMForecaster",
    "SignalClassifier",
    "train_lstm_model",
    "train_classifier_model",
    "ML_AVAILABLE",
]
