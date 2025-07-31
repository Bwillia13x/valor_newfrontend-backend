#!/usr/bin/env python3
"""
Valor IVX Backend Server Startup Script
"""

import os
import sys
from app import app, init_db

def main():
    """Main entry point for the backend server"""
    
    # Set environment
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(f'config.{env.capitalize()}Config')
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Get port from environment or default
    port = int(os.environ.get('PORT', 5002))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = app.config.get('DEBUG', True)
    
    print(f"Starting Valor IVX Backend Server...")
    print(f"Environment: {env}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"API URL: http://{host}:{port}")
    print(f"Debug: {debug}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("-" * 50)
    
    # Start the server
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )

if __name__ == '__main__':
    main() 