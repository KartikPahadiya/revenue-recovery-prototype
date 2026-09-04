from dataclasses import asdict, dataclass, field


@dataclass
class CustomerProfile:
    customer_id: str
    email: str = ""
    name: str = ""

    completed_orders: int = 0
    historical_revenue: float = 0.0
    lifetime_value: float = 0.0
    average_order_value: float = 0.0
    total_at_risk: float = 0.0
    total_recovered: float = 0.0

    failed_payments: int = 0
    failed_subscriptions: int = 0
    overdue_invoices: int = 0
    abandoned_carts: int = 0
    successful_recoveries: int = 0

    total_contacts: int = 0
    contacts_last_7_days: int = 0
    contact_history: list[str] = field(default_factory=list)

    discount_uses: int = 0
    successful_discount_recoveries: int = 0
    preferred_categories: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
