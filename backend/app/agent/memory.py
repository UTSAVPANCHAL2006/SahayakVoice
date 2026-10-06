"""
Conversation memory tracker for Sahayak Voice V2.
Records customer questions, key concerns, and agent answers.
"""

from __future__ import annotations

from typing import Any


def detectResolvedTopics(user_text: str, agent_reply: str) -> list[str]:
    """Infers banking topics that were addressed/resolved in this turn."""
    topics = []
    t = f"{user_text} {agent_reply}".lower()
    if any(k in t for k in ("charge", "ચાર્જ", "penalty", "523", "256", "fee")):
        topics.append("charge_explained")
    if any(k in t for k in ("balance", "બેલેન્સ", "લેજર", "ઉપલબ્ધ", "available", "ledger", "વાપરી")):
        topics.append("balance_clarified")
    if any(k in t for k in ("lien", "લિયન", "આવકવેરા", "income tax", "clearance")):
        topics.append("lien_explained")
    if any(k in t for k in ("hold", "હોલ્ડ", "upi", "48 કલાક", "સેટલમેન્ટ", "dispute")):
        topics.append("hold_explained")
    if any(k in t for k in ("freeze", "ફ્રીઝ", "re-kyc", "કેવાયસી", "unfreeze", "re-verification")):
        topics.append("freeze_kyc_explained")
    if any(k in t for k in ("inoperative", "નિષ્ક્રિય", "dormant", "સક્રિય", "reactivate", "reactivation")):
        topics.append("inoperative_reactivation_explained")
    return topics


def updateCallMemory(proof: dict[str, Any], user_text: str, agent_reply: str) -> dict[str, Any]:
    """Updates proof dictionary with latest conversational memory and resolved topics."""
    mem = dict(proof.get("callMemory") or {})
    turns = list(mem.get("turns") or [])
    resolved = list(proof.get("resolvedTopics") or mem.get("resolvedTopics") or [])

    if user_text:
        turns.append({"role": "customer", "text": user_text[:200]})
        mem["lastCustomerQuestion"] = user_text[:150]

    if agent_reply:
        turns.append({"role": "agent", "text": agent_reply[:200]})
        mem["lastAgentAnswer"] = agent_reply[:150]

    for topic in detectResolvedTopics(user_text, agent_reply):
        if topic not in resolved:
            resolved.append(topic)

    mem["turns"] = turns[-10:]
    mem["resolvedTopics"] = resolved
    proof["callMemory"] = mem
    proof["resolvedTopics"] = resolved
    return proof


def getMemorySummary(proof: dict[str, Any]) -> str:
    """Builds a compact summary string of recent conversation memory."""
    mem = proof.get("callMemory") or {}
    turns = mem.get("turns") or []
    resolved = proof.get("resolvedTopics") or mem.get("resolvedTopics") or []
    if not turns and not resolved:
        return ""
    lines = []
    if resolved:
        lines.append(f"RESOLVED_TOPICS: {', '.join(resolved)}")
    for t in turns:
        lines.append(f"{t.get('role')}: {t.get('text')}")
    return "\n".join(lines)
