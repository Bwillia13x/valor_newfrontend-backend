import json
import hashlib
import time
import logging
from functools import wraps
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime, timedelta

import redis
from redis.exceptions import RedisError

from .settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Redis client from settings
try:
    redis_client = redis.from_url(settings.REDIS_URL)
    # Test connection
    redis_client.ping()
    redis_available = True
    logger.info("Redis cache connection established")
except (RedisError, AttributeError) as e:
    logger.warning(f"Redis cache unavailable: {str(e)}")
    redis_available = False
    redis_client = None


class CacheManager:
    """Advanced cache management with multiple strategies and performance optimizations"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.redis_available = redis_available
        self.local_cache = {}  # In-memory cache for frequently accessed data
        self.local_cache_ttl = {}  # TTL for local cache entries
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "local_hits": 0,
            "local_misses": 0,
            "errors": 0
        }
    
    def _generate_cache_key(self, prefix: str, args: tuple, kwargs: dict) -> str:
        """Generate a stable cache key from function arguments"""
        # Create a stable representation of arguments
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        
        # Create hash for long arguments to keep keys manageable
        if len(args_str) + len(kwargs_str) > 100:
            content = f"{args_str}:{kwargs_str}"
            hash_obj = hashlib.md5(content.encode())
            return f"cache:{prefix}:{hash_obj.hexdigest()}"
        else:
            return f"cache:{prefix}:{args_str}:{kwargs_str}"
    
    def _get_local_cache(self, key: str) -> Optional[Any]:
        """Get value from local in-memory cache"""
        if key in self.local_cache:
            # Check if local cache entry is still valid
            if time.time() < self.local_cache_ttl.get(key, 0):
                self.cache_stats["local_hits"] += 1
                return self.local_cache[key]
            else:
                # Remove expired entry
                del self.local_cache[key]
                del self.local_cache_ttl[key]
        
        self.cache_stats["local_misses"] += 1
        return None
    
    def _set_local_cache(self, key: str, value: Any, ttl: int):
        """Set value in local in-memory cache"""
        try:
            self.local_cache[key] = value
            self.local_cache_ttl[key] = time.time() + ttl
            
            # Limit local cache size to prevent memory issues
            if len(self.local_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(self.local_cache_ttl.items(), key=lambda x: x[1])[:100]
                for old_key, _ in oldest_keys:
                    del self.local_cache[old_key]
                    del self.local_cache_ttl[old_key]
        except Exception as e:
            logger.warning(f"Failed to set local cache: {str(e)}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis + local)"""
        # Try local cache first
        local_value = self._get_local_cache(key)
        if local_value is not None:
            return local_value
        
        # Try Redis cache
        if not self.redis_available:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached is not None:
                try:
                    result = json.loads(cached)
                    # Also store in local cache for faster subsequent access
                    self._set_local_cache(key, result, 300)  # 5 minutes local TTL
                    self.cache_stats["hits"] += 1
                    return result
                except json.JSONDecodeError:
                    # Delete corrupted cache entry
                    self.redis_client.delete(key)
                    logger.warning(f"Corrupted cache entry deleted: {key}")
            
            self.cache_stats["misses"] += 1
            return None
            
        except RedisError as e:
            self.cache_stats["errors"] += 1
            logger.error(f"Redis cache error: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache (Redis + local)"""
        # Store in local cache
        self._set_local_cache(key, value, min(ttl, 300))  # Max 5 minutes local TTL
        
        # Store in Redis
        if not self.redis_available:
            return
        
        try:
            payload = json.dumps(value)
            self.redis_client.setex(key, ttl, payload)
        except (TypeError, RedisError) as e:
            self.cache_stats["errors"] += 1
            logger.warning(f"Failed to cache in Redis: {str(e)}")
    
    def delete(self, key: str):
        """Delete value from cache (Redis + local)"""
        # Remove from local cache
        if key in self.local_cache:
            del self.local_cache[key]
            del self.local_cache_ttl[key]
        
        # Remove from Redis
        if self.redis_available:
            try:
                self.redis_client.delete(key)
            except RedisError as e:
                logger.error(f"Failed to delete from Redis: {str(e)}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all cache keys matching a pattern"""
        if not self.redis_available:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
        except RedisError as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = self.cache_stats.copy()
        stats["local_cache_size"] = len(self.local_cache)
        stats["local_cache_keys"] = list(self.local_cache.keys())[:10]  # First 10 keys
        
        if self.redis_available:
            try:
                info = self.redis_client.info()
                stats["redis_memory_usage"] = info.get("used_memory_human", "N/A")
                stats["redis_connected_clients"] = info.get("connected_clients", "N/A")
            except RedisError:
                stats["redis_info"] = "Unavailable"
        
        return stats


# Global cache manager instance
cache_manager = CacheManager()


def cache_result(ttl: int = 3600, key_prefix: Optional[str] = None, 
                local_cache: bool = True, invalidate_on: Optional[List[str]] = None) -> Callable:
    """
    Enhanced decorator to cache function results with multiple strategies.

    Args:
        ttl: Time to live in seconds for the cached item.
        key_prefix: Optional static prefix for the cache key.
        local_cache: Whether to use local in-memory cache.
        invalidate_on: List of function names whose cache should be invalidated when this function runs.
    """

    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(prefix, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_manager.set(cache_key, result, ttl)
            
            # Invalidate related caches if specified
            if invalidate_on:
                for func_name in invalidate_on:
                    pattern = f"cache:{func_name}:*"
                    cache_manager.invalidate_pattern(pattern)
            
            return result

        return wrapper

    return decorator


def cache_warm(keys: List[str], ttl: int = 3600):
    """Decorator to warm cache with predefined keys"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            
            # Warm cache with result
            for key in keys:
                cache_manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """Decorator to invalidate cache after function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            
            # Invalidate cache
            cache_manager.invalidate_pattern(pattern)
            
            return result
        return wrapper
    return decorator


# Performance monitoring decorator
def monitor_performance(func_name: Optional[str] = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        name = func_name or func.__name__
        
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log slow functions
                if execution_time > 1.0:
                    logger.warning(f"Slow function execution: {name} took {execution_time:.2f}s")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Function {name} failed after {execution_time:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


# Cache health check
def health_check_cache() -> Dict[str, Any]:
    """Perform cache health check"""
    try:
        if not cache_manager.redis_available:
            return {
                "status": "degraded",
                "message": "Redis cache unavailable, using local cache only",
                "local_cache_size": len(cache_manager.local_cache)
            }
        
        # Test Redis connection
        cache_manager.redis_client.ping()
        
        # Test cache operations
        test_key = "health_check_test"
        test_value = {"test": True, "timestamp": time.time()}
        
        cache_manager.set(test_key, test_value, 60)
        retrieved = cache_manager.get(test_key)
        cache_manager.delete(test_key)
        
        if retrieved == test_value:
            return {
                "status": "healthy",
                "message": "Cache system operational",
                "stats": cache_manager.get_stats()
            }
        else:
            return {
                "status": "degraded",
                "message": "Cache read/write test failed"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Cache health check failed: {str(e)}"
        }
