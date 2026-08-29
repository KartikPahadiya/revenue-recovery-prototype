"""
Policy engine: the ONLY node allowed to decide + authorize a money action.
Pure Python rules -- no LLM. This is what makes actions "explainable,
bounded and gated" per the track brief.

Includes a minimal online-learning layer (epsilon-greedy bandit) for
failed_subscription nudges, so you can honestly say the system "learns which
intervention works" without training any model offline.
"""
import random
from app.agents.state import RecoveryState
from app import config
from app.agents.state import update_status
# --- simple in-memory bandit stats: strategy -> [successes, attempts] ---
SUBSCRIPTION_STRATEGIES = ["retry_immediately", "retry_in_3_days", "send_update_card_link"]
bandit_stats = {s: {"successes": 0, "attempts": 0} for s in SUBSCRIPTION_STRATEGIES}


def pick_subscription_strategy(epsilon: float = 0.2) -> str:
    if random.random() < epsilon:
        return random.choice(SUBSCRIPTION_STRATEGIES)  # explore
    # exploit: pick the strategy with best observed success rate so far
    def success_rate(s):
        a = bandit_stats[s]["attempts"]
        return bandit_stats[s]["successes"] / a if a > 0 else 0.5  # optimistic default
    return max(SUBSCRIPTION_STRATEGIES, key=success_rate)


def record_bandit_outcome(strategy: str, success: bool):
    bandit_stats[strategy]["attempts"] += 1
    if success:
        bandit_stats[strategy]["successes"] += 1


def decide_node(state: RecoveryState) -> RecoveryState:
    update_status("decide", message="Applying policy rules and bandit strategy...")
    if state.get("halted"):
        return state

    diag_by_id = {d["transaction_id"]: d for d in state["diagnoses"]}
    decisions = []

    for txn in state["transactions"]:
        diag = diag_by_id.get(txn["transaction_id"], {})
        category = diag.get("category", "customer_issue")
        leak_type = txn["leak_type"]
        retries = int(txn.get("retry_count", 0) or 0)

        # --- hard gates first (never violated) ---
        if category == "fraud_risk":
            action, rule = "do_not_touch", "Rule: never auto-recover fraud-flagged transactions"
        elif retries >= config.MAX_RETRIES_PER_TRANSACTION:
            action, rule = "escalate_human", f"Rule: stop after {config.MAX_RETRIES_PER_TRANSACTION} retries"
        elif leak_type == "failed_payment" and category == "bank_issue":
            action, rule = "retry_now", "Rule: bank-side failures are safe to auto-retry"
        elif leak_type == "failed_payment" and category == "customer_issue":
            action, rule = "notify_customer", "Rule: customer-side issues need customer action, not a retry"
        elif leak_type == "failed_payment" and category == "temporary_issue":
            action, rule = "retry_now", "Rule: temporary/transient failures are safe to auto-retry"
        elif leak_type == "failed_subscription":
            strategy = pick_subscription_strategy()
            action, rule = strategy, "Bandit: exploring/exploiting best-known dunning strategy"
        elif leak_type == "overdue_invoice" and float(txn["amount"]) > 50000:
            action, rule = "negotiate", "Rule: high-value overdue invoices go to bounded negotiation agent"
        else:
            action, rule = "notify_customer", "Rule: default safe fallback"

        priority = next(
            (a["expected_value_score"] for a in state.get("allocation", [])
             if a["transaction_id"] == txn["transaction_id"]), 0
        )

        decisions.append({
            "transaction_id": txn["transaction_id"],
            "action": action,
            "rule_applied": rule,
            "priority_score": priority,
        })

    state["decisions"] = decisions
    return state
