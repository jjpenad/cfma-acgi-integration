#!/bin/bash

# ACGI to HubSpot Integration - Heroku Deployment Script

echo "🚀 Starting Heroku deployment..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if we're in a Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a Git repository. Please initialize Git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Get app name from user
read -p "Enter your Heroku app name (or press Enter to create a new one): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "Creating new Heroku app..."
    heroku create
    APP_NAME=$(heroku apps:info --json | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    echo "Created app: $APP_NAME"
else
    echo "Using existing app: $APP_NAME"
    heroku git:remote -a $APP_NAME
fi

# Add PostgreSQL addon
echo "📦 Adding PostgreSQL addon..."
heroku addons:create heroku-postgresql:mini

# Set environment variables
echo "🔧 Setting environment variables..."
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
heroku config:set DATABASE_TYPE="postgres"
heroku config:set DEBUG="false"
heroku config:set SESSION_COOKIE_SECURE="true"

# Prompt for admin credentials
read -p "Enter admin username (default: admin): " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "Enter admin password: " ADMIN_PASSWORD
echo
read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
echo

if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
    echo "❌ Passwords don't match!"
    exit 1
fi

heroku config:set ADMIN_USERNAME="$ADMIN_USERNAME"
heroku config:set ADMIN_PASSWORD="$ADMIN_PASSWORD"

# Optional: Set default API credentials
read -p "Do you want to set default API credentials? (y/n): " SET_CREDENTIALS

if [ "$SET_CREDENTIALS" = "y" ] || [ "$SET_CREDENTIALS" = "Y" ]; then
    read -p "Enter HubSpot API key (optional): " HUBSPOT_API_KEY
    if [ ! -z "$HUBSPOT_API_KEY" ]; then
        heroku config:set HUBSPOT_API_KEY="$HUBSPOT_API_KEY"
    fi
    
    read -p "Enter ACGI username (optional): " ACGI_USERNAME
    if [ ! -z "$ACGI_USERNAME" ]; then
        heroku config:set ACGI_USERNAME="$ACGI_USERNAME"
    fi
    
    read -s -p "Enter ACGI password (optional): " ACGI_PASSWORD
    echo
    if [ ! -z "$ACGI_PASSWORD" ]; then
        heroku config:set ACGI_PASSWORD="$ACGI_PASSWORD"
    fi
    
    read -p "Enter ACGI environment (test/prod, default: test): " ACGI_ENVIRONMENT
    ACGI_ENVIRONMENT=${ACGI_ENVIRONMENT:-test}
    heroku config:set ACGI_ENVIRONMENT="$ACGI_ENVIRONMENT"
fi

# Deploy to Heroku
echo "📤 Deploying to Heroku..."
git add .
git commit -m "Deploy to Heroku" || git commit -m "Update for Heroku deployment"
git push heroku main

# Run database migrations
echo "🗄️ Setting up database..."
heroku run python -c "from src.models import init_db; init_db()"

# Open the application
echo "🌐 Opening application..."
heroku open

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Visit your app at: https://$APP_NAME.herokuapp.com"
echo "2. Login with username: $ADMIN_USERNAME"
echo "3. Configure your API credentials via the web interface"
echo "4. Test your connections using the test buttons"
echo ""
echo "🔧 Useful commands:"
echo "  heroku logs --tail          # View application logs"
echo "  heroku config               # View environment variables"
echo "  heroku restart              # Restart the application"
echo "  heroku ps                   # Check application status" 