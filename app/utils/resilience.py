"""Resilience utilities for fault tolerance: Circuit Breaker and Retry patterns."""

import time
import logging
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Simple circuit breaker implementation."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, name="circuit"):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit '{self.name}' entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit '{self.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit '{self.name}' closed - service recovered")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit '{self.name}' opened after {self.failure_count} failures")
            
            raise


def circuit_breaker(failure_threshold=5, recovery_timeout=60, name=None):
    """Decorator for circuit breaker pattern."""
    def decorator(func):
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(failure_threshold, recovery_timeout, breaker_name)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


def retry(max_attempts=3, delay=1, backoff=2):
    """
    Decorator for retry pattern with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Multiplier for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
        return wrapper
    return decorator
