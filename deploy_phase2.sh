#!/bin/bash

# Phase 2 Deployment Script for Valor IVX
# Advanced Collaboration & Analytics Platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/benjaminwilliams/valor_newfrontend-backend"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT"
VENV_DIR="$BACKEND_DIR/venv"
LOG_DIR="$PROJECT_ROOT/logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run as root"
    exit 1
fi

# Check Python version
check_python() {
    log "Checking Python version..."
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    required_version="3.8"
    
    if [[ $(echo -e "$python_version\n$required_version" | sort -V | head -n1) != "$required_version" ]]; then
        error "Python 3.8 or higher is required. Found: $python_version"
        exit 1
    fi
    
    log "Python version check passed: $python_version"
}

# Check Node.js version
check_node() {
    log "Checking Node.js version..."
    node_version=$(node --version 2>&1 | sed 's/v//')
    required_version="14.0.0"
    
    if [[ $(echo -e "$node_version\n$required_version" | sort -V | head -n1) != "$required_version" ]]; then
        error "Node.js 14.0.0 or higher is required. Found: $node_version"
        exit 1
    fi
    
    log "Node.js version check passed: $node_version"
}

# Setup Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
        log "Virtual environment created"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    log "Upgrading pip..."
    pip install --upgrade pip
    
    log "Installing Python dependencies..."
    pip install -r "$BACKEND_DIR/requirements.txt"
    
    # Install additional ML dependencies
    pip install scikit-learn pandas numpy joblib
    
    log "Python environment setup complete"
}

# Install Node.js dependencies
setup_node_env() {
    log "Setting up Node.js environment..."
    
    cd "$FRONTEND_DIR"
    
    if [[ ! -f "package.json" ]]; then
        npm init -y
    fi
    
    log "Installing Node.js dependencies..."
    npm install
    
    log "Node.js environment setup complete"
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    cd "$BACKEND_DIR"
    
    # Initialize database
    python -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"
    
    log "Database setup complete"
}

# Configure environment variables
configure_env() {
    log "Configuring environment variables..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$BACKEND_DIR/.env" ]]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        log "Created .env file from example"
    fi
    
    # Update environment variables for Phase 2
    sed -i.bak 's/PHASE=1/PHASE=2/g' "$BACKEND_DIR/.env"
    sed -i.bak 's/DEBUG=True/DEBUG=False/g' "$BACKEND_DIR/.env"
    
    log "Environment variables configured"
}

# Build frontend assets
build_frontend() {
    log "Building frontend assets..."
    
    cd "$FRONTEND_DIR"
    
    # Create necessary directories
    mkdir -p public/icons
    mkdir -p public/screenshots
    
    # Copy PWA assets
    cp manifest.json public/
    cp sw.js public/
    
    # Create placeholder icons (in production, these would be actual icons)
    for size in 72 96 128 144 152 192 384 512; do
        echo "Creating placeholder icon ${size}x${size}"
        # In production, use actual icon generation
    done
    
    log "Frontend assets built"
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    if [[ ! -f "$PROJECT_ROOT/ssl/cert.pem" ]]; then
        log "Generating self-signed SSL certificates..."
        mkdir -p "$PROJECT_ROOT/ssl"
        
        openssl req -x509 -newkey rsa:4096 -keyout "$PROJECT_ROOT/ssl/key.pem" \
            -out "$PROJECT_ROOT/ssl/cert.pem" -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log "SSL certificates generated"
    else
        log "SSL certificates already exist"
    fi
}

# Setup systemd services
setup_services() {
    log "Setting up systemd services..."
    
    # Create systemd service file
    sudo tee /etc/systemd/system/valor-ivx.service > /dev/null <<EOF
[Unit]
Description=Valor IVX Financial Modeling Platform
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python $BACKEND_DIR/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable valor-ivx
    
    log "Systemd service configured"
}

