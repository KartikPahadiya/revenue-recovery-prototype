# AI-Powered Revenue Recovery Agent

An AI-powered revenue recovery system for identifying and recovering revenue lost through failed payments, checkout abandonment, failed subscriptions, and overdue B2B invoices.

The system combines transaction context, customer history, recovery prioritization, deterministic business policies, and LLM-assisted reasoning to select and execute an appropriate recovery strategy.

AI is used for contextual reasoning, failure diagnosis, negotiation assistance, and personalized communication. Consequential financial decisions such as discounts, retries, contact limits, and escalation remain controlled by deterministic business rules.

> **The right recovery action, for the right customer, under the right business guardrails.**

---

## Project Walkthrough

Watch the complete project walkthrough:

https://youtu.be/JY0XGNna_rY

The walkthrough demonstrates:

- Running the recovery pipeline on sample transactions
- Customer profiling and segmentation
- Segment-aware recovery strategies
- Manual abandoned-cart submission
- End-to-end pipeline execution
- Personalized recovery communication
- SendGrid email delivery
- Razorpay test-mode payment recovery
- Explainable audit trails

---

## Problem

Digital businesses lose revenue through several common scenarios:

- Failed payments caused by insufficient funds, expired cards, or bank issues
- Checkout abandonment
- Failed subscription payments
- Overdue B2B invoices

Traditional recovery systems commonly apply generic rules such as:

```text
Payment failed -> Retry
Cart abandoned -> Send reminder
Invoice overdue -> Send email
```

This approach ignores customer context.

A loyal high-value customer, a price-sensitive customer, and a customer who has already received multiple recovery messages should not necessarily receive the same intervention.

---

## Solution

The Revenue Recovery Agent processes each revenue-loss opportunity through a customer-aware recovery pipeline.

For every transaction, the system:

1. Detects revenue at risk
2. Diagnoses the failure
3. Builds the customer profile
4. Determines the customer segment
5. Prioritizes the recovery opportunity
6. Selects a policy-safe recovery strategy
7. Handles bounded negotiation where applicable
8. Personalizes the intervention
9. Executes the approved recovery action
10. Creates an explainable audit trail

The central design principle is:

> **AI provides contextual intelligence. Deterministic policies retain control over consequential business decisions.**

---

## Recovery Pipeline

```text
Revenue Event
     |
     v
   Detect
     |
     v
  Diagnose
     |
     v
Customer Profile
     |
     v
Customer Segment
     |
     v
  Allocate
     |
     v
   Decide
     |
     v
 Negotiate
     |
     v
Personalize
     |
     v
  Execute
     |
     v
Audit Trail
```

### 1. Detect

Identifies transactions where revenue is currently at risk.

Supported scenarios include:

- Checkout abandonment
- Failed payment
- Failed subscription
- Overdue invoice

### 2. Diagnose

The diagnosis stage analyzes transaction context and determines the likely failure category.

Examples include:

- Bank issue
- Customer issue
- Temporary failure
- Fraud or suspicious activity

LLM-based diagnosis is supported through Groq or Ollama. Deterministic fraud signals can override uncertain model output where required.

### 3. Customer Profile

The system builds customer context from historical behavior.

Profile information can include:

- Historical revenue
- Completed orders
- Abandoned carts
- Previous recoveries
- Recovery response history
- Recent contact frequency
- Transaction history

This allows the recovery system to consider the customer relationship rather than treating each transaction as an isolated event.

### 4. Customer Segment

Customer profiles are mapped to explainable behavioral segments.

Supported segments include:

- `HIGH_VALUE`
- `LOYAL`
- `PRICE_SENSITIVE`
- `AT_RISK`
- `RECOVERY_RESPONSIVE`
- `NEW`
- `STANDARD`

Behavioral traits can additionally include:

- `RECOVERY_RESPONSIVE`
- `DISCOUNT_GUARDED`
- `CONTACT_LIMITED`

The system records the reason behind the assigned segment for auditability.

