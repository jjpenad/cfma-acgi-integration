import requests
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ACGIClient:
    """Client for interacting with ACGI API"""
    
    def __init__(self):
        self.base_url = "https://ams.cfma.org"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'ACGI-HubSpot-Integration/1.0'
        })
    
    def test_credentials(self, credentials: Dict[str, str]) -> Dict[str, any]:
        """Test ACGI credentials by making a simple queue request"""
        environment = "cetdigitdev" if credentials['environment'] == "test" else "cetdigit"
        try:
            # Create a minimal test request
            test_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<custRequest>
    <vendorId>{credentials['userid']}</vendorId>
    <vendorPassword>{credentials['password']}</vendorPassword>
</custRequest>"""
            
            url = f"{self.base_url}/{environment}/CENCUSTINTEGRATESYNCWEBSVCLIB.GET_QUEUE_CUSTS_W_REASONS_XML"
            
            response = self.session.post(
                url,
                data={'p_input_xml_doc': test_xml},
                timeout=30
            )
            
            if response.status_code == 200:
                # Try to parse the response to check for error messages
                try:
                    root = ET.fromstring(response.text)
                    # Check for error elements
                    error_elements = root.findall('.//error')
                    if error_elements:
                        error_msg = '; '.join([elem.text for elem in error_elements if elem.text])
                        return {
                            'success': False,
                            'message': f"ACGI API returned error: {error_msg}",
                            'response': response.text
                        }
                    
                    return {
                        'success': True,
                        'message': 'Credentials are valid',
                        'response': response.text
                    }
                except ET.ParseError:
                    # If we can't parse XML, check if response contains error indicators
                    if 'error' in response.text.lower() or 'invalid' in response.text.lower():
                        return {
                            'success': False,
                            'message': 'Invalid credentials or API error',
                            'response': response.text
                        }
                    return {
                        'success': True,
                        'message': 'Credentials appear valid (response parsing failed)',
                        'response': response.text
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text}",
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
    
    def get_queue_updates(self, credentials: Dict[str, str]) -> Dict[str, any]:
        """Get customer updates from the queue"""
        try:
            queue_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<custRequest>
    <vendorId>{credentials['userid']}</vendorId>
    <vendorPassword>{credentials['password']}</vendorPassword>
</custRequest>"""
            
            url = f"{self.base_url}/{credentials['environment']}/CENCUSTINTEGRATESYNCWEBSVCLIB.GET_QUEUE_CUSTS_W_REASONS_XML"
            print(url)
            response = self.session.post(
                url,
                data={'p_input_xml_doc': queue_xml},
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    
                    # Extract customer IDs from the response
                    customers = []
                    for cust_elem in root.findall('.//customer'):
                        customer_data = {
                            'custId': cust_elem.find('custId').text if cust_elem.find('custId') is not None else None,
                            'action': cust_elem.find('action').text if cust_elem.find('action') is not None else None,
                            'reason': cust_elem.find('reason').text if cust_elem.find('reason') is not None else None
                        }
                        customers.append(customer_data)
                    
                    return {
                        'success': True,
                        'customers': customers,
                        'raw_response': response.text
                    }
                    
                except ET.ParseError as e:
                    return {
                        'success': False,
                        'message': f"Failed to parse XML response: {str(e)}",
                        'raw_response': response.text
                    }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text}",
                    'raw_response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error getting queue updates: {str(e)}",
                'raw_response': None
            }
    
    def get_customer_data(self, credentials: Dict[str, str], customer_ids: List[str]) -> Dict[str, any]:
        """Get detailed customer data for given customer IDs"""
        try:
            customers_data = []
            
            for cust_id in customer_ids:
                customer_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<custInfoRequest>
    <custId>{cust_id}</custId>
    <integratorUsername>{credentials['userid']}</integratorUsername>
    <integratorPassword>{credentials['password']}</integratorPassword>
    <directoryId></directoryId>
    <bulkRequest>false</bulkRequest>
    <details includeCodeValues="true">
        <roles include="true" />
        <addresses include="true" includeBad="true" />
        <phones include="true" />
        <emails include="true" includeBad="true" />
        <websites include="true" includeBad="true" />
        <jobs include="true" includeInactive="true" />
        <employmentAttributes include="true" includeAll="true" />
        <committeePositions include="true" includeInactive="true" />
        <memberships include="true" includeInactive="true" />
        <subscriptions include="true" includeExpired="true" />
        <communicationPreferences include="true" />
        <customerAttributes include="true" includeAll="true" />
        <custDimAttrs include="true" includeAll="true" />
        <bio include="true" />
        <aliases include="true" />
        <companyAdmins include="true" />
        <certifications include="true" />
        <employees include="true" />
        <referralInfo include="true" />
        <files include="true" />
    </details>
