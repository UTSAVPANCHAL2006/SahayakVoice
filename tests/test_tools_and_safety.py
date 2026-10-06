"""
Tests for authorized banking tools and fact safety in Sahayak Voice V2.
Validates:
- Tool execution against snapshot (get_account_summary, get_balances, get_lien_details, etc.)
- Demo service request creation (CAS-2026-XXXX)
- Safe rejection of unknown tools
- Strict fact grounding without arbitrary SQL
"""

import pytest
from app.tools.banking import executeBankingTool, getAccountSnapshot, registerServiceRequest


def test_get_balances_tool():
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    res = executeBankingTool("get_balances", {}, snap)

    assert res["ledgerBalanceInr"] == 52783
    assert res["availableBalanceInr"] == 14364
    assert res["holdAmountInr"] == 38419


def test_get_cheque_status_tool():
    snap = getAccountSnapshot("ACC-CHQ-HARDIK")
    res = executeBankingTool("get_cheque_status", {}, snap)

    assert res["chequeNumber"] == "847293"
    assert res["amountInr"] == 49847
    assert res["chargesInr"] == 523


def test_get_freeze_details_tool():
    snap = getAccountSnapshot("ACC-FREEZE-VIKRAM")
    res = executeBankingTool("get_freeze_details", {}, snap)

    assert "Debit Freeze" in res["freezeType"]
    assert "KYC" in res["reason"]


def test_create_service_request():
    snap = getAccountSnapshot("ACC-HOLD-AMIT")
    res = executeBankingTool(
        "create_demo_service_request",
        {"category": "UPI Hold Review", "notes": "Customer requested settlement verification"},
        snap,
    )

    assert res["status"] == "REGISTERED"
    assert res["caseRef"].startswith("CAS-2026-")
    assert res["category"] == "UPI Hold Review"


def test_unknown_tool_safety():
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    res = executeBankingTool("arbitrary_sql_injection", {"query": "DROP TABLE users"}, snap)

    assert "error" in res
    assert "Unknown tool" in res["error"]
