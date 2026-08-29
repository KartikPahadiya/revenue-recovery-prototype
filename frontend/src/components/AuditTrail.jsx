// Expandable per-transaction "why" view -- this IS the explainability layer.
export default function AuditTrail({ auditTrail }) {
  return (
    <div className="audit-card">
      <h3>Audit Trail (why each action was taken)</h3>
      {auditTrail.slice(0, 20).map((entry) => (
        <details key={entry.transaction_id}>
          <summary>
            {entry.transaction_id} → {entry.decision?.action} ({entry.result?.outcome})
          </summary>
          <p><strong>Diagnosis:</strong> {entry.diagnosis?.category} — {entry.diagnosis?.explanation}</p>
          <p><strong>Rule applied:</strong> {entry.decision?.rule_applied}</p>
          <p><strong>Priority score:</strong> {entry.decision?.priority_score}</p>
          {entry.result?.payment_link_url && (
            <p>
              <strong>Real Razorpay payment link:</strong>{' '}
              <a href={entry.result.payment_link_url} target="_blank" rel="noreferrer">
                {entry.result.payment_link_url}
              </a>
            </p>
          )}
          
        </details>
      ))}
    </div>
  )
}
