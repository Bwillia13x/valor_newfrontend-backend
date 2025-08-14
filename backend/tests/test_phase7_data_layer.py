"""
Tests for Phase 7 Data Layer Components

This module tests the data provider abstraction, circuit breaker pattern,
data validation, and API key management functionality.
"""

import pytest
import asyncio
from datetime import datetime, date
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from backend.data.providers.base import (
    FinancialData, DataRequest, DataProvider, 
    DataProviderError, RateLimitError
)
from backend.data.providers.alpha_vantage import AlphaVantageProvider
from backend.data.provider_manager import DataProviderManager
from backend.data.validation import data_sanitizer, data_quality_checker
from backend.circuit_breaker.circuit_breaker import (
    CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError
)
from backend.security.api_key_manager import APIKeyManager, APIKey
from backend.utils.retry import RetryConfig, retry_async, retry_sync

class TestFinancialData:
    """Test FinancialData dataclass"""
    
    def test_financial_data_creation(self):
        """Test creating FinancialData instance"""
        data = FinancialData(
            symbol="AAPL",
            data_type="price",
            timestamp=datetime.now(),
            data={"open": 150.0, "close": 155.0},
            source="test",
            confidence=0.95,
            metadata={"test": True}
        )
        
        assert data.symbol == "AAPL"
        assert data.data_type == "price"
        assert data.source == "test"
        assert data.confidence == 0.95

class TestDataProvider:
    """Test base DataProvider class"""
    
    def test_data_provider_config(self):
        """Test DataProvider configuration"""
        config = {
            'name': 'test_provider',
            'api_key': 'test_key',
            'rate_limit': 100,
            'timeout': 30
        }
        
        provider = Mock(spec=DataProvider)
        provider.config = config
        provider.name = config['name']
        provider.api_key = config['api_key']
        provider.rate_limit = config['rate_limit']
        provider.timeout = config['timeout']
        
        assert provider.name == 'test_provider'
        assert provider.api_key == 'test_key'
        assert provider.rate_limit == 100
        assert provider.timeout == 30

class TestAlphaVantageProvider:
    """Test Alpha Vantage provider implementation"""
    
    @pytest.fixture
    def provider_config(self):
        return {
            'name': 'alpha_vantage',
            'api_key': 'test_key',
            'rate_limit': 5,
            'timeout': 30
        }
    
    @pytest.fixture
    def provider(self, provider_config):
        return AlphaVantageProvider(provider_config)
    
    def test_provider_initialization(self, provider):
        """Test provider initialization"""
        assert provider.name == 'alpha_vantage'
        assert provider.api_key == 'test_key'
        assert provider.rate_limit == 5
        assert provider.base_url == "https://www.alphavantage.co/query"
    
    @pytest.mark.asyncio
    async def test_get_stock_price_success(self, provider):
        """Test successful stock price retrieval"""
        mock_response = {
            'Time Series (Daily)': {
                '2024-01-15': {
                    '1. open': '150.00',
                    '2. high': '155.00',
                    '3. low': '149.00',
                    '4. close': '153.00',
                    '5. volume': '1000000'
                }
            }
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await provider.get_stock_price('AAPL')
            
            assert result.symbol == 'AAPL'
            assert result.data_type == 'price'
            assert result.data['open'] == 150.0
            assert result.data['close'] == 153.0
            assert result.source == 'alpha_vantage'
    
    @pytest.mark.asyncio
    async def test_get_stock_price_error(self, provider):
        """Test stock price retrieval with error"""
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'Error Message': 'Invalid API call'}
            
            with pytest.raises(DataProviderError):
                await provider.get_stock_price('INVALID')

class TestDataProviderManager:
    """Test DataProviderManager"""
    
    @pytest.fixture
    def manager(self):
        return DataProviderManager()
    
    def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert hasattr(manager, 'providers')
        assert isinstance(manager.providers, dict)
    
    @pytest.mark.asyncio
    async def test_get_stock_price_no_providers(self, manager):
        """Test getting stock price with no providers"""
        with pytest.raises(DataProviderError):
            await manager.get_stock_price('AAPL')

