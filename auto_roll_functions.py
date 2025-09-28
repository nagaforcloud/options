"""
Auto Roll Functions for Options Wheel Strategy Trading Bot
Handles auto-rolling of positions before expiry
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from .models.models import Position, Trade
from .models.enums import TransactionType, StrategyType
from .utils.logging_utils import logger
from .config.config import config


def should_roll_position(position: Position) -> bool:
    """
    Determine if a position should be rolled before expiry
    
    Args:
        position: Position to check
        
    Returns:
        True if position should be rolled, False otherwise
    """
    try:
        # Check if we're within the roll threshold (e.g., DTE <= 1)
        if hasattr(position, 'expiry_date'):
            days_to_expiry = (position.expiry_date - datetime.now()).days
            if days_to_expiry <= 1:
                logger.info(f"Position {position.symbol} should be rolled - {days_to_expiry} days to expiry")
                return True
        
        # For positions without explicit expiry, check the symbol naming convention
        # NSE options typically follow the format: INFY24JUL1600CE
        import re
        symbol = position.symbol
        # Extract expiry date from symbol (assuming format YYMMMDD)
        expiry_match = re.search(r'(\d{2}[A-Z]{3}\d{2,4}|\d{6})', symbol)
        if expiry_match:
            expiry_str = expiry_match.group(1)
            try:
                if len(expiry_str) == 6:  # YYMMDD format
                    expiry_date = datetime.strptime(expiry_str, '%y%m%d')
                elif len(expiry_str) == 7 and expiry_str[4].isalpha():  # YYMMD format for single digit days
                    month = expiry_str[2:5]
                    year = expiry_str[0:2]
                    day = expiry_str[5:]
                    expiry_date = datetime.strptime(f"{year}{month}{day}", '%y%b%d')
                else:
                    # More complex format, try different patterns
                    expiry_date = None
            except:
                expiry_date = None
            
            if expiry_date:
                days_to_expiry = (expiry_date - datetime.now()).days
                if days_to_expiry <= 1:
                    logger.info(f"Position {position.symbol} should be rolled - {days_to_expiry} days to expiry")
                    return True
    
        return False
        
    except Exception as e:
        logger.error(f"Error determining if position {position.symbol} should be rolled: {e}")
        return False


def roll_put_position(current_position: Position, new_strike: float, new_premium: float, quantity: int) -> Dict[str, Any]:
    """
    Roll a put position (roll down & out)
    
    Args:
        current_position: Current position to roll
        new_strike: New strike price for the rolled position
        new_premium: New premium for the rolled position
        quantity: Quantity to roll
        
    Returns:
        Dictionary with roll transaction details
    """
    try:
        roll_details = {
            'original_position': current_position,
            'action': 'ROLL_PUT_DOWN_OUT',
            'new_strike': new_strike,
            'new_premium': new_premium,
            'quantity': quantity,
            'roll_date': datetime.now(),
            'notes': f"Rolling put from {current_position.symbol} to lower strike at {new_strike} for premium of {new_premium}"
        }
        
        logger.info(f"Rolling put position: {current_position.symbol} -> New strike {new_strike} @ ₹{new_premium}")
        
        # In a real implementation, you would:
        # 1. Buy back the existing put option
        # 2. Sell a new put option with lower strike
        # 3. Update the position in the system
        
        return roll_details
        
    except Exception as e:
        logger.error(f"Error rolling put position {current_position.symbol}: {e}")
        return {}


def roll_call_position(current_position: Position, new_strike: float, new_premium: float, quantity: int) -> Dict[str, Any]:
    """
    Roll a call position (roll up & out)
    
    Args:
        current_position: Current position to roll
        new_strike: New strike price for the rolled position
        new_premium: New premium for the rolled position
        quantity: Quantity to roll
        
    Returns:
        Dictionary with roll transaction details
    """
    try:
        roll_details = {
            'original_position': current_position,
            'action': 'ROLL_CALL_UP_OUT',
            'new_strike': new_strike,
            'new_premium': new_premium,
            'quantity': quantity,
            'roll_date': datetime.now(),
            'notes': f"Rolling call from {current_position.symbol} to higher strike at {new_strike} for premium of {new_premium}"
        }
        
        logger.info(f"Rolling call position: {current_position.symbol} -> New strike {new_strike} @ ₹{new_premium}")
        
        # In a real implementation, you would:
        # 1. Buy back the existing call option
        # 2. Sell a new call option with higher strike
        # 3. Update the position in the system
        
        return roll_details
        
    except Exception as e:
        logger.error(f"Error rolling call position {current_position.symbol}: {e}")
        return {}


def find_roll_strikes_for_put(current_strike: float, underlying_price: float, option_chain: List) -> float:
    """
    Find appropriate strike for rolling a put position (down & out)
    
    Args:
        current_strike: Current strike price
        underlying_price: Current underlying price
        option_chain: Current options chain data
        
    Returns:
        New strike price for rolling
    """
    try:
        # For rolling puts down & out, we want to select a lower strike
        # Preferably at a similar delta to maintain similar risk profile
        available_puts = [opt for opt in option_chain if opt.option_type == 'PE' and opt.strike < current_strike]
        
        if not available_puts:
            # If no lower strikes available, return current strike
            return current_strike
        
        # Sort by proximity to target delta (similar to original position)
        target_delta = min([abs(opt.delta) for opt in available_puts if opt.delta]) if available_puts else 0
        
        # For now, just select the next lower strike with good liquidity
        sorted_puts = sorted(available_puts, key=lambda x: x.strike, reverse=True)  # Highest to lowest strike
        
        for put in sorted_puts:
            # Check if this put has sufficient open interest
            if put.open_interest >= config.min_open_interest:
                return put.strike
    
        # If no suitable strikes found, return the lowest available
        return sorted([opt.strike for opt in available_puts])[0]
        
    except Exception as e:
        logger.error(f"Error finding roll strike for put at {current_strike}: {e}")
        return current_strike


def find_roll_strikes_for_call(current_strike: float, underlying_price: float, option_chain: List) -> float:
    """
    Find appropriate strike for rolling a call position (up & out)
    
    Args:
        current_strike: Current strike price
        underlying_price: Current underlying price
        option_chain: Current options chain data
        
    Returns:
        New strike price for rolling
    """
    try:
        # For rolling calls up & out, we want to select a higher strike
        # Preferably at a similar delta to maintain similar risk profile
        available_calls = [opt for opt in option_chain if opt.option_type == 'CE' and opt.strike > current_strike]
        
        if not available_calls:
            # If no higher strikes available, return current strike
            return current_strike
        
        # For now, just select the next higher strike with good liquidity
        sorted_calls = sorted(available_calls, key=lambda x: x.strike)  # Lowest to highest strike
        
        for call in sorted_calls:
            # Check if this call has sufficient open interest
            if call.open_interest >= config.min_open_interest:
                return call.strike
    
        # If no suitable strikes found, return the highest available
        return sorted([opt.strike for opt in available_calls], reverse=True)[0]
        
    except Exception as e:
        logger.error(f"Error finding roll strike for call at {current_strike}: {e}")
        return current_strike


def execute_rolls_for_positions(positions: List[Position], strategy) -> List[Dict[str, Any]]:
    """
    Execute rolling for all positions that need to be rolled
    
    Args:
        positions: List of positions to check for rolling
        strategy: Strategy instance to execute trades
        
    Returns:
        List of roll transaction details
    """
    roll_transactions = []
    
    for position in positions:
        if should_roll_position(position):
            try:
                # Get current market data
                current_quote = strategy.kite.quote([f"NFO:{position.symbol}"])
                current_price = current_quote[f"NFO:{position.symbol}"]["last_price"]
                
                # Determine if this is a call or put position
                is_call = 'CE' in position.symbol.upper()
                is_short = position.quantity < 0  # Negative quantity means short position
                
                if is_short:  # Only roll short positions
                    if is_call:
                        # Roll call - sell higher strike
                        new_strike = find_roll_strikes_for_call(
                            position.strike,  # Assuming position has strike attribute
                            current_price,
                            strategy.get_options_chain(config.symbol)  # Get current options chain
                        )
                        
                        # Get premium for new strike
                        new_options_chain = strategy.get_options_chain(config.symbol)
                        new_option = next((opt for opt in new_options_chain if opt.strike == new_strike), None)
                        new_premium = new_option.last_price if new_option else current_price * 0.8  # 20% lower as fallback
                        
                        roll_details = roll_call_position(position, new_strike, new_premium, abs(position.quantity))
                    else:  # Put
                        # Roll put - sell lower strike
                        new_strike = find_roll_strikes_for_put(
                            position.strike,  # Assuming position has strike attribute
                            current_price, 
                            strategy.get_options_chain(config.symbol)
                        )
                        
                        # Get premium for new strike
                        new_options_chain = strategy.get_options_chain(config.symbol)
                        new_option = next((opt for opt in new_options_chain if opt.strike == new_strike), None)
                        new_premium = new_option.last_price if new_option else current_price * 0.8  # 20% lower as fallback
                        
                        roll_details = roll_put_position(position, new_strike, new_premium, abs(position.quantity))
                    
                    if roll_details:
                        roll_transactions.append(roll_details)
                        # Update position tracking in strategy
                        strategy.remove_position(position.symbol)
                        
            except Exception as e:
                logger.error(f"Error executing roll for position {position.symbol}: {e}")
    
    return roll_transactions