#!/usr/bin/env python3
"""
Test script for the make_request function with retry logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.hubspot_client import HubSpotClient
import logging

# Set up logging to see the retry behavior
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_make_request():
    """Test the make_request function"""
    client = HubSpotClient()
    
    print("Testing make_request function...")
    print("=" * 50)
    
    # Test 1: Normal request (should succeed)
    print("\n1. Testing normal request (should succeed):")
    try:
        response = client.make_request('GET', 'https://httpbin.org/status/200', timeout=5)
        print(f"✅ Success: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Request to non-existent endpoint (should fail with 404, no retry)
    print("\n2. Testing request to non-existent endpoint (should fail with 404, no retry):")
    try:
        response = client.make_request('GET', 'https://httpbin.org/status/404', timeout=5)
        print(f"✅ Got response: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Request that times out (should retry with exponential backoff)
    print("\n3. Testing request that times out (should retry with exponential backoff):")
    try:
        response = client.make_request('GET', 'https://httpbin.org/delay/10', timeout=2)
        print(f"✅ Success: Status {response.status_code}")
    except Exception as e:
        print(f"✅ Expected timeout after retries: {e}")
    
    # Test 4: Rate limited request (should retry with backoff)
    print("\n4. Testing rate limited request (should retry with backoff):")
    try:
        response = client.make_request('GET', 'https://httpbin.org/status/429', timeout=5)
        print(f"✅ Got response: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_make_request() 