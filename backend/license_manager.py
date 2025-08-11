import json
import hashlib
import platform
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class LicenseManager:
    """
    Manages trial periods, license validation, and feature restrictions.
    Designed to be tamper-resistant while maintaining user privacy.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.license_file = data_dir / ".memoire-license"
        self.config_file = data_dir / ".memoire-config" 
        
        # Generate encryption key from machine characteristics
        self.encryption_key = self._generate_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Trial settings
        self.TRIAL_DAYS = 30
        # No limits during trial - let them fall in love with the product!
        
        # Initialize license data
        self._init_license_data()
    
    def _generate_machine_fingerprint(self) -> str:
        """Generate a unique fingerprint for this machine"""
        try:
            # Collect machine characteristics
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
            logger.warning(f"Could not generate machine fingerprint: {e}")
            return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key from machine fingerprint"""
        fingerprint = self._generate_machine_fingerprint()
        # Use fingerprint to create Fernet key
        key_material = hashlib.sha256(fingerprint.encode()).digest()
        return base64.urlsafe_b64encode(key_material)
    
    def _init_license_data(self):
        """Initialize license data if not exists"""
        if not self.license_file.exists():
            self._create_trial_license()
        
        # Load existing license
        self.license_data = self._load_license_data()
    
    def _create_trial_license(self):
        """Create new trial license"""
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=self.TRIAL_DAYS)
        
        license_data = {
            'license_type': 'trial',
            'machine_fingerprint': self._generate_machine_fingerprint(),
            'trial_start': trial_start.isoformat(),
            'trial_end': trial_end.isoformat(),
            'trial_activated': True,
            'usage_stats': {
                'clients_created': 0,
                'documents_uploaded': 0,
                'queries_made_today': 0,
                'last_query_date': None,
                'total_queries': 0,
                'sessions_created': 0,
                'total_usage_time': 0
            },
            'features': {
                'max_clients': -1,  # Unlimited during trial
                'max_documents': -1,  # Unlimited during trial
                'max_queries_per_day': -1,  # Unlimited during trial
                'chat_history_days': 180,  # Full features during trial
                'export_enabled': True,  # Full features during trial
                'advanced_features': True  # Full features during trial
            }
        }
        
        self._save_license_data(license_data)
        logger.info(f"Created trial license valid until {trial_end.strftime('%Y-%m-%d')}")
    
    def _load_license_data(self) -> Dict[str, Any]:
        """Load and decrypt license data"""
        try:
            if not self.license_file.exists():
                return {}
            
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        
        except Exception as e:
            logger.error(f"Error loading license data: {e}")
            # If license is corrupted, create new trial
            self._create_trial_license()
            return self._load_license_data()
    
    def _save_license_data(self, data: Dict[str, Any]):
        """Encrypt and save license data"""
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Encrypt data
            json_data = json.dumps(data, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Write to file
            with open(self.license_file, 'wb') as f:
                f.write(encrypted_data)
            
            self.license_data = data
            
        except Exception as e:
            logger.error(f"Error saving license data: {e}")
            raise
    
    def is_trial_valid(self) -> bool:
        """Check if trial period is still valid"""
        if not self.license_data:
            return False
        
        if self.license_data.get('license_type') != 'trial':
            return True  # Pro license
        
        try:
            trial_end = datetime.fromisoformat(self.license_data['trial_end'])
            return datetime.now() < trial_end
        except:
            return False
    
    def get_trial_days_remaining(self) -> int:
        """Get number of days remaining in trial"""
        if self.license_data.get('license_type') != 'trial':
            return -1  # Pro license
        
        try:
            trial_end = datetime.fromisoformat(self.license_data['trial_end'])
            remaining = (trial_end - datetime.now()).days
            return max(0, remaining)
        except:
            return 0
    
    def can_create_client(self) -> tuple[bool, str]:
        """Check if user can create a new client"""
        if not self.is_trial_valid():
            return False, "🚫 Your 30-day trial has expired. All features are now locked. Please purchase a license to continue using Memoire and access all your valuable session data."
        
        # During trial or with pro license - everything is allowed
        return True, ""
    
    def can_upload_document(self) -> tuple[bool, str]:
        """Check if user can upload a document"""
        if not self.is_trial_valid():
            return False, "🚫 Your 30-day trial has expired. All features are now locked. Please purchase a license to continue using Memoire and access all your valuable session data."
        
        # During trial or with pro license - everything is allowed
        return True, ""
    
    def can_make_query(self) -> tuple[bool, str]:
        """Check if user can make a query"""
        if not self.is_trial_valid():
            return False, "🚫 Your 30-day trial has expired. All features are now locked. Please purchase a license to continue using Memoire and access all your valuable session data."
        
        # During trial or with pro license - everything is allowed
        return True, ""
    
    def _reset_daily_query_count_if_needed(self):
        """Reset daily query count if it's a new day"""
        today = datetime.now().date().isoformat()
        last_query_date = self.license_data['usage_stats'].get('last_query_date')
        
        if last_query_date != today:
            self.license_data['usage_stats']['queries_made_today'] = 0
            self.license_data['usage_stats']['last_query_date'] = today
            self._save_license_data(self.license_data)
    
    def record_client_creation(self):
        """Record that a client was created - pure engagement tracking"""
        self.license_data['usage_stats']['clients_created'] += 1
        self._save_license_data(self.license_data)
    
    def record_document_upload(self):
        """Record that a document was uploaded - pure engagement tracking"""
        self.license_data['usage_stats']['documents_uploaded'] += 1
        self._save_license_data(self.license_data)
    
    def record_query(self):
        """Record that a query was made - pure engagement tracking"""
        self._reset_daily_query_count_if_needed()
        self.license_data['usage_stats']['queries_made_today'] += 1
        self.license_data['usage_stats']['total_queries'] += 1
        self._save_license_data(self.license_data)
    
    def record_session_start(self):
        """Record a new session started"""
        self.license_data['usage_stats']['sessions_created'] += 1
        self._save_license_data(self.license_data)
    
    def get_engagement_score(self) -> float:
        """Calculate engagement score for conversion prediction"""
        stats = self.license_data['usage_stats']
        
        # Weight different activities for engagement scoring
        engagement = (
            stats.get('clients_created', 0) * 10 +      # High weight - shows real usage
            stats.get('documents_uploaded', 0) * 5 +    # High weight - data investment
            stats.get('total_queries', 0) * 1 +         # Regular usage
            stats.get('sessions_created', 0) * 2        # Regular return visits
        )
        
        return min(100.0, engagement / 10.0)  # Scale to 0-100
    
    def get_license_status(self) -> Dict[str, Any]:
        """Get comprehensive license status"""
        engagement_score = self.get_engagement_score()
        trial_start = datetime.fromisoformat(self.license_data.get('trial_start', datetime.now().isoformat()))
        days_used = (datetime.now() - trial_start).days
        
        return {
            'license_type': self.license_data.get('license_type', 'trial'),
            'is_valid': self.is_trial_valid(),
            'days_remaining': self.get_trial_days_remaining(),
            'days_used': days_used,
            'trial_start': self.license_data.get('trial_start'),
            'trial_end': self.license_data.get('trial_end'),
            'engagement_score': engagement_score,
            'usage_stats': self.license_data.get('usage_stats', {}),
            'features': {
                'unlimited_clients': True,
                'unlimited_documents': True,  
                'unlimited_queries': True,
                'full_chat_history': True,
                'export_enabled': True,
                'advanced_features': True
            },
            'conversion_indicators': {
                'has_uploaded_documents': self.license_data['usage_stats']['documents_uploaded'] > 0,
                'has_multiple_clients': self.license_data['usage_stats']['clients_created'] > 1,
                'high_query_usage': self.license_data['usage_stats']['total_queries'] > 20,
                'regular_user': self.license_data['usage_stats']['sessions_created'] > 5,
                'investment_level': 'high' if engagement_score > 70 else 'medium' if engagement_score > 30 else 'low'
            }
        }
    
    def activate_pro_license(self, license_key: str) -> tuple[bool, str]:
        """Activate a pro license (placeholder for future implementation)"""
        # TODO: Implement license key validation with server
        # For now, just simulate activation
        
        if len(license_key) < 10:
            return False, "Invalid license key format"
        
        # Update license to pro
        self.license_data.update({
            'license_type': 'pro',
            'license_key': license_key,
            'activated_at': datetime.now().isoformat(),
            'features': {
                'max_clients': -1,  # Unlimited
                'max_documents': -1,  # Unlimited
                'max_queries_per_day': -1,  # Unlimited
                'chat_history_days': 180,  # 6 months
                'export_enabled': True,
                'advanced_features': True
            }
        })
        
        self._save_license_data(self.license_data)
        return True, "Pro license activated successfully!"