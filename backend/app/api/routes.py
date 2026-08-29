import csv
import os
import json
import uuid
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.orchestrator import recovery_graph
from app.agents.state import RecoveryState
from app.agents.state import pipeline_status, update_status
from app.agents.baseline import run_naive_baseline

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BASE_DATA_PATH = os.path.join(DATA_DIR, "transactions.csv")
USER_SUBMISSIONS_PATH = os.path.join(DATA_DIR, "user_submissions.json")


class TransactionSubmission(BaseModel):
    customer_name: str
    amount: float
    payment_method: str
    failure_reason: str
    leak_type: str = "failed_payment"


def load_base_transactions():
    with open(BASE_DATA_PATH, newline="") as f:
        return list(csv.DictReader(f))


def load_user_submissions():
    if not os.path.exists(USER_SUBMISSIONS_PATH):
        return []
    with open(USER_SUBMISSIONS_PATH) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_user_submission(txn: dict):
    submissions = load_user_submissions()
    submissions.append(txn)
    with open(USER_SUBMISSIONS_PATH, "w") as f:
        json.dump(submissions, f, indent=2)


@router.get("/pipeline-status")
def get_pipeline_status():
    return pipeline_status


@router.post("/submit-transaction")
def submit_transaction(payload: TransactionSubmission):
    txn = {
        "leak_type": payload.leak_type,
        "transaction_id": f"USR{uuid.uuid4().hex[:8].upper()}",
        "customer_name": payload.customer_name,
        "amount": payload.amount,
        "payment_method": payload.payment_method,
        "failure_reason": payload.failure_reason,
        "retry_count": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    save_user_submission(txn)
    print(f"[submit] new transaction from {payload.customer_name}: {txn['transaction_id']}")
    return {"status": "ok", "transaction_id": txn["transaction_id"]}


@router.delete("/user-submissions")
def clear_user_submissions():
    """Lets you reset between demo runs without touching the base synthetic data."""
    with open(USER_SUBMISSIONS_PATH, "w") as f:
        json.dump([], f)
    print("[submissions] cleared all user submissions")
    return {"status": "ok"}


@router.get("/submissions-count")
def submissions_count():
    return {"count": len(load_user_submissions())}


@router.get("/transactions")
def get_transactions(source: str = "sample"):
    if source == "user":
        return load_user_submissions()
    return load_base_transactions()


@router.post("/run-batch")
def run_batch(limit: int | None = None, source: str = "sample"):
    print(f"[run-batch] request received (limit={limit}, source={source})")
    update_status("detect", message="Starting...")

    if source == "user":
        transactions = load_user_submissions()
        if not transactions:
            return {
                "total_at_risk": 0,
                "total_recovered": 0,
                "recovery_rate": 0,
                "escalated_count": 0,
                "halted": True,
                "halt_reason": "No user-submitted transactions yet. Scan the QR code to add some first.",
                "audit_trail": [],
                "source": "user",
            }
    else:
        transactions = load_base_transactions()

    if limit:
        transactions = transactions[:limit]
    print(f"[run-batch] processing {len(transactions)} transactions from '{source}' dataset...")

    initial_state: RecoveryState = {
        "transactions": transactions,
        "diagnoses": [],
        "allocation": [],
        "decisions": [],
        "results": [],
        "audit_trail": [],
        "halted": False,
        "halt_reason": "",
    }

    final_state = recovery_graph.invoke(initial_state)
    print(f"[run-batch] done. halted={final_state['halted']}")

    if final_state["halted"]:
        return {
            "total_at_risk": sum(float(t["amount"]) for t in transactions),
            "total_recovered": 0,
            "recovery_rate": 0,
            "escalated_count": 0,
            "halted": True,
            "halt_reason": final_state["halt_reason"],
            "audit_trail": [],
            "source": source,
        }

    total_at_risk = sum(float(t["amount"]) for t in transactions)
    total_recovered = sum(r["amount_recovered"] for r in final_state["results"])
    escalated_count = sum(1 for r in final_state["results"] if r["outcome"] == "escalated")

    return {
        "total_at_risk": round(total_at_risk, 2),
        "total_recovered": round(total_recovered, 2),
        "recovery_rate": round(total_recovered / total_at_risk, 4) if total_at_risk else 0,
        "escalated_count": escalated_count,
        "halted": False,
        "halt_reason": "",
        "audit_trail": final_state["audit_trail"],
        "source": source,
    }


@router.post("/run-comparison")
def run_comparison(limit: int | None = None, source: str = "sample"):
    """
    Run both the AI agent and a naive baseline on the SAME batch,
    then return side-by-side comparison metrics.
    """
    print(f"[run-comparison] request received (limit={limit}, source={source})")

    if source == "user":
        transactions = load_user_submissions()
        if not transactions:
            return {
                "halted": True,
                "halt_reason": "No user-submitted transactions yet. Scan the QR code to add some first.",
            }
    else:
        transactions = load_base_transactions()

    if limit:
        transactions = transactions[:limit]

    # --- AI Agent run ---
    update_status("detect", message="Starting AI agent pipeline...")
    ai_state: RecoveryState = {
        "transactions": transactions,
        "diagnoses": [],
        "allocation": [],
        "decisions": [],
        "results": [],
        "audit_trail": [],
        "halted": False,
        "halt_reason": "",
    }
    ai_final = recovery_graph.invoke(ai_state)

    total_at_risk = sum(float(t["amount"]) for t in transactions)
    ai_recovered = sum(r["amount_recovered"] for r in ai_final["results"])
    ai_escalated = sum(1 for r in ai_final["results"] if r["outcome"] == "escalated")
    ai_real_links = sum(1 for r in ai_final["results"] if r.get("execution_mode") == "real_razorpay_link")

    # --- Naive baseline run ---
    baseline = run_naive_baseline(transactions)

    # --- Comparison ---
    improvement = round(ai_recovered - baseline["total_recovered"], 2)
    improvement_pct = round((improvement / baseline["total_recovered"]) * 100, 2) if baseline["total_recovered"] > 0 else 0

    ai_data = {
        "total_at_risk": round(total_at_risk, 2),
        "total_recovered": round(ai_recovered, 2),
        "recovery_rate": round(ai_recovered / total_at_risk, 4) if total_at_risk else 0,
        "escalated_count": ai_escalated,
        "real_razorpay_links": ai_real_links,
        "has_negotiation": any(r.get("action_taken") == "negotiate" for r in ai_final["results"]),
        "fraud_blocked": any(
            d.get("category") == "fraud_risk" and d.get("action") == "do_not_touch"
            for d in ai_final.get("decisions", [])
        ),
    }

    return {
        "halted": False,
        "batch_size": len(transactions),
        "ai_agent": ai_data,
        "naive_baseline": baseline,
        "comparison": {
            "extra_recovered": improvement,
            "extra_recovered_percent": improvement_pct,
            "fraud_exposure_prevented": baseline["fraud_retried"],
            "escalations_only_by_ai": ai_escalated,
            "summary": f"AI recovered ₹{improvement} more than naive retry-all ({improvement_pct}% improvement)",
        },
    }


@router.get("/test-razorpay")
def test_razorpay():
    """Debug endpoint: test Razorpay connectivity directly."""
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")

    if not key_id or not key_secret:
        return {"configured": False, "error": "RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set"}

    try:
        from app.utils.razorpay_client import create_test_payment_link
        link_id, short_url = create_test_payment_link(
            customer_name="Test User",
            amount=1.0,
            description="Razorpay connectivity test",
        )
        return {
            "configured": True,
            "test_link_created": True,
            "link_id": link_id,
            "short_url": short_url,
        }
    except Exception as e:
        return {
            "configured": True,
            "test_link_created": False,
            "error": str(e),
        }
