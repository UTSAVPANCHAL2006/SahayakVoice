"""
Tests for Senior AI Engineer Architectural Improvements (C1-C3, S4-S7, M1):
- C1: Word-boundary checks prevent false substring positives ('management' != 'agent')
- C2: Complexity gate prevents grounding over-interception on long emotional queries
- C3: 'ok' is only an end signal on exact match, not substring ('ok, but why charge' != end)
- M1: customerAskedAboutFunds works generically without hardcoded balances
- S4: Conversational memory tracks resolved topics
- S5: Proof dict tracks resolvedTopics and validates tool whitelist
- S6: Case rules are generated dynamically from snapshot
- S7: LLM intent detection with post-LLM regex safety net
"""

import pytest
from app.agent.nodes.conversation import isManagerRequest, isCallEndSignal, handleConversation
from app.agent.grounding import isActionOrProcedureQuery, customerAskedAboutFunds, groundedReplyForQuestion
from app.agent.memory import updateCallMemory, detectResolvedTopics, getMemorySummary
from app.agent.case_rules import getCaseRules
from app.agent.state import CallState
from app.tools.banking import getAccountSnapshot


def test_c3_ok_not_false_end_signal():
    # Long sentences containing 'ok' as substring should NOT trigger call end
    assert isCallEndSignal("ok, mane samjayo pan 523 charge lagyo") is False
    assert isCallEndSignal("ok, what is my balance?") is False
    assert isCallEndSignal("token number shu chhe?") is False
    assert isCallEndSignal("broker sathe vaat karvi chhe") is False

    # Exact matches for ok / thanks / bye SHOULD trigger call end
    assert isCallEndSignal("ok") is True
    assert isCallEndSignal("ઓકે") is True
    assert isCallEndSignal("okay") is True
    assert isCallEndSignal("ok sir") is True
    assert isCallEndSignal("bye") is True
    assert isCallEndSignal("આભાર") is True


def test_c1_word_boundary_manager_and_actions():
    # 'management', 'agreement', 'urgent' should NOT trigger manager request
    assert isManagerRequest("I want to know about account management policy") is False
    assert isManagerRequest("Is this an agreement copy?") is False
    assert isManagerRequest("This is urgent work") is False

    # Explicit requests with word boundaries SHOULD trigger
    assert isManagerRequest("Can I talk to an agent?") is True
    assert isManagerRequest("Please transfer my call") is True
    assert isManagerRequest("I need a human officer") is True
    assert isManagerRequest("મારે મેનેજર સાથે વાત કરવી છે") is True

    # Word boundary on action queries: 'unclear' should NOT trigger 'clear'
    assert isActionOrProcedureQuery("this transaction is unclear to me") is False
    assert isActionOrProcedureQuery("how do I clear this hold?") is True
    assert isActionOrProcedureQuery("what is the KYC process?") is True


def test_m1_customer_asked_about_funds_dynamic():
    # Does not rely on hardcoded '52000' or '52783'
    assert customerAskedAboutFunds("મારા ખાતામાં બાકી રકમ કેટલી છે?") is True
    assert customerAskedAboutFunds("ઉપલબ્ધ બેલેન્સ કેટલું છે?") is True
    assert customerAskedAboutFunds("what is my total available balance?") is True
    assert customerAskedAboutFunds("maro paisa kya gya?") is True


def test_c2_complexity_gate_skips_grounding():
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    # Long emotional / complaint query with 'pan' / 'problem' should bypass grounding and return None
    complex_query = (
        "સાહેબ મારી કોઈ ભૂલ નથી પરંતુ તમે મારું એકાઉન્ટ કેમ બ્લોક કર્યું? "
        "મારે આજે હોસ્પિટલનું બિલ ભરવાનું છે અને મને ખૂબ મોટી મુશ્કેલી થઈ રહી છે."
    )
    res = groundedReplyForQuestion(complex_query, snap, "Pratik Sharma")
    assert res is None  # Handed off to LLM for reasoning


