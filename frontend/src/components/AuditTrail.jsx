// Expandable per-transaction "why" view -- this IS the explainability layer.
export default function AuditTrail({ auditTrail }) {
  return (
    <div className="audit-card">
      <h3>Audit Trail (why each action was taken)</h3>
      {auditTrail.slice(0, 20).map((entry) => {
        const isReal = entry.result?.execution_mode === 'real_razorpay_link'
        const hasError = entry.result?.razorpay_error
        return (
          <details key={entry.transaction_id}>
            <summary>
              {isReal && <span className="badge real" style={{ marginRight: 8 }}>🟢 REAL</span>}
              {entry.transaction_id} → {entry.decision?.action} ({entry.result?.outcome})
            </summary>
            <p><strong>Diagnosis:</strong> {entry.diagnosis?.category} — {entry.diagnosis?.explanation}</p>
            <p><strong>Rule applied:</strong> {entry.decision?.rule_applied}</p>
            <p><strong>Priority score:</strong> {entry.decision?.priority_score}</p>
            <p><strong>Execution mode:</strong> {entry.result?.execution_mode || 'simulated'}</p>
            {isReal && entry.result?.payment_link_url && (
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
            {hasError && (
              <p style={{ color: '#f87171', fontSize: '12px' }}>
                Razorpay error: {hasError}
              </p>
            )}
          </details>
        )
      })}
    </div>
  )
}
