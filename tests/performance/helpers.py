# [P5] Helpers for Locust performance runs
# - Utilities to emit environment info and configure default headers
# - CSV/JSON artifact paths

import os
import json
import time
from typing import Dict, Any

ARTIFACT_DIR = os.environ.get("PERF_ARTIFACT_DIR", "tests/performance/artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def default_headers() -> Dict[str, str]:
    hdrs = {"X-Tenant-ID": os.environ.get("TENANT_ID", "default")}
    auth = os.environ.get("AUTH_TOKEN")
    if auth:
        hdrs["Authorization"] = f"Bearer {auth}"
    return hdrs

def write_env_snapshot(filename: str = "env.json") -> str:
    path = os.path.join(ARTIFACT_DIR, filename)
    payload: Dict[str, Any] = {
        "timestamp": time.time(),
        "base_url": os.environ.get("LOCUST_BASE_URL", "http://localhost:8000"),
        "profile": os.environ.get("PERF_PROFILE", "baseline"),
        "users": os.environ.get("LOCUST_USERS"),
        "spawn_rate": os.environ.get("LOCUST_SPAWN_RATE"),
        "run_time": os.environ.get("LOCUST_RUN_TIME"),
        "ticker": os.environ.get("TICKER", "AAPL"),
        "tenant": os.environ.get("TENANT_ID", "default"),
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path
