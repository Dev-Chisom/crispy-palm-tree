# 🔬 QUANT & ML SYSTEMS ARCHITECTURE AUDIT
## Lead Quant & ML Systems Architect Review

**Date:** 2026-02-03  
**Platform:** SignalIQ - Buy/Hold/Sell Signal Generation System  
**Reviewer Perspective:** Production-grade quant trading system standards

---

## 🚨 CRITICAL FINDINGS

### 1. ❌ **TARGET VARIABLE DEFINITION - MAJOR FLAW**

**Current Implementation:**
- **Rule-based signals:** Fixed thresholds (score > 60 = BUY, < 40 = SELL)
- **ML Classifier:** Trained on historical signals (circular dependency - signals label themselves)
- **LSTM:** Predicts price at T+5, then converts to signal if change > 3%

**Problems:**
1. **No Triple Barrier Method:** Uses simple "price at T+5" or "score threshold" - ignores path-dependent risk
2. **No volatility adjustment:** A 3% move on a 50% volatility stock is different from 3% on a 10% volatility stock
3. **Fixed percentage targets:** Doesn't account for stop-losses or margin calls
4. **Label leakage:** Training labels are generated from the same rule-based system being "improved"

**Impact:** Model will fail in production when:
- Stock drops 30% before hitting target (would have been stopped out)
- High volatility stocks trigger false signals
- Market regime changes (bull → bear)

**Fix Required:**
```python
# Implement Triple Barrier Method
def create_triple_barrier_labels(
    prices: pd.Series,
    upper_barrier: float,  # Take-profit (e.g., 5%)
    lower_barrier: float,   # Stop-loss (e.g., -3%)
    max_holding_period: int,  # Time barrier (e.g., 20 days)
    volatility_adjusted: bool = True
) -> pd.Series:
    """
    Create labels using Triple Barrier Method:
    - Upper barrier (take-profit) hit first → BUY label
    - Lower barrier (stop-loss) hit first → SELL label
    - Time barrier hit first → HOLD label
    - Adjust barriers by volatility if enabled
    """
    labels = []
    for i in range(len(prices) - max_holding_period):
        entry_price = prices.iloc[i]
        window = prices.iloc[i:i+max_holding_period+1]
        
        # Volatility-adjusted barriers
        if volatility_adjusted:
            vol = prices.iloc[max(0, i-20):i].pct_change().std()
            upper = entry_price * (1 + upper_barrier * (1 + vol * 2))
            lower = entry_price * (1 + lower_barrier * (1 + vol * 2))
        else:
            upper = entry_price * (1 + upper_barrier)
            lower = entry_price * (1 + lower_barrier)
        
        # Check which barrier hit first
        hit_upper = (window > upper).any()
        hit_lower = (window < lower).any()
        
        if hit_upper and not hit_lower:
            labels.append(1)  # BUY
        elif hit_lower and not hit_upper:
            labels.append(-1)  # SELL
        else:
            labels.append(0)  # HOLD
    
    return pd.Series(labels)
```

---

### 2. ❌ **HORIZON MISMATCH - CRITICAL ISSUE**

**Current Implementation:**
- **Holding Period:** SHORT/MEDIUM/LONG (determined by volatility, not actual strategy)
- **Features:** Same features used for all horizons (20-day, 50-day, 200-day trends)
- **No separation:** 5-minute scalping features mixed with 5-year investment features

**Problems:**
1. **Short-term noise in long-term signals:** Daily volatility affects "LONG" signals
2. **No timeframe-specific models:** Same LSTM/classifier for all horizons
3. **Feature contamination:** RSI (14-day) used for both swing trading and buy-and-hold

**Impact:**
- Long-term investors get whipsawed by daily noise
- Short-term traders miss intraday opportunities
- Model can't distinguish between scalping and investing strategies

