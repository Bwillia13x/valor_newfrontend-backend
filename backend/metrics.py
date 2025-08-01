from __future__ import annotations

import os
import time
from typing import Optional

from flask import g, Response, current_app, has_request_context, request
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    generate_latest,
    multiprocess,
)
try:
    from .settings import settings
except ImportError:
    from settings import settings

# Registry (support multiprocess if PROMETHEUS_MULTIPROC_DIR is set)
_registry: Optional[CollectorRegistry] = None

# Metrics (initialized lazily against the active registry)
HTTP_REQUESTS_TOTAL: Optional[Counter] = None
HTTP_REQUEST_DURATION_SECONDS: Optional[Histogram] = None
CELERY_TASKS_TOTAL: Optional[Counter] = None
CELERY_TASK_DURATION_SECONDS: Optional[Histogram] = None
ACTIVE_USERS: Optional[Gauge] = None
CACHE_HIT_RATIO: Optional[Gauge] = None
MODEL_INFERENCE_DURATION_SECONDS: Optional[Histogram] = None
MODEL_PREDICTIONS_TOTAL: Optional[Counter] = None
MODEL_ERRORS_TOTAL: Optional[Counter] = None
CIRCUIT_BREAKER_METRICS: Optional[Counter] = None
DATA_PROVIDER_REQUESTS_TOTAL: Optional[Counter] = None
DATA_PROVIDER_DURATION_SECONDS: Optional[Histogram] = None
RATE_LIMIT_ALLOWED_TOTAL: Optional[Counter] = None
RATE_LIMIT_BLOCKED_TOTAL: Optional[Counter] = None
QUOTA_INCREMENT_SUCCESS_TOTAL: Optional[Counter] = None
QUOTA_INCREMENT_FAILURE_TOTAL: Optional[Counter] = None

# Optional extended labels for model/variant metrics to avoid cardinality blowup
FEATURE_MODEL_VARIANT_METRICS: bool = getattr(settings, "FEATURE_MODEL_VARIANT_METRICS", False)


def get_registry() -> CollectorRegistry:
    global _registry
    if _registry is not None:
        return _registry

    if settings.PROMETHEUS_MULTIPROC_DIR:
        os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", settings.PROMETHEUS_MULTIPROC_DIR)
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        _registry = registry
    else:
        _registry = CollectorRegistry()
    return _registry


def _init_metrics() -> None:
    global HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS
    global CELERY_TASKS_TOTAL, CELERY_TASK_DURATION_SECONDS
    global ACTIVE_USERS, CACHE_HIT_RATIO
    global MODEL_INFERENCE_DURATION_SECONDS, MODEL_PREDICTIONS_TOTAL, MODEL_ERRORS_TOTAL
    global CIRCUIT_BREAKER_METRICS, DATA_PROVIDER_REQUESTS_TOTAL, DATA_PROVIDER_DURATION_SECONDS
    global RATE_LIMIT_ALLOWED_TOTAL, RATE_LIMIT_BLOCKED_TOTAL
    global QUOTA_INCREMENT_SUCCESS_TOTAL, QUOTA_INCREMENT_FAILURE_TOTAL

    reg = get_registry()

    if HTTP_REQUESTS_TOTAL is None:
        HTTP_REQUESTS_TOTAL = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status", "tenant"],
            registry=reg,
        )
    if HTTP_REQUEST_DURATION_SECONDS is None:
        HTTP_REQUEST_DURATION_SECONDS = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            buckets=(0.025, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
            labelnames=["method", "endpoint", "tenant"],
            registry=reg,
        )

    if CELERY_TASKS_TOTAL is None:
        CELERY_TASKS_TOTAL = Counter(
            "celery_tasks_total",
            "Total Celery tasks by status",
            ["task_name", "status"],
            registry=reg,
        )
    if CELERY_TASK_DURATION_SECONDS is None:
        CELERY_TASK_DURATION_SECONDS = Histogram(
            "celery_task_duration_seconds",
            "Celery task duration in seconds",
            buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30, 60),
            labelnames=["task_name"],
            registry=reg,
        )

    if ACTIVE_USERS is None:
        ACTIVE_USERS = Gauge("active_users", "Number of active users", registry=reg)
    if CACHE_HIT_RATIO is None:
        CACHE_HIT_RATIO = Gauge("cache_hit_ratio", "Cache hit ratio", registry=reg)

    if MODEL_INFERENCE_DURATION_SECONDS is None:
        MODEL_INFERENCE_DURATION_SECONDS = Histogram(
            "model_inference_duration_seconds",
            "Model inference duration seconds",
            buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
            labelnames=["model", "variant"] if FEATURE_MODEL_VARIANT_METRICS else ["model"],
            registry=reg,
        )
    if MODEL_PREDICTIONS_TOTAL is None:
        MODEL_PREDICTIONS_TOTAL = Counter(
            "model_predictions_total",
            "Total model predictions",
            ["model", "variant"] if FEATURE_MODEL_VARIANT_METRICS else ["model"],
            registry=reg,
        )
    if MODEL_ERRORS_TOTAL is None:
        MODEL_ERRORS_TOTAL = Counter(
            "model_errors_total",
            "Total model errors",
            ["model", "variant"] if FEATURE_MODEL_VARIANT_METRICS else ["model"],
            registry=reg,
        )
    
    # Phase 7: Data Provider and Circuit Breaker Metrics
    if CIRCUIT_BREAKER_METRICS is None:
        CIRCUIT_BREAKER_METRICS = Counter(
            "circuit_breaker_state_changes_total",
            "Total circuit breaker state changes",
            ["circuit_name", "state"],
            registry=reg,
        )
    if DATA_PROVIDER_REQUESTS_TOTAL is None:
        DATA_PROVIDER_REQUESTS_TOTAL = Counter(
            "data_provider_requests_total",
            "Total data provider requests",
            ["provider", "data_type", "status"],
            registry=reg,
        )
    if DATA_PROVIDER_DURATION_SECONDS is None:
        DATA_PROVIDER_DURATION_SECONDS = Histogram(
            "data_provider_duration_seconds",
            "Data provider request duration in seconds",
            buckets=(0.1, 0.2, 0.5, 1, 2, 5, 10, 30),
            labelnames=["provider", "data_type"],
            registry=reg,
        )

    # Rate limiting metrics
    if RATE_LIMIT_ALLOWED_TOTAL is None:
        RATE_LIMIT_ALLOWED_TOTAL = Counter(
            "rate_limit_allowed_total",
            "Total requests allowed by rate limiter",
            ["tenant", "limit_type"],
            registry=reg,
        )
    if RATE_LIMIT_BLOCKED_TOTAL is None:
        RATE_LIMIT_BLOCKED_TOTAL = Counter(
            "rate_limit_blocked_total",
            "Total requests blocked by rate limiter",
            ["tenant", "limit_type"],
            registry=reg,
        )
    
    # Quota metrics
    if QUOTA_INCREMENT_SUCCESS_TOTAL is None:
        QUOTA_INCREMENT_SUCCESS_TOTAL = Counter(
            "quota_increment_success_total",
            "Total successful quota increments",
            ["tenant", "quota_type"],
            registry=reg,
        )
    if QUOTA_INCREMENT_FAILURE_TOTAL is None:
        QUOTA_INCREMENT_FAILURE_TOTAL = Counter(
            "quota_increment_failure_total",
            "Total failed quota increments",
            ["tenant", "quota_type"],
            registry=reg,
        )


