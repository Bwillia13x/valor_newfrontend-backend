"""
Performance monitoring and optimization for Valor IVX
Provides real-time performance tracking, optimization recommendations, and performance metrics
"""

import time
import logging
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
from contextlib import contextmanager

from .cache import cache_manager
from .db_enterprise import get_db_stats

# Configure logging
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.performance_data = {}
        self.optimization_recommendations = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.metrics_lock = threading.Lock()
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': 80.0,  # CPU usage percentage
            'memory_usage': 85.0,  # Memory usage percentage
            'disk_usage': 90.0,  # Disk usage percentage
            'response_time': 1.0,  # Response time in seconds
            'cache_hit_rate': 0.7,  # Cache hit rate (70%)
            'db_connection_pool': 0.8,  # Database pool utilization (80%)
        }
    
    def start_monitoring(self, interval: int = 30):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                self._analyze_performance()
                self._generate_recommendations()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in performance monitoring: {str(e)}")
                time.sleep(interval)
    
    def _collect_metrics(self):
        """Collect current system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            # Cache metrics
            cache_stats = cache_manager.get_stats()
            
            # Database metrics
            db_stats = get_db_stats()
            
            # Store metrics with timestamp
            timestamp = datetime.utcnow()
            metrics = {
                'timestamp': timestamp,
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'memory_available': memory.available,
                    'disk_free': disk.free
                },
                'application': {
                    'process_cpu': process_cpu,
                    'process_memory': process_memory.rss,
                    'process_memory_percent': process_memory_percent(process_memory.rss, memory.total)
                },
                'cache': cache_stats,
                'database': db_stats
            }
            
            with self.metrics_lock:
                # Store in rolling window (keep last 1000 measurements)
                for category, data in metrics.items():
                    if category != 'timestamp':
                        self.metrics[category].append(data)
                        if len(self.metrics[category]) > 1000:
                            self.metrics[category].popleft()
                
                self.performance_data = metrics
                
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
    
    def _analyze_performance(self):
        """Analyze collected metrics for performance issues"""
        try:
            with self.metrics_lock:
                if not self.performance_data:
                    return
                
                current = self.performance_data
                issues = []
                
                # Check CPU usage
                if current['system']['cpu_percent'] > self.thresholds['cpu_usage']:
                    issues.append({
                        'type': 'high_cpu',
                        'severity': 'warning',
                        'message': f"High CPU usage: {current['system']['cpu_percent']:.1f}%",
                        'value': current['system']['cpu_percent'],
                        'threshold': self.thresholds['cpu_usage']
                    })
                
                # Check memory usage
                if current['system']['memory_percent'] > self.thresholds['memory_usage']:
                    issues.append({
                        'type': 'high_memory',
                        'severity': 'warning',
                        'message': f"High memory usage: {current['system']['memory_percent']:.1f}%",
                        'value': current['system']['memory_percent'],
                        'threshold': self.thresholds['memory_usage']
                    })
                
                # Check disk usage
                if current['system']['disk_percent'] > self.thresholds['disk_usage']:
                    issues.append({
                        'type': 'high_disk',
                        'severity': 'critical',
                        'message': f"High disk usage: {current['system']['disk_percent']:.1f}%",
                        'value': current['system']['disk_percent'],
                        'threshold': self.thresholds['disk_usage']
                    })
                
                # Check cache performance
                if 'hits' in current['cache'] and 'misses' in current['cache']:
                    total_requests = current['cache']['hits'] + current['cache']['misses']
                    if total_requests > 0:
                        hit_rate = current['cache']['hits'] / total_requests
                        if hit_rate < self.thresholds['cache_hit_rate']:
                            issues.append({
                                'type': 'low_cache_hit_rate',
                                'severity': 'info',
                                'message': f"Low cache hit rate: {hit_rate:.1%}",
                                'value': hit_rate,
                                'threshold': self.thresholds['cache_hit_rate']
                            })
                
                # Check database pool utilization
                if 'pool_size' in current['database'] and 'checked_out' in current['database']:
                    pool_size = current['database']['pool_size']
                    checked_out = current['database']['checked_out']
                    if pool_size > 0:
                        utilization = checked_out / pool_size
                        if utilization > self.thresholds['db_connection_pool']:
                            issues.append({
                                'type': 'high_db_pool_utilization',
                                'severity': 'warning',
                                'message': f"High database pool utilization: {utilization:.1%}",
                                'value': utilization,
                                'threshold': self.thresholds['db_connection_pool']
                            })
                
                # Store issues for recommendations
                if issues:
                    self.performance_data['issues'] = issues
                    
        except Exception as e:
            logger.error(f"Failed to analyze performance: {str(e)}")
    
    def _generate_recommendations(self):
        """Generate optimization recommendations based on performance analysis"""
        try:
            with self.metrics_lock:
                if not self.performance_data or 'issues' not in self.performance_data:
                    return
                
                recommendations = []
                
                for issue in self.performance_data['issues']:
                    if issue['type'] == 'high_cpu':
                        recommendations.append({
                            'priority': 'medium',
                            'category': 'system',
                            'title': 'Optimize CPU Usage',
                            'description': 'Consider implementing background task processing for heavy computations',
                            'actions': [
                                'Move Monte Carlo simulations to background workers',
                                'Implement request queuing for high-load periods',
                                'Add CPU throttling for non-critical operations'
                            ],
                            'impact': 'High',
                            'effort': 'Medium'
                        })
                    
                    elif issue['type'] == 'high_memory':
                        recommendations.append({
                            'priority': 'high',
                            'category': 'system',
                            'title': 'Optimize Memory Usage',
                            'description': 'Memory usage is approaching critical levels',
                            'actions': [
                                'Implement memory pooling for large objects',
                                'Add memory limits to background tasks',
                                'Optimize data structures and algorithms'
                            ],
                            'impact': 'High',
                            'effort': 'Medium'
                        })
                    
                    elif issue['type'] == 'low_cache_hit_rate':
                        recommendations.append({
                            'priority': 'medium',
                            'category': 'performance',
                            'title': 'Improve Cache Performance',
                            'description': 'Cache hit rate is below optimal levels',
                            'actions': [
                                'Review cache key strategies',
                                'Implement cache warming for frequently accessed data',
                                'Add cache analytics and monitoring'
                            ],
                            'impact': 'Medium',
                            'effort': 'Low'
                        })
                    
                    elif issue['type'] == 'high_db_pool_utilization':
                        recommendations.append({
                            'priority': 'high',
                            'category': 'database',
                            'title': 'Optimize Database Connections',
                            'description': 'Database connection pool is heavily utilized',
                            'actions': [
                                'Increase connection pool size',
                                'Implement connection pooling best practices',
                                'Add database query optimization'
                            ],
                            'impact': 'High',
                            'effort': 'Medium'
                        })
                
                # Store recommendations
                self.optimization_recommendations = recommendations
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        with self.metrics_lock:
            if not self.performance_data:
                return {'status': 'no_data'}
            
            summary = {
                'timestamp': self.performance_data['timestamp'].isoformat(),
                'status': 'healthy',
                'metrics': self.performance_data.copy(),
                'recommendations': self.optimization_recommendations.copy()
            }
            
            # Determine overall status
            if 'issues' in self.performance_data:
                critical_issues = [i for i in self.performance_data['issues'] if i['severity'] == 'critical']
                warning_issues = [i for i in self.performance_data['issues'] if i['severity'] == 'warning']
                
                if critical_issues:
                    summary['status'] = 'critical'
                elif warning_issues:
                    summary['status'] = 'warning'
            
            return summary
    
    def get_historical_metrics(self, category: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for a specific category"""
        with self.metrics_lock:
            if category not in self.metrics:
                return []
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            historical_data = []
            
            for data in self.metrics[category]:
                if data.get('timestamp', datetime.min) >= cutoff_time:
                    historical_data.append(data)
            
            return historical_data
    
    def set_threshold(self, metric: str, value: float):
        """Set performance threshold for a metric"""
        if metric in self.thresholds:
            self.thresholds[metric] = value
            logger.info(f"Updated threshold for {metric}: {value}")
        else:
            logger.warning(f"Unknown metric: {metric}")


