"""
Production Configuration for Valor IVX Backend
Contains production-specific settings and security configurations
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration class"""
    
    # Flask Configuration
    DEBUG = False
    TESTING = False
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required for production")
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is required for production")
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Shorter token lifetime for security
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_ERROR_MESSAGE_KEY = 'error'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required for production")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    if not CORS_ORIGINS or CORS_ORIGINS == ['']:
        CORS_ORIGINS = ['https://valor-ivx.com', 'https://www.valor-ivx.com']
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Alpha Vantage Configuration
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not ALPHA_VANTAGE_API_KEY:
        print("WARNING: ALPHA_VANTAGE_API_KEY not set. Financial data features will be disabled.")
    
    # Redis Configuration (for caching and sessions)
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # Session Configuration
    SESSION_TYPE = 'redis' if REDIS_URL else 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Validate Redis in production
    if os.environ.get('FLASK_ENV') == 'production':
        if not REDIS_URL:
            raise ValueError("REDIS_URL environment variable is required for production")
    
    # Enhanced Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://www.alphavantage.co; frame-ancestors 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'X-Download-Options': 'noopen',
        'X-Permitted-Cross-Domain-Policies': 'none',
        'X-DNS-Prefetch-Control': 'off'
    }
    
    # SSL/HTTPS Configuration
    SSL_ENABLED = os.environ.get('SSL_ENABLED', 'true').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH')
    
    # Validate SSL certificates in production
    if os.environ.get('FLASK_ENV') == 'production' and SSL_ENABLED:
        if not SSL_CERT_PATH or not SSL_KEY_PATH:
            raise ValueError("SSL_CERT_PATH and SSL_KEY_PATH are required for production HTTPS")
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = '/tmp/valor_ivx_uploads'
    
    # Validate upload settings in production
    if os.environ.get('FLASK_ENV') == 'production':
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Validate email settings in production
    if os.environ.get('FLASK_ENV') == 'production':
        if not MAIL_SERVER or not MAIL_USERNAME or not MAIL_PASSWORD:
            raise ValueError("MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD are required for production email notifications")
        if not MAIL_DEFAULT_SENDER:
            MAIL_DEFAULT_SENDER = f"no-reply@valor-ivx.com"
    
    # Monitoring Configuration
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'false').lower() == 'true'
    METRICS_PORT = int(os.environ.get('METRICS_PORT', 9090))
    
    # Backup Configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    
    # Performance Configuration
    WORKER_PROCESSES = int(os.environ.get('WORKER_PROCESSES', 4))
    WORKER_TIMEOUT = int(os.environ.get('WORKER_TIMEOUT', 120))
    WORKER_MAX_REQUESTS = int(os.environ.get('WORKER_MAX_REQUESTS', 1000))
    
    # Cache Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis' if REDIS_URL else 'simple')
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    @staticmethod
    def init_app(app):
        """Initialize application with production settings"""
        
        # Set up logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # File handler
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                'logs/valor_ivx.log', 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            app.logger.addHandler(console_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Valor IVX startup')
        
        # Enhanced security headers middleware
        @app.after_request
        def add_security_headers(response):
            # Add all security headers
            for header, value in ProductionConfig.SECURITY_HEADERS.items():
                response.headers[header] = value
            
            # Add additional security headers based on environment
            if ProductionConfig.SSL_ENABLED:
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # Add cache control headers for API responses
            if response.headers.get('Content-Type', '').startswith('application/json'):
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            
            return response
        
        # Enhanced error handling
        @app.errorhandler(404)
        def not_found_error(error):
            return {'error': 'Not found'}, 404
        
        @app.errorhandler(500)
        def internal_error(error):
            app.logger.error(f'Server Error: {error}')
            return {'error': 'Internal server error'}, 500
        
        @app.errorhandler(413)
        def too_large(error):
            return {'error': 'File too large'}, 413
        
        @app.errorhandler(429)
        def too_many_requests(error):
            return {'error': 'Too many requests'}, 429
        
        @app.errorhandler(401)
        def unauthorized(error):
            return {'error': 'Unauthorized'}, 401
        
        @app.errorhandler(403)
        def forbidden(error):
            return {'error': 'Forbidden'}, 403

class StagingConfig(ProductionConfig):
    """Staging configuration (similar to production but with some debugging)"""
    
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Allow more CORS origins for testing
    CORS_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'https://staging.valor-ivx.com',
        'https://valor-ivx-staging.herokuapp.com'
    ]
    
    # Less strict security for staging
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://www.alphavantage.co;"
    }
    
    # Disable SSL requirement for staging
    SSL_ENABLED = False

class DevelopmentConfig(ProductionConfig):
    """Development configuration"""
    
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Allow all CORS origins for development
    CORS_ORIGINS = ['*']
    
    # Minimal security for development
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff'
    }
    
    # Disable SSL requirement for development
    SSL_ENABLED = False
    
    # Use in-memory database for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable rate limiting for development
    RATE_LIMIT_ENABLED = False
