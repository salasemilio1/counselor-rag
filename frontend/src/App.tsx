import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, MessageCircle, User, Bot, Search, FileText, Calendar, Clock } from 'lucide-react';

const App = () => {
  const [selectedClient, setSelectedClient] = useState('John Doe');
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: "Hello! I'm here to help you prepare for your session with John. What would you like to know about his case history, treatment goals, or previous sessions?",
      timestamp: new Date(Date.now() - 300000)
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const clients = [
    { 
      name: 'John Doe', 
      lastSession: '2 days ago', 
      status: 'active',
      nextSession: 'Today, 2:00 PM'
    },
    { 
      name: 'Jane Smith', 
      lastSession: '1 week ago', 
      status: 'scheduled',
      nextSession: 'Tomorrow, 10:00 AM'
    },
    { 
      name: 'Michael Johnson', 
      lastSession: '3 days ago', 
      status: 'active',
      nextSession: 'Friday, 3:30 PM'
    },
    { 
      name: 'Sarah Wilson', 
      lastSession: '2 weeks ago', 
      status: 'inactive',
      nextSession: 'Not scheduled'
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponses = [
        `Based on ${selectedClient}'s case notes, their primary treatment goals include improving coping strategies for anxiety and developing better communication skills. Their last session focused on cognitive behavioral techniques, and they showed good progress with the homework assignments.`,
        `${selectedClient} has been working on mindfulness exercises since our last session. Their anxiety levels have decreased from 7/10 to 4/10 over the past month. Key discussion points for today might include their workplace stress and relationship concerns.`,
        `Recent session notes indicate ${selectedClient} has been practicing grounding techniques successfully. They've reported better sleep patterns and reduced panic episodes. Consider exploring their progress with the breathing exercises we introduced.`
      ];
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: aiResponses[Math.floor(Math.random() * aiResponses.length)],
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleClientSelect = (clientName) => {
    setSelectedClient(clientName);
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: `Hello! I'm here to help you prepare for your session with ${clientName}. What would you like to know about their case history, treatment goals, or previous sessions?`,
        timestamp: new Date()
      }
    ]);
  };

  const formatTime = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp);
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
          
          <button className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Plus className="w-4 h-4" />
            New Chat
          </button>
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
            {clients.map((client) => (
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
            <div className="flex items-center gap-2">
              <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                <FileText className="w-5 h-5" />
              </button>
            </div>
          </div>
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
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  </div>
                  <span className="text-xs text-gray-500 mt-1 px-1">
                    {formatTime(message.timestamp)}
                  </span>
                </div>
              </div>
            ))}
            
            {isTyping && (
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
                  placeholder={`Ask about ${selectedClient}'s case, goals, or session history...`}
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
              <button
                onClick={handleSubmit}
                disabled={!inputValue.trim() || isTyping}
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
    </div>
  );
};

export default App;