"""
Performance testing for Valor IVX
Phase 6 - Performance Testing Infrastructure
"""

from locust import HttpUser, task, between
import json
import random

class ValorIVXUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        # Register a test user
        self.register_user()
        # Login
        self.login_user()
    
    def register_user(self):
        """Register a test user"""
        username = f"testuser_{random.randint(1000, 9999)}"
        email = f"{username}@test.com"
        password = "TestPassword123!"
        
        payload = {
            "username": username,
            "email": email,
            "password": password
        }
        
        response = self.client.post("/api/auth/register", json=payload)
        if response.status_code == 201:
            self.username = username
            self.password = password
        else:
            # Use existing test user if registration fails
            self.username = "testuser_1000"
            self.password = "TestPassword123!"
    
    def login_user(self):
        """Login user and get auth token"""
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        response = self.client.post("/api/auth/login", json=payload)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            self.headers = {'Authorization': f'Bearer {self.auth_token}'}
        else:
            self.auth_token = None
            self.headers = {}
    
    @task(3)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/api/health")
    
    @task(2)
    def get_financial_data(self):
        """Test financial data endpoint"""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        ticker = random.choice(tickers)
        self.client.get(f"/api/financial-data/{ticker}")
    
    @task(2)
    def get_dcf_inputs(self):
        """Test DCF inputs endpoint"""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        ticker = random.choice(tickers)
        self.client.get(f"/api/financial-data/{ticker}/dcf-inputs")
    
    @task(1)
    def save_dcf_run(self):
        """Test saving DCF run"""
        if not self.auth_token:
            return
            
        run_data = {
            "run_id": f"test_run_{random.randint(1000, 9999)}",
            "ticker": random.choice(['AAPL', 'MSFT', 'GOOGL']),
            "inputs": {
                "revenue": 1000000000,
                "growthY1": 0.10,
                "growthY2": 0.08,
                "growthY3": 0.06,
                "growthY4": 0.04,
                "growthY5": 0.03,
                "ebitMargin": 0.25,
                "taxRate": 0.21,
                "wacc": 0.09,
                "terminalGrowth": 0.02,
                "shares": 1000,
                "netDebt": 50000
            },
            "results": {
                "enterpriseValue": 1500000000,
                "equityValue": 1450000000,
                "sharePrice": 1450
            }
        }
        
        self.client.post("/api/runs", 
                        json=run_data, 
                        headers=self.headers)
    
    @task(1)
    def get_last_run(self):
        """Test getting last run"""
        self.client.get("/api/runs/last")
    
    @task(1)
    def save_scenarios(self):
        """Test saving scenarios"""
        if not self.auth_token:
            return
            
        scenarios_data = {
            "scenarios": [
                {
                    "scenario_id": f"test_scenario_{random.randint(1000, 9999)}",
                    "name": "Base Case",
                    "ticker": "AAPL",
                    "inputs": {
                        "revenue": 1000000000,
                        "growthY1": 0.10,
                        "wacc": 0.09
                    }
                }
            ]
        }
        
        self.client.post("/api/scenarios", 
                        json=scenarios_data, 
                        headers=self.headers)
    
    @task(1)
    def get_scenarios(self):
        """Test getting scenarios"""
        self.client.get("/api/scenarios")
    
    @task(1)
    def save_lbo_run(self):
        """Test saving LBO run"""
        if not self.auth_token:
            return
            
        lbo_data = {
            "run_id": f"test_lbo_{random.randint(1000, 9999)}",
            "company_name": "Test Company",
            "inputs": {
                "purchasePrice": 1000000000,
                "equityContribution": 300000000,
                "seniorDebt": 500000000,
                "revenue": 800000000,
                "ebitdaMargin": 0.20
            },
            "results": {
                "irr": 0.25,
                "moic": 3.2,
                "exitValue": 1200000000
            }
        }
        
        self.client.post("/api/lbo/runs", 
                        json=lbo_data, 
                        headers=self.headers)
    
    @task(1)
    def get_last_lbo_run(self):
        """Test getting last LBO run"""
        self.client.get("/api/lbo/runs/last")
    
    @task(1)
    def save_notes(self):
        """Test saving notes"""
        if not self.auth_token:
            return
            
        ticker = random.choice(['AAPL', 'MSFT', 'GOOGL'])
        notes_data = {
            "content": f"Test notes for {ticker} - {random.randint(1000, 9999)}"
        }
        
        self.client.post(f"/api/notes/{ticker}", 
                        json=notes_data, 
                        headers=self.headers)
    
    @task(1)
    def get_notes(self):
        """Test getting notes"""
        ticker = random.choice(['AAPL', 'MSFT', 'GOOGL'])
        self.client.get(f"/api/notes/{ticker}")
    
    @task(1)
    def get_user_profile(self):
        """Test getting user profile"""
        if not self.auth_token:
            return
            
        self.client.get("/api/auth/profile", headers=self.headers)

