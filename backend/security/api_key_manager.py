"""
API key management system for external data providers.

This module provides secure API key management with rotation,
rate limiting, and usage tracking.
"""

import hashlib
import secrets
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
# from backend.cache import cache_result  # Commented out for now

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
        # from backend.settings import settings  # Commented out for now
        
        # Load Alpha Vantage keys
        # if settings.ALPHA_VANTAGE_API_KEY:
        #     self.add_key(
        #         name="alpha_vantage_primary",
        #         key=settings.ALPHA_VANTAGE_API_KEY,
        #         provider="alpha_vantage"
        #     )
        # 
        # # Load backup keys if available
        # if hasattr(settings, 'ALPHA_VANTAGE_BACKUP_KEYS'):
        #     for i, key in enumerate(settings.ALPHA_VANTAGE_BACKUP_KEYS):
        #         self.add_key(
        #             name=f"alpha_vantage_backup_{i+1}",
        #             key=key,
        #             provider="alpha_vantage"
        #         )
    
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
    
    def get_provider_keys(self, provider: str) -> List[APIKey]:
        """Get all keys for a specific provider"""
        return [key for key in self.keys.values() if key.provider == provider]
    
    def deactivate_key(self, key_name: str):
        """Deactivate a specific API key"""
        if key_name in self.keys:
            self.keys[key_name].is_active = False
    
    def activate_key(self, key_name: str):
        """Activate a specific API key"""
        if key_name in self.keys:
            self.keys[key_name].is_active = True

# Global API key manager
api_key_manager = APIKeyManager() 