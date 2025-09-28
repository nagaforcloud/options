"""
Data models for the Options Wheel Strategy Trading Bot
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, Literal
import math


@dataclass
class Trade:
    """Represents a trade executed by the strategy"""
    order_id: str
    symbol: str
    exchange: str
    instrument_token: int
    transaction_type: str  # BUY/SELL
    order_type: str  # LIMIT/MARKET
    product: str  # CNC/NRML/MIS
    quantity: int
    price: float
    filled_quantity: int
    average_price: float
    trigger_price: float
    validity: str
    status: str  # COMPLETE/REJECTED/CANCELLED/OPEN
    disclosed_quantity: int
    market_protection: float
    order_timestamp: datetime
    exchange_timestamp: datetime
    exchange_order_id: str
    parent_order_id: Optional[str]
    
    # Additional fields for tax and fee tracking
    trade_type: Literal["intraday", "delivery", "fno"] = "fno"
    tax_category: str = "STT_applicable"
    stt_paid: float = 0.0
    brokerage: float = 0.0
    taxes: float = 0.0
    turnover_charges: float = 0.0
    stamp_duty: float = 0.0
    date: Optional[datetime] = None  # Date of the trade for historical analysis

    def net_pnl(self) -> float:
        """Calculate net profit/loss after accounting for all fees and taxes"""
        gross_pnl = (self.average_price * self.filled_quantity) if self.transaction_type == "BUY" else \
                    -(self.average_price * self.filled_quantity)
        total_fees = self.stt_paid + self.brokerage + self.taxes + self.turnover_charges + self.stamp_duty
        return gross_pnl - total_fees


@dataclass
class Position:
    """Represents a position in the portfolio"""
    symbol: str
    exchange: str
    instrument_token: int
    product: str  # CNC/NRML/MIS
    quantity: int
    average_price: float
    pnl: float
    unrealized_pnl: float
    realized_pnl: float
    multiplier: float
    last_price: float
    close_price: float
    buy_quantity: int
    buy_price: float
    buy_value: float
    sell_quantity: int
    sell_price: float
    sell_value: float
    day_buy_quantity: int
    day_buy_price: float
    day_buy_value: float
    day_sell_quantity: int
    day_sell_price: float
    day_sell_value: float
    
    # Additional fields for comprehensive P&L tracking
    entry_timestamp: Optional[datetime] = None
    exit_timestamp: Optional[datetime] = None
    position_type: Optional[str] = None  # LONG/SHORT/FLAT

    def position_type(self) -> str:
        """Determine position direction based on quantity"""
        if self.quantity > 0:
            return "LONG"
        elif self.quantity < 0:
            return "SHORT"
        else:
            return "FLAT"


@dataclass
class OptionContract:
    """Represents an option contract with Greeks and other data"""
    symbol: str
    instrument_token: int
    exchange: str
    last_price: float
    expiry: datetime
    strike: float
    tick_size: float
    lot_size: int
    instrument_type: str
    segment: str
    option_type: str  # CE/PE
    tradingsymbol: str
    
    # Greeks and additional data
    open_interest: float
    delta: Optional[float] = None  # Option delta
    gamma: Optional[float] = None  # Option gamma
    theta: Optional[float] = None  # Option theta
    vega: Optional[float] = None   # Option vega
    rho: Optional[float] = None    # Option rho
    implied_volatility: Optional[float] = None
    
    # Bid/Ask prices
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_quantity: Optional[int] = None
    ask_quantity: Optional[int] = None
    
    # Historical data
    historical_volatility: Optional[float] = None
    volume: Optional[int] = None
    oi_change: Optional[float] = None

    def intrinsic_value(self, underlying_price: float) -> float:
        """Calculate the intrinsic value of the option"""
        if self.option_type == "CE":  # Call option
            return max(0, underlying_price - self.strike)
        else:  # Put option
            return max(0, self.strike - underlying_price)

    def time_value(self, underlying_price: float) -> float:
        """Calculate the time value of the option"""
        intrinsic_value = self.intrinsic_value(underlying_price)
        return max(0, self.last_price - intrinsic_value)

    def is_in_the_money(self, underlying_price: float) -> bool:
        """Check if the option is in the money"""
        if self.option_type == "CE":  # Call option
            return underlying_price > self.strike
        else:  # Put option
            return underlying_price < self.strike


@dataclass
class StrategyState:
    """Represents the current state of the strategy"""
    active_positions: Dict[str, Position]
    active_orders: Dict[str, Dict[str, Any]]
    daily_pnl: float
    total_pnl: float
    daily_trades: int
    total_trades: int
    last_updated: datetime
    strategy_running: bool
    daily_loss: float
    max_daily_loss_breached: bool
    current_portfolio_value: float
    cash_available: float


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio monitoring"""
    portfolio_value: float
    position_risk_percentage: float
    portfolio_risk_percentage: float
    daily_loss_limit: float
    current_daily_loss: float
    max_concurrent_positions: int
    current_positions_count: int
    margin_utilization: float
    margin_available: float
    margin_used: float
    
    def risk_limits_exceeded(self) -> Dict[str, bool]:
        """Check if any risk limits are exceeded"""
        return {
            "portfolio_risk_exceeded": self.portfolio_risk_percentage > 0.02,  # 2% portfolio risk
            "daily_loss_exceeded": self.current_daily_loss >= self.daily_loss_limit,
            "position_limit_exceeded": self.current_positions_count >= self.max_concurrent_positions,
            "margin_exceeded": self.margin_utilization > 0.95  # 95% margin utilization
        }