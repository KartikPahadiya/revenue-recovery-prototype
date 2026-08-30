"""
Executor: hybrid real + simulated recovery outcomes.
- Top transactions get REAL Razorpay test-mode payment links.
- Messaging actions send REAL emails via SendGrid with payment links inside.
- Everything else is simulated.
- If any real service fails, gracefully falls back to simulation.
"""
import random
import os
import time
from app.agents.state import RecoveryState
from app.agents.policy_engine import record_bandit_outcome
from app.agents.state import update_status
from app.utils.razorpay_client import create_test_payment_link, should_create_real_link
from app.utils.sendgrid_client import (
    send_cart_reminder_email,
    send_discount_code_email,
    send_product_recommendation_email,
    send_payment_notification_email,
)

ACTION_SUCCESS_ODDS = {
    "retry_now": 0.7,
    "retry_immediately": 0.55,
    "retry_in_3_days": 0.6,
    "send_update_card_link": 0.4,
    "notify_customer": 0.3,
    "negotiate": 0.5,
    "send_discount_code": 0.45,
    "send_cart_reminder": 0.35,
    "send_product_recommendation": 0.25,
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

    # Check if real services are configured
    razorpay_enabled = bool(os.getenv("RAZORPAY_KEY_ID")) and bool(os.getenv("RAZORPAY_KEY_SECRET"))
    sendgrid_enabled = bool(os.getenv("SENDGRID_API_KEY"))
    real_links_created = 0
    emails_sent = 0

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
            "email_sent": False,
            "email_error": None,
            "discount_code": None,
        }

        # --- 1. Try Razorpay payment link for ALL eligible top-value transactions ---
        rank = value_ranks.get(txn["transaction_id"], 999)
        eligible_razorpay = should_create_real_link({"action_taken": action}, rank)

        if razorpay_enabled and success and eligible_razorpay:
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
                # Small delay to avoid Razorpay rate limits between links
                time.sleep(1.5)
            except Exception as e:
                error_msg = str(e)
                print(f"[razorpay] Failed for {txn['transaction_id']}: {error_msg}")
                result["execution_mode"] = "simulated (razorpay_failed)"
                result["razorpay_error"] = error_msg

        # --- 2. Try SendGrid email for messaging actions (includes payment link if available) ---
        customer_email = txn.get("customer_email", "")
        items = txn.get("items", txn.get("failure_reason", ""))
        payment_url = result.get("payment_link_url")  # may be None

        if sendgrid_enabled and customer_email and success:
            email_result = None
            if action == "send_cart_reminder":
                email_result = send_cart_reminder_email(
                    customer_name=txn["customer_name"],
                    customer_email=customer_email,
                    items=items,
                    cart_value=float(txn["amount"]),
                    payment_url=payment_url,
                )
            elif action == "send_discount_code":
                email_result = send_discount_code_email(
                    customer_name=txn["customer_name"],
                    customer_email=customer_email,
                    items=items,
                    cart_value=float(txn["amount"]),
                    payment_url=payment_url,
                )
                if email_result.get("discount_code"):
                    result["discount_code"] = email_result["discount_code"]
            elif action == "send_product_recommendation":
                email_result = send_product_recommendation_email(
                    customer_name=txn["customer_name"],
                    customer_email=customer_email,
                    items=items,
                    payment_url=payment_url,
                )
            elif action == "notify_customer":
                email_result = send_payment_notification_email(
                    customer_name=txn["customer_name"],
                    customer_email=customer_email,
                    failure_reason=txn.get("failure_reason", "payment issue"),
                    amount=float(txn["amount"]),
                    payment_url=payment_url,
                )

            if email_result:
                result["email_sent"] = email_result.get("sent", False)
                if email_result.get("error"):
                    result["email_error"] = email_result["error"]
                if result["email_sent"]:
                    emails_sent += 1
                    # Mark as real execution if email went out
                    if result["execution_mode"] == "simulated":
                        result["execution_mode"] = "real_email_sent"
                    elif result["execution_mode"] == "real_razorpay_link":
                        result["execution_mode"] = "real_link+email"

        results.append(result)

    print(f"[execute] {real_links_created} Razorpay links, {emails_sent} emails sent")
    state["results"] = results
    return state
