import React from 'react';
import { User } from 'lucide-react';

export default function UserMessage({ message }) {
  return (
    <div className="message-row user">
      <div className="message-card">
        {message.content}
      </div>
      <div className="avatar user">
        <User size={18} />
      </div>
    </div>
  );
}