### 5. Allocate

The allocator prioritizes recovery opportunities using expected recovery value.

Factors can include:

- Amount at risk
- Probability of recovery
- Intervention cost
- Customer value
- Customer segment

This allows recovery effort to be directed toward opportunities with greater expected value.

### 6. Decide

The deterministic policy engine selects which recovery actions are permitted.

Possible actions include:

- Retry payment
- Send reminder
- Send discount code
- Notify customer
- Negotiate invoice
- Escalate to human
- Do not contact

Policies enforce constraints such as:

- Discount limits
- Contact-frequency limits
- High-value approval requirements
- Fraud restrictions
- Customer-segment-specific treatment
- Transaction-specific recovery rules

This layer is intentionally deterministic and does not delegate financial authorization to the LLM.

### 7. Negotiate

High-value overdue invoices can enter a bounded negotiation workflow.

The LLM can assist with generating negotiation content, while deterministic rules constrain:

- Maximum discounts
- Installment options
- Approval requirements

Sensitive high-value cases can be routed for human approval.

### 8. Personalize

After a recovery strategy has been approved, the personalization stage receives:

- Transaction context
- Failure diagnosis
- Customer profile
- Customer segment
- Approved recovery action

The LLM uses this information to generate communication appropriate for the customer and recovery situation.

Personalization therefore goes beyond inserting a customer's name into a template. Customer intelligence influences both the recovery strategy and the resulting communication.

### 9. Execute

Execution depends on the transaction source.

**Sample transactions**

Sample-data recovery outcomes are simulated to safely demonstrate the complete pipeline.

**User-submitted transactions**

The system can perform real demo integrations including:

- SendGrid recovery email delivery
- On-demand Razorpay payment paths
- Execution result recording

### 10. Audit Trail

Each recovery decision produces an explainable audit record.

The dashboard exposes information such as:

- Transaction context
- Failure diagnosis
- Customer segment
- Segment reason
- Expected recovery score
- Selected action
- Policy decision
- Execution mode
- Execution result

This provides visibility into how and why the agent selected a particular intervention.

---

## Customer Intelligence

Customer intelligence is a key component of the recovery strategy.

Consider two customers who both abandon a similar-value shopping cart.

### High-Value Customer

Historical signals:

```text
High historical revenue
Multiple successful purchases
Low discount dependency
```

Potential recovery strategy:

```text
Send reminder
Protect margin
Avoid unnecessary discount
```

### Price-Sensitive Customer

Historical signals:

```text
Previous response to incentives
Higher abandonment behavior
Price-sensitive history
```

Potential recovery strategy:

```text
Apply policy-approved incentive
Generate personalized recovery communication
```

The transaction type may be similar, but customer context changes the recovery strategy.

---

## Policy Guardrails

The system deliberately separates probabilistic AI reasoning from deterministic financial authorization.

| LLM / AI Layer | Deterministic Policy Layer |
|---|---|
| Diagnose contextual failures | Authorize recovery actions |
| Understand transaction context | Enforce discount limits |
| Generate personalized communication | Enforce contact limits |
| Assist with negotiation wording | Require human approval |
| Interpret customer context | Block unsafe recovery actions |

The architecture follows:

```text
Probabilistic AI
       |
       v
Deterministic Business Policy
       |
       v
Approved Execution
```

The LLM does not have unrestricted control over consequential financial operations.

---

## Recovery Strategies by Customer Context

The sample dataset contains curated scenarios for demonstrating different recovery behaviors.

| Customer Context | Example Recovery Behavior |
|---|---|
| High-value customer | Protect margin and avoid unnecessary discounts |
| Price-sensitive customer | Apply a bounded, policy-approved incentive |
| At-risk customer | Contact protection or do-not-touch |
| New customer | Gentle recovery reminder |
| Loyal customer | Retry strategy for temporary or bank failures |
| High-value B2B invoice | Negotiation with human approval |
| Subscription customer | Adaptive dunning strategy |
| Fraud-like transaction | Block automated recovery |

