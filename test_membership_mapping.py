import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, MembershipFieldMapping, FormField, AppState

def test_membership_mapping():
    session = get_session()
    try:
        print("=== TESTING MEMBERSHIP MAPPING ===")
        
        # Check current membership mapping
        membership_mapping = session.query(MembershipFieldMapping).first()
        print(f"Current membership mapping: {membership_mapping.mapping if membership_mapping else 'None'}")
        
        # Check ACGI membership fields
        acgi_membership_fields_obj = session.query(AppState).filter_by(key='acgi_fields_memberships').first()
        if acgi_membership_fields_obj and acgi_membership_fields_obj.value:
            acgi_fields = json.loads(acgi_membership_fields_obj.value)
            print(f"ACGI Membership Fields: {list(acgi_fields.keys())}")
        else:
            print("No ACGI membership fields found")
        
        # Check important HubSpot membership properties
        important_memberships = session.query(FormField).filter(
            FormField.object_type == 'memberships',
            FormField.is_important.in_(['true', True, 1])
        ).order_by(FormField.order_index).all()
        
        print(f"Important Membership Properties ({len(important_memberships)}):")
        for prop in important_memberships:
            print(f"  {prop.field_name} (order: {prop.order_index}, important: {prop.is_important})")
        
        # Generate expected mapping
        if acgi_membership_fields_obj and important_memberships:
            correct_mapping = {
                'raw_subclass_code': 'subclassCd',
                'raw_class_code': 'classCd',
                'subgroup': 'subgroupName',
                'customer_id': 'customerId',
                'expiration_date': 'expireDate'
            }
            
            expected_mapping = {}
            for prop in important_memberships:
                if prop.field_name in correct_mapping:
                    expected_mapping[prop.field_name] = correct_mapping[prop.field_name]
            
            print(f"Expected mapping: {json.dumps(expected_mapping, indent=2)}")
            
            # Update the mapping
            MembershipFieldMapping.set_mapping(expected_mapping)
            print("✅ Membership mapping updated!")
            
            # Verify
            updated_mapping = MembershipFieldMapping.get_mapping()
            print(f"Updated mapping: {json.dumps(updated_mapping, indent=2)}")
            
    finally:
        session.close()

if __name__ == "__main__":
    test_membership_mapping() 