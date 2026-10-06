"""
End call prompts for Sahayak Voice V2.
Warm, professional Gujarati closing messages — like a real Indian bank agent.
Gender-aware: ભાઈ for male, બેન for female.
"""

from __future__ import annotations

# Gender-neutral suffix placeholder — resolved at runtime
_CLOSING_PHRASES = [
    "આજે સહાયક બેંક સાથે વાત કરવા બદલ ખૂબ ખૂબ આભાર {name}{suffix}. ભવિષ્યમાં કોઈ પણ સહાય માટે અમે હંમેશા અહીં છીએ. તમારો દિવસ ખૂબ સારો જાય.",
    "ધન્યવાદ {name}{suffix}, આજે અમારી સેવા પસંદ કરવા બદલ આભારી છીએ. તમારી સમસ્યાનો ઉકેલ થઈ ગયો છે. કોઈ પ્રશ્ન હોય તો ફરી ફોન કરજો. આવજો!",
    "ખૂબ ખૂબ આભાર {name}{suffix}. સહાયક બેંક હંમેશા તમારી સેવામાં હાજર છે. આગળ કોઈ જરૂર પડે તો આ જ નંબર પર ફોન કરી શકો છો. ધ્યાન રાખજો.",
    "ઠીક છે {name}{suffix}, આજે આટલું. ખૂબ આભાર તમારો. ભગવાન તમારું ભલું કરે, દિવસ શુભ રહે. આવજો!",
    "સહાયક બેંક તરફથી ખૂબ ખૂબ આભાર {name}{suffix}. આશા છે તમારો પ્રશ્ન ઉકેલાઈ ગયો. ફરી વાર આવવાનો ઉત્સાહ રહે. ખૂબ ખૂબ ધન્યવાદ.",
]

# Female names common in Indian banking — used for gender-aware suffix
_FEMALE_NAMES = {
    "priya", "meena", "sunita", "kavita", "pooja", "anita", "rekha",
    "geeta", "nisha", "ritu", "sonal", "hetal", "minal", "binal",
    "kinjal", "dhruti", "palak", "riddhi", "khushbu", "jyoti",
}

_closing_index = 0


def _getSuffix(first_name: str) -> str:
    """Returns ભાઈ for male names, બેન for female names."""
    return "બેન" if first_name.lower() in _FEMALE_NAMES else "ભાઈ"


def buildCallEndReply(customer_name: str) -> str:
    global _closing_index
    name = customer_name.split()[0] if customer_name else "ગ્રાહક"
    suffix = _getSuffix(name)
    phrase = _CLOSING_PHRASES[_closing_index % len(_CLOSING_PHRASES)]
    _closing_index += 1
    return phrase.format(name=name, suffix=suffix)