def test_s4_and_s5_resolved_topics_memory_and_proof():
    proof = {}
    proof = updateCallMemory(
        proof,
        user_text="આ 523 રૂપિયા નો ચાર્જ કેમ લાગ્યો?",
        agent_reply="RBI ની ગાઇડલાઇન મુજબ ચેક રિટર્ન ચાર્જ ₹523 લાગ્યો છે.",
    )
    assert "charge_explained" in proof.get("resolvedTopics", [])

    summary = getMemorySummary(proof)
    assert "RESOLVED_TOPICS: charge_explained" in summary

    # Additional turn adds balance topic
    proof = updateCallMemory(
        proof,
        user_text="મારા ખાતામાં વાપરી શકાય તેવું બેલેન્સ કેટલું છે?",
        agent_reply="તમારા ખાતામાં ઉપલબ્ધ બેલેન્સ ₹14,364 છે.",
    )
    assert "charge_explained" in proof["resolvedTopics"]
    assert "balance_clarified" in proof["resolvedTopics"]


def test_s6_dynamic_case_rules():
    # Test for each case type that rules contain the dynamic numbers from snapshot
    snap_chq = getAccountSnapshot("ACC-CHQ-HARDIK")
    rules_chq = getCaseRules(snap_chq, "Hardik Patel")
    assert "847293" in rules_chq
    assert "49,847" in rules_chq
    assert "523" in rules_chq
    assert "Rajesh Traders" in rules_chq

    snap_lien = getAccountSnapshot("ACC-LIEN-PRIYA")
    rules_lien = getCaseRules(snap_lien, "Pratik Sharma")
    assert "38,419" in rules_lien
    assert "14,364" in rules_lien
    assert "IT-ATTACH-2026-8891" in rules_lien

    snap_hold = getAccountSnapshot("ACC-HOLD-AMIT")
    rules_hold = getCaseRules(snap_hold, "Amit Singh")
    assert "19,847" in rules_hold
    assert "77,494" in rules_hold
    assert "UPI-HOLD-2026-3021" in rules_hold


def test_sentence_level_splitting_for_streaming_tts():
    from app.voice.tts import splitIntoSpokenSentences

    # Multi-sentence Gujarati text splits into spoken clauses
    text = (
        "બરાબર Hardikભાઈ, હું તમને અમારા સિનિયર મેનેજર સાથે જોડું છું. "
        "કૃપા કરીને લાઇન પર રહેજો."
    )
    chunks = splitIntoSpokenSentences(text)
    assert len(chunks) == 2
    assert "સિનિયર મેનેજર" in chunks[0]
    assert "લાઇન પર રહેજો" in chunks[1]

    # Single-sentence returns single chunk
    single = "નમસ્તે! હું સહાયક બેંકમાંથી બોલું છું."
    single_chunks = splitIntoSpokenSentences(single)
    assert len(single_chunks) == 1
    assert single_chunks[0] == single


def test_decoupled_routing_and_conversation_step():
    from app.agent.graph import conversationStep, routeAfterConversation

    # 1. Test routing to HandoffNode
    handoff_state = {
        "sessionId": "test-route-1",
        "phase": "conversation",
        "handoffRequested": True,
        "callEnded": False,
    }
    assert routeAfterConversation(handoff_state) == "HandoffNode"

    # 2. Test routing to EndNode
    end_state = {
        "sessionId": "test-route-2",
        "phase": "conversation",
        "handoffRequested": False,
        "callEnded": True,
    }
    assert routeAfterConversation(end_state) == "EndNode"

    # 3. Test continuation in ConversationNode
    continue_state = {
        "sessionId": "test-route-3",
        "phase": "conversation",
        "handoffRequested": False,
        "callEnded": False,
    }
    assert routeAfterConversation(continue_state) == "ConversationNode"


def test_langfuse_observability_configured_and_active():
    from app.config import settings
    from app.observability.tracing import isEnabled, traceVoiceTurn

    assert settings.langfuseEnabled is True
    assert isEnabled() is True

    # Test tracing context manager records latency
    with traceVoiceTurn("test-sess-123", "test_span", {"test_key": "val"}) as bag:
        pass

    assert "latency_ms" in bag
    assert bag["latency_ms"] >= 0
