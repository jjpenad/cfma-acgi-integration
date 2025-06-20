#!/usr/bin/env python3
"""
Development server for ACGI to HubSpot Integration
This script runs the Flask development server with debug mode enabled
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from config import Config

def run_dev_server():
    """Run the Flask development server"""
    app = create_app()
    
    print("🚀 Starting ACGI to HubSpot Integration (Development Mode)")
    print(f"📍 Server: http://{Config.HOST}:{Config.PORT}")
    print(f"🔧 Debug Mode: {Config.DEBUG}")
    print(f"🗄️ Database Type: {Config.DATABASE_TYPE}")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=True,  # Always enable debug for development
        use_reloader=True
    )

if __name__ == "__main__":
    run_dev_server() 