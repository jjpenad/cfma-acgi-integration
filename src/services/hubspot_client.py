import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import time

logger = logging.getLogger(__name__)

class HubSpotClient:
    """Client for interacting with HubSpot API using direct requests"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.hubapi.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ACGI-HubSpot-Integration/1.0'
        })
    
    def test_credentials(self, credentials: Dict[str, str]) -> Dict[str, any]:
        """Test HubSpot API key by making a simple API call"""
        try:
            api_key = credentials['api_key']
            
            # Test with a simple contacts list request
            url = f"{self.base_url}/crm/v3/objects/contacts?limit=1"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'HubSpot API key is valid',
                    'response': response.json()
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': 'Invalid HubSpot API key',
                    'response': response.text
                }
            else:
                return {
                    'success': False,
                    'message': f"HubSpot API error: {response.status_code} - {response.text}",
                    'response': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f"Network error: {str(e)}",
                'response': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Unexpected error: {str(e)}",
                'response': None
            }
    
    def initialize_client(self, api_key: str):
        """Initialize HubSpot client with API key"""
        try:
            self.api_key = api_key
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
            return True
        except Exception as e:
            logger.error(f"Failed to initialize HubSpot client: {str(e)}")
            return False
    
    def get_contact_properties(self) -> List[Dict[str, any]]:
        """Get all available contact properties from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/properties/contacts"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                properties = data.get('results', [])
                
                # Filter and format properties
                formatted_properties = []
                for prop in properties:
                    if prop.get('name') not in ['hs_object_id', 'createdate', 'lastmodifieddate']:
                        formatted_properties.append({
                            'name': prop.get('name', ''),
                            'label': prop.get('label', ''),
                            'type': prop.get('type', ''),
                            'fieldType': prop.get('fieldType', ''),
                            'groupName': prop.get('groupName', ''),
                            'description': prop.get('description', ''),
                            'options': prop.get('options', [])
                        })
                
                return formatted_properties
            else:
                logger.error(f"Failed to get contact properties: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting contact properties: {str(e)}")
            return []
        
    def create_order(self, order_data: Dict[str, any]) -> Dict[str, any]:
        """Create a new order in HubSpot"""
        try:    
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'HubSpot client not initialized',
                    'order_id': None
                }

            # Prepare order properties for HubSpot
            properties = {}

            print("ORDER DATA",order_data)

            # Add all form data as properties
            for key, value in order_data.items():
                if value:  # Only add non-empty values
                    properties[key] = value

            # Create order
            create_url = f"{self.base_url}/crm/v3/objects/orders"
            create_data = {'properties': properties}
            print("CREATE DATA",create_data)
            create_response = self.session.post(create_url, json=create_data, timeout=30)
            print("CREATE RESPONSE",create_response)
            
            if create_response.status_code == 201:
                new_order = create_response.json()
                order_id = new_order['id']
                print("NEW ORDER",new_order)
                return {
                    'success': True,
                    'message': f"Created new order {new_order}",
                    'order_id': order_id,
                    'action': 'created'
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to create order: {create_response.status_code} - {create_response.text}",
                    'order_id': None
                }
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return {
                'success': False,
                'message': f"Error creating order: {str(e)}",
                'order_id': None
            }
    

    def create_membership(self, membership_data: Dict[str, any]) -> Dict[str, any]:
        """Create a new membership in HubSpot"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'HubSpot client not initialized',
                    'membership_id': None
                }
            
            # Prepare membership properties for HubSpot
            properties = {}
            
            print("MEMBERSHIP DATA",membership_data)
            # Add all form data as properties
            for key, value in membership_data.items():
                if value:  # Only add non-empty values
                    # Ensure date fields are properly formatted for HubSpot
                    if 'date' in key.lower() and isinstance(value, str) and value.isdigit():
                        # Convert timestamp to ensure it's at midnight UTC
                        try:
                            timestamp = int(value)
                            # Convert to datetime and back to ensure midnight UTC
                            from datetime import datetime, timezone
                            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                            # Create new timestamp at midnight UTC
                            midnight_utc = datetime.now(timezone.utc).replace(
                                year=dt.year, 
                                month=dt.month, 
                                day=dt.day, 
                                hour=0, minute=0, second=0, microsecond=0
                            )
                            value = str(int(midnight_utc.timestamp() * 1000))
                            print(f"Converted date field {key}: {value}")
                        except Exception as e:
                            print(f"Error converting date field {key}: {e}")
                    
                    properties[key] = value

            # Create membership
            create_url = f"{self.base_url}/crm/v3/objects/2-46896622"
            create_data = {'properties': properties}
            print("CREATE DATA",create_data)
            create_response = self.session.post(create_url, json=create_data, timeout=30)
            print("CREATE RESPONSE",create_response)
            
            if create_response.status_code == 201:
                new_membership = create_response.json()
                membership_id = new_membership['id']
                print("NEW MEMBERSHIP",new_membership)
                return {
                    'success': True,
                    'message': f"Created new membership {new_membership}",
                    'membership_id': membership_id,
                    'action': 'created'
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to create membership: {create_response.status_code} - {create_response.text}",
                    'membership_id': None
                }       
            
        except Exception as e:
            logger.error(f"Error creating membership: {str(e)}")
            return {
                'success': False,
                'message': f"Error creating membership: {str(e)}",
                'membership_id': None
            }
    
    def get_event_properties(self) -> List[Dict[str, any]]:
        """Get all available event properties from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/properties/2-48134484"
            response = self.session.get(url, timeout=30)
            print("RESPONSE",response)
            if response.status_code == 200:
                data = response.json()
                properties = data.get('results', [])
                print("RESULT PROPERTIES",properties)

                formatted_properties = []
                for prop in properties:
                    if prop.get('name') not in ['hs_object_id', 'createdate', 'lastmodifieddate']:
                        formatted_properties.append({
                            'name': prop.get('name', ''),
                            'label': prop.get('label', ''),
                            'type': prop.get('type', ''),
                            'fieldType': prop.get('fieldType', ''),
                            'groupName': prop.get('groupName', ''),
                            'description': prop.get('description', ''),
                            'options': prop.get('options', [])
                        })
                
                return formatted_properties 
            else:
                logger.error(f"Failed to get event properties: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting event properties: {str(e)}")
            return []

    def get_order_properties(self) -> List[Dict[str, any]]:
        """Get all available order properties from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/properties/orders"
            response = self.session.get(url, timeout=30)
            print("RESPONSE",response)
            if response.status_code == 200:
                data = response.json()
                properties = data.get('results', [])
                print("RESULT PROPERTIES",properties)
                
                formatted_properties = []
                for prop in properties:
                    if prop.get('name') not in ['hs_object_id', 'createdate', 'lastmodifieddate']:
                        formatted_properties.append({
                            'name': prop.get('name', ''),
                            'label': prop.get('label', ''),
                            'type': prop.get('type', ''),
                            'fieldType': prop.get('fieldType', ''),
                            'groupName': prop.get('groupName', ''),
                            'description': prop.get('description', ''),
                            'options': prop.get('options', [])
                        })
                
                return formatted_properties
            else:
                logger.error(f"Failed to get order properties: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting order properties: {str(e)}")
            return []

    def get_membership_properties(self) -> List[Dict[str, any]]:
        """Get all available membership properties from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/properties/2-46896622"
            response = self.session.get(url, timeout=30)
            print("RESPONSE",response)
            if response.status_code == 200:
                data = response.json()
                properties = data.get('results', [])
                print("RESULT PROPERTIES",properties)
                # Filter and format properties  
                formatted_properties = []
                for prop in properties:
                    if prop.get('name') not in ['hs_object_id', 'createdate', 'lastmodifieddate']:
                        formatted_properties.append({
                            'name': prop.get('name', ''),
                            'label': prop.get('label', ''),
                            'type': prop.get('type', ''),
                            'fieldType': prop.get('fieldType', ''),
                            'groupName': prop.get('groupName', ''),
                            'description': prop.get('description', ''),
                            'options': prop.get('options', [])
                        })
                
                return formatted_properties
            else:
                logger.error(f"Failed to get membership properties: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting membership properties: {str(e)}")
            return []

    def get_custom_object_properties(self, object_type: str) -> List[Dict[str, any]]:
        """Get all available properties for a custom object from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/properties/{object_type}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                properties = data.get('results', [])
                
                # Filter and format properties
                formatted_properties = []
                for prop in properties:
                    if prop.get('name') not in ['hs_object_id', 'createdate', 'lastmodifieddate']:
                        formatted_properties.append({
                            'name': prop.get('name', ''),
                            'label': prop.get('label', ''),
                            'type': prop.get('type', ''),
                            'groupName': prop.get('groupName', ''),
                            'description': prop.get('description', ''),
                            'options': prop.get('options', [])
                        })
                
                return formatted_properties
            else:
                logger.error(f"Failed to get {object_type} properties: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting {object_type} properties: {str(e)}")
            return []

    def get_deal_properties(self) -> List[Dict[str, any]]:
        """Get all available deal properties from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/properties/deals"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                properties = data.get('results', [])
                
                # Filter and format properties
                formatted_properties = []
                for prop in properties:
                    if prop.get('name') not in ['hs_object_id', 'createdate', 'lastmodifieddate']:
                        formatted_properties.append({
                            'name': prop.get('name', ''),
                            'label': prop.get('label', ''),
                            'type': prop.get('type', ''),
                            'fieldType': prop.get('fieldType', ''),
                            'groupName': prop.get('groupName', ''),
                            'description': prop.get('description', ''),
                            'options': prop.get('options', [])
                        })
                
                return formatted_properties
            else:
                logger.error(f"Failed to get deal properties: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting deal properties: {str(e)}")
            return []
    
    def get_contacts(self, limit: int = 100) -> List[Dict[str, any]]:
        """Get contacts from HubSpot"""
        try:
            if not self.api_key:
                return []
            
            url = f"{self.base_url}/crm/v3/objects/contacts?limit={limit}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                contacts = data.get('results', [])
                
                formatted_contacts = []
                for contact in contacts:
                    formatted_contacts.append({
                        'id': contact.get('id'),
                        'properties': contact.get('properties', {})
                    })
                
                return formatted_contacts
            else:
                logger.error(f"Failed to get contacts: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting contacts: {str(e)}")
            return []
    
    def create_or_update_contact(self, contact_data: Dict[str, any], search_strategy: str = 'email_only') -> Dict[str, any]:
        """Create or update a contact in HubSpot"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'HubSpot client not initialized',
                    'contact_id': None
                }
            
            # Prepare contact properties for HubSpot
            properties = {}
            
            # Add all form data as properties
            for key, value in contact_data.items():
                if value:  # Only add non-empty values
                    # Ensure date fields are properly formatted for HubSpot
                    if 'date' in key.lower() and isinstance(value, str) and value.isdigit():
                        # Convert timestamp to ensure it's at midnight UTC
                        try:
                            timestamp = int(value)
                            # Convert to datetime and back to ensure midnight UTC
                            from datetime import datetime, timezone
                            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                            # Create new timestamp at midnight UTC
                            midnight_utc = datetime.now(timezone.utc).replace(
                                year=dt.year, 
                                month=dt.month, 
                                day=dt.day, 
                                hour=0, minute=0, second=0, microsecond=0
                            )
                            value = str(int(midnight_utc.timestamp() * 1000))
                            print(f"Converted date field {key}: {value}")
                        except Exception as e:
                            print(f"Error converting date field {key}: {e}")
                    
                    properties[key] = value
            
            # Always generate a unique ACGI customer ID (simulating ACGI record ID)
            # If user provided one, use it; otherwise generate a new one
            if properties.get('customer_id'):
                acgi_customer_id = properties['customer_id']
            else:
                # Generate a numeric customer ID (HubSpot expects numeric field)
                acgi_customer_id = int(time.time() * 1000) + int(str(uuid.uuid4().int)[:6])
                properties['customer_id'] = acgi_customer_id
            
            # Always set required ACGI properties
            properties['from_acgi'] = 'true'
            
            # Remove empty values
            properties = {k: v for k, v in properties.items() if v}
            
            # Search for existing contact based on strategy
            existing_contact = None
            email = properties.get('email')
            customer_id = properties.get('customer_id')
            
            if search_strategy == 'email_only':
                if email:
                    existing_contact = self._search_contact_by_email(email)
            elif search_strategy == 'customer_id_only':
                if customer_id:
                    existing_contact = self._search_contact_by_customer_id(customer_id)
            elif search_strategy == 'email_then_customer_id':
                if email:
                    existing_contact = self._search_contact_by_email(email)
                if not existing_contact and customer_id:
                    existing_contact = self._search_contact_by_customer_id(customer_id)
            elif search_strategy == 'customer_id_then_email':
                if customer_id:
                    existing_contact = self._search_contact_by_customer_id(customer_id)
                if not existing_contact and email:
                    existing_contact = self._search_contact_by_email(email)
            
            if existing_contact:
                # Update existing contact
                contact_id = existing_contact['id']
                update_url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
                update_data = {'properties': properties}
                
                update_response = self.session.patch(update_url, json=update_data, timeout=30)
                
                if update_response.status_code == 200:
                    updated_contact = update_response.json()
                    search_info = self._get_search_info(search_strategy, email, customer_id)
                    return {
                        'success': True,
                        'message': f"✅ Contact updated successfully!",
                        'details': f"Found existing contact using strategy: {search_info}. The contact now has ACGI customer ID: {acgi_customer_id}",
                        'contact_id': contact_id,
                        'acgi_customer_id': acgi_customer_id,
                        'action': 'updated',
                        'search_strategy': search_strategy,
                        'search_info': search_info,
                        'hubspot_response': updated_contact
                    }
                else:
                    return {
                        'success': False,
                        'message': f"❌ Failed to update contact",
                        'details': f"Error {update_response.status_code}: {update_response.text}",
                        'contact_id': None,
                        'acgi_customer_id': acgi_customer_id
                    }
            else:
                # Create new contact
                create_url = f"{self.base_url}/crm/v3/objects/contacts"
                create_data = {'properties': properties}
                
                create_response = self.session.post(create_url, json=create_data, timeout=30)
                
                if create_response.status_code == 201:
                    new_contact = create_response.json()
                    search_info = self._get_search_info(search_strategy, email, customer_id)
                    return {
                        'success': True,
                        'message': f"✅ New contact created successfully!",
                        'details': f"No existing contact found using strategy: {search_info}. A new contact was created with ACGI customer ID: {acgi_customer_id}",
                        'contact_id': new_contact['id'],
                        'acgi_customer_id': acgi_customer_id,
                        'action': 'created',
                        'search_strategy': search_strategy,
                        'search_info': search_info,
                        'hubspot_response': new_contact
                    }
                else:
                    return {
                        'success': False,
                        'message': f"❌ Failed to create contact",
                        'details': f"Error {create_response.status_code}: {create_response.text}",
                        'contact_id': None,
                        'acgi_customer_id': acgi_customer_id
                    }
                
        except Exception as e:
            logger.error(f"Error creating/updating contact: {str(e)}")
            return {
                'success': False,
                'message': f"❌ Error occurred while processing contact",
                'details': f"Unexpected error: {str(e)}",
                'contact_id': None,
                'acgi_customer_id': None
            }

    def _search_contact_by_email(self, email: str):
        """Search for contact by email"""
        try:
            search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
            search_data = {
                'filterGroups': [{
                    'filters': [{
                        'propertyName': 'email',
                        'operator': 'EQ',
                        'value': email
                    }]
                }],
                'limit': 1
            }
            
            search_response = self.session.post(search_url, json=search_data, timeout=30)
            if search_response.status_code == 200:
                search_results = search_response.json()
                if search_results.get('results'):
                    return search_results['results'][0]
            return None
        except Exception as e:
            logger.warning(f"Failed to search by email: {str(e)}")
            return None

    def _search_contact_by_customer_id(self, customer_id: str):
        """Search for contact by customer_id"""
        try:
            search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
            search_data = {
                'filterGroups': [{
                    'filters': [{
                        'propertyName': 'customer_id',
                        'operator': 'EQ',
                        'value': customer_id
                    }]
                }],
                'limit': 1
            }
            
            search_response = self.session.post(search_url, json=search_data, timeout=30)
            if search_response.status_code == 200:
                search_results = search_response.json()
                if search_results.get('results'):
                    return search_results['results'][0]
            return None
        except Exception as e:
            logger.warning(f"Failed to search by customer_id: {str(e)}")
            return None

    def _get_search_info(self, search_strategy: str, email: str, customer_id: str) -> str:
        """Get human-readable search information"""
        if search_strategy == 'email_only':
            return f"email only (searched for: {email})"
        elif search_strategy == 'customer_id_only':
            return f"customer_id only (searched for: {customer_id})"
        elif search_strategy == 'email_then_customer_id':
            return f"email then customer_id (searched for: {email}, then {customer_id})"
        elif search_strategy == 'customer_id_then_email':
            return f"customer_id then email (searched for: {customer_id}, then {email})"
        else:
            return f"unknown strategy: {search_strategy}"
    
    def create_deal(self, deal_data: Dict[str, any]) -> Dict[str, any]:
        """Create a new deal in HubSpot"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'HubSpot client not initialized',
                    'deal_id': None
                }
            
            # Prepare deal properties
            properties = {
                'dealname': deal_data.get('dealname', ''),
                'amount': deal_data.get('amount', ''),
                'dealstage': deal_data.get('dealstage', 'appointmentscheduled'),
                'pipeline': deal_data.get('pipeline', 'default'),
                'closedate': deal_data.get('closedate', ''),
                'description': deal_data.get('description', '')
            }
            
            # Add any additional custom properties
            for key, value in deal_data.items():
                if key not in ['dealname', 'amount', 'dealstage', 'pipeline', 'closedate', 'description', 'contact_id']:
                    if value:
                        properties[key] = value
            
            # Remove empty values
            properties = {k: v for k, v in properties.items() if v}
            
            # Create deal
            create_url = f"{self.base_url}/crm/v3/objects/deals"
            create_data = {'properties': properties}
            
            create_response = self.session.post(create_url, json=create_data, timeout=30)
            
            if create_response.status_code == 201:
                new_deal = create_response.json()
                deal_id = new_deal['id']
                
                # Associate with contact if provided
                if deal_data.get('contact_id'):
                    try:
                        association_url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}/associations/contacts/{deal_data['contact_id']}/deal_to_contact"
                        association_response = self.session.put(association_url, timeout=30)
                        
                        if association_response.status_code != 200:
                            logger.warning(f"Failed to associate deal with contact: {association_response.status_code} - {association_response.text}")
                    except Exception as e:
                        logger.warning(f"Failed to associate deal with contact: {str(e)}")
                
                return {
                    'success': True,
                    'message': f"Created new deal {deal_id}",
                    'deal_id': deal_id,
                    'action': 'created'
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to create deal: {create_response.status_code} - {create_response.text}",
                    'deal_id': None
                }
            
        except Exception as e:
            logger.error(f"Error creating deal: {str(e)}")
            return {
                'success': False,
                'message': f"Error creating deal: {str(e)}",
                'deal_id': None
            }
    
    def batch_create_or_update_contacts(self, contacts_data: List[Dict[str, any]]) -> Dict[str, any]:
        """Create or update multiple contacts in HubSpot"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'HubSpot client not initialized',
                    'results': []
                }
            
            results = []
            success_count = 0
            error_count = 0
            
            for contact_data in contacts_data:
                result = self.create_or_update_contact(contact_data)
                results.append(result)
                
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
            
            return {
                'success': True,
                'message': f"Processed {len(contacts_data)} contacts: {success_count} successful, {error_count} failed",
                'results': results,
                'success_count': success_count,
                'error_count': error_count
            }
            
        except Exception as e:
            logger.error(f"Error in batch contact processing: {str(e)}")
            return {
                'success': False,
                'message': f"Error in batch contact processing: {str(e)}",
                'results': []
            }
    
    def get_contact_by_email(self, email: str) -> Optional[Dict[str, any]]:
        """Get contact by email address"""
        try:
            if not self.api_key:
                return None
            
            search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
            search_data = {
                'filterGroups': [{
                    'filters': [{
                        'propertyName': 'email',
                        'operator': 'EQ',
                        'value': email
                    }]
                }],
                'limit': 1
            }
            
            response = self.session.post(search_url, json=search_data, timeout=30)
            
            if response.status_code == 200:
                search_results = response.json()
                if search_results.get('results'):
                    contact = search_results['results'][0]
                    return {
                        'id': contact['id'],
                        'properties': contact.get('properties', {})
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contact by email: {str(e)}")
            return None
    
    def get_contact_by_acgi_id(self, acgi_customer_id: str) -> Optional[Dict[str, any]]:
        """Get contact by ACGI customer ID"""
        try:
            if not self.api_key:
                return None
            
            search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
            search_data = {
                'filterGroups': [{
                    'filters': [{
                        'propertyName': 'acgi_customer_id',
                        'operator': 'EQ',
                        'value': acgi_customer_id
                    }]
                }],
                'limit': 1
            }
            
            response = self.session.post(search_url, json=search_data, timeout=30)
            
            if response.status_code == 200:
                search_results = response.json()
                if search_results.get('results'):
                    contact = search_results['results'][0]
                    return {
                        'id': contact['id'],
                        'properties': contact.get('properties', {})
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contact by ACGI ID: {str(e)}")
            return None

    def search_membership(self, customer_id: str, raw_class_code: str, subgroup: str, raw_subclass_code: str) -> Optional[Dict[str, any]]:
        """Search for existing membership by customer_id, raw_class_code, subgroup, and raw_subclass_code"""
        try:
            if not self.api_key:
                return None
            
            # Search for membership with the specified criteria
            url = f"{self.base_url}/crm/v3/objects/2-46896622/search"
            payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "customer_id",
                                "operator": "EQ",
                                "value": customer_id
                            },
                            {
                                "propertyName": "raw_class_code",
                                "operator": "EQ",
                                "value": raw_class_code
                            },
                            {
                                "propertyName": "subgroup",
                                "operator": "EQ",
                                "value": subgroup
                            },
                            {
                                "propertyName": "raw_subclass_code",
                                "operator": "EQ",
                                "value": raw_subclass_code
                            }
                        ]
                    }
                ],
                "properties": ["customer_id", "raw_class_code", "subgroup", "raw_subclass_code", "dealname", "amount"],
                "limit": 1
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    return results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching membership: {str(e)}")
            return None

    def update_membership(self, membership_id: str, membership_data: Dict[str, any]) -> Dict[str, any]:
        """Update existing membership in HubSpot"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'HubSpot client not initialized'}
            
            url = f"{self.base_url}/crm/v3/objects/2-46896622/{membership_id}"
            
            # Prepare properties for update
            properties = {}
            for key, value in membership_data.items():
                if value:  # Only add non-empty values
                    # Ensure date fields are properly formatted for HubSpot
                    if 'date' in key.lower() and isinstance(value, str) and value.isdigit():
                        # Convert timestamp to ensure it's at midnight UTC
                        try:
                            timestamp = int(value)
                            # Convert to datetime and back to ensure midnight UTC
                            from datetime import datetime, timezone
                            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                            # Create new timestamp at midnight UTC
                            midnight_utc = datetime.now(timezone.utc).replace(
                                year=dt.year, 
                                month=dt.month, 
                                day=dt.day, 
                                hour=0, minute=0, second=0, microsecond=0
                            )
                            value = str(int(midnight_utc.timestamp() * 1000))
                            print(f"Converted date field {key}: {value}")
                        except Exception as e:
                            print(f"Error converting date field {key}: {e}")
                    
                    properties[key] = value
            
            payload = {"properties": properties}
            
            response = self.session.patch(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': 'Membership updated successfully',
                    'membership_id': membership_id,
                    'hubspot_response': result
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update membership: {response.status_code} - {response.text}',
                    'hubspot_response': response.text
                }
                
        except Exception as e:
            logger.error(f"Error updating membership: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def create_or_update_membership(self, membership_data: Dict[str, any]) -> Dict[str, any]:
        """Create or update membership based on unique criteria (customer_id, raw_class_code, subgroup, raw_subclass_code)"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'HubSpot client not initialized'}
            
            # Extract the unique identifiers for searching
            customer_id = membership_data.get('customer_id', '')
            raw_class_code = membership_data.get('raw_class_code', '')
            subgroup = membership_data.get('subgroup', '')
            raw_subclass_code = membership_data.get('raw_subclass_code', '')
            
            if not all([customer_id, raw_class_code, subgroup, raw_subclass_code]):
                return {
                    'success': False, 
                    'error': 'Missing required fields for membership search: customer_id, raw_class_code, subgroup, raw_subclass_code'
                }
            
            # Search for existing membership
            existing_membership = self.search_membership(
                customer_id=customer_id,
                raw_class_code=raw_class_code,
                subgroup=subgroup,
                raw_subclass_code=raw_subclass_code
            )
            print("MEMBERSHIP DATA",membership_data)
            print("EXISTING MEMBERSHIP",existing_membership)
            
            if existing_membership:
                # Update existing membership
                membership_id = existing_membership['id']
                result = self.update_membership(membership_id, membership_data)
                if result['success']:
                    result['action'] = 'updated'
                    result['membership_id'] = membership_id
                return result
            else:
                # Create new membership
                result = self.create_membership(membership_data)
                if result['success']:
                    result['action'] = 'created'
                return result
                
        except Exception as e:
            logger.error(f"Error in create_or_update_membership: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            } 

    def create_custom_object(self, object_type: str, object_data: Dict[str, any]) -> Dict[str, any]:
        """Create a custom object in HubSpot"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'HubSpot client not initialized'}
            
            url = f"{self.base_url}/crm/v3/objects/{object_type}"
            
            # Prepare properties, filtering out empty values
            properties = {}
            for key, value in object_data.items():
                if value:  # Only add non-empty values
                    # Ensure date fields are properly formatted for HubSpot
                    if 'date' in key.lower() and isinstance(value, str) and value.isdigit():
                        # Convert timestamp to ensure it's at midnight UTC
                        try:
                            timestamp = int(value)
                            # Convert to datetime and back to ensure midnight UTC
                            from datetime import datetime, timezone
                            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                            # Create new timestamp at midnight UTC
                            midnight_utc = datetime.now(timezone.utc).replace(
                                year=dt.year, 
                                month=dt.month, 
                                day=dt.day, 
                                hour=0, minute=0, second=0, microsecond=0
                            )
                            value = str(int(midnight_utc.timestamp() * 1000))
                            print(f"Converted date field {key}: {value}")
                        except Exception as e:
                            print(f"Error converting date field {key}: {e}")
                    
                    properties[key] = value
            
            payload = {"properties": properties}
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'message': f'{object_type} created successfully',
                    'object_id': result.get('id'),
                    'hubspot_response': result
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to create {object_type}: {response.status_code} - {response.text}',
                    'hubspot_response': response.text
                }
                
        except Exception as e:
            logger.error(f"Error creating {object_type}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            } 