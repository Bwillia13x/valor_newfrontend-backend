#!/bin/bash

# Valor IVX Production Deployment Script
# This script sets up a production environment with SSL/HTTPS support

set -e  # Exit on any error

echo "🚀 Valor IVX Production Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Starting production deployment..."

# 1. Environment Setup
print_status "Setting up environment..."

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.production" ]; then
        print_warning "No .env file found. Copying from .env.production template..."
        cp backend/.env.production backend/.env
        print_warning "Please edit backend/.env with your actual production values"
        print_warning "Then run this script again"
        exit 1
    else
        print_error "No .env or .env.production file found"
        exit 1
    fi
fi

# Load environment variables
source backend/.env

# 2. Security Validation
print_status "Validating security configuration..."

# Check required environment variables
required_vars=("SECRET_KEY" "JWT_SECRET_KEY" "DATABASE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

# Check if SECRET_KEY is not the default value
if [[ "$SECRET_KEY" == *"change-this-in-production"* ]]; then
    print_error "SECRET_KEY is still set to default value. Please change it in .env"
    exit 1
fi

if [[ "$JWT_SECRET_KEY" == *"change-this-in-production"* ]]; then
    print_error "JWT_SECRET_KEY is still set to default value. Please change it in .env"
    exit 1
fi

# Check SSL configuration if enabled
if [[ "$SSL_ENABLED" == "true" ]]; then
    print_status "SSL is enabled, checking certificate paths..."
    
    if [ -z "$SSL_CERT_PATH" ] || [ -z "$SSL_KEY_PATH" ]; then
        print_error "SSL is enabled but SSL_CERT_PATH or SSL_KEY_PATH not set"
        exit 1
    fi
    
    if [ ! -f "$SSL_CERT_PATH" ]; then
        print_error "SSL certificate file not found: $SSL_CERT_PATH"
        exit 1
    fi
    
    if [ ! -f "$SSL_KEY_PATH" ]; then
        print_error "SSL private key file not found: $SSL_KEY_PATH"
        exit 1
    fi
    
    print_success "SSL certificate and key files found"
fi

# 3. System Dependencies
print_status "Checking system dependencies..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

print_success "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    print_status "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source backend/venv/bin/activate

# Install/upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# 4. Database Setup
print_status "Setting up database..."

# Check if database URL is PostgreSQL
if [[ "$DATABASE_URL" == postgresql://* ]]; then
    print_status "PostgreSQL database detected"
    
    # Extract database connection info
    db_host=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
    db_port=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    db_name=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    db_user=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    
    # Check if PostgreSQL is accessible
    if ! command -v psql &> /dev/null; then
        print_warning "psql not found. Please ensure PostgreSQL client is installed"
    else
        # Test database connection
        if PGPASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\([^@]*\)@.*/\1/p') psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -c "SELECT 1;" &> /dev/null; then
            print_success "Database connection successful"
        else
            print_error "Cannot connect to database. Please check your DATABASE_URL"
            exit 1
        fi
    fi
else
    print_status "Using SQLite database"
fi

# Initialize database
print_status "Initializing database..."
cd backend
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"
cd ..

# 5. SSL Certificate Setup (if enabled)
if [[ "$SSL_ENABLED" == "true" ]]; then
    print_status "Setting up SSL configuration..."
    
    # Check certificate permissions
    if [ "$(stat -c %a $SSL_CERT_PATH)" != "644" ]; then
        print_warning "SSL certificate permissions should be 644"
        sudo chmod 644 "$SSL_CERT_PATH"
    fi
    
    if [ "$(stat -c %a $SSL_KEY_PATH)" != "600" ]; then
        print_warning "SSL private key permissions should be 600"
        sudo chmod 600 "$SSL_KEY_PATH"
    fi
    
    print_success "SSL configuration validated"
fi

# 6. Create macOS LaunchAgent
print_status "Creating macOS LaunchAgent..."

# Create launchd plist file
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/valor-ivx.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>valor-ivx</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>\$(pwd)/backend/venv/bin/gunicorn --bind 0.0.0.0:5002 --workers $WORKER_PROCESSES --timeout $WORKER_TIMEOUT --max-requests $WORKER_MAX_REQUESTS app:app</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>\$(pwd)/backend</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>FLASK_ENV</key>
        <string>production</string>
        <key>SECRET_KEY</key>
        <string>\$SECRET_KEY</string>
        <key>JWT_SECRET_KEY</key>
        <string>\$JWT_SECRET_KEY</string>
        <key>DATABASE_URL</key>
        <string>\$DATABASE_URL</string>
        <key>REDIS_URL</key>
        <string>\$REDIS_URL</string>
        <key>SSL_CERT_PATH</key>
        <string>\$SSL_CERT_PATH</string>
        <key>SSL_KEY_PATH</key>
        <string>\$SSL_KEY_PATH</string>
        <key>MAIL_SERVER</key>
        <string>\$MAIL_SERVER</string>
        <key>MAIL_PORT</key>
        <string>\$MAIL_PORT</string>
        <key>MAIL_USE_TLS</key>
        <string>\$MAIL_USE_TLS</string>
        <key>MAIL_USERNAME</key>
        <string>\$MAIL_USERNAME</string>
        <key>MAIL_PASSWORD</key>
        <string>\$MAIL_PASSWORD</string>
    </dict>
    
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/valor-ivx.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/valor-ivx.stderr.log</string>
</dict>
</plist>
EOF

# Load and start service
launchctl load ~/Library/LaunchAgents/valor-ivx.plist
launchctl start valor-ivx

print_success "LaunchAgent created and started"

# 7. Nginx Configuration (if SSL enabled)
if [[ "$SSL_ENABLED" == "true" ]]; then
    print_status "Creating Nginx configuration..."
    
    # Create Nginx config
    sudo tee /etc/nginx/sites-available/valor-ivx > /dev/null <<EOF
server {
    listen 80;
    server_name valor-ivx.com www.valor-ivx.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name valor-ivx.com www.valor-ivx.com;
    
    # SSL Configuration
    ssl_certificate $SSL_CERT_PATH;
    ssl_certificate_key $SSL_KEY_PATH;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Frontend (static files)
    location / {
        root $(pwd);
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5002/api/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/valor-ivx /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    if sudo nginx -t; then
        print_success "Nginx configuration is valid"
        sudo systemctl reload nginx
    else
        print_error "Nginx configuration is invalid"
        exit 1
    fi
else
    print_status "SSL not enabled, skipping Nginx configuration"
fi

# 8. Firewall Configuration
print_status "Configuring firewall..."

# Check if ufw is available
if command -v ufw &> /dev/null; then
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP/HTTPS
    if [[ "$SSL_ENABLED" == "true" ]]; then
        sudo ufw allow 443/tcp
    else
        sudo ufw allow 80/tcp
    fi
    
    # Enable firewall
    sudo ufw --force enable
    
    print_success "Firewall configured"
else
    print_warning "ufw not found, skipping firewall configuration"
fi

# 9. Logging Setup
print_status "Setting up logging..."

# Create logs directory
mkdir -p backend/logs

# Set proper permissions
chmod 755 backend/logs

print_success "Logging directory created"

# 10. Start Services
print_status "Starting services..."

# Start the application via launchd
launchctl load ~/Library/LaunchAgents/valor-ivx.plist
launchctl start valor-ivx

# Verify service is running
if launchctl list | grep -q 'valor-ivx'; then
    print_success "Valor IVX service is running"
else
    print_error "Failed to start Valor IVX service"
    exit 1
fi

# 11. Health Check
print_status "Performing health check..."

# Wait a moment for the service to fully start
sleep 5

# Check if the service is responding
if curl -f -s http://localhost:5002/api/health > /dev/null; then
    print_success "Health check passed"
else
    print_error "Health check failed"
    exit 1
fi

# 12. Final Status
print_success "Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "======================"
    echo "• Service: valor-ivx"
echo "• Backend URL: http://localhost:5002"
if [[ "$SSL_ENABLED" == "true" ]]; then
    echo "• Frontend URL: https://valor-ivx.com"
    echo "• SSL: Enabled"
else
    echo "• Frontend URL: http://valor-ivx.com"
    echo "• SSL: Disabled"
fi
echo "• Database: $DATABASE_URL"
echo "• Logs: $(pwd)/backend/logs/"
echo ""
echo "🔧 Useful Commands:"
echo "==================="
    echo "• Check service status: launchctl list | grep valor-ivx"
    echo "• View logs: cat /Users/$USER/valor-ivx.stderr.log"
    echo "• Restart service: launchctl stop valor-ivx && launchctl start valor-ivx"
    echo "• Stop service: launchctl stop valor-ivx"
echo ""
echo "🔒 Security Notes:"
echo "=================="
echo "• Ensure your .env file has secure values"
echo "• Regularly update SSL certificates"
echo "• Monitor logs for security issues"
echo "• Keep system packages updated"
echo ""
print_success "Valor IVX is now running in production mode!"
