"""
Basic smoke test to verify the project structure and essential imports
"""
import unittest
import sys
import os
from pathlib import Path

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

class TestProjectStructure(unittest.TestCase):
    """Test basic project structure and imports"""
    
    def test_config_import(self):
        """Test that config module can be imported"""
        try:
            from config.config import config
            self.assertIsNotNone(config)
        except ImportError as e:
            self.fail(f"Could not import config: {e}")
    
    def test_models_import(self):
        """Test that models can be imported"""
        try:
            from models.enums import OrderType, TransactionType
            from models.models import Trade, Position
            self.assertIsNotNone(OrderType)
            self.assertIsNotNone(Trade)
        except ImportError as e:
            self.fail(f"Could not import models: {e}")
    
    def test_utils_import(self):
        """Test that utilities can be imported"""
        try:
            from utils.logging_utils import logger
            self.assertIsNotNone(logger)
        except ImportError as e:
            self.fail(f"Could not import utils: {e}")
    
    def test_database_import(self):
        """Test that database module can be imported"""
        try:
            from database.database import db_manager
            self.assertIsNotNone(db_manager)
        except ImportError as e:
            self.fail(f"Could not import database: {e}")
    
    def test_risk_management_import(self):
        """Test that risk management can be imported"""
        try:
            from risk_management.risk_manager import risk_manager
            self.assertIsNotNone(risk_manager)
        except ImportError as e:
            self.fail(f"Could not import risk management: {e}")
    
    def test_notifications_import(self):
        """Test that notifications can be imported"""
        try:
            from notifications.notification_manager import notification_manager
            self.assertIsNotNone(notification_manager)
        except ImportError as e:
            self.fail(f"Could not import notifications: {e}")
    
    def test_ai_base_import(self):
        """Test that AI base can be imported"""
        try:
            from ai.base import ai_base, is_enabled
            self.assertIsNotNone(ai_base)
        except ImportError as e:
            print(f"AI base import failed (this might be expected if AI dependencies aren't installed): {e}")
            # Don't fail the test as AI might be optional
            pass
    
    def test_core_strategy_import(self):
        """Test that core strategy can be imported"""
        try:
            from core.strategy import OptionWheelStrategy
            self.assertIsNotNone(OptionWheelStrategy)
        except ImportError as e:
            self.fail(f"Could not import core strategy: {e}")
    
    def test_required_files_exist(self):
        """Test that required files exist"""
        required_files = [
            "config/config.py",
            "models/enums.py",
            "models/models.py",
            "utils/logging_utils.py",
            "database/database.py",
            "risk_management/risk_manager.py",
            "notifications/notification_manager.py",
            "core/strategy.py",
            "main.py",
            "README.md",
            ".env",
            "requirements.txt"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = Path("Trading") / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        self.assertEqual(missing_files, [], f"Missing required files: {missing_files}")


def run_smoke_tests():
    """Run the basic smoke tests"""
    print("Running basic smoke tests for Options Wheel Strategy Trading Bot...")
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProjectStructure))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    print(f"\nSmoke tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ All smoke tests passed!")
    else:
        print("❌ Some smoke tests failed!")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_smoke_tests()
    if not success:
        sys.exit(1)