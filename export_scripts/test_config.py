#!/usr/bin/env python3
"""
Test script to verify .env configuration loading
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import config
sys.path.insert(0, os.path.dirname(__file__))

from config import ExportConfig

def test_config():
    """Test configuration loading"""
    print("Testing ACGI Contact Export Configuration")
    print("=" * 50)
    
    # Test environment variable loading
    print("Environment Variables:")
    print(f"  ACGI_USERNAME: {os.getenv('ACGI_USERNAME', 'Not set')}")
    print(f"  ACGI_PASSWORD: {'*' * len(os.getenv('ACGI_PASSWORD', '')) if os.getenv('ACGI_PASSWORD') else 'Not set'}")
    print(f"  ACGI_ENVIRONMENT: {os.getenv('ACGI_ENVIRONMENT', 'Not set')}")
    print()
    
    # Test configuration class
    print("Configuration Class Values:")
    print(f"  ACGI_USERNAME: {ExportConfig.ACGI_USERNAME}")
    print(f"  ACGI_PASSWORD: {'*' * len(ExportConfig.ACGI_PASSWORD) if ExportConfig.ACGI_PASSWORD else 'Not set'}")
    print(f"  ACGI_ENVIRONMENT: {ExportConfig.ACGI_ENVIRONMENT}")
    print(f"  START_CUSTOMER_ID: {ExportConfig.START_CUSTOMER_ID}")
    print(f"  END_CUSTOMER_ID: {ExportConfig.END_CUSTOMER_ID}")
    print(f"  BATCH_SIZE: {ExportConfig.BATCH_SIZE}")
    print(f"  REQUEST_TIMEOUT: {ExportConfig.REQUEST_TIMEOUT}")
    print(f"  REQUEST_DELAY: {ExportConfig.REQUEST_DELAY}")
    print(f"  OUTPUT_DIRECTORY: {ExportConfig.OUTPUT_DIRECTORY}")
    print(f"  INCLUDE_TIMESTAMP: {ExportConfig.INCLUDE_TIMESTAMP}")
    print(f"  LOG_LEVEL: {ExportConfig.LOG_LEVEL}")
    print(f"  LOG_FILE: {ExportConfig.LOG_FILE}")
    print()
    
    # Test validation
    print("Configuration Validation:")
    errors = ExportConfig.validate()
    if errors:
        print("  ❌ Configuration errors found:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✅ Configuration is valid")
    
    print()
    
    # Test credentials
    print("Credentials:")
    credentials = ExportConfig.get_credentials()
    print(f"  userid: {credentials['userid']}")
    print(f"  password: {'*' * len(credentials['password']) if credentials['password'] else 'Not set'}")
    print(f"  environment: {credentials['environment']}")

if __name__ == "__main__":
    test_config()
