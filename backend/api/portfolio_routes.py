"""
Portfolio Analysis API Routes
Handles portfolio optimization and analysis endpoints
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

from ml_models.portfolio_optimizer import PortfolioOptimizer
from utils.auth_utils import require_auth
from utils.response_utils import create_response, create_error_response

logger = logging.getLogger(__name__)

# Create Blueprint
portfolio_bp = Blueprint('portfolio', __name__)

# Initialize portfolio optimizer
portfolio_optimizer = PortfolioOptimizer()

@portfolio_bp.route('/api/portfolio/optimize/mean-variance', methods=['POST'])
@cross_origin()
@require_auth
def optimize_mean_variance():
    """Mean-variance portfolio optimization"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to DataFrame
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        risk_free_rate = float(data.get('risk_free_rate', 0.02))
        target_return = data.get('target_return')
        target_volatility = data.get('target_volatility')
        constraints = data.get('constraints', {})
        
        if target_return is not None:
            target_return = float(target_return)
        if target_volatility is not None:
            target_volatility = float(target_volatility)
        
        # Run optimization
        result = portfolio_optimizer.optimize_mean_variance(
            returns_df, risk_free_rate, target_return, target_volatility, constraints
        )
        
        return create_response("Mean-variance optimization completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in mean-variance optimization: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in mean-variance optimization: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/optimize/black-litterman', methods=['POST'])
@cross_origin()
@require_auth
def optimize_black_litterman():
    """Black-Litterman portfolio optimization"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['market_caps', 'returns', 'views']
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Convert data to appropriate formats
        market_caps = pd.Series(data['market_caps'])
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        views = data['views']
        view_confidences = data.get('view_confidences', {})
        
        # Extract optional parameters
        risk_aversion = float(data.get('risk_aversion', 2.5))
        tau = float(data.get('tau', 0.05))
        
        # Run optimization
        result = portfolio_optimizer.optimize_black_litterman(
            market_caps, returns_df, views, view_confidences, risk_aversion, tau
        )
        
        return create_response("Black-Litterman optimization completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in Black-Litterman optimization: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in Black-Litterman optimization: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/optimize/risk-parity', methods=['POST'])
@cross_origin()
@require_auth
def optimize_risk_parity():
    """Risk parity portfolio optimization"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to DataFrame
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        target_volatility = data.get('target_volatility')
        if target_volatility is not None:
            target_volatility = float(target_volatility)
        
        # Run optimization
        result = portfolio_optimizer.optimize_risk_parity(returns_df, target_volatility)
        
        return create_response("Risk parity optimization completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in risk parity optimization: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in risk parity optimization: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/optimize/max-sharpe', methods=['POST'])
@cross_origin()
@require_auth
def optimize_max_sharpe():
    """Maximum Sharpe ratio portfolio optimization"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to DataFrame
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        risk_free_rate = float(data.get('risk_free_rate', 0.02))
        constraints = data.get('constraints', {})
        
        # Run optimization
        result = portfolio_optimizer.optimize_max_sharpe(returns_df, risk_free_rate, constraints)
        
        return create_response("Maximum Sharpe ratio optimization completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in max Sharpe optimization: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in max Sharpe optimization: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/efficient-frontier', methods=['POST'])
@cross_origin()
@require_auth
def calculate_efficient_frontier():
    """Calculate efficient frontier"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to DataFrame
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        risk_free_rate = float(data.get('risk_free_rate', 0.02))
        num_portfolios = int(data.get('num_portfolios', 100))
        
        # Calculate efficient frontier
        result = portfolio_optimizer.calculate_efficient_frontier(
            returns_df, risk_free_rate, num_portfolios
        )
        
        return create_response("Efficient frontier calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in efficient frontier calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in efficient frontier calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/expected-returns', methods=['POST'])
@cross_origin()
@require_auth
def estimate_expected_returns():
    """Estimate expected returns"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to DataFrame
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        method = data.get('method', 'historical')
        
        # Estimate expected returns
        expected_returns = portfolio_optimizer.estimate_expected_returns(returns_df, method)
        
        result = {
            'expected_returns': expected_returns.to_dict(),
            'method': method,
            'assets': expected_returns.index.tolist()
        }
        
        return create_response("Expected returns estimated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in expected returns estimation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in expected returns estimation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/covariance-matrix', methods=['POST'])
@cross_origin()
@require_auth
def estimate_covariance_matrix():
    """Estimate covariance matrix"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'returns' not in data:
            return create_error_response("Missing returns data", 400)
        
        # Convert returns to DataFrame
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        method = data.get('method', 'sample')
        
        # Estimate covariance matrix
        cov_matrix = portfolio_optimizer.estimate_covariance_matrix(returns_df, method)
        
        result = {
            'covariance_matrix': cov_matrix.to_dict(),
            'method': method,
            'assets': cov_matrix.index.tolist()
        }
        
        return create_response("Covariance matrix estimated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in covariance matrix estimation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in covariance matrix estimation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/metrics', methods=['POST'])
@cross_origin()
@require_auth
def calculate_portfolio_metrics():
    """Calculate portfolio performance metrics"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['weights', 'returns']
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Convert data to appropriate formats
        weights = np.array(data['weights'])
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        risk_free_rate = float(data.get('risk_free_rate', 0.02))
        
        # Calculate portfolio metrics
        metrics = portfolio_optimizer.calculate_portfolio_metrics(
            weights, returns_df, risk_free_rate
        )
        
        return create_response("Portfolio metrics calculated successfully", metrics)
        
    except ValueError as e:
        logger.error(f"Validation error in portfolio metrics calculation: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in portfolio metrics calculation: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/rebalance', methods=['POST'])
@cross_origin()
@require_auth
def rebalance_portfolio():
    """Calculate optimal portfolio rebalancing"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['current_weights', 'target_weights']
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Convert weights to numpy arrays
        current_weights = np.array(data['current_weights'])
        target_weights = np.array(data['target_weights'])
        
        # Extract optional parameters
        transaction_costs = float(data.get('transaction_costs', 0.001))
        
        # Calculate rebalancing
        result = portfolio_optimizer.rebalance_portfolio(
            current_weights, target_weights, transaction_costs
        )
        
        return create_response("Portfolio rebalancing calculated successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in portfolio rebalancing: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in portfolio rebalancing: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/backtest', methods=['POST'])
@cross_origin()
@require_auth
def run_portfolio_backtest():
    """Run portfolio backtest"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['weights', 'returns']
        for param in required_params:
            if param not in data:
                return create_error_response(f"Missing required parameter: {param}", 400)
        
        # Convert data to appropriate formats
        weights = np.array(data['weights'])
        returns_data = data['returns']
        returns_df = pd.DataFrame(returns_data)
        
        # Extract optional parameters
        rebalance_frequency = data.get('rebalance_frequency', 'monthly')
        transaction_costs = float(data.get('transaction_costs', 0.001))
        
        # Run backtest (simplified implementation)
        portfolio_returns = np.dot(returns_df, weights)
        cumulative_returns = (1 + portfolio_returns).cumprod()
        
        # Calculate backtest metrics
        total_return = cumulative_returns.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(returns_df)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Calculate drawdown
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        result = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'portfolio_returns': portfolio_returns.tolist(),
            'cumulative_returns': cumulative_returns.tolist(),
            'rebalance_frequency': rebalance_frequency,
            'transaction_costs': transaction_costs
        }
        
        return create_response("Portfolio backtest completed successfully", result)
        
    except ValueError as e:
        logger.error(f"Validation error in portfolio backtest: {e}")
        return create_error_response(f"Invalid parameter value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in portfolio backtest: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/optimization-methods', methods=['GET'])
@cross_origin()
@require_auth
def get_optimization_methods():
    """Get available portfolio optimization methods"""
    try:
        methods = {
            'optimization_methods': [
                {
                    'name': 'Mean-Variance Optimization',
                    'description': 'Classical Markowitz portfolio optimization',
                    'parameters': ['returns', 'risk_free_rate', 'target_return', 'target_volatility', 'constraints'],
                    'outputs': ['weights', 'expected_return', 'volatility', 'sharpe_ratio']
                },
                {
                    'name': 'Black-Litterman Model',
                    'description': 'Bayesian portfolio optimization incorporating views',
                    'parameters': ['market_caps', 'returns', 'views', 'view_confidences', 'risk_aversion', 'tau'],
                    'outputs': ['weights', 'posterior_returns', 'equilibrium_returns']
                },
                {
                    'name': 'Risk Parity',
                    'description': 'Equal risk contribution portfolio optimization',
                    'parameters': ['returns', 'target_volatility'],
                    'outputs': ['weights', 'volatility', 'risk_contributions']
                },
                {
                    'name': 'Maximum Sharpe Ratio',
                    'description': 'Optimize for maximum risk-adjusted returns',
                    'parameters': ['returns', 'risk_free_rate', 'constraints'],
                    'outputs': ['weights', 'expected_return', 'volatility', 'sharpe_ratio']
                }
            ],
            'analysis_tools': [
                'efficient_frontier',
                'expected_returns_estimation',
                'covariance_matrix_estimation',
                'portfolio_metrics',
                'portfolio_rebalancing',
                'portfolio_backtest'
            ],
            'estimation_methods': {
                'expected_returns': ['historical', 'capm', 'factor_model'],
                'covariance_matrix': ['sample', 'shrinkage', 'factor_model']
            }
        }
        
        return create_response("Optimization methods retrieved successfully", methods)
        
    except Exception as e:
        logger.error(f"Error retrieving optimization methods: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@portfolio_bp.route('/api/portfolio/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'portfolio_analysis',
            'models_loaded': True,
            'timestamp': pd.Timestamp.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'portfolio_analysis',
            'error': str(e)
        }), 500 