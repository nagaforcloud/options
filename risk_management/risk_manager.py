"""
Risk Management module for Options Wheel Strategy Trading Bot
Handles risk calculations, limits, and monitoring
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Position, Trade
from models.enums import StrategyType, TransactionType
from config.config import config
from config.config import config
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_utils import logger
from datetime import datetime
import math


@dataclass
class RiskConfig:
    """Configuration for risk management parameters"""
    daily_loss_limit: float = config.max_daily_loss_limit
    position_size_limit: float = 0.10  # Max 10% of portfolio per position
    portfolio_risk_limit: float = config.max_portfolio_risk  # Max 2% portfolio risk
    max_concurrent_positions: int = config.max_concurrent_positions
    margin_utilization_limit: float = 0.95  # Max 95% margin utilization
    max_portfolio_value_at_risk: float = 0.15  # Max 15% of portfolio value at risk


@dataclass
class PositionRisk:
    """Risk metrics for an individual position"""
    symbol: str
    position_size_percentage: float
    margin_used: float
    risk_contribution: float
    delta: float
    gamma: float
    theta: float
    vega: float
    underlying_price: float
    position_value: float


class RiskManager:
    """Manages risk for the trading strategy"""
    
    def __init__(self, risk_config: Optional[RiskConfig] = None):
        """
        Initialize risk manager
        
        Args:
            risk_config: Risk configuration parameters
        """
        self.risk_config = risk_config or RiskConfig()
        self.daily_pnl = 0.0
        self.daily_losses = 0.0
        self.current_positions = {}
        self.trades_today = []
        self.portfolio_value = 0.0  # To be updated externally
        self.cash_available = 0.0  # To be updated externally
        self.margin_available = 0.0  # To be updated externally
        self.margin_used = 0.0  # To be updated externally
        
        logger.info("Risk Manager initialized")
    
    def update_portfolio_value(self, portfolio_value: float):
        """Update the current portfolio value"""
        self.portfolio_value = portfolio_value
        logger.debug(f"Portfolio value updated to: {portfolio_value}")
    
    def update_cash_available(self, cash_available: float):
        """Update the available cash"""
        self.cash_available = cash_available
        logger.debug(f"Cash available updated to: {cash_available}")
    
    def update_margin_info(self, margin_available: float, margin_used: float):
        """Update margin information"""
        self.margin_available = margin_available
        self.margin_used = margin_used
        logger.debug(f"Margin info updated - Available: {margin_available}, Used: {margin_used}")
    
    def should_place_order(self, trade: Trade, position: Optional[Position] = None) -> Tuple[bool, str]:
        """
        Determine if an order should be placed based on risk limits
        
        Args:
            trade: Trade to be placed
            position: Position information if applicable
            
        Returns:
            Tuple of (should_place, reason)
        """
        try:
            # Check daily loss limit
            if self.daily_losses >= self.risk_config.daily_loss_limit:
                return False, f"Daily loss limit exceeded: {self.daily_losses} >= {self.risk_config.daily_loss_limit}"
            
            # Check maximum concurrent positions
            if len(self.current_positions) >= self.risk_config.max_concurrent_positions:
                return False, f"Maximum concurrent positions reached: {len(self.current_positions)} >= {self.risk_config.max_concurrent_positions}"
            
            # Calculate position value
            position_value = abs(trade.price * trade.quantity)
            
            # Check position size limit (10% of portfolio)
            if self.portfolio_value > 0:
                position_size_percentage = position_value / self.portfolio_value
                if position_size_percentage > self.risk_config.position_size_limit:
                    return False, f"Position size exceeds limit: {position_size_percentage:.2%} > {self.risk_config.position_size_limit:.2%}"
            
            # Check if there's sufficient cash/margin available
            required_margin = self._calculate_required_margin(trade)
            if self.cash_available < required_margin:
                return False, f"Insufficient margin: Available {self.cash_available}, Required {required_margin}"
            
            # Check margin utilization
            if self.margin_available > 0:
                margin_utilization = (self.margin_used + required_margin) / (self.margin_available + self.margin_used)
                if margin_utilization > self.risk_config.margin_utilization_limit:
                    return False, f"Margin utilization exceeds limit: {margin_utilization:.2%} > {self.risk_config.margin_utilization_limit:.2%}"
            
            # If we reached here, the order is within risk limits
            logger.debug(f"Order approved for {trade.symbol}: {trade.transaction_type} {trade.quantity} @ {trade.price}")
            return True, "Order approved"
            
        except Exception as e:
            logger.error(f"Error in should_place_order: {e}")
            return False, f"Risk check failed: {str(e)}"
    
    def _calculate_required_margin(self, trade: Trade) -> float:
        """
        Calculate required margin for a trade
        
        Args:
            trade: Trade for which to calculate margin
            
        Returns:
            Required margin amount
        """
        # This is a simplified calculation - in real scenario, you'd use Kite's margin calculator
        if trade.transaction_type == TransactionType.BUY.value:
            # For buying options, margin is typically the premium amount
            return trade.price * trade.quantity
        else:
            # For selling options, margin requirements are more complex
            # This is a placeholder - real implementation would depend on option type and strike
            if "CE" in trade.symbol or "PE" in trade.symbol:  # Option
                # For selling options, we might need to calculate margin based on underlying
                # This is a simplified estimate
                return min(trade.price * trade.quantity * 2, self.risk_config.daily_loss_limit)
            else:  # Equity
                return trade.price * trade.quantity * 0.2  # 20% margin for equity
    
    def track_position(self, position: Position):
        """Track a new position"""
        self.current_positions[position.symbol] = position
        logger.info(f"Position tracked: {position.symbol}, Quantity: {position.quantity}")
    
    def remove_position(self, symbol: str):
        """Remove a position from tracking"""
        if symbol in self.current_positions:
            del self.current_positions[symbol]
            logger.info(f"Position removed: {symbol}")
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L and track losses"""
        self.daily_pnl += pnl
        if pnl < 0:
            self.daily_losses += abs(pnl)
        logger.debug(f"Daily P&L updated: {self.daily_pnl}, Daily losses: {self.daily_losses}")
    
    def add_trade(self, trade: Trade):
        """Add a trade to today's tracking"""
        self.trades_today.append(trade)
        logger.debug(f"Trade added to daily tracking: {trade.order_id}")
    
    def reset_daily_metrics(self):
        """Reset daily metrics at the start of a new trading day"""
        self.daily_pnl = 0.0
        self.daily_losses = 0.0
        self.trades_today = []
        logger.info("Daily metrics reset")
    
    def calculate_position_risk(self, position: Position) -> PositionRisk:
        """
        Calculate risk metrics for a specific position
        
        Args:
            position: Position to analyze
            
        Returns:
            PositionRisk object with risk metrics
        """
        # This is a simplified calculation - in a real system, you would calculate Greeks based on options data
        position_value = abs(position.average_price * position.quantity)
        position_size_percentage = (position_value / self.portfolio_value) if self.portfolio_value > 0 else 0
        
        # Placeholder values for Greeks (would be calculated from options data in real system)
        delta = 0.0
        gamma = 0.0
        theta = 0.0
        vega = 0.0
        
        risk_contribution = position_size_percentage * 1.0  # Simplified calculation
        
        return PositionRisk(
            symbol=position.symbol,
            position_size_percentage=position_size_percentage,
            margin_used=position_value * 0.2,  # Simplified margin calculation
            risk_contribution=risk_contribution,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            underlying_price=position.last_price,
            position_value=position_value
        )
    
    def calculate_portfolio_risk(self) -> Dict[str, float]:
        """
        Calculate overall portfolio risk metrics
        
        Returns:
            Dictionary with portfolio risk metrics
        """
        total_position_value = sum(abs(pos.average_price * pos.quantity) for pos in self.current_positions.values())
        
        portfolio_risk_percentage = (total_position_value / self.portfolio_value) if self.portfolio_value > 0 else 0
        
        margin_utilization = (self.margin_used / (self.margin_available + self.margin_used)) if (self.margin_available + self.margin_used) > 0 else 0
        
        return {
            "portfolio_value": self.portfolio_value,
            "total_position_value": total_position_value,
            "portfolio_risk_percentage": portfolio_risk_percentage,
            "margin_utilization": margin_utilization,
            "current_positions_count": len(self.current_positions),
            "daily_pnl": self.daily_pnl,
            "daily_losses": self.daily_losses,
            "cash_available": self.cash_available
        }
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """
        Check if any risk limits are currently exceeded
        
        Returns:
            Dictionary with risk limit status
        """
        limits_exceeded = {}
        
        # Portfolio risk percentage
        total_position_value = sum(abs(pos.average_price * pos.quantity) for pos in self.current_positions.values())
        portfolio_risk_percentage = (total_position_value / self.portfolio_value) if self.portfolio_value > 0 else 0
        limits_exceeded["portfolio_risk_exceeded"] = portfolio_risk_percentage > self.risk_config.portfolio_risk_limit
        
        # Daily loss limit
        limits_exceeded["daily_loss_exceeded"] = self.daily_losses >= self.risk_config.daily_loss_limit
        
        # Position count limit
        limits_exceeded["position_limit_exceeded"] = len(self.current_positions) >= self.risk_config.max_concurrent_positions
        
        # Margin utilization limit
        margin_utilization = (self.margin_used / (self.margin_available + self.margin_used)) if (self.margin_available + self.margin_used) > 0 else 0
        limits_exceeded["margin_exceeded"] = margin_utilization > self.risk_config.margin_utilization_limit
        
        # Portfolio value at risk
        portfolio_var = total_position_value / self.portfolio_value if self.portfolio_value > 0 else 0
        limits_exceeded["portfolio_var_exceeded"] = portfolio_var > self.risk_config.max_portfolio_value_at_risk
        
        # Log any exceeded limits
        for limit, exceeded in limits_exceeded.items():
            if exceeded:
                logger.warning(f"Risk limit exceeded: {limit}")
        
        return limits_exceeded
    
    def generate_risk_report(self) -> str:
        """
        Generate a comprehensive risk report
        
        Returns:
            Formatted risk report string
        """
        metrics = self.calculate_portfolio_risk()
        limits_status = self.check_risk_limits()
        
        report = f"""
        RISK REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ================================
        Portfolio Value: ₹{metrics['portfolio_value']:,.2f}
        Total Position Value: ₹{metrics['total_position_value']:,.2f}
        Portfolio Risk %: {metrics['portfolio_value'] and metrics['total_position_value'] / metrics['portfolio_value'] * 100 or 0:.2f}%
        Margin Utilization: {metrics['margin_utilization'] * 100:.2f}%
        Current Positions: {metrics['current_positions_count']}
        Daily P&L: ₹{metrics['daily_pnl']:,.2f}
        Daily Losses: ₹{metrics['daily_losses']:,.2f}
        Cash Available: ₹{metrics['cash_available']:,.2f}
        
        RISK LIMITS STATUS:
        - Portfolio Risk Limit (≤{self.risk_config.portfolio_risk_limit:.2%}): {'❌ EXCEEDED' if limits_status['portfolio_risk_exceeded'] else '✅ OK'}
        - Daily Loss Limit (≤₹{self.risk_config.daily_loss_limit:,.2f}): {'❌ EXCEEDED' if limits_status['daily_loss_exceeded'] else '✅ OK'}
        - Position Count Limit (≤{self.risk_config.max_concurrent_positions}): {'❌ EXCEEDED' if limits_status['position_limit_exceeded'] else '✅ OK'}
        - Margin Utilization Limit (≤{self.risk_config.margin_utilization_limit:.2%}): {'❌ EXCEEDED' if limits_status['margin_exceeded'] else '✅ OK'}
        - Portfolio VaR Limit (≤{self.risk_config.max_portfolio_value_at_risk:.2%}): {'❌ EXCEEDED' if limits_status['portfolio_var_exceeded'] else '✅ OK'}
        """
        
        logger.info("Risk report generated")
        return report
    
    def enforce_risk_limits(self) -> bool:
        """
        Check risk limits and take appropriate action if limits are exceeded
        
        Returns:
            True if limits are within acceptable range, False otherwise
        """
        limits_status = self.check_risk_limits()
        
        # If any critical limits are exceeded, return False
        critical_limit_exceeded = any([
            limits_status['daily_loss_exceeded'],
            limits_status['position_limit_exceeded'],
            limits_status['margin_exceeded']
        ])
        
        if critical_limit_exceeded:
            logger.critical("CRITICAL RISK LIMIT EXCEEDED - STOPPING TRADING")
            return False
        
        return True
    
    def calculate_max_position_size(self, underlying_price: float, strategy_type: StrategyType) -> int:
        """
        Calculate maximum position size based on risk parameters
        
        Args:
            underlying_price: Current price of the underlying asset
            strategy_type: Type of strategy (Cash Secured Put or Covered Call)
            
        Returns:
            Maximum position size in quantity
        """
        if self.portfolio_value <= 0:
            return 0
        
        # Calculate max risk per trade
        max_risk = self.portfolio_value * config.risk_per_trade_percent
        
        # Calculate max lots based on risk
        if strategy_type == StrategyType.CASH_SECURED_PUT:
            # For CSP, risk is approximately the strike price * lot size (if assigned)
            # But our risk is limited to the premium received
            strike_price = underlying_price * 0.95  # Approximate ATM strike
            max_lots = max_risk / (strike_price * config.quantity_per_lot)
        else:  # COVERED_CALL
            # For CC, risk is the value of shares held
            max_lots = max_risk / (underlying_price * config.quantity_per_lot)
        
        # Return integer lots
        max_position_size = int(max_lots) * config.quantity_per_lot
        
        # Ensure we don't exceed minimum lot requirements
        if max_position_size < config.quantity_per_lot:
            max_position_size = config.quantity_per_lot if max_risk >= (underlying_price * config.quantity_per_lot) else 0
        
        logger.debug(f"Max position size calculated: {max_position_size} for {strategy_type.value}")
        return max_position_size


# Global risk manager instance
risk_manager = RiskManager()