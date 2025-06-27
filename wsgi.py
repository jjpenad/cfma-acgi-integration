#!/usr/bin/env python3
"""
WSGI entry point for ACGI to HubSpot Integration
This file is used by production WSGI servers like Gunicorn
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    # For local development
    app.run(debug=True) 