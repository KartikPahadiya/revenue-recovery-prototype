"""
LangGraph wiring. This is the "orchestrator" that mirrors the video's
plugin/orchestrator: fixed execution order, dependency checks, and a hard
stop if a data-quality gate fails -- so a bad batch never silently produces
a confident-looking wrong report.
"""
from langgraph.graph import StateGraph, END
from app.agents.state import RecoveryState
from app.agents.detector_agent import detect_node
from app.agents.diagnosis_agent import diagnose_node
from app.agents.allocator import allocate_node
from app.agents.policy_engine import decide_node
from app.agents.negotiation_agent import negotiate_node
from app.agents.executor import execute_node
from app.agents.state import update_status

def route_after_detect(state: RecoveryState) -> str:
    return "halted" if state.get("halted") else "continue"


def build_graph():
    graph = StateGraph(RecoveryState)

    graph.add_node("detect", detect_node)
    graph.add_node("diagnose", diagnose_node)
    graph.add_node("allocate", allocate_node)
    graph.add_node("decide", decide_node)
    graph.add_node("negotiate", negotiate_node)
    graph.add_node("execute", execute_node)
    graph.add_node("build_audit_trail", build_audit_trail_node)

    graph.set_entry_point("detect")

    # conditional edge: only proceed past detection if data quality passes
    graph.add_conditional_edges(
        "detect",
        route_after_detect,
        {"continue": "diagnose", "halted": "build_audit_trail"},
    )

    graph.add_edge("diagnose", "allocate")
    graph.add_edge("allocate", "decide")
    graph.add_edge("decide", "negotiate")
    graph.add_edge("negotiate", "execute")
    graph.add_edge("execute", "build_audit_trail")
    graph.add_edge("build_audit_trail", END)

    return graph.compile()


def build_audit_trail_node(state: RecoveryState) -> RecoveryState:
    update_status("done", message="Complete")
    if state.get("halted"):
        state["audit_trail"] = []
        return state

    diag_by_id = {d["transaction_id"]: d for d in state["diagnoses"]}
    decision_by_id = {d["transaction_id"]: d for d in state["decisions"]}
    result_by_id = {r["transaction_id"]: r for r in state["results"]}
    negotiation_by_id = {n["transaction_id"]: n for n in state.get("negotiations", [])}

    trail = []
    for txn in state["transactions"]:
        tid = txn["transaction_id"]
        trail.append({
            "transaction_id": tid,
            "diagnosis": diag_by_id.get(tid, {}),
            "decision": decision_by_id.get(tid, {}),
            "result": result_by_id.get(tid, {}),
            "negotiation": negotiation_by_id.get(tid),
        })

    state["audit_trail"] = trail
    return state


recovery_graph = build_graph()
