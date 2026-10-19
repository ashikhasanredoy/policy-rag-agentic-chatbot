import React, { useState, useEffect, useRef } from 'react';
import { Plus, PanelLeftClose, PanelLeft, Trash2, MessageSquare, Sparkles } from 'lucide-react';
import UserMessage from '../components/chat/UserMessage';
import AIMessage from '../components/chat/AIMessage';
import TypingIndicator from '../components/chat/TypingIndicator';
import ChatInput from '../components/chat/ChatInput';
import { api } from '../services/api';

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    const saved = localStorage.getItem('policy_sidebar_open');
    return saved !== null ? JSON.parse(saved) : true;
  });
  const messagesEndRef = useRef(null);
  const viewportRef = useRef(null);
  const inputRef = useRef(null);
  const isInitialRestoreRef = useRef(true);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async (targetIdToSelect = null) => {
    try {
      const res = await api.getConversations();
      if (res.data) {
        setConversations(res.data);

        // Determine which conversation to restore
        const savedId = targetIdToSelect || localStorage.getItem('policy_active_conv_id');
        const convToRestore = res.data.find((c) => c.id === savedId) || (savedId ? null : (res.data.length > 0 ? res.data[0] : null));

        if (convToRestore) {
          handleSelectConversation(convToRestore.id, true);
        } else {
          isInitialRestoreRef.current = false;
        }
      }
    } catch (e) {
      console.error('Failed to load conversations', e);
    }
  };

  const scrollToBottom = (instant = false) => {
    if (instant) {
      if (viewportRef.current) {
        viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
      }
    } else {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    if (isInitialRestoreRef.current) {
      scrollToBottom(true);
    } else {
      scrollToBottom(false);
    }
  }, [messages, loading]);

  const handleToggleSidebar = (open) => {
    setSidebarOpen(open);
    localStorage.setItem('policy_sidebar_open', JSON.stringify(open));
  };

  const handleSelectConversation = async (convId, isInitial = false) => {
    setCurrentConvId(convId);
    localStorage.setItem('policy_active_conv_id', convId);
    try {
      const res = await api.getMessages(convId);
      if (res.data) {
        setMessages(res.data);
        if (isInitial) {
          setTimeout(() => {
            scrollToBottom(true);
            isInitialRestoreRef.current = false;
          }, 40);
        } else {
          isInitialRestoreRef.current = false;
        }
      }
    } catch (e) {
      console.error('Failed to load messages', e);
    }
  };

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (currentConvId === convId) {
        localStorage.removeItem('policy_active_conv_id');
        handleNewChat();
      }
    } catch (err) {
      console.error('Failed to delete conversation', err);
    }
  };

  const handleNewChat = () => {
    localStorage.removeItem('policy_active_conv_id');
    setCurrentConvId(null);
    setMessages([]);
    isInitialRestoreRef.current = false;
    api.getConversations().then((res) => {
      if (res.data) setConversations(res.data);
    });
    setTimeout(() => {
      inputRef.current?.focus();
    }, 50);
  };

  const handleSendMessage = async (text) => {
    isInitialRestoreRef.current = false;
    const userMsg = { id: `temp_${Date.now()}`, role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.sendMessage({
        message: text,
        conversation_id: currentConvId,
      });

      if (!currentConvId && res.conversation_id) {
        setCurrentConvId(res.conversation_id);
        localStorage.setItem('policy_active_conv_id', res.conversation_id);
        loadConversations(res.conversation_id);
      }

      const aiMsg = {
        id: res.message_id,
        role: 'assistant',
        content: res.answer,
        answerable: res.answerable,
        confidence: res.confidence,
        sources: res.sources,
        trace: res.trace,
        latency_ms: res.latency_ms,
        isStreaming: true,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Error processing policy request: ${err.message}`,
          answerable: false,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-layout">
      {/* Sidebar */}
      <aside className={`chat-sidebar ${!sidebarOpen ? 'collapsed' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button onClick={handleNewChat} className="new-chat-btn" style={{ flex: 1 }}>
            <Plus size={16} /> New Chat
          </button>
          <button
            onClick={() => handleToggleSidebar(false)}
            className="sidebar-toggle-btn"
            title="Hide Sidebar"
          >
            <PanelLeftClose size={18} />
          </button>
        </div>

        <div className="sidebar-section-header">
          <span>Recent Conversations</span>
          <span className="history-count-badge">{conversations.length}</span>
        </div>

        <div className="chat-history-list">
          {conversations.length === 0 ? (
            <div className="empty-history-notice">
              <MessageSquare size={20} style={{ opacity: 0.4, margin: '0 auto 8px' }} />
              <div>No conversations yet</div>
              <div style={{ fontSize: '0.74rem', opacity: 0.7, marginTop: '2px' }}>Start a new chat to begin</div>
            </div>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => handleSelectConversation(c.id)}
                className={`history-item ${currentConvId === c.id ? 'active' : ''}`}
                title={c.title || 'Policy Discussion'}
              >
                <MessageSquare size={15} className="history-icon" />
                <span className="history-title">{c.title || 'Policy Discussion'}</span>
                <button
                  type="button"
                  className="history-delete-btn"
                  title="Delete conversation"
                  onClick={(e) => handleDeleteConversation(e, c.id)}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-main">
        {/* Floating Controls when sidebar is closed */}
        {!sidebarOpen && (
          <div className="floating-top-controls">
            <button
              onClick={() => handleToggleSidebar(true)}
              className="floating-btn"
              title="Show Sidebar"
            >
              <PanelLeft size={17} />
            </button>
            <button
              onClick={handleNewChat}
              className="floating-btn"
              title="New Chat"
            >
              <Plus size={17} />
            </button>
          </div>
        )}

        <div className="messages-viewport" ref={viewportRef}>
          {messages.length === 0 && !loading && (
            <div className="empty-chat-hero">
              <div className="hero-badge">
                <Sparkles size={14} className="hero-sparkle" />
                <span>Enterprise Verified Policy AI</span>
              </div>
              <h1 className="hero-title">How can I help with company policies?</h1>
              <p className="hero-subtitle">
                Accurate, point-wise policy guidance with instant source citations and strict zero-hallucination guardrails.
              </p>

              <div className="suggestion-cards-grid">
                <button
                  type="button"
                  className="suggestion-card"
                  onClick={() => handleSendMessage("How many vacation days do I earn per year, and how many can I carry over into next year?")}
                >
                  <div className="suggestion-top">
                    <span className="suggestion-emoji">🌴</span>
                    <span className="suggestion-tag">HR & Leave</span>
                  </div>
                  <div className="suggestion-text">How many vacation days do I earn per year and carryover rules?</div>
                </button>

                <button
                  type="button"
                  className="suggestion-card"
                  onClick={() => handleSendMessage("What is the home office equipment stipend and monthly internet allowance for remote workers?")}
                >
                  <div className="suggestion-top">
                    <span className="suggestion-emoji">🏡</span>
                    <span className="suggestion-tag">Remote Work</span>
                  </div>
                  <div className="suggestion-text">Home office equipment stipend and monthly internet allowance</div>
                </button>

                <button
                  type="button"
                  className="suggestion-card"
                  onClick={() => handleSendMessage("What is the daily meal per diem and hotel rate limit for business travel?")}
                >
                  <div className="suggestion-top">
                    <span className="suggestion-emoji">✈️</span>
                    <span className="suggestion-tag">Travel & Expenses</span>
                  </div>
                  <div className="suggestion-text">Daily meal per diem and hotel limits for business travel</div>
                </button>

                <button
                  type="button"
                  className="suggestion-card"
                  onClick={() => handleSendMessage("Does the company offer a 401(k) match and education or tuition assistance?")}
                >
                  <div className="suggestion-top">
                    <span className="suggestion-emoji">🎓</span>
                    <span className="suggestion-tag">Benefits</span>
                  </div>
                  <div className="suggestion-text">401(k) company matching and annual tuition assistance</div>
                </button>
              </div>
            </div>
          )}

          {messages.map((msg, index) =>
            msg.role === 'user' ? (
              <UserMessage key={msg.id || index} message={msg} />
            ) : (
              <AIMessage
                key={msg.id || index}
                message={msg}
                onStreamProgress={() => scrollToBottom(false)}
              />
            )
          )}
          {loading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <ChatInput onSendMessage={handleSendMessage} disabled={loading} inputRef={inputRef} />
      </main>
    </div>
  );
}
