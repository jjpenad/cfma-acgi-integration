import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # Authentication Configuration
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Database Configuration
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'in_memory').lower()
    
    # Heroku PostgreSQL
    USE_POSTGRES = DATABASE_TYPE == 'postgres'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Local SQLite
    USE_LOCAL_DB = DATABASE_TYPE == 'local'
    LOCAL_DATABASE_URL = os.environ.get('LOCAL_DATABASE_URL') or 'sqlite:///local_app.db'
    
    # In-Memory SQLite (default)
    IN_MEMORY_DATABASE_URL = 'sqlite:///:memory:'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Application Configuration
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # HubSpot Configuration
    HUBSPOT_API_KEY = os.environ.get('HUBSPOT_API_KEY', '')
    
    # ACGI Configuration
    ACGI_API_URL = os.environ.get('ACGI_API_URL', '')
    ACGI_USERNAME = os.environ.get('ACGI_USERNAME', '')
    ACGI_PASSWORD = os.environ.get('ACGI_PASSWORD', '')
    
    # Integration settings
    INTEGRATION_INTERVAL_MINUTES = int(os.getenv('INTEGRATION_INTERVAL_MINUTES', 10)) 