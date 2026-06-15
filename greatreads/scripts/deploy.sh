#!/bin/bash

# GreatReads Deployment Script
# This script sets up the GreatReads application for production deployment

set -e  # Exit on any error

echo "🚀 Starting GreatReads deployment..."

# Configuration
PROJECT_DIR="/home/brandon/projects/GreatReads"
SERVICE_NAME="greatreads"
NGINX_CONF_SOURCE="$PROJECT_DIR/config/nginx/greatreads.conf"
SYSTEMD_SERVICE_SOURCE="$PROJECT_DIR/config/systemd/greatreads.service"
NGINX_SITES_DIR="/etc/nginx/sites-available"
SYSTEMD_DIR="/etc/systemd/system"

# Check if running as root for system configuration
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root - will configure system services"
    SUDO=""
else
    echo "📝 Running as user - will use sudo for system configuration"
    SUDO="sudo"
fi

# Step 1: Create virtual environment and install dependencies
echo "📦 Setting up Python environment..."
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
fi

source venv/bin/activate
pip install -e .
echo "✅ Installed dependencies"

# Step 2: Migrate data from original reading tracker
echo "📚 Migrating data..."
if [ ! -f "greatreads.db" ]; then
    python scripts/migrate_data.py
    echo "✅ Data migration completed"
else
    echo "⚠️  Database already exists, skipping migration"
fi

# Step 3: Test the application
echo "🧪 Testing application..."
python -c "
import sys
sys.path.insert(0, 'src')
from greatreads.main import app
from greatreads.database import create_tables
create_tables()
print('✅ Application test passed')
"

# Step 4: Configure systemd service
echo "⚙️  Configuring systemd service..."
$SUDO cp "$SYSTEMD_SERVICE_SOURCE" "$SYSTEMD_DIR/$SERVICE_NAME.service"
$SUDO systemctl daemon-reload
$SUDO systemctl enable "$SERVICE_NAME"
echo "✅ Systemd service configured"

# Step 5: Configure nginx
echo "🌐 Configuring nginx..."
if [ -f "$NGINX_CONF_SOURCE" ]; then
    echo "📋 Nginx configuration found. Please manually add the following to your nginx configuration:"
    echo ""
    cat "$NGINX_CONF_SOURCE"
    echo ""
    echo "💡 Add this to your main nginx server block for forge-freedom.com"
else
    echo "⚠️  Nginx configuration file not found"
fi

# Step 6: Start the service
echo "🔄 Starting GreatReads service..."
$SUDO systemctl start "$SERVICE_NAME"
$SUDO systemctl status "$SERVICE_NAME" --no-pager -l

# Step 7: Test the deployment
echo "🧪 Testing deployment..."
sleep 3  # Give the service time to start

if curl -f http://127.0.0.1:8002/health > /dev/null 2>&1; then
    echo "✅ Service is responding on port 8002"
else
    echo "❌ Service is not responding. Check the logs:"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
    exit 1
fi

# Step 8: Display final instructions
echo ""
echo "🎉 GreatReads deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Add the nginx configuration to your main server block"
echo "2. Reload nginx: sudo systemctl reload nginx"
echo "3. Access the application at: https://forge-freedom.com/greatreads/"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "   Restart service: sudo systemctl restart $SERVICE_NAME"
echo "   Stop service: sudo systemctl stop $SERVICE_NAME"
echo "   Check status: sudo systemctl status $SERVICE_NAME"
echo ""
echo "📊 Local development:"
echo "   Run locally: python scripts/server.py"
echo "   Access locally: http://localhost:8000"
echo ""

deactivate
