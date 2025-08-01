from flask import Blueprint, request, jsonify
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError, constr, conlist

from ..tasks import celery_app, run_revenue_prediction, run_portfolio_optimization

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


# Pydantic request/response schemas
class HistoricalPoint(BaseModel):
    date: constr(strip_whitespace=True) = Field(..., description="ISO date or label")
    value: float = Field(..., description="Historical metric value")


class RevenuePredictionRequest(BaseModel):
    ticker: constr(strip_whitespace=True, min_length=1)
    # Accept either list of numbers or list of objects with date/value
    historical_data: List[Dict[str, Any]]


class TaskEnqueuedResponse(BaseModel):
    task_id: str
    status: str = "started"


class PortfolioAsset(BaseModel):
    symbol: constr(strip_whitespace=True, min_length=1)
    weight_min: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    weight_max: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    expected_return: Optional[float] = None
    volatility: Optional[float] = None


class PortfolioConstraints(BaseModel):
    target_return: Optional[float] = None
    max_volatility: Optional[float] = None
    long_only: Optional[bool] = True


class PortfolioOptimizationRequest(BaseModel):
    assets: conlist(PortfolioAsset, min_length=1)
    constraints: PortfolioConstraints = Field(default_factory=PortfolioConstraints)


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None


def _validation_error(e: ValidationError, status_code: int = 422):
    return jsonify({"error": "ValidationError", "details": e.errors()}), status_code


@analytics_bp.route("/revenue-prediction", methods=["POST"])
def start_revenue_prediction() -> Any:
    try:
        payload = RevenuePredictionRequest.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return _validation_error(e)

    # inject request_id header for Celery propagation
    req_id = getattr(request, "headers", {}).get("X-Request-ID")
    task = run_revenue_prediction.apply_async(
        args=[payload.ticker, payload.historical_data],
        headers={"X-Request-ID": req_id} if req_id else None,
    )
    resp = TaskEnqueuedResponse(task_id=task.id, status="started")
    return jsonify(resp.model_dump()), 202


@analytics_bp.route("/portfolio-optimization", methods=["POST"])
def start_portfolio_optimization() -> Any:
    try:
        payload = PortfolioOptimizationRequest.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return _validation_error(e)

    # Convert Pydantic models to plain dicts for Celery serialization
    assets = [a.model_dump() for a in payload.assets]
    constraints = payload.constraints.model_dump()
    # inject request_id header for Celery propagation
    req_id = getattr(request, "headers", {}).get("X-Request-ID")
    task = run_portfolio_optimization.apply_async(
        args=[assets, constraints],
        headers={"X-Request-ID": req_id} if req_id else None,
    )
    resp = TaskEnqueuedResponse(task_id=task.id, status="started")
    return jsonify(resp.model_dump()), 202


@analytics_bp.route("/task/<task_id>", methods=["GET"])
def get_task_status(task_id: str) -> Any:
    task = celery_app.AsyncResult(task_id)
    resp = TaskStatusResponse(
        task_id=task_id,
        status=str(task.status),
        result=task.result if task.ready() else None,
    )
    return jsonify(resp.model_dump()), 200