def process_memory_percent(rss: int, total: int) -> float:
    """Calculate process memory usage percentage"""
    try:
        return (rss / total) * 100
    except ZeroDivisionError:
        return 0.0


# Performance monitoring decorators

def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                end_memory = psutil.Process().memory_info().rss
                memory_delta = end_memory - start_memory
                
                # Log performance metrics
                logger.info(f"Performance: {name} completed in {execution_time:.3f}s, memory delta: {memory_delta} bytes")
                
                # Check if performance is concerning
                if execution_time > 1.0:
                    logger.warning(f"Slow operation detected: {name} took {execution_time:.3f}s")
                
                if memory_delta > 10 * 1024 * 1024:  # 10MB
                    logger.warning(f"High memory usage detected: {name} used {memory_delta / (1024*1024):.1f}MB")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Performance: {name} failed after {execution_time:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


@contextmanager
def performance_context(operation_name: str):
    """Context manager for performance monitoring"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    try:
        yield
        execution_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss
        memory_delta = end_memory - start_memory
        
        logger.info(f"Performance: {operation_name} completed in {execution_time:.3f}s, memory delta: {memory_delta} bytes")
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Performance: {operation_name} failed after {execution_time:.3f}s: {str(e)}")
        raise


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Performance optimization utilities

def optimize_database_queries():
    """Provide database query optimization recommendations"""
    recommendations = [
        {
            'title': 'Implement Query Caching',
            'description': 'Cache frequently executed queries to reduce database load',
            'implementation': 'Use Redis cache with appropriate TTL for query results',
            'expected_improvement': '20-40% reduction in database response time'
        },
        {
            'title': 'Add Database Indexes',
            'description': 'Create indexes on frequently queried columns',
            'implementation': 'Analyze query patterns and add composite indexes',
            'expected_improvement': '50-80% improvement for indexed queries'
        },
        {
            'title': 'Implement Connection Pooling',
            'description': 'Optimize database connection management',
            'implementation': 'Configure connection pool size and recycling',
            'expected_improvement': '30-50% reduction in connection overhead'
        }
    ]
    
    return recommendations


def optimize_cache_strategy():
    """Provide cache optimization recommendations"""
    recommendations = [
        {
            'title': 'Implement Cache Warming',
            'description': 'Pre-populate cache with frequently accessed data',
            'implementation': 'Background jobs to refresh cache during low-traffic periods',
            'expected_improvement': '15-25% improvement in cache hit rate'
        },
        {
            'title': 'Add Cache Analytics',
            'description': 'Monitor cache performance and optimize strategies',
            'implementation': 'Track hit/miss ratios and access patterns',
            'expected_improvement': '10-20% optimization of cache policies'
        },
        {
            'title': 'Implement Cache Invalidation',
            'description': 'Smart cache invalidation to maintain data consistency',
            'implementation': 'Pattern-based invalidation and TTL management',
            'expected_improvement': 'Improved data consistency and reduced stale data'
        }
    ]
    
    return recommendations


def optimize_background_processing():
    """Provide background processing optimization recommendations"""
    recommendations = [
        {
            'title': 'Implement Task Queuing',
            'description': 'Queue heavy computations to prevent blocking',
            'implementation': 'Use Celery with Redis/RabbitMQ for task management',
            'expected_improvement': 'Eliminate blocking operations, improve responsiveness'
        },
        {
            'title': 'Add Task Prioritization',
            'description': 'Prioritize critical tasks over background operations',
            'implementation': 'Configure task priorities and resource allocation',
            'expected_improvement': 'Better resource utilization and user experience'
        },
        {
            'title': 'Implement Progress Tracking',
            'description': 'Track long-running task progress',
            'implementation': 'Real-time progress updates via WebSocket',
            'expected_improvement': 'Improved user experience and transparency'
        }
    ]
    
    return recommendations


# Health check for performance monitoring
def health_check_performance() -> Dict[str, Any]:
    """Perform health check on performance monitoring system"""
    try:
        # Check if monitoring is active
        if not performance_monitor.monitoring_active:
            return {
                'status': 'degraded',
                'message': 'Performance monitoring is not active'
            }
        
        # Get current performance summary
        summary = performance_monitor.get_performance_summary()
        
        if summary['status'] == 'healthy':
            return {
                'status': 'healthy',
                'message': 'Performance monitoring operational',
                'summary': summary
            }
        else:
            return {
                'status': summary['status'],
                'message': f'Performance issues detected: {summary["status"]}',
                'summary': summary
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Performance monitoring health check failed: {str(e)}'
        }