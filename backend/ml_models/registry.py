from __future__ import annotations

import importlib
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, List, Tuple


@dataclass(frozen=True)
class ModelSpec:
    module: str
    class_name: str
    factory: Optional[Callable[[], Any]] = None


@dataclass(frozen=True)
class ABTestConfig:
    """Configuration for A/B testing model variants"""
    variant_a: str
    variant_b: str
    traffic_split: float = 0.5  # Percentage of traffic to variant B
    enabled: bool = True


# Default registry map. Keys are stable aliases referenced from settings.
DEFAULT_REGISTRY: Dict[str, ModelSpec] = {
    # revenue prediction models
    "revenue_predictor": ModelSpec(
        module="backend.ml_models.revenue_predictor",
        class_name="RevenuePredictor",
    ),
    "revenue_predictor_v2": ModelSpec(
        module="backend.ml_models.revenue_predictor_v2",
        class_name="RevenuePredictorV2",
    ),
    # portfolio optimizers
    "portfolio_optimizer": ModelSpec(
        module="backend.ml_models.portfolio_optimizer",
        class_name="PortfolioOptimizer",
    ),
    "portfolio_optimizer_v2": ModelSpec(
        module="backend.ml_models.portfolio_optimizer_v2",
        class_name="PortfolioOptimizerV2",
    ),
}


class ModelRegistry:
    def __init__(self, base_registry: Optional[Dict[str, ModelSpec]] = None) -> None:
        self._registry: Dict[str, ModelSpec] = dict(base_registry or DEFAULT_REGISTRY)
        # optional alias remapping for experiments
        self._variants: Dict[str, str] = {}
        # Track variant mapping attempts for observability/tests
        self._last_resolution: Dict[str, str] = {}
        # A/B testing configurations
        self._ab_tests: Dict[str, ABTestConfig] = {}
        # Performance tracking
        self._performance_metrics: Dict[str, List[float]] = {}
        # Model usage counters
        self._usage_counters: Dict[str, int] = {}

    def register(self, alias: str, module: str, class_name: str, factory: Optional[Callable[[], Any]] = None) -> None:
        self._registry[alias] = ModelSpec(module=module, class_name=class_name, factory=factory)

    def set_variant(self, base_alias: str, variant_alias: str) -> None:
        """
        Route base_alias to variant_alias. If variant_alias is empty, remove override.
        """
        if variant_alias:
            self._variants[base_alias] = variant_alias
        elif base_alias in self._variants:
            del self._variants[base_alias]

    def configure_ab_test(self, base_alias: str, variant_a: str, variant_b: str, 
                         traffic_split: float = 0.5, enabled: bool = True) -> None:
        """
        Configure A/B testing for a model variant.
        
        Args:
            base_alias: The base model alias
            variant_a: First variant alias
            variant_b: Second variant alias  
            traffic_split: Percentage of traffic to send to variant B (0.0 to 1.0)
            enabled: Whether A/B testing is enabled
        """
        self._ab_tests[base_alias] = ABTestConfig(
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split,
            enabled=enabled
        )

    def resolve_alias(self, alias: str) -> str:
        """
        Return final alias considering variants and A/B testing.
        """
        # Check if A/B testing is configured for this alias
        if alias in self._ab_tests and self._ab_tests[alias].enabled:
            ab_config = self._ab_tests[alias]
            # Use random selection based on traffic split
            if random.random() < ab_config.traffic_split:
                final = ab_config.variant_b
            else:
                final = ab_config.variant_a
        else:
            # Use standard variant routing
            final = self._variants.get(alias, alias)
        
        # store for introspection/metrics/tests
        self._last_resolution[alias] = final
        return final

    def get(self, alias: str) -> Any:
        """
        Return an instance of the model for the given alias.

        Resolution order:
        1) A/B testing routing (if configured)
        2) variant alias mapping (if configured)
        3) factory() if provided
        4) dynamic import of module.class_name

        Fallback: if variant resolves to unknown alias, fallback to base alias.
        """
        final_alias = self.resolve_alias(alias)
        spec = self._registry.get(final_alias)
        if spec is None and final_alias != alias:
            # variant unknown, fallback to base
            spec = self._registry.get(alias)

        if spec is None:
            raise KeyError(f"Model alias not found in registry: {alias} (resolved={final_alias})")

        # Track usage
        self._usage_counters[final_alias] = self._usage_counters.get(final_alias, 0) + 1

        if spec.factory:
            return spec.factory()

        module = importlib.import_module(spec.module)
        cls = getattr(module, spec.class_name)
        return cls()

    def track_performance(self, alias: str, execution_time: float) -> None:
        """
        Track performance metrics for a model variant.
        
        Args:
            alias: The model alias
            execution_time: Execution time in seconds
        """
        if alias not in self._performance_metrics:
            self._performance_metrics[alias] = []
        self._performance_metrics[alias].append(execution_time)
        
        # Keep only last 1000 measurements to prevent memory bloat
        if len(self._performance_metrics[alias]) > 1000:
            self._performance_metrics[alias] = self._performance_metrics[alias][-1000:]

    def get_performance_stats(self, alias: str) -> Optional[Dict[str, float]]:
        """
        Get performance statistics for a model variant.
        
        Returns:
            Dictionary with min, max, mean, median, p95, p99 execution times
        """
        if alias not in self._performance_metrics or not self._performance_metrics[alias]:
            return None
        
        times = self._performance_metrics[alias]
        sorted_times = sorted(times)
        
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "mean": sum(times) / len(times),
            "median": sorted_times[len(sorted_times) // 2],
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
        }

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get usage statistics for all models.
        
        Returns:
            Dictionary mapping model aliases to usage counts
        """
        return dict(self._usage_counters)

    def get_ab_test_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get A/B testing statistics.
        
        Returns:
            Dictionary with A/B test configurations and usage counts
        """
        stats = {}
        for base_alias, config in self._ab_tests.items():
            variant_a_count = self._usage_counters.get(config.variant_a, 0)
            variant_b_count = self._usage_counters.get(config.variant_b, 0)
            total_count = variant_a_count + variant_b_count
            
            stats[base_alias] = {
                "variant_a": config.variant_a,
                "variant_b": config.variant_b,
                "traffic_split": config.traffic_split,
                "enabled": config.enabled,
                "variant_a_count": variant_a_count,
                "variant_b_count": variant_b_count,
                "total_count": total_count,
                "actual_split": variant_b_count / total_count if total_count > 0 else 0.0
            }
        return stats

    def clear_performance_metrics(self, alias: Optional[str] = None) -> None:
        """
        Clear performance metrics for a specific alias or all aliases.
        
        Args:
            alias: Specific alias to clear, or None to clear all
        """
        if alias:
            self._performance_metrics.pop(alias, None)
        else:
            self._performance_metrics.clear()

    def clear_usage_stats(self) -> None:
        """Clear all usage statistics."""
        self._usage_counters.clear()


# Singleton registry used by tasks and services
registry = ModelRegistry()


def get_model(alias: str) -> Any:
    return registry.get(alias)


def track_model_performance(alias: str, execution_time: float) -> None:
    """Track performance for a model variant."""
    registry.track_performance(alias, execution_time)


def get_model_performance_stats(alias: str) -> Optional[Dict[str, float]]:
    """Get performance statistics for a model variant."""
    return registry.get_performance_stats(alias)
