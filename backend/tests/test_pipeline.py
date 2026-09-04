"""
Minimal smoke test: runs the graph on a tiny fake batch and checks the
audit trail is well-formed. Extend this before the demo so you can say
"we have tests" with a straight face.
"""
from datetime import datetime

from app.agents.orchestrator import recovery_graph
from app.agents.customer_segment_agent import segment_customer
from app.agents.negotiation_agent import clamp_offer
from app.agents.policy_engine import decide_node
from app import config
from app.customer.repository import (
    PROFILE_PATH,
    get_or_create_customer_profile,
    record_contact,
    record_recovery,
)


def test_pipeline_runs_end_to_end():
    fake_batch = [{
        "leak_type": "failed_payment",
        "transaction_id": "TXN_TEST_1",
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "customer_id": "CUST_TEST",
        "amount": "1000",
        "payment_method": "card",
        "failure_reason": "bank_server_down",
        "retry_count": "0",
        "timestamp": "2026-08-01T10:00:00",
    }]

    state = {
        "transactions": fake_batch, "diagnoses": [], "customer_profiles": [],
        "customer_segments": [], "allocation": [], "decisions": [],
        "negotiations": [], "personalizations": [], "results": [], "audit_trail": [],
        "halted": False, "halt_reason": "",
    }
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        original_profiles = f.read()

    try:
        result = recovery_graph.invoke(state)
    finally:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            f.write(original_profiles)

    assert "audit_trail" in result
    assert result["audit_trail"][0]["customer_segment"]


def _with_profiles_file(payload="{}"):
    class ProfileFileGuard:
        def __enter__(self):
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                self.original = f.read()
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                f.write(payload)

        def __exit__(self, *_):
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                f.write(self.original)

    return ProfileFileGuard()


def test_repeated_abandonment_updates_existing_profile():
    txn_1 = {
        "transaction_id": "CART_A",
        "customer_id": "CUST_REPEAT",
        "customer_name": "Repeat User",
        "customer_email": "repeat@example.com",
        "leak_type": "checkout_abandonment",
        "amount": "900",
        "timestamp": "2026-09-01T10:00:00",
    }
    txn_2 = {**txn_1, "transaction_id": "CART_B", "amount": "1100"}

    with _with_profiles_file():
        get_or_create_customer_profile(txn_1)
        profile = get_or_create_customer_profile(txn_2)

    assert profile["abandoned_carts"] == 2
    assert profile["total_at_risk"] == 2000
    assert profile["completed_orders"] == 0
    assert profile["historical_revenue"] == 0


def test_contact_history_expires_after_seven_days():
    with _with_profiles_file('{"CUST_CONTACT": {"customer_id": "CUST_CONTACT", "contact_history": ["2026-08-01T10:00:00"]}}'):
        profile = record_contact(
            "CUST_CONTACT",
            contacted_at=datetime(2026, 9, 4, 10, 0, 0),
        )

    assert profile["contacts_last_7_days"] == 1
    assert profile["contact_history"] == ["2026-09-04T10:00:00"]


def test_high_value_segmentation_includes_reason():
    result = segment_customer({
        "customer_id": "CUST_HIGH",
        "historical_revenue": 32000,
        "completed_orders": 12,
        "contact_history": [],
    })

    assert result["segment"] == "HIGH_VALUE"
    assert "₹20,000" in result["segment_reason"]


def test_price_sensitive_segmentation():
    result = segment_customer({
        "customer_id": "CUST_PRICE",
        "historical_revenue": 6000,
        "completed_orders": 4,
        "successful_discount_recoveries": 2,
        "contact_history": [],
    })

    assert result["segment"] == "PRICE_SENSITIVE"


def test_contact_throttle_returns_do_not_touch():
    state = {
        "transactions": [{
            "transaction_id": "CART_LIMIT",
            "leak_type": "checkout_abandonment",
            "amount": "1500",
            "retry_count": "0",
        }],
        "diagnoses": [{"transaction_id": "CART_LIMIT", "category": "customer_issue"}],
        "customer_profiles": [{
            "transaction_id": "CART_LIMIT",
            "profile": {"customer_id": "CUST_LIMIT", "contacts_last_7_days": 2},
        }],
        "customer_segments": [{
            "transaction_id": "CART_LIMIT",
            "segment": "AT_RISK",
            "segment_reason": "Recent contact pressure.",
            "traits": ["CONTACT_LIMITED"],
        }],
        "allocation": [{"transaction_id": "CART_LIMIT", "expected_value_score": 100}],
        "decisions": [],
        "halted": False,
    }

    result = decide_node(state)

    assert result["decisions"][0]["action"] == "do_not_touch"


def test_large_overdue_invoice_gets_negotiation_with_approval():
    state = {
        "transactions": [{
            "transaction_id": "INV_BIG",
            "leak_type": "overdue_invoice",
            "amount": "80000",
            "retry_count": "0",
        }],
        "diagnoses": [{"transaction_id": "INV_BIG", "category": "customer_issue"}],
        "customer_profiles": [{
            "transaction_id": "INV_BIG",
            "profile": {"customer_id": "CUST_INV", "contacts_last_7_days": 0},
        }],
        "customer_segments": [{
            "transaction_id": "INV_BIG",
            "segment": "HIGH_VALUE",
            "segment_reason": "Historical recovered/completed revenue is at least ₹20,000.",
            "traits": [],
        }],
        "allocation": [{"transaction_id": "INV_BIG", "expected_value_score": 1000}],
        "decisions": [],
        "halted": False,
    }

    result = decide_node(state)

    assert result["decisions"][0]["action"] == "negotiate"
    assert result["decisions"][0]["requires_human_approval"] is True


def test_negotiation_discount_cap_is_enforced():
    assert clamp_offer("discount", config.DISCOUNT_CAP_PERCENT + 25) == config.DISCOUNT_CAP_PERCENT


def test_recovery_does_not_double_count_attempted_value():
    txn = {
        "transaction_id": "CART_DOUBLE",
        "customer_id": "CUST_DOUBLE",
        "customer_name": "Careful User",
        "customer_email": "careful@example.com",
        "leak_type": "checkout_abandonment",
        "amount": "1975",
        "timestamp": "2026-09-01T10:00:00",
    }

    with _with_profiles_file():
        profile = get_or_create_customer_profile(txn)
        recovered = record_recovery("CUST_DOUBLE", 1975, used_discount=True)

    assert profile["historical_revenue"] == 0
    assert profile["total_at_risk"] == 1975
    assert recovered["historical_revenue"] == 1975
    assert recovered["total_recovered"] == 1975
    assert recovered["completed_orders"] == 1
