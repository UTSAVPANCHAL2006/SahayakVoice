"""
Fetch prompts and context builders for Sahayak Voice V2.
Formats authorized account facts for injection into LLM prompts.
"""

from __future__ import annotations

from typing import Any


def formatAccountFactsForLlm(snapshot: dict[str, Any]) -> str:
    """Formats authorized banking facts cleanly for grounding."""
    lines = [
        f"Customer Name: {snapshot.get('customerName')}",
        f"Masked Account: {snapshot.get('maskedAcct')}",
        f"Primary Issue: {snapshot.get('primaryIssue')}",
        f"Total Ledger Balance: ₹{snapshot.get('ledgerBalanceInr', 0):,}",
        f"Available Balance to Spend: ₹{snapshot.get('availableBalanceInr', 0):,}",
        f"Hold / Blocked Amount: ₹{snapshot.get('holdAmountInr', 0):,}",
    ]

    cheque = snapshot.get("cheque")
    if cheque:
        lines.append(f"Cheque Details: Cheque No {cheque.get('chequeNumber')}, Amount ₹{cheque.get('amountInr', 0):,}, Payee: {cheque.get('payeeName')}, Reason: {cheque.get('reasonCode')}, Bounce Charges: ₹{cheque.get('chargesInr', 0):,}")

    lien = snapshot.get("lienDetails")
    if lien:
        lines.append(f"Lien Details: Authority: {lien.get('authority')}, Ref: {lien.get('referenceNumber')}, Lien Amount: ₹{lien.get('lienAmount', 0):,}, Usable: ₹{lien.get('usableBalanceInr', 0):,}")

    hold = snapshot.get("holdDetails")
    if hold:
        lines.append(f"Hold Details: Ref: {hold.get('referenceNumber')}, Hold Amount: ₹{hold.get('holdAmount', 0):,}, Reason: {hold.get('holdReason')}")

    freeze = snapshot.get("freezeDetails")
    if freeze:
        lines.append(f"Debit Freeze Details: Type: {freeze.get('freezeType')}, Reason: {freeze.get('reason')}, Required Documents: {freeze.get('requiredDocuments')}")

    inop = snapshot.get("inoperativeDetails")
    if inop:
        lines.append(f"Inoperative Details: Status: {inop.get('status')}, Last Active: {inop.get('lastTransactionDate')}, Reactivation: {inop.get('reactivationMethod')}")

    return "\n".join(lines)
