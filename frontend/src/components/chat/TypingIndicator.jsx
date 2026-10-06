import React from 'react';
import { Bot } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="message-row ai">
      <div className="avatar ai">
        <Bot size={18} />
      </div>
      <div
        className="message-card"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '14px 18px',
          minHeight: '44px',
        }}
      >
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Thinking</span>
        <span className="dot-pulse" style={{ display: 'inline-flex', gap: '3px' }}>
          <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--text-dim)', display: 'inline-block' }}></span>
          <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--text-dim)', display: 'inline-block' }}></span>
          <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--text-dim)', display: 'inline-block' }}></span>
        </span>
      </div>
    </div>
  );
}
