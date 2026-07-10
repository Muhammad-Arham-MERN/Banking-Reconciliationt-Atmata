# Tasks: Reconciliation Totals & Verification

**Input**: Design documents from `/specs/002-reconciliation-totals/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contract.md, quickstart.md

**Tests**: Not explicitly requested in specification — implementation-only tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

**Note**: No Setup or Foundational phases needed — the project already exists and is running. All tasks are feature-specific additions to existing files.

---

## Phase 1: User Story 1 — Run Full Reconciliation with Totals and Verification (Priority: P1) 🎯 MVP

**Goal**: Extract last Balance value from PDF bank statement and last Aggregated Total value from XLSX (user-provided column name), return both via API. On frontend, display Bank Net Total and Company Net Total cards.

**Independent Test**: Upload a bank statement PDF with known last Balance value and an XLSX with known last Aggregated Total value. Verify API response contains both values. Verify frontend displays them correctly.

### Implementation

- [X] T001 [P] [US1] Extract last Balance column value from raw DataFrame in `process_pdf()` in `backend/src/services/pdf_processor.py` — after `extract_bank_statement()` returns the DataFrame, get the last non-null value from the `"Balance"` column (index 10 in `CANONICAL_COLUMNS`). Add `"bank_net_total"` field to result dict with `value` (float) and `status` ("found"/"missing"/"invalid").

- [X] T002 [P] [US1] Add `aggregated_total_column` parameter to `extract_company_records()` and `process_excel()` in `backend/src/services/excel_processor.py` — accept the optional column name, read the last non-null value from that column in the DataFrame, parse by stripping currency symbols and commas. Add `"company_net_total"` to result dict with `value` (float) and `status` ("found"/"missing"/"invalid").

- [X] T003 [US1] Wire the `aggregatedTotalColumn` form parameter through `process_reconciliation()` in `backend/src/api/routes.py` — add `aggregatedTotalColumn: Optional[str] = Form(None)` to the endpoint signature, update `process_excel_async()` to accept and forward it, extract `bank_net_total` and `company_net_total` from processor results, and include them in the response dict.

- [X] T004 [P] [US1] Add `NetTotalValue` interface and `bank_net_total` / `company_net_total` fields to `ReconciliationResult` in `frontend/src/types/reconciliation.types.ts` — define `NetTotalValue { value: number | null; status: 'found' | 'missing' | 'invalid' }` and add both fields to the existing `ReconciliationResult` interface.

- [X] T005 [P] [US1] Add `aggregatedTotalColumn` parameter to `processReconciliation()` in `frontend/src/lib/api/reconciliationClient.ts` — add the optional string parameter and append it to the FormData when provided.

- [X] T006 [P] [US1] Add "Aggregated Total" column name text input in `frontend/src/components/upload/ColumnMappingFields.tsx` — following the existing column mapping input pattern (label, text input, placeholder). Add the new field to the `ColumnMappingConfiguration` type in `frontend/src/types/upload.ts`.

- [X] T007 [US1] Wire `aggregatedTotalColumn` through the submit handler in `frontend/src/components/upload/UploadForm.tsx` — include it in the API client call when submitting, following the pattern used for other column mapping fields.

- [X] T008 [US1] Create new `ReconciliationTotals` component in `frontend/src/components/results/ReconciliationTotals.tsx` — Card component displaying Bank Net Total, Company Net Total, adjustment breakdown, adjusted totals, and reconciliation verdict. Handles all US2 error states and US3 verdict logic.

- [X] T009 [US1] Integrate `ReconciliationTotals` into `ReconciliationResults` in `frontend/src/components/results/ReconciliationResults.tsx` — add the new component after the Discrepancies section Card, passing `result.bank_net_total`, `result.company_net_total`, and the discrepancies list.

**Checkpoint**: At this point, User Story 1 should be fully functional. User can upload files, see both raw totals displayed, and see discrepancy categories with their amounts.

---

## Phase 2: User Story 2 — Handle Missing or Invalid Data Gracefully (Priority: P2)

**Goal**: When the Balance column or Aggregated Total column has missing/null/non-numeric values or the column is not found, the system handles it gracefully with clear indicators instead of errors.

**Independent Test**: Upload a PDF with no Balance column and an XLSX with no Aggregated Total column. Verify the API returns status "missing" and the frontend shows appropriate warning messages without crashing.

### Implementation

- [X] T010 [P] [US2] Add graceful handling for missing/invalid Balance in `backend/src/services/pdf_processor.py` — check if the Balance column exists in the extracted DataFrame. If not, set `bank_net_total.status` = `"missing"` and `value` = null. If the last cell is empty or non-numeric after stripping `$` and `,`, set status = `"invalid"`. Log a warning but do not raise an exception.

- [X] T011 [P] [US2] Add graceful handling for missing/invalid Aggregated Total in `backend/src/services/excel_processor.py` — if `aggregated_total_column` is None or not found in DataFrame columns, set `company_net_total.status` = `"missing"` and `value` = null. If last cell is non-numeric after sanitization, set status = `"invalid"`. Log a warning but do not raise an exception.

- [X] T012 [US2] Display appropriate warnings in `frontend/src/components/results/ReconciliationTotals.tsx` — when `status` is `"missing"` or `"invalid"`, show a yellow warning badge with a message like "Balance column not found in bank statement" or "Aggregated Total could not be parsed". Omit the adjusted total calculation for the affected side.

**Checkpoint**: User Story 2 should now be functional. All error scenarios are handled gracefully on both backend and frontend.

---

## Phase 3: User Story 3 — Verify Reconciliation Outcome with Different Scenarios (Priority: P3)

**Goal**: The frontend automatically subtracts the adjusted totals and displays the reconciliation verdict — "Reconciliation Successful, Balanced" when the difference is zero, or the difference with an imbalance message when not.

**Independent Test**: Feed known balanced data (adjusted totals equal) and known unbalanced data (adjusted totals differ by X). Verify the correct verdict displays in each case.

### Implementation

- [X] T013 [US3] Implement the reconciliation verdict calculation in `frontend/src/components/results/ReconciliationTotals.tsx` — compute `difference = adjusted_bank_total - adjusted_company_total`. Use floating-point tolerance of `abs(difference) < 0.001` to determine balance. When balanced, display "Reconciliation Successful, Balanced" in a green success badge. When unbalanced, display the absolute difference formatted as currency and indicate which side ("Bank" or "Company") is higher.

- [X] T014 [US3] Handle all edge case states in `frontend/src/components/results/ReconciliationTotals.tsx`:
  - Zero discrepancy values: adjusted totals should equal raw totals
  - Negative discrepancy values: properly reduce the adjusted total
  - Negative difference: correctly identify which side is higher
  - Both totals missing: show a message indicating verification is unavailable
  - One total missing: show partial verdict with available side only

**Checkpoint**: All user stories should now be independently functional.

---

## Dependencies & Execution Order

### Phase Dependencies

- **User Story 1 (Phase 1)**: Can start immediately — all tasks modify existing files with clear extension points
- **User Story 2 (Phase 2)**: Depends on US1 completion (extends the error handling of code added in US1)
- **User Story 3 (Phase 3)**: Depends on US1 and US2 completion (extends the verdict logic in ReconciliationTotals)

### Within Each Phase

- Tasks marked [P] can run in parallel (different files, no dependencies)
- Non-[P] tasks must be executed in order (they depend on preceding tasks)

### Parallel Opportunities

#### User Story 1 (Phase 1):
```bash
# These three can run in parallel (different files, no cross-dependencies):
Task: T001 — backend/src/services/pdf_processor.py
Task: T002 — backend/src/services/excel_processor.py
Task: T004 — frontend/src/types/reconciliation.types.ts
Task: T005 — frontend/src/lib/api/reconciliationClient.ts
Task: T006 — frontend/src/components/upload/ColumnMappingFields.tsx

