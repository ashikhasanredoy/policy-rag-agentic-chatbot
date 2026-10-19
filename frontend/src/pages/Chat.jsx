import React, { useState, useEffect, useRef } from 'react';
import { Plus, PanelLeftClose, PanelLeft, Trash2, MoreHorizontal, Pin } from 'lucide-react';
import UserMessage from '../components/chat/UserMessage';
import AIMessage from '../components/chat/AIMessage';
import TypingIndicator from '../components/chat/TypingIndicator';
import ChatInput from '../components/chat/ChatInput';
import { api } from '../services/api';

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [pinnedIds, setPinnedIds] = useState(() => {
    try {
      const saved = localStorage.getItem('policy_pinned_conv_ids');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });
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

  const handleTogglePin = (e, convId) => {
    e.stopPropagation();
    setPinnedIds((prev) => {
      const isPinned = prev.includes(convId);
      const updated = isPinned ? prev.filter((id) => id !== convId) : [convId, ...prev];
      localStorage.setItem('policy_pinned_conv_ids', JSON.stringify(updated));
      return updated;
    });
    setActiveMenuId(null);
  };

  useEffect(() => {
    loadConversations();
    const handleOutsideClick = () => setActiveMenuId(null);
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
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

  const getGroupedConversations = () => {
    const groups = {
      'Pinned': [],
      'Today': [],
      '7 Days': [],
      '30 Days': [],
      'Older': [],
    };

    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const sevenDaysAgo = startOfToday - 7 * 24 * 60 * 60 * 1000;
    const thirtyDaysAgo = startOfToday - 30 * 24 * 60 * 60 * 1000;

    conversations.forEach((c) => {
      if (pinnedIds.includes(c.id)) {
        groups['Pinned'].push(c);
        return;
      }

      const dateStr = c.updated_at || c.created_at;
      let convTime = Date.now();
      if (dateStr) {
        convTime = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z').getTime();
        if (isNaN(convTime)) convTime = new Date(dateStr).getTime();
      }

      if (convTime >= startOfToday) {
        groups['Today'].push(c);
      } else if (convTime >= sevenDaysAgo) {
        groups['7 Days'].push(c);
      } else if (convTime >= thirtyDaysAgo) {
        groups['30 Days'].push(c);
      } else {
        groups['Older'].push(c);
      }
    });

    return Object.entries(groups).filter(([_, items]) => items.length > 0);
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
      setPinnedIds((prev) => {
        const updated = prev.filter((id) => id !== convId);
        localStorage.setItem('policy_pinned_conv_ids', JSON.stringify(updated));
        return updated;
      });
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

  const cleanTitle = (rawTitle) => {
    if (!rawTitle) return 'Policy Discussion';
    return rawTitle.replace(/\.{2,}$/, '').replace(/…+$/, '').trim();
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

        <div className="chat-history-list">
          {conversations.length === 0 ? (
            <div style={{ color: 'var(--text-dim)', fontSize: '0.82rem', textAlign: 'center', marginTop: '24px' }}>
              No previous chats
            </div>
          ) : (
            getGroupedConversations().map(([groupTitle, convList]) => (
              <div key={groupTitle} className="history-group">
                <div className="history-group-header">{groupTitle}</div>
                {convList.map((c) => {
                  const isActive = currentConvId === c.id;
                  const isMenuOpen = activeMenuId === c.id;
                  const isPinned = pinnedIds.includes(c.id);
                  const displayTitle = cleanTitle(c.title);
                  return (
                    <div
                      key={c.id}
                      onClick={() => handleSelectConversation(c.id)}
                      className={`history-item ${isActive ? 'active' : ''}`}
                      title={displayTitle}
                    >
                      <span className="history-title">{displayTitle}</span>
                      {isPinned && <Pin size={12} className="history-pin-badge" />}
                      <div className="history-action-container" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          className={`history-action-btn ${(isActive || isMenuOpen) ? 'force-visible' : ''}`}
                          title="Options"
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveMenuId(activeMenuId === c.id ? null : c.id);
                          }}
                        >
                          <MoreHorizontal size={15} />
                        </button>
                        {isMenuOpen && (
                          <div className="history-dropdown-menu">
                            <button
                              type="button"
                              className="history-dropdown-item"
                              onClick={(e) => handleTogglePin(e, c.id)}
                            >
                              <Pin size={13} style={isPinned ? { fill: 'currentColor' } : {}} />
                              <span>{isPinned ? 'Unpin' : 'Pin'}</span>
                            </button>
                            <button
                              type="button"
                              className="history-dropdown-item danger"
                              onClick={(e) => {
                                handleDeleteConversation(e, c.id);
                                setActiveMenuId(null);
                              }}
                            >
                              <Trash2 size={13} />
                              <span>Delete</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
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
            <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.9rem' }}>
              Ask any question about company policies below to start a new chat.
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
