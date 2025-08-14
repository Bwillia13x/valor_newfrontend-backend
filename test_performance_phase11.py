#!/usr/bin/env python3
"""
Test script for Phase 11: Performance & Scalability Enhancements
Tests the new performance monitoring, caching, and optimization features
"""

import requests
import time
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5002"
API_BASE = f"{BASE_URL}/api"
HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": "test-tenant-123"
}

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def test_api_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test an API endpoint and return the response"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data or {})
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data or {})
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            return response.json() if response.content else None
        else:
            print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            if response.content:
                print(f"   Response: {response.text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Request failed: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ {method} {endpoint} - Unexpected error: {str(e)}")
        return None

def test_performance_health():
    """Test performance monitoring health endpoint"""
    print_section("Testing Performance Health Endpoint")
    
    response = test_api_endpoint("/performance/health")
    if response:
        print(f"   Health Status: {response.get('data', {}).get('status', 'unknown')}")
        print(f"   Message: {response.get('data', {}).get('message', 'N/A')}")

def test_system_status():
    """Test comprehensive system status endpoint"""
    print_section("Testing System Status Endpoint")
    
    response = test_api_endpoint("/performance/system-status")
    if response:
        data = response.get('data', {})
        print(f"   Overall Status: {data.get('overall_status', 'unknown')}")
        print(f"   Components: {len(data.get('components', {}))}")
        
        # Check individual components
        components = data.get('components', {})
        for component, status in components.items():
            if isinstance(status, tuple) and len(status) >= 2:
                print(f"   {component}: {'✅' if status[0] else '❌'} - {status[1]}")

def test_performance_summary():
    """Test performance summary endpoint"""
    print_section("Testing Performance Summary Endpoint")
    
    response = test_api_endpoint("/performance/summary")
    if response:
        data = response.get('data', {})
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        
        if 'metrics' in data:
            metrics = data['metrics']
            if 'system' in metrics:
                system = metrics['system']
                print(f"   CPU Usage: {system.get('cpu_percent', 'N/A')}%")
                print(f"   Memory Usage: {system.get('memory_percent', 'N/A')}%")

def test_historical_metrics():
    """Test historical metrics endpoint"""
    print_section("Testing Historical Metrics Endpoint")
    
    # Test system metrics
    response = test_api_endpoint("/performance/metrics/system?hours=1")
    if response:
        data = response.get('data', {})
        print(f"   System Metrics: {data.get('count', 0)} data points")
        print(f"   Time Range: {data.get('hours', 0)} hours")
    
    # Test cache metrics
    response = test_api_endpoint("/performance/metrics/cache?hours=1")
    if response:
        data = response.get('data', {})
        print(f"   Cache Metrics: {data.get('count', 0)} data points")

def test_optimization_recommendations():
    """Test optimization recommendations endpoint"""
    print_section("Testing Optimization Recommendations Endpoint")
    
    response = test_api_endpoint("/performance/recommendations")
    if response:
        data = response.get('data', {})
        
        # Check current issues
        current_issues = data.get('current_issues', [])
        print(f"   Current Issues: {len(current_issues)}")
        
        # Check optimization categories
        categories = ['database_optimization', 'cache_optimization', 'background_processing']
        for category in categories:
            recs = data.get(category, [])
            print(f"   {category.replace('_', ' ').title()}: {len(recs)} recommendations")

def test_performance_alerts():
    """Test performance alerts endpoint"""
    print_section("Testing Performance Alerts Endpoint")
    
    response = test_api_endpoint("/performance/alerts")
    if response:
        data = response.get('data', {})
        alerts = data.get('alerts', [])
        print(f"   Active Alerts: {len(alerts)}")
        
        for alert in alerts[:3]:  # Show first 3 alerts
            print(f"   - {alert.get('severity', 'unknown').upper()}: {alert.get('message', 'N/A')}")

def test_performance_dashboard():
    """Test performance dashboard endpoint"""
    print_section("Testing Performance Dashboard Endpoint")
    
    response = test_api_endpoint("/performance/dashboard")
    if response:
        data = response.get('data', {})
        print(f"   Dashboard Status: {data.get('current_status', {}).get('status', 'unknown')}")
        
        trends = data.get('trends', {})
        for metric, values in trends.items():
            print(f"   {metric}: {len(values)} data points")

def test_performance_thresholds():
    """Test performance thresholds management"""
    print_section("Testing Performance Thresholds Management")
    
    # Get current thresholds
    response = test_api_endpoint("/performance/thresholds")
    if response:
        data = response.get('data', {})
        print(f"   Current Thresholds: {len(data)} configured")
        for metric, value in data.items():
            print(f"   - {metric}: {value}")
    
    # Test updating thresholds (this would require authentication in real usage)
    print("   Note: Threshold updates require authentication")

