"""
Executor: hybrid real + simulated recovery outcomes.
- User-submitted transactions (from demo store) with email addresses get REAL SendGrid emails
  with on-demand payment links (/api/pay/{txn_id} creates Razorpay link lazily when clicked).
- Sample/built-in data is ALWAYS purely simulated — no real emails, no real links.
- On-demand links avoid ALL batch-time and abandonment-time Razorpay rate limits.
"""
import random
import os
from app.agents.state import RecoveryState
from app.agents.policy_engine import record_bandit_outcome
from app.agents.state import update_status
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

# Base URL for on-demand payment links
BASE_URL = os.getenv("BASE_URL", "https://revenue-recovery-prototype.onrender.com")


def _get_on_demand_payment_url(txn_id: str) -> str:
    """Generate an on-demand payment URL that creates Razorpay link when clicked."""
    return f"{BASE_URL}/api/pay/{txn_id}"


def execute_node(state: RecoveryState) -> RecoveryState:
    if state.get("halted"):
        return state

    txn_by_id = {t["transaction_id"]: t for t in state["transactions"]}
    results = []
    total = len(state["decisions"])

    sendgrid_enabled = bool(os.getenv("SENDGRID_API_KEY"))
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

        # Determine if this is a user-submitted transaction (has email = real services)
        customer_email = txn.get("customer_email", "")
        is_user_submission = bool(customer_email)

        # On-demand payment URL only for user submissions
        payment_url = _get_on_demand_payment_url(txn["transaction_id"]) if is_user_submission else None

        result = {
            "transaction_id": txn["transaction_id"],
            "action_taken": action,
            "outcome": outcome,
            "amount_recovered": amount_recovered,
            "execution_mode": "simulated",
            "payment_link_id": None,
            "payment_link_url": payment_url,
            "razorpay_error": None,
            "email_sent": False,
            "email_error": None,
            "discount_code": None,
        }

        # Send REAL email only for user-submitted transactions (sample data stays simulated)
        if is_user_submission and sendgrid_enabled:
            items = txn.get("items", txn.get("failure_reason", ""))
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
                    result["execution_mode"] = "real_email_sent"

        results.append(result)

    print(f"[execute] {emails_sent} real emails sent (user submissions only)")
    state["results"] = results
    return state
