import React from 'react';
import { ShieldCheck, HelpCircle } from 'lucide-react';

export default function Navbar({ onOpenHelp }) {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <div className="brand-icon">
          <ShieldCheck size={20} />
        </div>
        <span>PolicyAI</span>
      </div>

      <div className="nav-links">
        <button onClick={onOpenHelp} className="nav-help-btn" title="View Indexed Policies">
          <HelpCircle size={16} />
          <span>Help</span>
        </button>
      </div>
    </nav>
  );
}

