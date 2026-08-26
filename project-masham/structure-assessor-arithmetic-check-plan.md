# Structure Assessor — Arithmetic Balance-Check Reimplementation Plan

> Status: **PLAN — awaiting approval. No code has been changed yet.**
> Location: `project-masham/structure-assessor-arithmetic-check-plan.md`
> Branch: `005-ai-data-extraction`

---

## 1. What this document is

This is the complete, detailed plan for reimplementing the PDF structure
assessment logic in `backend/tests/structure_assessor.py`. It captures:

- everything learned about the current implementation and its consumers,
- the four clarifying questions I asked and the answers chosen,
- the exact new logic, edge cases, and known limitations,
- the file-by-file implementation steps,
- a test/verification plan.

---

## 2. The current implementation (what exists today)

`backend/tests/structure_assessor.py` is a **deterministic, zero-LLM scoring
tool** that tells the AI agent how well its proposed PDF structure would
perform in the production extractor.

### 2.1 What it currently does

1. Runs the **same extraction logic as production**
   (`extract_pdf_words`, mirroring `backend/src/services/ai_pdf_processor.py::extract_pdf`):
   - groups words into visual lines by `top` coordinate,
   - filters by `band_top` (must be at/below the band) and `header_top` (must
     be below the header line + tolerance),
   - slices words into columns by horizontal center against `column_boundaries`,
   - keeps rows whose first-column marker matches `date_pattern`.
2. Builds an **independent "raw table rows" baseline**
   (`extract_raw_table_rows`) using pdfplumber's own `find_tables()` /
   `extract_table()` and only the page structural properties
   (`band_top`, `header_top`, `rows_dropped`) — NOT the LLM's
   `columns`/`boundaries`.
3. **Compares the two row counts**:
   `delta = llm_row_count - raw_row_count`; `|delta| <= 3` → OK, else MISMATCH.
4. Produces diagnostics:
   - per-page `in_band_lines` / `date_matching_lines` / `row_count`,
   - per-column fill rates (catches bad boundaries slicing cells away),
   - column-name → physical-slice mapping via the header line (name-based mode),
   - a 0–100 score rewarding date-column fill and penalizing empty cells,
   - `issues` and `suggestions` lists for the agent to act on.
5. Renders it all via `_pretty()` and via the raw dict
   (`assess_pdf_structure`).

### 2.2 Known consumers (all confirmed by code reading)

| Consumer | What it does |
|---|---|
| `backend/tests/validate_structures.py` | Imports `_pretty`, `assess_pdf_structure` and validates 3 known statements (Soneri, MCB, Meezan eStatement) against their known-good structures. |
| `project-masham/file_dhancha.md` | Documents the three derived structures and their validation table (rows extracted vs raw table rows vs delta vs score). |
| The AI agent workflow (manual) | The agent proposes a structure, the human runs the assessor, reads the verdict, and iterates. **It is NOT currently a registered `@tool` in `ai_structure_detector.py`.** |

### 2.3 Why the old comparison was inaccurate

The raw-row-count comparison is a weak proxy for correctness:

- pdfplumber's `extract_table()` is **flaky on statements without ruled lines,
  with merged cells, or with wrapped/continuation sub-lines** — the raw count
  itself is unreliable ground truth.
- A structure can extract the **right number of rows with wrong data**
  (mis-sliced columns, wrong signs) and still "pass".
- The ±3 tolerance is arbitrary; a 1-row structural error passes silently.
- The check says nothing about whether the **amounts** are correct.

This is why the results were inaccurate: it validated row *quantity* against
an unreliable baseline, not data *correctness* against a self-consistent
source of truth.

---

## 3. The new logic (what we are building)

### 3.1 Core idea

The bank statement is arithmetically self-consistent: every transaction
moves a running balance. So instead of comparing against pdfplumber's table
detection, we validate the **data itself**:

1. Extract rows with the agent's proposed structure (same as today).
2. **Merge Debit and Credit into one signed stream**:
   - Debit → **negative** (`−`),
   - Credit → **positive** (`+`).
   - (This resolves the wording contradiction in the request: "debited
     values are positive (-ve)" conflicts with "Debits (-ve)". We use
     standard accounting / our own bank-statement semantics:
     **positive = credit = money in, negative = debit = money out** —
     confirmed by the user.)
3. The agent passes the **Opening Balance** it read from the statement
   header (the figure from which debits are subtracted and to which credits
   are added; wording may differ per bank — "Opening Balance",
   "B/F", "Balance Brought Forward", etc.).
4. Compute:
   - `final_from_opening = opening_balance + Σ(credits) − Σ(debits)`
   - **Per-row cumulative sweep** (primary check): for each transaction row
     in order, `running += signed_amount`, and compare `running` against the
     row's **Cumulative Balance column** value.
   - **Final check** (secondary): compare `final_from_opening` against the
     **last** Cumulative Balance value in the extracted rows.
