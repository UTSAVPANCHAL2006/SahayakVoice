"""
Greeting prompts for Sahayak Voice V2.
Outbound call opening formula in polite Gujarati.
"""

from __future__ import annotations


def buildGreetingPrompt(customer_name: str, topic_phrase: str) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return (
        f"નમસ્તે {name}ભાઈ! હું સહાયક બેંકમાંથી બોલું છું. "
        f"{topic_phrase} અગત્યની માહિતી આપવા માટે ફોન કર્યો છે. "
        f"શું તમે બે મિનિટ વાત કરી શકશો?"
    )
