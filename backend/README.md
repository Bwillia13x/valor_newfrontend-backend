# Valor IVX Backend API

A comprehensive Flask-based backend API for the Valor IVX financial modeling application. This backend provides data persistence, user management, and API endpoints for saving and loading DCF analysis runs, scenarios, and analyst notes.

## 🚀 Features

### Core Functionality
- **Run Management**: Save and load DCF analysis runs with full input/output data
- **Scenario Management**: Store and retrieve multiple scenarios per ticker
- **Notes System**: Per-ticker analyst notes with auto-save functionality
- **User Management**: Basic user authentication and data isolation
- **Data Validation**: Comprehensive input validation and error handling

### Technical Features
- **RESTful API**: Clean, RESTful endpoints following best practices
- **Database Integration**: SQLAlchemy ORM with SQLite (dev) and PostgreSQL (prod)
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Error Handling**: Comprehensive error handling with meaningful responses
- **Testing**: Full test suite with pytest
- **Docker Support**: Containerized deployment with Docker and Docker Compose

## 🏗️ Architecture

```
backend/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── run.py                # Application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker container definition
├── docker-compose.yml   # Multi-service deployment
├── tests/               # Test suite
│   └── test_api.py      # API endpoint tests
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- (Optional) Docker and Docker Compose

### Local Development

1. **Clone and setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Initialize database**:
   ```bash
   python run.py
   ```

3. **Start the server**:
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:5000`

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**:
   ```bash
   docker build -t valor-ivx-backend .
   docker run -p 5000:5000 valor-ivx-backend
   ```

## 📚 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Authentication
Currently uses a demo user system. In production, implement proper JWT authentication.

### Endpoints

#### Health Check
```http
GET /api/health
```
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0"
}
```

#### Run Management

**Save Run**
```http
POST /api/runs
Content-Type: application/json

{
  "inputs": {
    "ticker": "AAPL",
    "revenue": 500,
    "growthY1": 12.0,
    "wacc": 9.0,
    // ... other DCF inputs
  },
  "mc_settings": {
    "trials": 1000,
    "volPP": 2.0,
    "seed": "analysis-1"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Get Last Run**
```http
GET /api/runs/last
```

**List All Runs**
```http
GET /api/runs
```

**Get Specific Run**
```http
GET /api/runs/{run_id}
```

#### Scenario Management

**Save Scenarios**
```http
POST /api/scenarios
Content-Type: application/json

[
  {
    "name": "Base Case",
    "ticker": "AAPL",
    "inputs": {
      "revenue": 500,
      "growthY1": 12.0,
      "wacc": 9.0
    },
    "mc_settings": {
      "trials": 1000,
      "volPP": 2.0
    }
  }
]
```

**Get All Scenarios**
```http
GET /api/scenarios
```

**Delete Scenario**
```http
DELETE /api/scenarios/{scenario_id}
```

#### Notes Management

**Save Notes**
```http
POST /api/notes/{ticker}
Content-Type: application/json

{
  "content": "Investment thesis and analysis notes..."
}
```

**Get Notes**
```http
GET /api/notes/{ticker}
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py
```

### Test Coverage
The test suite covers:
- All API endpoints
- Data validation
- Error handling
- Database operations
- Edge cases

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `DATABASE_URL` | Database connection string | `sqlite:///valor_ivx.db` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `JWT_SECRET_KEY` | JWT signing key | Auto-generated |
| `PORT` | Server port | `5000` |
| `HOST` | Server host | `0.0.0.0` |

### Database Configuration

**Development (SQLite)**:
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///valor_ivx.db'
```

**Production (PostgreSQL)**:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/valor_ivx'
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables**:
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@localhost/valor_ivx
   export SECRET_KEY=your-secure-secret-key
   export JWT_SECRET_KEY=your-jwt-secret-key
   ```

2. **Database Setup**:
   ```bash
   # Create PostgreSQL database
   createdb valor_ivx
   
   # Run migrations (if using Flask-Migrate)
   flask db upgrade
   ```

3. **Start with Gunicorn**:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
   ```

### Docker Production

1. **Build production image**:
   ```bash
   docker build -t valor-ivx-backend:prod .
   ```

2. **Run with environment variables**:
   ```bash
   docker run -d \
     -p 5000:5000 \
     -e FLASK_ENV=production \
     -e DATABASE_URL=postgresql://user:pass@host/valor_ivx \
     -e SECRET_KEY=your-secret-key \
     valor-ivx-backend:prod
   ```

## 🔒 Security Considerations

### Current Implementation
- Basic demo user system
- CORS configured for development
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy

### Production Recommendations
- Implement proper JWT authentication
- Add rate limiting
- Use HTTPS in production
- Implement proper password hashing
- Add request logging and monitoring
- Use environment variables for secrets
- Implement API versioning

## 📊 Monitoring and Logging

### Health Checks
The application includes a health check endpoint at `/api/health` that returns:
- Application status
- Timestamp
- Version information

### Logging
Configure logging in production:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Write tests for new endpoints
- Update API documentation
- Use type hints where appropriate

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the API documentation
- Review the test suite for examples
- Check the logs for debugging information

---

**Valor IVX Backend** - Professional-grade API for financial modeling applications. 