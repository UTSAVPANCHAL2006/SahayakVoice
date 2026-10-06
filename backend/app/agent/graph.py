"""
LangGraph StateGraph for Sahayak Voice V2.
A clean, beginner-friendly state machine powering all 5 banking cases.

HOW TO READ THIS GRAPH:
1. START -> GreetNode -> ConsentNode
2. ConsentNode -> (VerifyNode | EndNode)
3. VerifyNode -> (FetchNode | VerifyNode | EndNode)
4. FetchNode -> ExplainNode -> ConversationNode
5. ConversationNode -> (ConversationNode | HandoffNode | EndNode)
6. HandoffNode -> (HandoffNode | EndNode)
7. EndNode -> END
"""

from __future__ import annotations

from typing import Any, Literal
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.consent import getConsent
from app.agent.nodes.conversation import handleConversation
from app.agent.nodes.end import endCall
from app.agent.nodes.explain import explainIssue
from app.agent.nodes.fetch import fetchAccount
from app.agent.nodes.greet import greetCustomer
from app.agent.nodes.handoff import handleHandoff
from app.agent.nodes.verify import verifyCustomer
from app.agent.state import CallState


# ── Node Wrappers ─────────────────────────────────────────────────────────────

def greetStep(state: CallState) -> CallState:
    patch = greetCustomer(state)
    return {**state, **patch}


def consentStep(state: CallState) -> CallState:
    patch = getConsent(state)
    return {**state, **patch}


def verifyStep(state: CallState) -> CallState:
    patch = verifyCustomer(state)
    return {**state, **patch}


def fetchStep(state: CallState) -> CallState:
    patch = fetchAccount(state)
    return {**state, **patch}


def explainStep(state: CallState) -> CallState:
    patch = explainIssue(state)
    return {**state, **patch}


def conversationStep(state: CallState) -> CallState:
    patch = handleConversation(state)
    updated = {**state, **patch}
    # Explicit LangGraph conditional edge routing
    next_target = routeAfterConversation(updated)
    if next_target == "HandoffNode":
        updated["phase"] = "handoff_connecting"
    elif next_target == "EndNode":
        updated["phase"] = "end"
    else:
        updated["phase"] = "conversation"
    return updated


def handoffStep(state: CallState) -> CallState:
    patch = handleHandoff(state)
    return {**state, **patch}


def endStep(state: CallState) -> CallState:
    patch = endCall(state)
    return {**state, **patch}


# ── Routing Functions ─────────────────────────────────────────────────────────

def routeAfterConsent(state: CallState) -> Literal["VerifyNode", "EndNode"]:
    if state.get("callEnded") or state.get("phase") == "end":
        return "EndNode"
    return "VerifyNode"


def routeAfterVerify(state: CallState) -> Literal["FetchNode", "VerifyNode", "EndNode"]:
    if state.get("callEnded") or state.get("phase") == "end":
        return "EndNode"
    if state.get("verified"):
        return "FetchNode"
    return "VerifyNode"


def routeAfterConversation(state: CallState) -> Literal["ConversationNode", "HandoffNode", "EndNode"]:
    """Conditional edge evaluating customer intent flags to route to Handoff, End, or loop."""
    if state.get("callEnded") or state.get("phase") == "end":
        return "EndNode"
    if state.get("handoffRequested") or state.get("phase") in ("handoff", "handoff_connecting"):
        return "HandoffNode"
    return "ConversationNode"


def routeAfterHandoff(state: CallState) -> Literal["HandoffNode", "EndNode"]:
    if state.get("callEnded") or state.get("phase") == "end":
        return "EndNode"
    return "HandoffNode"


# ── StateGraph Workflow Construction ──────────────────────────────────────────

