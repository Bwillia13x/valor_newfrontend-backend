#!/bin/bash

# Infrastructure Monitoring and Auto-Scaling Script
# Phase 4: Performance & Scalability

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="backend"
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"
LOG_FILE="/var/log/valor-ivx/monitor.log"
CONFIG_FILE="monitor_config.json"

# Thresholds
CPU_THRESHOLD_HIGH=80
CPU_THRESHOLD_LOW=20
MEMORY_THRESHOLD_HIGH=85
MEMORY_THRESHOLD_LOW=30
REQUEST_RATE_THRESHOLD_HIGH=1000
REQUEST_RATE_THRESHOLD_LOW=100

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1" | tee -a $LOG_FILE
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1" | tee -a $LOG_FILE
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1" | tee -a $LOG_FILE
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1" | tee -a $LOG_FILE
}

# Create log directory if it doesn't exist
mkdir -p $(dirname $LOG_FILE)

# Get current service replicas
get_current_replicas() {
    docker-compose -f $COMPOSE_FILE ps -q $SERVICE_NAME | wc -l
}

# Scale service
scale_service() {
    local replicas=$1
    log_info "Scaling $SERVICE_NAME to $replicas replicas"
    docker-compose -f $COMPOSE_FILE up -d --scale $SERVICE_NAME=$replicas
    sleep 30  # Wait for scaling to complete
}

# Get CPU usage from Prometheus
get_cpu_usage() {
    local query='avg(rate(container_cpu_usage_seconds_total{container="backend"}[5m])) * 100'
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$query" | jq -r '.data.result[0].value[1] // "0"')
    echo $result
}

# Get memory usage from Prometheus
get_memory_usage() {
    local query='avg(container_memory_usage_bytes{container="backend"}) / avg(container_spec_memory_limit_bytes{container="backend"}) * 100'
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$query" | jq -r '.data.result[0].value[1] // "0"')
    echo $result
}

# Get request rate from Prometheus
get_request_rate() {
    local query='sum(rate(http_requests_total{job="backend"}[5m]))'
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$query" | jq -r '.data.result[0].value[1] // "0"')
    echo $result
}

# Get response time from Prometheus
get_response_time() {
    local query='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="backend"}[5m])) by (le))'
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$query" | jq -r '.data.result[0].value[1] // "0"')
    echo $result
}

# Check if Prometheus is available
check_prometheus() {
    if ! curl -f -s "$PROMETHEUS_URL/api/v1/query?query=up" > /dev/null 2>&1; then
        log_error "Prometheus is not available at $PROMETHEUS_URL"
        return 1
    fi
    return 0
}

# Auto-scaling logic
auto_scale() {
    local current_replicas=$(get_current_replicas)
    local cpu_usage=$(get_cpu_usage)
    local memory_usage=$(get_memory_usage)
    local request_rate=$(get_request_rate)
    local response_time=$(get_response_time)
    
    log_info "Current metrics - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Requests: ${request_rate}/s, Response: ${response_time}s"
    
    local should_scale_up=false
    local should_scale_down=false
    local new_replicas=$current_replicas
    
    # Check if we should scale up
    if (( $(echo "$cpu_usage > $CPU_THRESHOLD_HIGH" | bc -l) )) || \
       (( $(echo "$memory_usage > $MEMORY_THRESHOLD_HIGH" | bc -l) )) || \
       (( $(echo "$request_rate > $REQUEST_RATE_THRESHOLD_HIGH" | bc -l) )); then
        should_scale_up=true
        new_replicas=$((current_replicas + 1))
        log_warning "High resource usage detected, scaling up to $new_replicas replicas"
    fi
    
    # Check if we should scale down (but not below 2 replicas)
    if (( $(echo "$cpu_usage < $CPU_THRESHOLD_LOW" | bc -l) )) && \
       (( $(echo "$memory_usage < $MEMORY_THRESHOLD_LOW" | bc -l) )) && \
       (( $(echo "$request_rate < $REQUEST_RATE_THRESHOLD_LOW" | bc -l) )) && \
       [ $current_replicas -gt 2 ]; then
        should_scale_down=true
        new_replicas=$((current_replicas - 1))
        log_info "Low resource usage detected, scaling down to $new_replicas replicas"
    fi
    
    # Perform scaling if needed
    if [ "$should_scale_up" = true ] || [ "$should_scale_down" = true ]; then
        scale_service $new_replicas
        log_success "Scaled $SERVICE_NAME to $new_replicas replicas"
    else
        log_info "No scaling needed, current replicas: $current_replicas"
    fi
}

