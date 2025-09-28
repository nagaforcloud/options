"""
Health Check Utilities for Options Wheel Strategy Trading Bot
Provides system health monitoring and verification functionality
"""
import os
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List
import requests
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent))
from config.config import config
from database.database import db_manager
from risk_management.risk_manager import risk_manager
from notifications.notification_manager import send_health_check
from ai.base import ai_base, is_enabled


def health_check_api_connection() -> bool:
    """Check if we can connect to necessary APIs"""
    try:
        # For now, just check a basic web connection
        # In the full implementation, this would check KiteConnect, NSE APIs, etc.
        response = requests.get("https://httpbin.org/get", timeout=5)
        return response.status_code == 200
    except:
        return False


def health_check_database() -> bool:
    """Check if database connection is working"""
    try:
        # Attempt to query the database
        counts = db_manager.get_table_counts()
        return True  # If no exception, connection is working
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def health_check_disk_space() -> bool:
    """Check if there's sufficient disk space"""
    try:
        # Check if we have at least 100MB free space
        free_space_gb = psutil.disk_usage('/').free / (1024**3)
        return free_space_gb > 0.1  # At least 0.1 GB free
    except:
        return False


def health_check_memory() -> bool:
    """Check if system has sufficient memory"""
    try:
        memory_percent = psutil.virtual_memory().percent
        return memory_percent < 90  # Less than 90% memory usage
    except:
        return False


def health_check_kill_switch() -> bool:
    """Check if kill switch is activated"""
    return not os.path.exists(config.kill_switch_file)


def health_check_trading_time() -> bool:
    """Check if it's an appropriate time for trading"""
    # In a full implementation, this would check if market is open
    # For now, just return True
    return True


def run_comprehensive_health_check() -> Dict[str, Any]:
    """Run all health checks and return comprehensive status"""
    health_results = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",  # Will be updated based on checks
        "details": {
            "api_connection": health_check_api_connection(),
            "database_connection": health_check_database(),
            "disk_space": health_check_disk_space(),
            "memory_usage": health_check_memory(),
            "kill_switch_active": health_check_kill_switch(),
            "trading_time": health_check_trading_time()
        }
    }
    
    # Determine overall health status
    all_checks = list(health_results["details"].values())
    if all(all_checks):
        health_results["status"] = "healthy"
    elif not health_results["details"]["kill_switch_active"]:
        health_results["status"] = "critical"  # Kill switch is active
    else:
        health_results["status"] = "warning"
    
    # Log the health check results
    logger.info(f"Health check completed - Status: {health_results['status']}")
    
    return health_results


def log_health_metrics():
    """Log detailed system health metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process count
        process_count = len(list(psutil.process_iter()))
        
        logger.info(
            f"System Metrics - CPU: {cpu_percent}%, "
            f"Memory: {memory.percent}%, "
            f"Disk: {disk.percent}% used, "
            f"Processes: {process_count}"
        )
        
    except Exception as e:
        logger.error(f"Error logging health metrics: {e}")


def check_system_resources() -> Dict[str, Any]:
    """Check system resources and performance metrics"""
    try:
        return {
            "timestamp": datetime.now(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(list(psutil.process_iter())),
            "uptime_seconds": time.time() - psutil.boot_time()
        }
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
        return {}


def check_trading_limits() -> Dict[str, Any]:
    """Check if trading limits are within acceptable ranges"""
    try:
        # Get current positions count
        positions = db_manager.get_all_positions()
        current_positions_count = len(positions)
        
        # Check against configured limits
        limits_check = {
            "positions_limit": {
                "current": current_positions_count,
                "max": config.max_concurrent_positions,
                "ok": current_positions_count < config.max_concurrent_positions
            }
        }
        
        # Add other limit checks as needed
        # For example, daily loss limit, portfolio risk, etc.
        
        return limits_check
    except Exception as e:
        logger.error(f"Error checking trading limits: {e}")
        return {}


def monitor_trading_performance() -> Dict[str, Any]:
    """Monitor and return trading performance metrics"""
    try:
        # Get recent trades to calculate performance metrics
        trades = db_manager.get_all_trades()
        
        # Calculate basic metrics
        total_trades = len(trades)
        
        if total_trades > 0:
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            total_pnl = sum(t.pnl for t in trades)
            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            performance = {
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_win": avg_win,
                "avg_loss": avg_loss
            }
        else:
            performance = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_win": 0,
                "avg_loss": 0
            }
        
        return performance
    except Exception as e:
        logger.error(f"Error monitoring trading performance: {e}")
        return {}


def perform_health_check_cycle():
    """Perform a comprehensive health check cycle"""
    logger.info("Starting health check cycle")
    
    # Run comprehensive health check
    health_status = run_comprehensive_health_check()
    
    # Log system metrics
    log_health_metrics()
    
    # Check system resources
    resources = check_system_resources()
    
    # Check trading limits
    limits = check_trading_limits()
    
    # Monitor trading performance
    performance = monitor_trading_performance()
    
    # Compile results
    results = {
        "health_status": health_status,
        "system_resources": resources,
        "trading_limits": limits,
        "performance": performance
    }
    
    # Log summary
    overall_status = health_status["status"]
    logger.info(f"Health check cycle completed - Overall status: {overall_status}")
    
    return results


if __name__ == "__main__":
    # Run a sample health check
    health_results = run_comprehensive_health_check()
    print(f"Health check status: {health_results['status']}")
    print("Details:", health_results['details'])