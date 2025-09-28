"""
Final Verification Checks for Options Wheel Strategy Trading Bot
Comprehensive verification of all system components before deployment
"""
import os
import sys
from pathlib import Path
import subprocess
import importlib
import inspect
from datetime import datetime
from typing import Dict, List, Any

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import config
from utils.logging_utils import logger
from database.database import db_manager
from risk_management.risk_manager import risk_manager
from notifications.notification_manager import notification_manager
from core.strategy import OptionWheelStrategy
from models.models import Trade, Position, OptionContract, StrategyState, RiskMetrics
from models.enums import OrderType, ProductType, TransactionType, StrategyType, OptionType
from basic_functionality_test import run_basic_tests


def check_file_structure():
    """Check if all required files and directories exist"""
    required_paths = [
        "Trading/",
        "Trading/config/config.py",
        "Trading/models/enums.py", 
        "Trading/models/models.py",
        "Trading/core/strategy.py",
        "Trading/utils/logging_utils.py",
        "Trading/database/database.py",
        "Trading/risk_management/risk_manager.py",
        "Trading/notifications/notification_manager.py",
        "Trading/dashboard/dashboard.py",
        "Trading/backtesting/",
        "Trading/backtesting/mock_kite.py",
        "Trading/backtesting/nifty_backtesting.py",
        "Trading/backtesting/nse_data_collector.py",
        "Trading/backtesting/sample_data_generator.py",
        "Trading/backtesting/prepare_nifty_data.py",
        "Trading/ai/",
        "Trading/ai/base.py",
        "Trading/ai/rag/",
        "Trading/ai/regime/",
        "Trading/ai/slippage/",
        "Trading/ai/stress/",
        "Trading/ai/kill/",
        "Trading/ai/news/",
        "Trading/ai/compliance/",
        "Trading/ai/i18n/",
        "Trading/ai/voice/",
        "Trading/ai/synth_chain/",
        "Trading/ai/explain/",
        "Trading/ai/hedge/",
        "Trading/ai/mapper/",
        "Trading/ai/whatif/",
        "Trading/ai/automl/",
        "Trading/ai/testgen/",
        "Trading/ai/kelly/",
        "Trading/ai/sentiment/",
        "Trading/ai/patch/",
        "Trading/ai/cache/",
        "Trading/.env",
        "Trading/requirements.txt",
        "Trading/requirements-ai.txt",
        "Trading/main.py",
        "Trading/run_tests.py",
        "Trading/Dockerfile",
        "Trading/docker-compose.yml",
        "Trading/README.md",
        "Trading/data/",
        "Trading/logs/",
        "Trading/historical_trades/",
        "Trading/docs/"
    ]
    
    missing_paths = []
    for path in required_paths:
        full_path = Path("Trading") / Path(path.replace("Trading/", ""))
        if not full_path.exists():
            missing_paths.append(path)
    
    return missing_paths


def check_module_imports():
    """Check if all modules can be imported without errors"""
    modules_to_test = [
        "config.config",
        "models.enums", 
        "models.models",
        "core.strategy",
        "utils.logging_utils",
        "database.database",
        "risk_management.risk_manager",
        "notifications.notification_manager",
        "dashboard.dashboard",
        "backtesting.mock_kite",
        "backtesting.nifty_backtesting",
        "backtesting.nse_data_collector",
        "backtesting.sample_data_generator",
        "ai.base"
    ]
    
    failed_imports = []
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            logger.info(f"✓ Successfully imported {module_name}")
        except ImportError as e:
            logger.error(f"✗ Failed to import {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    return failed_imports


def check_class_definitions():
    """Check if key classes are properly defined"""
    from config.config import OptionWheelConfig
    from models.models import Trade, Position, OptionContract, StrategyState, RiskMetrics
    from core.strategy import OptionWheelStrategy
    from risk_management.risk_manager import RiskManager
    from database.database import DatabaseManager
    from notifications.notification_manager import NotificationManager
    
    classes_to_check = [
        (OptionWheelConfig, "OptionWheelConfig"),
        (Trade, "Trade"),
        (Position, "Position"), 
        (OptionContract, "OptionContract"),
        (StrategyState, "StrategyState"),
        (RiskMetrics, "RiskMetrics"),
        (OptionWheelStrategy, "OptionWheelStrategy"),
        (RiskManager, "RiskManager"),
        (DatabaseManager, "DatabaseManager"),
        (NotificationManager, "NotificationManager")
    ]
    
    failed_classes = []
    
    for cls, name in classes_to_check:
        try:
            # Try to inspect the class
            sig = inspect.signature(cls.__init__) if hasattr(cls, '__init') else "No signature"
            logger.info(f"✓ Class {name} found with signature: {sig}")
        except Exception as e:
            logger.error(f"✗ Error checking class {name}: {e}")
            failed_classes.append((name, str(e)))
    
    return failed_classes


def check_config_settings():
    """Verify configuration settings are properly loaded"""
    config_issues = []
    
    # Check that required config values exist
    required_configs = [
        'api_key',
        'api_secret', 
        'access_token',
        'symbol',
        'quantity_per_lot',
        'profit_target_percentage',
        'loss_limit_percentage',
        'otm_delta_range_low',
        'otm_delta_range_high',
        'min_open_interest',
        'strategy_run_interval_seconds',
        'market_open_hour',
        'market_open_minute',
        'market_close_hour',
        'market_close_minute',
        'max_concurrent_positions',
        'max_daily_loss_limit',
        'max_portfolio_risk',
        'enable_notifications',
        'dry_run',
        'strategy_mode',
        'risk_per_trade_percent',
        'min_cash_reserve',
        'enable_auto_roll'
    ]
    
    for attr in required_configs:
        try:
            value = getattr(config, attr)
            logger.debug(f"Config {attr}: {value}")
        except AttributeError:
            config_issues.append(f"Missing config attribute: {attr}")
    
    # Check values make sense
    if config.otm_delta_range_low >= config.otm_delta_range_high:
        config_issues.append("Delta range low >= delta range high")
    
    if config.max_daily_loss_limit <= 0:
        config_issues.append("Max daily loss limit should be positive")
    
    if config.quantity_per_lot <= 0:
        config_issues.append("Quantity per lot should be positive")
    
    return config_issues


def check_dependencies():
    """Check if required dependencies can be imported"""
    required_packages = [
        "requests",
        "pandas", 
        "numpy",
        "kiteconnect",
        "python-dotenv",
        "streamlit",
        "plotly",
        "pytz",
        "matplotlib",
        "seaborn",
        "scipy",
        "ta",
        "schedule",
        "apscheduler",
        "scikit-learn",
        "sentence_transformers",
        "chromadb",
        "onnxruntime",
        "ollama"
    ]
    
    failed_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"✓ Dependency {package} is available")
        except ImportError as e:
            logger.error(f"✗ Dependency {package} is missing: {e}")
            failed_packages.append((package, str(e)))
    
    return failed_packages