# Health check all services
health_check() {
    log_info "Performing health check on all services..."
    
    local services=("backend" "postgres" "redis" "prometheus" "grafana")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if docker-compose -f $COMPOSE_FILE ps $service | grep -q "Up"; then
            log_success "$service is healthy"
        else
            log_error "$service is not healthy"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi
    
    log_success "All services are healthy"
    return 0
}

# Database performance check
check_database_performance() {
    log_info "Checking database performance..."
    
    # Check connection pool
    local connections=$(docker-compose -f $COMPOSE_FILE exec -T postgres psql -U valor_user -d valor_ivx -c "SELECT count(*) FROM pg_stat_activity;" -t | tr -d ' ')
    
    if [ "$connections" -gt 100 ]; then
        log_warning "High number of database connections: $connections"
    else
        log_info "Database connections: $connections"
    fi
    
    # Check slow queries
    local slow_queries=$(docker-compose -f $COMPOSE_FILE exec -T postgres psql -U valor_user -d valor_ivx -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';" -t | tr -d ' ')
    
    if [ "$slow_queries" -gt 0 ]; then
        log_warning "Slow queries detected: $slow_queries"
    fi
}

# Redis performance check
check_redis_performance() {
    log_info "Checking Redis performance..."
    
    # Check memory usage
    local memory_info=$(docker-compose -f $COMPOSE_FILE exec -T redis redis-cli info memory | grep "used_memory_human\|maxmemory_human")
    log_info "Redis memory: $memory_info"
    
    # Check hit rate
    local hit_rate=$(docker-compose -f $COMPOSE_FILE exec -T redis redis-cli info stats | grep "keyspace_hits\|keyspace_misses" | awk -F: '{print $2}' | tr '\n' ' ')
    log_info "Redis hit rate info: $hit_rate"
}

# Generate monitoring report
generate_report() {
    local report_file="/tmp/valor-ivx-monitor-report-$(date +%Y%m%d-%H%M%S).json"
    
    cat > $report_file << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "metrics": {
        "cpu_usage": $(get_cpu_usage),
        "memory_usage": $(get_memory_usage),
        "request_rate": $(get_request_rate),
        "response_time": $(get_response_time),
        "current_replicas": $(get_current_replicas)
    },
    "thresholds": {
        "cpu_high": $CPU_THRESHOLD_HIGH,
        "cpu_low": $CPU_THRESHOLD_LOW,
        "memory_high": $MEMORY_THRESHOLD_HIGH,
        "memory_low": $MEMORY_THRESHOLD_LOW,
        "request_rate_high": $REQUEST_RATE_THRESHOLD_HIGH,
        "request_rate_low": $REQUEST_RATE_THRESHOLD_LOW
    },
    "health": {
        "services_healthy": $(health_check > /dev/null && echo "true" || echo "false")
    }
}
EOF
    
    log_info "Monitoring report generated: $report_file"
}

# Main monitoring loop
monitor_loop() {
    local interval=${1:-60}  # Default 60 seconds
    
    log_info "Starting monitoring loop with ${interval}s interval..."
    
    while true; do
        log_info "=== Monitoring cycle started ==="
        
        # Check if Prometheus is available
        if ! check_prometheus; then
            log_error "Prometheus unavailable, skipping metrics collection"
            sleep $interval
            continue
        fi
        
        # Perform health checks
        health_check
        
        # Check database and Redis performance
        check_database_performance
        check_redis_performance
        
        # Auto-scaling
        auto_scale
        
        # Generate report
        generate_report
        
        log_info "=== Monitoring cycle completed ==="
        sleep $interval
    done
}

# Handle script arguments
case "${1:-monitor}" in
    "monitor")
        monitor_loop ${2:-60}
        ;;
    "scale")
        auto_scale
        ;;
    "health")
        health_check
        ;;
    "report")
        generate_report
        ;;
    "db-check")
        check_database_performance
        ;;
    "redis-check")
        check_redis_performance
        ;;
    *)
        echo "Usage: $0 {monitor|scale|health|report|db-check|redis-check} [interval]"
        echo "  monitor     - Start continuous monitoring (default: 60s interval)"
        echo "  scale       - Run auto-scaling once"
        echo "  health      - Check health of all services"
        echo "  report      - Generate monitoring report"
        echo "  db-check    - Check database performance"
        echo "  redis-check - Check Redis performance"
        exit 1
        ;;
esac 