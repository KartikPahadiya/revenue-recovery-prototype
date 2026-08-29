export default function RecoveryStats({ result }) {
  const { total_at_risk, total_recovered, recovery_rate, escalated_count } = result
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <span className="stat-label">Total at Risk</span>
        <span className="stat-value">₹{total_at_risk.toLocaleString()}</span>
      </div>
      <div className="stat-card highlight">
        <span className="stat-label">Total Recovered</span>
        <span className="stat-value">₹{total_recovered.toLocaleString()}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Recovery Rate</span>
        <span className="stat-value">{(recovery_rate * 100).toFixed(1)}%</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Escalated to Human</span>
        <span className="stat-value">{escalated_count}</span>
      </div>
    </div>
  )
}
