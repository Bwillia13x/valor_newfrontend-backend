from __future__ import annotations
from typing import Any, Dict, List


class PortfolioOptimizerV2:
    """
    A simple variant of PortfolioOptimizer for testing/routing purposes.
    Implements optimize(assets, constraints) - returns a dict with variant marker.
    """

    def optimize(self, assets: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Any:
        # Minimal behavior to allow unit tests to assert variant selection
        tickers = [a.get("ticker") or a.get("symbol") for a in (assets or [])]
        return {
            "variant": "v2",
            "assets": tickers,
            "constraints_keys": sorted(list((constraints or {}).keys())),
        }
