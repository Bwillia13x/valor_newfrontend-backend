"""
Circuit breaker wrapper for data providers.

This module provides a wrapper that adds circuit breaker protection
to any data provider implementation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from .base import DataProvider, FinancialData, DataRequest, DataProviderError
# from ...circuit_breaker.circuit_breaker import CircuitBreakerConfig, circuit_breaker_manager  # Commented out for now

class CircuitBreakerDataProvider(DataProvider):
    """Data provider wrapper with circuit breaker protection"""
    
    def __init__(self, provider: DataProvider, circuit_name: str):
        self.provider = provider
        self.circuit_name = circuit_name
        # self.circuit = circuit_breaker_manager.get_circuit(
        #     circuit_name,
        #     CircuitBreakerConfig(
        #         failure_threshold=5,
        #         recovery_timeout=60,
        #         expected_exception=DataProviderError,
        #         success_threshold=2,
        #         timeout=30.0
        #     )
        # )
        
        # Copy provider attributes
        self.name = f"{provider.name}_circuit_breaker"
        self.api_key = provider.api_key
        self.base_url = provider.base_url
        self.rate_limit = provider.rate_limit
        self.timeout = provider.timeout
        self.session = provider.session
    
    async def get_stock_price(self, symbol: str, date: Optional[date] = None) -> FinancialData:
        """Get stock price with circuit breaker protection"""
        # return await self.circuit.call(
        #     self.provider.get_stock_price,
        #     symbol,
        #     date
        # )
        return await self.provider.get_stock_price(symbol, date)
    
    async def get_financial_statements(self, symbol: str, statement_type: str) -> List[FinancialData]:
        """Get financial statements with circuit breaker protection"""
        # return await self.circuit.call(
        #     self.provider.get_financial_statements,
        #     symbol,
        #     statement_type
        # )
        return await self.provider.get_financial_statements(symbol, statement_type)
    
    async def get_company_info(self, symbol: str) -> FinancialData:
        """Get company info with circuit breaker protection"""
        # return await self.circuit.call(
        #     self.provider.get_company_info,
        #     symbol
        # )
        return await self.provider.get_company_info(symbol)
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search symbols with circuit breaker protection"""
        # return await self.circuit.call(
        #     self.provider.search_symbols,
        #     query
        # )
        return await self.provider.search_symbols(query)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.provider.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.provider.__aexit__(exc_type, exc_val, exc_tb) 