"""
Security Configuration for Valor IVX
Centralized security settings and validation functions
"""

import os
import re
import secrets
from typing import Dict, Any, Optional
from datetime import timedelta

class SecurityConfig:
    """Centralized security configuration"""
    
    # Password policy
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = False  # Optional for better UX
    
    # Session security
    SESSION_TIMEOUT = timedelta(hours=24)
    REFRESH_TOKEN_TIMEOUT = timedelta(days=30)
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)
    
    # Rate limiting
    API_RATE_LIMIT = 100  # requests per minute
    AUTH_RATE_LIMIT = 5   # login attempts per minute
    FINANCIAL_DATA_RATE_LIMIT = 30  # requests per minute
    
    # Input validation
    MAX_TICKER_LENGTH = 10
    MAX_USERNAME_LENGTH = 50
    MAX_EMAIL_LENGTH = 254
    MAX_NOTE_LENGTH = 10000
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:;",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
    
    # Weak passwords to reject
    WEAK_PASSWORDS = {
        'password', '123456', 'qwerty', 'admin', 'letmein', 'welcome',
        'password123', 'admin123', 'root', 'guest', 'user', 'test',
        '123456789', '12345678', '1234567', '1234567890'
    }
    
    @classmethod
    def validate_password(cls, password: str) -> Dict[str, Any]:
        """Validate password against security policy"""
        if not password:
            return {'valid': False, 'error': 'Password is required'}
        
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            return {'valid': False, 'error': f'Password must be at least {cls.MIN_PASSWORD_LENGTH} characters'}
        
        if len(password) > cls.MAX_PASSWORD_LENGTH:
            return {'valid': False, 'error': f'Password must be no more than {cls.MAX_PASSWORD_LENGTH} characters'}
        
        if password.lower() in cls.WEAK_PASSWORDS:
            return {'valid': False, 'error': 'Password is too common, please choose a stronger password'}
        
        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return {'valid': False, 'error': 'Password must contain at least one uppercase letter'}
        
        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return {'valid': False, 'error': 'Password must contain at least one lowercase letter'}
        
        if cls.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            return {'valid': False, 'error': 'Password must contain at least one number'}
        
        if cls.REQUIRE_SPECIAL and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return {'valid': False, 'error': 'Password must contain at least one special character'}
        
        return {'valid': True}
    
    @classmethod
    def validate_username(cls, username: str) -> Dict[str, Any]:
        """Validate username"""
        if not username:
            return {'valid': False, 'error': 'Username is required'}
        
        if len(username) < 3:
            return {'valid': False, 'error': 'Username must be at least 3 characters'}
        
        if len(username) > cls.MAX_USERNAME_LENGTH:
            return {'valid': False, 'error': f'Username must be no more than {cls.MAX_USERNAME_LENGTH} characters'}
        
        # Only allow alphanumeric, underscore, and hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return {'valid': False, 'error': 'Username can only contain letters, numbers, underscores, and hyphens'}
        
        return {'valid': True}
    
    @classmethod
    def validate_email(cls, email: str) -> Dict[str, Any]:
        """Validate email address"""
        if not email:
            return {'valid': False, 'error': 'Email is required'}
        
        if len(email) > cls.MAX_EMAIL_LENGTH:
            return {'valid': False, 'error': f'Email must be no more than {cls.MAX_EMAIL_LENGTH} characters'}
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return {'valid': False, 'error': 'Please provide a valid email address'}
        
        return {'valid': True}
    
    @classmethod
    def validate_ticker(cls, ticker: str) -> Dict[str, Any]:
        """Validate stock ticker symbol"""
        if not ticker:
            return {'valid': False, 'error': 'Ticker symbol is required'}
        
        if len(ticker) > cls.MAX_TICKER_LENGTH:
            return {'valid': False, 'error': f'Ticker symbol must be no more than {cls.MAX_TICKER_LENGTH} characters'}
        
        # Only allow alphanumeric characters
        if not re.match(r'^[A-Za-z0-9]+$', ticker):
            return {'valid': False, 'error': 'Ticker symbol can only contain letters and numbers'}
        
        return {'valid': True}
    
    @classmethod
    def sanitize_input(cls, input_str: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input"""
        if not input_str:
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    def get_environment_secrets(cls) -> Dict[str, str]:
        """Get required environment secrets with validation"""
        secrets = {}
        
        # Required secrets
        required_secrets = ['SECRET_KEY', 'JWT_SECRET_KEY']
        
        for secret_name in required_secrets:
            secret_value = os.environ.get(secret_name)
            if not secret_value:
                if os.environ.get('FLASK_ENV') == 'production':
                    raise ValueError(f"{secret_name} environment variable is required in production")
                # Use development defaults
                if secret_name == 'SECRET_KEY':
                    secret_value = 'dev-secret-key-change-in-production'
                elif secret_name == 'JWT_SECRET_KEY':
                    secret_value = 'jwt-secret-key-change-in-production'
            
            secrets[secret_name] = secret_value
        
        return secrets