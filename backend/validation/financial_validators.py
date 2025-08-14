"""
Financial Data Validation Module

Provides comprehensive validation for financial inputs, ensuring data integrity
and preventing calculation errors in financial models.
"""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union, Tuple
from pydantic import BaseModel, ValidationError, validator, Field
import logging

logger = logging.getLogger(__name__)

# Financial validation constants
FINANCIAL_PRECISION = Decimal('0.01')  # 2 decimal places
MAX_FINANCIAL_VALUE = Decimal('1e12')  # 1 trillion max
MIN_FINANCIAL_VALUE = Decimal('-1e12')  # -1 trillion min
VALID_TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')  # 1-5 uppercase letters
VALID_CURRENCY_CODES = {'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY'}

class FinancialValidationError(Exception):
    """Custom exception for financial validation errors"""
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Validation error for {field}: {message}")

class TickerValidator:
    """Validates stock ticker symbols"""
    
    @staticmethod
    def validate_ticker(ticker: str) -> str:
        """Validate and normalize ticker symbol"""
        if not ticker:
            raise FinancialValidationError("ticker", ticker, "Ticker cannot be empty")
        
        ticker = ticker.strip().upper()
        
        if not VALID_TICKER_PATTERN.match(ticker):
            raise FinancialValidationError(
                "ticker", ticker, 
                "Ticker must be 1-5 uppercase letters"
            )
        
        return ticker

class FinancialValueValidator:
    """Validates financial numerical values with proper precision"""
    
    @staticmethod
    def validate_financial_value(
        value: Union[str, int, float, Decimal], 
        field_name: str,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        allow_negative: bool = True
    ) -> Decimal:
        """Validate and convert financial value to Decimal with proper precision"""
        
        if value is None:
            raise FinancialValidationError(field_name, value, "Value cannot be None")
        
        try:
            # Convert to Decimal for precise calculations
            if isinstance(value, str):
                value = value.strip().replace(',', '')  # Remove commas
                decimal_value = Decimal(value)
            elif isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            elif isinstance(value, Decimal):
                decimal_value = value
            else:
                raise FinancialValidationError(
                    field_name, value, 
                    f"Invalid type {type(value).__name__}"
                )
            
            # Apply financial precision
            decimal_value = decimal_value.quantize(FINANCIAL_PRECISION, rounding=ROUND_HALF_UP)
            
            # Check range limits
            if not allow_negative and decimal_value < 0:
                raise FinancialValidationError(
                    field_name, value, 
                    "Negative values not allowed"
                )
            
            if min_value is not None and decimal_value < min_value:
                raise FinancialValidationError(
                    field_name, value, 
                    f"Value {decimal_value} below minimum {min_value}"
                )
            
            if max_value is not None and decimal_value > max_value:
                raise FinancialValidationError(
                    field_name, value, 
                    f"Value {decimal_value} above maximum {max_value}"
                )
            
            # Check absolute limits
            if decimal_value > MAX_FINANCIAL_VALUE or decimal_value < MIN_FINANCIAL_VALUE:
                raise FinancialValidationError(
                    field_name, value, 
                    f"Value {decimal_value} outside acceptable range"
                )
            
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            raise FinancialValidationError(
                field_name, value, 
                f"Invalid numeric value: {str(e)}"
            )

class PercentageValidator:
    """Validates percentage values"""
    
    @staticmethod
    def validate_percentage(
        value: Union[str, int, float, Decimal], 
        field_name: str,
        min_percent: Optional[Decimal] = None,
        max_percent: Optional[Decimal] = None
    ) -> Decimal:
        """Validate percentage value (0-100 range typically)"""
        
        decimal_value = FinancialValueValidator.validate_financial_value(
            value, field_name, allow_negative=False
        )
        
        # Default percentage range checks
        if min_percent is None:
            min_percent = Decimal('-100')  # Allow negative growth rates
        if max_percent is None:
            max_percent = Decimal('1000')  # Allow up to 1000% growth
        
        if decimal_value < min_percent or decimal_value > max_percent:
            raise FinancialValidationError(
                field_name, value,
                f"Percentage {decimal_value}% outside valid range {min_percent}%-{max_percent}%"
            )
        
        return decimal_value

# Pydantic models for structured validation

