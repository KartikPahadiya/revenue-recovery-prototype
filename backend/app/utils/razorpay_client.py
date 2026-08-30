"""
Razorpay test-mode client using direct HTTP requests.
Avoids the razorpay SDK's pkg_resources dependency which breaks in python:3.12-slim.
"""
import os
import base64
import requests

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"


def _get_auth_headers():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET not set")
    credentials = base64.b64encode(f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }


def create_test_payment_link(customer_name: str, amount: float, description: str = "Payment recovery"):
    """
    Create a Razorpay test-mode payment link via direct HTTP POST.
    Amount in INR paise (amount * 100).
    Returns (link_id, short_url) or raises on failure.
    """
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
    response.raise_for_status()
    data = response.json()
    link_id = data.get("id")
    short_url = data.get("short_url")
    return link_id, short_url


# Cap on how many real payment links we create per batch
MAX_REAL_PAYMENT_LINKS_PER_BATCH = 5


def should_create_real_link(txn: dict, rank: int) -> bool:
    """
    Create real Razorpay links for the top-N highest-value transactions.
    Includes payment retries, notifications, AND cart recovery actions.
    """
    if rank >= MAX_REAL_PAYMENT_LINKS_PER_BATCH:
        return False
    action = txn.get("action_taken", "")
    return action in ("retry_now", "notify_customer", "send_discount_code", "send_cart_reminder")
