"""
Consent Node for Sahayak Voice V2.
Captures customer consent to discuss account details.
"""

from __future__ import annotations

from typing import Any
from app.agent.state import CallState
from app.prompts.consent import buildConsentDeclineReply, buildConsentExplanation
from app.prompts.verify import buildAskLast4Prompt


def _isNegative(user_text: str) -> bool:
    """Returns True if the customer clearly declined / said no."""
    t = user_text.strip().lower()

    # Exact-match short rejections (catches "na", "no", "nah", "nahi", "nai")
    exact_rejections = {
        "na", "no", "nah", "nahi", "nai", "nahin", "naa", "na.", "no.",
        "busy", "later", "pachi",
    }
    if t in exact_rejections:
        return True

    # Substring matches — Gujarati script
    gu_negative = [
        "ગાડી ચલ",        # "ગાડી ચલાવું છું" (driving)
        "ગાડી",            # any driving mention
        "ટ્રાફિક",          # in traffic
        "ચલાવ",            # driving verb alone
        "ડ્રાઈવ",           # driving (English-Gujarati mix)
        "વ્યસ્ત",           # busy
        "ટાઇમ નથ",         # no time
        "ટાઈમ નથ",
        "ટાઈમ ન ",
        "ફ્રી નથ",          # not free
        "ફ્રી ન ",
        "વાત ન",           # can't talk ("વાત નહીં", "વાત ન થાય")
        "નહ",              # broad: "નહ", "નહીં", "નહિ"
        "ન થ",             # "ન થાય" — can't be done
        "ના.",              # "ના" with punctuation
        "ગ્રાહક ન",
        "સમય ન",          # no time
        "હમણ",             # "હમણાં" — right now / at the moment (often negative)
        "પછ",              # later ("પછી ફોન")
        "કામ",             # at work / busy
    ]
    for sig in gu_negative:
        if sig in t:
            return True

    # Substring matches — Roman / English / Hindi
    en_negative = [
        "no ", "not now", "call later", "cant talk", "can't talk",
        "busy", "driving", "gadi chalav", "gadi",
        "nahi", "nai ", "abhi nahi", "baad me", "baad mein",
        "mane nahi", "later", "mat karo", "nai thay", "na thay",
        "vaat nahi", "vaat na", "tyare nai", "aaje nai",
        "vyast", "vyyast", "pachi kar", "pachi fon", "pachi bolar",
        "pachi", "paachi", "free nathi", "time nathi",
    ]
    for sig in en_negative:
        if sig in t:
            return True

    return False


def _isPositive(user_text: str) -> bool:
    """Returns True if the customer clearly said yes / agreed to talk."""
    t = user_text.strip().lower()
    positive_signals = [
        # Gujarati script
        "હા", "હાજી", "બોલો", "ચોક્કસ", "કહો", "સાંભળ", "ઠીક",
        "ઓ.કે", "ઓકે",
        # Roman Gujarati / Hindi / English
        "yes", "ha ", "ha,", "haan", "bolo", "sure", "okay", "ok",
        "kaho", "sambhlo", "han", "bolav",
        "karav", "saro", "thaik", "thik",
    ]
    # "ha" exact only — avoid false match in "nahi"
    if t == "ha" or t == "haa":
        return True
    return any(sig in t for sig in positive_signals)


def getConsent(state: CallState, db: Any = None) -> dict[str, Any]:
    """Evaluates customer consent to proceed with the call."""
    user_text = (state.get("lastUserText") or "").strip()
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    retries = int(state.get("consentRetries") or 0)

    # ── NEGATIVE check FIRST (before any positive check) ────────────────────────
    if _isNegative(user_text) and not _isPositive(user_text):
        reply = buildConsentDeclineReply(customer_name)
        return {
            "phase": "end",
            "callEnded": True,
            "speaker": "Sahayak",
            "lastAgentReply": reply,
        }

    # ── POSITIVE: move to verification ──────────────────────────────────────────
    if _isPositive(user_text):
        ask_digits_reply = buildAskLast4Prompt(customer_name)
        return {
            "phase": "verify",
            "speaker": "Sahayak",
            "lastAgentReply": ask_digits_reply,
            "consentRetries": 0,
        }

    # ── AMBIGUOUS but non-empty (> 4 chars, not clearly negative) → treat as implicit yes
    if len(user_text) > 4:
        ask_digits_reply = buildAskLast4Prompt(customer_name)
        return {
            "phase": "verify",
            "speaker": "Sahayak",
            "lastAgentReply": ask_digits_reply,
            "consentRetries": 0,
        }

    # ── Too many retries → politely end ─────────────────────────────────────────
    if retries >= 2:
        reply = buildConsentDeclineReply(customer_name)
        return {
            "phase": "end",
            "callEnded": True,
            "speaker": "Sahayak",
            "lastAgentReply": reply,
        }

    # ── Ask again politely ───────────────────────────────────────────────────────
    clarify_reply = buildConsentExplanation(customer_name)
    return {
        "phase": "consent",
        "speaker": "Sahayak",
        "lastAgentReply": clarify_reply,
        "consentRetries": retries + 1,
    }
