import React, { useState, useEffect } from 'react';
import { X, HelpCircle, FileText, Search, Shield, Briefcase, DollarSign, Laptop, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

const CATEGORY_ICONS = {
  HR: Briefcase,
  Finance: DollarSign,
  Security: Shield,
  IT: Laptop,
  Operations: FileText,
  Customer: FileText,
};

export default function HelpModal({ isOpen, onClose }) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadPolicies();
    }
  }, [isOpen]);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const res = await api.getPolicies();
      if (res.data) {
        setPolicies(res.data);
      }
    } catch (e) {
      console.error('Failed to load policies in help', e);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const filteredPolicies = policies.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.category && p.category.toLowerCase().includes(search.toLowerCase())) ||
    (p.department && p.department.toLowerCase().includes(search.toLowerCase())) ||
    (p.description && p.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="help-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="help-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="help-icon-badge">
              <HelpCircle size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>
                Policy Knowledge Base
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                Available policies indexed for question answering
              </p>
            </div>
          </div>
          <button onClick={onClose} className="modal-close-btn" title="Close">
            <X size={18} />
          </button>
        </div>

        {/* Search Input */}
        <div style={{ padding: '16px 20px 8px 20px' }}>
          <div className="help-search-box">
            <Search size={16} color="var(--text-dim)" />
            <input
              type="text"
              placeholder="Search policy name or topic..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="help-search-input"
              autoFocus
            />
          </div>
        </div>

        {/* Policy List */}
        <div className="help-policy-list">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
              Loading policies...
            </div>
          ) : filteredPolicies.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
              No matching policies found.
            </div>
          ) : (
            filteredPolicies.map((p) => {
              const IconComponent = CATEGORY_ICONS[p.category] || FileText;
              return (
                <div key={p.id} className="help-policy-card">
                  <div className="help-policy-icon">
                    <IconComponent size={18} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                      <span className="help-policy-name">{p.name}</span>
                      <span className="help-policy-category">{p.category}</span>
                      {p.version && <span className="help-policy-version">v{p.version}</span>}
                    </div>
                    <p className="help-policy-desc">{p.description || 'Company guidelines and compliance procedures.'}</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      <span>Dept: {p.department}</span>
                      {p.document_id && <span>ID: {p.document_id}</span>}
                      {p.chunk_count > 0 && <span>• {p.chunk_count} indexed sections</span>}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="help-modal-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
            <CheckCircle2 size={14} color="var(--success)" />
            <span>Strict anti-hallucination: only verified facts from these policies are cited.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
