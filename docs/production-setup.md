# Production Setup Guide

This guide describes how to securely deploy the Valor IVX application in production. It covers environment configuration, secrets management, TLS termination, security headers, logging/metrics, and high-level deployment steps.

[Canonical Notice]
If any other document conflicts with this guide, defer to:
- README.md → “How to run, test, and deploy”
- STARTUP_GUIDE.md for local DevX
- This guide for production posture and deployment

## Port Conventions (Production Defaults)
- Backend API: http://localhost:5002 (behind a reverse proxy)
- Frontend: http://localhost:8000 (static served or via CDN/proxy)

## Environment and Secrets

### Principles
- Never commit secrets to the repository.
- Use environment variables only for secrets and configuration.
- Prefer CI/CD secret stores (e.g., GitHub Actions Secrets, AWS SSM Parameter Store, GCP Secret Manager, HashiCorp Vault).
- Use separate configs per environment (dev/staging/prod).

### Core Variables (Backend)
- FLASK_ENV=production
- HOST=0.0.0.0
- PORT=5002
- DATABASE_URL=postgresql://USER:PASS@HOST/DB
- SECRET_KEY=“strong-secret” (environment only)
- JWT_SECRET_KEY=“strong-jwt-secret” (environment only)
- FEATURE_PROMETHEUS_METRICS=true|false
- PROMETHEUS_MULTIPROC_DIR=/var/run/prom (for Gunicorn multiprocess metrics)
- LOG_JSON=true
- LOG_LEVEL=INFO
- CORS_ORIGINS=https://your-frontend-domain.tld

Example export (for testing locally only; prefer CI/CD injection in real deployments):
```bash
export FLASK_ENV=production
export PORT=5002
export DATABASE_URL=postgresql://user:pass@db/valor_ivx
export SECRET_KEY='replace-with-strong'
export JWT_SECRET_KEY='replace-with-strong'
export FEATURE_PROMETHEUS_METRICS=true
export LOG_JSON=true
export LOG_LEVEL=INFO
```

## TLS Termination and Reverse Proxy

Terminate TLS at a reverse proxy (e.g., Nginx) and forward to the backend on 5002. Serve the frontend statically via Nginx or a CDN.

### Nginx Example (TLS termination + security headers)

```
server {
    listen 443 ssl http2;
    server_name your-domain.tld;

    ssl_certificate /etc/letsencrypt/live/your-domain.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.tld/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Content Security Policy (tighten per your asset and API usage)
    add_header Content-Security-Policy "
        default-src 'self';
        connect-src 'self' https://api.your-domain.tld;
        img-src 'self' data:;
        script-src 'self';
        style-src 'self' 'unsafe-inline';
        frame-ancestors 'none';
    " always;

    # Frontend static files
    root /var/www/valor-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120;
    }

    # Metrics (optionally expose internally only)
    location /metrics {
        allow 127.0.0.1;
        deny all; # expose only to Prometheus collector or internal network
        proxy_pass http://127.0.0.1:5002/metrics;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.tld;
    return 301 https://$host$request_uri;
}
```

Notes:
- Limit /metrics exposure to internal networks or specific IPs.
- Tighten CSP per your actual asset/CDN usage.
- Use a separate origin for API if preferred, and update CORS accordingly.

## Security Posture

- HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy enforced at proxy.
- Bcrypt for password hashing.
- Minimal JWT guard across sensitive endpoints (enhancements planned in P6: robust JWT with refresh and revocation).
- Tenant enforcement: required on runs, scenarios, financial-data, LBO, M&A, notes.
- Public/system endpoints: “/”, “/api/health”, websocket status, and “/metrics” when enabled.
- Health endpoint is unthrottled. Rate limiting remains across sensitive endpoints; financial data endpoints maintain a dedicated limiter.

## Observability

### Logging
- Structured JSON logs via structlog (backend/logging.py).
- Correlate by request_id and tenant_id.
- Configure level via LOG_LEVEL (INFO recommended for prod, DEBUG disabled).

### Metrics
- Enable with FEATURE_PROMETHEUS_METRICS=true.
- Prometheus metrics exposed at /metrics:
  - http_requests_total{method,endpoint,status,tenant}
  - http_request_duration_seconds
- Use PROMETHEUS_MULTIPROC_DIR for Gunicorn multiprocess scraping.

### SLOs and Alerting (roadmap P2)
- Define availability and latency (P95/P99) SLOs for key endpoints.
- Create alert rules on error rate and latency breaches.
- Reference docs/observability for example dashboards and runbooks.

## Deployment

### Option A: Gunicorn behind Nginx
1. Build and install dependencies.
2. Export environment variables (via systemd unit or process manager).
3. Start Gunicorn:
   ```bash
   gunicorn --bind 127.0.0.1:5002 --workers 4 --timeout 120 app:app
   ```
4. Ensure Nginx proxy configured as above.
5. Validate:
   - Health: curl -s https://your-domain.tld/api/health
   - Metrics (internal): curl -s http://127.0.0.1:5002/metrics

### Option B: Docker / Docker Compose
- Backend Dockerfile provided (backend/Dockerfile).
- Example run:
  ```bash
  docker build -t valor-ivx-backend:prod backend
  docker run -d \
    -p 5002:5002 \
    -e FLASK_ENV=production \
    -e DATABASE_URL=postgresql://user:pass@db/valor_ivx \
    -e SECRET_KEY=... \
    -e JWT_SECRET_KEY=... \
    -e FEATURE_PROMETHEUS_METRICS=true \
    valor-ivx-backend:prod
  ```
- Place Nginx in front of the container for TLS and headers.

### Zero-Downtime and Readiness (expand in P2)
- Use process managers (systemd, supervisor) or orchestration (Kubernetes) with readiness probes.
- Readiness should validate:
  - DB connectivity
  - Cache status (if used)
  - Third-party API reachability (as appropriate)
- Rolling restarts to avoid downtime.

## Verification Checklist

- [ ] HTTPS enabled with valid TLS certificate
- [ ] HSTS, CSP, and other security headers applied
- [ ] Backend bound to localhost:5002 behind proxy (or internal network only)
- [ ] Secrets loaded from environment/secret store
- [ ] /metrics enabled and scraped internally only (if enabled)
- [ ] Logs in JSON with request_id and tenant_id
- [ ] CORS configured for frontend domain
- [ ] Health endpoint accessible; protected routes enforce tenancy

## Sample cURL

Health (no tenant required):
```bash
curl -s https://your-domain.tld/api/health
```

Protected route (tenant required):
```bash
curl -s -H "X-Tenant-ID: demo" https://your-domain.tld/api/runs
```

Metrics (internal only):
```bash
curl -s http://127.0.0.1:5002/metrics
```

## Roadmap References
- P2: SLOs, readiness probes, alerting
- P6: Robust JWT session model with refresh rotation and revocation
- docs/observability: dashboards and runbooks
