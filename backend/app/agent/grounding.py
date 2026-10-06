"""Grounded banking explanations shared by conversation and manager modes."""

from __future__ import annotations

import re
from typing import Any


def isChargeDiscrepancyQuestion(user_text: str) -> bool:
    """Detects customer questioning WHY a charge is higher/different — let LLM handle this."""
    t = (user_text or "").lower()
    patterns = (
        "last time", "pehla", "pahela", "pahle", "aagal", "aagle", "aagalna",
        "kem vadhi", "keno vadhi", "kem vagyu", "charge kem", "523 kem", "256",
        "vdhu kem", "vahu kem", "vadharo", "vadhyo", "why more", "why this much",
        "last vakhte", "पहले", "pahle",
    )
    return any(p in t for p in patterns)


def isActionOrProcedureQuery(user_text: str) -> bool:
    # Don't classify charge-WHY questions as action queries
    if isChargeDiscrepancyQuestion(user_text):
        return False
    t = (user_text or "").lower()
    gujarati_and_phrases = (
        "su krvu", "shu karvu", "shu karu", "su karu", "su karvanu", "krvu",
        "hatav", "chalu", "prokriya", "solution", "ilaj", "sampark", "aavu", "aavvu",
        "kagal", "unfreeze", "chutse", "chute", "remedy", "nikal", "clearnace",
        "madad", "ચાર્જ", "કેવાયસી", "બ્રાન્ચ", "દસ્તાવેજ"
    )
    if any(a in t for a in gujarati_and_phrases):
        return True
    english_words = (
        "remove", "active", "kyc", "emergency", "process", "branch",
        "document", "documents", "unfreeze", "remedy", "clear", "guidance", "help", "charge"
    )
    return any(re.search(rf"\b{w}\b", t) for w in english_words)


def customerAskedAboutFunds(user_text: str) -> bool:
    if isActionOrProcedureQuery(user_text):
        return False
    t = (user_text or "").lower()
    markers = (
        "બાકી",
        "baki",
        "kyā",
        "kya",
        "gaya",
        "gya",
        "gayā",
        "ક્યાં",
        "vapri",
        "વાપરી",
        "use",
        "spend",
        "total",
        "કુલ",
        "kul",
        "paisa",
        "પૈસા",
        "rakkam",
        "રકમ",
        "અટક",
        "atki",
        "hold",
        "lien",
        "લિયન",
        "balance",
        "બેલેન્સ",
        "રૂપિયા",
        "rupya",
        "rupiya",
        "ketla",
        "ketlu",
        "funds",
        "available",
        "ledger",
    )
    return any(m in t for m in markers)


