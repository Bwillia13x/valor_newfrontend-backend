"""
Error Reporting API Routes - Phase 5 Frontend UX and Reliability
Handles error collection, storage, and analysis for the frontend error handling system
"""

from flask import Blueprint, request, jsonify, g
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime, timedelta
import json
import logging

from ..logging import logger
from ..settings import settings

error_bp = Blueprint("errors", __name__, url_prefix="/api/errors")

# In-memory error storage (in production, use Redis or database)
error_store = []
max_errors = 1000

# Pydantic models for error reporting
class ErrorDetails(BaseModel):
    stack: Optional[str] = None
    filename: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None

class ErrorInfo(BaseModel):
    id: str = Field(..., description="Unique error identifier")
    timestamp: str = Field(..., description="ISO timestamp")
    type: str = Field(..., description="Error type (validation, network, calculation, etc.)")
    severity: str = Field(..., description="Error severity (low, medium, high, critical)")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[ErrorDetails] = Field(None, description="Error details")
    context: str = Field(..., description="Error context")
    userAgent: Optional[str] = Field(None, description="User agent string")
    url: Optional[str] = Field(None, description="Page URL")
    sessionId: Optional[str] = Field(None, description="Session identifier")

class ErrorReport(BaseModel):
    error: ErrorInfo = Field(..., description="Error information")
    timestamp: str = Field(..., description="Report timestamp")
    sessionId: str = Field(..., description="Session identifier")

class BatchErrorReport(BaseModel):
    errors: List[ErrorInfo] = Field(..., description="List of errors")
    timestamp: str = Field(..., description="Report timestamp")
    sessionId: str = Field(..., description="Session identifier")

class ErrorStats(BaseModel):
    total_errors: int = Field(..., description="Total number of errors")
    errors_by_type: Dict[str, int] = Field(..., description="Error counts by type")
    errors_by_severity: Dict[str, int] = Field(..., description="Error counts by severity")
    recent_errors: List[ErrorInfo] = Field(..., description="Recent errors")

def _validation_error(e: ValidationError, status_code: int = 422):
    return jsonify({"error": "ValidationError", "details": e.errors()}), status_code

@error_bp.route("/", methods=["POST"])
def report_error() -> Any:
    """
    Report a single error from the frontend
    """
    try:
        payload = ErrorReport.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return _validation_error(e)

    try:
        # Store error
        store_error(payload.error)
        
        # Log error for monitoring
        logger.warning(
            "frontend_error_reported",
            error_id=payload.error.id,
            error_type=payload.error.type,
            error_severity=payload.error.severity,
            error_message=payload.error.message,
            session_id=payload.sessionId,
            tenant_id=getattr(g, 'tenant_id', 'unknown')
        )

        return jsonify({"status": "success", "error_id": payload.error.id}), 200

    except Exception as e:
        logger.error("error_reporting_failed", error=str(e))
        return jsonify({"error": "Failed to report error"}), 500

@error_bp.route("/batch", methods=["POST"])
def report_errors_batch() -> Any:
    """
    Report multiple errors in a batch
    """
    try:
        payload = BatchErrorReport.model_validate(request.get_json(force=True) or {})
    except ValidationError as e:
        return _validation_error(e)

    try:
        # Store all errors
        stored_count = 0
        for error in payload.errors:
            if store_error(error):
                stored_count += 1

        # Log batch report
        logger.info(
            "frontend_errors_batch_reported",
            total_errors=len(payload.errors),
            stored_errors=stored_count,
            session_id=payload.sessionId,
            tenant_id=getattr(g, 'tenant_id', 'unknown')
        )

        return jsonify({
            "status": "success",
            "total_errors": len(payload.errors),
            "stored_errors": stored_count
        }), 200

    except Exception as e:
        logger.error("batch_error_reporting_failed", error=str(e))
        return jsonify({"error": "Failed to report errors"}), 500

