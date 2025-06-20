import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IntegrationService:
    """Orchestrates the integration between ACGI and HubSpot"""
    
    def __init__(self, acgi_client, hubspot_client, data_mapper):
        self.acgi_client = acgi_client
        self.hubspot_client = hubspot_client
        self.data_mapper = data_mapper
    
    def run_integration(self, acgi_credentials: Dict[str, str], hubspot_credentials: Dict[str, str]) -> Dict[str, any]:
        """Run the complete integration process"""
        try:
            logger.info("Starting ACGI to HubSpot integration")
            
            # Step 1: Test credentials
            logger.info("Testing credentials...")
            acgi_test = self.acgi_client.test_credentials(acgi_credentials)
            hubspot_test = self.hubspot_client.test_credentials(hubspot_credentials)
            
            if not acgi_test['success']:
                return {
                    'success': False,
                    'message': f"ACGI credentials failed: {acgi_test['message']}",
                    'step': 'credential_test'
                }
            
            if not hubspot_test['success']:
                return {
                    'success': False,
                    'message': f"HubSpot credentials failed: {hubspot_test['message']}",
                    'step': 'credential_test'
                }
            
            # Step 2: Initialize HubSpot client
            logger.info("Initializing HubSpot client...")
            if not self.hubspot_client.initialize_client(hubspot_credentials['api_key']):
                return {
                    'success': False,
                    'message': "Failed to initialize HubSpot client",
                    'step': 'hubspot_init'
                }
            
            # Step 3: Get queue updates from ACGI
            logger.info("Getting queue updates from ACGI...")
            queue_result = self.acgi_client.get_queue_updates(acgi_credentials)
            
            if not queue_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to get queue updates: {queue_result['message']}",
                    'step': 'queue_fetch'
                }
            
            customers_in_queue = queue_result.get('customers', [])
            logger.info(f"Found {len(customers_in_queue)} customers in queue")
            
            if not customers_in_queue:
                return {
                    'success': True,
                    'message': "No customers in queue to process",
                    'customers_processed': 0,
                    'customers_created': 0,
                    'customers_updated': 0,
                    'errors': []
                }
            
            # Step 4: Get detailed customer data
            logger.info("Getting detailed customer data...")
            customer_ids = [cust['custId'] for cust in customers_in_queue if cust.get('custId')]
            
            if not customer_ids:
                return {
                    'success': False,
                    'message': "No valid customer IDs found in queue",
                    'step': 'customer_data_fetch'
                }
            
            customer_data_result = self.acgi_client.get_customer_data(acgi_credentials, customer_ids)
            
            if not customer_data_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to get customer data: {customer_data_result['message']}",
                    'step': 'customer_data_fetch'
                }
            
            acgi_customers = customer_data_result.get('customers', [])
            logger.info(f"Retrieved data for {len(acgi_customers)} customers")
            
            # Step 5: Map ACGI data to HubSpot format
            logger.info("Mapping data to HubSpot format...")
            hubspot_contacts = self.data_mapper.map_batch_acgi_to_hubspot(acgi_customers)
            
            # Step 6: Send data to HubSpot
            logger.info("Sending data to HubSpot...")
            hubspot_result = self.hubspot_client.batch_create_or_update_contacts(hubspot_contacts)
            
            if not hubspot_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to send data to HubSpot: {hubspot_result['message']}",
                    'step': 'hubspot_sync'
                }
            
            # Step 7: Purge processed customers from queue
            logger.info("Purging processed customers from queue...")
            successful_customer_ids = []
            for result in hubspot_result.get('results', []):
                if result.get('success'):
                    # Find the corresponding customer ID
                    for contact in hubspot_contacts:
                        if contact.get('custId'):
                            successful_customer_ids.append(contact['custId'])
                            break
            
            if successful_customer_ids:
                purge_result = self.acgi_client.purge_queue(acgi_credentials, successful_customer_ids)
                if not purge_result['success']:
                    logger.warning(f"Failed to purge queue: {purge_result['message']}")
            
            # Step 8: Compile results
            success_count = hubspot_result.get('success_count', 0)
            error_count = hubspot_result.get('error_count', 0)
            
            created_count = sum(1 for result in hubspot_result.get('results', []) 
                              if result.get('action') == 'created')
            updated_count = sum(1 for result in hubspot_result.get('results', []) 
                              if result.get('action') == 'updated')
            
            return {
                'success': True,
                'message': f"Integration completed successfully. Processed {len(customers_in_queue)} customers: {success_count} successful, {error_count} failed",
                'customers_processed': len(customers_in_queue),
                'customers_created': created_count,
                'customers_updated': updated_count,
                'customers_failed': error_count,
                'queue_purged': len(successful_customer_ids),
                'errors': [result.get('message') for result in hubspot_result.get('results', []) if not result.get('success')]
            }
            
        except Exception as e:
            logger.error(f"Integration failed: {str(e)}")
            return {
                'success': False,
                'message': f"Integration failed: {str(e)}",
                'step': 'unknown'
            }
    
    def simulate_integration_with_mock_data(self, acgi_credentials: Dict[str, str], hubspot_credentials: Dict[str, str]) -> Dict[str, any]:
        """Simulate integration with mock data for testing"""
        try:
            logger.info("Starting simulated integration with mock data")
            
            # Test credentials
            acgi_test = self.acgi_client.test_credentials(acgi_credentials)
            hubspot_test = self.hubspot_client.test_credentials(hubspot_credentials)
            
            if not acgi_test['success']:
                return {
                    'success': False,
                    'message': f"ACGI credentials failed: {acgi_test['message']}",
                    'step': 'credential_test'
                }
            
            if not hubspot_test['success']:
                return {
                    'success': False,
                    'message': f"HubSpot credentials failed: {hubspot_test['message']}",
                    'step': 'credential_test'
                }
            
            # Initialize HubSpot client
            if not self.hubspot_client.initialize_client(hubspot_credentials['api_key']):
                return {
                    'success': False,
                    'message': "Failed to initialize HubSpot client",
                    'step': 'hubspot_init'
                }
            
            # Create mock ACGI data
            mock_acgi_customers = [
                {
                    'custId': '12345',
                    'firstName': 'John',
                    'lastName': 'Doe',
                    'company': 'ACME Corporation',
                    'title': 'Manager',
                    'emails': [
                        {'email': 'john.doe@acme.com', 'type': 'work', 'isBad': False},
                        {'email': 'johndoe@personal.com', 'type': 'personal', 'isBad': False}
                    ],
                    'phones': [
                        {'phone': '555-123-4567', 'type': 'work', 'extension': '101'},
                        {'phone': '555-987-6543', 'type': 'mobile', 'extension': ''}
                    ],
                    'addresses': [
                        {
                            'address1': '123 Business St',
                            'address2': 'Suite 100',
                            'city': 'New York',
                            'state': 'NY',
                            'zip': '10001',
                            'country': 'USA',
                            'type': 'work',
                            'isBad': False
                        }
                    ],
                    'memberships': [
                        {'type': 'Professional', 'startDate': '2023-01-01', 'endDate': '2024-12-31', 'isActive': True}
                    ]
                },
                {
                    'custId': '67890',
                    'firstName': 'Jane',
                    'lastName': 'Smith',
                    'company': 'Tech Solutions Inc',
                    'title': 'Director',
                    'emails': [
                        {'email': 'jane.smith@techsolutions.com', 'type': 'work', 'isBad': False}
                    ],
                    'phones': [
                        {'phone': '555-456-7890', 'type': 'work', 'extension': '202'}
                    ],
                    'addresses': [
                        {
                            'address1': '456 Tech Ave',
                            'city': 'San Francisco',
                            'state': 'CA',
                            'zip': '94105',
                            'country': 'USA',
                            'type': 'work',
                            'isBad': False
                        }
                    ],
                    'memberships': [
                        {'type': 'Executive', 'startDate': '2022-06-01', 'endDate': '2024-05-31', 'isActive': True}
                    ]
                }
            ]
            
            # Map to HubSpot format
            hubspot_contacts = self.data_mapper.map_batch_acgi_to_hubspot(mock_acgi_customers)
            
            # Send to HubSpot
            hubspot_result = self.hubspot_client.batch_create_or_update_contacts(hubspot_contacts)
            
            if not hubspot_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to send mock data to HubSpot: {hubspot_result['message']}",
                    'step': 'hubspot_sync'
                }
            
            success_count = hubspot_result.get('success_count', 0)
            created_count = sum(1 for result in hubspot_result.get('results', []) 
                              if result.get('action') == 'created')
            updated_count = sum(1 for result in hubspot_result.get('results', []) 
                              if result.get('action') == 'updated')
            
            return {
                'success': True,
                'message': f"Simulated integration completed successfully. Processed {len(mock_acgi_customers)} mock customers: {success_count} successful",
                'customers_processed': len(mock_acgi_customers),
                'customers_created': created_count,
                'customers_updated': updated_count,
                'customers_failed': len(mock_acgi_customers) - success_count,
                'simulation': True
            }
            
        except Exception as e:
            logger.error(f"Simulated integration failed: {str(e)}")
            return {
                'success': False,
                'message': f"Simulated integration failed: {str(e)}",
                'step': 'unknown'
            } 