# Heroku Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Application Structure
- [x] Flask application with proper app factory pattern
- [x] All dependencies listed in `requirements.txt`
- [x] `Procfile` configured for Heroku
- [x] Environment variables template (`env.example`)
- [x] Database models with PostgreSQL support
- [x] Authentication system implemented
- [x] All routes protected with login required

### 2. Dependencies
- [x] Flask 2.3.3
- [x] SQLAlchemy 2.0.21
- [x] requests 2.31.0
- [x] APScheduler 3.10.4
- [x] python-dotenv 1.0.0
- [x] Werkzeug 2.3.7
- [x] psycopg2-binary 2.9.7 (PostgreSQL adapter)
- [x] gunicorn 21.2.0 (WSGI server)

### 3. Configuration
- [x] Environment-based configuration
- [x] Database URL handling for Heroku PostgreSQL
- [x] Secure session configuration
- [x] Debug mode disabled for production
- [x] Secret key generation

### 4. Database
- [x] SQLAlchemy models defined
- [x] PostgreSQL connection support
- [x] Database initialization function
- [x] User model for authentication
- [x] AppState model for configuration storage
- [x] FormField model for dynamic field mapping
- [x] SearchPreference model for search strategies

### 5. Security
- [x] Login system implemented
- [x] Session management
- [x] CSRF protection
- [x] Secure cookie configuration
- [x] Environment variable usage for secrets
- [x] Input validation and sanitization

### 6. API Integration
- [x] ACGI client with XML API support
- [x] HubSpot client with REST API support
- [x] Error handling and logging
- [x] Credential testing functionality
- [x] Data mapping and transformation

## 🚀 Deployment Steps

### Step 1: Prepare Git Repository
```bash
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

### Step 2: Install Heroku CLI
- Download from: https://devcenter.heroku.com/articles/heroku-cli
- Login: `heroku login`

### Step 3: Create Heroku App
```bash
heroku create your-app-name
```

### Step 4: Add PostgreSQL
```bash
heroku addons:create heroku-postgresql:mini
```

### Step 5: Set Environment Variables
```bash
# Required variables
heroku config:set SECRET_KEY="your-super-secret-key-change-this"
heroku config:set ADMIN_USERNAME="admin"
heroku config:set ADMIN_PASSWORD="your-secure-password"
heroku config:set DATABASE_TYPE="postgres"
heroku config:set DEBUG="false"
heroku config:set SESSION_COOKIE_SECURE="true"

# Optional: Default API credentials
heroku config:set HUBSPOT_API_KEY="your-hubspot-api-key"
heroku config:set ACGI_USERNAME="your-acgi-username"
heroku config:set ACGI_PASSWORD="your-acgi-password"
heroku config:set ACGI_ENVIRONMENT="test"
```

### Step 6: Deploy Application
```bash
git push heroku main
```

### Step 7: Initialize Database
```bash
heroku run python -c "from src.models import init_db; init_db()"
```

### Step 8: Verify Deployment
```bash
heroku open
heroku logs --tail
```

## 🔧 Post-Deployment Configuration

### 1. Access the Application
- Visit: `https://your-app-name.herokuapp.com`
- Login with admin credentials

### 2. Configure API Credentials
- Navigate to the Integration page
- Enter ACGI credentials (username, password, environment)
- Enter HubSpot API key
- Test connections using the test buttons

### 3. Set Up Field Mappings
- Go to "ACGI to HubSpot" page
- Configure field mappings for contacts and deals
- Set important fields and their order
- Configure search preferences

### 4. Test Integration
- Use the "Test Both" button to verify connectivity
- Run a manual integration simulation
- Check logs for any errors

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check application status
heroku ps

# View application logs
heroku logs --tail

# Check database status
heroku pg:info
```

### Scaling (if needed)
```bash
# Scale to multiple dynos
heroku ps:scale web=2

# Check current scaling
heroku ps
```

### Updates and Maintenance
```bash
# Deploy updates
git push heroku main

# Restart application
heroku restart

# Run database migrations
heroku run python -c "from src.models import init_db; init_db()"
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check `requirements.txt` for all dependencies
   - Verify Python version compatibility
   - Check build logs: `heroku logs --tail`

2. **Database Connection Errors**
   - Verify PostgreSQL addon is provisioned
   - Check `DATABASE_URL` environment variable
   - Ensure `DATABASE_TYPE=postgres`

3. **Runtime Errors**
   - Check application logs
   - Verify environment variables are set
   - Test locally before deploying

4. **Authentication Issues**
   - Verify `SECRET_KEY` is set
   - Check admin credentials
   - Ensure secure cookies are configured

### Useful Commands
```bash
# View all environment variables
heroku config

# Check application status
heroku ps

# View recent logs
heroku logs --tail

# Run one-off commands
heroku run python -c "print('Hello World')"

# Access database
heroku pg:psql

# Restart application
heroku restart
```

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit secrets to Git
   - Use strong, unique secret keys
   - Rotate API keys regularly

2. **Database Security**
   - Use Heroku's managed PostgreSQL
   - Enable connection pooling
   - Regular backups

3. **Application Security**
   - HTTPS enabled by default
   - Secure session cookies
   - Input validation and sanitization
   - Rate limiting (consider adding)

4. **Monitoring**
   - Set up log monitoring
   - Configure alerts for errors
   - Regular security audits

## 📈 Performance Optimization

1. **Database**
   - Use connection pooling
   - Optimize queries
   - Regular maintenance

2. **Application**
   - Enable caching where appropriate
   - Optimize static file serving
   - Monitor memory usage

3. **Scaling**
   - Start with hobby dyno
   - Scale based on usage
   - Monitor performance metrics

## ✅ Final Verification

Before going live:
- [ ] All tests pass
- [ ] Credentials are configured
- [ ] Field mappings are set up
- [ ] Integration is working
- [ ] Logs are clean
- [ ] Performance is acceptable
- [ ] Security measures are in place
- [ ] Monitoring is configured
- [ ] Backup strategy is in place

---

**Your application is now ready for Heroku deployment! 🎉** 