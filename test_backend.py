#!/usr/bin/env python3
"""
Test script to verify Valor IVX backend functionality
"""

import requests
import json
import time
import sys

def test_backend():
    """Test the backend API endpoints"""
    
    base_url = "http://localhost:5002/api"
    
    print("🧪 Testing Valor IVX Backend...")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health Check: {data['status']}")
            print(f"   📅 Timestamp: {data['timestamp']}")
            print(f"   🏷️  Version: {data['version']}")
        else:
            print(f"   ❌ Health Check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health Check error: {e}")
        return False
    
    # Test 2: Save Run
    print("\n2. Testing Save Run...")
    test_run_data = {
        "inputs": {
            "ticker": "TEST",
            "revenue": 1000,
            "growthY1": 15.0,
            "wacc": 10.0,
            "years": 5,
            "termGrowth": 3.0,
            "ebitMargin": 25.0,
            "taxRate": 25.0,
            "salesToCap": 3.0,
            "shares": 100,
            "netDebt": 500
        },
        "mc_settings": {
            "trials": 1000,
            "volPP": 2.0,
            "seed": "test-seed"
        },
        "timestamp": "2024-01-15T10:30:00.000Z"
    }
    
    try:
        response = requests.post(
            f"{base_url}/runs",
            json=test_run_data,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Run saved successfully")
            print(f"   🆔 Run ID: {data['run_id']}")
            run_id = data['run_id']
        else:
            print(f"   ❌ Save Run failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Save Run error: {e}")
        return False
    
    # Test 3: Get Last Run
    print("\n3. Testing Get Last Run...")
    try:
        response = requests.get(f"{base_url}/runs/last", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Last run retrieved successfully")
            print(f"   🏷️  Ticker: {data['data']['ticker']}")
            print(f"   💰 Revenue: ${data['data']['inputs']['revenue']}M")
        else:
            print(f"   ❌ Get Last Run failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Get Last Run error: {e}")
        return False
    
    # Test 4: Save Scenario
    print("\n4. Testing Save Scenario...")
    test_scenario_data = [{
        "name": "Test Scenario",
        "ticker": "TEST",
        "inputs": {
            "revenue": 1000,
            "growthY1": 15.0,
            "wacc": 10.0
        },
        "mc_settings": {
            "trials": 1000,
            "volPP": 2.0
        }
    }]
    
    try:
        response = requests.post(
            f"{base_url}/scenarios",
            json=test_scenario_data,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Scenario saved successfully")
            print(f"   📊 Saved count: {data['saved_count']}")
        else:
            print(f"   ❌ Save Scenario failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Save Scenario error: {e}")
        return False
    
    # Test 5: Get Scenarios
    print("\n5. Testing Get Scenarios...")
    try:
        response = requests.get(f"{base_url}/scenarios", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Scenarios retrieved successfully")
            print(f"   📊 Scenario count: {len(data['scenarios'])}")
        else:
            print(f"   ❌ Get Scenarios failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Get Scenarios error: {e}")
        return False
    
    # Test 6: Save Notes
    print("\n6. Testing Save Notes...")
    test_notes_data = {
        "content": "This is a test note for the TEST ticker."
    }
    
    try:
        response = requests.post(
            f"{base_url}/notes/TEST",
            json=test_notes_data,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Notes saved successfully")
        else:
            print(f"   ❌ Save Notes failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Save Notes error: {e}")
        return False
    
    # Test 7: Get Notes
    print("\n7. Testing Get Notes...")
    try:
        response = requests.get(f"{base_url}/notes/TEST", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Notes retrieved successfully")
            print(f"   📝 Content: {data['content'][:50]}...")
        else:
            print(f"   ❌ Get Notes failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Get Notes error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All backend tests passed!")
    print("✅ Backend is working correctly")
    return True

def main():
    """Main test function"""
    print("🚀 Valor IVX Backend Test Suite")
    print("=" * 50)
    
    # Wait a moment for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    success = test_backend()
    
    if success:
        print("\n🎯 Backend is ready for frontend integration!")
        print("📊 Frontend can now connect to: http://localhost:5002")
        sys.exit(0)
    else:
        print("\n❌ Backend tests failed!")
        print("🔧 Please check the backend logs and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 