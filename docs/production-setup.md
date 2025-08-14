# Valor IVX Production Setup Guide

This guide covers the production deployment of the Valor IVX backend with enterprise features, database migrations, and monitoring.

## 🏗️ Architecture Overview

### Components
- **Flask Backend**: Main API server
- **PostgreSQL Database**: Production database for enterprise models
- **Redis**: Caching and session storage
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization (optional)

## 🗄️ Database Setup

### PostgreSQL Configuration

1. **Install PostgreSQL**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo yum install postgresql postgresql-server
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   ```

2. **Create Database and User**:
   ```bash
   sudo -u postgres psql
   
   CREATE DATABASE valor_ivx;
   CREATE USER valor_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE valor_ivx TO valor_user;
   ALTER USER valor_user CREATEDB;
   \q
   ```

3. **Environment Variables**:
   ```bash
   # Database connection
   export DB_URL="postgresql://valor_user:secure_password@localhost/valor_ivx"
   
   # Alternative: Use connection string with SSL
   export DB_URL="postgresql://valor_user:secure_password@localhost/valor_ivx?sslmode=require"
   ```

### Database Migrations

1. **Install Alembic**:
   ```bash
   pip install alembic psycopg2-binary
   ```

2. **Run Migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Verify Migration Status**:
   ```bash
   alembic current
   alembic history
   ```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Database
export DB_URL="postgresql://user:pass@localhost/valor_ivx"

# Security
export SECRET_KEY="your-super-secret-key-here"
export JWT_SECRET_KEY="your-jwt-secret-key-here"

# Redis
export REDIS_URL="redis://localhost:6379/0"

# External APIs
export ALPHA_VANTAGE_API_KEY="your-api-key"

# Feature Flags
export FEATURE_PROMETHEUS_METRICS=true
export ENABLE_ML_MODELS=true
export ENABLE_COLLABORATION=true

# Observability
export LOG_JSON=true
export LOG_LEVEL=INFO
export METRICS_ROUTE="/metrics"
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
```

### Production Configuration File

Create `/etc/valor-ivx/config.env`:
```bash
# Database
DB_URL=postgresql://valor_user:secure_password@localhost/valor_ivx

# Security (generate secure keys)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
ALPHA_VANTAGE_API_KEY=your-api-key

# Features
FEATURE_PROMETHEUS_METRICS=true
ENABLE_ML_MODELS=true
ENABLE_COLLABORATION=true

# Logging
LOG_JSON=true
LOG_LEVEL=INFO
METRICS_ROUTE=/metrics
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

## 🚀 Deployment

### Using Docker Compose

1. **Create docker-compose.prod.yml**:
   ```yaml
   version: '3.8'
   
   services:
     postgres:
       image: postgres:13
       environment:
         POSTGRES_DB: valor_ivx
         POSTGRES_USER: valor_user
         POSTGRES_PASSWORD: secure_password
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
   
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
   
     backend:
       build: ./backend
       environment:
         - DB_URL=postgresql://valor_user:secure_password@postgres/valor_ivx
         - REDIS_URL=redis://redis:6379/0
         - FEATURE_PROMETHEUS_METRICS=true
       ports:
         - "5002:5002"
       depends_on:
         - postgres
         - redis
       volumes:
         - /tmp/prometheus_multiproc:/tmp/prometheus_multiproc
   
     prometheus:
       image: prom/prometheus
       ports:
         - "9090:9090"
       volumes:
         - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
   
   volumes:
     postgres_data:
   ```

2. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Manual Deployment

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install gunicorn psycopg2-binary
   ```

2. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Start with Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5002 --timeout 120 app:app
   ```

## 📊 Monitoring and Metrics

### Prometheus Configuration

Create `monitoring/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'valor-ivx-backend'
    static_configs:
      - targets: ['localhost:5002']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Available Metrics

- **HTTP Requests**: `http_requests_total`
- **Request Duration**: `http_request_duration_seconds`
- **Rate Limiting**: `rate_limit_allowed_total`, `rate_limit_blocked_total`
- **Quota Usage**: `quota_increment_success_total`, `quota_increment_failure_total`
- **Model Performance**: `model_inference_duration_seconds`, `model_predictions_total`

### Health Checks

```bash
# Application health
curl http://localhost:5002/api/health

# Metrics endpoint
curl http://localhost:5002/metrics

# Database connectivity
curl http://localhost:5002/api/health/db
```

## 🔒 Security Considerations

### Database Security
- Use strong passwords for database users
- Enable SSL connections
- Restrict database access to application servers only
- Regular security updates

### Application Security
- Use environment variables for secrets
- Enable HTTPS in production
- Implement proper CORS policies
- Regular dependency updates

### Rate Limiting
- Configure appropriate rate limits per tenant
- Monitor rate limit violations
- Implement progressive rate limiting for abuse prevention

## 🧪 Testing Production Setup

### Database Connection Test
```bash
cd backend
python -c "
from db_enterprise import get_enterprise_session
session = get_enterprise_session()
print('Database connection successful')
session.close()
"
```

### Migration Test
```bash
cd backend
alembic current
alembic history
```

### Metrics Test
```bash
curl http://localhost:5002/metrics | grep valor_ivx
```

## 📝 Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check PostgreSQL service status
   - Verify connection string
   - Check firewall settings

2. **Migration Errors**:
   - Ensure database user has proper permissions
   - Check for conflicting schema changes
   - Review migration history

3. **Metrics Not Available**:
   - Verify `FEATURE_PROMETHEUS_METRICS=true`
   - Check `/tmp/prometheus_multiproc` directory permissions
   - Restart application after configuration changes

### Logs
```bash
# Application logs
tail -f backend/backend.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Docker logs
docker-compose logs -f backend
```
