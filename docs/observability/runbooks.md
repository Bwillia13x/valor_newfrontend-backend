# Valor IVX - Incident Response Runbooks

## Overview

This document contains runbooks for common incidents and troubleshooting procedures for the Valor IVX platform. Each runbook provides step-by-step instructions for resolving specific issues.

## Table of Contents

1. [API Availability SLO Breach](#api-availability-slo-breach)
2. [API Latency SLO Breach](#api-latency-slo-breach)
3. [Financial Calculation Accuracy Issues](#financial-calculation-accuracy-issues)
4. [High Error Rate](#high-error-rate)
5. [High Response Time](#high-response-time)
6. [Resource Usage Issues](#resource-usage-issues)
7. [Database Connection Issues](#database-connection-issues)
8. [Redis Connection Issues](#redis-connection-issues)
9. [External API Issues](#external-api-issues)
10. [Service Down](#service-down)
11. [Security Incidents](#security-incidents)

---

## API Availability SLO Breach

### Alert Description
API availability has dropped below 99.9% for the last 5 minutes.

### Severity
**Critical**

### Immediate Actions

1. **Check Service Status**
   ```bash
   curl -f http://localhost:5000/health
   curl -f http://localhost:5000/health/ready
   curl -f http://localhost:5000/health/live
   ```

2. **Check Application Logs**
   ```bash
   tail -f /var/log/valor-ivx/valor_ivx.log
   grep -i error /var/log/valor-ivx/valor_ivx.log | tail -20
   ```

3. **Check System Resources**
   ```bash
   top
   free -h
   df -h
   ```

4. **Check Database Connectivity**
   ```bash
   # Test database connection
   python -c "from backend.app import db; print(db.engine.execute('SELECT 1').fetchone())"
   ```

5. **Check Redis Connectivity**
   ```bash
   # Test Redis connection
   redis-cli ping
   ```

### Investigation Steps

1. **Identify Affected Endpoints**
   ```bash
   # Check which endpoints are failing
   curl -s http://localhost:5000/metrics | grep http_requests_total
   ```

2. **Check Error Distribution**
   ```bash
   # Analyze error patterns
   grep "ERROR" /var/log/valor-ivx/valor_ivx.log | awk '{print $4}' | sort | uniq -c
   ```

3. **Check Recent Deployments**
   ```bash
   # Check if recent changes caused the issue
   git log --oneline -10
   ```

### Resolution Steps

1. **Restart Application (if necessary)**
   ```bash
   sudo systemctl restart valor-ivx
   ```

2. **Scale Up Resources (if needed)**
   ```bash
   # Increase worker processes
   export WORKER_PROCESSES=8
   sudo systemctl restart valor-ivx
   ```

3. **Check for Memory Leaks**
   ```bash
   # Monitor memory usage
   ps aux | grep valor-ivx
   ```

### Verification

1. **Monitor Recovery**
   ```bash
   # Watch metrics for improvement
   watch -n 5 'curl -s http://localhost:5000/metrics | grep http_requests_total'
   ```

2. **Check SLO Status**
   ```bash
   curl -s http://localhost:5000/slo/status | jq '.api_availability'
   ```

### Prevention

1. **Implement Circuit Breakers**
2. **Add Health Checks**
3. **Monitor Resource Usage**
4. **Implement Graceful Degradation**

---

## API Latency SLO Breach

### Alert Description
95th percentile API response time exceeds 200ms for the last 5 minutes.

### Severity
**Critical**

### Immediate Actions

1. **Check Current Response Times**
   ```bash
   curl -s http://localhost:5000/metrics | grep http_request_duration_seconds
   ```

2. **Identify Slow Endpoints**
   ```bash
   # Find endpoints with high latency
   curl -s http://localhost:5000/metrics | grep http_request_duration_seconds_bucket
   ```

3. **Check Database Performance**
   ```bash
   # Check database query performance
   python -c "from backend.app import db; import time; start=time.time(); db.engine.execute('SELECT 1'); print(f'Query time: {time.time()-start:.3f}s')"
   ```

### Investigation Steps

1. **Analyze Slow Queries**
   ```bash
   # Enable slow query logging
   # Check for long-running database queries
   ```

2. **Check External API Performance**
   ```bash
   # Test external API response times
   curl -w "@curl-format.txt" -o /dev/null -s "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=1min&apikey=demo"
   ```

3. **Check Cache Performance**
   ```bash
   # Monitor cache hit ratio
   curl -s http://localhost:5000/metrics | grep cache_hits_total
   ```

### Resolution Steps

1. **Optimize Database Queries**
   ```bash
   # Add database indexes if needed
   # Optimize slow queries
   ```

2. **Increase Cache Usage**
   ```bash
   # Check cache configuration
   # Implement additional caching layers
   ```

3. **Scale Resources**
   ```bash
   # Increase CPU/memory allocation
   # Add more worker processes
   ```

### Verification

1. **Monitor Latency Recovery**
   ```bash
   watch -n 5 'curl -s http://localhost:5000/metrics | grep http_request_duration_seconds'
   ```

2. **Check SLO Status**
   ```bash
   curl -s http://localhost:5000/slo/status | jq '.api_latency_p95'
   ```

### Prevention

1. **Implement Query Optimization**
2. **Add Database Indexes**
3. **Implement Caching Strategy**
4. **Monitor External API Performance**

---

## Financial Calculation Accuracy Issues

### Alert Description
Financial calculation accuracy has dropped below 99.9% for the last hour.

### Severity
**Critical**

### Immediate Actions

1. **Check Calculation Logs**
   ```bash
   grep -i "calculation" /var/log/valor-ivx/valor_ivx.log | tail -20
   grep -i "error" /var/log/valor-ivx/valor_ivx.log | grep -i "financial" | tail -20
   ```

2. **Check Financial Data Sources**
   ```bash
   # Verify external data sources
   curl -s "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=1min&apikey=demo" | jq '.'
   ```

3. **Check Model Performance**
   ```bash
   # Test ML model accuracy
   python -c "from backend.ml_models.registry import get_model; model = get_model('revenue_predictor'); print('Model loaded successfully')"
   ```

### Investigation Steps

1. **Analyze Calculation Errors**
   ```bash
   # Identify specific calculation types failing
   grep "ERROR" /var/log/valor-ivx/valor_ivx.log | grep "calculation" | awk '{print $NF}' | sort | uniq -c
   ```

2. **Check Input Data Quality**
   ```bash
   # Validate input data
   python -c "from backend.financial_data import validate_data; print('Data validation passed')"
   ```

3. **Test Calculation Components**
   ```bash
   # Test individual calculation modules
   python -m pytest tests/test_ml_models.py -k "test_revenue_predictor" -v
   ```

### Resolution Steps

1. **Fix Data Issues**
   ```bash
   # Clean or replace corrupted data
   # Implement data validation
   ```

2. **Update Models**
   ```bash
   # Retrain ML models if needed
   # Update calculation algorithms
   ```

3. **Implement Fallbacks**
   ```bash
   # Add calculation fallback mechanisms
   # Implement graceful degradation
   ```

### Verification

1. **Test Calculations**
   ```bash
   # Run calculation tests
   python -m pytest tests/test_ml_models.py -v
   ```

2. **Monitor Accuracy**
   ```bash
   curl -s http://localhost:5000/metrics | grep financial_calculations_total
   ```

### Prevention

1. **Implement Data Validation**
2. **Add Model Monitoring**
3. **Implement Fallback Mechanisms**
4. **Regular Model Retraining**

---

## High Error Rate

### Alert Description
Error rate exceeds 0.1 errors per second for the last 2 minutes.

### Severity
**Critical**

### Immediate Actions

1. **Check Error Logs**
   ```bash
   tail -f /var/log/valor-ivx/valor_ivx.log | grep ERROR
   ```

2. **Check Error Types**
   ```bash
   curl -s http://localhost:5000/metrics | grep errors_total
   ```

3. **Check System Resources**
   ```bash
   top
   free -h
   df -h
   ```

### Investigation Steps

1. **Categorize Errors**
   ```bash
   # Analyze error patterns
   grep "ERROR" /var/log/valor-ivx/valor_ivx.log | awk '{print $4}' | sort | uniq -c | sort -nr
   ```

2. **Check Recent Changes**
   ```bash
   # Look for recent deployments or changes
   git log --oneline --since="1 hour ago"
   ```

3. **Check Dependencies**
   ```bash
   # Test external dependencies
   curl -f http://localhost:5000/health
   ```

### Resolution Steps

1. **Fix Root Cause**
   ```bash
   # Address specific error types
   # Fix configuration issues
   # Resolve dependency problems
   ```

2. **Implement Circuit Breakers**
   ```bash
   # Add circuit breaker patterns
   # Implement graceful degradation
   ```

3. **Rollback Changes (if needed)**
   ```bash
   # Revert to previous stable version
   git revert HEAD
   ```

### Verification

1. **Monitor Error Rate**
   ```bash
   watch -n 5 'curl -s http://localhost:5000/metrics | grep errors_total'
   ```

2. **Check Application Health**
   ```bash
   curl -f http://localhost:5000/health
   ```

### Prevention

1. **Implement Error Handling**
2. **Add Circuit Breakers**
3. **Monitor Dependencies**
4. **Implement Rollback Procedures**

---

## High Response Time

### Alert Description
95th percentile response time exceeds 1 second for the last 2 minutes.

### Severity
**Warning**

### Immediate Actions

1. **Check Current Performance**
   ```bash
   curl -s http://localhost:5000/metrics | grep http_request_duration_seconds
   ```

2. **Identify Bottlenecks**
   ```bash
   # Check system resources
   top
   iostat -x 1 5
   ```

3. **Check Database Performance**
   ```bash
   # Monitor database connections
   python -c "from backend.app import db; print(f'Active connections: {db.engine.pool.size()}')"
   ```

### Investigation Steps

1. **Profile Application**
   ```bash
   # Use profiling tools
   # Identify slow code paths
   ```

2. **Check External Dependencies**
   ```bash
   # Test external API response times
   # Check cache performance
   ```

3. **Analyze Query Performance**
   ```bash
   # Check for slow database queries
   # Analyze query execution plans
   ```

### Resolution Steps

1. **Optimize Code**
   ```bash
   # Optimize slow algorithms
   # Implement caching
   # Add database indexes
   ```

2. **Scale Resources**
   ```bash
   # Increase CPU/memory
   # Add more worker processes
   ```

3. **Implement Caching**
   ```bash
   # Add Redis caching
   # Implement application-level caching
   ```

### Verification

1. **Monitor Performance**
   ```bash
   watch -n 5 'curl -s http://localhost:5000/metrics | grep http_request_duration_seconds'
   ```

2. **Load Test**
   ```bash
   # Run performance tests
   locust -f tests/performance/locustfile.py --host=http://localhost:5000
   ```

### Prevention

1. **Performance Monitoring**
2. **Regular Profiling**
3. **Database Optimization**
4. **Caching Strategy**

---

## Resource Usage Issues

### Alert Description
CPU, memory, or disk usage exceeds thresholds.

### Severity
**Warning/Critical**

### Immediate Actions

1. **Check Resource Usage**
   ```bash
   top
   free -h
   df -h
   iostat -x 1 5
   ```

2. **Identify Resource Consumers**
   ```bash
   # Find processes using most resources
   ps aux --sort=-%cpu | head -10
   ps aux --sort=-%mem | head -10
   ```

3. **Check Application Metrics**
   ```bash
   curl -s http://localhost:5000/system/metrics
   ```

### Investigation Steps

1. **Analyze Resource Patterns**
   ```bash
   # Check for memory leaks
   # Identify CPU-intensive operations
   # Check for disk I/O bottlenecks
   ```

2. **Check Application Logs**
   ```bash
   # Look for resource-related errors
   grep -i "memory\|cpu\|disk" /var/log/valor-ivx/valor_ivx.log
   ```

3. **Monitor Resource Trends**
   ```bash
   # Use monitoring tools
   # Check historical resource usage
   ```

### Resolution Steps

1. **Optimize Resource Usage**
   ```bash
   # Optimize memory usage
   # Reduce CPU-intensive operations
   # Implement resource limits
   ```

2. **Scale Resources**
   ```bash
   # Increase server resources
   # Add more instances
   # Implement auto-scaling
   ```

3. **Implement Resource Limits**
   ```bash
   # Set memory limits
   # Implement CPU quotas
   # Add disk space monitoring
   ```

### Verification

1. **Monitor Resource Recovery**
   ```bash
   watch -n 5 'top -bn1 | head -20'
   ```

2. **Check Application Performance**
   ```bash
   curl -f http://localhost:5000/health
   ```

### Prevention

1. **Resource Monitoring**
2. **Capacity Planning**
3. **Performance Optimization**
4. **Auto-scaling Implementation**

---

## Database Connection Issues

### Alert Description
Database errors are occurring or connection issues detected.

### Severity
**Critical**

### Immediate Actions

1. **Check Database Status**
   ```bash
   # Test database connectivity
   python -c "from backend.app import db; print(db.engine.execute('SELECT 1').fetchone())"
   ```

2. **Check Database Logs**
   ```bash
   # Check database server logs
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

3. **Check Connection Pool**
   ```bash
   # Monitor connection pool status
   python -c "from backend.app import db; print(f'Pool size: {db.engine.pool.size()}, Checked out: {db.engine.pool.checkedout()}')"
   ```

### Investigation Steps

1. **Analyze Connection Errors**
   ```bash
   # Check for connection timeouts
   # Look for authentication issues
   # Check for resource exhaustion
   ```

2. **Check Database Performance**
   ```bash
   # Monitor slow queries
   # Check for locks
   # Analyze query performance
   ```

3. **Check Network Connectivity**
   ```bash
   # Test network connectivity
   # Check firewall rules
   # Verify DNS resolution
   ```

### Resolution Steps

1. **Fix Connection Issues**
   ```bash
   # Restart database connections
   # Fix authentication problems
   # Resolve network issues
   ```

2. **Optimize Database**
   ```bash
   # Add database indexes
   # Optimize slow queries
   # Tune database parameters
   ```

3. **Scale Database**
   ```bash
   # Add read replicas
   # Implement connection pooling
   # Add database caching
   ```

### Verification

1. **Test Database Connectivity**
   ```bash
   python -c "from backend.app import db; print('Database connection successful')"
   ```

2. **Monitor Database Performance**
   ```bash
   # Check query performance
   # Monitor connection pool
   ```

### Prevention

1. **Database Monitoring**
2. **Connection Pooling**
3. **Query Optimization**
4. **Regular Maintenance**

---

## Redis Connection Issues

### Alert Description
Redis errors are occurring or connection issues detected.

### Severity
**Critical**

### Immediate Actions

1. **Check Redis Status**
   ```bash
   redis-cli ping
   redis-cli info
   ```

2. **Check Redis Logs**
   ```bash
   # Check Redis server logs
   sudo tail -f /var/log/redis/redis-server.log
   ```

3. **Test Redis Connectivity**
   ```bash
   # Test from application
   python -c "import redis; r = redis.Redis(); print(r.ping())"
   ```

### Investigation Steps

1. **Analyze Redis Errors**
   ```bash
   # Check for memory issues
   # Look for connection limits
   # Check for authentication problems
   ```

2. **Check Redis Performance**
   ```bash
   # Monitor memory usage
   # Check for slow commands
   # Analyze key patterns
   ```

3. **Check Network Connectivity**
   ```bash
   # Test network connectivity
   # Check firewall rules
   # Verify Redis configuration
   ```

### Resolution Steps

1. **Fix Redis Issues**
   ```bash
   # Restart Redis service
   sudo systemctl restart redis
   ```

2. **Optimize Redis**
   ```bash
   # Configure memory limits
   # Optimize key expiration
   # Implement eviction policies
   ```

3. **Scale Redis**
   ```bash
   # Add Redis clustering
   # Implement Redis replication
   # Add Redis Sentinel
   ```

### Verification

1. **Test Redis Connectivity**
   ```bash
   redis-cli ping
   ```

2. **Monitor Redis Performance**
   ```bash
   redis-cli info memory
   redis-cli info stats
   ```

### Prevention

1. **Redis Monitoring**
2. **Memory Management**
3. **Connection Pooling**
4. **Regular Maintenance**

---

## External API Issues

### Alert Description
External API is down or responding slowly.

### Severity
**Critical**

### Immediate Actions

1. **Check External API Status**
   ```bash
   # Test Alpha Vantage API
   curl -w "@curl-format.txt" -o /dev/null -s "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=1min&apikey=demo"
   ```

2. **Check API Keys**
   ```bash
   # Verify API key validity
   echo $ALPHA_VANTAGE_API_KEY
   ```

3. **Check Rate Limits**
   ```bash
   # Monitor API usage
   # Check rate limit headers
   ```

### Investigation Steps

1. **Analyze API Responses**
   ```bash
   # Check for error messages
   # Analyze response times
   # Check for rate limiting
   ```

2. **Check Network Connectivity**
   ```bash
   # Test network connectivity
   # Check DNS resolution
   # Verify firewall rules
   ```

3. **Check API Documentation**
   ```bash
   # Review API changes
   # Check for deprecation notices
   # Verify endpoint availability
   ```

### Resolution Steps

1. **Implement Fallbacks**
   ```bash
   # Use cached data
   # Implement alternative data sources
   # Add graceful degradation
   ```

2. **Fix API Issues**
   ```bash
   # Update API keys
   # Fix authentication issues
   # Resolve rate limiting
   ```

3. **Optimize API Usage**
   ```bash
   # Implement caching
   # Optimize request patterns
   # Add request batching
   ```

### Verification

1. **Test API Connectivity**
   ```bash
   curl -f "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=1min&apikey=demo"
   ```

2. **Monitor API Performance**
   ```bash
   # Check response times
   # Monitor error rates
   ```

### Prevention

1. **API Monitoring**
2. **Caching Strategy**
3. **Fallback Mechanisms**
4. **Rate Limit Management**

---

## Service Down

### Alert Description
Service health check is failing or service is completely down.

### Severity
**Critical**

### Immediate Actions

1. **Check Service Status**
   ```bash
   sudo systemctl status valor-ivx
   ```

2. **Check Process Status**
   ```bash
   ps aux | grep valor-ivx
   ```

3. **Check Port Availability**
   ```bash
   netstat -tlnp | grep :5000
   ```

### Investigation Steps

1. **Check Application Logs**
   ```bash
   tail -f /var/log/valor-ivx/valor_ivx.log
   ```

2. **Check System Resources**
   ```bash
   top
   free -h
   df -h
   ```

3. **Check Dependencies**
   ```bash
   # Check database connectivity
   # Check Redis connectivity
   # Check external APIs
   ```

### Resolution Steps

1. **Restart Service**
   ```bash
   sudo systemctl restart valor-ivx
   ```

2. **Check Configuration**
   ```bash
   # Verify configuration files
   # Check environment variables
   # Validate dependencies
   ```

3. **Rollback Changes**
   ```bash
   # Revert to previous version
   # Fix configuration issues
   # Resolve dependency problems
   ```

### Verification

1. **Test Service Health**
   ```bash
   curl -f http://localhost:5000/health
   ```

2. **Monitor Service Recovery**
   ```bash
   watch -n 5 'curl -f http://localhost:5000/health'
   ```

### Prevention

1. **Health Monitoring**
2. **Automated Restarts**
3. **Configuration Management**
4. **Dependency Monitoring**

---

## Security Incidents

### Alert Description
High rate of authentication failures, authorization issues, or security violations.

### Severity
**Critical**

### Immediate Actions

1. **Check Security Logs**
   ```bash
   grep -i "security\|auth\|unauthorized" /var/log/valor-ivx/valor_ivx.log
   ```

2. **Check Rate Limiting**
   ```bash
   curl -s http://localhost:5000/metrics | grep errors_total | grep rate_limit
   ```

3. **Check Authentication Metrics**
   ```bash
   curl -s http://localhost:5000/metrics | grep errors_total | grep authentication
   ```

### Investigation Steps

1. **Analyze Attack Patterns**
   ```bash
   # Check for brute force attacks
   # Look for suspicious IP addresses
   # Analyze request patterns
   ```

2. **Check User Accounts**
   ```bash
   # Review recent login attempts
   # Check for account lockouts
   # Verify user permissions
   ```

3. **Check System Security**
   ```bash
   # Review firewall rules
   # Check for unauthorized access
   # Verify security configurations
   ```

### Resolution Steps

1. **Implement Security Measures**
   ```bash
   # Block suspicious IPs
   # Implement additional rate limiting
   # Add security headers
   ```

2. **Update Security Configurations**
   ```bash
   # Update authentication settings
   # Review authorization policies
   # Implement security best practices
   ```

3. **Monitor and Alert**
   ```bash
   # Set up security monitoring
   # Implement intrusion detection
   # Add security alerts
   ```

### Verification

1. **Test Security Measures**
   ```bash
   # Verify rate limiting
   # Test authentication
   # Check authorization
   ```

2. **Monitor Security Metrics**
   ```bash
   curl -s http://localhost:5000/metrics | grep errors_total
   ```

### Prevention

1. **Security Monitoring**
2. **Regular Security Audits**
3. **Security Best Practices**
4. **Incident Response Procedures**

---

## General Troubleshooting Commands

### System Information
```bash
# System overview
uname -a
cat /etc/os-release
uptime

# Resource usage
top
htop
free -h
df -h
```

### Application Information
```bash
# Application status
sudo systemctl status valor-ivx
ps aux | grep valor-ivx

# Application logs
tail -f /var/log/valor-ivx/valor_ivx.log
journalctl -u valor-ivx -f
```

### Network Information
```bash
# Network connectivity
netstat -tlnp
ss -tlnp
ping -c 3 google.com

# DNS resolution
nslookup valor-ivx.com
dig valor-ivx.com
```

### Database Information
```bash
# Database status
sudo systemctl status postgresql
psql -U valor_ivx -d valor_ivx -c "SELECT version();"

# Database connections
psql -U valor_ivx -d valor_ivx -c "SELECT * FROM pg_stat_activity;"
```

### Redis Information
```bash
# Redis status
sudo systemctl status redis
redis-cli ping
redis-cli info

# Redis memory
redis-cli info memory
redis-cli info stats
```

### Monitoring Commands
```bash
# Application metrics
curl -s http://localhost:5000/metrics
curl -s http://localhost:5000/health
curl -s http://localhost:5000/slo/status

# System metrics
curl -s http://localhost:5000/system/metrics
```

### Performance Testing
```bash
# Load testing
locust -f tests/performance/locustfile.py --host=http://localhost:5000

# Stress testing
ab -n 1000 -c 10 http://localhost:5000/health

# Performance profiling
python -m cProfile -o profile.stats backend/app.py
```

---

## Emergency Contacts

### Development Team
- **Lead Developer**: [Contact Information]
- **DevOps Engineer**: [Contact Information]
- **System Administrator**: [Contact Information]

### External Services
- **Hosting Provider**: [Contact Information]
- **Database Provider**: [Contact Information]
- **CDN Provider**: [Contact Information]

### Escalation Procedures
1. **Level 1**: On-call engineer (immediate response)
2. **Level 2**: Senior engineer (within 30 minutes)
3. **Level 3**: Engineering manager (within 1 hour)
4. **Level 4**: CTO/VP Engineering (within 2 hours)

---

## Post-Incident Procedures

### Incident Documentation
1. **Incident Report**: Document the incident details
2. **Root Cause Analysis**: Identify the root cause
3. **Resolution Steps**: Document how the issue was resolved
4. **Prevention Measures**: Implement measures to prevent recurrence

### Lessons Learned
1. **Review Incident**: Conduct post-incident review
2. **Update Procedures**: Update runbooks and procedures
3. **Improve Monitoring**: Enhance monitoring and alerting
4. **Training**: Provide training to team members

### Continuous Improvement
1. **Regular Reviews**: Conduct regular incident reviews
2. **Process Updates**: Update incident response procedures
3. **Tool Improvements**: Enhance monitoring and alerting tools
4. **Team Training**: Provide ongoing training and education