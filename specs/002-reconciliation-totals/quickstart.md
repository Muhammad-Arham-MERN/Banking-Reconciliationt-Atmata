# Quickstart: Reconciliation Totals & Verification

## What This Feature Adds

This feature extends the existing bank reconciliation system with:

1. **Balance Extraction**: The last row of the Balance column from the PDF bank statement is extracted and returned as `bank_net_total`.
2. **Aggregated Total Extraction**: The last row of a user-specified Aggregated Total column from the XLSX is returned as `company_net_total`.
3. **Adjusted Totals**: On the frontend, discrepancies are applied to each total (Uncleared checks + Unpresented checks → Bank Net Total; Bank Debited/Credited differences → Company Net Total).
4. **Verdict**: The adjusted totals are auto-subtracted. If zero → "Reconciliation Successful, Balanced". If non-zero → shows the difference.

## Implementation Order

### Step 1: Backend — Excel Processor
- File: `backend/src/services/excel_processor.py`
- Add `aggregated_total_column` parameter to `extract_company_records()` and `process_excel()`
- After extracting standard columns, read the last non-null value from the specified column
- Add `"company_net_total"` to the result dictionary

### Step 2: Backend — PDF Processor
- File: `backend/src/services/pdf_processor.py`
- In `process_pdf()`, after `extract_bank_statement()`, get the last non-null Balance from the raw DataFrame
- Add `"bank_net_total"` to the result dictionary

### Step 3: Backend — API Route
- File: `backend/src/api/routes.py`
- Add `aggregatedTotalColumn: Optional[str] = Form(None)` parameter to the endpoint
- Pass it through to `process_excel_async()`
- Extract `bank_net_total` and `company_net_total` from processor results and add to response
- Update `process_excel_async()` signature

### Step 4: Frontend — Types
- File: `frontend/src/types/reconciliation.types.ts`
- Add `NetTotalValue` and `bank_net_total`/`company_net_total` fields to `ReconciliationResult`

### Step 5: Frontend — API Client
- File: `frontend/src/lib/api/reconciliationClient.ts`
- Add `aggregatedTotalColumn` parameter to `processReconciliation()`

### Step 6: Frontend — Column Mapping
- File: `frontend/src/components/upload/ColumnMappingFields.tsx`
- Add "Aggregated Total" column name text input

### Step 7: Frontend — Upload Form
- File: `frontend/src/components/upload/UploadForm.tsx`
- Pass `aggregatedTotalColumn` to the API call

### Step 8: Frontend — Results Display
- File: `frontend/src/components/results/ReconciliationTotals.tsx` (NEW)
- Create component showing Bank Net Total, Company Net Total, adjustments, and verdict
- File: `frontend/src/components/results/ReconciliationResults.tsx`
- Integrate `ReconciliationTotals` component after the discrepancies section

## Key Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Balance extraction location | PDF processor's `process_pdf()` | Raw DataFrame with Balance column available here before it's dropped |
| Aggregated Total extraction | Excel processor's `process_excel()` | User provides column name, processor already handles column mapping |
| Numeric parsing | Strip `$`, `,` and parse | Excel cells often contain formatted currency values |
| Missing column handling | Graceful with status field | Reconciliation still works without totals |
| Floating point tolerance | `abs(diff) < 0.001` | Standard financial tolerance for floating point comparison |
