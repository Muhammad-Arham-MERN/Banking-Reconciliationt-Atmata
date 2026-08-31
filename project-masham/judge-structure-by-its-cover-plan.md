# Implementation Plan: Judge Structure by its Cover

> Status: **PLAN — approved 2026-08-28. No code changed yet.**
> Location: `project-masham/judge-structure-by-its-cover-plan.md`
> Branch: `007-ai-reconciler-advisor` (working tree has uncommitted feature-007 work — keep it untouched)
> Date: 2026-08-28

---

## 1. What this document is

This is the complete, detailed implementation guide for the **"Judge Structure by
its Cover"** agent — a small agent that sits *inside* the main extraction agent as
a **tool** (OpenAI Agents SDK *agents-as-tools* pattern) and short-circuits the
expensive full structure-detection flow when the uploaded PDF belongs to a bank or
vendor whose structure was already extracted and persisted.

It captures:

- everything learned about the current extraction pipeline and its consumers,
- the clarifying questions asked and the answers chosen (including the
  architecture pivot to **Agent as Tool**),
- the exact new logic, edge cases, and known limitations,
- the file-by-file implementation steps,
- a verification plan.

---

## 2. The current implementation (what exists today)

The AI reconciliation flow (`POST /reconcile-ai` in `backend/src/api/ai_routes.py`)
does:

```
upload PDF (bank statement) + Excel (company ledger)
        │
        ▼
detect_structure()  ── backend/src/services/ai_structure_detector.py
  • main agent "Excel/PDF extraction agent" (OpenAI Agents SDK, LiteLLM/Gemini)
  • tools: read_excel, read_pdf, read_pdf_words, assess_structure
  • agent reads the file layout from scratch, proposes columns/boundaries/
    band_top/header_top/date_pattern/roles, iterates with assess_structure
    until Saghir+Kabir+Ihsan pass (output guardrail enforces this)
  • second agent (output formatter) re-emits the canonical ~~~ [output] ~~~ block
  • parse_output_block → FileStructureOutput
        │
        ▼
deterministic extraction (AIPDFProcessor + AIExcelProcessor, concurrent)
        │
        ▼
ReconciliationService.reconcile() → discrepancies → frontend
```

### 2.1 Why this is slow and expensive

The main detection agent must, on **every** upload, rediscover the entire layout
from scratch: page geometry, header line, band top, column boundaries, date
pattern, opening balance, and column roles — then run the full
Saghir/Kabir/Ihsan assessment loop (which itself can spawn nested LLM calls for
the Kabir adjudicator and the Ihsan closing-balance reader), with up to 3
LLM-failure retries and 3 guardrail retries. A big file can take 300+ seconds;
even small files take ~100+ seconds.

### 2.2 Key existing pieces this feature reuses

| Piece | Location | Role here |
|---|---|---|
| `detect_structure()` | `backend/src/services/ai_structure_detector.py` | The main agent flow we short-circuit |
| `build_agent_tools()` | same file | Where the Judge tool gets registered |
| `AGENT_INSTRUCTIONS` | same file | Must be updated so the main agent calls the Judge **first** |
| `assess_structure` tool | same file (closure in `build_agent_tools`) | Re-validates a stored structure against the **current** upload; gains `entity_name` param + persistence hook |
| `assess_pdf_structure()` | `backend/src/utils/structure_assessor.py` | The deterministic Saghir/Kabir/Ihsan gate the tool calls |
| `FileStructureOutput` | `backend/src/services/ai_structure_detector.py` | The persisted structure contract (stored in DB as JSONB) |
| `DatabaseService` (raw asyncpg) | `backend/src/services/db_service.py` | CockroachDB access (project taste: no SQLModel, raw asyncpg) |
| `db_migrations.py` | `backend/src/models/db_migrations.py` | Where the new table DDL is added |
| `_build_model()` / `_configure_tracing()` | `ai_structure_detector.py`, `advisor_service.py` | The model wiring the Judge agent mirrors |
| `parse_output_block` | `ai_structure_detector.py` | Unchanged — the output formatter path still produces the canonical block |
| `max_turns=25` | all `Runner.run*` call sites | Standing convention — applies to the Judge's nested runs too |

---

## 3. Architecture decision: Agent as Tool (confirmed)

