# Structure Assessor — Yabluwa al Saghir + Yabluwa al Kabir System

> Status: **PLAN — awaiting approval. No code has been changed yet.**
> Location: `project-masham/structure-assessor-kabir-saghir-plan.md`
> Branch: `005-ai-data-extraction`
> Builds on: `project-masham/structure-assessor-arithmetic-check-plan.md` (the Saghir implementation already in `backend/src/utils/structure_assessor.py`)

---

## 1. TL;DR — the problem this system solves

The current assessor (in `backend/src/utils/structure_assessor.py`) validates the
extracted rows against the statement's own arithmetic — a **running-balance sweep**
against the Cumulative Balance column. It is internally self-consistent **for whatever
subset of rows gets extracted**. When the agent extracted page 1 of a 6-page vendor
ledger correctly but pages 2–6 returned **0 rows**, the assessor **passed**: an empty
page cannot fail an arithmetic check it never participates in.

The agent moved on. Data was silently lost.

The fix is a second, complementary test — **Yabluwa al Kabir (Assessment of the Big)** —
that checks **completeness**: did the agent's structure extract the *same transaction
rows* the raw PDF actually contains? The existing arithmetic test becomes **Yabluwa al
Saghir (Assessment of the Small)** — it checks *correctness* of what was extracted.

> **Neither test alone is sufficient.**
> - Saghir alone → false PASS on incomplete subsets (the incident above).
> - Kabir alone → false PASS on complete-but-wrong data (column swaps, mis-sliced
>   amounts, wrong signs — the very cases the arithmetic test exists to catch).
>
> **Correctness + completeness = robust PDF structure.**

---

## 2. The incident (the motivation)

