---

description: "Task list for cloud file migration feature"
---

# Tasks: Cloud File Migration

**Input**: Design documents from `specs/001-cloud-file-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cloud-history-api.md

**Tests**: Not requested. Tests are included only if the feature specification explicitly requires them.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `frontend/src/` (Next.js App Router)
- **Backend**: `backend/src/` (FastAPI — already complete, no changes needed)

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 [P] Create cloud history TypeScript types in `frontend/src/types/cloud-history.types.ts` (types: `LoadCloudFilesResponse`, `SaveCloudFileRequest`, `SaveCloudFileResponse`, `CloudApiError`)
- [X] T002 [P] Create cloud history API client in `frontend/src/lib/api/cloudHistoryClient.ts` (methods: `listCloudFiles(token)`, `saveCloudFile(token, fileName, fileData)`)
- [X] T003 Expose JWT token in NextAuth session in `frontend/src/lib/auth.config.ts` (add `access_token` to `jwt()` callback output, propagate to `session()` callback)
- [X] T03a [P] Add 401 (Unauthorized) handling to `cloudHistoryClient.ts` — when a cloud API returns 401, redirect the user to sign-in via NextAuth `signIn()` to satisfy FR-010 (re-authentication on session expiry)

**Checkpoint**: Foundation ready — cloud client exists, token is accessible, 401 handling wired. User story implementation can now begin.

---

## Phase 2: User Story 1 — Cloud-Based Welcome & History Loading (Priority: P1) 🎯 MVP

**Goal**: After sign-in, the user is greeted with "Assalamu Alaikum [name]" and sees their cloud reconciliation history in the "Open Maazi" dropdown.

**Independent Test**: A user signs in, sees the greeting "Assalamu Alaikum [name]" at the top, and below it a dropdown listing file names returned by `load_files_cloud`. With no saved files, the dropdown shows an appropriate empty state. While loading, a spinner is visible.

### Implementation for User Story 1

- [X] T004 [US1] Add "Assalamu Alaikum [user.name]" greeting to `frontend/src/app/upload/page.tsx` using data from the `auth()` server-side session object
- [X] T005 [US1] Update `frontend/src/components/upload/UploadForm.tsx` to replace `historyClient.listHistory()` with `cloudHistoryClient.listCloudFiles(token)` using `useSession()` for the token; handle loading spinner, error state with Retry button, and empty state
- [X] T006 [US1] Update the `HistoryFile` type usage in `UploadForm.tsx` to accept the simpler cloud response (list of strings instead of `HistoryFile[]` objects)

**Checkpoint**: User Story 1 is complete — greeting visible, history loads from cloud with proper loading/error/empty states.

---

## Phase 3: User Story 2 — Cloud-Based File Saving (Priority: P1)

**Goal**: When a user completes a reconciliation and saves it, the data is persisted via `save_files_cloud` POST API.

**Independent Test**: A user completes a reconciliation, provides a file name, clicks save — the data is sent to `/api/cloud/save_files_cloud` with the Bearer token. On success, a confirmation message appears. On failure, an error message appears and data is not lost.

### Implementation for User Story 2

- [X] T006a [P] [US2] Add validation in `ReconciliationResults.tsx` to disable the save button when discrepancies list is empty, satisfying FR-008 (prevent empty save)
- [X] T007 [US2] Update `frontend/src/components/results/ReconciliationResults.tsx` to replace `historyClient.saveHistory()` with `cloudHistoryClient.saveCloudFile(token, fileName, fileData)` using `useSession()` for the token; map discrepancies to the cloud `file_data` format (list of dicts with `transaction_details`, `transaction_date`, `debit_credit_amount`, `category`)
- [X] T008 [US2] Add data-retention logic: if `saveCloudFile` fails, keep the discrepancies in-memory so the user can retry (FR-007)

**Checkpoint**: User Story 2 is complete — reconciliation saves go to cloud, success/error feedback shown, data retained on failure for retry.

---

## Phase 4: User Story 3 — Cloud History Cross-Device Continuity (Priority: P2)

**Goal**: A user's saved reconciliations persist in the cloud and are accessible from any device after signing in.

**Independent Test**: A user saves a reconciliation on one device, signs out, signs in on another device, and sees that same file in the history list.

**Note**: This story requires NO new code — it is inherently satisfied by US1 (cloud loading) and US2 (cloud saving) working together. This phase validates end-to-end cloud persistence.

### Validation for User Story 3

- [X] T009 [US3] End-to-end validation: save a reconciliation, verify the file appears in the history list on reload (confirms cloud persistence)
- [X] T010 [US3] Verify data persists across sessions: save, sign out, sign in, confirm file still in history list

**Checkpoint**: Full cloud round-trip validated — save persists, load retrieves.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Clean up dead code, prepare for deployment.

- [X] T011 [P] Remove or soft-deprecate old local `historyClient.ts` references in `UploadForm.tsx` and `ReconciliationResults.tsx` — replace all `historyClient.*` calls with `cloudHistoryClient.*` equivalents (verify no dead imports remain)
- [X] T012 [P] Update `frontend/src/lib/api/historyClient.ts` as deprecated (add JSDoc `@deprecated` tag) or remove if no other consumers exist
- [X] T013 [P] Run quickstart.md verification steps end-to-end
- [ ] T014 [P] Update `frontend/.env.local` or deployment config with production `NEXT_PUBLIC_API_URL` if deploying

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No code dependencies — can start immediately
  - T001, T002, T003 are all independent — can run in parallel
- **User Story 1 (Phase 2)**: Depends on T002 (cloud client) and T003 (JWT token) — needs the client and auth infrastructure
  - T004 (greeting) is independent of T002/T003 — uses existing `auth()` server-side
  - T005 + T006 depend on T002 + T003
- **User Story 2 (Phase 3)**: Depends on T002 (cloud client) and T003 (JWT token)
  - Independent of US1 — can run in parallel with Phase 2
- **User Story 3 (Phase 4)**: Depends on both US1 and US2 being complete — pure validation
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Needs T002 + T003 from Foundational
- **User Story 2 (P1)**: Needs T002 + T003 from Foundational — independent of US1
- **User Story 3 (P2)**: No code needed — validation only, depends on US1 + US2

### Within Each User Story

- Types before client (T001 before T002)
- Client + token before component integration (T002 + T003 before T005, T007)
- Core implementation before polish

### Parallel Opportunities

| Tasks | Can Run With | Reason |
|-------|-------------|--------|
| T001, T002, T003 | All in parallel | Different files, no interdependencies |
| T004 | Alongside T005, T006 | Different file, server vs client component |
| T005, T006 | Alongside T007, T008 | US1 and US2 are independent |
| T007, T008 | Alongside T005, T006 | US1 and US2 are independent |
| T011, T012, T013, T014 | All in parallel | Pure cleanup and config |

---

## Parallel Example: User Story 1

```bash
# Launch these together (different files, no dependencies):
Task: "Add greeting to frontend/src/app/upload/page.tsx"
Task: "Update history loading in frontend/src/components/upload/UploadForm.tsx"
Task: "Update types in frontend/src/components/upload/UploadForm.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch these together:
Task: "Update cloud save in frontend/src/components/results/ReconciliationResults.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (T001, T002, T003)
2. Complete Phase 2: User Story 1 (T004, T005, T006)
3. **STOP and VALIDATE**: Test that greeting appears and history loads from cloud independently
4. Deploy/demo if ready

