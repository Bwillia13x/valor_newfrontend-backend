# Valor IVX API Documentation

## Overview

The Valor IVX API provides comprehensive financial modeling capabilities including DCF analysis, LBO modeling, M&A analysis, and real-time collaboration features. This API is designed for enterprise-grade financial applications with support for multi-tenancy, advanced analytics, and real-time data processing.

## Base URL

```
Production: https://api.valor-ivx.com
Staging: https://staging-api.valor-ivx.com
Development: http://localhost:5000
```

## Authentication

The Valor IVX API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```bash
curl -X POST https://api.valor-ivx.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
```

## Multi-Tenancy

All API requests should include the tenant ID in the header:

```
X-Tenant-ID: your-tenant-id
```

## Rate Limiting

- **Standard Plan**: 100 requests per minute
- **Professional Plan**: 500 requests per minute
- **Enterprise Plan**: 2000 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": "Additional error details"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## API Endpoints

### Health and Monitoring

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "message": "Database connection OK"},
    "redis": {"status": "healthy", "message": "Redis connection OK"},
    "external_apis": {"status": "healthy", "message": "External APIs accessible"}
  }
}
```

#### GET /health/ready
Kubernetes readiness probe endpoint.

#### GET /health/live
Kubernetes liveness probe endpoint.

#### GET /metrics
Prometheus metrics endpoint.

#### GET /slo/status
Service Level Objectives status.

**Response:**
```json
{
  "api_availability": {
    "compliance": 0.9995,
    "target": 0.999,
    "meeting_target": true,
    "measurements_count": 1000,
    "window_seconds": 3600
  },
  "api_latency_p95": {
    "compliance": 0.98,
    "target": 0.2,
    "meeting_target": true,
    "measurements_count": 1000,
    "window_seconds": 300
  }
}
```

#### GET /system/metrics
System resource metrics.

**Response:**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "cpu": {
    "percent": 45.2,
    "count": 8
  },
  "memory": {
    "percent": 67.8,
    "available_gb": 4.2
  },
  "disk": {
    "percent": 23.1,
    "free_gb": 156.7
  }
}
```

### Financial Data

#### GET /api/financial-data/{ticker}
Get comprehensive financial data for a ticker.

**Parameters:**
- `ticker` (string, required): Stock ticker symbol

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "market_cap": "2.5T",
      "pe_ratio": 25.4,
      "dividend_yield": 0.5
    },
    "income_statement": {
      "revenue": 394328000000,
      "gross_profit": 170782000000,
      "operating_income": 114301000000,
      "net_income": 96995000000
    },
    "balance_sheet": {
      "total_assets": 352755000000,
      "total_liabilities": 287912000000,
      "total_equity": 64843000000
    },
    "cash_flow": {
      "operating_cash_flow": 122151000000,
      "investing_cash_flow": -109559000000,
      "financing_cash_flow": -110543000000
    }
  }
}
```

#### GET /api/financial-data/{ticker}/dcf-inputs
Get DCF model inputs calculated from financial data.

**Parameters:**
- `ticker` (string, required): Stock ticker symbol

**Response:**
```json
{
  "success": true,
  "data": {
    "revenue_growth": 0.08,
    "operating_margin": 0.29,
    "tax_rate": 0.21,
    "wacc": 0.085,
    "terminal_growth": 0.025,
    "free_cash_flow": 85000000000
  }
}
```

#### GET /api/financial-data/{ticker}/historical-prices
Get historical price data for a ticker.

**Parameters:**
- `ticker` (string, required): Stock ticker symbol
- `interval` (string, optional): Time interval (daily, weekly, monthly)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-01",
      "open": 150.00,
      "high": 152.50,
      "low": 149.75,
      "close": 151.25,
      "volume": 50000000
    }
  ]
}
```

### DCF Analysis

#### POST /api/runs
Save a DCF analysis run.

