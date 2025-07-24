# CFMA EC2 Production Deployment Guide

This guide will help you deploy the CFMA application to an EC2 instance for production use.

## Prerequisites

- AWS EC2 instance (Amazon Linux 2 recommended)
- SSH access to the instance
- Domain name (optional, for HTTPS)

## Step 1: Launch EC2 Instance

1. **Launch Instance:**
   - AMI: Amazon Linux 2
   - Instance Type: t3.medium or larger
   - Storage: 20GB minimum
   - Security Group: Allow HTTP (80), HTTPS (443), SSH (22)

2. **Security Group Configuration:**
   ```
   HTTP (80)     - 0.0.0.0/0
   HTTPS (443)   - 0.0.0.0/0 (if using SSL)
   SSH (22)      - Your IP
   ```

## Step 2: Connect to Instance

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

## Step 3: Deploy Application

### Option A: Using the Deployment Script

1. **Upload files to EC2:**
   ```bash
   scp -i your-key.pem -r . ec2-user@your-instance-ip:/tmp/cfma
   ```

2. **Run deployment script:**
   ```bash
   ssh -i your-key.pem ec2-user@your-instance-ip
   cd /tmp/cfma
   chmod +x deploy.sh
   ./deploy.sh
   ```

### Option B: Manual Deployment

1. **Update system:**
   ```bash
   sudo yum update -y
   sudo yum install -y python3 python3-pip python3-devel gcc git nginx
   ```

2. **Create application directory:**
   ```bash
   sudo mkdir -p /opt/cfma
   sudo chown ec2-user:ec2-user /opt/cfma
   ```

3. **Copy application files:**
   ```bash
   cp -r /tmp/cfma/* /opt/cfma/
   cd /opt/cfma
   ```

4. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
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
   ```

6. **Set up systemd service:**
   ```bash
   sudo cp cfma.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable cfma
   ```

7. **Set up Nginx:**
   ```bash
   sudo cp nginx.conf /etc/nginx/conf.d/cfma.conf
   sudo rm -f /etc/nginx/conf.d/default.conf
   sudo nginx -t
   sudo systemctl enable nginx
   ```

8. **Start services:**
   ```bash
   sudo systemctl start cfma
   sudo systemctl start nginx
   ```

## Step 4: Initialize Database

```bash
cd /opt/cfma
source venv/bin/activate
python3 -c "
from src.models import init_db, create_default_admin
init_db()
create_default_admin()
print('Database initialized successfully')
"
```

## Step 5: Configure Firewall

```bash
sudo yum install -y firewalld
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Step 6: Verify Deployment

1. **Check service status:**
   ```bash
   sudo systemctl status cfma
   sudo systemctl status nginx
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u cfma -f
   sudo tail -f /var/log/nginx/cfma_access.log
   ```

3. **Test health endpoint:**
   ```bash
   curl http://localhost/health
   ```

4. **Access application:**
   - Open browser: `http://your-instance-ip`
   - Default login: `admin` / `admin`

## Step 7: SSL/HTTPS Setup (Optional)

1. **Install Certbot:**
   ```bash
   sudo yum install -y certbot python3-certbot-nginx
   ```

2. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Update environment:**
   ```bash
   # Edit .env file
   SESSION_COOKIE_SECURE=True
   ```

## Step 8: Monitoring and Maintenance

### Service Management

```bash
# Start service
sudo systemctl start cfma

# Stop service
sudo systemctl stop cfma

# Restart service
sudo systemctl restart cfma

# Check status
sudo systemctl status cfma

# View logs
sudo journalctl -u cfma -f
```

### Application Updates

1. **Backup database:**
   ```bash
   cp /opt/cfma/cfma.db /opt/cfma/cfma.db.backup.$(date +%Y%m%d)
   ```

2. **Update code:**
   ```bash
   cd /opt/cfma
   git pull  # if using git
   # or copy new files manually
   ```

3. **Update dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Restart service:**
   ```bash
   sudo systemctl restart cfma
   ```

### Log Management

```bash
# Application logs
sudo journalctl -u cfma --since "1 hour ago"

# Nginx logs
sudo tail -f /var/log/nginx/cfma_access.log
sudo tail -f /var/log/nginx/cfma_error.log

# Application-specific logs
tail -f /opt/cfma/app.log
```

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo systemctl status cfma
   sudo journalctl -u cfma -n 50
   ```

2. **Permission issues:**
   ```bash
   sudo chown -R ec2-user:ec2-user /opt/cfma
   sudo chmod +x /opt/cfma/venv/bin/gunicorn
   ```

3. **Port conflicts:**
   ```bash
   sudo netstat -tlnp | grep :5000
   sudo lsof -i :5000
   ```

4. **Database issues:**
   ```bash
   cd /opt/cfma
   source venv/bin/activate
   python3 -c "from src.models import init_db; init_db()"
   ```

### Performance Tuning

1. **Adjust Gunicorn workers:**
   ```bash
   # Edit /etc/systemd/system/cfma.service
   # Change --workers 4 to --workers 2 for smaller instances
   sudo systemctl daemon-reload
   sudo systemctl restart cfma
   ```

2. **Monitor resource usage:**
   ```bash
   htop
   df -h
   free -h
   ```

## Security Considerations

1. **Regular updates:**
   ```bash
   sudo yum update -y
   ```

2. **Firewall rules:**
   - Only allow necessary ports
   - Restrict SSH access to specific IPs

3. **File permissions:**
   ```bash
   sudo chmod 600 /opt/cfma/.env
   sudo chmod 600 /opt/cfma/cfma.db
   ```

4. **Backup strategy:**
   - Regular database backups
   - Configuration backups
   - Code backups

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u cfma -f`
2. Check health endpoint: `curl http://localhost/health`
3. Verify configuration files
4. Check system resources

## Next Steps

1. Configure your API credentials via the web interface
2. Set up scheduling configuration
3. Test the integration
4. Monitor the application logs
5. Set up automated backups
6. Configure monitoring and alerting 