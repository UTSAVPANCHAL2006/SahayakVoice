"""
End call prompts for Sahayak Voice V2.
Polite closure and wrap-up messages.
"""

from __future__ import annotations


def buildCallEndReply(customer_name: str) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return f"સહાયક બેંક સાથે વાત કરવા બદલ આભાર {name}ભાઈ. તમારો દિવસ શુભ રહે!"