def buildWorkflow():
    """Builds and compiles the full LangGraph StateGraph."""
    graph = StateGraph(CallState)

    graph.add_node("GreetNode", greetStep)
    graph.add_node("ConsentNode", consentStep)
    graph.add_node("VerifyNode", verifyStep)
    graph.add_node("FetchNode", fetchStep)
    graph.add_node("ExplainNode", explainStep)
    graph.add_node("ConversationNode", conversationStep)
    graph.add_node("HandoffNode", handoffStep)
    graph.add_node("EndNode", endStep)

    graph.add_edge(START, "GreetNode")
    graph.add_edge("GreetNode", "ConsentNode")
    graph.add_conditional_edges("ConsentNode", routeAfterConsent)
    graph.add_conditional_edges("VerifyNode", routeAfterVerify)
    graph.add_edge("FetchNode", "ExplainNode")
    graph.add_edge("ExplainNode", "ConversationNode")
    graph.add_conditional_edges("ConversationNode", routeAfterConversation)
    graph.add_conditional_edges("HandoffNode", routeAfterHandoff)
    graph.add_edge("EndNode", END)

    return graph.compile()


# ── Single-Turn Runtime Dispatcher (Used by WebSocket) ─────────────────────────

class SahayakAgent:
    """Manages turn-by-turn conversation for live WebSocket and test runs."""

    def __init__(self) -> None:
        self.workflow = buildWorkflow()

    def initializeCall(self, state: CallState, db: Any = None) -> CallState:
        """Starts call: loads snapshot and triggers GreetNode."""
        snap = state.get("snapshot") or state.get("accountFacts") or {}
        if not snap:
            from app.tools.banking import getAccountSnapshot
            snap = getAccountSnapshot(state.get("accountId", "ACC-LIEN-PRIYA"), db)
            state["snapshot"] = snap
            state["accountFacts"] = snap
            state["customerName"] = snap.get("customerName", "ગ્રાહક")
            state["caseType"] = snap.get("primaryIssue", "")

        patch = greetCustomer(state, db)
        updated = {**state, **patch}
        self.recordTurnReply(updated)
        return updated

    def processTurn(self, state: CallState, db: Any = None) -> CallState:
        """Dispatches customer turn to the active node based on phase and mode."""
        phase = state.get("phase", "consent")
        mode = state.get("callMode", "ai")

        if phase == "handoff_connecting":
            from app.agent.nodes.handoff import startHumanConversation

            patch = startHumanConversation(state, db)
            updated = {**state, **patch}
            self.recordTurnReply(updated)
            return updated

        # Manager mode — no Sahayak conversation
        if mode == "human" or phase == "handoff":
            patch = handleHandoff(state, db)
            updated = {**state, **patch}
            self.recordTurnReply(updated)
            return updated

        if phase == "consent":
            patch = getConsent(state, db)
            updated = {**state, **patch}
            self.recordTurnReply(updated)
            return updated

        if phase == "verify":
            patch = verifyCustomer(state, db)
            updated = {**state, **patch}
            # Auto-chain to fetch and explain if verification just succeeded
            if updated.get("verified") and updated.get("phase") == "fetch":
                fetch_patch = fetchAccount(updated, db)
                updated = {**updated, **fetch_patch}
                explain_patch = explainIssue(updated, db)
                updated = {**updated, **explain_patch}
            self.recordTurnReply(updated)
            return updated

        if phase in ("explain", "conversation"):
            updated = conversationStep(state)
            self.recordTurnReply(updated)
            return updated

        if phase == "end":
            patch = endCall(state, db)
            updated = {**state, **patch}
            self.recordTurnReply(updated)
            return updated

        return state

    @staticmethod
    def recordTurnReply(state: CallState) -> None:
        """Appends assistant message to transcript if reply is present."""
        reply = (state.get("lastAgentReply") or "").strip()
        speaker = state.get("speaker") or "Sahayak"
        if reply:
            msgs = list(state.get("messages") or [])
            msgs.append({
                "role": "assistant",
                "speaker": speaker,
                "content": reply,
            })
            state["messages"] = msgs
