# Research: AI-Based Data Extraction

**Branch**: `005-ai-data-extraction` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)

Phase 0 research output. Every `NEEDS CLARIFICATION` in the plan's Technical Context was resolved. Decisions are derived from the canonical prototype (`test.py`, `test_results.py`), the existing backend architecture, and the `/sp.clarify` session (5 Q&A, Session 2026-08-06).

## 1. Agent framework for file structure detection

- **Decision**: Use the OpenAI Agents SDK (`openai-agents`), exactly as the validated prototype in `test.py` — `Agent`, `Runner`, the `@tool` decorator, and `LitellmModel` for model routing.
- **Rationale**: `test.py` is the canonical, developer-tested implementation (per the feature brief: "the most canonical file ... already developed and tested is /test.py"). Reusing its agent definition, tool contract, instruction prompt, and `parse_output_block` extractor minimizes risk and matches Developer Stack Authority (Constitution II).
- **Alternatives considered**:
  - Direct OpenAI SDK chat completions with manual tool-call loops — rejected: reimplements what the Agents SDK already does; deviates from the validated prototype.
  - LangChain / other agent frameworks — rejected: new framework proposal without developer approval; Constitution II forbids.
  - A purely deterministic structure guesser (regex/whitespace heuristics) — rejected: exactly the inflexibility the feature exists to remove.

## 2. Model selection & configuration

- **Decision**: Env vars `AI_MODEL` (model id, LiteLLM-prefixed, e.g. `gemini/gemini-2.0-flash` or `deepseek/deepseek-chat`) and `AI_API_KEY`, read via pydantic-settings in `backend/src/config.py`; added to `backend/.env.example`. `LitellmModel(model=AI_MODEL, api_key=AI_API_KEY)`.
- **Rationale**: FR-010 mandates env-var config (no hardcoded credentials/model ids). LiteLLM is already the abstraction in the prototype, giving provider flexibility through the single model string.
- **Alternatives considered**:
  - Hardcoding the prototype's defaults — rejected: violates FR-010.
  - Direct provider SDK per bank/provider — rejected: multiple SDKs, no benefit over LiteLLM.

## 3. Tool design (3 tools feeding the LLM)

- **Decision**: Port the three prototype tools, parameterized by uploaded file path instead of the hardcoded `assets_dev` constants:
  - `read_excel(drop, lines)` → rows of the Excel as a table (pandas, `header=None`, so the LLM sees raw rows and can locate the header row).
  - `read_pdf(drop, lines)` → `page.extract_table()` content per page (dates, details, amounts).
  - `read_pdf_words(drop, lines)` → word geometry of page 1: `top=... | 'word'[x0-x1] ...`, grouped into visual lines — the only tool that reveals physical column positions.
- **Rationale**: The prototype proves this trio gives the LLM everything needed to derive `columns_pdf`, `columns_excel`, `header_words_pdf`, `rows_dropped_pdf`, `header_top_pdf`, `column_boundaries_pdf`, `band_top_pdf`, `date_pattern_pdf`. Paths must come from the uploaded multipart files (edge case in the brief), so tools are closures/factories bound to the request's file paths.
- **Alternatives considered**: pdfplumber `extract_tables` only — rejected: loses geometry needed for boundaries; OCR tooling — rejected: out of scope (scanned PDFs fail gracefully to retry).

## 4. LLM output contract & parsing

- **Decision**: The agent emits EXACTLY ONE fenced block:
  ```
  ~~~
  [output]
  columns_pdf: [...]
  columns_excel: [...]
  header_words_pdf: [...]
  rows_dropped_pdf: 22
  header_top_pdf: 167.7
  column_boundaries_pdf: [...]
  band_top_pdf: 181.3
  date_pattern_pdf: "^\\d{2}-[A-Z]{3}-\\d{2}$"
  ~~~
  ```
  Parsed by `parse_output_block` (regex `~~~\s*\[output\]\s*(.*?)\s*~~~`, JSON-first value parse with quote-strip fallback for regex strings) into pydantic `FileStructureOutput`. Any missing/malformed field, wrong type, or missing block → failed attempt.
- **Rationale**: FR-008/FR-009 require retry on failed LLM behavior; a strict machine-readable contract is what makes "malformed output" detectable. The prototype's parser is battle-tested.
- **Alternatives considered**: Free-form JSON only — rejected: regex values (e.g. `\d`) break JSON parsing; the prototype's hybrid parser handles this. Structured output / function calling — deferred: changes the agent contract away from the validated prototype.

## 5. PDF extraction strategy

