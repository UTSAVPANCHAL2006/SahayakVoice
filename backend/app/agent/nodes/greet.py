"""
Greet Node for Sahayak Voice V2.
Initializes outbound call and greets customer in Gujarati.
"""

from __future__ import annotations

from typing import Any
from app.agent.state import CallState
from app.prompts.greet import buildGreetingPrompt
from app.voice.language import topicPhrase


def greetCustomer(state: CallState, db: Any = None) -> dict[str, Any]:
    """Greets the customer and sets stage for consent."""
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    primary_issue = state.get("caseType") or snap.get("primaryIssue") or ""

    phrase = topicPhrase(primary_issue)
    greeting_text = buildGreetingPrompt(customer_name, phrase)

    return {
        "phase": "consent",
        "callMode": "ai",
        "speaker": "Sahayak",
        "lastAgentReply": greeting_text,
    }
