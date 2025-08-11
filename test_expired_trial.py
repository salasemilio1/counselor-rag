#!/usr/bin/env python3
"""
Test expired trial scenario by manipulating license dates
"""

import json
import os
from datetime import datetime, timedelta
import requests
from cryptography.fernet import Fernet
import hashlib
import platform
import uuid
import base64

BASE_URL = "http://localhost:8000"
LICENSE_PATH = "/Users/emiliosalas/Desktop/rag-system/counselor-rag/data/.memoire-license"

def generate_machine_fingerprint():
    """Generate the same fingerprint as the license manager"""
    try:
        # Collect machine characteristics (same as LicenseManager)
        machine_data = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': platform.node()[:8],  # First 8 chars only for privacy
        }
        
        # Add MAC address if available (anonymized)
        try:
            mac = hex(uuid.getnode())[2:]
            machine_data['mac_hash'] = hashlib.sha256(mac.encode()).hexdigest()[:16]
        except:
            machine_data['mac_hash'] = 'unknown'
        
        # Create fingerprint
        fingerprint_str = json.dumps(machine_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]
    
    except Exception as e:
        print(f"Could not generate machine fingerprint: {e}")
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]

def generate_encryption_key():
    """Generate encryption key from machine fingerprint"""
    fingerprint = generate_machine_fingerprint()
    # Use fingerprint to create Fernet key
    key_material = hashlib.sha256(fingerprint.encode()).digest()
    return base64.urlsafe_b64encode(key_material)

def create_expired_license():
    """Create an expired license for testing"""
    # Generate dates that simulate an expired trial
    trial_start = datetime.now() - timedelta(days=35)  # Started 35 days ago
    anonymous_trial_end = trial_start + timedelta(days=7)  # Ended 28 days ago
    extended_trial_end = trial_start + timedelta(days=30)  # Ended 5 days ago
    
    license_data = {
        'license_type': 'extended_trial',
        'trial_phase': 'extended',
        'machine_fingerprint': generate_machine_fingerprint(),
        'trial_start': trial_start.isoformat(),
        'anonymous_trial_end': anonymous_trial_end.isoformat(),
        'extended_trial_end': extended_trial_end.isoformat(),
        'trial_activated': True,
        'user_account': {
            'email': 'expired@example.com',
            'name': 'Expired User',
            'created_at': (trial_start + timedelta(days=3)).isoformat(),
            'machine_fingerprint': generate_machine_fingerprint()
        },
        'account_created_at': (trial_start + timedelta(days=3)).isoformat(),
        'usage_stats': {
            'clients_created': 3,
            'documents_uploaded': 10,
            'queries_made_today': 0,
            'last_query_date': None,
            'total_queries': 25,
            'sessions_created': 8,
            'total_usage_time': 0,
            'phase_1_engagement': 15,
            'phase_2_engagement': 35
        },
        'features': {
            'max_clients': -1,
            'max_documents': -1,
            'max_queries_per_day': -1,
            'chat_history_days': 180,
            'export_enabled': True,
            'advanced_features': True
        }
    }
    
    return license_data

def save_expired_license(license_data):
    """Save the expired license using the same encryption as LicenseManager"""
    try:
        # Generate encryption key
        encryption_key = generate_encryption_key()
        cipher = Fernet(encryption_key)
        
        # Encrypt data
        json_data = json.dumps(license_data, indent=2)
        encrypted_data = cipher.encrypt(json_data.encode())
        
        # Write to file
        with open(LICENSE_PATH, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"✅ Created expired license file")
        return True
        
    except Exception as e:
        print(f"❌ Error creating expired license: {e}")
        return False

def test_expired_functionality():
    """Test that functionality is properly restricted when trial is expired"""
    print("\n🧪 TESTING EXPIRED TRIAL RESTRICTIONS")
    
    # Test license status
    try:
        response = requests.get(f"{BASE_URL}/license/status")
        status = response.json()
        print(f"📊 License Status:")
        print(f"   Phase: {status.get('trial_phase', 'N/A')}")
        print(f"   Valid: {status.get('is_valid', 'N/A')}")
        print(f"   Days Remaining: {status.get('days_remaining', 'N/A')}")
        print(f"   Message: {status.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ Error checking license status: {e}")
    
    # Test clients access
    try:
        response = requests.get(f"{BASE_URL}/clients")
        clients_data = response.json()
        print(f"📂 Clients access: {clients_data}")
    except Exception as e:
        print(f"❌ Error checking clients: {e}")
    
    # Test query functionality
    try:
        query_data = {"client_id": "eli", "query": "Test query"}
        response = requests.post(f"{BASE_URL}/query", json=query_data)
        query_result = response.json()
        print(f"🔍 Query result: {query_result.get('answer', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Error testing query: {e}")
    
    # Test license activation (should still work)
    try:
        activation_data = {"license_key": "test-pro-license-key-12345"}
        response = requests.post(f"{BASE_URL}/license/activate", json=activation_data)
        activation_result = response.json()
        print(f"🔑 License activation available: {activation_result.get('status', 'N/A')}")
    except Exception as e:
        print(f"❌ Error testing license activation: {e}")

def main():
    """Test expired trial scenario"""
    print("🧪 TESTING EXPIRED TRIAL SCENARIO")
    print("="*50)
    
    # Backup existing license if it exists
    backup_path = LICENSE_PATH + ".backup"
    if os.path.exists(LICENSE_PATH):
        os.rename(LICENSE_PATH, backup_path)
        print(f"📋 Backed up existing license to {backup_path}")
    
    try:
        # Create and save expired license
        expired_license = create_expired_license()
        if save_expired_license(expired_license):
            print(f"📅 Created expired trial:")
            print(f"   Started: {expired_license['trial_start']}")
            print(f"   Anonymous ended: {expired_license['anonymous_trial_end']}")
            print(f"   Extended ended: {expired_license['extended_trial_end']}")
            print(f"   Account: {expired_license['user_account']['email']}")
            
            # Test functionality with expired license
            test_expired_functionality()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore backup if it exists
        if os.path.exists(backup_path):
            if os.path.exists(LICENSE_PATH):
                os.remove(LICENSE_PATH)
            os.rename(backup_path, LICENSE_PATH)
            print(f"🔄 Restored original license")
        
        print("\n" + "="*50)
        print("✅ EXPIRED TRIAL TEST COMPLETED")

if __name__ == "__main__":
    main()