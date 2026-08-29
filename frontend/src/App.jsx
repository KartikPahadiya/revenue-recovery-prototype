import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard.jsx'
import QrPanel from './components/QrPanel.jsx'
import SubmitForm from './components/SubmitForm.jsx'
import { runBatch, getSubmissionsCount, clearUserSubmissions } from './api/client.js'
import PipelineTracker from './components/PipelineTracker.jsx'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [source, setSource] = useState('sample') // 'sample' | 'user'
  const [submissionsCount, setSubmissionsCount] = useState(0)
  const isSubmitPage = window.location.pathname === '/submit'

  const refreshCount = async () => {
    try {
      const data = await getSubmissionsCount()
      setSubmissionsCount(data.count)
    } catch {
      // non-critical, ignore
    }
  }

  useEffect(() => {
    if (!isSubmitPage) {
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
      console.error('run-batch failed:', err)
      setError(
        err.message === 'timeout'
          ? 'Request timed out. Check the backend terminal for a [run-batch] log line.'
          : `Could not reach backend: ${err.message}.`
      )
    } finally {
      setLoading(false)
    }
  }

  const handleClearSubmissions = async () => {
    await clearUserSubmissions()
    await refreshCount()
    setResult(null)
  }

  if (isSubmitPage) {
    return <SubmitForm />
  }

  return (
    <div className="app">
      <header>
        <h1>AI Revenue Recovery Agent</h1>
        <div className="header-right">
          <QrPanel />
        </div>
      </header>

      <div className="source-toggle-row">
        <button
          className={`source-btn ${source === 'sample' ? 'active' : ''}`}
          onClick={() => setSource('sample')}
        >
          Sample Data (415)
        </button>
        <button
          className={`source-btn ${source === 'user' ? 'active' : ''}`}
          onClick={() => setSource('user')}
        >
          Submitted Data ({submissionsCount})
        </button>
        {source === 'user' && submissionsCount > 0 && (
          <button className="clear-btn" onClick={handleClearSubmissions}>
            Clear submissions
          </button>
        )}
        <button className="run-btn" onClick={handleRun} disabled={loading}>
          {loading ? 'Running recovery batch...' : `Run on ${source === 'sample' ? 'Sample' : 'Submitted'} Data`}
        </button>
      </div>
      <PipelineTracker active={loading} />
      {error && <div className="halt-banner">⚠ {error}</div>}

      {result?.halted && (
        <div className="halt-banner">⚠ Pipeline halted: {result.halt_reason}</div>
      )}

      {result && !result.halted && <Dashboard result={result} />}
    </div>
  )
}
