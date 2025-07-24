#!/usr/bin/env python3
"""
Comprehensive script to check all field data storage for contacts and memberships tabs
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
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

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

def check_column_1_acgi_fields():
    """Check Column 1: ACGI Fields (stored in AppState)"""
    print_separator("COLUMN 1: ACGI FIELDS (AppState)")
    
    session = get_session()
    try:
        # Check ACGI fields for contacts
        acgi_fields_contact = session.query(AppState).filter_by(key='acgi_fields_contact').first()
        if acgi_fields_contact:
            print("\nACGI Fields for Contacts:")
            print_json_data(acgi_fields_contact.value, "Contact ACGI Fields")
        else:
            print("\nACGI Fields for Contacts: No data found")
        
        # Check ACGI fields for memberships
        acgi_fields_membership = session.query(AppState).filter_by(key='acgi_fields_membership').first()
        if acgi_fields_membership:
            print("\nACGI Fields for Memberships:")
            print_json_data(acgi_fields_membership.value, "Membership ACGI Fields")
        else:
            print("\nACGI Fields for Memberships: No data found")
            
    except Exception as e:
        print(f"Error reading ACGI fields: {e}")
    finally:
        session.close()

def check_column_2_3_hubspot_properties():
    """Check Column 2 & 3: HubSpot Properties (stored in FormField)"""
    print_separator("COLUMN 2 & 3: HUBSPOT PROPERTIES (FormField)")
    
    session = get_session()
    try:
        # Get all form fields for contacts and memberships
        contact_fields = session.query(FormField).filter_by(object_type='contacts').all()
        membership_fields = session.query(FormField).filter_by(object_type='memberships').all()
        
        print(f"\nCONTACTS - Found {len(contact_fields)} HubSpot property configurations:")
        if contact_fields:
            # Sort by order_index
            sorted_fields = sorted(contact_fields, key=lambda x: x.order_index or 0)
            
            print("\nImportant Fields (Column 2):")
            important_fields = [f for f in sorted_fields if f.is_important == 'true']
            for field in important_fields:
                importance = "⭐" if field.is_important == 'true' else "  "
                enabled = "✅" if field.is_enabled == 'true' else "❌"
                print(f"  {importance} {enabled} [{field.order_index:2d}] {field.field_name}")
                print(f"      Label: {field.field_label}")
                print(f"      Type: {field.field_type}")
            
            print("\nAll Available Fields (Column 3):")
            all_fields = sorted_fields
            for field in all_fields:
                importance = "⭐" if field.is_important == 'true' else "  "
                enabled = "✅" if field.is_enabled == 'true' else "❌"
                print(f"  {importance} {enabled} [{field.order_index:2d}] {field.field_name}")
                print(f"      Label: {field.field_label}")
                print(f"      Type: {field.field_type}")
        else:
            print("No HubSpot property configurations found for contacts")
        
        print(f"\nMEMBERSHIPS - Found {len(membership_fields)} HubSpot property configurations:")
        if membership_fields:
            # Sort by order_index
            sorted_fields = sorted(membership_fields, key=lambda x: x.order_index or 0)
            
            print("\nImportant Fields (Column 2):")
            important_fields = [f for f in sorted_fields if f.is_important == 'true']
            for field in important_fields:
                importance = "⭐" if field.is_important == 'true' else "  "
                enabled = "✅" if field.is_enabled == 'true' else "❌"
                print(f"  {importance} {enabled} [{field.order_index:2d}] {field.field_name}")
                print(f"      Label: {field.field_label}")
                print(f"      Type: {field.field_type}")
            
            print("\nAll Available Fields (Column 3):")
            all_fields = sorted_fields
            for field in all_fields:
                importance = "⭐" if field.is_important == 'true' else "  "
                enabled = "✅" if field.is_enabled == 'true' else "❌"
                print(f"  {importance} {enabled} [{field.order_index:2d}] {field.field_name}")
                print(f"      Label: {field.field_label}")
                print(f"      Type: {field.field_type}")
        else:
            print("No HubSpot property configurations found for memberships")
            
    except Exception as e:
        print(f"Error reading HubSpot properties: {e}")
    finally:
        session.close()

def check_column_4_mapping_fields():
    """Check Column 4: Field Mappings (stored in ContactFieldMapping and MembershipFieldMapping)"""
    print_separator("COLUMN 4: FIELD MAPPINGS")
    
    session = get_session()
    try:
        # Check contact field mappings
        contact_mapping = session.query(ContactFieldMapping).first()
        if contact_mapping:
            print("\nContact Field Mappings:")
            print(f"ID: {contact_mapping.id}")
            print_json_data(contact_mapping.mapping, "ACGI → HubSpot Mappings")
        else:
            print("\nContact Field Mappings: No data found")
        
        # Check membership field mappings
        membership_mapping = session.query(MembershipFieldMapping).first()
        if membership_mapping:
            print("\nMembership Field Mappings:")
            print(f"ID: {membership_mapping.id}")
            print_json_data(membership_mapping.mapping, "ACGI → HubSpot Mappings")
        else:
            print("\nMembership Field Mappings: No data found")
            
    except Exception as e:
        print(f"Error reading field mappings: {e}")
    finally:
        session.close()

def check_additional_configurations():
    """Check additional field configurations in AppState"""
    print_separator("ADDITIONAL FIELD CONFIGURATIONS (AppState)")
    
    session = get_session()
    try:
        # Check ACGI field configurations
        acgi_config_keys = [
            'acgi_field_config_contact',
            'acgi_field_config_membership'
        ]
        
        for key in acgi_config_keys:
            config_obj = session.query(AppState).filter_by(key=key).first()
            if config_obj:
                print(f"\n{key}:")
                print_json_data(config_obj.value, f"Configuration for {key}")
            else:
                print(f"\n{key}: No data found")
        
        # Check address, email, phone preferences
        preference_keys = [
            'acgi_address_preference',
            'acgi_email_preference', 
            'acgi_phone_preference'
        ]
        
        for key in preference_keys:
            pref_obj = session.query(AppState).filter_by(key=key).first()
            if pref_obj:
                print(f"\n{key}:")
                print_json_data(pref_obj.value, f"Preference for {key}")
            else:
                print(f"\n{key}: No data found")
                
    except Exception as e:
        print(f"Error reading additional configurations: {e}")
    finally:
        session.close()

def check_search_preferences():
    """Check search preferences"""
    print_separator("SEARCH PREFERENCES")
    
    session = get_session()
    try:
        from models import SearchPreference
        
        # Check search preferences for contacts and memberships
        contact_search = session.query(SearchPreference).filter_by(object_type='contacts').first()
        membership_search = session.query(SearchPreference).filter_by(object_type='memberships').first()
        
        if contact_search:
            print(f"\nContact Search Strategy: {contact_search.search_strategy}")
        else:
            print("\nContact Search Strategy: No preference set")
            
        if membership_search:
            print(f"\nMembership Search Strategy: {membership_search.search_strategy}")
        else:
            print("\nMembership Search Strategy: No preference set")
            
    except Exception as e:
        print(f"Error reading search preferences: {e}")
    finally:
        session.close()

def check_all_field_data():
    """Check all field data storage locations"""
    print_separator("COMPREHENSIVE FIELD DATA CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_column_1_acgi_fields()
    check_column_2_3_hubspot_properties()
    check_column_4_mapping_fields()
    check_additional_configurations()
    check_search_preferences()
    
    print_separator("CHECK COMPLETE")

def main():
    """Main function"""
    try:
        check_all_field_data()
    except Exception as e:
        print(f"Error running field data check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 