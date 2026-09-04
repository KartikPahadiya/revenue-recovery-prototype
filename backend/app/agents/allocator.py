"""
Allocator: treats recovery effort as a limited budget and ranks transactions
by expected value per unit of intervention cost. This is the "portfolio"
differentiator -- plain math, no ML training required.

    expected_value = (
        recovery_probability * amount_at_risk * customer_factor
    ) - intervention_cost
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

CUSTOMER_FACTORS = {
    "HIGH_VALUE": 1.25,
    "AT_RISK": 1.15,
    "PRICE_SENSITIVE": 1.1,
    "LOYAL": 1.05,
    "NEW": 1.0,
    "RECOVERY_RESPONSIVE": 1.1,
    "STANDARD": 1.0,
}


def allocate_node(state: RecoveryState) -> RecoveryState:
    update_status("allocate", message="Ranking by expected recovery value...")
    if state.get("halted"):
        return state

    diag_by_id = {d["transaction_id"]: d for d in state["diagnoses"]}
    segment_by_id = {s["transaction_id"]: s["segment"] for s in state.get("customer_segments", [])}
    ranked = []
    for txn in state["transactions"]:
        diag = diag_by_id.get(txn["transaction_id"], {})
        segment = segment_by_id.get(txn["transaction_id"], "NEW")
        prob = RECOVERY_PROBABILITY.get(diag.get("category", "customer_issue"), 0.3)
        cost = INTERVENTION_COST.get(txn["leak_type"], 5)
        customer_factor = CUSTOMER_FACTORS.get(segment, 1.0)
        score = (prob * float(txn["amount"]) * customer_factor) - cost

        ranked.append({
            "transaction_id": txn["transaction_id"],
            "expected_value_score": round(score, 2),
            "recovery_probability": prob,
            "customer_factor": customer_factor,
            "customer_segment": segment,
        })

    ranked.sort(key=lambda r: r["expected_value_score"], reverse=True)
    state["allocation"] = ranked
    return state
