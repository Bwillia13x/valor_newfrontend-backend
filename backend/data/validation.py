"""
Data validation and sanitization for financial data.

This module provides comprehensive validation and sanitization
for financial data from external providers.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import re
from pydantic import BaseModel, validator, ValidationError
from .providers.base import FinancialData

class StockPriceValidator(BaseModel):
    """Validator for stock price data"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,5}$', v):
            raise ValueError('Invalid symbol format')
        return v.upper()
    
    @validator('open', 'high', 'low', 'close')
    def validate_prices(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)
    
    @validator('volume')
    def validate_volume(cls, v):
        if v < 0:
            raise ValueError('Volume must be non-negative')
        return v
    
    @validator('high')
    def validate_high_price(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('High price cannot be less than low price')
        return v

class FinancialStatementValidator(BaseModel):
    """Validator for financial statement data"""
    symbol: str
    statement_type: str
    period: str
    fiscal_date_ending: date
    data: Dict[str, Union[str, float, int]]
    
    @validator('statement_type')
    def validate_statement_type(cls, v):
        valid_types = ['income', 'balance', 'cash_flow']
        if v not in valid_types:
            raise ValueError(f'Invalid statement type: {v}')
        return v
    
    @validator('period')
    def validate_period(cls, v):
        valid_periods = ['annual', 'quarterly']
        if v not in valid_periods:
            raise ValueError(f'Invalid period: {v}')
        return v

class CompanyInfoValidator(BaseModel):
    """Validator for company information data"""
    symbol: str
    name: str
    description: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,5}$', v):
            raise ValueError('Invalid symbol format')
        return v.upper()
    
    @validator('market_cap')
    def validate_market_cap(cls, v):
        if v is not None and v < 0:
            raise ValueError('Market cap must be non-negative')
        return v

class DataSanitizer:
    """Sanitizes and validates financial data"""
    
    @staticmethod
    def sanitize_stock_price(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize stock price data"""
        # Remove any non-numeric characters from prices
        for key in ['open', 'high', 'low', 'close']:
            if key in data and isinstance(data[key], str):
                data[key] = float(re.sub(r'[^\d.]', '', data[key]))
        
        # Ensure volume is integer
        if 'volume' in data:
            data['volume'] = int(float(data['volume']))
        
        return data
    
    @staticmethod
    def sanitize_financial_statement(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize financial statement data"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = re.sub(r'[$,€£¥]', '', value)
                cleaned = re.sub(r',', '', cleaned)
                
                # Try to convert to float if it looks like a number
                if re.match(r'^-?\d*\.?\d+$', cleaned):
                    try:
                        sanitized[key] = float(cleaned)
                    except ValueError:
                        sanitized[key] = value
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def sanitize_company_info(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize company information data"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove HTML tags and extra whitespace
                cleaned = re.sub(r'<[^>]+>', '', value)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                sanitized[key] = cleaned
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def validate_financial_data(data: FinancialData) -> bool:
        """Validate financial data structure"""
        try:
            if data.data_type == 'price':
                StockPriceValidator(**data.data)
            elif data.data_type.startswith('financial_'):
                FinancialStatementValidator(**data.data)
            elif data.data_type == 'company_info':
                CompanyInfoValidator(**data.data)
            
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def sanitize_financial_data(data: FinancialData) -> FinancialData:
        """Sanitize financial data"""
        if data.data_type == 'price':
            sanitized_data = DataSanitizer.sanitize_stock_price(data.data)
        elif data.data_type.startswith('financial_'):
            sanitized_data = DataSanitizer.sanitize_financial_statement(data.data)
        elif data.data_type == 'company_info':
            sanitized_data = DataSanitizer.sanitize_company_info(data.data)
        else:
            sanitized_data = data.data
        
        return FinancialData(
            symbol=data.symbol,
            data_type=data.data_type,
            timestamp=data.timestamp,
            data=sanitized_data,
            source=data.source,
            confidence=data.confidence,
            metadata=data.metadata
        )

class DataQualityChecker:
    """Checks data quality and completeness"""
    
    @staticmethod
    def check_price_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
        """Check quality of price data"""
        quality_score = 1.0
        issues = []
        
        # Check for missing required fields
        required_fields = ['open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if field not in data or data[field] is None:
                quality_score -= 0.2
                issues.append(f"Missing {field}")
        
        # Check for price consistency
        if all(field in data for field in ['open', 'high', 'low', 'close']):
            if data['high'] < data['low']:
                quality_score -= 0.3
                issues.append("High price less than low price")
            
            if data['close'] < 0 or data['open'] < 0:
                quality_score -= 0.3
                issues.append("Negative prices detected")
        
        # Check for volume consistency
        if 'volume' in data and data['volume'] < 0:
            quality_score -= 0.2
            issues.append("Negative volume")
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'is_acceptable': quality_score >= 0.7
        }
    
    @staticmethod
    def check_financial_statement_quality(data: Dict[str, Any]) -> Dict[str, Any]:
        """Check quality of financial statement data"""
        quality_score = 1.0
        issues = []
        
        # Check for required fields
        required_fields = ['fiscalDateEnding', 'reportedCurrency']
        for field in required_fields:
            if field not in data or data[field] is None:
                quality_score -= 0.2
                issues.append(f"Missing {field}")
        
        # Check for data completeness
        numeric_fields = [k for k, v in data.items() if isinstance(v, (int, float))]
        if len(numeric_fields) < 5:
            quality_score -= 0.3
            issues.append("Insufficient numeric data")
        
        return {
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'is_acceptable': quality_score >= 0.7
        }

# Global data sanitizer
data_sanitizer = DataSanitizer()
data_quality_checker = DataQualityChecker() 