"""
Personalize: the LLM drafts the *narrative* of the recovery email (tone,
specifics about the customer's situation) but NEVER the numbers. Discount
codes, amounts, and payment links are always inserted by code afterward --
this mirrors negotiation_agent's clamp pattern: LLM proposes, code controls
anything that touches money.

Batched like diagnosis_agent to stay within the Groq free-tier token budget.
"""
import json
import re
import time
from app.agents.state import RecoveryState
from app.utils.llm_client import ask_llm
from app.agents.state import update_status

SYSTEM_PROMPT = """You are a friendly customer-retention copywriter for an
Indian payments/e-commerce platform. You will receive a JSON array of
situations. For EACH one, write a short, warm, personalized email message
about their cart/payment/subscription situation and the action being taken.

Respond ONLY with a JSON array, one object per situation, SAME ORDER as
input, shaped like:
{"transaction_id": "...", "subject": "...", "body": "..."}

Rules:
- "subject": under 12 words, no ALL CAPS, at most one emoji.
- "body": 2-4 short sentences, plain text (NOT html), specific to their
  situation (name, items or reason) -- warm, not pushy.
- Use provided customer segment/history to choose tone, but do not invent
  facts or claim preferences that are not present in the input.
- Do NOT invent or mention discount percentages, amounts, dates, or
  promises you were not explicitly given. Do NOT include links or codes --
  those are inserted separately by the system.
- No markdown, no code fences, no preamble. JSON array only."""

BATCH_SIZE = 15
MAX_RETRIES = 3

# Only these actions send an email at all (matches executor.py's gating)
EMAIL_ACTIONS = {
    "send_cart_reminder",
    "send_discount_code",
    "send_product_recommendation",
    "notify_customer",
}

FALLBACK_SUBJECT = {
    "send_cart_reminder": "You left something in your cart",
    "send_discount_code": "A little something to help you finish your order",
    "send_product_recommendation": "You might like these too",
    "notify_customer": "There was an issue with your recent payment",
}
FALLBACK_BODY = {
    "send_cart_reminder": "We noticed you didn't finish checking out. Your items are still waiting for you.",
    "send_discount_code": "We saved your cart and have a little discount to help you complete it.",
    "send_product_recommendation": "Based on what you were browsing, we thought you'd like a few more picks.",
    "notify_customer": "Your recent payment didn't go through, but your order is still saved. You can retry anytime.",
}


def _sanitize(text: str, max_len: int) -> str:
    """Strip any HTML/markdown the model slipped in, hard-cap length."""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = text.strip()
    return text[:max_len]


def _chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def _personalize_batch(batch):
    payload = [
        {
            "transaction_id": t["transaction_id"],
            "customer_name": t["customer_name"],
            "action": t["_action"],
            "customer_segment": t.get("_customer_segment"),
            "customer_traits": t.get("_customer_traits", []),
            "customer_profile": t.get("_customer_profile", {}),
            "leak_type": t.get("leak_type", ""),
            "items": t.get("items", ""),
            "failure_reason": t.get("failure_reason", ""),
        }
        for t in batch
    ]
    user_prompt = json.dumps(payload)

    for attempt in range(MAX_RETRIES):
        try:
            raw = ask_llm(SYSTEM_PROMPT, user_prompt)
            parsed = json.loads(raw)
            by_id = {p["transaction_id"]: p for p in parsed}
            out = []
            for t in batch:
                p = by_id.get(t["transaction_id"], {})
                subject = _sanitize(p.get("subject", ""), 80) or FALLBACK_SUBJECT[t["_action"]]
                body = _sanitize(p.get("body", ""), 500) or FALLBACK_BODY[t["_action"]]
                out.append({"transaction_id": t["transaction_id"], "subject": subject, "body": body})
            return out
        except Exception as e:
            is_rate_limit = "429" in str(e) or "rate_limit" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            break

    # fallback: deterministic template text, never blocks the pipeline
    return [
        {
            "transaction_id": t["transaction_id"],
            "subject": FALLBACK_SUBJECT[t["_action"]],
            "body": FALLBACK_BODY[t["_action"]],
        }
        for t in batch
    ]


def personalize_node(state: RecoveryState) -> RecoveryState:
    update_status("personalize", message="Drafting personalized emails...")
    if state.get("halted"):
        return state

    decision_by_id = {d["transaction_id"]: d for d in state["decisions"]}
    profile_by_id = {p["transaction_id"]: p["profile"] for p in state.get("customer_profiles", [])}
    segment_by_id = {s["transaction_id"]: s for s in state.get("customer_segments", [])}

    # Only bother personalizing transactions that will actually get an email
    # AND are user submissions (have an email address) -- matches executor.py gating
    candidates = []
    for txn in state["transactions"]:
        decision = decision_by_id.get(txn["transaction_id"], {})
        action = decision.get("action")
        if action in EMAIL_ACTIONS and txn.get("customer_email"):
            enriched = dict(txn)
            enriched["_action"] = action
            enriched["_customer_profile"] = profile_by_id.get(txn["transaction_id"], {})
            enriched["_customer_segment"] = segment_by_id.get(txn["transaction_id"], {}).get("segment", "NEW")
            enriched["_customer_traits"] = segment_by_id.get(txn["transaction_id"], {}).get("traits", [])
            candidates.append(enriched)

    personalizations = []
    batches = list(_chunk(candidates, BATCH_SIZE))
    for i, batch in enumerate(batches):
        personalizations.extend(_personalize_batch(batch))
        time.sleep(0.3)

    state["personalizations"] = personalizations
    return state
