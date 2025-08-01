"""
Valor IVX Backend API
Advanced DCF Modeling Tool Backend

This Flask application provides the backend API for the Valor IVX frontend,
handling data persistence, user management, and financial analysis storage.
"""

import os
import json
import uuid
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, send_from_directory, g, make_response, Response
from werkzeug.http import http_date
import hashlib
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from pydantic import BaseModel, ValidationError

from .app_logging import configure_logging, request_start, log_request
from .metrics import (
    init_app as metrics_init_app,
    before_request as metrics_before_request,
    after_request as metrics_after_request,
)
from .settings import settings
from .rate_limiter import auth_rate_limit, financial_data_rate_limit, rate_limit
from .auth import AuthManager, auth_required, get_current_user_id
from weasyprint import HTML  # PDF generation
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import financial data module
from financial_data import financial_api, parse_financial_data, calculate_dcf_inputs

# Import WebSocket manager
from websocket_manager import websocket_manager

# Import error reporting routes
from api.error_routes import init_error_routes

# Import data routes (Phase 7)
from api.data_routes import data_bp

# Import Phase 9: Advanced Analytics and Machine Learning
from api.advanced_analytics_routes import advanced_analytics_bp
from api.ai_insights_routes import ai_insights_bp

# Import ML management routes (Phase 3)
from api.ml_management_routes import ml_management_bp

# Import tenant management routes (Phase 8)
from api.tenant_management_routes import tenant_management_bp

# Import ML registry for variant routing activation
from ml_models.registry import registry as ml_registry

# Import monitoring system
try:
    from monitoring import MonitoringManager, init_monitoring_routes
    import redis

    redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))
    monitoring_enabled = True
except ImportError:
    monitoring_enabled = False
    redis_client = None


# Configuration
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///valor_ivx.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "jwt-secret-key-change-in-production"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)


# Initialize Flask app
app = Flask(__name__, static_folder="../", static_url_path="")
app.config.from_object(Config)

# Configure structured logging (via structlog backend/logging.py)
configure_logging()
app.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


@app.before_request
def inject_request_context() -> None:
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = rid
    # capture tenant id if provided for correlation/metrics
    g.tenant_id = request.headers.get("X-Tenant-ID", getattr(g, "tenant_id", None))
    # start request timers/logging
    request_start()
    # metrics timer handled from metrics_before_request hook


@app.after_request
def set_request_id_header(response):
    rid = getattr(g, "request_id", None)
    if rid:
        response.headers["X-Request-ID"] = rid
    # structured access log
    return log_request(response)


# Initialize extensions
CORS(app, origins=["http://localhost:8000", "http://127.0.0.1:8000"])
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Initialize monitoring system
if monitoring_enabled:
    monitoring_manager = MonitoringManager(redis_client)
    init_monitoring_routes(app, monitoring_manager)

# Register blueprints
app.register_blueprint(data_bp)

# Register Phase 9 blueprints
app.register_blueprint(advanced_analytics_bp)
app.register_blueprint(ai_insights_bp)
app.register_blueprint(ml_management_bp)
app.register_blueprint(tenant_management_bp)

# Jinja2 environment for report templates
_templates_path = os.path.join(os.path.dirname(__file__), "reports", "templates")
_jinja_env = Environment(
    loader=FileSystemLoader(_templates_path),
    autoescape=select_autoescape(["html", "xml"])
)

# Initialize WebSocket manager with app
websocket_manager.init_app(app)

# Swagger (OpenAPI) setup (feature-flag via ENABLE_SWAGGER, default True)
if os.environ.get("ENABLE_SWAGGER", "true").lower() in {"1", "true", "yes"}:
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Valor IVX Backend API",
            "description": "API documentation for Valor IVX services",
            "version": "1.0.0",
        },
        "schemes": ["http", "https"],
        "basePath": "/",
        "tags": [
            {"name": "System", "description": "System and health endpoints"},
            {"name": "Runs", "description": "DCF Runs management"},
            {"name": "Scenarios", "description": "DCF Scenarios management"},
            {"name": "Financial Data", "description": "Financial data retrieval"},
            {"name": "LBO", "description": "LBO runs and scenarios"},
            {"name": "M&A", "description": "M&A runs and scenarios"},
            {"name": "WebSocket", "description": "Realtime/WebSocket status"},
        ],
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'",
            }
        },
    }
    Swagger(app, template=swagger_template)

