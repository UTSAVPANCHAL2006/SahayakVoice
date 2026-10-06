"""
Banking data and service tools for Sahayak Voice V2.
Encapsulates ground-truth banking facts for all 5 retail banking cases:
1. Cheque Bounce
2. Lien
3. Hold / UPI Pending
4. Debit Freeze
5. Inoperative Account
"""

from __future__ import annotations

import uuid
from typing import Any


SEED_ACCOUNTS: list[dict[str, Any]] = [
    {
        "accountId": "ACC-CHQ-HARDIK",
        "cifId": "CIF-CHQ-001",
        "fullName": "Hardik Patel",
        "customerName": "Hardik Patel",
        "mobile": "9824716390",
        "maskedAcct": "XXXX7294",
        "expectedLast4": "7294",
        "primaryIssue": "CHEQUE_BOUNCE",
        "caseLabel": "Cheque Bounce",
        "preferredLang": "gujarati",
        "ledgerBalanceInr": 18472,
        "availableBalanceInr": 18472,
        "holdAmountInr": 0,
        "cheque": {
            "chequeNumber": "847293",
            "payeeName": "Rajesh Traders (રાજેશ ટ્રેડર્સ)",
            "amountInr": 49847,
            "bounceDate": "28 સપ્ટેમ્બર 2026",
            "reasonCode": "NSF - Insufficient Funds (અપૂરતું બેલેન્સ)",
            "chargesInr": 523,
        },
        "extra": {
            "chequeNumber": "847293",
            "payeeName": "Rajesh Traders",
            "amountInr": 49847,
            "reasonCode": "NSF - Insufficient Funds",
            "chargesInr": 523,
        },
    },
    {
        "accountId": "ACC-LIEN-PRIYA",
        "cifId": "CIF-LIEN-001",
        "fullName": "Pratik Sharma",
        "customerName": "Pratik Sharma",
        "mobile": "9873165482",
        "maskedAcct": "XXXX4521",
        "expectedLast4": "4521",
        "primaryIssue": "LIEN",
        "caseLabel": "Lien Marked",
        "preferredLang": "gujarati",
        "ledgerBalanceInr": 52783,
        "availableBalanceInr": 14364,
        "holdAmountInr": 38419,
        "lienDetails": {
            "lienAmount": 38419,
            "authority": "Income Tax Department (આવકવેરા વિભાગ)",
            "referenceNumber": "IT-ATTACH-2026-8891",
            "markedDate": "18 સપ્ટેમ્બર 2026",
            "usableBalanceInr": 14364,
            "reason": "Statutory tax attachment notice",
        },
        "extra": {
            "authority": "Income Tax Department",
            "referenceNumber": "IT-ATTACH-2026-8891",
            "holdAmountInr": 38419,
            "usableBalanceInr": 14364,
        },
    },
    {
        "accountId": "ACC-HOLD-AMIT",
        "cifId": "CIF-HOLD-001",
        "fullName": "Amit Singh",
        "customerName": "Amit Singh",
        "mobile": "9815529047",
        "maskedAcct": "XXXX5619",
        "expectedLast4": "5619",
        "primaryIssue": "HOLD",
        "caseLabel": "UPI / Clearing Hold",
        "preferredLang": "gujarati",
        "ledgerBalanceInr": 97341,
        "availableBalanceInr": 77494,
        "holdAmountInr": 19847,
        "holdDetails": {
            "holdAmount": 19847,
            "referenceNumber": "UPI-HOLD-2026-3021",
            "holdReason": "Merchant UPI settlement dispute verification",
            "holdDate": "26 સપ્ટેમ્બર 2026",
            "resolutionEta": "2 કાર્યકારી દિવસ",
        },
        "extra": {
            "holdAmountInr": 19847,
            "referenceNumber": "UPI-HOLD-2026-3021",
        },
    },
    {
        "accountId": "ACC-FREEZE-VIKRAM",
        "cifId": "CIF-FRZ-001",
        "fullName": "Vikram Mehta",
        "customerName": "Vikram Mehta",
        "mobile": "9820014729",
        "maskedAcct": "XXXX3182",
        "expectedLast4": "3182",
        "primaryIssue": "DEBIT_FREEZE",
        "caseLabel": "Debit Freeze",
        "preferredLang": "gujarati",
        "ledgerBalanceInr": 78329,
        "availableBalanceInr": 0,
        "holdAmountInr": 0,
        "freezeDetails": {
            "freezeType": "Debit Freeze (માત્ર નાણાં ઉપાડ બંધ, જમા ચાલુ)",
            "reason": "Periodic KYC Re-verification Pending (KYC અપડેટ બાકી)",
            "branchVisitRequired": True,
            "requiredDocuments": "Aadhaar Card, PAN Card, Passport Size Photo",
            "resolutionTime": "બ્રાન્ચમાં દસ્તાવેજ જમા કર્યા બાદ ૨૪ કલાકમાં અનફ્રીઝ",
        },
        "extra": {
            "freezeType": "DEBIT_FREEZE",
            "reason": "KYC Pending",
        },
    },
    {
        "accountId": "ACC-INOP-SUNITA",
        "cifId": "CIF-INOP-001",
        "fullName": "Sunil Rao",
        "customerName": "Sunil Rao",
        "mobile": "9892147365",
        "maskedAcct": "XXXX8920",
        "expectedLast4": "8920",
        "primaryIssue": "INOPERATIVE",
        "caseLabel": "Inoperative Account",
        "preferredLang": "gujarati",
        "ledgerBalanceInr": 43827,
        "availableBalanceInr": 0,
        "holdAmountInr": 0,
        "inoperativeDetails": {
            "status": "Inoperative / Dormant (૨ વર્ષથી કોઈ વ્યવહાર ન હોવાથી નિષ્ક્રિય)",
            "lastTransactionDate": "14 ઑગસ્ટ 2024",
            "reactivationMethod": "હોમ બ્રાન્ચ ખાતે કેવાયસી ફોર્મ તથા ઓળખ પુરાવા જમા કરાવો",
            "chargesForReactivation": 0,
            "safetyNotice": "તમારું બેલેન્સ સંપૂર્ણ સુરક્ષિત છે, કોઈ રકમ કપાણી નથી",
        },
        "extra": {
            "status": "INOPERATIVE",
            "lastTxn": "2024-08-14",
        },
    },
]


