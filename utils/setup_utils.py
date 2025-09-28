"""
Setup utilities for the Options Wheel Strategy Trading Bot
Provides common imports and utilities to avoid code redundancy
"""
import os
import sys
from pathlib import Path


def setup_trading_path():
    """Setup the Python path to properly import Trading modules"""
    trading_dir = Path(__file__).parent
    if str(trading_dir) not in sys.path:
        sys.path.insert(0, str(trading_dir))


def get_module_logger(module_name: str):
    """Get a properly configured logger for a specific module"""
    import logging
    from utils.logging_utils import logger
    return logging.getLogger(f"Trading.{module_name}")


def with_retry(max_retries=3, backoff_factor=1):
    """Decorator for retrying API calls with exponential backoff"""
    import time
    import functools
    from utils.logging_utils import logger
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


def circuit_breaker(failure_threshold=5, timeout=60):
    """Circuit breaker decorator to prevent cascading failures"""
    import time
    import functools
    from utils.logging_utils import logger
    
    def decorator(func):
        calls = []
        failures = []
        state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        last_failure_time = None
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal state, last_failure_time
            
            if state == "OPEN":
                if last_failure_time and (time.time() - last_failure_time) > timeout:
                    state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                # Success - reset
                if state == "HALF_OPEN":
                    state = "CLOSED"
                return result
            except Exception as e:
                # Failure - record it
                failures.append(time.time())
                calls.append(time.time())
                
                # Trim old records
                cutoff = time.time() - 300  # 5 minutes window
                failures = [t for t in failures if t > cutoff]
                calls = [t for t in calls if t > cutoff]
                
                if len(failures) >= failure_threshold:
                    state = "OPEN"
                    last_failure_time = time.time()
                    logger.error(f"Circuit breaker OPENED due to {len(failures)} failures in 5 minutes")
                
                raise e
                
        return wrapper
    return decorator