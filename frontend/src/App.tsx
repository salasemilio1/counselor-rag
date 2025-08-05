import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, MessageCircle, User, Bot, Search, FileText, Calendar, Clock, Upload, X, Settings, Trash2, Eye, AlertTriangle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const App = () => {
  const [selectedClient, setSelectedClient] = useState('');
  const [messages, setMessages] = useState<Array<{
    id: number;
    type: 'user' | 'ai';
    content: string;
    timestamp: Date;
    sources?: { filename?: string }[];
  }>>([]);
  // New: track selected source document for viewing
  const [selectedSource, setSelectedSource] = useState(null);
  const [sourceText, setSourceText] = useState('');
  
  // Document management state
  const [showDocumentManager, setShowDocumentManager] = useState(false);
  const [allClientDocuments, setAllClientDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  // New: fetch and load selected source document text
  useEffect(() => {
    const fetchSourceText = async () => {
      if (!selectedSource?.filename) return;
      try {
        const clientId = selectedClient.toLowerCase().replace(/\s+/g, '');
        const res = await fetch(`${BACKEND_URL}/static/clients/${clientId}/${selectedSource.filename}`);
        const text = await res.text();
        setSourceText(text);
      } catch (err) {
        setSourceText(`⚠️ Failed to load document: ${err.message}`);
      }
    };
    if (selectedSource) {
      fetchSourceText();
    } else {
      setSourceText('');
    }
    // eslint-disable-next-line
  }, [selectedSource]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  // Client list state (fetched from backend)
  const [clientList, setClientList] = useState([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch documents when client changes
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const clientId = selectedClient.toLowerCase().replace(/\s+/g, '');
        const res = await fetch(`${BACKEND_URL}/meetings/${clientId}`);
        const data = await res.json();
        const realDocs = (data.meetings || data.files || []).map((doc, index) => ({
          id: doc.id || `doc_${index}`,
          name: doc.name || doc.filename || `Doc ${index + 1}`,
          filename: doc.filename || doc.name
        }));
        setDocuments(realDocs);
      } catch (error) {
        console.error('Failed to fetch documents:', error);
        setDocuments([]);
      }
    };
    fetchDocuments();
  }, [selectedClient]);

  // Fetch clients from backend (moved to component scope)
  const fetchClients = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/clients`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();

      if (data.error) {
        console.error("Backend error:", data.error);
        return;
      }

      const dynamicClients = data.clients.map((name) => ({
        name,
        lastSession: 'Unknown',
        status: 'active',
        nextSession: 'Not scheduled'
      }));

      setClientList(dynamicClients);
      if (dynamicClients.length === 0) {
        setMessages([{
          id: 1,
          type: 'ai',
          content: "Hi there! I'm ready to help you prepare for your sessions. To get started, add a client and upload some session notes - then I can help you review their history and identify patterns.",
          timestamp: new Date()
        }]);
      }
    } catch (err) {
      console.error("Failed to fetch clients:", err);
      setMessages([{
        id: 1,
        type: 'ai',
        content: `❌ Failed to connect to backend: ${err.message}. Please ensure the backend is running on ${BACKEND_URL}`,
        timestamp: new Date()
      }]);
    }
  };
  // Fetch clients from backend on mount
  useEffect(() => {
    fetchClients();
  }, []);

  // Add Client handler
  const handleAddClient = async () => {
    const name = window.prompt("Enter new client name:");
    if (!name?.trim()) return;
    try {
      const clientId = name.toLowerCase().replace(/\s+/g, "_");
      const res = await fetch(`${BACKEND_URL}/clients/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: clientId })
      });
      if (!res.ok) throw new Error("Failed to create client");
      await fetchClients();
      setSelectedClient(name);
      setMessages([{
        id: Date.now(),
        type: "ai",
        content: `Great! I've set up a profile for ${name}. Upload some session notes when you're ready, and I'll help you keep track of their progress and identify key themes.`,
        timestamp: new Date()
      }]);
    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const queryText = inputValue;
    setInputValue('');
    setIsTyping(true);

    // Create placeholder AI message for streaming
    const aiMessageId = Date.now() + 1;
    const aiMessage = {
      id: aiMessageId,
      type: 'ai',
      content: '',
      timestamp: new Date(),
      sources: []
    };
    setMessages(prev => [...prev, aiMessage]);
    
    // Switch from typing indicator to streaming mode
    setIsTyping(false);
    setIsStreaming(true);

    try {
      const clientId = selectedClient.toLowerCase().replace(/\s+/g, '');
      const response = await fetch(`${BACKEND_URL}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          client_id: clientId,
          query: queryText,
          meeting_ids: selectedDocs.length > 0 ? selectedDocs : undefined
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              setIsStreaming(false);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'metadata') {
                // Update message with sources and metadata
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, sources: parsed.sources || [] }
                    : msg
                ));
              } else if (parsed.type === 'content') {
                // Append content to the AI message
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, content: msg.content + parsed.content }
                    : msg
                ));
              } else if (parsed.type === 'error') {
                // Handle error
                setMessages(prev => prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, content: `❌ ${parsed.content}` }
                    : msg
                ));
                setIsStreaming(false);
                return;
              }
            } catch (parseError) {
              console.error('Error parsing streaming data:', parseError);
            }
          }
        }
      }
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessageId 
          ? { ...msg, content: `❌ Query failed: ${error.message}` }
          : msg
      ));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleClientSelect = (clientName) => {
    if (!clientName) return;
    setSelectedClient(clientName);
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: `Ready to help you prep for ${clientName}'s session! I can help you review their recent progress, remind you of key themes from past meetings, or help you spot patterns. What would you like to explore?`,
        timestamp: new Date()
      }
    ]);
    setSelectedDocs([]);
  };

  const handleDocSelect = (docId) => {
    setSelectedDocs(prev => {
      if (prev.includes(docId)) {
        return prev.filter(id => id !== docId);
      } else {
        return [...prev, docId];
      }
    });
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    // Compute clientId once
    const clientId = selectedClient.toLowerCase().replace(/\s+/g, "");

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append(
        "client_id",
        clientId
      );
      files.forEach((file) => {
        formData.append("files", file);
      });

      // Upload files
      const uploadRes = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData
      });

      if (!uploadRes.ok) {
        throw new Error("Upload failed");
      }

      // Trigger ingestion after upload
      const ingestRes = await fetch(`${BACKEND_URL}/ingest/${clientId}?force=true`, {
        method: "POST"
      });
      const ingestData = await ingestRes.json();
      if (!ingestRes.ok) {
        throw new Error(ingestData.message || "Ingestion failed");
      }

      const successMessage = {
        id: Date.now(),
        type: "ai",
        content: `Perfect! I've processed ${files.length} file(s) for ${selectedClient}. I'm now familiar with their recent sessions and ready to help you prepare for your next meeting.`,
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, successMessage]);

      const newDocs = files.map((file, index) => ({
        id: `upload_${Date.now()}_${index}`,
        name: file.name,
        filename: file.name
      }));
      setDocuments((prev) => [...prev, ...newDocs]);
    } catch (err) {
      const errorMessage = {
        id: Date.now(),
        type: "ai",
        content: `❌ Upload failed: ${err.message}`,
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const formatTime = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp);
  };

  // Document management functions
  const fetchAllClientDocuments = async () => {
    if (!selectedClient) return;
    
    setLoadingDocuments(true);
    try {
      const clientId = selectedClient.toLowerCase().replace(/\s+/g, '');
      const res = await fetch(`${BACKEND_URL}/clients/${clientId}/documents`);
      const data = await res.json();
      
      if (data.error) {
        console.error('Error fetching documents:', data.error);
        setAllClientDocuments([]);
      } else {
        setAllClientDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setAllClientDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
  };

  const handleDeleteDocument = async (filename) => {
    if (!selectedClient) return;
    
    try {
      const clientId = selectedClient.toLowerCase().replace(/\s+/g, '');
      const res = await fetch(`${BACKEND_URL}/clients/${clientId}/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        // Refresh document list
        await fetchAllClientDocuments();
        // Refresh the quick select documents too
        const quickRes = await fetch(`${BACKEND_URL}/meetings/${clientId}`);
        const quickData = await quickRes.json();
        const realDocs = (quickData.meetings || quickData.files || []).map((doc, index) => ({
          id: doc.id || `doc_${index}`,
          name: doc.name || doc.filename || `Doc ${index + 1}`,
          filename: doc.filename || doc.name
        }));
        setDocuments(realDocs);
        
        // Show success message
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'ai',
          content: `✅ Successfully deleted document "${filename}"`,
          timestamp: new Date()
        }]);
      } else {
        throw new Error('Failed to delete document');
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'ai',
        content: `❌ Failed to delete document "${filename}": ${error.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setShowDeleteConfirm(false);
      setDocumentToDelete(null);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'inactive': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Sidebar Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">CounselAI</h1>
              <p className="text-sm text-gray-500">Session Preparation</p>
            </div>
          </div>
          <div className="flex flex-row">
            <button
              onClick={handleAddClient}
              className="ml-0 mr-2 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Add Client"
              type="button"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button 
              onClick={() => {
                setMessages([{
                  id: 1,
                  type: 'ai',
                  content: `Ready to help you prep for ${selectedClient}'s session! I can help you review their recent progress, remind you of key themes from past meetings, or help you spot patterns. What would you like to explore?`,
                  timestamp: new Date()
                }]);
                setSelectedDocs([]);
              }}
              className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Chat
            </button>
          </div>
        </div>

        {/* Client List */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search clients..."
                className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide px-2">Clients</h3>
            {clientList.map((client) => (
              <div
                key={client.name}
                onClick={() => handleClientSelect(client.name)}
                className={`p-3 rounded-lg cursor-pointer transition-all hover:bg-gray-50 ${
                  selectedClient === client.name 
                    ? 'bg-blue-50 border border-blue-200' 
                    : 'border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900 text-sm">{client.name}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(client.status)}`}>
                    {client.status}
                  </span>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    Last: {client.lastSession}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-600">
                    <Calendar className="w-3 h-3" />
                    Next: {client.nextSession}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex flex-col flex-1">
        {/* Chat Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-gray-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">{selectedClient}</h2>
                <p className="text-sm text-gray-500">Session Preparation Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Document Selection */}
              {documents.length > 0 && (
                <div className="relative">
                  <div className="text-xs text-gray-500 mb-1">Available Documents ({documents.length})</div>
                  <div className="flex flex-wrap gap-1 max-w-xs">
                    {documents.slice(0, 3).map(doc => (
                      <button
                        key={doc.id}
                        onClick={() => handleDocSelect(doc.id)}
                        className={`px-2 py-1 text-xs rounded-full border transition-colors ${
                          selectedDocs.includes(doc.id)
                            ? 'bg-blue-100 border-blue-300 text-blue-800'
                            : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        {(doc.name || doc.filename || 'Document').slice(0, 15)}
                        {selectedDocs.includes(doc.id) && <X className="w-3 h-3 ml-1 inline" />}
                      </button>
                    ))}
                    {documents.length > 3 && (
                      <span className="px-2 py-1 text-xs text-gray-500">+{documents.length - 3} more</span>
                    )}
                  </div>
                </div>
              )}
              
              {/* Document Management */}
              {selectedClient && (
                <button
                  onClick={() => {
                    setShowDocumentManager(true);
                    fetchAllClientDocuments();
                  }}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Manage documents"
                >
                  <Settings className="w-5 h-5" />
                </button>
              )}
              
              {/* File Upload */}
              <div className="relative">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                  title="Upload documents"
                >
                  {isUploading ? (
                    <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
                  ) : (
                    <Upload className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Selected Documents Info */}
          {selectedDocs.length > 0 && (
            <div className="mt-2 text-xs text-blue-600">
              Querying {selectedDocs.length} selected document{selectedDocs.length > 1 ? 's' : ''}
            </div>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex gap-4 ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.type === 'user' 
                    ? 'bg-blue-600' 
                    : 'bg-gradient-to-br from-purple-500 to-pink-500'
                }`}>
                  {message.type === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>
                <div className={`flex flex-col max-w-2xl ${message.type === 'user' ? 'items-end' : ''}`}>
                  <div className={`px-4 py-3 rounded-2xl ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}>
                    <div className="text-sm leading-relaxed">
                      <ReactMarkdown
                        components={{
                          p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                          strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                          em: ({children}) => <em className="italic">{children}</em>,
                          ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                          ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                          li: ({children}) => <li className="text-sm">{children}</li>
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-gray-200">
                        <div className="flex items-center gap-1 mb-1">
                          <FileText className="w-3 h-3 text-gray-400" />
                          <span className="text-xs font-medium text-gray-600">Referenced Documents:</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {message.sources.map((src, i) => (
                            <button
                              key={i}
                              onClick={() => setSelectedSource(src)}
                              className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-md border border-blue-200 transition-colors"
                              type="button"
                            >
                              <FileText className="w-3 h-3" />
                              {src.filename || "Unnamed Document"}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 mt-1 px-1">
                    {formatTime(message.timestamp)}
                  </span>
                </div>
              </div>
            ))}
            
            {isTyping && !isStreaming && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  placeholder={`What would you like to know about ${selectedClient}? Ask about patterns, progress, goals, or specific sessions...`}
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  disabled={isTyping || isStreaming}
                />
              </div>
              <button
                onClick={handleSubmit}
                disabled={!inputValue.trim() || isTyping || isStreaming}
                className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              AI assistant to help prepare for counseling sessions with evidence-based insights
            </p>
          </div>
        </div>
      </div>

      {/* Document Viewer Side Panel */}
      {selectedSource && (
        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          {/* Panel Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Document Viewer</h3>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                type="button"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mt-1 truncate" title={selectedSource.filename}>
              {selectedSource.filename}
            </p>
          </div>
          
          {/* Document Content */}
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded-md border">
              {sourceText || (
                <div className="flex items-center justify-center py-8 text-gray-500">
                  <div className="text-center">
                    <div className="animate-spin w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full mx-auto mb-2"></div>
                    <p>Loading document...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Document Management Modal */}
      {showDocumentManager && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-4xl h-3/4 flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Settings className="w-6 h-6 text-blue-600" />
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Document Management</h2>
                    <p className="text-sm text-gray-600">Manage documents for {selectedClient}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowDocumentManager(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 p-6 overflow-y-auto">
              {loadingDocuments ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-3"></div>
                    <p className="text-gray-600">Loading documents...</p>
                  </div>
                </div>
              ) : allClientDocuments.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No documents found for this client</p>
                  <p className="text-sm text-gray-500 mt-1">Upload some documents to get started</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      Documents ({allClientDocuments.length})
                    </h3>
                  </div>
                  
                  {allClientDocuments.map((doc, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <FileText className="w-4 h-4 text-blue-600" />
                            <h4 className="font-medium text-gray-900">{doc.filename}</h4>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                            <div>
                              <span className="font-medium">Meeting ID:</span> {doc.meeting_id}
                            </div>
                            <div>
                              <span className="font-medium">Date:</span> {doc.date}
                            </div>
                            <div>
                              <span className="font-medium">Size:</span> {formatFileSize(doc.size)}
                            </div>
                            <div>
                              <span className="font-medium">Modified:</span> {formatDate(doc.modified)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <button
                            onClick={() => {
                              setSelectedSource({filename: doc.filename});
                              setShowDocumentManager(false);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="View document"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              setDocumentToDelete(doc);
                              setShowDeleteConfirm(true);
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && documentToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Document</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>
            
            <p className="text-gray-700 mb-6">
              Are you sure you want to delete <strong>"{documentToDelete.filename}"</strong>? 
              This will permanently remove the document and all associated data from the system.
            </p>
            
            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDocumentToDelete(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteDocument(documentToDelete.filename)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;