**Fix Required:**
```python
# Separate feature engineering by horizon
class HorizonAwareFeatureEngineer:
    @staticmethod
    def get_features_for_horizon(
        prices_df: pd.DataFrame,
        horizon: str  # 'SCALPING', 'SWING', 'INVESTING'
    ) -> Dict[str, Any]:
        if horizon == 'SCALPING':
            # 5-minute to 1-hour features
            return {
                'rsi_5m': calculate_rsi(prices_df, period=5),
                'volume_spike': detect_volume_spike(prices_df, window=5),
                'bid_ask_spread': get_spread(prices_df),
                'order_flow': get_order_flow_imbalance(prices_df),
            }
        elif horizon == 'SWING':
            # 1-day to 1-week features
            return {
                'rsi_14': calculate_rsi(prices_df, period=14),
                'macd': calculate_macd(prices_df),
                'sma_cross': detect_sma_crossover(prices_df),
                'momentum_5d': calculate_momentum(prices_df, days=5),
            }
        elif horizon == 'INVESTING':
            # 1-month to 5-year features
            return {
                'earnings_trend': get_earnings_trend(fundamentals),
                'revenue_growth_5y': calculate_revenue_growth(fundamentals, years=5),
                'dividend_yield': fundamentals.get('dividend_yield'),
                'pe_ratio_vs_sector': compare_pe_to_sector(fundamentals),
                'debt_to_equity': fundamentals.get('debt_ratio'),
            }
```

---

### 3. ❌ **SURVIVORSHIP BIAS - DATA PIPELINE FLAW**

**Current Implementation:**
- **Stock filtering:** Only `is_active = True` stocks
- **Data fetching:** Only fetches data for stocks that exist now
- **No delisted tracking:** Stocks that went bankrupt are excluded

**Problems:**
1. **Training only on winners:** Model never sees stocks that failed
2. **No bankruptcy data:** Missing critical "SELL" signals from companies that went to zero
3. **Selection bias:** Only analyzing stocks that survived to today

**Impact:**
- Model overestimates success rate
- Missing critical negative examples (stocks that went to $0)
- Backtest results are inflated (only tested on survivors)

**Fix Required:**
```python
# Track delisted/bankrupt stocks
class Stock(Base):
    # ... existing fields ...
    is_delisted = Column(Boolean, default=False, nullable=False)
    delisted_date = Column(DateTime, nullable=True)
    delisting_reason = Column(String(50), nullable=True)  # 'BANKRUPTCY', 'MERGER', 'VOLUNTARY'

# Include delisted stocks in training
def prepare_training_data_with_delisted(
    include_delisted: bool = True,
    include_bankrupt: bool = True
):
    query = db.query(Stock)
    if include_delisted:
        # Include delisted stocks
        pass
    else:
        query = query.filter(Stock.is_active == True)
    
    if include_bankrupt:
        # Explicitly include bankrupt stocks for negative examples
        query = query.filter(
            (Stock.is_active == True) | 
            (Stock.delisting_reason == 'BANKRUPTCY')
        )
```

---

### 4. ❌ **BACKTESTING REALISM - MISSING CRITICAL COSTS**

**Current Implementation:**
- **No slippage:** Assumes perfect execution at signal price
- **No latency:** Assumes instant signal execution
- **No transaction costs:** No commissions, spreads, or fees
- **Perfect fills:** Gets exact price from database

**Problems:**
1. **Unrealistic returns:** Backtest shows 20% return, reality might be 5% after costs
2. **No execution delay:** Assumes you can trade at the exact moment signal is generated
3. **No market impact:** Large orders don't move the market in backtest

**Impact:**
- Overestimated performance
- Production returns will be significantly lower
- Strategy may be unprofitable after real-world costs

