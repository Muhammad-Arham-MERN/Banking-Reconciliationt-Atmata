# Implementation Plan: Agentic Structure Extraction Upgrade

**Branch**: `006-agentic-structure-extraction` | **Date**: 2026-08-15 | **Spec**: [specs/006-agentic-structure-extraction/spec.md](specs/006-agentic-structure-extraction/spec.md)
**Input**: Feature specification from `/specs/006-agentic-structure-extraction/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Upgrade the production AI structure-detection agent (`backend/src/services/ai_structure_detector.py`) to match the validated prototype (`backend/tests/test.py`): add the fourth `assess_structure` evaluation tool (which scores a proposed PDF structure on three independent dimensions — arithmetic correctness with a fixed 50-unit tolerance, completeness vs. an independent raw dated-row count, and a closing-balance anchor read by a nested agent), wire the opening balance into the agent's output contract, make the agent iterate until its structure passes all three checks, and fail gracefully (same friendly retry message) if the evaluator itself cannot run. The assessor engine (`backend/src/utils/structure_assessor.py`) already ships in production, so this is a transfer of the prototype's agent construction pattern — tools, instructions, output contract, and evaluation loop — into the production service, keeping the route, extractors, retry/cancellation plumbing, and frontend unchanged.

## Technical Context

**Language/Version**: Python 3.10+ (backend); FastAPI async routes  
**Primary Dependencies**: `openai-agents` SDK (already in use), `pdfplumber` (already in use), `pandas` (already in use), `litellm` model extension (already in use)  
**Storage**: N/A (no new persistence; uploads continue to use the existing temporary file flow)  
**Testing**: pytest (existing backend tests), plus the prototype's CLI harness (`backend/tests/test.py`) for manual verification  
**Target Platform**: Backend service (FastAPI) on Linux; Python 3.10+  
**Project Type**: Backend service within a web application (frontend + backend monorepo)  
**Performance Goals**: Detection + evaluation iterations must stay within the existing 2-minute end-to-end bound (SC-004); the evaluator reuses the already-shipped assessor, so no new external calls beyond the existing agent turns  
**Constraints**: Must not change the route, extractors, retry/cancellation plumbing, or frontend; `reconciliation_type` remains "bank" by default (frontend does not surface it today — verified); output-contract additions must be backward-compatible for the deterministic extractors (verified: `opening_balance_pdf` is unused by `ai_pdf_processor.py`)  
**Scale/Scope**: Single-agent upgrade inside one backend module; touches one service, one output model, and the agent construction; assessor engine reused unchanged

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status |
|------|--------|
| Every Python/TypeScript file begins with `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` and ends with `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` (project convention) | PASS — all touched files follow this already; the assessor marks crux methods with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ` |
| No hardcoded credentials; model + API key configured via environment (`AI_MODEL`/`AI_API_KEY`) | PASS — prototype's hardcoded keys must NOT be copied; production uses `settings.AI_MODEL`/`settings.AI_API_KEY` |
| Debit/Credit sign convention is a parameterized `reconciliation_type` ("bank"/"vendor"), never hardcoded | PASS — the assessor already parameterizes it; the plan exposes it to the agent as an input, defaulting to "bank" |
| SQLModel removed; raw asyncpg for CockroachDB queries | PASS — this feature touches no database code |
| Backend cancellation handling catches `asyncio.CancelledError` explicitly | PASS — existing `detect_structure` already handles it; the evaluator call must not swallow it |
| Pydantic settings tolerate undeclared env vars (`extra = "ignore"`) | PASS — no config changes planned |

