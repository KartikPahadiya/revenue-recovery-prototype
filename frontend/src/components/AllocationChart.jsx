import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

// Groups audit trail by action taken -> count, so judges can see at a
// glance how effort was allocated across strategies.
export default function AllocationChart({ auditTrail }) {
  const counts = {}
  auditTrail.forEach((entry) => {
    const action = entry.decision?.action || 'unknown'
    counts[action] = (counts[action] || 0) + 1
  })
  const data = Object.entries(counts).map(([action, count]) => ({ action, count }))

  return (
    <div className="chart-card">
      <h3>Actions Taken (Allocation)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <XAxis dataKey="action" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#d97706" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
