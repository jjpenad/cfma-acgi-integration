#!/bin/bash

# Quick Production Setup Script for CFMA
# This script sets up the application for production use

echo "🚀 Setting up CFMA for production..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root"
    exit 1
fi

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/cfma
sudo chown $USER:$USER /opt/cfma

# Copy files to production directory
echo "📋 Copying application files..."
cp -r . /opt/cfma/
cd /opt/cfma

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create production environment file
echo "🔐 Creating production environment..."
cat > .env << EOF
FLASK_ENV=production
FLASK_APP=src.app:app
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:////opt/cfma/cfma.db
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=5000
DEBUG=False
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
PERMANENT_SESSION_LIFETIME=3600
EOF

# Set up systemd service
echo "⚙️ Setting up systemd service..."
sudo cp cfma.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cfma

# Set up Nginx
echo "🌐 Setting up Nginx..."
sudo cp nginx.conf /etc/nginx/conf.d/cfma.conf
sudo rm -f /etc/nginx/conf.d/default.conf
sudo nginx -t
sudo systemctl enable nginx

# Create log directory
echo "📝 Setting up logging..."
sudo mkdir -p /var/log/cfma
sudo chown $USER:$USER /var/log/cfma

# Initialize database
echo "🗄️ Initializing database..."
source venv/bin/activate
python3 -c "
from src.models import init_db, create_default_admin
init_db()
create_default_admin()
print('Database initialized successfully')
"

# Start services
echo "🚀 Starting services..."
sudo systemctl start cfma
sudo systemctl start nginx

# Check status
echo "📊 Checking service status..."
sleep 3
sudo systemctl status cfma --no-pager
sudo systemctl status nginx --no-pager

echo "✅ Production setup completed!"
echo "🌐 Application should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-instance-ip')"
echo "📋 Default login: admin / admin"
echo ""
echo "📊 Useful commands:"
echo "  sudo systemctl status cfma    # Check application status"
echo "  sudo journalctl -u cfma -f    # View application logs"
echo "  sudo systemctl restart cfma   # Restart application"
echo "  curl http://localhost/health  # Health check" 