No violations; complexity tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-agentic-structure-extraction/
├── spec.md              # Feature specification (/sp.specify + /sp.clarify output)
├── plan.md              # This file (/sp.plan output)
├── research.md          # Phase 0 output (assessor/prototype analysis)
├── data-model.md        # Phase 1 output (output contract changes)
├── quickstart.md        # Phase 1 output (local verification)
├── contracts/           # Phase 1 output (output block contract)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   └── ai_structure_detector.py   # PRIMARY CHANGE: 4-tool agent + evaluation loop
│   └── utils/
│       └── structure_assessor.py      # REUSED UNCHANGED: assess_pdf_structure (Saghir/Kabir/Ihsan)
├── tests/
│   ├── test.py                        # PROTOTYPE REFERENCE (unchanged)
│   └── (existing test suite)          # reused for regression
└── (config.py, ai_routes.py)          # UNCHANGED: route already calls detect_structure()
```

**Structure Decision**: Backend service upgrade inside the existing `backend/src/services/` layout. All changes land in `ai_structure_detector.py`; `structure_assessor.py` is already in production and is consumed as-is. The route (`ai_routes.py`) already threads `sheetName` and `request_id` into `detect_structure()`, so no route changes are needed.

## Phase 0 — Research Findings

- **Prototype agent (test.py)**: builds an `Agent` with 4 tools — `read_excel`, `read_pdf`, `read_pdf_words` (both pages in one call), and `assess_structure` (calls `assess_pdf_structure` with `use_ihsan=True` and returns the JSON verdict). Instructions require the agent to call `assess_structure` before emitting the final output block, iterate on failure (bounded by `max_turns=25`), read the Opening Balance from the statement header, and pass a `reconciliation_type`. Output contract adds `opening_balance_pdf` (optional float).
- **Production detector (ai_structure_detector.py)**: has 3 tools (no `assess_structure`), no opening balance in the contract, no reconciliation type, no self-evaluation loop. It already has: `build_agent_tools(pdf_path, excel_path, sheet_name)` closures, `AGENT_INSTRUCTIONS`, `build_agent()`, `parse_output_block()`, `_validate_detected_structure()`, `detect_structure()` with 3-attempt retry + cancellation registry integration, `_configure_tracing()`.
- **Assessor engine (structure_assessor.py)**: production-ready `assess_pdf_structure(pdf_path, columns, header_top, rows_dropped, boundaries, band_top, date_pattern, name_based, opening_balance, reconciliation_type, run_kabir, use_assessor_llm, use_ihsan, request_id)` — already wired for cancellation via `request_id`, already tolerates the 50.0 balance tolerance, already supports sparse balances, already supports bank/vendor conventions, already returns `overall_pass` + `issues`/`suggestions`/`kabir_check`/`ihsan_check`. This is exactly the "3 Evaluation marks" the spec describes, ready to reuse.
- **Gap summary**: the transfer is: (a) add the `assess_structure` tool closure to `build_agent_tools`, (b) add opening balance + reconciliation type to the output model/instructions/validation, (c) extend `AGENT_INSTRUCTIONS` with the evaluation-first workflow (mirror test.py), (d) keep the existing outer retry loop, adding evaluator-failure → friendly retry (FR-008), (e) thread `reconciliation_type` from the route (default "bank") into the tool.

## Phase 1 — Design

### Data Model / Output Contract

`FileStructureOutput` gains one optional field (backward-compatible; the extractors never read it):

```python
class FileStructureOutput(BaseModel):
    # ...existing fields unchanged...
    opening_balance_pdf: Optional[float] = None   # NEW - read from statement header