These scenarios demonstrate that recovery strategy depends on both transaction context and customer history.

---

## Real Recovery Email

For manually submitted transactions, the system can send recovery communication through SendGrid.

Depending on the approved strategy, the message may contain:

- Personalized recovery content
- Transaction or cart context
- Approved incentive
- Discount code
- Call to action
- Payment recovery link

Sample dataset execution remains simulated.

---

## Razorpay Payment Recovery

Razorpay payment links are generated on demand rather than during batch processing.

```text
Recovery Email
      |
      v
Customer selects "Pay Now"
      |
      v
/api/pay/{txn_id}
      |
      v
Razorpay API
      |
      v
Test-Mode Checkout
```

This approach:

- Avoids unnecessary Razorpay API calls
- Prevents creation of unused payment links
- Creates a payment path only when the customer expresses payment intent
- Keeps batch execution lightweight

---

## FreshKart Demo Store

The project includes a demo commerce interface for creating realistic recovery scenarios.

Supported functionality includes:

- Product catalog
- Add-to-cart
- Quantity management
- Cart total
- Customer information
- Checkout-abandonment reasons
- Failed-payment scenarios
- Subscription scenarios
- Overdue-invoice scenarios

A manually submitted scenario becomes a new revenue recovery opportunity that can be processed through the same recovery pipeline.

---

## Recovery Dashboard

The dashboard provides visibility into both sample and manually submitted transactions.

It includes:

- Total revenue at risk
- Recovered revenue
- Recovery rate
- Real emails sent
- On-demand payment links
- Recovery action distribution
- Transaction results
- Customer segments
- Segment explanations
- Recovery scores
- Pipeline progress
- Expandable audit trails

---

## Architecture

```text
+-------------------------------------------------------------+
|                    React + Vite Frontend                    |
|                                                             |
|  FreshKart Store     Recovery Dashboard       Audit Trail   |
+-----------------------------+-------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                       FastAPI Backend                       |
|                                                             |
|                    LangGraph Workflow                       |
|                                                             |
| Detect -> Diagnose -> Profile -> Segment -> Allocate        |
|                                      |                      |
|                                      v                      |
| Decide -> Negotiate -> Personalize -> Execute -> Audit      |
|                                                             |
+-------------------------------------------------------------+
| Customer Repository | Policy Engine | LLM Client            |
+-------------------------------------------------------------+
|              SendGrid             Razorpay                  |
+-------------------------------------------------------------+
```

---

## Technology Stack

### Backend

- Python
- FastAPI
- LangGraph
- Pydantic
- SendGrid
- Razorpay REST API

### Frontend

- React
- Vite
- Recharts
- React Router

### AI Layer

- Groq or Ollama
- LLM-based failure diagnosis
- Customer-aware personalization
- Bounded negotiation assistance

### Decision Intelligence

- Deterministic policy engine
- Customer profiling
- Explainable customer segmentation
- Expected-value recovery allocation
- Contact-frequency protection
- Segment-aware strategy selection
- Human approval gates
- Adaptive subscription recovery strategy selection

---

## Project Structure

```text
backend/
  app/
    agents/
      detector_agent.py
      diagnosis_agent.py
      customer_profile_agent.py
      customer_segment_agent.py
      allocator.py
      policy_engine.py
      negotiation_agent.py
      personalization_agent.py
      executor.py
      orchestrator.py

    customer/
      profile.py
      repository.py

    api/
      routes.py

    data/
      transactions.csv
      customer_profiles.json
      user_submissions.json

    utils/
      llm_client.py
      razorpay_client.py
      sendgrid_client.py

    main.py

frontend/
  src/
    components/
      AbandonedCartDemo.jsx
      Dashboard.jsx
      CustomerProfile.jsx
      RecoveryStats.jsx
      TransactionTable.jsx
      AuditTrail.jsx
      AllocationChart.jsx
      PipelineTracker.jsx

    api/
      client.js

    App.jsx
```

---

