"""
Detector: pure rules/statistics, NO LLM. Flags which transactions are worth
looking at at all, and computes a simple data-quality signal (this is what
the orchestrator uses to decide whether to halt the pipeline).
"""
from typing import Dict, Any
from app.agents.state import RecoveryState
from app.agents.state import update_status


def detect_node(state: RecoveryState) -> RecoveryState:
    update_status("detect", message="Checking data quality...")
    txns = state["transactions"]

    # crude data-quality check: are required fields present/sane?
    bad_rows = [t for t in txns if not t.get("amount") or float(t["amount"]) <= 0]
    match_rate = 1 - (len(bad_rows) / max(len(txns), 1))

    state["halted"] = match_rate < 0.85
    state["halt_reason"] = (
        f"Data quality too low to proceed: {match_rate:.0%} of rows are usable "
        f"(need >= 85%). Fix the input batch before recovery actions can be trusted."
        if state["halted"] else ""
    )
    return state