def check_database_connection():
    """Verify database connectivity"""
    try:
        # Test basic database operations
        counts = db_manager.get_table_counts()
        logger.info(f"✓ Database connection successful. Table counts: {counts}")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def check_risk_management():
    """Verify risk management functionality"""
    try:
        # Update with some test values
        risk_manager.update_portfolio_value(100000.0)
        risk_manager.update_cash_available(50000.0)
        risk_manager.update_margin_info(60000.0, 10000.0)
        
        # Get and verify metrics
        metrics = risk_manager.calculate_portfolio_risk()
        limits_status = risk_manager.check_risk_limits()
        
        logger.info(f"✓ Risk management check passed. Metrics: {list(metrics.keys())}")
        logger.info(f"Risk limits status: {limits_status}")
        return True
    except Exception as e:
        logger.error(f"✗ Risk management check failed: {e}")
        return False


def check_environment_variables():
    """Check if required environment variables are set"""
    # The config module should handle this, but let's verify some key ones
    env_issues = []
    
    # Check if .env file exists
    env_file = Path("Trading/.env")
    if not env_file.exists():
        env_issues.append("Missing .env file")
    
    # Check if API keys are set (but don't log them for security)
    if not config.dry_run:
        if not config.api_key:
            env_issues.append("KITE_API_KEY not set in config")
        if not config.api_secret:
            env_issues.append("KITE_API_SECRET not set in config")
        if not config.access_token:
            env_issues.append("KITE_ACCESS_TOKEN not set in config")
    
    return env_issues


