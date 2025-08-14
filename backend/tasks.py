"""
Background task processing for Valor IVX
Handles heavy computations like Monte Carlo simulations asynchronously
"""

import os
import time
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps

from celery import Celery, current_task
from celery.result import AsyncResult
from celery.exceptions import CeleryError

from .settings import settings
from .cache import cache_manager

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'valor_ivx',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['backend.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3000,  # 50 minutes soft timeout
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # Results expire after 1 hour
    task_always_eager=False,  # Set to True for testing without Celery
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_compression='gzip',
    result_compression='gzip',
)


class TaskManager:
    """Manages background task execution and monitoring"""
    
    def __init__(self):
        self.active_tasks = {}
        self.task_results = {}
    
    def submit_task(self, task_name: str, task_args: tuple = None, 
                   task_kwargs: dict = None, priority: int = 0) -> str:
        """Submit a task for background execution"""
        try:
            task_args = task_args or ()
            task_kwargs = task_kwargs or {}
            
            # Add metadata to task
            task_kwargs['submitted_at'] = datetime.utcnow().isoformat()
            task_kwargs['priority'] = priority
            
            # Submit task to Celery
            task = celery_app.send_task(
                task_name,
                args=task_args,
                kwargs=task_kwargs,
                priority=priority
            )
            
            task_id = task.id
            self.active_tasks[task_id] = {
                'task_name': task_name,
                'status': 'PENDING',
                'submitted_at': datetime.utcnow(),
                'priority': priority
            }
            
            logger.info(f"Task {task_name} submitted with ID: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task {task_name}: {str(e)}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current status of a task"""
        try:
            if task_id in self.active_tasks:
                # Check Celery result
                result = AsyncResult(task_id, app=celery_app)
                
                status_info = {
                    'task_id': task_id,
                    'status': result.status,
                    'submitted_at': self.active_tasks[task_id]['submitted_at'].isoformat(),
                    'priority': self.active_tasks[task_id]['priority']
                }
                
                if result.ready():
                    if result.successful():
                        status_info['result'] = result.result
                        status_info['completed_at'] = datetime.utcnow().isoformat()
                        # Store result and clean up
                        self.task_results[task_id] = result.result
                        del self.active_tasks[task_id]
                    else:
                        status_info['error'] = str(result.info)
                        status_info['failed_at'] = datetime.utcnow().isoformat()
                        del self.active_tasks[task_id]
                else:
                    # Task still running
                    if hasattr(result, 'info'):
                        status_info['progress'] = result.info
                
                return status_info
            else:
                # Check if task completed and result stored
                if task_id in self.task_results:
                    return {
                        'task_id': task_id,
                        'status': 'COMPLETED',
                        'result': self.task_results[task_id],
                        'completed_at': datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        'task_id': task_id,
                        'status': 'NOT_FOUND',
                        'error': 'Task not found'
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            if task_id in self.active_tasks:
                result = AsyncResult(task_id, app=celery_app)
                result.revoke(terminate=True)
                del self.active_tasks[task_id]
                logger.info(f"Task {task_id} cancelled")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of all active tasks"""
        active_tasks = []
        for task_id, task_info in self.active_tasks.items():
            status_info = self.get_task_status(task_id)
            active_tasks.append(status_info)
        return active_tasks
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed task results"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_task_ids = [
            task_id for task_id, result in self.task_results.items()
            if isinstance(result, dict) and 
            result.get('completed_at') and 
            datetime.fromisoformat(result['completed_at']) < cutoff_time
        ]
        
        for task_id in old_task_ids:
            del self.task_results[task_id]
        
        if old_task_ids:
            logger.info(f"Cleaned up {len(old_task_ids)} old task results")


# Global task manager instance
task_manager = TaskManager()


def background_task(task_name: str = None, priority: int = 0, 
                   cache_result: bool = True, cache_ttl: int = 3600):
    """Decorator to make a function run as a background task"""
    def decorator(func):
        name = task_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we're in a Celery worker
            if current_task:
                # Running in Celery worker, execute function
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Update task progress
                    current_task.update_state(
                        state='SUCCESS',
                        meta={
                            'execution_time': execution_time,
                            'result_size': len(str(result)) if result else 0
                        }
                    )
                    
                    # Cache result if requested
                    if cache_result and result:
                        cache_key = f"task_result:{name}:{hash(str(args) + str(kwargs))}"
                        cache_manager.set(cache_key, result, cache_ttl)
                    
                    return result
                    
                except Exception as e:
                    current_task.update_state(
                        state='FAILURE',
                        meta={'error': str(e)}
                    )
                    raise
            else:
                # Not in Celery worker, submit as background task
                task_id = task_manager.submit_task(name, args, kwargs, priority)
                return {
                    'task_id': task_id,
                    'status': 'SUBMITTED',
                    'message': f'Task {name} submitted for background execution'
                }
        
        return wrapper
    return decorator


# Specific task implementations for financial calculations

@celery_app.task(bind=True)
def monte_carlo_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Background Monte Carlo simulation task"""
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'progress': 0})
        
        # Extract parameters
        trials = params.get('trials', 1000)
        batch_size = 100
        
        results = []
        for i in range(0, trials, batch_size):
            # Simulate batch of trials
            batch_trials = min(batch_size, trials - i)
            
            # Simulate financial calculations (placeholder for actual logic)
            batch_results = simulate_financial_trials(batch_trials, params)
            results.extend(batch_results)
            
            # Update progress
            progress = min(100, (i + batch_size) / trials * 100)
            self.update_state(
                state='PROGRESS',
                meta={'progress': progress, 'completed_trials': i + batch_size}
            )
            
            # Small delay to prevent overwhelming
            time.sleep(0.01)
        
        # Calculate final statistics
        final_result = calculate_statistics(results)
        
        self.update_state(state='SUCCESS', meta={'progress': 100})
        return final_result
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True)
def portfolio_optimization(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Background portfolio optimization task"""
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0})
        
        # Portfolio optimization logic (placeholder)
        result = optimize_portfolio(params)
        
        self.update_state(state='SUCCESS', meta={'progress': 100})
        return result
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(bind=True)
def financial_data_processing(self, tickers: List[str]) -> Dict[str, Any]:
    """Background financial data processing task"""
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0})
        
        results = {}
        total_tickers = len(tickers)
        
        for i, ticker in enumerate(tickers):
            # Process financial data for ticker
            ticker_data = process_ticker_data(ticker)
            results[ticker] = ticker_data
            
            # Update progress
            progress = (i + 1) / total_tickers * 100
            self.update_state(
                state='PROGRESS',
                meta={'progress': progress, 'processed_tickers': i + 1}
            )
        
        self.update_state(state='SUCCESS', meta={'progress': 100})
        return results
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


# Placeholder functions for actual financial calculations
def simulate_financial_trials(trials: int, params: Dict[str, Any]) -> List[float]:
    """Simulate financial trials (placeholder implementation)"""
    import random
    return [random.gauss(100, 20) for _ in range(trials)]


def calculate_statistics(results: List[float]) -> Dict[str, Any]:
    """Calculate statistics from simulation results (placeholder implementation)"""
    if not results:
        return {}
    
    return {
        'mean': sum(results) / len(results),
        'median': sorted(results)[len(results) // 2],
        'min': min(results),
        'max': max(results),
        'count': len(results)
    }


def optimize_portfolio(params: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize portfolio (placeholder implementation)"""
    return {
        'optimal_weights': [0.3, 0.3, 0.4],
        'expected_return': 0.08,
        'volatility': 0.15,
        'sharpe_ratio': 0.53
    }


def process_ticker_data(ticker: str) -> Dict[str, Any]:
    """Process ticker data (placeholder implementation)"""
    return {
        'ticker': ticker,
        'processed_at': datetime.utcnow().isoformat(),
        'status': 'completed'
    }


# Health check for task system
def health_check_tasks() -> Dict[str, Any]:
    """Perform health check on task system"""
    try:
        # Check Celery worker status
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        
        # Check Redis connection
        celery_app.control.ping()
        
        return {
            'status': 'healthy',
            'message': 'Task system operational',
            'active_workers': len(active_workers) if active_workers else 0,
            'registered_tasks': len(registered_tasks) if registered_tasks else 0,
            'active_tasks': len(task_manager.active_tasks),
            'cached_results': len(task_manager.task_results)
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Task system health check failed: {str(e)}'
        }


# Task monitoring and metrics
def get_task_metrics() -> Dict[str, Any]:
    """Get task system metrics"""
    try:
        inspect = celery_app.control.inspect()
        
        metrics = {
            'active_tasks': len(task_manager.active_tasks),
            'cached_results': len(task_manager.task_results),
            'workers': {}
        }
        
        # Get worker statistics
        stats = inspect.stats()
        if stats:
            for worker_name, worker_stats in stats.items():
                metrics['workers'][worker_name] = {
                    'pool_size': worker_stats.get('pool', {}).get('size', 0),
                    'active_tasks': worker_stats.get('pool', {}).get('active', 0),
                    'processed_tasks': worker_stats.get('total', {}).get('total', 0)
                }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get task metrics: {str(e)}")
        return {'error': str(e)}
