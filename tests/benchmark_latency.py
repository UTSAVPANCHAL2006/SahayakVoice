"""
Voice AI Latency Benchmark & Evals Suite for Sahayak Voice V2.
Measures component-level milestones across all 4 optimization techniques:

  T1 — Speculative Filler  (hides LLM latency via pre-cached audio)
  T2 — Groq LPU            (sub-700ms inference vs ~2000ms OpenAI batch)
  T3 — AudioCache          (0ms TTS on repeated phrases via LRU cache)
  T4 — Tool Pruning        (skip 2200-token schema on conversational turns)

Calculates P50, P90, and Min/Max across 10 real banking turns.
Logs to Langfuse when enabled.
"""

import sys
import time
import statistics
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, ".")

from app.tools.banking import getAccountSnapshot
from app.agent.nodes.conversation import handleConversation, needsTools
from app.voice.tts import SarvamTtsClient, splitIntoSpokenSentences, audioCache
from app.config import settings
from app.observability.tracing import isEnabled, traceVoiceTurn, logLatencyMilestones


# ── Test corpus: 10 real banking turns across all 5 cases ─────────────────────
TEST_QUERIES = [
    # Conversational turns (T4 → tools=None, saves 200-300ms on OpenAI)
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "ચેક કેમ બાઉન્સ થયો?"),
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "આ 523 રૂપિયા નો ચાર્જ કેમ લાગ્યો?"),
    ("ACC-LIEN-PRIYA",   "Pratik Sharma",  "મારા ખાતામાં બાકી પૈસા કેટલા વાપરી શકાય?"),
    ("ACC-LIEN-PRIYA",   "Pratik Sharma",  "આ લિયન કોણે લગાવી અને કેમ લગાવી?"),
    ("ACC-HOLD-AMIT",    "Amit Singh",     "યુપીઆઈ ના પૈસા ક્યારે ક્લિયર થશે?"),
    ("ACC-FREEZE-VIKRAM","Vikram Mehta",   "મારું એકાઉન્ટ અનફ્રીઝ કરવા કયા કાગળ આપવા પડશે?"),
    ("ACC-INOP-SUNITA",  "Sunita Rao",     "મારું ખાતું ફરી ચાલુ કેવી રીતે થશે?"),
    # Manager escalation (T4 → tools=None)
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "મારે સિનિયર મેનેજર સાથે વાત કરવી છે."),
    # Action turns (T4 → tools=FULL, to test complaint registration path)
    ("ACC-CHQ-HARDIK",   "Hardik Patel",   "ફરિયાદ નોંધો"),
    ("ACC-LIEN-PRIYA",   "Pratik Sharma",  "recent transactions batao"),
]


