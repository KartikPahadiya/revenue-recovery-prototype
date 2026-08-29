export default function TransactionTable({ auditTrail }) {
  return (
    <div className="table-card">
      <h3>Transactions</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Category</th><th>Action</th><th>Outcome</th><th>Recovered</th><th>Mode</th>
          </tr>
        </thead>
        <tbody>
          {auditTrail.map((entry) => {
            const isReal = entry.result?.execution_mode === 'real_razorpay_link'
            return (
              <tr key={entry.transaction_id}>
                <td>{entry.transaction_id}</td>
                <td>{entry.diagnosis?.category}</td>
                <td>{entry.decision?.action}</td>
                <td className={entry.result?.outcome === 'recovered' ? 'ok' : ''}>
                  {entry.result?.outcome}
                </td>
                <td>₹{entry.result?.amount_recovered?.toLocaleString() || 0}</td>
                <td>
                  {isReal ? (
                    <span className="badge real">🟢 Real Link</span>
                  ) : (
                    <span className="badge sim">⚪ Simulated</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
