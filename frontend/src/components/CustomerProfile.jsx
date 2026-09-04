const SEGMENT_LABELS = {
  HIGH_VALUE: 'High value',
  PRICE_SENSITIVE: 'Price sensitive',
  AT_RISK: 'At risk',
  RECOVERY_RESPONSIVE: 'Recovery responsive',
  LOYAL: 'Loyal',
  NEW: 'New',
  STANDARD: 'Standard',
}

function money(value) {
  return `₹${Number(value || 0).toLocaleString()}`
}

export default function CustomerProfile({ auditTrail }) {
  const profiles = auditTrail
    .filter((entry) => entry.customer_profile?.customer_id)
    .reduce((acc, entry) => {
      const profile = entry.customer_profile
      if (!acc[profile.customer_id]) {
        acc[profile.customer_id] = {
          profile,
          segment: entry.customer_segment,
          segmentReason: entry.segment_reason,
          traits: entry.customer_traits || [],
          transactions: 0,
        }
      }
      acc[profile.customer_id].transactions += 1
      return acc
    }, {})

  const rows = Object.values(profiles).slice(0, 6)
  if (!rows.length) return null

  return (
    <section className="customer-profile-section">
      <div className="section-heading">
        <h3>Customer Intelligence</h3>
        <span>{rows.length} profiled customers</span>
      </div>
      <div className="customer-profile-grid">
        {rows.map(({ profile, segment, segmentReason, traits, transactions }) => (
          <article className="customer-profile-card" key={profile.customer_id}>
            <div className="customer-profile-top">
              <div>
                <h4>{profile.name || profile.customer_id}</h4>
                <p>{profile.email || profile.customer_id}</p>
              </div>
              <span className={`segment-chip segment-${segment}`}>{SEGMENT_LABELS[segment] || segment}</span>
            </div>
            <div className="customer-profile-metrics">
              <span><strong>{money(profile.historical_revenue || profile.lifetime_value)}</strong>Revenue</span>
              <span><strong>{profile.completed_orders || 0}</strong>Orders</span>
              <span><strong>{profile.successful_recoveries || 0}</strong>Recoveries</span>
              <span><strong>{profile.contacts_last_7_days || 0}</strong>Contacts 7d</span>
            </div>
            <p className="customer-profile-reason">
              {profile.abandoned_carts || 0} abandonments · {money(profile.total_at_risk)} at risk
            </p>
            {segmentReason && <p className="customer-profile-reason">{segmentReason}</p>}
            {traits?.length > 0 && <p className="customer-profile-reason">{traits.join(', ')}</p>}
            <div className="customer-profile-foot">
              {transactions} transaction{transactions === 1 ? '' : 's'} in this run
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
