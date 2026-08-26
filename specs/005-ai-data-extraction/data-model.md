# Data Model: AI-Based Data Extraction

**Branch**: `005-ai-data-extraction` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)

## Overview

This feature introduces **no new persisted entities**. The reconciliation pipeline's persisted domain (history records, user accounts, cloud DB records) is untouched. What is new is a set of **transient, in-memory** domain objects that carry the AI-detected file structure and extraction results through the request lifecycle. All are pydantic models or plain dicts matching existing backend conventions.

## Entities

### 1. DetectedFileStructure (transient, pydantic)

The machine-readable description of both uploaded files, produced by the AI agent and parsed via `parse_output_block`. Mirrors `FileStructureOutput` in `test.py`.

| Field | Type | Source / Validation |
|-------|------|---------------------|
| `columns_pdf` | `list[str]` | PDF column names, left-to-right visual order; non-empty |
| `columns_excel` | `list[str]` | Excel column names in canonical order `[date, details, total, amount(s)]`; 4 entries (combined Debit/Credit) or 5 entries (separate Debit + Credit) |
| `header_words_pdf` | `list[str]` | Exact header word strings from `read_pdf_words`, left-to-right |
| `rows_dropped_pdf` | `int` | Visual lines above the header line; `>= 0` |
| `header_top_pdf` | `float` | `top=` coordinate of the header line |
| `column_boundaries_pdf` | `list[float]` | Ascending x-coordinates; exactly `len(columns_pdf) - 1` values |
| `band_top_pdf` | `float` | Top coordinate of the first transaction data row |
| `date_pattern_pdf` | `str` | Regex matching the first-column transaction dates (e.g. `^\d{2}-[A-Z]{3}-\d{2}$`) |

**Relationship**: one `DetectedFileStructure` per reconciliation request; it is the input to both the PDF extractor and the Excel extractor.

### 2. AIExtractionResult (transient, dict — matches existing processor shapes)

The combined output of the AI-driven extraction, shaped identically to the existing `PDFProcessor.process_pdf` / `ExcelProcessor.process_excel` results so downstream `ReconciliationService` is unchanged.

| Field | Type | Notes |
|-------|------|-------|
| `pdf_result` | `dict` | `bank_statement: list`, `bank_net_total: {value, status}`, `processing_metadata` (same shape as `PDFProcessor.process_pdf`) |
| `excel_result` | `dict` | `company_records: list`, `company_net_total: {value, status}`, `processing_metadata` (same shape as `ExcelProcessor.process_excel`) |
| `ai_metadata` | `dict` | Detected structure summary, retries used per side, per-stage timings, model id |

### 3. Reused entities (unchanged, per FR-007/FR-012)

- **Extracted Transactions** — normalized transaction dicts from `standardize_transaction_data` (bank side: `bank_statement`; company side: `company_records`).
- **Reconciliation Result** — discrepancies + net totals from `ReconciliationService.reconcile`.
- **Past Reconciliation History** — saved history record the user selects; consumed via `HistoryService.load_history(file_name)`; `from_past=True` entries merged into the manual-reconciliation view exactly as in the current flow.

## Validation Rules (from functional requirements)

- `columns_pdf` non-empty and `column_boundaries_pdf` has exactly `len(columns_pdf) - 1` ascending values (LLM contract, `test.py`). Violation → failed detection attempt → retry (FR-008).
- `columns_excel` must contain 4 entries (combined Debit/Credit) or 5 entries (separate Debit + Credit) in canonical order `[date, details, total, amount(s)]`. `format_type` derived: 4 entries → `debit-plus-credit`; 5 entries → `debit-pipe-credit` (FR-004).
- Detected Excel sheet must exist in the workbook; fallback to first populated sheet when detection is inconclusive (Assumption).
- All detected PDF/Excel columns must actually exist in the file when cross-checked; mismatch → failed attempt (FR-008).
- No partial or corrupted results may be returned after 3 failed attempts (FR-009) — the endpoint returns 422 with a friendly retry message.

## State Transitions

Request lifecycle for `/reconcile-ai`:

```text
uploaded files
   → [AI detection (parallel)]            # FR-019, up to 3 retries each (FR-008)
        ├─ both succeed → extraction (PDF dynamic + Excel via detected columns)
        ├─ one succeeds, one fails → PARTIAL SUCCESS (FR-018): successful side's data + message naming failed file
        └─ both fail → 422 retry error (FR-009)
   → reconciliation (unchanged)           # FR-007
   → discrepancies presented              # no review step (FR-017)
   → manual reconciliation + save/load    # FR-013 (unchanged)
```

## Scale / Volume Notes

- Upload size limits unchanged (50MB PDF/Excel, 10MB warning threshold, `backend/src/config.py`).
- One AI detection round-trip per file; concurrency bounded by existing `MAX_CONCURRENT_REQUESTS` (10) and per-request 2-minute processing margin (SC-003).
- Temporary uploads cleaned up after processing (FR-014) and on shutdown, per existing `cleanup_old_files` / `cleanup_all_files`.