### Incremental Delivery

1. **Foundational complete** → Cloud client + JWT ready
2. **US1 complete** → Greeting + cloud history loading (MVP!)
3. **US2 complete** → Cloud saving functional → Deploy
4. **US3 validation** → Full round-trip verified → Deploy
5. **Polish** → Cleanup + deployment config

### Single Developer Strategy

Sequential execution in priority order:
1. Phase 1 → Phase 2 → **MVP checkpoint** → Phase 3 → Phase 4 → Phase 5

---

## Summary

| Phase | Story | Tasks | Priority | Independent? |
|-------|-------|-------|----------|-------------|
| 1 | Foundational | T001-T003 (3 tasks) | Blocking | Yes (all [P]) |
| 2 | US1: Welcome + History Loading | T004-T006 (3 tasks) | P1 | Yes, after Foundational |
| 3 | US2: Cloud File Saving | T007-T008 (2 tasks) | P1 | Yes, parallel to US1 |
| 4 | US3: Cross-Device Continuity | T009-T010 (2 tasks) | P2 | Dependent on US1+US2 |
| 5 | Polish & Deployment | T011-T014 (4 tasks) | Final | After all stories |

**Total**: 14 tasks (7 parallelizable, 7 sequential)
**MVP Scope**: Phases 1 + 2 (6 tasks)

---

## Notes

- Backend cloud routes are already implemented — no backend changes needed
- The exact JWT claim for `access_token` depends on Auth.js v5 beta internals — verify the claim name during T003
- US3 is automatically satisfied by US1+US2 — no additional code changes required
- CORS is already configured on the backend for `http://localhost:3000` — update if deploying to a different frontend URL
