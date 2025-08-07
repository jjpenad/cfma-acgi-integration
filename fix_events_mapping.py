#!/usr/bin/env python3
"""
Script to clear the corrupted events mapping.
"""

import sqlite3
import os

def fix_events_mapping():
    """Clear the corrupted events mapping"""
    
    # Database path
    db_path = 'local_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Fixing events mapping...")
        
        # Clear the corrupted mapping
        cursor.execute("DELETE FROM event_field_mapping")
        deleted_count = cursor.rowcount
        print(f"   ✅ Deleted {deleted_count} corrupted mapping records")
        
        # Commit changes
        conn.commit()
        
        print("✅ Events mapping has been cleared!")
        print("🔄 Next steps:")
        print("1. Go to the ACGI to HubSpot tab")
        print("2. Load properties for Events")
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

if __name__ == "__main__":
    fix_events_mapping() 