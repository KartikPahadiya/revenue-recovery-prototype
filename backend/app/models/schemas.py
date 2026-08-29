"""
Pydantic models used by the API layer and, loosely, by the agents.
Keeping these separate from agents/state.py: this file is the *external*
contract (API request/response); state.py is the *internal* LangGraph state.
"""
from pydantic import BaseModel
from typing import Optional, List


class Transaction(BaseModel):
    leak_type: str            # failed_payment | failed_subscription | overdue_invoice
    transaction_id: str
    customer_name: str
    amount: float
    payment_method: str
    failure_reason: str
    retry_count: int = 0
    timestamp: str


class DiagnosisResult(BaseModel):
    transaction_id: str
    category: str             # temporary_issue | customer_issue | bank_issue | fraud_risk
    explanation: str


class PolicyDecision(BaseModel):
    transaction_id: str
    action: str                # retry_now | retry_delayed | notify_customer |
                                # negotiate | escalate_human | do_not_touch
    rule_applied: str
    priority_score: float


class ActionResult(BaseModel):
    transaction_id: str
    action_taken: str
    outcome: str
    amount_recovered: float
    payment_link_id: Optional[str] = None
    payment_link_url: Optional[str] = None


class AuditLogEntry(BaseModel):
    transaction_id: str
    diagnosis: DiagnosisResult
    decision: PolicyDecision
    result: ActionResult


class BatchRunResponse(BaseModel):
    total_at_risk: float
    total_recovered: float
    recovery_rate: float
    escalated_count: int
    halted: bool
    halt_reason: Optional[str] = None
    audit_trail: List[AuditLogEntry]
