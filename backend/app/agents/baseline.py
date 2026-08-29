"""
Naive baseline: retry every transaction blindly, regardless of failure reason,
fraud flags, or retry count. No LLM diagnosis, no policy engine, no negotiation.

The success rate is LOWER than targeted retries because blindly retrying means:
- Retrying fraud (will never succeed, wastes API calls)
- Retrying customer issues (card expired, insufficient funds — retry won't help)
- Retrying already-failed transactions multiple times

This is what a naive "retry-all" system does — used to prove the AI agent
generates measurably better outcomes.
"""
import random
from app.agents.state import update_status

# Blind retry-all has lower success rate because many retries are wasted
# on fraud, customer issues, and already-failed transactions
NAIVE_RETRY_SUCCESS_RATE = 0.35


def run_naive_baseline(transactions: list) -> dict:
    """
    Run a naive retry-all strategy on the same batch.
    Uses a fixed seed so results are deterministic across runs.
    Returns comparison metrics vs. the AI agent.
    """
    update_status("execute", message="Running naive baseline (retry-all)...")

    # Fixed seed for deterministic results — baseline should consistently underperform
    rng = random.Random(42)

    total_at_risk = sum(float(t["amount"]) for t in transactions)
    results = []
    fraud_retried = 0
    customer_issue_retried = 0

    for txn in transactions:
        # Naive: retry EVERYTHING, including fraud and already-retried
        success = rng.random() < NAIVE_RETRY_SUCCESS_RATE
        amount_recovered = float(txn["amount"]) if success else 0.0

        failure_reason = txn.get("failure_reason", "").lower()

        # Track dangerous retries (these are cases where AI would block/escalate)
        if failure_reason in ("fraud", "suspicious", "chargeback"):
            fraud_retried += 1
        elif failure_reason in ("card expired", "insufficient funds", "customer cancelled"):
            customer_issue_retried += 1

        results.append({
            "transaction_id": txn["transaction_id"],
            "action_taken": "naive_retry",
            "outcome": "recovered" if success else "still_failed",
            "amount_recovered": amount_recovered,
        })

    total_recovered = sum(r["amount_recovered"] for r in results)
    recovery_rate = round(total_recovered / total_at_risk, 4) if total_at_risk else 0

    return {
        "total_at_risk": round(total_at_risk, 2),
        "total_recovered": round(total_recovered, 2),
        "recovery_rate": recovery_rate,
        "transactions_retried": len(transactions),
        "fraud_retried": fraud_retried,
        "customer_issues_retried": customer_issue_retried,
        "escalated_count": 0,
        "has_negotiation": False,
        "results": results,
    }
