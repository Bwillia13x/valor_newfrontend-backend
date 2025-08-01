from functools import wraps
from flask import g, request
from typing import Callable, Any, Tuple


def _error(message: str, status: int) -> Tuple[dict, int]:
    return {"error": message}, status


def tenant_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return _error("Tenant ID required", 400)
        g.tenant_id = tenant_id
        return f(*args, **kwargs)

    return decorated_function
