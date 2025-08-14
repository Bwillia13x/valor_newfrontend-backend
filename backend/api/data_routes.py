"""
Data API routes for Valor IVX financial modeling platform.

This module provides RESTful endpoints for accessing financial data
from external providers with caching, validation, and error handling.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import asyncio
from functools import wraps

# from backend.auth import require_auth  # Commented out for now
# from backend.data import provider_manager, data_sanitizer, data_quality_checker  # Commented out for now
from backend.data.providers.base import DataProviderError, RateLimitError
from backend.circuit_breaker.circuit_breaker import circuit_breaker_manager
# from backend.security.api_key_manager import api_key_manager  # Commented out for now
# from backend.metrics import DATA_PROVIDER_REQUESTS_TOTAL, DATA_PROVIDER_DURATION_SECONDS  # Commented out for now
# from backend.utils.response_utils import success_response, error_response  # Commented out for now

# Create blueprint
data_bp = Blueprint('data', __name__, url_prefix='/api/data')

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(f(*args, **kwargs))
            return result
        finally:
            loop.close()
    return decorated_function

def track_data_provider_metrics(provider: str, data_type: str, status: str, duration: float):
    """Track data provider metrics"""
    if DATA_PROVIDER_REQUESTS_TOTAL:
        DATA_PROVIDER_REQUESTS_TOTAL.labels(
            provider=provider, 
            data_type=data_type, 
            status=status
        ).inc()
    
    if DATA_PROVIDER_DURATION_SECONDS:
        DATA_PROVIDER_DURATION_SECONDS.labels(
            provider=provider, 
            data_type=data_type
        ).observe(duration)

@data_bp.route('/stock/<symbol>', methods=['GET'])
@require_auth
@async_route
async def get_stock_price(symbol: str):
    """Get stock price data for a symbol"""
    start_time = datetime.now()
    
    try:
        # Parse query parameters
        date_str = request.args.get('date')
        provider = request.args.get('provider')
        
        # Parse date if provided
        target_date = None
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid date format. Use YYYY-MM-DD", 400)
        
        # Get stock price data
        data = await provider_manager.get_stock_price(symbol, target_date, provider)
        
        # Sanitize and validate data
        sanitized_data = data_sanitizer.sanitize_financial_data(data)
        quality_check = data_quality_checker.check_price_data_quality(sanitized_data.data)
        
        # Track metrics
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            sanitized_data.source, 
            'price', 
            'success', 
            duration
        )
        
        return success_response({
            'symbol': sanitized_data.symbol,
            'data': sanitized_data.data,
            'timestamp': sanitized_data.timestamp.isoformat(),
            'source': sanitized_data.source,
            'confidence': sanitized_data.confidence,
            'quality_check': quality_check
        })
        
    except DataProviderError as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'price', 
            'error', 
            duration
        )
        return error_response(f"Data provider error: {str(e)}", 503)
    except RateLimitError as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'price', 
            'rate_limited', 
            duration
        )
        return error_response(f"Rate limit exceeded: {str(e)}", 429)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'price', 
            'error', 
            duration
        )
        current_app.logger.error(f"Error getting stock price for {symbol}: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/financials/<symbol>', methods=['GET'])
@require_auth
@async_route
async def get_financial_statements(symbol: str):
    """Get financial statements for a symbol"""
    start_time = datetime.now()
    
    try:
        # Parse query parameters
        statement_type = request.args.get('type', 'income')
        provider = request.args.get('provider')
        
        if statement_type not in ['income', 'balance', 'cash_flow']:
            return error_response("Invalid statement type. Use: income, balance, cash_flow", 400)
        
        # Get financial statements
        statements = await provider_manager.get_financial_statements(symbol, statement_type, provider)
        
        # Sanitize and validate data
        sanitized_statements = []
        for statement in statements:
            sanitized = data_sanitizer.sanitize_financial_data(statement)
            quality_check = data_quality_checker.check_financial_statement_quality(sanitized.data)
            sanitized_statements.append({
                'symbol': sanitized.symbol,
                'data': sanitized.data,
                'timestamp': sanitized.timestamp.isoformat(),
                'source': sanitized.source,
                'confidence': sanitized.confidence,
                'quality_check': quality_check
            })
        
        # Track metrics
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            statements[0].source if statements else 'unknown', 
            f'financial_{statement_type}', 
            'success', 
            duration
        )
        
        return success_response({
            'symbol': symbol,
            'statement_type': statement_type,
            'statements': sanitized_statements
        })
        
    except DataProviderError as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            f'financial_{statement_type}', 
            'error', 
            duration
        )
        return error_response(f"Data provider error: {str(e)}", 503)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            f'financial_{statement_type}', 
            'error', 
            duration
        )
        current_app.logger.error(f"Error getting financial statements for {symbol}: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/company/<symbol>', methods=['GET'])
@require_auth
@async_route
async def get_company_info(symbol: str):
    """Get company information for a symbol"""
    start_time = datetime.now()
    
    try:
        # Parse query parameters
        provider = request.args.get('provider')
        
        # Get company info
        company_data = await provider_manager.get_company_info(symbol, provider)
        
        # Sanitize data
        sanitized_data = data_sanitizer.sanitize_financial_data(company_data)
        
        # Track metrics
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            sanitized_data.source, 
            'company_info', 
            'success', 
            duration
        )
        
        return success_response({
            'symbol': sanitized_data.symbol,
            'data': sanitized_data.data,
            'timestamp': sanitized_data.timestamp.isoformat(),
            'source': sanitized_data.source,
            'confidence': sanitized_data.confidence
        })
        
    except DataProviderError as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'company_info', 
            'error', 
            duration
        )
        return error_response(f"Data provider error: {str(e)}", 503)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'company_info', 
            'error', 
            duration
        )
        current_app.logger.error(f"Error getting company info for {symbol}: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/search', methods=['GET'])
@require_auth
@async_route
async def search_symbols():
    """Search for symbols by company name or ticker"""
    start_time = datetime.now()
    
    try:
        # Parse query parameters
        query = request.args.get('q')
        provider = request.args.get('provider')
        
        if not query:
            return error_response("Query parameter 'q' is required", 400)
        
        # Search symbols
        results = await provider_manager.search_symbols(query, provider)
        
        # Track metrics
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'search', 
            'success', 
            duration
        )
        
        return success_response({
            'query': query,
            'results': results
        })
        
    except DataProviderError as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'search', 
            'error', 
            duration
        )
        return error_response(f"Data provider error: {str(e)}", 503)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'search', 
            'error', 
            duration
        )
        current_app.logger.error(f"Error searching symbols for '{query}': {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/batch/prices', methods=['POST'])
@require_auth
@async_route
async def batch_get_prices():
    """Get prices for multiple symbols concurrently"""
    start_time = datetime.now()
    
    try:
        # Parse request body
        data = request.get_json()
        if not data or 'symbols' not in data:
            return error_response("Request body must contain 'symbols' array", 400)
        
        symbols = data['symbols']
        date_str = data.get('date')
        provider = data.get('provider')
        
        if not isinstance(symbols, list) or len(symbols) == 0:
            return error_response("Symbols must be a non-empty array", 400)
        
        # Parse date if provided
        target_date = None
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid date format. Use YYYY-MM-DD", 400)
        
        # Get batch prices
        results = await provider_manager.batch_get_prices(symbols, target_date)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'symbol': symbols[i],
                    'error': str(result),
                    'success': False
                })
            else:
                sanitized = data_sanitizer.sanitize_financial_data(result)
                processed_results.append({
                    'symbol': sanitized.symbol,
                    'data': sanitized.data,
                    'timestamp': sanitized.timestamp.isoformat(),
                    'source': sanitized.source,
                    'confidence': sanitized.confidence,
                    'success': True
                })
        
        # Track metrics
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            provider or 'unknown', 
            'batch_prices', 
            'success', 
            duration
        )
        
        return success_response({
            'symbols': symbols,
            'results': processed_results
        })
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        track_data_provider_metrics(
            'unknown', 
            'batch_prices', 
            'error', 
            duration
        )
        current_app.logger.error(f"Error in batch price request: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/providers/status', methods=['GET'])
@require_auth
def get_provider_status():
    """Get status of all data providers"""
    try:
        status = provider_manager.get_provider_status()
        return success_response({
            'providers': status,
            'available_providers': provider_manager.get_available_providers()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting provider status: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/circuit-breakers', methods=['GET'])
@require_auth
def get_circuit_breakers():
    """Get status of all circuit breakers"""
    try:
        status = circuit_breaker_manager.get_all_status()
        return success_response({
            'circuit_breakers': status
        })
    except Exception as e:
        current_app.logger.error(f"Error getting circuit breaker status: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/circuit-breakers/<name>/reset', methods=['POST'])
@require_auth
def reset_circuit_breaker(name: str):
    """Manually reset a circuit breaker"""
    try:
        circuit_breaker_manager.reset_circuit(name)
        return success_response({
            'message': f'Circuit breaker {name} reset successfully'
        })
    except Exception as e:
        current_app.logger.error(f"Error resetting circuit breaker {name}: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/api-keys/status', methods=['GET'])
@require_auth
def get_api_key_status():
    """Get status of all API keys"""
    try:
        status = api_key_manager.get_key_status()
        return success_response({
            'api_keys': status
        })
    except Exception as e:
        current_app.logger.error(f"Error getting API key status: {str(e)}")
        return error_response("Internal server error", 500)

@data_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for data layer"""
    try:
        # Check if providers are available
        providers = provider_manager.get_available_providers()
        
        # Check circuit breaker status
        circuit_breakers = circuit_breaker_manager.get_all_status()
        
        # Check API key status
        api_keys = api_key_manager.get_key_status()
        
        return success_response({
            'status': 'healthy',
            'providers_available': len(providers),
            'circuit_breakers': len(circuit_breakers),
            'api_keys': len(api_keys)
        })
    except Exception as e:
        current_app.logger.error(f"Data layer health check failed: {str(e)}")
        return error_response("Data layer unhealthy", 503) 