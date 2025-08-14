# Phase 7 Startup Summary - Data Layer and External Integrations

## 🎯 **Phase 7: Data Layer and External Integrations - Ready to Start**

**Duration**: 6 weeks  
**Status**: 🚀 **READY TO START**  
**Start Date**: August 2025  

## 📋 **Executive Summary**

Phase 7 will implement robust data layer infrastructure and external API integrations for the Valor IVX financial modeling platform. This phase focuses on financial data provider abstraction, circuit breaker patterns, data validation, and external API hardening to create a resilient and scalable data foundation.

## 🏗️ **Current Architecture State**

### **Backend Infrastructure** ✅
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with Redis caching
- **Authentication**: JWT-based with middleware
- **API Structure**: RESTful endpoints in `backend/api/`
- **ML Models**: Registry system with variant support
- **Observability**: Prometheus metrics, structured logging
- **Async Processing**: Celery with Redis broker
- **Caching**: Redis integration with `cache_result()` decorator

### **Frontend Infrastructure** ✅
- **Framework**: Vanilla JavaScript with modular architecture
- **PWA**: Enhanced service worker with offline capabilities
- **Error Handling**: Comprehensive error categorization and reporting
- **Performance**: Core Web Vitals optimization and monitoring
- **Accessibility**: WCAG 2.1 AA compliance
- **Modules**: 20+ specialized modules in `js/modules/`

### **Completed Phases** ✅
- **Phase 1**: Stabilization and Quality Gates (85% complete)
- **Phase 2**: Backend Architecture and Performance (90% complete)
- **Phase 3**: ML/Analytics Hardening (75% complete)
- **Phase 5**: Frontend UX and Reliability (100% complete)
- **Phase 6**: Enterprise Features (Ready to start - summary created)

### **Current Progress**
- **Overall**: 45% complete
- **Data Layer**: 0% complete (ready to start)
- **Foundation**: Solid with observability, caching, async processing

## 🎯 **Phase 7 Implementation Plan**

### **Week 1-2: Financial Data Provider Abstraction**
**Objective**: Create unified interface for multiple financial data sources

#### **1.1 Data Provider Interface**
```python
# backend/data/providers/base.py (new file)
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date
import asyncio
import aiohttp
from backend.cache import cache_result

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
```

#### **1.2 Alpha Vantage Provider Implementation**
```python
# backend/data/providers/alpha_vantage.py (new file)
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import aiohttp
from .base import DataProvider, FinancialData, DataRequest, DataProviderError

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
```

#### **1.3 Data Provider Manager**
```python
# backend/data/provider_manager.py (new file)
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
from .providers.base import DataProvider, FinancialData, DataRequest, DataProviderError
from .providers.alpha_vantage import AlphaVantageProvider
from backend.cache import cache_result
from backend.settings import settings

class DataProviderManager:
    """Manages multiple data providers with fallback and caching"""
    
    def __init__(self):
        self.providers: Dict[str, DataProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize configured data providers"""
        if settings.ALPHA_VANTAGE_API_KEY:
            self.providers['alpha_vantage'] = AlphaVantageProvider({
                'name': 'alpha_vantage',
                'api_key': settings.ALPHA_VANTAGE_API_KEY,
                'rate_limit': settings.ALPHA_VANTAGE_RATE_LIMIT,
                'timeout': 30
            })
        
        # Add more providers as needed
        # if settings.YAHOO_FINANCE_ENABLED:
        #     self.providers['yahoo_finance'] = YahooFinanceProvider(...)
    
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_stock_price(self, symbol: str, date: Optional[date] = None, 
                             provider: Optional[str] = None) -> FinancialData:
        """Get stock price with fallback providers"""
        if provider and provider in self.providers:
            providers_to_try = [provider]
        else:
            providers_to_try = list(self.providers.keys())
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                async with self.providers[provider_name] as provider_instance:
                    return await provider_instance.get_stock_price(symbol, date)
            except Exception as e:
                last_error = e
                continue
        
        raise DataProviderError(f"All providers failed for {symbol}: {last_error}")
    
    @cache_result(ttl=3600)  # Cache for 1 hour
    async def get_financial_statements(self, symbol: str, statement_type: str,
                                     provider: Optional[str] = None) -> List[FinancialData]:
        """Get financial statements with fallback providers"""
        if provider and provider in self.providers:
            providers_to_try = [provider]
        else:
            providers_to_try = list(self.providers.keys())
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                async with self.providers[provider_name] as provider_instance:
                    return await provider_instance.get_financial_statements(symbol, statement_type)
            except Exception as e:
                last_error = e
                continue
        
        raise DataProviderError(f"All providers failed for {symbol}: {last_error}")
    
    async def batch_get_prices(self, symbols: List[str], date: Optional[date] = None) -> List[FinancialData]:
        """Get prices for multiple symbols concurrently"""
        tasks = [self.get_stock_price(symbol, date) for symbol in symbols]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                'name': name,
                'rate_limit': provider.rate_limit,
                'request_count': getattr(provider, '_request_count', 0),
                'last_request': getattr(provider, '_last_request_time', None)
            }
        return status

# Global provider manager instance
provider_manager = DataProviderManager()
```

