"""
Conversation Node for Sahayak Voice V2.
The single, common conversational intelligence engine for all 5 banking cases.
Handles arbitrary questions, multi-part inquiries, follow-ups, and objections.
"""

from __future__ import annotations

import re
from typing import Any
from app.agent.memory import getMemorySummary, updateCallMemory
from app.agent.state import CallState
from app.llm.client import callLlmJson
from app.prompts.conversation import CONVERSATION_SYSTEM_PROMPT, buildConversationUserPayload
from app.prompts.end import buildCallEndReply
from app.prompts.fetch import formatAccountFactsForLlm
from app.agent.case_rules import getCaseRules
from app.agent.grounding import groundedReplyForQuestion, isChargeDiscrepancyQuestion
from app.tools.banking import executeBankingTool
from app.tools.definitions import BANKING_TOOL_DEFINITIONS

ALLOWED_BANKING_TOOLS = {"getAccountSnapshot", "verifyIdentity", "registerServiceRequest"}


# ──────────────────────────────────────────────────────────────────────────────
# T4: Tool Definition Pruning
# Detects if customer explicitly requests a bankable ACTION.
# Only then do we pass the full BANKING_TOOL_DEFINITIONS to the LLM.
# Conversational turns (questions, follow-ups, objections) get clean JSON mode
# → saves 200-300ms OpenAI tool schema parsing overhead per turn.
# ──────────────────────────────────────────────────────────────────────────────

_ACTION_KEYWORDS_GU = [
    # Complaint / service request
    "ફરિયાદ", "ફરિયાદ નોंधो", "ફરિયાદ નોंधાव", "ફરિયાદ નoнdhav",
    "ફક્ત", "અરજી", "application", "request", "request karo", "nondho",
    "complaint", "नोंध", "service request", "tichet", "ticket",
    # Transaction list
    "transaction", "ट्रांजेक्शन", "vyavahar", "vyavhaar", "recent",
    "last few", "chhelo", "posatamo", "previous",
]

_ACTION_KEYWORDS_EN = [
    "register", "file", "complaint", "request", "transaction",
    "statement", "recent", "history", "log", "list",
]


def needsTools(user_text: str) -> bool:
    """
    T4: Returns True only when customer explicitly requests a bankable action.
    Keeps tool schema out of 90%+ of conversational turns.
    """
    t = (user_text or "").lower()
    return (
        any(kw in t for kw in _ACTION_KEYWORDS_GU) or
        any(kw in t for kw in _ACTION_KEYWORDS_EN)
    )


def isManagerRequest(text: str) -> bool:
    """Detects if customer asks for human manager or supervisor."""
    t = (text or "").lower()
    gujarati_patterns = ["મેનેજર", "અધિકારી", "માણસ", "સુપરવાઇઝર", "વાત કરાવો", "માણસ સાથે"]
    if any(p in t for p in gujarati_patterns):
        return True
    english_words = ["manager", "human", "supervisor", "officer", "agent", "transfer"]
    return any(re.search(rf"\b{w}\b", t) for w in english_words)


def isCallEndSignal(text: str) -> bool:
    """Detects if customer has no more questions or wants to end the call."""
    t = (text or "").lower().strip()
    exact_ends = {
        "na", "nah", "no", "nahi", "ના", "નહિ", "નથી",
        "vandho nai", "વાંધો નહિ", "વાંધો નથી",
        "ok", "ઓકે", "okay", "ok sir", "ઓકે સર", "ok aabhar", "ઠીક છે", "thik chhe",
    }
    if t in exact_ends:
        return True
    signals = [
        "આભાર", "સમજાઈ ગયું", "કાંઈ નથી", "થેન્ક્સ", "થેન્ક યુ", "બસ એટલું જ", "કંઈ નહિ", "વાંધો નથી", "વાંધો નહિ",
        "thanks", "thank you", "bye", "samjai gayu", "kain nathi", "all good", "no more", "vandho nai", "vandho nahi",
        "kai nathi", "kai nahi",
    ]
    return any(s in t for s in signals)