def explainGuidanceFromSnapshot(snapshot: dict[str, Any], user_text: str, customer_name: str) -> str | None:
    """Provides actionable resolution steps and guidance for each of the 5 banking cases."""
    name = (customer_name or "ગ્રાહક").split()[0]
    issue = (snapshot.get("primaryIssue") or "").upper()
    avail = int(snapshot.get("availableBalanceInr") or 0)
    t = (user_text or "").lower()

    if "LIEN" in issue:
        lien = snapshot.get("lienDetails") or {}
        ref = lien.get("referenceNumber") or "IT-ATTACH-2026-8891"
        amt = int(lien.get("lienAmount") or snapshot.get("holdAmountInr") or 38419)
        authority = lien.get("authority") or "આવકવેરા વિભાગ"

        if any(w in t for w in ("bank", "branch", "બ્રાન્ચ", "બેંક", "aavu", "આવું", "sampark")):
            return (
                f"{name}ભાઈ, તમે ચોક્કસ બ્રાન્ચમાં આવી શકો છો. બ્રાન્ચમાંથી તમને આવકવેરા આદેશ સંદર્ભ {ref} નો અધિકૃત લેટર મળશે. "
                f"પરંતુ લિયન સરકારી આદેશથી હોવાથી, તેને દૂર કરવા માટે આવકવેરા વિભાગનું ક્લિયરન્સ જરૂરી છે. "
                f"ત્યાં સુધી તમે બાકીના ₹{avail:,} સંપૂર્ણપણે વાપરી શકો છો."
            )
        return (
            f"{name}ભાઈ, લિયન હટાવવા માટે તમારે {authority} સાથે નોટિસ સંદર્ભ {ref} બાબતે સંપર્ક કરી સમાધાન કરવું પડશે. "
            f"તેમનું ક્લિયરન્સ મળતા જ બેંક ₹{amt:,} ની રકમ પરથી લિયન તરત હટાવી દેશે. "
            f"હાલ તમારા ખાતામાં રહેલા ₹{avail:,} સંપૂર્ણપણે સુરક્ષિત અને વાપરવા માટે ઉપલબ્ધ છે."
        )

    if "INOPERATIVE" in issue:
        if any(w in t for w in ("emergency", "ઇમરજન્સી", "તાત્કાલિક", "urgent")):
            return (
                f"{name}ભાઈ, જો તાત્કાલિક જરૂર હોય તો આજે જ આધાર કાર્ડ અને પાન કાર્ડ સાથે તમારી હોમ બ્રાન્ચમાં જાઓ. "
                f"બ્રાન્ચ મેનેજર સમક્ષ ઇમરજન્સી જણાવીને બાયોમેટ્રિક Re-KYC કરાવવાથી ખાતું ૨૪ કલાકની અંદર સક્રિય થઈ જશે અને સમગ્ર રકમ ઉપલબ્ધ થઈ જશે."
            )
        return (
            f"{name}ભાઈ, ૨ વર્ષથી વ્યવહાર ન થવાથી ખાતું ઇનઓપરેટિવ થયું છે. "
            f"તેને ફરી ચાલુ કરવા માટે તમારી હોમ બ્રાન્ચમાં આધાર કાર્ડ, પાન કાર્ડ અને પાસપોર્ટ સાઇઝ ફોટો સાથે Re-KYC ફોર્મ આપવું પડશે. "
            f"આ પ્રક્રિયા બિલકુલ વિનામૂલ્યે છે અને સામાન્ય રીતે ૨૪ કલાકમાં ખાતું સક્રિય થઈ જશે."
        )

    if "FREEZE" in issue:
        freeze_dt = snapshot.get("freezeDetails") or {}
        docs = freeze_dt.get("requiredDocuments", "Aadhaar Card અને PAN Card")
        return (
            f"{name}ભાઈ, કેવાયસી રિન્યુઅલ બાકી હોવાથી ખાતા પર ડેબિટ ફ્રીઝ છે. "
            f"તેને હટાવવા માટે {docs} ની નકલ સાથે નજીકની બ્રાન્ચમાં Re-KYC ફોર્મ જમા કરો. "
            f"દસ્તાવેજ ચકાસ્યા બાદ ૨ થી ૪ કલાકમાં ડેબિટ ફ્રીઝ અનફ્રીઝ થઈ જશે."
        )

    if "CHEQUE" in issue:
        cheque = snapshot.get("cheque") or {}
        chq_no = cheque.get("chequeNumber", "847293")
        amt = cheque.get("amountInr", 49847)
        chg = cheque.get("chargesInr", 523)
        return (
            f"{name}ભાઈ, ચેક નંબર {chq_no} માટે ₹{chg:,} બાઉન્સ ચાર્જ લાગ્યો છે. "
            f"હવે ખાતામાં ચેકની રકમ ₹{amt:,} અને ચાર્જ જમા કરાવો, અને પાર્ટીને ચેક ફરી રજૂ કરવા અથવા સીધા NEFT/UPI થી પેમેન્ટ કરી શકો છો."
        )

    if "HOLD" in issue:
        hold_dt = snapshot.get("holdDetails") or {}
        ref = hold_dt.get("referenceNumber", "UPI-HOLD-2026-3021")
        hold_amt = int(snapshot.get("holdAmountInr") or 12500)
        return (
            f"{name}ભાઈ, ₹{hold_amt:,} ની રકમ સંદર્ભ {ref} હેઠળ સુરક્ષા વેરિફિકેશન માટે હોલ્ડ પર છે. "
            f"આ રકમ ૨ કાર્યકારી દિવસમાં આપોઆપ ક્લિયર થઈ જાય છે. જો ૪૮ કલાકમાં ક્લિયર ન થાય, તો અમે તાત્કાલિક સર્વિસ રિક્વેસ્ટ નોંધાવી શકીએ છીએ."
        )

    return None


