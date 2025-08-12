import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, Crown, Calendar } from 'lucide-react';

interface TrialStatus {
  is_valid: boolean;
  days_remaining: number;
  trial_end_date: string;
  current_date: string;
  status: 'active' | 'expired';
  message: string;
}

interface SimpleTrialStatusProps {
  onUpgradeClick?: () => void;
  compact?: boolean;
}

const SimpleTrialStatus: React.FC<SimpleTrialStatusProps> = ({ 
  onUpgradeClick, 
  compact = false 
}) => {
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrialStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/license/status');
        const data = await response.json();
        setTrialStatus(data);
      } catch (error) {
        console.error('Failed to fetch trial status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrialStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchTrialStatus, 30000);
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

  if (!trialStatus) {
    return null;
  }

  const isExpired = trialStatus.status === 'expired';
  const daysRemaining = trialStatus.days_remaining;

  const getStatusColor = () => {
    if (isExpired) return 'text-red-600';
    if (daysRemaining <= 7) return 'text-amber-600';
    return 'text-green-600';
  };

  const getStatusIcon = () => {
    if (isExpired) return AlertTriangle;
    return Clock;
  };

  const StatusIcon = getStatusIcon();
  const statusColor = getStatusColor();

  if (compact) {
    return (
      <div 
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors
          ${isExpired 
            ? 'bg-red-50 border-red-200 hover:bg-red-100' 
            : daysRemaining <= 7 
              ? 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
              : 'bg-green-50 border-green-200 hover:bg-green-100'
          }`}
        onClick={onUpgradeClick}
      >
        <StatusIcon className={`w-4 h-4 ${statusColor.replace('text-', 'text-').replace('-600', '-500')}`} />
        <span className={`text-sm font-medium ${statusColor}`}>
          {trialStatus.message}
        </span>
        {!isExpired && <Crown className="w-4 h-4 text-amber-500" />}
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusIcon className={`w-5 h-5 ${statusColor.replace('text-', 'text-').replace('-600', '-500')}`} />
          <h3 className="font-semibold text-gray-900">
            {isExpired ? 'Trial Expired' : 'Trial Active'}
          </h3>
        </div>
      </div>

      <div className={`text-sm font-medium mb-3 ${statusColor}`}>
        {trialStatus.message}
      </div>

      {!isExpired && (
        <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-lg p-3 mb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">
                Trial ends October 1st, 2025
              </span>
            </div>
          </div>
          <div className="text-xs text-blue-700 mt-1">
            Full access to all features until then!
          </div>
        </div>
      )}

      {isExpired && (
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-3 mb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-sm font-medium text-red-800">
              Your trial has ended
            </span>
          </div>
          <div className="text-xs text-red-700 mt-1">
            Contact support to continue using Memoire
          </div>
        </div>
      )}

      {/* Features Available */}
      <div className="grid grid-cols-2 gap-2 text-xs mb-4">
        <div className={`flex items-center gap-1 ${isExpired ? 'text-gray-400' : 'text-green-600'}`}>
          <Crown className="w-3 h-3" />
          Unlimited clients
        </div>
        <div className={`flex items-center gap-1 ${isExpired ? 'text-gray-400' : 'text-green-600'}`}>
          <Crown className="w-3 h-3" />
          Unlimited documents
        </div>
        <div className={`flex items-center gap-1 ${isExpired ? 'text-gray-400' : 'text-green-600'}`}>
          <Crown className="w-3 h-3" />
          Unlimited queries
        </div>
        <div className={`flex items-center gap-1 ${isExpired ? 'text-gray-400' : 'text-green-600'}`}>
          <Crown className="w-3 h-3" />
          Full chat history
        </div>
      </div>

      {/* Contact Button */}
      <button
        onClick={onUpgradeClick}
        className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
          ${isExpired 
            ? 'bg-red-600 hover:bg-red-700 text-white' 
            : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
          }`}
      >
        <Crown className="w-4 h-4" />
        {isExpired ? 'Contact Support' : 'Upgrade Options'}
      </button>
    </div>
  );
};

export default SimpleTrialStatus;