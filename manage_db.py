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

def get_required_columns():
    """Get dictionary of required columns for each table"""
    return {
        'users': ['id', 'username', 'password_hash', 'created_at', 'last_login'],
        'app_state': ['id', 'key', 'value', 'created_at', 'updated_at'],
        'form_fields': ['id', 'object_type', 'field_name', 'field_label', 'field_type', 'is_enabled', 'is_important', 'order_index', 'created_at', 'field_source'],
        'search_preferences': ['id', 'object_type', 'search_strategy', 'created_at', 'updated_at'],
        'contact_field_mapping': ['id', 'mapping'],
        'scheduling_config': ['id', 'frequency', 'enabled', 'customer_ids', 'sync_contacts', 'sync_memberships', 'sync_orders', 'sync_events', 'last_sync', 'created_at', 'updated_at', 'production_mode'],
        'membership_field_mapping': ['id', 'mapping'],
        'event_field_mapping': ['id', 'mapping'],
        'purchased_products_field_mapping': ['id', 'mapping']
    }

def check_table_columns(inspector, table_name, required_columns):
    """Check if a table has all required columns"""
    try:
        columns = inspector.get_columns(table_name)
        existing_columns = [col['name'] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"   ❌ {table_name} - Missing columns: {missing_columns}")
            return False, missing_columns
        else:
            print(f"   ✅ {table_name} - All columns present")
            return True, []
    except Exception as e:
        print(f"   ❌ {table_name} - Error checking columns: {str(e)}")
        return False, []

def fix_missing_columns(table_name, missing_columns):
    """Add missing columns to a table"""
    try:
        from sqlalchemy import text
        
        # Get the engine
        from models import engine
        
        with engine.connect() as conn:
            for column in missing_columns:
                # Determine column type based on column name and table
                column_type = get_column_type(table_name, column)
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}"
                print(f"      Adding column: {column} ({column_type})")
                conn.execute(text(sql))
            conn.commit()
        return True
    except Exception as e:
        print(f"      ❌ Error adding column {column}: {str(e)}")
        return False

def get_column_type(table_name, column_name):
    """Determine the appropriate column type based on table and column name"""
    # Default to TEXT for most cases
    column_types = {
        'users': {
            'id': 'INTEGER PRIMARY KEY',
            'username': 'VARCHAR(50)',
            'password_hash': 'VARCHAR(255)',
            'created_at': 'DATETIME',
            'last_login': 'DATETIME'
        },
        'app_state': {
            'id': 'INTEGER PRIMARY KEY',
            'key': 'VARCHAR(100)',
            'value': 'TEXT',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        },
        'form_fields': {
            'id': 'INTEGER PRIMARY KEY',
            'object_type': 'VARCHAR(50)',
            'field_name': 'VARCHAR(100)',
            'field_label': 'VARCHAR(200)',
            'field_type': 'VARCHAR(50)',
            'is_enabled': 'VARCHAR(10)',
            'is_important': 'VARCHAR(10)',
            'order_index': 'INTEGER',
            'created_at': 'DATETIME',
            'field_source': 'VARCHAR(20)'
        },
        'search_preferences': {
            'id': 'INTEGER PRIMARY KEY',
            'object_type': 'VARCHAR(50)',
            'search_strategy': 'VARCHAR(50)',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        },
        'contact_field_mapping': {
            'id': 'INTEGER PRIMARY KEY',
            'mapping': 'TEXT'
        },
        'scheduling_config': {
            'id': 'INTEGER PRIMARY KEY',
            'frequency': 'INTEGER',
            'enabled': 'VARCHAR(10)',
            'customer_ids': 'TEXT',
            'sync_contacts': 'VARCHAR(10)',
            'sync_memberships': 'VARCHAR(10)',
            'sync_orders': 'VARCHAR(10)',
            'sync_events': 'VARCHAR(10)',
            'last_sync': 'DATETIME',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        },
        'membership_field_mapping': {
            'id': 'INTEGER PRIMARY KEY',
            'mapping': 'TEXT'
        },
        'event_field_mapping': {
            'id': 'INTEGER PRIMARY KEY',
            'mapping': 'TEXT'
        },
        'purchased_products_field_mapping': {
            'id': 'INTEGER PRIMARY KEY',
            'mapping': 'TEXT'
        }
    }
    
    return column_types.get(table_name, {}).get(column_name, 'TEXT')

def check_and_create_tables():
    """Check existence of all tables and columns, create/fix missing ones"""
    try:
        from models import engine
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = get_required_tables()
        required_columns = get_required_columns()
        
        print("🔍 Checking database tables and columns...")
        print(f"   Required tables: {len(required_tables)}")
        print(f"   Existing tables: {len(existing_tables)}")
        
        missing_tables = []
        existing_required_tables = []
        tables_with_missing_columns = []
        
        # Check tables first
        for table in required_tables:
            if table in existing_tables:
                existing_required_tables.append(table)
                print(f"   ✅ {table}")
            else:
                missing_tables.append(table)
                print(f"   ❌ {table} (missing)")
        
        # Create missing tables
        if missing_tables:
            print(f"\n📝 Creating {len(missing_tables)} missing tables...")
            try:
                Base.metadata.create_all(engine, checkfirst=True)
                print("✅ All missing tables created successfully!")
                
                # Create default admin user after table creation
                create_default_admin()
                
            except Exception as e:
                print(f"❌ Error creating missing tables: {str(e)}")
                return False
        else:
            print("\n✅ All required tables exist!")
        
        # Check columns in existing tables
        print("\n🔍 Checking table columns...")
        for table in existing_required_tables:
            if table in required_columns:
                is_valid, missing_cols = check_table_columns(inspector, table, required_columns[table])
                if not is_valid:
                    tables_with_missing_columns.append((table, missing_cols))
        
        # Fix missing columns
        if tables_with_missing_columns:
            print(f"\n🔧 Fixing {len(tables_with_missing_columns)} tables with missing columns...")
            for table_name, missing_columns in tables_with_missing_columns:
                print(f"   📝 Fixing {table_name}...")
                if fix_missing_columns(table_name, missing_columns):
                    print(f"   ✅ {table_name} columns fixed successfully!")
                else:
                    print(f"   ❌ Failed to fix {table_name} columns!")
        else:
            print("\n✅ All table columns are correct!")
        
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
                       help='Action to perform: status (show db status), init (initialize), reset (reset all data), check (check and fix tables/columns)')
    
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