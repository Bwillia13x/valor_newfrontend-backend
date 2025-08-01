import logging
import time
import uuid
from typing import Any, Dict

from flask import g, request, has_request_context
import structlog

from .settings import settings


def _add_request_context(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    # Safely add request-scoped context
    event_dict["request_id"] = getattr(g, "request_id", None)
    event_dict["tenant_id"] = getattr(g, "tenant_id", None)
    if has_request_context():
        event_dict["method"] = request.method
        event_dict["path"] = request.path
        event_dict["remote_addr"] = request.headers.get("X-Forwarded-For", request.remote_addr)
        event_dict["user_agent"] = request.headers.get("User-Agent")
    return event_dict


def configure_logging(level: int = logging.INFO) -> None:
    # Choose renderer based on settings.LOG_JSON
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        _add_request_context,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.LOG_JSON:
        processors.append(structlog.processors.JSONRenderer())
        fmt = "%(message)s"
    else:
        processors.append(structlog.dev.ConsoleRenderer())
        fmt = "%(levelname)s %(message)s"

    logging.basicConfig(
        format=fmt,
        stream=None,
        level=getattr(logging, settings.LOG_LEVEL.upper(), level),
    )

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), level)
        ),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger()


def request_start() -> None:
    g.start_time = time.time()
    g.request_id = getattr(g, "request_id", str(uuid.uuid4()))


def log_request(response):
    duration = time.time() - getattr(g, "start_time", time.time())
    logger.info(
        "request_processed",
        status_code=getattr(response, "status_code", None),
        duration_ms=int(duration * 1000),
    )
    return response
