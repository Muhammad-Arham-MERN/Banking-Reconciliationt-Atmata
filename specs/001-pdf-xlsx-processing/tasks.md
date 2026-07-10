---

description: "Task list for PDF and Excel file processing feature implementation"
---

# Tasks: PDF and Excel File Processing for Bank Reconciliation

**Input**: Design documents from `/specs/001-pdf-xlsx-processing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contract.md

**Tests**: Tests are OPTIONAL for this feature. Test tasks are included below but can be skipped if not explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/` for source code, `backend/tests/` for tests
- **Uploads**: `backend/uploads/pdfs/` and `backend/uploads/excels/` for file storage
- **Fixtures**: `backend/fixtures/` for test files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create service directories backend/src/services/, backend/src/models/, backend/src/utils/
- [X] T002 Create test directories backend/tests/unit/, backend/tests/integration/
- [X] T003 [P] Create fixtures directory backend/fixtures/ for test files
- [X] T004 [P] Create uploads subdirectories backend/uploads/pdfs/, backend/uploads/excels/
- [X] T005 [P] Copy test.py reference implementation to backend/fixtures/reference_pdf_implementation.py
- [X] T006 [P] Verify Java Runtime Environment installation for tabula-py (java -version)
- [X] T007 [P] Verify Python dependencies (fastapi, pandas, tabula-py, openpyxl, pytest)

**Checkpoint**: Directory structure and dependencies ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create ProcessedTransaction model in backend/src/models/processing_models.py with Transaction_date, Transaction Detail, Debit/Credit fields
- [X] T009 Create ProcessingResult model in backend/src/models/processing_models.py with bank_statement, company_records, processing_metadata fields
- [X] T010 Create ProcessingMetadata model in backend/src/models/processing_models.py with request_id, processing_time_ms, transaction_counts, filenames
- [X] T011 [P] Implement file validation utilities in backend/src/utils/file_helpers.py (file type validation, size checks, magic byte verification)
- [X] T012 [P] Implement data transformation utilities in backend/src/utils/data_transformers.py (date normalization, debit/credit merging, amount conversion)
- [X] T013 [P] Configure error handling framework in backend/src/utils/error_handlers.py (processing_error, bad_request, internal_error responses)
- [X] T014 [P] Configure logging infrastructure in backend/src/utils/logger.py (processing logs, error tracking, performance metrics)
- [X] T015 Update file upload handling in backend/src/api/routes.py to support pdfs/ and excels/ subdirectories with UUID naming

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Bank Statement Processing (Priority: P1) 🎯 MVP

**Goal**: Extract transaction data from PDF bank statements using tabula-py following test.py pattern

**Independent Test**: Upload a sample PDF bank statement and verify transaction data (dates, descriptions, amounts) is correctly extracted with proper debit/credit sign handling

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Unit test for PDF extraction in backend/tests/unit/test_pdf_processor.py (test_extract_bank_statement_success, test_extract_bank_statement_no_tables)
- [ ] T017 [P] [US1] Unit test for debit/credit merging in backend/tests/unit/test_pdf_processor.py (test_merge_debit_credit_columns, test_date_pattern_validation)
- [ ] T018 [P] [US1] Unit test for date normalization in backend/tests/unit/test_data_transformers.py (test_normalize_pdf_date, test_invalid_date_format)
- [ ] T019 [P] [US1] Integration test for PDF processing flow in backend/tests/integration/test_file_processing_flow.py (test_end_to_end_pdf_processing)

### Implementation for User Story 1

- [X] T020 [P] [US1] Create PDFProcessor class in backend/src/services/pdf_processor.py with CANONICAL_COLUMNS, DATE_PATTERN, BRANCH_NARRATIVE_PATTERN constants
- [X] T021 [P] [US1] Implement extract_bank_statement() method in backend/src/services/pdf_processor.py following test.py pattern (tabula.read_pdf, column mapping, branch/narrative extraction)
- [X] T022 [US1] Implement transform_to_standard_format() method in backend/src/services/pdf_processor.py (debit/credit merging, integer conversion, date normalization)
- [X] T023 [US1] Implement _normalize_date() method in backend/src/services/pdf_processor.py (DD-MMM-YY to YYYY-MM-DD conversion with validation)
- [X] T024 [US1] Add PDF error handling in backend/src/services/pdf_processor.py (no tables found, invalid date format, malformed PDF)
- [X] T025 [US1] Add processing logging in backend/src/services/pdf_processor.py (extraction stats, transformation results, performance timing)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Company Record Processing (Priority: P1) 🎯 MVP

