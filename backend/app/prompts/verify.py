"""
Verification prompts for Sahayak Voice V2.
Deterministic verification requesting last 4 digits of the account.
"""

from __future__ import annotations


def buildAskLast4Prompt(customer_name: str) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return f"સુરક્ષા ખાતર {name}ભાઈ, કૃપા કરીને તમારા બેંક ખાતાના છેલ્લા ૪ આંકડા જણાવો."


def buildVerifyMismatchPrompt(customer_name: str, attempts_left: int = 1) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return f"{name}ભાઈ, તમે કહેલા આંકડા રેકોર્ડ સાથે મેળ ખાતા નથી. કૃપા કરીને તમારા ખાતાના સાચા છેલ્લા ૪ આંકડા ફરી કહો."


def buildVerifyFailedPrompt(customer_name: str) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return (
        f"{name}ભાઈ, ઓળખ ચકાસણી પૂર્ણ ન થઈ શકવાથી અમે આ કૉલ પર વિગતો આપી શકતા નથી. "
        f"સુરક્ષા ખાતર કૃપા કરીને તમારી નજીકની સહાયક બેંક બ્રાન્ચની મુલાકાત લો. આભાર."
    )
