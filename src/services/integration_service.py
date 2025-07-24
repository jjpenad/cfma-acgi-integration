import logging
from typing import Dict, List, Any
from src.services.acgi_client import ACGIClient
from src.services.hubspot_client import HubSpotClient
from src.services.data_mapper import DataMapper
from src.models import ContactFieldMapping, MembershipFieldMapping, get_app_credentials

logger = logging.getLogger(__name__)

class IntegrationService:
    def __init__(self):
        try:
            self.acgi_client = ACGIClient()
            self.hubspot_client = HubSpotClient()
            self.data_mapper = DataMapper()
            logger.info("IntegrationService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing IntegrationService: {str(e)}")
            raise
        
    def run_sync(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run synchronization based on the provided configuration
        
        Args:
            config: Dictionary containing sync configuration
                - customer_ids: Comma/newline separated customer IDs
                - sync_contacts: Boolean to sync contacts
                - sync_memberships: Boolean to sync memberships
                
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info("Starting synchronization process")
            
            # Get credentials
            creds = get_app_credentials()
            if not creds:
                return {'success': False, 'error': 'ACGI credentials not set'}
            
            # Parse customer IDs
            customer_ids = self._parse_customer_ids(config.get('customer_ids', ''))
            if not customer_ids:
                return {'success': False, 'error': 'No valid customer IDs provided'}
            
            # Prepare credentials for ACGI
            acgi_credentials = {
                'userid': creds['acgi_username'],
                'password': creds['acgi_password'],
                'environment': "cetdigitdev" if creds['acgi_environment'] == "test" else "cetdigit"
            }
            
            # Initialize HubSpot client
            hubspot_api_key = creds.get('hubspot_api_key')
            if not hubspot_api_key:
                return {'success': False, 'error': 'HubSpot API key not set'}
            
            if not self.hubspot_client.initialize_client(hubspot_api_key):
                return {'success': False, 'error': 'Failed to initialize HubSpot client'}
            
            # Get field mappings
            contact_mapping = ContactFieldMapping.get_mapping()
            membership_mapping = MembershipFieldMapping.get_mapping()
            print("MEMBERSHIP MAPPING 2",membership_mapping)
            results = {
                    'success': True,
                'total_customers': len(customer_ids),
                'contacts_synced': 0,
                'memberships_synced': 0,
                    'errors': []
                }
            
            # Log sync configuration for debugging
            logger.info(f"Sync configuration: contacts={config.get('sync_contacts')}, memberships={config.get('sync_memberships')}")
            
            # Process each customer
            for customer_id in customer_ids:
                customer_id = customer_id.strip()
                if not customer_id:
                    continue
                    
                logger.info(f"Processing customer ID: {customer_id}")
                
                try:
                    # Sync contacts if enabled
                    sync_contacts = config.get('sync_contacts', True)
                    logger.info(f"Sync contacts for customer {customer_id}: {sync_contacts}")
                    if sync_contacts:
                        contact_result = self._sync_contact(
                            customer_id, acgi_credentials, contact_mapping
                        )
                        if contact_result.get('success'):
                            results['contacts_synced'] += 1
                            logger.info(f"Successfully synced contact for customer {customer_id}")
                        else:
                            results['errors'].append(f"Customer {customer_id} - Contact: {contact_result.get('error')}")
                            logger.error(f"Failed to sync contact for customer {customer_id}: {contact_result.get('error')}")
                    else:
                        logger.info(f"Skipping contact sync for customer {customer_id} (disabled)")
                    
                    # Sync memberships if enabled
                    sync_memberships = config.get('sync_memberships', True)
                    logger.info(f"Sync memberships for customer {customer_id}: {sync_memberships}")
                    if sync_memberships:
                        membership_result = self._sync_membership(
                            customer_id, acgi_credentials, membership_mapping
                        )
                        if membership_result.get('success'):
                            results['memberships_synced'] += 1
                            logger.info(f"Successfully synced memberships for customer {customer_id}")
                        else:
                            results['errors'].append(f"Customer {customer_id} - Membership: {membership_result.get('error')}")
                            logger.error(f"Failed to sync memberships for customer {customer_id}: {membership_result.get('error')}")
                    else:
                        logger.info(f"Skipping membership sync for customer {customer_id} (disabled)")
                            
                except Exception as e:
                    error_msg = f"Customer {customer_id} - Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Sync completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in run_sync: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _parse_customer_ids(self, customer_ids_str: str) -> List[str]:
        """Parse customer IDs from string (comma or newline separated)"""
        if not customer_ids_str:
            return []
        
        # Split by comma or newline and clean up
        ids = []
        for line in customer_ids_str.replace(',', '\n').split('\n'):
            customer_id = line.strip()
            if customer_id:
                ids.append(customer_id)
        
        return ids
    
    def _sync_contact(self, customer_id: str, acgi_credentials: Dict, contact_mapping: Dict) -> Dict[str, Any]:
        """Sync a single contact from ACGI to HubSpot"""
        try:
            # Get customer data from ACGI
            acgi_result = self.acgi_client.get_customer_data(acgi_credentials, customer_id)
            if not acgi_result.get('success') or not acgi_result.get('customers'):
                return {'success': False, 'error': 'Failed to fetch customer data from ACGI'}
            
            acgi_customer = acgi_result['customers'][0]
            
            # Get search preference for contacts
            from src.models import SearchPreference, get_session
            session = get_session()
            try:
                search_pref = session.query(SearchPreference).filter_by(object_type='contacts').first()
                search_strategy = search_pref.search_strategy if search_pref else 'email_only'
                logger.info(f"Using search strategy: {search_strategy}")
            finally:
                session.close()
            
            # Map ACGI data to HubSpot format using saved mapping
            hubspot_contact = self._map_contact_data(acgi_customer, contact_mapping)
            
            # Create or update contact in HubSpot using the search strategy
            hubspot_result = self.hubspot_client.create_or_update_contact(hubspot_contact, search_strategy)
            
            if hubspot_result.get('success'):
                return {'success': True, 'hubspot_id': hubspot_result.get('id')}
            else:
                return {'success': False, 'error': hubspot_result.get('error', 'HubSpot sync failed')}
            
        except Exception as e:
            logger.error(f"Error syncing contact for customer {customer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_membership(self, customer_id: str, acgi_credentials: Dict, membership_mapping: Dict) -> Dict[str, Any]:
        """Sync memberships for a single customer from ACGI to HubSpot"""
        try:
            print("MEMBERSHIP MAPPING",membership_mapping)
            # Get memberships data from ACGI
            acgi_result = self.acgi_client.get_memberships_data(acgi_credentials, customer_id)
            print("ACGI RESULT",acgi_result)
            if not acgi_result.get('success'):
                return {'success': False, 'error': 'Failed to fetch memberships data from ACGI'}
            
            memberships_data = acgi_result.get('memberships', {})
            memberships_list = memberships_data.get('memberships', [])
            print("MEMBERSHIPS List",memberships_list)
            
            if not memberships_list:
                return {'success': False, 'error': 'No memberships found for customer'}
            
            # Process each membership
            synced_count = 0
            for membership in memberships_list:
                try:
                    # Map membership data to HubSpot format using saved mapping
                    hubspot_membership = self._map_membership_data(membership, membership_mapping)
                    
                    # Use the create_or_update_membership method which handles deduplication
                    hubspot_result = self.hubspot_client.create_or_update_membership(hubspot_membership)
                    print("HUBSPOT RESULT",hubspot_result)
                    
                    if hubspot_result.get('success'):
                        action = hubspot_result.get('action', 'processed')
                        print(f"Membership {action}: {hubspot_result.get('membership_id', 'N/A')}")
                        synced_count += 1
                    else:
                        logger.warning(f"Failed to sync membership: {hubspot_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error syncing individual membership: {str(e)}")
            
            if synced_count > 0:
                return {'success': True, 'memberships_synced': synced_count}
            else:
                return {'success': False, 'error': 'No memberships were successfully synced'}
            
        except Exception as e:
            logger.error(f"Error syncing memberships for customer {customer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _map_contact_data(self, acgi_customer: Dict, contact_mapping: Dict) -> Dict[str, Any]:
        """Map ACGI contact data to HubSpot format using saved mapping"""
        hubspot_contact = {}
        
        # Get ACGI preferences for selecting best data
        from src.models import AppState, get_session
        session = get_session()
        try:
            # Get email preference
            email_pref = session.query(AppState).filter_by(key='acgi_email_preference').first()
            email_preference = email_pref.value if email_pref else 'first_non_bad'
            
            # Get phone preference
            phone_pref = session.query(AppState).filter_by(key='acgi_phone_preference').first()
            phone_preference = phone_pref.value if phone_pref else 'first'
            
            # Get address preference
            address_pref = session.query(AppState).filter_by(key='acgi_address_preference').first()
            address_preference = address_pref.value if address_pref else 'first_non_bad'
            
            logger.info(f"ACGI preferences - Email: {email_preference}, Phone: {phone_preference}, Address: {address_preference}")
        finally:
            session.close()
        
        # Apply the saved mapping
        for hubspot_field, acgi_field in contact_mapping.items():
            if acgi_field in acgi_customer:
                value = acgi_customer[acgi_field]
                
                # Handle special field types
                if hubspot_field == 'email':
                    # Get the best email based on preference
                    emails = acgi_customer.get('emails', [])
                    if emails:
                        value = self._select_best_email(emails, email_preference)
                
                elif hubspot_field == 'phone':
                    # Get the best phone based on preference
                    phones = acgi_customer.get('phones', [])
                    if phones:
                        value = self._select_best_phone(phones, phone_preference)
                
                elif hubspot_field == 'address':
                    # Get the best address based on preference
                    addresses = acgi_customer.get('addresses', [])
                    if addresses:
                        value = self._select_best_address(addresses, address_preference)
                
                hubspot_contact[hubspot_field] = value
        
        return hubspot_contact
    
    def _map_membership_data(self, membership: Dict, membership_mapping: Dict) -> Dict[str, Any]:
        """Map ACGI membership data to HubSpot format using saved mapping"""
        hubspot_membership = {}
        
        # Apply the saved mapping
        for hubspot_field, acgi_field in membership_mapping.items():
            if acgi_field in membership:
                value = membership[acgi_field]
                
                # Handle date fields
                if 'date' in acgi_field.lower() and value:
                    try:
                        # Convert ACGI date format to HubSpot timestamp (matching HubSpot form logic)
                        if isinstance(value, str):
                            # Handle common ACGI date formats
                            if '/' in value:
                                # mm/dd/yyyy format
                                parts = value.split('/')
                                if len(parts) == 3:
                                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                                    # Use UTC to ensure midnight UTC (matching HubSpot form logic)
                                    from datetime import datetime, timezone
                                    # Create date at midnight UTC (month is 0-indexed in Python)
                                    date_obj = datetime.now(timezone.utc).replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
                                    value = int(date_obj.timestamp() * 1000)  # HubSpot expects milliseconds
                            elif '-' in value:
                                # yyyy-mm-dd format
                                date_parts = value.split('-')
                                if len(date_parts) == 3:
                                    year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                                    # Use UTC to ensure midnight UTC (matching HubSpot form logic)
                                    from datetime import datetime, timezone
                                    # Create date at midnight UTC (month is 0-indexed in Python)
                                    date_obj = datetime.now(timezone.utc).replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
                                    value = int(date_obj.timestamp() * 1000)  # HubSpot expects milliseconds
                    except Exception as e:
                        logger.warning(f"Could not parse date {value}: {str(e)}")
                
                hubspot_membership[hubspot_field] = value
        
        return hubspot_membership
    
    def _format_address(self, address_data: Dict) -> str:
        """Format address data into a single string"""
        parts = []
        
        if address_data.get('address1'):
            parts.append(address_data['address1'])
        if address_data.get('address2'):
            parts.append(address_data['address2'])
        if address_data.get('city'):
            parts.append(address_data['city'])
        if address_data.get('state'):
            parts.append(address_data['state'])
        if address_data.get('zip'):
            parts.append(address_data['zip'])
        if address_data.get('country'):
            parts.append(address_data['country'])
        
        return ', '.join(parts)

    def _select_best_email(self, emails: List[Dict], preference: str) -> str:
        """Select the best email based on preference"""
        if not emails:
            return ''
        
        if preference == 'first':
            return emails[0].get('email', '')
        elif preference == 'first_non_bad':
            for email_data in emails:
                if not email_data.get('isBad', False):
                    return email_data.get('email', '')
            # If no non-bad emails, return first
            return emails[0].get('email', '')
        elif preference == 'primary':
            for email_data in emails:
                if email_data.get('isPrimary', False):
                    return email_data.get('email', '')
            # If no primary, fall back to first non-bad
            return self._select_best_email(emails, 'first_non_bad')
        else:
            # Default to first non-bad
            return self._select_best_email(emails, 'first_non_bad')

    def _select_best_phone(self, phones: List[Dict], preference: str) -> str:
        """Select the best phone based on preference"""
        if not phones:
            return ''
        
        if preference == 'first':
            return phones[0].get('phone', '')
        elif preference == 'primary':
            for phone_data in phones:
                if phone_data.get('isPrimary', False):
                    return phone_data.get('phone', '')
            # If no primary, return first
            return phones[0].get('phone', '')
        elif preference == 'mobile':
            for phone_data in phones:
                if phone_data.get('type', '').lower() == 'mobile':
                    return phone_data.get('phone', '')
            # If no mobile, return first
            return phones[0].get('phone', '')
        else:
            # Default to first
            return phones[0].get('phone', '')

    def _select_best_address(self, addresses: List[Dict], preference: str) -> str:
        """Select the best address based on preference"""
        if not addresses:
            return ''
        
        if preference == 'first':
            return self._format_address(addresses[0])
        elif preference == 'first_non_bad':
            for addr_data in addresses:
                if not addr_data.get('isBad', False):
                    return self._format_address(addr_data)
            # If no non-bad addresses, return first
            return self._format_address(addresses[0])
        elif preference == 'primary':
            for addr_data in addresses:
                if addr_data.get('isPrimary', False):
                    return self._format_address(addr_data)
            # If no primary, fall back to first non-bad
            return self._select_best_address(addresses, 'first_non_bad')
        elif preference == 'billing':
            for addr_data in addresses:
                if addr_data.get('type', '').lower() == 'billing':
                    return self._format_address(addr_data)
            # If no billing, fall back to first non-bad
            return self._select_best_address(addresses, 'first_non_bad')
        else:
            # Default to first non-bad
            return self._select_best_address(addresses, 'first_non_bad') 