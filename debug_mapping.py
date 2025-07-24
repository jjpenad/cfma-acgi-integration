import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, ContactFieldMapping, MembershipFieldMapping, FormField, AppState

def debug_mapping():
    session = get_session()
    try:
        print("=== DEBUGGING MAPPING SYSTEM ===")
        
        # Check ContactFieldMapping
        print("\n1. CONTACT FIELD MAPPING:")
        contact_mapping = session.query(ContactFieldMapping).first()
        if contact_mapping:
            print(f"ID: {contact_mapping.id}")
            print(f"Mapping: {contact_mapping.mapping}")
            if contact_mapping.mapping:
                try:
                    parsed = json.loads(contact_mapping.mapping)
                    print(f"Parsed mapping: {json.dumps(parsed, indent=2)}")
                except:
                    print("Failed to parse mapping JSON")
        else:
            print("No contact mapping found")
        
        # Check MembershipFieldMapping
        print("\n2. MEMBERSHIP FIELD MAPPING:")
        membership_mapping = session.query(MembershipFieldMapping).first()
        if membership_mapping:
            print(f"ID: {membership_mapping.id}")
            print(f"Mapping: {membership_mapping.mapping}")
            if membership_mapping.mapping:
                try:
                    parsed = json.loads(membership_mapping.mapping)
                    print(f"Parsed mapping: {json.dumps(parsed, indent=2)}")
                except:
                    print("Failed to parse mapping JSON")
        else:
            print("No membership mapping found")
        
        # Check FormField for important properties
        print("\n3. FORM FIELD - IMPORTANT PROPERTIES:")
        important_contacts = session.query(FormField).filter_by(object_type='contacts', is_important=True).order_by(FormField.order_index).all()
        print(f"Important contact properties ({len(important_contacts)}):")
        for prop in important_contacts:
            print(f"  - {prop.field_name} (order: {prop.order_index})")
        
        important_memberships = session.query(FormField).filter_by(object_type='memberships', is_important=True).order_by(FormField.order_index).all()
        print(f"Important membership properties ({len(important_memberships)}):")
        for prop in important_memberships:
            print(f"  - {prop.field_name} (order: {prop.order_index})")
        
        # Check ACGI fields in AppState
        print("\n4. ACGI FIELDS IN APPSTATE:")
        acgi_contact_fields = session.query(AppState).filter_by(key='acgi_fields_contacts').first()
        if acgi_contact_fields and acgi_contact_fields.value:
            try:
                parsed = json.loads(acgi_contact_fields.value)
                print(f"ACGI Contact Fields: {list(parsed.keys())}")
            except:
                print("Failed to parse ACGI contact fields")
        else:
            print("No ACGI contact fields found")
        
        acgi_membership_fields = session.query(AppState).filter_by(key='acgi_fields_memberships').first()
        if acgi_membership_fields and acgi_membership_fields.value:
            try:
                parsed = json.loads(acgi_membership_fields.value)
                print(f"ACGI Membership Fields: {list(parsed.keys())}")
            except:
                print("Failed to parse ACGI membership fields")
        else:
            print("No ACGI membership fields found")
            
    finally:
        session.close()

if __name__ == "__main__":
    debug_mapping() 