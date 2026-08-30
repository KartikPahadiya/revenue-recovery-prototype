import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard.jsx'
import QrPanel from './components/QrPanel.jsx'
import SubmitForm from './components/SubmitForm.jsx'
import AbandonedCartDemo from './components/AbandonedCartDemo.jsx'
import { runBatch, getSubmissionsCount, clearUserSubmissions } from './api/client.js'
import PipelineTracker from './components/PipelineTracker.jsx'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [source, setSource] = useState('sample')
  const [submissionsCount, setSubmissionsCount] = useState(0)
  const path = window.location.pathname
  const isSubmitPage = path === '/submit'
  const isDashboard = path === '/dashboard'

  const refreshCount = async () => {
    try {
      const data = await getSubmissionsCount()
      setSubmissionsCount(data.count)
    } catch {}
  }

  useEffect(() => {
    if (isDashboard) {
      refreshCount()
      const interval = setInterval(refreshCount, 5000)
      return () => clearInterval(interval)
    }
  }, [])

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await runBatch(source)
      setResult(data)
    } catch (err) {
      setError(err.message === 'timeout' ? 'Request timed out.' : `Backend error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleClearSubmissions = async () => {
    await clearUserSubmissions()
    await refreshCount()
    setResult(null)
  }

  if (isSubmitPage) return <SubmitForm />
  if (isDashboard) {
    return (
      <div className="app">
        <header>
          <h1>AI Revenue Recovery Agent</h1>
          <div className="header-right">
            <a href="/" className="store-link">🛒 Back to Store</a>
            <QrPanel />
          </div>
        </header>
        <div className="source-toggle-row">
          <button className={`source-btn ${source === 'sample' ? 'active' : ''}`} onClick={() => setSource('sample')}>
            Sample Data (415)
          </button>
          <button className={`source-btn ${source === 'user' ? 'active' : ''}`} onClick={() => setSource('user')}>
            Submitted Data ({submissionsCount})
          </button>
          {source === 'user' && submissionsCount > 0 && (
            <button className="clear-btn" onClick={handleClearSubmissions}>Clear submissions</button>
          )}
          <button className="run-btn" onClick={handleRun} disabled={loading}>
            {loading ? 'Running...' : `Run on ${source === 'sample' ? 'Sample' : 'Submitted'} Data`}
          </button>
        </div>
        <PipelineTracker active={loading} />
        {error && <div className="halt-banner">⚠ {error}</div>}
        {result?.halted && <div className="halt-banner">⚠ Halted: {result.halt_reason}</div>}
        {result && !result.halted && <Dashboard result={result} />}
      </div>
    )
  }

  // Default: show the store
  return <AbandonedCartDemo />
}