def init_app(app) -> None:
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()

    @app.route(settings.METRICS_ROUTE)
    def metrics() -> Response:
        if not settings.FEATURE_PROMETHEUS_METRICS:
            return Response("metrics disabled", status=404)
        reg = get_registry()
        return Response(generate_latest(reg), mimetype=CONTENT_TYPE_LATEST)


def before_request() -> None:
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if has_request_context():
        g._metrics_start_time = time.time()


def after_request(response):
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return response
    if not has_request_context():
        return response

    try:
        method = request.method
        endpoint = request.endpoint or request.path
        status = getattr(response, "status_code", None)
        tenant = getattr(g, "tenant_id", "unknown")

        # Increment request counter
        if HTTP_REQUESTS_TOTAL is not None and status is not None:
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status), tenant=tenant).inc()

        # Observe duration
        start = getattr(g, "_metrics_start_time", None)
        if start is not None and HTTP_REQUEST_DURATION_SECONDS is not None:
            duration = time.time() - start
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint, tenant=tenant).observe(duration)
    except Exception:
        # Do not break responses on metrics errors
        pass

    return response


# Celery instrumentation helpers
def celery_task_started(task_name: str) -> float:
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return time.time()
    _init_metrics()
    return time.time()


def celery_task_succeeded(task_name: str, start_time: float) -> None:
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if CELERY_TASKS_TOTAL is not None:
        CELERY_TASKS_TOTAL.labels(task_name=task_name, status="success").inc()
    if CELERY_TASK_DURATION_SECONDS is not None:
        CELERY_TASK_DURATION_SECONDS.labels(task_name=task_name).observe(time.time() - start_time)


def celery_task_failed(task_name: str, start_time: float) -> None:
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if CELERY_TASKS_TOTAL is not None:
        CELERY_TASKS_TOTAL.labels(task_name=task_name, status="failure").inc()
    if CELERY_TASK_DURATION_SECONDS is not None:
        CELERY_TASK_DURATION_SECONDS.labels(task_name=task_name).observe(time.time() - start_time)


# Rate limiting metrics helpers
def rate_limit_allowed(tenant: str, limit_type: str) -> None:
    """Record a rate limit allow event"""
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if RATE_LIMIT_ALLOWED_TOTAL is not None:
        # Hash tenant to avoid cardinality issues
        tenant_hash = str(hash(tenant) % 10000)
        RATE_LIMIT_ALLOWED_TOTAL.labels(tenant=tenant_hash, limit_type=limit_type).inc()


def rate_limit_blocked(tenant: str, limit_type: str) -> None:
    """Record a rate limit block event"""
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if RATE_LIMIT_BLOCKED_TOTAL is not None:
        # Hash tenant to avoid cardinality issues
        tenant_hash = str(hash(tenant) % 10000)
        RATE_LIMIT_BLOCKED_TOTAL.labels(tenant=tenant_hash, limit_type=limit_type).inc()


# Quota metrics helpers
def quota_increment_success(tenant: str, quota_type: str) -> None:
    """Record a successful quota increment"""
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if QUOTA_INCREMENT_SUCCESS_TOTAL is not None:
        # Hash tenant to avoid cardinality issues
        tenant_hash = str(hash(tenant) % 10000)
        QUOTA_INCREMENT_SUCCESS_TOTAL.labels(tenant=tenant_hash, quota_type=quota_type).inc()


def quota_increment_failure(tenant: str, quota_type: str) -> None:
    """Record a failed quota increment"""
    if not settings.FEATURE_PROMETHEUS_METRICS:
        return
    _init_metrics()
    if QUOTA_INCREMENT_FAILURE_TOTAL is not None:
        # Hash tenant to avoid cardinality issues
        tenant_hash = str(hash(tenant) % 10000)
        QUOTA_INCREMENT_FAILURE_TOTAL.labels(tenant=tenant_hash, quota_type=quota_type).inc()
