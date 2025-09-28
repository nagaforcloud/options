"""
Generic Data Access Object for the Options Wheel Strategy Trading Bot
Provides common CRUD operations to reduce code redundancy
"""
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime
import json
import os
from utils.logging_utils import logger
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Trade, Position


T = TypeVar('T')


class GenericDAO(Generic[T]):
    """Generic DAO for common database operations"""
    
    def __init__(self, db_path: str = "trading_data.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self.table_name = None
        self.columns = []
        self.primary_key = 'id'
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def insert(self, data: Dict[str, Any]) -> bool:
        """Generic insert operation"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare the INSERT statement
                columns = [k for k in data.keys() if k in self.columns]
                placeholders = ', '.join(['?' for _ in columns])
                columns_str = ', '.join(columns)
                
                query = f"INSERT OR REPLACE INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                values = [data[k] for k in columns]
                
                cursor.execute(query, values)
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting into {self.table_name}: {e}")
            return False
    
    def get_by_id(self, item_id: Any) -> Optional[Dict[str, Any]]:
        """Generic get by ID operation"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = ?"
                cursor.execute(query, (item_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting {self.table_name} by ID: {e}")
            return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Generic get all operation"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM {self.table_name} ORDER BY {self.primary_key}"
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all {self.table_name}: {e}")
            return []
    
    def update(self, item_id: Any, data: Dict[str, Any]) -> bool:
        """Generic update operation"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare the UPDATE statement
                update_fields = [k for k in data.keys() if k in self.columns and k != self.primary_key]
                set_clause = ', '.join([f"{field} = ?" for field in update_fields])
                values = [data[k] for k in update_fields] + [item_id]
                
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.primary_key} = ?"
                cursor.execute(query, values)
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating {self.table_name}: {e}")
            return False
    
    def delete(self, item_id: Any) -> bool:
        """Generic delete operation"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?"
                cursor.execute(query, (item_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting from {self.table_name}: {e}")
            return False


class TradeDAO(GenericDAO[Trade]):
    """DAO specifically for Trade operations"""
    
    def __init__(self, db_path: str = "trading_data.db"):
        super().__init__(db_path)
        self.table_name = 'trades'
        self.primary_key = 'order_id'
        self.columns = [
            'order_id', 'symbol', 'exchange', 'instrument_token', 'transaction_type',
            'order_type', 'product', 'quantity', 'price', 'filled_quantity',
            'average_price', 'trigger_price', 'validity', 'status', 'disclosed_quantity',
            'market_protection', 'order_timestamp', 'exchange_timestamp', 'exchange_order_id',
            'parent_order_id', 'trade_type', 'tax_category', 'stt_paid', 'brokerage',
            'taxes', 'turnover_charges', 'stamp_duty', 'date'
        ]
    
    def insert_trade(self, trade: Trade) -> bool:
        """Insert a trade object"""
        # Convert datetime objects to ISO format strings
        order_timestamp_str = trade.order_timestamp.isoformat() if trade.order_timestamp else None
        exchange_timestamp_str = trade.exchange_timestamp.isoformat() if trade.exchange_timestamp else None
        date_str = trade.date.isoformat() if trade.date else None
        
        trade_dict = {
            'order_id': trade.order_id,
            'symbol': trade.symbol,
            'exchange': trade.exchange,
            'instrument_token': trade.instrument_token,
            'transaction_type': trade.transaction_type,
            'order_type': trade.order_type,
            'product': trade.product,
            'quantity': trade.quantity,
            'price': trade.price,
            'filled_quantity': trade.filled_quantity,
            'average_price': trade.average_price,
            'trigger_price': trade.trigger_price,
            'validity': trade.validity,
            'status': trade.status,
            'disclosed_quantity': trade.disclosed_quantity,
            'market_protection': trade.market_protection,
            'order_timestamp': order_timestamp_str,
            'exchange_timestamp': exchange_timestamp_str,
            'exchange_order_id': trade.exchange_order_id,
            'parent_order_id': trade.parent_order_id,
            'trade_type': trade.trade_type,
            'tax_category': trade.tax_category,
            'stt_paid': trade.stt_paid,
            'brokerage': trade.brokerage,
            'taxes': trade.taxes,
            'turnover_charges': trade.turnover_charges,
            'stamp_duty': trade.stamp_duty,
            'date': date_str
        }
        
        return self.insert(trade_dict)
    
    def get_trade_by_id(self, order_id: str) -> Optional[Trade]:
        """Get a trade by order ID"""
        row = self.get_by_id(order_id)
        if not row:
            return None
        
        return self._row_to_trade(row)
    
    def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        """Get all trades for a given symbol"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM {self.table_name} WHERE symbol = ? ORDER BY order_timestamp DESC"
                cursor.execute(query, (symbol,))
                rows = cursor.fetchall()
                return [self._row_to_trade(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting trades for symbol {symbol}: {e}")
            return []
    
    def _row_to_trade(self, row: Dict[str, Any]) -> Trade:
        """Convert row dict to Trade object"""
        from datetime import datetime
        
        order_timestamp = datetime.fromisoformat(row['order_timestamp']) if row['order_timestamp'] else None
        exchange_timestamp = datetime.fromisoformat(row['exchange_timestamp']) if row['exchange_timestamp'] else None
        date = datetime.fromisoformat(row['date']) if row['date'] else None
        
        return Trade(
            order_id=row['order_id'],
            symbol=row['symbol'],
            exchange=row['exchange'],
            instrument_token=row['instrument_token'],
            transaction_type=row['transaction_type'],
            order_type=row['order_type'],
            product=row['product'],
            quantity=row['quantity'],
            price=row['price'],
            filled_quantity=row['filled_quantity'],
            average_price=row['average_price'],
            trigger_price=row['trigger_price'],
            validity=row['validity'],
            status=row['status'],
            disclosed_quantity=row['disclosed_quantity'],
            market_protection=row['market_protection'],
            order_timestamp=order_timestamp,
            exchange_timestamp=exchange_timestamp,
            exchange_order_id=row['exchange_order_id'],
            parent_order_id=row['parent_order_id'],
            trade_type=row.get('trade_type', 'fno'),
            tax_category=row.get('tax_category', 'STT_applicable'),
            stt_paid=row.get('stt_paid', 0.0),
            brokerage=row.get('brokerage', 0.0),
            taxes=row.get('taxes', 0.0),
            turnover_charges=row.get('turnover_charges', 0.0),
            stamp_duty=row.get('stamp_duty', 0.0),
            date=date
        )


class PositionDAO(GenericDAO[Position]):
    """DAO specifically for Position operations"""
    
    def __init__(self, db_path: str = "trading_data.db"):
        super().__init__(db_path)
        self.table_name = 'positions'
        self.primary_key = 'symbol'
        self.columns = [
            'symbol', 'exchange', 'instrument_token', 'product', 'quantity',
            'average_price', 'pnl', 'unrealized_pnl', 'realized_pnl', 'multiplier',
            'last_price', 'close_price', 'buy_quantity', 'buy_price', 'buy_value',
            'sell_quantity', 'sell_price', 'sell_value', 'day_buy_quantity', 'day_buy_price',
            'day_buy_value', 'day_sell_quantity', 'day_sell_price', 'day_sell_value',
            'entry_timestamp', 'exit_timestamp', 'position_type'
        ]
    
    def insert_position(self, position: Position) -> bool:
        """Insert a position object"""
        from datetime import datetime
        
        entry_timestamp_str = position.entry_timestamp.isoformat() if position.entry_timestamp else None
        exit_timestamp_str = position.exit_timestamp.isoformat() if position.exit_timestamp else None
        
        position_dict = {
            'symbol': position.symbol,
            'exchange': position.exchange,
            'instrument_token': position.instrument_token,
            'product': position.product,
            'quantity': position.quantity,
            'average_price': position.average_price,
            'pnl': position.pnl,
            'unrealized_pnl': position.unrealized_pnl,
            'realized_pnl': position.realized_pnl,
            'multiplier': position.multiplier,
            'last_price': position.last_price,
            'close_price': position.close_price,
            'buy_quantity': position.buy_quantity,
            'buy_price': position.buy_price,
            'buy_value': position.buy_value,
            'sell_quantity': position.sell_quantity,
            'sell_price': position.sell_price,
            'sell_value': position.sell_value,
            'day_buy_quantity': position.day_buy_quantity,
            'day_buy_price': position.day_buy_price,
            'day_buy_value': position.day_buy_value,
            'day_sell_quantity': position.day_sell_quantity,
            'day_sell_price': position.day_sell_price,
            'day_sell_value': position.day_sell_value,
            'entry_timestamp': entry_timestamp_str,
            'exit_timestamp': exit_timestamp_str,
            'position_type': position.position_type
        }
        
        return self.insert(position_dict)
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Get a position by symbol"""
        row = self.get_by_id(symbol)
        if not row:
            return None
        
        return self._row_to_position(row)
    
    def _row_to_position(self, row: Dict[str, Any]) -> Position:
        """Convert row dict to Position object"""
        from datetime import datetime
        
        entry_timestamp = datetime.fromisoformat(row['entry_timestamp']) if row['entry_timestamp'] else None
        exit_timestamp = datetime.fromisoformat(row['exit_timestamp']) if row['exit_timestamp'] else None
        
        return Position(
            symbol=row['symbol'],
            exchange=row['exchange'],
            instrument_token=row['instrument_token'],
            product=row['product'],
            quantity=row['quantity'],
            average_price=row['average_price'],
            pnl=row['pnl'],
            unrealized_pnl=row['unrealized_pnl'],
            realized_pnl=row['realized_pnl'],
            multiplier=row['multiplier'],
            last_price=row['last_price'],
            close_price=row['close_price'],
            buy_quantity=row['buy_quantity'],
            buy_price=row['buy_price'],
            buy_value=row['buy_value'],
            sell_quantity=row['sell_quantity'],
            sell_price=row['sell_price'],
            sell_value=row['sell_value'],
            day_buy_quantity=row['day_buy_quantity'],
            day_buy_price=row['day_buy_price'],
            day_buy_value=row['day_buy_value'],
            day_sell_quantity=row['day_sell_quantity'],
            day_sell_price=row['day_sell_price'],
            day_sell_value=row['day_sell_value'],
            entry_timestamp=entry_timestamp,
            exit_timestamp=exit_timestamp,
            position_type=row['position_type']
        )