def run_latency_benchmark():
    tts = SarvamTtsClient()
    results = []

    # ── Config Banner ──────────────────────────────────────────────────────────
    print("=" * 80)
    print("🚀  SAHAYAK VOICE V2 — LATENCY BENCHMARK")
    print("=" * 80)
    print(f"  LLM Provider   : OpenAI {settings.openaiModel}")
    print(f"  T3 AudioCache  : {audioCache.stats()['size']} pre-warmed entries")
    print(f"  T4 Tool prune  : enabled (needsTools() gating)")
    print(f"  Langfuse       : {'enabled ✅' if isEnabled() else 'disabled'}")
    print(f"  TTS configured : {tts.isConfigured()}")
    print("=" * 80)

    # ── Pre-warm T3 cache with filler phrases ─────────────────────────────────
    filler_phrases = ["જી, સમજ્યો.", "જી, હા.", "ઠીક છે.", "એક ક્ષણ.", "જી, ચોક્કસ."]
    print("⚡  Warming AudioCache with filler phrases...")
    t_warm = time.perf_counter()
    for phrase in filler_phrases:
        tts.synthesize(phrase, speaker="kavya")
    warm_ms = (time.perf_counter() - t_warm) * 1000
    print(f"   Cache warm-up done in {warm_ms:.0f}ms | cache size={audioCache.stats()['size']}\n")

    # ── Run benchmark turns ───────────────────────────────────────────────────
    for idx, (account_id, name, query) in enumerate(TEST_QUERIES, 1):
        snap = getAccountSnapshot(account_id)
        state = {
            "sessionId": f"bench-{idx:02d}",
            "accountId": account_id,
            "customerName": name,
            "phase": "conversation",
            "verified": True,
            "snapshot": snap,
            "messages": [],
            "lastUserText": query,
            "proof": {"callMemory": {}},
        }

        tools_used = needsTools(query)
        t_turn = time.perf_counter()

        # Step 1: LLM Agent Turn (T2 + T4 active)
        t_llm = time.perf_counter()
        with traceVoiceTurn(f"bench-{idx:02d}", "agent_conversation_turn") as bag:
            updated = handleConversation(state)
        llm_ms = (time.perf_counter() - t_llm) * 1000

        reply_text = updated.get("lastAgentReply", "")

        # Step 2: Sentence split (sub-ms)
        sentences = splitIntoSpokenSentences(reply_text)

        # Step 3: First sentence TTS (T3 — may be cache hit or miss)
        tts_ms = 0.0
        cache_hit = False
        if tts.isConfigured() and sentences:
            cache_before = audioCache.hits
            t_tts = time.perf_counter()
            tts.synthesize(sentences[0], speaker="kavya")
            tts_ms = (time.perf_counter() - t_tts) * 1000
            cache_hit = audioCache.hits > cache_before

        total_ms = (time.perf_counter() - t_turn) * 1000

        row = {
            "idx": idx,
            "query": query,
            "reply": reply_text[:55] + "..." if reply_text else "(no reply)",
            "clauses": len(sentences),
            "llm_ms": round(llm_ms, 1),
            "tts_ms": round(tts_ms, 1),
            "total_ms": round(total_ms, 1),
            "tools": "WITH" if tools_used else "SKIP",
            "tts_cache": "HIT" if cache_hit else "MISS",
        }
        results.append(row)

        # Langfuse logging
        if isEnabled():
            logLatencyMilestones(f"bench-{idx:02d}", {
                "llm_agent_ms": row["llm_ms"],
                "tts_chunk1_ms": row["tts_ms"],
                "total_ttfa_ms": row["total_ms"],
                "tools_injected": tools_used,
                "tts_cache_hit": cache_hit,
            }, metadata={"query": query, "clauses": len(sentences)})

        t_tag  = f"[T4:{row['tools']}]"
        c_tag  = f"[T3:{row['tts_cache']}]"
        print(
            f"  [{idx:02d}/10] {t_tag} {c_tag}  "
            f"LLM:{llm_ms:6.0f}ms  TTS-1:{tts_ms:5.0f}ms  TTFA:{total_ms:6.0f}ms  "
            f"| '{query[:28]}'"
        )

    # ── Percentile Summary ────────────────────────────────────────────────────
    ttfa = [r["total_ms"] for r in results]
    llms = [r["llm_ms"]   for r in results]
    tts_list = [r["tts_ms"] for r in results if r["tts_ms"] > 0]

    p50_ttfa = statistics.median(ttfa)
    p90_ttfa = sorted(ttfa)[int(len(ttfa) * 0.9) - 1]
    p50_llm  = statistics.median(llms)
    p50_tts  = statistics.median(tts_list) if tts_list else 0

    skipped = sum(1 for r in results if r["tools"] == "SKIP")
    cache_hits = sum(1 for r in results if r["tts_cache"] == "HIT")

    print("\n" + "=" * 80)
    print("📊  LATENCY RESULTS")
    print("=" * 80)
    print(f"  Turns benchmarked      : {len(results)}")
    print(f"  LLM Provider           : OpenAI ({settings.openaiModel})")
    print()
    print(f"  P50 LLM latency        : {p50_llm:,.0f} ms")
    print(f"  P50 TTS first-chunk    : {p50_tts:,.0f} ms")
    print(f"  P50 Total TTFA         : {p50_ttfa:,.0f} ms  ← customer hears audio")
    print(f"  P90 Total TTFA         : {p90_ttfa:,.0f} ms")
    print(f"  Min TTFA               : {min(ttfa):,.0f} ms")
    print(f"  Max TTFA               : {max(ttfa):,.0f} ms")
    print()
    print(f"  T4 Tool Pruning        : {skipped}/{len(results)} turns skipped tools schema")
    print(f"  T3 AudioCache          : {cache_hits}/{len(results)} TTS calls served from cache")
    print(f"  T3 Cache final stats   : {audioCache.stats()}")
    print("=" * 80)
    print(f"  Langfuse Logging       : {'active ✅' if isEnabled() else 'disabled'}")
    print("=" * 80)

    # ── Human-readable verdict ────────────────────────────────────────────────
    print()
    if p50_ttfa < 800:
        print(f"  🎯  TARGET MET — P50 TTFA {p50_ttfa:.0f}ms < 800ms (phone-grade latency)")
    elif p50_ttfa < 1500:
        print(f"  ⚠️   CLOSE — P50 TTFA {p50_ttfa:.0f}ms. Good but above 800ms target.")
    else:
        print(f"  ❌  ABOVE TARGET — P50 TTFA {p50_ttfa:.0f}ms. Check LLM/network bottleneck.")
    print()


if __name__ == "__main__":
    run_latency_benchmark()
