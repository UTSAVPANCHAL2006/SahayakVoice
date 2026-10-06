"""
WebSocket endpoint router for Sahayak Voice V2.
Streams real-time voice conversation turns on /ws/voice/{sessionId}.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket
from app.api.routes import SESSIONS
from app.ws.session import VoiceSessionHandler

router = APIRouter()
session_handler = VoiceSessionHandler()


@router.websocket("/ws/voice/{sessionId}")
async def websocketVoiceEndpoint(
    websocket: WebSocket,
    sessionId: str,
    lang: str | None = "gujarati",
):
    """Real-time bidirectional WebSocket voice connection."""
    account_id = "ACC-LIEN-PRIYA"
    if sessionId in SESSIONS:
        account_id = SESSIONS[sessionId].get("accountId", account_id)

    await session_handler.handle(
        websocket=websocket,
        db=None,
        session_id=sessionId,
        account_id=account_id,
    )
