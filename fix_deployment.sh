#!/bin/bash

# Fix CFMA Deployment Issues
echo "🔧 Fixing CFMA deployment issues..."

# Stop the broken service
echo "🛑 Stopping broken service..."
sudo systemctl stop cfma 2>/dev/null || true

# Remove the broken service file
echo "🗑️ Removing broken service file..."
sudo rm -f /etc/systemd/system/cfma.service

# Fix Nginx configuration
echo "🌐 Fixing Nginx configuration..."
if [ -d "/etc/nginx/sites-available" ]; then
    # Ubuntu/Debian style
    sudo tee /etc/nginx/sites-available/cfma > /dev/null <<EOF
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
}
EOF
    sudo ln -sf /etc/nginx/sites-available/cfma /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
else
    # CentOS/RHEL style
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
}
EOF
    sudo rm -f /etc/nginx/conf.d/default.conf
fi

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx

# Create correct systemd service
echo "⚙️ Creating correct systemd service..."
CURRENT_DIR=$(pwd)
sudo tee /etc/systemd/system/cfma.service > /dev/null <<EOF
[Unit]
Description=CFMA Application
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=src.app:app
ExecStart=$CURRENT_DIR/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 src.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Initialize database
echo "🗄️ Initializing database..."
source venv/bin/activate
python3 -c "
from src.models import init_db, create_default_admin
try:
    init_db()
    create_default_admin()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database already exists: {e}')
"

# Start the service
echo "🚀 Starting CFMA service..."
sudo systemctl daemon-reload
sudo systemctl enable cfma
sudo systemctl start cfma

# Check status
echo "📊 Checking services..."
sleep 3
echo "Nginx status:"
sudo systemctl status nginx --no-pager
echo ""
echo "CFMA status:"
sudo systemctl status cfma --no-pager

echo ""
echo "✅ Fix completed!"
echo "🌐 Application should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || hostname -I | awk '{print $1}')"
echo "📋 Default login: admin / admin" 