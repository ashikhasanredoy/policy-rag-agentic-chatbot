import React from 'react';
import { ShieldCheck, HelpCircle, CheckCircle2 } from 'lucide-react';

export default function Navbar({ onOpenHelp }) {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <div className="nav-brand">
          <div className="brand-icon">
            <ShieldCheck size={19} />
          </div>
          <div className="brand-text">
            <span className="brand-title">PolicyAI</span>
            <span className="brand-badge">Enterprise</span>
          </div>
        </div>

        <div className="nav-status-pill">
          <span className="status-dot-pulse"></span>
          <span>8 Verified Policies</span>
        </div>
      </div>

      <div className="nav-links">
        <button onClick={onOpenHelp} className="nav-help-btn" title="View Indexed Policies and System Information">
          <HelpCircle size={15} />
          <span>Policy Catalog</span>
        </button>
        <div className="nav-user-chip">
          <div className="user-avatar-small">AR</div>
          <div className="user-info-text">
            <span className="user-name">Alex Rivera</span>
            <span className="user-role">Staff Engineer</span>
          </div>
        </div>
      </div>
    </nav>
  );
}