5. Pass / Fail verdict:
   - PASS if the per-row sweep matches every cumulative value **and**
     `|final_from_opening − last_cumulative| <= tolerance`.
   - FAIL otherwise, with diagnostics pointing at the first row where the
     running balance diverges (that pinpoints the first missed/misparsed row).

### 3.2 Why the per-row sweep is the primary check

The opening + total check alone has a **false-pass case**: if the structure
drops the *final* transaction row, the second-to-last cumulative still equals
`opening + Σ(all extracted rows)` by construction, so the final check passes
even though a row is missing. Checking **every** cumulative value (same
arithmetic, per row) catches:

- missing interior rows (running diverges at that point and never re-syncs),
- wrong/mis-sliced amounts,
- a Debit/Credit column swap (every row's sign flips → divergence doubles),
- spurious non-transaction rows (subtotals, page footers) counted as rows,
- the dropped-final-row case.

### 3.3 Sign convention (confirmed)

| Column | Signed amount |
|---|---|
| Debit | `−amount` |
| Credit | `+amount` |
| Cumulative Balance | compared directly (parenthesized negative supported) |

This matches:
- the user's final-stage sentence ("Debits (-ve) values and all Credits (+ve)"),
- our own bank-statement semantics recorded in taste
  (positive = credit = money in, e.g. `INWARD CHEQUE`),
- standard accounting.

### 3.4 Opening Balance handling (confirmed)

- Required agent parameter: `opening_balance_pdf` (new optional field in the
  agent output contract).
- **Auto-verification**: when a first cumulative-balance row exists,
  cross-check `opening_balance + first_transaction == first_cumulative` to
  catch a misread/mis-reported opening balance. If the check fails there, the
  failure message tells the agent its opening balance may be wrong (so it can
  re-read the header), rather than blaming the structure.
- If no cumulative column / no rows are found, opening-balance verification is
  skipped with an explicit note (graceful degradation).

### 3.5 Tolerance (confirmed)

| Check | Tolerance |
|---|---|
| Per-row cumulative match | `abs(diff) <= 1.0` |
| Final value vs last cumulative | `abs(diff) <= 1.0` |

The small tolerance absorbs rounding and formatting noise (e.g. pennies,
1-cent cumulative drift), while still catching real extraction errors
(which are typically huge — whole rows or mis-ordered columns).

### 3.6 Amount parsing (edge cases to handle)

- Thousands separators: `1,234,567.89` → `1234567.89`
- Parenthesized negatives: `(29,880,105.57)` → `−29880105.57`
  (Meezan uses parentheses for negative balances; documented in
  `file_dhancha.md`).
- Leading/trailing whitespace, `-`, `−`, `–`, `+` prefixes.
- Currency symbols if present (`Rs.`, `₨`, `$`).
- Mixed decimal formats (`.` or `,` decimal separator) — keep a strict,
  documented parser; if a cell cannot be parsed as an amount, the row is
  flagged as unparseable rather than silently skipped.

---

## 4. Questions asked and answers received

| # | Question | Answer chosen |
|---|---|---|
| 1 | Sign mapping for the merged stream | **Debit −, Credit +** (standard accounting; matches bank semantics) |
| 2 | Opening Balance handling | **Agent provides + auto-verify** (cross-check against first cumulative row when available) |
| 3 | Keep other diagnostics (per-page, fill, header mapping, issues/suggestions)? | **Keep diagnostics** — arithmetic drives verdict/score, fill-rate & mapping stay as secondary guidance |
| 4 | Comparison tolerance | **Small tolerance** — `abs(diff) <= 1.0` |

---

## 5. Diagnostics kept (unchanged in spirit)

The following stay in the output so the agent still has actionable guidance:

- `total_rows`, `page_count`,
- `per_page` (page, band_top, header_top, in_band_lines, date_matching_lines,
  row_count),
- `columns` fill stats (name, total, filled, fill_rate, empty),
- `column_mapping` (name → physical slice, name-based mode),
- `date_matching_count`,
- `issues` / `suggestions`,
- `score` (0–100),
- `extracted_rows`.

**Removed:**

- `extract_raw_table_rows` and everything referencing `raw_row_count`,
  `llm_row_count`, `row_delta`, and the `|delta| <= 3` verdict.

**Added (new verdict fields):**

- `opening_balance` (as passed / None),
- `debit_total`, `credit_total`, `net_change` (Σ credits − Σ debits),
- `final_from_opening`,
- `last_cumulative` (last Cumulative Balance value in extracted rows),
- `cumulative_check` (per-row sweep): `{passed, rows_checked, mismatches,
  first_mismatch_row, max_abs_error}`,
- `final_check` (opening + Σ tx vs last cumulative): `{passed, diff}`,
- `overall_pass` (both checks pass),
- `balance_check_skipped` (reason, when no cumulative column or no rows),
- `parsing_errors` (rows whose Debit/Credit/Cumulative could not be parsed).

---

## 6. Column identification (robustness)

The assessor must locate the amount columns from the agent's `columns_pdf`
list without assuming exact names:

- **Debit column**: the column whose normalized name contains `debit`
  (or `dr`, `withdraw`, `payment` as fallback aliases — but `debit`/`dr` first).
- **Credit column**: the column whose normalized name contains `credit`
  (or `cr`, `deposit`, `receipt` as fallback).
- **Cumulative/Balance column**: the column whose normalized name contains
  `balance` or `cumulative` or `total` — and must be the **last** such
  column (a statement may have both a "Cumulative" and a closing-balance
  column; we want the running balance, i.e. the last one).
- If a required column is missing from `columns_pdf`, the balance check is
  skipped with a clear reason (not a false FAIL).

This keeps the tool correct across all three known statements:
- Soneri: `Debit`, `Credit`, `Closing Balance`
- MCB: `Debit`, `Credit`, `Balance`
- Meezan: `Debit`, `Credit`, `Balance`

---

## 7. Integration: assessor as an agent `@tool`

### 7.1 What changes and what does NOT

**Does NOT change** (production pipeline untouched):

- `FileStructureOutput` schema (the persisted structure contract),
- `extract_pdf` / `ai_pdf_processor.py`,
- `detect_structure` retry flow,
- the reconciliation pipeline itself.

**Does change:**

1. **Move** `structure_assessor.py` → `backend/src/utils/structure_assessor.py`
   (so `ai_structure_detector` can import it cleanly; it becomes a real
   importable module instead of a tests-only script). Update `REPO_ROOT` to
   account for the new depth.
2. **Wire** `assess_pdf_structure` as a `@tool` in
   `ai_structure_detector.build_agent_tools(...)` (bound to the uploaded
   `pdf_path`).
3. **Update `AGENT_INSTRUCTIONS`**:
   - mandate calling the assessor at the end,
   - instruct the agent to **iterate**: on `overall_pass: false` (or a
     non-perfect score) the agent reads the `issues`/`suggestions`, fixes its
     structure, and calls again — until the verdict passes,
   - add `opening_balance_pdf` to the output contract (required field the
     agent reads from the statement header).
4. **Update `validate_structures.py`** import path.
5. (Nice-to-have, explicit user permission required) optionally register the
   tool in `build_agent_tools` via a `@tool` decorator so the agent can call
   it during detection rather than only as a post-hoc human-run check.

### 7.2 Agent iteration loop (the point of the whole change)

```
agent proposes structure (+ opening balance)
        │
        ▼
assessor @tool runs the NEW arithmetic check
        │
        ▼
   overall_pass == true? ──yes──► structure accepted, agent emits [output]
        │
        no
        ▼
agent reads issues/suggestions (first mismatch row, fill rates, mapping)
        │
        ▼
agent corrects structure / opening balance, calls assessor again
```

The tool output is returned to the agent, so if it sees a FAIL it improves
itself and calls again until it gets correct results — exactly as the user
specified.

---

## 8. File-by-file implementation steps

### 8.1 `backend/src/utils/structure_assessor.py` (new home of the rewritten file)

- Keep module docstring; update the "purpose" to describe the arithmetic
  check.
- Keep: `_resolve_path`, `_per_page`, `_page_header_top`,
  `normalize_per_page`, `_slice_words_to_columns`, `extract_pdf_words`,
  `_normalize`, `_header_slice_mapping`, `_clean_text`,
  `_extract_rows_per_page`, `_pretty`.
- **Delete**: `extract_raw_table_rows`, all `raw_row_count` /
  `llm_row_count` / `row_delta` logic and output fields.
- **Add**:
  - `parse_amount(value) -> Optional[float]` (commas, parentheses, signs,
    currency symbols, strict).
  - `_find_column(columns, *aliases) -> Optional[int]` (normalized-name
    matching).
  - `_amount_columns(columns) -> Tuple[Optional[int], Optional[int],
    Optional[int]]` (debit, credit, balance indices).
  - `_signed_amount(row, debit_idx, credit_idx) -> Optional[float]`
    (credit − debit).
  - `_run_cumulative_check(rows, debit_idx, credit_idx, balance_idx,
    opening_balance) -> dict` (per-row sweep, first mismatch, max error).
  - `_run_final_check(...)`.
  - `assess_pdf_structure(..., opening_balance: Optional[float] = None)`
    — the verdict now comes from the arithmetic check; diagnostics kept.
- Preserve the file header/footer Islamic prayer bookends convention
  (per project constitution) and the `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`
  markers on logical crux methods.
- Keep `main()` demo (update to print the new verdict fields; keep the
  Soneri sample structure).

### 8.2 `backend/src/services/ai_structure_detector.py`

- Import `assess_pdf_structure` from `src.utils.structure_assessor`.
- Add `@tool assess_pdf_structure(pdf_path bound, ...) -> str` in
  `build_agent_tools`, returning `_pretty(assessment)` (JSON for the agent;
  text is fine — decide: return JSON since the agent consumes it; `_pretty`
  for humans, but the agent reads the dict either way — we'll return the
  JSON string for machine consumption).
- Update `AGENT_INSTRUCTIONS` (see 7.1.3).
- Optionally add `opening_balance_pdf: Optional[float]` to the output
  contract parsing — but since `FileStructureOutput` is the persisted
  contract, keep it **optional** and **non-breaking** (default None) so old
  flows still parse.

### 8.3 `backend/tests/validate_structures.py`

- Change import to `from src.utils.structure_assessor import ...`.
- Pass `opening_balance` for the three statements (read from their headers
  during implementation) so the demo validates the new verdict.

### 8.4 `project-masham/file_dhancha.md` (documentation, optional but recommended)

- Update the validation table to the new verdict (overall_pass, cumulative
  check, final check) instead of raw/llm row counts.

### 8.5 No other consumers exist

Confirmed by grep: only `structure_assessor.py`, `validate_structures.py`,
and `file_dhancha.md` reference the old symbols. Nothing else imports
`extract_raw_table_rows` or `raw_row_count`.

---

## 9. Verification plan

1. `python -m py_compile backend/src/utils/structure_assessor.py
   backend/src/services/ai_structure_detector.py
   backend/tests/validate_structures.py`
2. Run `validate_structures.py` (Soneri, MCB, Meezan) and confirm:
   - each known-good structure now yields `overall_pass: true`
     (after supplying correct `opening_balance`),
   - the verdict fields appear,
   - negative parenthesized balances parse correctly (Meezan).
3. Negative tests (deliberately break a structure and confirm FAIL):
   - drop a row (band_top wrong) → cumulative mismatch detected,
   - swap Debit/Credit columns → divergence,
   - wrong opening balance → opening-verification failure message,
   - missing final row → caught by the per-row sweep.
4. Confirm the agent flow can call the tool (import path works; tool
   registered; instructions updated).

---

## 10. Known limitations (honest trade-offs)

- **Equal missing debit + missing credit cancel out** in the totals check —
  rare; the per-row sweep partially mitigates (running still matches, but a
  single row's debit and credit both missing means that row contributed
  nothing; undetectable arithmetically). Acceptable.
- **Opening balance misread by the agent** → auto-verification catches it
  when a first cumulative row exists; without one, a wrong opening balance
  yields a FAIL with a hint, not a silent wrong pass.
- **Subtotal/footer rows misclassified as transactions** → caught (they
  break the running balance) — this is a *feature*.
- **Non-numeric amount formats** (e.g. `DR`/`CR` suffixes) → parser flags
  them as parsing errors rather than guessing.
- **Statements without a Cumulative Balance column** → balance check skipped
  with a clear reason (graceful degradation); diagnostics still returned.
- The check is **structural + arithmetic**, not semantic: two transactions
  with identical amounts swapped in order are indistinguishable (they produce
  the same running balance). The cumulative check compares each row in
  order, so an out-of-order *amount* row will mismatch — but two rows that
  are exact duplicates in amount cannot be distinguished. Acceptable.

---

## 11. Open items before implementation

1. Confirm the sign convention and all four Q&A answers (Section 4).
2. Confirm the move to `backend/src/utils/` (vs keeping the file in
   `backend/tests/`). The move is what makes the `@tool` wiring clean.
3. Confirm the agent tool output format: JSON string (machine-first) vs
   `_pretty` text (human-first). **Recommend JSON** since the agent consumes
   it programmatically.
4. Confirm whether to add `opening_balance_pdf` to the persisted
   `FileStructureOutput` schema (recommend **no** — keep it an assessor-only
   input to avoid breaking the production contract; the agent passes it to
   the tool, not to the extractor).

---

## 12. Summary

The new approach replaces an unreliable row-count comparison with a
self-consistent arithmetic audit of the extracted data: merge Debit (−) and
Credit (+), add them to the agent-provided (and auto-verified) Opening
Balance, and compare every running total — and the final total — against the
statement's own Cumulative Balance column within a 1.0 tolerance. It
dramatically reduces false verdicts, catches missing rows, column swaps, and
amount mis-slicing, and — wired as an agent `@tool` — lets the agent iterate
until its structure is provably correct.