class DCFAnalysisUser(HttpUser):
    """Specialized user for DCF analysis testing"""
    wait_time = between(2, 5)
    
    def on_start(self):
        """Initialize user session"""
        self.login_user()
    
    def login_user(self):
        """Login with test user"""
        payload = {
            "username": "testuser_1000",
            "password": "TestPassword123!"
        }
        
        response = self.client.post("/api/auth/login", json=payload)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            self.headers = {'Authorization': f'Bearer {self.auth_token}'}
        else:
            self.auth_token = None
            self.headers = {}
    
    @task(5)
    def complex_dcf_analysis(self):
        """Test complex DCF analysis workflow"""
        if not self.auth_token:
            return
        
        # Step 1: Get financial data
        ticker = random.choice(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])
        self.client.get(f"/api/financial-data/{ticker}")
        
        # Step 2: Get DCF inputs
        self.client.get(f"/api/financial-data/{ticker}/dcf-inputs")
        
        # Step 3: Save complex DCF run
        run_data = {
            "run_id": f"complex_dcf_{random.randint(1000, 9999)}",
            "ticker": ticker,
            "inputs": {
                "revenue": random.randint(500000000, 2000000000),
                "growthY1": random.uniform(0.05, 0.15),
                "growthY2": random.uniform(0.04, 0.12),
                "growthY3": random.uniform(0.03, 0.10),
                "growthY4": random.uniform(0.02, 0.08),
                "growthY5": random.uniform(0.01, 0.06),
                "ebitMargin": random.uniform(0.15, 0.35),
                "taxRate": random.uniform(0.15, 0.25),
                "wacc": random.uniform(0.07, 0.12),
                "terminalGrowth": random.uniform(0.01, 0.03),
                "shares": random.randint(500, 2000),
                "netDebt": random.randint(-100000, 100000)
            },
            "mc_settings": {
                "trials": 1000,
                "volPP": 0.15,
                "seedStr": "test_seed"
            },
            "results": {
                "enterpriseValue": random.randint(1000000000, 5000000000),
                "equityValue": random.randint(900000000, 4500000000),
                "sharePrice": random.randint(100, 500)
            }
        }
        
        self.client.post("/api/runs", 
                        json=run_data, 
                        headers=self.headers)
        
        # Step 4: Save multiple scenarios
        scenarios_data = {
            "scenarios": [
                {
                    "scenario_id": f"base_case_{random.randint(1000, 9999)}",
                    "name": "Base Case",
                    "ticker": ticker,
                    "inputs": run_data["inputs"]
                },
                {
                    "scenario_id": f"bull_case_{random.randint(1000, 9999)}",
                    "name": "Bull Case",
                    "ticker": ticker,
                    "inputs": {**run_data["inputs"], "growthY1": run_data["inputs"]["growthY1"] * 1.2}
                },
                {
                    "scenario_id": f"bear_case_{random.randint(1000, 9999)}",
                    "name": "Bear Case",
                    "ticker": ticker,
                    "inputs": {**run_data["inputs"], "growthY1": run_data["inputs"]["growthY1"] * 0.8}
                }
            ]
        }
        
        self.client.post("/api/scenarios", 
                        json=scenarios_data, 
                        headers=self.headers)

class LBOAnalysisUser(HttpUser):
    """Specialized user for LBO analysis testing"""
    wait_time = between(3, 7)
    
    def on_start(self):
        """Initialize user session"""
        self.login_user()
    
    def login_user(self):
        """Login with test user"""
        payload = {
            "username": "testuser_1000",
            "password": "TestPassword123!"
        }
        
        response = self.client.post("/api/auth/login", json=payload)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            self.headers = {'Authorization': f'Bearer {self.auth_token}'}
        else:
            self.auth_token = None
            self.headers = {}
    
    @task(3)
    def complex_lbo_analysis(self):
        """Test complex LBO analysis workflow"""
        if not self.auth_token:
            return
        
        # Step 1: Save complex LBO run
        lbo_data = {
            "run_id": f"complex_lbo_{random.randint(1000, 9999)}",
            "company_name": f"Test Company {random.randint(1, 100)}",
            "inputs": {
                "purchasePrice": random.randint(500000000, 2000000000),
                "equityContribution": random.randint(150000000, 600000000),
                "seniorDebt": random.randint(250000000, 1000000000),
                "mezzanineDebt": random.randint(50000000, 200000000),
                "highYieldDebt": random.randint(10000000, 50000000),
                "seniorRate": random.uniform(0.04, 0.08),
                "mezzanineRate": random.uniform(0.08, 0.12),
                "highYieldRate": random.uniform(0.10, 0.15),
                "revenue": random.randint(400000000, 1600000000),
                "ebitdaMargin": random.uniform(0.15, 0.25),
                "revenueGrowth": random.uniform(0.03, 0.08),
                "ebitdaGrowth": random.uniform(0.02, 0.06),
                "workingCapital": random.uniform(0.10, 0.20),
                "capex": random.uniform(0.05, 0.12),
                "taxRate": random.uniform(0.20, 0.30),
                "depreciation": random.uniform(0.03, 0.08),
                "exitYear": random.randint(3, 7),
                "exitMultiple": random.uniform(6.0, 14.0)
            },
            "results": {
                "irr": random.uniform(0.15, 0.35),
                "moic": random.uniform(2.0, 4.0),
                "exitValue": random.randint(600000000, 2400000000),
                "equityValue": random.randint(480000000, 1920000000)
            }
        }
        
        self.client.post("/api/lbo/runs", 
                        json=lbo_data, 
                        headers=self.headers)
        
        # Step 2: Save LBO scenarios
        scenarios_data = {
            "scenarios": [
                {
                    "scenario_id": f"lbo_base_{random.randint(1000, 9999)}",
                    "name": "Base Case LBO",
                    "company_name": lbo_data["company_name"],
                    "inputs": lbo_data["inputs"]
                },
                {
                    "scenario_id": f"lbo_optimistic_{random.randint(1000, 9999)}",
                    "name": "Optimistic LBO",
                    "company_name": lbo_data["company_name"],
                    "inputs": {**lbo_data["inputs"], "exitMultiple": lbo_data["inputs"]["exitMultiple"] * 1.2}
                }
            ]
        }
        
        self.client.post("/api/lbo/scenarios", 
                        json=scenarios_data, 
                        headers=self.headers)

class FinancialDataUser(HttpUser):
    """Specialized user for financial data testing"""
    wait_time = between(1, 3)
    
    @task(10)
    def financial_data_workflow(self):
        """Test financial data workflow"""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'CRM', 'ADBE']
        ticker = random.choice(tickers)
        
        # Get company overview
        self.client.get(f"/api/financial-data/{ticker}")
        
        # Get DCF inputs
        self.client.get(f"/api/financial-data/{ticker}/dcf-inputs")
        
        # Get historical prices
        self.client.get(f"/api/financial-data/{ticker}/historical-prices")
    
    @task(5)
    def multiple_tickers(self):
        """Test multiple tickers simultaneously"""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        for ticker in random.sample(tickers, 3):
            self.client.get(f"/api/financial-data/{ticker}")
            self.client.get(f"/api/financial-data/{ticker}/dcf-inputs")

class StressTestUser(HttpUser):
    """User for stress testing"""
    wait_time = between(0.1, 0.5)  # Very fast requests
    
    def on_start(self):
        """Initialize user session"""
        self.login_user()
    
    def login_user(self):
        """Login with test user"""
        payload = {
            "username": "testuser_1000",
            "password": "TestPassword123!"
        }
        
        response = self.client.post("/api/auth/login", json=payload)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            self.headers = {'Authorization': f'Bearer {self.auth_token}'}
        else:
            self.auth_token = None
            self.headers = {}
    
    @task(20)
    def rapid_requests(self):
        """Make rapid requests to test system limits"""
        endpoints = [
            "/api/health",
            "/api/runs/last",
            "/api/scenarios",
            "/api/lbo/runs/last",
            "/api/lbo/scenarios"
        ]
        
        endpoint = random.choice(endpoints)
        if self.auth_token and endpoint not in ["/api/health"]:
            self.client.get(endpoint, headers=self.headers)
        else:
            self.client.get(endpoint)
    
    @task(10)
    def rapid_financial_data(self):
        """Make rapid financial data requests"""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        ticker = random.choice(tickers)
        
        self.client.get(f"/api/financial-data/{ticker}")
    
    @task(5)
    def rapid_saves(self):
        """Make rapid save requests"""
        if not self.auth_token:
            return
        
        # Rapid DCF saves
        for i in range(3):
            run_data = {
                "run_id": f"stress_test_{random.randint(10000, 99999)}",
                "ticker": random.choice(['AAPL', 'MSFT', 'GOOGL']),
                "inputs": {
                    "revenue": random.randint(100000000, 1000000000),
                    "growthY1": random.uniform(0.05, 0.15),
                    "wacc": random.uniform(0.07, 0.12)
                }
            }
            
            self.client.post("/api/runs", 
                            json=run_data, 
                            headers=self.headers) 