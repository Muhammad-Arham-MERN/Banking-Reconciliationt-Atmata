---

description: "Task list for AI-Based Data Extraction (Istikhraj e Data Ma'a AI) implementation"
---

# Tasks: AI-Based Data Extraction (Istikhraj e Data Ma'a AI)

**Input**: Design documents from `/specs/005-ai-data-extraction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Backend test tasks are included — this repo has an established `pytest` suite under `backend/tests/`, and the plan specifies new test files. Tests are written to FAIL before implementation (TDD), per the repo's testing conventions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` (per plan.md structure)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the AI flow

- [X] T001 Add `openai-agents[litellm]` dependency to backend/requirements.txt
- [X] T002 [P] Add `AI_MODEL` and `AI_API_KEY` settings to backend/src/config.py (pydantic-settings, env-var driven)
- [X] T003 [P] Add `AI_MODEL` and `AI_API_KEY` placeholders to backend/.env.example
- [X] T004 Create `backend/src/services/ai_structure_detector.py` module scaffold (empty service with constitution header/footer)
- [X] T005 [P] Create `backend/src/api/ai_routes.py` module scaffold (empty router with constitution header/footer)
- [X] T006 Create frontend route scaffold `frontend/src/app/upload-ai/page.tsx` (auth-guarded like `frontend/src/app/upload/page.tsx`, empty shell)

**Checkpoint**: Project structure ready for foundational work

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement `parse_output_block` extractor + `FileStructureOutput` pydantic model in backend/src/services/ai_structure_detector.py (port from test.py, lines 31-90)
- [X] T008 [P] Port `extract_pdf` dynamic slicer into `backend/src/services/ai_pdf_processor.py` (port from test_results.py, lines 30-111: `_slice_words_to_columns` + `extract_pdf`)
- [X] T009 Register the AI router in backend/src/main.py (`app.include_router(ai_router)`) so the endpoint is reachable
- [-] T010 [P] Create `backend/tests/test_ai_structure_detector.py` with parsing/validation tests for `parse_output_block` (SKIPPED per developer: no test files)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Hands-free reconciliation with automatic structure detection (Priority: P1) 🎯 MVP

**Goal**: User uploads any-bank PDF + Excel ledger, selects past history, submits with no column/format input; system auto-detects both file structures, extracts transactions, runs reconciliation, shows discrepancies, allows save.

**Independent Test**: Upload a PDF from a bank other than the currently supported one + Excel ledger, submit with no column information, verify transactions are extracted correctly and discrepancies are produced and saved.

### Tests for User Story 1 ⚠️

> **NOTE: All US1 test tasks SKIPPED per developer instruction (no test files).**

- [-] T011 [P] [US1] Unit test for `read_excel` tool in backend/tests/test_ai_structure_detector.py (SKIPPED)
- [-] T012 [P] [US1] Unit test for `read_pdf` / `read_pdf_words` tools in backend/tests/test_ai_structure_detector.py (SKIPPED)
- [-] T013 [P] [US1] Unit test for `extract_pdf` slicing in backend/tests/test_ai_pdf_processor.py (SKIPPED)
- [-] T014 [P] [US1] Integration test for `/reconcile-ai` full success in backend/tests/test_ai_routes.py (SKIPPED)

### Implementation for User Story 1

- [X] T015 [US1] Implement the 3 agent tools (`read_excel`, `read_pdf`, `read_pdf_words`) as path-bound closures in backend/src/services/ai_structure_detector.py (port from test.py lines 94-164; paths parameterized to uploaded files, NOT hardcoded assets_dev)
- [X] T016 [US1] Implement the agent (OpenAI Agents SDK `Agent` + `LitellmModel(AI_MODEL, AI_API_KEY)`) + agent instructions contract in backend/src/services/ai_structure_detector.py (port from test.py lines 167-230; env-var model/key per FR-010)
- [X] T017 [US1] Implement `detect_structure(pdf_path, excel_path)` with per-side detection (PDF + Excel) in backend/src/services/ai_structure_detector.py — returns parsed `FileStructureOutput`
- [X] T018 [US1] Implement `ai_pdf_processor.py` pipeline: `extract_bank_statement` (dynamic `extract_pdf` + detect-verify) + transform via `standardize_transaction_data`/`normalize_pdf_date`/`clean_transaction_detail` → same result shape as `PDFProcessor.process_pdf` (bank_statement, bank_net_total, processing_metadata)
- [X] T019 [US1] Implement `ai_excel_processor.py` (NEW file): derive `format_type` (debit-plus-credit vs debit-pipe-credit) + sheet from detected columns, delegate to existing `ExcelProcessor.process_excel` → same result shape (company_records, company_net_total, processing_metadata)
- [X] T020 [US1] Implement `POST /reconcile-ai` in backend/src/api/ai_routes.py: multipart (bankStatement, companyData, historyName optional), reuse `save_upload_file`/`validate_upload_file`/`cleanup_uploaded_files`, `asyncio.gather` parallel extraction (FR-019), `ReconciliationService.reconcile` (FR-007), optional `HistoryService.load_history` (FR-013), response per contracts/api-contract.md with ai_metadata
- [X] T021 [US1] Implement frontend `UploadAIConfig` component in frontend/src/components/upload/UploadAIConfig.tsx: PDF + Excel dropzones, past-history selector, submit (NO column-name fields, NO format selector per FR-001)
- [X] T022 [US1] Implement frontend API call `reconcileAi` in frontend/src/lib/api/aiReconciliationClient.ts (fetch multipart POST /reconcile-ai)
- [X] T023 [US1] Wire results view: discrepancies display + manual reconciliation + save (reuse existing ReconciliationResults component) in frontend/src/app/upload-ai/page.tsx (FR-013)
- [-] T024 [US1] Add frontend test frontend/tests/upload-ai.test.tsx (SKIPPED per developer: no test files)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graceful handling of failed extraction (Priority: P2)

