#!/usr/bin/env python3
"""
Test script for the simple license system
"""

import sys
import os
from datetime import date

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from simple_license import SimpleLicenseManager

def test_simple_license():
    print("🧪 Testing Simple October 1st License System")
    print("=" * 50)
    
    # Create license manager
    license_manager = SimpleLicenseManager()
    
    print("1. Testing Current Trial Status...")
    status = license_manager.get_trial_status()
    print(f"   Is Valid: {status['is_valid']}")
    print(f"   Days Remaining: {status['days_remaining']}")
    print(f"   Status: {status['status']}")
    print(f"   Message: {license_manager.get_trial_message()}")
    
    print("\n2. Testing Feature Access...")
    can_use, message = license_manager.can_use_feature()
    print(f"   Can use features: {can_use}")
    if message:
        print(f"   Message: {message}")
    
    print("\n3. Testing Date Logic...")
    print(f"   Trial ends: {license_manager.TRIAL_END_DATE}")
    print(f"   Today: {date.today()}")
    
    print("\n✅ Simple license system test completed!")
    return True

if __name__ == "__main__":
    test_simple_license()