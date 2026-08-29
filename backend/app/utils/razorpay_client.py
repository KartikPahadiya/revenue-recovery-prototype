"""
Thin wrapper around Razorpay's test-mode API. Creates a real, verifiable
Payment Link for each recovery action. Includes a shared rate limiter and
retry-with-backoff, since Razorpay enforces a request-rate limit and will
return 429 "Too many requests" if you fire calls back-to-back at volume.

Falls back gracefully (returns None) if no keys are configured or a call
ultimately fails after retries, so the pipeline never crashes.
"""
import time
import threading
import razorpay
from app import config

_client = None

# --- simple shared rate limiter across all calls in this process ---
MAX_REQUESTS_PER_SECOND = 3   # conservative; adjust up only if you confirm your account's actual limit
_lock = threading.Lock()
_last_call_times = []

MAX_RETRIES = 4


def get_client():
    global _client
    if not config.RAZORPAY_ENABLED:
        return None
    if _client is None:
        _client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))
    return _client


def _wait_for_rate_limit():
    while True:
        with _lock:
            now = time.time()
            while _last_call_times and _last_call_times[0] < now - 1:
                _last_call_times.pop(0)
            if len(_last_call_times) < MAX_REQUESTS_PER_SECOND:
                _last_call_times.append(now)
                return
            sleep_time = 1 - (now - _last_call_times[0]) + 0.05
        time.sleep(max(sleep_time, 0.05))


def create_recovery_payment_link(transaction_id: str, amount: float, customer_name: str, description: str):
    client = get_client()
    if client is None:
        return None

    last_error = None
    for attempt in range(MAX_RETRIES):
        _wait_for_rate_limit()
        try:
            link = client.payment_link.create({
                "amount": int(round(amount * 100)),
                "currency": "INR",
                "description": description[:255],
                "customer": {"name": customer_name[:50]},
                "notify": {"sms": False, "email": False},
                "reference_id": transaction_id,
                "notes": {"source": "ai-revenue-recovery-agent", "transaction_id": transaction_id},
            })
            return {"id": link["id"], "short_url": link["short_url"]}
        except Exception as e:
            last_error = e
            is_rate_limit = "Too many requests" in str(e) or "429" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
                continue
            break

    print(f"[razorpay] payment link creation failed for {transaction_id} after {MAX_RETRIES} attempts: {last_error}")
    return None