# Revenue Recovery Prototype

An AI-assisted revenue recovery prototype for failed payments, failed subscriptions, and overdue B2B invoices. The project was built for a hackathon to show how payment businesses can identify revenue at risk, choose safe recovery actions, and explain every decision through an audit trail.

The core idea is simple: let AI help with diagnosis and drafting, but keep actual money-related decisions behind deterministic policy rules.

## Problem

Digital businesses lose revenue when payments fail, subscription mandates expire, customers abandon payment attempts, or invoices become overdue. These cases are usually handled with broad retry rules or manual follow-up, which can waste effort, annoy customers, and miss high-value recovery opportunities.

This prototype demonstrates a safer recovery workflow:

1. Detect transactions with revenue at risk.
2. Diagnose likely failure reason using an LLM.
3. Rank recovery opportunities by expected value.
4. Apply rule-based policy gates before any action.
5. Draft bounded negotiation offers for large invoices.
6. Execute simulated recovery actions or create Razorpay test-mode payment links.
7. Show an audit trail explaining every decision.

## Key Features

- Multi-stage recovery pipeline built with FastAPI and LangGraph.
- LLM-based failure diagnosis for payment/subscription/invoice issues.
- Rule-based policy engine that controls retries, customer notifications, escalation, and negotiation.
- Bounded negotiation logic with hard caps on discounts and installments.
- Expected-value allocation to prioritize the highest-impact recovery cases.
- Razorpay test-mode payment link integration.
- React dashboard showing recovery metrics, action allocation, and transaction-level audit logs.
- QR-based transaction submission flow for live hackathon demos.
- Synthetic dataset generation for realistic demo transactions.

## Why This Is Safe By Design

The LLM does not directly authorize money actions. It is used only for:

- Classifying likely failure causes.
- Drafting short negotiation messages.
- Suggesting offer terms that are clamped by hard-coded limits.

The policy engine is plain Python and is the only layer that decides whether to retry, notify, negotiate, escalate, or avoid action. This makes the system easier to audit and safer than a workflow where an LLM directly controls payment operations.

## Architecture

```text
Transactions
    |
    v
Detect data quality and revenue leaks
    |
    v
Diagnose failure reason with LLM
    |
    v
Allocate recovery priority by expected value
    |
    v
Apply deterministic policy rules
    |
    v
Draft bounded negotiation offers when needed
    |
    v
Execute simulated action or Razorpay test payment link
    |
    v
Audit trail and dashboard metrics
```

## Tech Stack

**Backend**

- Python
- FastAPI
- LangGraph
- Pydantic
- Pandas
- Razorpay Python SDK
- Groq or Ollama-compatible LLM provider

**Frontend**

- React
- Vite
- Recharts
- qrcode.react

## Project Structure

```text
backend/
  app/
    agents/
      detector_agent.py      # Data quality and revenue leak detection
      diagnosis_agent.py     # LLM-based root cause classification
      allocator.py           # Expected-value recovery prioritization
      policy_engine.py       # Deterministic action rules and guardrails
      negotiation_agent.py   # Bounded LLM-assisted invoice negotiation
      executor.py            # Simulated execution and Razorpay payment links
      orchestrator.py        # LangGraph workflow
    api/routes.py            # FastAPI endpoints
    data/
      generate_synthetic_data.py
      transactions.csv
    models/schemas.py
    utils/
      llm_client.py
      razorpay_client.py
    main.py
  tests/

frontend/
  src/
    components/
    api/client.js
    App.jsx
```

## Demo Flow

1. Start the backend.
2. Start the frontend.
3. Open the dashboard.
4. Run recovery on sample synthetic data.
5. Scan the QR code to submit a new test transaction from another device.
6. Run recovery on submitted data.
7. Inspect recovery metrics, action allocation, payment links, and audit trail.

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python -m app.data.generate_synthetic_data
uvicorn app.main:app --reload --port 8000
```

On Windows PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env
python -m app.data.generate_synthetic_data
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

The backend runs at:

```text
http://localhost:8000
```

## Environment Variables

Create a `.env` file in the project root using `.env.example`.

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434

RAZORPAY_KEY_ID=your_razorpay_test_key
RAZORPAY_KEY_SECRET=your_razorpay_test_secret

FRONTEND_ORIGIN=http://localhost:5173
```

If Razorpay keys are not configured, the pipeline still works in simulation mode.

## Deployment Notes

For a public demo, Dockerizing the app is the cleanest path because the project has both a backend and frontend. A single-container deployment can build the React frontend and serve it from FastAPI.

Hugging Face Spaces can work for a demo if you use Docker and a hosted LLM API key through Space secrets. Running Ollama directly inside a free Space is usually not a good choice because local LLMs need significant memory/CPU/GPU and model downloads can be slow or unreliable on free hardware.

Recommended demo deployment approach:

1. Build the React frontend.
2. Serve frontend static files from FastAPI.
3. Deploy as a Docker Space.
4. Put LLM and Razorpay test credentials in Hugging Face Space secrets.
5. Use Groq/Gemini/OpenRouter or another hosted provider instead of Ollama for the deployed demo.

## Current Limitations

This is a hackathon prototype, not a production-ready financial system.

Important production gaps:

- No authentication or role-based access control.
- Demo data is stored in local files instead of a database.
- Recovery outcomes are simulated unless verified through real payment events.
- No webhook reconciliation for actual Razorpay payment status.
- No durable job queue or idempotency layer for repeated batch runs.
- No tenant isolation for multiple merchants.
- Limited automated test coverage.
- Broad CORS settings for local demo convenience.

## What Would Make It Production-Ready

- PostgreSQL or another durable database.
- Auth, merchant accounts, and role-based permissions.
- Razorpay webhook ingestion and payment reconciliation.
- Idempotent execution so the same transaction is not recovered twice.
- Background job queue for long-running batches.
- Human approval workflow for high-value or uncertain cases.
- Policy configuration per merchant.
- Observability, logs, metrics, alerts, and retry handling.
- Stronger tests for policy gates, LLM failures, malformed data, and Razorpay failures.

## Resume Summary

Built an AI-powered revenue recovery prototype using FastAPI, React, LangGraph, LLM-based diagnosis, deterministic policy guardrails, Razorpay test-mode payment links, and an explainable audit dashboard for failed payments, subscriptions, and overdue invoices.

## License

MIT
