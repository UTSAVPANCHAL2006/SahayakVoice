# Sahayak Voice V2 — Migration & Cleanup Report

## 1. Final V2 Folder Structure

```
v2/
├── frontend/                     # Next.js 15 App Router Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── call/[id]/page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── globals.css
│   │   │   └── workbench.css
│   │   └── lib/
│   │       ├── api.ts
│   │       └── scenarios.ts
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   └── app/
│       ├── main.py               # FastAPI entrypoint (Port 8001)
│       ├── config.py             # Pydantic Settings
│       ├── api/
│       │   ├── routes.py         # HTTP endpoints (/api/health, /api/scenarios, /api/sessions)
│       │   └── websocket.py      # /ws/voice/{sessionId} WebSocket endpoint
│       ├── ws/
│       │   └── session.py        # VoiceSessionHandler for WebSocket streaming & TTS/STT
│       ├── agent/
│       │   ├── graph.py          # LangGraph StateGraph(CallState) & single-turn runner
│       │   ├── state.py          # Unified CallState TypedDict
│       │   ├── memory.py         # Conversational memory tracker
│       │   └── nodes/
│       │       ├── greet.py      # greetCustomer()
│       │       ├── consent.py    # getConsent()
│       │       ├── verify.py     # verifyCustomer()
│       │       ├── fetch.py      # fetchAccount()
│       │       ├── explain.py    # explainIssue()
│       │       ├── conversation.py # handleConversation()
│       │       ├── handoff.py    # handleHandoff() / startHumanConversation()
│       │       └── end.py        # endCall()
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
│       │   └── client.py         # callLlmJson() & callLlmText()
│       ├── tools/
│       │   ├── banking.py        # 5 banking scenarios data & executeBankingTool()
│       │   └── definitions.py    # OpenAI function schemas
│       └── voice/
│           ├── stt.py            # SarvamSttClient
│           ├── tts.py            # SarvamTtsClient
│           └── language.py       # Gujarati language utilities
│
├── tests/
│   ├── test_five_cases_e2e.py    # 5 passed E2E tests for the 5 banking cases
│   ├── test_handoff_manager.py   # 3 passed tests for manager speaks first & closes
│   ├── test_verification.py      # 6 passed tests for Gujarati spoken numbers & digits
│   └── test_tools_and_safety.py  # 5 passed tests for banking tools & security
│
├── README.md
├── CODEBASE_GUIDE.md
└── CLEANUP_REPORT.md
```

---

## 2. V1 Files Changed

**V1 Files Changed: EXACTLY 0.**
Verified via `git status -s`:
Only `?? v2/` is present in the working tree. V1 in `backend/app/` and `frontend/` is 100% frozen, untouched, and intact.

---

## 3. Files Moved / Copied into V2

1. **Frontend**:
   - `frontend/src/*` copied cleanly into `v2/frontend/src/` with identical visuals, layout, styles, and customer rail.
   - Configured `.env.local` to point to port 8001.
   - Added support for `"Senior Manager"` speaker label in the live call transcript.
2. **Backend**:
   - Core domain knowledge and banking scenario facts for all 5 cases cleanly codified in `v2/backend/app/tools/banking.py`.
   - Gujarati speech code, pace, and speaker configuration adapted into `v2/backend/app/voice/`.
   - Sarvam STT & TTS client integration ported into `v2/backend/app/voice/stt.py` and `tts.py`.

---

## 4. Files Removed from V2

- Removed all dead experimental folders outside `v2/`: `backend/app_v2`, `backend/start_v2.sh`, `backend/tests_v2`, `frontend_v2`.
- Removed complex legacy routing hierarchies, duplicate YAML loaders, and transcript-specific regex patches.

---

## 5. Functions Simplified and Renamed

All functions follow beginner-friendly Python naming conventions. **No normal function starts with an underscore `_`**:
- `greetCustomer(state, db)`
- `getConsent(state, db)`
- `verifyCustomer(state, db)`
- `fetchAccount(state, db)`
- `explainIssue(state, db)`
- `handleConversation(state, db)`
- `startHumanConversation(state, db)`
- `handleHumanConversation(state, db)`
- `handleHandoff(state, db)`
- `endCall(state, db)`
- `normalizeText(text)`
- `convertDigitsToAscii(text)`
- `parseIndianSpokenNumber(text)`
- `extractVerificationCandidates(text)`
- `executeBankingTool(tool_name, arguments, snapshot)`
- `getAccountSnapshot(account_id, db)`
- `listScenarioAccounts()`

---

## 6. V1 Behavior Preserved

1. **Deterministic Verification**: Preserved full natural Gujarati number recognition (e.g. `"સાત હજાર બસો ને ચોરાણું"` → `7294`, `"ચાર પાંચ બે એક"` → `4521`, `"૪૫૨૧"` → `4521`).
2. **5 Case Grounded Facts**: Preserved exact canonical amounts, reasons, payee names, and statutory notice references for Cheque Bounce, Lien, Hold, Debit Freeze, and Inoperative Account.
3. **Pure Gujarati Voice & Script**: Customer-facing responses and TTS audio are strictly natural spoken Gujarati.
4. **Fact Safety**: The LLM cannot invent figures or execute arbitrary database queries.

