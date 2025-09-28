import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pytz
import pandas as pd
import requests
from kiteconnect import KiteConnect
try:
    import pandas_market_calendars as mcal
except ImportError:
    mcal = None
    print("pandas_market_calendars not available, holiday calendar features will be limited")
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.setup_utils import setup_trading_path, with_retry, circuit_breaker
setup_trading_path()  # Ensure proper imports
from config.config import config
from models.models import Trade, Position, OptionContract, StrategyState, RiskMetrics
from models.enums import OrderType, ProductType, TransactionType, StrategyType, OptionType
from utils.logging_utils import logger, log_trade_entry, log_position_update, log_risk_alert, log_performance_metrics
from database.database import db_manager
from risk_management.risk_manager import risk_manager
from notifications.notification_manager import (
    send_notification, 
    send_order_notification, 
    send_position_notification, 
    send_performance_notification, 
    send_critical_alert,
    send_health_check
)
from ai.base import ai_base, is_enabled
import threading
import signal
import sys


class OptionWheelStrategy:
    """Main class implementing the Options Wheel Strategy"""
    
    def __init__(self, kite_client: Optional[KiteConnect] = None):
        """
        Initialize the Options Wheel Strategy
        
        Args:
            kite_client: KiteConnect client instance (optional, will create if not provided)
        """
        self.kite = kite_client or self._initialize_kite()
        self.state = StrategyState(
            active_positions={},
            active_orders={},
            daily_pnl=0.0,
            total_pnl=0.0,
            daily_trades=0,
            total_trades=0,
            last_updated=datetime.now(),
            strategy_running=False,
            daily_loss=0.0,
            max_daily_loss_breached=False,
            current_portfolio_value=0.0,
            cash_available=0.0
        )
        
        # Load state from persistence if available
        self.load_state()
        
        # Fetch and cache instruments
        self.instruments = {}
        self._fetch_instruments()
        
        # Options chain cache with TTL
        self.options_chain_cache = {}
        self.options_chain_last_fetch = {}
        self.options_chain_cache_ttl = config.data_refresh_interval  # seconds
        
        # Trading state
        self.trading_enabled = True
        self.kill_switch_active = False
        
        logger.info("Option Wheel Strategy initialized successfully")
    
    @with_retry(max_retries=3, backoff_factor=2)
    def _initialize_kite(self) -> KiteConnect:
        """Initialize KiteConnect client with API credentials"""
        try:
            if not config.api_key or not config.api_secret:
                raise ValueError("Kite API credentials not configured")
            
            kite = KiteConnect(api_key=config.api_key)
            
            # If access token is provided, set it directly
            if config.access_token:
                kite.set_access_token(config.access_token)
            else:
                # If no access token, provide the login URL
                login_url = kite.login_url()
                logger.warning(f"Please login using this URL to get access token: {login_url}")
                raise ValueError("Access token not provided. Please login and set access_token in config.")
            
            logger.info("KiteConnect initialized successfully")
            return kite
        except Exception as e:
            logger.error(f"Failed to initialize KiteConnect: {e}")
            raise
    
    @with_retry(max_retries=2, backoff_factor=1)
    @circuit_breaker(failure_threshold=3, timeout=120)
    def _fetch_instruments(self):
        """Fetch and cache all instruments from Kite"""
        try:
            # Fetch all instruments
            all_instruments = self.kite.instruments()
            
            # Create a mapping of symbol to instrument details
            self.instruments = {inst['instrument_token']: inst for inst in all_instruments}
            
            logger.info(f"Fetched {len(self.instruments)} instruments from Kite")
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            # Use cached instruments if available
            if not self.instruments:
                raise
    
    def is_market_open(self) -> bool:
        """Check if the market is currently open"""
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if it's a weekday
        if now.weekday() > 4:  # Saturday or Sunday
            return False
        
        # Check holiday calendar if enabled
        if config.use_holiday_calendar:
            if mcal is not None:
                try:
                    # Use mcal for holiday checking
                    holidays = mcal.get_calendar('NSE').schedule(start_date=now.date(), end_date=now.date())
                    if holidays.empty:
                        logger.info(f"Today ({now.date()}) is a holiday, market is closed")
                        return False
                except Exception as e:
                    logger.error(f"Error checking holiday calendar with mcal: {e}")
            else:
                # Fallback to CSV file method
                try:
                    holidays_df = pd.read_csv(config.holiday_file_path)
                    today = now.strftime('%Y-%m-%d')
                    if today in holidays_df.iloc[:, 0].astype(str).values:
                        logger.info(f"Today ({today}) is a holiday, market is closed")
                        return False
                except Exception as e:
                    logger.error(f"Error checking holiday calendar: {e}")
        
        # Check market hours
        current_time = now.time()
        market_open = now.replace(
            hour=config.market_open_hour, 
            minute=config.market_open_minute
        ).time()
        market_close = now.replace(
            hour=config.market_close_hour, 
            minute=config.market_close_minute
        ).time()
        
        return market_open <= current_time <= market_close
    
    def _check_kill_switch(self) -> bool:
        """Check if kill switch file exists to halt trading"""
        if os.path.exists(config.kill_switch_file):
            logger.critical(f"Kill switch file {config.kill_switch_file} detected, stopping trading")
            self.kill_switch_active = True
            self.trading_enabled = False
            return True
        return False
    
    def get_options_chain(self, underlying_symbol: str, expiry_date: Optional[datetime] = None) -> List[OptionContract]:
        """Fetch options chain for the given underlying symbol with caching and error handling"""
        # Check cache first
        cache_key = f"{underlying_symbol}_{expiry_date or 'nearest'}"
        current_time = datetime.now()
        
        # Check if we have cached data and it's still valid
        if cache_key in self.options_chain_last_fetch:
            time_since_cache = (current_time - self.options_chain_last_fetch[cache_key]).total_seconds()
            if time_since_cache < self.options_chain_cache_ttl:
                return self.options_chain_cache.get(cache_key, [])
        
        try:
            # Try NSE India API first if enabled
            if config.use_nse_api:
                chain = self._fetch_options_chain_nse(underlying_symbol, expiry_date)
                if chain:
                    # Update cache
                    self.options_chain_cache[cache_key] = chain
                    self.options_chain_last_fetch[cache_key] = current_time
                    return chain
            
            # Fallback: Use Kite instruments
            chain = self._fetch_options_chain_kite(underlying_symbol, expiry_date)
            
            # Update cache
            self.options_chain_cache[cache_key] = chain
            self.options_chain_last_fetch[cache_key] = current_time
            
            return chain
        except Exception as e:
            logger.error(f"Error fetching options chain for {underlying_symbol}: {e}")
            # Return cached data if available, even if expired
            return self.options_chain_cache.get(cache_key, [])
    
    def _fetch_options_chain_nse(self, underlying_symbol: str, expiry_date: Optional[datetime]) -> List[OptionContract]:
        """Fetch options chain from NSE India API"""
        # Placeholder for NSE API integration
        # The actual implementation would connect to NSE's options chain API
        logger.warning("NSE API integration not implemented yet, using fallback")
        return []
    
    def _fetch_options_chain_kite(self, underlying_symbol: str, expiry_date: Optional[datetime]) -> List[OptionContract]:
        """Fetch options chain from Kite instruments"""
        try:
            # Get all instruments for the underlying symbol
            if not self.instruments:
                self._fetch_instruments()
            
            # Filter for options for the underlying symbol
            underlying_token = None
            for token, instrument in self.instruments.items():
                if instrument['tradingsymbol'] == underlying_symbol:
                    underlying_token = token
                    break
            
            if not underlying_token:
                logger.error(f"Underlying symbol {underlying_symbol} not found in instruments")
                return []
            
            # Find all options for this underlying
            options = []
            for token, instrument in self.instruments.items():
                if (instrument['segment'] == 'NFO-OPT' and 
                    underlying_symbol in instrument['tradingsymbol']):
                    
                    # Filter by expiry if specified
                    if expiry_date and instrument['expiry'] != expiry_date.date():
                        continue
                    
                    # Calculate approximate delta if not available
                    delta = self._calculate_approximate_delta(
                        instrument['strike'],
                        instrument['instrument_type'],
                        # We need to get the underlying price here, but for now using placeholder
                        0  # Placeholder - will be updated later with real price
                    )
                    
                    option_contract = OptionContract(
                        symbol=instrument['tradingsymbol'],
                        instrument_token=instrument['instrument_token'],
                        exchange=instrument['exchange'],
                        last_price=instrument.get('last_price', 0),
                        expiry=datetime.combine(instrument['expiry'], datetime.min.time()),
                        strike=instrument['strike'],
                        tick_size=instrument['tick_size'],
                        lot_size=instrument['lot_size'],
                        instrument_type=instrument['instrument_type'],
                        segment=instrument['segment'],
                        option_type='CE' if 'CE' in instrument['instrument_type'] else 'PE',
                        tradingsymbol=instrument['tradingsymbol'],
                        delta=delta,
                        open_interest=instrument.get('oi', 0)
                    )
                    
                    options.append(option_contract)
            
            # Get the underlying price to update delta calculations
            try:
                underlying_quote = self.kite.quote([f"NSE:{underlying_symbol}"])
                if f"NSE:{underlying_symbol}" in underlying_quote:
                    underlying_price = underlying_quote[f"NSE:{underlying_symbol}"]["last_price"]
                    
                    # Recalculate deltas with the actual underlying price
                    for option in options:
                        option.delta = self._calculate_approximate_delta(
                            option.strike,
                            option.option_type,
                            underlying_price
                        )
            except Exception as e:
                logger.warning(f"Could not fetch underlying price for delta calculation: {e}")
            
            logger.info(f"Fetched {len(options)} options from Kite for {underlying_symbol}")
            return options
            
        except Exception as e:
            logger.error(f"Error fetching options chain from Kite: {e}")
            return []
    
    def _calculate_approximate_delta(self, strike: float, option_type: str, underlying_price: float) -> Optional[float]:
        """Calculate approximate delta when real delta is unavailable"""
        if underlying_price <= 0 or strike <= 0:
            return None
        
        try:
            moneyness = underlying_price / strike
            
            # Simplified delta approximation based on moneyness
            if option_type == "CE":  # Call option
                if moneyness > 1.1:  # Deep ITM
                    return 0.95
                elif moneyness > 1.05:  # ITM
                    return 0.7
                elif moneyness > 0.95:  # ATM
                    return 0.5
                elif moneyness > 0.9:  # OTM
                    return 0.3
                else:  # Deep OTM
                    return 0.05
            else:  # Put option
                if moneyness < 0.9:  # Deep ITM
                    return -0.95
                elif moneyness < 0.95:  # ITM
                    return -0.7
                elif moneyness < 1.05:  # ATM
                    return -0.5
                elif moneyness < 1.1:  # OTM
                    return -0.3
                else:  # Deep OTM
                    return -0.05
        except Exception as e:
            logger.warning(f"Error calculating approximate delta: {e}")
            return None
    
    def find_best_otm_strikes(
        self, 
        underlying_symbol: str, 
        strategy_type: StrategyType,
        expiry_date: Optional[datetime] = None
    ) -> List[OptionContract]:
        """Find the best OTM strikes based on delta range and open interest"""
        try:
            chain = self.get_options_chain(underlying_symbol, expiry_date)
            
            # Determine delta range based on strategy mode
            if config.strategy_mode == 'conservative':
                delta_low, delta_high = 0.10, 0.15
            elif config.strategy_mode == 'aggressive':
                delta_low, delta_high = 0.25, 0.35
            else:  # balanced
                delta_low, delta_high = config.otm_delta_range_low, config.otm_delta_range_high
            
            # Filter options based on criteria
            filtered_options = []
            for option in chain:
                # Check if delta is in range (considering absolute value for puts)
                option_delta = abs(option.delta) if option.delta else 0
                
                # Skip if no delta or outside range
                if not option.delta or option_delta < delta_low or option_delta > delta_high:
                    continue
                
                # Check if open interest meets minimum requirement
                if option.open_interest < config.min_open_interest:
                    continue
                
                # For Cash Secured Puts, we want PUT options
                # For Covered Calls, we want CALL options
                if strategy_type == StrategyType.CASH_SECURED_PUT and option.option_type == "PE":
                    filtered_options.append(option)
                elif strategy_type == StrategyType.COVERED_CALL and option.option_type == "CE":
                    filtered_options.append(option)
            
            # Sort by delta (closest to target) and then by open interest (highest first)
            filtered_options.sort(
                key=lambda x: (abs(abs(x.delta) - (delta_low + delta_high) / 2), -x.open_interest)
            )
            
            logger.info(f"Found {len(filtered_options)} suitable options for {strategy_type.value}")
            return filtered_options
            
        except Exception as e:
            logger.error(f"Error finding best OTM strikes: {e}")
            return []
    
    def place_order(self, symbol: str, transaction_type: str, quantity: int, price: float, 
                   order_type: str = "LIMIT", product: str = "NRML", **kwargs) -> Optional[str]:
        """
        Place an order with the broker
        
        Args:
            symbol: Trading symbol
            transaction_type: BUY or SELL
            quantity: Number of units
            price: Order price
            order_type: Type of order (LIMIT, MARKET, etc.)
            product: Product type (NRML, MIS, etc.)
            **kwargs: Additional order parameters
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Check kill switch
            if self._check_kill_switch():
                logger.warning("Kill switch active, order not placed")
                return None
            
            # Check if market is open
            if not self.is_market_open():
                logger.warning("Market is closed, order not placed")
                return None
            
            # Validate order parameters
            if quantity <= 0:
                logger.error("Invalid quantity for order")
                return None
            
            if price <= 0 and order_type == "LIMIT":
                logger.error("Invalid price for limit order")
                return None
            
            # Log the order attempt
            logger.info(f"Attempting to place order: {transaction_type} {quantity} {symbol} @ ₹{price}")
            
            # Check if we're in dry run mode
            if config.dry_run:
                order_id = f"DRY_RUN_{int(datetime.now().timestamp())}"
                logger.info(f"[DRY RUN] Would place order: {transaction_type} {quantity} {symbol} @ ₹{price}")
                send_notification(
                    f"[DRY RUN] Order: {transaction_type} {quantity} {symbol} @ ₹{price}", 
                    title="DRY RUN Order Simulation"
                )
                
                # Create a mock trade record
                mock_trade = Trade(
                    order_id=order_id,
                    symbol=symbol,
                    exchange="NFO",  # Options are traded on NFO
                    instrument_token=0,  # Will be updated
                    transaction_type=transaction_type,
                    order_type=order_type,
                    product=product,
                    quantity=quantity,
                    price=price,
                    filled_quantity=quantity,
                    average_price=price,
                    trigger_price=kwargs.get('trigger_price', 0),
                    validity=kwargs.get('validity', 'DAY'),
                    status="COMPLETE",
                    disclosed_quantity=kwargs.get('disclosed_quantity', 0),
                    market_protection=kwargs.get('market_protection', 0),
                    order_timestamp=datetime.now(),
                    exchange_timestamp=datetime.now(),
                    exchange_order_id=order_id,
                    parent_order_id=kwargs.get('parent_order_id'),
                    trade_type="fno",
                    tax_category="STT_applicable",
                    stt_paid=0,  # Will be calculated later
                    brokerage=0,  # Will be calculated later
                    taxes=0,
                    turnover_charges=0,
                    stamp_duty=0
                )
                
                # Add to database
                db_manager.insert_trade(mock_trade)
                
                # Update risk manager
                risk_manager.add_trade(mock_trade)
                
                return order_id
            
            # Check for live trading confirmation if not in dry run mode
            if not self._confirm_live_trading():
                logger.critical("Live trading confirmation failed. Exiting.")
                return None
            
            # Place real order
            order_params = {
                "tradingsymbol": symbol,
                "exchange": "NFO",
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
                "price": price,
                **kwargs
            }
            
            # Remove None values
            order_params = {k: v for k, v in order_params.items() if v is not None}
            
            order_id = self.kite.place_order(variety=self.kite.VARIETY_REGULAR, **order_params)
            
            logger.info(f"Order placed successfully: {order_id} for {transaction_type} {quantity} {symbol} @ {price}")
            
            # Send notification
            send_order_notification(transaction_type, symbol, quantity, price, "PLACED", order_id)
            
            # Track in active orders
            self.state.active_orders[order_id] = {
                "symbol": symbol,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "price": price,
                "timestamp": datetime.now()
            }
            
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            send_critical_alert("ORDER_PLACEMENT_FAILED", str(e))
            return None
    
    def _confirm_live_trading(self) -> bool:
        """
        Confirm live trading mode with user
        
        Returns:
            True if confirmed, False otherwise
        """
        if config.dry_run:
            return True
            
        logger.warning("⚠️ LIVE TRADING MODE ENABLED")
        confirmation = input("⚠️ LIVE TRADING MODE ENABLED. Type 'CONFIRM' to proceed: ")
        return confirmation == 'CONFIRM'
    
    def execute_strategy_cycle(self):
        """Execute one cycle of the strategy"""
        try:
            logger.debug("Starting strategy cycle")
            
            # Check for kill switch
            if self._check_kill_switch():
                logger.info("Kill switch active, skipping strategy cycle")
                return
            
            # Check if market is open
            if not self.is_market_open():
                logger.info("Market is closed, skipping strategy cycle")
                return
            
            # Get portfolio information
            self._update_portfolio_info()
            
            # Check risk limits
            if not risk_manager.enforce_risk_limits():
                logger.critical("Risk limits exceeded, stopping trading")
                self.trading_enabled = False
                return
            
            # Check if we have positions or should look for new positions
            positions = self.get_current_positions()
            
            if positions:
                # Manage existing positions (check for profit targets, stop losses, etc.)
                self._manage_existing_positions(positions)
            else:
                # No positions, look for new opportunities
                self._look_for_new_positions()
            
            # Update state
            self.state.last_updated = datetime.now()
            
            logger.debug("Strategy cycle completed")
            
        except Exception as e:
            logger.error(f"Error in strategy cycle: {e}")
            send_critical_alert("STRATEGY_CYCLE_ERROR", str(e))
    
    def _update_portfolio_info(self):
        """Update portfolio value and available cash"""
        try:
            # Get margin information
            margins = self.kite.margins()
            
            # Update risk manager with current margin info
            available_cash = margins['equity']['available']['cash']
            used_cash = margins['equity']['used']['debits']  # Note: debits represent used amount
            total_margin = available_cash + used_cash
            
            risk_manager.update_cash_available(available_cash)
            risk_manager.update_portfolio_value(total_margin)
            risk_manager.update_margin_info(
                margin_available=available_cash,
                margin_used=used_cash
            )
            
            # Update state
            self.state.cash_available = available_cash
            self.state.current_portfolio_value = total_margin
            
            logger.debug(f"Portfolio updated - Value: ₹{total_margin:,.2f}, Cash: ₹{available_cash:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating portfolio info: {e}")
    
    def _manage_existing_positions(self, positions: List[Position]):
        """Manage existing positions (check profit targets, stop losses, etc.)"""
        try:
            for position in positions:
                # Calculate P&L
                pnl = position.pnl if hasattr(position, 'pnl') else 0
                avg_price = position.average_price if hasattr(position, 'average_price') else 0
                quantity = position.quantity if hasattr(position, 'quantity') else 0
                
                # Determine if this is a short option position (sold, expecting premium)
                is_short_position = avg_price > 0 and quantity < 0  # Negative quantity indicates short position
                
                if is_short_position:
                    # For short option positions, positive P&L means we're making money (premium collected)
                    # So we take profit when premium has decayed by target percentage
                    original_premium = abs(avg_price)
                    current_premium = 0  # This would need to be calculated from market data
                    
                    # Placeholder: Calculate target thresholds based on premium
                    profit_target = original_premium * config.profit_target_percentage
                    loss_limit = original_premium * config.loss_limit_percentage
                    
                    # If we have current market price, we can calculate actual profit/loss
                    try:
                        current_quote = self.kite.quote([f"NFO:{position.symbol}"])
                        current_price = current_quote[f"NFO:{position.symbol}"]["last_price"]
                        current_pnl = (original_premium - current_price) * abs(quantity)  # For short positions
                        
                        # Check profit target
                        if current_pnl >= profit_target * abs(quantity):
                            logger.info(f"Profit target reached for {position.symbol}, closing position")
                            self._close_position(position, "PROFIT_TARGET")
                        # Check stop loss
                        elif current_pnl <= -loss_limit * abs(quantity):
                            logger.warning(f"Stop loss triggered for {position.symbol}, closing position")
                            self._close_position(position, "STOP_LOSS")
                    
                    except Exception as quote_error:
                        logger.warning(f"Could not get current quote for {position.symbol}: {quote_error}")
                
        except Exception as e:
            logger.error(f"Error managing existing positions: {e}")
    
    def _look_for_new_positions(self):
        """Look for new position opportunities based on strategy type"""
        try:
            # Check how many positions we're allowed to open
            active_positions_count = len(self.state.active_positions)
            if active_positions_count >= config.max_concurrent_positions:
                logger.info(f"Max concurrent positions reached ({config.max_concurrent_positions}), skipping new positions")
                return
            
            # Determine strategy type based on holdings (simplified)
            # In a full implementation, we'd check if we hold the underlying stock
            # For now, we'll default to Cash Secured Puts
            strategy_type = StrategyType.CASH_SECURED_PUT
            
            # Find best OTM strikes
            best_options = self.find_best_otm_strikes(config.symbol, strategy_type)
            
            if not best_options:
                logger.info("No suitable options found for new positions")
                return
            
            # Select the best option (first in the list after sorting)
            best_option = best_options[0]
            
            # Calculate position size based on risk management
            max_position_size = risk_manager.calculate_max_position_size(
                underlying_price=0,  # Placeholder - need to get current price
                strategy_type=strategy_type
            )
            
            if max_position_size <= 0:
                logger.info("Risk management prevents opening new position")
                return
            
            # Determine actual quantity (multiple of lot size)
            lots = min(
                max_position_size // config.quantity_per_lot,
                best_option.lot_size  # Use the minimum lot size available
            )
            quantity = lots * config.quantity_per_lot
            
            if quantity <= 0:
                logger.info("Calculated quantity is zero or negative, skipping trade")
                return
            
            # Place order to sell the option (collecting premium)
            order_id = self.place_order(
                symbol=best_option.symbol,
                transaction_type=TransactionType.SELL.value,
                quantity=quantity,
                price=best_option.last_price,
                product=ProductType.NRML.value
            )
            
            if order_id:
                logger.info(f"New position opened: {order_id} for {quantity} {best_option.symbol}")
                
                # In a real system, we would update the positions tracking here
                # For now, we'll just log the trade
                send_notification(
                    f"New {strategy_type.value} position: SELL {quantity} {best_option.symbol} @ ₹{best_option.last_price}",
                    title="New Position Opened"
                )
            
        except Exception as e:
            logger.error(f"Error looking for new positions: {e}")
    
    def _close_position(self, position: Position, reason: str):
        """Close a position by placing an offsetting order"""
        try:
            # Determine the closing transaction type (opposite of current position)
            # If we're short (sold), we need to buy to close
            if position.quantity < 0:
                closing_transaction = TransactionType.BUY.value
                quantity = abs(position.quantity)
            else:
                closing_transaction = TransactionType.SELL.value
                quantity = position.quantity
            
            # Get current market price for the option
            try:
                current_quote = self.kite.quote([f"NFO:{position.symbol}"])
                current_price = current_quote[f"NFO:{position.symbol}"]["last_price"]
                
                # Place closing order
                order_id = self.place_order(
                    symbol=position.symbol,
                    transaction_type=closing_transaction,
                    quantity=quantity,
                    price=current_price,
                    product=ProductType.NRML.value
                )
                
                if order_id:
                    logger.info(f"Position closed: {order_id} for {position.symbol} ({reason})")
                    send_position_notification(
                        f"CLOSED ({reason})",
                        position.symbol,
                        quantity,
                        position.pnl,
                        position.average_price
                    )
                    
                    # Remove from active positions
                    if position.symbol in self.state.active_positions:
                        del self.state.active_positions[position.symbol]
            except Exception as quote_error:
                logger.error(f"Could not get quote to close position {position.symbol}: {quote_error}")
                
                # Place market order as fallback
                order_id = self.place_order(
                    symbol=position.symbol,
                    transaction_type=closing_transaction,
                    quantity=quantity,
                    price=0,  # Market order
                    order_type=OrderType.MARKET.value,
                    product=ProductType.NRML.value
                )
                
                if order_id:
                    logger.info(f"Position closed with market order: {order_id} ({reason})")
        
        except Exception as e:
            logger.error(f"Error closing position {position.symbol}: {e}")
    
    def get_current_positions(self) -> List[Position]:
        """Get current positions from Kite or internal tracking"""
        try:
            # Get positions from Kite
            kite_positions = self.kite.positions()
            
            positions = []
            # Holdings (long positions)
            for pos in kite_positions['holdings']:
                position = Position(
                    symbol=pos['tradingsymbol'],
                    exchange=pos['exchange'],
                    instrument_token=pos['instrument_token'],
                    product=pos['product'],
                    quantity=pos['quantity'],
                    average_price=pos['average_price'],
                    pnl=pos['pnl'],
                    unrealized_pnl=pos['unrealized_pnl'],
                    realized_pnl=pos['realized_pnl'],
                    multiplier=pos['multiplier'],
                    last_price=pos['last_price'],
                    close_price=pos['close_price'],
                    buy_quantity=pos['buy_quantity'],
                    buy_price=pos['buy_price'],
                    buy_value=pos['buy_value'],
                    sell_quantity=pos['sell_quantity'],
                    sell_price=pos['sell_price'],
                    sell_value=pos['sell_value'],
                    day_buy_quantity=pos['day_buy_quantity'],
                    day_buy_price=pos['day_buy_price'],
                    day_buy_value=pos['day_buy_value'],
                    day_sell_quantity=pos['day_sell_quantity'],
                    day_sell_price=pos['day_sell_price'],
                    day_sell_value=pos['day_sell_value']
                )
                positions.append(position)
            
            # Net positions (including short positions)
            for pos in kite_positions['net']:
                # Skip zero positions
                if pos['quantity'] == 0 and pos['overnight_quantity'] == 0:
                    continue
                    
                position = Position(
                    symbol=pos['tradingsymbol'],
                    exchange=pos['exchange'],
                    instrument_token=pos['instrument_token'],
                    product=pos['product'],
                    quantity=pos['quantity'],
                    average_price=pos['average_price'],
                    pnl=pos['pnl'],
                    unrealized_pnl=pos['unrealized_pnl'],
                    realized_pnl=pos['realized_pnl'],
                    multiplier=pos['multiplier'],
                    last_price=pos['last_price'],
                    close_price=pos['close_price'],
                    buy_quantity=pos['buy_quantity'],
                    buy_price=pos['buy_price'],
                    buy_value=pos['buy_value'],
                    sell_quantity=pos['sell_quantity'],
                    sell_price=pos['sell_price'],
                    sell_value=pos['sell_value'],
                    day_buy_quantity=pos['day_buy_quantity'],
                    day_buy_price=pos['day_buy_price'],
                    day_buy_value=pos['day_buy_value'],
                    day_sell_quantity=pos['day_sell_quantity'],
                    day_sell_price=pos['day_sell_price'],
                    day_sell_value=pos['day_sell_value']
                )
                positions.append(position)
            
            logger.info(f"Retrieved {len(positions)} current positions")
            return positions
            
        except Exception as e:
            logger.error(f"Error getting current positions: {e}")
            # Return internal tracking as fallback
            return list(self.state.active_positions.values())
    
    def run(self):
        """Run the strategy continuously during market hours"""
        logger.info("Starting Option Wheel Strategy")
        
        # Check for live trading confirmation if not in dry run mode
        if not config.dry_run:
            confirmation = input("⚠️ LIVE TRADING MODE ENABLED. Type 'CONFIRM' to proceed: ")
            if confirmation != 'CONFIRM':
                logger.critical("Live trading confirmation failed. Exiting.")
                return
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Main strategy loop
        self.state.strategy_running = True
        logger.info("Strategy started successfully")
        
        while self.state.strategy_running and self.trading_enabled and not self.kill_switch_active:
            try:
                # Check for kill switch
                if self._check_kill_switch():
                    logger.info("Kill switch detected, stopping strategy")
                    break
                
                # Execute strategy cycle
                self.execute_strategy_cycle()
                
                # Sleep for configured interval
                time.sleep(config.strategy_run_interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main strategy loop: {e}")
                time.sleep(10)  # Wait a bit before retrying
        
        self.shutdown()
    
    def get_portfolio_metrics(self) -> Dict[str, float]:
        """Get portfolio performance metrics"""
        try:
            # Get P&L data from database
            trades = db_manager.get_all_trades()
            
            if not trades:
                return {
                    'daily_pnl': 0.0,
                    'total_pnl': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0
                }
            
            # Calculate metrics
            daily_pnl = sum(t.pnl for t in trades if 
                          t.order_timestamp.date() == datetime.now().date())
            total_pnl = sum(t.pnl for t in trades)
            
            # Calculate win rate and profit factor
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            
            win_rate = len(winning_trades) / len(trades) if trades else 0
            winning_pnl = sum(t.pnl for t in winning_trades)
            losing_pnl = abs(sum(t.pnl for t in losing_trades))
            profit_factor = winning_pnl / losing_pnl if losing_pnl != 0 else float('inf')
            
            metrics = {
                'daily_pnl': daily_pnl,
                'total_pnl': total_pnl,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {}
    
    def save_state(self):
        """Save strategy state to persistence"""
        try:
            state_data = {
                "active_positions": {k: v.__dict__ for k, v in self.state.active_positions.items()},
                "active_orders": self.state.active_orders,
                "daily_pnl": self.state.daily_pnl,
                "total_pnl": self.state.total_pnl,
                "daily_trades": self.state.daily_trades,
                "total_trades": self.state.total_trades,
                "last_updated": self.state.last_updated.isoformat(),
                "strategy_running": self.state.strategy_running,
                "daily_loss": self.state.daily_loss,
                "max_daily_loss_breached": self.state.max_daily_loss_breached,
                "current_portfolio_value": self.state.current_portfolio_value,
                "cash_available": self.state.cash_available
            }
            
            # Save to JSON file
            with open("strategy_state.json", "w") as f:
                json.dump(state_data, f, default=str, indent=2)
            
            logger.info("Strategy state saved successfully")
        except Exception as e:
            logger.error(f"Error saving strategy state: {e}")
    
    def load_state(self):
        """Load strategy state from persistence"""
        try:
            if not os.path.exists("strategy_state.json"):
                logger.info("No saved state found, starting fresh")
                return
            
            with open("strategy_state.json", "r") as f:
                state_data = json.load(f)
            
            # Restore state
            self.state.active_positions = state_data.get("active_positions", {})
            self.state.active_orders = state_data.get("active_orders", {})
            self.state.daily_pnl = state_data.get("daily_pnl", 0.0)
            self.state.total_pnl = state_data.get("total_pnl", 0.0)
            self.state.daily_trades = state_data.get("daily_trades", 0)
            self.state.total_trades = state_data.get("total_trades", 0)
            self.state.last_updated = datetime.fromisoformat(state_data.get("last_updated", datetime.now().isoformat()))
            self.state.strategy_running = state_data.get("strategy_running", False)
            self.state.daily_loss = state_data.get("daily_loss", 0.0)
            self.state.max_daily_loss_breached = state_data.get("max_daily_loss_breached", False)
            self.state.current_portfolio_value = state_data.get("current_portfolio_value", 0.0)
            self.state.cash_available = state_data.get("cash_available", 0.0)
            
            logger.info("Strategy state loaded successfully")
        except Exception as e:
            logger.error(f"Error loading strategy state: {e}")
    
    def shutdown(self):
        """Gracefully shut down the strategy"""
        logger.info("Initiating strategy shutdown...")
        
        # Update final state
        self.state.strategy_running = False
        
        # Save state
        self.save_state()
        
        # Send shutdown notification
        send_notification("Strategy shutting down", title="Strategy Shutdown")
        
        # Log final metrics
        final_metrics = self.get_portfolio_metrics()
        log_performance_metrics(logger, final_metrics)
        
        logger.info("Strategy shutdown completed")


# Example usage and testing
if __name__ == "__main__":
    # Initialize the strategy
    strategy = OptionWheelStrategy()
    
    # Run the strategy
    strategy.run()