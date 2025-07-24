#!/bin/bash

# Simple CFMA Deployment Script
# Just sets up Nginx and keeps the app running

echo "🚀 Simple CFMA Deployment..."

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    if command -v yum &> /dev/null; then
        # Amazon Linux / CentOS / RHEL
        sudo yum update -y
        sudo yum install -y nginx
    elif command -v apt-get &> /dev/null; then
        # Ubuntu / Debian
        sudo apt-get update
        sudo apt-get install -y nginx
    else
        echo "❌ Unsupported package manager. Please install Nginx manually."
        exit 1
    fi
fi

# Create Nginx configuration
echo "🌐 Setting up Nginx configuration..."
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

# Enable the site
if [ -d "/etc/nginx/sites-enabled" ]; then
    # Ubuntu/Debian style
    sudo ln -sf /etc/nginx/sites-available/cfma /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
else
    # CentOS/RHEL style
    sudo rm -f /etc/nginx/conf.d/default.conf
    sudo cp /etc/nginx/sites-available/cfma /etc/nginx/conf.d/cfma.conf
fi

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Start Nginx
echo "🚀 Starting Nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

# Create a simple startup script
echo "📝 Creating startup script..."
cat > start_app.sh <<EOF
#!/bin/bash
cd \$(dirname "\$0")
source venv/bin/activate
export FLASK_ENV=production
export FLASK_APP=src.app:app
python3 -c "
from src.models import init_db, create_default_admin
try:
    init_db()
    create_default_admin()
    print('Database ready')
except Exception as e:
    print(f'Database already exists: {e}')
"
gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 src.app:app
EOF

chmod +x start_app.sh

# Create a systemd service for the app
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/cfma.service > /dev/null <<EOF
[Unit]
Description=CFMA Application
After=network.target

[Service]
Type=simple
User=\$USER
Group=\$USER
WorkingDirectory=\$(pwd)
Environment=PATH=\$(pwd)/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=src.app:app
ExecStart=\$(pwd)/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 src.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
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
echo "✅ Simple deployment completed!"
echo "🌐 Application should be available at: http://\$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || hostname -I | awk '{print \$1}')"
echo "📋 Default login: admin / admin"
echo ""
echo "📊 Useful commands:"
echo "  sudo systemctl status cfma    # Check app status"
echo "  sudo systemctl restart cfma   # Restart app"
echo "  sudo systemctl status nginx   # Check nginx status"
echo "  sudo journalctl -u cfma -f    # View app logs" 