def fallbackConversationalReply(
    user_text: str,
    snapshot: dict[str, Any],
    customer_name: str,
) -> str:
    """
    Robust grounded fallback reply if LLM is unavailable or offline.
    Directly answers questions about amounts, reasons, procedures, and scam concerns.
    """
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    t = (user_text or "").lower()
    issue = (snapshot.get("primaryIssue") or "").upper()
    avail = snapshot.get("availableBalanceInr", 0)
    ledger = snapshot.get("ledgerBalanceInr", 0)
    hold = snapshot.get("holdAmountInr", 0)

    # Multi-part check: scam / OTP concern
    scam_clarification = ""
    if any(k in t for k in ("scam", "ફ્રોડ", "છેતરપિંડી", "otp", "pin", "સુરક્ષા")):
        scam_clarification = " સહાયક બેંક તમારી પાસેથી ક્યારેય OTP કે PIN નથી માંગતી, આ સત્તાવાર બેંક અપડેટ છે."

    # Question about available balance or amounts
    if any(k in t for k in ("બેલેન્સ", "રૂપિયા", "કેટલા", "balance", "amount", "ketla", "paise")):
        return f"{name}ભાઈ, તમારા ખાતાનું કુલ લેજર બેલેન્સ ₹{ledger:,} છે અને તમે વાપરી શકો તેવું ઉપલબ્ધ બેલેન્સ ₹{avail:,} છે.{scam_clarification}"

    # Case-specific reason queries
    if "CHEQUE" in issue:
        cheque = snapshot.get("cheque") or {}
        chq_no = cheque.get("chequeNumber", "847293")
        amt = cheque.get("amountInr", 49847)
        chg = cheque.get("chargesInr", 523)
        t = (user_text or "").lower()
        # Handle WHY charge is different / discrepancy question
        if isChargeDiscrepancyQuestion(user_text) or any(k in t for k in ("kem", "kyu", "why", "કેમ", "reason", "karano")):
            return (
                f"{name}ભાઈ, તમારો સવાલ બિલકુલ વાજાબી છે. RBI ની જૂની ગાઇડલાઇન મુજબ છોટી રકમના ચેક માટે ચાર્જ ઓછો હતો. "
                f"હવે ₹{amt:,} જેવી મોટી રકમના ચેક બાઉન્સ માટે RBIએ ચાર્જ ₹{chg:,} નક્કી કર્યો છે. "
                f"જો ચેક ફરી બાઉન્સ થાય તો ચાર્જ વધુ હોઈ શકે. અત્યારે ₹{chg:,} ચાર્જ અને ₹{amt:,} જમા કરાવીને પેમેન્ટ હલ કરવું સારું રહેશે.{scam_clarification}"
            )
        return (
            f"{name}ભાઈ, તમે આપેલો ચેક નંબર {chq_no}, રકમ ₹{amt:,}, ખાતામાં અપૂરતા બેલેન્સના લીધે રિટર્ન થયો છે. "
            f"તેનો ચાર્જ ₹{chg:,} લાગ્યો છે. તમે ખાતામાં જરૂરી રકમ જમા કરીને ચૂકવણી કરી શકો છો.{scam_clarification}"
        )

    if "LIEN" in issue:
        lien = snapshot.get("lienDetails") or {}
        amt = lien.get("lienAmount", 38419)
        ref = lien.get("referenceNumber", "IT-ATTACH-2026-8891")
        return (
            f"{name}ભાઈ, આવકવેરા વિભાગના નોટિસ સંદર્ભ {ref} મુજબ ₹{amt:,} ની રકમ પર લિયન લાગેલી છે. "
            f"પરંતુ તમારા બાકીના ₹{avail:,} સંપૂર્ણ વાપરી શકાય તેવા છે.{scam_clarification}"
        )

    if "HOLD" in issue:
        hold_dt = snapshot.get("holdDetails") or {}
        ref = hold_dt.get("referenceNumber", "UPI-HOLD-2026-3021")
        return (
            f"{name}ભાઈ, સંદર્ભ {ref} હેઠળના UPI સેટલમેન્ટ વ્યવહારની સુરક્ષા ચકાસણી માટે ₹{hold:,} ની રકમ હોલ્ડમાં છે. "
            f"સામાન્ય રીતે ૨ કાર્યકારી દિવસમાં આ રકમ ક્લિયર થઈ જશે.{scam_clarification}"
        )

    if "FREEZE" in issue:
        freeze_dt = snapshot.get("freezeDetails") or {}
        docs = freeze_dt.get("requiredDocuments", "Aadhaar Card, PAN Card")
        return (
            f"{name}ભાઈ, કેવાયસી (KYC) રી-વેરિફિકેશન બાકી હોવાથી ડેબિટ ફ્રીઝ છે. "
            f"તમે {docs} સાથે નજીકની બ્રાન્ચમાં જઈને તરત અનફ્રીઝ કરાવી શકો છો.{scam_clarification}"
        )

    if "INOPERATIVE" in issue:
        return (
            f"{name}ભાઈ, ૨ વર્ષથી ખાતામાં વ્યવહાર ન થવાથી આ ખાતું નિષ્ક્રિય થયું છે. "
            f"હોમ બ્રાન્ચમાં કેવાયસી ફોર્મ જમા કરાવવાથી ખાતું વિનામૂલ્યે ફરી સક્રિય થઈ જશે.{scam_clarification}"
        )

    return f"{name}ભાઈ, તમારા ખાતા બાબતે હું બીજી કઈ વિગત સમજાવું?{scam_clarification}"


