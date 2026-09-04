"""
Shared state that flows through every LangGraph node.
Each node reads what it needs and appends its own output --
nothing gets overwritten, which is what makes the audit trail possible.
"""
from typing import TypedDict, List, Dict, Any


class RecoveryState(TypedDict):
    transactions: List[Dict[str, Any]]
    diagnoses: List[Dict[str, Any]]
    customer_profiles: List[Dict[str, Any]]
    customer_segments: List[Dict[str, Any]]
    allocation: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    negotiations: List[Dict[str, Any]]      # was missing from the TypedDict too
    personalizations: List[Dict[str, Any]]  # NEW
    results: List[Dict[str, Any]]
    audit_trail: List[Dict[str, Any]]
    halted: bool
    halt_reason: str


# Shared, in-memory pipeline status the frontend polls during a run.
# Simple module-level dict is fine for a single-user hackathon demo.
pipeline_status = {
    "stage": "idle",
    "current": 0,
    "total": 0,
    "message": "",
}


def update_status(stage, current=0, total=0, message=""):
    pipeline_status["stage"] = stage
    pipeline_status["current"] = current
    pipeline_status["total"] = total
    pipeline_status["message"] = message