def explainFundsFromSnapshot(snapshot: dict[str, Any], customer_name: str) -> str | None:
    """Explain ledger vs restriction vs available when facts support it."""
    name = (customer_name or "ગ્રાહક").split()[0]
    ledger = int(snapshot.get("ledgerBalanceInr") or 0)
    avail = int(snapshot.get("availableBalanceInr") or 0)
    hold = int(snapshot.get("holdAmountInr") or 0)
    issue = (snapshot.get("primaryIssue") or "").upper()

    if ledger <= 0:
        return None

    if "LIEN" in issue and hold > 0:
        lien = snapshot.get("lienDetails") or {}
        ref = lien.get("referenceNumber") or snapshot.get("extra", {}).get("referenceNumber") or ""
        authority = lien.get("authority") or "આવકવેરા વિભાગ"
        ref_bit = f" (સંદર્ભ {ref})" if ref else ""
        return (
            f"{name}ભાઈ, તમારા ખાતામાં કુલ ₹{ledger:,} છે. તેમાંથી ₹{hold:,} પર લિયન{ref_bit} "
            f"({authority}) લાગેલી છે — આ રકમ ગઈ નથી, પરંતુ હાલ વાપરી શકાતી નથી. "
            f"બાકીની ઉપલબ્ધ રકમ ₹{avail:,} છે જે તમે વાપરી શકો છો."
        )

    if "HOLD" in issue and hold > 0:
        hd = snapshot.get("holdDetails") or {}
        ref = hd.get("referenceNumber") or ""
        ref_bit = f" સંદર્ભ {ref}." if ref else ""
        return (
            f"{name}ભાઈ, કુલ ₹{ledger:,} માંથી ₹{hold:,} હોલ્ડમાં છે{ref_bit} "
            f"ઉપલબ્ધ રકમ ₹{avail:,} છે. હોલ્ડ રકમ ગઈ નથી — સેટલમેન્ટ/ચકાસણી પછી સ્થિતિ અપડેટ થશે."
        )

    if avail != ledger:
        return (
            f"{name}ભાઈ, કુલ લેજર બેલેન્સ ₹{ledger:,} છે અને હાલ વાપરી શકાય તેવી રકમ ₹{avail:,} છે. "
            f"બાકીની ₹{ledger - avail:,} રકમ હાલ મર્યાદા/હોલ્ડ અંતર્ગત છે."
        )

    return (
        f"{name}ભાઈ, તમારા ખાતામાં કુલ ₹{ledger:,} છે અને હાલ વાપરી શકાય તેવી રકમ પણ ₹{avail:,} છે."
    )


def groundedReplyForQuestion(
    user_text: str,
    snapshot: dict[str, Any],
    customer_name: str,
    last_agent_answer: str = "",
) -> str | None:
    # Charge discrepancy / WHY questions must go to LLM — do not intercept
    if isChargeDiscrepancyQuestion(user_text):
        return None

    # C2 Complexity Gate: If customer query is long, multi-clause, or emotional,
    # let LLM reason over the nuanced context instead of template intercepting.
    t_clean = (user_text or "").lower().strip()
    if len(t_clean) > 60:
        complexity_markers = (
            "pan", "parantu", "kem ke", "problem", "khotu", "wrong",
            "mari bhul", "mari galti", "complaint", "naraz", "advocate",
            "court", "police", "fari kem", "samjatu nathi", "kayda",
            "lekin", "magar", "kyu", "reason", "but", "however", "why"
        )
        if any(cm in t_clean for cm in complexity_markers) or t_clean.count("?") > 1:
            return None

    if isActionOrProcedureQuery(user_text):
        guidance = explainGuidanceFromSnapshot(snapshot, user_text, customer_name)
        if guidance:
            return guidance

    if customerAskedAboutFunds(user_text):
        return explainFundsFromSnapshot(snapshot, customer_name)

    if last_agent_answer and user_text:
        norm_q = re.sub(r"\s+", " ", user_text.lower().strip())
        if len(norm_q) < 80 and any(
            k in norm_q for k in ("samji", "સમજ", "fari", "ફરી", "nai vapri", "નથી વાપરી")
        ):
            funds = explainFundsFromSnapshot(snapshot, customer_name)
            if funds:
                return funds

    return None