def listScenarioAccounts() -> list[dict[str, Any]]:
    """Returns the 5 canonical banking scenarios for dashboard and tests."""
    return list(SEED_ACCOUNTS)


def getAccountSnapshot(account_id: str, db: Any = None) -> dict[str, Any]:
    """
    Returns verified ground-truth account snapshot for the given account id.
    Falls back to closest seed account if id not found.
    """
    for acc in SEED_ACCOUNTS:
        if acc["accountId"].lower() == (account_id or "").lower():
            return dict(acc)
    # Default fallback to first scenario
    return dict(SEED_ACCOUNTS[0])


def registerServiceRequest(account_id: str, category: str, notes: str = "") -> dict[str, Any]:
    """Generates a formal bank service request reference."""
    case_ref = f"CAS-2026-{uuid.uuid4().hex[:6].upper()}"
    return {
        "status": "REGISTERED",
        "caseRef": case_ref,
        "category": category,
        "accountId": account_id,
        "notes": notes,
        "resolutionEtaDays": 3,
    }


def executeBankingTool(tool_name: str, arguments: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    """
    Executes authorized banking tools safely against the account snapshot.
    Does not touch arbitrary tables or execute raw SQL.
    """
    name = (tool_name or "").strip()
    if name == "get_account_summary":
        return {
            "customerName": snapshot.get("customerName"),
            "maskedAcct": snapshot.get("maskedAcct"),
            "primaryIssue": snapshot.get("primaryIssue"),
            "ledgerBalanceInr": snapshot.get("ledgerBalanceInr"),
            "availableBalanceInr": snapshot.get("availableBalanceInr"),
        }

    if name == "get_balances":
        return {
            "ledgerBalanceInr": snapshot.get("ledgerBalanceInr"),
            "availableBalanceInr": snapshot.get("availableBalanceInr"),
            "holdAmountInr": snapshot.get("holdAmountInr"),
        }

    if name == "get_cheque_status":
        return snapshot.get("cheque") or {"notice": "No returned cheque on file"}

    if name == "get_lien_details":
        return snapshot.get("lienDetails") or {"notice": "No active statutory lien"}

    if name == "get_hold_details":
        return snapshot.get("holdDetails") or {"notice": "No active clearing hold"}

    if name == "get_freeze_details":
        return snapshot.get("freezeDetails") or {"notice": "No active debit freeze"}

    if name == "get_inoperative_details":
        return snapshot.get("inoperativeDetails") or {"notice": "Account is active"}

    if name == "list_recent_transactions":
        return {
            "transactions": [
                {"date": "2026-09-25", "desc": "ATM Cash Withdrawal", "amount": -2000, "type": "DEBIT"},
                {"date": "2026-09-20", "desc": "NEFT Salary Credit", "amount": 35000, "type": "CREDIT"},
            ]
        }

    if name == "create_demo_service_request":
        cat = arguments.get("category", "General Inquiry")
        notes = arguments.get("notes", "")
        return registerServiceRequest(snapshot.get("accountId", "unknown"), cat, notes)

    return {"error": f"Unknown tool: {name}"}
