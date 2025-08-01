"""
Authentication Module for Valor IVX
Handles user registration, login, JWT token management, and password hashing
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

class AuthManager:
    """Authentication manager for user operations"""
    
    def __init__(self, db, User):
        self.db = db
        self.User = User
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user with validation"""
        try:
            # Validate input
            validation_result = self._validate_registration_data(username, email, password)
            if not validation_result['valid']:
                return validation_result
            
            # Check if user already exists
            if self.User.query.filter_by(username=username).first():
                return {
                    'valid': False,
                    'error': 'Username already exists'
                }
            
            if self.User.query.filter_by(email=email).first():
                return {
                    'valid': False,
                    'error': 'Email already registered'
                }
            
            # Create new user (bcrypt)
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            new_user = self.User(
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            
            self.db.session.add(new_user)
            self.db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=new_user.id)
            refresh_token = create_refresh_token(identity=new_user.id)
            
            return {
                'valid': True,
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
        except Exception as e:
            self.db.session.rollback()
            return {
                'valid': False,
                'error': f'Registration failed: {str(e)}'
            }
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        try:
            # Find user by username or email
            user = self.User.query.filter(
                (self.User.username == username) | (self.User.email == username)
            ).first()
            
            if not user:
                return {
                    'valid': False,
                    'error': 'Invalid username or password'
                }
            
            # Check password (bcrypt)
            try:
                valid_pw = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
            except Exception:
                valid_pw = False
            if not valid_pw:
                return {
                    'valid': False,
                    'error': 'Invalid username or password'
                }
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            return {
                'valid': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Login failed: {str(e)}'
            }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            user_id = payload.get('sub')
            if not user_id:
                return {
                    'valid': False,
                    'error': 'Invalid refresh token'
                }
            
            # Verify user exists
            user = self.User.query.get(user_id)
            if not user:
                return {
                    'valid': False,
                    'error': 'User not found'
                }
            
            # Generate new access token
            new_access_token = create_access_token(identity=user.id)
            
            return {
                'valid': True,
                'access_token': new_access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'error': 'Refresh token expired'
            }
        except jwt.InvalidTokenError:
            return {
                'valid': False,
                'error': 'Invalid refresh token'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Token refresh failed: {str(e)}'
            }
    
    def _validate_registration_data(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Validate registration data"""
        # Username validation
        if not username or len(username) < 3:
            return {
                'valid': False,
                'error': 'Username must be at least 3 characters long'
            }
        
        if not username.replace('_', '').replace('-', '').isalnum():
            return {
                'valid': False,
                'error': 'Username can only contain letters, numbers, underscores, and hyphens'
            }
        
        # Email validation
        if not email or not EMAIL_REGEX.match(email):
            return {
                'valid': False,
                'error': 'Please provide a valid email address'
            }
        
        # Password validation
        if not password or len(password) < 8:
            return {
                'valid': False,
                'error': 'Password must be at least 8 characters long'
            }
        
        # Check for common password patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            return {
                'valid': False,
                'error': 'Password is too common'
            }
        
        return {'valid': True}

def auth_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check for Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Authorization header required'}), 401
            
            # Extract token
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Invalid authorization header format'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Add user_id to request context
            request.user_id = payload.get('sub')
            if not request.user_id:
                return jsonify({'error': 'Invalid token'}), 401
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': f'Authentication failed: {str(e)}'}), 401
    
    return decorated_function

def get_current_user_id() -> Optional[int]:
    """Get current user ID from request context"""
    return getattr(request, 'user_id', None)
