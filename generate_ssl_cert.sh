#!/bin/bash

# Valor IVX SSL Certificate Generation Script
# This script generates SSL certificates for development and production use

set -e  # Exit on any error

echo "🔐 Valor IVX SSL Certificate Generation"
echo "======================================="

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

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create SSL directory
SSL_DIR="ssl"
mkdir -p "$SSL_DIR"

# Function to generate self-signed certificate for development
generate_self_signed() {
    print_status "Generating self-signed certificate for development..."
    
    # Generate private key
    openssl genrsa -out "$SSL_DIR/valor-ivx-dev.key" 2048
    
    # Generate certificate signing request
    openssl req -new -key "$SSL_DIR/valor-ivx-dev.key" -out "$SSL_DIR/valor-ivx-dev.csr" -subj "/C=US/ST=State/L=City/O=Valor IVX/OU=Development/CN=localhost"
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 -in "$SSL_DIR/valor-ivx-dev.csr" -signkey "$SSL_DIR/valor-ivx-dev.key" -out "$SSL_DIR/valor-ivx-dev.crt"
    
    # Set proper permissions
    chmod 600 "$SSL_DIR/valor-ivx-dev.key"
    chmod 644 "$SSL_DIR/valor-ivx-dev.crt"
    
    # Clean up CSR
    rm "$SSL_DIR/valor-ivx-dev.csr"
    
    print_success "Self-signed certificate generated:"
    echo "  Certificate: $SSL_DIR/valor-ivx-dev.crt"
    echo "  Private Key: $SSL_DIR/valor-ivx-dev.key"
}

# Function to generate Let's Encrypt certificate
generate_lets_encrypt() {
    print_status "Setting up Let's Encrypt certificate..."
    
    DOMAIN=${1:-"valor-ivx.com"}
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        print_error "certbot is not installed. Please install it first:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install certbot"
        exit 1
    fi
    
    # Generate certificate
    sudo certbot certonly --standalone -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN
    
    # Copy certificates to SSL directory
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/valor-ivx-prod.crt"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/valor-ivx-prod.key"
    
    # Set proper permissions
    sudo chown $USER:$USER "$SSL_DIR/valor-ivx-prod.crt" "$SSL_DIR/valor-ivx-prod.key"
    chmod 644 "$SSL_DIR/valor-ivx-prod.crt"
    chmod 600 "$SSL_DIR/valor-ivx-prod.key"
    
    print_success "Let's Encrypt certificate generated:"
    echo "  Certificate: $SSL_DIR/valor-ivx-prod.crt"
    echo "  Private Key: $SSL_DIR/valor-ivx-prod.key"
    echo "  Domain: $DOMAIN"
    
    # Create renewal script
    cat > "$SSL_DIR/renew-cert.sh" <<EOF
#!/bin/bash
# Let's Encrypt certificate renewal script

sudo certbot renew --quiet
sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/valor-ivx-prod.crt"
sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/valor-ivx-prod.key"
sudo chown $USER:$USER "$SSL_DIR/valor-ivx-prod.crt" "$SSL_DIR/valor-ivx-prod.key"
sudo systemctl reload nginx
EOF
    
    chmod +x "$SSL_DIR/renew-cert.sh"
    
    print_status "Renewal script created: $SSL_DIR/renew-cert.sh"
    print_warning "Add this to your crontab for automatic renewal:"
    echo "  0 12 * * * $(pwd)/$SSL_DIR/renew-cert.sh"
}

# Function to generate wildcard certificate
generate_wildcard() {
    print_status "Setting up wildcard certificate..."
    
    DOMAIN=${1:-"valor-ivx.com"}
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        print_error "certbot is not installed. Please install it first:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install certbot"
        exit 1
    fi
    
    # Generate certificate with DNS challenge
    sudo certbot certonly --manual --preferred-challenges=dns -d "$DOMAIN" -d "*.$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN
    
    # Copy certificates to SSL directory
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/valor-ivx-wildcard.crt"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/valor-ivx-wildcard.key"
    
    # Set proper permissions
    sudo chown $USER:$USER "$SSL_DIR/valor-ivx-wildcard.crt" "$SSL_DIR/valor-ivx-wildcard.key"
    chmod 644 "$SSL_DIR/valor-ivx-wildcard.crt"
    chmod 600 "$SSL_DIR/valor-ivx-wildcard.key"
    
    print_success "Wildcard certificate generated:"
    echo "  Certificate: $SSL_DIR/valor-ivx-wildcard.crt"
    echo "  Private Key: $SSL_DIR/valor-ivx-wildcard.key"
    echo "  Domain: *.$DOMAIN"
}