**Fix Required:**
```python
class RealisticBacktestService:
    # Transaction costs
    COMMISSION_RATE = 0.001  # 0.1% per trade
    SPREAD_BPS = 5  # 5 basis points bid-ask spread
    
    # Execution parameters
    EXECUTION_DELAY_SECONDS = 30  # 30 seconds to execute after signal
    SLIPPAGE_BPS = 10  # 10 bps slippage for market orders
    
    @staticmethod
    def calculate_realistic_pnl(
        entry_price: float,
        exit_price: float,
        quantity: float,
        is_market_order: bool = True
    ) -> float:
        # Apply slippage
        if is_market_order:
            entry_price_executed = entry_price * (1 + SLIPPAGE_BPS / 10000)
            exit_price_executed = exit_price * (1 - SLIPPAGE_BPS / 10000)
        else:
            entry_price_executed = entry_price
            exit_price_executed = exit_price
        
        # Calculate gross PnL
        gross_pnl = (exit_price_executed - entry_price_executed) * quantity
        
        # Subtract transaction costs
        entry_cost = entry_price_executed * quantity * COMMISSION_RATE
        exit_cost = exit_price_executed * quantity * COMMISSION_RATE
        spread_cost = entry_price_executed * quantity * (SPREAD_BPS / 10000)
        
        net_pnl = gross_pnl - entry_cost - exit_cost - spread_cost
        
        return net_pnl
```

---

### 5. ❌ **RISK MANAGEMENT - MISSING STOP-LOSS/TAKE-PROFIT**

**Current Implementation:**
- **No stop-loss logic:** Signals don't include stop-loss prices
- **No take-profit targets:** No explicit profit-taking levels
- **No position sizing:** Doesn't calculate position size based on risk
- **No risk limits:** No maximum drawdown or position limits

**Problems:**
1. **Unbounded losses:** A BUY signal can lose 50%+ with no exit
2. **No profit protection:** Doesn't lock in gains at target levels
3. **No risk-adjusted sizing:** All positions treated equally

**Impact:**
- Catastrophic losses possible (single trade can wipe out account)
- No systematic risk management
- Can't implement proper portfolio risk controls

**Fix Required:**
```python
class RiskManager:
    @staticmethod
    def calculate_position_size(
        account_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float = 0.02  # Risk 2% of account per trade
    ) -> Dict[str, float]:
        """
        Calculate position size based on risk.
        
        Returns:
            {
                'quantity': shares to buy,
                'stop_loss_price': price to exit if loss,
                'take_profit_price': price to exit if profit,
                'risk_amount': dollar amount at risk
            }
        """
        risk_amount = account_value * risk_per_trade
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return {'quantity': 0, 'error': 'Stop loss equals entry price'}
        
        quantity = risk_amount / price_risk
        
        # Calculate take-profit (risk:reward = 1:2)
        take_profit_price = entry_price + (2 * price_risk)
        
        return {
            'quantity': quantity,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'risk_amount': risk_amount,
            'max_loss_percent': (price_risk / entry_price) * 100,
            'target_profit_percent': ((take_profit_price - entry_price) / entry_price) * 100
        }
```

---

### 6. ❌ **FEATURE NEUTRALIZATION - CAPTURING BETA, NOT ALPHA**

**Current Implementation:**
- **No market neutralization:** Features don't subtract market/S&P 500 returns
- **No sector adjustment:** P/E ratios compared to sector, but not market-adjusted
- **No beta calculation:** Doesn't account for stock's correlation to market
- **No alpha isolation:** Can't distinguish stock-specific vs market-wide moves

**Problems:**
1. **Following the market:** BUY signals might just be "market is going up"
2. **No alpha generation:** Returns might just be beta (market exposure)
3. **False skill:** Model appears to work but is just tracking S&P 500

**Impact:**
- Model fails when market turns bearish
- No true edge - just market timing
- Can't generate alpha in sideways markets

