"""
Naive baseline: retry every transaction blindly, regardless of failure reason,
fraud flags, or retry count. No LLM diagnosis, no policy engine, no negotiation.
This is what a naive "retry-all" system does — used to prove the AI agent
generates measurably better outcomes.
"""
import random
from app.agents.state import RecoveryState
from app.agents.state import update_status

NAIVE_RETRY_SUCCESS_RATE = 0.55


def run_naive_baseline(transactions: list) -> dict:
    """
    Run a naive retry-all strategy on the same batch.
    Returns comparison metrics vs. the AI agent.
    """
    update_status("execute", message="Running naive baseline (retry-all)...")

    total_at_risk = sum(float(t["amount"]) for t in transactions)
    results = []
    fraud_retried = 0

    for txn in transactions:
        # Naive: retry EVERYTHING, including fraud and already-retried
        success = random.random() < NAIVE_RETRY_SUCCESS_RATE
        amount_recovered = float(txn["amount"]) if success else 0.0

        # Track dangerous retries
        if txn.get("failure_reason", "").lower() in ("fraud", "suspicious", "chargeback"):
            fraud_retried += 1

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
        "escalated_count": 0,
        "has_negotiation": False,
        "results": results,
    }
