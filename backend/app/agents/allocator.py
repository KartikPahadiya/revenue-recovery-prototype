"""
Allocator: treats recovery effort as a limited budget and ranks transactions
by expected value per unit of intervention cost. This is the "portfolio"
differentiator -- plain math, no ML training required.

    expected_value = (recovery_probability * amount_at_risk) / intervention_cost
"""
from app.agents.state import RecoveryState
from app.agents.state import update_status
# rough, hand-set priors per category x leak_type (a hackathon-appropriate
# stand-in for what a bandit would learn online -- see policy_engine.py for
# the online-learning version)
RECOVERY_PROBABILITY = {
    "bank_issue": 0.75,
    "temporary_issue": 0.65,
    "customer_issue": 0.35,
    "fraud_risk": 0.05,
}

INTERVENTION_COST = {
    "failed_payment": 1,        # auto-retry, ~free
    "failed_subscription": 3,   # nudge message, small cost
    "overdue_invoice": 15,      # human/negotiation time, expensive
}


def allocate_node(state: RecoveryState) -> RecoveryState:
    update_status("allocate", message="Ranking by expected recovery value...")
    if state.get("halted"):
        return state

    diag_by_id = {d["transaction_id"]: d for d in state["diagnoses"]}
    ranked = []
    for txn in state["transactions"]:
        diag = diag_by_id.get(txn["transaction_id"], {})
        prob = RECOVERY_PROBABILITY.get(diag.get("category", "customer_issue"), 0.3)
        cost = INTERVENTION_COST.get(txn["leak_type"], 5)
        score = (prob * float(txn["amount"])) / cost

        ranked.append({
            "transaction_id": txn["transaction_id"],
            "expected_value_score": round(score, 2),
            "recovery_probability": prob,
        })

    ranked.sort(key=lambda r: r["expected_value_score"], reverse=True)
    state["allocation"] = ranked
    return state