# Function to update environment file
update_env_file() {
    local cert_type=$1
    local env_file="backend/.env"
    
    if [ -f "$env_file" ]; then
        print_status "Updating environment file with SSL paths..."
        
        # Backup original file
        cp "$env_file" "$env_file.backup"
        
        # Update SSL configuration
        sed -i "s|SSL_CERT_PATH=.*|SSL_CERT_PATH=$(pwd)/$SSL_DIR/valor-ivx-$cert_type.crt|" "$env_file"
        sed -i "s|SSL_KEY_PATH=.*|SSL_KEY_PATH=$(pwd)/$SSL_DIR/valor-ivx-$cert_type.key|" "$env_file"
        sed -i "s|SSL_ENABLED=.*|SSL_ENABLED=true|" "$env_file"
        
        print_success "Environment file updated"
    else
        print_warning "No .env file found. Please update manually:"
        echo "  SSL_CERT_PATH=$(pwd)/$SSL_DIR/valor-ivx-$cert_type.crt"
        echo "  SSL_KEY_PATH=$(pwd)/$SSL_DIR/valor-ivx-$cert_type.key"
        echo "  SSL_ENABLED=true"
    fi
}

# Main script logic
case "${1:-dev}" in
    "dev"|"development")
        generate_self_signed
        update_env_file "dev"
        print_success "Development SSL certificate setup complete!"
        echo ""
        echo "📋 Next Steps:"
        echo "=============="
        echo "• Update your .env file with the SSL paths above"
        echo "• Run the deployment script: ./deploy_production.sh"
        echo "• Access your application via HTTPS"
        echo ""
        print_warning "Note: Self-signed certificates will show browser warnings"
        ;;
    
    "prod"|"production")
        if [ -z "$2" ]; then
            print_error "Please provide a domain name for production certificate"
            echo "Usage: $0 production <domain>"
            echo "Example: $0 production valor-ivx.com"
            exit 1
        fi
        generate_lets_encrypt "$2"
        update_env_file "prod"
        print_success "Production SSL certificate setup complete!"
        echo ""
        echo "📋 Next Steps:"
        echo "=============="
        echo "• Ensure your domain points to this server"
        echo "• Run the deployment script: ./deploy_production.sh"
        echo "• Set up automatic renewal: crontab -e"
        echo "• Add: 0 12 * * * $(pwd)/$SSL_DIR/renew-cert.sh"
        ;;
    
    "wildcard")
        if [ -z "$2" ]; then
            print_error "Please provide a domain name for wildcard certificate"
            echo "Usage: $0 wildcard <domain>"
            echo "Example: $0 wildcard valor-ivx.com"
            exit 1
        fi
        generate_wildcard "$2"
        update_env_file "wildcard"
        print_success "Wildcard SSL certificate setup complete!"
        echo ""
        echo "📋 Next Steps:"
        echo "=============="
        echo "• Ensure your domain and subdomains point to this server"
        echo "• Run the deployment script: ./deploy_production.sh"
        echo "• Set up automatic renewal: crontab -e"
        echo "• Add: 0 12 * * * $(pwd)/$SSL_DIR/renew-cert.sh"
        ;;
    
    "check")
        print_status "Checking existing certificates..."
        
        if [ -f "$SSL_DIR/valor-ivx-dev.crt" ]; then
            echo "Development certificate found:"
            openssl x509 -in "$SSL_DIR/valor-ivx-dev.crt" -text -noout | grep -E "(Subject:|Not After)"
        fi
        
        if [ -f "$SSL_DIR/valor-ivx-prod.crt" ]; then
            echo "Production certificate found:"
            openssl x509 -in "$SSL_DIR/valor-ivx-prod.crt" -text -noout | grep -E "(Subject:|Not After)"
        fi
        
        if [ -f "$SSL_DIR/valor-ivx-wildcard.crt" ]; then
            echo "Wildcard certificate found:"
            openssl x509 -in "$SSL_DIR/valor-ivx-wildcard.crt" -text -noout | grep -E "(Subject:|Not After)"
        fi
        ;;
    
    *)
        echo "Usage: $0 {dev|prod|wildcard|check} [domain]"
        echo ""
        echo "Options:"
        echo "  dev, development    Generate self-signed certificate for development"
        echo "  prod, production    Generate Let's Encrypt certificate for production"
        echo "  wildcard           Generate wildcard certificate for subdomains"
        echo "  check              Check existing certificates"
        echo ""
        echo "Examples:"
        echo "  $0 dev                    # Development certificate"
        echo "  $0 production valor-ivx.com  # Production certificate"
        echo "  $0 wildcard valor-ivx.com    # Wildcard certificate"
        echo "  $0 check                  # Check existing certificates"
        exit 1
        ;;
esac 