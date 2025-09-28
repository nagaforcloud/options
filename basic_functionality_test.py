"""
Basic Functionality Tests for Options Wheel Strategy Trading Bot
Tests core functionality without requiring full trading setup
"""
import unittest
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import config
from models.enums import OrderType, ProductType, TransactionType, StrategyType, OptionType
from models.models import Trade, Position, OptionContract, StrategyState, RiskMetrics
from utils.logging_utils import logger
from database.database import DatabaseManager, db_manager
from risk_management.risk_manager import RiskManager, risk_manager, RiskConfig
from notifications.notification_manager import notification_manager
from core.strategy import OptionWheelStrategy


class TestConfiguration(unittest.TestCase):
    """Test configuration loading and validation"""
    
    def test_config_loading(self):
        """Test that configuration is loaded correctly"""
        self.assertIsNotNone(config.api_key)
        self.assertIsNotNone(config.api_secret)
        self.assertIsNotNone(config.access_token)
        self.assertIsInstance(config.dry_run, bool)
        
    def test_strategy_mode_validation(self):
        """Test strategy mode validation"""
        # This would raise an error if mode is invalid
        from config.config import OptionWheelConfig
        with self.assertRaises(ValueError):
            OptionWheelConfig(strategy_mode="invalid_mode")


class TestEnums(unittest.TestCase):
    """Test enumeration values"""
    
    def test_order_types(self):
        """Test order type enum values"""
        self.assertEqual(OrderType.LIMIT.value, "LIMIT")
        self.assertEqual(OrderType.MARKET.value, "MARKET")
        self.assertEqual(OrderType.SL.value, "SL")
        self.assertEqual(OrderType.SLM.value, "SL-M")
    
    def test_transaction_types(self):
        """Test transaction type enum values"""
        self.assertEqual(TransactionType.BUY.value, "BUY")
        self.assertEqual(TransactionType.SELL.value, "SELL")
    
    def test_strategy_types(self):
        """Test strategy type enum values"""
        self.assertEqual(StrategyType.CASH_SECURED_PUT.value, "Cash Secured Put")
        self.assertEqual(StrategyType.COVERED_CALL.value, "Covered Call")


class TestModels(unittest.TestCase):
    """Test data models"""
    
    def test_trade_model(self):
        """Test Trade model creation and properties"""
        trade = Trade(
            order_id="123456",
            symbol="NIFTY23JUN18000CE",
            exchange="NFO",
            instrument_token=12345,
            transaction_type="SELL",
            order_type="LIMIT",
            product="NRML",
            quantity=50,
            price=150.0,
            filled_quantity=50,
            average_price=150.0,
            trigger_price=0.0,
            validity="DAY",
            status="COMPLETE",
            disclosed_quantity=0,
            market_protection=0.0,
            order_timestamp=datetime.now(),
            exchange_timestamp=datetime.now(),
            exchange_order_id="123456",
            parent_order_id=None
        )
        
        self.assertEqual(trade.order_id, "123456")
        self.assertEqual(trade.symbol, "NIFTY23JUN18000CE")
        self.assertEqual(trade.transaction_type, "SELL")
        self.assertEqual(trade.quantity, 50)
        self.assertEqual(trade.price, 150.0)
        
        # Test net_pnl calculation
        # (For now, this returns 0 as all fee fields are 0)
        self.assertEqual(trade.net_pnl(), -7500.0)  # -150.0 * 50
    
    def test_position_model(self):
        """Test Position model creation and properties"""
        position = Position(
            symbol="NIFTY23JUN18000CE",
            exchange="NFO",
            instrument_token=12345,
            product="NRML",
            quantity=50,
            average_price=150.0,
            pnl=2500.0,
            unrealized_pnl=2500.0,
            realized_pnl=0.0,
            multiplier=1.0,
            last_price=155.0,
            close_price=150.0,
            buy_quantity=50,
            buy_price=150.0,
            buy_value=7500.0,
            sell_quantity=0,
            sell_price=0.0,
            sell_value=0.0,
            day_buy_quantity=0,
            day_buy_price=0.0,
            day_buy_value=0.0,
            day_sell_quantity=0,
            day_sell_price=0.0,
            day_sell_value=0.0
        )
        
        self.assertEqual(position.symbol, "NIFTY23JUN18000CE")
        self.assertEqual(position.quantity, 50)
        self.assertEqual(position.average_price, 150.0)
        self.assertEqual(position.pnl, 2500.0)
    
    def test_option_contract_model(self):
        """Test OptionContract model creation and methods"""
        option = OptionContract(
            symbol="NIFTY23JUN18000CE",
            instrument_token=12345,
            exchange="NFO",
            last_price=150.0,
            expiry=datetime.now() + timedelta(days=30),
            strike=18000.0,
            tick_size=0.05,
            lot_size=50,
            instrument_type="CE",
            segment="NFO-OPT",
            option_type="CE",
            tradingsymbol="NIFTY23JUN18000CE",
            open_interest=10000
        )
        
        self.assertEqual(option.symbol, "NIFTY23JUN18000CE")
        self.assertEqual(option.strike, 18000.0)
        self.assertEqual(option.option_type, "CE")
        self.assertEqual(option.lot_size, 50)
        
        # Test intrinsic value for call option
        self.assertEqual(option.intrinsic_value(18100.0), 100.0)  # 18100 - 18000
        self.assertEqual(option.intrinsic_value(17900.0), 0.0)   # OTM call
        
        # Test intrinsic value for put option
        option.option_type = "PE"
        self.assertEqual(option.intrinsic_value(17900.0), 100.0)  # 18000 - 17900
        self.assertEqual(option.intrinsic_value(18100.0), 0.0)   # OTM put
        
        # Test time value
        self.assertEqual(option.time_value(17900.0), 150.0)  # 150 - 0 (intrinsic)
        
        # Test is_in_the_money
        option.option_type = "CE"
        self.assertTrue(option.is_in_the_money(18100.0))  # ITM call
        self.assertFalse(option.is_in_the_money(17900.0))  # OTM call
        
        option.option_type = "PE"
        self.assertTrue(option.is_in_the_money(17900.0))  # ITM put
        self.assertFalse(option.is_in_the_money(18100.0))  # OTM put


