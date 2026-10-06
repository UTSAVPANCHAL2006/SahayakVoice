"""
Comprehensive End-to-End Voice AI Latency Suite for Sahayak Voice V2.

Measures the WHOLE voice pipeline latency across every stage:
  1. Audio Input & STT (Speech-to-Text: Sarvam Saaras v3)
  2. Context & Agent Reasoning (OpenAI gpt-4o-mini + Grounding)
  3. Speculative Filler (T1: Pre-cached Gujarati immediate acknowledgment)
  4. Streaming TTS Sentence 1 (Time-to-First-Audio for actual response)
  5. Full Turn Audio Streaming (Complete voice response duration)

Calculates:
  - Perceived TTFA: STT + T1 Filler (What the caller hears immediately)
  - Raw TTFA:       STT + LLM + TTS Chunk 1 (Actual answer first byte)
  - Total Turn Time: STT + LLM + Full TTS (Complete turnaround)
"""

import sys
import time
import base64
import statistics
from pathlib import Path

# Add backend to sys.path
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.tools.banking import getAccountSnapshot
from app.agent.nodes.conversation import handleConversation, needsTools
from app.voice.tts import SarvamTtsClient, splitIntoSpokenSentences, audioCache
from app.voice.stt import SarvamSttClient
from app.config import settings
from app.observability.tracing import isEnabled, traceVoiceTurn, logLatencyMilestones


TEST_QUERIES = [
    # (Account ID, Customer Name, Spoken Gujarati Query)
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "ચેક કેમ બાઉન્સ થયો?"),
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "આ 523 રૂપિયા નો ચાર્જ કેમ લાગ્યો?"),
    ("ACC-LIEN-PRIYA",   "Pratik Sharma",  "મારા ખાતામાં બાકી પૈસા કેટલા વાપરી શકાય?"),
    ("ACC-LIEN-PRIYA",   "Pratik Sharma",  "આ લિયન કોણે લગાવી અને કેમ લગાવી?"),
    ("ACC-HOLD-AMIT",    "Amit Singh",     "યુપીઆઈ ના પૈસા ક્યારે ક્લિયર થશે?"),
    ("ACC-FREEZE-VIKRAM","Vikram Mehta",   "મારું એકાઉન્ટ અનફ્રીઝ કરવા કયા કાગળ આપવા પડશે?"),
    ("ACC-INOP-SUNITA",  "Sunita Rao",     "મારું ખાતું ફરી ચાલુ કેવી રીતે થશે?"),
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "મારે સિનિયર મેનેજર સાથે વાત કરવી છે."),
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "ફરિયાદ નોંધો"),
    ("ACC-LIEN-PRIYA",   "Pratik Sharma",  "મને મારા છેલ્લા વ્યવહારો જણાવો"),
]


