"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import {
  endCallSession,
  fetchCallSession,
  fetchCallSupervisorHint,
  getWsUrl,
  isSupervisorPanelEnabled,
  transcribeAudio,
  type CallLang,
  type CallSupervisorHint,
} from "@/lib/api";
import {
  issueFromScenarioId,
  loadPendingCallContext,
  type PendingCallContext,
} from "@/lib/callContext";
import { CaseContextPanel } from "@/components/CaseContextPanel";
import { SupervisorOnlyLast4 } from "@/components/SupervisorOnlyLast4";
import { formatAccountEnding } from "@/lib/format";

type Msg = { role: string; content: string; ts?: string; speaker?: string };

function caseLabel(issue?: string) {
  if (!issue) return "—";
  const map: Record<string, string> = {
    CHEQUE_BOUNCE: "Cheque bounce",
    LIEN: "Lien",
    HOLD: "Payment hold",
    DEBIT_FREEZE: "Debit freeze",
    FREEZE: "Debit freeze",
    INOPERATIVE: "Inoperative",
  };
  return map[issue.toUpperCase()] || issue.replace(/_/g, " ");
}

function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" />
    </svg>
  );
}

function SpeakerIcon({ muted }: { muted: boolean }) {
  if (muted) {
    return (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        <path d="M16.5 12.5L19 10v4l-2.5-2.5zm-9-1.5L7 9H4v6h3l2.5 2.5V11zM3 9v6h2V9H3zm14.59 3.41L21 12l-3.41-3.41L19 7.17 22.83 11 19 14.83l-1.41-1.42z" />
      </svg>
    );
  }
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M3 10v4h4l5 5V5L7 10H3zm13.5 2c0-1.77-1.02-3.29-2.5-4.03v8.06c1.48-.74 2.5-2.26 2.5-4.03zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m22 2-7 20-4-9-9-4 20-7z" />
    </svg>
  );
}

