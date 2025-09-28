"""
Main entry point for Options Wheel Strategy Trading Bot
Handles both live trading and backtesting modes
"""
import sys
import os
from datetime import datetime, timedelta
import pytz
import argparse
from pathlib import Path

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import config
from core.strategy import OptionWheelStrategy
from backtesting.nifty_backtesting import run_nifty_backtest
from backtesting.prepare_nifty_data import main as prepare_data
from utils.logging_utils import logger
from database.database import db_manager
from notifications.notification_manager import send_notification
from dashboard.dashboard import main as run_dashboard


def initialize_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'data',
        'logs', 
        'historical_trades',
        'results'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")


def check_kill_switch():
    """Check for the kill switch file"""
    if os.path.exists(config.kill_switch_file):
        logger.critical(f"Kill switch file {config.kill_switch_file} detected at startup. Exiting.")
        sys.exit(1)


def main():
    """Main function to handle different modes of operation"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Options Wheel Strategy Trading Bot')
    parser.add_argument(
        '--mode', 
        choices=['live', 'backtest', 'dashboard', 'prepare-data'], 
        default='live',
        help='Operation mode: live trading, backtesting, dashboard, or prepare data'
    )
    parser.add_argument(
        '--start-date',
        help='Start date for backtesting (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date', 
        help='End date for backtesting (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    # Initialize directories
    initialize_directories()
    
    # Check for kill switch
    check_kill_switch()
    
    # Log startup
    ist = pytz.timezone('Asia/Kolkata')
    start_time = datetime.now(ist)
    logger.info(f"Options Wheel Strategy Bot started at {start_time}")
    logger.info(f"Mode: {args.mode}")
    
    # Send startup notification
    send_notification(
        f"Options Wheel Strategy Bot started in {args.mode} mode",
        title="Bot Started"
    )
    
    try:
        if args.mode == 'live':
            # Verify live trading requirements
            if not config.dry_run:
                logger.info("⚠️ LIVE TRADING MODE ENABLED")
                confirmation = input("⚠️ LIVE TRADING MODE ENABLED. Type 'CONFIRM' to proceed: ")
                if confirmation != 'CONFIRM':
                    logger.critical("Live trading confirmation failed. Exiting.")
                    sys.exit(1)
            
            # Initialize and run live strategy
            logger.info("Initializing live trading strategy...")
            strategy = OptionWheelStrategy()
            strategy.run()
            
        elif args.mode == 'backtest':
            # Run backtesting
            logger.info("Starting backtesting mode...")
            
            # Use provided dates or default to last 3 months
            start_date = args.start_date or (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Running backtest from {start_date} to {end_date}")
            
            # Run the backtest
            backtester = run_nifty_backtest()
            backtester.simulate_strategy(start_date, end_date)
            backtester.print_summary()
            
        elif args.mode == 'dashboard':
            # Run the Streamlit dashboard
            logger.info("Starting dashboard...")
            run_dashboard()
            
        elif args.mode == 'prepare-data':
            # Prepare data for backtesting
            logger.info("Preparing data for backtesting...")
            prepare_data()
            
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        send_notification(
            f"Fatal error: {e}",
            title="Bot Error"
        )
        sys.exit(1)
    
    # Log shutdown
    end_time = datetime.now(ist)
    duration = end_time - start_time
    logger.info(f"Options Wheel Strategy Bot stopped at {end_time} (Duration: {duration})")
    
    # Send shutdown notification
    send_notification(
        f"Options Wheel Strategy Bot stopped after running for {duration}",
        title="Bot Stopped"
    )


if __name__ == "__main__":
    main()