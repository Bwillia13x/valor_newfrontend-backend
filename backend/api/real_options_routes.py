"""
Real Options API Routes
Phase 5A Implementation - Advanced Financial Models

This module provides REST API endpoints for real options analysis.
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
import traceback
from typing import Dict, List, Any
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.real_options import RealOptionsValuation, OptionParameters
from auth import require_auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
real_options_bp = Blueprint('real_options', __name__)

# Initialize real options engine
real_options_engine = RealOptionsValuation()

@real_options_bp.route('/api/real-options/expansion', methods=['POST'])
@cross_origin()
@require_auth
def calculate_expansion_option():
    """Calculate expansion option value"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['current_value', 'expansion_cost', 'time_to_expiry', 
                         'volatility', 'risk_free_rate']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        current_value = float(data['current_value'])
        expansion_cost = float(data['expansion_cost'])
        time_to_expiry = float(data['time_to_expiry'])
        volatility = float(data['volatility'])
        risk_free_rate = float(data['risk_free_rate'])
        expansion_multiplier = float(data.get('expansion_multiplier', 2.0))
        
        # Validate parameter ranges
        if current_value <= 0 or expansion_cost <= 0 or time_to_expiry < 0:
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        if volatility < 0 or volatility > 5:  # 500% max volatility
            return jsonify({'error': 'Volatility must be between 0 and 5'}), 400
        
        if risk_free_rate < -0.5 or risk_free_rate > 1:  # -50% to 100%
            return jsonify({'error': 'Risk-free rate must be between -0.5 and 1'}), 400
        
        # Calculate expansion option
        result = real_options_engine.calculate_expansion_option(
            current_value=current_value,
            expansion_cost=expansion_cost,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            expansion_multiplier=expansion_multiplier
        )
        
        logger.info(f"Expansion option calculated successfully: {result['option_value']:.2f}")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Expansion option calculated successfully'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in expansion option calculation: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in expansion option calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/abandonment', methods=['POST'])
@cross_origin()
@require_auth
def calculate_abandonment_option():
    """Calculate abandonment option value"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['current_value', 'salvage_value', 'time_to_expiry', 
                         'volatility', 'risk_free_rate']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        current_value = float(data['current_value'])
        salvage_value = float(data['salvage_value'])
        time_to_expiry = float(data['time_to_expiry'])
        volatility = float(data['volatility'])
        risk_free_rate = float(data['risk_free_rate'])
        
        # Validate parameter ranges
        if current_value <= 0 or salvage_value < 0 or time_to_expiry < 0:
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        if volatility < 0 or volatility > 5:
            return jsonify({'error': 'Volatility must be between 0 and 5'}), 400
        
        if risk_free_rate < -0.5 or risk_free_rate > 1:
            return jsonify({'error': 'Risk-free rate must be between -0.5 and 1'}), 400
        
        # Calculate abandonment option
        result = real_options_engine.calculate_abandonment_option(
            current_value=current_value,
            salvage_value=salvage_value,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        logger.info(f"Abandonment option calculated successfully: {result['option_value']:.2f}")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Abandonment option calculated successfully'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in abandonment option calculation: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in abandonment option calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/timing', methods=['POST'])
@cross_origin()
@require_auth
def calculate_timing_option():
    """Calculate timing option value"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['project_value', 'investment_cost', 'time_horizon', 
                         'volatility', 'risk_free_rate']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        project_value = float(data['project_value'])
        investment_cost = float(data['investment_cost'])
        time_horizon = float(data['time_horizon'])
        volatility = float(data['volatility'])
        risk_free_rate = float(data['risk_free_rate'])
        
        # Validate parameter ranges
        if project_value <= 0 or investment_cost <= 0 or time_horizon < 0:
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        if volatility < 0 or volatility > 5:
            return jsonify({'error': 'Volatility must be between 0 and 5'}), 400
        
        if risk_free_rate < -0.5 or risk_free_rate > 1:
            return jsonify({'error': 'Risk-free rate must be between -0.5 and 1'}), 400
        
        # Calculate timing option
        result = real_options_engine.calculate_timing_option(
            project_value=project_value,
            investment_cost=investment_cost,
            time_horizon=time_horizon,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        logger.info(f"Timing option calculated successfully: {result['option_value']:.2f}")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Timing option calculated successfully'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in timing option calculation: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in timing option calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/compound', methods=['POST'])
