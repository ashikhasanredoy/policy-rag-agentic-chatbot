import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, ThumbsUp, ThumbsDown, BookmarkCheck, ChevronDown, ChevronUp } from 'lucide-react';
import SourceCard from '../citations/SourceCard';
import TraceTimeline from '../trace/TraceTimeline';
import { api } from '../../services/api';

export default function AIMessage({ message }) {
  const [feedbackGiven, setFeedbackGiven] = useState(null);
  const [showSources, setShowSources] = useState(false);

  const handleFeedback = async (rating) => {
    if (feedbackGiven || !message.id) return;
    try {
      await api.sendFeedback({ message_id: message.id, rating });
      setFeedbackGiven(rating);
    } catch (e) {
      console.error('Feedback failed', e);
    }
  };

  const isAnswerable = message.answerable !== false;

  return (
    <div className="message-row ai">
      <div className="avatar ai">
        <Bot size={18} />
      </div>
      <div className="message-card">
        {/* Message Content with Markdown & Point-wise rendering */}
        <div className="markdown-content">
          <ReactMarkdown>{message.content || ''}</ReactMarkdown>
        </div>

        {/* Citations Slide Toggle Button & Collapsible Content */}
        {isAnswerable && message.sources && message.sources.length > 0 && (
          <div className="citations-wrapper">
            <button
              type="button"
              className="sources-toggle-btn"
              onClick={() => setShowSources(!showSources)}
              title="Click to view/hide policy sources"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookmarkCheck size={14} style={{ color: 'var(--primary)' }} />
                <span className="sources-btn-label">Sources</span>
                <span className="sources-count-badge">
                  {message.sources.length}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                <span>{showSources ? 'Hide' : 'Show Sources'}</span>
                {showSources ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </div>
            </button>

            {showSources && (
              <div className="sources-slide-content">
                <div className="sources-grid">
                  {message.sources.map((src, idx) => (
                    <SourceCard key={idx} source={src} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Trace Timeline */}
        {message.trace && (
          <TraceTimeline trace={message.trace} latencyMs={message.latency_ms || 0} />
        )}

        {/* Minimal Feedback Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px', marginTop: '10px' }}>
          <button
            onClick={() => handleFeedback(5)}
            disabled={feedbackGiven !== null}
            style={{
              background: 'transparent',
              border: 'none',
              color: feedbackGiven === 5 ? 'var(--primary-light)' : 'var(--text-dim)',
              padding: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              borderRadius: 'var(--radius-sm)',
            }}
            title="Helpful"
          >
            <ThumbsUp size={13} />
          </button>
          <button
            onClick={() => handleFeedback(1)}
            disabled={feedbackGiven !== null}
            style={{
              background: 'transparent',
              border: 'none',
              color: feedbackGiven === 1 ? 'var(--danger)' : 'var(--text-dim)',
              padding: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              borderRadius: 'var(--radius-sm)',
            }}
            title="Unhelpful"
          >
            <ThumbsDown size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
