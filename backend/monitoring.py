"""
Valor IVX - Comprehensive Monitoring and SLOs Implementation
Phase 9: Monitoring and SLOs

This module provides comprehensive monitoring, SLOs, and SLIs for the Valor IVX platform.
"""

import time
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import psutil
import redis
from flask import Flask, request, g, current_app
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, generate_latest, 
    CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess
)
import structlog

logger = structlog.get_logger(__name__)

# =============================================================================
# SLO/SLI Definitions
# =============================================================================

@dataclass
class SLO:
    """Service Level Objective definition"""
    name: str
    description: str
    target: float  # Target percentage (0.0 to 1.0)
    window: int    # Time window in seconds
    measurement: str  # Type of measurement (availability, latency, etc.)

@dataclass
class SLIMeasurement:
    """Service Level Indicator measurement"""
    slo_name: str
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]

class SLOManager:
    """Manages SLOs and SLI measurements"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.slos: Dict[str, SLO] = {}
        self.measurements: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        
        # Define default SLOs
        self._define_default_slos()
    
    def _define_default_slos(self):
        """Define default SLOs for Valor IVX"""
        default_slos = [
            SLO(
                name="api_availability",
                description="API availability target",
                target=0.999,  # 99.9% availability
                window=3600,   # 1 hour window
                measurement="availability"
            ),
            SLO(
                name="api_latency_p95",
                description="95th percentile API response time",
                target=0.200,  # 200ms target
                window=300,    # 5 minute window
                measurement="latency"
            ),
            SLO(
                name="financial_calculation_accuracy",
                description="Financial calculation accuracy",
                target=0.999,  # 99.9% accuracy
                window=86400,  # 24 hour window
                measurement="accuracy"
            ),
            SLO(
                name="user_session_success",
                description="User session success rate",
                target=0.995,  # 99.5% success rate
                window=3600,   # 1 hour window
                measurement="success_rate"
            ),
            SLO(
                name="websocket_connection_uptime",
                description="WebSocket connection uptime",
                target=0.999,  # 99.9% uptime
                window=300,    # 5 minute window
                measurement="uptime"
            )
        ]
        
        for slo in default_slos:
            self.add_slo(slo)
    
    def add_slo(self, slo: SLO):
        """Add a new SLO"""
        self.slos[slo.name] = slo
        logger.info("SLO added", slo_name=slo.name, target=slo.target)
    
    def record_measurement(self, slo_name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record an SLI measurement"""
        if slo_name not in self.slos:
            logger.warning("Unknown SLO", slo_name=slo_name)
            return
        
        measurement = SLIMeasurement(
            slo_name=slo_name,
            timestamp=datetime.utcnow(),
            value=value,
            metadata=metadata or {}
        )
        
        self.measurements[slo_name].append(measurement)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                key = f"slo_measurement:{slo_name}:{int(time.time())}"
                self.redis_client.setex(
                    key, 
                    86400,  # 24 hour TTL
                    json.dumps(asdict(measurement), default=str)
                )
            except Exception as e:
                logger.error("Failed to store measurement in Redis", error=str(e))
        
        logger.debug("SLI measurement recorded", slo_name=slo_name, value=value)
    
    def calculate_slo_compliance(self, slo_name: str, window_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Calculate SLO compliance for a given SLO"""
        if slo_name not in self.slos:
            return {"error": "SLO not found"}
        
        slo = self.slos[slo_name]
        window = window_seconds or slo.window
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        
        # Get measurements from memory
        measurements = [
            m for m in self.measurements[slo_name]
            if m.timestamp >= cutoff_time
        ]
        
        # Get measurements from Redis if available
        if self.redis_client:
            try:
                redis_measurements = self._get_redis_measurements(slo_name, cutoff_time)
                measurements.extend(redis_measurements)
            except Exception as e:
                logger.error("Failed to get Redis measurements", error=str(e))
        
        if not measurements:
            return {
                "slo_name": slo_name,
                "compliance": None,
                "measurements_count": 0,
                "window_seconds": window
            }
        
        # Calculate compliance based on measurement type
        if slo.measurement == "availability":
            success_count = sum(1 for m in measurements if m.value >= 1.0)
            compliance = success_count / len(measurements)
        elif slo.measurement == "latency":
            # For latency, we want values below target
            compliant_count = sum(1 for m in measurements if m.value <= slo.target)
            compliance = compliant_count / len(measurements)
        elif slo.measurement == "accuracy":
            compliance = sum(m.value for m in measurements) / len(measurements)
        elif slo.measurement == "success_rate":
            compliance = sum(m.value for m in measurements) / len(measurements)
        elif slo.measurement == "uptime":
            compliance = sum(m.value for m in measurements) / len(measurements)
        else:
            compliance = 0.0
        
        return {
            "slo_name": slo_name,
            "compliance": compliance,
            "target": slo.target,
            "meeting_target": compliance >= slo.target,
            "measurements_count": len(measurements),
            "window_seconds": window,
            "last_measurement": measurements[-1].timestamp.isoformat() if measurements else None
        }
    
    def _get_redis_measurements(self, slo_name: str, cutoff_time: datetime) -> List[SLIMeasurement]:
        """Get measurements from Redis"""
        measurements = []
        pattern = f"slo_measurement:{slo_name}:*"
        
        for key in self.redis_client.scan_iter(match=pattern):
            try:
                data = json.loads(self.redis_client.get(key))
                measurement = SLIMeasurement(
                    slo_name=data["slo_name"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    value=data["value"],
                    metadata=data["metadata"]
                )
                if measurement.timestamp >= cutoff_time:
                    measurements.append(measurement)
            except Exception as e:
                logger.error("Failed to parse Redis measurement", key=key, error=str(e))
        
        return measurements
    
    def get_all_slo_status(self) -> Dict[str, Any]:
        """Get status of all SLOs"""
        return {
            slo_name: self.calculate_slo_compliance(slo_name)
            for slo_name in self.slos.keys()
        }

# =============================================================================
# Prometheus Metrics
# =============================================================================

class PrometheusMetrics:
    """Prometheus metrics collection"""
    
    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status', 'tenant']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'tenant']
        )
        
        # Business metrics
        self.financial_calculations_total = Counter(
            'financial_calculations_total',
            'Total financial calculations',
            ['calculation_type', 'status', 'tenant']
        )
        
        self.financial_calculation_duration_seconds = Histogram(
            'financial_calculation_duration_seconds',
            'Financial calculation duration in seconds',
            ['calculation_type', 'tenant']
        )
        
        # System metrics
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            ['tenant']
        )
        
        self.websocket_connections = Gauge(
            'websocket_connections',
            'Number of active WebSocket connections',
            ['tenant']
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'endpoint', 'tenant']
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type', 'tenant']
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type', 'tenant']
        )
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float, tenant: str = "default"):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status, tenant=tenant).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint, tenant=tenant).observe(duration)
    
    def record_financial_calculation(self, calculation_type: str, duration: float, success: bool, tenant: str = "default"):
        """Record financial calculation metrics"""
        status = "success" if success else "error"
        self.financial_calculations_total.labels(calculation_type=calculation_type, status=status, tenant=tenant).inc()
        if success:
            self.financial_calculation_duration_seconds.labels(calculation_type=calculation_type, tenant=tenant).observe(duration)
    
    def set_active_users(self, count: int, tenant: str = "default"):
        """Set active users count"""
        self.active_users.labels(tenant=tenant).set(count)
    
    def set_websocket_connections(self, count: int, tenant: str = "default"):
        """Set WebSocket connections count"""
        self.websocket_connections.labels(tenant=tenant).set(count)
    
    def record_error(self, error_type: str, endpoint: str, tenant: str = "default"):
        """Record error metrics"""
        self.errors_total.labels(error_type=error_type, endpoint=endpoint, tenant=tenant).inc()
    
    def record_cache_hit(self, cache_type: str, tenant: str = "default"):
        """Record cache hit"""
        self.cache_hits_total.labels(cache_type=cache_type, tenant=tenant).inc()
    
    def record_cache_miss(self, cache_type: str, tenant: str = "default"):
        """Record cache miss"""
        self.cache_misses_total.labels(cache_type=cache_type, tenant=tenant).inc()

# =============================================================================
# System Monitoring
# =============================================================================

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self._monitoring_thread = None
        self._stop_monitoring = False
    
    def start_monitoring(self, interval: int = 60):
        """Start system monitoring in background thread"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._stop_monitoring = False
        self._monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("System monitoring started", interval_seconds=interval)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Monitoring loop"""
        while not self._stop_monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process metrics
            process = psutil.Process()
            process_cpu_percent = process.cpu_percent()
            process_memory_percent = process.memory_percent()
            process_memory_rss = process.memory_info().rss / (1024**2)  # MB
            
            self.metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "available_gb": memory_available
                },
                "disk": {
                    "percent": disk_percent,
                    "free_gb": disk_free
                },
                "network": {
                    "bytes_sent": network_bytes_sent,
                    "bytes_recv": network_bytes_recv
                },
                "process": {
                    "cpu_percent": process_cpu_percent,
                    "memory_percent": process_memory_percent,
                    "memory_rss_mb": process_memory_rss
                }
            }
            
            logger.debug("System metrics collected", metrics=self.metrics)
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return self.metrics.copy()

# =============================================================================
# Health Checks
# =============================================================================

class HealthChecker:
    """Comprehensive health checking"""
    
    def __init__(self, app: Flask, redis_client: Optional[redis.Redis] = None):
        self.app = app
        self.redis_client = redis_client
        self.checks = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check("database", self._check_database)
        self.register_check("redis", self._check_redis)
        self.register_check("external_apis", self._check_external_apis)
        self.register_check("disk_space", self._check_disk_space)
        self.register_check("memory_usage", self._check_memory_usage)
    
    def register_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Register a health check"""
        self.checks[name] = check_func
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from flask_sqlalchemy import SQLAlchemy
            db = SQLAlchemy(self.app)
            db.engine.execute("SELECT 1")
            return {"status": "healthy", "message": "Database connection OK"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database error: {str(e)}"}
    
    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        if not self.redis_client:
            return {"status": "healthy", "message": "Redis not configured"}
        
        try:
            self.redis_client.ping()
            return {"status": "healthy", "message": "Redis connection OK"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Redis error: {str(e)}"}
    
    def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        try:
            import requests
            # Check Alpha Vantage API
            response = requests.get("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=1min&apikey=demo", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "message": "External APIs accessible"}
            else:
                return {"status": "degraded", "message": "External APIs responding slowly"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"External API error: {str(e)}"}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = disk.percent
            if usage_percent < 80:
                return {"status": "healthy", "message": f"Disk usage: {usage_percent:.1f}%"}
            elif usage_percent < 90:
                return {"status": "degraded", "message": f"High disk usage: {usage_percent:.1f}%"}
            else:
                return {"status": "unhealthy", "message": f"Critical disk usage: {usage_percent:.1f}%"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Disk check error: {str(e)}"}
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            if usage_percent < 80:
                return {"status": "healthy", "message": f"Memory usage: {usage_percent:.1f}%"}
            elif usage_percent < 90:
                return {"status": "degraded", "message": f"High memory usage: {usage_percent:.1f}%"}
            else:
                return {"status": "unhealthy", "message": f"Critical memory usage: {usage_percent:.1f}%"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Memory check error: {str(e)}"}
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = result
                
                # Update overall status
                if result["status"] == "unhealthy":
                    overall_status = "unhealthy"
                elif result["status"] == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
                    
            except Exception as e:
                results[name] = {"status": "unhealthy", "message": f"Check failed: {str(e)}"}
                overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }

# =============================================================================
# Monitoring Manager
# =============================================================================

class MonitoringManager:
    """Main monitoring manager that coordinates all monitoring components"""
    
    def __init__(self, app: Flask, redis_client: Optional[redis.Redis] = None):
        self.app = app
        self.redis_client = redis_client
        
        # Initialize components
        self.slo_manager = SLOManager(redis_client)
        self.prometheus_metrics = PrometheusMetrics()
        self.system_monitor = SystemMonitor()
        self.health_checker = HealthChecker(app, redis_client)
        
        # Start monitoring
        self.system_monitor.start_monitoring()
        
        # Register Flask middleware
        self._register_middleware()
        
        logger.info("Monitoring manager initialized")
    
    def _register_middleware(self):
        """Register Flask middleware for monitoring"""
        
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            g.tenant_id = request.headers.get('X-Tenant-ID', 'default')
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                tenant = getattr(g, 'tenant_id', 'default')
                
                # Record HTTP metrics
                self.prometheus_metrics.record_http_request(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=response.status_code,
                    duration=duration,
                    tenant=tenant
                )
                
                # Record SLO measurements
                if response.status_code < 400:
                    self.slo_manager.record_measurement(
                        "api_availability",
                        1.0,
                        {"endpoint": request.endpoint, "method": request.method}
                    )
                else:
                    self.slo_manager.record_measurement(
                        "api_availability",
                        0.0,
                        {"endpoint": request.endpoint, "method": request.method}
                    )
                
                # Record latency SLO
                self.slo_manager.record_measurement(
                    "api_latency_p95",
                    duration,
                    {"endpoint": request.endpoint, "method": request.method}
                )
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            tenant = getattr(g, 'tenant_id', 'default')
            self.prometheus_metrics.record_error(
                error_type=type(e).__name__,
                endpoint=request.endpoint or 'unknown',
                tenant=tenant
            )
            raise e
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest()
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status"""
        return self.health_checker.run_health_checks()
    
    def get_slo_status(self) -> Dict[str, Any]:
        """Get SLO status"""
        return self.slo_manager.get_all_slo_status()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return self.system_monitor.get_system_metrics()
    
    def record_financial_calculation(self, calculation_type: str, duration: float, success: bool, tenant: str = "default"):
        """Record financial calculation metrics"""
        self.prometheus_metrics.record_financial_calculation(calculation_type, duration, success, tenant)
        
        if success:
            self.slo_manager.record_measurement(
                "financial_calculation_accuracy",
                1.0,
                {"calculation_type": calculation_type}
            )
        else:
            self.slo_manager.record_measurement(
                "financial_calculation_accuracy",
                0.0,
                {"calculation_type": calculation_type}
            )
    
    def set_user_metrics(self, active_users: int, websocket_connections: int, tenant: str = "default"):
        """Set user-related metrics"""
        self.prometheus_metrics.set_active_users(active_users, tenant)
        self.prometheus_metrics.set_websocket_connections(websocket_connections, tenant)
        
        # Record user session SLO
        if active_users > 0:
            self.slo_manager.record_measurement(
                "user_session_success",
                1.0,
                {"active_users": active_users}
            )
    
    def record_websocket_connection(self, connected: bool, tenant: str = "default"):
        """Record WebSocket connection metrics"""
        if connected:
            self.slo_manager.record_measurement(
                "websocket_connection_uptime",
                1.0,
                {"tenant": tenant}
            )
        else:
            self.slo_manager.record_measurement(
                "websocket_connection_uptime",
                0.0,
                {"tenant": tenant}
            )
    
    def record_cache_operation(self, hit: bool, cache_type: str, tenant: str = "default"):
        """Record cache operation metrics"""
        if hit:
            self.prometheus_metrics.record_cache_hit(cache_type, tenant)
        else:
            self.prometheus_metrics.record_cache_miss(cache_type, tenant)
    
    def shutdown(self):
        """Shutdown monitoring"""
        self.system_monitor.stop_monitoring()
        logger.info("Monitoring manager shutdown")

# =============================================================================
# Flask Routes
# =============================================================================

def init_monitoring_routes(app: Flask, monitoring_manager: MonitoringManager):
    """Initialize monitoring routes"""
    
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        return monitoring_manager.get_metrics(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return monitoring_manager.get_health()
    
    @app.route('/health/ready')
    def health_ready():
        """Readiness probe endpoint"""
        health_status = monitoring_manager.get_health()
        if health_status["status"] in ["healthy", "degraded"]:
            return {"status": "ready"}, 200
        else:
            return {"status": "not ready"}, 503
    
    @app.route('/health/live')
    def health_live():
        """Liveness probe endpoint"""
        return {"status": "alive"}, 200
    
    @app.route('/slo/status')
    def slo_status():
        """SLO status endpoint"""
        return monitoring_manager.get_slo_status()
    
    @app.route('/system/metrics')
    def system_metrics():
        """System metrics endpoint"""
        return monitoring_manager.get_system_metrics()
    
    logger.info("Monitoring routes initialized")