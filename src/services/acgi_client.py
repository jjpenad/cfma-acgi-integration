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
    
    def get_customer_data(self, credentials: Dict[str, str], customer_id: str) -> Dict[str, any]:
        """Get detailed customer data for given customer IDs"""
        try:
            customers_data = []
            print("customer_id",customer_id)
            
            customer_xml = f"""p_input_xml_doc=<?xml version="1.0" encoding="UTF-8"?>
        <custInfoRequest>
            <custId>{customer_id}</custId>
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
                
            print("customer_xml",customer_xml)
                
            url = f"{self.base_url}/{credentials['environment']}/CENSSAWEBSVCLIB.GET_CUST_INFO_XML"
            
            response = self.session.post(
                url,
                data=customer_xml,
                timeout=30
            )
            print("URLLLL",url)
            print("responseTEXT",response.text)
            
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    
                    # Parse customer data
                    customer_data = self._parse_customer_xml(root)
                    customer_data['custId'] = customer_id
                    customers_data.append(customer_data)
                    
                except ET.ParseError as e:
                    logger.error(f"Failed to parse customer {customer_id} XML: {str(e)}")
                    customers_data.append({
                        'custId': customer_id,
                        'error': f"XML parsing failed: {str(e)}",
                        'raw_response': response.text
                    })
            else:
                customers_data.append({
                    'custId': customer_id,
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

    def get_memberships_data(self, credentials: Dict[str, str], customer_id: str) -> Dict[str, any]:
        """Get memberships data for a specific customer"""
        try:
            print("Getting memberships for customer_id:", customer_id)
            
            memberships_xml = f"""p_input_xml_doc=<?xml version="1.0"?>
<member-request>
    <vendor-id>{credentials['userid']}</vendor-id>
    <vendor-password>{credentials['password']}</vendor-password>
    <cust-id>{customer_id}</cust-id> 
</member-request>"""
                
            print("memberships_xml:", memberships_xml)
                
            url = f"{self.base_url}/{credentials['environment']}/MEMSSAWEBSVCLIB.GET_MEMBERS_XML"
            
            response = self.session.post(
                url,
                data=memberships_xml,
                timeout=30
            )
            print("URL:", url)
            print("Response status:", response.status_code)
            print("Response text:", response.text)
            
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    
                    # Parse memberships data
                    memberships_data = self._parse_memberships_xml(root)
                    print("MEMBERSHIPS DATA",memberships_data)
                    for membership in memberships_data['memberships']:
                        membership['customerId'] = customer_id
                    
                    return {
                        'success': True,
                        'memberships': memberships_data
                    }
                    
                except ET.ParseError as e:
                    logger.error(f"Failed to parse memberships XML for customer {customer_id}: {str(e)}")
                    return {
                        'success': False,
                        'message': f"XML parsing failed: {str(e)}",
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
                'message': f"Error getting memberships data: {str(e)}",
                'memberships': {}
            }
    
    def get_purchased_products(self, credentials: Dict[str, str], customer_id: str) -> Dict[str, any]:
        """Get purchased products for a specific customer"""
        try:
            print("Getting purchased products for customer_id:", customer_id)
            
            purchased_products_xml = f"""p_input_xml_doc=<?xml version="1.0" encoding="UTF-8" ?>
<ecord-request>           
    <vendorId>{credentials['userid']}</vendorId>                 <!-- provided by ACGI -->
    <vendorPassword>{credentials['password']}</vendorPassword> <!-- provided by ACGI -->
    <custId>{customer_id}</custId> 
    <orderSerno></orderSerno> <!-- optional -->
    <productType></productType> <!-- optional -->      