@cross_origin()
@require_auth
def calculate_compound_option():
    """Calculate compound option value"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['underlying_value', 'exercise_prices', 'time_periods', 
                         'volatility', 'risk_free_rate']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        underlying_value = float(data['underlying_value'])
        exercise_prices = data['exercise_prices']
        time_periods = data['time_periods']
        volatility = float(data['volatility'])
        risk_free_rate = float(data['risk_free_rate'])
        
        # Validate parameter ranges
        if underlying_value <= 0:
            return jsonify({'error': 'Underlying value must be positive'}), 400
        
        if len(exercise_prices) != 2 or len(time_periods) != 2:
            return jsonify({'error': 'Compound options require exactly 2 exercise prices and 2 time periods'}), 400
        
        if any(price <= 0 for price in exercise_prices):
            return jsonify({'error': 'Exercise prices must be positive'}), 400
        
        if any(period < 0 for period in time_periods):
            return jsonify({'error': 'Time periods must be non-negative'}), 400
        
        if volatility < 0 or volatility > 5:
            return jsonify({'error': 'Volatility must be between 0 and 5'}), 400
        
        if risk_free_rate < -0.5 or risk_free_rate > 1:
            return jsonify({'error': 'Risk-free rate must be between -0.5 and 1'}), 400
        
        # Calculate compound option
        result = real_options_engine.calculate_compound_option(
            underlying_value=underlying_value,
            exercise_prices=exercise_prices,
            time_periods=time_periods,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        logger.info(f"Compound option calculated successfully: {result['total_value']:.2f}")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Compound option calculated successfully'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in compound option calculation: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in compound option calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/greeks', methods=['POST'])
@cross_origin()
@require_auth
def calculate_greeks():
    """Calculate option Greeks"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['underlying_price', 'volatility', 'time_to_expiry', 
                         'risk_free_rate']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        underlying_price = float(data['underlying_price'])
        volatility = float(data['volatility'])
        time_to_expiry = float(data['time_to_expiry'])
        risk_free_rate = float(data['risk_free_rate'])
        option_type = data.get('option_type', 'call')
        
        # Validate parameter ranges
        if underlying_price <= 0 or time_to_expiry < 0:
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        if volatility < 0 or volatility > 5:
            return jsonify({'error': 'Volatility must be between 0 and 5'}), 400
        
        if risk_free_rate < -0.5 or risk_free_rate > 1:
            return jsonify({'error': 'Risk-free rate must be between -0.5 and 1'}), 400
        
        if option_type not in ['call', 'put']:
            return jsonify({'error': 'Option type must be either "call" or "put"'}), 400
        
        # Calculate Greeks
        result = real_options_engine.calculate_greeks(
            option_value=0,  # Not used in the calculation
            underlying_price=underlying_price,
            volatility=volatility,
            time_to_expiry=time_to_expiry,
            risk_free_rate=risk_free_rate,
            option_type=option_type
        )
        
        logger.info(f"Greeks calculated successfully for {option_type} option")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'Greeks calculated successfully for {option_type} option'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in Greeks calculation: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in Greeks calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/volatility', methods=['POST'])
