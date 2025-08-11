import api from './api';

export interface LicenseStatus {
  license_type: 'trial' | 'pro';
  is_valid: boolean;
  days_remaining: number;
  trial_end: string;
  features: {
    max_clients: number;
    max_documents: number;
    max_queries_per_day: number;
    chat_history_days: number;
    export_enabled: boolean;
    advanced_features: boolean;
  };
  usage_stats: {
    clients_created: number;
    documents_uploaded: number;
    queries_made_today: number;
    total_queries: number;
  };
  limits: {
    clients: {
      max: number;
      used: number;
    };
    documents: {
      max: number;
      used: number;
    };
    queries_today: {
      max: number;
      used: number;
    };
  };
}

export interface TrialInfo {
  is_trial: boolean;
  days_remaining: number;
  trial_valid: boolean;
  trial_end: string;
}

export interface LicenseActivationResponse {
  status: 'success' | 'error';
  message: string;
}

class LicenseService {
  async getLicenseStatus(): Promise<LicenseStatus> {
    const response = await api.get('/license/status');
    return response.data;
  }

  async getTrialInfo(): Promise<TrialInfo> {
    const response = await api.get('/license/trial-info');
    return response.data;
  }

  async activateLicense(licenseKey: string): Promise<LicenseActivationResponse> {
    const response = await api.post('/license/activate', {
      license_key: licenseKey
    });
    return response.data;
  }

  // Helper methods for UI logic
  getTrialStatusColor(daysRemaining: number): string {
    if (daysRemaining <= 3) return 'text-red-500';
    if (daysRemaining <= 7) return 'text-yellow-500';
    return 'text-green-500';
  }

  getTrialStatusMessage(daysRemaining: number, isValid: boolean): string {
    if (!isValid) {
      return 'Trial expired - Upgrade to continue';
    }
    if (daysRemaining <= 0) {
      return 'Trial expires today';
    }
    if (daysRemaining === 1) {
      return '1 day remaining';
    }
    return `${daysRemaining} days remaining`;
  }

  formatUsageLimit(used: number, max: number): string {
    if (max === -1) return `${used} (Unlimited)`;
    return `${used}/${max}`;
  }

  getUsagePercentage(used: number, max: number): number {
    if (max === -1) return 0;
    return Math.min(100, (used / max) * 100);
  }

  isFeatureLimited(used: number, max: number): boolean {
    if (max === -1) return false;
    return used >= max;
  }
}

export const licenseService = new LicenseService();