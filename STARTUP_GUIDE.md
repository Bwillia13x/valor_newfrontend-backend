# Valor IVX - Startup Guide

[Canonical Notice]
These steps reflect the canonical DevX for local development. If anything conflicts elsewhere, defer to README.md → “How to run, test, and deploy” and docs/production-setup.md.

## 🚀 Quick Start

### Option 1: Full-Stack Startup (Recommended)
```bash
./start_fullstack.sh
```
This starts both backend and frontend services automatically.

### Option 2: Individual Services
```bash
# Start backend only
./start_backend.sh

# Start frontend only (in a new terminal)
python3 -m http.server 8000
```

## 📊 Service URLs

- **Frontend**: http://localhost:8000
- **Backend API**: http://localhost:5002
- **Backend Health**: http://localhost:5002/api/health

## 🔐 Auth, Tenancy, and Health

- Demo user: bcrypt-hashed non-sensitive password “demo_password” (for test flows)
- JWT guard: minimal guard across sensitive endpoints
- Tenant enforcement: required on runs, scenarios, financial-data, LBO, M&A, notes
- Public/system endpoints: `/`, `/api/health`, websocket status, and `/metrics` (when enabled)
- Health endpoint: unthrottled

## 🧪 Testing

### Test Backend Only
```bash
python3 test_backend.py
```

### Test Full-Stack Integration
```bash
python3 test_fullstack.py
```

### Sample Requests

Health (no tenant required):
```bash
curl -s http://localhost:5002/api/health
```

Protected route with tenant:
```bash
curl -s -H "X-Tenant-ID: demo" http://localhost:5002/api/runs
```

Metrics (when enabled):
```bash
curl -s http://localhost:5002/metrics
```

## 🔧 Troubleshooting

### Port Conflicts
If you get port conflicts, clean up existing processes:
```bash
# Kill all related processes
pkill -f "python.*run.py"
pkill -f "python.*http.server"
lsof -ti:5002 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
```

### Backend Issues
1. Check if backend is running: `curl http://localhost:5002/api/health`
2. Check backend logs: `cat backend/backend.log`
3. Restart backend: `./start_backend.sh`
4. If metrics not found, ensure feature flag is enabled in settings (FEATURE_PROMETHEUS_METRICS)

### Frontend Issues
1. Check if frontend is running: `curl http://localhost:8000`
2. Check frontend logs: `cat frontend.log`
3. Restart frontend: `python3 -m http.server 8000`

### Database Issues
If you encounter database errors:
```bash
cd backend
source venv/bin/activate
python -c "from app import init_db; init_db()"
```

## 📁 File Structure

```
valor_newfrontend-backend/
├── backend/                 # Flask backend
│   ├── app.py              # Main Flask application
│   ├── run.py              # Backend startup script
│   ├── config.py           # Configuration settings
│   ├── venv/               # Python virtual environment
│   └── backend.log         # Backend logs
├── js/                     # Frontend JavaScript modules
│   ├── main.js             # Main application logic
│   └── modules/            # Modular components
├── index.html              # Main frontend page
├── start_backend.sh        # Backend startup script
├── start_fullstack.sh      # Full-stack startup script
├── test_backend.py         # Backend test suite
├── test_fullstack.py       # Full-stack test suite
└── frontend.log            # Frontend logs
```

## 🎯 Features

### Backend API Endpoints
- `GET /api/health` - Health check
- `POST /api/runs` - Save DCF run data
- `GET /api/runs/last` - Get last run
- `POST /api/scenarios` - Save scenarios
- `GET /api/scenarios` - Get all scenarios
- `POST /api/notes/{ticker}` - Save notes
- `GET /api/notes/{ticker}` - Get notes

### Frontend Features
- DCF valuation calculator
- Monte Carlo simulation
- Scenario comparison
- Data persistence
- Real-time backend status

## 🔒 Security Notes

- Backend runs on port 5002 (development)
- Frontend runs on port 8000 (development)
- CORS is enabled for local development
- Database is SQLite (development)

## 📝 Development

### Adding New Features
1. Backend: Add routes in `backend/app.py`
2. Frontend: Add modules in `js/modules/`
3. Test: Update test scripts
4. Document: Update this guide

### Environment Variables
- `FLASK_ENV`: Set to 'development' or 'production'
- `PORT`: Backend port (default: 5002)
- `HOST`: Backend host (default: 0.0.0.0)

## 🆘 Support

If you encounter issues:
1. Check the logs in `backend/backend.log` and `frontend.log`
2. Run the test suites to identify problems
3. Ensure all dependencies are installed
4. Verify ports are not in use by other applications
