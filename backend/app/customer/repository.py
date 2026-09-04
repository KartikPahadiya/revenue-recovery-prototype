import json
import os
import re
from copy import deepcopy
from datetime import datetime, timedelta

from app.customer.profile import CustomerProfile


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROFILE_PATH = os.path.abspath(os.path.join(DATA_DIR, "customer_profiles.json"))


def resolve_customer_id(txn: dict) -> str:
    if txn.get("customer_id"):
        return str(txn["customer_id"])
    if txn.get("customer_email"):
        return f"CUST_{_slug(txn['customer_email'])}"
    if txn.get("customer_name"):
        return f"CUST_{_slug(txn['customer_name'])}"
    return f"CUST_{txn.get('transaction_id', 'UNKNOWN')}"


def get_customer_profile(customer_id: str) -> dict | None:
    return deepcopy(_load_profiles().get(customer_id))


def get_or_create_customer_profile(txn: dict) -> dict:
    profiles = _load_profiles()
    customer_id = resolve_customer_id(txn)
    existing = profiles.get(customer_id)
    if existing:
        profile = _apply_transaction_history(_normalize_profile(existing, txn), txn)
        profiles[customer_id] = profile
        _save_profiles(profiles)
        return deepcopy(profile)

    profile = _apply_transaction_history(CustomerProfile(
        customer_id=customer_id,
        email=txn.get("customer_email", ""),
        name=txn.get("customer_name", ""),
    ).to_dict(), txn)
    profiles[customer_id] = profile
    _save_profiles(profiles)
    return deepcopy(profile)


def record_contact(customer_id: str, used_discount: bool = False, contacted_at: datetime | None = None) -> dict | None:
    profiles = _load_profiles()
    profile = profiles.get(customer_id)
    if not profile:
        return None

    contacted_at = contacted_at or datetime.utcnow()
    contact_history = _recent_contact_history(profile, contacted_at)
    contact_history.append(contacted_at.isoformat())

    profile["total_contacts"] = int(profile.get("total_contacts", 0)) + 1
    profile["contact_history"] = contact_history
    profile["contacts_last_7_days"] = len(contact_history)
    profile["last_contacted_at"] = contacted_at.isoformat()
    if used_discount:
        profile["discount_uses"] = int(profile.get("discount_uses", 0)) + 1

    profiles[customer_id] = profile
    _save_profiles(profiles)
    return deepcopy(profile)


def record_recovery(customer_id: str, recovered_amount: float, used_discount: bool = False) -> dict | None:
    profiles = _load_profiles()
    profile = profiles.get(customer_id)
    if not profile:
        return None

    profile = _normalize_profile(profile, {})
    profile["successful_recoveries"] = int(profile.get("successful_recoveries", 0)) + 1
    profile["total_recovered"] = round(float(profile.get("total_recovered", 0.0)) + recovered_amount, 2)
    profile["historical_revenue"] = round(float(profile.get("historical_revenue", 0.0)) + recovered_amount, 2)
    profile["lifetime_value"] = profile["historical_revenue"]
    profile["completed_orders"] = int(profile.get("completed_orders", 0)) + 1
    orders = max(int(profile.get("completed_orders", 0)), 1)
    profile["average_order_value"] = round(profile["historical_revenue"] / orders, 2)
    profile["last_recovered_at"] = datetime.utcnow().isoformat()
    if used_discount:
        profile["successful_discount_recoveries"] = int(
            profile.get("successful_discount_recoveries", 0)
        ) + 1

    profiles[customer_id] = profile
    _save_profiles(profiles)
    return deepcopy(profile)


def _load_profiles() -> dict:
    if not os.path.exists(PROFILE_PATH) or os.path.getsize(PROFILE_PATH) == 0:
        return {}
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    if isinstance(data, list):
        return {p["customer_id"]: p for p in data if p.get("customer_id")}
    return data if isinstance(data, dict) else {}


def _save_profiles(profiles: dict):
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)


