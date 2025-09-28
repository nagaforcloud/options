"""
Enhanced logging utilities for Options Wheel Strategy Trading Bot
Provides comprehensive logging with both file and console handlers
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "OptionsWheelBot",
    log_file: str = "logs/options_wheel_bot.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Name of the logger
        log_file: Path to the log file
        level: Logging level (default: INFO)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter with comprehensive details
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)-8s] [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Set propagate to False to avoid duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str = "OptionsWheelBot") -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Name of the logger
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, msg: str = "An exception occurred"):
    """
    Log the current exception with traceback
    
    Args:
        logger: Logger instance
        msg: Message to include with the exception
    """
    logger.exception(msg)


def log_trade_entry(logger: logging.Logger, trade_details: dict):
    """
    Log trade entry details in a structured format
    
    Args:
        logger: Logger instance
        trade_details: Dictionary containing trade details
    """
    logger.info(
        f"Trade Entry - Symbol: {trade_details.get('symbol', 'N/A')}, "
        f"Type: {trade_details.get('transaction_type', 'N/A')}, "
        f"Quantity: {trade_details.get('quantity', 'N/A')}, "
        f"Price: {trade_details.get('price', 'N/A')}, "
        f"Order ID: {trade_details.get('order_id', 'N/A')}"
    )


def log_position_update(logger: logging.Logger, position_details: dict):
    """
    Log position update details in a structured format
    
    Args:
        logger: Logger instance
        position_details: Dictionary containing position details
    """
    logger.info(
        f"Position Update - Symbol: {position_details.get('symbol', 'N/A')}, "
        f"Quantity: {position_details.get('quantity', 'N/A')}, "
        f"Average Price: {position_details.get('average_price', 'N/A')}, "
        f"P&L: {position_details.get('pnl', 'N/A')}"
    )


def log_risk_alert(logger: logging.Logger, alert_details: dict):
    """
    Log risk alert details in a structured format
    
    Args:
        logger: Logger instance
        alert_details: Dictionary containing risk alert details
    """
    logger.warning(
        f"Risk Alert - Type: {alert_details.get('alert_type', 'N/A')}, "
        f"Message: {alert_details.get('message', 'N/A')}, "
        f"Value: {alert_details.get('value', 'N/A')}, "
        f"Threshold: {alert_details.get('threshold', 'N/A')}"
    )


def log_performance_metrics(logger: logging.Logger, metrics: dict):
    """
    Log performance metrics in a structured format
    
    Args:
        logger: Logger instance
        metrics: Dictionary containing performance metrics
    """
    logger.info(
        f"Performance Metrics - Daily P&L: {metrics.get('daily_pnl', 'N/A')}, "
        f"Total P&L: {metrics.get('total_pnl', 'N/A')}, "
        f"Win Rate: {metrics.get('win_rate', 'N/A')}, "
        f"Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}, "
        f"Max Drawdown: {metrics.get('max_drawdown', 'N/A')}"
    )


# Global logger instance
logger = setup_logger()


if __name__ == "__main__":
    # Example usage
    logger = setup_logger()
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Example of structured logging
    trade_details = {
        "symbol": "TCS",
        "transaction_type": "SELL",
        "quantity": 150,
        "price": 3450.5,
        "order_id": "1234567890"
    }
    
    log_trade_entry(logger, trade_details)