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
  const [reason, setReason] = useState('')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

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

  const abandonCart = async () => {
    if (cart.length === 0) {
      setStatus({ error: 'Cart is empty. Add some items first!' })
      return
    }
    if (!customerName.trim()) {
      setStatus({ error: 'Enter your name first.' })
      return
    }
    if (!reason) {
      setStatus({ error: 'Please select a reason for leaving.' })
      return
    }

    setLoading(true)
    setStatus(null)

    try {
      const res = await fetch('/api/abandon-cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          customer_email: customerEmail || `${customerName.toLowerCase().replace(/\s/g, '')}@demo.com`,
          items: cartItemsText,
          cart_value: cartTotal,
          reason: reason,
        }),
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setStatus({
          success: true,
          message: `Cart abandoned! The AI agent will now work on recovering it.`,
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
          Add items to cart, then <strong>abandon it with a reason</strong> to trigger the AI recovery agent.
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
              placeholder="Email (optional)"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
            />
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              <option value="">Why are you leaving? *</option>
              {ABANDON_REASONS.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <button className="abandon-btn" onClick={abandonCart} disabled={loading || cart.length === 0}>
            {loading ? 'Abandoning...' : '💨 Abandon Cart (Trigger AI)'}
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
