"""
Razorpay test-mode client using direct HTTP requests.
Avoids the razorpay SDK's pkg_resources dependency which breaks in python:3.12-slim.
Includes retry with exponential backoff for 429 rate limit errors.
"""
import os
import time
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
    Retries on 429 (rate limit) with exponential backoff.
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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{RAZORPAY_BASE_URL}/payment_links/",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if response.status_code == 429:
                # Rate limited — wait and retry
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"[razorpay] Rate limited (429), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            data = response.json()
            link_id = data.get("id")
            short_url = data.get("short_url")
            return link_id, short_url
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError("Razorpay rate limit exceeded after retries")


# Cap on how many real payment links we create per batch
# Keep at 1 to avoid Razorpay test mode rate limits
MAX_REAL_PAYMENT_LINKS_PER_BATCH = 1
# Keep low to avoid Razorpay rate limits in test mode
MAX_REAL_PAYMENT_LINKS_PER_BATCH = 2


def should_create_real_link(txn: dict, rank: int) -> bool:
    """
    Create real Razorpay links for the top-N highest-value transactions.
    Includes payment retries, notifications, AND cart recovery actions.
    """
    if rank >= MAX_REAL_PAYMENT_LINKS_PER_BATCH:
        return False
    action = txn.get("action_taken", "")
    return action in ("retry_now", "notify_customer", "send_discount_code", "send_cart_reminder")
