import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DataMapper:
    """Maps ACGI data to HubSpot format"""
    
    def __init__(self):
        pass
    
    def map_acgi_to_hubspot(self, acgi_customer_data: Dict[str, any]) -> Dict[str, any]:
        """Map ACGI customer data to HubSpot contact format"""
        try:
            hubspot_contact = {
                'custId': acgi_customer_data.get('custId', ''),
                'firstName': acgi_customer_data.get('firstName', ''),
                'lastName': acgi_customer_data.get('lastName', ''),
                'middleName': acgi_customer_data.get('middleName', ''),
                'company': acgi_customer_data.get('company', ''),
                'title': acgi_customer_data.get('title', ''),
                'primaryEmail': self._get_primary_email(acgi_customer_data.get('emails', [])),
                'primaryPhone': self._get_primary_phone(acgi_customer_data.get('phones', [])),
                'primaryAddress': self._get_primary_address(acgi_customer_data.get('addresses', [])),
                'city': '',
                'state': '',
                'zip': '',
                'country': '',
                'membershipStatus': self._get_membership_status(acgi_customer_data.get('memberships', [])),
                'membershipType': self._get_membership_type(acgi_customer_data.get('memberships', [])),
                'lastSync': datetime.now().isoformat(),
                'allEmails': acgi_customer_data.get('emails', []),
                'allPhones': acgi_customer_data.get('phones', []),
                'allAddresses': acgi_customer_data.get('addresses', []),
                'jobs': acgi_customer_data.get('jobs', []),
                'memberships': acgi_customer_data.get('memberships', [])
            }
            
            # Extract address components if primary address exists
            if hubspot_contact['primaryAddress']:
                address_parts = hubspot_contact['primaryAddress'].split(',')
                if len(address_parts) >= 3:
                    hubspot_contact['city'] = address_parts[-3].strip() if len(address_parts) >= 3 else ''
                    hubspot_contact['state'] = address_parts[-2].strip() if len(address_parts) >= 2 else ''
                    hubspot_contact['zip'] = address_parts[-1].strip() if len(address_parts) >= 1 else ''
            
            return hubspot_contact
            
        except Exception as e:
            logger.error(f"Error mapping ACGI data to HubSpot: {str(e)}")
            return {
                'custId': acgi_customer_data.get('custId', ''),
                'error': f"Mapping error: {str(e)}"
            }
    
    def _get_primary_email(self, emails: List[Dict[str, any]]) -> str:
        """Get the primary email address from the list"""
        if not emails:
            return ''
        
        # Prefer work email, then primary, then first available
        for email in emails:
            if email.get('type', '').lower() == 'work':
                return email.get('email', '')
        
        for email in emails:
            if email.get('type', '').lower() == 'primary':
                return email.get('email', '')
        
        # Return first valid email
        for email in emails:
            if email.get('email'):
                return email.get('email', '')
        
        return ''
    
    def _get_primary_phone(self, phones: List[Dict[str, any]]) -> str:
        """Get the primary phone number from the list"""
        if not phones:
            return ''
        
        # Prefer work phone, then primary, then first available
        for phone in phones:
            if phone.get('type', '').lower() == 'work':
                return self._format_phone(phone)
        
        for phone in phones:
            if phone.get('type', '').lower() == 'primary':
                return self._format_phone(phone)
        
        # Return first valid phone
        for phone in phones:
            if phone.get('phone'):
                return self._format_phone(phone)
        
        return ''
    
    def _format_phone(self, phone: Dict[str, any]) -> str:
        """Format phone number with extension if available"""
        phone_number = phone.get('phone', '')
        extension = phone.get('extension', '')
        
        if extension:
            return f"{phone_number} ext {extension}"
        return phone_number
    
    def _get_primary_address(self, addresses: List[Dict[str, any]]) -> str:
        """Get the primary address from the list"""
        if not addresses:
            return ''
        
        # Prefer work address, then primary, then first available
        for address in addresses:
            if address.get('type', '').lower() == 'work':
                return self._format_address(address)
        
        for address in addresses:
            if address.get('type', '').lower() == 'primary':
                return self._format_address(address)
        
        # Return first valid address
        for address in addresses:
            if address.get('address1'):
                return self._format_address(address)
        
        return ''
    
    def _format_address(self, address: Dict[str, any]) -> str:
        """Format address components into a single string"""
        parts = []
        
        if address.get('address1'):
            parts.append(address['address1'])
        
        if address.get('address2'):
            parts.append(address['address2'])
        
        city_state_zip = []
        if address.get('city'):
            city_state_zip.append(address['city'])
        
        if address.get('state'):
            city_state_zip.append(address['state'])
        
        if address.get('zip'):
            city_state_zip.append(address['zip'])
        
        if city_state_zip:
            parts.append(', '.join(city_state_zip))
        
        if address.get('country'):
            parts.append(address['country'])
        
        return ', '.join(parts)
    
    def _get_membership_status(self, memberships: List[Dict[str, any]]) -> str:
        """Get the current membership status"""
        if not memberships:
            return 'No Membership'
        
        # Find active memberships
        active_memberships = [m for m in memberships if m.get('isActive', False)]
        
        if active_memberships:
            return 'Active'
        
        # Check for expired memberships
        expired_memberships = [m for m in memberships if not m.get('isActive', False)]
        if expired_memberships:
            return 'Expired'
        
        return 'Unknown'
    
    def _get_membership_type(self, memberships: List[Dict[str, any]]) -> str:
        """Get the primary membership type"""
        if not memberships:
            return ''
        
        # Prefer active memberships
        active_memberships = [m for m in memberships if m.get('isActive', False)]
        
        if active_memberships:
            return active_memberships[0].get('type', '')
        
        # Return first membership type if no active ones
        return memberships[0].get('type', '')
    
    def map_batch_acgi_to_hubspot(self, acgi_customers: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Map multiple ACGI customers to HubSpot format"""
        hubspot_contacts = []
        
        for acgi_customer in acgi_customers:
            try:
                hubspot_contact = self.map_acgi_to_hubspot(acgi_customer)
                hubspot_contacts.append(hubspot_contact)
            except Exception as e:
                logger.error(f"Error mapping customer {acgi_customer.get('custId', 'unknown')}: {str(e)}")
                hubspot_contacts.append({
                    'custId': acgi_customer.get('custId', ''),
                    'error': f"Mapping error: {str(e)}"
                })
        
        return hubspot_contacts
    
    def validate_hubspot_contact(self, contact: Dict[str, any]) -> Dict[str, any]:
        """Validate HubSpot contact data before sending"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        if not contact.get('firstName') and not contact.get('lastName'):
            validation_result['errors'].append('First name or last name is required')
            validation_result['is_valid'] = False
        
        if not contact.get('primaryEmail'):
            validation_result['warnings'].append('No email address provided')
        
        if not contact.get('primaryPhone'):
            validation_result['warnings'].append('No phone number provided')
        
        # Check email format
        email = contact.get('primaryEmail', '')
        if email and '@' not in email:
            validation_result['errors'].append('Invalid email format')
            validation_result['is_valid'] = False
        
        # Check ACGI customer ID
        if not contact.get('custId'):
            validation_result['warnings'].append('No ACGI customer ID provided')
        
        return validation_result
    
    def create_hubspot_properties(self, contact: Dict[str, any]) -> Dict[str, any]:
        """Create HubSpot properties object from mapped contact data"""
        properties = {
            'firstname': contact.get('firstName', ''),
            'lastname': contact.get('lastName', ''),
            'company': contact.get('company', ''),
            'jobtitle': contact.get('title', ''),
            'phone': contact.get('primaryPhone', ''),
            'email': contact.get('primaryEmail', ''),
            'address': contact.get('primaryAddress', ''),
            'city': contact.get('city', ''),
            'state': contact.get('state', ''),
            'zip': contact.get('zip', ''),
            'country': contact.get('country', ''),
            'acgi_customer_id': contact.get('custId', ''),
            'acgi_membership_status': contact.get('membershipStatus', ''),
            'acgi_membership_type': contact.get('membershipType', ''),
            'acgi_last_sync': contact.get('lastSync', '')
        }
        
        # Remove empty values
        return {k: v for k, v in properties.items() if v} 