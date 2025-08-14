# Valor IVX - Advanced Financial Modeling Platform

## Overview

Valor IVX is a comprehensive financial modeling platform that provides advanced DCF (Discounted Cash Flow) and LBO (Leveraged Buyout) analysis capabilities. The platform features real-time financial data integration, sophisticated modeling engines, and a modern web-based interface.

## Core Features

### 1. DCF (Discounted Cash Flow) Analysis

**Advanced DCF Engine**
- Multi-stage growth modeling with configurable growth ramps
- Terminal value calculations using perpetuity or multiple methods
- Monte Carlo simulation capabilities
- Real-time sensitivity analysis
- Comprehensive input validation and error handling

**Key DCF Metrics**
- Enterprise Value and Equity Value calculations
- Free Cash Flow to Firm (FCFF) projections
- WACC (Weighted Average Cost of Capital) analysis
- Terminal value breakdown and analysis
- Payback period and ROIC calculations

**DCF Inputs**
- Revenue growth projections with decay modeling
- EBIT margin analysis
- Working capital and capital expenditure assumptions
- Tax rate and discount rate inputs
- Shares outstanding and net debt considerations

### 2. LBO (Leveraged Buyout) Analysis

**Comprehensive LBO Engine**
- Multi-tier debt structure modeling (Senior, Mezzanine, High Yield)
- Debt paydown and interest expense calculations
- IRR (Internal Rate of Return) analysis using Newton-Raphson method
- MOIC (Multiple on Invested Capital) calculations
- Exit scenario analysis with multiple valuation approaches

**LBO Key Features**
- Purchase price and equity contribution modeling
- EBITDA margin and revenue growth projections
- Working capital and capital expenditure assumptions
- Tax rate and depreciation modeling
- Debt structure with configurable interest rates

**Exit Scenarios**
- Exit multiple analysis (6x, 8x, 10x, 12x, 14x)
- Target IRR scenarios (15%, 20%, 25%, 30%)
- Implied multiple calculations for target returns
- Comprehensive exit value and equity value analysis

### 3. Financial Data API Integration

**Alpha Vantage Integration**
- Real-time company overview data
- Historical financial statements (Income Statement, Balance Sheet, Cash Flow)
- Historical price data with multiple intervals
- Automatic DCF input population from financial data
- Comprehensive financial metrics and ratios

**Financial Data Features**
- Company information and sector classification
- Market capitalization and valuation metrics
- Profitability and efficiency ratios
- Growth rates and financial health indicators
- Historical financial statement analysis

**Data Processing**
- Automatic parsing and validation of financial data
- Intelligent calculation of DCF model inputs
- Error handling and data quality checks
- Caching system for improved performance
- Comprehensive financial data display and analysis

### 4. Advanced UI/UX Features

**Modern Interface**
- Responsive design with dark theme
- Real-time calculations and updates
- Interactive charts and visualizations
- Tabbed interface for organized data presentation
- Comprehensive keyboard shortcuts

**Data Visualization**
- Cash flow projection charts
- Debt paydown visualization
- Sensitivity analysis graphs
- Monte Carlo simulation results
- Financial statement tables with formatting

**Export Capabilities**
- JSON export for data portability
- CSV export for spreadsheet analysis
- Shareable links with embedded parameters
- Backend integration for data persistence
- Comprehensive scenario management

### 5. Backend Integration

**RESTful API**
- Comprehensive CRUD operations for runs and scenarios
- User management and data persistence
- Financial data API proxy for security
- Real-time data validation and processing
- Scalable database architecture

**Data Management**
- SQLite database with SQLAlchemy ORM
- User-specific data isolation
- Automatic data validation and sanitization
- Backup and restore capabilities
- Comprehensive error handling and logging

**API Endpoints**
- `/api/financial-data/<ticker>` - Financial data retrieval
- `/api/financial-data/<ticker>/dcf-inputs` - DCF input calculation
- `/api/runs` - DCF run management
- `/api/lbo/runs` - LBO run management
- `/api/scenarios` - Scenario management
- `/api/notes/<ticker>` - Analyst notes

### 6. Scenario Management

**Comprehensive Scenario System**
- Save and load multiple analysis scenarios
- Scenario comparison and analysis
- Import/export functionality
- Backend persistence and synchronization
- Scenario naming and organization

