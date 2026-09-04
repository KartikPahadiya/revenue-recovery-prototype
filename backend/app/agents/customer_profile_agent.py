from app.agents.state import RecoveryState, update_status
from app.customer.repository import get_or_create_customer_profile


def build_customer_profiles_node(state: RecoveryState) -> RecoveryState:
    update_status("profile", message="Building customer profiles...")
    if state.get("halted"):
        return state

    profiles = []
    for txn in state["transactions"]:
        profile = get_or_create_customer_profile(txn)
        profiles.append({
            "transaction_id": txn["transaction_id"],
            "profile": profile,
        })

    state["customer_profiles"] = profiles
    return state
