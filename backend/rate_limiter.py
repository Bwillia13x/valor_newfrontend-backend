"""
Rate Limiting Module for Valor IVX
Implements API rate limiting to prevent abuse and ensure fair usage
"""

import time
import threading
import os
from collections import defaultdict, deque
from typing import Dict, Deque, Optional
from functools import wraps
from flask import request, jsonify, current_app, g
import logging
from .metrics import rate_limit_allowed, rate_limit_blocked

logger = logging.getLogger(__name__)

# Try to import Redis for production use
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class RateLimiter:
    """Rate limiter implementation using sliding window with Redis fallback"""
    
    def __init__(self):
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()
        
        # Initialize Redis if available
        self.redis_client = None
        if REDIS_AVAILABLE and os.environ.get("REDIS_URL"):
            try:
                self.redis_client = redis.from_url(os.environ.get("REDIS_URL"))
                self.redis_client.ping()  # Test connection
                logger.info("Rate limiter using Redis")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to memory: {e}")
                self.redis_client = None
        
        # Default rate limits (requests per window)
        self.default_limits = {
            'api': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 5, 'window': 60},   # 5 auth attempts per minute
            'financial_data': {'requests': 30, 'window': 60},  # 30 financial data requests per minute
            'heavy_operations': {'requests': 10, 'window': 60}  # 10 heavy operations per minute
        }
    
    def is_allowed(self, key: str, limit_type: str = 'api') -> bool:
        """Check if request is allowed based on rate limits"""
        if self.redis_client:
            return self._is_allowed_redis(key, limit_type)
        else:
            return self._is_allowed_memory(key, limit_type)
    
    def _is_allowed_redis(self, key: str, limit_type: str = 'api') -> bool:
        """Redis-based rate limiting"""
        try:
            current_time = time.time()
            limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            
            # Use Redis sorted set for sliding window
            window_start = current_time - limit_config['window']
            redis_key = f"rate_limit:{limit_type}:{key}"
            
            # Remove old entries
            self.redis_client.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests
            current_requests = self.redis_client.zcard(redis_key)
            
            if current_requests < limit_config['requests']:
                # Add current request
                self.redis_client.zadd(redis_key, {str(current_time): current_time})
                self.redis_client.expire(redis_key, limit_config['window'])
                
                # Record metrics
                tenant_id = getattr(g, 'tenant_id', 'unknown')
                rate_limit_allowed(tenant_id, limit_type)
                return True
            
            # Record metrics
            tenant_id = getattr(g, 'tenant_id', 'unknown')
            rate_limit_blocked(tenant_id, limit_type)
            return False
            
        except Exception as e:
            logger.error(f"Redis rate limiting failed: {e}")
            # Fallback to memory-based limiting
            return self._is_allowed_memory(key, limit_type)
    
    def _is_allowed_memory(self, key: str, limit_type: str = 'api') -> bool:
        """Memory-based rate limiting (fallback)"""
        with self.lock:
            current_time = time.time()
            limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            
            # Get request history for this key
            requests = self.requests[key]
            
            # Remove old requests outside the window
            window_start = current_time - limit_config['window']
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check if we're under the limit
            if len(requests) < limit_config['requests']:
                requests.append(current_time)
                # Record metrics
                tenant_id = getattr(g, 'tenant_id', 'unknown')
                rate_limit_allowed(tenant_id, limit_type)
                return True
            
            # Record metrics
            tenant_id = getattr(g, 'tenant_id', 'unknown')
            rate_limit_blocked(tenant_id, limit_type)
            return False
    
    def get_remaining_requests(self, key: str, limit_type: str = 'api') -> Dict[str, int]:
        """Get remaining requests and reset time for a key"""
        if self.redis_client:
            return self._get_remaining_requests_redis(key, limit_type)
        else:
            return self._get_remaining_requests_memory(key, limit_type)
    
    def _get_remaining_requests_redis(self, key: str, limit_type: str = 'api') -> Dict[str, int]:
        """Redis-based remaining requests"""
        try:
            limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            redis_key = f"rate_limit:{limit_type}:{key}"
            
            # Get current time
            current_time = time.time()
            
            # Get requests within the current window
            requests_in_window = self.redis_client.zrangebyscore(redis_key, current_time - limit_config['window'], current_time)
            
            remaining = max(0, limit_config['requests'] - len(requests_in_window))
            
            # Calculate reset time
            reset_time = 0
            if requests_in_window:
                reset_time = int(requests_in_window[0]) + limit_config['window']
            
            return {
                'remaining': remaining,
                'limit': limit_config['requests'],
                'reset_time': reset_time,
                'window': limit_config['window']
            }
    
    def _get_remaining_requests_memory(self, key: str, limit_type: str = 'api') -> Dict[str, int]:
        """Memory-based remaining requests"""
        with self.lock:
            current_time = time.time()
            limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            
            requests = self.requests[key]
            
            # Remove old requests
            window_start = current_time - limit_config['window']
            while requests and requests[0] < window_start:
                requests.popleft()
            
            remaining = max(0, limit_config['requests'] - len(requests))
            
            # Calculate reset time
            reset_time = 0
            if requests:
                reset_time = int(requests[0] + limit_config['window'])
            
            return {
                'remaining': remaining,
                'limit': limit_config['requests'],
                'reset_time': reset_time,
                'window': limit_config['window']
            }
    
    def get_client_key(self) -> str:
        """Get client identifier for rate limiting"""
        # Use IP address as primary identifier
        client_ip = request.remote_addr
        
        # If behind proxy, try to get real IP
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            client_ip = request.headers.get('X-Real-IP')
        
        # Add user agent for additional uniqueness
        user_agent = request.headers.get('User-Agent', 'unknown')
        
        return f"{client_ip}:{hash(user_agent) % 10000}"

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit_type: str = 'api'):
    """Decorator to apply rate limiting to routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_key = rate_limiter.get_client_key()
            
            if not rate_limiter.is_allowed(client_key, limit_type):
                # Get rate limit info for response headers
                limit_info = rate_limiter.get_remaining_requests(client_key, limit_type)
                
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limit_info["limit"]} requests per {limit_info["window"]} seconds',
                    'retry_after': limit_info['reset_time'] - int(time.time())
                })
                
                # Add rate limit headers
                response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(limit_info['reset_time'])
                response.headers['Retry-After'] = str(max(1, limit_info['reset_time'] - int(time.time())))
                
                logger.warning(f"Rate limit exceeded for {client_key} on {limit_type}")
                return response, 429
            
            # Add rate limit headers to successful responses
            limit_info = rate_limiter.get_remaining_requests(client_key, limit_type)
            response = f(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(limit_info['reset_time'])
            
            return response
        
        return decorated_function
    return decorator

def auth_rate_limit(f):
    """Decorator for authentication endpoints with stricter limits"""
    return rate_limit('auth')(f)

def financial_data_rate_limit(f):
    """Decorator for financial data endpoints"""
    return rate_limit('financial_data')(f)

def heavy_operation_rate_limit(f):
    """Decorator for computationally expensive operations"""
    return rate_limit('heavy_operations')(f)

class RateLimitConfig:
    """Configuration for rate limiting"""
    
    @staticmethod
    def get_limits() -> Dict[str, Dict[str, int]]:
        """Get current rate limit configuration"""
        return rate_limiter.default_limits.copy()
    
    @staticmethod
    def update_limits(new_limits: Dict[str, Dict[str, int]]):
        """Update rate limit configuration"""
        rate_limiter.default_limits.update(new_limits)
        logger.info(f"Updated rate limits: {new_limits}")
    
    @staticmethod
    def get_client_stats(client_key: str) -> Dict[str, Dict[str, int]]:
        """Get rate limit statistics for a client"""
        stats = {}
        for limit_type in rate_limiter.default_limits.keys():
            stats[limit_type] = rate_limiter.get_remaining_requests(client_key, limit_type)
        return stats 