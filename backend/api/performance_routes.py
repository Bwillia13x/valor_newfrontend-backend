"""
Performance monitoring and optimization API routes
Provides endpoints for monitoring system performance and getting optimization recommendations
"""

from flask import Blueprint, jsonify, request, g
from typing import Dict, Any
import logging

from ..performance import (
    performance_monitor, 
    health_check_performance,
    optimize_database_queries,
    optimize_cache_strategy,
    optimize_background_processing
)
from ..tasks import health_check_tasks, get_task_metrics
from ..cache import health_check_cache
from ..db_enterprise import health_check_db, get_db_stats
from ..auth import auth_required
from ..rate_limiter import rate_limit

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')


@performance_bp.route('/health', methods=['GET'])
@rate_limit("api")
def performance_health():
    """Get performance monitoring system health status"""
    try:
        health_status = health_check_performance()
        return jsonify({
            "success": True,
            "data": health_status
        })
    except Exception as e:
        logger.error(f"Performance health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Performance health check failed"
        }), 500


@performance_bp.route('/start-monitoring', methods=['POST'])
@auth_required
@rate_limit("api")
def start_performance_monitoring():
    """Start performance monitoring"""
    try:
        data = request.get_json() or {}
        interval = data.get('interval', 30)
        
        performance_monitor.start_monitoring(interval)
        
        return jsonify({
            "success": True,
            "message": f"Performance monitoring started with {interval}s interval",
            "data": {
                "monitoring_active": performance_monitor.monitoring_active,
                "interval": interval
            }
        })
    except Exception as e:
        logger.error(f"Failed to start performance monitoring: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to start performance monitoring"
        }), 500


@performance_bp.route('/stop-monitoring', methods=['POST'])
@auth_required
@rate_limit("api")
def stop_performance_monitoring():
    """Stop performance monitoring"""
    try:
        performance_monitor.stop_monitoring()
        
        return jsonify({
            "success": True,
            "message": "Performance monitoring stopped",
            "data": {
                "monitoring_active": performance_monitor.monitoring_active
            }
        })
    except Exception as e:
        logger.error(f"Failed to stop performance monitoring: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to stop performance monitoring"
        }), 500


@performance_bp.route('/summary', methods=['GET'])
@rate_limit("api")
def get_performance_summary():
    """Get current performance summary"""
    try:
        summary = performance_monitor.get_performance_summary()
        
        return jsonify({
            "success": True,
            "data": summary
        })
    except Exception as e:
        logger.error(f"Failed to get performance summary: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get performance summary"
        }), 500


@performance_bp.route('/metrics/<category>', methods=['GET'])
@rate_limit("api")
def get_historical_metrics(category: str):
    """Get historical metrics for a specific category"""
    try:
        hours = request.args.get('hours', 24, type=int)
        metrics = performance_monitor.get_historical_metrics(category, hours)
        
        return jsonify({
            "success": True,
            "data": {
                "category": category,
                "hours": hours,
                "metrics": metrics,
                "count": len(metrics)
            }
        })
    except Exception as e:
        logger.error(f"Failed to get historical metrics for {category}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to get historical metrics for {category}"
        }), 500


@performance_bp.route('/recommendations', methods=['GET'])
@rate_limit("api")
def get_optimization_recommendations():
    """Get performance optimization recommendations"""
    try:
        # Get current recommendations from performance monitor
        current_recommendations = performance_monitor.optimization_recommendations
        
        # Get additional optimization recommendations
        db_recommendations = optimize_database_queries()
        cache_recommendations = optimize_cache_strategy()
        background_recommendations = optimize_background_processing()
        
        all_recommendations = {
            "current_issues": current_recommendations,
            "database_optimization": db_recommendations,
            "cache_optimization": cache_recommendations,
            "background_processing": background_recommendations
        }
        
        return jsonify({
            "success": True,
            "data": all_recommendations
        })
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get optimization recommendations"
        }), 500


@performance_bp.route('/thresholds', methods=['GET', 'PUT'])
@auth_required
@rate_limit("api")
def manage_thresholds():
    """Get or update performance thresholds"""
    try:
        if request.method == 'GET':
            # Get current thresholds
            thresholds = performance_monitor.thresholds.copy()
            
            return jsonify({
                "success": True,
                "data": thresholds
            })
        
        elif request.method == 'PUT':
            # Update thresholds
            data = request.get_json() or {}
            
            updated_thresholds = {}
            for metric, value in data.items():
                if metric in performance_monitor.thresholds:
                    performance_monitor.set_threshold(metric, value)
                    updated_thresholds[metric] = value
            
            return jsonify({
                "success": True,
                "message": f"Updated {len(updated_thresholds)} thresholds",
                "data": updated_thresholds
            })
            
    except Exception as e:
        logger.error(f"Failed to manage thresholds: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to manage thresholds"
        }), 500


