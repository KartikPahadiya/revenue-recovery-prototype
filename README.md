# Revenue Recovery Prototype

An AI-assisted revenue recovery system for failed payments, failed subscriptions, checkout abandonment, and overdue B2B invoices. Built with FastAPI, LangGraph, React, and real integrations (SendGrid + Razorpay).

The core idea: AI handles diagnosis and drafting, but **money decisions stay behind deterministic policy rules**. Real emails go out for user-submitted scenarios; sample data stays purely simulated.

---

## Problem

Digital businesses lose revenue when:
- Payments fail (insufficient funds, expired card, bank downtime)
- Subscription mandates expire
- Customers abandon checkout
- Invoices become overdue

These are usually handled with broad retry rules or manual follow-up — wasting effort, annoying customers, and missing high-value recovery opportunities.

---

## Solution: 7-Stage Recovery Pipeline

```
Transactions
    |
    v
Detect → Diagnose (LLM) → Allocate (expected value)
    |
    v
Decide (policy rules) → Negotiate (bounded offers)
    |
    v
Execute (real email + on-demand pay link) → Audit trail
```

1. **Detect** — Identify transactions with revenue at risk.
2. **Diagnose** — LLM classifies failure reason (bank issue, customer issue, temporary, fraud).
3. **Allocate** — Rank by expected recovery value: `(probability × amount) / intervention_cost`.
4. **Decide** — Deterministic policy gates decide the action (retry, notify, discount, negotiate, escalate, do-not-touch).
5. **Negotiate** — For high-value overdue invoices, draft bounded offers (discount % or installments) clamped by hard limits.
6. **Execute** — 
   - **Sample data**: Purely simulated outcomes
   - **User submissions**: Real SendGrid emails with on-demand Razorpay payment links
7. **Audit Trail** — Explain every decision with transaction context, diagnosis, rule, priority score, and execution mode.

---

## Key Features

### AI Agent
- Multi-stage LangGraph pipeline with conditional routing and halt gates
- LLM-based diagnosis (Groq / Ollama)
- Rule-based policy engine (pure Python, no LLM money decisions)
- Epsilon-greedy bandit for subscription dunning strategy selection
- Expected-value allocator for recovery prioritization
- Bounded negotiation agent with hard caps on discounts/installments

### Real Integrations
- **SendGrid** — Real recovery emails: cart reminders, discount codes, payment notifications, product recommendations
- **Razorpay** — On-demand test-mode payment links (created lazily when user clicks "Pay Now" in email)

### Demo Store (FreshKart)
- 12-product Blinkit-style store at `/`
- Add-to-cart, quantity management, cart total
- **Transaction type selector**: Checkout abandonment, Failed payment, Failed subscription, Overdue invoice
- **Payment method & failure reason** selectors for non-checkout scenarios
- Submit scenarios to trigger the AI recovery agent

### Dashboard
- Recovery metrics (Total at Risk, Recovered, Rate)
- On-Demand Pay Links counter
- Real Emails Sent counter
- Action allocation bar chart
- Transaction table with mode badges
- Expandable audit trail with transaction context (type, amount, items, reason)

---

## Why This Is Safe By Design

| What LLM Does | What Policy Engine Does |
|---|---|
| Classify failure causes | Decide retry / notify / discount / negotiate / escalate |
| Draft negotiation messages | Clamp offers to hard limits |
| Suggest offer terms | Authorize every money action |

The LLM **never** directly controls payment operations. The policy engine is plain Python and fully auditable.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                    │
│  ├── /           → FreshKart Demo Store                     │
│  ├── /dashboard  → Recovery Dashboard                       │
│  └── /submit     → Legacy QR submission page                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + LangGraph)                              │
│  ├── /api/abandon-cart     → Store checkout abandonment     │
│  ├── /api/submit-transaction → Failed payment / sub / invoice│
│  ├── /api/run-batch        → Execute recovery pipeline      │
│  ├── /api/pay/{txn_id}     → On-demand Razorpay link        │
│  └── /api/test-razorpay    → Connectivity debug             │
│                                                             │
│  Agents: detect → diagnose → allocate → decide → negotiate  │
│          → execute → build_audit_trail                      │
│                                                             │
│  Integrations: SendGrid (emails), Razorpay (payment links)  │
│  LLM: Groq (hosted) or Ollama (local)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

**Backend**
- Python 3.12
- FastAPI
- LangGraph
- Pydantic
- SendGrid (real emails)
- Razorpay REST API (direct HTTP, not SDK — avoids `pkg_resources` crash in slim containers)
- Groq or Ollama-compatible LLM

**Frontend**
- React
- Vite
- Recharts
- React Router (SPA routing)

