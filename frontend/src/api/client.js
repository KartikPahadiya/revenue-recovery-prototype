const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function fetchWithTimeout(url, options = {}, timeoutMs = 60000) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { ...options, signal: controller.signal })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`)
    }
    return await res.json()
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('timeout')
    throw err
  } finally {
    clearTimeout(id)
  }
}

export async function fetchTransactions() {
  return fetchWithTimeout(`${BASE_URL}/transactions`)
}

export async function runBatch(source = 'sample', limit) {
  const params = new URLSearchParams({ source })
  if (limit) params.set('limit', limit)
  return fetchWithTimeout(`${BASE_URL}/run-batch?${params}`, { method: 'POST' }, 1200000)
}

export async function getSubmissionsCount() {
  return fetchWithTimeout(`${BASE_URL}/submissions-count`)
}

export async function clearUserSubmissions() {
  return fetchWithTimeout(`${BASE_URL}/user-submissions`, { method: 'DELETE' })
}

export async function runComparison(source = 'sample', limit) {
  const params = new URLSearchParams({ source })
  if (limit) params.set('limit', limit)
  return fetchWithTimeout(`${BASE_URL}/run-comparison?${params}`, { method: 'POST' }, 1200000)
}
  return fetchWithTimeout(`${BASE_URL}/user-submissions`, { method: 'DELETE' })
}
