"""
ML Model Management API Routes
Phase 3: ML/Analytics Hardening
"""

from flask import Blueprint, jsonify, request, g
from typing import Dict, Any, Optional
import logging
import time

from ..ml_models.registry import registry, get_model_performance_stats, ABTestConfig
from ..auth import auth_required
from ..rate_limiter import rate_limit
from ..middleware.tenant import tenant_required
from ..models.rbac import Permission, RBACManager

# Initialize RBAC manager
rbac_manager = RBACManager()

ml_management_bp = Blueprint('ml_management', __name__, url_prefix='/api/ml')


@ml_management_bp.route('/models', methods=['GET'])
@auth_required
@rate_limit("api")
@tenant_required
def list_models():
    """List all available ML models and their variants"""
    try:
        models = {
            "available_models": list(registry._registry.keys()),
            "active_variants": dict(registry._variants),
            "ab_tests": {
                alias: {
                    "variant_a": config.variant_a,
                    "variant_b": config.variant_b,
                    "traffic_split": config.traffic_split,
                    "enabled": config.enabled
                }
                for alias, config in registry._ab_tests.items()
            },
            "usage_stats": registry.get_usage_stats()
        }
        
        return jsonify({
            "success": True,
            "data": models
        })
    except Exception as e:
        logging.error(f"Error listing models: {str(e)}")
        return jsonify({"error": "Failed to list models"}), 500


@ml_management_bp.route('/models/<model_alias>/variant', methods=['PUT'])
@auth_required
@rate_limit("api")
@tenant_required
def set_model_variant(model_alias: str):
    """Set variant routing for a specific model"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, g.tenant_id):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        variant_alias = data.get('variant_alias', '')
        
        if variant_alias:
            # Validate that the variant exists
            if variant_alias not in registry._registry:
                return jsonify({"error": f"Variant '{variant_alias}' not found"}), 400
            
            registry.set_variant(model_alias, variant_alias)
            logging.info(f"Set variant routing: {model_alias} -> {variant_alias}")
        else:
            # Remove variant routing
            registry.set_variant(model_alias, '')
            logging.info(f"Removed variant routing for: {model_alias}")
        
        return jsonify({
            "success": True,
            "message": f"Variant routing updated for {model_alias}",
            "data": {
                "model_alias": model_alias,
                "variant_alias": variant_alias or None
            }
        })
    except Exception as e:
        logging.error(f"Error setting model variant: {str(e)}")
        return jsonify({"error": "Failed to set model variant"}), 500


@ml_management_bp.route('/models/<model_alias>/ab-test', methods=['PUT'])
@auth_required
@rate_limit("api")
@tenant_required
def configure_ab_test(model_alias: str):
    """Configure A/B testing for a model"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, g.tenant_id):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        variant_a = data.get('variant_a')
        variant_b = data.get('variant_b')
        traffic_split = data.get('traffic_split', 0.5)
        enabled = data.get('enabled', True)
        
        # Validate inputs
        if not variant_a or not variant_b:
            return jsonify({"error": "Both variant_a and variant_b are required"}), 400
        
        if variant_a not in registry._registry or variant_b not in registry._registry:
            return jsonify({"error": "One or both variants not found"}), 400
        
        if not 0.0 <= traffic_split <= 1.0:
            return jsonify({"error": "traffic_split must be between 0.0 and 1.0"}), 400
        
        # Configure A/B test
        registry.configure_ab_test(model_alias, variant_a, variant_b, traffic_split, enabled)
        
        logging.info(f"Configured A/B test for {model_alias}: {variant_a} vs {variant_b} ({traffic_split})")
        
        return jsonify({
            "success": True,
            "message": f"A/B test configured for {model_alias}",
            "data": {
                "model_alias": model_alias,
                "variant_a": variant_a,
                "variant_b": variant_b,
                "traffic_split": traffic_split,
                "enabled": enabled
            }
        })
    except Exception as e:
        logging.error(f"Error configuring A/B test: {str(e)}")
        return jsonify({"error": "Failed to configure A/B test"}), 500


