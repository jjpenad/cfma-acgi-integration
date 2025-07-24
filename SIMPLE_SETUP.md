# Simple CFMA Setup Guide

This guide will help you set up CFMA to run with Nginx and keep it running automatically.

## Prerequisites

- Python 3.7+ installed
- pip installed
- sudo access

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Nginx (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install nginx

# OR for Amazon Linux/CentOS/RHEL
sudo yum update -y
sudo yum install nginx
```

## Step 2: Set Up the Application

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "
from src.models import init_db, create_default_admin
init_db()
create_default_admin()
print('Database initialized')
"
```

## Step 3: Set Up Nginx

Create Nginx configuration:

```bash
sudo tee /etc/nginx/sites-available/cfma << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

Enable the site:

```bash
# For Ubuntu/Debian
sudo ln -sf /etc/nginx/sites-available/cfma /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# For CentOS/RHEL
sudo cp /etc/nginx/sites-available/cfma /etc/nginx/conf.d/cfma.conf
sudo rm -f /etc/nginx/conf.d/default.conf

# Test and start Nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Step 4: Create Systemd Service

Create a service file to keep the app running:

```bash
sudo tee /etc/systemd/system/cfma.service << EOF
[Unit]
Description=CFMA Application
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=src.app:app
ExecStart=$(pwd)/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 120 src.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cfma
sudo systemctl start cfma
```

## Step 5: Verify Setup

```bash
# Check service status
sudo systemctl status cfma
sudo systemctl status nginx

# Check if app is running
curl http://localhost:5000/health

# Check Nginx proxy
curl http://localhost
```

## Step 6: Access the Application

- Open your browser to: `http://your-server-ip`
- Login with: `admin` / `admin`

## Useful Commands

```bash
# Start/Stop/Restart the application
sudo systemctl start cfma
sudo systemctl stop cfma
sudo systemctl restart cfma

# View logs
sudo journalctl -u cfma -f

# Check status
sudo systemctl status cfma

# Start/Stop Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
```

## Troubleshooting

### App won't start
```bash
# Check logs
sudo journalctl -u cfma -n 50

# Check if port is in use
sudo netstat -tlnp | grep :5000

# Test manually
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 src.app:app
```

### Nginx issues
```bash
# Check Nginx config
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Check Nginx status
sudo systemctl status nginx
```

### Permission issues
```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Fix permissions
chmod +x venv/bin/gunicorn
```

## Auto-restart on Reboot

The systemd service will automatically start the application when the server reboots. To verify:

```bash
# Check if service is enabled
sudo systemctl is-enabled cfma

# Test reboot (optional)
sudo reboot
```

After reboot, check if the app is running:
```bash
sudo systemctl status cfma
curl http://localhost/health
```

That's it! Your CFMA application should now be running with Nginx and will automatically restart if it crashes or when the server reboots. 