class DCFInputsValidator(BaseModel):
    """DCF model input validation"""
    ticker: str = Field(..., description="Stock ticker symbol")
    revenue: Union[str, int, float, Decimal] = Field(..., description="Revenue in millions")
    growth_year_1: Union[str, int, float, Decimal] = Field(..., description="Year 1 growth rate %")
    growth_year_2: Union[str, int, float, Decimal] = Field(..., description="Year 2 growth rate %")
    growth_year_3: Union[str, int, float, Decimal] = Field(..., description="Year 3 growth rate %")
    growth_year_4: Union[str, int, float, Decimal] = Field(..., description="Year 4 growth rate %")
    growth_year_5: Union[str, int, float, Decimal] = Field(..., description="Year 5 growth rate %")
    terminal_growth: Union[str, int, float, Decimal] = Field(..., description="Terminal growth rate %")
    discount_rate: Union[str, int, float, Decimal] = Field(..., description="Discount rate %")
    ebitda_margin: Union[str, int, float, Decimal] = Field(..., description="EBITDA margin %")
    tax_rate: Union[str, int, float, Decimal] = Field(..., description="Tax rate %")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        return TickerValidator.validate_ticker(v)
    
    @validator('revenue')
    def validate_revenue(cls, v):
        return FinancialValueValidator.validate_financial_value(
            v, 'revenue', min_value=Decimal('0'), max_value=Decimal('1000000')
        )
    
    @validator('growth_year_1', 'growth_year_2', 'growth_year_3', 'growth_year_4', 'growth_year_5')
    def validate_growth_rates(cls, v):
        return PercentageValidator.validate_percentage(
            v, 'growth_rate', min_percent=Decimal('-50'), max_percent=Decimal('100')
        )
    
    @validator('terminal_growth')
    def validate_terminal_growth(cls, v):
        return PercentageValidator.validate_percentage(
            v, 'terminal_growth', min_percent=Decimal('0'), max_percent=Decimal('5')
        )
    
    @validator('discount_rate')
    def validate_discount_rate(cls, v):
        return PercentageValidator.validate_percentage(
            v, 'discount_rate', min_percent=Decimal('1'), max_percent=Decimal('50')
        )
    
    @validator('ebitda_margin', 'tax_rate')
    def validate_margin_rates(cls, v):
        return PercentageValidator.validate_percentage(
            v, 'margin_rate', min_percent=Decimal('0'), max_percent=Decimal('100')
        )

class PortfolioInputsValidator(BaseModel):
    """Portfolio optimization input validation"""
    tickers: List[str] = Field(..., description="List of stock tickers")
    weights: Optional[List[Union[str, int, float, Decimal]]] = Field(None, description="Portfolio weights")
    risk_tolerance: Union[str, int, float, Decimal] = Field(..., description="Risk tolerance level")
    
    @validator('tickers')
    def validate_tickers(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one ticker is required")
        
        validated_tickers = []
        for ticker in v:
            validated_tickers.append(TickerValidator.validate_ticker(ticker))
        
        # Check for duplicates
        if len(set(validated_tickers)) != len(validated_tickers):
            raise ValueError("Duplicate tickers not allowed")
        
        return validated_tickers
    
    @validator('weights')
    def validate_weights(cls, v, values):
        if v is None:
            return v
        
        tickers = values.get('tickers', [])
        if len(v) != len(tickers):
            raise ValueError("Number of weights must match number of tickers")
        
        validated_weights = []
        total_weight = Decimal('0')
        
        for weight in v:
            validated_weight = FinancialValueValidator.validate_financial_value(
                weight, 'weight', min_value=Decimal('0'), max_value=Decimal('1')
            )
            validated_weights.append(validated_weight)
            total_weight += validated_weight
        
        # Check if weights sum to approximately 1.0
        if abs(total_weight - Decimal('1.0')) > Decimal('0.01'):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        return validated_weights
    
    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        return FinancialValueValidator.validate_financial_value(
            v, 'risk_tolerance', min_value=Decimal('0.01'), max_value=Decimal('10.0')
        )

class FinancialInputSanitizer:
    """Sanitizes and validates financial inputs"""
    
    @staticmethod
    def sanitize_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize incoming request data"""
        if not isinstance(data, dict):
            raise FinancialValidationError("request_data", data, "Data must be a dictionary")
        
        sanitized = {}
        
        for key, value in data.items():
            # Remove dangerous characters from keys
            clean_key = re.sub(r'[^\w\-_]', '', str(key))
            
            if isinstance(value, str):
                # Basic XSS protection
                value = value.strip()
                # Remove potentially dangerous characters but preserve valid financial notation
                value = re.sub(r'[<>"\';\\]', '', value)
            
            sanitized[clean_key] = value
        
        return sanitized
    
    @staticmethod
    def validate_dcf_inputs(data: Dict[str, Any]) -> DCFInputsValidator:
        """Validate DCF model inputs"""
        try:
            sanitized_data = FinancialInputSanitizer.sanitize_request_data(data)
            return DCFInputsValidator(**sanitized_data)
        except ValidationError as e:
            logger.error(f"DCF validation failed: {e}")
            raise FinancialValidationError("dcf_inputs", data, str(e))
    
    @staticmethod
    def validate_portfolio_inputs(data: Dict[str, Any]) -> PortfolioInputsValidator:
        """Validate portfolio optimization inputs"""
        try:
            sanitized_data = FinancialInputSanitizer.sanitize_request_data(data)
            return PortfolioInputsValidator(**sanitized_data)
        except ValidationError as e:
            logger.error(f"Portfolio validation failed: {e}")
            raise FinancialValidationError("portfolio_inputs", data, str(e))

# Decorator for route validation
def validate_financial_input(validator_class):
    """Decorator to validate financial inputs on routes"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400
                
                # Apply validation
                if validator_class == DCFInputsValidator:
                    validated_data = FinancialInputSanitizer.validate_dcf_inputs(data)
                elif validator_class == PortfolioInputsValidator:
                    validated_data = FinancialInputSanitizer.validate_portfolio_inputs(data)
                else:
                    validated_data = validator_class(**data)
                
                # Replace request data with validated data
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except FinancialValidationError as e:
                logger.warning(f"Financial validation error: {e}")
                return jsonify({
                    "error": "Validation failed",
                    "field": e.field,
                    "message": e.message
                }), 400
            except Exception as e:
                logger.error(f"Unexpected validation error: {e}")
                return jsonify({"error": "Invalid input data"}), 400
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator