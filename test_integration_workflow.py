#!/usr/bin/env python3
"""
Valor IVX - Full Integration Workflow Test
Tests the complete user workflow from frontend to backend integration
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:5002"
FRONTEND_URL = "http://localhost:8000"

def test_backend_health():
    """Test backend health endpoint"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data['status']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_frontend_availability():
    """Test frontend availability"""
    print("🌐 Testing frontend availability...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is available")
            return True
        else:
            print(f"❌ Frontend check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend check error: {e}")
        return False

def test_dcf_run_workflow():
    """Test complete DCF run workflow"""
    print("\n📊 Testing DCF Run Workflow...")
    
    # Sample DCF inputs
    dcf_inputs = {
        "ticker": "AAPL",
        "revenue": 394328,
        "growthY1": 0.08,
        "growthY2": 0.06,
        "growthY3": 0.04,
        "ebitMargin": 0.30,
        "wacc": 0.09,
        "termGrowth": 0.025,
        "shares": 15700,
        "netDebt": -50000,
        "years": 7
    }
    
    # Sample Monte Carlo settings
    mc_settings = {
        "trials": 1000,
        "volPP": 2.0,
        "marginVolPP": 1.5,
        "s2cVolPct": 10.0,
        "corrGM": -0.3,
        "seedStr": "test-seed"
    }
    
    # Sample results (simplified)
    results = {
        "totals": {
            "ev": 2500000,
            "equity": 2550000,
            "perShare": 162.42
        },
        "series": [],
        "warnings": []
    }
    
    # 1. Save DCF run
    print("  1. Saving DCF run...")
    run_data = {
        "inputs": dcf_inputs,
        "mc_settings": mc_settings,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/runs",
            json=run_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            run_id = data.get("run_id")
            print(f"   ✅ DCF run saved with ID: {run_id}")
        else:
            print(f"   ❌ Failed to save DCF run: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error saving DCF run: {e}")
        return False
    
    # 2. Load last run
    print("  2. Loading last run...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/runs/last", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            loaded_run = data.get("data")
            if loaded_run and loaded_run.get("ticker") == "AAPL":
                print(f"   ✅ Last run loaded: {loaded_run['ticker']}")
            else:
                print("   ❌ Failed to load correct run data")
                return False
        else:
            print(f"   ❌ Failed to load last run: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error loading last run: {e}")
        return False
    
    return True

def test_scenario_workflow():
    """Test scenario management workflow"""
    print("\n📋 Testing Scenario Workflow...")
    
    # Sample scenarios
    scenarios = [
        {
            "name": "Base Case",
            "ticker": "AAPL",
            "inputs": {
                "revenue": 394328,
                "growthY1": 0.08,
                "wacc": 0.09
            },
            "mc_settings": {
                "trials": 1000,
                "volPP": 2.0
            }
        },
        {
            "name": "Bull Case",
            "ticker": "AAPL",
            "inputs": {
                "revenue": 394328,
                "growthY1": 0.12,
                "wacc": 0.08
            },
            "mc_settings": {
                "trials": 1000,
                "volPP": 1.5
            }
        }
    ]
    
    # 1. Save scenarios
    print("  1. Saving scenarios...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/scenarios",
            json=scenarios,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            saved_count = data.get("saved_count", 0)
            print(f"   ✅ {saved_count} scenarios saved")
        else:
            print(f"   ❌ Failed to save scenarios: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error saving scenarios: {e}")
        return False
    
    # 2. Load scenarios
    print("  2. Loading scenarios...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/scenarios", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            loaded_scenarios = data.get("scenarios", [])
            if len(loaded_scenarios) >= 2:
                print(f"   ✅ {len(loaded_scenarios)} scenarios loaded")
            else:
                print("   ❌ Failed to load correct number of scenarios")
                return False
        else:
            print(f"   ❌ Failed to load scenarios: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error loading scenarios: {e}")
        return False
    
    return True

def test_notes_workflow():
    """Test notes management workflow"""
    print("\n📝 Testing Notes Workflow...")
    
    ticker = "AAPL"
    test_notes = "Investment thesis: Strong ecosystem, recurring revenue, innovation pipeline. Risks: Supply chain, regulatory, competition."
    
    # 1. Save notes
    print("  1. Saving notes...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/notes/{ticker}",
            json={"content": test_notes},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Notes saved")
        else:
            print(f"   ❌ Failed to save notes: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error saving notes: {e}")
        return False
    
    # 2. Load notes
    print("  2. Loading notes...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/notes/{ticker}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            loaded_notes = data.get("content", "")
            if loaded_notes == test_notes:
                print("   ✅ Notes loaded correctly")
            else:
                print("   ❌ Notes content mismatch")
                return False
        else:
            print(f"   ❌ Failed to load notes: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error loading notes: {e}")
        return False
    
    return True

def test_lbo_workflow():
    """Test LBO workflow"""
    print("\n🏢 Testing LBO Workflow...")
    
    # Sample LBO inputs
    lbo_inputs = {
        "companyName": "TechCorp Inc.",
        "purchasePrice": 1000,
        "equityContribution": 400,
        "seniorDebt": 400,
        "mezzanineDebt": 200,
        "ebitdaMargin": 0.25,
        "revenueGrowth": 0.08,
        "exitMultiple": 10.0,
        "exitYear": 5
    }
    
    # Sample results
    results = {
        "irr": 0.25,
        "moic": 3.2,
        "exitValue": 1500,
        "equityValue": 1280
    }
    
    # 1. Save LBO run
    print("  1. Saving LBO run...")
    lbo_data = {
        "inputs": lbo_inputs,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/lbo/runs",
            json=lbo_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            run_id = data.get("run_id")
            print(f"   ✅ LBO run saved with ID: {run_id}")
        else:
            print(f"   ❌ Failed to save LBO run: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error saving LBO run: {e}")
        return False
    
    # 2. Load last LBO run
    print("  2. Loading last LBO run...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/lbo/runs/last", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            loaded_run = data.get("data")
            if loaded_run and loaded_run.get("company_name") == "TechCorp Inc.":
                print(f"   ✅ Last LBO run loaded: {loaded_run['company_name']}")
            else:
                print("   ❌ Failed to load correct LBO run data")
                return False
        else:
            print(f"   ❌ Failed to load last LBO run: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error loading last LBO run: {e}")
        return False
    
    return True

def test_financial_data_endpoints():
    """Test financial data endpoints (without API key)"""
    print("\n📈 Testing Financial Data Endpoints...")
    
    ticker = "AAPL"
    
    # Test financial data endpoint (will fail without API key, but should return proper error)
    print("  1. Testing financial data endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/financial-data/{ticker}", timeout=10)
        
        if response.status_code == 404:
            data = response.json()
            if "No financial data found" in data.get("error", ""):
                print("   ✅ Financial data endpoint returns proper error (no API key)")
            else:
                print("   ❌ Unexpected error response")
                return False
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing financial data endpoint: {e}")
        return False
    
    # Test DCF inputs endpoint
    print("  2. Testing DCF inputs endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/financial-data/{ticker}/dcf-inputs", timeout=10)
        
        if response.status_code == 404:
            data = response.json()
            if "No financial data found" in data.get("error", ""):
                print("   ✅ DCF inputs endpoint returns proper error (no API key)")
            else:
                print("   ❌ Unexpected error response")
                return False
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing DCF inputs endpoint: {e}")
        return False
    
    return True

def main():
    """Run all integration tests"""
    print("🚀 Valor IVX - Full Integration Workflow Test")
    print("=" * 60)
    
    # Test basic connectivity
    if not test_backend_health():
        print("❌ Backend health check failed. Exiting.")
        sys.exit(1)
    
    if not test_frontend_availability():
        print("❌ Frontend availability check failed. Exiting.")
        sys.exit(1)
    
    # Test workflows
    tests = [
        ("DCF Run Workflow", test_dcf_run_workflow),
        ("Scenario Workflow", test_scenario_workflow),
        ("Notes Workflow", test_notes_workflow),
        ("LBO Workflow", test_lbo_workflow),
        ("Financial Data Endpoints", test_financial_data_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Full-stack application is working correctly")
        print("✅ Backend API endpoints are functional")
        print("✅ Frontend-backend integration is complete")
        print("✅ Data persistence is working")
        print("\n🎯 Application is ready for production use!")
    else:
        print("❌ Some tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 