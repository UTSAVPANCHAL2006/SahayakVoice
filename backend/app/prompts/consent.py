"""
Consent prompts for Sahayak Voice V2.
Handles customer consent, clarifying purpose, or declining.
"""

from __future__ import annotations


def buildConsentExplanation(customer_name: str) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return (
        f"{name}ભાઈ, આ તમારા ખાતાની સુરક્ષા અને તાજેતરના મહત્વપૂર્ણ અપડેટ અંગે છે. "
        f"વિગતો જણાવવા માટે તમારી સહમતિ જરૂરી છે. શું હું આગળ વાત કરું?"
    )


def buildConsentDeclineReply(customer_name: str) -> str:
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    return (
        f"સમજી શકું છું {name}ભાઈ. તમારી અનુકૂળતા મુજબ તમે નજીકની બ્રાન્ચનો સંપર્ક કરી શકો છો. "
        f"સહાયક બેંકમાં સમય આપવા બદલ આભાર."
    )
