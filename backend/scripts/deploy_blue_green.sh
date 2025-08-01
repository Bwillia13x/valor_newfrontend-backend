#!/bin/bash

# Blue/Green Deployment Script for Valor IVX
# Phase 4: Performance & Scalability

set -e

# Configuration
SERVICE_NAME="backend"
BLUE_SERVICE="${SERVICE_NAME}-blue"
GREEN_SERVICE="${SERVICE_NAME}-green"
COMPOSE_FILE="docker-compose.yml"
HEALTH_CHECK_URL="http://localhost:5002/api/health"
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_INTERVAL=10  # 10 seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Health check function
check_health() {
    local service_url=$1
    local timeout=$2
    local interval=$3
    
    log_info "Checking health of $service_url (timeout: ${timeout}s)"
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if curl -f -s "$service_url" > /dev/null 2>&1; then
            log_success "Health check passed for $service_url"
            return 0
        fi
        
        log_info "Health check failed, retrying in ${interval}s... (${elapsed}/${timeout}s elapsed)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Health check failed for $service_url after ${timeout}s"
    return 1
}

# Get current active service
get_active_service() {
    local blue_replicas=$(docker-compose -f $COMPOSE_FILE ps -q $BLUE_SERVICE | wc -l)
    local green_replicas=$(docker-compose -f $COMPOSE_FILE ps -q $GREEN_SERVICE | wc -l)
    
    if [ $blue_replicas -gt 0 ]; then
        echo "blue"
    elif [ $green_replicas -gt 0 ]; then
        echo "green"
    else
        echo "none"
    fi
}

# Deploy to inactive environment
deploy_to_environment() {
    local target_env=$1
    local target_service="${SERVICE_NAME}-${target_env}"
    
    log_info "Deploying to $target_env environment..."
    
    # Build and start the target service
    docker-compose -f $COMPOSE_FILE build $target_service
    docker-compose -f $COMPOSE_FILE up -d --scale $target_service=3 $target_service
    
    # Wait for service to be ready
    log_info "Waiting for $target_service to be ready..."
    sleep 30
    
    # Health check
    if ! check_health $HEALTH_CHECK_URL $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
        log_error "Deployment to $target_env failed health check"
        docker-compose -f $COMPOSE_FILE down $target_service
        exit 1
    fi
    
    log_success "Deployment to $target_env completed successfully"
}

# Switch traffic to target environment
switch_traffic() {
    local target_env=$1
    local target_service="${SERVICE_NAME}-${target_env}"
    local current_env=$2
    
    log_info "Switching traffic from $current_env to $target_env..."
    
    # Scale down current service
    if [ "$current_env" != "none" ]; then
        local current_service="${SERVICE_NAME}-${current_env}"
        log_info "Scaling down $current_service..."
        docker-compose -f $COMPOSE_FILE up -d --scale $current_service=0 $current_service
    fi
    
    # Scale up target service
    log_info "Scaling up $target_service..."
    docker-compose -f $COMPOSE_FILE up -d --scale $target_service=5 $target_service
    
    # Final health check
    if ! check_health $HEALTH_CHECK_URL 60 5; then
        log_error "Traffic switch failed health check"
        # Rollback
        log_warning "Rolling back to $current_env..."
        if [ "$current_env" != "none" ]; then
            local current_service="${SERVICE_NAME}-${current_env}"
            docker-compose -f $COMPOSE_FILE up -d --scale $current_service=5 $current_service
            docker-compose -f $COMPOSE_FILE up -d --scale $target_service=0 $target_service
        fi
        exit 1
    fi
    
    log_success "Traffic switched to $target_env successfully"
}

# Rollback function
rollback() {
    local current_env=$1
    local previous_env=$2
    
    log_warning "Rolling back from $current_env to $previous_env..."
    
    if [ "$previous_env" != "none" ]; then
        switch_traffic $previous_env $current_env
    fi
}

# Main deployment function
main() {
    log_info "Starting blue/green deployment..."
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file $COMPOSE_FILE not found"
        exit 1
    fi
    
    # Get current active service
    local current_env=$(get_active_service)
    log_info "Current active environment: $current_env"
    
    # Determine target environment
    local target_env
    if [ "$current_env" = "blue" ]; then
        target_env="green"
    elif [ "$current_env" = "green" ]; then
        target_env="blue"
    else
        # No active service, start with blue
        target_env="blue"
    fi
    
    log_info "Target environment: $target_env"
    
    # Deploy to target environment
    deploy_to_environment $target_env
    
    # Switch traffic
    switch_traffic $target_env $current_env
    
    # Clean up old environment (optional)
    if [ "$current_env" != "none" ]; then
        log_info "Cleaning up $current_env environment..."
        local old_service="${SERVICE_NAME}-${current_env}"
        docker-compose -f $COMPOSE_FILE up -d --scale $old_service=0 $old_service
    fi
    
    log_success "Blue/green deployment completed successfully!"
    log_info "Active environment: $target_env"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        if [ -z "$2" ]; then
            log_error "Rollback requires target environment (blue or green)"
            exit 1
        fi
        current_env=$(get_active_service)
        rollback $current_env $2
        ;;
    "status")
        current_env=$(get_active_service)
        log_info "Current active environment: $current_env"
        docker-compose -f $COMPOSE_FILE ps
        ;;
    "health")
        check_health $HEALTH_CHECK_URL 30 5
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|health}"
        echo "  deploy   - Deploy using blue/green strategy"
        echo "  rollback - Rollback to specified environment (blue|green)"
        echo "  status   - Show deployment status"
        echo "  health   - Check service health"
        exit 1
        ;;
esac 