</ecord-request>"""
            
            print("purchased_products_xml:", purchased_products_xml)
            
            url = f"{self.base_url}/{credentials['environment']}/ECSSAWEBSVCLIB.GET_PURCHASED_PRODUCTS_XML"
            
            response = self.session.post(
                url,
                data=purchased_products_xml,
                timeout=30
            )
            print("URL:", url)
            print("Response status:", response.status_code)
            print("Response text:", response.text)
            
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    
                    # Parse purchased products data
                    purchased_products_data = self._parse_purchased_products_xml(root)
                    print("PURCHASED PRODUCTS DATA:", purchased_products_data)
                    for product in purchased_products_data['purchased_products']:
                        product['customerId'] = customer_id
                    return {
                        'success': True,
                        'purchased_products': purchased_products_data
                    }
                    
                except ET.ParseError as e:
                    logger.error(f"Failed to parse purchased products XML for customer {customer_id}: {str(e)}")
                    return {
                        'success': False,
                        'message': f"XML parsing failed: {str(e)}",
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
                'message': f"Error getting purchased products: {str(e)}",
                'purchased_products': []
            }

    def get_customer_events(self, credentials: Dict[str, str], customer_id: str) -> Dict[str, any]:
        """Get customer events for a specific customer"""
        try:
            print("Getting customer events for customer_id:", customer_id)
            
            events_xml = f"""p_input_xml_doc=<?xml version="1.0" encoding="UTF-8" ?>
<event-request>           
    <vendor-id>{credentials['userid']}</vendor-id>                 <!-- provided by ACGI -->
    <vendor-password>{credentials['password']}</vendor-password> <!-- provided by ACGI -->
    <cust-id>{customer_id}</cust-id>      
