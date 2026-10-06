"""
End-to-End Tests for all 5 Retail Banking Cases in Sahayak Voice V2:
1. Cheque Bounce (Hardik Patel, ACC-CHQ-HARDIK)
2. Lien (Priya Sharma, ACC-LIEN-PRIYA)
3. Hold / UPI Pending (Amit Singh, ACC-HOLD-AMIT)
4. Debit Freeze (Vikram Mehta, ACC-FREEZE-VIKRAM)
5. Inoperative Account (Sunita Rao, ACC-INOP-SUNITA)

Validates the full workflow for EACH case:
START -> Greet -> Consent -> Verify -> Fetch -> Explain -> Question -> Manager Request -> Manager Speaks FIRST -> Manager Resolve -> Manager Close -> End.
"""

import pytest
from app.agent.graph import SahayakAgent
from app.tools.banking import listScenarioAccounts


@pytest.mark.parametrize("scenario", listScenarioAccounts())
def test_full_e2e_flow_for_all_five_cases(scenario):
    account_id = scenario["accountId"]
    expected_last4 = scenario["expectedLast4"]
    agent = SahayakAgent()

    # Step 1: START & Greeting
    state = {
        "sessionId": f"e2e-{account_id}",
        "accountId": account_id,
        "phase": "connecting",
        "verified": False,
        "callMode": "ai",
        "messages": [],
    }
    state = agent.initializeCall(state)

    assert state["phase"] == "consent"
    assert state["speaker"] == "Sahayak"
    assert "સહાયક બેંકમાંથી" in state["lastAgentReply"]

    # Step 2: Customer gives Consent
    state["lastUserText"] = "હા બોલો, હું સાંભળું છું."
    state = agent.processTurn(state)

    assert state["phase"] == "verify"
    assert "છેલ્લા ૪ આંકડા" in state["lastAgentReply"]

    # Step 3: Customer provides Last 4 Digits (Verification)
    state["lastUserText"] = f"મારા ખાતાના છેલ્લા આંકડા {expected_last4} છે."
    state = agent.processTurn(state)

    # After verification, fetch and initial explain run automatically
    assert state["verified"] is True
    assert state["phase"] == "conversation"
    assert "તમારી માહિતી ચકાસાઈ ગઈ છે" in state["lastAgentReply"]

    # Step 4: Customer asks arbitrary banking question (e.g. balance or details)
    state["lastUserText"] = "મારા ખાતામાં અત્યારે કેટલા રૂપિયા ઉપલબ્ધ છે?"
    state = agent.processTurn(state)

    assert state["phase"] == "conversation"
    assert any(k in state["lastAgentReply"] for k in ("બેલેન્સ", "રૂપિયા", "₹", "ઉપલબ્ધ", "રકમ"))

    # Step 5: Customer requests to speak with Human Manager
    state["lastUserText"] = "મારે આ બાબતે સિનિયર મેનેજર સાથે વાત કરવી છે."
    state = agent.processTurn(state)

    # 5a: Sahayak FIRST says it will connect the manager
    assert state["phase"] == "handoff_connecting"
    assert state["speaker"] == "Sahayak"
    assert state["handoffRequested"] is True
    assert "મેનેજર" in state["lastAgentReply"]

    # 5b: Transfer happens — Senior Manager AUTOMATICALLY speaks first!
    state = agent.processTurn(state)
    assert state["handoffRequested"] is True
    assert state["handoffComplete"] is True
    assert state["callMode"] == "human"
    assert state["phase"] == "handoff"
    assert state["speaker"] == "Senior Manager"
    assert "નમસ્તે" in state["lastAgentReply"]
    assert "મેનેજર" in state["lastAgentReply"]

    # Step 6: Customer asks question to the Manager
    state["lastUserText"] = "સાહેબ આનું સોલ્યુશન ક્યારે આવશે?"
    state = agent.processTurn(state)

    assert state["callMode"] == "human"
    assert state["speaker"] == "Senior Manager"
    assert len(state["lastAgentReply"]) > 10

    # Step 7: Customer is satisfied and closes
    state["lastUserText"] = "સમજાઈ ગયું સાહેબ, તમારો ખૂબ ખૂબ આભાર."
    state = agent.processTurn(state)

    assert state["phase"] == "end"
    assert state["callEnded"] is True
    assert state["callMode"] == "ended"
    assert "આભાર" in state["lastAgentReply"]
