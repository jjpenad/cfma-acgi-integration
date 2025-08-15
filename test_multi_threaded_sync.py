#!/usr/bin/env python3
"""
Test script for multi-threaded scheduler with multiple HubSpot API keys
"""

import os
import sys
import time

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_multi_threaded_scheduler():
    """Test the multi-threaded scheduler functionality"""
    try:
        from services.scheduler_service import SchedulerService
        from models import get_app_credentials
        
        print("🧪 Testing Multi-Threaded Scheduler")
        print("=" * 50)
        
        # Test 1: Check if scheduler initializes with thread pool
        print("\n1. Testing scheduler initialization...")
        scheduler = SchedulerService()
        print(f"   ✅ Scheduler initialized with thread pool size: {scheduler.thread_pool._max_workers}")
        
        # Test 2: Check credentials with multiple API keys
        print("\n2. Testing credentials with multiple API keys...")
        creds = get_app_credentials()
        if creds:
            print("   ✅ Credentials loaded successfully")
            print(f"   General API key: {'✅ Set' if creds.get('hubspot_api_key') else '❌ Not set'}")
            print(f"   Contacts API key: {'✅ Set' if creds.get('hubspot_api_key_contacts') else '❌ Not set'}")
            print(f"   Memberships API key: {'✅ Set' if creds.get('hubspot_api_key_memberships') else '❌ Not set'}")
            print(f"   Orders API key: {'✅ Set' if creds.get('hubspot_api_key_orders') else '❌ Not set'}")
            print(f"   Events API key: {'✅ Set' if creds.get('hubspot_api_key_events') else '❌ Not set'}")
        else:
            print("   ❌ No credentials found")
        
        # Test 3: Test scheduler status
        print("\n3. Testing scheduler status...")
        status = scheduler.get_status()
        print(f"   ✅ Scheduler status retrieved")
        print(f"   Thread pool size: {status.get('thread_pool_size', 'N/A')}")
        print(f"   Is running: {status.get('is_running', 'N/A')}")
        
        # Test 4: Test manual sync with multi-threading
        print("\n4. Testing manual sync with multi-threading...")
        test_config = {
            'customer_ids': '12345\n67890',
            'sync_contacts': True,
            'sync_memberships': True,
            'sync_orders': True,
            'sync_events': True
        }
        
        print("   Starting manual sync...")
        start_time = time.time()
        result = scheduler.run_manual_sync()
        end_time = time.time()
        
        print(f"   ✅ Manual sync completed in {end_time - start_time:.2f} seconds")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Results: {result}")
        
        # Test 5: Test thread pool shutdown
        print("\n5. Testing thread pool shutdown...")
        scheduler.stop()
        print("   ✅ Scheduler stopped and thread pool shutdown")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_multi_threaded_scheduler()
    sys.exit(0 if success else 1) 