## Demo Flow

### Sample Dataset

1. Open the recovery dashboard.
2. Select **Sample Data**.
3. Select **Run on Sample Data**.
4. The transactions are processed through the recovery pipeline.
5. Review customer segments, recovery strategies, expected recovery values, and simulated outcomes.
6. Inspect individual audit records for detailed decision information.

### Manual End-to-End Recovery

1. Open the FreshKart demo store.
2. Add products to the cart.
3. Enter customer information.
4. Select the recovery scenario.
5. Submit the transaction.
6. Open the dashboard.
7. Switch to **Submitted Data**.
8. Run the recovery pipeline.
9. Review the generated customer profile and segment.
10. Review the selected recovery strategy.
11. Check the recovery email delivered through SendGrid.
12. Select **Pay Now**.
13. Continue to the Razorpay test-mode checkout.
14. Review the resulting audit trail.

The end-to-end workflow can be summarized as:

```text
Revenue at Risk
      |
      v
Transaction and Customer Intelligence
      |
      v
Policy-Safe Recovery Strategy
      |
      v
Personalized Intervention
      |
      v
Recovery Execution
      |
      v
Explainable Audit
```

---

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env

uvicorn app.main:app --reload --port 8000
```

Linux/macOS:

```bash
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env

uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## Environment Variables

Create a `.env` file in the project root.

```env
# LLM provider
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model

# Local Ollama alternative
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434

# Razorpay test mode
RAZORPAY_KEY_ID=your_test_key
RAZORPAY_KEY_SECRET=your_test_secret

# SendGrid
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_SENDER=your_verified_sender

# Application
BASE_URL=http://localhost:8000
FRONTEND_ORIGIN=http://localhost:5173
```

Do not commit `.env` or real API credentials to the repository.

---

## Docker

The repository includes Docker configuration for building and running the application.

```bash
docker build -t revenue-recovery .
docker run -p 8000:8000 --env-file .env revenue-recovery
```

---

## Current Limitations

This repository is a hackathon prototype rather than a production payment platform.

Current limitations include:

- No authentication or RBAC
- Local JSON and CSV persistence
- Sample recovery outcomes are simulated
- No Razorpay webhook reconciliation
- No durable background job queue
- No multi-tenant merchant isolation
- No production-grade idempotency layer
- Broad CORS configuration for development
- LLM responses can fall back to deterministic defaults when malformed

---

## Production Roadmap

A production implementation would add:

- PostgreSQL persistence
- Merchant authentication and RBAC
- Razorpay webhook ingestion and payment reconciliation
- Idempotent recovery execution
- Background job processing
- Configurable merchant recovery policies
- Durable customer profiles
- Human approval workflow and UI
- Monitoring and observability
- Experiment tracking
- Stronger strategy-learning feedback loops

Razorpay webhook reconciliation could also feed successful recovery outcomes back into customer profiles and future strategy selection.

---

## Key Differentiator

A basic AI recovery workflow might look like:

```text
Transaction Failed
       |
       v
Generate AI Email
```

This project implements a broader decision workflow:

```text
Revenue at Risk
       |
       v
Diagnose Failure
       |
       v
Understand Customer
       |
       v
Estimate Recovery Value
       |
       v
Select Allowed Strategy
       |
       v
Apply Business Guardrails
       |
       v
Personalize Intervention
       |
       v
Execute
       |
       v
Audit Decision
```

The project is therefore not simply an AI email generator. It is an **AI-powered revenue recovery workflow combining customer intelligence, deterministic financial guardrails, recovery execution, and explainable decision-making.**

---

## Project Summary

Built an AI-powered revenue recovery agent using **FastAPI, LangGraph, React, LLM-based failure diagnosis, customer profiling and segmentation, expected-value recovery prioritization, deterministic financial policy guardrails, customer-aware personalization, SendGrid email delivery, Razorpay payment recovery, and explainable audit trails**.

---

## Walkthrough

https://youtu.be/JY0XGNna_rY
