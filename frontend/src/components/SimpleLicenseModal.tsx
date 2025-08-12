import React from 'react';
import { X, Crown, AlertCircle, ExternalLink, Mail } from 'lucide-react';

interface SimpleLicenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  isTrialExpired?: boolean;
}

const SimpleLicenseModal: React.FC<SimpleLicenseModalProps> = ({ 
  isOpen, 
  onClose, 
  isTrialExpired = false 
}) => {
  if (!isOpen) return null;

  const handleContactSupport = () => {
    // Open email client
    const email = 'emilio.salas.data@gmail.com';
    const subject = isTrialExpired 
      ? 'Trial Expired - Continue Using Memoire'
      : 'Memoire License Information';
    const body = isTrialExpired
      ? 'Hi,\n\nMy Memoire trial has expired and I would like to continue using the application. Please let me know how to proceed.\n\nThank you!'
      : 'Hi,\n\nI would like to learn more about Memoire licensing options.\n\nThank you!';
    
    window.open(`mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Crown className="w-6 h-6 text-amber-500" />
            <h2 className="text-xl font-bold text-gray-900">
              {isTrialExpired ? 'Trial Has Ended' : 'Memoire License'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Trial Expired Message */}
          {isTrialExpired && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-800 mb-1">
                    Your Trial Period Has Ended
                  </h4>
                  <p className="text-sm text-red-700">
                    Your trial expired on October 1st, 2025. All features are now locked until you obtain a license.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* What You Get */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">
              {isTrialExpired ? 'Restore Full Access' : 'Memoire Features'}
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Crown className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Unlimited clients and session notes</span>
              </div>
              <div className="flex items-center gap-3">
                <Crown className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Unlimited document uploads and queries</span>
              </div>
              <div className="flex items-center gap-3">
                <Crown className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Complete chat history and insights</span>
              </div>
              <div className="flex items-center gap-3">
                <Crown className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">SOAP note templates and analysis</span>
              </div>
              <div className="flex items-center gap-3">
                <Crown className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Data export capabilities</span>
              </div>
              <div className="flex items-center gap-3">
                <Crown className="w-4 h-4 text-green-600 flex-shrink-0" />
                <span className="text-gray-700">Personal support and updates</span>
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4">
            <div className="text-center">
              <Mail className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <h4 className="font-semibold text-gray-900 mb-2">
                {isTrialExpired ? 'Continue Using Memoire' : 'Get Your License'}
              </h4>
              <p className="text-sm text-gray-600 mb-4">
                Contact us directly for licensing information and pricing options.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {isTrialExpired ? 'Close' : 'Maybe Later'}
            </button>
            <button
              onClick={handleContactSupport}
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 py-3 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2"
            >
              <Mail className="w-4 h-4" />
              Contact Support
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>

          {/* Contact Details */}
          <div className="text-center text-xs text-gray-500 border-t pt-4">
            <p>Support: emilio.salas.data@gmail.com</p>
            <p className="mt-1">Response within 24 hours</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleLicenseModal;