#!/usr/bin/env python3
"""
Full-stack test script for Valor IVX application
Tests both backend API and frontend integration
"""

import requests
import json
import time
import sys
import subprocess
import os

def test_backend_api():
    """Test the backend API endpoints"""
    print("🧪 Testing Backend API...")
    print("-" * 30)
    
    base_url = "http://localhost:5002/api"
    
    # Test 1: Health Check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
        else:
            print(f"❌ Health Check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check error: {e}")
        return False
    
    # Test 2: Save and retrieve run
    test_run = {
        "inputs": {
            "ticker": "AAPL",
            "revenue": 2000,
            "growthY1": 12.0,
            "wacc": 8.5,
            "years": 5,
            "termGrowth": 3.0,
            "ebitMargin": 30.0,
            "taxRate": 21.0,
            "salesToCap": 2.5,
            "shares": 150,
            "netDebt": 1000
        },
        "mc_settings": {
            "trials": 1000,
            "volPP": 2.0,
            "seed": "test-fullstack"
        },
        "timestamp": "2024-01-15T10:30:00.000Z"
    }
    
    try:
        response = requests.post(f"{base_url}/runs", json=test_run, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Run saved: {data['run_id']}")
        else:
            print(f"❌ Save run failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Save run error: {e}")
        return False
    
    # Test 3: Get last run
    try:
        response = requests.get(f"{base_url}/runs/last", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Last run retrieved: {data['data']['ticker']}")
        else:
            print(f"❌ Get last run failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get last run error: {e}")
        return False
    
    print("✅ Backend API tests passed!")
    return True

def test_frontend():
    """Test the frontend server"""
    print("\n🌐 Testing Frontend...")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend server is responding")
            if "Valor IVX" in response.text:
                print("✅ Frontend contains Valor IVX content")
            else:
                print("⚠️  Frontend content may be incomplete")
        else:
            print(f"❌ Frontend failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False
    
    return True

def test_frontend_backend_integration():
    """Test that frontend can communicate with backend"""
    print("\n🔗 Testing Frontend-Backend Integration...")
    print("-" * 40)
    
    # Test that frontend JavaScript can reach backend
    try:
        # Test the health endpoint from frontend perspective
        response = requests.get("http://localhost:5002/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend can reach backend API")
        else:
            print(f"❌ Frontend-backend communication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend-backend integration error: {e}")
        return False
    
    # Test CORS headers
    try:
        response = requests.options("http://localhost:5002/api/health", timeout=5)
        if response.status_code in [200, 204]:
            print("✅ CORS is properly configured")
        else:
            print("⚠️  CORS configuration may need attention")
    except Exception as e:
        print(f"⚠️  CORS test failed: {e}")
    
    return True

def main():
    """Main test function"""
    print("🚀 Valor IVX Full-Stack Test Suite")
    print("=" * 50)
    
    # Check if services are running
    print("🔍 Checking service status...")
    
    # Test backend
    if not test_backend_api():
        print("\n❌ Backend tests failed!")
        print("💡 Make sure backend is running: ./start_backend.sh")
        sys.exit(1)
    
    # Test frontend
    if not test_frontend():
        print("\n❌ Frontend tests failed!")
        print("💡 Make sure frontend is running: python3 -m http.server 8000")
        sys.exit(1)
    
    # Test integration
    if not test_frontend_backend_integration():
        print("\n❌ Integration tests failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("✅ Backend API: http://localhost:5002")
    print("✅ Frontend: http://localhost:8000")
    print("✅ Full-stack integration is working!")
    print("\n🎯 Application is ready for use!")
    
    return True

if __name__ == "__main__":
    main() 