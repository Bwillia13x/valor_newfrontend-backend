"""
Alpha Vantage API provider implementation.

This module provides a complete implementation of the Alpha Vantage API
with rate limiting, error handling, and data normalization.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import aiohttp
from .base import DataProvider, FinancialData, DataRequest, DataProviderError, RateLimitError

class AlphaVantageProvider(DataProvider):
    """Alpha Vantage API provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit = config.get('rate_limit', 5)  # Alpha Vantage free tier limit
        self._request_count = 0
        self._last_request_time = None
    
    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited API request"""
        # Rate limiting
        if self._last_request_time:
            time_since_last = (datetime.now() - self._last_request_time).total_seconds()
            if time_since_last < (60 / self.rate_limit):
                await asyncio.sleep((60 / self.rate_limit) - time_since_last)
        
        params['apikey'] = self.api_key
        
        async with self.session.get(self.base_url, params=params) as response:
            self._validate_response(response)
            data = await response.json()
            
            if 'Error Message' in data:
                raise DataProviderError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Note' in data:
                raise RateLimitError(f"Rate limit exceeded: {data['Note']}")
            
            self._request_count += 1
            self._last_request_time = datetime.now()
            
            return data
    
    async def get_stock_price(self, symbol: str, date: Optional[date] = None) -> FinancialData:
        """Get stock price data"""
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': 'compact'
        }
        
        data = await self._make_request(params)
        
        if 'Time Series (Daily)' not in data:
            raise DataProviderError(f"No price data found for {symbol}")
        
        time_series = data['Time Series (Daily)']
        latest_date = max(time_series.keys())
        
        if date:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in time_series:
                raise DataProviderError(f"No data for {symbol} on {date_str}")
            latest_date = date_str
        
        price_data = time_series[latest_date]
        
        return FinancialData(
            symbol=symbol,
            data_type='price',
            timestamp=datetime.strptime(latest_date, '%Y-%m-%d'),
            data={
                'open': float(price_data['1. open']),
                'high': float(price_data['2. high']),
                'low': float(price_data['3. low']),
                'close': float(price_data['4. close']),
                'volume': int(price_data['5. volume'])
            },
            source='alpha_vantage',
            confidence=0.95,
            metadata={'function': 'TIME_SERIES_DAILY'}
        )
    
    async def get_financial_statements(self, symbol: str, statement_type: str) -> List[FinancialData]:
        """Get financial statements"""
        function_map = {
            'income': 'INCOME_STATEMENT',
            'balance': 'BALANCE_SHEET',
            'cash_flow': 'CASH_FLOW'
        }
        
        if statement_type not in function_map:
            raise ValueError(f"Invalid statement type: {statement_type}")
        
        params = {
            'function': function_map[statement_type],
            'symbol': symbol
        }
        
        data = await self._make_request(params)
        
        if 'annualReports' not in data and 'quarterlyReports' not in data:
            raise DataProviderError(f"No financial data found for {symbol}")
        
        results = []
        
        # Process annual reports
        if 'annualReports' in data:
            for report in data['annualReports']:
                results.append(FinancialData(
                    symbol=symbol,
                    data_type=f'financial_{statement_type}',
                    timestamp=datetime.strptime(report['fiscalDateEnding'], '%Y-%m-%d'),
                    data=report,
                    source='alpha_vantage',
                    confidence=0.90,
                    metadata={'period': 'annual', 'function': function_map[statement_type]}
                ))
        
        # Process quarterly reports
        if 'quarterlyReports' in data:
            for report in data['quarterlyReports']:
                results.append(FinancialData(
                    symbol=symbol,
                    data_type=f'financial_{statement_type}',
                    timestamp=datetime.strptime(report['fiscalDateEnding'], '%Y-%m-%d'),
                    data=report,
                    source='alpha_vantage',
                    confidence=0.90,
                    metadata={'period': 'quarterly', 'function': function_map[statement_type]}
                ))
        
        return results
    
    async def get_company_info(self, symbol: str) -> FinancialData:
        """Get company information"""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = await self._make_request(params)
        
        if 'Symbol' not in data:
            raise DataProviderError(f"No company info found for {symbol}")
        
        return FinancialData(
            symbol=symbol,
            data_type='company_info',
            timestamp=datetime.now(),
            data=data,
            source='alpha_vantage',
            confidence=0.95,
            metadata={'function': 'OVERVIEW'}
        )
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query
        }
        
        data = await self._make_request(params)
        
        if 'bestMatches' not in data:
            return []
        
        return data['bestMatches']
    
    async def get_earnings(self, symbol: str) -> List[FinancialData]:
        """Get earnings data"""
        params = {
            'function': 'EARNINGS',
            'symbol': symbol
        }
        
        data = await self._make_request(params)
        
        if 'annualEarnings' not in data and 'quarterlyEarnings' not in data:
            raise DataProviderError(f"No earnings data found for {symbol}")
        
        results = []
        
        # Process annual earnings
        if 'annualEarnings' in data:
            for earning in data['annualEarnings']:
                results.append(FinancialData(
                    symbol=symbol,
                    data_type='earnings',
                    timestamp=datetime.strptime(earning['fiscalDateEnding'], '%Y-%m-%d'),
                    data=earning,
                    source='alpha_vantage',
                    confidence=0.90,
                    metadata={'period': 'annual', 'function': 'EARNINGS'}
                ))
        
        # Process quarterly earnings
        if 'quarterlyEarnings' in data:
            for earning in data['quarterlyEarnings']:
                results.append(FinancialData(
                    symbol=symbol,
                    data_type='earnings',
                    timestamp=datetime.strptime(earning['fiscalDateEnding'], '%Y-%m-%d'),
                    data=earning,
                    source='alpha_vantage',
                    confidence=0.90,
                    metadata={'period': 'quarterly', 'function': 'EARNINGS'}
                ))
        
        return results 