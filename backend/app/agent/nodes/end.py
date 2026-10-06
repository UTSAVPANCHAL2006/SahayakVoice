"""
End Node for Sahayak Voice V2.
Terminates the call cleanly and deterministically.
"""

from __future__ import annotations

from typing import Any
from app.agent.state import CallState
from app.prompts.end import buildCallEndReply


def endCall(state: CallState, db: Any = None) -> dict[str, Any]:
    """Wraps up the session and marks call ended."""
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    closing_reply = state.get("lastAgentReply") or buildCallEndReply(customer_name)

    return {
        "phase": "end",
        "callEnded": True,
        "callMode": "ended",
        "lastAgentReply": closing_reply,
        "proof": {
            **(state.get("proof") or {}),
            "callEnded": True,
        },
    }
