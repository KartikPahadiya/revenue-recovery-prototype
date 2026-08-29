"""
Diagnosis: the ONLY node that calls the LLM to interpret *why* something
failed. Batches multiple transactions into a single LLM call (instead of
one call per transaction) to stay well within Groq's free-tier token
budget (8000 tokens/minute) -- 415 individual calls blew past that budget
constantly; ~10 transactions per call keeps us comfortably under it.
"""
import json
import time
from app.agents.state import RecoveryState
from app.utils.llm_client import ask_llm
from app.agents.state import update_status
SYSTEM_PROMPT = """You are a payments diagnosis assistant. You will receive
a JSON array of failed transactions. For EACH transaction, classify it into
EXACTLY ONE of these four category values -- do not invent new categories,
do not use the failure_reason as the category:
- temporary_issue
- customer_issue
- bank_issue
- fraud_risk

Respond ONLY with a JSON array, one object per transaction, in the SAME
ORDER as the input, each shaped like:
{"transaction_id": "...", "category": "...", "explanation": "..."}
The "category" field MUST be one of the four values listed above, nothing else.
Keep each explanation under 15 words. No other text, no markdown fences."""

BATCH_SIZE = 10
MAX_RETRIES = 4

VALID_CATEGORIES = {"temporary_issue", "customer_issue", "bank_issue", "fraud_risk"}

def _chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def _diagnose_batch(txn_batch):
    payload = [
        {
            "transaction_id": t["transaction_id"],
            "leak_type": t["leak_type"],
            "failure_reason": t["failure_reason"],
            "payment_method": t["payment_method"],
            "amount": t["amount"],
            "retry_count": t.get("retry_count", 0),
        }
        for t in txn_batch
    ]
    user_prompt = json.dumps(payload)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            raw = ask_llm(SYSTEM_PROMPT, user_prompt)
            parsed = json.loads(raw)
            results_by_id = {r["transaction_id"]: r for r in parsed}
            # fill in any missing entries, AND reject any category the model
            # hallucinated outside the allowed set (small local models sometimes
            # echo the raw failure_reason instead of classifying it)
            output = []
            for t in txn_batch:
                result = results_by_id.get(t["transaction_id"], {})
                category = result.get("category", "customer_issue")
                if category not in VALID_CATEGORIES:
                    print(f"[diagnose] invalid category '{category}' for {t['transaction_id']}, defaulting to customer_issue")
                    category = "customer_issue"
                output.append({
                    "transaction_id": t["transaction_id"],
                    "category": category,
                    "explanation": result.get("explanation", ""),
                })
            return output
        except Exception as e:
            last_error = e
            is_rate_limit = "429" in str(e) or "rate_limit" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
                continue
            break

    print(f"[diagnose] batch failed after {MAX_RETRIES} attempts: {last_error}")
    return [
        {
            "transaction_id": t["transaction_id"],
            "category": "customer_issue",
            "explanation": "fallback: batch LLM call failed after retries",
        }
        for t in txn_batch
    ]


def diagnose_node(state: RecoveryState) -> RecoveryState:
    if state.get("halted"):
        return state

    transactions = state["transactions"]
    total = len(transactions)
    diagnoses = []

    batches = list(_chunk(transactions, BATCH_SIZE))
    for i, batch in enumerate(batches):
        diagnoses.extend(_diagnose_batch(batch))
        done = min((i + 1) * BATCH_SIZE, total)
        print(f"[diagnose] {done}/{total}...")
        update_status("diagnose", current=done, total=total, message=f"Classifying failure reasons ({done}/{total})")
        # time.sleep(1.5)
        time.sleep(1.5)  # small pause between batches to stay under token budget

    state["diagnoses"] = diagnoses
    return state