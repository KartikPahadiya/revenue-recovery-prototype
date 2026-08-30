// Expandable per-transaction "why" view -- this IS the explainability layer.
export default function AuditTrail({ auditTrail }) {
  return (
    <div className="audit-card">
      <h3>Audit Trail (why each action was taken)</h3>
      {auditTrail.slice(0, 20).map((entry) => {
        const mode = entry.result?.execution_mode || 'simulated'
        const isBoth = mode === 'real_link+email'
        const isRealLink = mode === 'real_razorpay_link' || isBoth
        const isRealEmail = mode === 'real_email_sent' || isBoth
        const hasError = entry.result?.razorpay_error || entry.result?.email_error
        return (
          <details key={entry.transaction_id}>
            <summary>
              {isBoth && <span className="badge real" style={{ marginRight: 8 }}>🟢 LINK + 📧 EMAIL</span>}
              {!isBoth && isRealLink && <span className="badge real" style={{ marginRight: 8 }}>🟢 REAL LINK</span>}
              {!isBoth && isRealEmail && <span className="badge real" style={{ marginRight: 8 }}>📧 EMAIL SENT</span>}
              {entry.transaction_id} → {entry.decision?.action} ({entry.result?.outcome})
            </summary>
            <p><strong>Diagnosis:</strong> {entry.diagnosis?.category} — {entry.diagnosis?.explanation}</p>
            <p><strong>Rule applied:</strong> {entry.decision?.rule_applied}</p>
            <p><strong>Priority score:</strong> {entry.decision?.priority_score}</p>
            <p><strong>Execution mode:</strong> {mode}</p>
            
            {isRealLink && entry.result?.payment_link_url && (
              <p style={{ background: '#1a3a1a', padding: '10px', borderRadius: '6px', marginTop: '8px' }}>
                <strong>✅ Real Razorpay Payment Link Created:</strong><br />
                <a href={entry.result.payment_link_url} target="_blank" rel="noreferrer" style={{ color: '#4ade80', fontWeight: 600 }}>
                  {entry.result.payment_link_url}
                </a>
                <br />
                <span style={{ fontSize: '12px', color: '#a89f92' }}>
                  Link ID: {entry.result?.payment_link_id}
                </span>
              </p>
            )}
            
            {isRealEmail && (
              <p style={{ background: '#1a2a3a', padding: '10px', borderRadius: '6px', marginTop: '8px' }}>
                <strong>📧 Real Email Sent{isBoth ? ' (with payment link above)' : ''}:</strong>
                {entry.result?.discount_code && (
                  <div style={{ marginTop: '6px', fontSize: '14px' }}>
                    Discount Code: <strong style={{ color: '#4ade80' }}>{entry.result.discount_code}</strong>
                  </div>
                )}
              </p>
            )}
            
            {hasError && (
              <p style={{ color: '#f87171', fontSize: '12px' }}>
                {entry.result?.razorpay_error && <>Razorpay: {entry.result.razorpay_error}<br /></>}
                {entry.result?.email_error && <>Email: {entry.result.email_error}</>}
              </p>
            )}
          </details>
        )
      })}
    </div>
  )
}
