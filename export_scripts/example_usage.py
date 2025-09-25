#!/usr/bin/env python3
"""
Example usage of the ACGI Contact Export Script

This script demonstrates how to use the ContactExporter class programmatically.
"""

import os
import sys

# Add current directory to Python path first (for local config)
sys.path.insert(0, os.path.dirname(__file__))

from config import ExportConfig
from export_contacts import ContactExporter

def main():
    """Example usage of the contact exporter"""
    
    # Validate configuration
    config_errors = ExportConfig.validate()
    if config_errors:
        print("Configuration errors:")
        for error in config_errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Get credentials from configuration
    credentials = ExportConfig.get_credentials()
    
    print("ACGI Contact Export Example")
    print("=" * 40)
    print(f"Environment: {credentials['environment']}")
    print(f"Username: {credentials['userid']}")
    print(f"Customer ID Range: {ExportConfig.START_CUSTOMER_ID}-{ExportConfig.END_CUSTOMER_ID}")
    print(f"Batch Size: {ExportConfig.BATCH_SIZE}")
    print("=" * 40)
    
    # Create exporter instance
    exporter = ContactExporter(credentials)
    
    # Example 1: Export all contacts (1-30000)
    print("\n1. Exporting all contacts...")
    try:
        output_file = exporter.export_contacts_to_csv()
        print(f"Export completed: {output_file}")
    except Exception as e:
        print(f"Export failed: {str(e)}")
    
    # Example 2: Export specific range (1-1000)
    print("\n2. Exporting contacts 1-1000...")
    try:
        # Temporarily modify the range
        original_start = ExportConfig.START_CUSTOMER_ID
        original_end = ExportConfig.END_CUSTOMER_ID
        
        # Create a custom exporter for specific range
        custom_exporter = ContactExporter(credentials)
        
        # Override the batch processing for custom range
        all_customers = []
        batch_size = 100
        
        for start_id in range(1, 1001, batch_size):
            end_id = min(start_id + batch_size - 1, 1000)
            customer_ids = list(range(start_id, end_id + 1))
            
            print(f"Processing batch: {start_id}-{end_id}")
            result = custom_exporter.get_customer_batch(customer_ids)
            
            if result['success']:
                customers = result['customers']
                all_customers.extend(customers)
                print(f"  Found {len(customers)} customers with emails")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        # Write to CSV
        output_file = "export_scripts/contacts_1_1000.csv"
        custom_exporter.write_customers_to_csv(all_customers, output_file)
        print(f"Custom export completed: {output_file}")
        
    except Exception as e:
        print(f"Custom export failed: {str(e)}")
    
    # Example 3: Test with a small batch
    print("\n3. Testing with small batch (1-10)...")
    try:
        test_exporter = ContactExporter(credentials)
        customer_ids = list(range(1, 11))
        result = test_exporter.get_customer_batch(customer_ids)
        
        if result['success']:
            customers = result['customers']
            print(f"Test successful: Found {len(customers)} customers with emails")
            
            # Print first customer details
            if customers:
                first_customer = customers[0]
                print(f"First customer: {first_customer.get('firstName')} {first_customer.get('lastName')}")
                print(f"  Email: {first_customer.get('emails', [{}])[0].get('address', 'N/A')}")
                print(f"  Customer ID: {first_customer.get('custId')}")
        else:
            print(f"Test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main()
