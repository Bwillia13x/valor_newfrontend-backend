"""
Data provider manager for Valor IVX financial modeling platform.

This module manages multiple data providers with fallback mechanisms,
caching, and circuit breaker protection.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
import os
import time

from .providers.base import DataProvider, FinancialData, DataRequest, DataProviderError
from .providers.alpha_vantage import AlphaVantageProvider
from .providers.circuit_breaker_provider import CircuitBreakerDataProvider
# from backend.cache import cache_result  # Commented out for now
# from backend.settings import settings  # Commented out for now

# [P5] Metrics integration
try:
    from backend.metrics import (
        DATA_PROVIDER_REQUESTS_TOTAL,
        DATA_PROVIDER_DURATION_SECONDS,
        CACHE_HIT_RATIO,
    )
except Exception:
    DATA_PROVIDER_REQUESTS_TOTAL = None
    DATA_PROVIDER_DURATION_SECONDS = None
    CACHE_HIT_RATIO = None

# [P5] Access request context when running under Flask to pick tenant header
try:
    from flask import has_request_context, request
except Exception:
    def has_request_context() -> bool:  # type: ignore
        return False
    request = None  # type: ignore

try:
    import redis as _redis  # optional dependency
except Exception:
    _redis = None

class DataProviderManager:
    """Manages multiple data providers with fallback and caching"""

    def __init__(self, default_ttl_seconds: int = 300):
        self.providers: Dict[str, DataProvider] = {}
        self._initialize_providers()
        # Cache init: default in-memory; optional Redis when REDIS_URL is set
        self._cache_ttl = max(1, int(default_ttl_seconds))
        self._cache_mem: Dict[str, Dict[str, Any]] = {}  # key -> {"exp": ts, "val": any}
        self._cache_redis = None
        self._redis_prefix = "valor:data"
        # [P5] Cache hit/miss counters to compute ratio
        self._hits = 0
        self._misses = 0
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and _redis is not None:
            try:
                self._cache_redis = _redis.Redis.from_url(redis_url)
                # quick ping to validate
                self._cache_redis.ping()
            except Exception:
                self._cache_redis = None
    
    def _initialize_providers(self):
        """Initialize configured data providers"""
        # Temporarily disabled for testing
        # if settings.ALPHA_VANTAGE_API_KEY:
        #     # Create base Alpha Vantage provider
        #     alpha_vantage = AlphaVantageProvider({
        #         'name': 'alpha_vantage',
        #         'api_key': settings.ALPHA_VANTAGE_API_KEY,
        #         'rate_limit': getattr(settings, 'ALPHA_VANTAGE_RATE_LIMIT', 5),
        #         'timeout': 30
        #     })
        #     
        #     # Wrap with circuit breaker
        #     self.providers['alpha_vantage'] = CircuitBreakerDataProvider(
        #         alpha_vantage, 
        #         'alpha_vantage_circuit'
        #     )
        
        # Add more providers as needed
        # if settings.YAHOO_FINANCE_ENABLED:
        #     self.providers['yahoo_finance'] = YahooFinanceProvider(...)
    
    # @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_stock_price(self, symbol: str, date: Optional[date] = None,
                              provider: Optional[str] = None, swr: bool = False) -> FinancialData:
        """Get stock price with fallback providers + caching, LKG, and optional SWR"""
        cache_key = self._ck("price", symbol, date.isoformat() if date else "latest")
        lkg = self._cache_get(cache_key)

        if lkg is not None:
            self._record_cache_hit()
            # SWR: return cached and refresh in background
            if swr:
                self._bg_refresh("price", symbol, date, provider, cache_key)
            return lkg

        self._record_cache_miss()
        providers_to_try = [provider] if (provider and provider in self.providers) else list(self.providers.keys())
        last_error = None

        for provider_name in providers_to_try:
            start = time.time()
            status = "success"
            try:
                async with self.providers[provider_name] as provider_instance:
                    val = await provider_instance.get_stock_price(symbol, date)
                    self._cache_set(cache_key, val, self._cache_ttl)
                    self._observe_provider(provider_name, "price", time.time() - start, status)
                    return val
            except Exception as e:
                last_error = e
                status = "error"
                self._observe_provider(provider_name, "price", time.time() - start, status)
                continue

        if lkg is not None:
            return lkg  # LKG graceful degradation

        raise DataProviderError(f"All providers failed for {symbol}: {last_error}")
    
    # @cache_result(ttl=3600)  # Cache for 1 hour
    async def get_financial_statements(self, symbol: str, statement_type: str,
                                       provider: Optional[str] = None, swr: bool = False) -> List[FinancialData]:
        """Get financial statements with fallback providers + caching, LKG, and optional SWR"""
        cache_key = self._ck("statements", symbol, statement_type)
        lkg = self._cache_get(cache_key)
        if lkg is not None:
            self._record_cache_hit()
            if swr:
                self._bg_refresh("statements", symbol, statement_type, provider, cache_key)
            return lkg

        self._record_cache_miss()
        providers_to_try = [provider] if (provider and provider in self.providers) else list(self.providers.keys())
        last_error = None

        for provider_name in providers_to_try:
            start = time.time()
            status = "success"
            try:
                async with self.providers[provider_name] as provider_instance:
                    val = await provider_instance.get_financial_statements(symbol, statement_type)
                    self._cache_set(cache_key, val, max(self._cache_ttl, 3600))
                    self._observe_provider(provider_name, "statements", time.time() - start, status)
                    return val
            except Exception as e:
                last_error = e
                status = "error"
                self._observe_provider(provider_name, "statements", time.time() - start, status)
                continue

        if lkg is not None:
            return lkg

        raise DataProviderError(f"All providers failed for {symbol}: {last_error}")
    
    # @cache_result(ttl=86400)  # Cache for 24 hours
    async def get_company_info(self, symbol: str, provider: Optional[str] = None, swr: bool = False) -> FinancialData:
        """Get company info with fallback providers + caching, LKG, and optional SWR"""
        cache_key = self._ck("company", symbol)
        lkg = self._cache_get(cache_key)
        if lkg is not None:
            self._record_cache_hit()
            if swr:
                self._bg_refresh("company", symbol, None, provider, cache_key)
            return lkg

        self._record_cache_miss()
        providers_to_try = [provider] if (provider and provider in self.providers) else list(self.providers.keys())
        last_error = None

        for provider_name in providers_to_try:
            start = time.time()
            status = "success"
            try:
                async with self.providers[provider_name] as provider_instance:
                    val = await provider_instance.get_company_info(symbol)
                    self._cache_set(cache_key, val, max(self._cache_ttl, 86400))
                    self._observe_provider(provider_name, "company", time.time() - start, status)
                    return val
            except Exception as e:
                last_error = e
                status = "error"
                self._observe_provider(provider_name, "company", time.time() - start, status)
                continue

        if lkg is not None:
            return lkg

        raise DataProviderError(f"All providers failed for {symbol}: {last_error}")
    
    # @cache_result(ttl=3600)  # Cache for 1 hour
    async def search_symbols(self, query: str, provider: Optional[str] = None, swr: bool = False) -> List[Dict[str, Any]]:
        """Search symbols with fallback providers + caching, LKG, and optional SWR"""
        cache_key = self._ck("search", query)
        lkg = self._cache_get(cache_key)
        if lkg is not None:
            self._record_cache_hit()
            if swr:
                self._bg_refresh("search", query, None, provider, cache_key)
            return lkg

        self._record_cache_miss()
        providers_to_try = [provider] if (provider and provider in self.providers) else list(self.providers.keys())
        last_error = None

        for provider_name in providers_to_try:
            start = time.time()
            status = "success"
            try:
                async with self.providers[provider_name] as provider_instance:
                    val = await provider_instance.search_symbols(query)
                    self._cache_set(cache_key, val, max(self._cache_ttl, 3600))
                    self._observe_provider(provider_name, "search", time.time() - start, status)
                    return val
            except Exception as e:
                last_error = e
                status = "error"
                self._observe_provider(provider_name, "search", time.time() - start, status)
                continue

        if lkg is not None:
            return lkg

        raise DataProviderError(f"All providers failed for search '{query}': {last_error}")
    
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

    # -------------------------
    # Internal cache helpers
    # -------------------------
    def _ck(self, *parts: Any) -> str:
        # [P5] tenant-aware key, default "default" if no request context
        tenant = "default"
        try:
            if has_request_context() and request is not None:
                tenant = request.headers.get("X-Tenant-ID", "default")
        except Exception:
            tenant = "default"
        return ":".join([self._redis_prefix, tenant, *[str(p) for p in parts]])

    def _cache_get(self, key: str):
        now = time.time()
        # Redis first if configured
        if self._cache_redis is not None:
            try:
                raw = self._cache_redis.get(key)
                if raw is not None:
                    import json as _json
                    obj = _json.loads(raw)
                    if obj.get("exp", 0) >= now:
                        return obj.get("val")
            except Exception:
                pass
        # Fallback to memory
        entry = self._cache_mem.get(key)
        if entry and entry.get("exp", 0) >= now:
            return entry.get("val")
        # cleanup stale
        if entry:
            self._cache_mem.pop(key, None)
        return None

    def _cache_set(self, key: str, value: Any, ttl: int):
        exp = time.time() + max(1, int(ttl))
        # Redis set
        if self._cache_redis is not None:
            try:
                import json as _json
                self._cache_redis.setex(key, int(ttl), _json.dumps({"exp": exp, "val": value}, default=str))
            except Exception:
                pass
        # Memory set
        self._cache_mem[key] = {"exp": exp, "val": value}
        # [P5] update hit ratio gauge if available
        self._publish_hit_ratio()

# Global provider manager instance
provider_manager = DataProviderManager()

# -------------------------
# [P5] Internal helpers for metrics and SWR
# -------------------------
    # Note: Define instance methods at class indentation level above. Adding here as free funcs for clarity would not bind.
