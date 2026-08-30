const TXN_TYPE_LABELS = {
  checkout_abandonment: '🛒 Checkout Abandonment',
  failed_payment: '💳 Failed Payment',
  failed_subscription: '🔄 Failed Subscription',
  overdue_invoice: '📄 Overdue Invoice',
}

const TXN_TYPE_COLORS = {
  checkout_abandonment: '#d97706',
  failed_payment: '#ef4444',
  failed_subscription: '#8b5cf6',
  overdue_invoice: '#3b82f6',
}

export default function AuditTrail({ auditTrail }) {
  return (
    <div className="audit-card">
      <h3>Audit Trail (why each action was taken)</h3>
      {auditTrail.slice(0, 20).map((entry) => {
        const mode = entry.result?.execution_mode || 'simulated'
        const isRealEmail = mode === 'real_email_sent'
        const hasError = entry.result?.razorpay_error || entry.result?.email_error
        const txn = entry.txn || {}
        const txnType = txn.leak_type || 'unknown'
        const typeLabel = TXN_TYPE_LABELS[txnType] || txnType
        const typeColor = TXN_TYPE_COLORS[txnType] || '#a89f92'
        const failureReason = txn.failure_reason || txn.reason || ''
        const items = txn.items || ''
        const amount = txn.amount || 0

        return (
          <details key={entry.transaction_id}>
            <summary>
              {isRealEmail && <span className="badge real" style={{ marginRight: 8 }}>📧 EMAIL SENT</span>}
              {entry.transaction_id} → {entry.decision?.action} ({entry.result?.outcome})
            </summary>

            {/* Transaction Type & Details */}
            <div style={{ background: '#1a1a1a', padding: '12px', borderRadius: '8px', marginBottom: '10px', borderLeft: `4px solid ${typeColor}` }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: typeColor, marginBottom: '4px' }}>
                {typeLabel}
              </div>
              <div style={{ fontSize: '12px', color: '#a89f92' }}>
                {items && <div><strong>Items:</strong> {items}</div>}
                {amount > 0 && <div><strong>Amount:</strong> ₹{Number(amount).toLocaleString()}</div>}
                {failureReason && (
                  <div>
                    <strong>Reason:</strong>{' '}
                    {failureReason.includes(':') ? failureReason.split(':')[0] : failureReason}
                  </div>
                )}
              </div>
            </div>

            <p><strong>Diagnosis:</strong> {entry.diagnosis?.category} — {entry.diagnosis?.explanation}</p>
            <p><strong>Rule applied:</strong> {entry.decision?.rule_applied}</p>
            <p><strong>Priority score:</strong> {entry.decision?.priority_score}</p>
            <p><strong>Execution mode:</strong> {mode}</p>

            {entry.result?.payment_link_url && (
              <p style={{ background: '#1a3a1a', padding: '10px', borderRadius: '6px', marginTop: '8px' }}>
                <strong>✅ On-Demand Payment Link Ready:</strong><br />
                <span style={{ fontSize: '12px', color: '#a89f92' }}>
                  Clicking "Pay Now" in the email will generate a live Razorpay checkout link.
                </span><br />
                <a href={entry.result.payment_link_url} target="_blank" rel="noreferrer" style={{ color: '#4ade80', fontWeight: 600, fontSize: '12px' }}>
                  {entry.result.payment_link_url}
                </a>
              </p>
            )}

            {isRealEmail && (
              <p style={{ background: '#1a2a3a', padding: '10px', borderRadius: '6px', marginTop: '8px' }}>
                <strong>📧 Real Email Sent:</strong>
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
