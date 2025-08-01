"""
Circuit breaker pattern implementation for external API calls.

This module provides circuit breaker functionality to prevent cascading failures
and improve system resilience when calling external APIs.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerManager, CircuitBreakerConfig, CircuitBreakerOpenError

__all__ = [
    'CircuitBreaker',
    'CircuitBreakerManager', 
    'CircuitBreakerConfig',
    'CircuitBreakerOpenError'
] 