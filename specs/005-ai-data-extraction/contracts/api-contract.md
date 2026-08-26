# API Contract: POST /reconcile-ai

**Branch**: `005-ai-data-extraction` | **Date**: 2026-08-06 | **Spec**: [spec.md](../spec.md)

New endpoint for the AI-based reconciliation flow ("Istikhraj e Data Ma'a AI"). The existing `/karwai` endpoint is untouched (FR-012).

## Endpoint

`POST /reconcile-ai` — multipart/form-data. Registered via a new router `backend/src/api/ai_routes.py`; global auth / security / rate-limit middleware applies automatically.

### Request (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bankStatement` | file | yes | PDF bank statement (any bank) |
| `companyData` | file | yes | Excel company ledger |
| `historyName` | string | no | Past reconciliation history name to load alongside (FR-001, FR-013) |

File validation reuses `validate_upload_file` (PDF MIME `application/pdf`; Excel MIME `application/vnd.ms-excel` or `.openxmlformats-officedocument.spreadsheetml.sheet`). Invalid → 400/422 same as `/karwai`.

### Response: 200 — Success (both files detected + reconciled)

```json
{
  "request_id": "uuid",
  "processing_status": "completed",
  "processing_timestamp": "ISO-8601",
  "summary": {
    "total_bank_transactions": 0,
    "total_company_transactions": 0,
    "total_discrepancies": 0,
    "bank_only_discrepancies": 0,
    "company_only_discrepancies": 0,
    "opposite_pairs_removed": 0,
    "processing_duration_ms": 0,
    "pdf_processing_time_ms": 0,
    "excel_processing_time_ms": 0,
    "ai_detection_time_ms": 0,
    "concurrent_processing": true
  },
  "results": {
    "bank_statement": [],
    "company_records": [],
    "discrepancies": []
  },
  "bank_net_total": { "value": null, "status": "missing" },
  "company_net_total": { "value": null, "status": "missing" },
  "ai_metadata": {
    "model": "gemini/gemini-2.0-flash",
    "detected_structure": {
      "columns_pdf": ["Tran. Date", "Effect Date"],
      "columns_excel": ["Date", "Details", "Amount"],
      "header_top_pdf": 167.7,
      "rows_dropped_pdf": 22,
      "column_boundaries_pdf": [45.0, 89.0],
      "band_top_pdf": 181.3,
      "date_pattern_pdf": "^\\d{2}-[A-Z]{3}-\\d{2}$",
      "excel_sheet": "Sheet1",
      "excel_format_type": "debit-plus-credit"
    },
    "retries_used": { "pdf": 1, "excel": 1 },
    "stages": [
      { "stage": "structure_detection", "duration_ms": 0 },
      { "stage": "extraction", "duration_ms": 0 },
      { "stage": "reconciliation", "duration_ms": 0 }
    ]
  },
  "errors": [],
  "message": "✅ Reconciliation complete - Found 0 discrepancies"
}
```

### Response: 200 — Partial success (one file failed after retries) — FR-018

Same envelope as the existing `/karwai` partial-success shape:

```json
{
  "request_id": "uuid",
  "processing_status": "partial_success",
  "processing_timestamp": "ISO-8601",
  "summary": {
    "total_bank_transactions": 0,
    "total_company_transactions": 0,
    "processing_duration_ms": 0,
    "partial_success": true,
    "failed_file": "PDF",
    "failure_reason": "string"
  },
  "results": {
    "bank_statement": [],
    "company_records": []
  },
  "ai_metadata": { "retries_used": { "pdf": 3, "excel": 1 }, "failed_file": "PDF" },
  "errors": ["PDF processing failed: <reason>"],
  "message": "⚠️ We couldn't analyze the PDF file, but the Excel was processed successfully. Please try again."
}
```

### Response: 422 — Detection failed for both files (FR-009)

```json
{
  "error": "ai_detection_failed",
  "message": "We couldn't analyze your files. Please try again.",
  "details": {
    "retries_used": 3,
    "failed_files": ["PDF", "Excel"]
  }
}
```

### Response: 400/422 — Validation errors

Same shapes as `/karwai` (`error: "bad_request"` for invalid format, `error: "processing_error"` for invalid files, with `details`).

### Response: 401 — Unauthenticated

Existing `auth_middleware` behavior (redirect/reject), unchanged.

## Error Semantics Summary

| Condition | Status | Error code |
|-----------|--------|------------|
| Missing/invalid PDF or Excel file | 400/422 | `bad_request` / `processing_error` |
| Both detections fail after 3 retries each | 422 | `ai_detection_failed` |
| One detection succeeds, one fails | 200 | `partial_success` (in body) |
| Model credentials missing/invalid | 422 | `ai_detection_failed` (after retries) |
| Server shutdown | 503 | `service_unavailable` |