@cross_origin()
@require_auth
def estimate_volatility():
    """Estimate volatility from historical data"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'historical_data' not in data:
            return jsonify({'error': 'Missing required parameter: historical_data'}), 400
        
        # Extract parameters
        historical_data = data['historical_data']
        method = data.get('method', 'historical')
        
        # Validate historical data
        if not isinstance(historical_data, list) or len(historical_data) < 2:
            return jsonify({'error': 'Historical data must be a list with at least 2 values'}), 400
        
        if any(price <= 0 for price in historical_data):
            return jsonify({'error': 'All historical prices must be positive'}), 400
        
        if method not in ['historical', 'implied']:
            return jsonify({'error': 'Method must be either "historical" or "implied"'}), 400
        
        # Estimate volatility
        volatility = real_options_engine.estimate_volatility(
            historical_data=historical_data,
            method=method
        )
        
        logger.info(f"Volatility estimated successfully: {volatility:.4f}")
        
        return jsonify({
            'success': True,
            'result': {
                'volatility': volatility,
                'method': method,
                'data_points': len(historical_data)
            },
            'message': f'Volatility estimated successfully using {method} method'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in volatility estimation: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in volatility estimation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/sensitivity', methods=['POST'])
@cross_origin()
@require_auth
def run_sensitivity_analysis():
    """Run sensitivity analysis for option parameters"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['base_params', 'parameter', 'range_values']
        for param in required_params:
            if param not in data:
                return jsonify({'error': f'Missing required parameter: {param}'}), 400
        
        # Extract parameters
        base_params = data['base_params']
        parameter = data['parameter']
        range_values = data['range_values']
        
        # Validate base parameters
        if not isinstance(base_params, dict):
            return jsonify({'error': 'Base parameters must be a dictionary'}), 400
        
        if 'option_type' not in base_params:
            return jsonify({'error': 'Base parameters must include option_type'}), 400
        
        if parameter not in base_params:
            return jsonify({'error': f'Parameter {parameter} not found in base parameters'}), 400
        
        if not isinstance(range_values, list) or len(range_values) < 2:
            return jsonify({'error': 'Range values must be a list with at least 2 values'}), 400
        
        # Run sensitivity analysis
        result = real_options_engine.run_sensitivity_analysis(
            base_params=base_params,
            parameter=parameter,
            range_values=range_values
        )
        
        logger.info(f"Sensitivity analysis completed for parameter: {parameter}")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'Sensitivity analysis completed for parameter: {parameter}'
        })
        
    except ValueError as e:
        logger.error(f"ValueError in sensitivity analysis: {str(e)}")
        return jsonify({'error': f'Invalid parameter value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/scenarios', methods=['GET'])
@cross_origin()
@require_auth
def get_predefined_scenarios():
    """Get predefined real options scenarios"""
    try:
        scenarios = {
            'expansion_scenarios': [
                {
                    'name': 'Technology Startup Expansion',
                    'description': 'Expansion option for a technology startup',
                    'current_value': 1000000,
                    'expansion_cost': 500000,
                    'time_to_expiry': 2.0,
                    'volatility': 0.4,
                    'risk_free_rate': 0.05,
                    'expansion_multiplier': 2.5
                },
                {
                    'name': 'Manufacturing Plant Expansion',
                    'description': 'Expansion option for a manufacturing facility',
                    'current_value': 5000000,
                    'expansion_cost': 2000000,
                    'time_to_expiry': 3.0,
                    'volatility': 0.3,
                    'risk_free_rate': 0.04,
                    'expansion_multiplier': 1.8
                }
            ],
            'abandonment_scenarios': [
                {
                    'name': 'Oil Field Abandonment',
                    'description': 'Abandonment option for an oil field',
                    'current_value': 20000000,
                    'salvage_value': 5000000,
                    'time_to_expiry': 5.0,
                    'volatility': 0.5,
                    'risk_free_rate': 0.03
                },
                {
                    'name': 'Real Estate Development Abandonment',
                    'description': 'Abandonment option for a real estate project',
                    'current_value': 15000000,
                    'salvage_value': 8000000,
                    'time_to_expiry': 2.5,
                    'volatility': 0.35,
                    'risk_free_rate': 0.04
                }
            ],
            'timing_scenarios': [
                {
                    'name': 'R&D Project Timing',
                    'description': 'Timing option for an R&D project',
                    'project_value': 8000000,
                    'investment_cost': 3000000,
                    'time_horizon': 4.0,
                    'volatility': 0.45,
                    'risk_free_rate': 0.05
                },
                {
                    'name': 'Mining Project Timing',
                    'description': 'Timing option for a mining project',
                    'project_value': 50000000,
                    'investment_cost': 20000000,
                    'time_horizon': 6.0,
                    'volatility': 0.4,
                    'risk_free_rate': 0.03
                }
            ],
            'compound_scenarios': [
                {
                    'name': 'Pharmaceutical R&D',
                    'description': 'Compound option for pharmaceutical R&D',
                    'underlying_value': 10000000,
                    'exercise_prices': [2000000, 5000000],
                    'time_periods': [2.0, 4.0],
                    'volatility': 0.5,
                    'risk_free_rate': 0.04
                }
            ]
        }
        
        logger.info("Predefined scenarios retrieved successfully")
        
        return jsonify({
            'success': True,
            'result': scenarios,
            'message': 'Predefined scenarios retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving predefined scenarios: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/models', methods=['GET'])
@cross_origin()
@require_auth
def get_available_models():
    """Get available pricing models"""
    try:
        models = real_options_engine.get_available_models()
        model_info = {}
        
        for model_name in models:
            model_info[model_name] = real_options_engine.get_model_info(model_name)
        
        logger.info("Available models retrieved successfully")
        
        return jsonify({
            'success': True,
            'result': {
                'models': models,
                'model_info': model_info
            },
            'message': 'Available models retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving available models: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@real_options_bp.route('/api/real-options/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint for real options module"""
    try:
        # Test basic functionality
        test_params = {
            'current_value': 1000000,
            'expansion_cost': 500000,
            'time_to_expiry': 2.0,
            'volatility': 0.3,
            'risk_free_rate': 0.05
        }
        
        result = real_options_engine.calculate_expansion_option(**test_params)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'message': 'Real options module is operational',
            'test_result': result['option_value']
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'message': f'Real options module error: {str(e)}'
        }), 500 