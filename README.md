# Valor IVX — Advanced DCF Modeling Tool

A comprehensive, full-stack financial modeling application featuring DCF analysis, Monte Carlo simulations, sensitivity analysis, and scenario management. Built with modern JavaScript modules and a Flask backend for data persistence.

## 🚀 Features

### Core Financial Modeling
- **Multi-Stage DCF Engine**: Support for 3-stage growth models with customizable ramps
- **Terminal Value Methods**: Both Gordon Growth (perpetuity) and Exit Multiple approaches
- **Advanced Assumptions**: Multi-stage growth, margin, and capital efficiency ramps
- **Real-time Validation**: Input validation with visual feedback

### Monte Carlo Analysis
- **Correlated Shocks**: Growth and margin correlation modeling
- **Advanced Parameters**: Growth volatility, margin volatility, Sales-to-Capital volatility
- **Progress Tracking**: Real-time progress with ETA and cancellation support
- **Statistical Output**: Mean, median, percentiles with histogram visualization

### Visualization & Analysis
- **Interactive Charts**: FCFF, Revenue, Margins, PV contributions, Waterfall charts
- **Sensitivity Analysis**: 2D heatmaps and 1D sensitivity plots
- **Real-time Updates**: Live chart updates as parameters change
- **Export Capabilities**: PNG chart exports and CSV data exports

### Scenario Management
- **Save/Load Scenarios**: Persistent scenario storage with deduplication
- **Import/Export**: JSON-based scenario sharing
- **MC Settings Snapshot**: Scenarios include Monte Carlo parameter snapshots
- **Deep Linking**: Shareable URLs with all parameters encoded

### Backend Integration
- **Data Persistence**: Save and load analysis runs to/from database
- **User Management**: Basic authentication and data isolation
- **RESTful API**: Clean API endpoints for all functionality
- **Real-time Sync**: Automatic synchronization with backend

### Professional Features
- **CLI Interface**: In-browser command-line interface for power users
- **Notes System**: Per-ticker analyst notes with auto-save
- **Backend Integration**: Full server-side data persistence
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

## 🏗️ Architecture

### Frontend (Modular JavaScript)
```
js/
├── main.js                 # Application entry point
└── modules/
    ├── utils.js           # Common utilities and helpers
    ├── backend.js         # Backend communication
    ├── dcf-engine.js      # Core DCF calculation engine
    ├── monte-carlo.js     # Monte Carlo simulation engine
    ├── charting.js        # Chart rendering and visualization
    ├── scenarios.js       # Scenario management and persistence
    └── ui-handlers.js     # UI interactions and event management
```

### Backend (Flask API)
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
└── README.md            # Backend documentation
```

## ℹ️ Canonical Notice

This README contains the canonical instructions for running, testing, and deploying. If any other document conflicts, defer to the “How to run, test, and deploy” section here and docs/production-setup.md.

## 🔌 Port Conventions

- Backend API: http://localhost:5002
- Frontend: http://localhost:8000

Public/system endpoints (no tenant header required): `/`, `/api/health`, websocket status, and `/metrics` (when enabled).
Core data routes (runs, scenarios, financial-data, LBO, M&A, notes) enforce tenancy via tenant headers.

## 🚀 Quick Start

### Option 1: Full Stack (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd valor_newfrontend-backend
   ```

2. **Start both services**:
   ```bash
   ./start.sh
   ```

3. **Access the application**:
   - Frontend: http://localhost:8000
- Backend API: http://localhost:5002
- Health Check: http://localhost:5002/api/health

### Option 2: Frontend Only

1. **Start frontend server**:
   ```bash
   python3 -m http.server 8000
   ```

2. **Open in browser**:
   ```
   http://localhost:8000
   ```

### Option 3: Docker Deployment

1. **Start with Docker Compose**:
   ```bash
   cd backend
   docker-compose up --build
   ```

2. **Access the application**:
   - Frontend: http://localhost:8000
   - Backend: http://localhost:5002

## 📊 Usage Guide

### Basic DCF Analysis
1. **Input Assumptions**: Fill in revenue, growth, margins, WACC, etc.
2. **Multi-Stage Ramps**: Configure 3-stage growth and margin assumptions
3. **Run Analysis**: Click "Run" or press Enter
4. **Review Results**: Check Enterprise Value, Per Share value, and charts

### Monte Carlo Simulation
1. **Set Parameters**: Configure trials, volatility, correlation
2. **Run MC**: Click "Run Monte Carlo" or use Ctrl+Enter
3. **Monitor Progress**: Watch real-time progress with ETA
4. **Analyze Results**: Review histogram and statistics

### Scenario Management
1. **Save Scenario**: Click "Save Scenario" to store current state
2. **Apply Scenario**: Select from dropdown and click "Apply"
3. **Export/Import**: Use JSON export/import for sharing
4. **Deep Linking**: Copy URL to share specific parameter sets

### Backend Integration
1. **Save Run**: Click "Send to Backend: Save Run JSON" to persist analysis
2. **Load Run**: Click "Load Last Run" to restore previous analysis
3. **Sync Scenarios**: Use "Send to Backend: Save Scenarios" and "Fetch Scenarios"
4. **Auto-save Notes**: Notes are automatically saved per ticker

