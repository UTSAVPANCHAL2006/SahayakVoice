"""
Explain Node for Sahayak Voice V2.
Provides the initial, factual explanation of the primary banking issue.
"""

from __future__ import annotations

from typing import Any
from app.agent.state import CallState
from app.prompts.explain import buildInitialExplanation


def explainIssue(state: CallState, db: Any = None) -> dict[str, Any]:
    """Explains the verified issue cleanly in Gujarati."""
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    explanation = buildInitialExplanation(snap)

    return {
        "phase": "conversation",
        "speaker": "Sahayak",
        "lastAgentReply": explanation,
        "proof": {
            **(state.get("proof") or {}),
            "explained": True,
        },
    }