</custInfoRequest>"""
                
                url = f"{self.base_url}/{credentials['environment']}/CENSSAWEBSVCLIB.GET_CUST_INFO_XML"
                
                response = self.session.post(
                    url,
                    data={'p_input_xml_doc': customer_xml},
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        root = ET.fromstring(response.text)
                        
                        # Parse customer data
                        customer_data = self._parse_customer_xml(root)
                        customer_data['custId'] = cust_id
                        customers_data.append(customer_data)
                        
                    except ET.ParseError as e:
                        logger.error(f"Failed to parse customer {cust_id} XML: {str(e)}")
                        customers_data.append({
                            'custId': cust_id,
                            'error': f"XML parsing failed: {str(e)}",
                            'raw_response': response.text
                        })
                else:
                    customers_data.append({
                        'custId': cust_id,
                        'error': f"HTTP {response.status_code}: {response.text}",
                        'raw_response': response.text
                    })
            
            return {
                'success': True,
                'customers': customers_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error getting customer data: {str(e)}",
                'customers': []
            }
    
    def _parse_customer_xml(self, root: ET.Element) -> Dict[str, any]:
        """Parse customer XML data into a structured format"""
        customer = {}
        
        # Basic customer info
        basic_info = root.find('.//customer')
        if basic_info is not None:
            customer['firstName'] = self._get_element_text(basic_info, 'firstName')
            customer['lastName'] = self._get_element_text(basic_info, 'lastName')
            customer['middleName'] = self._get_element_text(basic_info, 'middleName')
            customer['company'] = self._get_element_text(basic_info, 'company')
            customer['title'] = self._get_element_text(basic_info, 'title')
            customer['birthDate'] = self._get_element_text(basic_info, 'birthDate')
            customer['gender'] = self._get_element_text(basic_info, 'gender')
        
        # Emails
        emails = []
        for email_elem in root.findall('.//email'):
            email_data = {
                'email': self._get_element_text(email_elem, 'email'),
                'type': self._get_element_text(email_elem, 'type'),
                'isBad': self._get_element_text(email_elem, 'isBad') == 'true'
            }
            if email_data['email'] and not email_data['isBad']:
                emails.append(email_data)
        customer['emails'] = emails
        
        # Phones
        phones = []
        for phone_elem in root.findall('.//phone'):
            phone_data = {
                'phone': self._get_element_text(phone_elem, 'phone'),
                'type': self._get_element_text(phone_elem, 'type'),
                'extension': self._get_element_text(phone_elem, 'extension')
            }
            if phone_data['phone']:
                phones.append(phone_data)
        customer['phones'] = phones
        
        # Addresses
        addresses = []
        for addr_elem in root.findall('.//address'):
            addr_data = {
                'address1': self._get_element_text(addr_elem, 'address1'),
                'address2': self._get_element_text(addr_elem, 'address2'),
                'city': self._get_element_text(addr_elem, 'city'),
                'state': self._get_element_text(addr_elem, 'state'),
                'zip': self._get_element_text(addr_elem, 'zip'),
                'country': self._get_element_text(addr_elem, 'country'),
                'type': self._get_element_text(addr_elem, 'type'),
                'isBad': self._get_element_text(addr_elem, 'isBad') == 'true'
            }
            if addr_data['address1'] and not addr_data['isBad']:
                addresses.append(addr_data)
        customer['addresses'] = addresses
        
        # Jobs/Employment
        jobs = []
        for job_elem in root.findall('.//job'):
            job_data = {
                'company': self._get_element_text(job_elem, 'company'),
                'title': self._get_element_text(job_elem, 'title'),
                'startDate': self._get_element_text(job_elem, 'startDate'),
                'endDate': self._get_element_text(job_elem, 'endDate'),
                'isActive': self._get_element_text(job_elem, 'isActive') == 'true'
            }
            if job_data['company']:
                jobs.append(job_data)
        customer['jobs'] = jobs
        
        # Memberships
        memberships = []
        for mem_elem in root.findall('.//membership'):
            mem_data = {
                'type': self._get_element_text(mem_elem, 'type'),
                'startDate': self._get_element_text(mem_elem, 'startDate'),
                'endDate': self._get_element_text(mem_elem, 'endDate'),
                'isActive': self._get_element_text(mem_elem, 'isActive') == 'true'
            }
            if mem_data['type']:
                memberships.append(mem_data)
        customer['memberships'] = memberships
        
        return customer
    
    def _get_element_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Safely get text from an XML element"""
        elem = parent.find(tag)
        return elem.text if elem is not None else None
    
    def purge_queue(self, credentials: Dict[str, str], customer_ids: List[str]) -> Dict[str, any]:
        """Purge processed customers from the queue"""
        try:
            # Build XML with customer IDs to purge
            purge_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<purgeRequest>
    <vendorId>{credentials['userid']}</vendorId>
    <vendorPassword>{credentials['password']}</vendorPassword>
    <customers>"""
            
            for cust_id in customer_ids:
                purge_xml += f"\n        <customer>{cust_id}</customer>"
            
            purge_xml += """
    </customers>
</purgeRequest>"""
            
            url = f"{self.base_url}/{credentials['environment']}/CENCUSTINTEGRATESYNCWEBSVCLIB.PURGE_QUEUE_XML"
            
            response = self.session.post(
                url,
                data={'p_input_xml_doc': purge_xml},
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f"Successfully purged {len(customer_ids)} customers from queue",
                    'raw_response': response.text
                }
            else:
                return {
                    'success': False,
                    'message': f"HTTP {response.status_code}: {response.text}",
                    'raw_response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error purging queue: {str(e)}",
                'raw_response': None
            } 