import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import get_session, ContactFieldMapping, MembershipFieldMapping, FormField, AppState

def test_mapping_generation():
    session = get_session()
    try:
        print("=== TESTING MAPPING GENERATION ===")
        
        # Simulate ACGI contact fields
        acgi_contact_fields = {
            "firstName": "John",
            "lastName": "Doe", 
            "emailAddress": "john@example.com",
            "phoneNumber": "123-456-7890",
            "companyName": "ACME Corp"
        }
        
        # Simulate important HubSpot properties
        important_hubspot_properties = [
            {"name": "firstname", "order_index": 0},
            {"name": "lastname", "order_index": 1},
            {"name": "email", "order_index": 2},
            {"name": "phone", "order_index": 3}
        ]
        
        print(f"ACGI Contact Fields: {list(acgi_contact_fields.keys())}")
        print(f"Important HubSpot Properties: {[p['name'] for p in important_hubspot_properties]}")
        
        # Generate mapping based on order
        mapping = {}
        acgi_fields = list(acgi_contact_fields.keys())
        max_length = min(len(acgi_fields), len(important_hubspot_properties))
        
        for i in range(max_length):
            acgi_field = acgi_fields[i]
            hubspot_property = important_hubspot_properties[i]
            mapping[hubspot_property['name']] = acgi_field
            print(f"Mapping {i}: {hubspot_property['name']} -> {acgi_field}")
        
        print(f"\nFinal mapping: {json.dumps(mapping, indent=2)}")
        
        # Test saving to database
        print("\n=== SAVING TO DATABASE ===")
        ContactFieldMapping.set_mapping(mapping)
        print("Contact mapping saved successfully")
        
        # Test retrieving from database
        retrieved_mapping = ContactFieldMapping.get_mapping()
        print(f"Retrieved mapping: {json.dumps(retrieved_mapping, indent=2)}")
        
        # Verify they match
        if mapping == retrieved_mapping:
            print("✅ Mapping saved and retrieved successfully!")
        else:
            print("❌ Mapping mismatch!")
            
    finally:
        session.close()

if __name__ == "__main__":
    test_mapping_generation() 