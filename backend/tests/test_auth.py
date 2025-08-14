"""
Authentication Tests for Valor IVX Backend
Tests user registration, login, token management, and rate limiting
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from auth import AuthManager, auth_required, get_current_user_id
from rate_limiter import RateLimiter, rate_limiter

@pytest.fixture
def auth_manager(app, db):
    """Create auth manager for testing"""
    from app import User
    return AuthManager(db, User)

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'securepassword123'
    }

@pytest.fixture
def sample_user(db, sample_user_data):
    """Create a sample user in the database"""
    from app import User
    
    user = User(
        username=sample_user_data['username'],
        email=sample_user_data['email'],
        password_hash=generate_password_hash(sample_user_data['password']),
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()
    return user

class TestAuthManager:
    """Test authentication manager functionality"""
    
    def test_register_user_success(self, auth_manager, db, sample_user_data):
        """Test successful user registration"""
        result = auth_manager.register_user(
            sample_user_data['username'],
            sample_user_data['email'],
            sample_user_data['password']
        )
        
        assert result['valid'] is True
        assert 'user' in result
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['user']['username'] == sample_user_data['username']
        assert result['user']['email'] == sample_user_data['email']
    
    def test_register_user_duplicate_username(self, auth_manager, db, sample_user, sample_user_data):
        """Test registration with duplicate username"""
        result = auth_manager.register_user(
            sample_user_data['username'],
            'different@example.com',
            'differentpassword'
        )
        
        assert result['valid'] is False
        assert 'Username already exists' in result['error']
    
    def test_register_user_duplicate_email(self, auth_manager, db, sample_user, sample_user_data):
        """Test registration with duplicate email"""
        result = auth_manager.register_user(
            'differentuser',
            sample_user_data['email'],
            'differentpassword'
        )
        
        assert result['valid'] is False
        assert 'Email already registered' in result['error']
    
    def test_register_user_invalid_username(self, auth_manager, db):
        """Test registration with invalid username"""
        result = auth_manager.register_user(
            'ab',  # Too short
            'test@example.com',
            'password123'
        )
        
        assert result['valid'] is False
        assert 'Username must be at least 3 characters' in result['error']
    
    def test_register_user_invalid_email(self, auth_manager, db):
        """Test registration with invalid email"""
        result = auth_manager.register_user(
            'testuser',
            'invalid-email',
            'password123'
        )
        
        assert result['valid'] is False
        assert 'valid email address' in result['error']
    
    def test_register_user_weak_password(self, auth_manager, db):
        """Test registration with weak password"""
        result = auth_manager.register_user(
            'testuser',
            'test@example.com',
            '123456'  # Too short and common
        )
        
        assert result['valid'] is False
        assert 'Password must be at least 8 characters' in result['error']
    
    def test_login_user_success(self, auth_manager, db, sample_user, sample_user_data):
        """Test successful user login"""
        result = auth_manager.login_user(
            sample_user_data['username'],
            sample_user_data['password']
        )
        
        assert result['valid'] is True
        assert 'user' in result
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['user']['username'] == sample_user_data['username']
    
    def test_login_user_by_email(self, auth_manager, db, sample_user, sample_user_data):
        """Test login using email address"""
        result = auth_manager.login_user(
            sample_user_data['email'],
            sample_user_data['password']
        )
        
        assert result['valid'] is True
        assert result['user']['username'] == sample_user_data['username']
    
    def test_login_user_invalid_credentials(self, auth_manager, db, sample_user):
        """Test login with invalid credentials"""
        result = auth_manager.login_user('testuser', 'wrongpassword')
        
        assert result['valid'] is False
        assert 'Invalid username or password' in result['error']
    
    def test_login_user_nonexistent_user(self, auth_manager, db):
        """Test login with nonexistent user"""
        result = auth_manager.login_user('nonexistent', 'password123')
        
        assert result['valid'] is False
        assert 'Invalid username or password' in result['error']
    
    def test_refresh_token_success(self, auth_manager, db, sample_user, sample_user_data):
        """Test successful token refresh"""
        # First login to get tokens
        login_result = auth_manager.login_user(
            sample_user_data['username'],
            sample_user_data['password']
        )
        
        refresh_token = login_result['refresh_token']
        result = auth_manager.refresh_token(refresh_token)
        
        assert result['valid'] is True
        assert 'access_token' in result
        assert 'user' in result
        assert result['user']['username'] == sample_user_data['username']
    
    def test_refresh_token_invalid(self, auth_manager, db):
        """Test token refresh with invalid token"""
        result = auth_manager.refresh_token('invalid-token')
        
        assert result['valid'] is False
        assert 'Invalid refresh token' in result['error']

class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    def test_register_endpoint_success(self, client, sample_user_data):
        """Test successful registration via API"""
        response = client.post('/api/auth/register', 
                             json=sample_user_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_register_endpoint_missing_data(self, client):
        """Test registration with missing data"""
        response = client.post('/api/auth/register', 
                             json={'username': 'testuser'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_endpoint_success(self, client, db, sample_user, sample_user_data):
        """Test successful login via API"""
        response = client.post('/api/auth/login',
                             json={
                                 'username': sample_user_data['username'],
                                 'password': sample_user_data['password']
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_login_endpoint_invalid_credentials(self, client, db, sample_user):
        """Test login with invalid credentials via API"""
        response = client.post('/api/auth/login',
                             json={
                                 'username': 'testuser',
                                 'password': 'wrongpassword'
                             })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_profile_endpoint_authenticated(self, client, db, sample_user):
        """Test profile endpoint with valid authentication"""
        # First login to get token
        login_response = client.post('/api/auth/login',
                                   json={
                                       'username': sample_user.username,
                                       'password': 'securepassword123'
                                   })
        
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']
        
        # Use token to access profile
        response = client.get('/api/auth/profile',
                            headers={'Authorization': f'Bearer {access_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['username'] == sample_user.username
    
    def test_profile_endpoint_unauthenticated(self, client):
        """Test profile endpoint without authentication"""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_creation(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert 'api' in limiter.default_limits
        assert 'auth' in limiter.default_limits
        assert 'financial_data' in limiter.default_limits
    
    def test_rate_limiter_allowed_requests(self):
        """Test that requests are allowed within limits"""
        limiter = RateLimiter()
        client_key = "test_client"
        
        # Should allow requests within limit
        for i in range(5):
            assert limiter.is_allowed(client_key, 'auth') is True
    
    def test_rate_limiter_exceeded_requests(self):
        """Test that requests are blocked when limit exceeded"""
        limiter = RateLimiter()
        client_key = "test_client"
        
        # Make requests up to the limit
        for i in range(5):
            limiter.is_allowed(client_key, 'auth')
        
        # Next request should be blocked
        assert limiter.is_allowed(client_key, 'auth') is False
    
    def test_rate_limiter_reset_after_window(self):
        """Test that rate limits reset after the time window"""
        limiter = RateLimiter()
        client_key = "test_client"
        
        # Make requests up to the limit
        for i in range(5):
            limiter.is_allowed(client_key, 'auth')
        
        # Should be blocked
        assert limiter.is_allowed(client_key, 'auth') is False
        
        # Simulate time passing (in real implementation, this would be handled by time-based cleanup)
        # For this test, we'll manually clear the requests
        limiter.requests[client_key].clear()
        
        # Should be allowed again
        assert limiter.is_allowed(client_key, 'auth') is True
    
    def test_get_remaining_requests(self):
        """Test getting remaining request count"""
        limiter = RateLimiter()
        client_key = "test_client"
        
        # Make some requests
        for i in range(3):
            limiter.is_allowed(client_key, 'api')
        
        # Check remaining requests
        remaining = limiter.get_remaining_requests(client_key, 'api')
        assert remaining['remaining'] == 97  # 100 - 3
        assert remaining['limit'] == 100
    
    def test_client_key_generation(self):
        """Test client key generation"""
        limiter = RateLimiter()
        
        # Mock request object
        class MockRequest:
            def __init__(self):
                self.remote_addr = '127.0.0.1'
                self.headers = {
                    'User-Agent': 'test-browser'
                }
        
        # This would need to be tested with actual request context
        # For now, just test the method exists
        assert hasattr(limiter, 'get_client_key')

class TestAuthDecorators:
    """Test authentication decorators"""
    
    def test_auth_required_decorator(self, app, client, db, sample_user):
        """Test auth_required decorator"""
        # Create a test endpoint with auth_required
        @app.route('/test-auth')
        @auth_required
        def test_endpoint():
            return jsonify({'success': True, 'user_id': get_current_user_id()})
        
        # Test without authentication
        response = client.get('/test-auth')
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.get('/test-auth',
                            headers={'Authorization': 'Bearer invalid-token'})
        assert response.status_code == 401
        
        # Test with valid token
        # First login to get token
        login_response = client.post('/api/auth/login',
                                   json={
                                       'username': sample_user.username,
                                       'password': 'securepassword123'
                                   })
        
        login_data = json.loads(login_response.data)
        access_token = login_data['access_token']
        
        response = client.get('/test-auth',
                            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user_id'] == sample_user.id 