**Goal**: Detection failures retry up to 3 times; after exhaustion user sees a clear friendly retry message; no partial or corrupted results; one-file partial success shows successful side + clear message.

**Independent Test**: Submit a file while the model is unavailable (invalid credentials configured) and verify the user receives a clear retry message after retries are exhausted, with no partial results presented.

### Tests for User Story 2 ⚠️

> **NOTE: All US2 test tasks SKIPPED per developer instruction (no test files).**

- [-] T025 [P] [US2] Unit test for retry orchestration (SKIPPED)
- [-] T026 [P] [US2] Unit test for retry exhaustion (SKIPPED)
- [-] T027 [P] [US2] Integration test for `/reconcile-ai` 422 ai_detection_failed (SKIPPED)
- [-] T028 [P] [US2] Integration test for `/reconcile-ai` partial_success (SKIPPED)

### Implementation for User Story 2

- [X] T029 [US2] Implement `detect_structure` retry loop (max 3 attempts; catch parse/validation/provider errors; track retries_used) in backend/src/services/ai_structure_detector.py (FR-008)
- [X] T030 [US2] Define `AIDetectionError` exception + friendly retry message in backend/src/services/ai_structure_detector.py (FR-009)
- [X] T031 [US2] Handle partial success in backend/src/api/ai_routes.py: independent per-side extraction via asyncio.gather, one-side failure → partial_success response with failed_file named + friendly message (FR-018)
- [X] T032 [US2] Implement frontend error handling in frontend/src/components/upload/UploadAIConfig.tsx: clear banner "We couldn't analyze your files. Please try again." on 422; partial-success banner naming failed file; no partial data shown as final result (FR-009, FR-018)
- [-] T033 [US2] Add frontend test for error banner + no-columns-preserved on failure (SKIPPED per developer: no test files)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Current flow remains available and unchanged (Priority: P3)

**Goal**: The existing `/upload` flow (manual column entry, current bank's PDF) keeps working exactly as before; the new AI flow lives at `/upload-AI`.

**Independent Test**: Run the current upload flow end-to-end and verify identical behavior and output to before this feature was added.

### Tests for User Story 3 ⚠️

> **NOTE: All US3 test tasks SKIPPED per developer instruction (no test files).**

- [-] T034 [P] [US3] Regression test: existing `/karwai` endpoint behavior unchanged (SKIPPED)
- [-] T035 [P] [US3] Frontend test: `/upload` route still renders and functions (SKIPPED)

### Implementation for User Story 3

- [X] T036 [US3] Verify no modifications to backend/src/api/routes.py, backend/src/services/pdf_processor.py, backend/src/services/excel_processor.py, frontend/src/app/upload/page.tsx, frontend/src/components/upload/UploadForm.tsx (FR-012 — audit via git diff, confirmed untouched)
- [X] T037 [US3] Confirm `/upload-AI` is reachable at its own distinct path and does not redirect to or alias `/upload` (FR-011) in frontend/src/app/upload-ai/page.tsx (confirmed — separate route directory, builds successfully)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update backend/.env.example and docs with AI env-var setup (quickstart.md validation)
- [ ] T039 Add `bank_net_total`/`company_net_total` Balance-column mapping heuristic for arbitrary detected PDF columns (fallback: "missing" status, matching existing processor) in backend/src/services/ai_pdf_processor.py
- [ ] T040 [P] Add logging for AI detection stages (per-stage timings, retries used, model id) in backend/src/services/ai_structure_detector.py + backend/src/api/ai_routes.py
- [ ] T041 Run existing backend test suite: `cd backend && pytest` — all pre-existing tests still pass (no new test files per developer)
- [ ] T042 Verify frontend still builds/lints: `cd frontend && npm run build` (no new test files per developer)
- [ ] T043 Constitution compliance audit: verify all new Python/TS files have `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` header (`/** ... */` for TS), `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ` on crux methods (agent orchestration, extractor), `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` footer
- [ ] T044 Run quickstart.md validation end-to-end (manual: /upload-AI with non-MCB PDF + Excel; verify /upload still works)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1's `detect_structure`; adds retry + error handling. Independently testable via mocked failure
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Regression verification only; no new implementation expected (FR-012)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Tools/agent before detect_structure
- detect_structure before processors
- Processors before endpoint
- Endpoint before frontend integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Tools + agent + extract_pdf within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T011 [P] [US1] Unit test for read_excel tool in backend/tests/test_ai_structure_detector.py"
Task: "T012 [P] [US1] Unit test for read_pdf / read_pdf_words tools in backend/tests/test_ai_structure_detector.py"
Task: "T013 [P] [US1] Unit test for extract_pdf slicing in backend/tests/test_ai_pdf_processor.py"
Task: "T014 [P] [US1] Integration test for /reconcile-ai full success in backend/tests/test_ai_routes.py"

# Launch implementation blocks together:
Task: "T015 [P] [US1] Implement 3 agent tools in backend/src/services/ai_structure_detector.py"
Task: "T018 [P] [US1] Implement ai_pdf_processor.py pipeline in backend/src/services/ai_pdf_processor.py"
Task: "T019 [P] [US1] Implement ai_excel_processor.py in backend/src/services/ai_excel_processor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Regression-verify → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2 (mocked failures, independent)
   - Developer C: User Story 3 (regression verification)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Per FR-012 and the developer's brief: the old system (`/upload`, `/karwai`, pdf_processor.py, excel_processor.py, routes.py) MUST NOT be modified — US3 is a regression audit, not new implementation
