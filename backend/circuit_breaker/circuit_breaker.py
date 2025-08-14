"""
Circuit breaker pattern implementation for external API calls.

This module provides a robust circuit breaker implementation with:
- Three states: CLOSED, OPEN, HALF_OPEN
- Configurable failure thresholds and recovery timeouts
- Metrics integration for monitoring
- Async support for modern Python applications
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
# from backend.metrics import circuit_breaker_metrics  # Commented out for now

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Number of failures to open circuit
    recovery_timeout: int = 60        # Seconds to wait before half-open
    expected_exception: type = Exception  # Exception type to count as failure
    success_threshold: int = 2        # Successes needed to close circuit
    timeout: float = 30.0             # Request timeout in seconds

class CircuitBreaker:
    """Circuit breaker implementation for external API calls"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Metrics
        # self.metrics = circuit_breaker_metrics.labels(
        #     circuit_name=name,
        #     state=self.state.value
        # )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._set_half_open()
            else:
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self._on_failure(TimeoutError("Request timeout"))
            raise
        except self.config.expected_exception as e:
            self._on_failure(e)
            raise
        except Exception as e:
            # Unexpected exceptions don't count as failures
            raise
    
    def _on_success(self):
        """Handle successful request"""
        self.failure_count = 0
        self.success_count += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN and self.success_count >= self.config.success_threshold:
            self._set_closed()
        
        # Update metrics
        # self.metrics.labels(state=self.state.value).inc()
    
    def _on_failure(self, exception: Exception):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self._set_open()
        
        # Update metrics
        # self.metrics.labels(state=self.state.value).inc()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return False
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _set_open(self):
        """Set circuit to open state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        # self.metrics.labels(state=self.state.value).inc()
    
    def _set_half_open(self):
        """Set circuit to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        # self.metrics.labels(state=self.state.value).inc()
    
    def _set_closed(self):
        """Set circuit to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        # self.metrics.labels(state=self.state.value).inc()
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time,
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'timeout': self.config.timeout
            }
        }

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.circuits: Dict[str, CircuitBreaker] = {}
    
    def get_circuit(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuits:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuits[name] = CircuitBreaker(name, config)
        
        return self.circuits[name]
    
    def get_all_status(self) -> Dict[str, dict]:
        """Get status of all circuit breakers"""
        return {name: circuit.get_status() for name, circuit in self.circuits.items()}
    
    def reset_circuit(self, name: str):
        """Manually reset a circuit breaker"""
        if name in self.circuits:
            self.circuits[name]._set_closed()

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager() 