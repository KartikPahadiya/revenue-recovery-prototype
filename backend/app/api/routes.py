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
