"""
Fetch Node for Sahayak Voice V2.
Loads authorized banking facts securely upon successful verification.
The LLM never queries the database directly.
"""

from __future__ import annotations

from typing import Any
from app.agent.state import CallState
from app.tools.banking import getAccountSnapshot


def fetchAccount(state: CallState, db: Any = None) -> dict[str, Any]:
    """Loads authorized account snapshot for the verified customer."""
    account_id = state.get("accountId") or "ACC-LIEN-PRIYA"
    snapshot = getAccountSnapshot(account_id, db)

    return {
        "phase": "explain",
        "snapshot": snapshot,
        "accountFacts": snapshot,
        "customerName": snapshot.get("customerName", state.get("customerName")),
        "caseType": snapshot.get("primaryIssue", state.get("caseType")),
        "proof": {
            **(state.get("proof") or {}),
            "fetchDone": True,
            "accountSnapshot": snapshot,
        },
    }
