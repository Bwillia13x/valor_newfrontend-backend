"""
Comprehensive Error Handling Module

Provides structured error handling, logging, and correlation ID tracking
for financial applications with proper security considerations.
"""

import logging
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from flask import g, request, jsonify
import functools

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    FINANCIAL_CALCULATION = "financial_calculation"
    DATA_INTEGRITY = "data_integrity"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"

class FinancialError(Exception):
    """Base exception for financial application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or "An error occurred while processing your request"
        self.correlation_id = correlation_id or getattr(g, 'request_id', str(uuid.uuid4()))
        self.timestamp = datetime.now(timezone.utc)
        
        super().__init__(self.message)

class ValidationError(FinancialError):
    """Validation-specific error"""
    
    def __init__(self, field: str, value: Any, message: str, **kwargs):
        self.field = field
        self.value = value
        super().__init__(
            message=f"Validation error for {field}: {message}",
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details={"field": field, "value": str(value)[:100]},  # Limit value length for security
            user_message=f"Invalid {field}: {message}",
            **kwargs
        )

class AuthenticationError(FinancialError):
    """Authentication-specific error"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            user_message="Authentication failed. Please check your credentials.",
            **kwargs
        )

class AuthorizationError(FinancialError):
    """Authorization-specific error"""
    
    def __init__(self, message: str = "Access denied", resource: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHZ_ERROR",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            details={"resource": resource} if resource else {},
            user_message="You don't have permission to access this resource.",
            **kwargs
        )

class FinancialCalculationError(FinancialError):
    """Financial calculation-specific error"""
    
    def __init__(self, calculation_type: str, message: str, **kwargs):
        self.calculation_type = calculation_type
        super().__init__(
            message=f"Financial calculation error ({calculation_type}): {message}",
            error_code="CALC_ERROR",
            category=ErrorCategory.FINANCIAL_CALCULATION,
            severity=ErrorSeverity.HIGH,
            details={"calculation_type": calculation_type},
            user_message=f"Error in {calculation_type} calculation. Please check your inputs.",
            **kwargs
        )

class ExternalAPIError(FinancialError):
    """External API-specific error"""
    
    def __init__(self, provider: str, message: str, **kwargs):
        self.provider = provider
        super().__init__(
            message=f"External API error ({provider}): {message}",
            error_code="API_ERROR",
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            details={"provider": provider},
            user_message="Unable to retrieve external data. Please try again later.",
            **kwargs
        )

class ErrorLogger:
    """Structured error logging with correlation IDs"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_error(self, error: FinancialError, request_context: Optional[Dict] = None):
        """Log structured error with context"""
        
        # Sanitize request context to avoid logging sensitive data
        safe_context = self._sanitize_context(request_context or {})
        
        log_data = {
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "correlation_id": error.correlation_id,
            "timestamp": error.timestamp.isoformat(),
            "message": error.message,
            "details": error.details,
            "request_context": safe_context
        }
        
        # Log at appropriate level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error", extra=log_data)
        else:
            self.logger.info("Low severity error", extra=log_data)
    
    def _sanitize_context(self, context: Dict) -> Dict:
        """Remove sensitive information from request context"""
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'auth', 'authorization',
            'ssn', 'social', 'credit_card', 'cc_number', 'account_number'
        }
        
        sanitized = {}
        for key, value in context.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 200:
                sanitized[key] = value[:200] + "..."
            else:
                sanitized[key] = value
        
        return sanitized

class ErrorHandler:
    """Central error handler for Flask applications"""
    
    def __init__(self, app=None):
        self.logger = ErrorLogger()
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handling for Flask app"""
        app.register_error_handler(FinancialError, self.handle_financial_error)
        app.register_error_handler(ValidationError, self.handle_validation_error)
        app.register_error_handler(AuthenticationError, self.handle_auth_error)
        app.register_error_handler(AuthorizationError, self.handle_authz_error)
        app.register_error_handler(Exception, self.handle_generic_error)
    
    def handle_financial_error(self, error: FinancialError):
        """Handle FinancialError instances"""
        request_context = self._get_request_context()
        self.logger.log_error(error, request_context)
        
        return jsonify({
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.user_message,
                "correlation_id": error.correlation_id,
                "category": error.category.value,
                "timestamp": error.timestamp.isoformat()
            }
        }), self._get_http_status(error)
    
    def handle_validation_error(self, error: ValidationError):
        """Handle ValidationError instances"""
        request_context = self._get_request_context()
        self.logger.log_error(error, request_context)
        
        return jsonify({
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.user_message,
                "field": error.field,
                "correlation_id": error.correlation_id,
                "timestamp": error.timestamp.isoformat()
            }
        }), 400
    
    def handle_auth_error(self, error: AuthenticationError):
        """Handle AuthenticationError instances"""
        request_context = self._get_request_context()
        self.logger.log_error(error, request_context)
        
        return jsonify({
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.user_message,
                "correlation_id": error.correlation_id,
                "timestamp": error.timestamp.isoformat()
            }
        }), 401
    
    def handle_authz_error(self, error: AuthorizationError):
        """Handle AuthorizationError instances"""
        request_context = self._get_request_context()
        self.logger.log_error(error, request_context)
        
        return jsonify({
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.user_message,
                "correlation_id": error.correlation_id,
                "timestamp": error.timestamp.isoformat()
            }
        }), 403
    
    def handle_generic_error(self, error: Exception):
        """Handle unexpected generic errors"""
        correlation_id = getattr(g, 'request_id', str(uuid.uuid4()))
        
        # Create a generic FinancialError for logging
        financial_error = FinancialError(
            message=str(error),
            error_code="INTERNAL_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            correlation_id=correlation_id,
            details={"traceback": traceback.format_exc()}
        )
        
        request_context = self._get_request_context()
        self.logger.log_error(financial_error, request_context)
        
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }), 500
    
    def _get_request_context(self) -> Dict:
        """Extract safe request context for logging"""
        if not request:
            return {}
        
        return {
            "method": request.method,
            "url": request.url,
            "endpoint": request.endpoint,
            "user_agent": request.headers.get('User-Agent', ''),
            "ip_address": request.remote_addr,
            "tenant_id": getattr(g, 'tenant_id', None),
            "user_id": getattr(g, 'user_id', None)
        }
    
    def _get_http_status(self, error: FinancialError) -> int:
        """Get appropriate HTTP status code for error"""
        status_map = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.FINANCIAL_CALCULATION: 422,
            ErrorCategory.DATA_INTEGRITY: 422,
            ErrorCategory.EXTERNAL_API: 502,
            ErrorCategory.DATABASE: 503,
            ErrorCategory.SYSTEM: 500,
            ErrorCategory.BUSINESS_LOGIC: 422
        }
        
        return status_map.get(error.category, 500)

def error_handler(func):
    """Decorator to wrap functions with error handling"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FinancialError:
            raise  # Re-raise FinancialError instances to be handled by Flask
        except Exception as e:
            # Convert generic exceptions to FinancialError
            correlation_id = getattr(g, 'request_id', str(uuid.uuid4()))
            raise FinancialError(
                message=str(e),
                error_code="UNEXPECTED_ERROR",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                correlation_id=correlation_id
            )
    
    return wrapper

# Global error handler instance
error_handler_instance = ErrorHandler()