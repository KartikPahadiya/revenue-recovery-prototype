import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export default function SubmitForm() {
  const [form, setForm] = useState({
    customer_name: '',
    amount: '',
    payment_method: 'card',
    failure_reason: 'insufficient_funds',
    leak_type: 'failed_payment',
  })
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/submit-transaction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, amount: parseFloat(form.amount) }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setSubmitted(true)
    } catch (err) {
      setError('Could not submit — make sure your phone is on the same WiFi as the host laptop.')
    }
  }

  if (submitted) {
    return (
      <div className="submit-wrap">
        <h2>Added ✅</h2>
        <p>Your test transaction will be included in the next batch run.</p>
        <button onClick={() => { setSubmitted(false); setForm({ ...form, customer_name: '', amount: '' }) }}>
          Add another
        </button>
      </div>
    )
  }

  return (
    <div className="submit-wrap">
      <h2>Add a test transaction</h2>
      <form onSubmit={handleSubmit}>
        <label>Customer name
          <input name="customer_name" value={form.customer_name} onChange={handleChange} required />
        </label>
        <label>Amount (₹)
          <input name="amount" type="number" step="0.01" min="1" value={form.amount} onChange={handleChange} required />
        </label>
        <label>Payment method
          <select name="payment_method" value={form.payment_method} onChange={handleChange}>
            <option value="card">Card</option>
            <option value="upi">UPI</option>
            <option value="netbanking">Netbanking</option>
            <option value="wallet">Wallet</option>
          </select>
        </label>
        <label>Failure reason
          <select name="failure_reason" value={form.failure_reason} onChange={handleChange}>
            <option value="insufficient_funds">Insufficient funds</option>
            <option value="card_expired">Card expired</option>
            <option value="bank_server_down">Bank server down</option>
            <option value="otp_timeout">OTP timeout</option>
            <option value="mandate_expired">Mandate expired</option>
          </select>
        </label>
        <label>Type
          <select name="leak_type" value={form.leak_type} onChange={handleChange}>
            <option value="failed_payment">Failed payment</option>
            <option value="failed_subscription">Failed subscription</option>
            <option value="overdue_invoice">Overdue invoice</option>
          </select>
        </label>
        {error && <p className="form-error">{error}</p>}
        <button type="submit">Submit</button>
      </form>
    </div>
  )
}
