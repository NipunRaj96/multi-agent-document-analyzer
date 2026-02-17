"""
Performance monitoring utilities for tracking latency and system metrics.
"""

import time
from functools import wraps
from typing import Callable, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """Track performance metrics for system components."""
    
    @staticmethod
    def track_latency(operation_name: str):
        """
        Decorator to track operation latency.
        
        Args:
            operation_name: Name of the operation being tracked
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    logger.info(f"[PERFORMANCE] {operation_name} completed in {elapsed:.3f}s")
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(f"[PERFORMANCE] {operation_name} failed after {elapsed:.3f}s: {str(e)}")
                    raise
            return wrapper
        return decorator


def log_event(event_type: str, details: dict):
    """
    Log a system event with structured details.
    
    Args:
        event_type: Type of event (e.g., 'TOOL_CALL', 'AGENT_DECISION')
        details: Dictionary of event details
    """
    logger.info(f"[EVENT:{event_type}] {details}")