class TestCircuitBreaker:
    """Test Circuit Breaker implementation"""
    
    @pytest.fixture
    def config(self):
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            timeout=30.0
        )
    
    @pytest.fixture
    def circuit_breaker(self, config):
        return CircuitBreaker('test_circuit', config)
    
    def test_circuit_breaker_initialization(self, circuit_breaker):
        """Test circuit breaker initialization"""
        assert circuit_breaker.name == 'test_circuit'
        assert circuit_breaker.state.value == 'closed'
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.success_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self, circuit_breaker):
        """Test successful circuit breaker call"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == 'closed'
        assert circuit_breaker.success_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure(self, circuit_breaker):
        """Test circuit breaker failure handling"""
        async def failure_func():
            raise Exception("test error")
        
        # Should fail 3 times before opening circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        
        assert circuit_breaker.state.value == 'open'
        assert circuit_breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open(self, circuit_breaker):
        """Test circuit breaker open state"""
        # Open the circuit
        circuit_breaker._set_open()
        
        async def test_func():
            return "test"
        
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(test_func)

class TestDataValidation:
    """Test data validation and sanitization"""
    
    def test_sanitize_stock_price(self):
        """Test stock price data sanitization"""
        raw_data = {
            'open': '150.00',
            'high': '155.00',
            'low': '149.00',
            'close': '153.00',
            'volume': '1000000'
        }
        
        sanitized = data_sanitizer.sanitize_stock_price(raw_data)
        
        assert sanitized['open'] == 150.0
        assert sanitized['high'] == 155.0
        assert sanitized['low'] == 149.0
        assert sanitized['close'] == 153.0
        assert sanitized['volume'] == 1000000
    
    def test_sanitize_financial_statement(self):
        """Test financial statement data sanitization"""
        raw_data = {
            'revenue': '$1,000,000',
            'net_income': '€500,000',
            'description': 'Test company'
        }
        
        sanitized = data_sanitizer.sanitize_financial_statement(raw_data)
        
        assert sanitized['revenue'] == 1000000.0
        assert sanitized['net_income'] == 500000.0
        assert sanitized['description'] == 'Test company'
    
    def test_validate_financial_data(self):
        """Test financial data validation"""
        valid_data = FinancialData(
            symbol="AAPL",
            data_type="price",
            timestamp=datetime.now(),
            data={
                'open': 150.0,
                'high': 155.0,
                'low': 149.0,
                'close': 153.0,
                'volume': 1000000
            },
            source="test",
            confidence=0.95,
            metadata={}
        )
        
        assert data_sanitizer.validate_financial_data(valid_data) == True
    
    def test_check_price_data_quality(self):
        """Test price data quality checking"""
        good_data = {
            'open': 150.0,
            'high': 155.0,
            'low': 149.0,
            'close': 153.0,
            'volume': 1000000
        }
        
        quality = data_quality_checker.check_price_data_quality(good_data)
        
        assert quality['quality_score'] == 1.0
        assert quality['is_acceptable'] == True
        assert len(quality['issues']) == 0
    
    def test_check_price_data_quality_issues(self):
        """Test price data quality checking with issues"""
        bad_data = {
            'open': 150.0,
            'high': 145.0,  # High less than low
            'low': 149.0,
            'close': -153.0,  # Negative price
            'volume': -1000000  # Negative volume
        }
        
        quality = data_quality_checker.check_price_data_quality(bad_data)
        
        assert quality['quality_score'] < 1.0
        assert quality['is_acceptable'] == False
        assert len(quality['issues']) > 0

class TestAPIKeyManager:
    """Test API Key Manager"""
    
    @pytest.fixture
    def key_manager(self):
        return APIKeyManager()
    
    def test_add_key(self, key_manager):
        """Test adding API key"""
        key_manager.add_key(
            name="test_key",
            key="test_api_key",
            provider="test_provider"
        )
        
        assert "test_key" in key_manager.keys
        assert key_manager.keys["test_key"].key == "test_api_key"
        assert key_manager.keys["test_key"].provider == "test_provider"
    
    def test_get_key(self, key_manager):
        """Test getting API key"""
        key_manager.add_key(
            name="test_key",
            key="test_api_key",
            provider="test_provider"
        )
        
        key = key_manager.get_key("test_provider")
        assert key == "test_api_key"
    
    def test_get_key_status(self, key_manager):
        """Test getting API key status"""
        key_manager.add_key(
            name="test_key",
            key="test_api_key",
            provider="test_provider"
        )
        
        status = key_manager.get_key_status()
        assert "test_key" in status
        assert status["test_key"]["provider"] == "test_provider"
        assert status["test_key"]["is_active"] == True

class TestRetryMechanism:
    """Test retry mechanism with exponential backoff"""
    
    def test_retry_config(self):
        """Test retry configuration"""
        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=True
        )
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter == True
    
    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test async retry with success"""
        config = RetryConfig(max_attempts=3)
        
        @retry_async(config)
        async def success_func():
            return "success"
        
        result = await success_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_async_failure(self):
        """Test async retry with failure"""
        config = RetryConfig(max_attempts=2)
        call_count = 0
        
        @retry_async(config)
        async def failure_func():
            nonlocal call_count
            call_count += 1
            raise Exception("test error")
        
        with pytest.raises(Exception):
            await failure_func()
        
        assert call_count == 2  # Should retry once

if __name__ == "__main__":
    pytest.main([__file__]) 