**Goal**: Extract transaction data from Excel company records using pandas with user-provided column mappings

**Independent Test**: Upload a sample Excel file with column name parameters and verify correct columns are identified and data is extracted with proper debit/credit handling

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US2] Unit test for 3-column format processing in backend/tests/unit/test_excel_processor.py (test_process_excel_3_column_format)
- [ ] T027 [P] [US2] Unit test for 4-column format processing in backend/tests/unit/test_excel_processor.py (test_process_excel_4_column_format)
- [ ] T028 [P] [US2] Unit test for column mapping validation in backend/tests/unit/test_excel_processor.py (test_column_not_found_error, test_invalid_numeric_data_handling)
- [ ] T029 [P] [US2] Integration test for Excel processing flow in backend/tests/integration/test_file_processing_flow.py (test_end_to_end_excel_processing)

### Implementation for User Story 2

- [X] T030 [P] [US2] Create ExcelProcessor class in backend/src/services/excel_processor.py with column_mapping parameter support
- [X] T031 [P] [US2] Implement extract_company_records() method in backend/src/services/excel_processor.py (pandas.read_excel, column validation, 3/4-column format detection)
- [X] T032 [US2] Implement transform_to_standard_format() method in backend/src/services/excel_processor.py (column mapping, debit/credit merging for 4-column format, sign handling)
- [X] T033 [US2] Implement _normalize_date() method in backend/src/services/excel_processor.py (Excel serial dates, multiple string format support, YYYY-MM-DD output)
- [X] T034 [US2] Add Excel error handling in backend/src/services/excel_processor.py (column not found, invalid data, file format errors)
- [X] T035 [US2] Add processing logging in backend/src/services/excel_processor.py (column mapping results, extraction stats, transformation results)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simultaneous Processing (Priority: P2)

**Goal**: Process PDF and Excel files concurrently using async operations to minimize total processing time

**Independent Test**: Upload both files simultaneously and measure that processing completes faster than sequential processing, with both datasets returned together

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [P] [US3] Integration test for concurrent processing in backend/tests/integration/test_file_processing_flow.py (test_concurrent_processing_performance)

### Implementation for User Story 3

- [X] T037 [US3] Implement async wrapper for PDF processing in backend/src/api/routes.py (process_pdf_async with asyncio.to_thread)
- [X] T038 [US3] Implement async wrapper for Excel processing in backend/src/api/routes.py (process_excel_async with asyncio.to_thread)
- [X] T039 [US3] Implement concurrent task execution in backend/src/api/routes.py POST /api/karwai endpoint (asyncio.gather with return_exceptions=True)
- [X] T040 [US3] Add concurrent error handling in backend/src/api/routes.py (handle one file failure while other succeeds, partial_success response)
- [X] T041 [US3] Add performance tracking in backend/src/api/routes.py (measure individual and total processing time_ms)
- [X] T042 [US3] Implement file cleanup logic in backend/src/api/routes.py (delete uploaded files after processing completes)

**Checkpoint**: All three user stories should now be independently functional

---

## Phase 6: User Story 4 - Standardized Output Format (Priority: P2)

**Goal**: Return processed data from both PDF and Excel sources in identical standardized format for downstream comparison

**Independent Test**: Process both file types and verify output structures are identical with same field names and data types

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T043 [P] [US4] Unit test for standardized output format in backend/tests/unit/test_data_transformers.py (test_standardize_transaction_format, test_output_structure_consistency)

### Implementation for User Story 4

- [ ] T044 [US4] Implement output validation in backend/src/utils/data_transformers.py (verify Transaction_date, Transaction Detail, Debit/Credit fields exist with correct types)
- [ ] T045 [US4] Implement response builder in backend/src/api/routes.py POST /api/karwai endpoint (build ProcessingResult with standardized results.bank_statement and results.company_records)
- [ ] T046 [US4] Add processing metadata to response in backend/src/api/routes.py (request_id, processing_timestamp, transaction_counts, processing_duration_ms)
- [ ] T047 [US4] Implement standardized error responses in backend/src/api/routes.py (400 for invalid params, 422 for processing errors, 500 for internal errors)

