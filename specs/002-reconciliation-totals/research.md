# Research: Reconciliation Totals & Verification

## Overview

Research findings after exploring the full codebase to identify integration points for the Reconciliation Totals feature. No NEEDS CLARIFICATION items existed — all technical decisions were derived from the existing architecture.

## Backend Integration Points

### PDF Processor (`backend/src/services/pdf_processor.py`)

**Decision**: Extract last Balance column value from raw DataFrame before transformation.

**Rationale**: The `CANONICAL_COLUMNS` list already includes `"Balance"` at positional index 10. The raw DataFrame from `extract_bank_statement()` contains the Balance column. The `transform_to_standard_format()` method drops it. The cleanest approach is to extract the last non-null Balance value from the raw DataFrame in `process_pdf()` and pass it through the result.

**Approach**:
1. In `process_pdf()`, after `extract_bank_statement()` returns the DataFrame, inspect the last row's Balance column value
2. Add a `"bank_net_total"` field to the returned result dictionary alongside `"bank_statement"` and `"processing_metadata"`

**Alternatives considered**:
- Adding Balance to the standardized transaction format — rejected because Balance is a running total, not a per-transaction amount, and doesn't fit the `Debit/Credit` column model
- Extracting in a post-processing step in `routes.py` — rejected because the processor already has the raw DataFrame; extracting it later would require re-reading the data

### Excel Processor (`backend/src/services/excel_processor.py`)

**Decision**: Accept an optional `aggregated_total_column` parameter and extract its last row value.

**Rationale**: The user provides the Aggregated Total column name at upload time (similar to how date/details columns are mapped). The last row of that column contains the final company total.

**Approach**:
1. Add `aggregated_total_column: Optional[str] = None` parameter to `process_excel()` and `extract_company_records()`
2. After extracting the standard columns, if the column exists and has data, read the last non-null value from it
3. Add `"company_net_total"` to the returned result dictionary

**Alternatives considered**:
- Frontend calculating from the last transaction — rejected because the Aggregated Total is a separate column that may not match computed totals from individual transaction amounts
- Relying on the last standardized transaction amount — rejected because the order of standardized data may differ from the original spreadsheet

### Route (`backend/src/api/routes.py`)

**Decision**: Add `aggregatedTotalColumn` as an optional form parameter to POST /karwai, and pass it through to the Excel processor.

**Rationale**: Follows the existing pattern where column names are passed as form fields.

**Approach**:
1. Add `aggregatedTotalColumn: Optional[str] = Form(None)` parameter
2. Pass it to `process_excel_async()`
3. Add `"bank_net_total"` and `"company_net_total"` fields to the response object
4. Update `process_excel_async()` signature to accept and forward the new parameter

### Microsoft Excel Column Name Behavior

**Decision**: The last row of the Aggregated Total column is taken as-is, with basic numeric parsing (strip currency symbols, handle comma separators).

**Rationale**: Excel cells can contain formatted values with currency symbols, commas, and other non-numeric characters. The value needs to be cleaned to a float before use.

## Frontend Integration Points

### Column Mapping (`frontend/src/components/upload/ColumnMappingFields.tsx`)

**Decision**: Add a new text input for "Aggregated Total" column name.

**Rationale**: Users need to specify which column in their XLSX contains the running total. The existing column mapping pattern (date, details, debit/credit) serves as a template.

### API Client (`frontend/src/lib/api/reconciliationClient.ts`)

**Decision**: Add `aggregatedTotalColumn` parameter to `processReconciliation()`.

**Rationale**: The frontend must send this value to the backend as a form field.

### Types (`frontend/src/types/reconciliation.types.ts`)

**Decision**: Add `bank_net_total` and `company_net_total` fields to the `ReconciliationResult` interface.

**Rationale**: TypeScript types must reflect the extended API response.

### Results Display (`frontend/src/components/results/`)

**Decision**: Create a new `ReconciliationTotals.tsx` component for the totals section, integrated into `ReconciliationResults.tsx`.

**Rationale**: The totals section is a self-contained UI element showing:
1. Bank Net Total and Company Net Total cards
2. Adjusted Bank Total (with discrepancy additions)
3. Adjusted Company Total (with discrepancy additions)
4. Reconciliation verdict (Balanced / Not Balanced)

**Approach**:
- Place the totals section after the discrepancies card
- Use the existing categorization logic to group discrepancies by type
- Bank Net Total + Uncleared checks + Unpresented checks = Adjusted Bank Total
- Company Net Total + Bank Debited But not credited + Bank credited but not debited = Adjusted Company Total
- Subtract Adjusted Bank Total - Adjusted Company Total
- Display result: 0 → "Reconciliation Successful, Balanced", non-zero → show difference

## Testing Strategy

### Backend Tests

**Decision**: Add unit tests for:
1. PDF processor extracting last Balance value
2. Excel processor extracting last Aggregated Total value
3. Route passing the new form parameter through the pipeline

### Frontend Tests

**Decision**: Add a component test for `ReconciliationTotals` verifying:
1. Correct display of totals
2. Correct calculation with known discrepancy values
3. Correct verdict display for balanced and unbalanced scenarios

## Error Handling

**Decision**: Graceful degradation if columns are missing:
- If Balance column is missing from PDF → omit Bank Net Total, show warning
- If Aggregated Total column is missing or empty → omit Company Net Total, show warning
- If last cell is empty/non-numeric → show specific error message

## Performance Considerations

**Decision**: Negligible performance impact — extracting a single cell value from an already-loaded DataFrame is O(1). No new heavy dependencies.
