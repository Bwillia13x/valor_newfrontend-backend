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
from .settings import settings

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