**Request Body:**
```json
{
  "ticker": "AAPL",
  "inputs": {
    "revenue_growth": 0.08,
    "operating_margin": 0.29,
    "tax_rate": 0.21,
    "wacc": 0.085,
    "terminal_growth": 0.025
  },
  "mc_settings": {
    "iterations": 10000,
    "confidence_level": 0.95
  },
  "results": {
    "dcf_value": 175.50,
    "sensitivity_analysis": {...}
  }
}
```

**Response:**
```json
{
  "success": true,
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "DCF run saved successfully"
}
```

#### GET /api/runs/last
Get the most recent DCF run.

**Response:**
```json
{
  "success": true,
  "run": {
    "id": 1,
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "ticker": "AAPL",
    "inputs": {...},
    "results": {...},
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### GET /api/runs/{run_id}
Get a specific DCF run by ID.

#### GET /api/runs
List all DCF runs for the user.

**Query Parameters:**
- `limit` (integer, optional): Number of runs to return (default: 50)
- `offset` (integer, optional): Number of runs to skip (default: 0)
- `ticker` (string, optional): Filter by ticker

### Scenarios

#### POST /api/scenarios
Save or update DCF scenarios.

**Request Body:**
```json
{
  "scenarios": [
    {
      "scenario_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Base Case",
      "ticker": "AAPL",
      "inputs": {...},
      "mc_settings": {...}
    }
  ]
}
```

#### GET /api/scenarios
Get all scenarios for the user.

#### DELETE /api/scenarios/{scenario_id}
Delete a scenario.

### LBO Analysis

#### POST /api/lbo/runs
Save an LBO analysis run.

**Request Body:**
```json
{
  "company_name": "Target Corp",
  "inputs": {
    "purchase_price": 1000000000,
    "equity_contribution": 300000000,
    "debt_financing": 700000000,
    "exit_multiple": 8.0,
    "exit_year": 5
  },
  "results": {
    "irr": 0.25,
    "moic": 2.5,
    "payback_period": 3.2
  }
}
```

#### GET /api/lbo/runs/last
Get the most recent LBO run.

#### GET /api/lbo/runs/{run_id}
Get a specific LBO run by ID.

#### GET /api/lbo/runs
List all LBO runs for the user.

### M&A Analysis

#### POST /api/ma/runs
Save an M&A analysis run.

**Request Body:**
```json
{
  "deal_name": "Acquirer-Target Merger",
  "acquirer_name": "Acquirer Corp",
  "target_name": "Target Corp",
  "inputs": {
    "purchase_price": 1000000000,
    "equity_consideration": 600000000,
    "cash_consideration": 400000000,
    "synergies": 50000000
  },
  "results": {
    "accretion_dilution": 0.05,
    "irr": 0.15,
    "synergy_value": 250000000
  }
}
```

#### GET /api/ma/runs/last
Get the most recent M&A run.

#### GET /api/ma/runs/{run_id}
Get a specific M&A run by ID.

#### GET /api/ma/runs
List all M&A runs for the user.

### Notes

#### GET /api/notes/{ticker}
Get analyst notes for a ticker.

#### POST /api/notes/{ticker}
Save analyst notes for a ticker.

**Request Body:**
```json
{
  "content": "Analysis notes and insights..."
}
```

### WebSocket Collaboration

#### GET /api/websocket/status
Get WebSocket connection status.

#### GET /api/websocket/room/{room_id}/status
Get room collaboration status.

#### GET /api/websocket/user/{user_id}/status
Get user connection status.

## WebSocket Events

### Connection
```javascript
const socket = new WebSocket('wss://api.valor-ivx.com/ws');

socket.onopen = function(event) {
  console.log('Connected to Valor IVX WebSocket');
};
```

### Authentication
```javascript
socket.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### Join Room
```javascript
socket.send(JSON.stringify({
  type: 'join_room',
  room_id: 'room-123',
  user_id: 'user-456'
}));
```

### Collaboration Events
```javascript
// Send collaboration update
socket.send(JSON.stringify({
  type: 'collaboration_update',
  room_id: 'room-123',
  data: {
    cursor_position: {x: 100, y: 200},
    selection: {start: 0, end: 10}
  }
}));

// Receive collaboration updates
socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'collaboration_update') {
    // Handle collaboration update
  }
};
```

