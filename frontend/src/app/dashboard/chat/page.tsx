'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';
import { 
  MessageSquare, Plus, Send, FileText, 
  Bot, User, AlertTriangle, Loader2 
} from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';

export default function ChatPage() {
  const { user } = useAuthStore();
  const [sessions, setSessions] = useState<any[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [visibleCount, setVisibleCount] = useState(20);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  
  // Dialog State
  const [showNewSessionDialog, setShowNewSessionDialog] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [availableDocs, setAvailableDocs] = useState<any[]>([]);
  
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Fetch sessions on load
  useEffect(() => {
    if (user) {
      fetchSessions();
      fetchDocuments();
    }
  }, [user]);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents/user/me');
      setAvailableDocs(res.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSessions = async () => {
    try {
      setSessionsLoading(true);
      const res = await api.get('/chatbot/sessions/me');
      setSessions(res.data || []);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load chat sessions');
    } finally {
      setSessionsLoading(false);
    }
  };

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      setVisibleCount(20);
      fetchMessages(activeSessionId);
    }
  }, [activeSessionId]);

  const fetchMessages = async (id: string) => {
    try {
      const res = await api.get(`/chatbot/sessions/${id}`);
      setMessages(res.data.messages || []);
      scrollToBottom();
    } catch (e) {
      console.error(e);
      toast.error('Failed to load messages');
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (e.currentTarget.scrollTop === 0) {
      if (visibleCount < messages.length) {
        setVisibleCount(prev => prev + 20);
      }
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleCreateSession = async () => {
    try {
      const res = await api.post('/chatbot/sessions', {
        selected_document_ids: selectedDocs,
        selected_paper_ids: []
      });
      setSessions([res.data, ...sessions]);
      setActiveSessionId(res.data.id);
      setShowNewSessionDialog(false);
      setSelectedDocs([]); // reset selection
      toast.success('Session created');
    } catch (e: any) {
      console.error(e);
      toast.error(e.response?.data?.detail || 'Failed to create session');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeSessionId) return;

    const newMsg = { role: 'user', content: inputMessage, created_at: new Date().toISOString() };
    setMessages([...messages, newMsg]);
    setInputMessage('');
    setLoading(true);
    scrollToBottom();

    try {
      // Add a placeholder message for the assistant
      setMessages((prev) => [...prev, { role: 'assistant', content: '', references: [], created_at: new Date().toISOString() }]);

      const res = await fetch(`http://localhost:8000/chatbot/sessions/${activeSessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message: newMsg.content,
          selected_document_ids: selectedDocs,
          selected_paper_ids: []
        })
      });
      
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No reader");
      const decoder = new TextDecoder();
      
      let fullContent = '';
      setLoading(false); // We have started receiving, no need for the bouncing dots loader
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '');
            if (!dataStr) continue;
            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'chunk') {
                fullContent += data.content;
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].content = fullContent;
                  return newMsgs;
                });
                scrollToBottom();
              } else if (data.type === 'end') {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].references = data.references;
                  return newMsgs;
                });
              }
            } catch (e) {}
          }
        }
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to send message');
      setLoading(false);
    }
  };

  const exactFallbackText = "I don't have information about this in the available documents.";

  return (
    <div className="flex h-[calc(100vh-140px)] w-full max-w-6xl mx-auto bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-top-4 duration-300">
      
      {/* Sidebar */}
      <div className="w-72 border-r border-slate-200 bg-slate-50 flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-200">
          <button 
            onClick={() => setShowNewSessionDialog(true)}
            className="w-full flex items-center justify-center gap-2 bg-primary text-white py-2.5 rounded-xl font-semibold hover:bg-primary/90 transition-all shadow-sm"
          >
            <Plus className="h-4 w-4" />
            New Chat Session
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {sessionsLoading ? (
            <div className="flex justify-center p-4">
              <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center p-4 text-sm text-slate-500">
              No chat sessions yet.
            </div>
          ) : (
            sessions.map(s => (
              <button 
                key={s.id}
                onClick={() => setActiveSessionId(s.id)}
                className={`w-full text-left px-3 py-3 rounded-xl text-sm transition-colors ${
                  activeSessionId === s.id 
                    ? 'bg-primary/10 text-primary font-semibold' 
                    : 'text-slate-700 hover:bg-slate-200/50'
                }`}
              >
                <div className="truncate">{s.title}</div>
                <div className="text-xs font-normal opacity-70 mt-1">
                  {new Date(s.created_at).toLocaleDateString()}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-slate-50/30 relative">
        
        {/* Messages Window */}
        <div 
          className="flex-1 overflow-y-auto p-6"
          onScroll={handleScroll}
          ref={messagesContainerRef}
        >
          {!activeSessionId ? (
            <div className="flex flex-col h-full items-center justify-center text-slate-400">
              <MessageSquare className="h-16 w-16 mb-4 text-slate-200" />
              <p className="text-lg font-medium text-slate-600">MasterQ AI Chat</p>
              <p className="text-sm">Select a session or create a new one to begin.</p>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto">
              {messages.length > visibleCount && (
                <div className="text-center text-xs text-slate-400 mb-4 font-medium">
                  Scroll up to load older messages
                </div>
              )}
              {messages.slice(-visibleCount).map((m, idx) => {
                const isUser = m.role === 'user';
                const isFallback = !isUser && m.content.includes(exactFallbackText);

                return (
                  <div key={idx} className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex shrink-0 items-center justify-center h-8 w-8 rounded-full ${isUser ? 'bg-primary text-white' : 'bg-slate-200 text-slate-600'}`}>
                      {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}>
                      <div 
                        className={`rounded-2xl px-5 py-3.5 shadow-sm text-sm whitespace-pre-wrap leading-relaxed ${
                          isUser 
                            ? 'bg-primary text-white rounded-tr-none' 
                            : isFallback
                              ? 'bg-orange-50 border border-orange-200 text-orange-900 rounded-tl-none'
                              : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
                        }`}
                      >
                        {isFallback && (
                          <div className="flex items-center gap-2 mb-2 text-orange-600 font-semibold">
                            <AlertTriangle className="h-4 w-4" />
                            Missing Information
                          </div>
                        )}
                        <div className="prose-strong:font-bold prose-p:my-2 prose-ul:list-disc prose-ul:ml-4 prose-ol:list-decimal prose-ol:ml-4">
                          <ReactMarkdown>{m.content}</ReactMarkdown>
                        </div>
                        
                        {/* References */}
                        {!isUser && m.references && m.references.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-slate-100">
                            <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Sources referenced</p>
                            <ul className="space-y-1.5">
                              {m.references.map((ref: any, i: number) => (
                                <li key={i} className="text-xs flex items-center gap-1.5 text-primary bg-primary/5 w-fit px-2 py-1 rounded-md">
                                  <FileText className="h-3 w-3" />
                                  {ref.filename}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      <span className="text-[10px] font-medium text-slate-400 mt-1.5 mx-1">
                        {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                );
              })}
              {loading && (
                <div className="flex gap-3 flex-row">
                  <div className="flex shrink-0 items-center justify-center h-8 w-8 rounded-full bg-slate-200 text-slate-600">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm flex items-center gap-1 h-[46px]">
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              )}
              <div ref={endOfMessagesRef} className="h-1" />
            </div>
          )}
        </div>

        {/* Input Box */}
        {activeSessionId && (
          <div className="p-4 bg-white border-t border-slate-200">
            <div className="max-w-3xl mx-auto relative">
              <form onSubmit={handleSendMessage} className="flex relative">
                <input 
                  type="text" 
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask something about your documents..."
                  className="flex w-full rounded-2xl border border-slate-300 bg-white px-5 py-3.5 pr-14 text-sm shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:opacity-50"
                  disabled={loading}
                />
                <button 
                  type="submit" 
                  disabled={loading || !inputMessage.trim()}
                  className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-primary text-white rounded-xl shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          </div>
        )}
        
        {/* New Session Dialog */}
        {showNewSessionDialog && (
          <div className="absolute inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-white w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in zoom-in-95 duration-200">
              <div className="p-6">
                <h2 className="text-xl font-bold text-slate-900 mb-2">Create Chat Session</h2>
                <p className="text-sm text-slate-500 mb-6">
                  Select specific documents to restrict the AI's knowledge base. It will only answer from these sources.
                </p>
                
                <div className="space-y-2 mb-6">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Knowledge Base Documents</label>
                  <div className="max-h-60 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                    {availableDocs.length === 0 ? (
                      <div className="text-sm text-slate-500 p-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                        No documents uploaded yet.
                      </div>
                    ) : (
                      availableDocs.map(doc => (
                        <label key={doc.id} className={`flex items-center space-x-3 p-3 rounded-xl border cursor-pointer transition-colors ${selectedDocs.includes(doc.id) ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'}`}>
                          <input 
                            type="checkbox" 
                            checked={selectedDocs.includes(doc.id)}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedDocs([...selectedDocs, doc.id]);
                              else setSelectedDocs(selectedDocs.filter(id => id !== doc.id));
                            }}
                            className="w-4 h-4 text-primary rounded border-slate-300 focus:ring-primary focus:ring-offset-0"
                          />
                          <FileText className={`h-4 w-4 ${selectedDocs.includes(doc.id) ? 'text-primary' : 'text-slate-400'}`} />
                          <span className="text-sm font-medium truncate flex-1 text-slate-700">{doc.filename}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                  <button 
                    onClick={() => setShowNewSessionDialog(false)}
                    className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleCreateSession}
                    className="px-6 py-2.5 bg-primary text-white rounded-xl hover:bg-primary/90 text-sm font-bold transition-all shadow-sm"
                  >
                    Start Chatting
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
