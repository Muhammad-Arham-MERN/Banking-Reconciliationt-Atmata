---

description: "Task list for Open de Past feature implementation"
---

# Tasks: Open de Past — Save & Load Historical Reconciliation Data

**Input**: Design documents from `/specs/003-open-de-past/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No test tasks included — not explicitly requested in the specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `Reconciliation History/` directory at project root (created automatically by backend on first save, but ensure `.gitkeep` is added so folder is tracked)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure — the SQLite history service that BOTH user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Create `backend/src/services/history_service.py` with save/list/load SQLite CRUD operations

**Checkpoint**: `history_service.py` exists and can save/list/load SQLite files independently

---

## Phase 3: User Story 1 — Save Completed Reconciliation Results (Priority: P1) 🎯 MVP

**Goal**: User can save all currently displayed discrepancies to a SQLite history file with a single click (optionally with a custom name).

**Independent Test**: Complete a reconciliation, click "Complete Reconciliation" — a `.sqlite` file appears in the `Reconciliation History/` folder containing all discrepancy entries with their categories, details, dates, and amounts.

### Implementation for User Story 1

- [x] T003 [P] [US1] Add `fromPast` boolean field to `DiscrepancyTransaction` in `backend/src/models/reconciliation_models.py`
- [x] T004 [P] [US1] Create TypesScript types in `frontend/src/types/history.types.ts` (HistoryFile interface, SaveHistoryRequest, HistoryEntry)
- [x] T005 [P] [US1] Add `fromPast` boolean field to `DiscrepancyTransaction` in `frontend/src/types/reconciliation.types.ts`
- [x] T006 [P] [US1] Add `saveHistory()`, `listHistory()`, `loadHistory()` methods to `frontend/src/lib/api/historyClient.ts`
- [x] T007 [US1] Add `POST /history/save` endpoint to `backend/src/api/routes.py` — accepts JSON with `discrepancies` array and optional `custom_name`, calls `history_service.save_history()`, returns 201 on success or 409 on name collision
- [x] T008 [US1] Add "Complete Reconciliation" button below manual reconciliation section in `frontend/src/components/results/ReconciliationResults.tsx` — disabled when no discrepancies exist, on click calls `saveHistory()` with current discrepancies
- [x] T009 [US1] Add optional custom name text input near the "Complete Reconciliation" button in `ReconciliationResults.tsx` — if empty, auto-generates date-time name before calling save API; if provided, validates uniqueness

**Checkpoint**: At this point, User Story 1 should be fully functional. User can complete a reconciliation, optionally name it, click save, and find the `.sqlite` file in the history folder.

---

## Phase 4: User Story 2 — Load and Display Past Reconciliation Discrepancies (Priority: P1)

**Goal**: User can select a past history file from an "Open Maazi" dropdown on the upload page. When a new reconciliation completes, past discrepancies appear alongside current ones in the results table, sorted by date, marked with a "From Past" column and light purple background.

**Independent Test**: Save a reconciliation with known discrepancies. Start a new session, select that file via "Open Maazi", upload new files, run reconciliation — verify past discrepancies appear in the correct categories with "From Past" column and purple background.

### Implementation for User Story 2

- [x] T010 [P] [US2] Add `GET /history/list` endpoint to `backend/src/api/routes.py`
- [x] T011 [P] [US2] Add `POST /history/load` endpoint to `backend/src/api/routes.py`
- [x] T012 [US2] Merge past discrepancies client-side in `UploadForm.tsx` — load history data on reconciliation complete, merge into results
- [x] T013 [US2] Add merge function in `UploadForm.tsx` — date+details dedup, from_past flag, chronological sort
- [x] T014 [US2] Add "Open Maazi" dropdown above upload zones in `UploadForm.tsx`
- [x] T015 [US2] Wire selected history file into reconciliation flow in `UploadForm.tsx`
- [x] T016 [US2] Add "From Past" column + purple row background in `CategorizedResults.tsx`

**Checkpoint**: Both user stories should be independently functional. Save + load cycle works end-to-end.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and improvements that affect multiple user stories

- [x] T017 [P] Add error handling for save failure (disk full, permissions) in `ReconciliationResults.tsx` — show error notification, keep results on screen so user can retry
- [x] T018 [P] Handle corrupted history file in POST /history/load — catch SQLite errors, return 422 with "file is corrupted or unreadable" message
- [x] T019 [P] Handle empty history folder in "Open Maazi" dropdown — show "No history available" placeholder, disable selection
- [x] T020 [P] Handle name collision in save endpoint (409 response) — frontend shows notification and lets user choose different name
- [x] T021 Run quickstart.md validation — verify all three API endpoints work, save/load cycle complete, "From Past" styling renders correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — independent of other stories
- **US2 (Phase 4)**: Depends on Phase 2 — independent of US1 (can be built in parallel)
- **Polish (Final Phase)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on US2
- **US2 (P1)**: Can start after Phase 2 — No dependencies on US1

### Within Each Phase

- **[P] tasks within each phase can run in parallel**
- Non-[P] tasks within a phase run sequentially
- Story complete before moving to next priority

### Execution Order

1. T001 (Setup)
2. T002 (Foundational — blocks everything)
3. Parallel: T003 through T009 (all US1 tasks — many are [P])
4. Parallel: T010 through T016 (all US2 tasks — many are [P])
5. T017 through T021 (Polish, after both stories done)

---

## Parallel Opportunities

### Phase 3 (US1): Can parallelize

```bash
Task: "Add fromPast to backend model in backend/src/models/reconciliation_models.py"
Task: "Create history.types.ts in frontend/src/types/history.types.ts"
Task: "Add fromPast to frontend types in frontend/src/types/reconciliation.types.ts"
Task: "Add API client methods in frontend/src/lib/api/reconciliationClient.ts"
```

Then sequentially:
- T007 → T008 → T009

### Phase 4 (US2): Can parallelize

```bash
Task: "Add GET /history/list endpoint in backend/src/api/routes.py"
Task: "Add POST /history/load endpoint in backend/src/api/routes.py"
Task: "Add Open Maazi dropdown in frontend/src/components/upload/UploadForm.tsx"
```

Then sequentially:
- T011 + T012 (backend done) → T013 (merge logic in routes.py or reconciliation_service.py)
- T014 (frontend dropdown) → T015 (pass history file to API call)
- T016 (CategorizedResults column) — independent of T014/T015

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: US1 — Save Reconciliation (T003–T009)
4. **STOP and VALIDATE**: Complete a reconciliation, click "Complete Reconciliation", verify `.sqlite` file created with correct data

### Incremental Delivery

1. Save only → User can archive results (immediate value!)
2. Add load + merge → Full save/load cycle
3. Polish → Error handling for all edge cases

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- SQLite uses Python stdlib `sqlite3` — zero new dependencies
- History files stored at `<project-root>/Reconciliation History/*.sqlite`
- Backend resolves the project root relative to its working directory or via config
pecific user story for traceability
- Each user story should be independently completable and testable
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- SQLite uses Python stdlib `sqlite3` — zero new dependencies
- History files stored at `<project-root>/Reconciliation History/*.sqlite`
- Backend resolves the project root relative to its working directory or via config
