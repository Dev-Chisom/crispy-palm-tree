"""Alpha feature engineering - market-neutral features that capture true alpha, not beta."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


class AlphaFeatureEngineer:
    """
    Creates market-neutral features that capture alpha (stock-specific returns)
    rather than beta (market exposure).
    
    This helps distinguish between:
    - Stock going up because market is up (beta)
    - Stock going up because of stock-specific factors (alpha)
    """
    
    @staticmethod
    def calculate_beta(
        stock_returns: pd.Series,
        market_returns: pd.Series,
        window: int = 252  # 1 year
    ) -> float:
        """
        Calculate stock's beta to market.
        
        Args:
            stock_returns: Stock returns series
            market_returns: Market/benchmark returns series
            window: Rolling window for calculation
        
        Returns:
            Beta coefficient
        """
        if len(stock_returns) < window or len(market_returns) < window:
            window = min(len(stock_returns), len(market_returns))
        
        if window < 2:
            return 1.0  # Default beta
        
        # Align series
        aligned = pd.DataFrame({
            'stock': stock_returns.tail(window),
            'market': market_returns.tail(window)
        }).dropna()
        
        if len(aligned) < 2:
            return 1.0
        
        # Calculate covariance and variance
        covariance = aligned['stock'].cov(aligned['market'])
        market_variance = aligned['market'].var()
        
        if market_variance == 0 or pd.isna(market_variance):
            return 1.0
        
        beta = covariance / market_variance
        return float(beta)
    
    @staticmethod
    def neutralize_market_beta(
        stock_returns: pd.Series,
        market_returns: pd.Series,
        beta: Optional[float] = None
    ) -> pd.Series:
        """
        Calculate market-neutral returns (alpha).
        
        Formula: alpha = stock_return - (beta * market_return)
        
        Args:
            stock_returns: Stock returns
            market_returns: Market returns
            beta: Pre-calculated beta (if None, calculates it)
        
        Returns:
            Alpha returns (market-neutral)
        """
        # Align series
        aligned = pd.DataFrame({
            'stock': stock_returns,
            'market': market_returns
        }).dropna()
        
        if len(aligned) < 2:
            return pd.Series(dtype=float)
        
        if beta is None:
            beta = AlphaFeatureEngineer.calculate_beta(
                aligned['stock'], aligned['market']
            )
        
        # Calculate alpha: stock_return - (beta * market_return)
        alpha = aligned['stock'] - (beta * aligned['market'])
        
        return alpha
    
    @staticmethod
    def create_alpha_features(
        stock_prices: pd.DataFrame,
        benchmark_prices: Optional[pd.DataFrame] = None,
        fundamentals: Optional[Dict[str, Any]] = None,
        sector_pe: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Create features that capture alpha, not beta.
        
        Args:
            stock_prices: Stock price DataFrame
            benchmark_prices: Benchmark (S&P 500) price DataFrame
            fundamentals: Fundamental metrics
            sector_pe: Sector average P/E
        
        Returns:
            Dictionary of alpha features
        """
        features = {}
        
        # Calculate returns
        stock_returns = stock_prices['close'].pct_change().dropna()
        
        if benchmark_prices is not None and len(benchmark_prices) > 0:
            benchmark_returns = benchmark_prices['close'].pct_change().dropna()
            
            # Align series
            aligned = pd.DataFrame({
                'stock': stock_returns,
                'market': benchmark_returns
            }).dropna()
            
            if len(aligned) >= 20:
                # Calculate beta
                beta = AlphaFeatureEngineer.calculate_beta(
                    aligned['stock'], aligned['market']
                )
                features['beta'] = beta
                
                # Calculate alpha returns
                alpha_returns = AlphaFeatureEngineer.neutralize_market_beta(
                    aligned['stock'], aligned['market'], beta
                )
                
                # Alpha-based features
                if len(alpha_returns) >= 5:
                    features['alpha_5d'] = alpha_returns.tail(5).mean()
                    features['alpha_5d_volatility'] = alpha_returns.tail(5).std()
                
                if len(alpha_returns) >= 20:
                    features['alpha_20d'] = alpha_returns.tail(20).mean()
                    features['alpha_20d_volatility'] = alpha_returns.tail(20).std()
                    features['alpha_sharpe'] = (
                        alpha_returns.tail(20).mean() / alpha_returns.tail(20).std()
                        if alpha_returns.tail(20).std() > 0 else 0
                    )
                
                # Market correlation
                features['market_correlation'] = aligned['stock'].corr(aligned['market'])
                
                # Relative strength vs market
                stock_cumulative = (1 + aligned['stock']).cumprod()
                market_cumulative = (1 + aligned['market']).cumprod()
                if len(stock_cumulative) > 0 and len(market_cumulative) > 0:
                    features['relative_strength'] = (
                        stock_cumulative.iloc[-1] / market_cumulative.iloc[-1]
                    )
        else:
            # No benchmark data - set defaults
            features['beta'] = 1.0
            features['market_correlation'] = 0.0
            features['alpha_5d'] = 0.0
            features['alpha_20d'] = 0.0
        
        # Sector-adjusted fundamental features
        if fundamentals and sector_pe:
            pe_ratio = fundamentals.get('pe_ratio')
            if pe_ratio and sector_pe:
                features['pe_vs_sector'] = pe_ratio - sector_pe
                features['pe_vs_sector_pct'] = ((pe_ratio - sector_pe) / sector_pe) * 100
        
        # Volatility-adjusted features
        if len(stock_returns) >= 20:
            stock_vol = stock_returns.tail(20).std()
            if benchmark_prices is not None and len(benchmark_prices) > 0:
                benchmark_returns = benchmark_prices['close'].pct_change().dropna()
                if len(benchmark_returns) >= 20:
                    market_vol = benchmark_returns.tail(20).std()
                    if market_vol > 0:
                        features['volatility_ratio'] = stock_vol / market_vol
        
        return features
