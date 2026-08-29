import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard.jsx'
import ComparisonDashboard from './components/ComparisonDashboard.jsx'
import QrPanel from './components/QrPanel.jsx'
import SubmitForm from './components/SubmitForm.jsx'
import { runBatch, runComparison, getSubmissionsCount, clearUserSubmissions } from './api/client.js'
import PipelineTracker from './components/PipelineTracker.jsx'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [source, setSource] = useState('sample') // 'sample' | 'user'
  const [submissionsCount, setSubmissionsCount] = useState(0)
  const [mode, setMode] = useState('ai') // 'ai' | 'comparison'
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
      setMode('ai')
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

  const handleCompare = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await runComparison(source)
      setResult(data)
      setMode('comparison')
    } catch (err) {
      console.error('run-comparison failed:', err)
      setError(
        err.message === 'timeout'
          ? 'Request timed out. The comparison may take longer.'
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
        <button className="compare-btn" onClick={handleCompare} disabled={loading}>
          {loading ? 'Running comparison...' : '⚖️ Compare vs Baseline'}
        </button>
      </div>
      <PipelineTracker active={loading} />
      {error && <div className="halt-banner">⚠ {error}</div>}

      {result?.halted && (
        <div className="halt-banner">⚠ Pipeline halted: {result.halt_reason}</div>
      )}

      {result && !result.halted && mode === 'comparison' && (
        <ComparisonDashboard result={result} />
      )}

      {result && !result.halted && mode === 'ai' && <Dashboard result={result} />}
    </div>
  )
}