**Fix Required:**
```python
class AlphaFeatureEngineer:
    @staticmethod
    def neutralize_market_beta(
        stock_returns: pd.Series,
        market_returns: pd.Series  # S&P 500 or benchmark
    ) -> pd.Series:
        """
        Calculate market-neutral returns (alpha).
        
        Returns stock returns minus market beta exposure.
        """
        # Calculate beta
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        beta = covariance / market_variance if market_variance > 0 else 1.0
        
        # Neutralize: alpha = stock_return - (beta * market_return)
        alpha = stock_returns - (beta * market_returns)
        
        return alpha
    
    @staticmethod
    def create_alpha_features(
        stock_prices: pd.DataFrame,
        benchmark_prices: pd.DataFrame,
        fundamentals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create features that capture alpha, not beta.
        """
        stock_returns = stock_prices['close'].pct_change()
        benchmark_returns = benchmark_prices['close'].pct_change()
        
        # Market-neutral returns
        alpha_returns = AlphaFeatureEngineer.neutralize_market_beta(
            stock_returns, benchmark_returns
        )
        
        # Alpha-based features
        return {
            'alpha_5d': alpha_returns.tail(5).mean(),
            'alpha_20d': alpha_returns.tail(20).mean(),
            'alpha_volatility': alpha_returns.std(),
            'alpha_sharpe': alpha_returns.mean() / alpha_returns.std() if alpha_returns.std() > 0 else 0,
            'beta': calculate_beta(stock_returns, benchmark_returns),
            'market_correlation': stock_returns.corr(benchmark_returns),
            # Sector-adjusted P/E
            'pe_vs_sector_alpha': fundamentals.get('pe_ratio', 0) - fundamentals.get('sector_pe', 0),
        }
```

---

### 7. ❌ **INFORMATION LEAKAGE - SCALING VIOLATION**

**Current Implementation:**
```python
# app/ml/models.py line 77
scaled_features = self.scaler.fit_transform(features)  # ❌ LEAKAGE!
```

**Problem:**
- `fit_transform()` uses **entire dataset** to calculate mean/std
- Model "sees the future" during training
- In production, model won't have future statistics

**Impact:**
- Training performance is inflated
- Production performance will be much worse
- Model is overfitted to historical data

**Fix Required:**
```python
class TimeSeriesScaler:
    """
    Rolling window scaler to prevent information leakage.
    """
    def __init__(self, window_size: int = 252):  # 1 year rolling
        self.window_size = window_size
    
    def fit_transform_rolling(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Scale using only past data (expanding or rolling window).
        """
        scaled_data = data.copy()
        
        for i in range(len(data)):
            # Use only data up to current point
            window_start = max(0, i - self.window_size)
            window_data = data.iloc[window_start:i+1]
            
            if len(window_data) > 1:
                mean = window_data.mean()
                std = window_data.std()
                # Avoid division by zero
                std = std.replace(0, 1)
                
                scaled_data.iloc[i] = (data.iloc[i] - mean) / std
        
        return scaled_data
```

---

### 8. ❌ **DATA SNOOPING - INDICATOR SELECTION BIAS**

**Current Implementation:**
- **Fixed indicators:** RSI, MACD, SMA, Bollinger Bands (hardcoded)
- **No validation:** Indicators selected without out-of-sample testing
- **No walk-forward analysis:** Same indicators used across all time periods

**Problems:**
1. **Overfitting to history:** These indicators might have worked by chance
2. **No robustness testing:** Haven't tested if indicators work in different market regimes
3. **Selection bias:** If you tested 100 indicators and picked these 4, that's data snooping

**Impact:**
- Indicators may fail in future market conditions
- No statistical significance testing
- False confidence in selected features