```

`reconciliation_type` is NOT added to the output model — it is an input the agent passes to the `assess_structure` tool (spec FR-006). The route threads it into `detect_structure()` as a new optional parameter defaulting to `"bank"`; the frontend does not surface it today (verified), so the default keeps existing behavior.

### Agent Construction

- `build_agent_tools(pdf_path, excel_path, sheet_name)` gains a 4th tool `assess_structure(...)` mirroring the prototype: calls `assess_pdf_structure(pdf_path=pdf_path, ..., opening_balance=..., reconciliation_type=..., use_ihsan=True)` and returns the JSON verdict. Because the tool is a closure over the uploaded `pdf_path`, it works in production exactly like the prototype's hardcoded-path version.
- The tool MUST be passed `request_id` when available so the assessor's nested LLM calls honor cancellation (the engine already accepts it).
- `AGENT_INSTRUCTIONS` is extended to the prototype's workflow: read files with the 3 reading tools → derive structure → call `assess_structure` with the opening balance + reconciliation type → on `overall_pass: false`, read `issues`/`suggestions`/`cumulative_check.first_mismatch_row`/`kabir_check`/`ihsan_check` and revise → emit the `[output]` block only after all three checks pass (or a bounded attempt count with no arithmetic failure). This is "constant reiteration for tip-top structure extraction."
- Opening Balance guidance mirrors the prototype: read from the upper region of page 1; pass to the tool; omit (null) when absent — the evaluator still runs (FR-005).
- Reconciliation type guidance mirrors the prototype: pick "bank" (default) or "vendor"; the tool's docstring explains the inverted sign roles.

### Failure Behavior (FR-008)

- Keep the existing 3-attempt outer retry in `detect_structure()`.
- Inside each attempt, if `assess_structure` raises (model unreachable, malformed verdict, evaluator crash), treat it as a failed attempt: `last_error = e; continue` — the existing loop already surfaces `AIDetectionError(retries_used=...)` → route returns 422 with `FRIENDLY_RETRY_MESSAGE`. This satisfies "fail gracefully, never emit an unverified structure."
- If the user cancels mid-evaluation, `asyncio.CancelledError` must propagate (the assessor already receives `request_id`; the existing `except asyncio.CancelledError: raise` in `detect_structure` handles it → route returns 499).
- The evaluator's INCONCLUSIVE cases (e.g., no closing balance printed) already defer to the deterministic checks inside the assessor — no production change needed (FR-010).

### Route Integration

- `ai_routes.py` unchanged except (optionally) threading a `reconciliationType` Form field with default `"bank"` into `detect_structure(...)` — small, non-breaking, and matches FR-006's "expose the statement type to the agent as an input." Frontend remains untouched (no selector today); the default preserves behavior.
- `ai_metadata.detected_structure` in the success response already emits `structure.columns_pdf` etc.; `opening_balance_pdf` can be added to that payload for observability without breaking the frontend.

### Contracts

- `contracts/` documents the `[output]` block contract (unchanged fields + optional `opening_balance_pdf`) and the `assess_structure` tool contract (inputs, verdict JSON, tolerance 50.0, INCONCLUSIVE semantics).

## Phase 2 — Task Breakdown (handled by /sp.tasks)

1. Add `assess_structure` tool closure + `request_id` plumbing to `build_agent_tools`.
2. Add `opening_balance_pdf` to `FileStructureOutput` + `parse_output_block` passthrough.
3. Extend `AGENT_INSTRUCTIONS` with evaluation-first workflow + opening balance + reconciliation type.
4. Thread `reconciliation_type` (default "bank") through `detect_structure` and the route (optional Form field).
5. Wire evaluator failures into the existing retry loop (friendly retry, no unverified emission).
6. Add `opening_balance_pdf` (and reconciliation type) to `ai_metadata.detected_structure` for observability.
7. Verify: run the production detector against the prototype's sample files; confirm the agent iterates, `overall_pass` gates the output, and the 3-attempt/499/422 behaviors hold.
8. Regression: existing `/reconcile-ai` flow and manual `/karwai` flow behave identically.

## Risks & Mitigations

- **Agent cost/latency**: evaluation adds LLM turns per attempt (bounded by `max_turns=25` + the existing 3-attempt outer loop). Mitigation: the assessor short-circuits — Kabir runs only after Saghir passes, Ihsan only after both — and clear-cut cases spend no LLM call in the adjudicate tier. SC-004 (2-minute bound) is preserved by the same bound that already exists.
- **Credential hygiene**: the prototype hardcodes keys; production must NOT copy them — `settings.AI_MODEL`/`AI_API_KEY` drive the model (FR-010). Flag in tasks.
- **Cancellation correctness**: the assessor's nested LLM runs must honor `request_id`; passing it into the tool closure and re-raising `CancelledError` preserves the 499 path.
- **Output-contract drift**: the extractors ignore `opening_balance_pdf` (verified), so the addition is non-breaking; still covered by the regression check.

## Success Criteria Traceability

| SC | Plan coverage |
|----|---------------|
| SC-001 (100% of finalized structures pass all 3 checks) | Evaluator gate before emission; verify against test set |
| SC-002 (0% user intervention) | Same user-facing flow; no new inputs |
| SC-003 (beyond-current-bank layouts extracted correctly) | 4-tool agent + evaluation loop; verify on sample files |
| SC-004 (≤2 min end-to-end) | Existing bound + assessor short-circuit; verify timing |
| SC-005 (failure behavior preserved) | Retry/422/499 unchanged; evaluator failure → friendly retry |
| SC-006 (manual flow unchanged) | No changes to `/karwai`; regression check |