| Fact | Value |
|---|---|
| File | Vendor ledger (6 pages) |
| What happened | Page 1 extracted accurately; pages 2–6 → `rows=0` |
| Assessor verdict | PASS |
| Why | Saghir assesses `credit + debit = last cumulative` on the rows it *has*. Page 1 is internally consistent by construction (`opening + Σ(page-1 rows)` always equals page-1's last cumulative). Pages 2–6 contributed no rows → no arithmetic → **no possibility of failure** → PASS. |
| Consequence | Agent moved forward, correct per the tool's verdict, with ~83% of the ledger missing. |

**Root cause:** the arithmetic check validates *correctness of the extracted subset*, and
gives zero information about *completeness of the extraction*.

---

## 3. Core principle: two complementary tests

### 3.1 Yabluwa al Saghir (Assessment of the Small) — the existing test

- Per-row cumulative sweep: from the agent-provided Opening Balance, add each row's
  signed amount (Bank: Debit = −, Credit = +; Vendor: inverted) and compare the running
  total against the statement's Cumulative Balance column on **every row**.
- Final check: `opening + Σ(credits) − Σ(debits)` vs the **last** Cumulative Balance.
- Verdict: PASS only when both checks match within tolerance (`abs(diff) <= 1.0`).
- Catches: missing rows, Debit/Credit column swaps, mis-sliced amounts,
  footer/subtotal lines counted as transactions.
- **Blindness:** anything it cannot see is not checked. Missing pages = nothing to check.

### 3.2 Yabluwa al Kabir (Assessment of the Big) — the new test

- Extract the **raw** transaction rows from the PDF using pdfplumber's own table
  detection — **independently of the agent's proposed structure** (see Hole A).
- Filter raw rows to *plausible transactions* using a date-regex filter (see §6).
- Compare the raw row count against the agent-structure row count.
- Verdict: percentage-based ladder (see §7).
- Catches: lost pages, clipped bands, hallucinated extra rows, dropped headers.
- **Blindness:** row count says nothing about *value* correctness — that's Saghir's job.

### 3.3 The verdict composition

```
overall_pass = saghir.passed AND kabir.passed
```

- Both must pass for the structure to be accepted.
- Each test's failure path produces its own actionable summary so the agent knows
  *which* problem to fix and *where*.

---

## 4. What we learned (from the codebase)

### 4.1 The two assessors today

| | `backend/tests/structure_assessor.py` (old) | `backend/src/utils/structure_assessor.py` (current) |
|---|---|---|
| Baseline | pdfplumber `extract_table()` rows ("raw table rows") | the statement's own arithmetic |
| Verdict | `llm_row_count − raw_row_count`, `abs(delta) <= 3` → OK | cumulative sweep + final check |
| Strengths | catches row-count cliffs, needs no arithmetic | catches wrong data, column swaps, amount mis-slicing |
| Weaknesses | ±3 arbitrary; raw baseline flaky on unruled/merged tables; says nothing about amounts | validates only the extracted subset; silent on missing pages |

### 4.2 Why each alone fails

- The old assessor's raw baseline **reused the agent's `band_top`/`header_top`**. If the
  agent's continuation-page band is wrong, the raw extractor clips the same rows →
  delta stays small → PASS while pages vanish. **Shared blindness.**
- The current assessor's arithmetic is **self-consistent by construction** on whatever
  subset is extracted → the page-1-only incident.

### 4.3 The filter-symmetry trap (the deep lesson of the design discussion)

A naive "build a Date Array from the raw rows, filter both sides, compare leftovers"
fails in the *healthy* case:

- Normal statements have raw extraction covering **all** dates.
- A raw-derived Date Array therefore contains every date.
- Filtering removes every dated row from **both** sides → both leftovers ≈ empty →
  difference ≈ 0 → **always PASS**, even when pages were lost.

The filter erases the loss signal symmetrically: "wrapped sub-lines" and "lost pages"
both reduce to "raw leftover ≈ undated debris." The mechanism must **not** be built from
the side that defines the healthy state.

**Resolution:** derive the Date Array from the **agent's** rows (§8). Then raw rows whose
dates the agent never saw **survive the filter** — the loss signal is preserved.

### 4.4 Percentages over absolute counts

Absolute thresholds (10/30 rows) are ledger-size-dependent: a 15-row statement can lose
a whole page and never cross 30. Percentage thresholds scale with the document.

---

## 5. The improvements (problem → fix)

| # | Improvement | Fixes |
|---|---|---|
| 1 | Raw baseline filtered by a **date-regex** (5 standard patterns + extensions) instead of trusting pdfplumber's row count raw | wrapped sub-lines, merged cells, footer/subtotal lines polluting the raw count |
| 2 | Raw extractor runs with **no `band_top`/`header_top`/`rows_dropped`** — the date filter is the only vertical guard | **Hole A**: the old raw baseline inherited the agent's band/header, sharing its blindness on continuation pages |
| 3 | **Percentage thresholds**: `< 2%` → PASS, `> 25%` → FAIL, between → Assessor LLM | absolute-count blindness on small statements; wasted LLM calls on catastrophic cases |
| 4 | **Date Array derived from the agent's rows** (deduplicated, canonical dates), used to filter both sides | the filter-symmetry trap — raw-derived arrays make the healthy case degenerate |
| 5 | **Dated/Undated leftover split** on the raw side | separates *hard evidence of missed transactions* (deterministic FAIL) from *benign debris* (the only thing the Assessor must judge) |
| 6 | **Date canonicalization** on both sides before any compare | string mismatch false-negatives (agent `23-MAY-2026` vs raw `23-05-2026`) |
| 7 | **Classification-only Assessor LLM** in the ambiguous middle, with fail-safe instructions | context bloat (no full dumps), and LLMs rationalizing a PASS on real data loss |
| 8 | **Saghir + Kabir composed verdict** | neither test alone is sufficient |

---

## 6. Date pattern set (raw-side transaction filter)

Applied to the first non-empty cell of each raw table row, **case-insensitive**.
The raw filter is deliberately **independent of the agent's proposed `date_pattern_pdf`** —
otherwise a wrong agent pattern drags the raw count down with it (Hole A again).

| # | Pattern | Matches |
|---|---|---|
| 1 | `^\d{4}-\d{2}-\d{2}$` | ISO `YYYY-MM-DD` |
| 2 | `^\d{2}/\d{2}/\d{4}$` | `DD/MM/YYYY` or `MM/DD/YYYY` (ambiguous by design — we only need "is a date") |
| 3 | `^\d{2}-\d{2}-\d{4}$` | `DD-MM-YYYY` |
| 4 | `^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$` | generalized short/medium numeric, any separator (`MM-DD-YY`, `DD.MM.YY`, …) |
| 5 | `^\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}$` | `05-MAY-26`, `05/MAY/2026`, `23-may-2026` |
| 6 | `^\d{1,2} [A-Za-z]{3} \d{4}$` | `23 May 2026` (space-separated month name) |
| 7 | `^\d{1,2} \d{1,2} \d{2,4}$` | `23 05 2026` (space-separated numeric, Soneri style) |

Pre-processing before matching:

- Trim a trailing time component (credit-card statements carry `12:00 AM`) before matching.
- After matching, **canonicalize to a real date object** (see §8.1) — the raw and agent
  sides must be compared as *dates*, never as strings.

---

## 7. Thresholds and the tier ladder

```
      |raw_dated − llm_rows|
diff = ─────────────────────  × 100        (raw_dated = date-filtered raw row count)
            raw_dated
```

| Tier | Condition | Verdict | LLM needed? |
|---|---|---|---|
| PASS | `diff < 2%` | PASS | no |
| FAIL | `diff > 25%` | FAIL (template summary, §8.4) | no |
| ADJUDICATE | `2% <= diff <= 25%` | Assessor LLM decides | yes |

Notes:

- `diff` uses **absolute value** — the LLM can *exceed* the raw count via hallucinated
  rows, and 25% must bite in both directions.
- `raw_dated = 0` → **Kabir inconclusive** (the patterns may not cover this statement's
  format) → defer to Saghir, never auto-FAIL.
- The adjudicate band is where the genuinely ambiguous cases live: coverage looks full,
  but per-date row counts differ (wrapped sub-lines vs one real lost entry).

### 7.1 Quiet-loss guard — DECIDED: NOT adopted

A quiet-loss guard was considered (escalate to the Assessor when DatedLeftovers is
non-trivial even under 2%) but rejected by the user: **`diff < 2%` is a plain PASS,
no exceptions.** The 2% band is small enough that the residual risk is accepted;
simplicity wins.

---

## 8. The Data Filter Pipeline (context control + evidence extraction)

### 8.1 Canonicalization (the load-bearing prerequisite)

Every date — raw side and agent side — is parsed into a **real `datetime.date`**:

- matched via the pattern set (§6) on the raw side,
- via the agent's patterns on the agent side, with the agent's own `date_pattern_pdf`
  passed as a hint for exotic formats,
- case-insensitive month names,
- 2-digit years → `20XX` (e.g. `26` → `2026`),
- trailing time stripped first.

Without this, `23-MAY-2026` vs `23-05-2026` compares as zero coverage → false FAIL.

### 8.2 Building the Date Array (from the AGENT's rows)

- Parse each agent row's date cell → canonical date.
- Deduplicate: `{date: count}` map — 3 rows on `23-may-2026` + 4 on `24-may-2026`
  → 2 unique dates with counts `{23: 3, 24: 4}`.
- This array is the **filter key** and the **coverage record**.

### 8.3 Filtering both sides

- **Agent rows** minus the Date Array → ~empty by construction (every agent-dated row is
  in its own array). The leftover is whatever the agent's own date column failed to parse
  — itself diagnostic.
- **Raw rows** minus the Date Array → the **evidence**. Split it:

| Leftover class | Definition | Meaning | Handling |
|---|---|---|---|
| **DatedLeftovers** | first cell matches a date pattern, date **not** in the agent's array | hard evidence of missed transactions | non-trivial → **deterministic FAIL** with template summary (§8.4); trivial → absorb |
| **UndatedLeftovers** | first cell is not a date | benign candidates: wrapped continuation sub-lines, merged-cell artifacts, headers, footers, page numbers, subtotals | the **only** thing the Assessor LLM judges |

This split does most of the work for free: DatedLeftovers = provable loss, no LLM needed.
The Assessor fires only for the genuinely ambiguous middle.

### 8.4 Template failure summaries (deterministic tiers)

- `> 25%` or non-trivial DatedLeftovers → e.g.
  *"FAIL: raw extraction has N dated rows on dates {d1..dk} that the LLM structure never
  covered — pages p..q missing entirely. Most likely cause: continuation-page
  band_top/header_top too low."*
- Agent rows exist but **none** canonicalize → *"FAIL: agent's date cells matched no
  pattern — check date_pattern_pdf and the date-column slice/boundary."*

---

## 9. The Assessor LLM (the adjudication step)

### 9.1 Role — classification only

> It must NEVER do entry-level matching or identify individual discrepancies.
> Its only job: **is the difference real data/entry loss, or structural
> noise (headers, footers, subtotals, wrapped sub-lines, merged cells)?**

### 9.2 The packet (what gets passed — context-controlled)

No full dumps. The packet is a structured digest:

```json
{
  "structure": { "columns_pdf": [...], "header_words_pdf": [...],
                 "rows_dropped_pdf": n, "header_top_pdf": ...,
                 "column_boundaries_pdf": [...], "band_top_pdf": ...,
                 "date_pattern_pdf": "..." },
  "raw_date_coverage": { "unique_dates": 30, "per_date_counts": { ... },
                         "monthly_rollup": { "2023-05": 14, ... } },
  "agent_date_coverage": { "unique_dates": 8, "dates": [...] },
  "per_page": [ { "page": 1, "raw_dated": 44, "llm": 44 }, ... ],
  "dated_leftovers_capped": [ ... ],     // first ~15 raw rows with dates the agent missed
  "undated_leftovers_capped": [ ... ],   // first ~15 raw debris rows
  "saghir": { "passed": true, "rows_checked": n, "first_mismatch_row": null }
}
```

- Per-page counts catch **offsetting errors** (page 1 +5, page 2 −35 → net ≈ 0).
- Monthly rollup keeps multi-year ledgers (2017–2023) readable.
- Caps keep context bounded regardless of statement size (300 ↔ 260 rows is fine).

### 9.3 Instructions (fail-safe bias)

- PASS **only if** the difference is fully explained by benign artifacts (wrapping,
  merged cells, headers, footers, subtotals) **and** date coverage is complete.
- **FAIL on any date or page gap, or any per-date count anomaly**, citing which
  page(s)/date range(s) and the likely parameter to fix
  ("page 4 covers 08-Mar→22-Mar, entirely absent → continuation band_top wrong").
- The cost asymmetry is explicit: a false PASS = silent data loss; a false FAIL = one
  extra agent iteration. When unsure, **fail**.

### 9.4 Output contract

```json
{ "passed": true | false, "summary": "one actionable paragraph" }
```

### 9.5 Implementation

- The adjudicator is a **nested Agent via the OpenAI Agents SDK** (`Agent`,
  `Runner`), built like the main structure-detection agent in
  `ai_structure_detector.py`, with `settings.AI_MODEL` / `AI_API_KEY` and the
  existing `processing_cancellation` registry for mid-run cancellation.
  (User decision: an Agent, not a bare LiteLLM call.)
- Gated: skipped entirely when Saghir already failed (verdict is fail either way) or
  when a deterministic tier already decided.

---

## 10. The complete system workflow

```
Agent proposes structure (+ opening_balance)
        │
        ▼
┌─────────────────────────────── assess_pdf_structure ───────────────────────────────┐
│                                                                                     │
│  SAGHIR (Small)                              KABIR (Big)                             │
│  ────────────────                             ───────────────                        │
│  extract with agent structure                raw extract: find_tables()/             │
│  per-row cumulative sweep                    extract_table(), NO band/header/        │
│  final check (opening + net)                 rows_dropped → date-regex filter        │
│  verdict: cumulative & final                 canonicalize → raw_dated + coverage     │
│                                                                                      │
│  saghir.passed? ──no──► FAIL: arithmetic diagnostics (first mismatch row, etc.)      │
│        │ yes                                                                          │
│        ▼                                                                              │
│  diff% = |raw_dated − llm_rows| / raw_dated                                           │
│        │                                                                              │
│        ├─ < 2% ────────────► PASS (Kabir)                                             │
│        ├─ > 25% ───────────► FAIL (template summary, no LLM)                          │
│        └─ between ─────────► Date Array from AGENT rows (canonical, dedup)            │
│                              filter agent + raw sides                                  │
│                              raw leftover → DatedLeftovers | UndatedLeftovers          │
│                                   │                                                   │
│                                   ├─ DatedLeftovers non-trivial ► FAIL (template)     │
│                                   └─ else ► Assessor LLM (packet §9.2)                │
│                                               ├─ passed ► PASS                        │
│                                               └─ failed ► FAIL + actionable summary   │
│                                                                                      │
│  overall_pass = saghir.passed AND kabir.passed                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
        │
        ├─ PASS ► agent emits [output] block ► production extractor
        └─ FAIL ► agent reads issues/suggestions/summary, fixes structure,
                  calls assessor again (iterate until pass)
```

---

## 11. Edge cases and guards

| Case | Handling |
|---|---|
| `raw_dated = 0` | Kabir inconclusive — defer to Saghir, never auto-FAIL |
| Agent rows > 0 but none canonicalize | FAIL with template summary (§8.4) |
| String mismatch across sides (`23-MAY-2026` vs `23-05-2026`) | canonicalization (§8.1) |
| Agent extracts MORE rows than raw (hallucination) | abs diff; both directions capped at 25% |
| Offsetting per-page deltas | per-page counts in the packet (§9.2) |
| Multi-year ledger (2017–2023) | monthly rollup in coverage |
| Wrapped continuation sub-lines | UndatedLeftovers → benign class, Assessor-only |
| Weekend/holiday gaps | coverage measured against the raw set itself — impossible to false-fail |
| Saghir already failed | skip Kabir's adjudicator LLM call entirely (verdict is fail anyway) |
| Cancellation mid-run | adjudicator registered in `processing_cancellation`; stream cancellable |

---

## 12. Known limitations (honest)

- **Assessor quality is prompt-dependent** — the classification-only instructions and
  fail-safe bias must be validated on real statements.
- **Date-pattern coverage is heuristic** — an unanticipated date format makes
  `raw_dated` undercount (mitigated: inconclusive, not fail; patterns are additive).
- **Thresholds (2% / 25%) are uncalibrated** against real data — initial values from
  domain reasoning; expect tuning after the first real ledger runs.
- **Saghir's inherited blind spots remain**: equal missing debit + credit cancel out;
  two identical-amount rows swapped in order are indistinguishable. Kabir does not fix
  these — it fixes completeness, not value semantics.
- **The adjudicator adds an LLM dependency** to a tool that was "deterministic,
  zero-LLM" — its docstring and expectations must be updated to match.
- **Column-slicing errors on the raw side** are possible (a date column sliced wrongly
  drops raw rows) — the date filter is applied to the first *non-empty* cell to reduce
  this.

---

## 13. Implementation plan (file-by-file)

### 13.1 `backend/src/utils/structure_assessor.py`

- Add `RAW_DATE_PATTERNS` (the 7 patterns, §6) and `_canonicalize_date(text)` (§8.1).
- Add `extract_raw_rows_date_filtered(pdf_path)` → `(rows, date_counts, per_page_counts)`
  — `find_tables()`/`extract_table()` per page, **no band/header/rows_dropped**, rows
  kept only when the first non-empty cell canonicalizes to a date.
- Add `run_kabir_check(raw_counts, llm_rows, columns, date_pattern_pdf)` → `kabir_check`
  dict: `{tier, diff_pct, raw_dated, llm_rows, date_coverage,
  dated_leftovers, undated_leftovers, passed, summary}`.
- Add `run_assessor_agent(packet)` → `{passed, summary}` (OpenAI Agents SDK Agent,
  cancellable).
- Compose the verdict: `overall_pass = cumulative_check.passed and final_check.passed
  and kabir_check.passed`.
- Keep all existing diagnostics (`per_page`, fill rates, mapping, issues/suggestions,
  score) — Saghir unchanged.
- Update the module docstring: no longer "zero-LLM" — deterministic core with an
  optional adjudicator LLM in the ambiguous band.

### 13.2 `backend/src/services/ai_structure_detector.py`

- Import `assess_pdf_structure` (and `_pretty`); register it as a `@tool` in
  `build_agent_tools`, bound to the uploaded `pdf_path`.
- Update `AGENT_INSTRUCTIONS`:
  - mandate calling the assessor before the final `[output]` block,
  - iterate on FAIL (read issues/suggestions/summary → fix → re-call),
  - add `opening_balance_pdf` to the output contract (agent reads from header),
- Adjudicator is a nested Agents SDK `Agent` using `settings.AI_MODEL`/`AI_API_KEY`
  and the cancellation registry.

### 13.3 `backend/tests/validate_structures.py`

- Update the import path to `src.utils.structure_assessor`.
- Add `opening_balance` for Soneri/MCB/Meezan; assert `overall_pass` for known-good
  structures under the **composed** verdict.

### 13.4 `project-masham/file_dhancha.md` (docs)

- Update the validation table to the composed verdict (saghir + kabir columns).

---

## 14. Verification plan

1. `python -m py_compile` on all touched files.
2. `validate_structures.py`: known-good Soneri/MCB/Meezan structures →
   `overall_pass: true` with both tests passing.
3. **Saghir negatives**: drop a row → sweep mismatch; swap Debit/Credit → divergence;
   wrong opening balance → opening-verification message; missing final row → swept.
4. **Kabir negatives** (the new critical ones):
   - wrong continuation-page band/header (the incident reproduced: pages 2–6 → 0 rows)
     → raw_dated ≈ 5× llm_rows → tier FAIL or DatedLeftovers non-trivial → FAIL,
   - wrapped-sub-line statement → diff inside 2–25% band → Assessor → PASS with note,
   - LLM hallucinated extra rows → abs diff → FAIL.
5. Assessor packet smoke test: verify caps, per-page counts, rollups are sane on the
   6-page ledger and the multi-year 2017–2023 statement.
6. Agent flow: tool registered, instructions updated, iteration loop exercised end-to-end.

---

## 15. Rating — how well does this system work?

**8 / 10** — with the caveat that it is a *design* rating: the architecture is sound and
directly eliminates the root cause.

Why not higher:

- thresholds (2% / 25%) and the date-pattern set are **uncalibrated** — they encode
  domain reasoning, not empirical evidence from real statements,
- the Assessor LLM's verdict quality is prompt-dependent and must be battle-tested,
- more moving parts (deterministic core + LLM step) than the current single test.

Why not lower — the structure is provably right:

- Saghir (correctness) + Kabir (completeness) are mathematically complementary; the
  page-1-only incident cannot recur (lost pages now surface as DatedLeftovers or a
  >25% delta),
- deterministic-first: the clear-cut cases (catastrophic delta, date-gap evidence) never
  spend an LLM call,
- the agent-derived Date Array + leftover split preserves the loss signal exactly where
  a naive filter erased it,
- every FAIL path yields an actionable, fixable summary, not just a boolean.

After calibrating thresholds on real statements and validating the Assessor on a handful
of ledgers, this is a 9. Expect the final tuning pass to settle it.

---

## 16. Open items before implementation

1. Approve the 2% / 25% thresholds as starting values (expect tuning).
2. Confirm the Assessor as a nested Agents SDK Agent (user decision: **yes**, done).
3. Confirm the raw extractor drops `rows_dropped` entirely (recommended: yes — the date
   filter is the only guard needed; `rows_dropped` is a header-block artifact, and
   headers never match a date pattern).
