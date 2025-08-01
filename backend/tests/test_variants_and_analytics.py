import json
import types
import pytest

from backend.ml_models.registry import ModelRegistry, DEFAULT_REGISTRY, registry as global_registry, get_model
from backend.settings import settings
from backend.tasks import run_revenue_prediction, run_portfolio_optimization
from backend.api.analytics_routes import AnalyticsRequest, PortfolioOptimizationRequest


class TestModelRegistryVariants:
    def test_variant_resolution_known_alias(self, monkeypatch):
        reg = ModelRegistry(base_registry=DEFAULT_REGISTRY)
        # ensure v2 aliases exist in DEFAULT_REGISTRY
        assert "revenue_predictor_v2" in DEFAULT_REGISTRY
        reg.set_variant("revenue_predictor", "revenue_predictor_v2")
        final = reg.resolve_alias("revenue_predictor")
        assert final == "revenue_predictor_v2"

        inst = reg.get("revenue_predictor")
        # variant class comes from v2 module; ensure it has a predict method
        assert hasattr(inst, "predict")

    def test_variant_resolution_unknown_alias_fallback(self):
        reg = ModelRegistry(base_registry=DEFAULT_REGISTRY)
        reg.set_variant("revenue_predictor", "nonexistent_variant")
        # resolve should point to unknown, but get() must fallback to base alias and succeed
        final = reg.resolve_alias("revenue_predictor")
        assert final == "nonexistent_variant"
        inst = reg.get("revenue_predictor")  # should fallback to "revenue_predictor"
        # base class should have predict
        assert hasattr(inst, "predict")

    def test_missing_base_raises(self):
        reg = ModelRegistry(base_registry=DEFAULT_REGISTRY)
        with pytest.raises(KeyError):
            reg.get("does_not_exist")


class TestTaskVariantSelection:
    def test_revenue_prediction_uses_variant_when_configured(self, monkeypatch):
        # set settings to use v2
        monkeypatch.setattr(settings, "REVENUE_MODEL_NAME", "revenue_predictor", raising=False)
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "revenue_predictor_v2", raising=False)

        # run task directly (celery decorator wraps but callable is available)
        data = [{"x": 1}, {"x": 2}]
        result = run_revenue_prediction.run("AAPL", data)  # use .run for eager-like execution in tests
        # v2 model returns a dict with variant: "v2"
        assert isinstance(result, dict)
        assert result.get("variant") == "v2"
        assert result.get("count") == len(data)

    def test_portfolio_optimizer_uses_variant_when_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_NAME", "portfolio_optimizer", raising=False)
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "portfolio_optimizer_v2", raising=False)

        assets = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
        constraints = {"max_weight": 0.2}
        result = run_portfolio_optimization.run(assets, constraints)
        assert isinstance(result, dict)
        assert result.get("variant") == "v2"
        assert result.get("assets") == ["AAPL", "MSFT"]
        assert result.get("constraints_keys") == ["max_weight"]

    def test_revenue_prediction_fallback_when_variant_unknown(self, monkeypatch):
        # Set an unknown variant; should fallback to base model which likely doesn't return variant marker
        monkeypatch.setattr(settings, "REVENUE_MODEL_NAME", "revenue_predictor", raising=False)
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "unknown_alias", raising=False)

        data = [{"x": 1}]
        out = run_revenue_prediction.run("AAPL", data)
        # base RevenuePredictor may return any structure; assert it did NOT return our v2 marker
        assert not (isinstance(out, dict) and out.get("variant") == "v2")


class TestAnalyticsSchemasAndEnqueue:
    def test_analytics_request_schema_validation_success(self):
        payload = {
            "ticker": "AAPL",
            "historical_data": [{"date": "2024-01-01", "revenue": 100.0}],
        }
        req = AnalyticsRequest(**payload)
        assert req.ticker == "AAPL"
        assert isinstance(req.historical_data, list)
        assert req.historical_data[0]["revenue"] == 100.0

    def test_analytics_request_schema_validation_failure(self):
        # Missing required fields should fail
        with pytest.raises(Exception):
            AnalyticsRequest(**{"ticker": "AAPL"})  # no historical_data

    def test_portfolio_request_schema_validation_success(self):
        payload = {
            "assets": [{"ticker": "AAPL"}, {"ticker": "MSFT"}],
            "constraints": {"max_weight": 0.1},
        }
        req = PortfolioOptimizationRequest(**payload)
        assert len(req.assets) == 2
        assert "max_weight" in req.constraints

    def test_portfolio_request_schema_validation_failure(self):
        with pytest.raises(Exception):
            PortfolioOptimizationRequest(**{"constraints": {}})  # no assets


# Note: API enqueue tests would normally hit Flask endpoints and Celery broker.
# Here we focus on Celery task callables via .run() for deterministic unit tests without Redis.
