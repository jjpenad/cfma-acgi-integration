# ACGI to HubSpot Integration

A Flask application that integrates ACGI's XML-based API with HubSpot, featuring a web interface for data synchronization and management.

## Features

- 🔐 **Secure Authentication**: Login system with configurable admin credentials
- 🔄 **ACGI Integration**: XML-based API client for ACGI data retrieval
- 📊 **HubSpot Integration**: Direct API integration for contact and deal management
- 🎛️ **Dynamic Field Mapping**: Configurable field mappings with drag-and-drop ordering
- 🔍 **Smart Contact Search**: Multiple search strategies (email, customer ID, or both)
- ⏰ **Scheduled Integration**: Background job scheduling for automated sync
- 🎨 **Modern UI**: Bootstrap-based responsive interface
- 🗄️ **Database Support**: In-memory, local SQLite, and PostgreSQL support

## Heroku Deployment

### Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI**: Install from [devcenter.heroku.com](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Ensure your code is in a Git repository

### Deployment Steps

#### 1. Prepare Your Application

```bash
# Ensure all files are committed to Git
git add .
git commit -m "Prepare for Heroku deployment"
```

#### 2. Create Heroku App

```bash
# Create a new Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini
```

#### 3. Configure Environment Variables

```bash
# Set required environment variables
heroku config:set SECRET_KEY="your-super-secret-key-change-this"
heroku config:set ADMIN_USERNAME="admin"
heroku config:set ADMIN_PASSWORD="your-secure-password"
heroku config:set DATABASE_TYPE="postgres"
heroku config:set DEBUG="false"
heroku config:set SESSION_COOKIE_SECURE="true"

# Optional: Set default credentials (can also be set via web interface)
heroku config:set HUBSPOT_API_KEY="your-hubspot-api-key"
heroku config:set ACGI_USERNAME="your-acgi-username"
heroku config:set ACGI_PASSWORD="your-acgi-password"
heroku config:set ACGI_ENVIRONMENT="test"
```

#### 4. Deploy to Heroku

```bash
# Deploy the application
git push heroku main

# Run database migrations
heroku run python -c "from src.models import init_db; init_db()"
```

#### 5. Verify Deployment

```bash
# Open the application
heroku open

# Check logs
heroku logs --tail
```

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Flask secret key for sessions | `your-secret-key-change-this-in-production` |
| `ADMIN_USERNAME` | Yes | Admin login username | `admin` |
| `ADMIN_PASSWORD` | Yes | Admin login password | `admin123` |
| `DATABASE_TYPE` | Yes | Database type: `in_memory`, `local`, `postgres` | `in_memory` |
| `DATABASE_URL` | Auto | PostgreSQL URL (set by Heroku, automatically converted from `postgres://` to `postgresql://`) | - |
| `DEBUG` | No | Enable debug mode | `false` |
| `SESSION_COOKIE_SECURE` | Yes | Secure cookies for HTTPS | `true` |
| `HUBSPOT_API_KEY` | No | HubSpot API key | - |
| `ACGI_USERNAME` | No | ACGI username | - |
| `ACGI_PASSWORD` | No | ACGI password | - |
| `ACGI_ENVIRONMENT` | No | ACGI environment: `test` or `prod` | `test` |

### Post-Deployment Setup

1. **Access the Application**: Visit your Heroku app URL
2. **Login**: Use the admin credentials you set in environment variables
3. **Configure Credentials**: Set up your ACGI and HubSpot credentials via the web interface
4. **Test Connections**: Use the test buttons to verify API connectivity
5. **Configure Field Mappings**: Set up your ACGI to HubSpot field mappings

### Troubleshooting

#### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check if PostgreSQL is provisioned
   heroku addons
   
   # Check database URL
   heroku config:get DATABASE_URL
   ```

2. **Build Failures**
   ```bash
   # Check build logs
   heroku logs --tail
   
   # Ensure all dependencies are in requirements.txt
   pip freeze > requirements.txt
   ```

3. **Runtime Errors**
   ```bash
   # Check application logs
   heroku logs --tail
   
   # Run the app locally to test
   python src/app.py
   ```

#### Performance Optimization

1. **Database Connection Pooling**: The app automatically uses PostgreSQL connection pooling on Heroku
2. **Static Files**: Consider using a CDN for static assets in production
3. **Caching**: Implement Redis caching for frequently accessed data

### Security Considerations

1. **Environment Variables**: Never commit sensitive data to Git
2. **HTTPS**: Heroku automatically provides SSL certificates
3. **Session Security**: Secure cookies are enabled by default
4. **API Keys**: Store all API keys as environment variables
5. **Database**: Use Heroku's managed PostgreSQL service

### Monitoring and Maintenance

```bash
# Monitor application performance
heroku ps

# Check application logs
heroku logs --tail

# Scale the application if needed
heroku ps:scale web=1

# Restart the application
heroku restart
```

## Local Development

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CFMA
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**

   **Option A: Development server (recommended for development)**
   ```bash
   python run_dev.py
   ```

   **Option B: Flexible startup script**
   ```bash
   python start.py --mode dev --debug
   ```

   **Option C: Direct Flask run**
   ```bash
   python src/app.py
   ```

   **Option D: Production mode with Gunicorn (local testing)**
   ```bash
   gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 2 --timeout 120
   ```

### Development Database Options

- **In-Memory** (default): `DATABASE_TYPE=in_memory`
- **Local SQLite**: `DATABASE_TYPE=local`
- **PostgreSQL**: `DATABASE_TYPE=postgres` (requires local PostgreSQL)

## API Documentation

### ACGI API Integration

The application integrates with ACGI's XML-based API:

- **Queue Management**: Retrieves customer updates from ACGI queue
- **Customer Data**: Fetches detailed customer information
- **Data Purge**: Removes processed records from queue

### HubSpot API Integration

Direct integration with HubSpot's REST API:

- **Contact Management**: Create, update, and search contacts
- **Deal Management**: Create and manage deals
- **Property Management**: Dynamic property fetching and mapping

## Architecture

```
CFMA/
├── src/
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration management
│   ├── models.py              # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py            # Authentication routes
│   │   ├── main.py            # Main application routes
│   │   ├── api.py             # API endpoints
│   │   └── pages.py           # Page routes
│   ├── services/
│   │   ├── acgi_client.py     # ACGI API client
│   │   ├── hubspot_client.py  # HubSpot API client
│   │   ├── data_mapper.py     # Data transformation
│   │   └── integration_service.py # Integration orchestration
│   ├── templates/             # HTML templates
│   └── utils.py               # Utility functions
├── wsgi.py                    # WSGI entry point for production
├── run_dev.py                 # Development server script
├── start.py                   # Flexible startup script
├── requirements.txt           # Python dependencies
├── Procfile                  # Heroku deployment configuration
├── env.example               # Environment variables template
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 