import React, { useState } from 'react';
import { X, Key, Crown, Check, AlertCircle, ExternalLink } from 'lucide-react';
import { licenseService } from '../lib/licenseApi';

interface LicenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  isTrialExpired?: boolean;
}

const LicenseModal: React.FC<LicenseModalProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  isTrialExpired = false 
}) => {
  const [activeTab, setActiveTab] = useState<'upgrade' | 'activate'>('upgrade');
  const [licenseKey, setLicenseKey] = useState('');
  const [activating, setActivating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleActivate = async () => {
    if (!licenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setActivating(true);
    setError('');

    try {
      const result = await licenseService.activateLicense(licenseKey);
      if (result.status === 'success') {
        setSuccess(true);
        setTimeout(() => {
          onSuccess();
          onClose();
          setSuccess(false);
          setLicenseKey('');
        }, 2000);
      } else {
        setError(result.message);
      }
    } catch (error: any) {
      setError(error.response?.data?.message || 'Failed to activate license');
    } finally {
      setActivating(false);
    }
  };

  const handleClose = () => {
    if (!activating) {
      setError('');
      setLicenseKey('');
      setSuccess(false);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Crown className="w-6 h-6 text-amber-500" />
            <h2 className="text-xl font-bold text-gray-900">
              {isTrialExpired ? 'Your Trial Has Ended - Unlock Your Data' : 'Upgrade to Memoire Pro'}
            </h2>
          </div>
          <button
            onClick={handleClose}
            disabled={activating}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {success ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              License Activated Successfully!
            </h3>
            <p className="text-gray-600">
              Welcome to Memoire Pro. Enjoy unlimited access to all features.
            </p>
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div className="border-b">
              <nav className="flex">
                <button
                  onClick={() => setActiveTab('upgrade')}
                  className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                    activeTab === 'upgrade'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Purchase License
                </button>
                <button
                  onClick={() => setActiveTab('activate')}
                  className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                    activeTab === 'activate'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Activate License
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'upgrade' ? (
                <div className="space-y-6">
                  {/* Trial Expired Message */}
                  {isTrialExpired && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-red-800 mb-1">
                            Don't Lose Your Valuable Session Data
                          </h4>
                          <p className="text-sm text-red-700">
                            You've built up valuable client insights and session notes during your trial. 
                            All your data is safely stored and waiting for you - just activate your license to continue accessing everything.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Pro Features */}
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-4">
                      {isTrialExpired ? 'Reactivate Full Access' : 'Memoire Pro Features'}
                    </h3>
                    <div className="space-y-3">
                      {[
                        isTrialExpired ? 'Access to all your existing client data' : 'Unlimited clients and documents',
                        isTrialExpired ? 'Continue where you left off' : 'Unlimited daily queries', 
                        isTrialExpired ? 'Restore your chat history and insights' : 'Extended chat history (6 months)',
                        'Advanced SOAP note templates',
                        'Data export capabilities',
                        'Priority email support',
                        'Early access to new features'
                      ].map((feature, index) => (
                        <div key={index} className="flex items-center gap-3">
                          <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                          <span className="text-gray-700">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Pricing */}
                  <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        $29<span className="text-lg font-normal text-gray-600">/month</span>
                      </div>
                      <p className="text-gray-600 mt-2">
                        {isTrialExpired ? 'Instant access to your data' : 'Cancel anytime'} • 30-day money-back guarantee
                      </p>
                    </div>
                  </div>

                  {/* Purchase Button */}
                  <div className="text-center">
                    <button
                      onClick={() => {
                        // TODO: Integrate with payment processor
                        window.open('mailto:emilio.salas.data@gmail.com?subject=Memoire Pro License&body=I would like to purchase a Memoire Pro license.', '_blank');
                      }}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 mx-auto"
                    >
                      <Crown className="w-5 h-5" />
                      {isTrialExpired ? 'Reactivate Now' : 'Get License Key'}
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    <p className="text-xs text-gray-500 mt-3">
                      {isTrialExpired ? 'Immediate activation after purchase' : 'Contact us for licensing information'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      Enter License Key
                    </h3>
                    <p className="text-gray-600 text-sm mb-4">
                      Enter the license key you received after purchase
                    </p>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <span className="text-red-700 text-sm">{error}</span>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      License Key
                    </label>
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        value={licenseKey}
                        onChange={(e) => setLicenseKey(e.target.value)}
                        placeholder="Enter your license key..."
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={activating}
                      />
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleClose}
                      disabled={activating}
                      className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleActivate}
                      disabled={activating || !licenseKey.trim()}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {activating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Activating...
                        </>
                      ) : (
                        <>
                          <Key className="w-4 h-4" />
                          Activate License
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default LicenseModal;