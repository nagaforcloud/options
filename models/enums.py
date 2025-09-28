"""
Enumerations for the Options Wheel Strategy Trading Bot
"""
from enum import Enum


class OrderType(Enum):
    """Order types supported by the exchange"""
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    SL = "SL"  # Stop Loss
    SLM = "SL-M"  # Stop Loss Market


class ProductType(Enum):
    """Product types for different trading segments"""
    CNC = "CNC"  # Cash & Carry (Delivery)
    NRML = "NRML"  # Normal (Margin)
    MIS = "MIS"  # Margin Intraday Square-off


class TransactionType(Enum):
    """Transaction types - Buy or Sell"""
    BUY = "BUY"
    SELL = "SELL"


class StrategyType(Enum):
    """Types of strategies implemented"""
    CASH_SECURED_PUT = "Cash Secured Put"
    COVERED_CALL = "Covered Call"


class PositionType(Enum):
    """Types of positions in portfolio"""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class OptionType(Enum):
    """Types of options - Call or Put"""
    CALL = "CE"  # Call European
    PUT = "PE"   # Put European


class OrderStatus(Enum):
    """Status of orders"""
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    OPEN = "OPEN"
    TRIGGER_PENDING = "TRIGGER_PENDING"


class ExchangeType(Enum):
    """Exchange types"""
    NSE = "NSE"  # National Stock Exchange
    BSE = "BSE"  # Bombay Stock Exchange
    NFO = "NFO"  # NSE Futures & Options
    BFO = "BFO"  # BSE Futures & Options
    CDS = "CDS"  # Currency Derivatives Segment
    MCX = "MCX"  # Multi Commodity Exchange