"""
Tests for ML Variant Routing Activation and Functionality
Phase 3: ML/Analytics Hardening
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.app import init_ml_variant_routing
from backend.ml_models.registry import registry as ml_registry
from backend.settings import settings


class TestMLVariantRoutingActivation:
    """Test ML variant routing activation at startup"""
    
    def test_init_ml_variant_routing_with_revenue_variant(self, monkeypatch):
        """Test revenue model variant routing activation"""
        # Mock settings
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "revenue_predictor_v2", raising=False)
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "", raising=False)
        monkeypatch.setattr(settings, "FEATURE_MODEL_VARIANT_METRICS", False, raising=False)
        
        # Mock logger
        mock_logger = MagicMock()
        monkeypatch.setattr("backend.app.app.logger", mock_logger)
        
        # Clear any existing variants
        ml_registry._variants.clear()
        
        # Run initialization
        init_ml_variant_routing()
        
        # Verify variant was set
        assert ml_registry._variants.get("revenue_predictor") == "revenue_predictor_v2"
        assert "revenue_predictor -> revenue_predictor_v2" in str(mock_logger.info.call_args_list)
    
    def test_init_ml_variant_routing_with_portfolio_variant(self, monkeypatch):
        """Test portfolio optimizer variant routing activation"""
        # Mock settings
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "", raising=False)
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "portfolio_optimizer_v2", raising=False)
        monkeypatch.setattr(settings, "FEATURE_MODEL_VARIANT_METRICS", False, raising=False)
        
        # Mock logger
        mock_logger = MagicMock()
        monkeypatch.setattr("backend.app.app.logger", mock_logger)
        
        # Clear any existing variants
        ml_registry._variants.clear()
        
        # Run initialization
        init_ml_variant_routing()
        
        # Verify variant was set
        assert ml_registry._variants.get("portfolio_optimizer") == "portfolio_optimizer_v2"
        assert "portfolio_optimizer -> portfolio_optimizer_v2" in str(mock_logger.info.call_args_list)
    
    def test_init_ml_variant_routing_with_both_variants(self, monkeypatch):
        """Test both model variant routing activation"""
        # Mock settings
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "revenue_predictor_v2", raising=False)
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "portfolio_optimizer_v2", raising=False)
        monkeypatch.setattr(settings, "FEATURE_MODEL_VARIANT_METRICS", True, raising=False)
        
        # Mock logger
        mock_logger = MagicMock()
        monkeypatch.setattr("backend.app.app.logger", mock_logger)
        
        # Clear any existing variants
        ml_registry._variants.clear()
        
        # Run initialization
        init_ml_variant_routing()
        
        # Verify both variants were set
        assert ml_registry._variants.get("revenue_predictor") == "revenue_predictor_v2"
        assert ml_registry._variants.get("portfolio_optimizer") == "portfolio_optimizer_v2"
        assert "ML variant metrics enabled" in str(mock_logger.info.call_args_list)
    
    def test_init_ml_variant_routing_with_no_variants(self, monkeypatch):
        """Test initialization when no variants are configured"""
        # Mock settings
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "", raising=False)
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "", raising=False)
        monkeypatch.setattr(settings, "FEATURE_MODEL_VARIANT_METRICS", False, raising=False)
        
        # Mock logger
        mock_logger = MagicMock()
        monkeypatch.setattr("backend.app.app.logger", mock_logger)
        
        # Clear any existing variants
        ml_registry._variants.clear()
        
        # Run initialization
        init_ml_variant_routing()
        
        # Verify no variants were set
        assert len(ml_registry._variants) == 0
        assert "ML variant routing initialization completed" in str(mock_logger.info.call_args_list)
    
    def test_init_ml_variant_routing_error_handling(self, monkeypatch):
        """Test error handling during variant routing initialization"""
        # Mock settings to cause an error
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "invalid_variant", raising=False)
        
        # Mock logger
        mock_logger = MagicMock()
        monkeypatch.setattr("backend.app.app.logger", mock_logger)
        
        # Mock registry.set_variant to raise an exception
        with patch.object(ml_registry, 'set_variant', side_effect=Exception("Test error")):
            # Run initialization - should not raise exception
            init_ml_variant_routing()
            
            # Verify error was logged
            assert "Error initializing ML variant routing" in str(mock_logger.error.call_args_list)


class TestMLVariantRoutingIntegration:
    """Test ML variant routing integration with actual model resolution"""
    
    def test_revenue_model_variant_resolution(self, monkeypatch):
        """Test that revenue model variant routing works correctly"""
        # Set up variant routing
        ml_registry.set_variant("revenue_predictor", "revenue_predictor_v2")
        
        # Get model instance
        model = ml_registry.get("revenue_predictor")
        
        # Verify we got the v2 model
        assert hasattr(model, "predict")
        
        # Test prediction to verify it's the v2 variant
        result = model.predict([{"x": 1}, {"x": 2}])
        assert isinstance(result, dict)
        assert result.get("variant") == "v2"
    
    def test_portfolio_optimizer_variant_resolution(self, monkeypatch):
        """Test that portfolio optimizer variant routing works correctly"""
        # Set up variant routing
        ml_registry.set_variant("portfolio_optimizer", "portfolio_optimizer_v2")
        
        # Get model instance
        model = ml_registry.get("portfolio_optimizer")
        
        # Verify we got the v2 model
        assert hasattr(model, "optimize")
        
        # Test optimization to verify it's the v2 variant
        result = model.optimize([{"ticker": "AAPL"}], {"max_weight": 0.5})
        assert isinstance(result, dict)
        assert result.get("variant") == "v2"
    
    def test_variant_fallback_mechanism(self):
        """Test that unknown variants fallback to base models"""
        # Set up unknown variant routing
        ml_registry.set_variant("revenue_predictor", "unknown_variant")
        
        # Get model instance - should fallback to base model
        model = ml_registry.get("revenue_predictor")
        
        # Verify we got a model (fallback worked)
        assert hasattr(model, "predict")
        
        # Test prediction - should not return v2 variant marker
        result = model.predict([{"x": 1}])
        assert not (isinstance(result, dict) and result.get("variant") == "v2")


class TestMLVariantMetrics:
    """Test ML variant metrics functionality"""
    
    def test_variant_metrics_enabled_flag(self, monkeypatch):
        """Test that variant metrics can be enabled/disabled"""
        # Test with metrics enabled
        monkeypatch.setattr(settings, "FEATURE_MODEL_VARIANT_METRICS", True, raising=False)
        from backend.metrics import FEATURE_MODEL_VARIANT_METRICS
        assert FEATURE_MODEL_VARIANT_METRICS is True
        
        # Test with metrics disabled
        monkeypatch.setattr(settings, "FEATURE_MODEL_VARIANT_METRICS", False, raising=False)
        from backend.metrics import FEATURE_MODEL_VARIANT_METRICS
        assert FEATURE_MODEL_VARIANT_METRICS is False
    
    def test_variant_resolution_tracking(self):
        """Test that variant resolution is tracked for metrics"""
        # Clear tracking
        ml_registry._last_resolution.clear()
        
        # Set up variant routing
        ml_registry.set_variant("revenue_predictor", "revenue_predictor_v2")
        
        # Resolve alias
        final_alias = ml_registry.resolve_alias("revenue_predictor")
        
        # Verify tracking
        assert ml_registry._last_resolution.get("revenue_predictor") == "revenue_predictor_v2"
        assert final_alias == "revenue_predictor_v2" 