---

## 7. Frontend Changes

1. **V2 Backend Connection**: Configured `v2/frontend/.env.local` to `http://localhost:8001` and `ws://localhost:8001`.
2. **Manager Speaker Support**: Updated `call/[id]/page.tsx` so that when `m.speaker` or `callMode === "human"` is active, the transcript turns and live speaking wave display `"Senior Manager"` with a distinct badge instead of `"Sahayak"`.

---

## 8. Backend Changes

1. **LangGraph StateGraph**: Implemented clean `StateGraph(CallState)` in `v2/backend/app/agent/graph.py` with 8 clear nodes and conditional edges.
2. **Single Workflow for All 5 Cases**: Replaced case-specific code branches with one unified pipeline (`START -> Greet -> Consent -> Verify -> Fetch -> Explain -> Conversation -> Handoff -> End`).
3. **Dedicated Prompt Layer**: 8 separate prompt files in `v2/backend/app/prompts/` keeping prompt engineering modular.

---

## 9. Critical Human Handoff Fix

### Previous Defect in V1 / Early V2:
Customer says: `"મારે મેનેજર સાથે વાત કરવી છે."`  
AI replies: `"હું તમને મેનેજર સાથે જોડું છું."`  
Then customer had to awkwardly speak again (e.g. `"hello"`) before the manager would respond.

### V2 Resolution:
1. When customer requests manager: `handoffRequested = True` is triggered.
2. `startHumanConversation()` is called **in the same turn**.
3. **MANAGER SPEAKS FIRST IMMEDIATELY** with full context:
   `"નમસ્તે Hardikભાઈ! હું વિક્રમ મહેતા બોલું છું, સિનિયર મેનેજર. તમારા ચેક રિટર્ન અંગેનો કૉલ મારી સાથે જોડાયો છે... હું તમારી સંપૂર્ણ સહાય કરીશ. કહો, તમારે શું વિગત જાણવી છે?"`
4. The customer does **NOT** need to say `"hello"`.
5. `callMode` is set to `"human"`. The AI `ConversationNode` stops.
6. Subsequent customer turns are handled directly by `handleHumanConversation()`.
7. Manager resolves the issue and closes the call gracefully when customer is satisfied.

---

## 10. Actual Test Execution & Results

Executed test suite using pytest on Python 3.10 / macOS:
```bash
PYTHONPATH=v2/backend pytest v2/tests -v
```

### Output:
```
v2/tests/test_five_cases_e2e.py::test_full_e2e_flow_for_all_five_cases[scenario0] PASSED [  5%]
v2/tests/test_five_cases_e2e.py::test_full_e2e_flow_for_all_five_cases[scenario1] PASSED [ 10%]
v2/tests/test_five_cases_e2e.py::test_full_e2e_flow_for_all_five_cases[scenario2] PASSED [ 15%]
v2/tests/test_five_cases_e2e.py::test_full_e2e_flow_for_all_five_cases[scenario3] PASSED [ 21%]
v2/tests/test_five_cases_e2e.py::test_full_e2e_flow_for_all_five_cases[scenario4] PASSED [ 26%]
v2/tests/test_handoff_manager.py::test_manager_speaks_first_immediately PASSED [ 31%]
v2/tests/test_handoff_manager.py::test_manager_receives_and_continues_conversation PASSED [ 36%]
v2/tests/test_handoff_manager.py::test_manager_closes_call_naturally PASSED [ 42%]
v2/tests/test_tools_and_safety.py::test_get_balances_tool PASSED         [ 47%]
v2/tests/test_tools_and_safety.py::test_get_cheque_status_tool PASSED    [ 52%]
v2/tests/test_tools_and_safety.py::test_get_freeze_details_tool PASSED   [ 57%]
v2/tests/test_tools_and_safety.py::test_create_service_request PASSED    [ 63%]
v2/tests/test_tools_and_safety.py::test_unknown_tool_safety PASSED       [ 68%]
v2/tests/test_verification.py::test_parse_spoken_gujarati_compound_numbers PASSED [ 73%]
v2/tests/test_verification.py::test_extract_candidates_various_formats PASSED [ 78%]
v2/tests/test_verification.py::test_verify_node_success PASSED           [ 84%]
v2/tests/test_verification.py::test_verify_node_spoken_compound_match PASSED [ 89%]
v2/tests/test_verification.py::test_verify_node_mismatch_and_retry PASSED [ 94%]
v2/tests/test_verification.py::test_verify_node_exceeded_retries PASSED  [100%]

============================== 19 passed in 0.15s ==============================
```

Frontend build:
```bash
npm run build (in v2/frontend)
✓ Compiled successfully in 2.6s
✓ Generating static pages (5/5)
✓ Finalizing page optimization
Exit code: 0
```
