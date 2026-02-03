"""Realistic backtesting service with transaction costs, slippage, and latency."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from app.models.signal import SignalHistory, SignalType
from app.models.price import StockPrice


class RealisticBacktestService:
    """
    Realistic backtesting that accounts for:
    - Transaction costs (commissions, spreads)
    - Slippage (difference between expected and executed price)
    - Execution latency (delay between signal and trade)
    - Market impact (large orders moving the market)
    """
    
    # Transaction cost parameters
    COMMISSION_RATE = 0.001  # 0.1% per trade (typical online broker)
    SPREAD_BPS = 5  # 5 basis points bid-ask spread (typical for liquid stocks)
    
    # Execution parameters
    EXECUTION_DELAY_SECONDS = 30  # 30 seconds to execute after signal
    SLIPPAGE_BPS_MARKET = 10  # 10 bps slippage for market orders
    SLIPPAGE_BPS_LIMIT = 2  # 2 bps slippage for limit orders (if not filled)
    
    # Market impact (for large orders)
    MARKET_IMPACT_BPS_PER_PCT = 0.5  # 0.5 bps per 1% of daily volume
    
    @staticmethod
    def calculate_transaction_costs(
        price: float,
        quantity: float,
        is_market_order: bool = True,
        daily_volume: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Calculate total transaction costs.
        
        Args:
            price: Execution price
            quantity: Number of shares
            is_market_order: Whether using market or limit order
            daily_volume: Daily trading volume (for market impact)
        
        Returns:
            Dictionary with cost breakdown
        """
        trade_value = price * quantity
        
        # Commission
        commission = trade_value * RealisticBacktestService.COMMISSION_RATE
        
        # Spread cost (half spread on entry, half on exit)
        spread_cost = trade_value * (RealisticBacktestService.SPREAD_BPS / 10000)
        
        # Slippage
        if is_market_order:
            slippage_bps = RealisticBacktestService.SLIPPAGE_BPS_MARKET
        else:
            slippage_bps = RealisticBacktestService.SLIPPAGE_BPS_LIMIT
        
        slippage_cost = trade_value * (slippage_bps / 10000)
        
        # Market impact (if order is large relative to daily volume)
        market_impact_cost = 0
        if daily_volume and daily_volume > 0:
            order_pct_of_volume = (quantity / daily_volume) * 100
            if order_pct_of_volume > 1:  # Order > 1% of daily volume
                impact_bps = order_pct_of_volume * RealisticBacktestService.MARKET_IMPACT_BPS_PER_PCT
                market_impact_cost = trade_value * (impact_bps / 10000)
        
        total_cost = commission + spread_cost + slippage_cost + market_impact_cost
        
        return {
            'commission': commission,
            'spread_cost': spread_cost,
            'slippage_cost': slippage_cost,
            'market_impact_cost': market_impact_cost,
            'total_cost': total_cost,
            'cost_percent': (total_cost / trade_value) * 100,
        }
    
    @staticmethod
    def apply_execution_delay(
        signal_time: datetime,
        prices_df: pd.DataFrame,
        delay_seconds: int = EXECUTION_DELAY_SECONDS,
    ) -> Optional[float]:
        """
        Apply execution delay and get actual execution price.
        
        Args:
            signal_time: When signal was generated
            prices_df: DataFrame with price data (indexed by time)
            delay_seconds: Execution delay in seconds
        
        Returns:
            Execution price or None if price not available
        """
        execution_time = signal_time + timedelta(seconds=delay_seconds)
        
        # Find closest price after execution time
        future_prices = prices_df[prices_df.index >= execution_time]
        
        if len(future_prices) == 0:
            # Use next available price
            future_prices = prices_df[prices_df.index > signal_time]
        
        if len(future_prices) == 0:
            return None
        
        # Use first available price after delay
        execution_price = float(future_prices.iloc[0]['close'])
        
        return execution_price
    
    @staticmethod
    def calculate_realistic_pnl(
        entry_price: float,
        exit_price: float,
        quantity: float,
        entry_time: datetime,
        exit_time: datetime,
        prices_df: pd.DataFrame,
        is_market_order: bool = True,
        daily_volume: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Calculate realistic PnL after all costs.
        
        Args:
            entry_price: Intended entry price
            exit_price: Intended exit price
            quantity: Number of shares
            entry_time: Entry signal time
            exit_time: Exit signal time
            prices_df: Price DataFrame
            is_market_order: Whether using market orders
            daily_volume: Daily trading volume
        
        Returns:
            Dictionary with PnL breakdown
        """
        # Apply execution delay to get actual prices
        actual_entry_price = RealisticBacktestService.apply_execution_delay(
            entry_time, prices_df
        ) or entry_price
        
        actual_exit_price = RealisticBacktestService.apply_execution_delay(
            exit_time, prices_df
        ) or exit_price
        
        # Calculate gross PnL
        gross_pnl = (actual_exit_price - actual_entry_price) * quantity
        
        # Calculate transaction costs
        entry_costs = RealisticBacktestService.calculate_transaction_costs(
            actual_entry_price, quantity, is_market_order, daily_volume
        )
        exit_costs = RealisticBacktestService.calculate_transaction_costs(
            actual_exit_price, quantity, is_market_order, daily_volume
        )
        
        total_costs = entry_costs['total_cost'] + exit_costs['total_cost']
        
        # Net PnL
        net_pnl = gross_pnl - total_costs
        
        # Calculate returns
        initial_value = actual_entry_price * quantity
        gross_return_pct = (gross_pnl / initial_value) * 100
        net_return_pct = (net_pnl / initial_value) * 100
        cost_impact_pct = (total_costs / initial_value) * 100
        
        return {
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'total_costs': total_costs,
            'gross_return_pct': gross_return_pct,
            'net_return_pct': net_return_pct,
            'cost_impact_pct': cost_impact_pct,
            'entry_price_intended': entry_price,
            'entry_price_actual': actual_entry_price,
            'exit_price_intended': exit_price,
            'exit_price_actual': actual_exit_price,
            'entry_costs': entry_costs,
            'exit_costs': exit_costs,
        }
    
    @staticmethod
    def backtest_with_costs(
        stock_id: int,
        start_date: date,
        end_date: date,
        db: Session,
        account_value: float = 100000,  # Starting capital
        risk_per_trade: float = 0.02,  # 2% risk per trade
    ) -> Dict[str, Any]:
        """
        Run realistic backtest with all costs accounted for.
        
        Args:
            stock_id: Stock ID
            start_date: Backtest start date
            end_date: Backtest end date
            db: Database session
            account_value: Starting account value
            risk_per_trade: Risk per trade as fraction
        
        Returns:
            Backtest results with realistic returns
        """
        # Get signals and prices (same as original backtest)
        from app.services.backtest import BacktestService
        performance = BacktestService.calculate_signal_performance(
            stock_id, start_date, end_date, db
        )
        
        if "error" in performance:
            return performance
        
        # Get price data for execution delays
        prices = (
            db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock_id,
                StockPrice.time >= datetime.combine(start_date, datetime.min.time()),
                StockPrice.time <= datetime.combine(end_date, datetime.max.time()),
            )
            .order_by(StockPrice.time.asc())
            .all()
        )
        
        prices_df = pd.DataFrame([
            {'time': p.time, 'close': p.close, 'volume': p.volume}
            for p in prices
        ])
        if len(prices_df) > 0:
            prices_df.set_index('time', inplace=True)
        
        # Recalculate with realistic costs
        trades = performance.get('trades', [])
        realistic_trades = []
        current_account = account_value
        
        for trade in trades:
            # Get daily volume for market impact
            trade_date = datetime.fromisoformat(trade['entry_date']) if isinstance(trade['entry_date'], str) else trade['entry_date']
            daily_volume = None
            if len(prices_df) > 0 and trade_date in prices_df.index:
                daily_volume = prices_df.loc[trade_date, 'volume']
            
            # Calculate position size based on risk
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            
            # Estimate stop-loss (3% for this example)
            stop_loss = entry_price * 0.97
            from app.services.risk_manager import RiskManager
            position_size = RiskManager.calculate_position_size(
                current_account, entry_price, stop_loss, risk_per_trade
            )
            
            quantity = position_size.quantity
            
            # Calculate realistic PnL
            entry_time = trade_date
            exit_time = datetime.fromisoformat(trade['exit_date']) if isinstance(trade['exit_date'], str) else trade['exit_date']
            
            realistic_pnl = RealisticBacktestService.calculate_realistic_pnl(
                entry_price, exit_price, quantity, entry_time, exit_time,
                prices_df, is_market_order=True, daily_volume=daily_volume
            )
            
            # Update account value
            current_account += realistic_pnl['net_pnl']
            
            realistic_trades.append({
                **trade,
                'realistic_pnl': realistic_pnl,
                'quantity': quantity,
                'account_value_after': current_account,
            })
        
        # Recalculate metrics with realistic returns
        realistic_pnls = [t['realistic_pnl']['net_return_pct'] for t in realistic_trades]
        total_realistic_return = sum(realistic_pnls)
        
        # Compare to naive backtest
        naive_return = performance.get('total_return_percent', 0)
        cost_impact = naive_return - total_realistic_return
        
        return {
            **performance,
            'realistic_total_return_pct': round(total_realistic_return, 2),
            'naive_total_return_pct': round(naive_return, 2),
            'cost_impact_pct': round(cost_impact, 2),
            'final_account_value': round(current_account, 2),
            'realistic_trades': realistic_trades[-10:],  # Last 10 trades
        }
