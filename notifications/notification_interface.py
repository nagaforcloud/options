"""
Notification interfaces for the Options Wheel Strategy Trading Bot
Provides a modular approach to notification systems
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
from datetime import datetime
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_utils import logger
from config.config import config


class NotificationInterface(ABC):
    """Abstract base class for notification systems"""
    
    @abstractmethod
    def send(self, message: str, **kwargs) -> bool:
        """Send a notification"""
        pass


class WebhookNotification(NotificationInterface):
    """Webhook notification implementation"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or config.notification_webhook_url
    
    def send(self, message: str, **kwargs) -> bool:
        """Send webhook notification"""
        if not self.webhook_url:
            logger.warning("Webhook URL not configured, skipping notification")
            return False
        
        try:
            payload = {
                "text": message,
                "timestamp": datetime.now().isoformat(),
                **kwargs  # Include any additional parameters
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                return True
            else:
                logger.error(f"Webhook notification failed with status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook notification request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in webhook notification: {e}")
            return False


class TelegramNotification(NotificationInterface):
    """Telegram notification implementation"""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or config.telegram_bot_token
        self.chat_id = chat_id or config.telegram_chat_id
    
    def send(self, message: str, **kwargs) -> bool:
        """Send Telegram notification"""
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not configured, skipping notification")
            return False
        
        try:
            telegram_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            
            # Limit message length to Telegram's limit (4096 characters)
            if len(message) > 4000:
                message = message[:4000] + "... (truncated)"
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(
                telegram_url,
                data=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description')}")
                    return False
            else:
                logger.error(f"Telegram notification failed with status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram notification request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in telegram notification: {e}")
            return False


class NotificationManager:
    """Manages multiple notification systems"""
    
    def __init__(self):
        """Initialize notification manager with configured systems"""
        self.enabled = config.enable_notifications
        self.notification_type = config.notification_type
        
        # Initialize notification systems
        self.notification_systems: Dict[str, NotificationInterface] = {
            "webhook": WebhookNotification(),
            "telegram": TelegramNotification()
        }
        
        logger.info("Notification Manager initialized with systems: " + 
                   ", ".join(self.notification_systems.keys()))
    
    def send_notification(
        self, 
        message: str, 
        notification_type: Optional[str] = None,
        title: str = "Options Wheel Bot",
        **kwargs
    ) -> bool:
        """
        Send notification through configured system
        
        Args:
            message: Notification message
            notification_type: Type of notification (webhook, telegram, etc.)
            title: Title for the notification
            **kwargs: Additional parameters for specific notification types
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Notifications disabled, skipping notification")
            return True
        
        # Use configured type if none provided
        send_type = notification_type or self.notification_type
        
        # Check if the notification type exists
        if send_type not in self.notification_systems:
            logger.warning(f"Notification type '{send_type}' not supported")
            return False
        
        # Format message with title
        formatted_message = f"{title}: {message}"
        
        # Send through the appropriate system
        notification_system = self.notification_systems[send_type]
        success = notification_system.send(formatted_message, **kwargs)
        
        if success:
            logger.info(f"Notification sent successfully via {send_type}: {message[:100]}...")
        else:
            logger.error(f"Failed to send notification via {send_type}")
        
        return success
    
    def send_order_notification(
        self, 
        order_type: str, 
        symbol: str, 
        quantity: int, 
        price: float,
        status: str,
        order_id: str
    ) -> bool:
        """Send specific notification for order events"""
        message = f"ORDER {status.upper()}: {order_type} {quantity} {symbol} @ ₹{price} (ID: {order_id})"
        return self.send_notification(message, title="Order Notification")
    
    def send_position_notification(
        self, 
        position_type: str, 
        symbol: str, 
        quantity: int, 
        pnl: float,
        avg_price: float
    ) -> bool:
        """Send specific notification for position events"""
        pnl_sign = "+" if pnl >= 0 else ""
        message = f"POSITION {position_type}: {quantity} {symbol} @ ₹{avg_price} (P&L: ₹{pnl_sign}{pnl})"
        return self.send_notification(message, title="Position Notification")
    
    def send_performance_notification(self, metrics: Dict[str, Any]) -> bool:
        """Send performance metrics notification"""
        daily_pnl = metrics.get('daily_pnl', 0)
        total_pnl = metrics.get('total_pnl', 0)
        win_rate = metrics.get('win_rate', 0)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        
        pnl_sign = "+" if daily_pnl >= 0 else ""
        total_pnl_sign = "+" if total_pnl >= 0 else ""
        
        message = (
            f"PERFORMANCE UPDATE:\n"
            f"Daily P&L: ₹{pnl_sign}{daily_pnl:,.2f}\n"
            f"Total P&L: ₹{total_pnl_sign}{total_pnl:,.2f}\n"
            f"Win Rate: {win_rate:.2%}\n"
            f"Sharpe Ratio: {sharpe_ratio:.2f}"
        )
        
        return self.send_notification(message, title="Performance Update")
    
    def send_critical_alert(self, alert_type: str, message: str) -> bool:
        """Send critical alert notification (higher priority)"""
        critical_message = f"🚨 CRITICAL ALERT 🚨\nType: {alert_type}\nMessage: {message}"
        
        # Send to all configured channels for critical alerts
        success = True
        for notification_type in self.notification_systems:
            success = success and self.send_notification(
                critical_message, 
                notification_type=notification_type,
                title="CRITICAL ALERT"
            )
        
        return success


# Global notification manager instance
notification_manager = NotificationManager()


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