### CLI Interface
Access the command-line interface in the bottom panel:
```bash
run                    # Run DCF analysis
set wacc 8.5          # Set WACC to 8.5%
eval ps               # Show per-share value
mc 1000 2.0           # Run 1000 MC trials with 2% vol
clear                 # Clear CLI output
help                  # Show all commands
```

## 🔧 Configuration

### Frontend Configuration
The frontend is configured through the modular JavaScript architecture. Key configuration points:

- **Backend URL**: Configured in `js/modules/backend.js`
- **Chart Settings**: Customizable in `js/modules/charting.js`
- **Monte Carlo Parameters**: Set in `js/modules/monte-carlo.js`

### Backend Configuration
Environment variables for backend configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `DATABASE_URL` | Database connection string | `sqlite:///valor_ivx.db` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `JWT_SECRET_KEY` | JWT signing key | Auto-generated |
| `PORT` | Server port | `5000` |

### Monte Carlo Parameters
- **Growth vol (pp)**: Absolute percentage-point volatility for revenue growth
- **Margin vol (pp)**: Absolute percentage-point volatility for EBIT margins
- **S2C vol (%)**: Relative volatility on Sales-to-Capital ratio
- **Corr(G↔M)**: Correlation between growth and margin shocks (-0.99 to 0.99)
- **Trials**: Number of Monte Carlo draws (100-10,000)
- **Seed**: Optional deterministic seed for reproducibility

## 📁 File Structure

```
valor_newfrontend-backend/
├── index.html              # Main HTML file
├── styles.css              # Application styles
├── js/                     # Frontend JavaScript modules
│   ├── main.js            # Application entry point
│   └── modules/           # Modular JavaScript components
│       ├── utils.js
│       ├── backend.js
│       ├── dcf-engine.js
│       ├── monte-carlo.js
│       ├── charting.js
│       ├── scenarios.js
│       └── ui-handlers.js
├── backend/                # Backend Flask application
│   ├── app.py             # Main Flask application
│   ├── config.py          # Configuration management
│   ├── run.py             # Application entry point
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Docker container definition
│   ├── docker-compose.yml # Multi-service deployment
│   ├── tests/             # Test suite
│   └── README.md          # Backend documentation
├── package.json           # Project metadata
├── start.sh              # Full-stack startup script
├── REFACTORING_SUMMARY.md # Refactoring documentation
└── README.md             # This file
```

## 🧪 Testing

### Frontend Testing
Run the built-in test suite:
1. Start the development server
2. Open `http://localhost:8000?tests`
3. Check browser console for test results

### Backend Testing
```bash
cd backend
pip install pytest pytest-flask
pytest tests/
```

The test suite validates:
- DCF calculation accuracy
- Monte Carlo simulation correctness
- Input validation
- Chart rendering
- API endpoint functionality
- Database operations

## 🔌 API Endpoints

### Base URL
```
http://localhost:5002/api
```

### Run Management
- `POST /api/runs` - Save DCF analysis run
- `GET /api/runs/last` - Load last run
- `GET /api/runs` - List all runs
- `GET /api/runs/{run_id}` - Get specific run

### Scenario Management
- `POST /api/scenarios` - Save scenarios
- `GET /api/scenarios` - Load scenarios
- `DELETE /api/scenarios/{scenario_id}` - Delete scenario

### Notes Management
- `POST /api/notes/{ticker}` - Save notes for ticker
- `GET /api/notes/{ticker}` - Load notes for ticker

### Health Check
- `GET /api/health` - Application health status

## 🚀 Deployment

### Development
```bash
./start.sh
```

### Production
1. **Backend**: Use Docker or deploy Flask app with Gunicorn
2. **Frontend**: Serve static files with Nginx or similar
3. **Database**: Use PostgreSQL for production data

### Docker Deployment
```bash
cd backend
docker-compose up --build
```

## 🔒 Security

### Current Implementation
- Basic demo user system
- CORS configured for development
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy

### Production Recommendations
- JWT authentication with refresh rotation and token revocation (see roadmap P6)
- Rate limiting across sensitive endpoints; health endpoint unthrottled
- Use HTTPS in production with TLS termination (see docs/production-setup.md)
- Password hashing with bcrypt; secrets via environment-only (no secrets in repo)
- Structured JSON logging with request_id and tenant_id; monitoring and metrics (/metrics exposed when enabled)
- Use environment variables for secrets and CI/CD-managed configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (both frontend and backend)
5. Submit a pull request

### Development Guidelines
- Follow the modular architecture
- Add appropriate error handling
- Include input validation
- Maintain accessibility features
- Add tests for new functionality
- Update documentation

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with modern web standards
- No external frontend dependencies
- Designed for professional financial analysis
- Accessibility-first approach
- Comprehensive testing and documentation

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review the test suite for examples
- Check the logs for debugging information

---

**Valor IVX** - Professional-grade financial modeling with full-stack capabilities.
