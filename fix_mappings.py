import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, ContactFieldMapping, MembershipFieldMapping, FormField, AppState

def fix_mappings():
    session = get_session()
    try:
        print("=== FIXING MAPPINGS BASED ON CURRENT DATABASE STATE ===")
        
        # Get current important properties in order
        important_contacts = session.query(FormField).filter(
            FormField.object_type == 'contacts',
            FormField.is_important.in_(['true', True, 1])
        ).order_by(FormField.order_index).all()
        
        important_memberships = session.query(FormField).filter(
            FormField.object_type == 'memberships',
            FormField.is_important.in_(['true', True, 1])
        ).order_by(FormField.order_index).all()
        
        print("Current Contact Properties in Order:")
        for prop in important_contacts:
            print(f"  {prop.order_index}: {prop.field_name}")
        
        print("Current Membership Properties in Order:")
        for prop in important_memberships:
            print(f"  {prop.order_index}: {prop.field_name}")
        
        # Get ACGI fields
        acgi_contact_fields_obj = session.query(AppState).filter_by(key='acgi_fields_contacts').first()
        acgi_membership_fields_obj = session.query(AppState).filter_by(key='acgi_fields_memberships').first()
        
        acgi_contact_fields = json.loads(acgi_contact_fields_obj.value) if acgi_contact_fields_obj else {}
        acgi_membership_fields = json.loads(acgi_membership_fields_obj.value) if acgi_membership_fields_obj else {}
        
        print(f"ACGI Contact Fields: {list(acgi_contact_fields.keys())}")
        print(f"ACGI Membership Fields: {list(acgi_membership_fields.keys())}")
        
        # Define correct mappings
        contact_mapping = {
            'customer_id': 'custId',
            'address': 'addresses', 
            'email': 'emails',
            'firstname': 'firstName',
            'lastname': 'lastName',
            'phone': 'phones'
        }
        
        membership_mapping = {
            'raw_subclass_code': 'subclassCd',
            'raw_class_code': 'classCd',
            'subgroup': 'subgroupName',
            'customer_id': 'customerId',
            'expiration_date': 'expireDate',
            'name': 'subgroupName'  # Map name to subgroupName as a reasonable default
        }
        
        # Generate contact mapping based on current order
        final_contact_mapping = {}
        for prop in important_contacts:
            if prop.field_name in contact_mapping:
                final_contact_mapping[prop.field_name] = contact_mapping[prop.field_name]
        
        # Generate membership mapping based on current order
        final_membership_mapping = {}
        for prop in important_memberships:
            if prop.field_name in membership_mapping:
                final_membership_mapping[prop.field_name] = membership_mapping[prop.field_name]
        
        print(f"\nNew Contact Mapping: {json.dumps(final_contact_mapping, indent=2)}")
        print(f"New Membership Mapping: {json.dumps(final_membership_mapping, indent=2)}")
        
        # Save to database
        ContactFieldMapping.set_mapping(final_contact_mapping)
        MembershipFieldMapping.set_mapping(final_membership_mapping)
        
        print("✅ Mappings updated successfully!")
        
        # Verify
        retrieved_contact = ContactFieldMapping.get_mapping()
        retrieved_membership = MembershipFieldMapping.get_mapping()
        
        print(f"Retrieved Contact Mapping: {json.dumps(retrieved_contact, indent=2)}")
        print(f"Retrieved Membership Mapping: {json.dumps(retrieved_membership, indent=2)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    fix_mappings() 