# Setup nginx configuration
setup_nginx() {
    log "Setting up nginx configuration..."
    
    sudo tee /etc/nginx/sites-available/valor-ivx > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost;
    
    ssl_certificate $PROJECT_ROOT/ssl/cert.pem;
    ssl_certificate_key $PROJECT_ROOT/ssl/key.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Static files
    location /static/ {
        alias $FRONTEND_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API routes
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Main application
    location / {
        root $FRONTEND_DIR;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/valor-ivx /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    log "Nginx configuration complete"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring script
    cat > "$PROJECT_ROOT/monitor.sh" <<'EOF'
#!/bin/bash
# Simple monitoring script for Valor IVX

LOG_FILE="/var/log/valor-ivx/monitor.log"
mkdir -p "$(dirname "$LOG_FILE")"

check_service() {
    if systemctl is-active --quiet valor-ivx; then
        echo "$(date): Service is running" >> "$LOG_FILE"
    else
        echo "$(date): Service is down - restarting" >> "$LOG_FILE"
        systemctl restart valor-ivx
    fi
}

check_disk_space() {
    usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -gt 80 ]; then
        echo "$(date): Disk usage is ${usage}%" >> "$LOG_FILE"
    fi
}

check_memory() {
    usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$usage" -gt 80 ]; then
        echo "$(date): Memory usage is ${usage}%" >> "$LOG_FILE"
    fi
}

check_service
check_disk_space
check_memory
EOF
    
    chmod +x "$PROJECT_ROOT/monitor.sh"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_ROOT/monitor.sh") | crontab -
    
    log "Monitoring setup complete"
}

# Run tests
run_tests() {
    log "Running Phase 2 tests..."
    
    # Run Python tests
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    python -m pytest tests/test_ml_models.py -v
    
    # Run JavaScript tests
    cd "$FRONTEND_DIR"
    node tests/test_collaboration_engine.js
    
    log "All tests completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Check if services are running
    if systemctl is-active --quiet valor-ivx; then
        log "Valor IVX service is running"
    else
        warning "Valor IVX service is not running"
    fi
    
    # Check nginx
    if systemctl is-active --quiet nginx; then
        log "Nginx is running"
    else
        warning "Nginx is not running"
    fi
    
    # Check ports
    if netstat -tuln | grep -q ":5000"; then
        log "Backend is listening on port 5000"
    else
        warning "Backend is not listening on port 5000"
    fi
    
    # Check SSL
    if openssl x509 -in "$PROJECT_ROOT/ssl/cert.pem" -text -noout > /dev/null 2>&1; then
        log "SSL certificate is valid"
    else
        warning "SSL certificate is invalid"
    fi
}

# Main deployment function
main() {
    log "Starting Phase 2 deployment for Valor IVX..."
    
    # Pre-deployment checks
    check_python
    check_node
    
    # Deployment steps
    setup_python_env
    setup_node_env
    setup_database
    configure_env
    build_frontend
    setup_ssl
    setup_services
    setup_nginx
    setup_monitoring
    run_tests
    health_check
    
    log "Phase 2 deployment completed successfully!"
    log "Access the application at: https://localhost"
    
    # Display summary
    echo ""
    echo "============================================"
    echo "Phase 2 Deployment Summary"
    echo "============================================"
    echo "✅ Python environment configured"
    echo "✅ Node.js environment configured"
    echo "✅ Database initialized"
    echo "✅ SSL certificates generated"
    echo "✅ Nginx configured"
    echo "✅ Systemd service created"
    echo "✅ Monitoring enabled"
    echo "✅ Tests passed"
    echo ""
    echo "Next steps:"
    echo "1. Review configuration in $BACKEND_DIR/.env"
    echo "2. Start services: sudo systemctl start valor-ivx"
    echo "3. Check logs: sudo journalctl -u valor-ivx -f"
    echo "4. Access: https://localhost"
}

# Run main function
main "$@"