def prepareConversationContext(state: CallState) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any], str]:
    """Extracts facts, dynamic rules, and memory to build LLM context payload."""
    user_text = (state.get("lastUserText") or "").strip()
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    proof = dict(state.get("proof") or {})

    account_facts_str = formatAccountFactsForLlm(snap)
    transcript_str = getMemorySummary(proof)
    mem = proof.get("callMemory") or {}
    last_answer = mem.get("lastAgentAnswer") or state.get("lastAnswer") or ""
    recent_messages = list(state.get("messages") or [])
    resolved_topics = list(proof.get("resolvedTopics") or mem.get("resolvedTopics") or [])
    case_rules = getCaseRules(snap, customer_name)

    payload = buildConversationUserPayload(
        user_text, account_facts_str, transcript_str, customer_name,
        last_answer=last_answer, recent_messages=recent_messages,
        case_rules=case_rules, resolved_topics=resolved_topics,
    )
    return payload, snap, customer_name, proof, last_answer


def executeLlmReasoning(
    payload: dict[str, Any],
    snap: dict[str, Any],
    proof: dict[str, Any],
) -> tuple[str, bool, bool, dict[str, Any]]:
    """
    Invokes LLM with or without banking tools.
    T4: Tool Definition Pruning — tools are only injected when the customer
    explicitly requests an action (complaint, transactions). Conversational
    turns use clean JSON mode → ~200-300ms faster per turn on OpenAI.
    """
    user_text = payload.get("CUSTOMER_MESSAGE", "")

    # T4: Decide whether this turn needs the full tool schema
    tools_for_this_turn = BANKING_TOOL_DEFINITIONS if needsTools(user_text) else None

    llm_result = callLlmJson(
        system_prompt=CONVERSATION_SYSTEM_PROMPT,
        user_payload=payload,
        tools=tools_for_this_turn,
    )

    agent_reply = ""
    wants_manager = False
    wants_end = False

    if llm_result and isinstance(llm_result, dict):
        agent_reply = (llm_result.get("reply") or "").strip()
        wants_manager = bool(llm_result.get("wants_manager"))
        wants_end = bool(llm_result.get("wants_end"))

        for tc in llm_result.get("tools_to_call", []):
            t_name = str(tc.get("name") or "").strip()
            if t_name in ALLOWED_BANKING_TOOLS:
                t_args = tc.get("arguments", {})
                t_res = executeBankingTool(t_name, t_args, snap)
                proof[f"tool_{t_name}"] = t_res

    return agent_reply, wants_manager, wants_end, proof


def detectCustomerIntents(
    user_text: str,
    llm_wants_manager: bool,
    llm_wants_end: bool,
) -> tuple[bool, bool]:
    """Reconciles LLM intent decisions with deterministic post-LLM safety nets."""
    wants_manager = llm_wants_manager
    wants_end = llm_wants_end

    if not wants_manager and isManagerRequest(user_text):
        wants_manager = True

    if not wants_end and isCallEndSignal(user_text):
        wants_end = True

    return wants_manager, wants_end


def resolveAgentReply(
    raw_reply: str,
    user_text: str,
    snap: dict[str, Any],
    customer_name: str,
    last_answer: str,
    wants_manager: bool,
    wants_end: bool,
) -> str:
    """Selects grounded fallback or escalation/closing message if needed."""
    sal = customer_name.split()[0] if customer_name else "ગ્રાહક"

    if raw_reply:
        return raw_reply

    if wants_manager:
        return f"બરાબર {sal}ભાઈ, હું તમને અમારા સિનિયર મેનેજર સાથે જોડું છું. કૃપા કરીને લાઇન પર રહેજો."

    if wants_end:
        return buildCallEndReply(customer_name)

    grounded = groundedReplyForQuestion(user_text, snap, customer_name, last_answer)
    return grounded or fallbackConversationalReply(user_text, snap, customer_name)


def handleConversation(state: CallState, db: Any = None) -> dict[str, Any]:
    """
    Main turn processing for ConversationNode.
    Decomposed into distinct stages: context prep, reasoning, intent reconciliation, memory.
    Routing is delegated to LangGraph conditional edges.
    """
    user_text = (state.get("lastUserText") or "").strip()

    # 1. Context Preparation
    payload, snap, customer_name, proof, last_answer = prepareConversationContext(state)

    # 2. LLM Reasoning & Whitelisted Tool Execution
    agent_reply, llm_mgr, llm_end, proof = executeLlmReasoning(payload, snap, proof)

    # 3. Intent Detection & Reconciliation
    wants_manager, wants_end = detectCustomerIntents(user_text, llm_mgr, llm_end)

    # 4. Agent Reply Resolution
    final_reply = resolveAgentReply(
        agent_reply, user_text, snap, customer_name, last_answer, wants_manager, wants_end
    )

    # 5. Conversational Memory Update (tracks turns & resolved topics)
    proof = updateCallMemory(proof, user_text, final_reply)
    if wants_manager:
        proof["handoffRequested"] = True
    if wants_end:
        proof["callEnded"] = True

    # Determine phase corresponding to intent for node patch
    target_phase = "handoff_connecting" if wants_manager else ("end" if wants_end else "conversation")

    return {
        "phase": target_phase,
        "speaker": "Sahayak",
        "lastAgentReply": final_reply,
        "handoffRequested": wants_manager,
        "callEnded": wants_end,
        "proof": proof,
        "resolvedTopics": proof.get("resolvedTopics", []),
    }
