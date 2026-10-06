"""
OpenAI function definitions for authorized banking tools.
The LLM can only query these authorized read tools and request case creation.
Direct SQL execution is strictly forbidden.
"""

from __future__ import annotations

BANKING_TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_account_summary",
            "description": "Verified customer account overview: balances and primary issue.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balances",
            "description": "Ledger balance, available balance, and blocked/hold/lien amounts in INR.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cheque_status",
            "description": "Cheque bounce details if this account has a returned cheque.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lien_details",
            "description": "Lien amount, authority, notice reference, usable balance.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hold_details",
            "description": "Hold or pending UPI/clearing details and references.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_freeze_details",
            "description": "Debit freeze / restriction reason and branch visit requirements.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inoperative_details",
            "description": "Inoperative account reason, last active date, and KYC reactivation docs.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_recent_transactions",
            "description": "Last few disclosable transactions on this account.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 5}},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_demo_service_request",
            "description": "Register a demo bank complaint or service request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["category"],
                "additionalProperties": False,
            },
        },
    },
]
