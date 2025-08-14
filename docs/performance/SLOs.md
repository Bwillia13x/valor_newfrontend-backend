# [P5] Performance Budgets and SLOs

Scope Endpoints
- GET /api/financial-data/:ticker
- GET /api/runs
- GET /api/reports/*
- Health: /api/health, /api/readiness (observed but not budgeted)

SLIs
- Throughput (RPS)
- Latency percentiles (P50, P95, P99)
- Error rate (HTTP 5xx) under load
- Saturation (CPU, memory, worker utilization)

Budgets (initial; refine after baseline)
- /api/financial-data/:ticker
  - P95 ≤ 300ms
  - P99 ≤ 600ms
  - Sustain 150 RPS
- /api/runs
  - P95 ≤ 500ms
  - P99 ≤ 1000ms
  - Sustain 100 RPS
- /api/reports/*
  - P95 ≤ 1500ms
  - P99 ≤ 3000ms
  - Sustain 40 RPS
- Error rate ≤ 0.5% during sustained load windows
- No prolonged tail: P99 should not exceed 2x P95 for longer than 5 minutes

Timeouts and Retries
- Upstream/client: 5–10s for interactive endpoints; report generation is offloaded
- Server (Gunicorn): worker timeout 60s; keepalive 2s
- Providers: 2–5s timeouts with exponential backoff and circuit breaker

Scaling Guidance
- Start 2–4 workers per node (gthread or gevent for I/O)
- Autoscale on CPU ≥ 70% over 5m or sustained P95 budget violations
- Redis for shared cache and rate-limit state

Observability Alignment
- Prometheus histograms for HTTP duration
- Per-endpoint counters and error tracking
- Burn-rate alerts for SLOs

Change Control
- Any change to budgets requires updating this doc and alerting rules
