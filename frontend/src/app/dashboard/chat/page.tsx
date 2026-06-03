'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

export default function ChatPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [visibleCount, setVisibleCount] = useState(20);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Dialog State
  const [showNewSessionDialog, setShowNewSessionDialog] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const topOfMessagesRef = useRef<HTMLDivElement>(null);

  // Fetch sessions on load
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://localhost:8000/chatbot/sessions/me', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setSessions(data);
    } catch (e) {
      console.error(e);
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
      const res = await fetch(`http://localhost:8000/chatbot/sessions/${id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setMessages(data.messages || []);
      scrollToBottom();
    } catch (e) {
      console.error(e);
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
      const res = await fetch('http://localhost:8000/chatbot/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          selected_document_ids: selectedDocs,
          selected_paper_ids: []
        })
      });
      const data = await res.json();
      setSessions([data, ...sessions]);
      setActiveSessionId(data.id);
      setShowNewSessionDialog(false);
    } catch (e) {
      console.error("Failed to create session");
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
      const data = await res.json();
      
      setMessages((prev) => [...prev, { 
        role: 'assistant', 
        content: data.content, 
        references: data.references,
        created_at: new Date().toISOString() 
      }]);
      scrollToBottom();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const exactFallbackText = "I don't have information about this in the available documents.";

  return (
    <div className="flex h-[calc(100vh-64px)] w-full max-w-7xl mx-auto bg-background border rounded-xl overflow-hidden mt-6">
      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/20 flex flex-col">
        <div className="p-4 border-b">
          <button 
            onClick={() => setShowNewSessionDialog(true)}
            className="w-full bg-primary text-primary-foreground py-2 rounded-md font-medium hover:bg-primary/90 transition-colors"
          >
            + New Chat Session
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(s => (
            <button 
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={`w-full text-left px-3 py-3 rounded-md text-sm truncate transition-colors ${activeSessionId === s.id ? 'bg-primary/10 font-semibold text-primary' : 'hover:bg-muted'}`}
            >
              {s.title}
              <div className="text-xs text-muted-foreground font-normal mt-1">
                {new Date(s.created_at).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-background relative">
        
        {/* Messages Window */}
        <div 
          className="flex-1 overflow-y-auto p-6 space-y-6"
          onScroll={handleScroll}
        >
          {!activeSessionId ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Select or create a chat session to begin.
            </div>
          ) : (
            <>
              {messages.length > visibleCount && (
                <div className="text-center text-xs text-muted-foreground mb-4">
                  Scroll up to load more messages...
                </div>
              )}
              {messages.slice(-visibleCount).map((m, idx) => {
                const isUser = m.role === 'user';
                const isFallback = !isUser && m.content.includes(exactFallbackText);

                return (
                  <div key={idx} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                    <div 
                      className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                        isUser 
                          ? 'bg-primary text-primary-foreground rounded-br-none' 
                          : isFallback
                            ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200 border border-orange-200 rounded-bl-none'
                            : 'bg-muted rounded-bl-none'
                      }`}
                    >
                      <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                      
                      {/* References Toggle */}
                      {!isUser && m.references && m.references.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-border/50">
                          <p className="text-xs font-semibold uppercase tracking-wider opacity-70 mb-2">Sources Referenced</p>
                          <ul className="space-y-1">
                            {m.references.map((ref: any, i: number) => (
                              <li key={i} className="text-xs flex items-center gap-2 text-primary">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                                {ref.filename}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] text-muted-foreground mt-1 mx-1">
                      {new Date(m.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                );
              })}
              {loading && (
                <div className="flex items-start">
                  <div className="bg-muted rounded-2xl rounded-bl-none px-5 py-3 flex space-x-1 items-center h-10">
                    <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              )}
              <div ref={endOfMessagesRef} />
            </>
          )}
        </div>

        {/* Input Box */}
        {activeSessionId && (
          <div className="p-4 bg-background border-t">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input 
                type="text" 
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask something about your documents..."
                className="flex h-12 w-full rounded-full border border-input bg-transparent px-4 py-2 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                disabled={loading}
              />
              <button 
                type="submit" 
                disabled={loading || !inputMessage.trim()}
                className="h-12 px-6 bg-primary text-primary-foreground rounded-full font-medium shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                Send
              </button>
            </form>
          </div>
        )}
        
        {/* New Session Dialog */}
        {showNewSessionDialog && (
          <div className="absolute inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card w-full max-w-md rounded-xl shadow-lg border p-6">
              <h2 className="text-xl font-bold mb-4">Create New Chat Session</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Select specific documents to restrict the AI's knowledge base. It will only answer from these sources.
              </p>
              
              <div className="space-y-4 mb-8">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Link Document IDs (Comma separated)</label>
                  <input 
                    type="text" 
                    onChange={e => setSelectedDocs(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" 
                    placeholder="UUID1, UUID2..."
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button 
                  onClick={() => setShowNewSessionDialog(false)}
                  className="px-4 py-2 border rounded-md hover:bg-muted text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleCreateSession}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-sm font-medium transition-colors"
                >
                  Create & Chat
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