### **Week 3-4: Circuit Breaker Implementation**
**Objective**: Implement resilient external API communication

#### **2.1 Circuit Breaker Pattern**
```python
# backend/circuit_breaker/circuit_breaker.py (new file)
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass
from backend.metrics import circuit_breaker_metrics

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Number of failures to open circuit
    recovery_timeout: int = 60        # Seconds to wait before half-open
    expected_exception: type = Exception  # Exception type to count as failure
    success_threshold: int = 2        # Successes needed to close circuit
    timeout: float = 30.0             # Request timeout in seconds

class CircuitBreaker:
    """Circuit breaker implementation for external API calls"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Metrics
        self.metrics = circuit_breaker_metrics.labels(
            circuit_name=name,
            state=self.state.value
        )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self._on_failure(TimeoutError("Request timeout"))
            raise
        except self.config.expected_exception as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exceptions don't count as failures
            raise
    
    def _on_success(self):
        """Handle successful request"""
        self.failure_count = 0
        self.success_count += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN and self.success_count >= self.config.success_threshold:
            self._set_closed()
        
        # Update metrics
        self.metrics.labels(state=self.state.value).inc()
    
    def _on_failure(self, exception: Exception):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self._set_open()
        
        # Update metrics
        self.metrics.labels(state=self.state.value).inc()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return False
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _set_open(self):
        """Set circuit to open state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.metrics.labels(state=self.state.value).inc()
    
    def _set_half_open(self):
        """Set circuit to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.metrics.labels(state=self.state.value).inc()
    
    def _set_closed(self):
        """Set circuit to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.metrics.labels(state=self.state.value).inc()
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout
            }
        }

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.circuits: Dict[str, CircuitBreaker] = {}
    
    def get_circuit(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuits:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuits[name] = CircuitBreaker(name, config)
        
        return self.circuits[name]
    
    def get_all_status(self) -> Dict[str, dict]:
        """Get status of all circuit breakers"""
        return {name: circuit.get_status() for name, circuit in self.circuits.items()}
    
    def reset_circuit(self, name: str):
        """Manually reset a circuit breaker"""
        if name in self.circuits:
            self.circuits[name]._set_closed()

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()
```

