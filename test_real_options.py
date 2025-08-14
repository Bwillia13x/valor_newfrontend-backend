#!/usr/bin/env python3
"""
Test script for Real Options Analysis
Phase 5A Implementation - Advanced Financial Models

This script tests the real options valuation engine and API endpoints.
"""

import sys
import os
import requests
import json
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_real_options_engine():
    """Test the real options engine directly"""
    print("Testing Real Options Engine...")
    
    try:
        from ml_models.real_options import RealOptionsValuation
        
        # Initialize engine
        engine = RealOptionsValuation()
        print("✓ Real Options Engine initialized successfully")
        
        # Test expansion option
        expansion_result = engine.calculate_expansion_option(
            current_value=1000000,
            expansion_cost=500000,
            time_to_expiry=2.0,
            volatility=0.3,
            risk_free_rate=0.05
        )
        print(f"✓ Expansion option calculated: ${expansion_result['option_value']:,.2f}")
        
        # Test abandonment option
        abandonment_result = engine.calculate_abandonment_option(
            current_value=20000000,
            salvage_value=5000000,
            time_to_expiry=5.0,
            volatility=0.5,
            risk_free_rate=0.03
        )
        print(f"✓ Abandonment option calculated: ${abandonment_result['option_value']:,.2f}")
        
        # Test timing option
        timing_result = engine.calculate_timing_option(
            project_value=8000000,
            investment_cost=3000000,
            time_horizon=4.0,
            volatility=0.45,
            risk_free_rate=0.05
        )
        print(f"✓ Timing option calculated: ${timing_result['option_value']:,.2f}")
        
        # Test volatility estimation
        historical_data = [100, 105, 110, 108, 115, 120, 118, 125, 130, 128]
        volatility = engine.estimate_volatility(historical_data)
        print(f"✓ Volatility estimated: {volatility:.4f}")
        
        print("✓ All engine tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Engine test failed: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints"""
    print("\nTesting API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/api/real-options/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API server. Make sure the backend is running.")
        return False
    
    # Test expansion option endpoint
    try:
        expansion_data = {
            "current_value": 1000000,
            "expansion_cost": 500000,
            "time_to_expiry": 2.0,
            "volatility": 0.3,
            "risk_free_rate": 0.05
        }
        
        response = requests.post(
            f"{base_url}/api/real-options/expansion",
            json=expansion_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Expansion API test passed: ${result['result']['option_value']:,.2f}")
            else:
                print(f"✗ Expansion API test failed: {result.get('error')}")
                return False
        else:
            print(f"✗ Expansion API test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Expansion API test failed: {e}")
        return False
    
    # Test scenarios endpoint
    try:
        response = requests.get(f"{base_url}/api/real-options/scenarios")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                scenarios = result['result']
                print(f"✓ Scenarios API test passed: {len(scenarios)} scenario categories")
            else:
                print(f"✗ Scenarios API test failed: {result.get('error')}")
                return False
        else:
            print(f"✗ Scenarios API test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Scenarios API test failed: {e}")
        return False
    
    print("✓ All API tests passed!")
    return True

def test_frontend_integration():
    """Test frontend integration"""
    print("\nTesting Frontend Integration...")
    
    try:
        # Check if real-options.html exists
        if os.path.exists('real-options.html'):
            print("✓ Real options HTML file exists")
        else:
            print("✗ Real options HTML file not found")
            return False
        
        # Check if real-options.js exists
        if os.path.exists('js/modules/real-options.js'):
            print("✓ Real options JavaScript module exists")
        else:
            print("✗ Real options JavaScript module not found")
            return False
        
        # Check if backend.js exists
        if os.path.exists('js/modules/backend.js'):
            print("✓ Backend API module exists")
        else:
            print("✗ Backend API module not found")
            return False
        
        print("✓ All frontend files present!")
        return True
        
    except Exception as e:
        print(f"✗ Frontend integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Real Options Analysis - Phase 5A Implementation Test")
    print("=" * 60)
    
    # Test engine
    engine_success = test_real_options_engine()
    
    # Test API endpoints (only if engine passed)
    api_success = False
    if engine_success:
        api_success = test_api_endpoints()
    
    # Test frontend integration
    frontend_success = test_frontend_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Engine Tests: {'✓ PASSED' if engine_success else '✗ FAILED'}")
    print(f"API Tests: {'✓ PASSED' if api_success else '✗ FAILED'}")
    print(f"Frontend Tests: {'✓ PASSED' if frontend_success else '✗ FAILED'}")
    
    if engine_success and api_success and frontend_success:
        print("\n🎉 ALL TESTS PASSED! Real Options Analysis is ready for use.")
        print("\nTo use the real options analysis:")
        print("1. Start the backend server: python backend/app.py")
        print("2. Open real-options.html in your browser")
        print("3. Select an option type and enter parameters")
        print("4. Click 'Calculate Option Value' to see results")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 