**Checkpoint**: All four user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Create sample PDF test file backend/fixtures/sample_bank_statement.pdf (20 transactions, multi-page)
- [ ] T049 [P] Create sample Excel test files backend/fixtures/sample_company_3col.xlsx and backend/fixtures/sample_company_4col.xlsx
- [ ] T050 [P] Create malformed test files backend/fixtures/malformed.pdf and backend/fixtures/invalid_column_names.xlsx for error testing
- [ ] T051 [P] Update API documentation in backend/README.md with /api/karwai endpoint examples and error response formats
- [ ] T052 Code cleanup and refactoring in backend/src/services/ (remove duplicate code, extract common patterns)
- [ ] T053 Performance optimization across all stories (profile slow operations, optimize pandas/tabula calls)
- [ ] T054 Security hardening (validate file uploads, sanitize file paths, prevent path traversal)
- [ ] T055 Run quickstart.md validation (test all implementation steps, verify environment setup)
- [ ] T056 [P] End-to-end integration test in backend/tests/integration/test_full_reconciliation_flow.py (test complete PDF + Excel processing workflow)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P2)**: Depends on US1 and US2 completion - Requires both processors to exist
- **User Story 4 (P2)**: Depends on US1 and US2 completion - Requires both processors to output data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (Phase 1)
- All Foundational tasks marked [P] can run in parallel (Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1 & 2 (P1 - Can start together after Foundational)

```bash
# User Story 1 - PDF Processing (Team A):
Task T016: Unit test for PDF extraction
Task T017: Unit test for debit/credit merging
Task T018: Unit test for date normalization
Task T019: Integration test for PDF processing flow
[All tests run in parallel]

# User Story 2 - Excel Processing (Team B):
Task T026: Unit test for 3-column format processing
Task T027: Unit test for 4-column format processing
Task T028: Unit test for column mapping validation
Task T029: Integration test for Excel processing flow
[All tests run in parallel]

# Both teams work independently after Foundational phase completes
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only - P1 Stories)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (PDF Processing)
4. Complete Phase 4: User Story 2 (Excel Processing)
5. **STOP and VALIDATE**: Test both file processing independently
6. Demo MVP: PDF and Excel files can be processed separately

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → PDF processing works
3. Add User Story 2 → Test independently → Excel processing works
4. **MVP CHECKPOINT**: Both file types processable separately
5. Add User Story 3 → Test independently → Concurrent processing enabled
6. Add User Story 4 → Test independently → Standardized output guaranteed
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With 2-4 developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - **Developer A**: User Story 1 (PDF Processing)
   - **Developer B**: User Story 2 (Excel Processing)
   - [Parallel work on P1 stories]
3. After US1 and US2 complete:
   - **Developer A**: User Story 3 (Concurrent Processing)
   - **Developer B**: User Story 4 (Standardized Output)
   - [Parallel work on P2 stories]
4. Stories complete and integrate independently

---

## Summary

**Total Tasks**: 56 tasks across 7 phases
- **Setup (Phase 1)**: 7 tasks
- **Foundational (Phase 2)**: 8 tasks (BLOCKS all user stories)
- **User Story 1 (Phase 3)**: 10 tasks (PDF Processing - P1)
- **User Story 2 (Phase 4)**: 10 tasks (Excel Processing - P1)
- **User Story 3 (Phase 5)**: 7 tasks (Concurrent Processing - P2)
- **User Story 4 (Phase 6)**: 7 tasks (Standardized Output - P2)
- **Polish (Phase 7)**: 9 tasks (Cross-cutting improvements)

**Parallel Opportunities**: 31 tasks marked [P] can run in parallel with proper team coordination

**Independent Test Criteria**:
- **US1**: Upload PDF, verify extracted transaction data matches expected structure
- **US2**: Upload Excel with column params, verify correct columns extracted
- **US3**: Upload both files, verify processing faster than sequential
- **US4**: Process both types, verify identical output structures

**Suggested MVP Scope**: Phases 1-4 (Setup, Foundational, US1, US2) - Enables core file processing functionality
