from __future__ import annotations
from typing import Any, Dict, List


class RevenuePredictorV2:
    """
    A simple variant of RevenuePredictor for testing/routing purposes.
    Implements predict(historical_data) - returns a dict with variant marker.
    """

    def predict(self, historical_data: List[Dict[str, Any]]) -> Any:
        # Minimal behavior to allow unit tests to assert variant selection
        return {
            "variant": "v2",
            "count": len(historical_data or []),
        }
