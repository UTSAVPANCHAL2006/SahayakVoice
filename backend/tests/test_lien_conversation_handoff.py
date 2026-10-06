"""Focused tests: lien balance questions + two-step handoff."""

from app.agent.grounding import explainFundsFromSnapshot, groundedReplyForQuestion
from app.agent.graph import SahayakAgent
from app.tools.banking import getAccountSnapshot


def test_lien_balance_explanation_not_generic_branch():
    snap = getAccountSnapshot("ACC-LIEN-PRIYA", None)
    reply = groundedReplyForQuestion(
        "pan saheb mari pase total 52000 hata baki na paisa kya gya",
        snap,
        "Pratik Sharma",
    )
    assert reply
    assert "52,783" in reply or "52783" in reply
    assert "38,419" in reply or "38419" in reply
    assert "14,364" in reply or "14364" in reply
    assert "બ્રાન્ચ" not in reply or "લિયન" in reply


def test_handoff_ack_then_manager_speaks_first():
    agent = SahayakAgent()
    snap = getAccountSnapshot("ACC-LIEN-PRIYA", None)
    state = {
        "sessionId": "t1",
        "accountId": "ACC-LIEN-PRIYA",
        "customerName": snap["customerName"],
        "caseType": "LIEN",
        "phase": "conversation",
        "callMode": "ai",
        "verified": True,
        "messages": [],
        "snapshot": snap,
        "accountFacts": snap,
        "proof": {},
    }
    state["lastUserText"] = "mare manager sathe vat krvi che"
    state = agent.processTurn(state, None)
    assert state.get("phase") == "handoff_connecting"
    assert state.get("speaker") == "Sahayak"
    assert "મેનેજર" in (state.get("lastAgentReply") or "")

    state = agent.processTurn(state, None)
    assert state.get("callMode") == "human"
    assert state.get("speaker") == "Senior Manager"
    assert (state.get("lastAgentReply") or "").strip()