# T003 depends on T001 + T002 (needs the processor output)
# T007 depends on T006 (needs the new field)
# T008 depends on T004 + T005 (needs types and API client)
# T009 depends on T008 (needs the component)
```

#### User Story 2 (Phase 2):
```bash
# These can run in parallel:
Task: T010 — backend/src/services/pdf_processor.py (missing balance)
Task: T011 — backend/src/services/excel_processor.py (missing aggregated total)

# T012 depends on T010 + T011 for the frontend warnings
```

#### User Story 3 (Phase 3):
```bash
# Sequential within ReconciliationTotals component:
Task: T013 → T014 (verdict logic, then edge cases)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: User Story 1 (T001–T009)
2. **STOP and VALIDATE**: Test US1 independently — upload files with known values, verify API returns totals, frontend displays them
3. Deploy/demo if ready

### Incremental Delivery

1. Add US1 → Test independently → Deploy/Demo (MVP!)
2. Add US2 → Test independently → Deploy/Demo
3. Add US3 → Test independently → Deploy/Demo

### Key Files to Modify

| File | Change | Story |
|------|--------|-------|
| `backend/src/services/pdf_processor.py` | Extract last Balance value in `process_pdf()` | US1, US2 |
| `backend/src/services/excel_processor.py` | Extract last Aggregated Total value | US1, US2 |
| `backend/src/api/routes.py` | Add form param, wire totals into response | US1 |
| `frontend/src/types/reconciliation.types.ts` | Add NetTotalValue and fields | US1 |
| `frontend/src/types/upload.ts` | Add aggregatedTotalColumn to ColumnMappingConfiguration | US1 |
| `frontend/src/lib/api/reconciliationClient.ts` | Add aggregatedTotalColumn param | US1 |
| `frontend/src/components/upload/ColumnMappingFields.tsx` | Add Aggregated Total input | US1 |
| `frontend/src/components/upload/UploadForm.tsx` | Wire aggregatedTotalColumn | US1 |
| `frontend/src/components/results/ReconciliationTotals.tsx` | **NEW** — totals + adjustments + verdict | US1, US2, US3 |
| `frontend/src/components/results/ReconciliationResults.tsx` | Integrate ReconciliationTotals | US1 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- All code must include Islamic prayer bookends per constitution: `# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ` at start, `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` at end. Mark logical crux methods with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`.