## SDKs and Libraries

### Python SDK
```bash
pip install valor-ivx-sdk
```

```python
from valor_ivx import ValorIVX

client = ValorIVX(
    api_key='your-api-key',
    tenant_id='your-tenant-id'
)

# Get financial data
data = client.get_financial_data('AAPL')

# Run DCF analysis
result = client.run_dcf_analysis('AAPL', inputs={...})
```

### JavaScript SDK
```bash
npm install @valor-ivx/sdk
```

```javascript
import { ValorIVX } from '@valor-ivx/sdk';

const client = new ValorIVX({
  apiKey: 'your-api-key',
  tenantId: 'your-tenant-id'
});

// Get financial data
const data = await client.getFinancialData('AAPL');

// Run DCF analysis
const result = await client.runDCFAnalysis('AAPL', inputs);
```

## Code Examples

### Complete DCF Analysis Workflow

```python
import requests

# 1. Get financial data
response = requests.get(
    'https://api.valor-ivx.com/api/financial-data/AAPL',
    headers={'Authorization': 'Bearer your-token'}
)
financial_data = response.json()['data']

# 2. Get DCF inputs
response = requests.get(
    'https://api.valor-ivx.com/api/financial-data/AAPL/dcf-inputs',
    headers={'Authorization': 'Bearer your-token'}
)
dcf_inputs = response.json()['data']

# 3. Run DCF analysis (client-side calculation)
dcf_value = calculate_dcf(dcf_inputs)

# 4. Save results
response = requests.post(
    'https://api.valor-ivx.com/api/runs',
    headers={'Authorization': 'Bearer your-token'},
    json={
        'ticker': 'AAPL',
        'inputs': dcf_inputs,
        'results': {'dcf_value': dcf_value}
    }
)
```

### Real-time Collaboration

```javascript
// Connect to WebSocket
const socket = new WebSocket('wss://api.valor-ivx.com/ws');

// Authenticate
socket.onopen = () => {
  socket.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
};

// Join collaboration room
socket.send(JSON.stringify({
  type: 'join_room',
  room_id: 'dcf-analysis-room',
  user_id: 'user-123'
}));

// Send cursor position updates
document.addEventListener('mousemove', (event) => {
  socket.send(JSON.stringify({
    type: 'collaboration_update',
    room_id: 'dcf-analysis-room',
    data: {
      cursor_position: {x: event.clientX, y: event.clientY}
    }
  }));
});

// Receive updates from other users
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'collaboration_update') {
    updateCollaborationUI(data);
  }
};
```

## Best Practices

### Error Handling
```python
try:
    response = requests.get('https://api.valor-ivx.com/api/financial-data/AAPL')
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
except ValueError as e:
    print(f"Invalid JSON response: {e}")
```

### Rate Limiting
```python
import time

def make_api_request(url, headers):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return make_api_request(url, headers)
    
    return response
```

### Caching
```python
import redis

redis_client = redis.Redis()

def get_cached_financial_data(ticker):
    cache_key = f"financial_data:{ticker}"
    
    # Check cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    response = requests.get(f'https://api.valor-ivx.com/api/financial-data/{ticker}')
    data = response.json()
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(data))
    
    return data
```

## Support

For API support and questions:
- **Documentation**: https://docs.valor-ivx.com
- **API Status**: https://status.valor-ivx.com
- **Support Email**: api-support@valor-ivx.com
- **Developer Community**: https://community.valor-ivx.com

## Changelog

### v1.0.0 (2024-01-01)
- Initial API release
- DCF analysis endpoints
- Financial data endpoints
- Basic authentication

### v1.1.0 (2024-02-01)
- LBO analysis endpoints
- M&A analysis endpoints
- WebSocket collaboration
- Multi-tenancy support

### v1.2.0 (2024-03-01)
- Advanced analytics endpoints
- Real-time monitoring
- Enhanced error handling
- Performance improvements