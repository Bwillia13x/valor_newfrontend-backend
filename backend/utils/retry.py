"""
Retry mechanism with exponential backoff for external API calls.

This module provides decorators for both sync and async functions
with configurable retry logic, exponential backoff, and jitter.
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional, List
from functools import wraps

class RetryConfig:
    """Configuration for retry mechanism"""
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True, retry_exceptions: Optional[List[type]] = None):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or [Exception]

def retry_async(config: RetryConfig):
    """Decorator for async retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except tuple(config.retry_exceptions) as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        raise last_exception
                    
                    # Calculate delay with exponential backoff
                    delay = config.base_delay * (config.exponential_base ** attempt)
                    delay = min(delay, config.max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

def retry_sync(config: RetryConfig):
    """Decorator for sync retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(config.retry_exceptions) as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        raise last_exception
                    
                    # Calculate delay with exponential backoff
                    delay = config.base_delay * (config.exponential_base ** attempt)
                    delay = min(delay, config.max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

# Pre-configured retry configs for common use cases
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
    retry_exceptions=[Exception]
)

API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retry_exceptions=[Exception, TimeoutError, ConnectionError]
)

def retry_async_default(func: Callable) -> Callable:
    """Default async retry decorator"""
    return retry_async(DEFAULT_RETRY_CONFIG)(func)

def retry_sync_default(func: Callable) -> Callable:
    """Default sync retry decorator"""
    return retry_sync(DEFAULT_RETRY_CONFIG)(func)

def retry_async_api(func: Callable) -> Callable:
    """API-specific async retry decorator"""
    return retry_async(API_RETRY_CONFIG)(func)

def retry_sync_api(func: Callable) -> Callable:
    """API-specific sync retry decorator"""
    return retry_sync(API_RETRY_CONFIG)(func) 