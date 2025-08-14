"""
Base data provider interface for financial data sources.

This module defines the abstract base classes and data structures
for all financial data providers in the Valor IVX platform.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date
import asyncio
import aiohttp
# from backend.cache import cache_result  # Commented out for now

@dataclass
class FinancialData:
    """Standardized financial data structure"""
    symbol: str
    data_type: str  # 'price', 'financials', 'ratios', 'news'
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]

@dataclass
class DataRequest:
    """Standardized data request structure"""
    symbols: List[str]
    data_types: List[str]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    frequency: str = 'daily'  # daily, weekly, monthly, quarterly
    fields: Optional[List[str]] = None

class DataProvider(ABC):
    """Abstract base class for all data providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', self.__class__.__name__)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.rate_limit = config.get('rate_limit', 100)  # requests per minute
        self.timeout = config.get('timeout', 30)
        self.session = None
    
    @abstractmethod
    async def get_stock_price(self, symbol: str, date: Optional[date] = None) -> FinancialData:
        """Get stock price data"""
        pass
    
    @abstractmethod
    async def get_financial_statements(self, symbol: str, statement_type: str) -> List[FinancialData]:
        """Get financial statements (income, balance, cash flow)"""
        pass
    
    @abstractmethod
    async def get_company_info(self, symbol: str) -> FinancialData:
        """Get company information and metadata"""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols by company name or ticker"""
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _validate_response(self, response: aiohttp.ClientResponse) -> bool:
        """Validate API response"""
        if response.status >= 400:
            raise DataProviderError(f"API error: {response.status}")
        return True
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object"""
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {date_str}")

class DataProviderError(Exception):
    """Custom exception for data provider errors"""
    pass

class RateLimitError(DataProviderError):
    """Exception for rate limit violations"""
    pass

class DataValidationError(DataProviderError):
    """Exception for data validation failures"""
    pass 