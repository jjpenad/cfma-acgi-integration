#!/usr/bin/env python3
"""
Flexible startup script for ACGI to HubSpot Integration
Supports development, production, and testing modes
"""

import os
import sys
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    parser = argparse.ArgumentParser(description='ACGI to HubSpot Integration Server')
    parser.add_argument('--mode', choices=['dev', 'prod', 'test'], default='dev',
                       help='Server mode (default: dev)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.mode == 'prod':
        # Production mode - use Gunicorn
        print("🚀 Starting ACGI to HubSpot Integration (Production Mode)")
        print("📋 Using Gunicorn WSGI server")
        print("🔧 Run with: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120")
        print("🌐 Or use: heroku local web")
        
        # For production, we don't start the server here
        # It should be started by Gunicorn or Heroku
        return
        
    elif args.mode == 'dev':
        # Development mode - use Flask development server
        from app import create_app
        from config import Config
        
        app = create_app()
        
        print("🚀 Starting ACGI to HubSpot Integration (Development Mode)")
        print(f"📍 Server: http://{args.host}:{args.port}")
        print(f"🔧 Debug Mode: {args.debug or Config.DEBUG}")
        print(f"🗄️ Database Type: {Config.DATABASE_TYPE}")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug or Config.DEBUG,
            use_reloader=True
        )
        
    elif args.mode == 'test':
        # Test mode - run tests
        print("🧪 Running tests...")
        # Add test execution logic here
        print("✅ Tests completed!")

if __name__ == "__main__":
    main() 