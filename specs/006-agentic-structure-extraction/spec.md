# Feature Specification: Agentic Structure Extraction Upgrade

**Feature Branch**: `006-agentic-structure-extraction`  
**Created**: 2026-08-15  
**Status**: Draft  
**Input**: User description: "Upgrade the current agentic extraction system. The old AI structure detection system had many weak points, limitations, lack of tools, lack of structure, unpredictable implementation flow, low accuracy, and was unusable in most cases. The new agentic system has many more tools (PDF reading tool, Excel read tool, assessment tool), a detailed tester/analysis tool that tests the agent response using Intelligence and 3 Evaluation marks, and constant reiteration of the agent for perfect, tip-top structure extraction. The new implementation with substantial accuracy increase is developed in backend/tests/test.py. The structure extraction is mainly done by the agent; the new agent extracts just like before and passes the structure to the main system flow for further processing. Implement/upgrade it exactly as implemented in test.py in the Production Agentic Structure Assessor. Everything is already built, just a transfer is needed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Self-correcting structure extraction (Priority: P1)

A user uploads a PDF bank statement and an Excel ledger in the AI flow. The system's agent inspects both files, proposes a structure for the PDF (columns, header position, transaction band, boundaries, date format) and the Excel (column names), and — before finalizing — evaluates its own proposal against the statement's own data using three independent tests: (1) arithmetic correctness — every extracted transaction must move the running balance consistently, (2) completeness — no transactions or pages may be silently dropped, and (3) a closing-balance anchor — the extracted transactions must add up to the statement's printed closing balance within the same tolerance. When any test fails, the agent revises its proposal and re-evaluates, iterating until the structure passes or a bounded number of attempts is reached. The user submits once and receives an accurate reconciliation result without any manual correction.

**Why this priority**: This is the core upgrade. The old system proposed a structure once with no way to verify it, so wrong proposals flowed straight into extraction and produced unusable results. Self-evaluation with iteration is what makes extraction accurate and reliable for arbitrary statement layouts.

**Independent Test**: Can be fully tested by uploading a PDF statement and Excel ledger in the AI flow, then verifying that the final extracted structure passes all three evaluation tests (arithmetic, completeness, closing-balance anchor) on a sample where the first proposed structure is intentionally incorrect — the agent must correct itself before emitting the final structure.

**Acceptance Scenarios**:

1. **Given** a user uploads a PDF statement and an Excel ledger, **When** the agent proposes an initial structure that fails the arithmetic test, **Then** the agent revises the structure and re-evaluates until it passes (or the attempt bound is reached), and only a passing structure reaches extraction.
2. **Given** a structure that silently drops whole pages of transactions, **When** the completeness test runs, **Then** the extraction is rejected and the agent must correct the structure (e.g., continuation-page positions) before finalizing.
3. **Given** a statement where the final day's transactions are missing but everything else looks consistent, **When** the closing-balance anchor test runs, **Then** the loss is detected and the agent corrects the structure before finalizing.
4. **Given** a final structure that passes all three tests, **When** it is passed to the main processing flow, **Then** transactions are extracted and the reconciliation proceeds exactly as before, with no additional user input.

---

### User Story 2 - Deeper file understanding with dedicated reading tools (Priority: P2)

