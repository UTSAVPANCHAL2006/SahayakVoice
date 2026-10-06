"""
End Node for Sahayak Voice V2.
Terminates the call cleanly and deterministically.
Always uses the warm Gujarati closing from buildCallEndReply —
never re-uses the last LLM reply as the goodbye message.
"""

from __future__ import annotations

from typing import Any
from app.agent.state import CallState
from app.prompts.end import buildCallEndReply


def endCall(state: CallState, db: Any = None) -> dict[str, Any]:
    """Wraps up the session with a warm deterministic Gujarati closing."""
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"

    # Always use the rotating warm closing — never re-use the last LLM reply
    closing_reply = buildCallEndReply(customer_name)

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
