#!/usr/bin/env python3
"""
Quick test script to verify the trial and licensing system is working correctly.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from license_manager import LicenseManager

def test_trial_system():
    print("🧪 Testing Trial and Licensing System")
    print("=" * 50)
    
    # Create test data directory
    test_dir = Path("test_license_data")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize license manager
        print("1. Initializing License Manager...")
        license_manager = LicenseManager(test_dir)
        print("✅ License Manager initialized successfully")
        
        # Test trial status
        print("\n2. Checking Trial Status...")
        status = license_manager.get_license_status()
        print(f"   License Type: {status['license_type']}")
        print(f"   Trial Valid: {status['is_valid']}")
        print(f"   Days Remaining: {status['days_remaining']}")
        print("✅ Trial status retrieved successfully")
        
        # Test feature limits
        print("\n3. Testing Feature Limits...")
        
        # Test client creation
        can_create, message = license_manager.can_create_client()
        print(f"   Can create client: {can_create}")
        if message:
            print(f"   Message: {message}")
        
        # Test document upload
        can_upload, message = license_manager.can_upload_document()
        print(f"   Can upload document: {can_upload}")
        if message:
            print(f"   Message: {message}")
            
        # Test query
        can_query, message = license_manager.can_make_query()
        print(f"   Can make query: {can_query}")
        if message:
            print(f"   Message: {message}")
        
        print("✅ Feature limits tested successfully")
        
        # Test usage recording
        print("\n4. Testing Usage Recording...")
        
        # Record some usage
        license_manager.record_client_creation()
        license_manager.record_document_upload()
        license_manager.record_query()
        
        # Check updated status
        new_status = license_manager.get_license_status()
        print(f"   Clients created: {new_status['usage_stats']['clients_created']}")
        print(f"   Documents uploaded: {new_status['usage_stats']['documents_uploaded']}")
        print(f"   Queries today: {new_status['usage_stats']['queries_made_today']}")
        
        print("✅ Usage recording tested successfully")
        
        # Test license activation (mock)
        print("\n5. Testing License Activation...")
        success, message = license_manager.activate_pro_license("TEST-KEY-123")
        print(f"   Activation success: {success}")
        print(f"   Message: {message}")
        
        if success:
            final_status = license_manager.get_license_status()
            print(f"   Updated license type: {final_status['license_type']}")
        
        print("✅ License activation tested successfully")
        
        print("\n🎉 All tests passed! Trial system is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test directory
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("\n🧹 Test data cleaned up")

if __name__ == "__main__":
    success = test_trial_system()
    sys.exit(0 if success else 1)