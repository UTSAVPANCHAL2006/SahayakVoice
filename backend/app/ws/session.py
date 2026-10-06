"""
WebSocket session handler for Sahayak Voice V2.
Streams real-time audio and JSON state events to the frontend client.

Technique 1: Speculative Filler — sends empathetic acknowledgment audio immediately
while the LLM is still processing. Hides inference latency from the user.
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any
from fastapi import WebSocket

from app.agent.graph import SahayakAgent
from app.config import settings
from app.tools.banking import getAccountSnapshot
from app.voice.language import getSpeakerName
from app.voice.stt import SarvamSttClient
from app.voice.tts import SarvamTtsClient, splitIntoSpokenSentences, audioCache


# ──────────────────────────────────────────────────────────────────────────────
# T1: Speculative Filler Phrases
# Gujarati empathetic acknowledgments — short enough to synthesize in <300ms
# These are pre-rendered into the AudioCache on startup to achieve 0ms TTFA.
# ──────────────────────────────────────────────────────────────────────────────

_FILLER_PHRASES = [
    "જી, સમજ્યો.",         # "Understood."
    "જી, હા.",              # "Yes."
    "ઠીક છે.",              # "Okay."
    "એક ક્ષણ.",             # "One moment."
    "જી, ચોક્કસ.",          # "Certainly."
]

# Which filler to use per turn (cycles through list for naturalness)
_filler_index = 0


def _nextFiller() -> str:
    global _filler_index
    phrase = _FILLER_PHRASES[_filler_index % len(_FILLER_PHRASES)]
    _filler_index += 1
    return phrase


# ──────────────────────────────────────────────────────────────────────────────
# Cache warm-up: pre-render all filler phrases on first SessionHandler creation
# ──────────────────────────────────────────────────────────────────────────────

def _warmupFillerCache(tts: SarvamTtsClient) -> None:
    """
    Pre-renders filler phrases into the AudioCache at startup.
    After this, each filler is served at 0ms (T3 cache hit).
    """
    speaker = getSpeakerName("ai")
    for phrase in _FILLER_PHRASES:
        audioCache.get(phrase, speaker) or tts.synthesize(phrase, speaker=speaker)


class VoiceSessionHandler:
    def __init__(self) -> None:
        self.agent = SahayakAgent()
        self.tts = SarvamTtsClient()
        self.stt = SarvamSttClient()
        # T1 + T3: warm up filler cache in background so first call is instant
        asyncio.get_event_loop().run_until_complete(
            asyncio.to_thread(_warmupFillerCache, self.tts)
        ) if False else None  # deferred to first request to avoid startup crash

    async def handle(
        self,
        websocket: WebSocket,
        db: Any,
        session_id: str,
        account_id: str = "ACC-LIEN-PRIYA",
    ) -> None:
        await websocket.accept()
        send_lock = asyncio.Lock()

        # T1+T3: warm up filler cache once per session (non-blocking)
        asyncio.create_task(asyncio.to_thread(_warmupFillerCache, self.tts))

        # Initialize call state with ground-truth snapshot
        snapshot = getAccountSnapshot(account_id, db)
        state: dict[str, Any] = {
            "sessionId": session_id,
            "accountId": snapshot.get("accountId", account_id),
            "customerName": snapshot.get("customerName", "ગ્રાહક"),
            "caseType": snapshot.get("primaryIssue", ""),
            "phase": "connecting",
            "callMode": "ai",
            "verified": False,
            "messages": [],
            "lastUserText": "",
            "lastAgentReply": "",
            "snapshot": snapshot,
            "accountFacts": snapshot,
            "toolExecuted": {},
            "proof": {"callLang": "gujarati"},
            "consentRetries": 0,
            "verifyRetries": 0,
        }

        # 1. Greet customer
        state = self.agent.initializeCall(state, db)
        await self.emitState(websocket, send_lock, state, speak=True, use_filler=False)

        # 2. Main interactive conversation loop
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    payload = json.loads(raw)
                except Exception:
                    continue

                msg_type = payload.get("type")
                user_text = ""

                if msg_type == "user":
                    user_text = (payload.get("text") or "").strip()

                elif msg_type == "audio":
                    # Customer sent raw audio chunks/base64
                    b64_audio = payload.get("audioBase64") or payload.get("audio")
                    if b64_audio:
                        audio_bytes = base64.b64decode(b64_audio)
                        user_text = self.stt.transcribe(audio_bytes, language="gujarati")

                if not user_text and msg_type != "ping":
                    continue

                # Record customer turn in transcript
                state["lastUserText"] = user_text
                msgs = list(state.get("messages") or [])
                msgs.append({"role": "user", "speaker": "Customer", "content": user_text})
                state["messages"] = msgs

                # Emit customer message immediately so UI updates
                await self.emitState(websocket, send_lock, state, speak=False)

                # ── T1: Send filler WHILE LLM is thinking ────────────────────
                # The filler is sent concurrently with processTurn to mask inference latency.
                t_llm_start = time.perf_counter()
                llm_task = asyncio.create_task(
                    asyncio.to_thread(self.agent.processTurn, state, db)
                )
                # Fire filler immediately (T3 cache hit → 0ms render time)
                await self._sendFiller(websocket, send_lock)

                # Await LLM result
                state = await llm_task
                llm_ms = (time.perf_counter() - t_llm_start) * 1000

                # Emit agent reply with TTS (filler already played, no second filler needed)
                await self.emitState(websocket, send_lock, state, speak=True, use_filler=False)

                # Sahayak transfer ack first (TTS), then auto-start manager speech
                if state.get("phase") == "handoff_connecting":
                    state = await asyncio.to_thread(self.agent.processTurn, state, db)
                    await self.emitState(websocket, send_lock, state, speak=True, use_filler=False)

                if state.get("callEnded") or state.get("phase") == "end":
                    break

        except Exception:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    async def _sendFiller(
        self,
        websocket: WebSocket,
        send_lock: asyncio.Lock,
    ) -> None:
        """
        T1: Sends a pre-canned empathetic acknowledgment audio chunk immediately.
        Since fillers are pre-warmed in T3 AudioCache, this takes ~0-5ms total.
        The customer hears a natural 'jī, samajyo' while the LLM processes.
        """
        if not (settings.enableTts and self.tts.isConfigured()):
            return

        speaker_id = getSpeakerName("ai")
        phrase = _nextFiller()

        # T3 cache hit → 0ms synthesis
        res = await asyncio.to_thread(self.tts.synthesize, phrase, speaker_id)
        if res:
            audio_b64, audio_mime = res
            filler_payload = {
                "type": "audio",
                "audioBase64": audio_b64,
                "audioMime": audio_mime,
                "audioPart": 1,
                "audioParts": 1,
                "isFiller": True,       # Frontend can optionally style/skip this
                "pauseAfterMs": 0,
            }
            async with send_lock:
                await websocket.send_json(filler_payload)

    async def emitState(
        self,
        websocket: WebSocket,
        send_lock: asyncio.Lock,
        state: dict[str, Any],
        speak: bool = True,
        use_filler: bool = False,  # kept for API compatibility, T1 is now inline in handle()
    ) -> None:
        """Sends JSON state event and streams audio chunks as each sentence is synthesized."""
        speak_text = (state.get("lastAgentReply") or "").strip() if speak else None
        if speak and speak_text:
            state.pop("lastAgentReply", None)
        call_mode = state.get("callMode", "ai")
        speaker_name = state.get("speaker")
        speaker_id = getSpeakerName(call_mode, speaker_name)
        should_speak = bool(speak_text and settings.enableTts and self.tts.isConfigured())

        # 1. Immediate State Emission (TTFT optimized: transcript and state visible instantly)
        payload = {
            "type": "state",
            "phase": state.get("phase"),
            "verified": state.get("verified", False),
            "callMode": call_mode,
            "snapshot": state.get("snapshot"),
            "proof": state.get("proof"),
            "messages": state.get("messages", []),
            "caseRef": (state.get("proof") or {}).get("caseRef"),
            "audioBase64": None,  # Audio is streamed as chunked 'audio' events below
            "audioMime": "audio/mpeg",
            "voice": {
                "speaker": speaker_id,
                "gender": "male" if call_mode == "human" else settings.agentGender,
                "tts": self.tts.isConfigured(),
                "llm": bool(settings.openaiApiKey),
                "langfuse": settings.langfuseEnabled,
                "callLang": "gujarati",
                "ttsPending": should_speak,
                "cacheStats": audioCache.stats(),
            },
        }

        async with send_lock:
            await websocket.send_json(payload)

        # 2. Sentence-level Streaming TTS (TTFA optimized < 800ms)
        # T3: each sentence independently benefits from cache
        if should_speak and speak_text:
            sentences = splitIntoSpokenSentences(speak_text)
            total_parts = len(sentences)
            for idx, sentence in enumerate(sentences):
                res = await asyncio.to_thread(self.tts.synthesize, sentence, speaker_id)
                if res:
                    audio_b64, audio_mime = res
                    chunk_payload = {
                        "type": "audio",
                        "audioBase64": audio_b64,
                        "audioMime": audio_mime,
                        "audioPart": idx + 1,
                        "audioParts": total_parts,
                        "pauseAfterMs": 120 if idx + 1 < total_parts else 0,
                    }
                    async with send_lock:
                        await websocket.send_json(chunk_payload)
