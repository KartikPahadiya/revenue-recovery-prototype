"""
Shared state that flows through every LangGraph node.
Each node reads what it needs and appends its own output --
nothing gets overwritten, which is what makes the audit trail possible.
"""
from typing import TypedDict, List, Dict, Any


class RecoveryState(TypedDict):
    transactions: List[Dict[str, Any]]       # raw batch loaded from CSV
    diagnoses: List[Dict[str, Any]]          # output of diagnosis_agent
    allocation: List[Dict[str, Any]]         # output of allocator (priority order)
    decisions: List[Dict[str, Any]]          # output of policy_engine
    results: List[Dict[str, Any]]            # output of action executor
    audit_trail: List[Dict[str, Any]]        # final merged, per-transaction record
    halted: bool                             # set True if a data-quality gate fails
    halt_reason: str


# Shared, in-memory pipeline status the frontend polls during a run.
# Simple module-level dict is fine for a single-user hackathon demo.
pipeline_status = {
    "stage": "idle",       # idle | detect | diagnose | allocate | decide | negotiate | execute | done
    "current": 0,
    "total": 0,
    "message": "",
}


def update_status(stage, current=0, total=0, message=""):
    pipeline_status["stage"] = stage
    pipeline_status["current"] = current
    pipeline_status["total"] = total
    pipeline_status["message"] = message