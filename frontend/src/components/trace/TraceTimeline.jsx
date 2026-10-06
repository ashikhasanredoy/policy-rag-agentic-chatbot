import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react';

export default function TraceTimeline({ trace, latencyMs }) {
  const [open, setOpen] = useState(false);

  if (!trace) return null;

  return (
    <div className="trace-panel">
      <div className="trace-header" onClick={() => setOpen(!open)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={13} style={{ color: 'var(--primary-light)' }} />
          <span>Verification Trace</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '4px' }}>({latencyMs} ms)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {trace.conflict_detected && (
            <span style={{ fontSize: '0.7rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: '3px' }}>
              <AlertTriangle size={11} /> Conflict
            </span>
          )}
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      {open && (
        <div className="trace-steps">
          {/* 1. Relevance */}
          <div className="trace-step-item">
            <span>Relevance Filter</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{trace.relevance_score.toFixed(2)}</span>
              {trace.relevance_passed ? (
                <CheckCircle size={13} style={{ color: 'var(--success)' }} />
              ) : (
                <XCircle size={13} style={{ color: 'var(--danger)' }} />
              )}
            </div>
          </div>

          {/* 2. Answerability */}
          <div className="trace-step-item">
            <span>Answerability Guardrail</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{trace.answerability_score.toFixed(2)}</span>
              {trace.answerability_passed ? (
                <CheckCircle size={13} style={{ color: 'var(--success)' }} />
              ) : (
                <XCircle size={13} style={{ color: 'var(--danger)' }} />
              )}
            </div>
          </div>

          {/* 3. Faithfulness */}
          {trace.answerability_passed && (
            <div className="trace-step-item">
              <span>Faithfulness Verifier</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{trace.faithfulness_score.toFixed(2)}</span>
                {trace.faithfulness_passed ? (
                  <CheckCircle size={13} style={{ color: 'var(--success)' }} />
                ) : (
                  <XCircle size={13} style={{ color: 'var(--danger)' }} />
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
