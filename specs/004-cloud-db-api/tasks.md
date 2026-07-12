# Tasks: Cloud Database API Endpoints

**Branch**: `004-cloud-db-api` | **Date**: 2026-07-10
**Input**: Design documents from `specs/004-cloud-db-api/` (plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/cloud-api.yaml)
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Integration tests are included at the end (contract-level with httpx.AsyncClient against a real CockroachDB test DB per research.md).

**Organization**: Tasks are grouped by user story. Both stories are P1. US1 (GET files listing) is the foundational read — it comes first because US2 tests verify write-after-read consistency (SC-005).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies required by this feature

- [X] T001 Add SQLModel, asyncpg, psycopg2-binary, greenlet to `backend/requirements.prod.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SQLModel async engine setup and shared model that BOTH user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create SQLModel async engine session factory in `backend/src/db/session.py` — include required basmalah header `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ` and footer `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`
- [X] T003 [P] Create ReconciliationData SQLModel table model + Pydantic request/response models in `backend/src/models/cloud_models.py`
- [X] T004 Wire SQLModel metadata table creation into app startup in `backend/src/main.py` (call `SQLModel.metadata.create_all(sync_engine)` in the existing lifespan startup, alongside the current migration runner)

**Checkpoint**: Foundation ready — async SQLModel sessions can be created and `cloud_models.py` models are importable by both stories.

---

## Phase 3: User Story 1 — Retrieve Cloud-Stored Files (Priority: P1) 🎯 MVP

**Goal**: Authenticated users can GET their list of stored file names from the cloud database.

**Independent Test**: Call `GET /api/cloud/files` with a valid JWT token and verify the response returns `{"files": [...]}`. With no saved files, returns `{"files": []}`. Without auth, returns 401.

### Implementation for User Story 1

- [X] T005 [US1] Implement `get_user_files()` service function in `backend/src/services/cloud_service.py` — reads `users.files` JSONB column via existing asyncpg `db_service.fetchrow()`
- [X] T006 [US1] Implement `GET /api/cloud/files` route in `backend/src/api/cloud_routes.py` — reads `request.state.user_id` from auth middleware, calls `get_user_files()`, returns `FileListResponse`. Include required basmalah header and footer.
- [X] T007 [US1] Register `cloud_router` in `backend/src/main.py` — import and `app.include_router()`

**Checkpoint**: User Story 1 functional — `GET /api/cloud/files` returns file list or empty array, rejects unauthenticated requests with 401.

---

## Phase 4: User Story 2 — Save Reconciliation Data (Priority: P1)

**Goal**: Authenticated users can POST reconciliation data (file_name + file_data) to the cloud database. Duplicate file_name triggers upsert.

**Independent Test**: Call `POST /api/cloud/save` with valid file_name and file_data, verify 200 response. Call again with same file_name (upsert), verify 200. Call with empty file_name, verify 422. Call without auth, verify 401.

### Implementation for User Story 2

- [X] T008 [P] [US2] Implement `save_reconciliation()` service function in `backend/src/services/cloud_service.py` — upsert logic with SQLModel AsyncSession: select existing by file_name + user_id, update or insert, sync `users.files` for new records. Mark the upsert crux with `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ` per Constitution Standard 2.
- [X] T009 [US2] Implement `POST /api/cloud/save` route in `backend/src/api/cloud_routes.py` — validates body via `SaveReconciliationRequest` Pydantic model, calls `save_reconciliation()`, returns `SaveSuccessResponse`

**Checkpoint**: User Stories 1 AND 2 both functional independently.

---

## Phase 5: Integration Tests

**Purpose**: End-to-end contract tests verifying GET and POST endpoints against the real CockroachDB test database.

- [ ] ~~T010 [P] Create test fixtures~~ — SKIPPED (not requested)
- [ ] ~~T011 [US1] Write integration tests~~ — SKIPPED (not requested)
- [ ] ~~T012 [US2] Write integration tests~~ — SKIPPED (not requested)
- [ ] ~~T013 Run full test suite~~ — SKIPPED (not requested)

---

## Phase 6: Edge Cases & Error Handling

**Purpose**: Handle database errors, large payloads, and remaining edge cases from the spec.

- [X] T014 Add database error handling in `backend/src/services/cloud_service.py` — wrap asyncpg/SQLModel operations in try/except, raise consistent HTTP exceptions for 503 (db unreachable) and 500 (unexpected errors)
- [X] T015 Add 503 error response handler for cloud routes in `backend/src/api/cloud_routes.py` — catch `ConnectionError`, `RuntimeError` from DB layer, return 503
- [X] T016 Implement `users.files` JSONB size management in `backend/src/services/cloud_service.py` — ensure append operation doesn't exceed reasonable limits (warn log if > 1000 files)
- [X] T017 [P] Verify all new files (T002, T003, T005, T006, T008, T009, T010) have required basmalah header `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ` and footer `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` per Constitution Standards 1 & 3

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Foundational)**: Depends on T001 — BLOCKS all user stories
- **Phase 3 (US1 — GET)**: Depends on Phase 2 (T002, T003, T004)
- **Phase 4 (US2 — POST)**: Depends on Phase 2 (T002, T003, T004); independent of US1
- **Phase 5 (Tests)**: Depends on all implementation tasks (T001–T009)
- **Phase 6 (Edge Cases)**: Depends on all implementation tasks (T001–T009)

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependency on US2
- **US2 (P1)**: Can start after Foundational (Phase 2) — No dependency on US1

### Within Each User Story

- Models and session setup before service functions
- Service functions before routes
- Implementation before tests
- Story complete before moving to next

### Parallel Opportunities

- T002 (session.py) and T003 (cloud_models.py) can run in parallel
- T008 (save service) and T010 (test config) can run in parallel
- T011 (US1 tests) and T012 (US2 tests) can run in parallel
- T014, T015, T016 (edge cases) can all run in parallel

---

## Parallel Execution Examples

```bash
# Phase 2: Foundational — T002 and T003 in parallel:
Task: "Create SQLModel async engine + session factory in backend/src/db/session.py"
Task: "Create ReconciliationData model + Pydantic models in backend/src/models/cloud_models.py"
```

```bash
# Phase 3 vs Phase 4: US1 and US2 service functions in sequence (same file):
# First: T005 (get_user_files in cloud_service.py)
# Second: T006 (GET route in cloud_routes.py)
# Then: T008 (save_reconciliation in cloud_service.py)
# Then: T009 (POST route in cloud_routes.py)
```

```bash
# Phase 5: T011 and T012 in parallel:
Task: "Write GET /files tests in test_cloud_api.py"
Task: "Write POST /save tests in test_cloud_api.py"
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: T001 (dependencies)
2. Complete Phase 2: T002, T003, T004 (foundational)
3. Complete Phase 3: T005, T006, T007 (US1 — GET endpoint)
4. **STOP and VALIDATE**: Test `GET /api/cloud/files` manually or with curl
5. Deploy/demo with read-only cloud access

### Full Delivery

1. Complete MVP steps 1–4 above
2. Complete Phase 4: T008, T009 (US2 — POST endpoint)
3. Complete Phase 5: T010, T011, T012, T013 (integration tests)
4. Complete Phase 6: T014, T015, T016 (edge cases)
5. Run full test suite, verify all acceptance scenarios pass

---

## Summary

| Item | Count |
|------|-------|
| Total tasks | 17 |
| Phase 1 (Setup) | 1 |
| Phase 2 (Foundational) | 3 |
| Phase 3 (US1 — GET) | 3 |
| Phase 4 (US2 — POST) | 2 |
| Phase 5 (Tests) | 4 |
| Phase 6 (Edge Cases) | 4 |
| Parallel tasks | 9 (marked [P]) |
| User stories | 2 (both P1) |
|
