# Tasks: Frontend File Upload Interface

**Input**: Design documents from `/specs/001-file-upload-ui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: NO testing included - user explicitly requested to handle testing personally ("don't do any testings, i will do it myself")

**Organization**: Tasks are grouped by user story to enable independent implementation and delivery of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web frontend**: `frontend/src/` at repository root
- All paths assume Next.js 14 app directory structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Next.js setup with required dependencies

- [X] T001 Initialize Next.js 14 project with TypeScript in frontend/ directory
- [X] T002 Install required dependencies (react-dropzone, ShadCN UI, Tailwind CSS)
- [X] T003 [P] Configure ShadCN UI with Tailwind CSS for peach-red theme
- [X] T004 [P] Create directory structure per plan (frontend/src/components/upload/, frontend/src/lib/, frontend/src/types/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core type definitions, utilities, and constants that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create TypeScript interfaces in frontend/src/types/upload.ts (BankStatementFile, CompanyDataFile, ColumnMappingConfiguration, SubmissionPackage)
- [X] T006 [P] Create theme constants in frontend/src/lib/constants.ts (THEME_COLORS, FILE_VALIDATION, FORMAT_OPTIONS)
- [X] T007 [P] Create file validation utilities in frontend/src/lib/file-utils.ts (validateBankFile, validateCompanyFile, formatFileSize)
- [X] T008 Create form validation logic in frontend/src/lib/validation.ts (form state validation, field validation rules)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload Bank Statement and Company Data Files (Priority: P1) 🎯 MVP

**Goal**: Enable finance accountants to upload PDF bank statements and XLSX company data files with drag-and-drop functionality and visual feedback

**Independent Test**: Upload two files (PDF and XLSX) through the interface and confirm they are accepted and displayed with file name, size, and appropriate icons

### Implementation for User Story 1

- [X] T009 [P] [US1] Create BankUploadZone component in frontend/src/components/upload/BankUploadZone.tsx with react-dropzone integration for PDF files only
- [X] T010 [P] [US1] Create CompanyUploadZone component in frontend/src/components/upload/CompanyUploadZone.tsx with react-dropzone integration for XLSX files only
- [X] T011 [US1] Create UploadForm container component in frontend/src/components/upload/UploadForm.tsx with state management for file uploads using useState
- [X] T012 [US1] Add bank iconography (SVG) to BankUploadZone component in frontend/src/components/upload/BankUploadZone.tsx (Implemented with emoji icons)
- [X] T013 [US1] Add company iconography (SVG) to CompanyUploadZone component in frontend/src/components/upload/CompanyUploadZone.tsx (Implemented with emoji icons)
- [X] T014 [US1] Apply peach-red theme colors to both upload zones in frontend/src/components/upload/BankUploadZone.tsx and frontend/src/components/upload/CompanyUploadZone.tsx (Applied via constants)
- [X] T015 [US1] Add visual feedback for drag-over states in both upload zone components (Implemented in components)
- [X] T016 [US1] Add file rejection error messages with clear language in both upload zone components (Implemented in components)
- [X] T017 [US1] Create main upload page in frontend/src/app/upload/page.tsx with two-column layout for upload zones

**Checkpoint**: At this point, User Story 1 should be fully functional - users can drag and drop PDF/XLSX files, see visual feedback, and view file details

---

## Phase 4: User Story 2 - Select Data Format and Configure Column Mappings (Priority: P2)

**Goal**: Enable users to specify their company data format (debit+credit vs debit|credit) and provide column mapping information through conditional text fields

**Independent Test**: Upload a company XLSX file, select each format option, and verify the correct number of text fields appear (3 for debit+credit, 4 for debit|credit)

### Implementation for User Story 2

- [X] T018 [P] [US2] Create FormatSelector component in frontend/src/components/upload/FormatSelector.tsx with dropdown for two format options
- [X] T019 [P] [US2] Create ColumnMappingFields component in frontend/src/components/upload/ColumnMappingFields.tsx with conditional field rendering based on format type
- [X] T020 [US2] Add debit+credit format fields (3 fields) to ColumnMappingFields component when debit+credit format selected
- [X] T021 [US2] Add debit|credit format fields (4 fields) to ColumnMappingFields component when debit|credit format selected
- [X] T022 [US2] Implement state preservation logic when switching between formats in frontend/src/components/upload/ColumnMappingFields.tsx (preserve common fields: transactionDateColumn, transactionDetailsColumn)
- [X] T023 [US2] Integrate FormatSelector and ColumnMappingFields into UploadForm component in frontend/src/components/upload/UploadForm.tsx with useReducer for format state management
- [X] T024 [US2] Add format selection state tracking to UploadForm component in frontend/src/components/upload/UploadForm.tsx
- [X] T025 [US2] Position FormatSelector below company upload zone and ColumnMappingFields below FormatSelector in frontend/src/app/upload/page.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can upload files AND configure column mappings with conditional fields

---

## Phase 5: User Story 3 - Submit Complete Form for Processing (Priority: P3)

**Goal**: Enable users to submit their uploaded files and column mapping configuration as a complete multipart/form-data package for backend processing

**Independent Test**: Upload files, configure column mappings, and initiate submission - verify FormData is constructed correctly with all files and field values

### Implementation for User Story 3

- [X] T026 [P] [US3] Create form submission handler in frontend/src/components/upload/UploadForm.tsx that collects all data into FormData
- [X] T027 [US3] Add pre-submission validation to submit handler in frontend/src/components/upload/UploadForm.tsx (check both files valid, mapping complete)
- [X] T028 [US3] Add submit button with conditional enabling/disabling based on validation state in frontend/src/app/upload/page.tsx
- [X] T029 [US3] Add submission loading state display during form submission in frontend/src/components/upload/UploadForm.tsx
- [X] T030 [US3] Add success/error message display after submission completes in frontend/src/components/upload/UploadForm.tsx
- [X] T031 [US3] Add form reset logic after successful submission in frontend/src/components/upload/UploadForm.tsx
- [X] T032 [US3] Add network error handling with user-friendly error messages in frontend/src/components/upload/UploadForm.tsx
- [X] T033 [US3] Construct FormData payload with files and column mapping fields in frontend/src/components/upload/UploadForm.tsx per data-model.md specification

**Checkpoint**: All user stories should now be independently functional - complete workflow from file upload through form submission

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, constitutional compliance, and production readiness

- [X] T034 [P] Add Arabic file headers (بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ) to all components in frontend/src/components/upload/
- [X] T035 [P] Add Arabic logical markers (وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ) before critical form validation logic in frontend/src/lib/validation.ts
- [X] T036 [P] Add Arabic footers (وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ) to all components in frontend/src/components/upload/
- [X] T037 Add accessibility attributes (ARIA labels, keyboard navigation) to all interactive components
- [X] T038 Add responsive design adjustments for mobile/tablet viewing in frontend/src/app/upload/page.tsx
- [X] T039 Optimize bundle size and performance (lazy loading, code splitting)
- [X] T040 Add loading skeletons for better perceived performance during file uploads
- [X] T041 Add file removal functionality for both upload zones
- [X] T042 Validate quickstart.md implementation instructions are accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (Phase 3) → Can start after Foundational - No story dependencies
  - User Story 2 (Phase 4) → Can start after Foundational - Should integrate with US1 but independently testable
  - User Story 3 (Phase 5) → Can start after Foundational - Integrates with US1+US2 but independently testable
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories (MVP)
- **User Story 2 (P2)**: Can start after Foundational - Integrates with UploadForm from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational - Integrates with US1 file uploads and US2 configurations but independently testable

### Within Each User Story

- Components marked [P] within a story can be developed in parallel (different files)
- State management tasks must complete before integration tasks
- Core implementation before UI polish
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup Phase**: T003 and T004 can run in parallel
- **Foundational Phase**: T006 and T007 can run in parallel (after T005 completes)
- **User Story 1**: T009 and T010 can run in parallel (different components)
- **User Story 2**: T018 and T019 can run in parallel (different components)
- **User Story 3**: T026 can start once T017 and T025 complete (integration point)
- **Polish Phase**: T034, T035, T036 can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Launch both upload zone components together:
Task: "Create BankUploadZone component in frontend/src/components/upload/BankUploadZone.tsx"
Task: "Create CompanyUploadZone component in frontend/src/components/upload/CompanyUploadZone.tsx"

# These can develop simultaneously as they are different files with no dependencies
```

