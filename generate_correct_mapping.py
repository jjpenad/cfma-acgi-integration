import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, ContactFieldMapping, MembershipFieldMapping, FormField, AppState

def generate_correct_mapping():
    session = get_session()
    try:
        print("=== GENERATING CORRECT MAPPING ===")
        
        # CONTACT MAPPING
        print("\n--- CONTACT MAPPING ---")
        acgi_contact_fields_obj = session.query(AppState).filter_by(key='acgi_fields_contacts').first()
        if not acgi_contact_fields_obj or not acgi_contact_fields_obj.value:
            print("❌ No ACGI contact fields found")
            return
            
        acgi_contact_fields = json.loads(acgi_contact_fields_obj.value)
        acgi_fields_list = list(acgi_contact_fields.keys())
        print(f"ACGI Contact Fields: {acgi_fields_list}")
        
        # Get important HubSpot properties in order (handle string boolean values)
        important_contacts = session.query(FormField).filter(
            FormField.object_type == 'contacts',
            FormField.is_important.in_(['true', True, 1])
        ).order_by(FormField.order_index).all()
        
        print(f"Important Contact Properties ({len(important_contacts)}):")
        for prop in important_contacts:
            print(f"  {prop.field_name} (order: {prop.order_index})")
        
        # Define the correct contact mapping based on the image
        correct_contact_mapping = {
            'customer_id': 'custId',
            'address': 'addresses', 
            'email': 'emails',
            'firstname': 'firstName',
            'lastname': 'lastName',
            'phone': 'phones'
        }
        
        # Generate contact mapping
        contact_mapping = {}
        for hubspot_prop in important_contacts:
            if hubspot_prop.field_name in correct_contact_mapping:
                acgi_field = correct_contact_mapping[hubspot_prop.field_name]
                contact_mapping[hubspot_prop.field_name] = acgi_field
                print(f"  {hubspot_prop.field_name} -> {acgi_field}")
        
        print(f"Contact mapping: {json.dumps(contact_mapping, indent=2)}")
        
        # Save contact mapping to database
        ContactFieldMapping.set_mapping(contact_mapping)
        print("✅ Contact mapping saved successfully!")
        
        # MEMBERSHIP MAPPING
        print("\n--- MEMBERSHIP MAPPING ---")
        acgi_membership_fields_obj = session.query(AppState).filter_by(key='acgi_fields_memberships').first()
        if acgi_membership_fields_obj and acgi_membership_fields_obj.value:
            acgi_membership_fields = json.loads(acgi_membership_fields_obj.value)
            acgi_membership_fields_list = list(acgi_membership_fields.keys())
            print(f"ACGI Membership Fields: {acgi_membership_fields_list}")
            
            # Get important HubSpot membership properties
            important_memberships = session.query(FormField).filter(
                FormField.object_type == 'memberships',
                FormField.is_important.in_(['true', True, 1])
            ).order_by(FormField.order_index).all()
            
            print(f"Important Membership Properties ({len(important_memberships)}):")
            for prop in important_memberships:
                print(f"  {prop.field_name} (order: {prop.order_index})")
            
            # Define the correct membership mapping based on the image
            correct_membership_mapping = {
                'raw_subclass_code': 'subclassCd',
                'raw_class_code': 'classCd',
                'subgroup': 'subgroupName',
                'customer_id': 'customerId',
                'expiration_date': 'expireDate'
            }
            
            # Generate membership mapping
            membership_mapping = {}
            for hubspot_prop in important_memberships:
                if hubspot_prop.field_name in correct_membership_mapping:
                    acgi_field = correct_membership_mapping[hubspot_prop.field_name]
                    membership_mapping[hubspot_prop.field_name] = acgi_field
                    print(f"  {hubspot_prop.field_name} -> {acgi_field}")
            
            print(f"Membership mapping: {json.dumps(membership_mapping, indent=2)}")
            
            # Save membership mapping to database
            MembershipFieldMapping.set_mapping(membership_mapping)
            print("✅ Membership mapping saved successfully!")
        else:
            print("❌ No ACGI membership fields found")
            
        # Verify both mappings
        print("\n--- VERIFICATION ---")
        retrieved_contact_mapping = ContactFieldMapping.get_mapping()
        retrieved_membership_mapping = MembershipFieldMapping.get_mapping()
        
        print(f"Retrieved contact mapping: {json.dumps(retrieved_contact_mapping, indent=2)}")
        print(f"Retrieved membership mapping: {json.dumps(retrieved_membership_mapping, indent=2)}")
        
        if contact_mapping == retrieved_contact_mapping:
            print("✅ Contact mapping verification successful!")
        else:
            print("❌ Contact mapping verification failed!")
            
        if membership_mapping == retrieved_membership_mapping:
            print("✅ Membership mapping verification successful!")
        else:
            print("❌ Membership mapping verification failed!")
            
    finally:
        session.close()

if __name__ == "__main__":
    generate_correct_mapping() 