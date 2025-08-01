from functools import wraps
from flask import g, request, Response
from typing import Callable, Any, Tuple
from .rate_limiter import rate_limiter


def _error(message: str, status: int) -> Tuple[dict, int]:
    return {"error": message}, status


def tenant_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return _error("Tenant ID required", 400)
        g.tenant_id = tenant_id
        
        # Apply rate limiting and add precise headers
        client_key = rate_limiter.get_client_key()
        limit_info = rate_limiter.get_remaining_requests(client_key, 'api')
        
        response = f(*args, **kwargs)
        
        # Add precise rate limit headers
        if hasattr(response, 'headers'):
            response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(limit_info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(limit_info['reset_time'])
        
        return response

    return decorated_function
