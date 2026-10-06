"""
Tests for Human Handoff and Manager Mode in Sahayak Voice V2.
Validates:
1. Manager speaks FIRST immediately upon connection.
2. Customer does NOT have to say "hello".
3. AI mode stops; callMode switches to "human".
4. Manager receives full prior case context.
5. Manager can resolve questions and naturally close the call.
"""

import pytest
from app.agent.graph import SahayakAgent
from app.agent.nodes.handoff import handleHandoff, startHumanConversation
from app.agent.state import CallState
from app.tools.banking import getAccountSnapshot


def test_manager_speaks_first_immediately():
    agent = SahayakAgent()
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    state: CallState = {
        "sessionId": "test-ho-1",
        "accountId": "ACC-LIEN-PRIYA",
        "customerName": "Pratik Sharma",
        "caseType": "LIEN",
        "phase": "conversation",
        "callMode": "ai",
        "verified": True,
        "snapshot": snap,
        "accountFacts": snap,
        "messages": [
            {"role": "user", "content": "મારે મેનેજર સાથે વાત કરવી છે."}
        ],
        "lastUserText": "મારે મેનેજર સાથે વાત કરવી છે.",
        "proof": {
            "callMemory": {
                "lastCustomerQuestion": "લિયન કેમ લાગ્યું અને પૈસા ક્યારે છૂટશે?",
            }
        },
    }

    # Customer turn requesting manager
    updated = agent.processTurn(state)
    assert updated.get("phase") == "handoff_connecting"
    assert updated.get("speaker") == "Sahayak"
    assert "મેનેજર" in (updated.get("lastAgentReply") or "")

    # Manager speaks FIRST immediately upon connection
    updated = agent.processTurn(updated)

    # Assertions
    assert updated["handoffRequested"] is True
    assert updated["handoffComplete"] is True
    assert updated["callMode"] == "human"
    assert updated["phase"] == "handoff"
    assert updated["speaker"] == "Senior Manager"
    assert updated["assignedAgentName"] == "વિક્રમ મહેતા"

    # Manager spoke FIRST! Text contains manager greeting and context
    reply = updated["lastAgentReply"]
    assert "નમસ્તે Pratikભાઈ" in reply or "નમસ્તે" in reply
    assert "સિનિયર મેનેજર" in reply
    assert "લિયન" in reply


def test_manager_receives_and_continues_conversation():
    agent = SahayakAgent()
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    state: CallState = {
        "sessionId": "test-ho-2",
        "accountId": "ACC-LIEN-PRIYA",
        "customerName": "Pratik Sharma",
        "caseType": "LIEN",
        "phase": "handoff",
        "callMode": "human",
        "handoffComplete": True,
        "verified": True,
        "snapshot": snap,
        "accountFacts": snap,
        "speaker": "Senior Manager",
        "messages": [
            {"role": "assistant", "speaker": "Senior Manager", "content": "નમસ્તે! હું સિનિયર મેનેજર બોલું છું."}
        ],
        "lastUserText": "સાહેબ આ રકમ ક્યારે અનફ્રીઝ થશે?",
    }

    updated = agent.processTurn(state)

    # Remains in human mode, manager replies
    assert updated["callMode"] == "human"
    assert updated["speaker"] == "Senior Manager"
    assert len(updated["lastAgentReply"]) > 10


def test_manager_closes_call_naturally():
    agent = SahayakAgent()
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    state: CallState = {
        "sessionId": "test-ho-3",
        "accountId": "ACC-LIEN-PRIYA",
        "customerName": "Pratik Sharma",
        "caseType": "LIEN",
        "phase": "handoff",
        "callMode": "human",
        "handoffComplete": True,
        "verified": True,
        "snapshot": snap,
        "accountFacts": snap,
        "speaker": "Senior Manager",
        "messages": [],
        "lastUserText": "સમજાઈ ગયું સાહેબ, તમારો ખૂબ ખૂબ આભાર.",
    }

    updated = agent.processTurn(state)

    # Call ends cleanly
    assert updated["phase"] == "end"
    assert updated["callEnded"] is True
    assert updated["callMode"] == "ended"
    assert "આભાર" in updated["lastAgentReply"]
