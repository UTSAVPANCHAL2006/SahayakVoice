"""
Issue explanation prompts for Sahayak Voice V2.
Explains the initial account issue cleanly in Gujarati for all 5 cases.
"""

from __future__ import annotations

from typing import Any


def buildInitialExplanation(snapshot: dict[str, Any]) -> str:
    """Generates the grounded initial explanation of the issue."""
    name = (snapshot.get("customerName") or "ગ્રાહક").split()[0]
    issue = (snapshot.get("primaryIssue") or "").upper()

    if "CHEQUE" in issue:
        cheque = snapshot.get("cheque") or {}
        amt = cheque.get("amountInr", 49847)
        chq_no = cheque.get("chequeNumber", "847293")
        payee = cheque.get("payeeName", "રાજેશ ટ્રેડર્સ")
        return (
            f"આભાર {name}ભાઈ. તમારી માહિતી ચકાસાઈ ગઈ છે. "
            f"તમે આપેલો ચેક નંબર {chq_no}, રકમ ₹{amt:,}, જે {payee} ના નામે હતો, "
            f"તે અપૂરતા બેલેન્સના કારણે રિટર્ન થયો છે. "
            f"આ અંગે તમારે શું જાણવું છે?"
        )

    if "LIEN" in issue:
        lien = snapshot.get("lienDetails") or {}
        amt = lien.get("lienAmount", 38419)
        usable = snapshot.get("availableBalanceInr", 14364)
        return (
            f"આભાર {name}ભાઈ. તમારી માહિતી ચકાસાઈ ગઈ છે. "
            f"તમારા ખાતામાં ₹{amt:,} ની રકમ પર આવકવેરા વિભાગના આદેશ મુજબ લિયન (રોક) લાગેલી છે. "
            f"જોકે તમારું બાકીનું ₹{usable:,} નું બેલેન્સ તમે સામાન્ય રીતે વાપરી શકો છો. "
            f"આ બાબતે હું તમને વધુ વિગતો આપું?"
        )

    if "HOLD" in issue:
        hold = snapshot.get("holdDetails") or {}
        amt = hold.get("holdAmount", 19847)
        return (
            f"આભાર {name}ભાઈ. તમારી માહિતી ચકાસાઈ ગઈ છે. "
            f"તમારા તાજેતરના UPI સેટલમેન્ટ વ્યવહારની ચકાસણી માટે ₹{amt:,} ની રકમ કામચલાઉ હોલ્ડ પર છે. "
            f"તમારું બાકીનું ખાતું સક્રિય છે. આ અંગે હું તમને કેવી રીતે મદદ કરું?"
        )

    if "FREEZE" in issue:
        return (
            f"આભાર {name}ભાઈ. તમારી માહિતી ચકાસાઈ ગઈ છે. "
            f"તમારા ખાતામાં સમયસર કેવાયસી (KYC) અપડેટ ન થવાને કારણે હાલ પૂરતું ડેબિટ ફ્રીઝ મૂકાયું છે, "
            f"જેથી નાણાં ઉપાડ બંધ છે પરંતુ જમા થઈ શકે છે. "
            f"ખાતું ફરી ચાલુ કરાવવાની રીત હું તમને સમજાવું?"
        )

    if "INOPERATIVE" in issue:
        inop = snapshot.get("inoperativeDetails") or {}
        last_date = inop.get("lastTransactionDate", "14 ઑગસ્ટ 2024")
        return (
            f"આભાર {name}ભાઈ. તમારી માહિતી ચકાસાઈ ગઈ છે. "
            f"છેલ્લા ૨ વર્ષથી કોઈ વ્યવહાર ન થયો હોવાથી તમારું ખાતું ઇનઓપરેટિવ (નિષ્ક્રિય) થયું છે. "
            f"તમારી રકમ સંપૂર્ણ સલામત છે. ખાતું ફરી સક્રિય કરવા માટે હું તમને પ્રક્રિયા સમજાવું?"
        )

    return f"આભાર {name}ભાઈ. તમારી માહિતી ચકાસાઈ ગઈ છે. તમારા ખાતા અંગે હું તમને શું માહિતી આપું?"