#### **2.2 Enhanced Data Provider with Circuit Breaker**
```python
# backend/data/providers/circuit_breaker_provider.py (new file)
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from .base import DataProvider, FinancialData, DataRequest, DataProviderError
from ..circuit_breaker.circuit_breaker import CircuitBreakerConfig, circuit_breaker_manager

class CircuitBreakerDataProvider(DataProvider):
    """Data provider wrapper with circuit breaker protection"""
    
    def __init__(self, provider: DataProvider, circuit_name: str):
        self.provider = provider
        self.circuit_name = circuit_name
        self.circuit = circuit_breaker_manager.get_circuit(
            circuit_name,
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                expected_exception=DataProviderError,
                success_threshold=2,
                timeout=30.0
            )
        )
    
    async def get_stock_price(self, symbol: str, date: Optional[date] = None) -> FinancialData:
        """Get stock price with circuit breaker protection"""
        return await self.circuit.call(
            self.provider.get_stock_price,
            symbol,
            date
        )
    
    async def get_financial_statements(self, symbol: str, statement_type: str) -> List[FinancialData]:
        """Get financial statements with circuit breaker protection"""
        return await self.circuit.call(
            self.provider.get_financial_statements,
            symbol,
            statement_type
        )
    
    async def get_company_info(self, symbol: str) -> FinancialData:
        """Get company info with circuit breaker protection"""
        return await self.circuit.call(
            self.provider.get_company_info,
            symbol
        )
    
    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search symbols with circuit breaker protection"""
        return await self.circuit.call(
            self.provider.search_symbols,
            query
        )
```

### **Week 5-6: External API Hardening**
**Objective**: Implement comprehensive error handling and security

#### **3.1 Retry Mechanism with Exponential Backoff**
```python
# backend/utils/retry.py (new file)
import asyncio
import random
from typing import Callable, Any, Optional, List
from functools import wraps

class RetryConfig:
    """Configuration for retry mechanism"""
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True, retry_exceptions: Optional[List[type]] = None):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or [Exception]

def retry_async(config: RetryConfig):
    """Decorator for async retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except tuple(config.retry_exceptions) as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        raise last_exception
                    
                    # Calculate delay with exponential backoff
                    delay = config.base_delay * (config.exponential_base ** attempt)
                    delay = min(delay, config.max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

def retry_sync(config: RetryConfig):
    """Decorator for sync retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(config.retry_exceptions) as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        raise last_exception
                    
                    # Calculate delay with exponential backoff
                    delay = config.base_delay * (config.exponential_base ** attempt)
                    delay = min(delay, config.max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator
```

#### **3.2 API Key Management and Rotation**
```python
# backend/security/api_key_manager.py (new file)
import hashlib
import secrets
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from backend.cache import cache_result

@dataclass
class APIKey:
    """API key configuration"""
    name: str
    key: str
    provider: str
    is_active: bool = True
    created_at: datetime = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    rate_limit: int = 100  # requests per minute
    rotation_interval: int = 30  # days

class APIKeyManager:
    """Manages API keys with rotation and rate limiting"""
    
    def __init__(self):
        self.keys: Dict[str, APIKey] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from configuration"""
        from backend.settings import settings
        
        # Load Alpha Vantage keys
        if settings.ALPHA_VANTAGE_API_KEY:
            self.add_key(
                name="alpha_vantage_primary",
                key=settings.ALPHA_VANTAGE_API_KEY,
                provider="alpha_vantage"
            )
        
        # Load backup keys if available
        if hasattr(settings, 'ALPHA_VANTAGE_BACKUP_KEYS'):
            for i, key in enumerate(settings.ALPHA_VANTAGE_BACKUP_KEYS):
                self.add_key(
                    name=f"alpha_vantage_backup_{i+1}",
                    key=key,
                    provider="alpha_vantage"
                )
    
    def add_key(self, name: str, key: str, provider: str, **kwargs):
        """Add a new API key"""
        api_key = APIKey(
            name=name,
            key=key,
            provider=provider,
            created_at=datetime.now(),
            **kwargs
        )
        self.keys[name] = api_key
    
    def get_key(self, provider: str) -> Optional[str]:
        """Get the best available key for a provider"""
        available_keys = [
            key for key in self.keys.values()
            if key.provider == provider and key.is_active
        ]
        
        if not available_keys:
            return None
        
        # Sort by usage count and last used time
        available_keys.sort(key=lambda k: (k.usage_count, k.last_used or datetime.min))
        
        # Check rate limits
        for key in available_keys:
            if self._check_rate_limit(key):
                return key.key
        
        return None
    
    def _check_rate_limit(self, key: APIKey) -> bool:
        """Check if key is within rate limit"""
        if not key.last_used:
            return True
        
        # Simple rate limiting - can be enhanced with Redis
        time_since_last = (datetime.now() - key.last_used).total_seconds()
        return time_since_last >= (60 / key.rate_limit)
    
    def record_usage(self, key_name: str):
        """Record API key usage"""
        if key_name in self.keys:
            key = self.keys[key_name]
            key.last_used = datetime.now()
            key.usage_count += 1
    
    def rotate_keys(self):
        """Rotate API keys based on age"""
        current_time = datetime.now()
        
        for key in self.keys.values():
            if key.created_at:
                age = current_time - key.created_at
                if age.days >= key.rotation_interval:
                    self._rotate_key(key)
    
    def _rotate_key(self, key: APIKey):
        """Rotate a specific API key"""
        # In a real implementation, this would:
        # 1. Generate a new key
        # 2. Update the key in the provider's system
        # 3. Update the local configuration
        # 4. Deactivate the old key after a grace period
        
        key.is_active = False
        # Implementation depends on provider-specific rotation mechanisms
    
    def get_key_status(self) -> Dict[str, dict]:
        """Get status of all API keys"""
        status = {}
        for name, key in self.keys.items():
            status[name] = {
                'provider': key.provider,
                'is_active': key.is_active,
                'created_at': key.created_at.isoformat() if key.created_at else None,
                'last_used': key.last_used.isoformat() if key.last_used else None,
                'usage_count': key.usage_count,
                'rate_limit': key.rate_limit,
                'rotation_interval': key.rotation_interval
            }
        return status

# Global API key manager
api_key_manager = APIKeyManager()
```

