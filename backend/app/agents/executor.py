"""
Executor: for actions that involve payment collection, creates a REAL
Razorpay test-mode Payment Link (a verifiable artifact) when Razorpay
credentials are configured. Whether the customer actually pays it is still
simulated (we can't force a real human to click "pay" in an automated
demo) -- but the link itself is genuine, not a fabricated placeholder.

If Razorpay isn't configured, falls back to pure simulation so the
pipeline still runs end-to-end without setup.
"""
import random
from app.agents.state import RecoveryState
from app.agents.policy_engine import record_bandit_outcome
from app.utils.razorpay_client import create_recovery_payment_link
from app import config

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

# actions that involve asking the customer to pay -- these get a real payment link
PAYMENT_LINK_ACTIONS = {
    "retry_now", "retry_immediately", "retry_in_3_days",
    "send_update_card_link", "notify_customer",
}


def execute_node(state: RecoveryState) -> RecoveryState:
    if state.get("halted"):
        return state

    txn_by_id = {t["transaction_id"]: t for t in state["transactions"]}
    results = []

    for decision in state["decisions"]:
        txn = txn_by_id[decision["transaction_id"]]
        action = decision["action"]
        odds = ACTION_SUCCESS_ODDS.get(action, 0.3)
        success = random.random() < odds

        payment_link = None
        if action in PAYMENT_LINK_ACTIONS:
            payment_link = create_recovery_payment_link(
                transaction_id=txn["transaction_id"],
                amount=float(txn["amount"]),
                customer_name=txn["customer_name"],
                description=f"Recovery: {txn['leak_type']} for {txn['transaction_id']}",
            )

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
        }
        if payment_link:
            result["payment_link_id"] = payment_link["id"]
            result["payment_link_url"] = payment_link["short_url"]

        results.append(result)

    state["results"] = results
    return state