# Wire Prometheus metrics via centralized backend/metrics.py if feature enabled
if settings.FEATURE_PROMETHEUS_METRICS:
    metrics_init_app(app)
    app.before_request(metrics_before_request)
    app.after_request(metrics_after_request)


# Database Models
class User(db.Model):
    """User model for authentication and data ownership"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    runs = db.relationship("Run", backref="user", lazy=True, cascade="all, delete-orphan")
    scenarios = db.relationship("Scenario", backref="user", lazy=True, cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="user", lazy=True, cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_user_tenant_id', 'tenant_id'),
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_username', 'username'),
    )


class Run(db.Model):
    """DCF analysis run data"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    ticker = db.Column(db.String(20), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    mc_settings = db.Column(db.Text)  # JSON
    results = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_run_tenant_id', 'tenant_id'),
        db.Index('idx_run_user_id', 'user_id'),
        db.Index('idx_run_ticker', 'ticker'),
        db.Index('idx_run_created_at', 'created_at'),
        db.Index('idx_run_tenant_user', 'tenant_id', 'user_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "ticker": self.ticker,
            "inputs": json.loads(self.inputs),
            "mc_settings": json.loads(self.mc_settings) if self.mc_settings else None,
            "results": json.loads(self.results) if self.results else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Scenario(db.Model):
    """Saved scenario data"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
    scenario_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    mc_settings = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_scenario_tenant_id', 'tenant_id'),
        db.Index('idx_scenario_user_id', 'user_id'),
        db.Index('idx_scenario_ticker', 'ticker'),
        db.Index('idx_scenario_created_at', 'created_at'),
        db.Index('idx_scenario_tenant_user', 'tenant_id', 'user_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "name": self.name,
            "ticker": self.ticker,
            "inputs": json.loads(self.inputs),
            "mc_settings": json.loads(self.mc_settings) if self.mc_settings else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Note(db.Model):
    """Analyst notes per ticker"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
    ticker = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_note_tenant_id', 'tenant_id'),
        db.Index('idx_note_user_id', 'user_id'),
        db.Index('idx_note_ticker', 'ticker'),
        db.Index('idx_note_tenant_user_ticker', 'tenant_id', 'user_id', 'ticker'),
    )

    def etag(self) -> str:
        base = f"{self.id}:{self.ticker}:{self.version}:{self.updated_at.timestamp() if self.updated_at else 0}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ticker": self.ticker,
            "content": self.content,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class LBORun(db.Model):
    """LBO analysis run data"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    company_name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    results = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "company_name": self.company_name,
            "inputs": json.loads(self.inputs),
            "results": json.loads(self.results) if self.results else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class LBOScenario(db.Model):
    """Saved LBO scenario data"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
    scenario_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    inputs = db.Column(db.Text, nullable=False)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "name": self.name,
            "company_name": self.company_name,
            "inputs": json.loads(self.inputs),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class MARun(db.Model):
    """M&A analysis run data"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
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
            "id": self.id,
            "run_id": self.run_id,
            "deal_name": self.deal_name,
            "acquirer_name": self.acquirer_name,
            "target_name": self.target_name,
            "inputs": json.loads(self.inputs),
            "results": json.loads(self.results) if self.results else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class MAScenario(db.Model):
    """Saved M&A scenario data"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=False)  # Multi-tenant support
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
            "id": self.id,
            "scenario_id": self.scenario_id,
            "name": self.name,
            "deal_name": self.deal_name,
            "acquirer_name": self.acquirer_name,
            "target_name": self.target_name,
            "inputs": json.loads(self.inputs),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Helper functions
def get_or_create_user() -> User:
    """Get or create a default user for demo purposes"""
    # Prefer authenticated user if present
    current_user_id = get_current_user_id()
    if current_user_id:
        user = User.query.get(current_user_id)
        if user:
            return user
    # Fallback to demo user for unauthenticated flows (non-sensitive)
    user = User.query.filter_by(username="demo_user").first()
    if not user:
        # bcrypt hash of literal "demo_password"
        # Precomputed once to avoid runtime bcrypt dependency here
        # Use backend/auth.py for hashing logic for real users
        user = User(
            username="demo_user",
            email="demo@valor-ivx.com",
            password_hash="$2b$12$h0QxqYV9z8kF0f2s2s6bO.3b0fJ2FIV4ZrI9Jp6i5a7wM8w4sZr7u",  # bcrypt("demo_password")
        )
        db.session.add(user)
        db.session.commit()
    return user


