"""
Speech-to-Text (STT) service using Sarvam AI Saaras model.
Converts customer audio bytes to Gujarati text.
"""

from __future__ import annotations

import httpx
from app.config import settings
from app.voice.language import getSarvamSpeechCode


def getAudioMimeType(filename: str, fallback: str = "audio/webm") -> str:
    """Determine MIME type based on file extension."""
    name = (filename or "").lower()
    if name.endswith(".mp3"):
        return "audio/mpeg"
    if name.endswith(".mp4") or name.endswith(".m4a"):
        return "audio/mp4"
    if name.endswith(".wav"):
        return "audio/wav"
    if name.endswith(".ogg"):
        return "audio/ogg"
    return fallback


def extractTranscriptText(payload: dict) -> str:
    """Extract transcript string from Sarvam response structure."""
    if not isinstance(payload, dict):
        return ""
    for key in ("transcript", "text", "transcription"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    for nest in ("data", "result", "output"):
        inner = payload.get(nest)
        if isinstance(inner, dict):
            extracted = extractTranscriptText(inner)
            if extracted:
                return extracted
    items = payload.get("transcripts")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            extracted = extractTranscriptText(first)
            if extracted:
                return extracted
        if isinstance(first, str):
            return first.strip()
    return ""


class SarvamSttClient:
    def isConfigured(self) -> bool:
        return bool(settings.sarvamApiKey)

    def transcribe(
        self,
        audio: bytes,
        filename: str = "input.webm",
        language: str = "gujarati",
    ) -> str:
        if not self.isConfigured() or not audio:
            return ""

        headers = {"api-subscription-key": settings.sarvamApiKey}
        mime = getAudioMimeType(filename)
        files = {"file": (filename, audio, mime)}
        data = {
            "language_code": getSarvamSpeechCode(language),
            "model": settings.sarvamSttModel,
            "mode": "transcribe",
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers=headers,
                    files=files,
                    data=data,
                )
                if res.status_code == 200:
                    return extractTranscriptText(res.json())
        except Exception:
            pass
        return ""
