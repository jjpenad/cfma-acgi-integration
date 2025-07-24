#!/bin/bash

# CFMA Production Deployment Script for EC2
# This script sets up the application to run as a production service

set -e  # Exit on any error

echo "🚀 Starting CFMA Production Deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo yum update -y

# Install required system dependencies
echo "🔧 Installing system dependencies..."
sudo yum install -y python3 python3-pip python3-devel gcc git nginx

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/cfma
sudo chown ec2-user:ec2-user /opt/cfma

# Clone or copy application files
echo "📋 Copying application files..."
# If using git:
# git clone https://github.com/your-repo/cfma.git /opt/cfma
# Or copy files manually to /opt/cfma

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /opt/cfma
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
echo "🔐 Setting up environment variables..."
sudo tee /opt/cfma/.env > /dev/null <<EOF
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

# Create systemd service file
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/cfma.service > /dev/null <<EOF
[Unit]
Description=CFMA Application
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/cfma
Environment=PATH=/opt/cfma/venv/bin
ExecStart=/opt/cfma/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 src.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx configuration
echo "🌐 Setting up Nginx..."
sudo tee /etc/nginx/conf.d/cfma.conf > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if any)
    location /static {
        alias /opt/cfma/static;
        expires 30d;
    }
}
EOF

# Remove default nginx site
sudo rm -f /etc/nginx/conf.d/default.conf

# Test nginx configuration
sudo nginx -t

# Start and enable services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable cfma
sudo systemctl start cfma
sudo systemctl enable nginx
sudo systemctl start nginx

# Set up firewall (if using security groups, this may not be needed)
echo "🔥 Configuring firewall..."
sudo yum install -y firewalld
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Create log directory
echo "📝 Setting up logging..."
sudo mkdir -p /var/log/cfma
sudo chown ec2-user:ec2-user /var/log/cfma

# Initialize database
echo "🗄️ Initializing database..."
cd /opt/cfma
source venv/bin/activate
python3 -c "
from src.models import init_db, create_default_admin
init_db()
create_default_admin()
print('Database initialized successfully')
"

echo "✅ Deployment completed successfully!"
echo "🌐 Application should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "📊 Check service status with: sudo systemctl status cfma"
echo "📋 View logs with: sudo journalctl -u cfma -f" 