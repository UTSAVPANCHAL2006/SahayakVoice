"""
Langfuse Observability Tracing for Sahayak Voice V2.
Captures end-to-end voice latency milestones (STT, LLM TTFT, TTS TTFA),
token economics, state transitions, and user session telemetry.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

from app.config import settings

logger = logging.getLogger(__name__)

_langfuse = None


def _client():
    """Initializes and returns cached Langfuse client if enabled."""
    global _langfuse
    if not settings.langfuseEnabled:
        return None
    if _langfuse is not None:
        try:
            _ = _langfuse.public_key
            return _langfuse
        except Exception:
            _langfuse = None
    try:
        from langfuse import Langfuse

        _langfuse = Langfuse(
            public_key=settings.langfusePublicKey,
            secret_key=settings.langfuseSecretKey,
            host=settings.langfuseHost,
        )
        return _langfuse
    except Exception as e:
        logger.warning(f"Langfuse init failed: {e}")
        return None


def isEnabled() -> bool:
    """Returns True if Langfuse is configured and available."""
    return settings.langfuseEnabled and _client() is not None


@contextmanager
def traceVoiceTurn(
    session_id: str,
    name: str = "voice_turn",
    metadata: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """
    Context manager to trace a single voice turn with high-resolution latency.
    Records overall turn duration and updates Langfuse observation span.
    """
    bag: dict[str, Any] = {"start_time": time.perf_counter()}
    lf = _client()
    span = None
    if lf:
        try:
            span = lf.start_observation(
                name=name,
                as_type="span",
                input=metadata or {},
                metadata={"session_id": session_id, **(metadata or {})},
            )
        except Exception as e:
            logger.debug(f"Langfuse start_observation failed: {e}")
            span = None

    try:
        yield bag
    finally:
        elapsed_ms = (time.perf_counter() - bag["start_time"]) * 1000
        bag["latency_ms"] = round(elapsed_ms, 1)
        if span:
            try:
                span.update(output={"latency_ms": bag["latency_ms"], **bag.get("output", {})})
                span.end()
            except Exception:
                pass
        if lf and bag.get("flush"):
            try:
                lf.flush()
            except Exception:
                pass


def logLlmGeneration(
    session_id: str,
    name: str,
    model: str,
    input_messages: Any,
    output_response: Any,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Logs an LLM generation observation with prompt payload and structured response."""
    lf = _client()
    if not lf:
        return
    try:
        gen = lf.start_observation(
            name=name,
            as_type="generation",
            model=model,
            input=input_messages,
            output=output_response,
            metadata={"session_id": session_id, **(metadata or {})},
        )
        gen.end()
    except Exception as e:
        logger.debug(f"Langfuse logLlmGeneration failed: {e}")


def logLatencyMilestones(
    session_id: str,
    metrics: dict[str, float],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Logs high-resolution voice latency milestones (STT ms, LLM ms, TTS chunk1 ms, TTFA ms)."""
    lf = _client()
    if not lf:
        return
    try:
        span = lf.start_observation(
            name="voice_latency_waterfall",
            as_type="span",
            input=metrics,
            metadata={"session_id": session_id, **(metadata or {})},
        )
        span.end(output=metrics)
    except Exception as e:
        logger.debug(f"Langfuse logLatencyMilestones failed: {e}")


def logEvalScore(
    name: str,
    value: float,
    comment: str | None = None,
    session_id: str | None = None,
) -> None:
    """Logs evaluation score (0.0 to 1.0) into Langfuse safely."""
    lf = _client()
    if not lf:
        return
    try:
        if hasattr(lf, "score"):
            lf.score(name=name, value=value, comment=comment or "")
    except Exception:
        pass

