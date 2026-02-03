"""Triple Barrier Method for creating realistic trading labels.

This implements the Triple Barrier Method from "Advances in Financial Machine Learning"
by Marcos López de Prado. This prevents the "loophole" of using simple price targets
that ignore path-dependent risk (stop-losses, margin calls, etc.).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class BarrierType(Enum):
    """Type of barrier hit."""
    UPPER = "UPPER"  # Take-profit hit
    LOWER = "LOWER"  # Stop-loss hit
    TIME = "TIME"    # Time barrier hit first
    NONE = "NONE"    # No barrier hit (insufficient data)


class TripleBarrierLabeler:
    """
    Creates labels using Triple Barrier Method.
    
    The Triple Barrier Method creates labels based on which barrier is hit first:
    1. Upper barrier (take-profit) - BUY signal
    2. Lower barrier (stop-loss) - SELL signal  
    3. Time barrier (max holding period) - HOLD signal
    
    This is more realistic than simple "price at T+10" because it accounts for:
    - Path-dependent risk (stop-losses)
    - Volatility-adjusted targets
    - Maximum holding periods
    """
    
    def __init__(
        self,
        upper_barrier_pct: float = 0.05,  # 5% take-profit
        lower_barrier_pct: float = -0.03,  # 3% stop-loss
        max_holding_period: int = 20,  # 20 days max
        volatility_adjusted: bool = True,
        volatility_window: int = 20,
        min_volatility: float = 0.01,  # Minimum 1% volatility adjustment
    ):
        """
        Initialize Triple Barrier Labeler.
        
        Args:
            upper_barrier_pct: Take-profit percentage (e.g., 0.05 = 5%)
            lower_barrier_pct: Stop-loss percentage (e.g., -0.03 = -3%)
            max_holding_period: Maximum days to hold position
            volatility_adjusted: Whether to adjust barriers by volatility
            volatility_window: Days to calculate volatility
            min_volatility: Minimum volatility for adjustment
        """
        self.upper_barrier_pct = upper_barrier_pct
        self.lower_barrier_pct = lower_barrier_pct
        self.max_holding_period = max_holding_period
        self.volatility_adjusted = volatility_adjusted
        self.volatility_window = volatility_window
        self.min_volatility = min_volatility
    
    def calculate_volatility(self, prices: pd.Series, window: int) -> float:
        """Calculate historical volatility."""
        if len(prices) < window:
            return self.min_volatility
        
        returns = prices.pct_change().dropna()
        if len(returns) < window:
            return self.min_volatility
        
        vol = returns.tail(window).std()
        return max(vol, self.min_volatility)
    
    def create_labels(
        self,
        prices: pd.Series,
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Create labels using Triple Barrier Method.
        
        Args:
            prices: Series of closing prices
            start_idx: Starting index
            end_idx: Ending index (None = end of series)
        
        Returns:
            Tuple of (labels, barrier_types)
            - labels: 1 (BUY), -1 (SELL), 0 (HOLD)
            - barrier_types: Which barrier was hit
        """
        if end_idx is None:
            end_idx = len(prices)
        
        prices_subset = prices.iloc[start_idx:end_idx]
        
        if len(prices_subset) < self.max_holding_period + 1:
            return pd.Series(dtype=int), pd.Series(dtype=str)
        
        labels = []
        barrier_types = []
        
        for i in range(len(prices_subset) - self.max_holding_period):
            entry_idx = i
            entry_price = prices_subset.iloc[entry_idx]
            
            # Calculate volatility for adjustment
            if self.volatility_adjusted:
                historical_prices = prices_subset.iloc[max(0, entry_idx - self.volatility_window):entry_idx + 1]
                vol = self.calculate_volatility(historical_prices, self.volatility_window)
                # Adjust barriers: higher vol = wider barriers
                vol_multiplier = 1 + (vol * 2)  # Scale volatility impact
            else:
                vol_multiplier = 1.0
            
            # Calculate barrier prices
            upper_barrier = entry_price * (1 + self.upper_barrier_pct * vol_multiplier)
            lower_barrier = entry_price * (1 + self.lower_barrier_pct * vol_multiplier)
            
            # Look ahead window
            window_start = entry_idx + 1
            window_end = min(entry_idx + 1 + self.max_holding_period, len(prices_subset))
            window_prices = prices_subset.iloc[window_start:window_end]
            
            if len(window_prices) == 0:
                labels.append(0)
                barrier_types.append(BarrierType.NONE.value)
                continue
            
            # Check which barrier hit first
            hit_upper = (window_prices >= upper_barrier).any()
            hit_lower = (window_prices <= lower_barrier).any()
            
            if hit_upper:
                upper_hit_idx = (window_prices >= upper_barrier).idxmax()
            else:
                upper_hit_idx = None
            
            if hit_lower:
                lower_hit_idx = (window_prices <= lower_barrier).idxmax()
            else:
                lower_hit_idx = None
            
            # Determine which barrier hit first
            if hit_upper and hit_lower:
                # Both hit - check which came first
                if upper_hit_idx < lower_hit_idx:
                    labels.append(1)  # BUY
                    barrier_types.append(BarrierType.UPPER.value)
                else:
                    labels.append(-1)  # SELL
                    barrier_types.append(BarrierType.LOWER.value)
            elif hit_upper:
                labels.append(1)  # BUY
                barrier_types.append(BarrierType.UPPER.value)
            elif hit_lower:
                labels.append(-1)  # SELL
                barrier_types.append(BarrierType.LOWER.value)
            else:
                # Time barrier hit (max holding period reached)
                labels.append(0)  # HOLD
                barrier_types.append(BarrierType.TIME.value)
        
        return pd.Series(labels), pd.Series(barrier_types)
    
    def create_labels_for_horizon(
        self,
        prices: pd.Series,
        horizon: str  # 'SCALPING', 'SWING', 'INVESTING'
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Create labels adjusted for trading horizon.
        
        Args:
            prices: Price series
            horizon: Trading horizon
        
        Returns:
            Tuple of (labels, barrier_types)
        """
        if horizon == 'SCALPING':
            # 5-minute to 1-hour: tight barriers, short holding
            self.upper_barrier_pct = 0.01  # 1% take-profit
            self.lower_barrier_pct = -0.005  # 0.5% stop-loss
            self.max_holding_period = 12  # 12 periods (1 hour if 5-min bars)
        elif horizon == 'SWING':
            # 1-day to 1-week: moderate barriers
            self.upper_barrier_pct = 0.05  # 5% take-profit
            self.lower_barrier_pct = -0.03  # 3% stop-loss
            self.max_holding_period = 20  # 20 days
        elif horizon == 'INVESTING':
            # 1-month to 5-year: wide barriers, long holding
            self.upper_barrier_pct = 0.20  # 20% take-profit
            self.lower_barrier_pct = -0.10  # 10% stop-loss
            self.max_holding_period = 252  # 1 year (trading days)
        
        return self.create_labels(prices)
