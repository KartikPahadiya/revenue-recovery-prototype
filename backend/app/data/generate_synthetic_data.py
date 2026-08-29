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
    all_rows = (
        generate_failed_payments(300)
        + generate_failed_subscriptions(100)
        + generate_overdue_invoices(15)
    )
    random.shuffle(all_rows)

    fieldnames = sorted({key for row in all_rows for key in row.keys()})
    out_path = os.path.join(OUT_DIR, "transactions.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} synthetic records to {out_path}")


if __name__ == "__main__":
    main()
