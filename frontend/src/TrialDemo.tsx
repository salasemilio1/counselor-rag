import React, { useState, useEffect } from 'react';
import { Crown, Clock, Users, FileText, MessageCircle } from 'lucide-react';

interface LicenseStatus {
  license_type: string;
  is_valid: boolean;
  days_remaining: number;
  days_used: number;
  engagement_score: number;
  usage_stats: {
    clients_created: number;
    documents_uploaded: number;
    total_queries: number;
  };
}

const TrialDemo: React.FC = () => {
  const [licenseStatus, setLicenseStatus] = useState<LicenseStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/license/status');
        const data = await response.json();
        setLicenseStatus(data);
      } catch (error) {
        console.error('Failed to fetch license status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading trial system...</p>
        </div>
      </div>
    );
  }

  if (!licenseStatus) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center text-red-600">
          <p>Failed to connect to backend. Make sure the server is running on port 8000.</p>
        </div>
      </div>
    );
  }

  const createTestClient = async () => {
    try {
      const response = await fetch('http://localhost:8000/clients/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: `demo_client_${Date.now()}` })
      });
      
      if (response.ok) {
        // Refresh status
        const statusResponse = await fetch('http://localhost:8000/license/status');
        const data = await statusResponse.json();
        setLicenseStatus(data);
      }
    } catch (error) {
      console.error('Failed to create client:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Crown className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Memoire Trial System Demo</h1>
              <p className="text-gray-600">Experience the unlimited trial approach</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Trial Status Card */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-3 mb-4">
              <Clock className="w-6 h-6 text-blue-500" />
              <h2 className="text-xl font-semibold">Trial Status</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">License Type:</span>
                <span className="font-medium text-blue-600 uppercase">{licenseStatus.license_type}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Days Remaining:</span>
                <span className="font-bold text-2xl text-green-600">{licenseStatus.days_remaining}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Days Used:</span>
                <span className="font-medium">{licenseStatus.days_used}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Status:</span>
                <span className={`px-2 py-1 rounded text-sm font-medium ${
                  licenseStatus.is_valid 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {licenseStatus.is_valid ? 'Active - Full Access' : 'Expired - Locked'}
                </span>
              </div>
              
              <div className="pt-4 border-t">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Engagement Score:</span>
                  <span className="font-medium">{licenseStatus.engagement_score}/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, licenseStatus.engagement_score)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Usage Stats Card */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-3 mb-4">
              <Users className="w-6 h-6 text-purple-500" />
              <h2 className="text-xl font-semibold">Usage Statistics</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-blue-600" />
                  <span className="font-medium">Clients Created</span>
                </div>
                <span className="text-2xl font-bold text-blue-600">
                  {licenseStatus.usage_stats.clients_created}
                </span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-green-600" />
                  <span className="font-medium">Documents Uploaded</span>
                </div>
                <span className="text-2xl font-bold text-green-600">
                  {licenseStatus.usage_stats.documents_uploaded}
                </span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <MessageCircle className="w-5 h-5 text-purple-600" />
                  <span className="font-medium">Total Queries</span>
                </div>
                <span className="text-2xl font-bold text-purple-600">
                  {licenseStatus.usage_stats.total_queries}
                </span>
              </div>
            </div>
          </div>

          {/* Demo Actions Card */}
          <div className="bg-white rounded-lg shadow-sm border p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Demo Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={createTestClient}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <Users className="w-4 h-4" />
                Create Test Client
              </button>
              
              <button
                onClick={() => window.open('http://localhost:8000/license/status', '_blank')}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-3 rounded-lg font-medium transition-colors"
              >
                View API Response
              </button>
              
              <button
                onClick={() => {
                  const statusResponse = fetch('http://localhost:8000/license/status');
                  statusResponse.then(res => res.json()).then(data => setLicenseStatus(data));
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg font-medium transition-colors"
              >
                Refresh Status
              </button>
            </div>
            
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="font-semibold text-yellow-800 mb-2">🎯 Trial Strategy Demo</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• <strong>Unlimited Access:</strong> Create as many clients as you want - no restrictions!</li>
                <li>• <strong>Engagement Tracking:</strong> Watch your engagement score increase with usage</li>
                <li>• <strong>Dependency Building:</strong> Users build complete workflows over 30 days</li>
                <li>• <strong>Hard Cutoff:</strong> After expiration, complete product lockdown drives conversion</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrialDemo;