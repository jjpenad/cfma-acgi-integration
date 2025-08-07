#!/usr/bin/env python3
"""
Database management script for ACGI to HubSpot Integration
"""

import os
import sys
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import init_db, reset_db, get_session, User, AppState, FormField, SearchPreference, ContactFieldMapping, Base, engine
from sqlalchemy import inspect
from config import Config

def get_required_tables():
    """Get list of all required tables from models"""
    return [
        'users',
        'app_state', 
        'form_fields',
        'search_preferences',
        'contact_field_mapping',
        'scheduling_config',
        'membership_field_mapping',
        'event_field_mapping',
        'purchased_products_field_mapping'
    ]

def check_and_create_tables():
    """Check existence of all tables and create missing ones"""
    try:
        from models import engine
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = get_required_tables()
        
        print("🔍 Checking database tables...")
        print(f"   Required tables: {len(required_tables)}")
        print(f"   Existing tables: {len(existing_tables)}")
        
        missing_tables = []
        existing_required_tables = []
        
        for table in required_tables:
            if table in existing_tables:
                existing_required_tables.append(table)
                print(f"   ✅ {table}")
            else:
                missing_tables.append(table)
                print(f"   ❌ {table} (missing)")
        
        if missing_tables:
            print(f"\n📝 Creating {len(missing_tables)} missing tables...")
            try:
                # Create all missing tables at once using Base.metadata.create_all()
                # This is more reliable than creating tables individually
                Base.metadata.create_all(engine, checkfirst=True)
                print("✅ All missing tables created successfully!")
                
                # Create default admin user after table creation
                create_default_admin()
                
            except Exception as e:
                print(f"❌ Error creating missing tables: {str(e)}")
                return False
        else:
            print("\n✅ All required tables exist!")
        
        # Check for admin user
        session = get_session()
        try:
            admin_user = session.query(User).filter_by(username=Config.ADMIN_USERNAME).first()
            if admin_user:
                print(f"   ✅ Admin user exists: {Config.ADMIN_USERNAME}")
            else:
                print(f"   ❌ Admin user missing: {Config.ADMIN_USERNAME}")
                print("   📝 Creating admin user...")
                create_default_admin()
        finally:
            session.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        from werkzeug.security import generate_password_hash
        
        session = get_session()
        try:
            # Check if admin user exists
            admin_user = session.query(User).filter_by(username=Config.ADMIN_USERNAME).first()
            if not admin_user:
                # Create default admin user
                password_hash = generate_password_hash(Config.ADMIN_PASSWORD)
                admin_user = User(
                    username=Config.ADMIN_USERNAME,
                    password_hash=password_hash
                )
                session.add(admin_user)
                session.commit()
                print(f"   ✅ Created default admin user: {Config.ADMIN_USERNAME}")
            else:
                print(f"   ✅ Admin user already exists: {Config.ADMIN_USERNAME}")
        except Exception as e:
            session.rollback()
            print(f"   ❌ Error creating admin user: {str(e)}")
        finally:
            session.close()
    except Exception as e:
        print(f"   ❌ Error in create_default_admin: {str(e)}")

def check_db_status():
    """Check database status and list tables"""
    try:
        from models import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        required_tables = get_required_tables()
        
        print("🗄️ Database Status:")
        print(f"   Database Type: {Config.DATABASE_TYPE}")
        print(f"   Total Tables Found: {len(tables)}")
        print(f"   Required Tables: {len(required_tables)}")
        
        if tables:
            print("   All Tables:")
            for table in tables:
                status = "✅" if table in required_tables else "📋"
                print(f"     {status} {table}")
        else:
            print("   No tables found")
        
        # Check required tables specifically
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"\n   ❌ Missing Required Tables: {missing_tables}")
        else:
            print(f"\n   ✅ All required tables present")
            
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
    parser.add_argument('action', choices=['status', 'init', 'reset', 'check'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'status':
        check_db_status()
    elif args.action == 'init':
        init_database()
    elif args.action == 'reset':
        reset_database()
    elif args.action == 'check':
        check_and_create_tables()

if __name__ == "__main__":
    main() 