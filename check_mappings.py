#!/usr/bin/env python3
"""
Script to check ContactFieldMapping and MembershipFieldMapping data
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, ContactFieldMapping, MembershipFieldMapping, FormField, AppState

def print_separator(title):
    """Print a formatted separator with title"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_json_data(data, title):
    """Print JSON data in a formatted way"""
    print(f"\n{title}:")
    if data:
        try:
            # Try to parse as JSON if it's a string
            if isinstance(data, str):
                parsed_data = json.loads(data)
                print(json.dumps(parsed_data, indent=2))
            else:
                print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(f"Raw data (not valid JSON): {data}")
    else:
        print("No data found")

def check_contact_mapping():
    """Check ContactFieldMapping data"""
    print_separator("CONTACT FIELD MAPPING")
    
    session = get_session()
    try:
        # Get contact field mapping
        contact_mapping_obj = session.query(ContactFieldMapping).first()
        
        if contact_mapping_obj:
            print(f"Contact Mapping ID: {contact_mapping_obj.id}")
            print(f"Mapping data:")
            print_json_data(contact_mapping_obj.mapping, "Contact Field Mappings")
        else:
            print("No contact field mapping found in database")
            
    except Exception as e:
        print(f"Error reading contact mapping: {e}")
    finally:
        session.close()

def check_membership_mapping():
    """Check MembershipFieldMapping data"""
    print_separator("MEMBERSHIP FIELD MAPPING")
    
    session = get_session()
    try:
        # Get membership field mapping
        membership_mapping_obj = session.query(MembershipFieldMapping).first()
        
        if membership_mapping_obj:
            print(f"Membership Mapping ID: {membership_mapping_obj.id}")
            print(f"Mapping data:")
            print_json_data(membership_mapping_obj.mapping, "Membership Field Mappings")
        else:
            print("No membership field mapping found in database")
            
    except Exception as e:
        print(f"Error reading membership mapping: {e}")
    finally:
        session.close()

def check_form_fields():
    """Check FormField data for field order and configuration"""
    print_separator("FORM FIELD CONFIGURATION")
    
    session = get_session()
    try:
        # Get all form fields
        form_fields = session.query(FormField).all()
        
        if form_fields:
            print(f"Found {len(form_fields)} form field configurations:")
            
            # Group by object type
            by_object_type = {}
            for field in form_fields:
                obj_type = field.object_type
                if obj_type not in by_object_type:
                    by_object_type[obj_type] = []
                by_object_type[obj_type].append(field)
            
            # Display by object type
            for obj_type, fields in by_object_type.items():
                print(f"\n--- {obj_type.upper()} FIELDS ---")
                # Sort by order_index
                sorted_fields = sorted(fields, key=lambda x: x.order_index or 0)
                
                for field in sorted_fields:
                    importance = "⭐" if field.is_important == 'true' else "  "
                    enabled = "✅" if field.is_enabled == 'true' else "❌"
                    print(f"  {importance} {enabled} [{field.order_index:2d}] {field.field_name}")
                    print(f"      Label: {field.field_label}")
                    print(f"      Type: {field.field_type}")
        else:
            print("No form field configurations found in database")
            
    except Exception as e:
        print(f"Error reading form fields: {e}")
    finally:
        session.close()

def check_app_state_mappings():
    """Check AppState for additional mapping configurations"""
    print_separator("APP STATE MAPPING CONFIGURATIONS")
    
    session = get_session()
    try:
        # Get all app state entries related to mappings
        mapping_keys = [
            'acgi_field_config_contact',
            'acgi_field_config_membership',
            'acgi_fields_contact',
            'acgi_fields_membership'
        ]
        
        for key in mapping_keys:
            app_state_obj = session.query(AppState).filter_by(key=key).first()
            if app_state_obj:
                print(f"\n{key}:")
                print_json_data(app_state_obj.value, f"Configuration for {key}")
            else:
                print(f"\n{key}: No data found")
                
    except Exception as e:
        print(f"Error reading app state mappings: {e}")
    finally:
        session.close()

def check_all_mappings():
    """Check all mapping-related data"""
    print_separator("MAPPING DATA CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_contact_mapping()
    check_membership_mapping()
    check_form_fields()
    check_app_state_mappings()
    
    print_separator("CHECK COMPLETE")

def main():
    """Main function"""
    try:
        check_all_mappings()
    except Exception as e:
        print(f"Error running mapping check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 