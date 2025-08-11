import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, Crown, Users, FileText, MessageCircle, X, Key, Heart, Zap } from 'lucide-react';
import { licenseService, LicenseStatus } from '../lib/licenseApi';

interface TrialStatusProps {
  onUpgradeClick: () => void;
  compact?: boolean;
}

const TrialStatus: React.FC<TrialStatusProps> = ({ onUpgradeClick, compact = false }) => {
  const [licenseStatus, setLicenseStatus] = useState<LicenseStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(!compact);

  useEffect(() => {
    const fetchLicenseStatus = async () => {
      try {
        const status = await licenseService.getLicenseStatus();
        setLicenseStatus(status);
      } catch (error) {
        console.error('Failed to fetch license status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLicenseStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchLicenseStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-24"></div>
      </div>
    );
  }

  if (!licenseStatus || licenseStatus.license_type === 'pro') {
    return null; // Don't show for pro users
  }

  const daysRemaining = licenseStatus.days_remaining;
  const daysUsed = licenseStatus.days_used || 0;
  const isExpired = !licenseStatus.is_valid;
  const engagementScore = licenseStatus.engagement_score || 0;
  const hasData = licenseStatus.conversion_indicators?.has_uploaded_documents || false;
  
  const getTrialMessage = () => {
    if (isExpired) {
      return hasData 
        ? "Trial expired - Your data is waiting!" 
        : "Trial expired - Reactivate to continue";
    }
    
    if (daysRemaining <= 3 && hasData) {
      return `${daysRemaining} days left - Don't lose your progress!`;
    }
    
    if (daysRemaining <= 7) {
      return `${daysRemaining} days remaining in trial`;
    }
    
    return `${daysRemaining} days of unlimited access`;
  };
  
  const statusColor = isExpired ? 'text-red-600' : daysRemaining <= 7 ? 'text-amber-600' : 'text-blue-600';

  if (compact) {
    return (
      <div 
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors
          ${isExpired 
            ? 'bg-red-50 border-red-200 hover:bg-red-100' 
            : daysRemaining <= 7 
              ? 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
              : 'bg-blue-50 border-blue-200 hover:bg-blue-100'
          }`}
        onClick={() => setShowDetails(!showDetails)}
      >
        {isExpired ? (
          <AlertTriangle className="w-4 h-4 text-red-500" />
        ) : (
          <Clock className="w-4 h-4 text-blue-500" />
        )}
        <span className={`text-sm font-medium ${statusColor}`}>
          {getTrialMessage()}
        </span>
        <Crown className="w-4 h-4 text-amber-500" />
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isExpired ? (
            <AlertTriangle className="w-5 h-5 text-red-500" />
          ) : (
            <Clock className="w-5 h-5 text-blue-500" />
          )}
          <h3 className="font-semibold text-gray-900">
            {isExpired ? 'Trial Expired' : 'Trial Version'}
          </h3>
        </div>
        {!compact && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-gray-400 hover:text-gray-600"
          >
            {showDetails ? <X className="w-4 h-4" /> : <Key className="w-4 h-4" />}
          </button>
        )}
      </div>

      <div className={`text-sm font-medium mb-3 ${statusColor}`}>
        {getTrialMessage()}
      </div>

      {showDetails && (
        <div className="space-y-4">
          {/* Engagement Progress */}
          {!isExpired && (
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Heart className="w-4 h-4 text-purple-500" />
                <span className="text-sm font-medium text-gray-700">Your Progress</span>
              </div>
              <div className="text-xs text-gray-600 mb-2">
                {daysUsed} days exploring • {licenseStatus.usage_stats.clients_created} clients • {licenseStatus.usage_stats.documents_uploaded} documents • {licenseStatus.usage_stats.total_queries} queries
              </div>
              {hasData && (
                <div className="text-xs text-purple-600 font-medium">
                  ✨ You're building valuable session insights!
                </div>
              )}
            </div>
          )}
          
          {/* Features Available */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-1 text-green-600">
              <Zap className="w-3 h-3" />
              Unlimited clients
            </div>
            <div className="flex items-center gap-1 text-green-600">
              <Zap className="w-3 h-3" />
              Unlimited documents
            </div>
            <div className="flex items-center gap-1 text-green-600">
              <Zap className="w-3 h-3" />
              Unlimited queries
            </div>
            <div className="flex items-center gap-1 text-green-600">
              <Zap className="w-3 h-3" />
              Full chat history
            </div>
          </div>

          {/* Upgrade Button */}
          <button
            onClick={onUpgradeClick}
            className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
              ${isExpired 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : daysRemaining <= 7
                  ? 'bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
              }`}
          >
            <Crown className="w-4 h-4" />
            {isExpired 
              ? (hasData ? 'Unlock Your Data' : 'Reactivate Account')
              : daysRemaining <= 7 
                ? 'Secure Your Access'
                : 'Get Pro License'
            }
          </button>
        </div>
      )}
    </div>
  );
};

interface UsageBarProps {
  icon: React.ComponentType<any>;
  label: string;
  used: number;
  max: number;
  color: 'blue' | 'green' | 'purple';
}

const UsageBar: React.FC<UsageBarProps> = ({ icon: Icon, label, used, max, color }) => {
  const percentage = licenseService.getUsagePercentage(used, max);
  const isLimited = licenseService.isFeatureLimited(used, max);
  const formattedUsage = licenseService.formatUsageLimit(used, max);

  const colorClasses = {
    blue: {
      bar: isLimited ? 'bg-red-500' : 'bg-blue-500',
      bg: 'bg-blue-100',
      text: isLimited ? 'text-red-600' : 'text-blue-600'
    },
    green: {
      bar: isLimited ? 'bg-red-500' : 'bg-green-500',
      bg: 'bg-green-100',
      text: isLimited ? 'text-red-600' : 'text-green-600'
    },
    purple: {
      bar: isLimited ? 'bg-red-500' : 'bg-purple-500',
      bg: 'bg-purple-100',
      text: isLimited ? 'text-red-600' : 'text-purple-600'
    }
  };

  return (
    <div className="flex items-center gap-3">
      <Icon className={`w-4 h-4 ${colorClasses[color].text}`} />
      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs font-medium text-gray-700">{label}</span>
          <span className={`text-xs font-medium ${colorClasses[color].text}`}>
            {formattedUsage}
          </span>
        </div>
        {max !== -1 && (
          <div className={`h-2 rounded-full ${colorClasses[color].bg}`}>
            <div
              className={`h-2 rounded-full transition-all duration-300 ${colorClasses[color].bar}`}
              style={{ width: `${Math.min(100, percentage)}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TrialStatus;