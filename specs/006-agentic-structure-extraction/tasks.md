---

description: "Task list for Agentic Structure Extraction Upgrade"
---

# Tasks: Agentic Structure Extraction Upgrade

**Input**: Design documents from `/specs/006-agentic-structure-extraction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per the template — this feature does not request TDD; verification tasks are included in each story and the polish phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a transfer feature: the assessor engine (`backend/src/utils/structure_assessor.py`) already ships in production with all three evaluation checks, so Setup/Foundational are minimal and the real work is confined to `backend/src/services/ai_structure_detector.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/` (this feature is backend-only)
- Primary file: `backend/src/services/ai_structure_detector.py`
- Reused unchanged: `backend/src/utils/structure_assessor.py`
- Route: `backend/src/api/ai_routes.py` (unchanged except optional Form field)
- Reference prototype: `backend/tests/test.py` (do not modify)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline state and confirm the production assessor is the current reference — no new project scaffolding is needed.

- [x] T001 Confirm `backend/src/utils/structure_assessor.py` exposes `assess_pdf_structure(pdf_path, columns, header_top, rows_dropped, boundaries, band_top, date_pattern, name_based, opening_balance, reconciliation_type, run_kabir, use_assessor_llm, use_ihsan, request_id)` with `use_ihsan=True` available, matching the plan's Phase 0 findings
- [x] T002 Confirm `backend/src/services/ai_structure_detector.py` `detect_structure()` signature is `(pdf_path, excel_path, sheet_name, max_attempts, request_id)` and the route `backend/src/api/ai_routes.py` calls it with `request_id=` — no route re-wiring required
- [x] T003 Confirm `backend/src/config.py` exposes `AI_MODEL` and `AI_API_KEY` (used by `build_agent`) — no new config needed

**Checkpoint**: Baseline confirmed — the assessor is production-ready and the transfer targets one module.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The one foundational capability every user story depends on — the `assess_structure` evaluation tool bound to uploaded files. Every story's evaluation loop needs this tool to exist first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add `assess_structure(columns_pdf, header_top_pdf, rows_dropped_pdf, column_boundaries_pdf, band_top_pdf, date_pattern_pdf, opening_balance, reconciliation_type) -> str` tool closure to `build_agent_tools()` in `backend/src/services/ai_structure_detector.py`, mirroring the prototype (`backend/tests/test.py`) — calls `assess_pdf_structure(pdf_path=pdf_path, ..., use_ihsan=True)` and returns `json.dumps(assessment, indent=2, default=str)`; include the full docstring explaining the three checks (arithmetic correctness with 50-unit tolerance, completeness, closing-balance anchor) and the bank/vendor sign convention
- [x] T005 Thread `request_id` into the `assess_structure` tool closure so the assessor's nested LLM runs honor cancellation — pass `request_id=request_id` to `assess_pdf_structure` inside the tool, and accept `request_id` in `build_agent_tools()`/`build_agent()` signatures in `backend/src/services/ai_structure_detector.py`
- [x] T006 [P] Add `opening_balance_pdf: Optional[float] = None` to `FileStructureOutput` in `backend/src/services/ai_structure_detector.py` (backward-compatible — `backend/src/services/ai_pdf_processor.py` never reads it; verified in plan Phase 0)

**Checkpoint**: Foundation ready — the agent can now evaluate its own proposals and carry the opening balance. User story implementation can begin.

---

## Phase 3: User Story 1 - Self-correcting structure extraction (Priority: P1) 🎯 MVP

**Goal**: The agent evaluates its proposed PDF structure on three dimensions (arithmetic correctness within 50 units, completeness, closing-balance anchor) and iterates until it passes or a bound is reached — only a verified structure reaches extraction (FR-002, FR-003, FR-004, FR-011).

**Independent Test**: Upload a PDF statement + Excel ledger in the AI flow; confirm the agent's final structure passes all three evaluation checks on a sample where the first proposal is intentionally wrong — the agent must correct itself before emitting the output block.

### Implementation for User Story 1

- [x] T007 [US1] Extend `AGENT_INSTRUCTIONS` in `backend/src/services/ai_structure_detector.py` with the evaluation-first workflow (mirror `backend/tests/test.py`): use the 3 reading tools → derive structure → call `assess_structure` with opening balance + reconciliation type → on `overall_pass: false` read `issues`/`suggestions`/`cumulative_check.first_mismatch_row`/`kabir_check`/`ihsan_check` and revise → emit the `[output]` block only after all three checks pass or a bounded attempt count with no arithmetic failure; keep the existing per-page band/header contract and output-format rules intact
- [x] T008 [US1] Register `assess_structure` in the `tools=[...]` list of `build_agent()` in `backend/src/services/ai_structure_detector.py` (4th tool alongside `read_excel`, `read_pdf`, `read_pdf_words`)
- [x] T009 [US1] Wire evaluator failures into the existing 3-attempt retry loop in `detect_structure()` in `backend/src/services/ai_structure_detector.py`: when `assess_structure` raises (model unreachable, malformed verdict, evaluator crash), set `last_error` and `continue` so the loop surfaces `AIDetectionError(retries_used=...)` → route returns 422 with `FRIENDLY_RETRY_MESSAGE`; ensure `asyncio.CancelledError` still propagates (499 path) — never emit an unverified structure (FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional — the agent self-evaluates, iterates, and only verified structures flow to extraction.

---

## Phase 4: User Story 2 - Deeper file understanding with dedicated reading tools (Priority: P2)

**Goal**: The agent uses the three dedicated reading tools (Excel content, PDF table content, PDF word geometry) to derive accurate structure — including multi-page layouts where page 1 differs from continuation pages (FR-001, per-page band/header support).

**Why mostly satisfied by foundation**: The three reading tools already exist in production `build_agent_tools()`; this story's work is ensuring the instructions leverage them fully for multi-page geometry and unusual Excel headers.

### Implementation for User Story 2

- [x] T010 [P] [US2] Verify `read_pdf_words` in `build_agent_tools()` in `backend/src/services/ai_structure_detector.py` supports per-page inspection (`page` param) and that `AGENT_INSTRUCTIONS` already instructs comparing page 0 vs page 1 (continuation pages start straight at the band); extend instructions only if the prototype's two-pages-in-one-call behavior (`backend/tests/test.py` `read_pdf_words`) adds accuracy the production single-page tool lacks — align the tool to the prototype's contract (drop/lines/page params)
- [x] T011 [P] [US2] Verify `read_excel` in `build_agent_tools()` in `backend/src/services/ai_structure_detector.py` iterates rows (`drop`/`lines`) so the agent can locate the header row for unusual layouts; align signature to the prototype if needed

**Checkpoint**: The reading tools fully match the prototype's capabilities — accurate multi-page geometry and Excel header discovery.

---

## Phase 5: User Story 3 - Opening balance and reconciliation-type awareness (Priority: P3)

**Goal**: The agent reads the statement's Opening Balance from the header (when present) and applies the correct bank/vendor sign convention — both fed into the evaluator so the arithmetic and closing-balance checks are meaningful (FR-005, FR-006).

### Implementation for User Story 3

- [x] T012 [US3] Extend `AGENT_INSTRUCTIONS` in `backend/src/services/ai_structure_detector.py` with Opening Balance guidance (mirror `backend/tests/test.py`): read the figure from the upper region of page 1 (labels like "Opening Balance", "B/F", "Balance Brought Forward"); pass it to `assess_structure`; omit (null) when absent — the evaluator still runs against the cumulative column and closing balance (FR-005)
- [x] T013 [US3] Extend `AGENT_INSTRUCTIONS` in `backend/src/services/ai_structure_detector.py` with reconciliation-type guidance: pass `reconciliation_type="bank"` (default) or `"vendor"` to `assess_structure`; explain the inverted sign roles (bank: Credit = +, Debit = -; vendor: Credit = -, Debit = +) so a mislabeled type surfaces as an arithmetic divergence the agent must fix (FR-006)
- [x] T014 [US3] Thread `reconciliation_type: str = "bank"` through `detect_structure()` in `backend/src/services/ai_structure_detector.py` and add an optional `reconciliationType: str = Form("bank")` field to the `/reconcile-ai` route in `backend/src/api/ai_routes.py`, passed into `detect_structure()`; keep the frontend untouched (no selector today — verified); default preserves existing behavior (FR-006)

**Checkpoint**: All user stories independently functional — opening balance and convention are part of the evaluation loop.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Observability, regression safety, and final verification across all stories.

- [x] T015 Add `opening_balance_pdf` (and `reconciliation_type`) to the `ai_metadata.detected_structure` payload in `backend/src/api/ai_routes.py` success response for observability — non-breaking for the frontend (verified)
- [x] T016 Verify end-to-end: run the production detector (`detect_structure`) against the prototype's sample files (`backend/assets_dev/Bank Recon May-26.xlsx`, `backend/assets_dev/eStatement_6-1-1-20311-714-5XXXX4.pdf` via `backend/tests/test.py` paths) and confirm the agent iterates, `overall_pass` gates the output, and structures pass all three checks (SC-001, SC-003)
- [x] T017 Regression: confirm existing `/reconcile-ai` flow and manual `/karwai` flow behave identically (SC-005, SC-006) — run the existing backend tests and a manual reconcile of a known-good sample; confirm no hardcoded credentials from `backend/tests/test.py` leaked into `backend/src/services/ai_structure_detector.py` (constitution gate — use `settings.AI_MODEL`/`settings.AI_API_KEY`)
- [x] T018 [P] Confirm SC-004 (end-to-end ≤ 2 min) holds with the added evaluation turns — the assessor short-circuits (Kabir after Saghir, Ihsan after both) so clear-cut cases spend no extra LLM call; log detection time via the existing `ai_detection_time_ms` metric
- [x] T019 Update `specs/006-agentic-structure-extraction/` docs (this tasks.md, and note any contract drift in `contracts/`) to reflect the final implementation

---

## Implementation Notes (T019)

**Final agent tool contract** (matches `backend/tests/test.py` exactly):
- `read_excel(drop, lines)` — rows of the Excel sheet
- `read_pdf(drop, lines, page=None)` — PDF table content; `page` is 0-based, `None` = all pages
- `read_pdf_words(drop, lines, page=None)` — word geometry of pages 1 AND 2 in one call (divider-separated); `page` = single 0-based page
- `assess_structure(columns_pdf, header_top_pdf, rows_dropped_pdf, column_boundaries_pdf, band_top_pdf, date_pattern_pdf, opening_balance, reconciliation_type)` — runs `assess_pdf_structure(..., use_ihsan=True, request_id=request_id)`; returns the JSON verdict with `overall_pass`

**Output block contract** (`FileStructureOutput`): 9 fields — `columns_pdf`, `columns_excel`, `header_words_pdf`, `rows_dropped_pdf`, `header_top_pdf`, `column_boundaries_pdf`, `band_top_pdf`, `date_pattern_pdf`, plus new optional `opening_balance_pdf`. Backward-compatible: the deterministic extractors never read `opening_balance_pdf` (verified in plan Phase 0).

**Route change**: `/reconcile-ai` gained optional `reconciliationType` Form field (default `"bank"`), threaded into `detect_structure(..., reconciliation_type=...)` → `build_agent` → `build_agent_tools` → the `assess_structure` tool's default. The frontend does not send it today; the default preserves existing behavior (FR-006). Also added `opening_balance_pdf` + `reconciliation_type` to `ai_metadata.detected_structure` for observability (T015).

**Bug found & fixed during verification (T016)**: `backend/src/utils/structure_assessor.py` used `@tool` in `_ihsan_page_text_tool` (the Ihsan closing-balance reader's PDF text tool) without importing `tool` — a runtime `NameError` the moment Saghir+Kabir passed and Ihsan ran. Fixed by adding `from agents.decorators import tool` at the top of the module (the module already declares the openai-agents SDK dependency in its docstring). Re-verified: Ihsan now runs (`ran=True, found=True, passed=True`) and the closing-balance check passes.

**Constitution gate (T017)**: grep of `backend/src` found zero hardcoded credentials; production uses `settings.AI_MODEL`/`settings.AI_API_KEY`. `backend/tests/test.py` (which contains hardcoded keys) was not modified and its keys were not copied.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories (the `assess_structure` tool must exist before any evaluation loop)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 is the MVP and the primary value; US2/US3 build on the same tool + instructions
  - Sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — touches `AGENT_INSTRUCTIONS` (shared with US1 T007), so sequence after US1 to avoid same-file conflicts
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — touches `AGENT_INSTRUCTIONS` (shared with US1/US2) and `ai_routes.py`; sequence after US1/US2

### Within Each User Story

- Models before services before endpoints (only one model change: T006 `opening_balance_pdf`)
- Story complete before moving to next priority

### Parallel Opportunities

- T006 ([P]) can run in parallel with T004/T005 (different fields; same file but disjoint edits)
- T010, T011 ([P], US2) can run in parallel once Foundational completes
- T018 ([P]) can run in parallel with T016/T017 (independent verification)
- Different user stories touch the same file (`AGENT_INSTRUCTIONS`) — sequential execution avoids merge conflicts

---

## Parallel Example: Foundational Phase

```bash
# T004 + T005 build the tool; T006 adds the output field (parallel-safe, disjoint edits):
Task: "Add assess_structure tool closure in backend/src/services/ai_structure_detector.py"
Task: "Thread request_id into the tool closure in backend/src/services/ai_structure_detector.py"
Task: "Add opening_balance_pdf to FileStructureOutput in backend/src/services/ai_structure_detector.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline confirm)
2. Complete Phase 2: Foundational (assess_structure tool + opening_balance_pdf)
3. Complete Phase 3: User Story 1 (instructions + tool registration + failure wiring)
4. **STOP and VALIDATE**: T016 — the agent iterates and `overall_pass` gates the output
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (4th tool live)
2. Add User Story 1 → Test (T016) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test → Deploy/Demo
4. Add User Story 3 → Test → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (instructions + evaluation loop)
   - Developer B: User Story 2 (reading-tool alignment) — parallel-safe once US1's instruction edits land or if B works on the tools file only
   - Developer C: User Story 3 (route + reconciliation_type) — depends on US1's instruction structure
3. Stories complete and integrate independently; watch the shared `AGENT_INSTRUCTIONS` file

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a transfer: the assessor engine already exists in production; no new dependencies, storage, or config are required (T001-T003 confirm this)
- Do NOT modify `backend/tests/test.py` or copy its hardcoded credentials into production — `settings.AI_MODEL`/`settings.AI_API_KEY` drive the model (constitution gate)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts on `AGENT_INSTRUCTIONS`, cross-story dependencies that break independence
