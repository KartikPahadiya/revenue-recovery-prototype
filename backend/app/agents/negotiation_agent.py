"""
Negotiation agent: the LLM is allowed to *draft* a negotiation message and
propose terms for high-value overdue invoices, but the actual offer is
clamped to hard limits from config BEFORE it's shown to the customer. The
LLM never has unbounded authority over a monetary offer.
"""
import json
from app.agents.state import RecoveryState
from app.utils.llm_client import ask_llm
from app import config
from app.agents.state import update_status
SYSTEM_PROMPT = """You are a polite B2B collections negotiator. Given an
overdue invoice, propose ONE offer: either an early-payment discount percent
(0-100) OR a number of installments (1-12). Respond ONLY with compact JSON:
{"offer_type": "discount"|"installments", "value": <number>, "message": "..."}
Keep message under 40 words, professional tone."""


def clamp_offer(offer_type: str, value: float) -> float:
    if offer_type == "discount":
        return min(value, config.DISCOUNT_CAP_PERCENT)
    if offer_type == "installments":
        return min(int(value), config.MAX_INSTALLMENTS)
    return value


def negotiate_node(state: RecoveryState) -> RecoveryState:
    update_status("negotiate", message="Drafting bounded offers for high-value invoices...")
    if state.get("halted"):
        return state

    negotiations = []
    for txn, decision in zip(state["transactions"], state["decisions"]):
        if decision["action"] != "negotiate":
            continue
        user_prompt = (
            f"customer={txn['customer_name']}, amount_due={txn['amount']}, "
            f"days_overdue={txn.get('days_overdue', 'unknown')}"
        )
        try:
            raw = ask_llm(SYSTEM_PROMPT, user_prompt)
            parsed = json.loads(raw)
            offer_type = parsed.get("offer_type", "installments")
            clamped_value = clamp_offer(offer_type, parsed.get("value", 1))
            message = parsed.get("message", "")
        except Exception:
            offer_type, clamped_value, message = "installments", 2, (
                "fallback: could not generate offer, defaulting to 2 installments"
            )

        negotiations.append({
            "transaction_id": txn["transaction_id"],
            "offer_type": offer_type,
            "offer_value": clamped_value,   # ALWAYS within config limits, regardless of what LLM said
            "message": message,
        })

    state["negotiations"] = negotiations
    return state