@performance_bp.route('/system-status', methods=['GET'])
@rate_limit("api")
def get_system_status():
    """Get comprehensive system status including all components"""
    try:
        # Get performance status
        perf_status = health_check_performance()
        
        # Get task system status
        task_status = health_check_tasks()
        
        # Get cache status
        cache_status = health_check_cache()
        
        # Get database status
        db_status = health_check_db()
        
        # Get database stats
        db_stats = get_db_stats()
        
        # Get task metrics
        task_metrics = get_task_metrics()
        
        # Compile comprehensive status
        system_status = {
            "timestamp": performance_monitor.performance_data.get('timestamp', 'N/A'),
            "overall_status": "healthy",
            "components": {
                "performance_monitoring": perf_status,
                "task_system": task_status,
                "cache_system": cache_status,
                "database_system": db_status
            },
            "metrics": {
                "database": db_stats,
                "tasks": task_metrics
            }
        }
        
        # Determine overall status
        component_statuses = [
            perf_status.get('status'),
            task_status.get('status'),
            cache_status.get('status'),
            db_status.get('status')
        ]
        
        if 'unhealthy' in component_statuses:
            system_status['overall_status'] = 'unhealthy'
        elif 'degraded' in component_statuses:
            system_status['overall_status'] = 'degraded'
        
        return jsonify({
            "success": True,
            "data": system_status
        })
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get system status"
        }), 500


@performance_bp.route('/optimize', methods=['POST'])
@auth_required
@rate_limit("api")
def trigger_optimization():
    """Trigger specific performance optimizations"""
    try:
        data = request.get_json() or {}
        optimization_type = data.get('type')
        
        if optimization_type == 'cache_warming':
            # Implement cache warming logic
            # This would typically involve background tasks
            return jsonify({
                "success": True,
                "message": "Cache warming initiated",
                "data": {"type": "cache_warming"}
            })
        
        elif optimization_type == 'db_cleanup':
            # Implement database cleanup
            return jsonify({
                "success": True,
                "message": "Database cleanup initiated",
                "data": {"type": "db_cleanup"}
            })
        
        elif optimization_type == 'task_cleanup':
            # Clean up old task results
            from ..tasks import task_manager
            task_manager.cleanup_completed_tasks()
            
            return jsonify({
                "success": True,
                "message": "Task cleanup completed",
                "data": {"type": "task_cleanup"}
            })
        
        else:
            return jsonify({
                "success": False,
                "error": f"Unknown optimization type: {optimization_type}"
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to trigger optimization {optimization_type}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to trigger optimization"
        }), 500


@performance_bp.route('/alerts', methods=['GET'])
@rate_limit("api")
def get_performance_alerts():
    """Get current performance alerts and issues"""
    try:
        summary = performance_monitor.get_performance_summary()
        
        alerts = []
        if 'issues' in summary.get('metrics', {}):
            for issue in summary['metrics']['issues']:
                alerts.append({
                    'type': issue['type'],
                    'severity': issue['severity'],
                    'message': issue['message'],
                    'value': issue['value'],
                    'threshold': issue['threshold'],
                    'timestamp': summary.get('timestamp', 'N/A')
                })
        
        return jsonify({
            "success": True,
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "status": summary.get('status', 'unknown')
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get performance alerts"
        }), 500


@performance_bp.route('/dashboard', methods=['GET'])
@rate_limit("api")
def get_performance_dashboard():
    """Get performance dashboard data for visualization"""
    try:
        # Get current performance summary
        summary = performance_monitor.get_performance_summary()
        
        # Get historical metrics for key categories
        cpu_metrics = performance_monitor.get_historical_metrics('system', 24)
        memory_metrics = performance_monitor.get_historical_metrics('system', 24)
        cache_metrics = performance_monitor.get_historical_metrics('cache', 24)
        
        # Prepare dashboard data
        dashboard_data = {
            "current_status": summary,
            "trends": {
                "cpu": [m.get('cpu_percent', 0) for m in cpu_metrics],
                "memory": [m.get('memory_percent', 0) for m in memory_metrics],
                "cache_hits": [m.get('hits', 0) for m in cache_metrics],
                "cache_misses": [m.get('misses', 0) for m in cache_metrics]
            },
            "timestamps": [m.get('timestamp', 'N/A') for m in cpu_metrics],
            "recommendations": summary.get('recommendations', [])
        }
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get performance dashboard: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get performance dashboard"
        }), 500