function CallPageInner() {
  const params = useParams();
  const search = useSearchParams();
  const sessionId = params.id as string;
  const urlLang: CallLang = "gujarati";

  const [messages, setMessages] = useState<Msg[]>([]);
  const [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null);
  const [proof, setProof] = useState<Record<string, unknown> | null>(null);
  const [caseRef, setCaseRef] = useState<string | null>(null);
  const [phase, setPhase] = useState("connecting");
  const [verified, setVerified] = useState(false);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const [voiceOn, setVoiceOn] = useState(true);
  const [listening, setListening] = useState(false);
  const [micHint, setMicHint] = useState("");
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [ttsPending, setTtsPending] = useState(false);
  // Progressive text reveal — synced with audio clause streaming
  const [revealedText, setRevealedText] = useState("");
  const [speakingReveal, setSpeakingReveal] = useState(false);
  const pendingFullTextRef = useRef("");
  const revealIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const revealIndexRef = useRef(0);
  const pendingMessagesRef = useRef<Msg[]>([]);
  const [supervisorHint, setSupervisorHint] = useState<CallSupervisorHint | null>(null);
  const [outreach, setOutreach] = useState<PendingCallContext | null>(null);
  const supervisorPanelEnabled = isSupervisorPanelEnabled();
  const [endingCall, setEndingCall] = useState(false);
  const [callStartTime] = useState(() => Date.now());
  const [elapsedSec, setElapsedSec] = useState(0);
  const [voiceWarning, setVoiceWarning] = useState<string | null>(null);

  const [voiceMeta, setVoiceMeta] = useState<{
    speaker?: string;
    gender?: string;
    tts?: boolean;
    llm?: boolean;
    callLang?: CallLang;
    langfuse?: boolean;
  } | null>({ callLang: "gujarati" });

  const callLangRef = useRef<CallLang>("gujarati");
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioQueueRef = useRef<{ base64: string; mime: string; pauseAfterMs: number }[]>([]);
  const audioPlayingRef = useRef(false);
  const voiceOnRef = useRef(voiceOn);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const reconnectRef = useRef(0);
  voiceOnRef.current = voiceOn;

  // Call timer
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - callStartTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [callStartTime]);

  function formatDuration(sec: number) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  // ── Progressive text reveal helpers ───────────────────────────────────
  function startTextReveal(fullText: string, charsPerTick = 1, tickMs = 45) {
    if (revealIntervalRef.current) clearInterval(revealIntervalRef.current);
    pendingFullTextRef.current = fullText;
    revealIndexRef.current = 0;
    setRevealedText("");
    setSpeakingReveal(true);
    revealIntervalRef.current = setInterval(() => {
      revealIndexRef.current = Math.min(
        revealIndexRef.current + charsPerTick,
        pendingFullTextRef.current.length
      );
      setRevealedText(pendingFullTextRef.current.slice(0, revealIndexRef.current));
      if (revealIndexRef.current >= pendingFullTextRef.current.length) {
        if (revealIntervalRef.current) clearInterval(revealIntervalRef.current);
        revealIntervalRef.current = null;
      }
    }, tickMs);
  }

  function accelerateReveal(clauseIdx: number, totalClauses: number) {
    // As each audio clause arrives, jump text reveal forward proportionally
    const full = pendingFullTextRef.current;
    if (!full) return;
    const targetIdx = Math.round(((clauseIdx + 1) / totalClauses) * full.length);
    if (targetIdx > revealIndexRef.current) {
      revealIndexRef.current = targetIdx;
      setRevealedText(full.slice(0, targetIdx));
    }
  }

  function finaliseReveal() {
    if (revealIntervalRef.current) { clearInterval(revealIntervalRef.current); revealIntervalRef.current = null; }
    const full = pendingFullTextRef.current;
    if (!full) return;
    setRevealedText(full);
    // Short pause so the user sees the complete text, then commit to history
    window.setTimeout(() => {
      setSpeakingReveal(false);
      setRevealedText("");
      pendingFullTextRef.current = "";
      setMessages(pendingMessagesRef.current);
    }, 380);
  }

  // ── Audio queue helpers ───────────────────────────────────────────────
  function interruptAgentAudio() {
    audioQueueRef.current = [];
    audioPlayingRef.current = false;
    if (revealIntervalRef.current) { clearInterval(revealIntervalRef.current); revealIntervalRef.current = null; }
    if (audioRef.current) {
      try { audioRef.current.pause(); audioRef.current.currentTime = 0; } catch { /* ignore */ }
      setAgentSpeaking(false);
    }
    finaliseReveal();
  }

  function drainAudioQueue() {
    if (audioPlayingRef.current || !voiceOnRef.current) return;
    const next = audioQueueRef.current.shift();
    if (!next) {
      setAgentSpeaking(false);
      finaliseReveal();
      return;
    }
    audioPlayingRef.current = true;
    setAgentSpeaking(true);
    const src = `data:${next.mime};base64,${next.base64}`;
    const audio = new Audio(src);
    audioRef.current = audio;
    audio.onended = () => {
      audioPlayingRef.current = false;
      const pause = next.pauseAfterMs || 0;
      if (pause > 0) window.setTimeout(() => drainAudioQueue(), pause);
      else drainAudioQueue();
    };
    audio.onerror = () => { audioPlayingRef.current = false; drainAudioQueue(); };
    audio.play().catch((err) => {
      audioPlayingRef.current = false;
      if (err && (err.name === "NotAllowedError" || err.message?.includes("interact"))) {
        // Retain audio in queue and replay on first user gesture
        audioQueueRef.current.unshift(next);
        const unlock = () => {
          window.removeEventListener("click", unlock);
          window.removeEventListener("keydown", unlock);
          window.removeEventListener("touchstart", unlock);
          drainAudioQueue();
        };
        window.addEventListener("click", unlock, { once: true });
        window.addEventListener("keydown", unlock, { once: true });
        window.addEventListener("touchstart", unlock, { once: true });
      } else {
        drainAudioQueue();
      }
    });
  }

  function enqueueAgentAudio(base64: string, mime: string, pauseAfterMs = 0, audioPart?: number, audioParts?: number) {
    setTtsPending(false);
    if (!voiceOnRef.current) return;
    // Sync text reveal with each arriving audio clause
    if (typeof audioPart === "number" && typeof audioParts === "number" && pendingFullTextRef.current) {
      accelerateReveal(audioPart - 1, audioParts);
    }
    audioQueueRef.current.push({ base64, mime, pauseAfterMs });
    drainAudioQueue();
  }

  function setAgentVoice(on: boolean) {
    setVoiceOn(on);
    voiceOnRef.current = on;
    if (!on) interruptAgentAudio();
  }

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) return;
    const initialLang = "gujarati";
    callLangRef.current = initialLang;
    const ws = new WebSocket(`${getWsUrl()}/ws/voice/${sessionId}?lang=${encodeURIComponent(initialLang)}`);
    wsRef.current = ws;
    ws.onopen = () => { setConnected(true); reconnectRef.current = 0; };
    const playAudio = (base64: string, mime: string, pauseAfterMs = 0, audioPart?: number, audioParts?: number) => {
      enqueueAgentAudio(base64, mime, pauseAfterMs, audioPart, audioParts);
    };
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "state") {
        setSnapshot(data.snapshot || null);
        setProof(data.proof || null);
        setCaseRef(data.caseRef || null);
        setPhase(data.phase || "");
        setVerified(!!data.verified);
        if (data.phase === "end") reconnectRef.current = 99;

        const incomingMsgs: Msg[] = data.messages || [];
        if (data.voice) {
          setVoiceMeta(data.voice);
          callLangRef.current = "gujarati";

          const hasAudio = !!(data.audioBase64 || data.voice.ttsPending);
          if (hasAudio) {
            // Audio is playing or streaming — reveal last assistant message progressively in sync with speech
            const lastAgentIdx = [...incomingMsgs].map((m, i) => ({ m, i }))
              .filter(({ m }) => m.role === "assistant").at(-1)?.i ?? -1;
            const msgsWithoutLastAgent = lastAgentIdx >= 0
              ? incomingMsgs.slice(0, lastAgentIdx)
              : incomingMsgs;
            pendingMessagesRef.current = incomingMsgs; // full list committed after audio finishes
            setMessages(msgsWithoutLastAgent);
            const lastAssistantContent = lastAgentIdx >= 0 ? incomingMsgs[lastAgentIdx].content : "";
            if (lastAssistantContent) {
              startTextReveal(lastAssistantContent);
            }
            setTtsPending(false);
          } else {
            setMessages(incomingMsgs);
            setTtsPending(false);
          }
        } else {
          setMessages(incomingMsgs);
        }

        if (data.audioBase64) playAudio(data.audioBase64, data.audioMime || "audio/mpeg", data.pauseAfterMs || 0);
      }
      if (data.type === "voice_warning") {
        setVoiceWarning(data.message || "Sarvam Voice AI credits exhausted. Text conversation remains active.");
      }
      if (data.type === "audio" && data.audioBase64) {
        playAudio(
          data.audioBase64,
          data.audioMime || "audio/mpeg",
          typeof data.pauseAfterMs === "number" ? data.pauseAfterMs : 0,
          data.audioPart,
          data.audioParts,
        );
      }
    };
    ws.onclose = () => {
      setConnected(false);
      const n = reconnectRef.current + 1;
      reconnectRef.current = n;
      if (n <= 5) setTimeout(() => connect(), Math.min(1000 * n, 5000));
    };
  }, [sessionId, urlLang]);

  useEffect(() => {
    connect();
    return () => { reconnectRef.current = 99; wsRef.current?.close(); };
  }, [connect]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, speakingReveal]);

  async function handleEndCall() {
    setEndingCall(true);
    try {
      await endCallSession(sessionId);
      setPhase("end");
    } catch {
      setPhase("end");
    } finally {
      setEndingCall(false);
    }
  }

  function sendText(text: string) {
    const trimmed = text.trim();
    if (!trimmed || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const ts = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    setMessages((prev) => [...prev, { role: "user", content: trimmed, ts }]);
    wsRef.current.send(JSON.stringify({ type: "user", text: trimmed }));
    setInput("");
  }

  function send() { sendText(input); }

  async function toggleListen() {
    if (!connected) { setMicHint("Line not connected yet"); return; }
    if (listening) {
      const rec = recorderRef.current;
      if (rec && rec.state !== "inactive") { try { rec.requestData(); } catch { /* ignore */ } rec.stop(); }
      return;
    }
    interruptAgentAudio();
    const restoreVoiceAfterMic = voiceOnRef.current;
    setAgentVoice(false);
    if (input.trim()) { sendText(input); return; }
    if (!navigator.mediaDevices?.getUserMedia) { setMicHint("Microphone unavailable — type customer reply"); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
      streamRef.current = stream;
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4";
      const ext = mime.includes("mp4") ? "reply.mp4" : "reply.webm";
      const rec = new MediaRecorder(stream, { mimeType: mime });
      chunksRef.current = [];
      rec.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      rec.onstop = async () => {
        setListening(false);
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setAgentVoice(restoreVoiceAfterMic);
        const blob = new Blob(chunksRef.current, { type: mime });
        if (blob.size < 400) { setMicHint("No speech detected — try again"); return; }
        const sttLang = "gujarati";
        setMicHint("Transcribing (ગુજરાતી)…");
        try {
          const text = await transcribeAudio(blob, sttLang, sessionId, ext);
          if (text.trim()) { setMicHint(""); sendText(text); }
          else setMicHint("Could not transcribe — type the reply");
        } catch {
          setMicHint("Speech service error — type the reply");
        }
      };
      recorderRef.current = rec;
      rec.start(200);
      setListening(true);
      setMicHint("● Listening (GU) — speak full sentence, tap mic to send");
    } catch {
      setMicHint("Allow microphone access in the browser");
    }
  }

  const snap = snapshot as {
    ledgerBalanceInr?: number;
    availableBalanceInr?: number;
    holdAmountInr?: number;
    customerName?: string;
    primaryIssue?: string;
    maskedAcct?: string;
    bankName?: string;
    snapshotId?: string;
    extra?: Record<string, unknown>;
    cheque?: Record<string, unknown>;
    lienDetails?: Record<string, unknown>;
    holdDetails?: Record<string, unknown>;
    freezeDetails?: Record<string, unknown>;
    inoperativeDetails?: Record<string, unknown>;
  } | null;

  const effectiveLang = "gujarati";
  const langLabel = "ગુજરાતી";

  useEffect(() => {
    const pending = loadPendingCallContext();
    if (pending?.accountId) setOutreach(pending);
  }, [sessionId]);

  useEffect(() => {
    fetchCallSession(sessionId)
      .then((detail) => {
        setOutreach((prev) => ({
          accountId: detail.accountId || prev?.accountId || "",
          customerName: prev?.customerName,
          maskedAcct: detail.maskedAcct || prev?.maskedAcct,
          primaryIssue:
            prev?.primaryIssue || issueFromScenarioId(detail.scenario),
          callLang: prev?.callLang,
        }));
      })
      .catch(() => {
        /* session may not exist yet */
      });
  }, [sessionId]);

  useEffect(() => {
    if (!supervisorPanelEnabled) return;
    fetchCallSupervisorHint(sessionId).then(setSupervisorHint);
  }, [supervisorPanelEnabled, sessionId, verified, phase]);

  const primaryIssue =
    (snap?.primaryIssue as string) ||
    supervisorHint?.primaryIssue ||
    outreach?.primaryIssue ||
    "";
  const customerName =
    snap?.customerName ||
    supervisorHint?.customerName ||
    outreach?.customerName ||
    "";
  const accountDisplay =
    formatAccountEnding({
      maskedAcct:
        snap?.maskedAcct ||
        supervisorHint?.maskedAcct ||
        outreach?.maskedAcct,
      accountId: outreach?.accountId,
    }) ?? "Not available";

  const voiceStateLabel =
    phase === "end"
      ? "Ended"
      : agentSpeaking
        ? "Speaking"
        : listening
          ? "Listening"
          : ttsPending
            ? "Processing"
            : connected
              ? "Listening"
              : "Connecting";

  const agentStatusClass = agentSpeaking ? "speaking" : listening ? "listening" : "idle";

  return (
    <AppShell>
      <div className="workbench">
        <header className="call-command-bar">
          <div className="call-command-bar__left">
            <Link href="/dashboard" className="call-command-bar__back">← Customer Queue</Link>
            <div className="call-command-bar__title">
              <span className="call-command-bar__product">Sahayak Voice</span>
              <h1>Live call</h1>
            </div>
            <dl className="call-command-bar__session">
              <div>
                <dt>Customer</dt>
                <dd>{customerName || "—"}</dd>
              </div>
              <div>
                <dt>Account</dt>
                <dd className="mono">{accountDisplay}</dd>
              </div>
              <div>
                <dt>Issue</dt>
                <dd>{caseLabel(primaryIssue)}</dd>
              </div>
            </dl>
          </div>
          <div className="call-command-bar__meta">
            <span className="call-command-bar__status-label">Status</span>
            <span className={`call-command-bar__status ${connected ? "is-on" : ""}`}>
              <span className="status-dot" style={{ background: connected ? "var(--ok)" : "#94a3b8" }} />
              {connected ? "Connected" : "Connecting"}
            </span>
            <span>{langLabel}</span>
            <span className="call-command-bar__timer">{formatDuration(elapsedSec)}</span>
          </div>
          <div className="call-command-bar__actions">
            {phase !== "end" && (
              <button
                type="button"
                className="btn-end-call"
                onClick={handleEndCall}
                disabled={endingCall}
                aria-label="End active voice call"
              >
                {endingCall ? "Ending…" : "End call"}
              </button>
            )}
            {caseRef && (
              <Link href={`/cases/${caseRef}`} className="call-command-bar__case-link">
                Case
              </Link>
            )}
          </div>
        </header>

        <div className="workbench-grid">
          <aside className="customer-rail" aria-label="Customer context">
            <div className="rail-section">
              <div className="rail-section__label">Customer</div>
              <div className="rail-section__primary">
                {customerName || "Customer on line"}
              </div>
            </div>
            <hr className="rail-divider" />
            <div className="rail-section">
              <div className="rail-section__label">Account</div>
              <div className="rail-section__mono">{accountDisplay}</div>
            </div>
            <hr className="rail-divider" />
            <div className="rail-section">
              <div className="rail-section__label">Case</div>
              <div className="rail-section__value">{caseLabel(primaryIssue)}</div>
            </div>
            <hr className="rail-divider" />
            <div className="rail-section">
              <div className="rail-section__label">Language</div>
              <div className="rail-section__value">
                Gujarati (ગુજરાતી)
              </div>
            </div>
            <hr className="rail-divider" />
            <div className="rail-section">
              <div className="rail-section__label">Verification</div>
              <div className={`rail-verify ${verified ? "rail-verify--ok" : ""}`}>
                <span className="status-dot" style={{ background: verified ? "var(--ok)" : "var(--warn)" }} />
                {verified ? "Verified" : "Pending"}
              </div>
            </div>
            {!verified && (
              <p className="rail-note">Banking context locked until verification.</p>
            )}

            {supervisorPanelEnabled && (
              <>
                <hr className="rail-divider rail-divider--spaced" />
                <div className="rail-section rail-section--compact">
                  <div className="rail-section__label">Supervisor</div>
                  <div className="rail-section__value">Monitoring</div>
                  {supervisorHint?.expectedLast4 ? (
                    <SupervisorOnlyLast4 digits={supervisorHint.expectedLast4} />
                  ) : (
                    <p className="rail-note">Verification hint available after session sync.</p>
                  )}
                </div>
              </>
            )}
          </aside>

          <section className="transcript-pane" aria-label="Live conversation">
            <div className="transcript-pane__head">
              <h2>Live conversation</h2>
            </div>

            {voiceWarning && (
              <div
                style={{
                  background: "rgba(245, 158, 11, 0.12)",
                  border: "1px solid rgba(245, 158, 11, 0.35)",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  margin: "8px 16px 4px 16px",
                  color: "#fbbf24",
                  fontSize: "12px",
                  lineHeight: "1.4",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "10px",
                }}
                role="alert"
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "15px" }}>⚠️</span>
                  <span>
                    <strong>Voice Notice:</strong> {voiceWarning}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setVoiceWarning(null)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#fbbf24",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "bold",
                    padding: "2px 6px",
                  }}
                  title="Dismiss"
                >
                  ✕
                </button>
              </div>
            )}

            <div className="transcript-scroll" role="log" aria-live="polite">
              {messages.length === 0 && !speakingReveal ? (
                <p className="transcript-empty">
                  {connected ? "Outbound greeting in progress…" : "Connecting voice line…"}
                </p>
              ) : (
                messages.map((m, i) => {
                  const isAgent = m.role !== "user";
                  const speakerLabel = m.speaker || (m.role === "manager" ? "Senior Manager" : isAgent ? "Sahayak" : "Customer");
                  const ts =
                    m.ts ||
                    new Date().toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    });
                  return (
                    <article
                      key={i}
                      className={`call-record__turn call-record__turn--${isAgent ? "agent" : "customer"}`}
                    >
                      <header className="call-record__head">
                        <span className="call-record__speaker">{speakerLabel}</span>
                        <span className="call-record__time">{ts}</span>
                      </header>
                      <p className="call-record__body">{m.content}</p>
                    </article>
                  );
                })
              )}

              {/* ── Live speaking bubble: text types out as audio plays ── */}
              {speakingReveal && (
                <article className="call-record__turn call-record__turn--agent call-record__turn--speaking">
                  <header className="call-record__head">
                    <span className="call-record__speaker">{voiceMeta?.speaker === "ratan" || phase === "handoff" ? "Senior Manager" : "Sahayak"}</span>
                    <span className="call-record__speaking-badge">
                      <span className="speaking-wave">
                        <span /><span /><span /><span /><span />
                      </span>
                      Speaking
                    </span>
                  </header>
                  <p className="call-record__body call-record__body--live">
                    {revealedText}
                    {revealedText.length < pendingFullTextRef.current.length && (
                      <span className="call-record__cursor" aria-hidden />
                    )}
                  </p>
                </article>
              )}

              <div ref={bottomRef} />
            </div>

            {micHint && <p className="mic-hint mic-hint--inline" aria-live="polite">{micHint}</p>}

            <footer className="call-console-footer">
              <div className="call-console-footer__voice" aria-live="polite">
                <span className={`voice-activity-bar__dots voice-activity-bar__dots--${agentStatusClass}`} aria-hidden />
                <span>{voiceStateLabel}</span>
              </div>
              <div className="call-console-footer__controls">
                <button
                  type="button"
                  className={`call-console-footer__labeled ${!voiceOn ? "is-active" : ""}`}
                  title="Mute Sahayak audio"
                  aria-label="Mute"
                  aria-pressed={!voiceOn}
                  onClick={() => setAgentVoice(false)}
                >
                  <SpeakerIcon muted />
                  <span>Mute</span>
                </button>
                <button
                  type="button"
                  className={`call-console-footer__labeled ${voiceOn ? "is-active" : ""}`}
                  title="Speaker on"
                  aria-label="Speaker"
                  aria-pressed={voiceOn}
                  onClick={() => setAgentVoice(true)}
                >
                  <SpeakerIcon muted={false} />
                  <span>Speaker</span>
                </button>
                <button
                  type="button"
                  className={`call-console-footer__labeled ${listening ? "is-active" : ""}`}
                  title={listening ? "Stop recording" : "Record customer voice"}
                  aria-label={listening ? "Stop recording" : "Microphone"}
                  onClick={toggleListen}
                >
                  <MicIcon />
                  <span>{listening ? "Listening" : "Mic"}</span>
                </button>
                <input
                  className="call-console-footer__input"
                  placeholder={
                    !verified
                      ? "Speak or type last 4 digits…"
                      : "Speak or type customer reply…"
                  }
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                  aria-label="Customer reply"
                />
                {input.trim() && (
                  <button type="button" className="call-console-footer__icon" onClick={send} aria-label="Send message">
                    <SendIcon />
                  </button>
                )}
              </div>
            </footer>
          </section>

          <aside className="case-rail-wrap" aria-label="Case context">
            <CaseContextPanel
              primaryIssue={primaryIssue}
              verified={verified}
              snap={snap as Record<string, unknown> | null}
              phase={phase}
              proof={proof}
              outreachAccount={accountDisplay !== "Not available" ? accountDisplay : null}
              outreachCustomer={customerName || null}
            />
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

export default function CallPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <p className="workbench-loading">Connecting outbound line…</p>
        </AppShell>
      }
    >
      <CallPageInner />
    </Suspense>
  );
}
