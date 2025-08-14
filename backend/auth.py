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
        
        # Password validation with comprehensive complexity requirements
        password_validation = self._validate_password_complexity(password)
        if not password_validation['valid']:
            return password_validation
        
        # Check for common password patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            return {
                'valid': False,
                'error': 'Password is too common'
            }
        
        return {'valid': True}
    
    def _validate_password_complexity(self, password: str) -> Dict[str, Any]:
        """Validate password complexity for financial application security"""
        if not password:
            return {
                'valid': False,
                'error': 'Password cannot be empty'
            }
        
        # Minimum length requirement
        if len(password) < 12:
            return {
                'valid': False,
                'error': 'Password must be at least 12 characters long'
            }
        
        # Maximum length to prevent DoS attacks
        if len(password) > 128:
            return {
                'valid': False,
                'error': 'Password cannot exceed 128 characters'
            }
        
        # Character complexity requirements
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+=\[\]{}|\\:";\'<>?,./~`-]', password))
        
        missing_requirements = []
        if not has_lower:
            missing_requirements.append('lowercase letters')
        if not has_upper:
            missing_requirements.append('uppercase letters')
        if not has_digit:
            missing_requirements.append('numbers')
        if not has_special:
            missing_requirements.append('special characters')
        
        if missing_requirements:
            return {
                'valid': False,
                'error': f'Password must contain: {", ".join(missing_requirements)}'
            }
        
        # Check for sequential characters (123, abc, etc.)
        if self._has_sequential_chars(password):
            return {
                'valid': False,
                'error': 'Password cannot contain sequential characters (123, abc, etc.)'
            }
        
        # Check for repeated characters (aaa, 111, etc.)
        if self._has_repeated_chars(password, max_repeats=3):
            return {
                'valid': False,
                'error': 'Password cannot contain more than 2 consecutive identical characters'
            }
        
        # Check against common patterns
        if self._has_common_patterns(password):
            return {
                'valid': False,
                'error': 'Password contains common patterns and is not secure enough'
            }
        
        # Check for keyboard patterns (qwerty, asdf, etc.)
        if self._has_keyboard_patterns(password):
            return {
                'valid': False,
                'error': 'Password cannot contain keyboard patterns (qwerty, asdf, etc.)'
            }
        
        return {'valid': True}
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters in password"""
        sequences = [
            'abcdefghijklmnopqrstuvwxyz',
            '0123456789',
            'zyxwvutsrqponmlkjihgfedcba',
            '9876543210'
        ]
        
        password_lower = password.lower()
        for sequence in sequences:
            for i in range(len(sequence) - 2):
                if sequence[i:i+3] in password_lower:
                    return True
        
        return False
    
    def _has_repeated_chars(self, password: str, max_repeats: int = 3) -> bool:
        """Check for repeated characters"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                count += 1
                if count >= max_repeats:
                    return True
            else:
                count = 1
        
        return False
    
    def _has_common_patterns(self, password: str) -> bool:
        """Check for common password patterns"""
        password_lower = password.lower()
        
        # Common patterns to avoid
        common_patterns = [
            'password', 'admin', 'login', 'user', 'test',
            'welcome', 'default', 'secret', 'master', 'root',
            'valor', 'finance', 'money', 'investment', 'trading',
            'dcf', 'portfolio', 'stock', 'market', 'analysis'
        ]
        
        for pattern in common_patterns:
            if pattern in password_lower:
                return True
        
        # Check for simple substitutions (password -> p@ssw0rd)
        substitutions = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$', 't': '7'}
        for pattern in common_patterns:
            substituted = pattern
            for char, sub in substitutions.items():
                substituted = substituted.replace(char, sub)
            if substituted in password:
                return True
        
        return False
    
    def _has_keyboard_patterns(self, password: str) -> bool:
        """Check for keyboard patterns"""
        password_lower = password.lower()
        
        # Common keyboard patterns
        keyboard_patterns = [
            'qwerty', 'qwertyuiop', 'asdf', 'asdfghjkl', 'zxcv', 'zxcvbnm',
            'yuiop', 'hjkl', 'bnm', '1234', '567890',
            # Reverse patterns
            'ytrewq', 'poiuytrewq', 'fdsa', 'lkjhgfdsa', 'vcxz', 'mnbvcxz',
            '0987', '65432'
        ]
        
        for pattern in keyboard_patterns:
            if len(pattern) >= 4 and pattern in password_lower:
                return True
        
        return False

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