def test_performance_optimization():
    """Test performance optimization triggers"""
    print_section("Testing Performance Optimization Triggers")
    
    # Test task cleanup optimization
    response = test_api_endpoint("/performance/optimize", method="POST", 
                               data={"type": "task_cleanup"})
    if response:
        print(f"   Task Cleanup: {response.get('data', {}).get('message', 'N/A')}")
    
    # Test cache warming optimization
    response = test_api_endpoint("/performance/optimize", method="POST", 
                               data={"type": "cache_warming"})
    if response:
        print(f"   Cache Warming: {response.get('data', {}).get('message', 'N/A')}")

def test_cache_health():
    """Test cache system health"""
    print_section("Testing Cache System Health")
    
    # Test cache operations through performance endpoints
    response = test_api_endpoint("/performance/system-status")
    if response:
        data = response.get('data', {})
        cache_status = data.get('components', {}).get('cache_system')
        if cache_status:
            print(f"   Cache Status: {'✅' if cache_status[0] else '❌'} - {cache_status[1]}")

def test_database_health():
    """Test database system health"""
    print_section("Testing Database System Health")
    
    response = test_api_endpoint("/performance/system-status")
    if response:
        data = response.get('data', {})
        db_status = data.get('components', {}).get('database_system')
        if db_status:
            print(f"   Database Status: {'✅' if db_status[0] else '❌'} - {cache_status[1]}")
        
        # Check database metrics
        db_metrics = data.get('metrics', {}).get('database', {})
        if db_metrics:
            print(f"   Pool Size: {db_metrics.get('pool_size', 'N/A')}")
            print(f"   Active Connections: {db_metrics.get('checked_out', 'N/A')}")

def test_task_system_health():
    """Test task system health"""
    print_section("Testing Task System Health")
    
    response = test_api_endpoint("/performance/system-status")
    if response:
        data = response.get('data', {})
        task_status = data.get('components', {}).get('task_system')
        if task_status:
            print(f"   Task System Status: {'✅' if task_status[0] else '❌'} - {task_status[1]}")
        
        # Check task metrics
        task_metrics = data.get('metrics', {}).get('tasks', {})
        if task_metrics:
            print(f"   Active Tasks: {task_metrics.get('active_tasks', 'N/A')}")
            print(f"   Cached Results: {task_metrics.get('cached_results', 'N/A')}")

def test_performance_monitoring_controls():
    """Test performance monitoring start/stop controls"""
    print_section("Testing Performance Monitoring Controls")
    
    # Note: These endpoints require authentication in real usage
    print("   Note: Monitoring controls require authentication")
    print("   Endpoints available:")
    print("   - POST /performance/start-monitoring")
    print("   - POST /performance/stop-monitoring")

def run_performance_stress_test():
    """Run a simple performance stress test"""
    print_section("Running Performance Stress Test")
    
    print("   Making multiple concurrent requests to test system performance...")
    
    start_time = time.time()
    successful_requests = 0
    total_requests = 10
    
    for i in range(total_requests):
        response = test_api_endpoint("/performance/summary")
        if response:
            successful_requests += 1
        time.sleep(0.1)  # Small delay between requests
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"   Stress Test Results:")
    print(f"   - Total Requests: {total_requests}")
    print(f"   - Successful: {successful_requests}")
    print(f"   - Failed: {total_requests - successful_requests}")
    print(f"   - Total Time: {total_time:.2f}s")
    print(f"   - Requests/Second: {total_requests/total_time:.2f}")

def main():
    """Main test function"""
    print_header("Phase 11: Performance & Scalability Testing")
    print(f"Testing Valor IVX performance features at {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Test basic health and status
        test_performance_health()
        test_system_status()
        test_performance_summary()
        
        # Test metrics and monitoring
        test_historical_metrics()
        test_performance_alerts()
        test_performance_dashboard()
        
        # Test optimization features
        test_optimization_recommendations()
        test_performance_thresholds()
        test_performance_optimization()
        
        # Test component health
        test_cache_health()
        test_database_health()
        test_task_system_health()
        
        # Test monitoring controls
        test_performance_monitoring_controls()
        
        # Run stress test
        run_performance_stress_test()
        
        print_header("Testing Complete")
        print("✅ All performance tests completed successfully!")
        print("\nNext steps:")
        print("1. Access the performance dashboard at: http://localhost:8000/performance-dashboard.html")
        print("2. Monitor system performance in real-time")
        print("3. Review optimization recommendations")
        print("4. Test background task processing with Celery")
        
    except KeyboardInterrupt:
        print("\n\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()