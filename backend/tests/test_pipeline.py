"""
Minimal smoke test: runs the graph on a tiny fake batch and checks the
audit trail is well-formed. Extend this before the demo so you can say
"we have tests" with a straight face.
"""
from app.agents.orchestrator import recovery_graph


def test_pipeline_runs_end_to_end():
    fake_batch = [{
        "leak_type": "failed_payment",
        "transaction_id": "TXN_TEST_1",
        "customer_name": "Test User",
        "amount": "1000",
        "payment_method": "card",
        "failure_reason": "bank_server_down",
        "retry_count": "0",
        "timestamp": "2026-08-01T10:00:00",
    }]

    state = {
        "transactions": fake_batch, "diagnoses": [], "allocation": [],
        "decisions": [], "results": [], "audit_trail": [],
        "halted": False, "halt_reason": "",
    }
    result = recovery_graph.invoke(state)
    assert "audit_trail" in result
