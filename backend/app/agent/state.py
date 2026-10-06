"""
Unified CallState for Sahayak Voice V2.
Holds the complete conversation state across all 8 nodes.
"""

from __future__ import annotations

from typing import Any, TypedDict


class CallState(TypedDict, total=False):
    sessionId: str
    accountId: str
    customerName: str
    caseType: str
    phase: str  # "greet" | "consent" | "verify" | "fetch" | "explain" | "conversation" | "handoff" | "end"
    callMode: str  # "ai" | "human" | "ended"
    verified: bool
    messages: list[dict[str, Any]]
    lastUserText: str
    lastAgentReply: str
    speaker: str  # "Sahayak" | "Senior Manager"
    assignedAgentName: str
    accountFacts: dict[str, Any]
    snapshot: dict[str, Any]
    toolExecuted: dict[str, Any]
    proof: dict[str, Any]
    resolvedTopics: list[str]
    handoffRequested: bool
    handoffComplete: bool
    callEnded: bool
    consentRetries: int
    verifyRetries: int