# Pydantic schemas (minimal, additive; replaces ad-hoc validation where used)
class RunInputSchema(BaseModel):
    inputs: Dict[str, Any]
    mc_settings: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    timestamp: Optional[Any] = None


class ScenarioSchema(BaseModel):
    name: str
    ticker: str
    inputs: Dict[str, Any]
    mc_settings: Optional[Dict[str, Any]] = None


class LBORunSchema(BaseModel):
    inputs: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None


class LBOScenarioSchema(BaseModel):
    name: str
    inputs: Dict[str, Any]
    companyName: Optional[str] = "Unknown"


class MARunSchema(BaseModel):
    deal_name: str
    acquirer_name: str
    target_name: str
    inputs: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None


def _validation_error_response(e: ValidationError):
    return jsonify({"error": "ValidationError", "details": e.errors()}), 400


# API Routes
@app.route("/")
def index():
    """Serve the main application"""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"})


@app.route("/api/readiness")
def readiness_check():
    """
    Readiness probe:
    - DB connectivity (simple query)
    - Third-party provider reachability (lightweight check)
    - Cache status (if available via monitoring/redis)
    Returns 200 only when all critical checks pass.
    """
    checks = {
        "db": {"ok": False, "detail": ""},
        "provider": {"ok": False, "detail": ""},
        "cache": {"ok": True, "detail": "not_configured"},
    }

    # DB connectivity: minimal query
    try:
        # Use an extremely lightweight query against an existing table
        db.session.execute(db.text("SELECT 1")).scalar()
        checks["db"]["ok"] = True
        checks["db"]["detail"] = "ok"
    except Exception as e:
        checks["db"]["detail"] = f"error: {str(e)}"

    # Provider reachability: use a very lightweight Alpha Vantage check if available
    try:
        # ping provider by fetching a tiny resource; keep timeout short inside provider if supported
        # Fallback to company overview for a well-known symbol
        _ = financial_api.get_company_overview("IBM")
        checks["provider"]["ok"] = True
        checks["provider"]["detail"] = "ok"
    except Exception as e:
        checks["provider"]["detail"] = f"error: {str(e)}"

    # Cache/Redis via monitoring (if enabled)
    global monitoring_enabled, redis_client
    if monitoring_enabled and redis_client is not None:
        try:
            pong = redis_client.ping()
            checks["cache"]["ok"] = bool(pong)
            checks["cache"]["detail"] = "ok" if pong else "no_pong"
        except Exception as e:
            checks["cache"]["ok"] = False
            checks["cache"]["detail"] = f"error: {str(e)}"

    all_ok = all(v.get("ok") for v in checks.values())
    status_code = 200 if all_ok else 503
    return jsonify({"status": "ready" if all_ok else "degraded", "checks": checks, "timestamp": datetime.utcnow().isoformat()}), status_code


