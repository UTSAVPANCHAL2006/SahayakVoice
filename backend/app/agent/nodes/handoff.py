"""
Handoff and Manager Node for Sahayak Voice V2.
Controls human escalation to Senior Relationship Manager (Vikram Mehta / Ratan voice).
CRITICAL RULES:
1. Manager speaks FIRST automatically upon connection — customer does NOT need to say 'hello'.
2. Once handoff is connected, callMode = 'human'; AI mode stops.
3. Manager receives all prior account facts and context.
4. Manager can resolve questions and naturally close the call.
"""

from __future__ import annotations

import json
from typing import Any
from app.agent.grounding import groundedReplyForQuestion
from app.agent.memory import getMemorySummary, updateCallMemory
from app.agent.state import CallState
from app.llm.client import callLlmJson
from app.prompts.end import buildCallEndReply
from app.prompts.fetch import formatAccountFactsForLlm
from app.prompts.handoff import (
    MANAGER_SYSTEM_PROMPT,
    buildManagerOpeningGreeting,
    buildManagerUserPayload,
)


def startHumanConversation(state: CallState, db: Any = None) -> dict[str, Any]:
    """
    Initiates handoff to Senior Manager.
    Manager speaks FIRST with case context without waiting for customer.
    """
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    primary_issue = state.get("caseType") or snap.get("primaryIssue") or ""
    proof = dict(state.get("proof") or {})

    # Extract unresolved question if customer just asked something
    last_unresolved = proof.get("callMemory", {}).get("lastCustomerQuestion", "")

    # Build proactive opening greeting from manager
    manager_name = "વિક્રમ મહેતા"
    manager_greeting = buildManagerOpeningGreeting(
        customer_name=customer_name,
        primary_issue=primary_issue,
        agent_name=manager_name,
        unresolved_query=last_unresolved,
    )

    proof["handoffComplete"] = True
    proof["callMode"] = "human"
    proof["assignedAgent"] = {
        "name": manager_name,
        "role": "Senior Relationship Manager",
        "gender": "male",
    }

    return {
        "phase": "handoff",
        "callMode": "human",
        "handoffComplete": True,
        "speaker": "Senior Manager",
        "assignedAgentName": manager_name,
        "lastAgentReply": manager_greeting,
        "proof": proof,
    }


def handleHumanConversation(state: CallState, db: Any = None) -> dict[str, Any]:
    """
    Handles ongoing turns between Customer and Senior Manager.
    Uses manager persona and context to answer or close the call.
    """
    user_text = (state.get("lastUserText") or "").strip()
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    proof = dict(state.get("proof") or {})

    # Check for closing signals during manager mode
    closing_signals = ["આભાર", "સમજાઈ ગયું", "કાંઈ નથી", "થેન્ક્સ", "થેન્ક યુ", "ઓકે", "bye", "શુભ દિવસ"]
    if any(s in user_text.lower() for s in closing_signals):
        closing_text = (
            f"તમારી સમસ્યા અંગે મેં જરૂરી વિગત સમજાવી છે {name}ભાઈ. "
            f"વધુ મદદની જરૂર હોય તો અમે હંમેશાં ઉપલબ્ધ છીએ. સહાયક બેંકમાં કૉલ કરવા બદલ આભાર, તમારો દિવસ શુભ રહે!"
        )
        return {
            "phase": "end",
            "callEnded": True,
            "callMode": "ended",
            "speaker": "Senior Manager",
            "lastAgentReply": closing_text,
            "proof": {**proof, "callEnded": True},
        }

    # Manager LLM response with authorized context
    account_facts_str = formatAccountFactsForLlm(snap)
    context_str = getMemorySummary(proof)
    payload = buildManagerUserPayload(user_text, account_facts_str, context_str, customer_name)

    llm_res = callLlmJson(
        system_prompt=MANAGER_SYSTEM_PROMPT,
        user_payload=payload,
    )

    manager_reply = ""
    call_ended = False
    if llm_res and isinstance(llm_res, dict):
        manager_reply = (llm_res.get("reply") or "").strip()
        call_ended = bool(llm_res.get("call_ended"))

    if not manager_reply:
        manager_reply = groundedReplyForQuestion(user_text, snap, customer_name) or (
            f"{name}ભાઈ, તમારા ખાતાના અધિકૃત રેકોર્ડ મુજબ હું તમને વિગત સમજાવું છું. "
            f"તમારો પ્રશ્ન શું છે તે ફરીથી એક વાર કહો."
        )

    if call_ended:
        return {
            "phase": "end",
            "callEnded": True,
            "callMode": "ended",
            "speaker": "Senior Manager",
            "lastAgentReply": manager_reply,
            "proof": {**proof, "callEnded": True},
        }

    proof = updateCallMemory(proof, user_text, manager_reply)
    return {
        "phase": "handoff",
        "callMode": "human",
        "speaker": "Senior Manager",
        "lastAgentReply": manager_reply,
        "proof": proof,
    }


def handleHandoff(state: CallState, db: Any = None) -> dict[str, Any]:
    """
    Handoff entry point:
    If handoff has not connected yet -> startHumanConversation (Manager speaks FIRST).
    If already connected in human mode -> handleHumanConversation.
    """
    if state.get("callMode") == "human" or state.get("handoffComplete"):
        return handleHumanConversation(state, db)
    return startHumanConversation(state, db)
