#!/usr/bin/env python3
"""
Database management script for ACGI to HubSpot Integration
"""

import os
import sys
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import init_db, reset_db, get_session, User, AppState, FormField, SearchPreference
from sqlalchemy import inspect
from config import Config

def check_db_status():
    """Check database status and list tables"""
    try:
        from models import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("🗄️ Database Status:")
        print(f"   Database Type: {Config.DATABASE_TYPE}")
        print(f"   Tables Found: {len(tables)}")
        
        if tables:
            print("   Tables:")
            for table in tables:
                print(f"     - {table}")
        else:
            print("   No tables found")
            
        # Check for admin user
        session = get_session()
        try:
            admin_user = session.query(User).filter_by(username=Config.ADMIN_USERNAME).first()
            if admin_user:
                print(f"   ✅ Admin user exists: {Config.ADMIN_USERNAME}")
            else:
                print(f"   ❌ Admin user missing: {Config.ADMIN_USERNAME}")
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")

def reset_database():
    """Reset the database - drop all tables and recreate them"""
    print("⚠️  WARNING: This will delete all data!")
    confirm = input("Are you sure you want to reset the database? (yes/no): ")
    
    if confirm.lower() == 'yes':
        print("🗄️ Resetting database...")
        if reset_db():
            print("✅ Database reset successful!")
        else:
            print("❌ Database reset failed!")
    else:
        print("❌ Database reset cancelled.")

def init_database():
    """Initialize database tables"""
    print("🗄️ Initializing database...")
    init_db()
    print("✅ Database initialization completed!")

def main():
    parser = argparse.ArgumentParser(description='Database management for ACGI to HubSpot Integration')
    parser.add_argument('action', choices=['status', 'init', 'reset'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'status':
        check_db_status()
    elif args.action == 'init':
        init_database()
    elif args.action == 'reset':
        reset_database()

if __name__ == "__main__":
    main() 