def run_whole_pipeline_benchmark():
    tts = SarvamTtsClient()
    stt = SarvamSttClient()

    print("=" * 96)
    print("🎙️   SAHAYAK VOICE V2 — WHOLE PIPELINE VOICE LATENCY BENCHMARK")
    print("=" * 96)
    print(f"  STT Provider   : Sarvam AI Saaras ({settings.sarvamSttModel})")
    print(f"  LLM Provider   : OpenAI ({settings.openaiModel})")
    print(f"  TTS Provider   : Sarvam AI Bulbul ({settings.sarvamModel} @ {settings.sarvamSpeaker})")
    print(f"  Langfuse       : {'enabled ✅' if isEnabled() else 'disabled'}")
    print("=" * 96)

    # 1. Warm-up AudioCache with T1 filler phrases (as done in session.py on call start)
    filler_phrases = ["જી, સમજ્યો.", "જી, હા.", "ઠીક છે.", "એક ક્ષણ.", "જી, ચોક્કસ."]
    print("⚡ [Phase 0] Warming speculative filler audio cache...")
    for phrase in filler_phrases:
        tts.synthesize(phrase, speaker="kavya")
    print(f"   ✓ AudioCache pre-warmed with {len(filler_phrases)} phrases.\n")

    # 2. Pre-generate customer voice audio clips to test real STT
    print("🎧 [Phase 0] Preparing customer audio utterances for STT benchmark...")
    audio_inputs = []
    for _, _, query in TEST_QUERIES:
        res = tts.synthesize(query, speaker="ratan")
        if res:
            audio_inputs.append(base64.b64decode(res[0]))
        else:
            audio_inputs.append(b"")
    print(f"   ✓ Prepared {len(audio_inputs)} authentic Gujarati speech utterances.\n")

    # 3. Warm up OpenAI connection (eliminates TLS/TCP cold-handshake skew from averages)
    print("🔥 [Phase 0] Warming OpenAI connection pool...")
    t_warm = time.perf_counter()
    from app.llm.client import callLlmJson
    callLlmJson("You are a warm-up tester. Reply in JSON.", {"test": "ping"})
    print(f"   ✓ Connection warm in {(time.perf_counter() - t_warm)*1000:.0f}ms.\n")

    results = []

    print("-" * 96)
    print(f"{'#':<3} | {'Query':<24} | {'STT':<8} | {'Filler':<8} | {'LLM':<8} | {'TTS-1':<8} | {'Perceived':<10} | {'Raw TTFA':<9}")
    print("-" * 96)

    for idx, ((account_id, name, query), audio_bytes) in enumerate(zip(TEST_QUERIES, audio_inputs), 1):
        # ── STAGE 1: STT (Audio bytes -> Gujarati text) ─────────────────────
        t_stt = time.perf_counter()
        if audio_bytes and stt.isConfigured():
            recognized_text = stt.transcribe(audio_bytes, filename="user.mp3", language="gujarati")
        else:
            recognized_text = query
        stt_ms = (time.perf_counter() - t_stt) * 1000
        if not recognized_text:
            recognized_text = query

        # ── STAGE 2: T1 Speculative Filler (Immediate acknowledgment) ────────
        t_filler = time.perf_counter()
        filler_phrase = filler_phrases[(idx - 1) % len(filler_phrases)]
        filler_audio = audioCache.get(filler_phrase, "kavya")
        filler_ms = (time.perf_counter() - t_filler) * 1000

        # Perceived TTFA = STT transcription + Filler audio dispatch
        perceived_ttfa = stt_ms + filler_ms

        # ── STAGE 3: Agent Reasoning & LLM (OpenAI gpt-4o-mini) ──────────────
        snap = getAccountSnapshot(account_id)
        state = {
            "sessionId": f"whole-{idx:02d}",
            "accountId": account_id,
            "customerName": name,
            "phase": "conversation",
            "verified": True,
            "snapshot": snap,
            "messages": [],
            "lastUserText": recognized_text,
            "proof": {"callMemory": {}},
        }

        tools_used = needsTools(recognized_text)
        t_llm = time.perf_counter()
        with traceVoiceTurn(f"whole-{idx:02d}", "whole_voice_pipeline") as bag:
            updated = handleConversation(state)
        llm_ms = (time.perf_counter() - t_llm) * 1000
        reply_text = updated.get("lastAgentReply", "")

        # ── STAGE 4: Sentence Splitting (Streaming TTS preparation) ─────────
        sentences = splitIntoSpokenSentences(reply_text)

        # ── STAGE 5: TTS Chunk 1 (First spoken response sentence) ────────────
        tts_chunk1_ms = 0.0
        if sentences and tts.isConfigured():
            t_tts1 = time.perf_counter()
            tts.synthesize(sentences[0], speaker="kavya")
            tts_chunk1_ms = (time.perf_counter() - t_tts1) * 1000

        # ── STAGE 6: Remaining Sentences TTS (Full turn streaming) ───────────
        tts_total_ms = tts_chunk1_ms
        if len(sentences) > 1 and tts.isConfigured():
            for s in sentences[1:]:
                t_s = time.perf_counter()
                tts.synthesize(s, speaker="kavya")
                tts_total_ms += (time.perf_counter() - t_s) * 1000

        # Raw TTFA = Customer stops speaking -> STT + LLM + TTS First Chunk
        raw_ttfa = stt_ms + llm_ms + tts_chunk1_ms

        # Complete Turn = Entire audio completely generated
        complete_turn_ms = stt_ms + llm_ms + tts_total_ms

        row = {
            "idx": idx,
            "query": query,
            "recognized": recognized_text,
            "clauses": len(sentences),
            "stt_ms": round(stt_ms, 1),
            "filler_ms": round(filler_ms, 2),
            "llm_ms": round(llm_ms, 1),
            "tts_chunk1_ms": round(tts_chunk1_ms, 1),
            "tts_total_ms": round(tts_total_ms, 1),
            "perceived_ttfa": round(perceived_ttfa, 1),
            "raw_ttfa": round(raw_ttfa, 1),
            "complete_turn_ms": round(complete_turn_ms, 1),
            "tools_skipped": not tools_used,
        }
        results.append(row)

        print(
            f"{idx:<3} | {query[:22]:<24} | "
            f"{stt_ms:6.0f}ms | {filler_ms:6.2f}ms | {llm_ms:6.0f}ms | {tts_chunk1_ms:6.0f}ms | "
            f"{perceived_ttfa:7.0f}ms  | {raw_ttfa:7.0f}ms"
        )

    print("-" * 96)

    # ── Statistical Percentiles ───────────────────────────────────────────────
    stt_list       = [r["stt_ms"] for r in results]
    filler_list    = [r["filler_ms"] for r in results]
    llm_list       = [r["llm_ms"] for r in results]
    tts1_list      = [r["tts_chunk1_ms"] for r in results]
    perceived_list = [r["perceived_ttfa"] for r in results]
    raw_list       = [r["raw_ttfa"] for r in results]
    complete_list  = [r["complete_turn_ms"] for r in results]

    p50 = lambda l: statistics.median(l)
    p90 = lambda l: sorted(l)[int(len(l) * 0.9) - 1]

    print("\n" + "=" * 96)
    print("📊   WHOLE PIPELINE LATENCY BREAKDOWN (PERCENTILES)")
    print("=" * 96)
    print(f"{'Pipeline Stage':<35} | {'P50 (Median)':<15} | {'P90':<15} | {'Min / Max'}")
    print("-" * 96)
    print(f"1. STT (Sarvam Saaras Speech-to-Text)| {p50(stt_list):8.0f} ms     | {p90(stt_list):8.0f} ms     | {min(stt_list):.0f} / {max(stt_list):.0f} ms")
    print(f"2. T1 Filler (Pre-cached Audio)      | {p50(filler_list):8.2f} ms     | {p90(filler_list):8.2f} ms     | {min(filler_list):.2f} / {max(filler_list):.2f} ms")
    print(f"3. LLM (OpenAI gpt-4o-mini + Agent)  | {p50(llm_list):8.0f} ms     | {p90(llm_list):8.0f} ms     | {min(llm_list):.0f} / {max(llm_list):.0f} ms")
    print(f"4. TTS Chunk 1 (Sentence Streaming)  | {p50(tts1_list):8.0f} ms     | {p90(tts1_list):8.0f} ms     | {min(tts1_list):.0f} / {max(tts1_list):.0f} ms")
    print("=" * 96)
    print(f"⚡  PERCEIVED TTFA (User hears filler) | {p50(perceived_list):8.0f} ms     | {p90(perceived_list):8.0f} ms     | {min(perceived_list):.0f} / {max(perceived_list):.0f} ms  ← REAL CALL LATENCY")
    print(f"⏱️   RAW TTFA (Without filler masking)  | {p50(raw_list):8.0f} ms     | {p90(raw_list):8.0f} ms     | {min(raw_list):.0f} / {max(raw_list):.0f} ms")
    print(f"🏁  COMPLETE TURN (All Audio Streamed) | {p50(complete_list):8.0f} ms     | {p90(complete_list):8.0f} ms     | {min(complete_list):.0f} / {max(complete_list):.0f} ms")
    print("=" * 96)
    print()


if __name__ == "__main__":
    run_whole_pipeline_benchmark()
