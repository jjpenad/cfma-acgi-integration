#!/usr/bin/env python3
"""
ACGI Contact Export Script

This script exports contacts from ACGI by querying customer IDs from 1 to 30000
in batches of 100 using the CENSSAWEBSVCLIB.GET_CUST_INFO_XML endpoint with bulk request.

Only contacts with email addresses are exported to CSV.
"""

import os
import sys
import csv
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import time
from dotenv import load_dotenv

# Add current directory to Python path first (for local config)
sys.path.insert(0, os.path.dirname(__file__))

# Import local config module
from config import ExportConfig

# Import shared utilities
from shared_utils import BaseExporter

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.acgi_client import ACGIClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = getattr(logging, ExportConfig.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ExportConfig.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ContactExporter(BaseExporter):
    """Export contacts from ACGI to CSV"""
    
    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize the contact exporter
        
        Args:
            credentials: Dictionary containing ACGI credentials
                - userid: ACGI username
                - password: ACGI password
                - environment: 'test' or 'prod'
        """
        # Initialize parent class
        super().__init__(credentials)
        
        # Additional statistics specific to contacts
        self.total_with_emails = 0
        
    def create_bulk_request_xml(self, customer_ids: List[int]) -> str:
        """
        Create XML request for bulk customer data retrieval
        
        Args:
            customer_ids: List of customer IDs to query
            
        Returns:
            XML string for the request
        """
        # Create custId elements
        cust_id_elements = '\n'.join([f'    <custId>{cid}</custId>' for cid in customer_ids])
        
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
        <custInfoRequest>
        {cust_id_elements}
            <integratorUsername>{self.credentials['userid']}</integratorUsername>
            <integratorPassword>{self.credentials['password']}</integratorPassword>
            <directoryId></directoryId>
            <bulkRequest>true</bulkRequest>
            <details includeCodeValues="true">
                <roles include="true" />
                <addresses include="true" includeBad="true" />
                <phones include="true" />
                <emails include="true" includeBad="true" />
                <websites include="true" includeBad="true" />
                <jobs include="true" includeInactive="true" />
                <bio include="true" />
                <aliases include="true" />
                <companyAdmins include="true" />
                <certifications include="true" />
                <employees include="true" />
                <referralInfo include="true" />
                <files include="true" />
            </details>
        </custInfoRequest>"""
        
        return xml_template
    
    def get_customer_batch(self, customer_ids: List[int]) -> Dict[str, Any]:
        """
        Get customer data for a batch of customer IDs
        
        Args:
            customer_ids: List of customer IDs to query
            
        Returns:
            Dictionary containing success status and customer data
        """
        try:
            # Create the XML request
            xml_request = self.create_bulk_request_xml(customer_ids)
            
            # Determine environment URL
            environment = self.credentials['environment']
            url = f"{self.base_url}/{environment}/CENSSAWEBSVCLIB.GET_CUST_INFO_XML"
            
            logger.info(f"Requesting batch of {len(customer_ids)} customers: {customer_ids[0]}-{customer_ids[-1]}")
            
            # Make the request
            response = self.session.post(
                url,
                data={'p_input_xml_doc': xml_request},
                timeout=ExportConfig.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                try:
                    # Parse the XML response
                    root = ET.fromstring(response.text)
                    customers = self.parse_customer_batch_xml(root)
                    
                    return {
                        'success': True,
                        'customers': customers,
                        'batch_size': len(customer_ids)
                    }
                    
                except ET.ParseError as e:
                    logger.error(f"Failed to parse XML response for batch {customer_ids[0]}-{customer_ids[-1]}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"XML parsing failed: {str(e)}",
                        'batch_size': len(customer_ids)
                    }
            else:
                logger.error(f"HTTP {response.status_code} for batch {customer_ids[0]}-{customer_ids[-1]}: {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'batch_size': len(customer_ids)
                }
                
        except Exception as e:
            logger.error(f"Error processing batch {customer_ids[0]}-{customer_ids[-1]}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'batch_size': len(customer_ids)
            }
    
    def parse_customer_batch_xml(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Parse customer batch XML response
        
        Args:
            root: XML root element
            
        Returns:
            List of customer dictionaries
        """
        customers = []
        
        # Find all customer elements
        for customer_elem in root.findall('.//custInfo'):
            try:
                customer = self.parse_single_customer_xml(customer_elem)
                if customer:
                    customers.append(customer)
            except Exception as e:
                logger.error(f"Error parsing customer element: {str(e)}")
                continue
        
        return customers
    
    def parse_single_customer_xml(self, customer_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a single customer XML element
        
        Args:
            customer_elem: Customer XML element
            
        Returns:
            Customer dictionary or None if parsing fails
        """
        try:
            customer = {}
            
            # Basic customer info
            customer['custId'] = self.get_element_text(customer_elem, 'custId')
            print("customer['custId']",customer['custId'])
            customer['custType'] = self.get_element_text(customer_elem, 'custType')
            customer['loginId'] = self.get_element_text(customer_elem, 'loginId')
            
            # Name fields
            name_elem = customer_elem.find('name')
            if name_elem is not None:
                customer['prefixName'] = self.get_element_text(name_elem, 'prefixName')
                customer['firstName'] = self.get_element_text(name_elem, 'firstName')
                customer['middleName'] = self.get_element_text(name_elem, 'middleName')
                customer['lastName'] = self.get_element_text(name_elem, 'lastName')
                customer['suffixName'] = self.get_element_text(name_elem, 'suffixName')
                customer['degreeName'] = self.get_element_text(name_elem, 'degreeName')
                customer['informalName'] = self.get_element_text(name_elem, 'informalName')
                customer['displayName'] = self.get_element_text(name_elem, 'displayName')
            
            # Emails - this is what we need to filter on
            emails = []
            for email_elem in customer_elem.findall('.//emails/email'):
                email_data = {
                    'emailSerno': self.get_element_text(email_elem, 'emailSerno'),
                    'emailType': self.get_element_text(email_elem, 'emailType'),
                    'emailTypeDescr': self.get_element_text(email_elem, 'emailTypeDescr'),
                    'best': self.get_element_text(email_elem, 'best') == 'true',
                    'preferred': self.get_element_text(email_elem, 'preferred') == 'true',
                    'address': self.get_element_text(email_elem, 'address'),
                    'badAddress': self.get_element_text(email_elem, 'badAddress') == 'true'
                }
                # Only include non-bad email addresses
                if email_data['address'] and not email_data['badAddress']:
                    emails.append(email_data)
            
            customer['emails'] = emails
            
            # Only return customers that have at least one valid email
            if not emails:
                return None
            
            # Addresses
            addresses = []
            for addr_elem in customer_elem.findall('.//addresses/address'):
                addr_data = {
                    'addressSerno': self.get_element_text(addr_elem, 'addressSerno'),
                    'addressType': self.get_element_text(addr_elem, 'addressType'),
                    'addressTypeDescr': self.get_element_text(addr_elem, 'addressTypeDescr'),
                    'best': self.get_element_text(addr_elem, 'best') == 'true',
                    'preferred': self.get_element_text(addr_elem, 'preferred') == 'true',
                    'street1': self.get_element_text(addr_elem, 'street1'),
                    'street2': self.get_element_text(addr_elem, 'street2'),
                    'street3': self.get_element_text(addr_elem, 'street3'),
                    'city': self.get_element_text(addr_elem, 'city'),
                    'state': self.get_element_text(addr_elem, 'state'),
                    'postalCode': self.get_element_text(addr_elem, 'postalCode'),
                    'countryCode': self.get_element_text(addr_elem, 'countryCode'),
                    'countryDescr': self.get_element_text(addr_elem, 'countryDescr'),
                    'badAddress': self.get_element_text(addr_elem, 'badAddress') == 'true'
                }
                addresses.append(addr_data)
            customer['addresses'] = addresses
            
            # Phones
            phones = []
            for phone_elem in customer_elem.findall('.//phones/phone'):
                phone_data = {
                    'phoneSerno': self.get_element_text(phone_elem, 'phoneSerno'),
                    'phoneType': self.get_element_text(phone_elem, 'phoneType'),
                    'phoneTypeDescr': self.get_element_text(phone_elem, 'phoneTypeDescr'),
                    'best': self.get_element_text(phone_elem, 'best') == 'true',
                    'preferred': self.get_element_text(phone_elem, 'preferred') == 'true',
                    'number': self.get_element_text(phone_elem, 'number'),
                    'ext': self.get_element_text(phone_elem, 'ext')
                }
                phones.append(phone_data)
            customer['phones'] = phones
            
            # Jobs
            jobs = []
            for job_elem in customer_elem.findall('.//jobs/job'):
                job_data = {
                    'employerName': self.get_element_text(job_elem, 'employerName'),
                    'titleName': self.get_element_text(job_elem, 'titleName'),
                    'startDate': self.get_element_text(job_elem, 'startDate'),
                    'endDate': self.get_element_text(job_elem, 'endDate'),
                    'best': self.get_element_text(job_elem, 'best') == 'true',
                    'preferred': self.get_element_text(job_elem, 'preferred') == 'true'
                }
                jobs.append(job_data)
            customer['jobs'] = jobs
            
            return customer
            
        except Exception as e:
            logger.error(f"Error parsing customer XML: {str(e)}")
            return None
    
    def get_element_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Safely get text from an XML element"""
        elem = parent.find(tag)
        return elem.text if elem is not None else None
    
    def export_contacts_to_csv(self, output_file: str = None) -> str:
        """
        Export all contacts with emails to CSV
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to the created CSV file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if ExportConfig.INCLUDE_TIMESTAMP else ""
            filename = f"contacts_export_{timestamp}.csv" if timestamp else "contacts_export.csv"
            output_file = os.path.join(ExportConfig.OUTPUT_DIRECTORY, filename)
        
        self.start_time = datetime.now()
        logger.info(f"Starting contact export to {output_file}")
        logger.info(f"Processing customer IDs {ExportConfig.START_CUSTOMER_ID}-{ExportConfig.END_CUSTOMER_ID} in batches of {ExportConfig.BATCH_SIZE}")
        
        # Create batches of customer IDs
        batch_size = ExportConfig.BATCH_SIZE
        batch_count = 0
        
        for start_id in range(ExportConfig.START_CUSTOMER_ID, ExportConfig.END_CUSTOMER_ID + 1, batch_size):
            end_id = min(start_id + batch_size - 1, ExportConfig.END_CUSTOMER_ID)
            customer_ids = list(range(start_id, end_id + 1))
            
            logger.info(f"Processing batch: {start_id}-{end_id}")
            # Get customer data for this batch
            result = self.get_customer_batch(customer_ids)
            
            if result['success']:
                customers = result['customers']
                self.total_processed += result['batch_size']
                self.total_with_emails += len(customers)
                logger.info(f"Batch {start_id}-{end_id}: Found {len(customers)} customers with emails")
                
                # Write batch to CSV immediately
                if customers:
                    self.write_customers_batch_to_csv(customers, output_file, is_first_batch=(batch_count == 0))
                    batch_count += 1
            else:
                self.total_errors += result['batch_size']
                logger.error(f"Batch {start_id}-{end_id} failed: {result.get('error', 'Unknown error')}")
            
            # Add a delay between requests to be respectful to the API
            time.sleep(ExportConfig.REQUEST_DELAY)
        
        # Print summary
        self.print_summary()
        
        return output_file
    
    def export_contacts_from_csv(self, csv_file_path: str, id_column: str = 'custId', output_file: str = None) -> str:
        """
        Export contacts from ACGI for customer IDs read from a CSV file
        
        Args:
            csv_file_path: Path to CSV file containing customer IDs
            id_column: Name of the column containing customer IDs
            output_file: Optional output file path
            
        Returns:
            Path to the created CSV file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if ExportConfig.INCLUDE_TIMESTAMP else ""
            filename = f"contacts_export_{timestamp}.csv" if timestamp else "contacts_export.csv"
            output_file = os.path.join(ExportConfig.OUTPUT_DIRECTORY, filename)
        
        self.start_time = datetime.now()
        logger.info(f"Starting contact export from CSV to {output_file}")
        logger.info(f"Reading customer IDs from {csv_file_path}")
        
        # Read customer IDs from CSV
        customer_ids = self.read_customer_ids_from_csv(csv_file_path, id_column)
        
        if not customer_ids:
            logger.warning("No customer IDs found in CSV file")
            return output_file
        
        batch_count = 0
        
        for i, customer_id in enumerate(customer_ids, 1):
            logger.info(f"Processing customer {i}/{len(customer_ids)}: {customer_id}")
            
            # Get customer data for this customer ID
            result = self.get_customer_batch([int(customer_id)])
            
            if result['success']:
                customers = result['customers']
                self.total_processed += result['batch_size']
                self.total_with_emails += len(customers)
                logger.info(f"  Found {len(customers)} customers with emails")
                
                # Write batch to CSV immediately
                if customers:
                    self.write_customers_batch_to_csv(customers, output_file, is_first_batch=(batch_count == 0))
                    batch_count += 1
            else:
                self.total_errors += result['batch_size']
                logger.error(f"  Error: {result.get('error', 'Unknown error')}")
            
            # Add delay between requests
            time.sleep(ExportConfig.REQUEST_DELAY)
        
        # Print summary
        self.print_summary()
        
        return output_file
    
    def write_customers_to_csv(self, customers: List[Dict[str, Any]], output_file: str):
        """
        Write customers to CSV file
        
        Args:
            customers: List of customer dictionaries
            output_file: Output file path
        """
        if not customers:
            logger.warning("No customers to export")
            return
        
        # Define CSV columns
        fieldnames = [
            'custId', 'custType', 'loginId',
            'prefixName', 'firstName', 'middleName', 'lastName', 'suffixName', 
            'degreeName', 'informalName', 'displayName',
            'Email', 'Additional_Emails',
            'primary_phone', 'primary_phone_type', 'primary_phone_number',
            'primary_address_street1', 'primary_address_street2', 'primary_address_city',
            'primary_address_state', 'primary_address_postalCode', 'primary_address_country',
            'primary_job_employer', 'primary_job_title',
            'total_emails', 'total_phones', 'total_addresses', 'total_jobs'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for customer in customers:
                # Extract preferred email and additional emails
                preferred_email = None
                additional_emails = []
                
                if customer.get('emails'):
                    # Find preferred email (preferred=True)
                    preferred_email_data = next((email for email in customer['emails'] if email.get('preferred')), None)
                    if preferred_email_data:
                        preferred_email = preferred_email_data.get('address')
                    
                    # If no preferred email, use the first email as primary
                    if not preferred_email and customer['emails']:
                        preferred_email = customer['emails'][0].get('address')
                    
                    # Collect all other emails (excluding the preferred one)
                    for email in customer['emails']:
                        email_address = email.get('address')
                        if email_address and email_address != preferred_email:
                            additional_emails.append(email_address)
                
                # Extract primary phone (best or first)
                primary_phone = None
                primary_phone_type = None
                primary_phone_number = None
                
                if customer.get('phones'):
                    best_phone = next((phone for phone in customer['phones'] if phone.get('best')), None)
                    primary_phone_data = best_phone or customer['phones'][0]
                    
                    primary_phone = primary_phone_data.get('phoneTypeDescr')
                    primary_phone_type = primary_phone_data.get('phoneType')
                    primary_phone_number = primary_phone_data.get('number')
                
                # Extract primary address (best or first)
                primary_address_street1 = None
                primary_address_street2 = None
                primary_address_city = None
                primary_address_state = None
                primary_address_postalCode = None
                primary_address_country = None
                
                if customer.get('addresses'):
                    best_address = next((addr for addr in customer['addresses'] if addr.get('best')), None)
                    primary_address_data = best_address or customer['addresses'][0]
                    
                    primary_address_street1 = primary_address_data.get('street1')
                    primary_address_street2 = primary_address_data.get('street2')
                    primary_address_city = primary_address_data.get('city')
                    primary_address_state = primary_address_data.get('state')
                    primary_address_postalCode = primary_address_data.get('postalCode')
                    primary_address_country = primary_address_data.get('countryDescr')
                
                # Extract primary job (best or first)
                primary_job_employer = None
                primary_job_title = None
                
                if customer.get('jobs'):
                    best_job = next((job for job in customer['jobs'] if job.get('best')), None)
                    primary_job_data = best_job or customer['jobs'][0]
                    
                    primary_job_employer = primary_job_data.get('employerName')
                    primary_job_title = primary_job_data.get('titleName')
                
                # Write row
                row = {
                    'custId': customer.get('custId'),
                    'custType': customer.get('custType'),
                    'loginId': customer.get('loginId'),
                    'prefixName': customer.get('prefixName'),
                    'firstName': customer.get('firstName'),
                    'middleName': customer.get('middleName'),
                    'lastName': customer.get('lastName'),
                    'suffixName': customer.get('suffixName'),
                    'degreeName': customer.get('degreeName'),
                    'informalName': customer.get('informalName'),
                    'displayName': customer.get('displayName'),
                    'Email': preferred_email,
                    'Additional_Emails': '; '.join(additional_emails) if additional_emails else '',
                    'primary_phone': primary_phone,
                    'primary_phone_type': primary_phone_type,
                    'primary_phone_number': primary_phone_number,
                    'primary_address_street1': primary_address_street1,
                    'primary_address_street2': primary_address_street2,
                    'primary_address_city': primary_address_city,
                    'primary_address_state': primary_address_state,
                    'primary_address_postalCode': primary_address_postalCode,
                    'primary_address_country': primary_address_country,
                    'primary_job_employer': primary_job_employer,
                    'primary_job_title': primary_job_title,
                    'total_emails': len(customer.get('emails', [])),
                    'total_phones': len(customer.get('phones', [])),
                    'total_addresses': len(customer.get('addresses', [])),
                    'total_jobs': len(customer.get('jobs', []))
                }
                
                writer.writerow(row)
        
        logger.info(f"Exported {len(customers)} customers to {output_file}")
    
    def write_customers_batch_to_csv(self, customers: List[Dict[str, Any]], output_file: str, is_first_batch: bool = False):
        """
        Write a batch of customers to CSV file incrementally
        
        Args:
            customers: List of customer dictionaries
            output_file: Output file path
            is_first_batch: Whether this is the first batch (write header)
        """
        if not customers:
            return
        
        # Define CSV columns
        fieldnames = [
            'custId', 'custType', 'loginId',
            'prefixName', 'firstName', 'middleName', 'lastName', 'suffixName', 
            'degreeName', 'informalName', 'displayName',
            'Email', 'Additional_Emails',
            'primary_phone', 'primary_phone_type', 'primary_phone_number',
            'primary_address_street1', 'primary_address_street2', 'primary_address_city',
            'primary_address_state', 'primary_address_postalCode', 'primary_address_country',
            'primary_job_employer', 'primary_job_title',
            'total_emails', 'total_phones', 'total_addresses', 'total_jobs'
        ]
        
        # Prepare batch data
        batch_data = []
        for customer in customers:
            # Extract preferred email and additional emails
            preferred_email = None
            additional_emails = []
            
            if customer.get('emails'):
                # Find preferred email (preferred=True)
                preferred_email_data = next((email for email in customer['emails'] if email.get('preferred')), None)
                if preferred_email_data:
                    preferred_email = preferred_email_data.get('address')
                
                # If no preferred email, use the first email as primary
                if not preferred_email and customer['emails']:
                    preferred_email = customer['emails'][0].get('address')
                
                # Collect all other emails (excluding the preferred one)
                for email in customer['emails']:
                    email_address = email.get('address')
                    if email_address and email_address != preferred_email:
                        additional_emails.append(email_address)
            
            # Extract primary phone (best or first)
            primary_phone = None
            primary_phone_type = None
            primary_phone_number = None
            
            if customer.get('phones'):
                best_phone = next((phone for phone in customer['phones'] if phone.get('best')), None)
                primary_phone_data = best_phone or customer['phones'][0]
                
                primary_phone = primary_phone_data.get('phoneTypeDescr')
                primary_phone_type = primary_phone_data.get('phoneType')
                primary_phone_number = primary_phone_data.get('number')
            
            # Extract primary address (best or first)
            primary_address_street1 = None
            primary_address_street2 = None
            primary_address_city = None
            primary_address_state = None
            primary_address_postalCode = None
            primary_address_country = None
            
            if customer.get('addresses'):
                best_address = next((addr for addr in customer['addresses'] if addr.get('best')), None)
                primary_address_data = best_address or customer['addresses'][0]
                
                primary_address_street1 = primary_address_data.get('street1')
                primary_address_street2 = primary_address_data.get('street2')
                primary_address_city = primary_address_data.get('city')
                primary_address_state = primary_address_data.get('state')
                primary_address_postalCode = primary_address_data.get('postalCode')
                primary_address_country = primary_address_data.get('countryDescr')
            
            # Extract primary job (best or first)
            primary_job_employer = None
            primary_job_title = None
            
            if customer.get('jobs'):
                best_job = next((job for job in customer['jobs'] if job.get('best')), None)
                primary_job_data = best_job or customer['jobs'][0]
                
                primary_job_employer = primary_job_data.get('employer')
                primary_job_title = primary_job_data.get('title')
            
            # Create row data
            row_data = {
                'custId': customer.get('custId', ''),
                'custType': customer.get('custType', ''),
                'loginId': customer.get('loginId', ''),
                'prefixName': customer.get('prefixName', ''),
                'firstName': customer.get('firstName', ''),
                'middleName': customer.get('middleName', ''),
                'lastName': customer.get('lastName', ''),
                'suffixName': customer.get('suffixName', ''),
                'degreeName': customer.get('degreeName', ''),
                'informalName': customer.get('informalName', ''),
                'displayName': customer.get('displayName', ''),
                'Email': preferred_email or '',
                'Additional_Emails': '; '.join(additional_emails) if additional_emails else '',
                'primary_phone': primary_phone or '',
                'primary_phone_type': primary_phone_type or '',
                'primary_phone_number': primary_phone_number or '',
                'primary_address_street1': primary_address_street1 or '',
                'primary_address_street2': primary_address_street2 or '',
                'primary_address_city': primary_address_city or '',
                'primary_address_state': primary_address_state or '',
                'primary_address_postalCode': primary_address_postalCode or '',
                'primary_address_country': primary_address_country or '',
                'primary_job_employer': primary_job_employer or '',
                'primary_job_title': primary_job_title or '',
                'total_emails': len(customer.get('emails', [])),
                'total_phones': len(customer.get('phones', [])),
                'total_addresses': len(customer.get('addresses', [])),
                'total_jobs': len(customer.get('jobs', []))
            }
            
            batch_data.append(row_data)
        
        # Write batch to CSV using the base class method
        self.write_batch_to_csv(batch_data, output_file, fieldnames, is_first_batch)
    
    def print_summary(self):
        """Print export summary"""
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info("=" * 50)
            logger.info("EXPORT SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Total customer IDs processed: {self.total_processed}")
            logger.info(f"Customers with emails exported: {self.total_with_emails}")
            logger.info(f"Errors encountered: {self.total_errors}")
            logger.info(f"Duration: {duration}")
            logger.info(f"Success rate: {(self.total_with_emails / self.total_processed * 100):.2f}%" if self.total_processed > 0 else "N/A")
            logger.info("=" * 50)


def main():
    """Main function to run the contact export"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Export contacts from ACGI to CSV')
    parser.add_argument('csv_file', nargs='?', help='CSV file containing customer IDs (optional)')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--id-column', default='custId', help='Name of the column containing customer IDs')
    
    args = parser.parse_args()
    
    # Validate configuration
    config_errors = ExportConfig.validate()
    if config_errors:
        logger.error("Configuration errors:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.error("Please check your .env file or environment variables")
        sys.exit(1)
    
    # Get credentials from configuration
    credentials = ExportConfig.get_credentials()
    
    logger.info("ACGI Contact Export Starting")
    logger.info(f"Environment: {credentials['environment']}")
    logger.info(f"Username: {credentials['userid']}")
    
    # Create exporter and run export
    exporter = ContactExporter(credentials)
    
    try:
        if args.csv_file:
            # Export from CSV file
            logger.info(f"Reading customer IDs from: {args.csv_file}")
            logger.info(f"ID Column: {args.id_column}")
            output_file = exporter.export_contacts_from_csv(args.csv_file, args.id_column, args.output)
        else:
            # Export from configured range
            logger.info(f"Customer ID Range: {ExportConfig.START_CUSTOMER_ID}-{ExportConfig.END_CUSTOMER_ID}")
            logger.info(f"Batch Size: {ExportConfig.BATCH_SIZE}")
            output_file = exporter.export_contacts_to_csv(args.output)
        
        logger.info(f"Export completed successfully: {output_file}")
    except KeyboardInterrupt:
        logger.info("Export interrupted by user")
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
