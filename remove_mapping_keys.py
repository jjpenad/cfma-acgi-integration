#!/usr/bin/env python3
"""
Script to remove specific keys from mapping in AppState for contacts and memberships.
Run this script from the root directory of the project.
"""

import sys
import os
import json

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import get_session, AppState

def remove_keys_from_appstate_mapping(keys_to_remove, object_type='both'):
    """
    Remove specific keys from the mapping stored in AppState JSON.
    
    Args:
        keys_to_remove (list): List of keys to remove from the mapping
        object_type (str): 'contacts', 'memberships', or 'both' (default)
    """
    session = get_session()
    
    try:
        if object_type in ['contacts', 'both']:
            print(f"Processing contacts ACGI field config...")
            
            # Get current ACGI field config from AppState
            acgi_config_key = f'acgi_field_config_contacts'
            acgi_config_obj = session.query(AppState).filter_by(key=acgi_config_key).first()
            
            if acgi_config_obj and acgi_config_obj.value:
                acgi_config = json.loads(acgi_config_obj.value)
                print(f"Current contacts ACGI config: {acgi_config}")
                
                # Remove specified keys
                removed_keys = []
                for key in keys_to_remove:
                    if key in acgi_config:
                        del acgi_config[key]
                        removed_keys.append(key)
                        print(f"Removed key '{key}' from contacts ACGI config")
                    else:
                        print(f"Key '{key}' not found in contacts ACGI config")
                
                if removed_keys:
                    # Save updated config
                    acgi_config_obj.value = json.dumps(acgi_config)
                    session.commit()
                    print(f"Updated contacts ACGI config: {acgi_config}")
                else:
                    print("No keys were removed from contacts ACGI config")
            else:
                print("No contacts ACGI config found in AppState")
        
        if object_type in ['memberships', 'both']:
            print(f"\nProcessing memberships ACGI field config...")
            
            # Get current ACGI field config from AppState
            acgi_config_key = f'acgi_field_config_memberships'
            acgi_config_obj = session.query(AppState).filter_by(key=acgi_config_key).first()
            
            if acgi_config_obj and acgi_config_obj.value:
                acgi_config = json.loads(acgi_config_obj.value)
                print(f"Current memberships ACGI config: {acgi_config}")
                
                # Remove specified keys
                removed_keys = []
                for key in keys_to_remove:
                    if key in acgi_config:
                        del acgi_config[key]
                        removed_keys.append(key)
                        print(f"Removed key '{key}' from memberships ACGI config")
                    else:
                        print(f"Key '{key}' not found in memberships ACGI config")
                
                if removed_keys:
                    # Save updated config
                    acgi_config_obj.value = json.dumps(acgi_config)
                    session.commit()
                    print(f"Updated memberships ACGI config: {acgi_config}")
                else:
                    print("No keys were removed from memberships ACGI config")
            else:
                print("No memberships ACGI config found in AppState")
        
        print("\n✅ AppState mapping cleanup completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        session.close()
    
    return True

def show_current_appstate_mappings():
    """Display current AppState mappings for both contacts and memberships."""
    session = get_session()
    
    try:
        print("=== CURRENT APPSTATE MAPPINGS ===")
        
        # Show contacts ACGI config
        contacts_config_obj = session.query(AppState).filter_by(key='acgi_field_config_contacts').first()
        if contacts_config_obj and contacts_config_obj.value:
            contacts_config = json.loads(contacts_config_obj.value)
            print(f"Contacts ACGI Config: {contacts_config}")
        else:
            print("Contacts ACGI Config: None")
        
        # Show memberships ACGI config
        memberships_config_obj = session.query(AppState).filter_by(key='acgi_field_config_memberships').first()
        if memberships_config_obj and memberships_config_obj.value:
            memberships_config = json.loads(memberships_config_obj.value)
            print(f"Memberships ACGI Config: {memberships_config}")
        else:
            print("Memberships ACGI Config: None")
        
        print("==================================")
        
    except Exception as e:
        print(f"❌ Error showing AppState mappings: {str(e)}")
    finally:
        session.close()

def main():
    """Main function to run the script."""
    print("🔧 AppState Mapping Key Removal Tool")
    print("=" * 45)
    
    # Show current mappings first
    show_current_appstate_mappings()
    
    # Get user input
    print("\nEnter the keys you want to remove (comma-separated):")
    keys_input = input("Keys: ").strip()
    
    if not keys_input:
        print("❌ No keys specified. Exiting.")
        return
    
    # Parse keys
    keys_to_remove = [key.strip() for key in keys_input.split(',') if key.strip()]
    
    print(f"\nKeys to remove: {keys_to_remove}")
    
    # Get object type
    print("\nWhich AppState config to update?")
    print("1. Contacts only")
    print("2. Memberships only") 
    print("3. Both (default)")
    
    choice = input("Choice (1-3): ").strip()
    
    if choice == '1':
        object_type = 'contacts'
    elif choice == '2':
        object_type = 'memberships'
    else:
        object_type = 'both'
    
    print(f"\nUpdating {object_type} AppState config...")
    
    # Confirm action
    confirm = input(f"\nAre you sure you want to remove these keys from {object_type} AppState config? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        success = remove_keys_from_appstate_mapping(keys_to_remove, object_type)
        if success:
            print("\n✅ Operation completed successfully!")
            print("\nUpdated AppState configs:")
            show_current_appstate_mappings()
        else:
            print("\n❌ Operation failed!")
    else:
        print("❌ Operation cancelled.")

if __name__ == "__main__":
    main() 