#### **3.3 Data Validation and Sanitization**
```python
# backend/data/validation.py (new file)
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import re
from pydantic import BaseModel, validator, ValidationError
from backend.data.providers.base import FinancialData

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
    def validate_financial_data(data: FinancialData) -> bool:
        """Validate financial data structure"""
        try:
            if data.data_type == 'price':
                StockPriceValidator(**data.data)
            elif data.data_type.startswith('financial_'):
                FinancialStatementValidator(**data.data)
            
            return True
        except ValidationError:
            return False

# Global data sanitizer
data_sanitizer = DataSanitizer()
```

## 🎯 **Success Metrics and Targets**

### **Data Provider Metrics**
- ✅ **Provider Uptime**: 99.9% availability across all providers
- ✅ **Response Time**: < 2 seconds for single requests
- ✅ **Cache Hit Ratio**: > 80% for frequently requested data
- ✅ **Data Accuracy**: > 95% confidence score for all data

### **Circuit Breaker Metrics**
- ✅ **Failure Detection**: < 5 seconds to detect failures
- ✅ **Recovery Time**: < 60 seconds to attempt recovery
- ✅ **False Positives**: < 1% of circuit opens
- ✅ **Service Protection**: 100% of external calls protected

### **API Hardening Metrics**
- ✅ **Retry Success Rate**: > 90% of retried requests succeed
- ✅ **Key Rotation**: Automatic rotation every 30 days
- ✅ **Data Validation**: 100% of data validated before use
- ✅ **Security**: Zero API key exposures

## 🚀 **Getting Started Guide**

### **1. Environment Setup**
```bash
# Install additional dependencies
pip install aiohttp pydantic

# Set environment variables
export ALPHA_VANTAGE_API_KEY="your_api_key_here"
export ALPHA_VANTAGE_RATE_LIMIT=5
export ALPHA_VANTAGE_BACKUP_KEYS="key1,key2,key3"
```

### **2. Database Migration**
```bash
# No database changes required for Phase 7
# All data is cached in Redis and external APIs
```

### **3. Configuration Updates**
```python
# backend/settings.py - Add new settings
class Settings(BaseSettings):
    # Existing settings...
    
    # Data Provider Settings
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_RATE_LIMIT: int = 5
    ALPHA_VANTAGE_BACKUP_KEYS: List[str] = []
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    
    # Retry Settings
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 60.0
```

### **4. API Testing**
```bash
# Test data provider
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/data/stock/AAPL

# Test circuit breaker status
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/data/circuit-breakers

# Test provider status
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/data/providers/status
```

## 📁 **File Structure for Phase 7**