**The Judge is NOT a separate pre-step.** Per the user's direction (and the
[OpenAI Agents SDK agents-as-tools docs](https://openai.github.io/openai-agents-python/tools/#agents-as-tools)),
the Judge agent is registered as **a tool on the main extraction agent** via
`judge_agent.as_tool(tool_name=..., tool_description=...)`. The main agent is
instructed to call it **first and foremost** to assess the PDF structure
prehand instead of starting from scratch.

### 3.1 Why this kills the parsing problem

The Judge's final response is returned to the main agent **as a tool result**,
not parsed by our code. The main agent (an LLM) reads it directly and decides:

- if the result contains **structure extraction data** (known bank/vendor) → it
  re-validates that structure against the current upload and uses it,
- if the result says **no data / new file** → it proceeds with full detection.

No `~~~ [output] ~~~` block, no `parse_output_block` variant, no decision
branches in deterministic code. The orchestrator LLM absorbs the verdict — the
exact behavior the user asked for ("the agent returns response as either
'structure extraction data' or 'no data' ... This completely kills out the issue
of output parsing and extraction").

### 3.2 Nested-run semantics

- `judge_agent.as_tool(tool_name="judge_structure_by_cover", tool_description=...)`
  runs the Judge as a nested `Runner.run` inside the main run.
- The nested agent gets its own tools (`read_pdf_first_lines`,
  `lookup_pdf_structure`) bound to the uploaded `pdf_path` + `reconciliation_type`
  via closures, exactly like the main agent's existing tools.
- Nested runs carry `max_turns=25` (standing convention).
- Cancellation: the main `stream.cancel()` propagates to the nested run (same
  `Run`); the Judge also checks the shared `processing_cancellation` registry
  (`request_id`) so a client Stop halts it mid-nested-run.

---

## 4. The Judge agent ("Judge Structure by its Cover")

### 4.1 Purpose

Given a PDF and the reconciliation type (`bank` | `vendor`), answer **"whose
file is this?"** by reading the first ~10 lines of the PDF, then decide whether
that entity's PDF structure is **already known** in the database. Return either:

- the **stored structure data** (when known), or
- a clear **"no data / new entity"** answer (when unknown or unidentifiable).

### 4.2 Tools (exactly 2, per the user's spec)

**Tool 1 — `read_pdf_first_lines`** (pdf extraction tool)
- Plain readable **text lines** of the PDF (user-confirmed: "plain readable text
  from our trusted pdfplumber"), **not** word geometry — the Judge only needs to
  READ a name, not locate columns (same principle as the Ihsan closing-balance
  reader).
- Returns the first ~10 visual text lines of **page 1** (where bank/vendor
  names and statement headers live), paged via `drop`/`lines` (taste: tool
  outputs kept small + pageable, e.g. `drop=0, lines=10`).
- Implemented with pdfplumber `page.extract_words()` grouped into visual lines
  by `top`, rendered as `" ".join(words)` per line (no coordinates).

**Tool 2 — `lookup_pdf_structure`** (pdf structures data storage access)
- Two modes via one optional argument `entity_name`:
  - `entity_name=None` → returns the **compact list** of known entities:
    `name + entity_type` per row (e.g. `"Askari Bank (bank), Meezan Bank (bank),
    Faisal Cement (vendor), ..."`). Keeps context tiny when the DB has many
    profiles (taste: context-bloat control).
  - `entity_name="askari bank"` → returns the **full stored structure** for that
    entity (every field of `FileStructureOutput` as JSON), or
    `"No profile found for ..."` when absent.
- Matching is by **normalized name** (lowercased, punctuation stripped,
  whitespace collapsed) + entity type — user-confirmed so `"askari bank"`
  matches `"Askari Bank"`.
- Reads via the new `PdfStructureStore` service (Section 7).

### 4.3 Judge instructions (draft contract)

```
You are "Judge Structure by its Cover", the first stop for every uploaded PDF in
a Banking Reconciliation System.

Your ONLY job: identify whose PDF this is, and whether the system already knows
its structure.

Steps:
1. Call read_pdf_first_lines (page 1's first ~10 lines) and read the bank/vendor
   name from the statement header / letterhead. This is a "<type>" statement
   (type = bank | vendor — passed to you).
2. If the PDF carries NO identifiable name (some vendor PDFs have none), do NOT
   guess. Stop and answer "no data".
3. Call lookup_pdf_structure with NO argument to see the known entities.
4. If the entity you identified is in that list, call lookup_pdf_structure with
   the entity name to fetch its full stored structure, and return it.
5. If the entity is NOT in the list (or you are unsure), answer "no data".

OUTPUT RULES:
- KNOWN: return the full structure JSON exactly as lookup_pdf_structure returned
  it, prefixed with "KNOWN_ENTITY <name>:".
- UNKNOWN/UNIDENTIFIABLE: return exactly "NO_DATA" followed by a one-line reason.
- Nothing before/after. No prose.
```

### 4.4 Judge model + tracing

- Same model family as the existing AI flows (`settings.AI_MODEL` /
  `AI_API_KEY` via `_build_model()`), `_configure_tracing()` enabled — the
  user's standing preference: same infrastructure, tracing ON with
  `AI_TRACING_API_KEY`.
- `max_turns=25` on the nested run.

### 4.5 Judge failure behavior (fail-open)

- If the nested Judge run raises (model/transport error), the SDK returns the
  error as the tool result to the main agent. `AGENT_INSTRUCTIONS` will tell the
  main agent: *"If the judge tool errors or returns garbage, proceed with full
  structure detection from scratch."* The Judge is an optimization — it must
  never block the run.
- If the DB is unreachable, `lookup_pdf_structure` returns an empty list +
  a note (fail-open) rather than raising.

---

## 5. The two paths (what the main agent does)

### 5.1 Path A — KNOWN entity (the speed win)

```
main agent calls judge_structure_by_cover
        │
        ▼
Judge returns KNOWN_ENTITY Askari Bank + full stored structure
        │
        ▼
main agent takes the stored structure values
        │
        ▼
calls assess_structure(columns_pdf=..., header_top_pdf=..., ...,
                       reconciliation_type=..., entity_name="Askari Bank")
        │                          │
        │   overall_pass: true     │  overall_pass: false
        ▼                          ▼
structure validated for THIS      stored structure no longer fits THIS file
upload → agent emits [output]     → agent fixes it (re-calls assess_structure),
block → formatter → parse         and/or falls back to full detection from
→ extraction (huge time saved)     scratch; the corrected passing structure
                                  is upserted to the store (Section 6.2)
```

- **Re-validation is confirmed by the user**: even a known structure is run
  through the assessor against the **current** upload before extraction, so a
  bank that changed its layout can never silently produce garbage rows.
- Cost in the happy path: 1 nested Judge run (2 cheap tool calls) + 1
  assess_structure call — vs. the current full multi-turn detection + nested
  adjudicator/Ihsan LLM calls. This is the entire point of the feature.

### 5.2 Path B — UNKNOWN / NEW entity (the learning path)

```
Judge returns NO_DATA (new vendor, or unidentifiable PDF)
        │
        ▼
main agent does FULL detection from scratch (exactly today's flow)
        │
        ▼
calls assess_structure(..., entity_name="Dilbar Electronics")
        │
        ▼
Saghir + Kabir + Ihsan all pass  →  the assess_structure tool ALSO upserts the
                                    structure to the DB keyed by
                                    (normalized name, entity_type)
        │
        ▼
agent emits [output] block → formatter → parse → extraction (unchanged)
```

- The main agent passes the entity name it read from the PDF into
  `assess_structure`; if it could **not** find any name, it omits the parameter
  (`entity_name=None`) and **no persistence happens** — exactly the user's
  spec: "if the main extraction agent could not find any proper name of the
  company of this pdf then it will skip this parameter".

---

## 6. Changes to the structure assessor flow (item 6 of the spec)

### 6.1 `assess_structure` tool (in `ai_structure_detector.py`) — new params

The tool closure gains:

- `entity_name: Optional[str] = None` — the bank/vendor name the agent read from
  the PDF (the spec's "Bank name/Vendor Name"). `reconciliation_type` already
  exists ("Vendor/Bank").

These are threaded into `assess_pdf_structure(...)` (new optional params,
backward-compatible — defaults `None`/`"bank"` so existing callers/tests keep
working).

### 6.2 Persistence hook (in the tool, not in the utils module)

`structure_assessor.py` stays a **pure, deterministic utils module with no DB
access** (keeps it unit-testable and importable anywhere). Instead, the
persistence lives in the `assess_structure` **tool closure** in
`ai_structure_detector.py`:

```
assessment = assess_pdf_structure(pdf_path, ..., entity_name=entity_name)
verdict_holder["last"] = assessment
if assessment["overall_pass"] and entity_name:
    await upsert_profile(entity_name=entity_name,
                         entity_type=reconciliation_type,
                         structure=FileStructureOutput(...))   # fire-and-log
return json.dumps(assessment)
```

- Fires on **any** all-pass with a name — from either Path A (a corrected
  known-entity structure, keeping the store fresh when a bank changes layout)
  or Path B (a brand-new entity).
- Upsert is **fail-open**: if the DB write errors, log a warning and continue —
  a store failure must never fail the reconciliation.
- `entity_type` = `reconciliation_type` ("bank" | "vendor") — same concept
  (which books the statement belongs to).

### 6.3 `assess_pdf_structure()` (in `structure_assessor.py`) — signature only

- New optional params: `entity_name: Optional[str] = None` (and it already has
  `reconciliation_type: str = "bank"`).
- The params are **accepted and echoed** in the assessment dict (so the tool can
  read them / diagnostics show them) but the utils module performs **no** DB
  writes. Purely a plumbing change; the verdict logic is untouched.
- Update the `assess_structure` tool docstring + `AGENT_INSTRUCTIONS` to tell
  the agent: *pass `entity_name` = the bank/vendor name you read from the PDF
  header; omit it when the PDF has no identifiable name* (and explain why:
  only a named, fully-passing structure gets persisted for future runs).

---

## 7. Data model & storage (CockroachDB)

### 7.1 New table — `pdf_structure_profiles`

```sql
CREATE TABLE IF NOT EXISTS pdf_structure_profiles (
    id                     SERIAL PRIMARY KEY,
    entity_name            VARCHAR(255) NOT NULL,
    entity_name_normalized VARCHAR(255) NOT NULL,
    entity_type            VARCHAR(16)  NOT NULL,   -- 'bank' | 'vendor'
    structure              JSONB        NOT NULL,   -- full FileStructureOutput
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pdf_structure_profile
    ON pdf_structure_profiles(entity_name_normalized, entity_type);
CREATE INDEX IF NOT EXISTS idx_pdf_structure_profile_type
    ON pdf_structure_profiles(entity_type);
```

- **Key**: `(entity_name_normalized, entity_type)` — normalized-name matching
  (user-confirmed). `entity_name` keeps the human-readable form for display.
- `structure` JSONB stores the full `FileStructureOutput` (columns_pdf,
  columns_excel, header_top_pdf, band_top_pdf, rows_dropped_pdf,
  column_boundaries_pdf, date_pattern_pdf, opening_balance_pdf, all role
  columns, reconciliation_type) — the exact fields `assess_structure` consumes
  and the extractor needs.
- Added to `MIGRATIONS` in `backend/src/models/db_migrations.py` (existing
  convention: ordered list of `CREATE ... IF NOT EXISTS` statements).

### 7.2 New service — `backend/src/services/pdf_structure_store.py`

Raw asyncpg via the existing `DatabaseService` (project taste: no SQLModel).

```
normalize_entity_name(name) -> str
  # lowercase, strip non-alphanumeric, collapse whitespace
  # (same _normalize pattern as ai_pdf_processor.py)

async list_profiles(entity_type: str | None = None) -> list[dict]
  # compact: [{entity_name, entity_type}]  (context-bloat control)

async get_profile(entity_name: str, entity_type: str) -> dict | None
  # full row: {entity_name, entity_type, structure (dict), updated_at}
  # matched by normalized name + type

async upsert_profile(entity_name, entity_type, structure: dict) -> None
  # INSERT ... ON CONFLICT (entity_name_normalized, entity_type)
  # DO UPDATE SET structure = EXCLUDED.structure, updated_at = NOW()
```

All three methods **swallow DB errors and return the fail-open default**
(empty list / None / no-op) — the Judge and the persistence hook must degrade
gracefully, never crash the run.

### 7.3 No frontend changes

This feature is backend-only. `/reconcile-ai`'s request/response contract is
unchanged; the frontend sees the same flow (and, transparently, faster runs).

---

## 8. File-by-file implementation steps

### 8.1 `backend/src/models/db_migrations.py` (EDIT)

- Add `CREATE_PDF_STRUCTURE_PROFILES`, `CREATE_UQ_PDF_STRUCTURE_PROFILE`,
  `CREATE_IDX_PDF_STRUCTURE_PROFILE_TYPE` (Section 7.1).
- Append all three to `MIGRATIONS`.

### 8.2 `backend/src/services/pdf_structure_store.py` (NEW)

- Module with the Bismillah header/footer + crux markers.
- `normalize_entity_name()`, `PdfStructureStore` class wrapping
  `db_service` (or module-level async functions matching the `db_service`
  convention — `list_profiles` / `get_profile` / `upsert_profile`).
- Fail-open error handling (log + return default).

### 8.3 `backend/src/services/judge_structure_service.py` (NEW)

- `build_judge_agent(pdf_path, reconciliation_type, request_id=None) -> Agent`
  - instructions per Section 4.3,
  - model via `_build_model()` (mirror `advisor_service.py`/`ai_structure_detector.py`),
  - tools: `read_pdf_first_lines` + `lookup_pdf_structure` (Section 4.2),
  - `_configure_tracing()`.
- `judge_agent.as_tool(tool_name="judge_structure_by_cover",
  tool_description="...")` — a module-level helper `build_judge_tool(...)` the
  detector imports.
- Cancellation: register the nested run against `request_id` in the
  `processing_cancellation` registry where possible; the main stream's cancel
  propagates.

### 8.4 `backend/src/services/ai_structure_detector.py` (EDIT — the core wiring)

1. **`build_agent_tools(...)` / `build_agent(...)`**:
   - accept the `reconciliation_type` (already does) + build the Judge tool,
   - append `judge_structure_by_cover` to the main agent's `tools` list,
   - pass `request_id` through so the nested Judge honors cancellation.
2. **`assess_structure` tool**:
   - add `entity_name: Optional[str] = None` param,
   - thread it into `assess_pdf_structure(...)`,
   - after the verdict, on `overall_pass` + `entity_name` → fire-and-log
     `upsert_profile(...)` (Section 6.2),
   - update the tool docstring (explain `entity_name` + persistence).
3. **`AGENT_INSTRUCTIONS`** — add a new opening section (the contract change
   MUST ship with the instruction change, per the standing taste rule):
   - "FIRST, before any file inspection, call `judge_structure_by_cover`. It
     returns either a known structure (KNOWN_ENTITY ...) or NO_DATA."
   - Path A: "If it returns a known structure, DO NOT re-detect from scratch.
     Take those values, call assess_structure with them + the entity name to
     verify against THIS file. If it passes, emit the [output] block with those
     values. If it fails, fix the structure and re-validate, or fall back to
     full detection."
   - Path B: "If NO_DATA (new file or judge error), detect the structure from
     scratch as usual."
   - "When you identify the bank/vendor name from the PDF, pass it as
     `entity_name` to assess_structure. Omit it only when the PDF has no
     identifiable name."
4. **`detect_structure(...)`**: no signature change (it already has
   `pdf_path`, `reconciliation_type`, `request_id`). The Judge is built inside
   `build_agent` per attempt. Guardrail retries still replay the full
   conversation (the Judge result is part of it, so it isn't re-invoked unless
   the agent chooses to).

### 8.5 `backend/src/utils/structure_assessor.py` (EDIT — minimal)

- `assess_pdf_structure(...)`: add `entity_name: Optional[str] = None` optional
  param; echo it in the returned dict (e.g. `"entity_name": entity_name`).
- **No DB access, no verdict-logic change** — pure plumbing so the tool can
  carry the name. All existing checks (Saghir/Kabir/Ihsan), diagnostics, and the
  return shape stay byte-identical apart from the new echoed field.

### 8.6 `backend/src/services/ai_routes.py` / others (NO CHANGE)

- `/reconcile-ai` is untouched (it just calls `detect_structure`, which now
  carries the Judge internally).
- No new endpoints; no auth-middleware changes.

---

## 9. Verification plan

1. `python -m py_compile` on every edited/created file.
2. **Store layer** (standalone, DB up): `upsert_profile("Askari Bank", "bank",
   {...})` → `list_profiles()` shows it → `get_profile("askari bank", "bank")`
   returns it → `upsert_profile` with a different structure updates in place
   (ON CONFLICT) → `get_profile("askari", "bank")` still matches (normalized).
3. **Judge unit behavior** (mock tools or a real small PDF):
   - reads the first ~10 lines and identifies the bank name,
   - returns KNOWN_ENTITY + structure when the entity exists in the store,
   - returns NO_DATA when the entity is absent,
   - returns NO_DATA on an unidentifiable PDF (no name),
   - `lookup_pdf_structure()` compact list vs `lookup_pdf_structure("name")`
     full structure.
4. **Path A end-to-end**: seed the store with the known MCB structure
   (`getjobid4620060.pdf`, from `project-masham/file_dhancha.md`), run
   `/reconcile-ai`, confirm: the main agent calls the Judge first, uses the
   stored structure, re-validates with `assess_structure` (passes), and the run
   completes **significantly faster** than a cold detect (compare
   `ai_detection_time_ms`).
5. **Path A regression**: seed a *wrong* structure for an entity (or point a
   known structure at a different bank's PDF) → the assessor re-validation
   FAILS → the agent falls back to full detection and the run still completes
   correctly.
6. **Path B end-to-end**: upload a brand-new vendor PDF (e.g. a new ledger) →
   Judge returns NO_DATA → full detection → agent passes `entity_name` →
   on all-pass the profile is upserted → a second upload of the same vendor now
   takes Path A.
7. **Name-less PDF**: upload a PDF with no identifiable company name → agent
   omits `entity_name` → no profile written, flow completes normally.
8. **Fail-open**: stop the DB (or point at a bad DSN) → Judge still runs, sees
   an empty list, returns NO_DATA → full detection proceeds; no 500s.
9. Frontend: run a normal reconciliation through the UI — unchanged behavior,
   faster detection on known files.

---

## 10. Known limitations (honest trade-offs)

- **Judge is only as good as its identification**: a PDF whose first 10 lines
  don't carry the entity name yields NO_DATA → full detection (correct, just no
  speedup). We intentionally never guess (user spec).
- **Stored structure can go stale**: a bank that changes its layout produces a
  failed re-validation on Path A → the agent fixes it and the upsert updates the
  store. Cost: one slower run for that entity, then speed returns.
- **Normalized-name collisions**: two distinct entities with identical
  normalized names (rare) collide on the unique key. Accepted; the unique key
  is per the user's choice.
- **Nested LLM cost**: the Judge adds one small nested run even on Path B (new
  files). That cost is ~2 tool calls + 1 short LLM turn — far smaller than the
  full detection it can bypass, and it's fail-open.
- **DB write is fire-and-log**: a failed upsert loses the learning for that run
  (the structure is not persisted) but never fails the reconciliation.

---

## 11. Open items before implementation

1. **Judge output format wording**: exact `KNOWN_ENTITY <name>:` / `NO_DATA`
   sentinel strings (Section 4.3) — confirm or adjust at implementation start.
2. **Tests**: feature 007 explicitly skipped pytest ("dont write any tests");
   this plan keeps verification manual/scripted (Section 9). Confirm whether
   any pytest coverage is wanted for the store layer.
3. **`entity_type` vs `reconciliation_type`**: one column storing
   `"bank" | "vendor"` (this plan collapses them; they are the same concept).
4. **Store service shape**: class wrapper vs module-level functions matching
   `db_service.py` — decide at implementation (recommend module-level functions
   in a `pdf_structure_store.py` module, matching the repo's flat service
   convention).

---

## 12. Summary

"Judge Structure by its Cover" is a small nested agent exposed to the main
extraction agent as an **agent-as-tool**. It reads the first ~10 lines of the
uploaded PDF, identifies the bank/vendor, looks up the entity's previously
extracted structure in a new CockroachDB table (`pdf_structure_profiles`,
keyed by normalized name + bank/vendor type), and returns either the stored
structure or "no data". The main agent then either re-validates the stored
structure with the existing `assess_structure` tool (huge speed win) or does
full detection from scratch. On any fully-passing, named structure, the tool
persists it for future runs — so the system learns every new bank/vendor it
successfully extracts. Backend-only, no contract changes, fail-open everywhere:
the Judge accelerates but can never break the existing flow.
