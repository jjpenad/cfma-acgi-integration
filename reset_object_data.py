#!/usr/bin/env python3
"""
Script to reset data for a specific object type in the CFMA integration.
This will clear all mapping data, field configurations, and related data for the specified object type.
"""

import sqlite3
import sys
import os

def reset_object_data(object_type):
    """
    Reset all data for a specific object type in the integration.
    
    Args:
        object_type (str): The object type to reset ('contacts', 'memberships', 'purchased_products', 'events')
    """
    
    # Validate object type
    valid_object_types = ['contacts', 'memberships', 'purchased_products', 'events']
    if object_type not in valid_object_types:
        print(f"❌ Invalid object type: {object_type}")
        print(f"Valid object types: {', '.join(valid_object_types)}")
        return False
    
    # Database path
    db_path = 'local_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔄 Resetting data for object type: {object_type}")
        print("=" * 50)
        
        # 1. Delete FormField records for the object type
        print(f"1. Deleting FormField records for '{object_type}'...")
        cursor.execute("DELETE FROM form_fields WHERE object_type = ?", (object_type,))
        form_fields_deleted = cursor.rowcount
        print(f"   ✅ Deleted {form_fields_deleted} FormField records")
        
        # 2. Delete AppState records for ACGI field config
        print(f"2. Deleting AppState ACGI field config for '{object_type}'...")
        cursor.execute("DELETE FROM app_state WHERE key = ?", (f'acgi_field_config_{object_type}',))
        acgi_config_deleted = cursor.rowcount
        print(f"   ✅ Deleted {acgi_config_deleted} AppState ACGI config records")
        
        # 3. Delete AppState records for ACGI fields
        print(f"3. Deleting AppState ACGI fields for '{object_type}'...")
        cursor.execute("DELETE FROM app_state WHERE key = ?", (f'acgi_fields_{object_type}',))
        acgi_fields_deleted = cursor.rowcount
        print(f"   ✅ Deleted {acgi_fields_deleted} AppState ACGI fields records")
        
        # 4. Delete field mapping records based on object type
        if object_type == 'contacts':
            print("4. Deleting ContactFieldMapping records...")
            cursor.execute("DELETE FROM contact_field_mapping")
            mapping_deleted = cursor.rowcount
            print(f"   ✅ Deleted {mapping_deleted} ContactFieldMapping records")
            
        elif object_type == 'memberships':
            print("4. Deleting MembershipFieldMapping records...")
            cursor.execute("DELETE FROM membership_field_mapping")
            mapping_deleted = cursor.rowcount
            print(f"   ✅ Deleted {mapping_deleted} MembershipFieldMapping records")
            
        elif object_type == 'purchased_products':
            print("4. Deleting PurchasedProductsFieldMapping records...")
            cursor.execute("DELETE FROM purchased_products_field_mapping")
            mapping_deleted = cursor.rowcount
            print(f"   ✅ Deleted {mapping_deleted} PurchasedProductsFieldMapping records")
            
        elif object_type == 'events':
            print("4. Deleting EventFieldMapping records...")
            cursor.execute("DELETE FROM event_field_mapping")
            mapping_deleted = cursor.rowcount
            print(f"   ✅ Deleted {mapping_deleted} EventFieldMapping records")
        
        # 5. Delete SearchPreference records for the object type
        print(f"5. Deleting SearchPreference records for '{object_type}'...")
        cursor.execute("DELETE FROM search_preferences WHERE object_type = ?", (object_type,))
        search_pref_deleted = cursor.rowcount
        print(f"   ✅ Deleted {search_pref_deleted} SearchPreference records")
        
        # 6. Delete ACGI preference records for contacts
        if object_type == 'contacts':
            print("6. Deleting ACGI preference records for contacts...")
            cursor.execute("DELETE FROM app_state WHERE key IN (?, ?, ?)", 
                         ('acgi_email_preference', 'acgi_phone_preference', 'acgi_address_preference'))
            pref_deleted = cursor.rowcount
            print(f"   ✅ Deleted {pref_deleted} ACGI preference records")
        
        # Commit changes
        conn.commit()
        
        # Summary
        total_deleted = form_fields_deleted + acgi_config_deleted + acgi_fields_deleted + mapping_deleted + search_pref_deleted
        if object_type == 'contacts':
            total_deleted += pref_deleted
        
        print("=" * 50)
        print(f"✅ Successfully reset data for '{object_type}'")
        print(f"📊 Total records deleted: {total_deleted}")
        print(f"🗂️  Database file: {db_path}")
        print("\n🔄 Next steps:")
        print("1. Restart the application")
        print("2. Go to the ACGI to HubSpot tab")
        print("3. Load properties for the reset object type")
        print("4. Configure field mappings as needed")
        
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
    
    if len(sys.argv) != 2:
        print("Usage: python reset_object_data.py <object_type>")
        print("\nValid object types:")
        print("  - contacts")
        print("  - memberships") 
        print("  - purchased_products")
        print("  - events")
        print("\nExample: python reset_object_data.py purchased_products")
        return
    
    object_type = sys.argv[1].lower()
    
    # Confirm before proceeding
    print(f"⚠️  WARNING: This will permanently delete all data for '{object_type}'")
    print("This includes:")
    print("  - Field mappings")
    print("  - Field configurations") 
    print("  - ACGI field data")
    print("  - Search preferences")
    print("  - All related configuration data")
    print()
    
    confirm = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        success = reset_object_data(object_type)
        if success:
            print("\n🎉 Reset completed successfully!")
        else:
            print("\n💥 Reset failed!")
            sys.exit(1)
    else:
        print("❌ Reset cancelled.")

if __name__ == "__main__":
    main() 