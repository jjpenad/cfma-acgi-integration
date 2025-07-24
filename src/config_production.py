import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration for EC2 deployment"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    DEBUG = False
    TESTING = False
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:////opt/cfma/cfma.db'
    
    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Gunicorn settings
    GUNICORN_WORKERS = 4
    GUNICORN_TIMEOUT = 120
    GUNICORN_BIND = '0.0.0.0:5000'
    
    # Application specific settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    } 