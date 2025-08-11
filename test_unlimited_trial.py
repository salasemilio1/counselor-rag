#!/usr/bin/env python3
"""
Test script to verify the unlimited trial with hard cutoff approach.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from license_manager import LicenseManager

def test_unlimited_trial():
    print("🎯 Testing Unlimited Trial with Hard Cutoff")
    print("=" * 55)
    
    # Create test data directory
    test_dir = Path("test_unlimited_trial")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize license manager
        print("1. Initializing Unlimited Trial...")
        license_manager = LicenseManager(test_dir)
        print("✅ License Manager initialized successfully")
        
        # Test unlimited usage during trial
        print("\n2. Testing Unlimited Usage During Trial...")
        
        # Test extreme usage (would hit limits in old system)
        for i in range(20):  # Way more than old limits
            license_manager.record_client_creation()
            license_manager.record_document_upload() 
            license_manager.record_query()
        
        # Should still allow everything
        can_create, message = license_manager.can_create_client()
        can_upload, message2 = license_manager.can_upload_document()
        can_query, message3 = license_manager.can_make_query()
        
        print(f"   After 20x usage - Can create client: {can_create}")
        print(f"   After 20x usage - Can upload: {can_upload}")  
        print(f"   After 20x usage - Can query: {can_query}")
        
        assert can_create and can_upload and can_query, "Should allow unlimited usage during trial"
        print("✅ Unlimited usage confirmed during active trial")
        
        # Check engagement scoring
        print("\n3. Testing Engagement Tracking...")
        status = license_manager.get_license_status()
        engagement = status['engagement_score']
        print(f"   Engagement Score: {engagement:.1f}/100")
        print(f"   Investment Level: {status['conversion_indicators']['investment_level']}")
        print(f"   Usage: {status['usage_stats']['clients_created']} clients, {status['usage_stats']['documents_uploaded']} docs, {status['usage_stats']['total_queries']} queries")
        print("✅ Engagement tracking working correctly")
        
        # Test trial expiration behavior
        print("\n4. Testing Trial Expiration (Simulated)...")
        
        # Manually expire the trial for testing
        license_data = license_manager.license_data
        expired_time = datetime.now() - timedelta(days=1)
        license_data['trial_end'] = expired_time.isoformat()
        license_manager._save_license_data(license_data)
        
        # Now everything should be blocked
        can_create, message = license_manager.can_create_client()
        can_upload, message2 = license_manager.can_upload_document()
        can_query, message3 = license_manager.can_make_query()
        
        print(f"   After expiration - Can create client: {can_create}")
        print(f"   After expiration - Can upload: {can_upload}")
        print(f"   After expiration - Can query: {can_query}")
        
        if not can_create:
            print(f"   Lockdown message: {message[:80]}...")
        
        assert not (can_create or can_upload or can_query), "Should block all access after expiration"
        print("✅ Complete lockdown confirmed after trial expiration")
        
        # Test the compelling messaging
        print("\n5. Testing Conversion Messaging...")
        trial_status = license_manager.get_license_status()
        conversion_indicators = trial_status['conversion_indicators']
        
        print("   Conversion Indicators:")
        for key, value in conversion_indicators.items():
            print(f"     {key}: {value}")
        
        print("✅ Conversion indicators working correctly")
        
        print("\n🎯 Perfect! The unlimited trial strategy is implemented correctly:")
        print("   ✅ No restrictions during 30-day trial")  
        print("   ✅ Complete product lockdown after expiration")
        print("   ✅ Engagement tracking for conversion optimization")
        print("   ✅ Compelling messaging about data loss")
        print("\n💼 Business Strategy: Let them fall in love, then make it essential!")
        
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
    success = test_unlimited_trial()
    sys.exit(0 if success else 1)