def run_final_verification():
    """Run all final verification checks"""
    logger.info("Starting final verification of Options Wheel Strategy Trading Bot...")
    logger.info(f"Verification timestamp: {datetime.now()}")
    
    verification_results = {
        "file_structure": None,
        "module_imports": None,
        "class_definitions": None,
        "config_settings": None,
        "dependencies": None,
        "database_connection": None,
        "risk_management": None,
        "environment_variables": None,
        "basic_functionality_tests": None
    }
    
    # Run file structure check
    logger.info("\n1. Checking file structure...")
    verification_results["file_structure"] = check_file_structure()
    if verification_results["file_structure"]:
        logger.error(f"Missing paths: {verification_results['file_structure']}")
    else:
        logger.info("✓ All required files and directories exist")
    
    # Run module import check
    logger.info("\n2. Checking module imports...")
    verification_results["module_imports"] = check_module_imports()
    if not verification_results["module_imports"]:
        logger.info("✓ All modules imported successfully")
    else:
        logger.error(f"Failed imports: {verification_results['module_imports']}")
    
    # Run class definition check
    logger.info("\n3. Checking class definitions...")
    verification_results["class_definitions"] = check_class_definitions()
    if not verification_results["class_definitions"]:
        logger.info("✓ All classes are properly defined")
    else:
        logger.error(f"Class definition issues: {verification_results['class_definitions']}")
    
    # Run config check
    logger.info("\n4. Checking configuration settings...")
    verification_results["config_settings"] = check_config_settings()
    if not verification_results["config_settings"]:
        logger.info("✓ Configuration settings are valid")
    else:
        logger.error(f"Configuration issues: {verification_results['config_settings']}")
    
    # Run dependency check
    logger.info("\n5. Checking dependencies...")
    verification_results["dependencies"] = check_dependencies()
    if not verification_results["dependencies"]:
        logger.info("✓ All dependencies are available")
    else:
        logger.error(f"Missing dependencies: {verification_results['dependencies']}")
    
    # Run database connection check
    logger.info("\n6. Checking database connection...")
    verification_results["database_connection"] = check_database_connection()
    
    # Run risk management check
    logger.info("\n7. Checking risk management...")
    verification_results["risk_management"] = check_risk_management()
    
    # Run environment variable check
    logger.info("\n8. Checking environment variables...")
    verification_results["environment_variables"] = check_environment_variables()
    if not verification_results["environment_variables"]:
        logger.info("✓ Environment variables are set correctly")
    else:
        logger.warning(f"Environment variable issues: {verification_results['environment_variables']}")
    
    # Run basic functionality tests
    logger.info("\n9. Running basic functionality tests...")
    from basic_functionality_test import run_basic_tests
    test_result = run_basic_tests()
    verification_results["basic_functionality_tests"] = {
        'tests_run': test_result.testsRun,
        'failures': len(test_result.failures),
        'errors': len(test_result.errors),
        'success_rate': (test_result.testsRun - len(test_result.failures) - len(test_result.errors)) / test_result.testsRun if test_result.testsRun > 0 else 0
    }
    
    # Generate summary report
    logger.info("\n" + "="*70)
    logger.info("FINAL VERIFICATION SUMMARY")
    logger.info("="*70)
    
    all_passed = True
    
    # File structure
    if verification_results["file_structure"]:
        logger.error(f"✗ File structure issues: {len(verification_results['file_structure'])} missing paths")
        all_passed = False
    else:
        logger.info("✓ File structure: All required files present")
    
    # Module imports
    if verification_results["module_imports"]:
        logger.error(f"✗ Module import issues: {len(verification_results['module_imports'])} failed imports")
        all_passed = False
    else:
        logger.info("✓ Module imports: All modules imported successfully")
    
    # Class definitions
    if verification_results["class_definitions"]:
        logger.error(f"✗ Class definition issues: {len(verification_results['class_definitions'])} issues")
        all_passed = False
    else:
        logger.info("✓ Class definitions: All classes properly defined")
    
    # Config settings
    if verification_results["config_settings"]:
        logger.error(f"✗ Config issues: {len(verification_results['config_settings'])} configuration problems")
        all_passed = False
    else:
        logger.info("✓ Config settings: All configurations valid")
    
    # Dependencies
    if verification_results["dependencies"]:
        logger.error(f"✗ Dependency issues: {len(verification_results['dependencies'])} missing packages")
        all_passed = False
    else:
        logger.info("✓ Dependencies: All required packages available")
    
    # Database connection
    if not verification_results["database_connection"]:
        logger.error("✗ Database connection: Failed")
        all_passed = False
    else:
        logger.info("✓ Database: Connection successful")
    
    # Risk management
    if not verification_results["risk_management"]:
        logger.error("✗ Risk management: Failed")
        all_passed = False
    else:
        logger.info("✓ Risk management: Functioning correctly")
    
    # Environment variables
    if verification_results["environment_variables"]:
        logger.warning(f"⚠️ Environment variables: {len(verification_results['environment_variables'])} issues")
    else:
        logger.info("✓ Environment variables: Properly set")
    
    # Basic functionality tests
    test_results = verification_results["basic_functionality_tests"]
    if test_results['failures'] == 0 and test_results['errors'] == 0:
        logger.info(f"✓ Basic functionality tests: All passed ({test_results['tests_run']} tests)")
    else:
        logger.error(f"✗ Basic functionality tests: {test_results['failures']} failures, {test_results['errors']} errors")
        all_passed = False
    
    logger.info("\n" + "="*70)
    logger.info(f"FINAL RESULT: {'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
    logger.info(f"Success Rate: {test_results['success_rate']*100:.2f}%")
    logger.info("="*70)
    
    # Save verification results to file
    try:
        import json
        os.makedirs("verification_results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"verification_results/final_verification_{timestamp}.json"
        
        # Convert any non-serializable objects to strings for JSON
        serializable_results = {}
        for key, value in verification_results.items():
            if value is None:
                serializable_results[key] = None
            elif isinstance(value, (list, dict)):
                serializable_results[key] = str(value)
            else:
                serializable_results[key] = str(value)
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"Verification results saved to {results_file}")
    except Exception as e:
        logger.error(f"Failed to save verification results: {e}")
    
    return all_passed


if __name__ == "__main__":
    success = run_final_verification()
    if success:
        logger.info("\n🎉 Final verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n💥 Final verification failed!")
        sys.exit(1)
