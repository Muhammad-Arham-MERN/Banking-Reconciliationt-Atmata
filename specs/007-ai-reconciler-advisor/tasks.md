---
description: "Actionable task breakdown for the AI Reconciler Advisor feature (007)"
---

# Tasks: AI Reconciler Advisor ("Subh al Baqaya")

**Feature**: `007-ai-reconciler-advisor` | **Branch**: `007-ai-reconciler-advisor`
**Input**: Design documents from `specs/007-ai-reconciler-advisor/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)
**User stories**: US1 (P1) — Suggest & manually reconcile potential discrepancies; US2 (P2) — Ask the agent anything about the reconciliation
**Tests**: Required — `quickstart.md` and the spec's Independent Tests define concrete pytest scenarios; spec mandates an existing `backend/tests/` unit-test convention.

## Format

`- [ ] [ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (`[US1]`, `[US2]`); Setup, Foundational, and Polish phases carry no story label
- Tests for a story MUST be written first and FAIL before that story's implementation
- **Constitution (G7, mandatory on EVERY created/edited file)**: `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` header, `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` footer, `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٍ` inline crux marker on the core suggestion/reconciliation logic

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment configuration so backend and frontend tasks can run

- [x] T001 Verify `AI_MODEL` / `AI_API_KEY` (Gemini family, same as existing AI flows) and `DATABASE_URL` are present in `backend/.env` (needed by `backend/src/services/advisor_service.py` and existing flows)
- [x] T002 [P] Verify Python >=3.13 and `openai-agents[litellm]` is installed/resolvable in `backend/requirements.prod.txt` (needed by `advisor_service.py`; do NOT add a new dependency)
- [x] T003 [P] Verify the frontend can run `next dev` with `frontend/package.json` dependencies present (shadcn/ui base-nova, `@base-ui/react`, Tailwind v4) — no new frontend dependencies allowed

**Checkpoint**: Environment confirmed; no code changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend capability the advisor depends on — stable per-discrepancy keys and cumulative Bank/Company balance. **⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [x] T004 [P] Assign a stable backend-generated `discrepancy_id` (`"<source>:<n>"`, e.g. `Bank:1`, `Company:1`) over the assembled `final_discrepancies` in `backend/src/services/reconciliation_service.py` (at the `final_discrepancies = bank_discrepancies + company_discrepancies` point, ~line 63); carry it on each discrepancy dict (matches the unused `TransactionDiscrepancy.discrepancy_id` field in `backend/src/models/api_models.py`). Deterministic for the same inputs; never rendered in the UI. Mark the key-assignment crux inline with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`.
- [x] T005 [P] Compute the cumulative Bank/Company balance context over `final_discrepancies` in `backend/src/services/reconciliation_service.py`: one `BalancePoint` per item (in list order) with `index` (1-based), `discrepancy_id`, `bank_running`, `company_running`, `net` (`bank_running + company_running`), each item's signed `Debit/Credit` added to its own `FROM` bucket only; plus final `bank_balance` / `company_balance` summary totals. Mark the totals crux inline.
- [x] T006 [P] Confirm the existing `processing_cancellation` registry and 499/`asyncio.CancelledError` pattern in `backend/src/services/processing_cancellation.py` and `backend/src/api/ai_routes.py` is reusable for the advisor (no changes unless reuse requires it)
- [x] T007 [P] Confirm `AUTH_EXEMPT_PREFIXES` in `backend/src/api/auth_middleware.py` does NOT include `/advisor` (FR-001 — the advisor requires Bearer auth, unlike `/karwai`)

**Checkpoint**: `ReconciliationService.reconcile()` returns discrepancies carrying `discrepancy_id` + a balance context; advisor paths are auth-required.

---

## Phase 3: User Story 1 — Suggest and manually reconcile potential discrepancies (Priority: P1) 🎯 MVP

**Goal**: A "Reconcile With Agent" button sends the complete final discrepancies list + cumulative balance context to a no-tools agent that returns typed suggestions for broken cheques/pairs and reversals, rendered in a dedicated panel with a reason tooltip and a per-suggestion Reconcile button that removes exactly the suggested items frontend-only.

**Independent Test**: Run a reconciliation ending with the broken-cheque scenario (Bank +79,000 and +100,000 vs Company +179,000), click "Reconcile With Agent", verify the agent receives the discrepancy details + cumulative totals/balance context and returns that group as a suggestion with a reason, then click Reconcile and verify exactly those three items disappear from the live list while all others remain.

### Tests for User Story 1 ⚠️ (SKIPPED — user explicitly requested no tests be written)

- [x] T008 [P] [US1] Test broken-cheque suggestion in `backend/tests/test_advisor.py` — **SKIPPED per user instruction ("dont write any tests")**
- [x] T009 [P] [US1] Test reversal suggestion in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T010 [P] [US1] Test no-suggestion empty state in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T011 [P] [US1] Test exact-item removal mapping in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T012 [P] [US1] Test agent never alters in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T013 [P] [US1] Test 3-retry → friendly error in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T014 [P] [US1] Test cancellation → 499 in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**

### Implementation for User Story 1

- [x] T015 [P] [US1] Create the advisor pydantic v2 models in `backend/src/models/advisor_models.py` per `data-model.md` §6: `AdvisorReconcileRequest`, `AdvisorDiscrepancy`, `BalanceContext`, `BalancePoint`, `AdvisorSuggestion`, `AdvisorSuggestionItem`, `AdvisorResponse`, `ChatMessage`
- [x] T016 [US1] Implement the Reconciler Agent in `backend/src/services/advisor_service.py`: build the chat model from `settings.AI_MODEL`/`AI_API_KEY` via a `_build_model()` helper exactly like `backend/src/services/ai_structure_detector.py`; Agent with NO tools; strict two-case system instructions (broken cheque/pair, reversal — FR-003; signed amounts primary, dates/descriptions/balance secondary — FR-004; concise-response rule — FR-008b; latest context authoritative — FR-008a); structured output into the pydantic models; unified 3-attempt retry for malformed/empty output AND transport/model errors (FR-006). Mark the suggestion logic crux inline with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`.
- [x] T017 [US1] Implement streaming + cancellation in `backend/src/services/advisor_service.py`: `Runner.run_streamed` for token-by-token output; reuse the `processing_cancellation` registry (`register_run`/`is_cancelled`/`cancel_run`); catch `asyncio.CancelledError` explicitly and honor the 499 JSON (FR-008c)
- [x] T018 [US1] Implement `POST /advisor/reconcile` in `backend/src/api/advisor_routes.py` (request: `request_id` + full discrepancies + balance context + history + optional `question`; response streams suggestions + `chat_message`; 401/422/499/503 per `contracts/advisor-openapi.yaml`)
- [x] T019 [US1] Implement `POST /advisor/{request_id}/cancel` in `backend/src/api/advisor_routes.py` (acknowledges cancellation via the registry, per the contract)
- [x] T020 [US1] Mount `advisor_router` in `backend/src/main.py` (`app.include_router(advisor_router)` alongside `api_router`/`ai_router`/`cloud_router`, ~line 171); do NOT add `/advisor` to `AUTH_EXEMPT_PREFIXES` in `backend/src/api/auth_middleware.py`
- [x] T021 [P] [US1] Create the fetch client in `frontend/src/lib/api/advisorClient.ts` (plain-`fetch` singleton like `frontend/src/lib/api/aiReconciliationClient.ts`/`cloudHistoryClient.ts`; Bearer `access_token`; streaming consumption; maps the typed response)
- [x] T022 [P] [US1] Add the shadcn tooltip component in `frontend/src/components/ui/tooltip.tsx` (none exists today)
- [x] T023 [US1] Create `frontend/src/components/advisor/AdvisorPanel.tsx`: visually distinct card headed "Agent Suggestions"; each suggestion renders rows (Date, Details, signed Amount, Source) grouped under Company/Bank headers with the agent's reason; per-suggestion reason tooltip (T022) + **Reconcile** button; empty state when no suggestions; displays the agent's `chat_message` (FR-009/FR-010)
- [x] T024 [US1] Wire the "Reconcile With Agent" button and the suggestion-reconcile callback into `frontend/src/components/results/ReconciliationResults.tsx` (~line 102): the callback filters `discrepancies` by the suggested `keys` via `prev.filter(...)`, mirroring the existing `handleReconcile`, so the live list, manual reconcile, and "Complete Reconciliation" save stay in sync (FR-010); resolve keys against the live list, skip+inform on stale suggestions; disable/hide the button when zero discrepancies; reset all advisor state on new reconciliation (FR-013)

**Checkpoint**: US1 fully functional — agent suggestions render, Reconcile removes exactly the suggested items, the live list + save stay in sync, and the panel handles empty/stale/failed/cancelled states.

---

## Phase 4: User Story 2 — Ask the agent anything about the reconciliation (Priority: P2)

**Goal**: After suggestions are presented, the user keeps conversing in a stateless streaming chat; follow-ups re-send the CURRENT live discrepancies + history keyed by `request_id` (FR-008a).

**Independent Test**: Load a reconciliation with suggestions, send a follow-up question ("why are these three linked?"), and verify the agent answers in context of the same discrepancies without altering the suggestions or the discrepancies list.

### Tests for User Story 2 ⚠️ (SKIPPED — user explicitly requested no tests be written)

- [x] T025 [P] [US2] Test stateless chat re-send in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T026 [P] [US2] Test no-removal on follow-up in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**
- [x] T027 [P] [US2] Test out-of-scope question handling in `backend/tests/test_advisor.py` — **SKIPPED per user instruction**

### Implementation for User Story 2

- [x] T028 [US2] Extend `backend/src/services/advisor_service.py` to accept the optional `question` + `history` and fold them into the agent turn (suggestions may additionally be returned); keep the request stateless — every call re-sends the current context + history (FR-008a)
- [x] T029 [US2] Create `frontend/src/components/advisor/AdvisorChat.tsx`: stateless streaming chat (messages list; follow-ups re-send the current live discrepancies + history via `advisorClient.ts`); cancel button for a running stream; resets on new reconciliation (FR-013)
- [x] T030 [US2] Integrate `AdvisorChat.tsx` into `AdvisorPanel.tsx` / `ReconciliationResults.tsx` so chat state (messages) and suggestions live together and reset together

**Checkpoint**: US1 AND US2 both work independently — chat follows up in context, never alters the list, and resets on new reconciliation.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Full-flow validation and non-functional requirements

- [x] T031 [P] Run the full backend test suite (`backend/tests/`, including new `test_advisor.py`) to confirm existing reconciliation/AI flows are unchanged (SC-006) — **test_advisor.py not written (user requested no tests); backend import + reconcile/advisor unit checks passed, existing tests untouched**
- [x] T032 [P] Run the frontend production build (`npm run build` in `frontend/`) to confirm no type/build regressions
- [ ] T033 Verify performance on a 400+ item / 100+ discrepancy file: suggestions panel renders without degradation (SC-004)
- [ ] T034 Verify SC-001/SC-002/SC-007 manually via `specs/007-ai-reconciler-advisor/quickstart.md`: run the agent on a reconciliation containing both cases (≥1 correct suggestion per case; every user-approved Reconcile removes exactly the suggested items; no suggestion's sums break the running Bank/Company totals)
- [ ] T035 Confirm the "Reconcile With Agent" button is disabled/hidden at zero discrepancies and agent state resets on a fresh page load (FR-013)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (the endpoint contract needs `discrepancy_id` + balance context)
- **User Stories (Phase 3+)**: Depend on Foundational; US1 then US2 (US2's chat integrates with the US1 panel)
- **Polish (Final Phase)**: Depends on both user stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational — no dependency on US2
- **User Story 2 (P2)**: Starts after Foundational — integrates with US1's panel/state, independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation (T008–T014 → T015+; T025–T027 → T028+)
- Models → Service → Routes → Frontend client → UI components → Integration

### Parallel Opportunities

- T001/T002/T003 (Setup), T004/T005/T006/T007 (Foundational) — all `[P]`
- T008–T014 (US1 tests) — all `[P]`, one file but independent test cases; T015 and T021/T022 are `[P]` (backend models vs frontend client/tooltip)
- T021 and T022 are `[P]` (different files) — can start as soon as the request/response contract is clear, even before T016–T020 land
- T025–T027 (US2 tests) — all `[P]`
- T031/T032 (Polish) — `[P]` in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (must FAIL first):
Task: "Test broken-cheque suggestion in backend/tests/test_advisor.py"
Task: "Test reversal suggestion in backend/tests/test_advisor.py"
Task: "Test no-suggestion empty state in backend/tests/test_advisor.py"
Task: "Test exact-item removal mapping in backend/tests/test_advisor.py"
Task: "Test agent never alters in backend/tests/test_advisor.py"
Task: "Test 3-retry -> friendly error in backend/tests/test_advisor.py"
Task: "Test cancellation -> 499 in backend/tests/test_advisor.py"

# Backend models + frontend client + tooltip in parallel (different files):
Task: "Create advisor pydantic models in backend/src/models/advisor_models.py"
Task: "Create advisor fetch client in frontend/src/lib/api/advisorClient.ts"
Task: "Add shadcn tooltip in frontend/src/components/ui/tooltip.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch all US2 tests together (must FAIL first):
Task: "Test stateless chat re-send in backend/tests/test_advisor.py"
Task: "Test no-removal on follow-up in backend/tests/test_advisor.py"
Task: "Test out-of-scope question handling in backend/tests/test_advisor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the US1 independent test (broken-cheque scenario end-to-end)
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready (keys + balance context + auth posture)
2. User Story 1 → suggestions + Reconcile panel → Test independently → Deploy/Demo (MVP)
3. User Story 2 → stateless streaming chat → Test independently → Deploy/Demo
4. Polish → full validation (SC-001…SC-007, build + test suite)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend: models → service → routes; frontend: client → panel → wire-up)
   - Developer B: User Story 2 (extends the service + builds AdvisorChat)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps a task to its user story for traceability
- Every file created/edited carries the constitution prayer bookends (G7); crux markers on `advisor_service.py` and the `reconciliation_service.py` key/totals logic
- Commit after each task or logical group; run `git status` between phases
- Tests in `backend/tests/test_advisor.py` map to the scenarios in `specs/007-ai-reconciler-advisor/quickstart.md`
- "What we Removed" visibility is out of scope — do not implement
