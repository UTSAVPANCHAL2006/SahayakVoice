# Sahayak Voice V2 (સહાયક વોઇસ ૨.૦)

Independent, production-grade Gujarati Voice AI Relationship Manager for Indian Retail Banking.
Built with **LangGraph StateGraph**, **FastAPI**, **Sarvam AI (Saaras + Bulbul v3)**, and **Next.js**.

---

## 🌟 Key Highlights

- **V1 Remains Frozen**: V1 is untouched as a reference; V2 is completely independent in `v2/`.
- **Single Common Workflow for All 5 Cases**:
  1. Cheque Bounce (`CHEQUE_BOUNCE`)
  2. Statutory Lien (`LIEN`)
  3. UPI / Clearing Hold (`HOLD`)
  4. Debit Freeze (`DEBIT_FREEZE`)
  5. Inoperative Account (`INOPERATIVE`)
- **Deterministic Security & Verification**: Natural Gujarati number parsing (compound numbers, digit sequences, and numerals).
- **Critical Human Handoff Fix**:
  - Customer asks for manager → Handoff triggers immediately.
  - **Manager speaks FIRST** with full prior case context (no waiting for customer to say "hello").
  - Mode switches to `callMode = "human"`; AI conversation stops.
  - Manager resolves queries and cleanly closes the call.
- **Pure Gujarati Output**: Output is strictly natural spoken Gujarati.
- **Zero V1 Runtime Dependencies**: Runs entirely from `v2/`.

---

## 📁 Folder Structure

```
v2/
├── frontend/                     # Next.js 15 App Router Frontend (Identical V1 visual design)
│   ├── src/app/
│   │   ├── call/[id]/page.tsx    # Live voice call interface with Manager speaker support
│   │   ├── dashboard/page.tsx    # 5 Banking scenarios queue
│   │   └── globals.css           # Styling
│   └── package.json
│
├── backend/
│   └── app/
│       ├── main.py               # FastAPI server entrypoint (Port 8001)
│       ├── config.py             # Pydantic Settings
│       ├── api/
│       │   ├── routes.py         # REST endpoints (/api/scenarios, /api/health)
│       │   └── websocket.py      # /ws/voice/{sessionId}
│       ├── ws/
│       │   └── session.py        # Real-time WebSocket streaming & TTS/STT
│       ├── agent/
│       │   ├── graph.py          # LangGraph StateGraph & turn dispatcher
│       │   ├── state.py          # Unified CallState TypedDict
│       │   ├── memory.py         # Conversational memory tracker
│       │   └── nodes/
│       │       ├── greet.py      # Call opening & greeting
│       │       ├── consent.py    # Customer consent handler
│       │       ├── verify.py     # Deterministic last-4 verification
│       │       ├── fetch.py      # Authorized account data loader
│       │       ├── explain.py    # Factual issue explanation
│       │       ├── conversation.py # Common LLM-first conversation engine
│       │       ├── handoff.py    # Human escalation (Manager speaks FIRST)
│       │       └── end.py        # Deterministic call termination
│       ├── prompts/
│       │   ├── greet.py
│       │   ├── consent.py
│       │   ├── verify.py
│       │   ├── fetch.py
│       │   ├── explain.py
│       │   ├── conversation.py
│       │   ├── handoff.py
│       │   └── end.py
│       ├── llm/
│       │   └── client.py         # OpenAI-compatible client with offline fallback
│       ├── tools/
│       │   ├── banking.py        # Ground-truth scenario data & tool executor
│       │   └── definitions.py    # OpenAI function schemas
│       └── voice/
│           ├── stt.py            # Sarvam Saaras v3 STT
│           ├── tts.py            # Sarvam Bulbul v3 TTS (Priya & Ratan)
│           └── language.py       # Gujarati language utilities
│
├── tests/
│   ├── test_five_cases_e2e.py    # E2E test for all 5 banking cases
│   ├── test_handoff_manager.py   # Manager speaks first and handoff tests
│   ├── test_verification.py      # Gujarati spoken numbers & verification tests
│   └── test_tools_and_safety.py  # Banking tools & fact safety tests
│
├── README.md
├── CODEBASE_GUIDE.md
└── CLEANUP_REPORT.md
```

---

## 🚀 How to Run

### 1. Run Backend (Port 8001)
```bash
cd v2/backend
PYTHONPATH=. uvicorn app.main:app --port 8001 --reload
```

### 2. Run Frontend
```bash
cd v2/frontend
npm run dev
```
Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard) to launch any of the 5 banking call scenarios.

### 3. Run Tests
```bash
PYTHONPATH=v2/backend pytest v2/tests -v
```
