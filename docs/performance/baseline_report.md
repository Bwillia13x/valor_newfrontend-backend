# [P5] Baseline Performance Report

Version: 1.0.0  
Date: TBD (auto-filled after run)  
Environment: Local (Gunicorn + Flask, Redis local)

Executive Summary
- Scope: /api/financial-data/:ticker, /api/runs, /api/reports/*
- Budgets vs Baseline: Pending initial execution
- Risks / Notes:
  - Financial-data endpoints depend on external providers; cache or mock recommended for deterministic baselines.
  - /api/runs requires valid JWT; without AUTH_TOKEN test will record 401/403 as expected.

Methodology
- Tooling: Locust (tests/performance/locustfile.py)
- Profiles:
  - smoke: sanity checks, low concurrency
  - baseline: steady-state for percentile measurement
  - stress: ramp load to find knee point
  - soak: long duration stability check
- Configuration (defaults; override via env):
  - LOCUST_BASE_URL=http://localhost:8000
  - TICKER=AAPL
  - TENANT_ID=default
  - USERS, SPAWN_RATE, RUN_TIME set by profile wrappers or CLI
- Metrics captured:
  - RPS, P50/P95/P99 latency, error rate
  - Per-endpoint breakdown
  - System metrics (via Prometheus where enabled)

Results (Initial)
- Pending first run. Artifacts will be written to tests/performance/artifacts:
  - baseline_stats.csv/json
  - env.json snapshot

Endpoints and Budgets (from SLOs.md)
- /api/financial-data/:ticker: P95 ≤ 300ms, P99 ≤ 600ms, 150 RPS
- /api/runs: P95 ≤ 500ms, P99 ≤ 1000ms, 100 RPS
- /api/reports/*: P95 ≤ 1500ms, P99 ≤ 3000ms, 40 RPS
- Error rate ≤ 0.5% sustained

Optimizations Roadmap (to validate after baseline)
- Computation:
  - Add timing spans around heavy computations (DCF/Monte Carlo), consider NumPy for backend paths.
  - Cache by parameter hash (Redis + in-process LRU), adaptive sampling for Monte Carlo.
- Data access:
  - Audit N+1 queries; add proper indexes; projection & pagination; read-through cache + negative caching.
- Caching patterns:
  - LKG + TTL; consider stale-while-revalidate for provider-backed data; circuit breaker/backoff.
- Transport:
  - Gzip/Brotli; consider MessagePack for large arrays; server-side aggregation for heavy reports.

Tuning Artifacts Summary
- Gunicorn (backend/gunicorn.conf.py): workers=2–4, gthread worker-class, timeout=60, keepalive=2, max_requests with jitter.
- Nginx (backend/nginx/nginx.conf): gzip enabled; brotli hints; proxy buffers tuned; security headers.
- Redis: redis://localhost:6379; per-tenant key namespace for cache.

Next Steps
1) Run smoke and baseline profiles locally.
2) Populate this report with CSV/JSON stats and summarized metrics.
3) Prioritize top hot paths and implement targeted optimizations.
4) Re-run baseline and update deltas.
