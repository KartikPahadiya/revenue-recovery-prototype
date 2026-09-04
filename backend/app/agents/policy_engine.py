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
# --- simple in-memory bandit stats: context -> strategy -> [successes, attempts] ---
SUBSCRIPTION_STRATEGIES = ["retry_immediately", "retry_in_3_days", "send_update_card_link"]
MAX_CONTACTS_7D = 2
HUMAN_APPROVAL_AMOUNT = 25000
bandit_stats = {}


def _bandit_key(customer_segment: str, failure_type: str) -> str:
    return f"{customer_segment}:{failure_type}"


def _stats_for_context(customer_segment: str, failure_type: str) -> dict:
    key = _bandit_key(customer_segment, failure_type)
    if key not in bandit_stats:
        bandit_stats[key] = {
            s: {"successes": 0, "attempts": 0}
            for s in SUBSCRIPTION_STRATEGIES
        }
    return bandit_stats[key]


def pick_subscription_strategy(customer_segment: str = "NEW", failure_type: str = "unknown", epsilon: float = 0.2) -> str:
    stats = _stats_for_context(customer_segment, failure_type)
    if random.random() < epsilon:
        return random.choice(SUBSCRIPTION_STRATEGIES)  # explore
    # exploit: pick the strategy with best observed success rate so far
    def success_rate(s):
        a = stats[s]["attempts"]
        return stats[s]["successes"] / a if a > 0 else 0.5  # optimistic default
    return max(SUBSCRIPTION_STRATEGIES, key=success_rate)


def record_bandit_outcome(strategy: str, success: bool, customer_segment: str = "NEW", failure_type: str = "unknown"):
    stats = _stats_for_context(customer_segment, failure_type)
    if strategy not in stats:
        return
    stats[strategy]["attempts"] += 1
    if success:
        stats[strategy]["successes"] += 1


def decide_node(state: RecoveryState) -> RecoveryState:
    update_status("decide", message="Applying policy rules and bandit strategy...")
    if state.get("halted"):
        return state

    diag_by_id = {d["transaction_id"]: d for d in state["diagnoses"]}
    profile_by_id = {p["transaction_id"]: p["profile"] for p in state.get("customer_profiles", [])}
    segment_by_id = {s["transaction_id"]: s for s in state.get("customer_segments", [])}
    decisions = []

    for txn in state["transactions"]:
        diag = diag_by_id.get(txn["transaction_id"], {})
        profile = profile_by_id.get(txn["transaction_id"], {})
        segment_info = segment_by_id.get(txn["transaction_id"], {})
        segment = segment_info.get("segment", "NEW")
        traits = segment_info.get("traits", [])
        category = diag.get("category", "customer_issue")
        leak_type = txn["leak_type"]
        retries = int(txn.get("retry_count", 0) or 0)
        amount = float(txn["amount"])

        # --- hard gates first (never violated) ---
        if category == "fraud_risk":
            action, rule = "do_not_touch", "Rule: never auto-recover fraud-flagged transactions"
        elif int(profile.get("contacts_last_7_days", 0)) >= MAX_CONTACTS_7D:
            action, rule = "do_not_touch", f"Rule: max {MAX_CONTACTS_7D} contacts per customer in 7 days"
        elif retries >= config.MAX_RETRIES_PER_TRANSACTION:
            action, rule = "escalate_human", f"Rule: stop after {config.MAX_RETRIES_PER_TRANSACTION} retries"
        elif leak_type == "overdue_invoice" and amount > 50000:
            action, rule = "negotiate", "Rule: high-value overdue invoice gets bounded negotiation proposal with human approval required"
        elif amount >= HUMAN_APPROVAL_AMOUNT:
            action, rule = "escalate_human", f"Rule: transactions >= ₹{HUMAN_APPROVAL_AMOUNT:,} require human approval"
        elif leak_type == "failed_payment" and category == "bank_issue":
            action, rule = "retry_now", "Rule: bank-side failures are safe to auto-retry"
        elif leak_type == "failed_payment" and category == "customer_issue":
            action, rule = "notify_customer", "Rule: customer-side issues need customer action, not a retry"
        elif leak_type == "failed_payment" and category == "temporary_issue":
            action, rule = "retry_now", "Rule: temporary/transient failures are safe to auto-retry"
        elif leak_type == "checkout_abandonment":
            follow_ups = int(txn.get("follow_up_count", 0) or 0)
            if follow_ups >= 3:
                action, rule = "do_not_touch", "Rule: max 3 recovery nudges per abandoned cart, then stop"
            elif "DISCOUNT_GUARDED" in traits:
                action, rule = "send_cart_reminder", "Rule: discount-abuse guardrail blocks another offer"
            elif segment == "HIGH_VALUE":
                action, rule = "send_cart_reminder", "Rule: high-value loyal customers get concierge reminder before discounts"
            elif segment == "PRICE_SENSITIVE" and amount > 300:
                action, rule = "send_discount_code", "Rule: price-sensitive customers respond well to bounded incentives"
            elif amount > 1000:
                action, rule = "send_discount_code", "Rule: high-value abandoned cart (>₹1000) gets discount offer"
            elif amount > 300:
                action, rule = "send_cart_reminder", "Rule: medium-value cart gets personalized reminder"
            else:
                action, rule = "send_product_recommendation", "Rule: low-value cart gets product recommendation only"
        elif leak_type == "failed_subscription":
            strategy = pick_subscription_strategy(segment, category)
            action, rule = strategy, "Bandit: exploring/exploiting best-known dunning strategy"
        elif leak_type == "overdue_invoice" and amount > 50000:
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
            "customer_segment": segment,
            "segment_reason": segment_info.get("segment_reason"),
            "customer_traits": traits,
            "customer_id": profile.get("customer_id"),
            "requires_human_approval": action in {"escalate_human", "negotiate"} and amount >= HUMAN_APPROVAL_AMOUNT,
        })

    state["decisions"] = decisions
    return state
