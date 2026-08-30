import { useState } from 'react'

const PRODUCTS = [
  { id: 1, name: 'Amul Butter 500g', price: 275, emoji: '🧈' },
  { id: 2, name: 'Britannia Bread', price: 45, emoji: '🍞' },
  { id: 3, name: 'Tata Salt 1kg', price: 28, emoji: '🧂' },
  { id: 4, name: 'Maggi Noodles 4-pack', price: 72, emoji: '🍜' },
  { id: 5, name: 'Amul Milk 1L', price: 68, emoji: '🥛' },
  { id: 6, name: 'Lays Classic', price: 35, emoji: '🥔' },
  { id: 7, name: 'Cadbury Dairy Milk', price: 80, emoji: '🍫' },
  { id: 8, name: 'Tropicana Orange 1L', price: 110, emoji: '🍊' },
  { id: 9, name: 'Aashirvaad Atta 5kg', price: 285, emoji: '🌾' },
  { id: 10, name: 'Surf Excel 1kg', price: 195, emoji: '🧺' },
  { id: 11, name: 'Dove Shampoo', price: 165, emoji: '🧴' },
  { id: 12, name: 'Basmati Rice 5kg', price: 450, emoji: '🍚' },
]

const TXN_TYPES = [
  { value: 'checkout_abandonment', label: '🛒 Checkout abandonment' },
  { value: 'failed_payment', label: '💳 Failed payment' },
  { value: 'failed_subscription', label: '🔄 Failed subscription' },
  { value: 'overdue_invoice', label: '📄 Overdue invoice' },
]

const PAYMENT_METHODS = [
  { value: 'card', label: '💳 Card' },
  { value: 'netbanking', label: '🏦 Netbanking' },
  { value: 'upi', label: '📱 UPI' },
  { value: 'wallet', label: '👛 Wallet' },
]

const FAILURE_REASONS = [
  { value: 'insufficient_funds', label: '💸 Insufficient funds' },
  { value: 'card_expired', label: '🚫 Card expired' },
  { value: 'bank_server_down', label: '🏦 Bank server down' },
  { value: 'otp_timeout', label: '⏱️ OTP timeout' },
  { value: 'mandate_expired', label: '📋 Mandate expired' },
]

const ABANDON_REASONS = [
  { value: 'price_hesitation', label: '💰 Price too high / Hesitating' },
  { value: 'just_browsing', label: '👀 Just browsing / Not ready to buy' },
  { value: 'payment_issue', label: '💳 Payment method not available' },
  { value: 'distraction', label: '📱 Got distracted / Interrupted' },
  { value: 'shipping_cost', label: '🚚 Shipping cost too high' },
  { value: 'found_better', label: '🔍 Found better price elsewhere' },
]

