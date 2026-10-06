"""
Language utilities for Sahayak Voice V2.
Sahayak Voice V2 is Gujarati-first.
Ensures customer-facing speech and text are natural Gujarati.
"""

from __future__ import annotations

import re
from app.config import settings

GUJARATI = "gujarati"

# Gujarati digits mapping
DIGITS_GU = {
    "0": "૦", "1": "૧", "2": "૨", "3": "૩", "4": "૪",
    "5": "૫", "6": "૬", "7": "૭", "8": "૮", "9": "૯",
}


def normalizeLanguage(lang: str | None = None) -> str:
    """Normalize language code to gujarati."""
    return GUJARATI


def getSarvamSpeechCode(lang: str = GUJARATI) -> str:
    """Sarvam speech language code for Gujarati."""
    return "gu-IN"


def isHandoffVoiceActive(state: dict | None) -> bool:
    """Check if handoff male voice should be active."""
    if not state:
        return False
    return bool(state.get("rmVoiceActive") or state.get("callMode") == "human")


def getSpeakerName(call_mode: str = "ai", speaker: str | None = None) -> str:
    """
    Returns voice speaker id for Sarvam TTS:
    - 'kavya': female natural voice for AI bot (Sahayak)
    - 'ratan': male authoritative voice for senior manager
    """
    if call_mode == "human" or speaker == "Senior Manager":
        return settings.managerSpeaker
    return settings.sarvamSpeaker


def topicPhrase(primary_issue: str | None) -> str:
    """Natural Gujarati phrase describing the banking issue for greetings."""
    issue = (primary_issue or "").upper()
    if "LIEN" in issue:
        return "તમારા ખાતામાં લિયન બાબતે"
    if "HOLD" in issue or "UPI" in issue:
        return "તમારા ખાતામાં રકમ હોલ્ડ બાબતે"
    if "INOPERATIVE" in issue:
        return "તમારા ખાતામાં ઇનઓપરેટિવ સ્થિતિ બાબતે"
    if "CHEQUE" in issue or "BOUNCE" in issue:
        return "તમારા ચેક રિટર્ન બાબતે"
    if "FREEZE" in issue:
        return "તમારા ખાતામાં ડેબિટ ફ્રીઝ બાબતે"
    return "તમારા ખાતા બાબતે"


def enforceGujaratiOutput(text: str) -> str:
    """
    Ensures text is clean for Gujarati speech and display.
    Replaces common English symbols with Gujarati words or clean characters.
    """
    if not text:
        return ""
    t = text.strip()
    t = t.replace("Rs.", "રૂપિયા ").replace("INR", "રૂપિયા").replace("₹", "રૂપિયા ")
    # Replace common trailing tags if present
    t = re.sub(r"\[.*?\]", "", t)
    return re.sub(r"\s+", " ", t).strip()