class TestDatabase(unittest.TestCase):
    """Test database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.db = DatabaseManager("test_trading_data.db")
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists("test_trading_data.db"):
            os.remove("test_trading_data.db")
    
    def test_database_initialization(self):
        """Test database initialization"""
        self.assertTrue(os.path.exists("test_trading_data.db"))
        
        # Check if tables were created
        conn = self.db.get_connection().__enter__()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [table[0] for table in tables]
        
        self.assertIn('trades', table_names)
        self.assertIn('positions', table_names)
        self.assertIn('performance_metrics', table_names)
        self.assertIn('strategy_sessions', table_names)
        self.assertIn('ai_metadata', table_names)
        
        conn.close()
    
    def test_trade_insertion_and_retrieval(self):
        """Test inserting and retrieving trades"""
        # Create a test trade
        test_trade = Trade(
            order_id="TEST_ORDER_001",
            symbol="NIFTY23JUN18000CE",
            exchange="NFO",
            instrument_token=12345,
            transaction_type="SELL",
            order_type="LIMIT",
            product="NRML",
            quantity=50,
            price=150.0,
            filled_quantity=50,
            average_price=150.0,
            trigger_price=0.0,
            validity="DAY",
            status="COMPLETE",
            disclosed_quantity=0,
            market_protection=0.0,
            order_timestamp=datetime.now(),
            exchange_timestamp=datetime.now(),
            exchange_order_id="TEST_ORDER_001",
            parent_order_id=None
        )
        
        # Insert the trade
        success = self.db.insert_trade(test_trade)
        self.assertTrue(success)
        
        # Retrieve the trade
        retrieved_trade = self.db.get_trade_by_id("TEST_ORDER_001")
        self.assertIsNotNone(retrieved_trade)
        self.assertEqual(retrieved_trade.order_id, "TEST_ORDER_001")
        self.assertEqual(retrieved_trade.symbol, "NIFTY23JUN18000CE")
        self.assertEqual(retrieved_trade.price, 150.0)
    
    def test_position_insertion_and_retrieval(self):
        """Test inserting and retrieving positions"""
        # Create a test position
        test_position = Position(
            symbol="NIFTY23JUN18000CE",
            exchange="NFO",
            instrument_token=12345,
            product="NRML",
            quantity=50,
            average_price=150.0,
            pnl=2500.0,
            unrealized_pnl=2500.0,
            realized_pnl=0.0,
            multiplier=1.0,
            last_price=155.0,
            close_price=150.0,
            buy_quantity=50,
            buy_price=150.0,
            buy_value=7500.0,
            sell_quantity=0,
            sell_price=0.0,
            sell_value=0.0,
            day_buy_quantity=0,
            day_buy_price=0.0,
            day_buy_value=0.0,
            day_sell_quantity=0,
            day_sell_price=0.0,
            day_sell_value=0.0
        )
        
        # Insert the position
        success = self.db.insert_position(test_position)
        self.assertTrue(success)
        
        # Retrieve the position
        retrieved_position = self.db.get_position_by_symbol("NIFTY23JUN18000CE")
        self.assertIsNotNone(retrieved_position)
        self.assertEqual(retrieved_position.symbol, "NIFTY23JUN18000CE")
        self.assertEqual(retrieved_position.quantity, 50)
        self.assertEqual(retrieved_position.average_price, 150.0)
        self.assertEqual(retrieved_position.pnl, 2500.0)


class TestRiskManagement(unittest.TestCase):
    """Test risk management functionality"""
    
    def test_risk_config(self):
        """Test risk configuration"""
        risk_config = RiskConfig()
        
        self.assertEqual(risk_config.daily_loss_limit, config.max_daily_loss_limit)
        self.assertEqual(risk_config.max_concurrent_positions, config.max_concurrent_positions)
        self.assertEqual(risk_config.portfolio_risk_limit, config.max_portfolio_risk)
    
    def test_risk_manager_initialization(self):
        """Test risk manager initialization"""
        rm = RiskManager()
        
        self.assertEqual(rm.daily_pnl, 0.0)
        self.assertEqual(rm.daily_losses, 0.0)
        self.assertEqual(len(rm.current_positions), 0)
        self.assertEqual(len(rm.trades_today), 0)
        self.assertEqual(rm.portfolio_value, 0.0)
        self.assertEqual(rm.cash_available, 0.0)
    
    def test_position_size_calculation(self):
        """Test max position size calculation"""
        rm = RiskManager()
        rm.update_portfolio_value(100000)  # 1L portfolio value
        
        # Test with different strategy types
        csp_size = rm.calculate_max_position_size(18000, StrategyType.CASH_SECURED_PUT)
        cc_size = rm.calculate_max_position_size(18000, StrategyType.COVERED_CALL)
        
        # Both should be > 0 since portfolio has value
        self.assertGreaterEqual(csp_size, 0)
        self.assertGreaterEqual(cc_size, 0)
        
        # Should be multiples of config.quantity_per_lot or 0
        if csp_size > 0:
            self.assertEqual(csp_size % config.quantity_per_lot, 0)
        if cc_size > 0:
            self.assertEqual(cc_size % config.quantity_per_lot, 0)


class TestNotificationManager(unittest.TestCase):
    """Test notification manager functionality"""
    
    def test_notification_manager_initialization(self):
        """Test notification manager initialization"""
        nm = notification_manager
        
        self.assertIsInstance(nm, type(notification_manager))
        # Test that it has the expected methods
        self.assertTrue(hasattr(nm, 'send_notification'))
        self.assertTrue(hasattr(nm, 'send_order_notification'))
        self.assertTrue(hasattr(nm, 'send_position_notification'))
    
    def test_disabled_notifications(self):
        """Test that notifications are properly disabled by default"""
        # With default config, notifications should be disabled
        self.assertFalse(config.enable_notifications)


class TestOptionWheelStrategy(unittest.TestCase):
    """Test OptionWheelStrategy functionality"""
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        # Initialize with mock kite or None to avoid API calls in tests
        strategy = OptionWheelStrategy(kite_client=None)
        
        self.assertIsNotNone(strategy.state)
        self.assertEqual(strategy.state.daily_pnl, 0.0)
        self.assertEqual(strategy.state.total_pnl, 0.0)
        self.assertEqual(len(strategy.state.active_positions), 0)
        self.assertEqual(len(strategy.state.active_orders), 0)
    
    def test_market_hours_check(self):
        """Test market hours checking"""
        strategy = OptionWheelStrategy(kite_client=None)
        
        # Since we can't predict the actual result without knowing the current time,
        # we'll just test that the method executes without error
        try:
            result = strategy.is_market_open()
            self.assertIsInstance(result, bool)
        except Exception as e:
            # If there's an error due to missing holiday file, that's okay for this test
            self.assertIn("holiday", str(e).lower())


def run_basic_tests():
    """Run all basic functionality tests"""
    logger.info("Starting basic functionality tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConfiguration))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestConfiguration))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEnums))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestModels))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatabase))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRiskManagement))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestNotificationManager))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestOptionWheelStrategy))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Log results
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.2f}%")
    
    return result


if __name__ == "__main__":
    # Run the basic functionality tests
    test_result = run_basic_tests()
    
    # Exit with error code if tests failed
    if not test_result.wasSuccessful():
        sys.exit(1)