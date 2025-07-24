#!/usr/bin/env python3

"""Simple test script to check if the CFMA app can start properly"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        print("  Testing wsgi...")
        from wsgi import app
        print("  ✅ wsgi imported successfully")
    except Exception as e:
        print(f"  ❌ wsgi import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        print("  Testing src.models...")
        from src.models import init_db, create_default_admin
        print("  ✅ src.models imported successfully")
    except Exception as e:
        print(f"  ❌ src.models import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        print("  Testing src.services.scheduler_service...")
        from src.services.scheduler_service import scheduler_service
        print("  ✅ scheduler_service imported successfully")
    except Exception as e:
        print(f"  ❌ scheduler_service import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_database():
    """Test database initialization"""
    print("🗄️ Testing database...")
    
    try:
        from src.models import init_db, create_default_admin
        init_db()
        print("  ✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"  ❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test if the Flask app can be created"""
    print("🚀 Testing app creation...")
    
    try:
        from wsgi import app
        print("  ✅ Flask app created successfully")
        print(f"  📋 App name: {app.name}")
        print(f"  📋 App config: {app.config.get('ENV', 'unknown')}")
        return True
    except Exception as e:
        print(f"  ❌ Flask app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 CFMA App Test Suite")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return 1
    
    # Test database
    if not test_database():
        print("❌ Database tests failed")
        return 1
    
    # Test app creation
    if not test_app_creation():
        print("❌ App creation tests failed")
        return 1
    
    print("✅ All tests passed!")
    print("🎉 The app should be able to start properly")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 