import os
import logging
from flask import Flask
from config import Config
from models import init_db
from routes.auth import auth_bp
from routes.main import main_bp, init_routes
from routes.api import init_api_routes
from routes.pages import init_page_routes

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
    app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT
    )
    
    # Initialize database
    init_db()
    
    # Initialize scheduler service
    try:
        from services.scheduler_service import scheduler_service
        scheduler_service.start()
        logging.info("Scheduler service started successfully")
    except Exception as e:
        logging.error(f"Error starting scheduler service: {str(e)}")
        # Don't fail the app startup, just log the error
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # Initialize routes
    init_routes(app)
    init_api_routes(app)
    
    return app

# Create the app instance for WSGI servers
app = create_app()

if __name__ == '__main__':
    # This is for direct execution (development)
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    ) 