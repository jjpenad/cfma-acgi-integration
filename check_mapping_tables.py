#!/usr/bin/env python3
"""
Simple script to check ContactFieldMapping and MembershipFieldMapping data
"""

import sys
import os
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, ContactFieldMapping, MembershipFieldMapping

def check_mapping_tables():
    """Check both mapping tables"""
    print("="*60)
    print(" MAPPING TABLES CHECK")
    print("="*60)
    
    session = get_session()
    
    try:
        # Check ContactFieldMapping
        print("\n1. CONTACT FIELD MAPPING TABLE:")
        print("-" * 40)
        contact_mapping = session.query(ContactFieldMapping).first()
        
        if contact_mapping:
            print(f"ID: {contact_mapping.id}")
            print(f"Mapping data:")
            if contact_mapping.mapping:
                try:
                    mapping_data = json.loads(contact_mapping.mapping)
                    print(json.dumps(mapping_data, indent=2))
                except json.JSONDecodeError:
                    print(f"Raw data (not valid JSON): {contact_mapping.mapping}")
            else:
                print("No mapping data stored")
        else:
            print("No contact field mapping found")
        
        # Check MembershipFieldMapping
        print("\n2. MEMBERSHIP FIELD MAPPING TABLE:")
        print("-" * 40)
        membership_mapping = session.query(MembershipFieldMapping).first()
        
        if membership_mapping:
            print(f"ID: {membership_mapping.id}")
            print(f"Mapping data:")
            if membership_mapping.mapping:
                try:
                    mapping_data = json.loads(membership_mapping.mapping)
                    print(json.dumps(mapping_data, indent=2))
                except json.JSONDecodeError:
                    print(f"Raw data (not valid JSON): {membership_mapping.mapping}")
            else:
                print("No mapping data stored")
        else:
            print("No membership field mapping found")
            
    except Exception as e:
        print(f"Error reading mapping tables: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print("\n" + "="*60)
    print(" CHECK COMPLETE")
    print("="*60)

if __name__ == "__main__":
    check_mapping_tables() 