@error_bp.route("/stats", methods=["GET"])
def get_error_stats() -> Any:
    """
    Get error statistics
    """
    try:
        # Calculate time range (last 24 hours by default)
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter errors by time
        recent_errors = [
            error for error in error_store
            if datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) > since
        ]

        # Calculate statistics
        stats = {
            "total_errors": len(recent_errors),
            "errors_by_type": {},
            "errors_by_severity": {},
            "recent_errors": recent_errors[-10:]  # Last 10 errors
        }

        # Count by type and severity
        for error in recent_errors:
            error_type = error.get('type', 'unknown')
            error_severity = error.get('severity', 'unknown')
            
            stats["errors_by_type"][error_type] = stats["errors_by_type"].get(error_type, 0) + 1
            stats["errors_by_severity"][error_severity] = stats["errors_by_severity"].get(error_severity, 0) + 1

        return jsonify(stats), 200

    except Exception as e:
        logger.error("error_stats_failed", error=str(e))
        return jsonify({"error": "Failed to get error statistics"}), 500

@error_bp.route("/clear", methods=["POST"])
def clear_errors() -> Any:
    """
    Clear error store (admin function)
    """
    try:
        global error_store
        cleared_count = len(error_store)
        error_store.clear()
        
        logger.info("error_store_cleared", cleared_count=cleared_count)
        
        return jsonify({
            "status": "success",
            "cleared_count": cleared_count
        }), 200

    except Exception as e:
        logger.error("error_clear_failed", error=str(e))
        return jsonify({"error": "Failed to clear errors"}), 500

@error_bp.route("/health", methods=["GET"])
def error_health() -> Any:
    """
    Health check for error reporting system
    """
    try:
        health = {
            "status": "healthy",
            "error_count": len(error_store),
            "max_errors": max_errors,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Check if error store is getting full
        if len(error_store) > max_errors * 0.9:
            health["status"] = "warning"
            health["message"] = "Error store is nearly full"
        
        return jsonify(health), 200

    except Exception as e:
        logger.error("error_health_check_failed", error=str(e))
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

def store_error(error: ErrorInfo) -> bool:
    """
    Store an error in the error store
    """
    try:
        global error_store
        
        # Convert to dict for storage
        error_dict = error.model_dump()
        
        # Add to store
        error_store.append(error_dict)
        
        # Maintain size limit
        if len(error_store) > max_errors:
            error_store = error_store[-max_errors:]
        
        return True

    except Exception as e:
        logger.error("error_storage_failed", error=str(e))
        return False

# Error analysis functions
def analyze_error_patterns() -> Dict[str, Any]:
    """
    Analyze error patterns for insights
    """
    try:
        if not error_store:
            return {"message": "No errors to analyze"}

        # Group errors by type and severity
        patterns = {
            "most_common_types": {},
            "most_common_severities": {},
            "error_trends": {},
            "critical_errors": []
        }

        # Count occurrences
        for error in error_store:
            error_type = error.get('type', 'unknown')
            error_severity = error.get('severity', 'unknown')
            
            patterns["most_common_types"][error_type] = patterns["most_common_types"].get(error_type, 0) + 1
            patterns["most_common_severities"][error_severity] = patterns["most_common_severities"].get(error_severity, 0) + 1
            
            # Track critical errors
            if error_severity == 'critical':
                patterns["critical_errors"].append(error)

        # Sort by frequency
        patterns["most_common_types"] = dict(
            sorted(patterns["most_common_types"].items(), key=lambda x: x[1], reverse=True)
        )
        patterns["most_common_severities"] = dict(
            sorted(patterns["most_common_severities"].items(), key=lambda x: x[1], reverse=True)
        )

        return patterns

    except Exception as e:
        logger.error("error_analysis_failed", error=str(e))
        return {"error": "Failed to analyze error patterns"}

@error_bp.route("/analysis", methods=["GET"])
def get_error_analysis() -> Any:
    """
    Get error pattern analysis
    """
    try:
        analysis = analyze_error_patterns()
        return jsonify(analysis), 200

    except Exception as e:
        logger.error("error_analysis_endpoint_failed", error=str(e))
        return jsonify({"error": "Failed to get error analysis"}), 500

# Register blueprint
def init_error_routes(app):
    """Initialize error reporting routes"""
    app.register_blueprint(error_bp)
    logger.info("error_routes_initialized") 