"""Risk management service for position sizing and stop-loss/take-profit calculation."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = "CONSERVATIVE"  # 1% risk per trade
    MODERATE = "MODERATE"  # 2% risk per trade
    AGGRESSIVE = "AGGRESSIVE"  # 3% risk per trade


@dataclass
class PositionSize:
    """Position sizing calculation result."""
    quantity: float
    stop_loss_price: float
    take_profit_price: float
    risk_amount: float
    max_loss_percent: float
    target_profit_percent: float
    risk_reward_ratio: float


class RiskManager:
    """
    Risk management service for calculating position sizes,
    stop-losses, and take-profit levels.
    """
    
    # Default risk parameters
    DEFAULT_RISK_PER_TRADE = 0.02  # 2% of account per trade
    DEFAULT_RISK_REWARD_RATIO = 2.0  # Risk $1 to make $2
    DEFAULT_MAX_POSITION_SIZE = 0.10  # Max 10% of account in single position
    
    @staticmethod
    def calculate_position_size(
        account_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade: float = DEFAULT_RISK_PER_TRADE,
        risk_reward_ratio: float = DEFAULT_RISK_REWARD_RATIO,
        max_position_pct: float = DEFAULT_MAX_POSITION_SIZE,
    ) -> PositionSize:
        """
        Calculate position size based on risk management principles.
        
        Uses the formula:
        Quantity = (Account Value * Risk Per Trade) / (Entry Price - Stop Loss Price)
        
        Args:
            account_value: Total account value
            entry_price: Intended entry price
            stop_loss_price: Stop-loss price
            risk_per_trade: Percentage of account to risk per trade (default 2%)
            risk_reward_ratio: Target profit / risk (default 2:1)
            max_position_pct: Maximum position size as % of account
        
        Returns:
            PositionSize object with calculated values
        """
        # Validate inputs
        if account_value <= 0:
            raise ValueError("Account value must be positive")
        if entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if stop_loss_price <= 0:
            raise ValueError("Stop loss price must be positive")
        
        # Calculate price risk
        if entry_price > stop_loss_price:
            # Long position: stop loss below entry
            price_risk = entry_price - stop_loss_price
        else:
            # Short position: stop loss above entry
            price_risk = stop_loss_price - entry_price
        
        if price_risk == 0:
            raise ValueError("Stop loss price cannot equal entry price")
        
        # Calculate risk amount
        risk_amount = account_value * risk_per_trade
        
        # Calculate position size
        quantity = risk_amount / price_risk
        
        # Apply maximum position size limit
        max_position_value = account_value * max_position_pct
        max_quantity_by_size = max_position_value / entry_price
        quantity = min(quantity, max_quantity_by_size)
        
        # Recalculate actual risk based on capped quantity
        actual_risk_amount = quantity * price_risk
        
        # Calculate take-profit based on risk-reward ratio
        if entry_price > stop_loss_price:
            # Long: take profit above entry
            take_profit_price = entry_price + (price_risk * risk_reward_ratio)
        else:
            # Short: take profit below entry
            take_profit_price = entry_price - (price_risk * risk_reward_ratio)
        
        # Calculate percentages
        max_loss_percent = (price_risk / entry_price) * 100
        target_profit_percent = (abs(take_profit_price - entry_price) / entry_price) * 100
        
        return PositionSize(
            quantity=quantity,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            risk_amount=actual_risk_amount,
            max_loss_percent=max_loss_percent,
            target_profit_percent=target_profit_percent,
            risk_reward_ratio=risk_reward_ratio,
        )
    
    @staticmethod
    def calculate_stop_loss(
        entry_price: float,
        volatility: float,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        atr_multiplier: float = 2.0,
    ) -> float:
        """
        Calculate stop-loss price based on volatility.
        
        Uses Average True Range (ATR) or volatility-based approach.
        
        Args:
            entry_price: Entry price
            volatility: Historical volatility (as decimal, e.g., 0.20 = 20%)
            risk_level: Risk tolerance level
            atr_multiplier: ATR multiplier for stop distance
        
        Returns:
            Stop-loss price
        """
        # Risk level determines stop distance
        risk_multipliers = {
            RiskLevel.CONSERVATIVE: 1.5,
            RiskLevel.MODERATE: 2.0,
            RiskLevel.AGGRESSIVE: 3.0,
        }
        
        multiplier = risk_multipliers.get(risk_level, 2.0)
        
        # Calculate stop distance based on volatility
        stop_distance = entry_price * volatility * multiplier * atr_multiplier
        
        # For long positions, stop is below entry
        stop_loss = entry_price - stop_distance
        
        # Ensure stop is reasonable (not negative, not too close)
        min_stop_distance = entry_price * 0.01  # At least 1% away
        stop_loss = max(stop_loss, entry_price - (entry_price * 0.20))  # Max 20% stop
        
        return stop_loss
    
    @staticmethod
    def calculate_take_profit(
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float = 2.0,
    ) -> float:
        """
        Calculate take-profit price based on risk-reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop-loss price
            risk_reward_ratio: Desired profit/risk ratio
        
        Returns:
            Take-profit price
        """
        price_risk = abs(entry_price - stop_loss_price)
        
        if entry_price > stop_loss_price:
            # Long position
            take_profit = entry_price + (price_risk * risk_reward_ratio)
        else:
            # Short position
            take_profit = entry_price - (price_risk * risk_reward_ratio)
        
        return take_profit
    
    @staticmethod
    def validate_position_risk(
        account_value: float,
        position_value: float,
        max_portfolio_risk: float = 0.10,  # Max 10% of portfolio at risk
    ) -> Dict[str, Any]:
        """
        Validate that position doesn't exceed portfolio risk limits.
        
        Args:
            account_value: Total account value
            position_value: Value of position
            max_portfolio_risk: Maximum % of portfolio that can be at risk
        
        Returns:
            Validation result with warnings if limits exceeded
        """
        position_pct = (position_value / account_value) * 100
        is_valid = position_pct <= (max_portfolio_risk * 100)
        
        warnings = []
        if position_pct > 20:
            warnings.append(f"Position size ({position_pct:.2f}%) exceeds 20% of portfolio")
        if position_pct > max_portfolio_risk * 100:
            warnings.append(f"Position exceeds maximum risk limit ({max_portfolio_risk * 100}%)")
        
        return {
            'is_valid': is_valid,
            'position_percent': position_pct,
            'warnings': warnings,
        }
