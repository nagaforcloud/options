"""
Database module for Options Wheel Strategy Trading Bot
Handles SQLite database operations for persistence
"""
import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Trade, Position
from utils.logging_utils import logger
from .generic_dao import TradeDAO, PositionDAO


class DatabaseManager:
    """Manages SQLite database operations for the trading bot using Generic DAOs"""
    
    def __init__(self, db_path: str = "trading_data.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self.init_db()
        
        # Initialize DAOs for common operations
        self.trade_dao = TradeDAO(db_path)
        self.position_dao = PositionDAO(db_path)
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def init_db(self):
        """Initialize database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    instrument_token INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    product TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    filled_quantity INTEGER NOT NULL,
                    average_price REAL NOT NULL,
                    trigger_price REAL NOT NULL,
                    validity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    disclosed_quantity INTEGER NOT NULL,
                    market_protection REAL NOT NULL,
                    order_timestamp TEXT,
                    exchange_timestamp TEXT,
                    exchange_order_id TEXT,
                    parent_order_id TEXT,
                    trade_type TEXT DEFAULT 'fno',
                    tax_category TEXT DEFAULT 'STT_applicable',
                    stt_paid REAL DEFAULT 0.0,
                    brokerage REAL DEFAULT 0.0,
                    taxes REAL DEFAULT 0.0,
                    turnover_charges REAL DEFAULT 0.0,
                    stamp_duty REAL DEFAULT 0.0,
                    date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for trades table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id)')
            
            # Positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    exchange TEXT NOT NULL,
                    instrument_token INTEGER NOT NULL,
                    product TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    average_price REAL NOT NULL,
                    pnl REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    multiplier REAL NOT NULL,
                    last_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    buy_quantity INTEGER NOT NULL,
                    buy_price REAL NOT NULL,
                    buy_value REAL NOT NULL,
                    sell_quantity INTEGER NOT NULL,
                    sell_price REAL NOT NULL,
                    sell_value REAL NOT NULL,
                    day_buy_quantity INTEGER NOT NULL,
                    day_buy_price REAL NOT NULL,
                    day_buy_value REAL NOT NULL,
                    day_sell_quantity INTEGER NOT NULL,
                    day_sell_price REAL NOT NULL,
                    day_sell_value REAL NOT NULL,
                    entry_timestamp TEXT,
                    exit_timestamp TEXT,
                    position_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for positions table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)')
            
            # Performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance metrics table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_metric_name ON performance_metrics(metric_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)')
            
            # Strategy sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    pnl REAL NOT NULL,
                    trades_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
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
    
    # Trade Operations - now using GenericDAO
    def insert_trade(self, trade: Trade) -> bool:
        """Insert a trade record using the TradeDAO"""
        return self.trade_dao.insert_trade(trade)
    
    def get_trade_by_id(self, order_id: str) -> Optional[Trade]:
        """Retrieve a trade by order ID using the TradeDAO"""
        return self.trade_dao.get_trade_by_id(order_id)
    
    def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        """Retrieve all trades for a given symbol using the TradeDAO"""
        return self.trade_dao.get_trades_by_symbol(symbol)
    
    def get_trades_by_date_range(self, start_date: str, end_date: str) -> List[Trade]:
        """
        Retrieve all trades within a date range
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of Trade objects
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trades 
                    WHERE date >= ? AND date <= ? 
                    ORDER BY order_timestamp DESC
                ''', (start_date, end_date))
                rows = cursor.fetchall()
                
                from datetime import datetime
                trades = []
                for row in rows:
                    row_dict = dict(row)
                    order_timestamp = datetime.fromisoformat(row_dict['order_timestamp']) if row_dict['order_timestamp'] else None
                    exchange_timestamp = datetime.fromisoformat(row_dict['exchange_timestamp']) if row_dict['exchange_timestamp'] else None
                    date = datetime.fromisoformat(row_dict['date']) if row_dict['date'] else None
                    
                    trade = Trade(
                        order_id=row_dict['order_id'],
                        symbol=row_dict['symbol'],
                        exchange=row_dict['exchange'],
                        instrument_token=row_dict['instrument_token'],
                        transaction_type=row_dict['transaction_type'],
                        order_type=row_dict['order_type'],
                        product=row_dict['product'],
                        quantity=row_dict['quantity'],
                        price=row_dict['price'],
                        filled_quantity=row_dict['filled_quantity'],
                        average_price=row_dict['average_price'],
                        trigger_price=row_dict['trigger_price'],
                        validity=row_dict['validity'],
                        status=row_dict['status'],
                        disclosed_quantity=row_dict['disclosed_quantity'],
                        market_protection=row_dict['market_protection'],
                        order_timestamp=order_timestamp,
                        exchange_timestamp=exchange_timestamp,
                        exchange_order_id=row_dict['exchange_order_id'],
                        parent_order_id=row_dict['parent_order_id'],
                        trade_type=row_dict.get('trade_type', 'fno'),
                        tax_category=row_dict.get('tax_category', 'STT_applicable'),
                        stt_paid=row_dict.get('stt_paid', 0.0),
                        brokerage=row_dict.get('brokerage', 0.0),
                        taxes=row_dict.get('taxes', 0.0),
                        turnover_charges=row_dict.get('turnover_charges', 0.0),
                        stamp_duty=row_dict.get('stamp_duty', 0.0),
                        date=date
                    )
                    trades.append(trade)
                
                return trades
        except Exception as e:
            logger.error(f"Error retrieving trades for date range {start_date} to {end_date}: {e}")
            return []
    
    def get_all_trades(self) -> List[Trade]:
        """
        Retrieve all trades from the database using the TradeDAO
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM trades ORDER BY order_timestamp DESC')
                rows = cursor.fetchall()
                
                from datetime import datetime
                trades = []
                for row in rows:
                    row_dict = dict(row)
                    order_timestamp = datetime.fromisoformat(row_dict['order_timestamp']) if row_dict['order_timestamp'] else None
                    exchange_timestamp = datetime.fromisoformat(row_dict['exchange_timestamp']) if row_dict['exchange_timestamp'] else None
                    date = datetime.fromisoformat(row_dict['date']) if row_dict['date'] else None
                    
                    trade = Trade(
                        order_id=row_dict['order_id'],
                        symbol=row_dict['symbol'],
                        exchange=row_dict['exchange'],
                        instrument_token=row_dict['instrument_token'],
                        transaction_type=row_dict['transaction_type'],
                        order_type=row_dict['order_type'],
                        product=row_dict['product'],
                        quantity=row_dict['quantity'],
                        price=row_dict['price'],
                        filled_quantity=row_dict['filled_quantity'],
                        average_price=row_dict['average_price'],
                        trigger_price=row_dict['trigger_price'],
                        validity=row_dict['validity'],
                        status=row_dict['status'],
                        disclosed_quantity=row_dict['disclosed_quantity'],
                        market_protection=row_dict['market_protection'],
                        order_timestamp=order_timestamp,
                        exchange_timestamp=exchange_timestamp,
                        exchange_order_id=row_dict['exchange_order_id'],
                        parent_order_id=row_dict['parent_order_id'],
                        trade_type=row_dict.get('trade_type', 'fno'),
                        tax_category=row_dict.get('tax_category', 'STT_applicable'),
                        stt_paid=row_dict.get('stt_paid', 0.0),
                        brokerage=row_dict.get('brokerage', 0.0),
                        taxes=row_dict.get('taxes', 0.0),
                        turnover_charges=row_dict.get('turnover_charges', 0.0),
                        stamp_duty=row_dict.get('stamp_duty', 0.0),
                        date=date
                    )
                    trades.append(trade)
                
                return trades
        except Exception as e:
            logger.error(f"Error retrieving all trades: {e}")
            return []
    
    # Position Operations - now using GenericDAO
    def insert_position(self, position: Position) -> bool:
        """Insert or update a position record using the PositionDAO"""
        return self.position_dao.insert_position(position)
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Retrieve a position by symbol using the PositionDAO"""
        return self.position_dao.get_position_by_symbol(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """
        Retrieve all positions from the database
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM positions')
                rows = cursor.fetchall()
                
                from datetime import datetime
                positions = []
                for row in rows:
                    row_dict = dict(row)
                    entry_timestamp = datetime.fromisoformat(row_dict['entry_timestamp']) if row_dict['entry_timestamp'] else None
                    exit_timestamp = datetime.fromisoformat(row_dict['exit_timestamp']) if row_dict['exit_timestamp'] else None
                    
                    position = Position(
                        symbol=row_dict['symbol'],
                        exchange=row_dict['exchange'],
                        instrument_token=row_dict['instrument_token'],
                        product=row_dict['product'],
                        quantity=row_dict['quantity'],
                        average_price=row_dict['average_price'],
                        pnl=row_dict['pnl'],
                        unrealized_pnl=row_dict['unrealized_pnl'],
                        realized_pnl=row_dict['realized_pnl'],
                        multiplier=row_dict['multiplier'],
                        last_price=row_dict['last_price'],
                        close_price=row_dict['close_price'],
                        buy_quantity=row_dict['buy_quantity'],
                        buy_price=row_dict['buy_price'],
                        buy_value=row_dict['buy_value'],
                        sell_quantity=row_dict['sell_quantity'],
                        sell_price=row_dict['sell_price'],
                        sell_value=row_dict['sell_value'],
                        day_buy_quantity=row_dict['day_buy_quantity'],
                        day_buy_price=row_dict['day_buy_price'],
                        day_buy_value=row_dict['day_buy_value'],
                        day_sell_quantity=row_dict['day_sell_quantity'],
                        day_sell_price=row_dict['day_sell_price'],
                        day_sell_value=row_dict['day_sell_value'],
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=exit_timestamp,
                        position_type=row_dict['position_type']
                    )
                    positions.append(position)
                
                return positions
        except Exception as e:
            logger.error(f"Error retrieving all positions: {e}")
            return []
    
    def delete_position(self, symbol: str) -> bool:
        """
        Delete a position by symbol using the PositionDAO
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM positions WHERE symbol = ?', (symbol,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Position deleted successfully: {symbol}")
                    return True
                else:
                    logger.warning(f"No position found to delete for symbol: {symbol}")
                    return False
        except Exception as e:
            logger.error(f"Error deleting position {symbol}: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database
        
        Args:
            backup_path: Path to save the backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
                logger.info(f"Database backed up to: {backup_path}")
                return True
        except Exception as e:
            logger.error(f"Error backing up database to {backup_path}: {e}")
            return False
    
    def get_table_counts(self) -> Dict[str, int]:
        """
        Get count of records in each table
        
        Returns:
            Dictionary with table names and record counts
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                tables = ['trades', 'positions', 'performance_metrics', 'strategy_sessions']
                counts = {}
                
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                    row = cursor.fetchone()
                    counts[table] = row['count']
                
                return counts
        except Exception as e:
            logger.error(f"Error getting table counts: {e}")
            return {}


# Global instance for easy access
db_manager = DatabaseManager()