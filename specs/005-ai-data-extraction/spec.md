# Feature Specification: AI-Based Data Extraction (Istikhraj e Data Ma'a AI)

**Feature Branch**: `005-ai-data-extraction`  
**Created**: 2026-08-06  
**Status**: Draft  
**Input**: User description: "AI-based automatic file structure detection for PDF bank statements and Excel column mapping, replacing manual column entry; exposed on a new /upload-AI flow while the current flow stays intact."

## User Scenarios & Testing

### User Story 1 - Hands-free reconciliation with automatic structure detection (Priority: P1)

A user uploads a PDF bank statement (from any bank) and an Excel company ledger, selects a past reconciliation history, and submits for processing — without manually entering any column names or format details. The system automatically figures out the structure of both files (PDF layout: column positions, header location, transaction band, date format; Excel: which columns hold dates, transaction details, debits/credits, and totals) and uses that structure to extract the transactions and run the reconciliation exactly as the current flow does. The user then sees the discrepancies, reconciles them manually, and saves the result.

**Why this priority**: This is the core promise of the feature — removing the two main pain points (only one bank's PDF supported; error-prone manual column entry). Without it, nothing else in the feature delivers value.

**Independent Test**: Can be fully tested by uploading a PDF from a bank other than the currently supported one together with an Excel ledger, submitting with no column information, and verifying that transactions are extracted correctly and discrepancies are produced and saved.

**Acceptance Scenarios**:

1. **Given** a user uploads a PDF bank statement and an Excel ledger, **When** they submit for processing without entering any column names, **Then** the system automatically detects both file structures, extracts transactions, and shows the reconciliation discrepancies.
2. **Given** a PDF from a bank with a different statement layout than the currently supported bank, **When** the user submits it, **Then** the system still extracts the transactions correctly.
3. **Given** an Excel ledger whose column names differ from previous uploads, **When** the user submits it, **Then** the system automatically identifies the date, details, and amount columns without user input.
4. **Given** a successful extraction, **When** the user completes manual reconciliation and saves, **Then** the result is saved and retrievable exactly as in the current flow.

---

### User Story 2 - Graceful handling of failed extraction (Priority: P2)

If the automatic structure detection fails or produces unusable output (e.g., the model is unreachable, credentials are missing, or the response is malformed), the system retries up to 3 times. If it still cannot extract the structure, the user sees a clear, friendly error message asking them to retry — never a partial or corrupted result.

**Why this priority**: A feature that silently fails or corrupts data is worse than no feature. Users must be able to trust that a failure is temporary and retryable, and must never be left with unusable results.

**Independent Test**: Can be fully tested by submitting a file while the model is unavailable (e.g., invalid credentials configured) and verifying that the user receives a clear retry message after the retries are exhausted, with no partial results presented.

**Acceptance Scenarios**:

1. **Given** the extraction model returns a malformed or incomplete result, **When** the system processes it, **Then** it automatically retries up to 3 times before giving up.
2. **Given** all 3 retries fail, **When** the user submits a file, **Then** they see a clear, friendly error message asking them to try again, and no partial results are shown.
3. **Given** the model credentials are missing or invalid, **When** the user submits a file, **Then** the system fails gracefully with the same clear retry message.

---

### User Story 3 - Current flow remains available and unchanged (Priority: P3)

The existing upload flow (manual column entry, current bank's PDF) keeps working exactly as it does today. The new AI-based flow is available on a separate path so both can be used in parallel while the new approach is validated on production data.

**Why this priority**: The user explicitly wants to keep the proven current system as a safety net while the AI approach is tested. No regression to the current flow is acceptable.

**Independent Test**: Can be fully tested by running the current upload flow end-to-end and verifying identical behavior and output to before this feature was added.

**Acceptance Scenarios**:

1. **Given** a user uses the current upload flow, **When** they submit files with manual column entry, **Then** the behavior and results are identical to before this feature.
2. **Given** the new AI flow, **When** a user navigates to it, **Then** it is available at its own distinct path, separate from the current one.

---

### Edge Cases

- What happens when the model API key is missing or invalid? The system fails gracefully with a clear retry message (no crash, no partial output).
- What happens when the model is unreachable (network failure, service outage)? The system retries up to 3 times, then shows the retry message.
- What happens when the model response is malformed — missing fields, wrong types, or unparseable output? Treated as a failed attempt and retried; after 3 attempts, the retry message is shown.
- What happens when the PDF has an unexpected layout (different page size, no extractable text, scanned image)? The system detects the failure and shows the retry message rather than returning wrong data.
- What happens when the Excel ledger uses a single combined amount column instead of separate debit and credit columns (or vice versa)? The system detects the layout automatically and processes it accordingly.
- What happens when the Excel has multiple sheets? The system selects the relevant sheet automatically.
- What happens with multi-page PDFs where the header repeats on continuation pages? The system handles them so transactions are extracted from all pages.
- What happens when the uploaded files are invalid types or corrupted? Existing file validation applies, with the same clear errors as the current flow.
- What happens if the user's session expires mid-processing? The system returns the same authentication error behavior as the current flow.

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept a PDF bank statement and an Excel company ledger as user uploads (multipart files) in the new AI flow, alongside a selection of a past reconciliation history.
- **FR-002**: System MUST automatically determine the PDF file's structure — column names, header line position, number of lines to skip, physical column boundaries, transaction data band, and date format — without any manual input.
- **FR-003**: System MUST automatically determine the Excel file's relevant columns — transaction date, transaction details, debit/credit amount column(s), and total column — without any manual input.
- **FR-004**: System MUST automatically determine whether the Excel uses a single combined debit/credit column or separate debit and credit columns, and select the appropriate processing format without user input.
- **FR-005**: System MUST extract transactions from the PDF using the automatically detected structure, supporting bank statement layouts beyond the currently supported bank.
- **FR-006**: System MUST extract transactions from the Excel using the automatically detected column names.
- **FR-007**: System MUST run the remaining pipeline (comparing debits and credits, generating discrepancies, net totals) identically to the current flow, using the extracted PDF and Excel transactions.
- **FR-008**: When the automatic detection fails or produces invalid output, System MUST retry the detection up to 3 times.
- **FR-009**: When all 3 retries fail, System MUST return a clear, user-friendly error asking the user to try again, and MUST NOT return partial or incorrect results.
- **FR-010**: The model used for detection and its API key MUST be configurable through environment variables; no credentials or model identifiers may be hardcoded.
- **FR-011**: System MUST expose the new AI-based flow at a route distinct from the current upload route.
- **FR-012**: System MUST leave the current upload flow fully functional and unmodified.
- **FR-013**: System MUST allow users to save and reload the reconciliation results produced by the new flow, consistent with the current flow.
- **FR-014**: System MUST clean up uploaded files after processing, consistent with the current flow.
- **FR-015**: System MUST reject uploads that fail standard file-type validation with the same clear errors as the current flow.
- **FR-016**: System MUST show the user a step-by-step progress indicator during processing (file structure detection → transaction extraction → reconciliation), so the user understands the current stage while waiting.
- **FR-017**: System MUST proceed directly from detection to extraction to reconciliation and present discrepancies to the user without a review/correction step; a review-and-correct step for detected structure is explicitly deferred to a future enhancement.
- **FR-018**: When structure detection succeeds for one file but fails for the other after retries, System MUST return partial success — showing the successfully extracted side's data with a clear, user-friendly message naming the failed file and recommending a retry.
- **FR-019**: The AI structure detection runs ONCE, producing both the PDF layout and Excel column names in a single output. The deterministic (systematic) PDF and Excel extractors then process the files concurrently, keeping total latency low for large files. AI is used only for structure/column detection; all transaction processing remains systematic.

### Key Entities

- **Uploaded Bank Statement (PDF)**: The user's bank statement file. Its structure (columns, header position, band, boundaries, date pattern) is unknown until the AI detection step determines it.
- **Uploaded Company Ledger (Excel)**: The user's company record file. Its relevant columns (date, details, amounts) are unknown until the AI detection step determines them.
- **Detected File Structure**: The machine-readable description of both files produced by the AI detection — PDF column names, header location, dropped lines, column boundaries, transaction band, date pattern, and Excel column names plus amount-column layout. This is what feeds the deterministic extraction.
- **Extracted Transactions**: The normalized transaction lists produced from the PDF (bank statement) and Excel (company records) using the detected structure.
- **Reconciliation Result**: The discrepancies and net totals produced by comparing the two extracted transaction lists, plus the manually reconciled final state.
- **Past Reconciliation History**: The saved reconciliation record the user selects alongside the file uploads; it is an input to the new flow exactly as in the current flow.

### Assumptions

- The AI detection derives the Excel amount-column layout (combined debit/credit vs. separate columns) and selects the processing format automatically — no manual format selection in the new flow.
- The AI detection also identifies the correct Excel sheet automatically; when detection is inconclusive, the first populated sheet is used.
- Multi-page PDFs are supported, with repeated headers on continuation pages handled so that all transaction rows are captured.
- The model provider is configurable via environment variables; the provider currently used in the reference prototype is an acceptable default.
- Uploaded files are stored temporarily and deleted after processing, matching the current flow's behavior.
- The new flow reuses the existing reconciliation, history, and validation logic; only the structure detection and extraction inputs change.
- Removing the old system is out of scope for this feature — it will only be removed after the developer confirms the new approach on production data.
- Uploaded file content is transmitted to the external model provider for structure detection, as in the validated prototype; no file data is persisted beyond the existing temporary upload handling. (The developer will seek executive sign-off on data transmission before production rollout.)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can complete a full reconciliation in the new flow without entering any column names, format details, or sheet names.
- **SC-002**: 90% of PDF statements from banks other than the currently supported bank are processed successfully on the first attempt (no manual correction or retry needed).
- **SC-003**: Automatic structure detection completes and results are presented to the user within 2 minutes per submission, with the step-by-step progress indicator shown throughout.
- **SC-004**: When detection fails, the user sees a clear retry prompt within 2 minutes, and no partial or corrupted results are ever displayed.
- **SC-005**: The current upload flow behaves identically to before this feature — verified by running the same test scenarios against it.
- **SC-006**: Users can save and reload results produced by the new flow with the same success rate as the current flow.

## Clarifications

### Session 2026-08-06

- Q: Is it acceptable to transmit raw file-derived content (word geometry, row samples) to the external model provider for structure detection, or must data be restricted? → A: Option A — raw file-derived content is sent to the model provider as in the validated prototype; no file data is persisted beyond existing temporary upload handling; executive sign-off will be sought before production rollout.
- Q: During file processing, what should the user see on screen? → A: Option B — a step-by-step progress indicator (file structure detection → transaction extraction → reconciliation); processing may take up to 2 minutes, so the success/retry margins are set to 2 minutes.
- Q: Before showing discrepancies, should the user get a chance to review/correct the automatically detected structure? → A: Option A — no review step for now; the flow goes straight from detection to discrepancies. A review-and-correct feature may be added later.
- Q: If structure detection succeeds for one file but fails for the other, what should the system do? → A: Option A — partial success matching the current flow: show the successfully extracted side's data plus a clear, user-friendly error message naming the failed file and recommending a retry.
- Q: Should the AI structure detection for PDF and Excel run in parallel or sequentially? → A: The AI agent runs ONCE and produces both the PDF structure and Excel column names in a single output. The concurrency (parallel processing) applies to the SYSTEMATIC extraction phase: after the AI supplies the structure, the deterministic PDF and Excel extractors process the files concurrently. AI is only for structure/column detection; all transaction processing remains systematic. This avoids slowdowns for large Excel/PDF files.
