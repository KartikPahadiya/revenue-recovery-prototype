"""
Razorpay test-mode client with rate-limit safety.
Only creates REAL payment links for the top-N highest-value transactions.
Everything else falls back to simulated outcomes gracefully.
"""
import os
from app import config

# Lazy init — only created when first needed
_razorpay_client = None

def _get_client():
    global _razorpay_client
    if _razorpay_client is None:
        # Lazy import to avoid startup crash if setuptools/pkg_resources is missing
        import razorpay
        key_id = os.getenv("RAZORPAY_KEY_ID", "")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
        if not key_id or not key_secret:
            raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET not set")
        _razorpay_client = razorpay.Client(auth=(key_id, key_secret))
    return _razorpay_client


def create_test_payment_link(customer_name: str, amount: float, description: str = "Payment recovery"):
    """
    Create a Razorpay test-mode payment link.
    Amount in INR paise (amount * 100).
    Returns (link_id, short_url) or raises on failure.
    """
    client = _get_client()
    # Razorpay amount is in paise
    amount_paise = int(amount * 100)

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {
            "name": customer_name,
        },
        "notify": {
            "sms": False,
            "email": False,
        },
        "reminder_enable": False,
        "notes": {
            "source": "ai_revenue_recovery_agent",
            "mode": "test",
        },
    }

    response = client.payment_link.create(data=payload)
    link_id = response.get("id")
    short_url = response.get("short_url")
    return link_id, short_url


# Cap on how many real payment links we create per batch
# Razorpay test mode has ~100 req/min but we stay far below that
MAX_REAL_PAYMENT_LINKS_PER_BATCH = 5


def should_create_real_link(txn: dict, rank: int) -> bool:
    """
    Only create real links for the top-N highest-value transactions
    where the action is 'retry_now' or 'notify_customer'.
    """
    if rank >= MAX_REAL_PAYMENT_LINKS_PER_BATCH:
        return False
    action = txn.get("action_taken", "")
    return action in ("retry_now", "notify_customer")
