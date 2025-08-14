"""
Data layer module for Valor IVX financial modeling platform.

This module provides:
- Data provider abstraction layer
- Circuit breaker pattern implementation
- Data validation and sanitization
- API key management
- Retry mechanisms with exponential backoff
"""

from .provider_manager import provider_manager
from .validation import data_sanitizer
from .providers.base import FinancialData, DataRequest, DataProviderError

__all__ = [
    'provider_manager',
    'data_sanitizer',
    'FinancialData',
    'DataRequest',
    'DataProviderError'
] 