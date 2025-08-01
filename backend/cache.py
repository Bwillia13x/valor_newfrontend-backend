import json
from functools import wraps
from typing import Any, Callable, Optional

import redis

from .settings import settings

# Initialize Redis client from settings
redis_client = redis.from_url(settings.REDIS_URL)


def cache_result(ttl: int = 3600, key_prefix: Optional[str] = None) -> Callable:
    """
    Decorator to cache function results in Redis using JSON serialization.

    Args:
        ttl: Time to live in seconds for the cached item.
        key_prefix: Optional static prefix for the cache key.

    Notes:
        - Cache key is composed of key_prefix (or function name) and a hash of args/kwargs.
        - Function result must be JSON-serializable.
    """

    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a stable key by using repr of args/kwargs
            raw_key = f"{prefix}:{repr(args)}:{repr(sorted(kwargs.items()))}"
            cache_key = f"cache:{raw_key}"

            cached = redis_client.get(cache_key)
            if cached is not None:
                try:
                    return json.loads(cached)
                except Exception:
                    # Fallback: delete bad cache and recompute
                    redis_client.delete(cache_key)

            result = func(*args, **kwargs)

            try:
                payload = json.dumps(result)
                redis_client.setex(cache_key, ttl, payload)
            except Exception:
                # If result is not JSON serializable, skip caching
                pass

            return result

        return wrapper

    return decorator
