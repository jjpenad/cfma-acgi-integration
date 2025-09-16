#!/usr/bin/env python3
"""
Test script for the new queue-based customer functions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.acgi_client import ACGIClient

def test_queue_functions():
    """Test the new queue-based functions"""
    
    # Initialize ACGI client
    acgi_client = ACGIClient()
    
    # Test credentials (you'll need to replace with actual credentials)
    test_credentials = {
        'userid': 'test_user',
        'password': 'test_password',
        'environment': 'cetdigitdev'
    }
    
    print("Testing queue-based customer functions...")
    
    # Test 1: Get queue customers
    print("\n1. Testing get_queue_customers...")
    queue_result = acgi_client.get_queue_customers(test_credentials)
    print(f"Queue result success: {queue_result.get('success')}")
    print(f"Queue result message: {queue_result.get('message', 'No message')}")
    
    if queue_result.get('success'):
        queue_data = queue_result.get('queue_data', {})
        print(f"Customers in queue: {len(queue_data.get('customers', []))}")
        print(f"Max queue number: {queue_data.get('maxQueueNum')}")
        print(f"Status: {queue_data.get('status')}")
    
    # Test 2: Extract customer IDs
    print("\n2. Testing extract_customer_ids_from_queue...")
    customer_ids = acgi_client.extract_customer_ids_from_queue(queue_result)
    print(f"Extracted customer IDs: {customer_ids}")
    
    # Test 3: Purge queue (if we have a max queue number)
    if queue_result.get('success') and queue_result.get('queue_data', {}).get('maxQueueNum'):
        print("\n3. Testing purge_queue...")
        max_queue_num = queue_result['queue_data']['maxQueueNum']
        purge_result = acgi_client.purge_queue(test_credentials, max_queue_num)
        print(f"Purge result success: {purge_result.get('success')}")
        print(f"Purge result message: {purge_result.get('message', 'No message')}")
        
        if purge_result.get('success'):
            purge_data = purge_result.get('purge_result', {})
            print(f"Purge status: {purge_data.get('status')}")
            print(f"Purge message: {purge_data.get('message', 'No message')}")
    
    print("\nQueue function tests completed!")

if __name__ == "__main__":
    test_queue_functions()
