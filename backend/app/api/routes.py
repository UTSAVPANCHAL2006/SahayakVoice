"""
REST API endpoints for Sahayak Voice V2.
Provides health check, scenario listing for the 5 banking cases, and call initiation.
Matches all frontend REST queries:
- /health and /api/health
- /api/scenarios and /api/scenarios/supervisor
- /api/demo/start and /api/sessions
- /api/calls/{sessionId} and /api/calls/{sessionId}/supervisor
- /api/calls/{sessionId}/end
- /api/stt
"""

from __future__ import annotations

import uuid
from typing import Any
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.tools.banking import getAccountSnapshot, listScenarioAccounts
from app.voice.stt import SarvamSttClient
from app.voice.tts import audioCache

router = APIRouter()
stt_client = SarvamSttClient()

# In-memory session registry
SESSIONS: dict[str, dict[str, Any]] = {}


class StartCallRequest(BaseModel):
    accountId: str
    primaryIssue: str | None = None
    callLang: str = "gujarati"


@router.get("/health")
@router.get("/api/health")
def healthCheck() -> dict[str, Any]:
    """Health check endpoint expected by frontend."""
    return {
        "ok": True,
        "status": "ok",
        "version": "v2",
        "language": "gujarati",
        "database": "connected (v2 standalone grounded)",
        "accounts": len(listScenarioAccounts()),
        "langfuse": settings.langfuseEnabled,
        "llm_provider": "openai",
        "audio_cache": audioCache.stats(),
    }


@router.get("/api/scenarios")
def getScenarios() -> list[dict[str, Any]]:
    """Returns the 5 canonical retail banking scenarios."""
    return listScenarioAccounts()


@router.get("/api/scenarios/supervisor")
@router.get("/api/supervisor/scenarios")
def getSupervisorScenarios() -> list[dict[str, Any]]:
    """Supervisor view of the scenarios with expected last 4 digits."""
    return listScenarioAccounts()


@router.post("/api/demo/start")
def startDemoCall(accountId: str, lang: str = "gujarati") -> dict[str, Any]:
    """Starts a demo call as requested by frontend dashboard."""
    session_id = f"v2-sess-{uuid.uuid4().hex[:10]}"
    snap = getAccountSnapshot(accountId)
    SESSIONS[session_id] = {
        "sessionId": session_id,
        "accountId": accountId,
        "customerName": snap.get("customerName", "ગ્રાહક"),
        "primaryIssue": snap.get("primaryIssue"),
        "caseLabel": snap.get("caseLabel"),
        "callLang": lang,
        "maskedAcct": snap.get("maskedAcct"),
        "expectedLast4": snap.get("expectedLast4"),
        "snapshot": snap,
        "phase": "connecting",
        "verified": False,
        "messages": [],
    }
    return {
        "sessionId": session_id,
        "accountId": accountId,
        "callLang": lang,
        "maskedAcct": snap.get("maskedAcct"),
    }


@router.post("/api/sessions")
def startCallSession(req: StartCallRequest) -> dict[str, Any]:
    """Creates a new call session for a customer account."""
    return startDemoCall(req.accountId, req.callLang)


@router.get("/api/calls/{session_id}")
def getCallSession(session_id: str) -> dict[str, Any]:
    """Retrieves session metadata."""
    if session_id in SESSIONS:
        sess = SESSIONS[session_id]
        return {
            "sessionId": session_id,
            "accountId": sess.get("accountId"),
            "maskedAcct": sess.get("maskedAcct"),
            "scenario": sess.get("caseLabel", sess.get("primaryIssue", "")),
            "phase": sess.get("phase", "connecting"),
            "verified": sess.get("verified", False),
            "transcript": sess.get("messages", []),
            "proof": sess.get("proof", {}),
        }
    snap = getAccountSnapshot("ACC-LIEN-PRIYA")
    return {
        "sessionId": session_id,
        "accountId": snap["accountId"],
        "maskedAcct": snap.get("maskedAcct"),
        "scenario": snap.get("caseLabel", "Lien"),
        "phase": "connecting",
        "verified": False,
        "transcript": [],
        "proof": {},
    }


@router.get("/api/calls/{session_id}/supervisor")
def getCallSupervisorHint(session_id: str) -> dict[str, Any]:
    """Retrieves supervisor guidance and expected last 4 digits."""
    sess = SESSIONS.get(session_id, {})
    account_id = sess.get("accountId", "ACC-LIEN-PRIYA")
    snap = sess.get("snapshot") or getAccountSnapshot(account_id)
    return {
        "sessionId": session_id,
        "accountId": account_id,
        "customerName": snap.get("customerName"),
        "primaryIssue": snap.get("primaryIssue"),
        "caseLabel": snap.get("caseLabel"),
        "callLang": "gujarati",
        "expectedLast4": snap.get("expectedLast4"),
        "maskedAcct": snap.get("maskedAcct"),
        "phase": sess.get("phase", "connecting"),
        "verified": sess.get("verified", False),
    }


@router.post("/api/calls/{session_id}/end")
def endCallSessionEndpoint(session_id: str) -> dict[str, Any]:
    """Terminates session on customer or manager request."""
    if session_id in SESSIONS:
        SESSIONS[session_id]["phase"] = "end"
        SESSIONS[session_id]["callEnded"] = True
    return {"status": "ended", "sessionId": session_id}


@router.post("/api/stt")
async def transcribeAudioUpload(
    file: UploadFile = File(...),
    lang: str = "gujarati",
    sessionId: str | None = None,
) -> dict[str, Any]:
    """Transcribes an uploaded audio file via Sarvam Saaras model."""
    audio_bytes = await file.read()
    transcript = stt_client.transcribe(audio_bytes, filename=file.filename or "reply.webm", language=lang)
    return {"transcript": transcript}
