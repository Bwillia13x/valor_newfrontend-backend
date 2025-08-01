"""
Risk Management API Routes
Handles VaR, stress testing, and risk attribution endpoints
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
import traceback
import sys
import os
import pandas as pd
import numpy as np

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.risk_management import RiskManager
from utils.auth_utils import require_auth
from utils.response_utils import create_response, create_error_response

logger = logging.getLogger(__name__)

# Create Blueprint
risk_bp = Blueprint('risk', __name__)

# Initialize risk manager
risk_manager = RiskManager()

@risk_bp.route('/api/risk/var/historical', methods=['POST'])
@cross_origin()
@require_auth
def calculate_historical_var():
    """Calculate historical VaR"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to Series
        returns_data = data['returns']
        returns_series = pd.Series(returns_data)
        
        # Extract optional parameters
        confidence_level = float(data.get('confidence_level', 0.95))
        time_horizon = int(data.get('time_horizon', 1))
        
        # Calculate historical VaR
        result = risk_manager.calculate_var(
            returns_series, method='historical', 
            confidence_level=confidence_level, time_horizon=time_horizon
        )
        
        return create_response("Historical VaR calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in historical VaR calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in historical VaR calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/var/parametric', methods=['POST'])
@cross_origin()
@require_auth
def calculate_parametric_var():
    """Calculate parametric VaR"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to Series
        returns_data = data['returns']
        returns_series = pd.Series(returns_data)
        
        # Extract optional parameters
        confidence_level = float(data.get('confidence_level', 0.95))
        time_horizon = int(data.get('time_horizon', 1))
        distribution = data.get('distribution', 'normal')
        
        # Calculate parametric VaR
        result = risk_manager.calculate_var(
            returns_series, method='parametric',
            confidence_level=confidence_level, time_horizon=time_horizon,
            distribution=distribution
        )
        
        return create_response("Parametric VaR calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in parametric VaR calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in parametric VaR calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/var/monte-carlo', methods=['POST'])
@cross_origin()
@require_auth
def calculate_monte_carlo_var():
    """Calculate Monte Carlo VaR"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to Series
        returns_data = data['returns']
        returns_series = pd.Series(returns_data)
        
        # Extract optional parameters
        confidence_level = float(data.get('confidence_level', 0.95))
        time_horizon = int(data.get('time_horizon', 1))
        num_simulations = int(data.get('num_simulations', 10000))
        distribution = data.get('distribution', 'normal')
        
        # Calculate Monte Carlo VaR
        result = risk_manager.calculate_var(
            returns_series, method='monte_carlo',
            confidence_level=confidence_level, time_horizon=time_horizon,
            num_simulations=num_simulations, distribution=distribution
        )
        
        return create_response("Monte Carlo VaR calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in Monte Carlo VaR calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in Monte Carlo VaR calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/cvar', methods=['POST'])
@cross_origin()
@require_auth
def calculate_conditional_var():
    """Calculate Conditional VaR (Expected Shortfall)"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to Series
        returns_data = data['returns']
        returns_series = pd.Series(returns_data)
        
        # Extract optional parameters
        confidence_level = float(data.get('confidence_level', 0.95))
        time_horizon = int(data.get('time_horizon', 1))
        
        # Calculate CVaR using historical method (includes CVaR)
        result = risk_manager.calculate_var(
            returns_series, method='historical',
            confidence_level=confidence_level, time_horizon=time_horizon
        )
        
        # Extract CVaR from result
        cvar_result = {
            'conditional_var': result['conditional_var'],
            'scaled_cvar': result['scaled_cvar'],
            'confidence_level': confidence_level,
            'time_horizon': time_horizon
        }
        
        return create_response("Conditional VaR calculated successfully", cvar_result)
        
    except ValueError as e:
        logger.error(f"Validation error in CVaR calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in CVaR calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/incremental-var', methods=['POST'])
@cross_origin()
@require_auth
def calculate_incremental_var():
    """Calculate incremental VaR"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['portfolio_data', 'new_position']
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        portfolio_data = data['portfolio_data']
        new_position = data['new_position']
        
        # Calculate incremental VaR
        result = risk_manager.calculate_incremental_var(portfolio_data, new_position)
        
        return create_response("Incremental VaR calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in incremental VaR calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in incremental VaR calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/stress-test', methods=['POST'])
@cross_origin()
@require_auth
def run_stress_test():
    """Run stress test"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        scenario = data.get('scenario')
        
        # Run stress test
        result = risk_manager.run_stress_test(portfolio_data, scenario)
        
        return create_response("Stress test completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in stress testing: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in stress testing: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/stress-test/multiple', methods=['POST'])
@cross_origin()
@require_auth
def run_multiple_stress_scenarios():
    """Run multiple stress scenarios"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        scenarios = data.get('scenarios')
        
        # Run multiple stress scenarios
        result = risk_manager.run_multiple_stress_scenarios(portfolio_data, scenarios)
        
        return create_response("Multiple stress scenarios completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in multiple stress scenarios: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in multiple stress scenarios: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/attribution', methods=['POST'])
@cross_origin()
@require_auth
def calculate_risk_attribution():
    """Calculate risk attribution"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        method = data.get('method', 'factor')
        
        # Calculate risk attribution
        result = risk_manager.calculate_risk_attribution(portfolio_data, method)
        
        return create_response("Risk attribution calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in risk attribution: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in risk attribution: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/budget', methods=['POST'])
@cross_origin()
@require_auth
def optimize_risk_budget():
    """Optimize risk budget"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['portfolio_data', 'risk_budget']
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        portfolio_data = data['portfolio_data']
        risk_budget = data['risk_budget']
        optimization_constraints = data.get('optimization_constraints')
        
        # Optimize risk budget
        result = risk_manager.optimize_risk_budget(
            portfolio_data, risk_budget, optimization_constraints
        )
        
        return create_response("Risk budget optimization completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in risk budget optimization: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in risk budget optimization: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/tail-measures', methods=['POST'])
@cross_origin()
@require_auth
def calculate_tail_risk_measures():
    """Calculate tail risk measures"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to Series
        returns_data = data['returns']
        returns_series = pd.Series(returns_data)
        
        # Extract optional parameters
        confidence_levels = data.get('confidence_levels', [0.95, 0.99, 0.995])
        
        # Calculate tail risk measures
        result = risk_manager.calculate_tail_risk_measures(returns_series, confidence_levels)
        
        return create_response("Tail risk measures calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in tail risk measures calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in tail risk measures calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/sensitivity', methods=['POST'])
@cross_origin()
@require_auth
def run_sensitivity_analysis():
    """Run sensitivity analysis"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        sensitivity_params = data.get('sensitivity_params', {})
        
        # Run sensitivity analysis (simplified implementation)
        results = {}
        
        # Example: sensitivity to risk-free rate changes
        if 'risk_free_rate_range' in sensitivity_params:
            risk_free_rates = sensitivity_params['risk_free_rate_range']
            for rf in risk_free_rates:
                # Modify portfolio data with new risk-free rate
                modified_data = portfolio_data.copy()
                modified_data['risk_free_rate'] = rf
                
                # Calculate VaR with modified parameters
                returns_series = pd.Series(modified_data.get('returns', []))
                if len(returns_series) > 0:
                    var_result = risk_manager.calculate_var(returns_series, method='historical')
                    results[f'rf_{rf}'] = var_result['historical_var']
        
        return create_response("Sensitivity analysis completed successfully", results)
        
    except ValueError as e:
        logger.error(f"Validation error in sensitivity analysis: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/scenarios', methods=['GET'])
@cross_origin()
@require_auth
def get_stress_scenarios():
    """Get available stress scenarios"""
    try:
        scenarios = {
            'default_scenarios': [
                {
                    'name': 'Market Crash',
                    'description': 'Severe market downturn scenario',
                    'equity_shock': -0.30,
                    'interest_rate_shock': 0.02,
                    'volatility_shock': 2.0,
                    'correlation_shock': 0.3
                },
                {
                    'name': 'Economic Recession',
                    'description': 'Economic downturn scenario',
                    'equity_shock': -0.20,
                    'interest_rate_shock': -0.01,
                    'volatility_shock': 1.5,
                    'correlation_shock': 0.2
                },
                {
                    'name': 'Inflation Shock',
                    'description': 'Rising inflation scenario',
                    'equity_shock': -0.10,
                    'interest_rate_shock': 0.05,
                    'volatility_shock': 1.8,
                    'correlation_shock': 0.25
                },
                {
                    'name': 'Liquidity Crisis',
                    'description': 'Market liquidity crisis scenario',
                    'equity_shock': -0.15,
                    'interest_rate_shock': 0.03,
                    'volatility_shock': 2.5,
                    'correlation_shock': 0.4
                }
            ],
            'var_methods': [
                'historical',
                'parametric',
                'monte_carlo'
            ],
            'attribution_methods': [
                'asset',
                'factor',
                'systematic'
            ]
        }
        
        return create_response("Stress scenarios retrieved successfully", scenarios)
        
    except Exception as e:
        logger.error(f"Error retrieving stress scenarios: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@risk_bp.route('/api/risk/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'risk_management',
            'models_loaded': True,
            'timestamp': pd.Timestamp.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'risk_management',
            'error': str(e)
        }), 500 