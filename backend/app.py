"""
Valor IVX Backend API
Advanced DCF Modeling Tool Backend

This Flask application provides the backend API for the Valor IVX frontend,
handling data persistence, user management, and financial analysis storage.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt
)

# Import financial data module
from financial_data import financial_api, parse_financial_data, calculate_dcf_inputs

# Import WebSocket manager
from websocket_manager import websocket_manager

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///valor_ivx.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# Initialize Flask app
app = Flask(__name__, static_folder='../', static_url_path='')
app.config.from_object(Config)

# Initialize extensions
CORS(app, origins=['http://localhost:8000', 'http://127.0.0.1:8000', 'http://localhost:5001', 'http://127.0.0.1:5001'])
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Initialize WebSocket manager with app
websocket_manager.init_app(app)

# Database Models
class User(db.Model):
    """User model for authentication and data ownership"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    runs = db.relationship('Run', backref='user', lazy=True, cascade='all, delete-orphan')
    scenarios = db.relationship('Scenario', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')

class Run(db.Model):
    """DCF analysis run data"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    ticker = db.Column(db.String(20), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    mc_settings = db.Column(db.Text)  # JSON
    results = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'run_id': self.run_id,
            'ticker': self.ticker,
            'inputs': json.loads(self.inputs),
            'mc_settings': json.loads(self.mc_settings) if self.mc_settings else None,
            'results': json.loads(self.results) if self.results else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Scenario(db.Model):
    """Saved scenario data"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scenario_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    mc_settings = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'name': self.name,
            'ticker': self.ticker,
            'inputs': json.loads(self.inputs),
            'mc_settings': json.loads(self.mc_settings) if self.mc_settings else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Note(db.Model):
    """Analyst notes per ticker"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticker': self.ticker,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LBORun(db.Model):
    """LBO analysis run data"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    company_name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    results = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'run_id': self.run_id,
            'company_name': self.company_name,
            'inputs': json.loads(self.inputs),
            'results': json.loads(self.results) if self.results else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LBOScenario(db.Model):
    """Saved LBO scenario data"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scenario_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'name': self.name,
            'company_name': self.company_name,
            'inputs': json.loads(self.inputs),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MARun(db.Model):
    """M&A analysis run data"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    deal_name = db.Column(db.String(100), nullable=False)
    acquirer_name = db.Column(db.String(100), nullable=False)
    target_name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    results = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'run_id': self.run_id,
            'deal_name': self.deal_name,
            'acquirer_name': self.acquirer_name,
            'target_name': self.target_name,
            'inputs': json.loads(self.inputs),
            'results': json.loads(self.results) if self.results else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MAScenario(db.Model):
    """Saved M&A scenario data"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scenario_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(100), nullable=False)
    deal_name = db.Column(db.String(100), nullable=False)
    acquirer_name = db.Column(db.String(100), nullable=False)
    target_name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'name': self.name,
            'deal_name': self.deal_name,
            'acquirer_name': self.acquirer_name,
            'target_name': self.target_name,
            'inputs': json.loads(self.inputs),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Helper functions
def get_or_create_user() -> User:
    """Get or create a default user for demo purposes"""
    # In production, this would use proper authentication
    user = User.query.filter_by(username='demo_user').first()
    if not user:
        user = User(
            username='demo_user',
            email='demo@valor-ivx.com',
            password_hash='demo_hash'  # In production, use proper hashing
        )
        db.session.add(user)
        db.session.commit()
    return user

def validate_run_data(data: Dict[str, Any]) -> bool:
    """Validate run data structure"""
    required_fields = ['inputs', 'mc_settings', 'timestamp']
    return all(field in data for field in required_fields)

def validate_scenario_data(data: Dict[str, Any]) -> bool:
    """Validate scenario data structure"""
    required_fields = ['name', 'ticker', 'inputs']
    return all(field in data for field in required_fields)

# API Routes

@app.route('/')
def index():
    """Serve the main application"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Run Management Endpoints
@app.route('/api/runs', methods=['POST'])
def save_run():
    """Save a DCF analysis run"""
    try:
        data = request.get_json()
        if not data or not validate_run_data(data):
            return jsonify({'error': 'Invalid run data'}), 400
        
        user = get_or_create_user()
        
        # Create new run
        run = Run(
            user_id=user.id,
            run_id=str(uuid.uuid4()),
            ticker=data.get('inputs', {}).get('ticker', 'UNKNOWN'),
            inputs=json.dumps(data['inputs']),
            mc_settings=json.dumps(data['mc_settings']) if data.get('mc_settings') else None,
            results=json.dumps(data.get('results')) if data.get('results') else None
        )
        
        db.session.add(run)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'run_id': run.run_id,
            'message': 'Run saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/runs/last', methods=['GET'])
