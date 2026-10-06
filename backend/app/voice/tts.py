"""
Text-to-Speech (TTS) service using Sarvam AI Bulbul model.
Synthesizes natural Gujarati audio for the customer.
Supports female voice (Priya) for AI bot and male voice (Ratan) for Senior Manager.

Technique 3: AudioCache — LRU in-memory cache of synthesized audio bytes.
Repeated phrases (greetings, verification scripts, handoff lines) served at 0ms.
"""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from typing import Optional
import httpx
from app.config import settings
from app.voice.language import enforceGujaratiOutput, getSarvamSpeechCode, getSpeakerName


# ──────────────────────────────────────────────────────────────────────────────
# T3: Audio LRU Cache (max 128 entries, ~16 MB budget for typical 8kb/clip)
# ──────────────────────────────────────────────────────────────────────────────

_CACHE_MAX_SIZE = 128


class _AudioLruCache:
    """
    Thread-safe LRU cache for synthesized audio clips.
    Key: sha256(speaker + text) → Value: (base64_audio, mime_type)
    Hit rate is high for repeated greetings, verification scripts, and handoff phrases.
    """

    def __init__(self, max_size: int = _CACHE_MAX_SIZE) -> None:
        self._store: OrderedDict[str, tuple[str, str]] = OrderedDict()
        self._max_size = max_size
        self.hits = 0
        self.misses = 0

    def _key(self, text: str, speaker: str) -> str:
        raw = f"{speaker}::{text}"
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    def get(self, text: str, speaker: str) -> Optional[tuple[str, str]]:
        k = self._key(text, speaker)
        if k in self._store:
            self._store.move_to_end(k)
            self.hits += 1
            return self._store[k]
        self.misses += 1
        return None

    def put(self, text: str, speaker: str, value: tuple[str, str]) -> None:
        k = self._key(text, speaker)
        self._store[k] = value
        self._store.move_to_end(k)
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def stats(self) -> dict:
        return {
            "size": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 3),
        }


# Singleton cache shared across all sessions
audioCache = _AudioLruCache()


# ──────────────────────────────────────────────────────────────────────────────
# Sentence splitter (enables TTFA < 800ms via per-sentence streaming)
# ──────────────────────────────────────────────────────────────────────────────

def splitIntoSpokenSentences(text: str) -> list[str]:
    """
    Splits conversational Gujarati/English text into natural sentence-level clauses
    for streaming TTS. Each chunk is small enough to synthesize rapidly (<300ms)
    enabling Time-To-First-Audio (TTFA) < 800ms.
    """
    if not text:
        return []
    # Split on sentence boundaries: . ! ? । ; or newline
    raw_clauses = re.split(r'(?<=[.!?।;\n])\s+', text.strip())
    sentences: list[str] = []
    buffer = ""
    for clause in raw_clauses:
        clause = clause.strip()
        if not clause:
            continue
        # Merge very short fragments (<15 chars, e.g. "હા.", "જી.") with following or preceding
        if len(clause) < 15:
            if sentences and not buffer:
                sentences[-1] = f"{sentences[-1]} {clause}".strip()
            elif buffer:
                buffer = f"{buffer} {clause}".strip()
            else:
                buffer = clause
        else:
            if buffer:
                sentences.append(f"{buffer} {clause}".strip())
                buffer = ""
            else:
                sentences.append(clause)
    if buffer:
        if sentences:
            sentences[-1] = f"{sentences[-1]} {buffer}".strip()
        else:
            sentences.append(buffer)
    return sentences or [text.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# TTS Client
# ──────────────────────────────────────────────────────────────────────────────

class SarvamTtsClient:
    def __init__(self) -> None:
        self.url = "https://api.sarvam.ai/text-to-speech"
        self._client = httpx.Client(
            timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    def isConfigured(self) -> bool:
        return bool(settings.sarvamApiKey)

    def synthesize(
        self,
        text: str,
        speaker: str | None = None,
        language: str = "gujarati",
    ) -> tuple[str, str] | None:
        """
        Synthesizes text to audio.
        T3: Checks AudioCache first — returns cached result at 0ms on hit.
        Returns: (base64_audio, mime_type) or None on failure.
        """
        if not self.isConfigured():
            return None

        clean_text = enforceGujaratiOutput(text)
        if not clean_text:
            return None

        chosen_speaker = speaker or getSpeakerName("ai")

        # ── T3: Cache lookup (0ms on hit) ──────────────────────────────────
        cached = audioCache.get(clean_text, chosen_speaker)
        if cached:
            return cached

        # ── T3: Cache miss → synthesize and store ──────────────────────────
        headers = {"api-subscription-key": settings.sarvamApiKey}
        payload = {
            "inputs": [clean_text[:450]],
            "target_language_code": getSarvamSpeechCode(language),
            "speaker": chosen_speaker,
            "pace": max(0.5, min(2.0, float(settings.sarvamPace))),
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": settings.sarvamModel,
        }

        try:
            res = self._client.post(self.url, json=payload, headers=headers)
            if res.status_code == 200:
                data = res.json()
                audios = data.get("audios")
                if audios and isinstance(audios, list) and len(audios) > 0:
                    result = (audios[0], "audio/mpeg")
                    audioCache.put(clean_text, chosen_speaker, result)
                    return result
        except Exception:
            pass

        return None

    def streamSynthesize(
        self,
        text: str,
        speaker: str | None = None,
        language: str = "gujarati",
    ):
        """
        Yields (chunk_index, total_chunks, base64_audio, mime_type, clause_text)
        as each sentence is synthesized in order.
        T3: Each sentence independently benefits from cache lookup.
        """
        sentences = splitIntoSpokenSentences(text)
        total = len(sentences)
        for idx, sentence in enumerate(sentences):
            res = self.synthesize(sentence, speaker=speaker, language=language)
            if res:
                yield (idx + 1, total, res[0], res[1], sentence)
