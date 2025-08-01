from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class ModelSpec:
    module: str
    class_name: str
    factory: Optional[Callable[[], Any]] = None


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

    def resolve_alias(self, alias: str) -> str:
        """
        Return final alias considering variants.
        """
        final = self._variants.get(alias, alias)
        # store for introspection/metrics/tests
        self._last_resolution[alias] = final
        return final

    def get(self, alias: str) -> Any:
        """
        Return an instance of the model for the given alias.

        Resolution order:
        1) variant alias mapping (if configured)
        2) factory() if provided
        3) dynamic import of module.class_name

        Fallback: if variant resolves to unknown alias, fallback to base alias.
        """
        final_alias = self.resolve_alias(alias)
        spec = self._registry.get(final_alias)
        if spec is None and final_alias != alias:
            # variant unknown, fallback to base
            spec = self._registry.get(alias)

        if spec is None:
            raise KeyError(f"Model alias not found in registry: {alias} (resolved={final_alias})")

        if spec.factory:
            return spec.factory()

        module = importlib.import_module(spec.module)
        cls = getattr(module, spec.class_name)
        return cls()


# Singleton registry used by tasks and services
registry = ModelRegistry()


def get_model(alias: str) -> Any:
    return registry.get(alias)