def _normalize_profile(profile: dict, txn: dict) -> dict:
    profile = dict(profile)
    profile.setdefault("customer_id", resolve_customer_id(txn))
    profile.setdefault("email", txn.get("customer_email", ""))
    profile.setdefault("name", txn.get("customer_name", ""))
    legacy_orders = int(profile.get("total_orders", 0) or 0)
    legacy_revenue = float(profile.get("lifetime_value", 0.0) or 0.0)
    profile.setdefault("completed_orders", legacy_orders)
    profile.setdefault("historical_revenue", legacy_revenue)
    profile.setdefault("lifetime_value", profile.get("historical_revenue", 0.0))
    profile.setdefault("average_order_value", 0.0)
    profile.setdefault("total_at_risk", 0.0)
    profile.setdefault("total_recovered", 0.0)
    profile.setdefault("failed_payments", 0)
    profile.setdefault("failed_subscriptions", 0)
    profile.setdefault("overdue_invoices", 0)
    profile.setdefault("abandoned_carts", 0)
    profile.setdefault("successful_recoveries", profile.get("recovered_transactions", 0))
    profile.setdefault("total_contacts", 0)
    profile.setdefault("contact_history", [])
    profile["contacts_last_7_days"] = contacts_last_7_days(profile)
    profile.setdefault("discount_uses", 0)
    profile.setdefault("successful_discount_recoveries", 0)
    profile.setdefault("preferred_categories", [])
    profile.setdefault("traits", [])
    profile["lifetime_value"] = profile["historical_revenue"]
    orders = int(profile.get("completed_orders", 0) or 0)
    if orders:
        profile["average_order_value"] = round(float(profile.get("historical_revenue", 0.0)) / orders, 2)
    return profile


def contacts_last_7_days(profile: dict, now: datetime | None = None) -> int:
    return len(_recent_contact_history(profile, now or datetime.utcnow()))


def _recent_contact_history(profile: dict, now: datetime) -> list[str]:
    cutoff = now - timedelta(days=7)
    recent = []
    for raw_ts in profile.get("contact_history", []):
        parsed = _parse_datetime(raw_ts)
        if parsed and parsed >= cutoff:
            recent.append(parsed.isoformat())
    return recent


def _apply_transaction_history(profile: dict, txn: dict) -> dict:
    profile = _normalize_profile(profile, txn)
    amount = _amount(txn)
    leak_type = txn.get("leak_type", "")
    seen = set(profile.get("seen_transaction_ids", []))
    transaction_id = txn.get("transaction_id")
    if transaction_id and transaction_id in seen:
        return profile

    if transaction_id:
        seen.add(transaction_id)
        profile["seen_transaction_ids"] = sorted(seen)

    profile["total_at_risk"] = round(float(profile.get("total_at_risk", 0.0)) + amount, 2)
    profile["last_seen_at"] = txn.get("timestamp") or datetime.utcnow().isoformat()
    if txn.get("customer_email") and not profile.get("email"):
        profile["email"] = txn["customer_email"]
    if txn.get("customer_name") and not profile.get("name"):
        profile["name"] = txn["customer_name"]

    if leak_type == "checkout_abandonment":
        profile["abandoned_carts"] = int(profile.get("abandoned_carts", 0)) + 1
    elif leak_type == "failed_payment":
        profile["failed_payments"] = int(profile.get("failed_payments", 0)) + 1
    elif leak_type == "failed_subscription":
        profile["failed_subscriptions"] = int(profile.get("failed_subscriptions", 0)) + 1
    elif leak_type == "overdue_invoice":
        profile["overdue_invoices"] = int(profile.get("overdue_invoices", 0)) + 1

    return _normalize_profile(profile, txn)


def _parse_datetime(raw_ts: str) -> datetime | None:
    if not raw_ts:
        return None
    try:
        return datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug.upper() or "UNKNOWN"


def _amount(txn: dict) -> float:
    try:
        return round(float(txn.get("amount", 0.0)), 2)
    except (TypeError, ValueError):
        return 0.0
