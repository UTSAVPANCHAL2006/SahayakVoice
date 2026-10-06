"""
LLM Client for Sahayak Voice V2.
Uses OpenAI gpt-4o-mini with streaming JSON mode and tool calling.
Includes automatic IPv4 socket resolution (bypasses macOS 9s IPv6 blackhole on Indian ISPs).
All callers use the same callLlmJson / callLlmText interface.
"""

from __future__ import annotations

import json
import re
import socket
import time
from typing import Any, Callable
from app.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# Network Optimization: Force IPv4 resolution on macOS
# Prevents ~9-second TCP hang where macOS waits for broken IPv6 before IPv4 fallback
# ──────────────────────────────────────────────────────────────────────────────
_orig_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4(host: Any, port: Any, family: int = 0, type: int = 0, proto: int = 0, flags: int = 0) -> Any:
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _getaddrinfo_ipv4

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Client singleton (lazy-init, connection-pooled)
# ──────────────────────────────────────────────────────────────────────────────

_openai_client = None


def _getOpenAiClient() -> Any:
    """Returns cached OpenAI client with persistent connection pool."""
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    if OpenAI and settings.openaiApiKey:
        _openai_client = OpenAI(
            api_key=settings.openaiApiKey,
            max_retries=2,
            timeout=15.0,
        )
        return _openai_client
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def callLlmJson(
    system_prompt: str,
    user_payload: dict[str, Any],
    tools: list[dict] | None = None,
    temperature: float = 0.3,
    on_sentence: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """
    Calls OpenAI LLM with streaming JSON mode and returns structured dict.
    Streaming cuts Time-To-First-Token (TTFT) from 10s down to <1s.
    Optional on_sentence callback receives spoken Gujarati sentences as they stream.
    Returns: {"reply": "...", "tools_to_call": [...], "wants_manager": bool, "wants_end": bool}
    """
    t_start = time.perf_counter()
    user_text = json.dumps(user_payload, ensure_ascii=False)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    openai_client = _getOpenAiClient()
    if not openai_client:
        return {}

    try:
        kwargs: dict[str, Any] = {
            "model": settings.openaiModel,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "max_tokens": 180,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        stream = openai_client.chat.completions.create(**kwargs)

        content_parts: list[str] = []
        tools_dict: dict[int, dict[str, str]] = {}
        ttft_ms: float | None = None

        # Sentence streaming tracking
        stream_buffer = ""
        emitted_sentences: set[str] = set()

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - t_start) * 1000
                content_parts.append(delta.content)
                stream_buffer += delta.content

                # If callback requested, detect sentence boundary in "reply"
                if on_sentence and '"reply"' in stream_buffer:
                    match = re.search(r'\"reply\"\s*:\s*\"([^\"\n]+?[.!?।])', stream_buffer)
                    if match:
                        sentence = match.group(1).strip()
                        if sentence and sentence not in emitted_sentences:
                            emitted_sentences.add(sentence)
                            try:
                                on_sentence(sentence)
                            except Exception:
                                pass

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tools_dict:
                        tools_dict[idx] = {
                            "name": tc.function.name if tc.function and tc.function.name else "",
                            "arguments": tc.function.arguments if tc.function and tc.function.arguments else "",
                        }
                    else:
                        if tc.function and tc.function.name:
                            tools_dict[idx]["name"] += tc.function.name
                        if tc.function and tc.function.arguments:
                            tools_dict[idx]["arguments"] += tc.function.arguments

        full_content = "".join(content_parts).strip()
        parsed: dict[str, Any] = {}
        if full_content:
            try:
                parsed = json.loads(full_content)
            except Exception:
                # If json has trailing text, attempt clean extraction
                m = re.search(r"\{.*\}", full_content, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))

        # Reassemble streamed tool calls if present
        tools_to_call: list[dict[str, Any]] = []
        for idx in sorted(tools_dict.keys()):
            item = tools_dict[idx]
            try:
                args = json.loads(item.get("arguments") or "{}")
            except Exception:
                args = {}
            tools_to_call.append({
                "name": item.get("name", ""),
                "arguments": args,
            })

        if tools_to_call:
            parsed["tools_to_call"] = tools_to_call

        llm_ms = (time.perf_counter() - t_start) * 1000
        _logLlmCall(
            "openai",
            settings.openaiModel,
            messages,
            parsed,
            llm_ms,
            user_payload,
            ttft_ms=ttft_ms or llm_ms,
        )
        return parsed

    except Exception:
        return {}


def callLlmText(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.4,
) -> str:
    """
    Plain-text LLM completion using OpenAI streaming.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    openai_client = _getOpenAiClient()
    if not openai_client:
        return ""

    try:
        stream = openai_client.chat.completions.create(
            model=settings.openaiModel,
            messages=messages,
            temperature=temperature,
            max_tokens=250,
            stream=True,
        )
        parts = []
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                parts.append(chunk.choices[0].delta.content)
        return "".join(parts).strip()
    except Exception:
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Internal: Langfuse instrumentation
# ──────────────────────────────────────────────────────────────────────────────

def _logLlmCall(
    provider: str,
    model: str,
    messages: list,
    output: dict,
    latency_ms: float,
    user_payload: dict,
    ttft_ms: float | None = None,
) -> None:
    """Fire-and-forget Langfuse logging with latency and TTFT metrics."""
    try:
        from app.observability.tracing import isEnabled, logLlmGeneration
        if isEnabled():
            meta: dict[str, Any] = {
                "total_latency_ms": round(latency_ms, 1),
            }
            if ttft_ms is not None:
                meta["ttft_ms"] = round(ttft_ms, 1)

            logLlmGeneration(
                session_id=str(user_payload.get("CUSTOMER_NAME", "session")),
                name=f"llm_{provider}_streaming",
                model=f"{provider}/{model}",
                input_messages=messages,
                output_response={**output, "_metrics": meta},
                metadata=meta,
            )
    except Exception:
        pass