**Scenario Features**
- DCF scenario management
- LBO scenario management
- Monte Carlo scenario analysis
- Sensitivity analysis scenarios
- Cross-scenario comparison tools

### 7. Monte Carlo Simulation

**Advanced Simulation Engine**
- Configurable input distributions
- Real-time simulation execution
- Comprehensive result analysis
- Confidence interval calculations
- Sensitivity analysis integration

**Simulation Features**
- Normal and uniform distributions
- Correlation matrix support
- Custom distribution definitions
- Real-time result visualization
- Export capabilities for further analysis

## Technical Architecture

### Frontend
- **Framework**: Vanilla JavaScript with ES6 modules
- **Styling**: Custom CSS with modern design principles
- **Charts**: Canvas-based custom charting library
- **State Management**: Modular JavaScript architecture
- **Build System**: No build step required (pure HTML/CSS/JS)

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **API**: RESTful design with JSON responses
- **Authentication**: JWT-based authentication system
- **External APIs**: Alpha Vantage financial data integration

### Dependencies
- **Python**: Flask, SQLAlchemy, requests, python-dotenv
- **Frontend**: No external dependencies (vanilla JS)
- **Development**: pytest, black, flake8 for code quality

## Installation and Setup

### Prerequisites
- Python 3.8+
- Modern web browser
- Alpha Vantage API key (optional, for financial data)

### Quick Start
1. Clone the repository
2. Install Python dependencies: `pip install -r backend/requirements.txt`
3. Set environment variables (optional):
   - `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
   - `SECRET_KEY`: Flask secret key
   - `JWT_SECRET_KEY`: JWT secret key
4. Start the backend: `cd backend && python app.py`
5. Start the frontend: `python3 -m http.server 8000`
6. Open `http://localhost:8000` in your browser

### Configuration
- Backend runs on port 5000 by default
- Frontend runs on port 8000 by default
- Database is automatically created on first run
- CORS is configured for local development

## Usage Guide

### DCF Analysis
1. Enter company ticker and basic financial data
2. Configure growth assumptions and margins
3. Set discount rate and terminal growth
4. Run analysis to see results
5. Use Monte Carlo for sensitivity analysis
6. Save scenarios for comparison

### LBO Analysis
1. Enter target company and purchase price
2. Configure equity contribution and debt structure
3. Set operational assumptions and growth rates
4. Run analysis to see IRR and MOIC
5. Analyze exit scenarios
6. Compare different debt structures

### Financial Data Integration
1. Enter a valid stock ticker
2. Click "Fetch Data" to retrieve financial information
3. Review company overview and financial metrics
4. Click "Load DCF Inputs" to populate model
5. Adjust assumptions as needed
6. Run analysis with real financial data

## API Documentation

### Financial Data Endpoints

#### GET `/api/financial-data/<ticker>`
Retrieve comprehensive financial data for a ticker.

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "revenue": 394328000000,
    "ebit": 119437000000,
    "market_cap": 3000000000000,
    "income_statements": [...],
    "balance_sheets": [...],
    "cash_flows": [...]
  }
}
```

#### GET `/api/financial-data/<ticker>/dcf-inputs`
Calculate DCF model inputs from financial data.

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "AAPL",
    "revenue": 394328,
    "growthY1": 0.08,
    "ebitMargin": 0.30,
    "wacc": 0.09,
    "shares": 15700,
    "netDebt": -50000
  }
}
```

### Run Management Endpoints

#### POST `/api/runs`
Save a DCF analysis run.

#### GET `/api/runs/last`
Retrieve the most recent DCF run.

#### POST `/api/lbo/runs`
Save an LBO analysis run.

#### GET `/api/lbo/runs/last`
Retrieve the most recent LBO run.

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure code quality with black and flake8
6. Submit a pull request

### Code Style
- Python: Follow PEP 8 with black formatting
- JavaScript: Use ES6+ features and modular architecture
- CSS: Follow BEM methodology for class naming
- Documentation: Comprehensive docstrings and comments

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:
- Create an issue on GitHub
- Check the documentation
- Review the code examples

## Roadmap

### Planned Features
- M&A (Merger & Acquisition) analysis module
- Real-time market data integration
- Advanced charting and visualization
- Collaborative analysis features
- Mobile-responsive design improvements
- Additional financial data providers
- Advanced scenario comparison tools
- Automated report generation 