# Run Management Endpoints
@app.route("/api/runs", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_run():
    """Save a DCF analysis run"""
    try:
        data = request.get_json() or {}
        try:
            payload = RunInputSchema.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)

        user = get_or_create_user()

        run = Run(
            user_id=user.id,
            run_id=str(uuid.uuid4()),
            ticker=payload.inputs.get("ticker", "UNKNOWN"),
            inputs=json.dumps(payload.inputs),
            mc_settings=json.dumps(payload.mc_settings) if payload.mc_settings else None,
            results=json.dumps(payload.results) if payload.results else None,
        )

        db.session.add(run)
        db.session.commit()

        return jsonify({"success": True, "run_id": run.run_id, "message": "Run saved successfully"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"save_run failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/runs/last", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_last_run():
    """Get the most recent run for the user"""
    try:
        user = get_or_create_user()
        run = Run.query.filter_by(user_id=user.id).order_by(Run.updated_at.desc()).first()

        if not run:
            return jsonify({"error": "No runs found"}), 404

        return jsonify({"success": True, "data": run.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/runs/<run_id>", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_run(run_id):
    """Get a specific run by ID"""
    try:
        user = get_or_create_user()
        run = Run.query.filter_by(user_id=user.id, run_id=run_id).first()

        if not run:
            return jsonify({"error": "Run not found"}), 404

        return jsonify({"success": True, "data": run.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/runs", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def list_runs():
    """List all runs for the current user with pagination"""
    try:
        user = get_or_create_user()
        
        # Import pagination utilities
        from utils.pagination import (
            apply_pagination, create_paginated_response, 
            apply_tenant_filter, apply_user_filter, get_search_params
        )
        
        # Start with base query
        query = Run.query
        
        # Apply tenant filter
        query = apply_tenant_filter(query, g.tenant_id)
        
        # Apply user filter
        query = apply_user_filter(query, user.id)
        
        # Apply search filter if provided
        search_field, search_term = get_search_params()
        if search_field and search_term:
            query = apply_search_filter(query, Run, search_field, search_term)
        
        # Apply pagination
        paginated_query, pagination_info = apply_pagination(query, Run)
        
        # Convert to dict format
        runs = [run.to_dict() for run in paginated_query.items]
        
        return jsonify(create_paginated_response(runs, pagination_info, "runs"))
        
    except Exception as e:
        app.logger.error(f"Error retrieving runs: {str(e)}")
        return jsonify({"error": "Failed to retrieve runs"}), 500


# Scenario Management Endpoints
@app.route("/api/scenarios", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_scenarios():
    """Save multiple scenarios"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "Invalid scenarios data"}), 400

        user = get_or_create_user()
        saved_count = 0

        for scenario_data in data:
            try:
                sc = ScenarioSchema.model_validate(scenario_data)
            except ValidationError as e:
                app.logger.warning(f"Invalid scenario payload skipped: {e.errors()}")
                continue

            existing = Scenario.query.filter_by(user_id=user.id, ticker=sc.ticker, name=sc.name).first()

            if existing:
                existing.inputs = json.dumps(sc.inputs)
                existing.mc_settings = json.dumps(sc.mc_settings) if sc.mc_settings else None
                existing.updated_at = datetime.utcnow()
            else:
                scenario = Scenario(
                    user_id=user.id,
                    scenario_id=str(uuid.uuid4()),
                    name=sc.name,
                    ticker=sc.ticker,
                    inputs=json.dumps(sc.inputs),
                    mc_settings=json.dumps(sc.mc_settings) if sc.mc_settings else None,
                )
                db.session.add(scenario)

            saved_count += 1

        db.session.commit()

        return jsonify({"success": True, "saved_count": saved_count, "message": f"{saved_count} scenarios saved successfully"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"save_scenarios failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/scenarios", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_scenarios():
    """Get all scenarios for the user"""
    try:
        user = get_or_create_user()
        scenarios = Scenario.query.filter_by(user_id=user.id).order_by(Scenario.updated_at.desc()).all()

        return jsonify({"success": True, "scenarios": [scenario.to_dict() for scenario in scenarios]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scenarios/<scenario_id>", methods=["DELETE"])
@auth_required
@rate_limit("api")
@tenant_required
def delete_scenario(scenario_id):
    """Delete a specific scenario"""
    try:
        user = get_or_create_user()
        scenario = Scenario.query.filter_by(user_id=user.id, scenario_id=scenario_id).first()

        if not scenario:
            return jsonify({"error": "Scenario not found"}), 404

        db.session.delete(scenario)
        db.session.commit()

        return jsonify({"success": True, "message": "Scenario deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Financial Data API Endpoints
@app.route("/api/financial-data/<ticker>", methods=["GET"])
@financial_data_rate_limit
@tenant_required
def get_financial_data(ticker):
    """Get comprehensive financial data for a ticker"""
    start_time = time.time()
    success = False
    try:
        overview_data = financial_api.get_company_overview(ticker)
        income_data = financial_api.get_income_statement(ticker)
        balance_data = financial_api.get_balance_sheet(ticker)
        cash_flow_data = financial_api.get_cash_flow(ticker)

        if not overview_data:
            return jsonify({"success": False, "error": "No financial data found for this ticker"}), 404

        parsed_data = parse_financial_data(overview_data, income_data, balance_data, cash_flow_data)

        success = True
        return jsonify({"success": True, "data": parsed_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if monitoring_enabled:
            duration = time.time() - start_time
            monitoring_manager.record_financial_calculation(
                calculation_type="financial_data_fetch",
                duration=duration,
                success=success,
                tenant=request.headers.get("X-Tenant-ID", "default"),
            )


@app.route("/api/financial-data/<ticker>/dcf-inputs", methods=["GET"])
@financial_data_rate_limit
@tenant_required
def get_dcf_inputs(ticker):
    """Get DCF model inputs calculated from financial data"""
    start_time = time.time()
    success = False
    try:
        overview_data = financial_api.get_company_overview(ticker)
        income_data = financial_api.get_income_statement(ticker)
        balance_data = financial_api.get_balance_sheet(ticker)
        cash_flow_data = financial_api.get_cash_flow(ticker)

        if not overview_data:
            return jsonify({"success": False, "error": "No financial data found for this ticker"}), 404

        parsed_data = parse_financial_data(overview_data, income_data, balance_data, cash_flow_data)

        dcf_inputs = calculate_dcf_inputs(parsed_data)

        success = True
        return jsonify({"success": True, "data": dcf_inputs})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if monitoring_enabled:
            duration = time.time() - start_time
            monitoring_manager.record_financial_calculation(
                calculation_type="dcf_inputs_calculation",
                duration=duration,
                success=success,
                tenant=request.headers.get("X-Tenant-ID", "default"),
            )


@app.route("/api/financial-data/<ticker>/historical-prices", methods=["GET"])
@financial_data_rate_limit
@tenant_required
def get_historical_prices(ticker):
    """Get historical price data for a ticker"""
    try:
        interval = request.args.get("interval", "daily")

        price_data = financial_api.get_historical_prices(ticker, interval)

        if not price_data:
            return jsonify({"success": False, "error": "No historical price data found for this ticker"}), 404

        return jsonify({"success": True, "data": price_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Report Generation Endpoints (DCF/LBO)
def _render_html(template_name: str, context: Dict[str, Any]) -> str:
    template = _jinja_env.get_template(template_name)
    return template.render(**context)

def _pdf_response(html_str: str, filename: str) -> Response:
    pdf_bytes = HTML(string=html_str).write_pdf()
    resp = make_response(pdf_bytes)
    resp.headers["Content-Type"] = "application/pdf"
    # Stream inline by default
    resp.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp

@app.route("/api/reports/dcf", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def report_dcf():
    """
    Generate a DCF report for a given run_id.
    Query params:
      - run_id: UUID of the DCF Run
      - format: 'html' for HTML response; otherwise inline PDF by default
    """
    try:
        run_id = request.args.get("run_id")
        if not run_id:
            return jsonify({"error": "run_id is required"}), 400

        user = get_or_create_user()
        run = Run.query.filter_by(user_id=user.id, run_id=run_id).first()
        if not run:
            return jsonify({"error": "Run not found"}), 404

        # Prepare context
        ctx = {
            "title": f"DCF Report - {run.ticker}",
            "generated_at": datetime.utcnow().isoformat(),
            "user": {"id": user.id, "username": user.username},
            "run": run.to_dict(),
        }

        fmt = request.args.get("format", "").lower()
        html_str = _render_html("dcf_report.html", ctx)
        if fmt == "html":
            return make_response(html_str, 200, {"Content-Type": "text/html; charset=utf-8"})
        return _pdf_response(html_str, f"dcf_report_{run.ticker}_{run.run_id}.pdf")

    except Exception as e:
        app.logger.error(f"report_dcf failed: {str(e)}")
        return jsonify({"error": "Failed to generate DCF report"}), 500

@app.route("/api/reports/lbo", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def report_lbo():
    """
    Generate an LBO report for a given run_id.
    Query params:
      - run_id: UUID of the LBO Run
      - format: 'html' for HTML response; otherwise inline PDF by default
    """
    try:
        run_id = request.args.get("run_id")
        if not run_id:
            return jsonify({"error": "run_id is required"}), 400

        user = get_or_create_user()
        lbo_run = LBORun.query.filter_by(user_id=user.id, run_id=run_id).first()
        if not lbo_run:
            return jsonify({"error": "LBO run not found"}), 404

        # Prepare context
        ctx = {
            "title": f"LBO Report - {lbo_run.company_name}",
            "generated_at": datetime.utcnow().isoformat(),
            "user": {"id": user.id, "username": user.username},
            "run": lbo_run.to_dict(),
        }

        fmt = request.args.get("format", "").lower()
        html_str = _render_html("lbo_report.html", ctx)
        if fmt == "html":
            return make_response(html_str, 200, {"Content-Type": "text/html; charset=utf-8"})
        return _pdf_response(html_str, f"lbo_report_{lbo_run.company_name}_{lbo_run.run_id}.pdf")

    except Exception as e:
        app.logger.error(f"report_lbo failed: {str(e)}")
        return jsonify({"error": "Failed to generate LBO report"}), 500

# LBO Management Endpoints
@app.route("/api/lbo/runs", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_lbo_run():
    """Save an LBO analysis run"""
    try:
        data = request.get_json() or {}
        try:
            payload = LBORunSchema.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)

        user = get_or_create_user()

        lbo_run = LBORun(
            user_id=user.id,
            run_id=str(uuid.uuid4()),
            company_name=payload.inputs.get("companyName", "Unknown Company"),
            inputs=json.dumps(payload.inputs),
            results=json.dumps(payload.results) if payload.results else None,
        )

        db.session.add(lbo_run)
        db.session.commit()

        return jsonify({"success": True, "run_id": lbo_run.run_id, "message": "LBO run saved successfully"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"save_lbo_run failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/lbo/runs/last", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_last_lbo_run():
    """Get the most recent LBO run for the user"""
    try:
        user = get_or_create_user()
        lbo_run = LBORun.query.filter_by(user_id=user.id).order_by(LBORun.updated_at.desc()).first()

        if not lbo_run:
            return jsonify({"error": "No LBO runs found"}), 404

        return jsonify({"success": True, "data": lbo_run.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/lbo/runs/<run_id>", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_lbo_run(run_id):
    """Get a specific LBO run by ID"""
    try:
        user = get_or_create_user()
        lbo_run = LBORun.query.filter_by(user_id=user.id, run_id=run_id).first()

        if not lbo_run:
            return jsonify({"error": "LBO run not found"}), 404

        return jsonify({"success": True, "data": lbo_run.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/lbo/runs", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def list_lbo_runs():
    """List all LBO runs for the user"""
    try:
        user = get_or_create_user()
        lbo_runs = LBORun.query.filter_by(user_id=user.id).order_by(LBORun.updated_at.desc()).limit(50).all()

        return jsonify({"success": True, "runs": [run.to_dict() for run in lbo_runs]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/lbo/scenarios", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_lbo_scenarios():
    """Save multiple LBO scenarios"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "Invalid LBO scenarios data"}), 400

        user = get_or_create_user()
        saved_count = 0

        for scenario_data in data:
            try:
                sc = LBOScenarioSchema.model_validate(scenario_data)
            except ValidationError as e:
                app.logger.warning(f"Invalid LBO scenario payload skipped: {e.errors()}")
                continue

            existing = LBOScenario.query.filter_by(user_id=user.id, company_name=sc.companyName or "Unknown", name=sc.name).first()

            if existing:
                existing.inputs = json.dumps(sc.inputs)
                existing.updated_at = datetime.utcnow()
            else:
                scenario = LBOScenario(
                    user_id=user.id,
                    scenario_id=str(uuid.uuid4()),
                    name=sc.name,
                    company_name=sc.companyName or "Unknown",
                    inputs=json.dumps(sc.inputs),
                )
                db.session.add(scenario)

            saved_count += 1

        db.session.commit()

        return jsonify({"success": True, "saved_count": saved_count, "message": f"{saved_count} LBO scenarios saved successfully"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"save_lbo_scenarios failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/lbo/scenarios", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_lbo_scenarios():
    """Get all LBO scenarios for the user"""
    try:
        user = get_or_create_user()
        scenarios = LBOScenario.query.filter_by(user_id=user.id).order_by(LBOScenario.updated_at.desc()).all()

        return jsonify({"success": True, "scenarios": [scenario.to_dict() for scenario in scenarios]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/lbo/scenarios/<scenario_id>", methods=["DELETE"])
@auth_required
@rate_limit("api")
@tenant_required
def delete_lbo_scenario(scenario_id):
    """Delete a specific LBO scenario"""
    try:
        user = get_or_create_user()
        scenario = LBOScenario.query.filter_by(user_id=user.id, scenario_id=scenario_id).first()

        if not scenario:
            return jsonify({"error": "LBO scenario not found"}), 404

        db.session.delete(scenario)
        db.session.commit()

        return jsonify({"success": True, "message": "LBO scenario deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Notes Management Endpoints
@app.route("/api/notes/<ticker>", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_notes(ticker):
    """Get notes for a specific ticker with ETag/version for optimistic concurrency"""
    try:
        user = get_or_create_user()
        note = Note.query.filter_by(user_id=user.id, ticker=ticker.upper()).first()

        if not note:
            # Create ephemeral empty response with no ETag/version
            resp = jsonify({"success": True, "content": "", "version": 0})
            return resp

        resp = jsonify({"success": True, "content": note.content, "version": note.version})
        resp.headers["ETag"] = note.etag()
        resp.headers["Last-Modified"] = http_date(note.updated_at)
        return resp

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notes/<ticker>", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_notes(ticker):
    """Save notes for a specific ticker with optimistic locking via If-Match ETag or version"""
    try:
        data = request.get_json() or {}
        if "content" not in data:
            return jsonify({"error": "Invalid notes data"}), 400

        user = get_or_create_user()
        note = Note.query.filter_by(user_id=user.id, ticker=ticker.upper()).first()

        # Determine client version/etag
        client_version = data.get("version")
        client_etag = request.headers.get("If-Match")

        if note:
            # check version/etag if provided
            if client_version is not None and int(client_version) != int(note.version):
                return jsonify({"error": "Version conflict"}), 409
            if client_etag and client_etag != note.etag():
                return jsonify({"error": "ETag conflict"}), 409

            note.content = data["content"]
            note.version = int(note.version) + 1
            note.updated_at = datetime.utcnow()
        else:
            note = Note(user_id=user.id, ticker=ticker.upper(), content=data["content"], version=1)
            db.session.add(note)

        db.session.commit()
        resp = jsonify({"success": True, "message": "Notes saved successfully", "version": note.version})
        resp.headers["ETag"] = note.etag()
        resp.headers["Last-Modified"] = http_date(note.updated_at)
        return resp

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# M&A Analysis Endpoints
@app.route("/api/ma/runs", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_ma_run():
    """Save M&A analysis run"""
    try:
        user = get_or_create_user()
        data = request.get_json() or {}

        try:
            payload = MARunSchema.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)

        run_id = str(uuid.uuid4())

        ma_run = MARun(
            user_id=user.id,
            run_id=run_id,
            deal_name=payload.deal_name,
            acquirer_name=payload.acquirer_name,
            target_name=payload.target_name,
            inputs=json.dumps(payload.inputs),
            results=json.dumps(payload.results) if payload.results else None,
        )

        db.session.add(ma_run)
        db.session.commit()

        return jsonify({"success": True, "message": "M&A run saved successfully", "data": {"run_id": run_id, "deal_name": payload.deal_name}})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving M&A run: {str(e)}")
        return jsonify({"error": "Failed to save M&A run"}), 500


@app.route("/api/ma/runs/last", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_last_ma_run():
    """Get the most recent M&A run"""
    try:
        user = get_or_create_user()

        ma_run = MARun.query.filter_by(user_id=user.id).order_by(MARun.created_at.desc()).first()

        if not ma_run:
            return jsonify({"error": "No M&A runs found"}), 404

        return jsonify({"success": True, "data": ma_run.to_dict()})

    except Exception as e:
        app.logger.error(f"Error retrieving M&A run: {str(e)}")
        return jsonify({"error": "Failed to retrieve M&A run"}), 500


@app.route("/api/ma/runs/<run_id>", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_ma_run(run_id):
    """Get specific M&A run by ID"""
    try:
        user = get_or_create_user()

        ma_run = MARun.query.filter_by(user_id=user.id, run_id=run_id).first()

        if not ma_run:
            return jsonify({"error": "M&A run not found"}), 404

        return jsonify({"success": True, "data": ma_run.to_dict()})

    except Exception as e:
        app.logger.error(f"Error retrieving M&A run: {str(e)}")
        return jsonify({"error": "Failed to retrieve M&A run"}), 500


@app.route("/api/ma/runs", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def list_ma_runs():
    """List all M&A runs for the user"""
    try:
        user = get_or_create_user()

        ma_runs = MARun.query.filter_by(user_id=user.id).order_by(MARun.created_at.desc()).all()

        return jsonify({"success": True, "data": [run.to_dict() for run in ma_runs]})

    except Exception as e:
        app.logger.error(f"Error listing M&A runs: {str(e)}")
        return jsonify({"error": "Failed to list M&A runs"}), 500


@app.route("/api/ma/scenarios", methods=["POST"])
@auth_required
@rate_limit("api")
@tenant_required
def save_ma_scenarios():
    """Save M&A scenarios"""
    try:
        user = get_or_create_user()
        data = request.get_json() or {}

        scenarios_data = data.get("scenarios")
        if not scenarios_data or not isinstance(scenarios_data, list):
            return jsonify({"error": "Scenarios must be a non-empty list"}), 400

        saved_scenarios: List[Dict[str, Any]] = []

        for scenario_data in scenarios_data:
            if not isinstance(scenario_data, dict):
                continue
            required_fields = ["name", "deal_name", "acquirer_name", "target_name", "inputs"]
            missing = [f for f in required_fields if f not in scenario_data]
            if missing:
                app.logger.warning(f"Skipping M&A scenario due to missing fields: {missing}")
                continue

            scenario_id = str(uuid.uuid4())

            existing = MAScenario.query.filter_by(user_id=user.id, name=scenario_data["name"]).first()
            if existing:
                existing.deal_name = scenario_data["deal_name"]
                existing.acquirer_name = scenario_data["acquirer_name"]
                existing.target_name = scenario_data["target_name"]
                existing.inputs = json.dumps(scenario_data["inputs"])
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                saved_scenarios.append(existing.to_dict())
            else:
                scenario = MAScenario(
                    user_id=user.id,
                    scenario_id=scenario_id,
                    name=scenario_data["name"],
                    deal_name=scenario_data["deal_name"],
                    acquirer_name=scenario_data["acquirer_name"],
                    target_name=scenario_data["target_name"],
                    inputs=json.dumps(scenario_data["inputs"]),
                )
                db.session.add(scenario)
                db.session.flush()
                saved_scenarios.append(scenario.to_dict())

        db.session.commit()

        return jsonify({"success": True, "message": f"{len(saved_scenarios)} M&A scenarios saved successfully", "data": saved_scenarios})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving M&A scenarios: {str(e)}")
        return jsonify({"error": "Failed to save M&A scenarios"}), 500


@app.route("/api/ma/scenarios", methods=["GET"])
@auth_required
@rate_limit("api")
@tenant_required
def get_ma_scenarios():
    """Get all M&A scenarios for the user"""
    try:
        user = get_or_create_user()

        scenarios = MAScenario.query.filter_by(user_id=user.id).order_by(MAScenario.created_at.desc()).all()

        return jsonify({"success": True, "data": [scenario.to_dict() for scenario in scenarios]})

    except Exception as e:
        app.logger.error(f"Error retrieving M&A scenarios: {str(e)}")
        return jsonify({"error": "Failed to retrieve M&A scenarios"}), 500


@app.route("/api/ma/scenarios/<scenario_id>", methods=["DELETE"])
@auth_required
@rate_limit("api")
@tenant_required
def delete_ma_scenario(scenario_id):
    """Delete M&A scenario by ID"""
    try:
        user = get_or_create_user()

        scenario = MAScenario.query.filter_by(user_id=user.id, scenario_id=scenario_id).first()

        if not scenario:
            return jsonify({"error": "M&A scenario not found"}), 404

        db.session.delete(scenario)
        db.session.commit()

        return jsonify({"success": True, "message": "M&A scenario deleted successfully"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting M&A scenario: {str(e)}")
        return jsonify({"error": "Failed to delete M&A scenario"}), 500


# WebSocket status endpoints
@app.route("/api/websocket/status")
@rate_limit("api")
def websocket_status():
    """Get WebSocket server status"""
    try:
        status = {
            "connected": True,
            "rooms": len(websocket_manager.rooms),
            "users": len(websocket_manager.users),
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/websocket/room/<room_id>/status")
@rate_limit("api")
def room_status(room_id):
    """Get room status"""
    try:
        status = websocket_manager.get_room_status(room_id)
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/websocket/user/<user_id>/status")
@rate_limit("api")
def user_status(user_id):
    """Get user status"""
    try:
        status = websocket_manager.get_user_status(user_id)
        if status:
            return jsonify({"success": True, "data": status})
        else:
            return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f"Unhandled error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# Database initialization
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")


def init_ml_variant_routing():
    """Initialize ML variant routing based on settings"""
    try:
        # Configure revenue model variant routing
        revenue_variant = getattr(settings, "REVENUE_MODEL_VARIANT", "") or ""
        if revenue_variant:
            ml_registry.set_variant("revenue_predictor", revenue_variant)
            app.logger.info(f"ML variant routing: revenue_predictor -> {revenue_variant}")
        
        # Configure portfolio optimizer variant routing
        portfolio_variant = getattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "") or ""
        if portfolio_variant:
            ml_registry.set_variant("portfolio_optimizer", portfolio_variant)
            app.logger.info(f"ML variant routing: portfolio_optimizer -> {portfolio_variant}")
        
        # Enable model variant metrics if configured
        if getattr(settings, "FEATURE_MODEL_VARIANT_METRICS", False):
            app.logger.info("ML variant metrics enabled")
        
        app.logger.info("ML variant routing initialization completed")
    except Exception as e:
        app.logger.error(f"Error initializing ML variant routing: {str(e)}")


if __name__ == "__main__":
    init_db()
    init_ml_variant_routing()
    # Standardize to port 5002 as per STATUS_REPORT.md
    app.run(debug=True, host="0.0.0.0", port=5002)
