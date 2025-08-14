"""
Credit Risk API Routes
Handles credit risk modeling endpoints
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
import traceback
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.credit_risk import CreditRiskValuation
from utils.auth_utils import require_auth
from utils.response_utils import create_response, create_error_response

logger = logging.getLogger(__name__)

# Create Blueprint
credit_risk_bp = Blueprint('credit_risk', __name__)

# Initialize credit risk model
credit_risk_model = CreditRiskValuation()

@credit_risk_bp.route('/api/credit-risk/merton-pd', methods=['POST'])
@cross_origin()
@require_auth
def calculate_merton_pd():
    """Calculate probability of default using Merton model"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['asset_value', 'debt_value', 'asset_volatility', 
                         'risk_free_rate', 'time_to_maturity']
        
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Extract parameters
        asset_value = float(data['asset_value'])
        debt_value = float(data['debt_value'])
        asset_volatility = float(data['asset_volatility'])
        risk_free_rate = float(data['risk_free_rate'])
        time_to_maturity = float(data['time_to_maturity'])
        
        # Calculate Merton PD
        result = credit_risk_model.calculate_merton_pd(
            asset_value, debt_value, asset_volatility, risk_free_rate, time_to_maturity
        )
        
        return create_response("Merton PD calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in Merton PD calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in Merton PD calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/kmv-pd', methods=['POST'])
@cross_origin()
@require_auth
def calculate_kmv_pd():
    """Calculate probability of default using KMV model"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['asset_value', 'debt_value', 'asset_volatility', 
                         'risk_free_rate', 'time_to_maturity']
        
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Extract parameters
        asset_value = float(data['asset_value'])
        debt_value = float(data['debt_value'])
        asset_volatility = float(data['asset_volatility'])
        risk_free_rate = float(data['risk_free_rate'])
        time_to_maturity = float(data['time_to_maturity'])
        default_threshold = float(data.get('default_threshold', 0.5))
        
        # Calculate KMV PD
        result = credit_risk_model.calculate_kmv_pd(
            asset_value, debt_value, asset_volatility, risk_free_rate, 
            time_to_maturity, default_threshold
        )
        
        return create_response("KMV PD calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in KMV PD calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in KMV PD calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/portfolio', methods=['POST'])
@cross_origin()
@require_auth
def calculate_portfolio_risk():
    """Calculate portfolio-level credit risk"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        
        # Validate portfolio data structure
        for asset in portfolio_data:
            if 'exposure' not in asset or 'pd' not in asset:
                return create_error_response("Each asset must have 'exposure' and 'pd' fields", 400)
        
        # Calculate portfolio risk
        result = credit_risk_model.calculate_portfolio_risk(portfolio_data)
        
        return create_response("Portfolio risk calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in portfolio risk calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in portfolio risk calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/credit-metrics-var', methods=['POST'])
@cross_origin()
@require_auth
def calculate_credit_metrics_var():
    """Calculate Credit VaR using CreditMetrics"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        confidence_level = float(data.get('confidence_level', 0.99))
        
        # Validate portfolio data structure
        for asset in portfolio_data:
            required_fields = ['exposure', 'rating']
            for field in required_fields:
                if field not in asset:
                    return create_error_response(f"Each asset must have '{field}' field", 400)
        
        # Calculate Credit VaR
        result = credit_risk_model.calculate_credit_metrics_var(portfolio_data, confidence_level)
        
        return create_response("Credit VaR calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in Credit VaR calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in Credit VaR calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/asset-estimation', methods=['POST'])
@cross_origin()
@require_auth
def estimate_asset_parameters():
    """Estimate asset value and volatility from equity data"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['equity_value', 'equity_volatility', 'debt_value', 
                         'risk_free_rate', 'time_to_maturity']
        
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Extract parameters
        equity_value = float(data['equity_value'])
        equity_volatility = float(data['equity_volatility'])
        debt_value = float(data['debt_value'])
        risk_free_rate = float(data['risk_free_rate'])
        time_to_maturity = float(data['time_to_maturity'])
        
        # Estimate asset parameters
        result = credit_risk_model.estimate_asset_parameters(
            equity_value, equity_volatility, debt_value, risk_free_rate, time_to_maturity
        )
        
        return create_response("Asset parameters estimated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in asset parameter estimation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in asset parameter estimation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/credit-spread', methods=['POST'])
@cross_origin()
@require_auth
def calculate_credit_spread():
    """Calculate credit spread"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['risk_free_rate', 'pd', 'lgd', 'maturity']
        
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Extract parameters
        risk_free_rate = float(data['risk_free_rate'])
        pd = float(data['pd'])
        lgd = float(data['lgd'])
        maturity = float(data['maturity'])
        
        # Calculate credit spread
        credit_spread = credit_risk_model.calculate_credit_spread(
            risk_free_rate, pd, lgd, maturity
        )
        
        result = {
            'credit_spread': credit_spread,
            'risk_free_rate': risk_free_rate,
            'probability_of_default': pd,
            'loss_given_default': lgd,
            'maturity': maturity
        }
        
        return create_response("Credit spread calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in credit spread calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in credit spread calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/rating/train', methods=['POST'])
@cross_origin()
@require_auth
def train_rating_model():
    """Train internal rating model"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'training_data' not in data:
            return create_error_response("Missing training_data", 400)
        
        training_data = data['training_data']
        model_type = data.get('model_type', 'logistic')
        
        # Convert to DataFrame (simplified - in practice you'd handle this properly)
        import pandas as pd
        df = pd.DataFrame(training_data)
        
        # Train rating model
        result = credit_risk_model.train_rating_model(df, model_type)
        
        return create_response("Rating model trained successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in rating model training: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in rating model training: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/rating/predict', methods=['POST'])
@cross_origin()
@require_auth
def predict_credit_rating():
    """Predict credit rating using trained model"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'financial_data' not in data:
            return create_error_response("Missing financial_data", 400)
        
        financial_data = data['financial_data']
        trained_model = data.get('trained_model', {})
        
        # Predict credit rating
        result = credit_risk_model.predict_credit_rating(financial_data, trained_model)
        
        return create_response("Credit rating predicted successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in credit rating prediction: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in credit rating prediction: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/stress-test', methods=['POST'])
@cross_origin()
@require_auth
def run_credit_stress_test():
    """Run credit risk stress testing"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'portfolio_data' not in data:
            return create_error_response("Missing portfolio_data", 400)
        
        portfolio_data = data['portfolio_data']
        stress_scenarios = data.get('stress_scenarios', [])
        
        # If no scenarios provided, use default scenarios
        if not stress_scenarios:
            stress_scenarios = [
                {
                    'name': 'Severe Recession',
                    'pd_stress_factor': 3.0,
                    'lgd_stress_factor': 1.5
                },
                {
                    'name': 'Market Crisis',
                    'pd_stress_factor': 2.5,
                    'lgd_stress_factor': 1.3
                }
            ]
        
        # Run stress test
        result = credit_risk_model.run_stress_test(portfolio_data, stress_scenarios)
        
        return create_response("Credit stress test completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in credit stress testing: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in credit stress testing: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/models', methods=['GET'])
@cross_origin()
@require_auth
def get_available_models():
    """Get available credit risk models"""
    try:
        models = {
            'available_models': [
                {
                    'name': 'Merton Model',
                    'description': 'Structural model for credit risk based on option pricing theory',
                    'parameters': ['asset_value', 'debt_value', 'asset_volatility', 'risk_free_rate', 'time_to_maturity'],
                    'outputs': ['probability_of_default', 'distance_to_default', 'expected_loss', 'credit_spread']
                },
                {
                    'name': 'KMV Model',
                    'description': 'Enhanced structural model with empirical default thresholds',
                    'parameters': ['asset_value', 'debt_value', 'asset_volatility', 'risk_free_rate', 'time_to_maturity', 'default_threshold'],
                    'outputs': ['probability_of_default', 'expected_default_frequency', 'distance_to_default', 'expected_loss']
                },
                {
                    'name': 'CreditMetrics',
                    'description': 'Portfolio credit risk model based on rating transitions',
                    'parameters': ['portfolio_data', 'confidence_level'],
                    'outputs': ['credit_var', 'expected_portfolio_value', 'unexpected_loss']
                }
            ],
            'portfolio_analysis': [
                'portfolio_pd',
                'portfolio_expected_loss',
                'portfolio_unexpected_loss'
            ],
            'stress_testing': [
                'pd_stress_factor',
                'lgd_stress_factor'
            ]
        }
        
        return create_response("Available models retrieved successfully", models)
        
    except Exception as e:
        logger.error(f"Error retrieving available models: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@credit_risk_bp.route('/api/credit-risk/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    try:
        import pandas as pd
        return jsonify({
            'status': 'healthy',
            'service': 'credit_risk',
            'models_loaded': True,
            'timestamp': pd.Timestamp.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'credit_risk',
            'error': str(e)
        }), 500 