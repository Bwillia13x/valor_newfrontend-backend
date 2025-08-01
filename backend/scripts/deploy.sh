#!/bin/bash

# Valor IVX Platform Deployment Script
# Supports blue/green deployment with zero downtime

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${1:-production}"
IMAGE_TAG="${2:-latest}"
NAMESPACE="valor-ivx-${DEPLOYMENT_ENV}"

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
health_check() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    log_info "Performing health check for $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl get pods -n "$NAMESPACE" -l app="$service_name" | grep -q "Running"; then
            if kubectl exec -n "$NAMESPACE" deployment/"$service_name" -- curl -f http://localhost:5002/api/health >/dev/null 2>&1; then
                log_success "Health check passed for $service_name"
                return 0
            fi
        fi
        
        log_warning "Health check attempt $attempt/$max_attempts failed for $service_name"
        sleep 10
        ((attempt++))
    done
    
    log_error "Health check failed for $service_name after $max_attempts attempts"
    return 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
    
    # Check if secrets exist
    if ! kubectl get secret valor-ivx-secrets -n "$NAMESPACE" &> /dev/null; then
        log_error "Required secrets not found in namespace $NAMESPACE"
        log_error "Please create the secrets before deployment"
        exit 1
    fi
    
    # Check available resources
    log_info "Checking cluster resources..."
    kubectl top nodes 2>/dev/null || log_warning "Metrics server not available"
    
    log_success "Pre-deployment checks completed"
}

# Backup current deployment
backup_deployment() {
    log_info "Creating backup of current deployment..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    kubectl get all -n "$NAMESPACE" -o yaml > "$backup_dir/deployment_backup.yaml"
    kubectl get configmap -n "$NAMESPACE" -o yaml > "$backup_dir/configmap_backup.yaml"
    kubectl get secret -n "$NAMESPACE" -o yaml > "$backup_dir/secret_backup.yaml"
    
    log_success "Backup created at $backup_dir"
}

# Deploy new version
deploy_new_version() {
    local deployment_name="$1"
    local image_tag="$2"
    
    log_info "Deploying new version of $deployment_name with image tag $image_tag"
    
    # Update the deployment with new image
    kubectl set image deployment/"$deployment_name" valor-backend="valor-ivx-backend:$image_tag" -n "$NAMESPACE"
    
    # Wait for rollout to complete
    kubectl rollout status deployment/"$deployment_name" -n "$NAMESPACE" --timeout=300s
    
    # Perform health check
    health_check "$deployment_name"
}

# Blue/Green deployment
blue_green_deployment() {
    log_info "Starting blue/green deployment..."
    
    # Determine current active deployment
    local current_deployment
    if kubectl get deployment valor-backend-blue -n "$NAMESPACE" &> /dev/null; then
        current_deployment="blue"
        inactive_deployment="green"
    else
        current_deployment="green"
        inactive_deployment="blue"
    fi
    
    log_info "Current active deployment: $current_deployment"
    
    # Deploy to inactive environment
    log_info "Deploying to $inactive_deployment environment..."
    deploy_new_version "valor-backend-$inactive_deployment" "$IMAGE_TAG"
    
    # Switch traffic
    log_info "Switching traffic to $inactive_deployment environment..."
    kubectl apply -f "$PROJECT_ROOT/k8s/production/ingress-$inactive_deployment.yaml" -n "$NAMESPACE"
    
    # Wait for traffic to stabilize
    log_info "Waiting for traffic to stabilize..."
    sleep 60
    
    # Verify new deployment is healthy
    if health_check "valor-backend-$inactive_deployment"; then
        log_success "Blue/green deployment completed successfully"
        
        # Clean up old deployment
        log_info "Cleaning up old $current_deployment deployment..."
        kubectl delete deployment "valor-backend-$current_deployment" -n "$NAMESPACE" || true
    else
        log_error "New deployment health check failed, rolling back..."
        rollback_deployment "$current_deployment"
        exit 1
    fi
}

# Rollback deployment
rollback_deployment() {
    local target_deployment="$1"
    
    log_warning "Rolling back to $target_deployment deployment..."
    
    # Switch traffic back
    kubectl apply -f "$PROJECT_ROOT/k8s/production/ingress-$target_deployment.yaml" -n "$NAMESPACE"
    
    # Verify rollback
    if health_check "valor-backend-$target_deployment"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed - manual intervention required"
        exit 1
    fi
}

# Post-deployment verification
post_deployment_verification() {
    log_info "Running post-deployment verification..."
    
    # Check all pods are running
    kubectl get pods -n "$NAMESPACE"
    
    # Check services
    kubectl get services -n "$NAMESPACE"
    
    # Check ingress
    kubectl get ingress -n "$NAMESPACE"
    
    # Run smoke tests
    if [ -f "$PROJECT_ROOT/scripts/smoke-tests.sh" ]; then
        log_info "Running smoke tests..."
        "$PROJECT_ROOT/scripts/smoke-tests.sh" "$DEPLOYMENT_ENV"
    fi
    
    # Check metrics
    log_info "Checking application metrics..."
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || log_warning "Metrics not available"
    
    log_success "Post-deployment verification completed"
}

# Main deployment function
main() {
    log_info "Starting Valor IVX deployment to $DEPLOYMENT_ENV environment"
    log_info "Image tag: $IMAGE_TAG"
    log_info "Namespace: $NAMESPACE"
    
    # Pre-deployment checks
    pre_deployment_checks
    
    # Create backup
    backup_deployment
    
    # Deploy based on environment
    case "$DEPLOYMENT_ENV" in
        "production")
            blue_green_deployment
            ;;
        "staging")
            deploy_new_version "valor-backend" "$IMAGE_TAG"
            ;;
        *)
            log_error "Unknown deployment environment: $DEPLOYMENT_ENV"
            exit 1
            ;;
    esac
    
    # Post-deployment verification
    post_deployment_verification
    
    log_success "Deployment completed successfully!"
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@" 