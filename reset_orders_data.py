#!/usr/bin/env python3
"""
Script to reset all database data associated with the orders tab.
This will clear FormField configurations, ACGI field configurations, and field mappings for orders.
"""

import sqlite3
import os
import sys

def reset_orders_data():
    """Reset all orders-related data from the database"""
    
    # Get the database path
    db_path = 'local_app.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting orders data reset...")
        
        # 1. Delete FormField records for orders
        print("1. Deleting FormField records for orders...")
        cursor.execute("DELETE FROM form_fields WHERE object_type = 'orders'")
        deleted_form_fields = cursor.rowcount
        print(f"   ✓ Deleted {deleted_form_fields} FormField records")
        
        # 2. Delete AppState records for orders ACGI field config
        print("2. Deleting ACGI field configuration for orders...")
        cursor.execute("DELETE FROM app_state WHERE key = 'acgi_field_config_orders'")
        deleted_acgi_config = cursor.rowcount
        print(f"   ✓ Deleted {deleted_acgi_config} ACGI field config records")
        
        # 3. Delete OrderFieldMapping records
        print("3. Deleting OrderFieldMapping records...")
        cursor.execute("DELETE FROM order_field_mapping")
        deleted_mappings = cursor.rowcount
        print(f"   ✓ Deleted {deleted_mappings} OrderFieldMapping records")
        
        # 4. Delete SearchPreference records for orders
        print("4. Deleting SearchPreference records for orders...")
        cursor.execute("DELETE FROM search_preferences WHERE object_type = 'orders'")
        deleted_search_prefs = cursor.rowcount
        print(f"   ✓ Deleted {deleted_search_prefs} SearchPreference records")
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        print("\n5. Verifying changes...")
        
        # Check remaining records
        cursor.execute("SELECT COUNT(*) FROM form_fields WHERE object_type = 'orders'")
        remaining_form_fields = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM app_state WHERE key = 'acgi_field_config_orders'")
        remaining_acgi_config = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM order_field_mapping")
        remaining_mappings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_preferences WHERE object_type = 'orders'")
        remaining_search_prefs = cursor.fetchone()[0]
        
        print(f"   Remaining FormField records for orders: {remaining_form_fields}")
        print(f"   Remaining ACGI field config records for orders: {remaining_acgi_config}")
        print(f"   Remaining OrderFieldMapping records: {remaining_mappings}")
        print(f"   Remaining SearchPreference records for orders: {remaining_search_prefs}")
        
        conn.close()
        print("\n✅ Orders data reset completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during orders data reset: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting orders data reset...")
    success = reset_orders_data()
    
    if success:
        print("\n🎉 Orders data reset successful!")
        print("The orders tab is now reset and will use the new HubSpot custom object '2-48354706 (ACGI Purchased Products)'.")
        print("You can now:")
        print("1. Go to the Orders tab in the ACGI to HubSpot interface")
        print("2. Load properties to see the new custom object properties")
        print("3. Configure field mappings and save to HubSpot")
    else:
        print("\n💥 Orders data reset failed! Please check the error messages above.")
        sys.exit(1) 