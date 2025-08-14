"""
Response Utilities
Provides helper functions for creating standardized API responses.
"""

from flask import jsonify

def create_response(message, data=None, status_code=200):
    """Creates a standardized success response."""
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['result'] = data
    return jsonify(response), status_code

def create_error_response(message, status_code):
    """Creates a standardized error response."""
    response = {
        'success': False,
        'error': message
    }
    return jsonify(response), status_code

def success_response(data=None, message="Success"):
    """Creates a standardized success response."""
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response)

def error_response(message, status_code=400):
    """Creates a standardized error response."""
    response = {
        'success': False,
        'error': message
    }
    return jsonify(response), status_code
