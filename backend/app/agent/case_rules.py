"""
Dynamic Case Rules for Sahayak Voice V2.
Generates structured banking explanation guidelines and resolution steps
per case using live snapshot values, avoiding hardcoded amounts in prompts.
"""

from __future__ import annotations

from typing import Any


def getCaseRules(snapshot: dict[str, Any], customer_name: str = "") -> str:
    """
    Builds dynamic per-case explanation and resolution guidance
    using actual values from the customer's account snapshot.
    """
    issue = (snapshot.get("primaryIssue") or "").upper()
    avail = int(snapshot.get("availableBalanceInr") or 0)
    ledger = int(snapshot.get("ledgerBalanceInr") or 0)
    name = (customer_name or snapshot.get("customerName") or "ગ્રાહક").split()[0]

    if "CHEQUE" in issue:
        cheque = snapshot.get("cheque") or snapshot.get("extra") or {}
        chq_num = cheque.get("chequeNumber", "847293")
        amt = int(cheque.get("amountInr", 49847))
        chg = int(cheque.get("chargesInr", 523))
        payee = cheque.get("payeeName", "Rajesh Traders")
        return (
            f"CASE SPECIFIC KNOWLEDGE [CHEQUE BOUNCE]:\n"
            f"- Cheque #{chq_num} for ₹{amt:,} payable to {payee} bounced due to insufficient funds.\n"
            f"- Charge applied: ₹{chg:,}.\n"
            f"- WHY IS THE CHARGE ₹{chg:,}? Explain politely: Under RBI 2022 revised cheque return guidelines, "
            f"cheques exceeding ₹25,000 incur a standard return charge of ₹{chg:,}. For lower amounts, the charge was lower (₹256 or ₹350). "
            f"In repeat bounce instances, regulations allow banks to levy standard penalty.\n"
            f"- RESOLUTION STEPS: Advise {name}bhai to immediately deposit ₹{amt:,} (cheque amount) + ₹{chg:,} (charge) "
            f"into their account, and contact {payee} to re-present the cheque or settle via NEFT/UPI."
        )

    if "LIEN" in issue:
        lien = snapshot.get("lienDetails") or snapshot.get("extra") or {}
        ref = lien.get("referenceNumber") or "IT-ATTACH-2026-8891"
        amt = int(lien.get("lienAmount") or snapshot.get("holdAmountInr") or 38419)
        authority = lien.get("authority") or "Income Tax Department (આવકવેરા વિભાગ)"
        return (
            f"CASE SPECIFIC KNOWLEDGE [STATUTORY LIEN]:\n"
            f"- A statutory attachment/lien of ₹{amt:,} is placed under order ref {ref} from {authority}.\n"
            f"- WHY IS MONEY BLOCKED? Bank is legally obligated under government order to hold ₹{amt:,}. "
            f"The money is completely SAFE and not deducted or lost.\n"
            f"- ACCESSIBILITY: The customer's remaining available balance of ₹{avail:,} is 100% usable.\n"
            f"- RESOLUTION STEPS: Customer should contact {authority} or their CA with reference {ref}. "
            f"They can visit their bank branch to obtain the official attachment notice copy. "
            f"Once {authority} sends clearance, the bank lifts the lien immediately."
        )

    if "HOLD" in issue:
        hold_dt = snapshot.get("holdDetails") or snapshot.get("extra") or {}
        ref = hold_dt.get("referenceNumber") or "UPI-HOLD-2026-3021"
        hold_amt = int(snapshot.get("holdAmountInr") or 19847)
        return (
            f"CASE SPECIFIC KNOWLEDGE [UPI / CLEARING HOLD]:\n"
            f"- A temporary hold of ₹{hold_amt:,} is placed under reference {ref} for UPI merchant dispute / clearing reconciliation.\n"
            f"- WHY IS IT HELD? Verification of pending settlement. The money is SAFE and has not been deducted.\n"
            f"- ACCESSIBILITY: Available balance of ₹{avail:,} is completely unrestricted.\n"
            f"- RESOLUTION STEPS: The hold automatically resolves within 48 hours (2 business days). "
            f"If not released after 48 hours, the bank will register an urgent service dispute ticket."
        )

    if "FREEZE" in issue:
        freeze_dt = snapshot.get("freezeDetails") or snapshot.get("extra") or {}
        docs = freeze_dt.get("requiredDocuments", "Aadhaar Card, PAN Card, Photo")
        return (
            f"CASE SPECIFIC KNOWLEDGE [DEBIT FREEZE / KYC PENDING]:\n"
            f"- Account has a debit freeze due to periodic KYC re-verification being overdue per RBI norms.\n"
            f"- WHAT IS BLOCKED? Only outgoing debits are temporarily restricted. Incoming credits/deposits are allowed.\n"
            f"- ACCESSIBILITY: Ledger balance ₹{ledger:,} is 100% safe. Zero penalty or deduction.\n"
            f"- RESOLUTION STEPS: Visit any nearest branch with {docs}, submit the Re-KYC form. "
            f"The debit freeze is removed within 24 hours of verification. Completely FREE of cost."
        )

    if "INOPERATIVE" in issue:
        inop = snapshot.get("inoperativeDetails") or snapshot.get("extra") or {}
        last_tx = inop.get("lastTransactionDate", "August 2024")
        return (
            f"CASE SPECIFIC KNOWLEDGE [INOPERATIVE / DORMANT ACCOUNT]:\n"
            f"- Account became inoperative due to no customer-initiated transactions for over 2 years (last active: {last_tx}).\n"
            f"- SAFETY: Total balance ₹{ledger:,} is 100% safe and intact. No maintenance penalty deducted.\n"
            f"- RESOLUTION STEPS: Visit HOME BRANCH with Aadhaar Card, PAN Card, and passport photo to submit a Re-KYC reactivation form. "
            f"Reactivation is completely FREE and processed within 24 hours.\n"
            f"- EMERGENCY: If urgent, visit branch today and request branch manager for expedited biometric Re-KYC."
        )

    return (
        f"CASE SPECIFIC KNOWLEDGE:\n"
        f"- Total ledger balance: ₹{ledger:,}, Available balance: ₹{avail:,}."
    )
