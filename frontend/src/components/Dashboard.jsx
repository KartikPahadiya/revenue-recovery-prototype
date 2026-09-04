import { useState } from 'react'
import RecoveryStats from './RecoveryStats.jsx'
import AllocationChart from './AllocationChart.jsx'
import TransactionTable from './TransactionTable.jsx'
import AuditTrail from './AuditTrail.jsx'
import CustomerProfile from './CustomerProfile.jsx'

export default function Dashboard({ result }) {
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div className="dashboard">
      <RecoveryStats result={result} />
      <CustomerProfile auditTrail={result.audit_trail} />
      <AllocationChart auditTrail={result.audit_trail} />

      <div className="detail-toggle-row">
        <button className="detail-toggle-btn" onClick={() => setShowDetails(!showDetails)}>
          {showDetails ? 'Hide Detailed Report' : 'View Detailed Report'}
        </button>
      </div>

      {showDetails && (
        <>
          <TransactionTable auditTrail={result.audit_trail} />
          <AuditTrail auditTrail={result.audit_trail} />
        </>
      )}
    </div>
  )
}
