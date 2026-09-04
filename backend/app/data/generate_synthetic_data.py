"""
Generates a realistic synthetic batch covering the 3 revenue-leak types the
agent handles: failed payments, failed subscriptions (dunning), and overdue
B2B invoices. Column choices are inspired by public Kaggle transaction/churn
datasets (see README) so the shape feels realistic to a judge, but every
value here is fabricated -- no real data is used or needed.

Run: python -m app.data.generate_synthetic_data
"""
import random
import csv
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_IN")
random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__))

FAILURE_REASONS_CARD = [
    "insufficient_funds", "card_expired", "bank_server_down",
    "otp_timeout", "card_declined_by_issuer", "network_error",
]
FAILURE_REASONS_UPI = [
    "bank_server_down", "insufficient_funds", "upi_pin_wrong",
    "mandate_expired", "payer_bank_timeout",
]
PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]

DEMO_PERSONAS = [
    {
        "leak_type": "failed_payment",
        "transaction_id": "DEMO_HIGH_001",
        "customer_id": "CUST_HIGH_001",
        "customer_name": "Aarav Mehta",
        "customer_email": "",
        "amount": 2450.00,
        "payment_method": "card",
        "failure_reason": "card_expired",
        "retry_count": 0,
        "timestamp": "2026-09-04T09:00:00",
    },
    {
        "leak_type": "checkout_abandonment",
        "transaction_id": "DEMO_PRICE_002",
        "customer_id": "CUST_PRICE_002",
        "customer_name": "Meera Shah",
        "customer_email": "",
        "amount": 1875.00,
        "payment_method": "online",
        "failure_reason": "abandoned_cart (shipping_cost): coffee, breakfast cereal, almond milk",
        "items": "coffee, breakfast cereal, almond milk",
        "retry_count": 0,
        "follow_up_count": 0,
        "timestamp": "2026-09-04T09:05:00",
    },
    {
        "leak_type": "checkout_abandonment",
        "transaction_id": "DEMO_RISK_003",
        "customer_id": "CUST_RISK_003",
        "customer_name": "Kabir Rao",
        "customer_email": "",
        "amount": 1650.00,
        "payment_method": "online",
        "failure_reason": "abandoned_cart (just_browsing): protein bars, juice pack",
        "items": "protein bars, juice pack",
        "retry_count": 0,
        "follow_up_count": 1,
        "timestamp": "2026-09-04T09:10:00",
    },
    {
        "leak_type": "checkout_abandonment",
        "transaction_id": "DEMO_NEW_004",
        "customer_id": "CUST_NEW_004",
        "customer_name": "Nisha Iyer",
        "customer_email": "",
        "amount": 620.00,
        "payment_method": "online",
        "failure_reason": "abandoned_cart (comparison_shopping): tea, biscuits",
        "items": "tea, biscuits",
        "retry_count": 0,
        "follow_up_count": 0,
        "timestamp": "2026-09-04T09:15:00",
    },
    {
        "leak_type": "failed_payment",
        "transaction_id": "DEMO_LOYAL_005",
        "customer_id": "CUST_LOYAL_005",
        "customer_name": "Rohan Kapoor",
        "customer_email": "",
        "amount": 3200.00,
        "payment_method": "upi",
        "failure_reason": "bank_server_down",
        "retry_count": 0,
        "timestamp": "2026-09-04T09:20:00",
    },
    {
        "leak_type": "overdue_invoice",
        "transaction_id": "DEMO_INV_006",
        "customer_id": "CUST_INV_006",
        "customer_name": "Northstar Retail Pvt Ltd",
        "customer_email": "",
        "amount": 80000.00,
        "payment_method": "bank_transfer",
        "failure_reason": "overdue",
        "retry_count": 0,
        "due_date": "2026-08-01T00:00:00",
        "days_overdue": 34,
        "timestamp": "2026-08-01T00:00:00",
    },
    {
        "leak_type": "failed_subscription",
        "transaction_id": "DEMO_SUB_007",
        "customer_id": "CUST_SUB_007",
        "customer_name": "Sana Khan",
        "customer_email": "",
        "amount": 999.00,
        "payment_method": "card",
        "failure_reason": "mandate_expired",
        "retry_count": 0,
        "billing_cycle_day": 4,
        "timestamp": "2026-09-04T09:25:00",
    },
    {
        "leak_type": "failed_payment",
        "transaction_id": "DEMO_FRAUD_008",
        "customer_id": "CUST_FRAUD_008",
        "customer_name": "Unknown Buyer",
        "customer_email": "",
        "amount": 42000.00,
        "payment_method": "card",
        "failure_reason": "velocity_check_failed suspected_fraud",
        "retry_count": 0,
        "timestamp": "2026-09-04T09:30:00",
    },
]


def generate_failed_payments(n=300):
    rows = []
    base_time = datetime(2026, 8, 1, 9, 0, 0)
    for i in range(n):
        method = random.choice(PAYMENT_METHODS)
        reasons = FAILURE_REASONS_UPI if method == "upi" else FAILURE_REASONS_CARD
        # simulate clustered bank outages: 20% of rows fall in a "burst" window
        is_burst = random.random() < 0.2
        reason = "bank_server_down" if is_burst else random.choice(reasons)
        rows.append({
            "leak_type": "failed_payment",
            "transaction_id": f"TXN{i:05d}",
            "customer_name": fake.first_name(),
            "amount": round(random.uniform(150, 5000), 2),
            "payment_method": method,
            "failure_reason": reason,
            "retry_count": 0,
            "timestamp": (base_time + timedelta(minutes=random.randint(0, 600))).isoformat(),
        })
    return rows


def generate_failed_subscriptions(n=100):
    rows = []
    reasons = ["card_expired", "insufficient_funds", "bank_declined", "mandate_expired"]
    for i in range(n):
        rows.append({
            "leak_type": "failed_subscription",
            "transaction_id": f"SUB{i:05d}",
            "customer_name": fake.first_name(),
            "amount": round(random.choice([199, 499, 999, 1999]), 2),
            "payment_method": random.choice(["card", "upi"]),
            "failure_reason": random.choice(reasons),
            "retry_count": 0,
            "billing_cycle_day": random.randint(1, 28),
            "timestamp": (datetime(2026, 8, 1) + timedelta(days=random.randint(0, 27))).isoformat(),
        })
    return rows


def generate_overdue_invoices(n=15):
    rows = []
    for i in range(n):
        due_date = datetime(2026, 7, 1) + timedelta(days=random.randint(0, 45))
        rows.append({
            "leak_type": "overdue_invoice",
            "transaction_id": f"INV{i:04d}",
            "customer_name": fake.company(),
            "amount": round(random.uniform(20000, 400000), 2),
            "payment_method": "bank_transfer",
            "failure_reason": "overdue",
            "retry_count": 0,
            "due_date": due_date.isoformat(),
            "days_overdue": (datetime(2026, 8, 15) - due_date).days,
            "timestamp": due_date.isoformat(),
        })
    return rows


def main():
    general_rows = (
        generate_failed_payments(300)
        + generate_failed_subscriptions(100)
        + generate_overdue_invoices(15)
    )
    random.shuffle(general_rows)
    all_rows = DEMO_PERSONAS + general_rows

    fieldnames = sorted({key for row in all_rows for key in row.keys()})
    out_path = os.path.join(OUT_DIR, "transactions.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} synthetic records to {out_path}")


if __name__ == "__main__":
    main()