### **New Files to Create**
```
backend/
├── data/
│   ├── __init__.py
│   ├── provider_manager.py          # Main provider manager
│   ├── validation.py                # Data validation and sanitization
│   └── providers/
│       ├── __init__.py
│       ├── base.py                  # Base provider interface
│       ├── alpha_vantage.py         # Alpha Vantage implementation
│       └── circuit_breaker_provider.py  # Circuit breaker wrapper
├── circuit_breaker/
│   ├── __init__.py
│   └── circuit_breaker.py           # Circuit breaker implementation
├── utils/
│   └── retry.py                     # Retry mechanism
├── security/
│   └── api_key_manager.py           # API key management
└── api/
    └── data_routes.py               # Data API endpoints
```

### **Files to Enhance**
```
backend/
├── app.py                           # Register new data routes
├── settings.py                      # Add data provider settings
├── metrics.py                       # Add circuit breaker metrics
└── requirements.txt                 # Add new dependencies
```

## 🔧 **Technical Implementation Details**

### **API Endpoints to Implement**
- **Data Access**: `/api/data/stock/<symbol>`, `/api/data/financials/<symbol>`
- **Provider Management**: `/api/data/providers/status`, `/api/data/providers/switch`
- **Circuit Breaker**: `/api/data/circuit-breakers`, `/api/data/circuit-breakers/reset`
- **Health Checks**: `/api/data/health`, `/api/data/providers/health`

### **Caching Strategy**
- **Stock Prices**: 5-minute cache for real-time data
- **Financial Statements**: 1-hour cache for quarterly/annual data
- **Company Info**: 24-hour cache for static data
- **Search Results**: 1-hour cache for symbol searches

### **Error Handling**
- **Provider Failures**: Automatic fallback to backup providers
- **Rate Limiting**: Automatic retry with exponential backoff
- **Data Validation**: Comprehensive validation with detailed error messages
- **Circuit Breaker**: Fast failure with graceful degradation

## 📊 **Monitoring and Observability**

### **Metrics to Track**
- Data provider response times and success rates
- Circuit breaker state changes and failure counts
- Cache hit ratios and eviction rates
- API key usage and rotation events
- Data validation success rates

### **Alerts to Configure**
- High circuit breaker failure rates
- Data provider downtime
- Cache miss rates above threshold
- API key usage approaching limits

## 🎯 **Next Steps After Phase 7**

### **Phase 8: Deployment and Scalability**
- Docker optimization and containerization
- Horizontal scaling setup
- Blue/green deployment strategies
- Infrastructure automation

### **Phase 9: Monitoring and SLOs**
- SLO definition and implementation
- Alerting configuration and runbooks
- Dashboard setup and maintenance
- Performance optimization

### **Phase 10: Documentation and Developer Experience**
- API documentation completion
- Developer guide enhancement
- Code documentation and examples
- Knowledge transfer and training

## ✅ **Phase 7 Success Criteria**

- ✅ **Data Provider Abstraction**: Unified interface for multiple providers
- ✅ **Circuit Breaker Pattern**: Resilient external API communication
- ✅ **Retry Mechanisms**: Exponential backoff with jitter
- ✅ **API Key Management**: Secure rotation and rate limiting
- ✅ **Data Validation**: Comprehensive validation and sanitization
- ✅ **Performance**: < 2 second response times for data requests
- ✅ **Reliability**: 99.9% uptime with graceful degradation

## 🏆 **Conclusion**

Phase 7 will establish a robust and resilient data layer foundation for the Valor IVX platform, enabling reliable access to financial data from multiple providers with comprehensive error handling, security, and performance optimization. The implementation builds upon the solid infrastructure established in previous phases and prepares the platform for enterprise-scale data operations.

The next developer should focus on:
1. **Data provider implementation** and integration
2. **Circuit breaker pattern** deployment across all external calls
3. **API key management** and security hardening
4. **Data validation** and quality assurance
5. **Performance optimization** and monitoring

This phase represents a critical infrastructure enhancement that will ensure the platform's reliability and scalability for enterprise financial modeling operations. 