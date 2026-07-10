# Tasks: Bank Reconciliation Logic

**Input**: Design documents from `/specs/001-bank-reconciliation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/reconciliation-api.json ✅

**Tests**: Test tasks included as this is a financial system requiring accuracy validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for reconciliation feature

- [X] T001 Create backend directory structure if not exists (backend/src/models, backend/src/services, backend/tests/unit, backend/tests/integration)
- [X] T002 Create frontend directory structure if not exists (frontend/src/components/results, frontend/src/types, frontend/src/lib/api, frontend/tests/components)
- [X] T003 [P] Verify backend dependencies installed (FastAPI, Pandas, Tabula-py, pytest)
- [X] T004 [P] Verify frontend dependencies installed (TypeScript, React, Jest)

**Checkpoint**: Project structure ready - can proceed to foundational phase

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create BankTransaction Pydantic model in backend/src/models/reconciliation_models.py
- [X] T006 [P] Create CompanyTransaction Pydantic model in backend/src/models/reconciliation_models.py
- [X] T007 [P] Create DiscrepancyTransaction Pydantic model in backend/src/models/reconciliation_models.py
- [X] T008 [P] Create ReconciliationSummary Pydantic model in backend/src/models/reconciliation_models.py
- [X] T009 [P] Create ReconciliationResult Pydantic model in backend/src/models/reconciliation_models.py
- [X] T010 [P] Create TypeScript BankTransaction interface in frontend/src/types/reconciliation.types.ts
- [X] T011 [P] Create TypeScript CompanyTransaction interface in frontend/src/types/reconciliation.types.ts
- [X] T012 [P] Create TypeScript DiscrepancyTransaction interface in frontend/src/types/reconciliation.types.ts
- [X] T013 [P] Create TypeScript ReconciliationResult interface in frontend/src/types/reconciliation.types.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Transaction Reconciliation (Priority: P1) 🎯 MVP

**Goal**: Deliver core reconciliation functionality that compares bank statements against company records, identifies discrepancies, removes opposite sign pairs, and presents unified discrepancy list with source attribution

**Independent Test**: Upload test bank and company files with known discrepancies and verify output contains bank-only transactions marked FROM:"Bank", company-only transactions marked FROM:"Company", no opposite sign duplicate pairs, and all expected discrepancies captured

### Tests for User Story 1 (SKIPPED - Not Required)

> **NOTE: Tests skipped per user request - moving to implementation**

- [X] T014 [P] [US1] Unit test for opposite sign removal in backend/tests/unit/test_reconciliation_service.py (SKIPPED)
- [X] T015 [P] [US1] Unit test for bank-only discrepancy identification in backend/tests/unit/test_reconciliation_service.py (SKIPPED)
- [X] T016 [P] [US1] Unit test for company-only discrepancy identification in backend/tests/unit/test_reconciliation_service.py (SKIPPED)
- [X] T017 [P] [US1] Unit test for deterministic behavior in backend/tests/unit/test_reconciliation_service.py (SKIPPED)
- [X] T018 [P] [US1] Integration test for reconciliation flow in backend/tests/integration/test_reconciliation_flow.py (SKIPPED)
- [X] T019 [P] [US1] Frontend component test for DiscrepancyList in frontend/tests/components/DiscrepancyList.test.tsx (SKIPPED)

### Implementation for User Story 1

**Backend Core Logic**:
- [X] T020 [US1] Create ReconciliationService class with reconcile() method in backend/src/services/reconciliation_service.py (depends on T005-T009)
- [X] T021 [US1] Implement _find_bank_discrepancies() method in backend/src/services/reconciliation_service.py
- [X] T022 [US1] Implement _find_company_discrepancies() method in backend/src/services/reconciliation_service.py
- [X] T023 [US1] Implement _amounts_match() method with direct equality in backend/src/services/reconciliation_service.py
- [X] T024 [US1] Implement _remove_opposite_pairs() method in backend/src/services/reconciliation_service.py

**Backend API Integration**:
- [X] T025 [US1] Import ReconciliationService in backend/src/api/routes.py
- [X] T026 [US1] Instantiate reconciliation_service in karwai endpoint in backend/src/api/routes.py
- [X] T027 [US1] Call reconcile() with bank and company transactions in backend/src/api/routes.py
- [X] T028 [US1] Add discrepancies field to results object in backend/src/api/routes.py
- [X] T029 [US1] Update summary with discrepancy statistics in backend/src/api/routes.py
- [X] T030 [US1] Add error handling for reconciliation failures in backend/src/api/routes.py

**Frontend Display**:
- [X] T031 [P] [US1] Create reconciliationClient API client in frontend/src/lib/api/reconciliationClient.ts
- [X] T032 [US1] Create DiscrepancyList component structure in frontend/src/components/results/DiscrepancyList.tsx
- [X] T033 [US1] Implement discrepancy rendering with source attribution in frontend/src/components/results/DiscrepancyList.tsx
- [X] T034 [US1] Add Bank vs Company highlighting with color coding in frontend/src/components/results/DiscrepancyList.tsx
- [X] T035 [US1] Display debit/credit amounts with proper formatting in frontend/src/components/results/DiscrepancyList.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Performance Optimization for Large Files (Priority: P2)

**Goal**: Ensure reconciliation completes within 10 seconds for monthly statements with hundreds of transactions (100+ transactions per source)

**Independent Test**: Upload files with 100+ transactions each and measure processing time stays under 10 seconds

### Tests for User Story 2 (TDD - Write these FIRST, ensure they FAIL)

- [ ] T036 [P] [US2] Performance test for 100x100 transaction comparison in backend/tests/performance/test_reconciliation_performance.py
- [ ] T037 [P] [US2] Memory usage test for large transaction lists in backend/tests/performance/test_reconciliation_performance.py

### Implementation for User Story 2

**Backend Optimization**:
- [ ] T038 [US2] Add early termination optimization in _find_bank_discrepancies() in backend/src/services/reconciliation_service.py
- [ ] T039 [US2] Add early termination optimization in _find_company_discrepancies() in backend/src/services/reconciliation_service.py
- [ ] T040 [US2] Implement processing time tracking in ReconciliationService in backend/src/services/reconciliation_service.py
- [ ] T041 [US2] Add concurrent processing flag to summary in backend/src/api/routes.py

**Frontend Performance**:
- [ ] T042 [US2] Add loading state for reconciliation processing in frontend/src/components/results/DiscrepancyList.tsx
- [ ] T043 [US2] Implement virtual scrolling for large discrepancy lists in frontend/src/components/results/DiscrepancyList.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Data Quality and Validation (Priority: P3)

**Goal**: Handle various data quality issues including missing fields, malformed dates, invalid amounts, and duplicate entries within the same source file

**Independent Test**: Upload files with intentional data quality issues and verify appropriate error messages or handling

### Tests for User Story 3 (TDD - Write these FIRST, ensure they FAIL)

- [ ] T044 [P] [US3] Unit test for empty transaction lists in backend/tests/unit/test_reconciliation_service.py
- [ ] T045 [P] [US3] Unit test for malformed transaction data in backend/tests/unit/test_reconciliation_service.py
- [ ] T046 [P] [US3] Unit test for duplicate transactions in same source in backend/tests/unit/test_reconciliation_service.py
- [ ] T047 [P] [US3] Unit test for extremely large monetary values in backend/tests/unit/test_reconciliation_service.py

### Implementation for User Story 3

**Backend Validation**:
- [ ] T048 [US3] Add empty list validation in reconcile() method in backend/src/services/reconciliation_service.py
- [ ] T049 [US3] Add transaction data validation with error handling in backend/src/services/reconciliation_service.py
- [ ] T050 [US3] Implement graceful handling of malformed transactions in backend/src/services/reconciliation_service.py
- [ ] T051 [US3] Add validation for extremely large monetary values in backend/src/services/reconciliation_service.py
- [ ] T052 [US3] Update error responses with clear validation messages in backend/src/api/routes.py

**Frontend Error Display**:
- [ ] T053 [US3] Add error message display for validation failures in frontend/src/components/results/DiscrepancyList.tsx
- [ ] T054 [US3] Add user-friendly error guidance in frontend/src/components/results/DiscrepancyList.tsx

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final quality assurance

- [ ] T055 [P] Add comprehensive docstrings to all reconciliation methods in backend/src/services/reconciliation_service.py
- [ ] T056 [P] Add input validation comments in backend/src/models/reconciliation_models.py
- [ ] T057 [P] Add TypeScript JSDoc comments in frontend/src/types/reconciliation.types.ts
- [ ] T058 [P] Add inline comments for opposite sign removal logic in backend/src/services/reconciliation_service.py
- [ ] T059 [P] Create README documentation for reconciliation service in backend/src/services/README.md
- [ ] T060 [P] Update API documentation in backend/docs/reconciliation-api.md
- [ ] T061 Add edge case handling for zero amount transactions in backend/src/services/reconciliation_service.py
- [ ] T062 Add logging for reconciliation operations in backend/src/services/reconciliation_service.py
- [ ] T063 Add metrics tracking for reconciliation performance in backend/src/utils/metrics.py
- [ ] T064 Run full test suite and ensure 100% pass rate (pytest + Jest)
- [ ] T065 Run quickstart.md validation and update if needed
- [ ] T066 Code cleanup: remove unused imports and variables
- [ ] T067 Security review: validate file upload limits and malicious input handling
- [ ] T068 Final integration test with real PDF/Excel files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Extends US1 but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD approach)
- Models (T005-T009) must complete before services (T020-T024)
- Services (T020-T024) must complete before API integration (T025-T030)
- Core backend (T020-T030) should complete before frontend (T031-T035)

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T003 and T004 can run in parallel

**Foundational Phase (Phase 2)**:
- All model creation tasks (T005-T009) can run in parallel
- All TypeScript type definitions (T010-T013) can run in parallel

**User Story 1 Tests (Phase 3)**:
- All unit tests (T014-T017) can run in parallel
- Integration and component tests (T018-T019) can run in parallel

**User Story 2 Tests (Phase 4)**:
- Both performance tests (T036-T037) can run in parallel

**User Story 3 Tests (Phase 5)**:
- All unit tests (T044-T047) can run in parallel

**Polish Phase (Phase 6)**:
- Documentation tasks (T055-T060) can run in parallel
- Quality tasks (T066-T067) can run in parallel

**Cross-Story Parallelization**:
- Once Foundational phase completes, all three user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD approach):
Task: "Unit test for opposite sign removal in backend/tests/unit/test_reconciliation_service.py"
Task: "Unit test for bank-only discrepancy identification in backend/tests/unit/test_reconciliation_service.py"
Task: "Unit test for company-only discrepancy identification in backend/tests/unit/test_reconciliation_service.py"
Task: "Unit test for deterministic behavior in backend/tests/unit/test_reconciliation_service.py"
Task: "Integration test for reconciliation flow in backend/tests/integration/test_reconciliation_flow.py"
Task: "Frontend component test for DiscrepancyList in frontend/tests/components/DiscrepancyList.test.tsx"

# After tests fail, launch all backend models together:
Task: "Create BankTransaction Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create CompanyTransaction Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create DiscrepancyTransaction Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create ReconciliationSummary Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create ReconciliationResult Pydantic model in backend/src/models/reconciliation_models.py"
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all backend models together:
Task: "Create BankTransaction Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create CompanyTransaction Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create DiscrepancyTransaction Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create ReconciliationSummary Pydantic model in backend/src/models/reconciliation_models.py"
Task: "Create ReconciliationResult Pydantic model in backend/src/models/reconciliation_models.py"

# Launch all frontend types together:
Task: "Create TypeScript BankTransaction interface in frontend/src/types/reconciliation.types.ts"
Task: "Create TypeScript CompanyTransaction interface in frontend/src/types/reconciliation.types.ts"
Task: "Create TypeScript DiscrepancyTransaction interface in frontend/src/types/reconciliation.types.ts"
Task: "Create TypeScript ReconciliationResult interface in frontend/src/types/reconciliation.types.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T013) ⚠️ CRITICAL
3. Complete Phase 3: User Story 1 (T014-T035)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Demo core reconciliation functionality

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T001-T013)
2. Add User Story 1 → Test independently → Deploy/Demo MVP! (T014-T035)
3. Add User Story 2 → Test independently → Deploy/Demo (T036-T043)
4. Add User Story 3 → Test independently → Deploy/Demo (T044-T054)
5. Polish → Final production release (T055-T068)

### Parallel Team Strategy

With multiple developers:

1. **Foundation Sprint**: Team completes Setup (T001-T004) + Foundational (T005-T013) together
2. **Feature Sprint**: Once Foundational is done:
   - Developer A: User Story 1 (T014-T035) - Core reconciliation
   - Developer B: User Story 2 (T036-T043) - Performance optimization
   - Developer C: User Story 3 (T044-T054) - Data quality validation
3. Stories complete and integrate independently
4. **Polish Sprint**: Team completes final quality tasks together (T055-T068)

---

## Task Summary

- **Total Tasks**: 68 tasks
- **Setup Tasks**: 4 tasks
- **Foundational Tasks**: 9 tasks (BLOCKS all user stories)
- **User Story 1 Tasks**: 22 tasks (MVP - core reconciliation)
- **User Story 2 Tasks**: 8 tasks (performance optimization)
- **User Story 3 Tasks**: 11 tasks (data quality validation)
- **Polish Tasks**: 14 tasks (cross-cutting concerns)

**Parallel Opportunities**: 35+ tasks can run in parallel within their phases

**Suggested MVP Scope**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (User Story 1) = 35 tasks for core reconciliation functionality

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests use TDD approach: write tests first, ensure they FAIL, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Financial system requires 100% test coverage for reconciliation logic
- Performance targets: <100ms for reconciliation, <10s total processing
- Follow constitutional principles: accuracy, reliability, strict instruction following
