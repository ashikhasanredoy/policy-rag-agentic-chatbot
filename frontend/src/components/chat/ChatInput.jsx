import React, { useState } from 'react';
import { Send } from 'lucide-react';

export default function ChatInput({ onSendMessage, disabled, inputRef }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSendMessage(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-input-wrapper">
      <form onSubmit={handleSubmit} className="input-container">
        <input
          ref={inputRef}
          type="text"
          className="chat-input-field"
          placeholder="Ask a question about company policies..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          autoFocus
        />
        <button type="submit" className="send-btn" disabled={!text.trim() || disabled}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
