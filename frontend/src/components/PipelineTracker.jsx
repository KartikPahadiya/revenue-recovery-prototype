import { useEffect, useState } from 'react'

const STAGES = [
  { key: 'detect', label: 'Detect' },
  { key: 'diagnose', label: 'Diagnose' },
  { key: 'allocate', label: 'Allocate' },
  { key: 'decide', label: 'Decide' },
  { key: 'negotiate', label: 'Negotiate' },
  { key: 'personalize', label: 'Personalize' },   // NEW
  { key: 'execute', label: 'Execute' },
]

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api`

export default function PipelineTracker({ active }) {
  const [status, setStatus] = useState({ stage: 'idle', current: 0, total: 0, message: '' })

  useEffect(() => {
    if (!active) return
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/pipeline-status`)
        setStatus(await res.json())
      } catch { /* ignore transient errors while polling */ }
    }, 400)
    return () => clearInterval(poll)
  }, [active])

  if (!active) return null

  const activeIndex = STAGES.findIndex((s) => s.key === status.stage)

  return (
    <div className="pipeline-tracker">
      <div className="pipeline-stages">
        {STAGES.map((s, i) => (
          <div key={s.key} className={`pipeline-stage ${i === activeIndex ? 'active' : i < activeIndex ? 'done' : ''}`}>
            {s.label}
          </div>
        ))}
      </div>
      <div className="pipeline-message">
        {status.message}
        {status.total > 0 && ` — ${status.current}/${status.total}`}
      </div>
    </div>
  )
}