"""
Tests for deterministic verification and Gujarati number parsing in Sahayak Voice V2.
Validates:
- Spoken Gujarati compound numbers ("સાત હજાર બસો ને ચોરાણું")
- Digit sequences ("ચાર પાંચ બે એક")
- Gujarati numerals ("૪૫૨૧")
- ASCII numbers ("4521")
- Wrong digits and retries
"""

import pytest
from app.agent.nodes.verify import (
    extractVerificationCandidates,
    parseIndianSpokenNumber,
    verifyCustomer,
)
from app.agent.state import CallState


def test_parse_spoken_gujarati_compound_numbers():
    # સાત હજાર બસો ને ચોરાણું = 7294
    val = parseIndianSpokenNumber("સાત હજાર બસો ને ચોરાણું")
    assert val == 7294

    # બસો ને ત્રીસ = 230
    val2 = parseIndianSpokenNumber("બસો ને ત્રીસ")
    assert val2 == 230

    # એક હજાર પાંચસો = 1500
    val3 = parseIndianSpokenNumber("એક હજાર પાંચસો")
    assert val3 == 1500


def test_extract_candidates_various_formats():
    # Compound Gujarati words
    c1 = extractVerificationCandidates("મારા ખાતાના આંકડા સાત હજાર બસો ને ચોરાણું છે")
    assert "7294" in c1

    # Digit by digit spoken Gujarati
    c2 = extractVerificationCandidates("ચાર પાંચ બે એક")
    assert "4521" in c2

    # Gujarati script numerals
    c3 = extractVerificationCandidates("મારું એકાઉન્ટ ૪૫૨૧ છે")
    assert "4521" in c3

    # Direct ASCII numbers
    c4 = extractVerificationCandidates("last four digits 5619 please check")
    assert "5619" in c4


def test_verify_node_success():
    state: CallState = {
        "sessionId": "test-1",
        "customerName": "Pratik Sharma",
        "snapshot": {"expectedLast4": "4521", "customerName": "Pratik Sharma"},
        "lastUserText": "ચાર પાંચ બે એક",
        "verifyRetries": 0,
    }
    result = verifyCustomer(state)
    assert result["verified"] is True
    assert result["phase"] == "fetch"
    assert result["verifyRetries"] == 0


def test_verify_node_spoken_compound_match():
    state: CallState = {
        "sessionId": "test-2",
        "customerName": "Hardik Patel",
        "snapshot": {"expectedLast4": "7294", "customerName": "Hardik Patel"},
        "lastUserText": "હા સાહેબ સાત હજાર બસો ને ચોરાણું",
        "verifyRetries": 0,
    }
    result = verifyCustomer(state)
    assert result["verified"] is True
    assert result["phase"] == "fetch"


def test_verify_node_mismatch_and_retry():
    state: CallState = {
        "sessionId": "test-3",
        "customerName": "Pratik Sharma",
        "snapshot": {"expectedLast4": "4521", "customerName": "Pratik Sharma"},
        "lastUserText": "9999",
        "verifyRetries": 0,
    }
    result = verifyCustomer(state)
    assert result["verified"] is False
    assert result["phase"] == "verify"
    assert result["verifyRetries"] == 1
    assert "મેળ ખાતા નથી" in result["lastAgentReply"]


def test_verify_node_exceeded_retries():
    state: CallState = {
        "sessionId": "test-4",
        "customerName": "Pratik Sharma",
        "snapshot": {"expectedLast4": "4521", "customerName": "Pratik Sharma"},
        "lastUserText": "9999",
        "verifyRetries": 2,
    }
    result = verifyCustomer(state)
    assert result["verified"] is False
    assert result["phase"] == "end"
    assert result["callEnded"] is True
