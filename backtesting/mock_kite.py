"""
Mock KiteConnect class for backtesting purposes
Simulates Kite API calls for historical testing
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np


class MockKiteConnect:
    """
    Mock KiteConnect class for backtesting that simulates the real KiteConnect API
    """
    
    def __init__(self, initial_balance: float = 100000):
        """
        Initialize mock KiteConnect with starting balance
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}
        self.orders = {}
        self.order_id_counter = 1000
        self.historical_data = {}
        self.current_timestamp = datetime.now()
        self.trades = []  # Track executed trades for P&L calculation
        
    def set_current_timestamp(self, timestamp: datetime):
        """Set the current timestamp for simulated trading"""
        self.current_timestamp = timestamp
    
    def set_historical_data(self, symbol: str, data: pd.DataFrame):
        """Set historical data for a symbol"""
        self.historical_data[symbol] = data
    
    def quote(self, instruments: List[str]) -> Dict[str, Any]:
        """
        Mock quote method that returns current prices for instruments
        """
        result = {}
        for instrument in instruments:
            if instrument in self.historical_data:
                # Get the price at the current timestamp
                data = self.historical_data[instrument]
                # Find the closest time point to current timestamp
                closest_time = data.index[data.index <= self.current_timestamp].max()
                if pd.notna(closest_time):
                    price = data.loc[closest_time, 'close']
                    result[instrument] = {
                        'instrument_token': 12345,  # Mock value
                        'last_price': float(price),
                        'ohlc': {
                            'open': float(data.loc[closest_time, 'open']),
                            'high': float(data.loc[closest_time, 'high']),
                            'low': float(data.loc[closest_time, 'low']),
                            'close': float(data.loc[closest_time, 'close'])
                        }
                    }
                else:
                    # If no data for current timestamp, return the last available price
                    result[instrument] = {
                        'instrument_token': 12345,
                        'last_price': float(data['close'].iloc[-1]),
                        'ohlc': {
                            'open': float(data['open'].iloc[-1]),
                            'high': float(data['high'].iloc[-1]),
                            'low': float(data['low'].iloc[-1]),
                            'close': float(data['close'].iloc[-1])
                        }
                    }
            else:
                # Return mock values if no historical data
                result[instrument] = {
                    'instrument_token': 12345,
                    'last_price': 100.0,  # Mock value
                    'ohlc': {
                        'open': 100.0,
                        'high': 101.0,
                        'low': 99.0,
                        'close': 100.0
                    }
                }
        return result
    
    def instruments(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Mock instruments method
        """
        # Return mock instrument data
        return [
            {
                'instrument_token': 12345,
                'exchange_token': 123,
                'tradingsymbol': 'NIFTY24JUN18000CE',
                'name': 'NIFTY',
                'exchange': 'NFO',
                'instrument_type': 'CE',
                'segment': 'NFO-OPT',
                'breach': False,
                'tick_size': 0.05,
                'lot_size': 50,
                'expiry': datetime.now() + timedelta(days=30),
                'strike': 18000.0
            },
            {
                'instrument_token': 12346,
                'exchange_token': 124,
                'tradingsymbol': 'NIFTY24JUN18000PE',
                'name': 'NIFTY',
                'exchange': 'NFO',
                'instrument_type': 'PE',
                'segment': 'NFO-OPT',
                'breach': False,
                'tick_size': 0.05,
                'lot_size': 50,
                'expiry': datetime.now() + timedelta(days=30),
                'strike': 18000.0
            }
        ]
    
    def holdings(self) -> List[Dict[str, Any]]:
        """
        Mock holdings method
        """
        return [
            {
                'tradingsymbol': symbol,
                'exchange': 'NFO',
                'instrument_token': pos.get('instrument_token', 12345),
                'quantity': pos['quantity'],
                'average_price': pos['average_price'],
                'last_price': pos['last_price'],
                'pnl': pos['pnl'],
                'close_price': pos['last_price'],
                'product': 'NRML'
            } for symbol, pos in self.positions.items()
        ]
    
    def positions(self) -> Dict[str, List[Dict]]:
        """
        Mock positions method
        """
        net_positions = [
            {
                'tradingsymbol': symbol,
                'exchange': 'NFO',
                'instrument_token': pos.get('instrument_token', 12345),
                'product': 'NRML',
                'quantity': pos['quantity'],
                'average_price': pos['average_price'],
                'last_price': pos['last_price'],
                'pnl': pos['pnl'],
                'unrealized': pos['pnl'],  # For mock purposes
                'realized': 0,  # For mock purposes
                'multiplier': 1,
                'close_price': pos['last_price'],
                'buy_quantity': pos['quantity'] if pos['quantity'] > 0 else 0,
                'buy_price': pos['average_price'] if pos['quantity'] > 0 else 0,
                'buy_value': abs(pos['quantity'] * pos['average_price']) if pos['quantity'] > 0 else 0,
                'sell_quantity': abs(pos['quantity']) if pos['quantity'] < 0 else 0,
                'sell_price': pos['average_price'] if pos['quantity'] < 0 else 0,
                'sell_value': abs(pos['quantity'] * pos['average_price']) if pos['quantity'] < 0 else 0,
                'day_buy_quantity': 0,
                'day_buy_price': 0,
                'day_buy_value': 0,
                'day_sell_quantity': 0,
                'day_sell_price': 0,
                'day_sell_value': 0
            } for symbol, pos in self.positions.items()
        ]
        
        return {
            'net': net_positions,
            'holdings': []
        }
    
    def place_order(
        self,
        variety: str,
        exchange: str,
        tradingsymbol: str,
        transaction_type: str,
        quantity: int,
        product: str,
        order_type: str,
        price: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Mock place_order method
        """
        order_id = f"{self.order_id_counter}"
        self.order_id_counter += 1
        
        # Determine price for the order
        if order_type == 'MARKET':
            # For market orders, get the current price
            quote_data = self.quote([f"{exchange}:{tradingsymbol}"])
            price = quote_data[f"{exchange}:{tradingsymbol}"]["last_price"]
        elif price is None:
            # If no price provided for limit orders, use current price
            quote_data = self.quote([f"{exchange}:{tradingsymbol}"])
            price = quote_data[f"{exchange}:{tradingsymbol}"]["last_price"]
        
        # Calculate cost
        cost = price * quantity
        if transaction_type == 'BUY':
            cost = -cost  # Negative for purchases
        
        # Update balance
        self.current_balance += cost
        if self.current_balance < 0:
            # For backtesting, we'll allow negative balance (no margin checking)
            pass
        
        # Create order record
        self.orders[order_id] = {
            'order_id': order_id,
            'tradingsymbol': tradingsymbol,
            'exchange': exchange,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'price': price,
            'product': product,
            'order_type': order_type,
            'status': 'COMPLETE',
            'order_timestamp': self.current_timestamp,
            'filled_quantity': quantity
        }
        
        # Update position if the order is completed
        if tradingsymbol not in self.positions:
            self.positions[tradingsymbol] = {
                'quantity': 0,
                'average_price': 0,
                'last_price': 0,
                'pnl': 0,
                'instrument_token': 12345
            }
        
        pos = self.positions[tradingsymbol]
        prev_quantity = pos['quantity']
        prev_avg_price = pos['average_price']
        
        # Update quantity
        if transaction_type == 'BUY':
            new_quantity = prev_quantity + quantity
        else:  # SELL
            new_quantity = prev_quantity - quantity
        
        # Update average price based on transaction type
        if transaction_type == 'BUY':
            # Adding to position
            new_value = (prev_quantity * prev_avg_price) + (quantity * price)
            if new_quantity != 0:
                new_avg_price = new_value / new_quantity
            else:
                new_avg_price = 0
        elif transaction_type == 'SELL' and prev_quantity > 0:
            # Reducing long position
            new_avg_price = prev_avg_price  # Average price doesn't change when selling part of position
        else:  # SELL to create short position or add to short position
            new_value = (abs(prev_quantity) * prev_avg_price) + (quantity * price)
            if new_quantity != 0:
                new_avg_price = new_value / abs(new_quantity)
            else:
                new_avg_price = 0
        
        # Update position
        pos['quantity'] = new_quantity
        pos['average_price'] = new_avg_price
        pos['last_price'] = price
        
        # Track the trade for P&L calculation
        self.trades.append({
            'order_id': order_id,
            'timestamp': self.current_timestamp,
            'symbol': tradingsymbol,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'price': price,
            'value': cost
        })
        
        return order_id
    
    def modify_order(self, variety: str, order_id: str, **kwargs) -> Dict[str, Any]:
        """
        Mock modify_order method
        """
        return {
            'order_id': order_id,
            'status': 'MODIFIED'
        }
    
    def cancel_order(self, variety: str, order_id: str) -> Dict[str, Any]:
        """
        Mock cancel_order method
        """
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'CANCELLED'
        
        return {
            'order_id': order_id,
            'status': 'CANCELLED'
        }
    
    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Mock get_order_history method
        """
        if order_id in self.orders:
            return [self.orders[order_id]]
        return []
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """
        Mock get_orders method
        """
        return list(self.orders.values())
    
    def get_trades(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Mock get_trades method
        """
        order_trades = [t for t in self.trades if t['order_id'] == order_id]
        return order_trades
    
    def margins(self) -> Dict[str, Any]:
        """
        Mock margins method
        """
        return {
            'equity': {
                'enabled': True,
                'net': self.current_balance,
                'available': {
                    'ad_hoc_margin': 0,
                    'cash': self.current_balance,
                    'collateral': 0,
                },
                'utilised': {
                    'debits': self.initial_balance - self.current_balance,
                    'exposure': 0,
                    'm2m_realised': 0,
                    'm2m_unrealised': 0,
                    'option_premium': 0,
                    'payout': 0,
                    'span': 0,
                    'holding_sales': 0,
                    ' turnover': 0,
                }
            }
        }
    
    def get_trigger_range(self, exchange: str, tradingsymbol: str, transaction_type: str) -> Dict[str, float]:
        """
        Mock get_trigger_range method
        """
        return {
            'lower': 95.0,
            'upper': 105.0,
        }

    # Additional utility methods that might be needed for backtesting
    def get_historical_data(self, instrument_token: int, from_date: str, to_date: str, interval: str) -> pd.DataFrame:
        """
        Mock method to get historical data
        """
        # This is just a placeholder - in a real backtesting scenario, 
        # you would use actual historical data
        dates = pd.date_range(start=from_date, end=to_date, freq=interval[:1])
        # Generate mock OHLC data
        np.random.seed(42)  # For reproducible results
        close_prices = 100 + np.random.randn(len(dates)).cumsum()
        open_prices = close_prices + np.random.uniform(-0.5, 0.5, len(dates))
        high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 1, len(dates))
        low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 1, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.random.randint(10000, 50000, len(dates))
        }, index=dates)