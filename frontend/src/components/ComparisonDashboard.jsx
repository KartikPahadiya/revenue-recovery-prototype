export default function ComparisonDashboard({ result }) {
  const ai = result.ai_agent
  const baseline = result.naive_baseline
  const comp = result.comparison

  return (
    <div className="comparison-dashboard">
      <h2>🧪 AI Agent vs. Naive Baseline</h2>
      <p className="comparison-summary">{comp.summary}</p>

      <div className="comparison-cards">
        <div className="card baseline-card">
          <h3>Naive Baseline (Retry-All)</h3>
          <div className="metric">
            <span className="metric-label">Recovery Rate</span>
            <span className="metric-value">{(baseline.recovery_rate * 100).toFixed(1)}%</span>
          </div>
          <div className="metric">
            <span className="metric-label">Total Recovered</span>
            <span className="metric-value">₹{baseline.total_recovered.toLocaleString()}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Transactions Retried</span>
            <span className="metric-value">{baseline.transactions_retried}</span>
          </div>
          <div className="metric danger">
            <span className="metric-label">Fraud Risk Retried</span>
            <span className="metric-value">{baseline.fraud_retried}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Has Negotiation</span>
            <span className="metric-value">{baseline.has_negotiation ? 'Yes' : 'No'}</span>
          </div>
        </div>

        <div className="card ai-card">
          <h3>🤖 AI Agent</h3>
          <div className="metric">
            <span className="metric-label">Recovery Rate</span>
            <span className="metric-value highlight">{(ai.recovery_rate * 100).toFixed(1)}%</span>
          </div>
          <div className="metric">
            <span className="metric-label">Total Recovered</span>
            <span className="metric-value highlight">₹{ai.total_recovered.toLocaleString()}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Escalated to Human</span>
            <span className="metric-value">{ai.escalated_count}</span>
          </div>
          <div className="metric safe">
            <span className="metric-label">Fraud Risk Blocked</span>
            <span className="metric-value">{ai.fraud_blocked ? 'Yes' : 'No'}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Has Negotiation</span>
            <span className="metric-value">{ai.has_negotiation ? 'Yes' : 'No'}</span>
          </div>
          {ai.real_razorpay_links > 0 && (
            <div className="metric">
              <span className="metric-label">Real Payment Links</span>
              <span className="metric-value">{ai.real_razorpay_links}</span>
            </div>
          )}
        </div>
      </div>

      <div className="comparison-insights">
        <h4>Key Insights</h4>
        <ul>
          <li>✅ AI recovered <strong>₹{comp.extra_recovered.toLocaleString()} more</strong> ({comp.extra_recovered_percent}% improvement)</li>
          <li>🛡️ AI prevented <strong>{comp.fraud_exposure_prevented} fraud-risk retries</strong> that the baseline blindly attempted</li>
          <li>🎯 AI escalated <strong>{comp.escalations_only_by_ai} cases</strong> to human review instead of wasting retries</li>
          <li>💬 AI used <strong>bounded negotiation</strong> for high-value invoices, something the baseline cannot do</li>
        </ul>
      </div>
    </div>
  )
}
