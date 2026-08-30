"""
Razorpay test-mode client using direct HTTP requests.
Avoids the razorpay SDK's pkg_resources dependency which breaks in python:3.12-slim.
Includes cooldown tracking to avoid hammering Razorpay's test mode rate limits.
"""
import os
import time
import base64
import requests

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"

# Cooldown tracking to prevent 429 rate limits in test mode
_LAST_RAZORPAY_CALL = 0
_MIN_COOLDOWN_SECONDS = 60  # Razorpay test mode: max 1 call per minute


def _get_auth_headers():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET not set")
    credentials = base64.b64encode(f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }


def get_cooldown_remaining() -> int:
    """Return seconds remaining before next Razorpay call is allowed."""
    global _LAST_RAZORPAY_CALL
    elapsed = time.time() - _LAST_RAZORPAY_CALL
    remaining = max(0, _MIN_COOLDOWN_SECONDS - int(elapsed))
    return remaining


def create_test_payment_link(customer_name: str, amount: float, description: str = "Payment recovery"):
    """
    Create a Razorpay test-mode payment link via direct HTTP POST.
    Enforces a 60-second cooldown between calls to avoid test mode rate limits.
    Amount in INR paise (amount * 100).
    Returns (link_id, short_url) or raises on failure.
    """
    global _LAST_RAZORPAY_CALL

    remaining = get_cooldown_remaining()
    if remaining > 0:
        raise RuntimeError(
            f"Razorpay rate limit cooldown: {remaining}s remaining. "
            f"Test mode allows ~1 payment link per minute."
        )

    headers = _get_auth_headers()
    amount_paise = int(amount * 100)

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {"name": customer_name},
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": {
            "source": "ai_revenue_recovery_agent",
            "mode": "test",
        },
    }

    response = requests.post(
        f"{RAZORPAY_BASE_URL}/payment_links/",
        headers=headers,
        json=payload,
        timeout=30,
    )
    _LAST_RAZORPAY_CALL = time.time()
    response.raise_for_status()
    data = response.json()
    link_id = data.get("id")
    short_url = data.get("short_url")
    return link_id, short_url


MAX_REAL_PAYMENT_LINKS_PER_BATCH = 1


def should_create_real_link(txn: dict, rank: int) -> bool:
    """
    Create real Razorpay links for the top-N highest-value transactions.
    """
    if rank >= MAX_REAL_PAYMENT_LINKS_PER_BATCH:
        return False
    action = txn.get("action_taken", "")
    return action in ("retry_now", "notify_customer", "send_discount_code", "send_cart_reminder")
