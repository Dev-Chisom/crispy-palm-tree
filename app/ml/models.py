"""ML model architectures for time-series forecasting and signal classification."""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from tensorflow import keras
from tensorflow.keras import layers, models
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import joblib
import os


class LSTMForecaster:
    """
    LSTM model for stock price forecasting.
    
    Uses Temporal Convolutional Network (TCN) architecture as alternative.
    """

    def __init__(self, sequence_length: int = 60, features: int = 5):
        """
        Initialize LSTM forecaster.

        Args:
            sequence_length: Number of time steps to look back
            features: Number of features (OHLCV = 5)
        """
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False

    def build_model(self, units: int = 50, dropout: float = 0.2) -> keras.Model:
        """
        Build LSTM model architecture.

        Args:
            units: Number of LSTM units
            dropout: Dropout rate

        Returns:
            Compiled Keras model
        """
        model = models.Sequential([
            layers.LSTM(units, return_sequences=True, input_shape=(self.sequence_length, self.features)),
            layers.Dropout(dropout),
            layers.LSTM(units, return_sequences=False),
            layers.Dropout(dropout),
            layers.Dense(25),
            layers.Dense(1)  # Predict next close price
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )

        self.model = model
        return model

    def prepare_data(self, prices_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for LSTM training.

        Args:
            prices_df: DataFrame with OHLCV data

        Returns:
            X (sequences), y (targets)
        """
        # Use OHLCV as features
        features = prices_df[['open', 'high', 'low', 'close', 'volume']].values

        # Scale features
        scaled_features = self.scaler.fit_transform(features)

        X, y = [], []
        for i in range(self.sequence_length, len(scaled_features)):
            X.append(scaled_features[i - self.sequence_length:i])
            y.append(scaled_features[i, 3])  # Close price is at index 3

        return np.array(X), np.array(y)

    def train(
        self,
        prices_df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 1
    ) -> Dict[str, Any]:
        """
        Train the LSTM model.

        Args:
            prices_df: Training data
            epochs: Number of training epochs
            batch_size: Batch size
            validation_split: Validation split ratio
            verbose: Verbosity level

        Returns:
            Training history
        """
        if len(prices_df) < self.sequence_length + 10:
            raise ValueError(f"Insufficient data. Need at least {self.sequence_length + 10} data points")

        X, y = self.prepare_data(prices_df)

        if self.model is None:
            self.build_model()

        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=verbose,
            shuffle=False
        )

        self.is_trained = True
        return history.history

    def predict(self, prices_df: pd.DataFrame, steps: int = 1) -> np.ndarray:
        """
        Predict future prices.

        Args:
            prices_df: Recent price data (last sequence_length days)
            steps: Number of steps ahead to predict

        Returns:
            Predicted prices
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        if len(prices_df) < self.sequence_length:
            raise ValueError(f"Need at least {self.sequence_length} data points for prediction")

        # Get last sequence
        features = prices_df[['open', 'high', 'low', 'close', 'volume']].values
        scaled_features = self.scaler.transform(features)
        last_sequence = scaled_features[-self.sequence_length:].reshape(1, self.sequence_length, self.features)

        predictions = []
        current_sequence = last_sequence.copy()

        for _ in range(steps):
            # Predict next step
            pred = self.model.predict(current_sequence, verbose=0)
            predictions.append(pred[0, 0])

            # Update sequence (simplified - in production, use actual next values)
            # For multi-step, we'd need to predict all features or use actual values
            new_row = current_sequence[0, -1, :].copy()
            new_row[3] = pred[0, 0]  # Update close price
            current_sequence = np.append(
                current_sequence[:, 1:, :],
                new_row.reshape(1, 1, self.features),
                axis=1
            )

        # Inverse transform predictions
        # Create dummy array for inverse transform
        dummy = np.zeros((len(predictions), self.features))
        dummy[:, 3] = predictions
        predictions_scaled = self.scaler.inverse_transform(dummy)[:, 3]

        return predictions_scaled

    def save(self, filepath: str):
        """Save model and scaler."""
        if self.model:
            self.model.save(filepath)
        scaler_path = filepath.replace('.h5', '_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)

    def load(self, filepath: str):
        """Load model and scaler."""
        self.model = keras.models.load_model(filepath)
        scaler_path = filepath.replace('.h5', '_scaler.pkl')
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        self.is_trained = True


class SignalClassifier:
    """
    Classification model for predicting BUY/HOLD/SELL signals.
    
    Uses features from technical indicators, fundamentals, and price trends.
    """

    def __init__(self):
        """Initialize signal classifier."""
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []

    def build_model(self, input_dim: int, num_classes: int = 3) -> keras.Model:
        """
        Build classification model.

        Args:
            input_dim: Number of input features
            num_classes: Number of classes (BUY/HOLD/SELL = 3)

        Returns:
            Compiled Keras model
        """
        model = models.Sequential([
            layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(32, activation='relu'),
            layers.Dense(num_classes, activation='softmax')
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        self.model = model
        return model

    def prepare_features(
        self,
        indicators: Dict[str, Any],
        fundamentals: Dict[str, Any],
        price_features: Dict[str, Any]
    ) -> np.ndarray:
        """
        Prepare feature vector from indicators, fundamentals, and price data.

        Args:
            indicators: Technical indicators
            fundamentals: Fundamental metrics
            price_features: Price-based features (trends, volatility)

        Returns:
            Feature vector
        """
        features = []

        # Technical indicators
        features.extend([
            indicators.get('rsi', 50) / 100,  # Normalize RSI
            indicators.get('macd', 0) or 0,
            indicators.get('macd_histogram', 0) or 0,
            indicators.get('sma_20', 0) or 0,
            indicators.get('sma_50', 0) or 0,
            indicators.get('sma_200', 0) or 0,
            indicators.get('bollinger_upper', 0) or 0,
            indicators.get('bollinger_lower', 0) or 0,
        ])

        # Fundamental features
        features.extend([
            fundamentals.get('pe_ratio', 20) / 100 if fundamentals.get('pe_ratio') else 0.2,
            fundamentals.get('earnings_growth', 0) / 100 if fundamentals.get('earnings_growth') else 0,
            fundamentals.get('debt_ratio', 50) / 100 if fundamentals.get('debt_ratio') else 0.5,
        ])

        # Price features
        features.extend([
            price_features.get('short_term_trend', 0) / 100,
            price_features.get('medium_term_trend', 0) / 100,
            price_features.get('volatility', 20) / 100,
            price_features.get('volume_ratio', 1),
        ])

        return np.array(features).reshape(1, -1)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 1
    ) -> Dict[str, Any]:
        """
        Train the classifier.

        Args:
            X: Feature matrix
            y: Labels (one-hot encoded: BUY=[1,0,0], HOLD=[0,1,0], SELL=[0,0,1])
            epochs: Number of epochs
            batch_size: Batch size
            validation_split: Validation split
            verbose: Verbosity level

        Returns:
            Training history
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        if self.model is None:
            self.build_model(input_dim=X_scaled.shape[1], num_classes=y.shape[1])

        history = self.model.fit(
            X_scaled, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=verbose
        )

        self.is_trained = True
        return history.history

    def predict(
        self,
        indicators: Dict[str, Any],
        fundamentals: Dict[str, Any],
        price_features: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        Predict signal class and confidence.

        Args:
            indicators: Technical indicators
            fundamentals: Fundamental metrics
            price_features: Price-based features

        Returns:
            Tuple of (signal_type, confidence_score)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        features = self.prepare_features(indicators, fundamentals, price_features)
        features_scaled = self.scaler.transform(features)

        predictions = self.model.predict(features_scaled, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx] * 100)

        signal_map = {0: 'BUY', 1: 'HOLD', 2: 'SELL'}
        signal_type = signal_map.get(class_idx, 'HOLD')

        return signal_type, confidence

    def save(self, filepath: str):
        """Save model and scaler."""
        if self.model:
            self.model.save(filepath)
        scaler_path = filepath.replace('.h5', '_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)

    def load(self, filepath: str):
        """Load model and scaler."""
        self.model = keras.models.load_model(filepath)
        scaler_path = filepath.replace('.h5', '_scaler.pkl')
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        self.is_trained = True