export default function AbandonedCartDemo() {
  const [cart, setCart] = useState([])
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [txnType, setTxnType] = useState('checkout_abandonment')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [failureReason, setFailureReason] = useState('')
  const [abandonReason, setAbandonReason] = useState('')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const isCheckout = txnType === 'checkout_abandonment'

  const addToCart = (product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.id === product.id)
      if (existing) {
        return prev.map((item) =>
          item.id === product.id ? { ...item, qty: item.qty + 1 } : item
        )
      }
      return [...prev, { ...product, qty: 1 }]
    })
  }

  const removeFromCart = (productId) => {
    setCart((prev) => prev.filter((item) => item.id !== productId))
  }

  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.qty, 0)
  const cartItemsText = cart.map((item) => `${item.name} x${item.qty}`).join(', ')

  const submit = async () => {
    if (cart.length === 0) {
      setStatus({ error: 'Cart is empty. Add some items first!' })
      return
    }
    if (!customerName.trim()) {
      setStatus({ error: 'Enter your name first.' })
      return
    }
    if (!customerEmail.trim() || !customerEmail.includes('@')) {
      setStatus({ error: 'Enter a valid email address.' })
      return
    }
    if (isCheckout && !abandonReason) {
      setStatus({ error: 'Please select a reason for leaving.' })
      return
    }
    if (!isCheckout && !paymentMethod) {
      setStatus({ error: 'Please select a payment method.' })
      return
    }
    if (!isCheckout && !failureReason) {
      setStatus({ error: 'Please select a failure reason.' })
      return
    }

    setLoading(true)
    setStatus(null)

    try {
      let res, data
      if (isCheckout) {
        res = await fetch('/api/abandon-cart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customer_name: customerName,
            customer_email: customerEmail,
            items: cartItemsText,
            cart_value: cartTotal,
            reason: abandonReason,
          }),
        })
      } else {
        res = await fetch('/api/submit-transaction', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customer_name: customerName,
            customer_email: customerEmail,
            amount: cartTotal,
            payment_method: paymentMethod,
            failure_reason: failureReason,
            leak_type: txnType,
          }),
        })
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customer_name: customerName,
            amount: cartTotal,
            payment_method: paymentMethod,
            failure_reason: failureReason,
            leak_type: txnType,
          }),
        })
      }
      data = await res.json()
      if (data.status === 'ok') {
        setStatus({
          success: true,
          message: isCheckout
            ? `Cart abandoned! The AI agent will now work on recovering it.`
            : `${txnType.replace('_', ' ')} recorded! The AI agent will now work on recovering it.`,
          txnId: data.transaction_id,
        })
        setCart([])
      } else {
        setStatus({ error: data.detail || 'Something went wrong' })
      }
    } catch (err) {
      setStatus({ error: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="abandoned-cart-demo">
      <header className="cart-header">
        <h1>🛒 FreshKart — Demo Store</h1>
        <p className="cart-subtitle">
          Add items to cart, then <strong>submit a scenario</strong> to trigger the AI recovery agent.
        </p>
        <a href="/dashboard" className="dashboard-link">📊 Go to Recovery Dashboard</a>
      </header>

      <div className="cart-layout">
        <div className="product-grid">
          {PRODUCTS.map((product) => (
            <div key={product.id} className="product-card">
              <div className="product-emoji">{product.emoji}</div>
              <div className="product-name">{product.name}</div>
              <div className="product-price">₹{product.price}</div>
              <button className="add-btn" onClick={() => addToCart(product)}>+ Add</button>
            </div>
          ))}
        </div>

        <div className="cart-sidebar">
          <h3>Your Cart</h3>
          {cart.length === 0 ? (
            <p className="empty-cart">Cart is empty. Add some items!</p>
          ) : (
            <>
              {cart.map((item) => (
                <div key={item.id} className="cart-item">
                  <span>{item.emoji} {item.name} x{item.qty}</span>
                  <span>₹{item.price * item.qty}</span>
                  <button className="remove-btn" onClick={() => removeFromCart(item.id)}>×</button>
                </div>
              ))}
              <div className="cart-total"><strong>Total: ₹{cartTotal}</strong></div>
            </>
          )}

          <div className="customer-fields">
            <input
              type="text"
              placeholder="Your name *"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
            <input
              type="email"
              placeholder="Your email *"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
            />

            <select value={txnType} onChange={(e) => setTxnType(e.target.value)}>
              <option value="">Transaction type *</option>
              {TXN_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>

            {isCheckout ? (
              <select value={abandonReason} onChange={(e) => setAbandonReason(e.target.value)}>
                <option value="">Why are you leaving? *</option>
                {ABANDON_REASONS.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            ) : (
              <>
                <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                  <option value="">Payment method *</option>
                  {PAYMENT_METHODS.map((p) => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
                <select value={failureReason} onChange={(e) => setFailureReason(e.target.value)}>
                  <option value="">Failure reason *</option>
                  {FAILURE_REASONS.map((f) => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                  ))}
                </select>
              </>
            )}
          </div>

          <button className="abandon-btn" onClick={submit} disabled={loading || cart.length === 0}>
            {loading ? 'Submitting...' : isCheckout ? '💨 Abandon Cart (Trigger AI)' : '⚡ Submit Scenario (Trigger AI)'}
          </button>

          {status?.success && (
            <div className="status-success">
              ✅ {status.message}
              <div style={{ fontSize: '12px', color: '#a89f92', marginTop: 6 }}>
                Transaction ID: {status.txnId}
              </div>
              <div style={{ marginTop: 12 }}>
                <a href="/dashboard" className="back-link">→ See AI Recovery in Action</a>
              </div>
            </div>
          )}
          {status?.error && <div className="status-error">⚠ {status.error}</div>}
        </div>
      </div>
    </div>
  )
}
