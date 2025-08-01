# [P5] Locust performance tests for Valor IVX backend (Flask)
# Targets: /api/financial-data/<ticker>, /api/runs, /api/reports/dcf
# Usage examples:
#   LOCUST_BASE_URL=http://localhost:8000 locust -f tests/performance/locustfile.py --headless -u 20 -r 5 -t 1m --csv=tests/performance/artifacts/baseline
# Profiles via ENV:
#   PERF_PROFILE=smoke|baseline|stress|soak
#   TICKER=AAPL (default)
#   AUTH_TOKEN=<bearer jwt> (optional)

import os
import random
from locust import HttpUser, task, between, events

BASE_URL = os.environ.get("LOCUST_BASE_URL", "http://localhost:8000")
PROFILE = os.environ.get("PERF_PROFILE", "baseline").lower()
TICKER = os.environ.get("TICKER", "AAPL")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

# Simple profile presets
def apply_profile(user):
    if PROFILE == "smoke":
        user.wait_time = between(0.5, 1.5)
    elif PROFILE == "baseline":
        user.wait_time = between(0.1, 0.5)
    elif PROFILE == "stress":
        user.wait_time = between(0.0, 0.1)
    elif PROFILE == "soak":
        user.wait_time = between(0.5, 1.0)
    else:
        user.wait_time = between(0.2, 0.6)


def auth_headers():
    hdrs = {"X-Tenant-ID": os.environ.get("TENANT_ID", "default")}
    if AUTH_TOKEN:
        hdrs["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return hdrs


class ValorBackendUser(HttpUser):
    host = BASE_URL
    wait_time = between(0.2, 0.6)

    def on_start(self):
        apply_profile(self)

    @task(4)
    def financial_data(self):
        # GET /api/financial-data/<ticker>
        with self.client.get(f"/api/financial-data/{TICKER}", headers=auth_headers(), name="/api/financial-data/:ticker", catch_response=True) as resp:
            if resp.status_code not in (200, 404):
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(2)
    def list_runs(self):
        # GET /api/runs (requires auth in backend; if AUTH_TOKEN omitted may return 401/403)
        with self.client.get("/api/runs", headers=auth_headers(), name="/api/runs", catch_response=True) as resp:
            if resp.status_code not in (200, 401, 403):
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(1)
    def dcf_report(self):
        # DCF report requires an existing run_id; use a placeholder or skip if not available.
        run_id = os.environ.get("LOCUST_RUN_ID")
        if not run_id:
            return
        params = {"run_id": run_id, "format": "html"}
        with self.client.get("/api/reports/dcf", params=params, headers=auth_headers(), name="/api/reports/dcf?run_id", catch_response=True) as resp:
            if resp.status_code not in (200, 404, 400):
                resp.failure(f"Unexpected status: {resp.status_code}")


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--profile", type=str, env_var="PERF_PROFILE", default="baseline", help="smoke|baseline|stress|soak")
    parser.add_argument("--ticker", type=str, env_var="TICKER", default="AAPL", help="Ticker symbol")
    parser.add_argument("--tenant", type=str, env_var="TENANT_ID", default="default", help="Tenant ID")
    parser.add_argument("--run-id", type=str, env_var="LOCUST_RUN_ID", default="", help="Existing run_id for /api/reports/dcf")
