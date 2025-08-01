# [P5] Gunicorn configuration for Valor IVX Flask backend
# Run with:
#   gunicorn -c backend/gunicorn.conf.py backend.app:app
# Targets: Python 3.11, Flask app at backend.app:app, bind :8000 for local perf tests

import multiprocessing
import os
import random

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# Workers: start with CPU count; gthread for mixed I/O; can switch to gevent if desired
workers = int(os.environ.get("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count())))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.environ.get("GUNICORN_THREADS", 2))

# Timeouts and keepalive tuned for interactive APIs
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 60))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 2))

# Mitigate memory bloat
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 100))

# Access/error logs to stdout/stderr for container environments
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

# Request header size and proxy protocol handling (if behind nginx)
limit_request_line = int(os.environ.get("GUNICORN_LIMIT_REQUEST_LINE", 8190))
limit_request_fields = int(os.environ.get("GUNICORN_LIMIT_REQUEST_FIELDS", 100))
limit_request_field_size = int(os.environ.get("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", 8190))

# Preload app to share memory pages across workers if safe
preload_app = os.environ.get("GUNICORN_PRELOAD", "false").lower() in {"1", "true", "yes"}

def post_worker_init(worker):
    # [P5] Hook for initializing any per-worker state if needed
    pass