The agent uses dedicated tools to inspect the files before proposing a structure: one reads Excel content row by row, one reads PDF table content, and one reads the raw word geometry of the PDF pages (each word's exact position on the page). These tools let the agent derive accurate column boundaries, header positions, and transaction-band positions for layouts the old system could not handle, including statements where the first page differs from continuation pages.

**Why this priority**: The old system's limited tools produced low accuracy — the agent could not reliably see where columns started and ended. The word-geometry tool in particular is the source of accurate physical measurements.

**Independent Test**: Can be fully tested by uploading a multi-page statement whose first page has an account-header block above the table while continuation pages start straight at the table, and verifying the extracted structure accounts for both layouts (per-page positions) and captures all transactions.

**Acceptance Scenarios**:

1. **Given** a multi-page PDF statement, **When** the agent inspects the pages, **Then** it detects whether page 1 differs from continuation pages and reports per-page header/band positions accordingly.
2. **Given** a PDF whose column boundaries are not obvious from content alone, **When** the agent uses the word-geometry tool, **Then** the derived boundaries fall in real gaps and no data word is cut.
3. **Given** an Excel ledger with an unusual header layout, **When** the agent uses the Excel reading tool iteratively, **Then** it locates the actual column header row and returns the correct column names.

---

### User Story 3 - Opening balance and reconciliation-type awareness (Priority: P3)

Before finalizing, the agent reads the statement's Opening Balance figure from the statement header (when present) and applies the correct debit/credit sign convention for the statement type (bank vs vendor). These inputs make the arithmetic evaluation meaningful: the running balance is checked against the printed cumulative column and the printed closing balance, and the system knows whether a Credit is money in (bank statement) or money out (vendor ledger).

**Why this priority**: Without the opening balance and correct sign convention, the arithmetic tests would either be skipped or produce false failures. This is a correctness enabler for the P1 self-evaluation loop, so it ships together with it.

**Independent Test**: Can be fully tested by uploading a bank statement with a clear opening-balance header and a vendor ledger file, and verifying that each is evaluated under its correct convention (a structure that passes as "bank" fails as "vendor" and vice versa when the type is mislabeled).

**Acceptance Scenarios**:

1. **Given** a statement with a printed opening balance, **When** the agent finalizes the structure, **Then** the opening balance is read from the header region and used in the arithmetic evaluation (auto-verified against the first cumulative row).
2. **Given** a statement with no usable opening balance, **When** the agent finalizes the structure, **Then** the arithmetic evaluation still runs using the statement's cumulative column and closing balance.
3. **Given** a bank statement evaluated under the bank convention, **When** the same structure is evaluated under the vendor convention, **Then** the evaluation reflects the inverted sign roles and the agent reports which type matches the file.

---

### Edge Cases

- What happens when the agent's proposed structure fails one of the three evaluation tests repeatedly? The agent revises and re-evaluates up to the bounded attempt limit; when the limit is reached, the existing graceful-retry behavior applies (clear error message, no partial results).
- What happens when a statement has no printed closing balance? The closing-balance anchor test is inconclusive (not a failure); the verdict defers to the arithmetic and completeness tests.
- What happens when a statement prints a balance only on some rows (sparse balances)? The arithmetic test still advances the running total on every row and compares only where the statement prints a balance.
- What happens when the agent chooses the wrong reconciliation type (bank vs vendor)? The arithmetic test diverges and the agent is expected to switch the type and re-evaluate.
- What happens when the model is unreachable, returns a malformed output, or the credentials are missing? The existing retry and graceful-error behavior applies unchanged, and the same applies if the evaluation itself cannot run — the submission fails gracefully with the retry message and no unverified structure is emitted.
- What happens when the user cancels processing mid-run? The existing cancellation behavior applies unchanged.
- What happens when the detected Excel columns are invalid (missing from the sheet)? The existing deterministic validation rejects the attempt and triggers a retry.
- What happens with a statement whose opening balance is misread from the header? The arithmetic evaluation auto-verifies it against the first cumulative row and the agent corrects it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide the agent with dedicated file-reading tools covering Excel content, PDF table content, and raw PDF word geometry (word positions on the page), before it proposes any structure.
- **FR-002**: System MUST allow the agent to evaluate its proposed PDF structure against the file before finalizing it.
- **FR-003**: The evaluation MUST score the proposed structure on three independent dimensions: (1) arithmetic correctness — every extracted transaction moves a running balance that matches the statement's printed cumulative column within a fixed per-row tolerance of 50 currency units (absorbs per-row rounding; real extraction errors diverge by orders of magnitude); (2) completeness — the extracted row count matches an independently derived raw count of dated transaction rows, so no pages or transactions are silently dropped; (3) closing-balance anchor — the sum of the extracted transactions reconciles with the statement's printed closing balance within the same 50-unit tolerance when one exists.
- **FR-004**: When the evaluation fails, System MUST require the agent to revise its proposed structure and re-evaluate; the final structure is emitted only after all three evaluation dimensions pass, or after a bounded number of attempts with no arithmetic failure.
- **FR-005**: System MUST instruct the agent to read the statement's Opening Balance from the statement header when present and include it in the evaluation; when absent, the evaluation MUST still run using the cumulative column and closing balance.
- **FR-006**: System MUST support both bank and vendor reconciliation conventions in the evaluation's sign handling, and MUST expose the statement type to the agent as an input it can pass to the evaluation tool.
- **FR-007**: The agent's emitted structure MUST include the opening balance (when present) alongside the existing structure fields, and MUST continue to feed the same deterministic extraction and reconciliation pipeline with no further user input.
- **FR-008**: System MUST retain the existing failure behavior — up to 3 detection attempts on failed behavior, a clear friendly retry message when attempts are exhausted, no partial or corrupted results, and cancellation support — unchanged by this upgrade. If the evaluation itself cannot run (model unreachable, credentials missing, malformed verdict), System MUST fail gracefully with the same friendly retry message and MUST NOT emit an unverified structure.
- **FR-009**: The current manual upload flow MUST remain fully functional and unchanged.
- **FR-010**: The evaluation MUST degrade gracefully on files it cannot assess (e.g., no closing balance printed): inconclusive results defer to the other tests rather than failing the verdict.
- **FR-011**: The evaluation's verdict MUST include actionable feedback (which rows, pages, or parameters are wrong) so the agent can correct the right part of the structure on each iteration.
- **FR-012**: System MUST produce accurate structures without requiring any new input or action from the user — the user still submits files once and receives results.

### Key Entities *(include if feature involves data)*

- **Uploaded Bank Statement (PDF)**: The user's statement file. Its structure (columns, header position, band, boundaries, date pattern, opening balance) is derived by the agent and verified by evaluation before use.
- **Uploaded Company Ledger (Excel)**: The user's ledger file. Its relevant column names are derived by the agent and validated against the sheet's header row.
- **Detected File Structure**: The machine-readable description produced by the agent and passed to the deterministic extractors — PDF column names, header words, dropped lines, header position, column boundaries, band position, date pattern, opening balance, and Excel column names.
- **Evaluation Verdict**: The outcome of assessing a proposed structure — three independent dimensions (arithmetic correctness, completeness, closing-balance anchor), each pass/fail/inconclusive, plus actionable issues and suggestions that drive the next agent iteration.
- **Reconciliation Result**: The discrepancies and totals produced by the main pipeline from the verified structure — unchanged from the current flow.

### Assumptions

- The evaluation applies to the PDF structure only; the Excel side continues to be validated by the existing deterministic checks (detected column names must exist in the sheet's header row), as in the validated prototype.
- The upgraded agent fully replaces the detection logic inside the AI flow; the retry loop, cancellation handling, deterministic validation, route, and frontend remain as they are. Only the agent's tools, instructions, output contract, and evaluation loop change.
- The opening balance is an optional addition to the output contract; downstream extraction does not require it, but the evaluation uses it when present.
- The three evaluation dimensions are applied against the statement's own printed figures (cumulative balance column, raw dated row count, printed closing balance) — no external reference data is needed.
- The attempt bound for self-iteration inside a single agent run is bounded by the same maximum-turns limit already used, plus the existing 3-attempt outer retry.
- The current manual upload flow and the existing AI flow's user experience (single submission, progress steps, retry message) are unchanged by this upgrade.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of structures finalized by the upgraded agent pass all three evaluation dimensions on the validated test set (arithmetic correctness, completeness, closing-balance anchor) — measured by running the evaluator over the agent's final outputs.
- **SC-002**: The share of AI-flow submissions that require user intervention or manual correction drops to 0% for the supported test files, versus the old system which was "unusable in most cases".
- **SC-003**: Statements from banks and layouts beyond the currently supported bank are extracted correctly (no missing or duplicated transactions) on the first submission, without manual correction.
- **SC-004**: End-to-end processing time for a submission does not increase beyond the existing bound (results presented within 2 minutes, per the current AI-flow success criteria), despite the agent's self-evaluation iterations.
- **SC-005**: The existing failure behavior is preserved: on exhausted attempts the user still sees the clear retry message, no partial results are ever displayed, and cancellation works as before.
- **SC-006**: The current manual upload flow behaves identically to before this feature — verified by running the same test scenarios against it.

## Clarifications

### Session 2026-08-15

- Q: What tolerance should the arithmetic-correctness dimension use when comparing the running balance against the statement's printed cumulative column? → A: Fixed per-row tolerance of 50 currency units; the closing-balance anchor uses the same 50-unit tolerance.
- Q: What should happen if the evaluation tool itself cannot run (model unreachable, credentials missing, malformed verdict)? → A: Fail gracefully with the existing friendly retry message; never emit an unverified structure.
