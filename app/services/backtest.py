"""Backtesting service for signal performance analysis."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from app.models.signal import SignalHistory, SignalType
from app.models.price import StockPrice


class BacktestService:
    """Service for backtesting signal performance."""

    @staticmethod
    def calculate_signal_performance(
        stock_id: int,
        start_date: date,
        end_date: date,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for signals in a date range.

        Args:
            stock_id: Stock ID
            start_date: Start date for backtest
            end_date: End date for backtest
            db: Database session

        Returns:
            Dictionary with performance metrics
        """
        # Get signal history
        signals = (
            db.query(SignalHistory)
            .filter(
                SignalHistory.stock_id == stock_id,
                SignalHistory.created_at >= datetime.combine(start_date, datetime.min.time()),
                SignalHistory.created_at <= datetime.combine(end_date, datetime.max.time()),
            )
            .order_by(SignalHistory.created_at.asc())
            .all()
        )

        if not signals:
            return {
                "total_signals": 0,
                "error": "No signals found in date range",
            }

        # Get price data for the period
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

        if len(prices) < 2:
            return {
                "total_signals": len(signals),
                "error": "Insufficient price data for backtest",
            }

        # Convert to DataFrame
        prices_df = pd.DataFrame(
            [
                {
                    "time": p.time,
                    "close": p.close,
                }
                for p in prices
            ]
        )
        prices_df.set_index("time", inplace=True)

        # Simulate following signals
        trades = []
        current_position = None  # None, "BUY", or "SELL"
        entry_price = None
        entry_date = None

        for signal in signals:
            signal_date = signal.created_at.date()
            signal_type = signal.signal_type

            # Get price on signal date
            price_on_date = prices_df[prices_df.index.date == signal_date]
            if price_on_date.empty:
                # Find closest price
                price_on_date = prices_df.iloc[
                    (prices_df.index.date - signal_date).abs().argsort()[:1]
                ]
            if price_on_date.empty:
                continue

            current_price = float(price_on_date["close"].iloc[0])

            # Execute signal logic
            if signal_type == SignalType.BUY and current_position != "BUY":
                if current_position == "SELL":
                    # Close short position
                    if entry_price:
                        pnl = ((entry_price - current_price) / entry_price) * 100
                        trades.append(
                            {
                                "type": "SELL_CLOSE",
                                "entry_date": entry_date,
                                "exit_date": signal_date,
                                "entry_price": entry_price,
                                "exit_price": current_price,
                                "pnl_percent": pnl,
                                "signal_confidence": signal.confidence_score,
                            }
                        )
                # Open long position
                current_position = "BUY"
                entry_price = current_price
                entry_date = signal_date

            elif signal_type == SignalType.SELL and current_position != "SELL":
                if current_position == "BUY":
                    # Close long position
                    if entry_price:
                        pnl = ((current_price - entry_price) / entry_price) * 100
                        trades.append(
                            {
                                "type": "BUY_CLOSE",
                                "entry_date": entry_date,
                                "exit_date": signal_date,
                                "entry_price": entry_price,
                                "exit_price": current_price,
                                "pnl_percent": pnl,
                                "signal_confidence": signal.confidence_score,
                            }
                        )
                # Open short position
                current_position = "SELL"
                entry_price = current_price
                entry_date = signal_date

            elif signal_type == SignalType.HOLD:
                # Hold current position, no action
                pass

        # Close final position if still open
        if current_position and entry_price:
            final_price = float(prices_df["close"].iloc[-1])
            final_date = prices_df.index[-1].date()
            if current_position == "BUY":
                pnl = ((final_price - entry_price) / entry_price) * 100
            else:
                pnl = ((entry_price - final_price) / entry_price) * 100

            trades.append(
                {
                    "type": f"{current_position}_CLOSE",
                    "entry_date": entry_date,
                    "exit_date": final_date,
                    "entry_price": entry_price,
                    "exit_price": final_price,
                    "pnl_percent": pnl,
                    "signal_confidence": None,
                }
            )

        # Calculate metrics
        if not trades:
            return {
                "total_signals": len(signals),
                "total_trades": 0,
                "error": "No trades executed",
            }

        pnls = [t["pnl_percent"] for t in trades]
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]

        total_return = sum(pnls)
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0

        # Calculate drawdown
        cumulative_returns = []
        cumulative = 0
        for pnl in pnls:
            cumulative += pnl
            cumulative_returns.append(cumulative)

        if cumulative_returns:
            running_max = pd.Series(cumulative_returns).expanding().max()
            drawdown = (pd.Series(cumulative_returns) - running_max) / (running_max + 100)
            max_drawdown = drawdown.min() * 100
        else:
            max_drawdown = 0

        # Calculate volatility (std dev of returns)
        volatility = pd.Series(pnls).std() if len(pnls) > 1 else 0

        # Sharpe ratio (simplified, assuming risk-free rate = 0)
        sharpe_ratio = (total_return / len(trades)) / volatility if volatility > 0 else 0

        return {
            "total_signals": len(signals),
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "total_return_percent": round(total_return, 2),
            "average_return_per_trade": round(total_return / len(trades), 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "max_drawdown_percent": round(max_drawdown, 2),
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "trades": trades[-10:],  # Last 10 trades
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    @staticmethod
    def compare_to_benchmark(
        stock_id: int,
        start_date: date,
        end_date: date,
        benchmark_return: float,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Compare signal performance to a benchmark.

        Args:
            stock_id: Stock ID
            start_date: Start date
            end_date: End date
            benchmark_return: Benchmark return percentage
            db: Database session

        Returns:
            Comparison metrics
        """
        performance = BacktestService.calculate_signal_performance(
            stock_id, start_date, end_date, db
        )

        if "error" in performance:
            return performance

        signal_return = performance.get("total_return_percent", 0)
        outperformance = signal_return - benchmark_return

        return {
            **performance,
            "benchmark_return_percent": round(benchmark_return, 2),
            "outperformance_percent": round(outperformance, 2),
            "beat_benchmark": outperformance > 0,
        }
