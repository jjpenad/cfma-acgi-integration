#!/usr/bin/env python3
"""
Script to check and debug the current mappings in the database.
This will show what mappings are currently stored for each object type.
"""

import sqlite3
import json
import sys
import os

def check_mappings():
    """Check all mappings in the database"""
    
    # Database path
    db_path = 'local_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking all mappings in the database")
        print("=" * 60)
        
        # Check ContactFieldMapping
        print("📋 CONTACT FIELD MAPPING:")
        cursor.execute("SELECT mapping FROM contact_field_mapping LIMIT 1")
        result = cursor.fetchone()
        if result:
            try:
                mapping = json.loads(result[0])
                print(f"   Records: 1")
                print(f"   Mapping: {mapping}")
            except json.JSONDecodeError:
                print(f"   Records: 1")
                print(f"   Error: Invalid JSON in mapping")
        else:
            print("   Records: 0 (No mapping found)")
        print()
        
        # Check MembershipFieldMapping
        print("📋 MEMBERSHIP FIELD MAPPING:")
        cursor.execute("SELECT mapping FROM membership_field_mapping LIMIT 1")
        result = cursor.fetchone()
        if result:
            try:
                mapping = json.loads(result[0])
                print(f"   Records: 1")
                print(f"   Mapping: {mapping}")
            except json.JSONDecodeError:
                print(f"   Records: 1")
                print(f"   Error: Invalid JSON in mapping")
        else:
            print("   Records: 0 (No mapping found)")
        print()
        
        # Check PurchasedProductsFieldMapping
        print("📋 PURCHASED PRODUCTS FIELD MAPPING:")
        cursor.execute("SELECT mapping FROM purchased_products_field_mapping LIMIT 1")
        result = cursor.fetchone()
        if result:
            try:
                mapping = json.loads(result[0])
                print(f"   Records: 1")
                print(f"   Mapping: {mapping}")
                
                # Check if this looks like contact mapping
                contact_fields = ['emails', 'firstName', 'lastName', 'phones', 'custId']
                found_contact_fields = [field for field in contact_fields if field in mapping.values()]
                if found_contact_fields:
                    print(f"   ⚠️  WARNING: Found contact fields in purchased products mapping!")
                    print(f"   Contact fields found: {found_contact_fields}")
                    print(f"   This mapping appears to be corrupted!")
            except json.JSONDecodeError:
                print(f"   Records: 1")
                print(f"   Error: Invalid JSON in mapping")
        else:
            print("   Records: 0 (No mapping found)")
        print()
        
        # Check EventFieldMapping
        print("📋 EVENT FIELD MAPPING:")
        cursor.execute("SELECT mapping FROM event_field_mapping LIMIT 1")
        result = cursor.fetchone()
        if result:
            try:
                mapping = json.loads(result[0])
                print(f"   Records: 1")
                print(f"   Mapping: {mapping}")
            except json.JSONDecodeError:
                print(f"   Records: 1")
                print(f"   Error: Invalid JSON in mapping")
        else:
            print("   Records: 0 (No mapping found)")
        print()
        
        # Check AppState for ACGI field configs
        print("📋 APP STATE - ACGI FIELD CONFIGS:")
        cursor.execute("SELECT key, value FROM app_state WHERE key LIKE 'acgi_field_config_%'")
        results = cursor.fetchall()
        for key, value in results:
            print(f"   {key}: {value[:100]}..." if len(value) > 100 else f"   {key}: {value}")
        print()
        
        # Check AppState for ACGI fields
        print("📋 APP STATE - ACGI FIELDS:")
        cursor.execute("SELECT key, value FROM app_state WHERE key LIKE 'acgi_fields_%'")
        results = cursor.fetchall()
        for key, value in results:
            print(f"   {key}: {value[:100]}..." if len(value) > 100 else f"   {key}: {value}")
        print()
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def fix_purchased_products_mapping():
    """Fix the purchased products mapping by clearing it"""
    
    # Database path
    db_path = 'local_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Fixing purchased products mapping...")
        
        # Clear the corrupted mapping
        cursor.execute("DELETE FROM purchased_products_field_mapping")
        deleted_count = cursor.rowcount
        print(f"   ✅ Deleted {deleted_count} corrupted mapping records")
        
        # Commit changes
        conn.commit()
        
        print("✅ Purchased products mapping has been cleared!")
        print("🔄 Next steps:")
        print("1. Go to the ACGI to HubSpot tab")
        print("2. Load properties for Purchased Products")
        print("3. Configure the field mappings correctly")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) == 1:
        # Just check mappings
        check_mappings()
    elif len(sys.argv) == 2 and sys.argv[1] == 'fix':
        # Check mappings first, then fix if needed
        print("🔍 Checking mappings first...")
        check_mappings()
        print("\n" + "=" * 60)
        
        confirm = input("Do you want to clear the corrupted purchased products mapping? (yes/no): ").lower().strip()
        if confirm in ['yes', 'y']:
            fix_purchased_products_mapping()
        else:
            print("❌ Fix cancelled.")
    else:
        print("Usage:")
        print("  python check_mappings.py          # Check all mappings")
        print("  python check_mappings.py fix      # Check and fix corrupted mappings")

if __name__ == "__main__":
    main() 