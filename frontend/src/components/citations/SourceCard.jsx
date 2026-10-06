import React, { useState } from 'react';
import { FileText, Bookmark, ExternalLink } from 'lucide-react';

export default function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="source-card"
      onClick={() => setExpanded(!expanded)}
      title="Click to toggle text snippet"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
        <FileText size={14} style={{ color: 'var(--primary-light)', flexShrink: 0 }} />
        <span className="source-policy-name">{source.policy}</span>
      </div>
      <div className="source-meta">
        <span>§ {source.section}</span>
        <span>Page {source.page} • v{source.version}</span>
      </div>
      {expanded && source.text_snippet && (
        <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem', lineHeight: '1.4' }}>
          "{source.text_snippet}"
        </div>
      )}
    </div>
  );
}