@ml_management_bp.route('/models/<model_alias>/ab-test', methods=['DELETE'])
@auth_required
@rate_limit("api")
@tenant_required
def disable_ab_test(model_alias: str):
    """Disable A/B testing for a model"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, g.tenant_id):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        if model_alias in registry._ab_tests:
            # Disable the A/B test
            registry.configure_ab_test(model_alias, "", "", 0.0, False)
            logging.info(f"Disabled A/B test for {model_alias}")
        
        return jsonify({
            "success": True,
            "message": f"A/B test disabled for {model_alias}"
        })
    except Exception as e:
        logging.error(f"Error disabling A/B test: {str(e)}")
        return jsonify({"error": "Failed to disable A/B test"}), 500


@ml_management_bp.route('/models/<model_alias>/performance', methods=['GET'])
@auth_required
@rate_limit("api")
@tenant_required
def get_model_performance(model_alias: str):
    """Get performance statistics for a model variant"""
    try:
        stats = get_model_performance_stats(model_alias)
        
        if stats is None:
            return jsonify({
                "success": True,
                "data": {
                    "model_alias": model_alias,
                    "performance_stats": None,
                    "message": "No performance data available"
                }
            })
        
        return jsonify({
            "success": True,
            "data": {
                "model_alias": model_alias,
                "performance_stats": stats
            }
        })
    except Exception as e:
        logging.error(f"Error getting model performance: {str(e)}")
        return jsonify({"error": "Failed to get model performance"}), 500


@ml_management_bp.route('/models/performance', methods=['GET'])
@auth_required
@rate_limit("api")
@tenant_required
def get_all_model_performance():
    """Get performance statistics for all models"""
    try:
        all_stats = {}
        for alias in registry._registry.keys():
            stats = get_model_performance_stats(alias)
            if stats:
                all_stats[alias] = stats
        
        return jsonify({
            "success": True,
            "data": {
                "performance_stats": all_stats
            }
        })
    except Exception as e:
        logging.error(f"Error getting all model performance: {str(e)}")
        return jsonify({"error": "Failed to get model performance"}), 500


@ml_management_bp.route('/models/ab-test-stats', methods=['GET'])
@auth_required
@rate_limit("api")
@tenant_required
def get_ab_test_stats():
    """Get A/B testing statistics"""
    try:
        stats = registry.get_ab_test_stats()
        
        return jsonify({
            "success": True,
            "data": {
                "ab_test_stats": stats
            }
        })
    except Exception as e:
        logging.error(f"Error getting A/B test stats: {str(e)}")
        return jsonify({"error": "Failed to get A/B test statistics"}), 500


@ml_management_bp.route('/models/usage', methods=['GET'])
@auth_required
@rate_limit("api")
@tenant_required
def get_usage_stats():
    """Get usage statistics for all models"""
    try:
        usage_stats = registry.get_usage_stats()
        
        return jsonify({
            "success": True,
            "data": {
                "usage_stats": usage_stats
            }
        })
    except Exception as e:
        logging.error(f"Error getting usage stats: {str(e)}")
        return jsonify({"error": "Failed to get usage statistics"}), 500


@ml_management_bp.route('/models/<model_alias>/test', methods=['POST'])
@auth_required
@rate_limit("api")
@tenant_required
def test_model(model_alias: str):
    """Test a model with sample data"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.READ_MODELS, g.tenant_id):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        test_data = data.get('test_data', {})
        
        # Get the model
        try:
            model = registry.get(model_alias)
        except KeyError:
            return jsonify({"error": f"Model '{model_alias}' not found"}), 404
        
        # Test the model based on its type
        start_time = time.time()
        
        if hasattr(model, 'predict'):
            # Revenue predictor
            result = model.predict(test_data.get('historical_data', [{"x": 1}]))
        elif hasattr(model, 'optimize'):
            # Portfolio optimizer
            result = model.optimize(
                test_data.get('assets', [{"ticker": "AAPL"}]),
                test_data.get('constraints', {"max_weight": 0.5})
            )
        else:
            return jsonify({"error": "Unknown model type"}), 400
        
        execution_time = time.time() - start_time
        
        # Track performance
        effective_alias = registry._last_resolution.get(model_alias, model_alias)
        registry.track_performance(effective_alias, execution_time)
        
        return jsonify({
            "success": True,
            "data": {
                "model_alias": model_alias,
                "effective_alias": effective_alias,
                "result": result,
                "execution_time": execution_time
            }
        })
    except Exception as e:
        logging.error(f"Error testing model: {str(e)}")
        return jsonify({"error": "Failed to test model"}), 500


@ml_management_bp.route('/models/clear-metrics', methods=['POST'])
@auth_required
@rate_limit("api")
@tenant_required
def clear_performance_metrics():
    """Clear performance metrics for all models"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, g.tenant_id):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        model_alias = data.get('model_alias')  # Optional, clear specific model
        
        registry.clear_performance_metrics(model_alias)
        
        return jsonify({
            "success": True,
            "message": f"Performance metrics cleared for {'all models' if model_alias is None else model_alias}"
        })
    except Exception as e:
        logging.error(f"Error clearing performance metrics: {str(e)}")
        return jsonify({"error": "Failed to clear performance metrics"}), 500 