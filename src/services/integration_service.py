import logging
import re
from typing import Dict, List, Any
from src.services.acgi_client import ACGIClient
from datetime import datetime, timezone
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
            from src.models import PurchasedProductsFieldMapping, EventFieldMapping
            orders_mapping = PurchasedProductsFieldMapping.get_mapping()
            events_mapping = EventFieldMapping.get_mapping()
            print("MEMBERSHIP MAPPING 2",membership_mapping)
            print("ORDERS MAPPING 2",orders_mapping)
            print("EVENTS MAPPING 2",events_mapping)
            results = {
                    'success': True,
                'total_customers': len(customer_ids),
                'contacts_synced': 0,
                'memberships_synced': 0,
                'orders_synced': 0,
                'events_synced': 0,
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
                    
                    # Sync orders if enabled
                    sync_orders = config.get('sync_orders', True)
                    logger.info(f"Sync orders for customer {customer_id}: {sync_orders}")
                    if sync_orders:
                        orders_result = self._sync_orders(customer_id, acgi_credentials, orders_mapping)
                        if orders_result.get('success'):
                            results['orders_synced'] += orders_result.get('total_processed', 0)
                            logger.info(f"Successfully synced orders for customer {customer_id}: {orders_result.get('total_processed', 0)} processed")
                        else:
                            results['errors'].append(f"Customer {customer_id} - Orders: {orders_result.get('error')}")
                            logger.error(f"Failed to sync orders for customer {customer_id}: {orders_result.get('error')}")
                    else:
                        logger.info(f"Skipping orders sync for customer {customer_id} (disabled)")
                    
                    # Sync events if enabled
                    sync_events = config.get('sync_events', True)
                    logger.info(f"Sync events for customer {customer_id}: {sync_events}")
                    if sync_events:
                        events_result = self._sync_events(customer_id, acgi_credentials, events_mapping)
                        if events_result.get('success'):
                            results['events_synced'] += events_result.get('total_processed', 0)
                            logger.info(f"Successfully synced events for customer {customer_id}: {events_result.get('total_processed', 0)} processed")
                        else:
                            results['errors'].append(f"Customer {customer_id} - Events: {events_result.get('error')}")
                            logger.error(f"Failed to sync events for customer {customer_id}: {events_result.get('error')}")
                    else:
                        logger.info(f"Skipping events sync for customer {customer_id} (disabled)")
                            
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
            print("CONTACT MAPPING",contact_mapping)
            print("ACGI CUSTOMER",acgi_customer)
            print("HUBSPOT CONTACT",hubspot_contact)
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
            return emails[0].get('address', '')
        elif preference == 'first_non_bad':
            for email_data in emails:
                # if not email_data.get('isBad', False):
                return email_data.get('address', '')
            # If no non-bad emails, return first
            return emails[0].get('address', '')
        elif preference == 'primary':
            for email_data in emails:
                if email_data.get('isPrimary', False):
                    return email_data.get('address', '')
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
            return phones[0].get('number', '')
        elif preference == 'primary':
            for phone_data in phones:
                if phone_data.get('isPrimary', False):
                    return phone_data.get('number', '')
            # If no primary, return first
            return phones[0].get('number', '')
        elif preference == 'mobile':
            for phone_data in phones:
                if phone_data.get('type', '').lower() == 'mobile':
                    return phone_data.get('number', '')
            # If no mobile, return first
            return phones[0].get('number', '')
        else:
            # Default to first
            return phones[0].get('number', '')

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
    
    def _sync_orders(self, customer_id: str, acgi_credentials: Dict, orders_mapping: Dict) -> Dict[str, Any]:
        """Sync orders for a single customer from ACGI to HubSpot"""
        try:
            # Get orders data from ACGI
            acgi_result = self.acgi_client.get_purchased_products(acgi_credentials, customer_id)
            print("ACGI RESULT TEST",acgi_result)
            if not acgi_result.get('success'):
                return {'success': False, 'error': 'Failed to fetch orders data from ACGI'}
            
            orders_data = acgi_result.get('purchased_products', {})
            orders_list = orders_data.get('purchased_products', [])
            print("ORDERS LIST",orders_list)
            if not orders_list:
                return {'success': False, 'error': 'No orders found for customer'}
            
            # Process each order
            synced_count = 0
            updated_count = 0
            for order in orders_list:
                try:
                    # Map order data to HubSpot format using saved mapping
                    hubspot_order = self._map_order_data(order, orders_mapping)
                    
                    # Use orderSerno as the unique identifier for deduplication
                    order_serial = order.get('orderSerno')
                    if not order_serial:
                        logger.warning(f"Order missing orderSerno, skipping: {order}")
                        continue
                    
                    # Create or update order in HubSpot custom object using orderSerno for deduplication
                    hubspot_result = self.hubspot_client.create_or_update_custom_object(
                        '2-48354706', 
                        hubspot_order, 
                        'order_id', 
                        order_serial
                    )
                    
                    if hubspot_result.get('success'):
                        action = hubspot_result.get('action', 'unknown')
                        if action == 'created':
                            logger.info(f"Order created successfully: {hubspot_result.get('id')}")
                            synced_count += 1
                        elif action == 'updated':
                            logger.info(f"Order updated successfully: {hubspot_result.get('id')}")
                            updated_count += 1
                    else:
                        logger.error(f"Failed to sync order: {hubspot_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Error processing order: {str(e)}")
            
            total_processed = synced_count + updated_count
            if total_processed > 0:
                return {
                    'success': True, 
                    'synced_count': synced_count,
                    'updated_count': updated_count,
                    'total_processed': total_processed
                }
            else:
                return {'success': False, 'error': 'No orders were successfully synced'}
                
        except Exception as e:
            logger.error(f"Error syncing orders for customer {customer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_events(self, customer_id: str, acgi_credentials: Dict, events_mapping: Dict) -> Dict[str, Any]:
        """Sync events for a single customer from ACGI to HubSpot"""
        try:
            # Get events data from ACGI
            acgi_registrations_result = self.acgi_client.get_customer_registrations_to_events(acgi_credentials, customer_id)
            acgi_registrations = acgi_registrations_result['registrations']['registrations']
            if not acgi_registrations:
                print(f"No registrations found for customer {customer_id}")
                logger.info(f"No registrations found for customer {customer_id}")
                return {'success': False, 'error': f'No registrations found for customer {customer_id}'}
            logger.info(f"Found {len(acgi_registrations)} registrations for customer {customer_id}")
            
            # Map ACGI data to HubSpot format using saved mapping
            hubspot_registrations = []
            hubspot_events = {}
            for acgi_registration in acgi_registrations:
                hubspot_registration = self._map_registration_data(acgi_registration)
                if hubspot_registration:
                    hubspot_registrations.append(hubspot_registration)

                # get event data from acgi only if not already in hubspot_events
                if acgi_registration['eventId'] not in hubspot_events:
                    acgi_event_result = self.acgi_client.get_event_by_id(acgi_credentials, acgi_registration['eventId'])
                    if acgi_event_result.get('success'):
                        acgi_event = acgi_event_result['event']
                        hubspot_event = self._map_event_data(acgi_event, events_mapping)
                        hubspot_events[hubspot_event['acgi_event_id']] = hubspot_event
                    else:
                        logger.error(f"Failed to fetch event data for registration {acgi_registration['regiSerno']}: {acgi_event_result.get('error')}")
            
            hubspot_events = list(hubspot_events.values())
            print("HUBSPOT REGISTRATIONS",hubspot_registrations)
            print("HUBSPOT EVENTS",hubspot_events)

            if not hubspot_events:
                return {'success': False, 'error': 'No valid events data to sync'}
            
            # Sync each event to HubSpot
            synced_count = 0
            errors = []
            
            for hubspot_event in hubspot_events:
                try:
                    # Search for existing event to avoid duplicates
                    logger.info( "hubspot_event", hubspot_event)
                    print("hubspot_event", hubspot_event)
                    existing_event = self.hubspot_client.search_custom_object('2-48134484', 'acgi_event_id', hubspot_event.get('acgi_event_id'))
                    logger.info( "existing_event", existing_event)
                    print("existing_event", existing_event)
                    if existing_event:
                        # Update existing event
                        acgi_event_id = existing_event['id']
                        update_result = self.hubspot_client.update_custom_object('2-48134484', acgi_event_id, hubspot_event)
                        if update_result.get('success'):
                            synced_count += 1
                            logger.info(f"Updated event {acgi_event_id} for customer {customer_id}")
                        else:
                            errors.append(f"Failed to update event: {update_result.get('error')}")
                    else:
                        # Create new event
                        create_result = self.hubspot_client.create_custom_object('2-48134484', hubspot_event)
                        if create_result.get('success'):
                            synced_count += 1
                            logger.info(f"Created new event for customer {customer_id}")
                        else:
                            errors.append(f"Failed to create event: {create_result.get('error')}")
                            
                except Exception as e:
                    error_msg = f"Error syncing event: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            for hubspot_registration in hubspot_registrations:
                try:
                    # Search for existing registration to avoid duplicates
                    logger.info( "hubspot_registration", hubspot_registration)
                    existing_registration = self.hubspot_client.search_custom_object('2-49619799', 'registration_id', hubspot_registration.get('registration_id'))
                    logger.info( "existing_registration", existing_registration)
                    if existing_registration:
                        # Update existing registration
                        registration_id = existing_registration['id']
                        update_result = self.hubspot_client.update_custom_object('2-49619799', registration_id, hubspot_registration)
                        if update_result.get('success'):
                            synced_count += 1
                            logger.info(f"Updated registration {registration_id} for customer {customer_id}")
                        else:
                            errors.append(f"Failed to update registration: {update_result.get('error')}")
                    else:
                        # Create new registration
                        create_result = self.hubspot_client.create_custom_object('2-49619799', hubspot_registration)
                        if create_result.get('success'):
                            synced_count += 1
                            logger.info(f"Created new registration for customer {customer_id}")
                        else:
                            errors.append(f"Failed to create registration: {create_result.get('error')}")
                except Exception as e:
                    error_msg = f"Error syncing registration: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            if errors:
                logger.warning(f"Completed events sync with {len(errors)} errors: {errors}")
            
            return {
                'success': True,
                'total_processed': len(hubspot_events) + len(hubspot_registrations),
                "total_events_processed": len(hubspot_events),
                "total_registrations_processed": len(hubspot_registrations),
                'synced_count': synced_count,
                "synced_events_count": synced_events_count,
                "synced_registrations_count": synced_registrations_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error syncing events for customer {customer_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_contacts_batch(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync contacts for multiple customers in batch with dedicated HubSpot client"""
        try:
            logger.info(f"Starting batch contacts sync for {len(customer_ids)} customers")
            
            # Get credentials with contacts-specific API key
            creds = get_app_credentials()
            if not creds:
                return {'success': False, 'error': 'ACGI credentials not set'}
            
            # Use contacts-specific HubSpot API key if available
            hubspot_api_key = creds.get('hubspot_api_key_contacts') or creds.get('hubspot_api_key')
            if not hubspot_api_key:
                return {'success': False, 'error': 'HubSpot API key not set for contacts'}
            
            # Initialize dedicated HubSpot client for this thread
            if not self.hubspot_client.initialize_client(hubspot_api_key):
                return {'success': False, 'error': 'Failed to initialize HubSpot client for contacts'}
            
            # Get field mappings
            contact_mapping = ContactFieldMapping.get_mapping()
            
            # Prepare ACGI credentials
            acgi_credentials = {
                'userid': creds['acgi_username'],
                'password': creds['acgi_password'],
                'environment': "cetdigitdev" if creds['acgi_environment'] == "test" else "cetdigit"
            }
            
            results = {
                'success': True,
                'total_customers': len(customer_ids),
                'total_processed': 0,
                'errors': []
            }
            
            # Process each customer
            for customer_id in customer_ids:
                customer_id = customer_id.strip()
                if not customer_id:
                    continue
                    
                logger.info(f"Processing contact for customer ID: {customer_id}")
                
                try:
                    contact_result = self._sync_contact(customer_id, acgi_credentials, contact_mapping)
                    if contact_result.get('success'):
                        results['total_processed'] += 1
                        logger.info(f"Successfully synced contact for customer {customer_id}")
                    else:
                        results['errors'].append(f"Customer {customer_id} - Contact: {contact_result.get('error')}")
                        logger.error(f"Failed to sync contact for customer {customer_id}: {contact_result.get('error')}")
                            
                except Exception as e:
                    error_msg = f"Customer {customer_id} - Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Batch contacts sync completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch contacts sync: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_memberships_batch(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync memberships for multiple customers in batch with dedicated HubSpot client"""
        try:
            logger.info(f"Starting batch memberships sync for {len(customer_ids)} customers")
            
            # Get credentials with memberships-specific API key
            creds = get_app_credentials()
            if not creds:
                return {'success': False, 'error': 'ACGI credentials not set'}
            
            # Use memberships-specific HubSpot API key if available
            hubspot_api_key = creds.get('hubspot_api_key_memberships') or creds.get('hubspot_api_key')
            if not hubspot_api_key:
                return {'success': False, 'error': 'HubSpot API key not set for memberships'}
            
            # Initialize dedicated HubSpot client for this thread
            if not self.hubspot_client.initialize_client(hubspot_api_key):
                return {'success': False, 'error': 'Failed to initialize HubSpot client for memberships'}
            
            # Get field mappings
            membership_mapping = MembershipFieldMapping.get_mapping()
            
            # Prepare ACGI credentials
            acgi_credentials = {
                'userid': creds['acgi_username'],
                'password': creds['acgi_password'],
                'environment': "cetdigitdev" if creds['acgi_environment'] == "test" else "cetdigit"
            }
            
            results = {
                'success': True,
                'total_customers': len(customer_ids),
                'total_processed': 0,
                'errors': []
            }
            
            # Process each customer
            for customer_id in customer_ids:
                customer_id = customer_id.strip()
                if not customer_id:
                    continue
                    
                logger.info(f"Processing memberships for customer ID: {customer_id}")
                
                try:
                    membership_result = self._sync_membership(customer_id, acgi_credentials, membership_mapping)
                    if membership_result.get('success'):
                        results['total_processed'] += 1
                        logger.info(f"Successfully synced memberships for customer {customer_id}")
                    else:
                        results['errors'].append(f"Customer {customer_id} - Membership: {membership_result.get('error')}")
                        logger.error(f"Failed to sync memberships for customer {customer_id}: {membership_result.get('error')}")
                            
                except Exception as e:
                    error_msg = f"Customer {customer_id} - Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Batch memberships sync completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch memberships sync: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_orders_batch(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync orders for multiple customers in batch with dedicated HubSpot client"""
        try:
            logger.info(f"Starting batch orders sync for {len(customer_ids)} customers")
            
            # Get credentials with orders-specific API key
            creds = get_app_credentials()
            if not creds:
                return {'success': False, 'error': 'ACGI credentials not set'}
            
            # Use orders-specific HubSpot API key if available
            hubspot_api_key = creds.get('hubspot_api_key_orders') or creds.get('hubspot_api_key')
            if not hubspot_api_key:
                return {'success': False, 'error': 'HubSpot API key not set for orders'}
            
            # Initialize dedicated HubSpot client for this thread
            if not self.hubspot_client.initialize_client(hubspot_api_key):
                return {'success': False, 'error': 'Failed to initialize HubSpot client for orders'}
            
            # Get field mappings
            from src.models import PurchasedProductsFieldMapping
            orders_mapping = PurchasedProductsFieldMapping.get_mapping()
            
            # Prepare ACGI credentials
            acgi_credentials = {
                'userid': creds['acgi_username'],
                'password': creds['acgi_password'],
                'environment': "cetdigitdev" if creds['acgi_environment'] == "test" else "cetdigit"
            }
            
            results = {
                'success': True,
                'total_customers': len(customer_ids),
                'total_processed': 0,
                'errors': []
            }
            
            # Process each customer
            for customer_id in customer_ids:
                customer_id = customer_id.strip()
                if not customer_id:
                    continue
                    
                logger.info(f"Processing orders for customer ID: {customer_id}")
                
                try:
                    orders_result = self._sync_orders(customer_id, acgi_credentials, orders_mapping)
                    if orders_result.get('success'):
                        results['total_processed'] += orders_result.get('total_processed', 0)
                        logger.info(f"Successfully synced orders for customer {customer_id}: {orders_result.get('total_processed', 0)} processed")
                    else:
                        results['errors'].append(f"Customer {customer_id} - Orders: {orders_result.get('error')}")
                        logger.error(f"Failed to sync orders for customer {customer_id}: {orders_result.get('error')}")
                            
                except Exception as e:
                    error_msg = f"Customer {customer_id} - Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Batch orders sync completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch orders sync: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _sync_events_batch(self, customer_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync events for multiple customers in batch with dedicated HubSpot client"""
        try:
            logger.info(f"Starting batch events sync for {len(customer_ids)} customers")
            
            # Get credentials with events-specific API key
            creds = get_app_credentials()
            if not creds:
                return {'success': False, 'error': 'ACGI credentials not set'}
            
            # Use events-specific HubSpot API key if available
            hubspot_api_key = creds.get('hubspot_api_key_events') or creds.get('hubspot_api_key')
            if not hubspot_api_key:
                return {'success': False, 'error': 'HubSpot API key not set for events'}
            
            # Initialize dedicated HubSpot client for this thread
            if not self.hubspot_client.initialize_client(hubspot_api_key):
                return {'success': False, 'error': 'Failed to initialize HubSpot client for events'}
            
            # Get field mappings
            from src.models import EventFieldMapping
            events_mapping = EventFieldMapping.get_mapping()

            print( "events_mapping", events_mapping)
            
            # Prepare ACGI credentials
            acgi_credentials = {
                'userid': creds['acgi_username'],
                'password': creds['acgi_password'],
                'environment': "cetdigitdev" if creds['acgi_environment'] == "test" else "cetdigit"
            }
            
            results = {
                'success': True,
                'total_customers': len(customer_ids),
                'total_processed': 0,
                'errors': []
            }
            
            # Process each customer
            for customer_id in customer_ids:
                customer_id = customer_id.strip()
                if not customer_id:
                    continue
                    
                logger.info(f"Processing events for customer ID: {customer_id}")
                
                try:
                    events_result = self._sync_events(customer_id, acgi_credentials, events_mapping)
                    if events_result.get('success'):
                        results['total_processed'] += events_result.get('total_processed', 0)
                        logger.info(f"Successfully synced events for customer {customer_id}: {events_result.get('total_processed', 0)} processed")
                    else:
                        results['errors'].append(f"Customer {customer_id} - Events: {events_result.get('error')}")
                        logger.error(f"Failed to sync events for customer {customer_id}: {events_result.get('error')}")
                            
                except Exception as e:
                    error_msg = f"Customer {customer_id} - Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Batch events sync completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch events sync: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _map_order_data(self, order: Dict, orders_mapping: Dict) -> Dict[str, Any]:
        """Map ACGI order data to HubSpot format using saved mapping"""
        hubspot_order = {}
        
        # Apply the saved mapping
        for hubspot_field, acgi_field in orders_mapping.items():
            if acgi_field in order:
                value = order[acgi_field]
                
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
                
                hubspot_order[hubspot_field] = value
        
        return hubspot_order
    
    def _map_event_data(self, event: Dict, events_mapping: Dict) -> Dict[str, Any]:
        """Map ACGI event data to HubSpot format using saved mapping"""
        hubspot_event = {}
        
        # Apply the saved mapping
        for hubspot_field, acgi_field in events_mapping.items():
            if acgi_field in event:
                value = event[acgi_field]
                
                # Handle date fields
                if 'date' in acgi_field.lower() or 'dt' in acgi_field.lower() and value:
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
                                    # Create date at midnight UTC (month is 0-indexed in Python)
                                    date_obj = datetime.now(timezone.utc).replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
                                    value = int(date_obj.timestamp() * 1000)  # HubSpot expects milliseconds
                            elif '-' in value:
                                # yyyy-mm-dd format
                                date_parts = value.split('-')
                                if len(date_parts) == 3:
                                    year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                                    # Use UTC to ensure midnight UTC (matching HubSpot form logic)
                                    
                                    # Create date at midnight UTC (month is 1-indexed in Python)
                                    date_obj = datetime.now(timezone.utc).replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
                                    value = int(date_obj.timestamp() * 1000)  # HubSpot expects milliseconds
                            elif re.match(r'^\d{14}$', value):
                                # handle format 20121004800000 (YYYYMMDDHHMMSS)
                                # Validate year is within reasonable range (1900-2099)
                                year = int(value[:4])
                                if year < 1900 or year > 2099:
                                    logger.warning(f"Invalid year {year} in date {value}, skipping date parsing")
                                    continue
                                month = int(value[4:6])  # Month is 1-indexed in Python datetime
                                day = int(value[6:8])
                                hours = int(value[8:10])
                                minutes = int(value[10:12])
                                seconds = int(value[12:14])
                                date_obj = datetime.now(timezone.utc).replace(year=year, month=month, day=day, hour=hours, minute=minutes, second=seconds, microsecond=0)
                                value = int(date_obj.timestamp() * 1000)  # HubSpot expects milliseconds
                            
                    except Exception as e:
                        logger.warning(f"Could not parse date {value}: {str(e)}")
                
                hubspot_event[hubspot_field] = value
        
        return hubspot_event 


    def _map_registration_data(self, registration: Dict) -> Dict[str, Any]:
        """Map ACGI registration data to HubSpot format using saved mapping"""
        hubspot_registration = {}

        # convert registration['registration-date'] to milisenconds in at midnight UTC. Comes in format 02/01/2011
        # Ensure registration date is set to midnight UTC
        registration_date = datetime.strptime(registration['registrationDate'], '%m/%d/%Y')
        # Convert to UTC timezone
        registration_date = registration_date.replace(tzinfo=timezone.utc)
        # Set to midnight UTC
        registration_date = registration_date.replace(hour=0, minute=0, second=0, microsecond=0)
        registration_date = int(registration_date.timestamp() * 1000)
        
        # Apply the saved mapping
        result = {
            "name": registration['registrationName'] + "-" + registration['eventName'],
            "registration_id": registration['regiSerno'],
            "customer_id": registration['customerId'],
            "registration_date": registration_date,
            "acgi_event_id": registration['eventId'],
            "representing_company": registration['representing'],
            "total_charges": float(registration['totalCharges']) if registration['totalCharges'] else None,
            "total_payment": abs(float(registration['totalPayment'])) if registration['totalPayment'] else None,
            "balance": float(registration['balance']) if registration['balance'] else None,    
        }

        return result