**Fix Required:**
```python
class RobustIndicatorSelector:
    """
    Statistically validate indicators using walk-forward analysis.
    """
    @staticmethod
    def validate_indicator_robustness(
        indicator_func: Callable,
        prices: pd.DataFrame,
        n_splits: int = 5,
        min_significance: float = 0.05
    ) -> Dict[str, Any]:
        """
        Test indicator across multiple time periods.
        
        Returns:
            {
                'is_robust': bool,
                'p_value': float,
                'sharpe_consistency': float,
                'regime_stability': float
            }
        """
        # Walk-forward validation
        results = []
        for split in range(n_splits):
            train_end = len(prices) * (split + 1) / (n_splits + 1)
            test_start = train_end
            test_end = len(prices) * (split + 2) / (n_splits + 1)
            
            train_data = prices.iloc[:int(train_end)]
            test_data = prices.iloc[int(test_start):int(test_end)]
            
            # Calculate indicator on training data
            indicator_values = indicator_func(train_data)
            
            # Test on out-of-sample data
            performance = backtest_indicator(indicator_values, test_data)
            results.append(performance)
        
        # Statistical significance
        p_value = calculate_statistical_significance(results)
        is_robust = p_value < min_significance
        
        return {
            'is_robust': is_robust,
            'p_value': p_value,
            'mean_sharpe': np.mean([r['sharpe'] for r in results]),
            'sharpe_std': np.std([r['sharpe'] for r in results]),
        }
```

---

## 📊 SEVERITY ASSESSMENT

| Issue | Severity | Production Risk | Fix Priority |
|-------|----------|------------------|--------------|
| Target Variable (No Triple Barrier) | 🔴 **CRITICAL** | Model will fail in volatile markets | **P0** |
| Information Leakage (Scaling) | 🔴 **CRITICAL** | Training performance ≠ Production | **P0** |
| Horizon Mismatch | 🟠 **HIGH** | Wrong signals for wrong strategies | **P1** |
| No Risk Management | 🟠 **HIGH** | Unbounded losses possible | **P1** |
| Survivorship Bias | 🟠 **HIGH** | Inflated backtest results | **P1** |
| No Slippage/Latency | 🟡 **MEDIUM** | Overestimated returns | **P2** |
| Feature Neutralization | 🟡 **MEDIUM** | Capturing beta, not alpha | **P2** |
| Data Snooping | 🟡 **MEDIUM** | Indicators may fail in future | **P2** |

---

## 🛠️ RECOMMENDED FIXES (Priority Order)

### **P0 - IMMEDIATE (Before Production)**

1. **Implement Triple Barrier Method for labels**
2. **Fix information leakage in scaling** (use rolling window)
3. **Add stop-loss/take-profit to signals**

### **P1 - HIGH PRIORITY (Next Sprint)**

4. **Separate models by horizon** (scalping vs investing)
5. **Include delisted stocks in training**
6. **Add realistic transaction costs to backtest**

### **P2 - MEDIUM PRIORITY (Future Enhancement)**

7. **Neutralize market beta in features**
8. **Validate indicators with walk-forward analysis**
9. **Add position sizing based on risk**

---

## 💡 ARCHITECTURAL RECOMMENDATIONS

1. **Separate Signal Generation by Horizon:**
   - `ScalpingSignalGenerator` (5min-1hr)
   - `SwingSignalGenerator` (1d-1wk)
   - `InvestingSignalGenerator` (1mo-5yr)

2. **Implement Proper Labeling Pipeline:**
   - Use Triple Barrier Method
   - Volatility-adjusted targets
   - Path-dependent risk assessment

3. **Add Risk Management Layer:**
   - Stop-loss calculation
   - Position sizing
   - Portfolio risk limits

4. **Realistic Backtesting:**
   - Slippage simulation
   - Transaction costs
   - Execution latency

5. **Alpha Generation:**
   - Market-neutral features
   - Beta-adjusted returns
   - Sector-relative metrics

---

## ⚠️ CURRENT SYSTEM STATUS

**Can be used for:** Educational purposes, proof-of-concept, basic signal generation

**NOT ready for:** Production trading, live capital deployment, institutional use

**Critical gaps prevent production deployment without significant refactoring.**

---

## 📝 NEXT STEPS

1. Review this audit with quant team
2. Prioritize fixes based on business needs
3. Implement P0 fixes immediately
4. Re-test with realistic backtesting
5. Validate on out-of-sample data
6. Consider hiring quant consultant for production deployment