def get_last_run():
    """Get the most recent run for the user"""
    try:
        user = get_or_create_user()
        run = Run.query.filter_by(user_id=user.id).order_by(Run.updated_at.desc()).first()
        
        if not run:
            return jsonify({'error': 'No runs found'}), 404
        
        return jsonify({
            'success': True,
            'data': run.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    """Get a specific run by ID"""
    try:
        user = get_or_create_user()
        run = Run.query.filter_by(user_id=user.id, run_id=run_id).first()
        
        if not run:
            return jsonify({'error': 'Run not found'}), 404
        
        return jsonify({
            'success': True,
            'data': run.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runs', methods=['GET'])
def list_runs():
    """List all runs for the user"""
    try:
        user = get_or_create_user()
        runs = Run.query.filter_by(user_id=user.id).order_by(Run.updated_at.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'runs': [run.to_dict() for run in runs]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Scenario Management Endpoints
@app.route('/api/scenarios', methods=['POST'])
def save_scenarios():
    """Save multiple scenarios"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({'error': 'Invalid scenarios data'}), 400
        
        user = get_or_create_user()
        saved_count = 0
        
        for scenario_data in data:
            if not validate_scenario_data(scenario_data):
                continue
            
            # Check if scenario already exists
            existing = Scenario.query.filter_by(
                user_id=user.id,
                ticker=scenario_data['ticker'],
                name=scenario_data['name']
            ).first()
            
            if existing:
                # Update existing scenario
                existing.inputs = json.dumps(scenario_data['inputs'])
                existing.mc_settings = json.dumps(scenario_data.get('mc_settings')) if scenario_data.get('mc_settings') else None
                existing.updated_at = datetime.utcnow()
            else:
                # Create new scenario
                scenario = Scenario(
                    user_id=user.id,
                    scenario_id=str(uuid.uuid4()),
                    name=scenario_data['name'],
                    ticker=scenario_data['ticker'],
                    inputs=json.dumps(scenario_data['inputs']),
                    mc_settings=json.dumps(scenario_data.get('mc_settings')) if scenario_data.get('mc_settings') else None
                )
                db.session.add(scenario)
            
            saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'saved_count': saved_count,
            'message': f'{saved_count} scenarios saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get all scenarios for the user"""
    try:
        user = get_or_create_user()
        scenarios = Scenario.query.filter_by(user_id=user.id).order_by(Scenario.updated_at.desc()).all()
        
        return jsonify({
            'success': True,
            'scenarios': [scenario.to_dict() for scenario in scenarios]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scenarios/<scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    """Delete a specific scenario"""
    try:
        user = get_or_create_user()
        scenario = Scenario.query.filter_by(user_id=user.id, scenario_id=scenario_id).first()
        
        if not scenario:
            return jsonify({'error': 'Scenario not found'}), 404
        
        db.session.delete(scenario)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Scenario deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Financial Data API Endpoints
@app.route('/api/financial-data/<ticker>', methods=['GET'])
def get_financial_data(ticker):
    """Get comprehensive financial data for a ticker"""
    try:
        # Fetch data from Alpha Vantage
        overview_data = financial_api.get_company_overview(ticker)
        income_data = financial_api.get_income_statement(ticker)
        balance_data = financial_api.get_balance_sheet(ticker)
        cash_flow_data = financial_api.get_cash_flow(ticker)
        
        if not overview_data:
            return jsonify({
                'success': False,
                'error': 'No financial data found for this ticker'
            }), 404
        
        # Parse and structure the data
        parsed_data = parse_financial_data(overview_data, income_data, balance_data, cash_flow_data)
        
        return jsonify({
            'success': True,
            'data': parsed_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/financial-data/<ticker>/dcf-inputs', methods=['GET'])
def get_dcf_inputs(ticker):
    """Get DCF model inputs calculated from financial data"""
    try:
        # Fetch data from Alpha Vantage
        overview_data = financial_api.get_company_overview(ticker)
        income_data = financial_api.get_income_statement(ticker)
        balance_data = financial_api.get_balance_sheet(ticker)
        cash_flow_data = financial_api.get_cash_flow(ticker)
        
        if not overview_data:
            return jsonify({
                'success': False,
                'error': 'No financial data found for this ticker'
            }), 404
        
        # Parse and structure the data
        parsed_data = parse_financial_data(overview_data, income_data, balance_data, cash_flow_data)
        
        # Calculate DCF inputs
        dcf_inputs = calculate_dcf_inputs(parsed_data)
        
        return jsonify({
            'success': True,
            'data': dcf_inputs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/financial-data/<ticker>/historical-prices', methods=['GET'])
def get_historical_prices(ticker):
    """Get historical price data for a ticker"""
    try:
        interval = request.args.get('interval', 'daily')
        
        # Fetch historical prices
        price_data = financial_api.get_historical_prices(ticker, interval)
        
        if not price_data:
            return jsonify({
                'success': False,
                'error': 'No historical price data found for this ticker'
            }), 404
        
        return jsonify({
            'success': True,
            'data': price_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# LBO Management Endpoints
@app.route('/api/lbo/runs', methods=['POST'])
def save_lbo_run():
    """Save an LBO analysis run"""
    try:
        data = request.get_json()
        if not data or 'inputs' not in data:
            return jsonify({'error': 'Invalid LBO run data'}), 400
        
        user = get_or_create_user()
        
        # Create new LBO run
        lbo_run = LBORun(
            user_id=user.id,
            run_id=str(uuid.uuid4()),
            company_name=data.get('inputs', {}).get('companyName', 'Unknown Company'),
            inputs=json.dumps(data['inputs']),
            results=json.dumps(data.get('results')) if data.get('results') else None
        )
        
        db.session.add(lbo_run)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'run_id': lbo_run.run_id,
            'message': 'LBO run saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/lbo/runs/last', methods=['GET'])
def get_last_lbo_run():
    """Get the most recent LBO run for the user"""
    try:
        user = get_or_create_user()
        lbo_run = LBORun.query.filter_by(user_id=user.id).order_by(LBORun.updated_at.desc()).first()
        
        if not lbo_run:
            return jsonify({'error': 'No LBO runs found'}), 404
        
        return jsonify({
            'success': True,
            'data': lbo_run.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lbo/runs/<run_id>', methods=['GET'])
def get_lbo_run(run_id):
    """Get a specific LBO run by ID"""
    try:
        user = get_or_create_user()
        lbo_run = LBORun.query.filter_by(user_id=user.id, run_id=run_id).first()
        
        if not lbo_run:
            return jsonify({'error': 'LBO run not found'}), 404
        
        return jsonify({
            'success': True,
            'data': lbo_run.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lbo/runs', methods=['GET'])
def list_lbo_runs():
    """List all LBO runs for the user"""
    try:
        user = get_or_create_user()
        lbo_runs = LBORun.query.filter_by(user_id=user.id).order_by(LBORun.updated_at.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'runs': [run.to_dict() for run in lbo_runs]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lbo/scenarios', methods=['POST'])
def save_lbo_scenarios():
    """Save multiple LBO scenarios"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({'error': 'Invalid LBO scenarios data'}), 400
        
        user = get_or_create_user()
        saved_count = 0
        
        for scenario_data in data:
            if 'name' not in scenario_data or 'inputs' not in scenario_data:
                continue
            
            # Check if scenario already exists
            existing = LBOScenario.query.filter_by(
                user_id=user.id,
                company_name=scenario_data.get('companyName', 'Unknown'),
                name=scenario_data['name']
            ).first()
            
            if existing:
                # Update existing scenario
                existing.inputs = json.dumps(scenario_data['inputs'])
                existing.updated_at = datetime.utcnow()
            else:
                # Create new scenario
                scenario = LBOScenario(
                    user_id=user.id,
                    scenario_id=str(uuid.uuid4()),
                    name=scenario_data['name'],
                    company_name=scenario_data.get('companyName', 'Unknown'),
                    inputs=json.dumps(scenario_data['inputs'])
                )
                db.session.add(scenario)
            
            saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'saved_count': saved_count,
            'message': f'{saved_count} LBO scenarios saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/lbo/scenarios', methods=['GET'])
def get_lbo_scenarios():
    """Get all LBO scenarios for the user"""
    try:
        user = get_or_create_user()
        scenarios = LBOScenario.query.filter_by(user_id=user.id).order_by(LBOScenario.updated_at.desc()).all()
        
        return jsonify({
            'success': True,
            'scenarios': [scenario.to_dict() for scenario in scenarios]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lbo/scenarios/<scenario_id>', methods=['DELETE'])
def delete_lbo_scenario(scenario_id):
    """Delete a specific LBO scenario"""
    try:
        user = get_or_create_user()
        scenario = LBOScenario.query.filter_by(user_id=user.id, scenario_id=scenario_id).first()
        
        if not scenario:
            return jsonify({'error': 'LBO scenario not found'}), 404
        
        db.session.delete(scenario)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'LBO scenario deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Notes Management Endpoints
@app.route('/api/notes/<ticker>', methods=['GET'])
def get_notes(ticker):
    """Get notes for a specific ticker"""
    try:
        user = get_or_create_user()
        note = Note.query.filter_by(user_id=user.id, ticker=ticker.upper()).first()
        
        if not note:
            return jsonify({
                'success': True,
                'content': ''
            })
        
        return jsonify({
            'success': True,
            'content': note.content
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<ticker>', methods=['POST'])
def save_notes(ticker):
    """Save notes for a specific ticker"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Invalid notes data'}), 400
        
        user = get_or_create_user()
        note = Note.query.filter_by(user_id=user.id, ticker=ticker.upper()).first()
        
        if note:
            # Update existing note
            note.content = data['content']
            note.updated_at = datetime.utcnow()
        else:
            # Create new note
            note = Note(
                user_id=user.id,
                ticker=ticker.upper(),
                content=data['content']
            )
            db.session.add(note)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notes saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# M&A Analysis Endpoints
@app.route('/api/ma/runs', methods=['POST'])
def save_ma_run():
    """Save M&A analysis run"""
    try:
        user = get_or_create_user()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['deal_name', 'acquirer_name', 'target_name', 'inputs']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate run ID
        run_id = str(uuid.uuid4())
        
        # Create new run
        ma_run = MARun(
            user_id=user.id,
            run_id=run_id,
            deal_name=data['deal_name'],
            acquirer_name=data['acquirer_name'],
            target_name=data['target_name'],
            inputs=json.dumps(data['inputs']),
            results=json.dumps(data.get('results'))
        )
        
        db.session.add(ma_run)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'M&A run saved successfully',
            'data': {
                'run_id': run_id,
                'deal_name': data['deal_name']
            }
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving M&A run: {str(e)}")
        return jsonify({'error': 'Failed to save M&A run'}), 500

@app.route('/api/ma/runs/last', methods=['GET'])
def get_last_ma_run():
    """Get the most recent M&A run"""
    try:
        user = get_or_create_user()
        
        # Get the most recent run for the user
        ma_run = MARun.query.filter_by(user_id=user.id).order_by(MARun.created_at.desc()).first()
        
        if not ma_run:
            return jsonify({'error': 'No M&A runs found'}), 404
        
        return jsonify({
            'success': True,
            'data': ma_run.to_dict()
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving last M&A run: {str(e)}")
        return jsonify({'error': 'Failed to retrieve M&A run'}), 500

@app.route('/api/ma/runs/<run_id>', methods=['GET'])
def get_ma_run(run_id):
    """Get specific M&A run by ID"""
    try:
        user = get_or_create_user()
        
        ma_run = MARun.query.filter_by(user_id=user.id, run_id=run_id).first()
        
        if not ma_run:
            return jsonify({'error': 'M&A run not found'}), 404
        
        return jsonify({
            'success': True,
            'data': ma_run.to_dict()
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving M&A run: {str(e)}")
        return jsonify({'error': 'Failed to retrieve M&A run'}), 500

@app.route('/api/ma/runs', methods=['GET'])
def list_ma_runs():
    """List all M&A runs for the user"""
    try:
        user = get_or_create_user()
        
        ma_runs = MARun.query.filter_by(user_id=user.id).order_by(MARun.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [run.to_dict() for run in ma_runs]
        })
        
    except Exception as e:
        app.logger.error(f"Error listing M&A runs: {str(e)}")
        return jsonify({'error': 'Failed to list M&A runs'}), 500

@app.route('/api/ma/scenarios', methods=['POST'])
def save_ma_scenarios():
    """Save M&A scenarios"""
    try:
        user = get_or_create_user()
        data = request.get_json()
        
        if not data or 'scenarios' not in data:
            return jsonify({'error': 'Scenarios data is required'}), 400
        
        scenarios_data = data['scenarios']
        if not isinstance(scenarios_data, list):
            return jsonify({'error': 'Scenarios must be a list'}), 400
        
        saved_scenarios = []
        
        for scenario_data in scenarios_data:
            # Validate required fields
            required_fields = ['name', 'deal_name', 'acquirer_name', 'target_name', 'inputs']
            for field in required_fields:
                if field not in scenario_data:
                    return jsonify({'error': f'Missing required field in scenario: {field}'}), 400
            
            # Generate scenario ID
            scenario_id = str(uuid.uuid4())
            
            # Check for duplicate name
            existing = MAScenario.query.filter_by(user_id=user.id, name=scenario_data['name']).first()
            if existing:
                # Update existing scenario
                existing.deal_name = scenario_data['deal_name']
                existing.acquirer_name = scenario_data['acquirer_name']
                existing.target_name = scenario_data['target_name']
                existing.inputs = json.dumps(scenario_data['inputs'])
                existing.updated_at = datetime.utcnow()
                db.session.commit()  # Commit the update
                saved_scenarios.append(existing.to_dict())
            else:
                # Create new scenario
                scenario = MAScenario(
                    user_id=user.id,
                    scenario_id=scenario_id,
                    name=scenario_data['name'],
                    deal_name=scenario_data['deal_name'],
                    acquirer_name=scenario_data['acquirer_name'],
                    target_name=scenario_data['target_name'],
                    inputs=json.dumps(scenario_data['inputs'])
                )
                db.session.add(scenario)
                db.session.flush()  # Flush to get the ID
                saved_scenarios.append(scenario.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(saved_scenarios)} M&A scenarios saved successfully',
            'data': saved_scenarios
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving M&A scenarios: {str(e)}")
        return jsonify({'error': 'Failed to save M&A scenarios'}), 500

@app.route('/api/ma/scenarios', methods=['GET'])
def get_ma_scenarios():
    """Get all M&A scenarios for the user"""
    try:
        user = get_or_create_user()
        
        scenarios = MAScenario.query.filter_by(user_id=user.id).order_by(MAScenario.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [scenario.to_dict() for scenario in scenarios]
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving M&A scenarios: {str(e)}")
        return jsonify({'error': 'Failed to retrieve M&A scenarios'}), 500

@app.route('/api/ma/scenarios/<scenario_id>', methods=['DELETE'])
def delete_ma_scenario(scenario_id):
    """Delete M&A scenario by ID"""
    try:
        user = get_or_create_user()
        
        scenario = MAScenario.query.filter_by(user_id=user.id, scenario_id=scenario_id).first()
        
        if not scenario:
            return jsonify({'error': 'M&A scenario not found'}), 404
        
        db.session.delete(scenario)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'M&A scenario deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting M&A scenario: {str(e)}")
        return jsonify({'error': 'Failed to delete M&A scenario'}), 500

# Add WebSocket status endpoint
@app.route('/api/websocket/status')
def websocket_status():
    """Get WebSocket server status"""
    try:
        status = {
            'connected': True,
            'rooms': len(websocket_manager.rooms),
            'users': len(websocket_manager.users),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Add room status endpoint
@app.route('/api/websocket/room/<room_id>/status')
def room_status(room_id):
    """Get room status"""
    try:
        status = websocket_manager.get_room_status(room_id)
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Add user status endpoint
@app.route('/api/websocket/user/<user_id>/status')
def user_status(user_id):
    """Get user status"""
    try:
        status = websocket_manager.get_user_status(user_id)
        if status:
            return jsonify({'success': True, 'data': status})
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Database initialization
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001) 