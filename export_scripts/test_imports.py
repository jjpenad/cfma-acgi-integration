#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import os
import sys

print("Testing imports...")

# Add current directory to Python path first (for local config)
sys.path.insert(0, os.path.dirname(__file__))

try:
    from config import ExportConfig
    print("✅ ExportConfig import successful")
except ImportError as e:
    print(f"❌ ExportConfig import failed: {e}")

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from services.acgi_client import ACGIClient
    print("✅ ACGIClient import successful")
except ImportError as e:
    print(f"❌ ACGIClient import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✅ dotenv import successful")
except ImportError as e:
    print(f"❌ dotenv import failed: {e}")

try:
    import requests
    print("✅ requests import successful")
except ImportError as e:
    print(f"❌ requests import failed: {e}")

print("\nTesting configuration...")
try:
    load_dotenv()
    errors = ExportConfig.validate()
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration validation passed")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")

print("\nAll tests completed!")
