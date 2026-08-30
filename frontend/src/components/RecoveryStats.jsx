export default function RecoveryStats({ result }) {
  const { total_at_risk, total_recovered, recovery_rate, escalated_count, audit_trail } = result

  // Count transactions that have on-demand payment links (emails with /api/pay/{txn_id})
  const onDemandLinksCount = audit_trail?.filter(
    (entry) => entry.result?.payment_link_url
  ).length || 0

  const realEmailsCount = audit_trail?.filter(
    (entry) => entry.result?.execution_mode === 'real_email_sent'
  ).length || 0

  const simulatedCount = audit_trail?.filter(
    (entry) => !entry.result?.execution_mode || entry.result?.execution_mode === 'simulated'
  ).length || 0

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <span className="stat-label">Total at Risk</span>
        <span className="stat-value">₹{total_at_risk?.toLocaleString()}</span>
      </div>
      <div className="stat-card highlight">
        <span className="stat-label">Total Recovered</span>
        <span className="stat-value">₹{total_recovered?.toLocaleString()}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Recovery Rate</span>
        <span className="stat-value">{(recovery_rate * 100).toFixed(1)}%</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Escalated to Human</span>
        <span className="stat-value">{escalated_count}</span>
      </div>
      <div className="stat-card" style={{ border: '1px solid #4ade80' }}>
        <span className="stat-label">On-Demand Pay Links</span>
        <span className="stat-value" style={{ color: '#4ade80' }}>{onDemandLinksCount}</span>
        <span className="stat-label" style={{ fontSize: '10px' }}>Lazy-generated on click</span>
      </div>
      <div className="stat-card" style={{ border: '1px solid #60a5fa' }}>
        <span className="stat-label">Real Emails Sent</span>
        <span className="stat-value" style={{ color: '#60a5fa' }}>{realEmailsCount}</span>
        <span className="stat-label" style={{ fontSize: '10px' }}>{simulatedCount} simulated</span>
      </div>
    </div>
  )
}