- **Decision**: Port `extract_pdf` from `test_results.py` verbatim as the core of `ai_pdf_processor.py`: group words by `top` coordinate, keep only lines at/below `band_top` and at/below `header_top + 4.0`, slice words into cells by x-center against `column_boundaries`, keep rows whose first cell matches `date_pattern`, map cells to detected `columns`. Then reuse the existing transform layer (`standardize_transaction_data`, `normalize_pdf_date`, `clean_transaction_detail` from `src/utils/data_transformers.py`) to produce the exact same result shape as `PDFProcessor.process_pdf` (`bank_statement`, `bank_net_total`, `processing_metadata`), so `ReconciliationService` consumes it unchanged.
- **Rationale**: `test_results.py` already mirrors the production `pdf_processor.py` slicing logic but is fully dynamic. Reusing data transformers keeps the standardized output identical to the old flow.
- **Alternatives considered**: Modifying the existing `pdf_processor.py` to accept dynamic boundaries — rejected: FR-012 (old flow unmodified); the AI processor is a separate module.
- **Deferred to tasks**: whether the `Balance`-column net-total extraction (from the old processor) generalizes to arbitrary detected column names — handled by using the last column name present in `columns_pdf` labeled as balance, or falling back to "missing" status as the old code does.

## 6. Excel extraction strategy

- **Decision**: `ai_excel_processor.py` reads the LLM-detected `columns_excel` (exactly 4: transaction date, transaction details, debit/credit column(s), total/sum) and `excel_sheet`, derives `format_type` (`debit-plus-credit` if one amount column, `debit-pipe-credit` if separate debit+credit), and delegates to the existing `ExcelProcessor.process_excel` with those parameters. Result shape (`company_records`, `company_net_total`, `processing_metadata`) unchanged.
- **Rationale**: FR-003/FR-004 (auto column detection + auto format selection) + reuse existing processor; sheet name auto-detected per Assumption.
- **Alternatives considered**: A parallel reimplementation of Excel extraction — rejected: unnecessary duplication; existing processor is already generic given column names.

## 7. Retry & failure orchestration

- **Decision**: `detect_structure(pdf_path, excel_path)` runs the agent ONCE (a single LLM call producing both PDF structure and Excel columns). Wrapped in a retry loop of up to 3 attempts: run agent → `parse_output_block` → pydantic validation → deterministic cross-checks (detected Excel columns must exist in the workbook; boundary count matches columns). Any exception or validation failure consumes an attempt. After 3 failures → structured `AIDetectionError` with `retries_used`. The endpoint maps this to HTTP 422 with a friendly retry message (FR-009). **The AI is detection-only; extraction stays deterministic.**
- **Rationale**: Matches FR-008/FR-009 and the corrected concurrency semantics — the AI runs once (single structure output), while the deterministic extraction phase runs concurrently.
- **Alternatives considered**: Parallel AI calls per file — rejected: FR-019 correction; the agent produces both structures in one run (as the prototype does).

## 8. Concurrency model (corrected)

- **Decision**: The AI agent runs ONCE for structure/column detection. The SYSTEMATIC extraction phase then processes the PDF (`AIPDFProcessor.process_pdf`) and Excel (`AIExcelProcessor.process_excel`) concurrently via `asyncio.gather` (FR-019). Partial failure semantics (FR-018): if the single AI detection fails after retries, both files fail together → 422; the extraction phase can still partial-fail if one processor errors independently → partial_success response naming the failed file.
- **Rationale**: AI = structure detection only (per developer clarification); concurrency lives in the deterministic extractors, which are CPU-bound and benefit from `asyncio.to_thread`/`gather` for large files.
- **Alternatives considered**: Concurrent AI detection calls — rejected (see correction). Sequential extraction — rejected: violates FR-019's latency goal for large files.

## 9. Frontend

- **Decision**: New `frontend/src/app/upload-ai/page.tsx` (auth-guarded like `/upload`, `redirect("/")` when unauthenticated) rendering a new `UploadAIConfig` component: PDF dropzone + Excel dropzone + past-history selector + submit; NO column-name fields, NO format selector (FR-001). During processing, a step-by-step progress indicator (Analyzing file structure → Extracting transactions → Reconciling) driven by `ai_metadata`/stage updates (FR-016, SC-003 2-minute margin). On 422 → clear friendly banner "We couldn't analyze your files. Please try again." (FR-009). Success → reuse existing results/discrepancies components and manual reconciliation + save flow (FR-013).
- **Rationale**: `/upload-AI` per FR-011 + brief ("new Route called '/upload-AI' not changing '/upload'").
- **Alternatives considered**: Extending the existing `/upload` page with a toggle — rejected: violates the explicit route requirement; risk of regressing the old flow (FR-012).

## 10. Dependency additions

- **Decision**: Add `openai-agents` and `litellm` to `backend/requirements.txt`. No new frontend dependencies (fetch-based API call in `frontend/src/lib/api.ts`).
- **Rationale**: The prototype imports `from agents import Agent, Runner` (openai-agents) and `from agents.extensions.models.litellm_model import LitellmModel` (litellm). These are not currently in requirements.
- **Alternatives considered**: Vendoring the agent code from test.py into the backend — rejected: test.py is a standalone prototype; the production module needs the library dependency properly declared.

## Open items (deferred to tasks phase)

- Exact `Balance`-column mapping heuristic for arbitrary PDF column layouts (fallback: "missing" net-total status, same as existing processor).
- History-selection payload shape for `/reconcile-ai` (reuse `HistoryService.load_history` file-name convention).
- Unit-test fixture PDF: reuse `assets_dev/getjobid4620060.pdf` if still present, else generate a synthetic pdfplumber fixture.