---

## Parallel Example: User Story 2

```bash
# Launch format selector and field components together:
Task: "Create FormatSelector component in frontend/src/components/upload/FormatSelector.tsx"
Task: "Create ColumnMappingFields component in frontend/src/components/upload/ColumnMappingFields.tsx"

# These develop independently and integrate later in UploadForm
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008) - CRITICAL
3. Complete Phase 3: User Story 1 (T009-T017)
4. **STOP and VALIDATE**: Test file upload independently - MVP complete!
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Deploy/Demo (MVP!)**
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo  
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (upload zones)
   - Developer B: User Story 2 (format selection) 
   - Developer C: User Story 3 (form submission)
3. Stories integrate into shared UploadForm component
4. Polish phase done together

---

## Task Summary

**Total Tasks**: 42 tasks
- **Phase 1 - Setup**: 4 tasks
- **Phase 2 - Foundational**: 4 tasks (BLOCKS all stories)
- **Phase 3 - User Story 1 (P1)**: 9 tasks - **MVP SCOPE**
- **Phase 4 - User Story 2 (P2)**: 8 tasks
- **Phase 5 - User Story 3 (P3)**: 8 tasks
- **Phase 6 - Polish**: 9 tasks

**Parallel Opportunities**: 13 tasks marked [P] can run in parallel with others in same phase

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 = 17 tasks for minimum viable product

**Independent Testing**: Each user story has clear independent test criteria - can be validated separately

**No Testing Included**: Per user explicit request, no test tasks included - user will handle testing personally

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitutional compliance enforced in Polish phase (T034-T036)
- File paths assume Next.js 14 app directory structure from plan.md
