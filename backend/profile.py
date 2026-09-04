from dataclasses import dataclass, field

@dataclass
class CustomerProfile:
    customer_id: str
    email: str

    total_orders: int = 0
    lifetime_value: float = 0.0
    average_order_value: float = 0.0

    failed_payments: int = 0
    abandoned_carts: int = 0
    recovered_transactions: int = 0

    total_contacts: int = 0
    contacts_last_7_days: int = 0

    discount_uses: int = 0
    successful_discount_recoveries: int = 0