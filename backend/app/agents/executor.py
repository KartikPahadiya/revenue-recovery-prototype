"""
Executor: hybrid real + simulated recovery outcomes.
- Top 5 highest-value transactions get REAL Razorpay test-mode payment links.
- Everything else is simulated.
- If Razorpay rate-limits or fails, gracefully falls back to simulation.
"""
import random
import os
from app.agents.state import RecoveryState
from app.agents.policy_engine import record_bandit_outcome
from app.agents.state import update_status
from app.utils.razorpay_client import create_test_payment_link, should_create_real_link

ACTION_SUCCESS_ODDS = {
    "retry_now": 0.7,
    "retry_immediately": 0.55,
    "retry_in_3_days": 0.6,
    "send_update_card_link": 0.4,
    "notify_customer": 0.3,
    "negotiate": 0.5,
    "escalate_human": 0.0,
    "do_not_touch": 0.0,
}


def _rank_by_value(transactions: list) -> dict:
    """Return transaction_id -> rank (0 = highest value)."""
    sorted_txns = sorted(transactions, key=lambda t: float(t.get("amount", 0)), reverse=True)
    return {t["transaction_id"]: i for i, t in enumerate(sorted_txns)}


def execute_node(state: RecoveryState) -> RecoveryState:
    if state.get("halted"):
        return state

    txn_by_id = {t["transaction_id"]: t for t in state["transactions"]}
    results = []
    total = len(state["decisions"])

    # Rank all transactions by value so we know which are "top"
    value_ranks = _rank_by_value(state["transactions"])

    # Check if Razorpay is configured
    razorpay_enabled = bool(os.getenv("RAZORPAY_KEY_ID")) and bool(os.getenv("RAZORPAY_KEY_SECRET"))
    real_links_created = 0

    for index, decision in enumerate(state["decisions"], start=1):
        update_status(
            "execute",
            current=index,
            total=total,
            message=f"Executing recovery actions ({index}/{total})",
        )
        txn = txn_by_id[decision["transaction_id"]]
        action = decision["action"]
        odds = ACTION_SUCCESS_ODDS.get(action, 0.3)
        success = random.random() < odds

        if action in ("retry_immediately", "retry_in_3_days", "send_update_card_link"):
            record_bandit_outcome(action, success)

        outcome = "recovered" if success else (
            "escalated" if action == "escalate_human" else "still_failed"
        )
        amount_recovered = float(txn["amount"]) if success else 0.0

        result = {
            "transaction_id": txn["transaction_id"],
            "action_taken": action,
            "outcome": outcome,
            "amount_recovered": amount_recovered,
            "execution_mode": "simulated",
            "payment_link_id": None,
            "payment_link_url": None,
            "razorpay_error": None,
        }

        # Try to create a REAL Razorpay payment link for top-value transactions
        rank = value_ranks.get(txn["transaction_id"], 999)
        eligible = should_create_real_link({"action_taken": action}, rank)

        if razorpay_enabled and success and eligible:
            try:
                link_id, short_url = create_test_payment_link(
                    customer_name=txn["customer_name"],
                    amount=float(txn["amount"]),
                    description=f"Recovery for {txn.get('failure_reason', 'failed payment')}",
                )
                result["payment_link_id"] = link_id
                result["payment_link_url"] = short_url
                result["execution_mode"] = "real_razorpay_link"
                real_links_created += 1
            except Exception as e:
                # Include the error in the result so it's visible in the audit trail
                error_msg = str(e)
                print(f"[razorpay] Failed for {txn['transaction_id']}: {error_msg}")
                result["execution_mode"] = "simulated (razorpay_failed)"
                result["razorpay_error"] = error_msg
        elif not razorpay_enabled:
            result["razorpay_error"] = "Razorpay keys not configured"
        elif not eligible:
            result["razorpay_error"] = f"Not in top 5 (rank {rank}) or action={action}"

        results.append(result)

    print(f"[execute] {real_links_created} real Razorpay links created, {total - real_links_created} simulated")
    state["results"] = results
    return state
