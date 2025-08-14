import time
import logging
from typing import List, Dict, Any

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_success, task_failure
import contextvars

from .settings import settings
from .ml_models.revenue_predictor import RevenuePredictor
from .ml_models.portfolio_optimizer import PortfolioOptimizer
from .metrics import (
    celery_task_started,
    celery_task_succeeded,
    celery_task_failed,
)
from .logging import logger
from .ml_models.registry import get_model, registry, track_model_performance

celery_app = Celery("valor_ivx", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# request correlation id propagated via Celery signals (best-effort)
_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

# Instrumentation state (per-task timing)
_task_start_times: Dict[str, float] = {}


@task_prerun.connect
def _on_task_prerun(task_id=None, task=None, *args, **kwargs):
    try:
        task_name = getattr(task, "name", "unknown")
        _task_start_times[task_id] = celery_task_started(task_name)
        # capture request_id from headers/context if provided in kwargs
        req_id = None
        try:
            headers = kwargs.get("headers") or {}
            req_id = headers.get("X-Request-ID")
        except Exception:
            req_id = None
        _request_id_ctx.set(req_id)
        logger.info("celery_task_started", task_id=task_id, task_name=task_name, request_id=req_id)
    except Exception:
        # Never break task execution due to observability
        pass


@task_postrun.connect
def _on_task_postrun(task_id=None, task=None, retval=None, state=None, *args, **kwargs):
    try:
        task_name = getattr(task, "name", "unknown")
        start = _task_start_times.pop(task_id, None)
        if start is not None:
            celery_task_succeeded(task_name, start)
        req_id = _request_id_ctx.get()
        logger.info("celery_task_succeeded", task_id=task_id, task_name=task_name, state=state, request_id=req_id)
    except Exception:
        pass


@task_failure.connect
def _on_task_failure(task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, sender=None, *a, **k):
    try:
        task_name = getattr(sender, "name", "unknown")
        start = _task_start_times.pop(task_id, None)
        if start is not None:
            celery_task_failed(task_name, start)
        req_id = _request_id_ctx.get()
        logger.error(
            "celery_task_failed",
            task_id=task_id,
            task_name=task_name,
            error=str(exception) if exception else None,
            request_id=req_id,
        )
    except Exception:
        pass


@celery_app.task(name="analytics.run_revenue_prediction")
def run_revenue_prediction(ticker: str, historical_data: List[Dict[str, Any]]) -> Any:
    """
    Resolve revenue prediction model via registry/settings.REVENUE_MODEL_NAME and optional variant.
    Standard interface: model.predict(historical_data) -> Any
    """
    base_alias = getattr(settings, "REVENUE_MODEL_NAME", "revenue_predictor")
    variant = getattr(settings, "REVENUE_MODEL_VARIANT", "") or ""
    # Apply variant routing at call-time (idempotent if already set at boot)
    try:
        registry.set_variant(base_alias, variant)
    except Exception:
        # non-fatal
        pass

    try:
        start_time = time.time()
        predictor = get_model(base_alias)
        effective_alias = registry._last_resolution.get(base_alias, base_alias)  # introspection for logs/metrics
        result = predictor.predict(historical_data)
        execution_time = time.time() - start_time
        
        # Track performance
        track_model_performance(effective_alias, execution_time)
        
        logger.info(
            "revenue_prediction_completed",
            ticker=ticker,
            model=base_alias,
            variant=variant or None,
            effective_model=effective_alias,
            execution_time=execution_time,
        )
        return result
    except Exception as e:
        logger.error(
            "revenue_prediction_failed",
            ticker=ticker,
            error=str(e),
            model=base_alias,
            variant=variant or None,
            effective_model=registry._last_resolution.get(base_alias, base_alias),
        )
        raise


@celery_app.task(name="analytics.run_portfolio_optimization")
def run_portfolio_optimization(assets: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Any:
    """
    Resolve optimizer via registry/settings.PORTFOLIO_OPTIMIZER_NAME and optional variant.
    Standard interface: model.optimize(assets, constraints) -> Any
    """
    base_alias = getattr(settings, "PORTFOLIO_OPTIMIZER_NAME", "portfolio_optimizer")
    variant = getattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "") or ""
    # Apply variant routing at call-time
    try:
        registry.set_variant(base_alias, variant)
    except Exception:
        pass

    try:
        start_time = time.time()
        optimizer = get_model(base_alias)
        effective_alias = registry._last_resolution.get(base_alias, base_alias)
        result = optimizer.optimize(assets, constraints)
        execution_time = time.time() - start_time
        
        # Track performance
        track_model_performance(effective_alias, execution_time)
        
        logger.info(
            "portfolio_optimization_completed",
            model=base_alias,
            variant=variant or None,
            effective_model=effective_alias,
            execution_time=execution_time,
        )
        return result
    except Exception as e:
        logger.error(
            "portfolio_optimization_failed",
            error=str(e),
            model=base_alias,
            variant=variant or None,
            effective_model=registry._last_resolution.get(base_alias, base_alias),
        )
        raise