**Deployment**
- Docker (multi-stage: Vite build → Python slim)
- Render (live at [revenue-recovery-prototype.onrender.com](https://revenue-recovery-prototype.onrender.com))

---

## Project Structure

```text
backend/
  app/
    agents/
      detector_agent.py      # Data quality and revenue leak detection
      diagnosis_agent.py     # LLM-based root cause classification
      allocator.py           # Expected-value recovery prioritization
      policy_engine.py       # Deterministic action rules + bandit
      negotiation_agent.py   # Bounded LLM-assisted invoice negotiation
      executor.py            # Simulated vs real execution (SendGrid + Razorpay)
      orchestrator.py        # LangGraph workflow
    api/routes.py            # FastAPI endpoints
    data/
      transactions.csv       # 415 sample synthetic transactions
      user_submissions.json  # Live demo submissions
    utils/
      llm_client.py          # Groq / Ollama client
      razorpay_client.py     # Direct HTTP Razorpay client
      sendgrid_client.py     # Real email templates
    main.py                  # FastAPI app with static SPA serving

frontend/
  src/
    components/
      AbandonedCartDemo.jsx  # FreshKart store + scenario submission
      Dashboard.jsx          # Recovery metrics + detailed report
      RecoveryStats.jsx      # Stat cards
      TransactionTable.jsx   # Transaction list
      AuditTrail.jsx         # Explainable decision log
      AllocationChart.jsx    # Action distribution chart
      PipelineTracker.jsx    # Live pipeline status
    api/client.js            # API wrapper
    App.jsx                  # Router + dashboard logic
```

---

## Demo Flow

### Option 1: Sample Data (Purely Simulated)
1. Open `/dashboard`
2. Click **"Sample Data"** tab
3. Click **"Run on Sample Data"**
4. See AI workflow, decisions, and simulated outcomes — no real emails or payment links

### Option 2: Live Demo (Real Emails + On-Demand Payment Links)
1. Go to `/` (FreshKart store)
2. Add items to cart
3. Fill name, email, choose transaction type:
   - **Checkout abandonment** → select reason, click "Abandon Cart"
   - **Failed payment / subscription / invoice** → select payment method + failure reason, click "Submit Scenario"
4. Go to `/dashboard`, switch to **"Submitted Data"** tab
5. Click **"Run on Submitted Data"**
6. Check your email — you'll receive a real recovery email with a "Pay Now" button
7. Click "Pay Now" → Razorpay payment link is created on-demand and you're redirected to checkout

---

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
# Edit .env with your keys
uvicorn app.main:app --reload --port 8000
```

On Windows PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env
# Edit .env with your keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## Environment Variables

Create a `.env` file in the project root.

```env
# LLM Provider (groq recommended for deployment)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

# Local alternative
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434

# Razorpay (test mode)
RAZORPAY_KEY_ID=your_razorpay_test_key
RAZORPAY_KEY_SECRET=your_razorpay_test_secret

# SendGrid (for real recovery emails)
SENDGRID_API_KEY=your_sendgrid_key
SENDGRID_SENDER=noreply@yourdomain.com

# Deployment
BASE_URL=https://your-app.onrender.com
FRONTEND_ORIGIN=http://localhost:5173
```

> **Note:** If SendGrid or Razorpay keys are missing, user submissions still run through the AI pipeline but fall back to simulation mode.

---

## Deployment

### Docker (Recommended)

The project includes a `Dockerfile` that builds the Vite frontend and serves it from FastAPI:

```bash
docker build -t revenue-recovery .
docker run -p 8000:8000 --env-file .env revenue-recovery
```

### Render

1. Connect GitHub repo to Render
2. Use **Docker** environment
3. Add environment variables in Render dashboard
4. Deploy — Render handles the build automatically

Live demo: [https://revenue-recovery-prototype.onrender.com](https://revenue-recovery-prototype.onrender.com)

---

## How On-Demand Payment Links Work

Instead of creating Razorpay links during batch execution (which hits rate limits), links are **lazily generated**:

1. Batch run sends email with `/api/pay/{txn_id}` URL
2. User clicks "Pay Now" in email
3. Server calls Razorpay API **once** → creates live `rzp.io` link
4. User is immediately redirected to Razorpay checkout

This means:
- No batch-time rate limits
- Links only created when a real user intends to pay
- Zero unnecessary API calls

---

## Current Limitations

This is a hackathon prototype, not production-ready.

- No authentication or RBAC
- Demo data stored in local files (not a database)
- Recovery outcomes for sample data are simulated
- No webhook reconciliation for Razorpay payment status
- No durable job queue or idempotency layer
- No tenant isolation for multiple merchants
- Limited automated test coverage
- Broad CORS for local demo convenience

---

## What Would Make It Production-Ready

- PostgreSQL with proper schema
- Auth, merchant accounts, RBAC
- Razorpay webhook ingestion + payment reconciliation
- Idempotent execution (same transaction never recovered twice)
- Background job queue (Celery / RQ) for long batches
- Human approval workflow for high-value cases
- Per-merchant policy configuration
- Observability: logs, metrics, alerts
- Comprehensive tests for policy gates, LLM failures, Razorpay errors

---

## Resume Summary

Built an AI-powered revenue recovery system using **FastAPI**, **React**, **LangGraph**, **LLM-based diagnosis**, **deterministic policy guardrails**, **SendGrid real email delivery**, **Razorpay on-demand payment links**, and an **explainable audit dashboard** for failed payments, subscriptions, checkout abandonment, and overdue invoices.
