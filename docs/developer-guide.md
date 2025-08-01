# Valor IVX Developer Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment](#development-environment)
4. [Code Structure](#code-structure)
5. [API Development](#api-development)
6. [Frontend Development](#frontend-development)
7. [Database Design](#database-design)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)
10. [Monitoring and Observability](#monitoring-and-observability)
11. [Security](#security)
12. [Performance Optimization](#performance-optimization)
13. [Contributing](#contributing)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis 6+
- PostgreSQL 13+
- Docker and Docker Compose

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/valor-ivx.git
   cd valor-ivx
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Run locally**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python run.py

   # Frontend
   cd ..
   npm install
   npm start
   ```

5. **Access the application**
   - Frontend: http://localhost:8000
   - Backend API: http://localhost:5000
   - API Documentation: http://localhost:5000/docs

## Architecture Overview

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/JS)    │◄──►│   (Flask)       │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Redis Cache   │    │   File Storage  │
│   (Real-time)   │    │   (Session)     │    │   (Uploads)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Backend:**
- **Framework**: Flask 2.3+
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Authentication**: JWT
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest
- **Monitoring**: Prometheus + Grafana

**Frontend:**
- **Framework**: Vanilla JavaScript (ES6+)
- **Build Tool**: Webpack/Vite
- **Styling**: CSS3 with custom framework
- **Charts**: Chart.js
- **Real-time**: WebSocket

**DevOps:**
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana
- **Logging**: Structured logging with structlog

## Development Environment

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Application
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/valor_ivx

# Redis
REDIS_URL=redis://localhost:6379

# External APIs
ALPHA_VANTAGE_API_KEY=your-api-key

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_MULTIPROC_DIR=/tmp

# Security
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Development Tools

**Recommended VS Code Extensions:**
- Python
- JavaScript and TypeScript
- Docker
- GitLens
- REST Client
- Thunder Client

**Useful Commands:**
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend

# Format code
black backend/
prettier --write js/

# Lint code
flake8 backend/
eslint js/

# Type checking
mypy backend/
```

## Code Structure

### Backend Structure

```
backend/
├── api/                    # API route modules
│   ├── __init__.py
│   ├── analytics_routes.py
│   ├── credit_risk_routes.py
│   ├── portfolio_routes.py
│   ├── real_options_routes.py
│   ├── risk_routes.py
│   └── tenant_routes.py
├── ml_models/             # Machine learning models
│   ├── __init__.py
│   ├── credit_risk.py
│   ├── portfolio_optimizer.py
│   ├── real_options.py
│   ├── registry.py
│   ├── revenue_predictor.py
│   └── risk_assessor.py
├── models/                # Database models
│   ├── __init__.py
│   └── rbac.py
├── security/              # Security modules
│   ├── __init__.py
│   └── encryption.py
├── utils/                 # Utility modules
│   ├── __init__.py
│   └── response_utils.py
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_auth.py
│   └── test_ml_models.py
├── app.py                 # Main application
├── auth.py                # Authentication
├── config.py              # Configuration
├── financial_data.py      # Financial data handling
├── monitoring.py          # Monitoring and SLOs
├── websocket_manager.py   # WebSocket management
└── requirements.txt       # Python dependencies
```

### Frontend Structure

```
js/
├── modules/               # JavaScript modules
│   ├── analytics.js
│   ├── auth.js
│   ├── backend.js
│   ├── charting.js
│   ├── collaboration-engine.js
│   ├── dcf-engine.js
│   ├── financial-data.js
│   ├── lbo-engine.js
│   ├── ma-engine.js
│   ├── monte-carlo.js
│   ├── real-options.js
│   ├── scenarios.js
│   ├── sensitivity-analysis.js
│   └── utils.js
├── main.js                # Main application entry
└── modules/               # Additional modules
    ├── advanced-charting.js
    ├── analytics-dashboard.js
    ├── pwa-manager.js
    ├── realtime.js
    ├── ui-handlers.js
    ├── version-control.js
    └── video-conference.js
```

## API Development

### Creating New Endpoints

1. **Define the route in the appropriate module**

```python
# backend/api/analytics_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/new-endpoint', methods=['POST'])
@jwt_required()
def new_endpoint():
    """New analytics endpoint"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Process data
        result = process_data(data)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

2. **Register the blueprint in app.py**

```python
# backend/app.py
from api.analytics_routes import analytics_bp

app.register_blueprint(analytics_bp)
```

3. **Add tests**

```python
# backend/tests/test_api.py
def test_new_endpoint():
    """Test new analytics endpoint"""
    response = client.post('/api/analytics/new-endpoint', 
                          json={'test': 'data'})
    assert response.status_code == 200
    assert response.json['success'] is True
```

### Input Validation

Use Pydantic for request/response validation:

```python
from pydantic import BaseModel, Field
from typing import Optional

class AnalyticsRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    analysis_type: str = Field(..., regex='^(dcf|lbo|ma)$')
    parameters: dict = Field(default_factory=dict)

class AnalyticsResponse(BaseModel):
    success: bool
    data: dict
    message: Optional[str] = None

@analytics_bp.route('/api/analytics/analyze', methods=['POST'])
def analyze():
    try:
        # Validate request
        request_data = AnalyticsRequest(**request.get_json())
        
        # Process request
        result = perform_analysis(request_data)
        
        # Validate response
        response_data = AnalyticsResponse(
            success=True,
            data=result
        )
        
        return jsonify(response_data.dict())
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
```

### Error Handling

Implement consistent error handling:

```python
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions"""
    if isinstance(e, HTTPException):
        return jsonify({
            'error': e.description,
            'code': e.code
        }), e.code
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    
    return jsonify({
        'error': 'Internal server error',
        'code': 500
    }), 500
```

## Frontend Development

### Module Structure

Each JavaScript module should follow this structure:

```javascript
// js/modules/example-module.js
(function() {
    'use strict';
    
    // Private variables
    let moduleState = {};
    
    // Private functions
    function privateFunction() {
        // Implementation
    }
    
    // Public API
    window.ExampleModule = {
        init: function() {
            // Initialize module
        },
        
        processData: function(data) {
            // Process data
            return privateFunction(data);
        },
        
        cleanup: function() {
            // Cleanup resources
        }
    };
})();
```

### Event Handling

Use a centralized event system:

```javascript
// js/modules/event-manager.js
window.EventManager = {
    events: {},
    
    on: function(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    },
    
    emit: function(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    },
    
    off: function(event, callback) {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        }
    }
};

// Usage
EventManager.on('dataLoaded', function(data) {
    console.log('Data loaded:', data);
});

EventManager.emit('dataLoaded', {ticker: 'AAPL', price: 150});
```

### API Communication

Use a centralized API client:

```javascript
// js/modules/api-client.js
window.APIClient = {
    baseURL: 'http://localhost:5000',
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    async get(endpoint) {
        return this.request(endpoint, {method: 'GET'});
    },
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};
```

## Database Design

### Model Definition

```python
# backend/models/example.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ExampleModel(db.Model):
    __tablename__ = 'examples'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='examples')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

### Database Migrations

Use Flask-Migrate for database migrations:

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Add example table"

# Apply migration
flask db upgrade
```

### Query Optimization

```python
# Use eager loading for relationships
runs = Run.query.options(db.joinedload(Run.user)).all()

# Use indexes for frequently queried columns
class Run(db.Model):
    __table_args__ = (
        db.Index('idx_run_ticker', 'ticker'),
        db.Index('idx_run_created_at', 'created_at'),
    )

# Use pagination for large datasets
runs = Run.query.paginate(
    page=page, 
    per_page=per_page, 
    error_out=False
)
```

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_example.py
import pytest
from unittest.mock import patch, MagicMock
from backend.models.example import ExampleModel

class TestExampleModel:
    def test_example_creation(self):
        """Test example model creation"""
        example = ExampleModel(name="Test", description="Test description")
        assert example.name == "Test"
        assert example.description == "Test description"
    
    def test_to_dict(self):
        """Test model serialization"""
        example = ExampleModel(name="Test")
        data = example.to_dict()
        assert 'id' in data
        assert data['name'] == "Test"
```

### Integration Tests

```python
# backend/tests/test_integration.py
import pytest
from backend.app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_api_endpoint(client):
    """Test API endpoint integration"""
    response = client.post('/api/example', json={'name': 'Test'})
    assert response.status_code == 200
    assert response.json['success'] is True
```

### Frontend Tests

```javascript
// tests/test-module.js
describe('ExampleModule', function() {
    beforeEach(function() {
        // Setup
    });
    
    afterEach(function() {
        // Cleanup
    });
    
    it('should process data correctly', function() {
        const result = ExampleModule.processData({test: 'data'});
        expect(result).toBeDefined();
    });
});
```

## Deployment

### Docker Configuration

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/valor_ivx
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=valor_ivx
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=.
```

## Monitoring and Observability

### Logging

```python
# backend/logging.py
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info("User action", user_id=123, action="login")
logger.error("API error", endpoint="/api/data", error=str(e))
```

### Metrics

```python
# backend/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# Usage in endpoints
@app.route('/api/data')
def get_data():
    start_time = time.time()
    
    try:
        # Process request
        result = process_data()
        
        # Record metrics
        http_requests_total.labels(
            method='GET',
            endpoint='/api/data',
            status=200
        ).inc()
        
        return jsonify(result)
        
    except Exception as e:
        http_requests_total.labels(
            method='GET',
            endpoint='/api/data',
            status=500
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method='GET',
            endpoint='/api/data'
        ).observe(duration)
```

## Security

### Authentication

```python
# backend/auth.py
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/protected')
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify({'user_id': current_user_id})
```

### Input Validation

```python
# backend/validation.py
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))

# Usage
schema = UserSchema()
try:
    user_data = schema.load(request.get_json())
except ValidationError as e:
    return jsonify({'error': e.messages}), 400
```

### Rate Limiting

```python
# backend/rate_limiter.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/data')
@limiter.limit("10 per minute")
def get_data():
    return jsonify({'data': 'example'})
```

## Performance Optimization

### Caching

```python
# backend/cache.py
import redis
from functools import wraps

redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL'))

def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=600)
def get_financial_data(ticker):
    # Expensive operation
    return fetch_from_api(ticker)
```

### Database Optimization

```python
# Use connection pooling
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20
}

# Use bulk operations
def bulk_create_users(users_data):
    users = [User(**data) for data in users_data]
    db.session.bulk_save_objects(users)
    db.session.commit()
```

### Frontend Optimization

```javascript
// Lazy loading
const loadModule = async (moduleName) => {
    const module = await import(`./modules/${moduleName}.js`);
    return module.default;
};

// Debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Usage
const debouncedSearch = debounce(searchFunction, 300);
```

## Contributing

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Run tests**
   ```bash
   pytest
   npm test
   ```

4. **Create pull request**
   - Include description of changes
   - Add tests for new functionality
   - Update documentation if needed

### Code Style

**Python (Black + Flake8):**
```python
# Use type hints
def process_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process data and return results."""
    return [{"processed": item} for item in data]

# Use docstrings
def calculate_dcf(inputs: Dict[str, float]) -> float:
    """
    Calculate DCF value.
    
    Args:
        inputs: Dictionary containing DCF inputs
        
    Returns:
        Calculated DCF value
    """
    # Implementation
    pass
```

**JavaScript (ESLint + Prettier):**
```javascript
// Use ES6+ features
const processData = (data) => {
    return data.map(item => ({
        processed: item
    }));
};

// Use JSDoc comments
/**
 * Calculate DCF value
 * @param {Object} inputs - DCF inputs
 * @returns {number} Calculated DCF value
 */
const calculateDCF = (inputs) => {
    // Implementation
};
```

### Testing Guidelines

- Write unit tests for all new functions
- Maintain >80% code coverage
- Include integration tests for API endpoints
- Test error conditions and edge cases

### Documentation

- Update API documentation for new endpoints
- Add code comments for complex logic
- Update README files for new features
- Include usage examples

### Review Process

1. **Self-review**: Check your own code before submitting
2. **Peer review**: At least one other developer must review
3. **Automated checks**: CI/CD pipeline must pass
4. **Manual testing**: Test in staging environment

## Support and Resources

### Documentation
- [API Documentation](docs/api/README.md)
- [Architecture Documentation](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)

### Tools and Services
- **Code Repository**: GitHub
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with ELK stack
- **Testing**: pytest, Jest

### Community
- **Slack**: #valor-ivx-dev
- **Email**: dev-team@valor-ivx.com
- **Wiki**: Internal development wiki

### Learning Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Prometheus Documentation](https://prometheus.io/docs/)