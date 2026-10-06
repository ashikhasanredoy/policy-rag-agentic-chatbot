import React, { useState } from 'react';
import { User, Copy, Check } from 'lucide-react';

export default function UserMessage({ message }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy text', e);
    }
  };

  return (
    <div className="message-row user">
      <div className="message-card user-card">
        <div className="user-message-text">{message.content}</div>
        <div className="message-actions user-actions">
          <button
            type="button"
            onClick={handleCopy}
            className="msg-action-btn user-copy-btn"
            title={copied ? 'Copied!' : 'Copy question'}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span style={{ fontSize: '0.7rem' }}>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>
      <div className="avatar user">
        <User size={18} />
      </div>
    </div>
  );
}