</event-request>"""
            
            
            url = f"{self.base_url}/{credentials['environment']}/EVTSSAWEBSVCLIB.GET_EVENT_INFO_XML"
            
            response = self.session.post(
                url,
                data=events_xml,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    
                    # Parse customer events data
                    events_data = self._parse_customer_events_xml(root)
                    print("CUSTOMER EVENTS DATA:", events_data)
                    for event in events_data['events']:
                        event['customerId'] = customer_id
                    return {
                        'success': True,
                        'events': events_data
                    }
                    
                except ET.ParseError as e:
                    logger.error(f"Failed to parse customer events XML for customer {customer_id}: {str(e)}")
                    return {
                        'success': False,
                        'message': f"XML parsing failed: {str(e)}",
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
                'message': f"Error getting customer events: {str(e)}",
                'events': []
            }

    
    def _parse_customer_xml(self, root: ET.Element) -> Dict[str, any]:
        """Parse customer XML data into a structured format"""
        customer = {}
        print("roottttt",root)
        
        # Basic customer info
        customer['custId'] = self._get_element_text(root, './/custId')
        customer['custType'] = self._get_element_text(root, './/custType')
        customer['loginId'] = self._get_element_text(root, './/loginId')
        
        # Name fields
        name_elem = root.find('.//name')
        if name_elem is not None:
            customer['prefixName'] = self._get_element_text(name_elem, 'prefixName')
            customer['firstName'] = self._get_element_text(name_elem, 'firstName') 
            customer['middleName'] = self._get_element_text(name_elem, 'middleName')
            customer['lastName'] = self._get_element_text(name_elem, 'lastName')
            customer['suffixName'] = self._get_element_text(name_elem, 'suffixName')
            customer['degreeName'] = self._get_element_text(name_elem, 'degreeName')
            customer['informalName'] = self._get_element_text(name_elem, 'informalName')
            customer['displayName'] = self._get_element_text(name_elem, 'displayName')
        
        # Roles
        roles = []
        for role_elem in root.findall('.//roles/role'):
            role = role_elem.text
            if role:
                roles.append(role.strip())
        customer['roles'] = roles
        
        # Addresses
        addresses = []
        for addr_elem in root.findall('.//addresses/address'):
            addr_data = {
                'addressSerno': self._get_element_text(addr_elem, 'addressSerno'),
                'addressType': self._get_element_text(addr_elem, 'addressType'),
                'addressTypeDescr': self._get_element_text(addr_elem, 'addressTypeDescr'),
                'best': self._get_element_text(addr_elem, 'best') == 'true',
                'preferred': self._get_element_text(addr_elem, 'preferred') == 'true',
                'street1': self._get_element_text(addr_elem, 'street1'),
                'street2': self._get_element_text(addr_elem, 'street2'),
                'street3': self._get_element_text(addr_elem, 'street3'),
                'city': self._get_element_text(addr_elem, 'city'),
                'state': self._get_element_text(addr_elem, 'state'),
                'postalCode': self._get_element_text(addr_elem, 'postalCode'),
                'countryCode': self._get_element_text(addr_elem, 'countryCode'),
                'countryDescr': self._get_element_text(addr_elem, 'countryDescr'),
                'badAddress': self._get_element_text(addr_elem, 'badAddress') == 'true'
            }
            addresses.append(addr_data)
        customer['addresses'] = addresses
        
        # Phones
        phones = []
        for phone_elem in root.findall('.//phones/phone'):
            phone_data = {
                'phoneSerno': self._get_element_text(phone_elem, 'phoneSerno'),
                'phoneType': self._get_element_text(phone_elem, 'phoneType'),
                'phoneTypeDescr': self._get_element_text(phone_elem, 'phoneTypeDescr'),
                'best': self._get_element_text(phone_elem, 'best') == 'true',
                'preferred': self._get_element_text(phone_elem, 'preferred') == 'true',
                'number': self._get_element_text(phone_elem, 'number'),
                'ext': self._get_element_text(phone_elem, 'ext')
            }
            phones.append(phone_data)
        customer['phones'] = phones
        
        # Emails
        emails = []
        for email_elem in root.findall('.//emails/email'):
            email_data = {
                'emailSerno': self._get_element_text(email_elem, 'emailSerno'),
                'emailType': self._get_element_text(email_elem, 'emailType'),
                'emailTypeDescr': self._get_element_text(email_elem, 'emailTypeDescr'),
                'best': self._get_element_text(email_elem, 'best') == 'true',
                'preferred': self._get_element_text(email_elem, 'preferred') == 'true',
                'address': self._get_element_text(email_elem, 'address'),
                'badAddress': self._get_element_text(email_elem, 'badAddress') == 'true'
            }
            emails.append(email_data)
        customer['emails'] = emails
        
        # Jobs
        jobs = []
        for job_elem in root.findall('.//jobs/job'):
            job_data = {
                'employerName': self._get_element_text(job_elem, 'employerName'),
                'titleName': self._get_element_text(job_elem, 'titleName'),
                'startDate': self._get_element_text(job_elem, 'startDate'),
                'endDate': self._get_element_text(job_elem, 'endDate'),
                'best': self._get_element_text(job_elem, 'best') == 'true',
                'preferred': self._get_element_text(job_elem, 'preferred') == 'true'
            }
            jobs.append(job_data)
        customer['jobs'] = jobs

        #Customer Attributes
        customer_attributes = []
        for cust_attr_elem in root.findall('.//customerAttributes/customerAttribute'):
            cust_attr_data = {
                'type': self._get_element_text(cust_attr_elem, 'type'),
                'typeName': self._get_element_text(cust_attr_elem, 'typeName'),
                'code': self._get_element_text(cust_attr_elem, 'code'),
                'codeDescr': self._get_element_text(cust_attr_elem, 'codeDescr'),
                'char': self._get_element_text(cust_attr_elem, 'char'),
                'number': self._get_element_text(cust_attr_elem, 'number')
            }
            customer_attributes.append(cust_attr_data)
        customer['customerAttributes'] = customer_attributes

        # Memberships
        memberships = []
        for mem_elem in root.findall('.//memberships/membership'):
            mem_data = {
                'subgroupId': self._get_element_text(mem_elem, 'subgroupId'),
                'startsubgroupNameDate': self._get_element_text(mem_elem, 'subgroupName'),
                'subgroupTypeDescr': self._get_element_text(mem_elem, 'subgroupTypeDescr'),
                'member': self._get_element_text(mem_elem, 'member'),
                'statusDescr': self._get_element_text(mem_elem, 'statusDescr'),
                'isActive': self._get_element_text(mem_elem, 'statusCode') == "ACTIVE",
                'directOrInherited': self._get_element_text(mem_elem, 'directOrInherited'),
                'subgroupType': self._get_element_text(mem_elem, 'subgroupType'),
                'classCode': self._get_element_text(mem_elem, 'classCode'),
                'joinDate': self._get_element_text(mem_elem, 'joinDate'),
            }
            memberships.append(mem_data)
        customer['memberships'] = memberships

        return customer

    def _parse_memberships_xml(self, root: ET.Element) -> Dict[str, any]:
        """Parse memberships XML data into a structured format"""
        memberships_data = {}
        
        # Get first membership record for customer info
        first_membership = root.find('.//membership')
        if first_membership is not None:
            memberships_data['custId'] = self._get_element_text(first_membership, 'customer-id')
            memberships_data['firstName'] = self._get_element_text(first_membership, 'first-name')
            memberships_data['lastName'] = self._get_element_text(first_membership, 'last-name')
            memberships_data['company'] = self._get_element_text(first_membership, 'company')
            memberships_data['employerId'] = self._get_element_text(first_membership, 'employer-id')
            memberships_data['employerName'] = self._get_element_text(first_membership, 'employer-name')
            memberships_data['city'] = self._get_element_text(first_membership, 'city')
            memberships_data['state'] = self._get_element_text(first_membership, 'state')

        # Memberships
        memberships = []
        for mem_elem in root.findall('.//membership'):
            mem_data = {
                'customerId': self._get_element_text(mem_elem, 'customer-id'),
                'subgroupId': self._get_element_text(mem_elem, 'subgroup-id'),
                'subgroupName': self._get_element_text(mem_elem, 'subgroup-name'),
                'classCd': self._get_element_text(mem_elem, 'class-cd'),
                'subclassCd': self._get_element_text(mem_elem, 'subclass-cd'),
                'status': self._get_element_text(mem_elem, 'status'),
                'isActive': self._get_element_text(mem_elem, 'status') == "ACTIVE",
                'joinDate': self._get_element_text(mem_elem, 'join-date'),
                'expireDate': self._get_element_text(mem_elem, 'expire-date'),
                'currentStatusReasonCd': self._get_element_text(mem_elem, 'current-status-reason-cd'),
                'currentStatusReasonNote': self._get_element_text(mem_elem, 'current-status-reason-note'),
                'reinstateDate': self._get_element_text(mem_elem, 'reinstate-date'),
                'terminateDate': self._get_element_text(mem_elem, 'terminate-date')
            }
            memberships.append(mem_data)
            
        memberships_data['memberships'] = memberships
        
        return memberships_data

    def _parse_purchased_products_xml(self, root: ET.Element) -> Dict[str, any]:
        """Parse purchased products XML data into a structured format"""
        purchased_products_data = {}
        
        # Get status
        status_elem = root.find('.//status')
        if status_elem is not None:
            purchased_products_data['status'] = status_elem.text
        
        # Orders/Products
        orders = []
        limit = 1000
        for order_elem in root.findall('.//order'):
            order_data = {
                'productSerno': self._get_element_text(order_elem, 'productSerno'),
                'productId': self._get_element_text(order_elem, 'productId'),
                'productName': self._get_element_text(order_elem, 'productName'),
                'length': self._get_element_text(order_elem, 'length'),
                'width': self._get_element_text(order_elem, 'width'),
                'height': self._get_element_text(order_elem, 'height'),
                'weight': self._get_element_text(order_elem, 'weight'),
                'activeFlag': self._get_element_text(order_elem, 'activeFlag'),
                'internalOrderFlag': self._get_element_text(order_elem, 'internalOrderFlag'),
                'firstAvailableDate': self._get_element_text(order_elem, 'firstAvailableDate'),
                'defaultUnitCost': self._get_element_text(order_elem, 'defaultUnitCost'),
                'showProductRelativeURL': self._get_element_text(order_elem, 'showProductRelativeURL'),
                'imageThumbnail': self._get_element_text(order_elem, 'imageThumbnail'),
                'imageFullsize': self._get_element_text(order_elem, 'imageFullsize'),
                'orderDate': self._get_element_text(order_elem, 'orderDate'),
                'orderStatus': self._get_element_text(order_elem, 'orderStatus'),
                'orderSerno': self._get_element_text(order_elem, 'orderSerno'),
                'productType': self._get_element_text(order_elem, 'productType'),
                'priceProfile': self._get_element_text(order_elem, 'priceProfile'),
                'invoiceBalanceStatus': self._get_element_text(order_elem, 'invoiceBalanceStatus'),
                'invoiceBalance': self._get_element_text(order_elem, 'invoiceBalance'),
                'quantity': self._get_element_text(order_elem, 'quantity')
            }
            if len(orders) >= limit:
                break
            # # Parse attributes
            # attributes = []
            # for attr_elem in order_elem.findall('.//attributes/attribute'):
            #     attr_data = {
            #         'attributeType': self._get_element_text(attr_elem, 'attribute-type'),
            #         'attributeText': self._get_element_text(attr_elem, 'attribute-text')
            #     }
            #     attributes.append(attr_data)
            # order_data['attributes'] = attributes
            
            orders.append(order_data)
            
        purchased_products_data['purchased_products'] = orders
        
        return purchased_products_data

    def _parse_customer_events_xml(self, root: ET.Element) -> Dict[str, any]:
        """Parse customer events XML data into a structured format"""
        events_data = {}
        
        # Get status
        status_elem = root.find('.//status')
        if status_elem is not None:
            events_data['status'] = status_elem.text
        
        # Events
        events = []
        limit = 1000
        for event_elem in root.findall('.//event'):
            event_data = {
                'id': self._get_element_text(event_elem, 'id'),
                'programName': self._get_element_text(event_elem, 'program-name'),
                'name': self._get_element_text(event_elem, 'name'),
                'type': self._get_element_text(event_elem, 'type'),
                'typeDescr': self._get_element_text(event_elem, 'type-descr'),
                'status': self._get_element_text(event_elem, 'status'),
                'startDt': self._get_element_text(event_elem, 'start-dt'),
                'endDt': self._get_element_text(event_elem, 'end-dt'),
                'deadlineDt': self._get_element_text(event_elem, 'deadline-dt'),
                'requireSecondaryItem': self._get_element_text(event_elem, 'requireSecondaryItem'),
                'locationNm': self._get_element_text(event_elem, 'location-nm'),
                'locationStreet1': self._get_element_text(event_elem, 'location-street1'),
                'locationStreet2': self._get_element_text(event_elem, 'location-street2'),
                'locationCity': self._get_element_text(event_elem, 'location-city'),
                'locationState': self._get_element_text(event_elem, 'location-state'),
                'locationZip': self._get_element_text(event_elem, 'location-zip'),
                'locationCountry': self._get_element_text(event_elem, 'location-country'),
                'locationCountryDescr': self._get_element_text(event_elem, 'location-country-descr'),
                'registerUrl': self._get_element_text(event_elem, 'register-url'),
                'registrationStatus': self._get_element_text(event_elem, 'registration-status'),
                'lastChangeDate': self._get_element_text(event_elem, 'lastChangeDate')
            }
            
            # Parse attributes
            attributes = []
            for attr_elem in event_elem.findall('.//attribute-list/attribute'):
                attr_data = {
                    'type': self._get_element_text(attr_elem, 'type'),
                    'code': self._get_element_text(attr_elem, 'code'),
                    'characterValue': self._get_element_text(attr_elem, 'character-value'),
                    'numberValue': self._get_element_text(attr_elem, 'number-value'),
                    'dateValue': self._get_element_text(attr_elem, 'date-value'),
                    'URLtoFile': self._get_element_text(attr_elem, 'URLtoFile'),
                    'URLtoThumbnail': self._get_element_text(attr_elem, 'URLtoThumbnail')
                }
                attributes.append(attr_data)
            event_data['attributes'] = attributes
            
            # Parse valid registration types
            registration_types = []
            for reg_type_elem in event_elem.findall('.//validRegistrationTypes/regType'):
                reg_type_data = {
                    'type': self._get_element_text(reg_type_elem, 'type'),
                    'descr': self._get_element_text(reg_type_elem, 'descr'),
                    'defaultCl': self._get_element_text(reg_type_elem, 'defaultCl'),
                    'waitlistingFlag': self._get_element_text(reg_type_elem, 'waitlistingFlag'),
                    'staffFlag': self._get_element_text(reg_type_elem, 'staffFlag')
                }
                registration_types.append(reg_type_data)
            event_data['validRegistrationTypes'] = registration_types
            
            # Parse sponsor list (if any)
            sponsors = []
            for sponsor_elem in event_elem.findall('.//sponsor-list/sponsor'):
                sponsor_data = {
                    'sponsorId': self._get_element_text(sponsor_elem, 'sponsor-id'),
                    'sponsorName': self._get_element_text(sponsor_elem, 'sponsor-name'),
                    'sponsorType': self._get_element_text(sponsor_elem, 'sponsor-type')
                }
                sponsors.append(sponsor_data)
            event_data['sponsors'] = sponsors
            
            if len(events) >= limit:
                break
            events.append(event_data)
            
        events_data['events'] = events
        
        return events_data

    def _parse_customer_xml_old(self, root: ET.Element) -> Dict[str, any]:
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