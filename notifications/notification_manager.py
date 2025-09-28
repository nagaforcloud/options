"""
Notification Manager for Options Wheel Strategy Trading Bot
Handles sending notifications via multiple channels (using interface pattern)
"""
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import config
from utils.logging_utils import logger
from .notification_interface import NotificationManager as NewNotificationManager


# Use the new interface-based notification manager
notification_manager = NewNotificationManager()


# Wrapper functions for convenience
def send_notification(
    message: str, 
    notification_type: Optional[str] = None,
    title: str = "Options Wheel Bot",
    **kwargs
) -> bool:
    """Send notification using global instance"""
    return notification_manager.send_notification(message, notification_type, title, **kwargs)


def send_order_notification(
    order_type: str, 
    symbol: str, 
    quantity: int, 
    price: float,
    status: str,
    order_id: str
) -> bool:
    """Send order notification using global instance"""
    return notification_manager.send_order_notification(order_type, symbol, quantity, price, status, order_id)


def send_position_notification(
    position_type: str, 
    symbol: str, 
    quantity: int, 
    pnl: float,
    avg_price: float
) -> bool:
    """Send position notification using global instance"""
    return notification_manager.send_position_notification(position_type, symbol, quantity, pnl, avg_price)


def send_performance_notification(metrics: Dict[str, Any]) -> bool:
    """Send performance notification using global instance"""
    return notification_manager.send_performance_notification(metrics)


def send_critical_alert(alert_type: str, message: str) -> bool:
    """Send critical alert using global instance"""
    return notification_manager.send_critical_alert(alert_type, message)


def send_health_check(status: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """Send health check using global instance"""
    health_emoji = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌"}
    emoji = health_emoji.get(status, "❓")
    
    message = f"{emoji} HEALTH CHECK: {status}"
    if details:
        for key, value in details.items():
            message += f"\n{key}: {value}"
    
    return notification_manager.send_notification(message, title="Health Check", **(details or {}))