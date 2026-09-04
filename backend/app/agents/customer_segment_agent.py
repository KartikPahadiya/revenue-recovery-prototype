from app.agents.state import RecoveryState, update_status


def segment_customer(profile: dict) -> dict:
    historical_revenue = float(profile.get("historical_revenue", profile.get("lifetime_value", 0)) or 0)
    completed_orders = int(profile.get("completed_orders", profile.get("total_orders", 0)) or 0)
    abandoned_carts = int(profile.get("abandoned_carts", 0) or 0)
    contacts_last_7_days = int(profile.get("contacts_last_7_days", 0) or 0)
    successful_recoveries = int(profile.get("successful_recoveries", profile.get("recovered_transactions", 0)) or 0)
    discount_uses = int(profile.get("discount_uses", 0) or 0)
    successful_discount_recoveries = int(profile.get("successful_discount_recoveries", 0) or 0)

    traits = []
    if successful_recoveries >= 2:
        traits.append("RECOVERY_RESPONSIVE")
    if discount_uses >= 3 and successful_discount_recoveries == 0:
        traits.append("DISCOUNT_GUARDED")
    if contacts_last_7_days >= 2:
        traits.append("CONTACT_LIMITED")

    if historical_revenue >= 20000:
        return {
            "segment": "HIGH_VALUE",
            "segment_reason": "Historical recovered/completed revenue is at least ₹20,000.",
            "traits": traits,
        }

    if abandoned_carts >= 3 or contacts_last_7_days >= 2:
        return {
            "segment": "AT_RISK",
            "segment_reason": "Repeated abandonment or recent contact pressure indicates churn risk.",
            "traits": traits,
        }

    if successful_discount_recoveries >= 2:
        return {
            "segment": "PRICE_SENSITIVE",
            "segment_reason": "Multiple previous recoveries succeeded with incentives.",
            "traits": traits,
        }

    if successful_recoveries >= 2:
        return {
            "segment": "RECOVERY_RESPONSIVE",
            "segment_reason": "Customer has recovered successfully multiple times before.",
            "traits": traits,
        }

    if completed_orders <= 1:
        return {
            "segment": "NEW",
            "segment_reason": "Customer has one or fewer completed orders on record.",
            "traits": traits,
        }

    if completed_orders >= 5:
        return {
            "segment": "LOYAL",
            "segment_reason": "Customer has a strong history of completed orders.",
            "traits": traits,
        }

    return {
        "segment": "STANDARD",
        "segment_reason": "Customer history does not match a higher-priority segment.",
        "traits": traits,
    }


def segment_customers_node(state: RecoveryState) -> RecoveryState:
    update_status("segment", message="Segmenting customers...")
    if state.get("halted"):
        return state

    segments = []
    for item in state.get("customer_profiles", []):
        profile = item["profile"]
        segmentation = segment_customer(profile)
        segments.append({
            "transaction_id": item["transaction_id"],
            "customer_id": profile["customer_id"],
            "segment": segmentation["segment"],
            "segment_reason": segmentation["segment_reason"],
            "traits": segmentation["traits"],
        })

    state["customer_segments"] = segments
    return state
