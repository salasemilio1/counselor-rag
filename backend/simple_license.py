"""
Simple License Manager - Trial expires October 1st, 2025
"""

from datetime import datetime, date
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleLicenseManager:
    """
    Simple license manager that checks if trial has expired.
    Trial ends on October 1st, 2025.
    """
    
    def __init__(self):
        # Set trial end date - October 1st, 2025
        self.TRIAL_END_DATE = date(2025, 10, 1)
        
    def is_trial_valid(self) -> bool:
        """Check if trial is still valid (before October 1st, 2025)"""
        today = date.today()
        return today < self.TRIAL_END_DATE
    
    def get_days_remaining(self) -> int:
        """Get number of days remaining in trial"""
        today = date.today()
        if today >= self.TRIAL_END_DATE:
            return 0
        
        delta = self.TRIAL_END_DATE - today
        return delta.days
    
    def get_trial_status(self) -> Dict[str, Any]:
        """Get comprehensive trial status"""
        today = date.today()
        days_remaining = self.get_days_remaining()
        is_valid = self.is_trial_valid()
        
        return {
            'is_valid': is_valid,
            'days_remaining': days_remaining,
            'trial_end_date': self.TRIAL_END_DATE.isoformat(),
            'current_date': today.isoformat(),
            'status': 'active' if is_valid else 'expired'
        }
    
    def can_use_feature(self) -> tuple[bool, str]:
        """Check if user can use features (generic check for all features)"""
        if not self.is_trial_valid():
            return False, "Your trial period has ended. Please contact support to continue using Memoire."
        
        return True, ""
    
    def get_trial_message(self) -> str:
        """Get appropriate message for current trial status"""
        days_remaining = self.get_days_remaining()
        
        if days_remaining <= 0:
            return "Trial expired - Contact support to continue"
        elif days_remaining == 1:
            return "1 day remaining in trial"
        elif days_remaining <= 7:
            return f"{days_remaining} days remaining - Trial ends October 1st"
        else:
            return f"{days_remaining} days of unlimited access remaining"