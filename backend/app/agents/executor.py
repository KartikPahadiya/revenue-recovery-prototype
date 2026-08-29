"""
Executor: simulates recovery outcomes for a hackathon demo.

In a production system this node would enqueue real payment operations and
reconcile outcomes from provider webhooks. For the demo, keeping execution
simulated avoids external API limits and makes every run reliable.
"""
import random
from app.agents.state import RecoveryState
from app.agents.policy_engine import record_bandit_outcome
from app.agents.state import update_status

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

def execute_node(state: RecoveryState) -> RecoveryState:
    if state.get("halted"):
        return state

    txn_by_id = {t["transaction_id"]: t for t in state["transactions"]}
    results = []
    total = len(state["decisions"])

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
        }

        results.append(result)

    state["results"] = results
    return state
