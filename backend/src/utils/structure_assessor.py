# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Structure Assessor (Jaaiza e Bunyad) — Saghir + Kabir

Deterministic scoring tool that tells an AI agent how well its proposed PDF
structure parameters would perform in the production extractor. It runs the
EXACT same extraction logic as the production pipeline
(backend/src/services/ai_pdf_processor.py -> extract_pdf, mirrored here by
extract_pdf_words) using the agent's proposed structure, then validates the
extracted DATA against the statement's own arithmetic.

The verdict is TWO complementary tests (correctness + completeness):

  YABLUWA AL SAGHIR (Assessment of the Small) — the arithmetic check.
  Validates the *correctness of the extracted subset*:
      1. Per-row cumulative sweep (primary): starting from the agent-provided
         Opening Balance, add each transaction's signed amount (Debit = -,
         Credit = +; vendor ledgers invert the signs) in order, but compare
         the running total against the statement's Cumulative Balance column
         ONLY on rows that actually carry a printed balance (SPARSE balance
         support - Habib-style statements print one balance per day-group,
         e.g. 4 rows on 22 May with the balance only on the 4th). The running
         total ALWAYS advances; only the comparison is skipped.
      2. Final check (secondary): opening + sum(credits) - sum(debits) against
         the LAST printed Cumulative Balance value.
  A subset passes only when both checks match within a small tolerance
  (abs(diff) <= 50.0 - absorbs per-row rounding; real extraction errors
  diverge by thousands). Blindness: anything it cannot see is not checked -
  an empty page cannot fail an arithmetic check it never participates in, so
  a structure that silently drops entire pages still PASSES Saghir.

  YABLUWA AL KABIR (Assessment of the Big) — the completeness check.
  Independently extracts the RAW transaction rows from the PDF (word-line
  based, NO band_top/header_top/rows_dropped - those inherit the agent's
  blindness) and keeps only rows whose first non-empty cell matches a date
  pattern (7 standard patterns + extensions). The date-filtered raw count is
  compared against the LLM structure's row count on a percentage ladder:

      diff < 2%                    -> PASS
      diff > 25%                   -> FAIL (template summary, no LLM)
      2% <= diff <= 25%            -> Assessor LLM adjudicates

  In the adjudicate band, a Date Array is built from the AGENT's own rows
  (deduplicated canonical dates) and both sides are filtered by it. Raw rows
  whose dates the agent never saw (DatedLeftovers) are hard evidence of
  missed transactions -> deterministic FAIL. The remaining undated debris
  (wrapped sub-lines, headers, footers, merged cells) is the only thing the
  Assessor LLM judges.

  overall_pass = saghir.passed AND kabir.passed

  The adjudicator is a nested OpenAI Agents SDK Agent (classification only).
  It is skipped when Saghir already failed or a deterministic tier already
  decided, so the clear-cut cases never spend an LLM call.

  YABLUWA AL IHSAN (Assessment of the Finest) — the closing-balance anchor.
  The final completeness gate: a nested OpenAI Agents SDK Agent reads the
  statement's printed CLOSING BALANCE from the LAST page of the PDF (falling
  back to earlier pages when the last page carries no balance - blank
  signature/annex pages). The agent returns the figure and where it read it
  (page + label/date). The assessor then checks
      opening + Σ(signed amounts)  vs  closing balance
  within the same tolerance. This is the ONLY check that defeats the
  self-consistent-subset trap deterministically: it anchors on a figure that
  comes from the STATEMENT itself, not from the extracted rows, so a dropped
  final-day group (e.g. row 40 of 40 lost while row 39 still carries a
  balance) fails even though Saghir + Kabir both pass. When the agent cannot
  find a closing balance anywhere, Ihsan is INCONCLUSIVE (defer to Saghir +
  Kabir), never a silent pass or a hard fail.

  overall_pass = saghir.passed AND kabir.passed AND ihsan.passed
  (Ihsan is skipped entirely when Saghir or Kabir already failed, and an
  INCONCLUSIVE Ihsan does not fail the verdict.)

Diagnostics are kept alongside the verdict so the agent still sees why a
structure fails: per-page row counts, per-column fill rates, the name ->
physical-slice header mapping, and actionable issues/suggestions.

Dependencies: pdfplumber (already used by the backend), openai-agents SDK
(only when the Assessor LLM adjudication step is actually invoked).
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber
from agents.decorators import tool

# Canonical parsers shared with the production transformers (single source of
# truth): canonicalize_date + parse_amount live in data_transformers.py and are
# reused here so the assessor and the pipeline always agree on formats.
from src.utils.data_transformers import (
    _strip_trailing_time,
    canonicalize_date,
    parse_amount,
)

# Default MCB statement layout (same as test_results.py / LLM_run_check.py).
DEFAULT_COLUMN_BOUNDARIES = [45.0, 89.0, 195.0, 246.0, 298.0, 348.0, 440.0, 500.0, 570.0]
DEFAULT_BAND_TOP = 170.0
DEFAULT_DATE_PATTERN = r"^\d{2}-[A-Z]{3}-\d{2}$"

# Arithmetic tolerance (abs diff <= 50.0) absorbs rounding/formatting noise
# (statement amounts are often rounded to whole PKR, so a few rupees of drift
# per row is expected) while still catching real extraction errors (whole
# rows, mis-sliced amounts, column swaps - these diverge by thousands).
BALANCE_TOLERANCE = 50.0

# ---- Kabir (completeness check) configuration --------------------------------
# Percentage ladder: below PASS_PCT is a plain PASS; above FAIL_PCT is a
# deterministic FAIL; in between the Assessor LLM adjudicates. Initial values
# from domain reasoning - expect tuning after the first real ledger runs.
KABIR_PASS_PCT = 2.0
KABIR_FAIL_PCT = 25.0
# A DatedLeftover block is "trivial" when its rows account for at most this
# fraction of the raw dated rows (leftover dates can drift a few rows when a
# wrapped sub-line carries its own date). Non-trivial -> deterministic FAIL.
KABIR_TRIVIAL_LEFT_BLOCK = 0.02

# 7 standard date patterns, applied to the first non-empty cell of each raw
# word line, case-insensitive. The raw filter is deliberately INDEPENDENT of
# the agent's proposed date_pattern_pdf - otherwise a wrong agent pattern
# drags the raw count down with it (Hole A).
RAW_DATE_PATTERNS: List[str] = [
    r"^\d{4}-\d{2}-\d{2}$",                        # ISO YYYY-MM-DD
    r"^\d{2}/\d{2}/\d{4}$",                        # DD/MM/YYYY or MM/DD/YYYY
    r"^\d{2}-\d{2}-\d{4}$",                        # DD-MM-YYYY
    r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$",          # short/medium numeric, any separator
    r"^\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}$",        # 05-MAY-26, 05/MAY/2026, 23-may-2026
    r"^\d{1,2} [A-Za-z]{3} \d{4}$",                # 23 May 2026 (space-separated month name)
    r"^\d{1,2} \d{1,2} \d{2,4}$",                  # 23 05 2026 (space-separated numeric)
]
_RAW_DATE_COMPILED = [re.compile(p) for p in RAW_DATE_PATTERNS]

# Repo root = the backend/ directory (utils/ sits at backend/src/utils/).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Amount-cell markers for the debit / credit / balance columns.
_DEBIT_ALIASES = ("debit", "dr", "withdraw", "payment")
_CREDIT_ALIASES = ("credit", "cr", "deposit", "receipt")
_BALANCE_ALIASES = ("balance", "cumulative", "total")
# Combined Debit/Credit column (rare): a single column holding both.
_COMBINED_ALIASES = ("debit credit", "debit/credit", "debit-credit", "cd", "c d", "debitcredit")


def _resolve_path(path: str | Path) -> Path:
    """Resolve a relative path against the repo root."""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _per_page(value: Any, page_index: int) -> Any:
    """Pick the value for a given page from a per-page list (or a scalar)."""
    if isinstance(value, (list, tuple)):
        if page_index < len(value):
            return value[page_index]
        return value[-1] if value else None
    return value


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _page_header_top(
    header_top: Optional[float | List[float]],
    band_top: Optional[float | List[float]],
    page_index: int,
) -> Optional[float]:
    """Resolve the effective header top for a page.

    A page whose header line sits at or below its data band has no usable
    header (e.g. a continuation page that starts straight at the data band).
    Returning None there disables the header filter, so the first data row is
    never swallowed by the header-top tolerance.
    """
    page_header_top = _per_page(header_top, page_index)
    if page_header_top is None:
        return None
    page_band_top = _per_page(band_top, page_index)
    if page_band_top is not None and page_header_top >= page_band_top:
        return None
    return page_header_top


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def normalize_per_page(
    value: Optional[float | List[Optional[float]]],
    page_count: int,
    name: str,
) -> Optional[List[Optional[float]]]:
    """Normalize a per-page structural value to the agent's output contract.

    The agent emits either a single scalar (structure identical on the first
    two pages - the canonical structure applies everywhere) or a list of the
    form [page1_value, page2_value] (structure differs between page 1 and
    page 2; page 2's value is canonical for pages 3+).

    This helper expands a scalar into a length-`page_count` list (repeating
    the scalar) and pads a short list with its LAST element so page 2's
    canonical value extends to all continuation pages. A None value becomes
    all-None (filter disabled).

    Args:
        value: The raw value from the LLM (scalar or list, or None).
        page_count: Number of pages in the PDF.
        name: Field name for error messages.

    Returns:
        A per-page list of length `page_count`, or None if `value` is None.

    Raises:
        ValueError: If `value` is a list that is empty or longer than
            `page_count`.
    """
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            raise ValueError(f"'{name}' list is empty - provide [page1, page2]")
        if len(value) > page_count:
            raise ValueError(
                f"'{name}' has {len(value)} entries but the PDF has only "
                f"{page_count} page(s) - provide [page1, page2] at most"
            )
        # Pad with the last entry so page 2's canonical value extends onward.
        return [value[min(i, len(value) - 1)] for i in range(page_count)]
    # Scalar: applies to every page (canonical structure is uniform).
    return [value] * page_count


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _slice_words_to_columns(words: list[dict], boundaries: list[float]) -> list[str]:
    """Assign words to columns by their horizontal center (same as production)."""
    cells = ["" for _ in range(len(boundaries) + 1)]
    for w in words:
        cx = (w["x0"] + w["x1"]) / 2
        idx = sum(1 for b in boundaries if cx > b)
        if idx < len(cells):
            cells[idx] = (cells[idx] + " " + w["text"]).strip()
    return cells


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def extract_pdf_words(
    pdf_path: str | Path,
    columns: List[str],
    header_top: Optional[float | List[Optional[float]]] = None,
    rows_dropped: int = 0,
    boundaries: Optional[List[float]] = None,
    band_top: Optional[float | List[Optional[float]]] = None,
    date_pattern: str = DEFAULT_DATE_PATTERN,
    name_based: bool = True,
) -> Tuple[List[Dict[str, str]], int]:
    """Extract transaction rows from ALL pages using the production logic.

    Mirrors backend/src/services/ai_pdf_processor.py::extract_pdf exactly
    (per-page band/header filters, per-page dedup, center-based column slice),
    so the assessor measures the SAME output the production pipeline would
    produce with the proposed structure.

    The row-marker and column assignment differ by `name_based`:
      - name_based=True (default): each column NAME is mapped to its physical
        slice index via the header line (`_header_slice_mapping`), so values
        land in the right columns even when `columns` is out of physical order.
      - name_based=False: production's index-based behaviour - column i is
        assigned cells[i] and the row marker is cells[0] always.

    Returns:
        (rows, page_count) where rows is a list of {column: value} dicts.
    """
    compiled = re.compile(date_pattern)
    rows: List[Dict[str, str]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        for page_index, page in enumerate(pdf.pages):
            words = page.extract_words()

            page_header_top = _page_header_top(header_top, band_top, page_index)
            page_band_top = _per_page(band_top, page_index)

            slice_map = (
                _header_slice_mapping(page, page_header_top, boundaries or [], columns)
                if name_based
                else {}
            )

            # Group words into visual lines by their top coordinate.
            lines: dict[float, list[dict]] = {}
            for w in words:
                top = round(w["top"], 1)
                in_band = page_band_top is None or top >= page_band_top
                below_header = page_header_top is None or top >= page_header_top + 4.0
                if in_band and below_header:
                    lines.setdefault(top, []).append(w)

            # Dedup is PER-PAGE (same as production).
            seen_tops: set[float] = set()
            for top in sorted(lines):
                if top in seen_tops:
                    continue
                seen_tops.add(top)
                cells = _slice_words_to_columns(lines[top], boundaries or [])
                if not cells:
                    continue
                # Row marker: name-based uses the slice mapped to the first
                # column name; index-based always uses cells[0].
                if name_based:
                    marker_idx = slice_map.get(columns[0], 0)
                    marker_idx = marker_idx if marker_idx is not None else 0
                    marker = cells[marker_idx] if marker_idx < len(cells) else ""
                else:
                    marker = cells[0]
                if marker and re.match(compiled, marker.strip()):
                    row: Dict[str, str] = {}
                    for i, name in enumerate(columns):
                        if name_based:
                            idx = slice_map.get(name, i)
                            idx = idx if idx is not None else i
                        else:
                            idx = i
                        row[name] = cells[idx] if idx < len(cells) else ""
                    rows.append(row)

    return rows, page_count


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _normalize(text: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace for name matching."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _header_slice_mapping(
    page,
    page_header_top: Optional[float],
    boundaries: List[float],
    columns: List[str],
) -> Dict[str, Optional[int]]:
    """Map each column NAME to its physical slice index via the header line.

    NAME-BASED lookup: the physical header line at `page_header_top` is sliced
    with the same boundaries, and each column's normalized name is matched
    against each slice's normalized header text. This lets extraction pull the
    right physical column even when the LLM returns `columns` out of physical
    order (e.g. Debit physically at slice index 5, not 2). Columns that cannot
    be matched get None (caller decides the fallback).
    """
    mapping: Dict[str, Optional[int]] = {}
    if page_header_top is None:
        return mapping
    words = page.extract_words()
    header_words = [
        w for w in words
        if abs(round(w["top"], 1) - round(page_header_top, 1)) <= 1.5
    ]
    if not header_words:
        return mapping
    header_cells = _slice_words_to_columns(header_words, boundaries)
    for name in columns:
        target = _normalize(name)
        mapping[name] = next(
            (i for i, cell in enumerate(header_cells)
             if target and target in _normalize(cell)),
            None,
        )
    return mapping


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _clean_text(value: Any) -> str:
    """Normalize a cell value for emptiness checks."""
    if value is None:
        return ""
    return str(value).strip()


# ---------------------------------------------------------------------------
# Kabir: date canonicalization + raw extraction + the completeness check
# ---------------------------------------------------------------------------

# Canonical date/amount parsers live in data_transformers.py (single source of
# truth shared with the production pipeline). The assessor reuses them.
# canonicalize_date -> datetime.date | None, parse_amount -> float | None.

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _is_raw_date_cell(text: Any) -> bool:
    """Whether a raw cell matches any of the standard date patterns."""
    if text is None:
        return False
    t = _strip_trailing_time(str(text))
    if not t:
        return False
    return any(p.match(t) for p in _RAW_DATE_COMPILED)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def extract_raw_rows_date_filtered(
    pdf_path: str | Path,
) -> Tuple[List[Dict[str, Any]], Dict[_dt.date, int], List[int]]:
    """Independently extract the raw dated transaction rows from the PDF.

    Word-line based (matching the production extractor's visual-line model)
    with NO band_top / header_top / rows_dropped - those structural
    properties belong to the agent's proposal and would share its blindness
    (Hole A). A line counts when its first non-empty cell (the leftmost word)
    canonicalizes to a date.

    Returns:
        (rows, date_counts, per_page_counts) where rows is a list of
        {page, top, first_cell, date} dicts (first_cell = the raw date text),
        date_counts maps canonical date -> row count, and per_page_counts is
        the raw dated row count per page.
    """
    rows: List[Dict[str, Any]] = []
    date_counts: Dict[_dt.date, int] = {}
    per_page_counts: List[int] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            words = page.extract_words()
            lines: dict[float, list[dict]] = {}
            for w in words:
                lines.setdefault(round(w["top"], 1), []).append(w)

            page_count = 0
            for top in sorted(lines):
                ws = sorted(lines[top], key=lambda w: w["x0"])
                if not ws:
                    continue
                # The first non-empty cell is the leftmost word of the line.
                first_cell = ws[0]["text"].strip()
                d = canonicalize_date(first_cell)
                if d is None:
                    continue
                rows.append(
                    {"page": page_index + 1, "top": top, "first_cell": first_cell, "date": d}
                )
                date_counts[d] = date_counts.get(d, 0) + 1
                page_count += 1
            per_page_counts.append(page_count)

    return rows, date_counts, per_page_counts


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _build_date_array(
    llm_rows: List[Dict[str, str]],
    date_column: str,
    agent_date_pattern: str,
) -> Tuple[List[_dt.date], Dict[_dt.date, int], int]:
    """Build the Date Array from the AGENT's rows (the filter key).

    The array MUST come from the agent side: a raw-derived array covers every
    date in a healthy statement, so filtering both sides by it erases the loss
    signal symmetrically (the filter-symmetry trap).

    Returns:
        (unique_dates, per_date_counts, parse_failures) where parse_failures
        counts agent rows whose date cell could not be canonicalized.
    """
    unique: List[_dt.date] = []
    counts: Dict[_dt.date, int] = {}
    failures = 0

    for row in llm_rows:
        text = _clean_text(row.get(date_column, ""))
        d = canonicalize_date(text)
        if d is None:
            # Fall back to the agent's own date_pattern as a hint for exotic
            # formats the standard set does not cover.
            try:
                m = re.match(agent_date_pattern, text)
                if m and m.group(0) == text:
                    d = canonicalize_date(text)
            except re.error:
                d = None
            if d is None:
                failures += 1
                continue
        if d not in counts:
            unique.append(d)
        counts[d] = counts.get(d, 0) + 1

    return unique, counts, failures


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def run_kabir_check(
    raw_rows: List[Dict[str, Any]],
    llm_rows: List[Dict[str, str]],
    raw_date_counts: Dict[_dt.date, int],
    raw_per_page: List[int],
    llm_per_page: List[int],
    date_column: str,
    date_pattern: str,
) -> Dict[str, Any]:
    """Run the Kabir (completeness) check against the LLM structure's rows.

    Percentage ladder:
      - raw_dated == 0      -> inconclusive (patterns may not cover this
                               statement's format) -> defer to Saghir.
      - diff < PASS_PCT     -> PASS.
      - diff > FAIL_PCT     -> FAIL (template summary, no LLM).
      - otherwise           -> ADJUDICATE: Date Array from the agent's rows,
                               split raw leftovers into DatedLeftovers (hard
                               evidence of missed transactions -> FAIL) vs
                               UndatedLeftovers (benign debris -> Assessor LLM).
    """
    raw_dated = len(raw_rows)
    llm_rows_count = len(llm_rows)
    date_array, agent_date_counts, agent_failures = _build_date_array(
        llm_rows, date_column, date_pattern
    )
    agent_set = set(date_array)

    # Dated/Undated leftover split on the RAW side, using the agent-derived
    # Date Array. Raw rows whose canonical date is NOT in the agent's array
    # are DatedLeftovers (hard evidence of missed transactions).
    dated_leftovers: List[Dict[str, Any]] = []
    undated_leftovers: List[Dict[str, Any]] = []
    raw_cells_not_parsed = 0

    for rr in raw_rows:
        if rr["date"] in agent_set:
            continue
        if _is_raw_date_cell(rr["first_cell"]):
            dated_leftovers.append(rr)
        else:
            undated_leftovers.append(rr)
            if canonicalize_date(rr["first_cell"]) is None:
                raw_cells_not_parsed += 1

    if raw_dated == 0:
        tier = "INCONCLUSIVE"
        passed = True  # defer to Saghir - never auto-FAIL
        summary = (
            "Kabir raw extraction found 0 dated lines - the standard date "
            "patterns may not cover this statement's format. Deferring to "
            "Saghir; treat the verdict as Saghir-only."
        )
        diff_pct = None
    else:
        diff_pct = abs(raw_dated - llm_rows_count) / raw_dated * 100.0
        dated_block = sum(1 for r in dated_leftovers if r["date"] not in agent_set)
        if diff_pct < KABIR_PASS_PCT:
            tier = "PASS"
            passed = True
            summary = (
                f"Kabir completeness check PASSED: raw dated rows {raw_dated} "
                f"vs LLM structure rows {llm_rows_count} "
                f"(diff {diff_pct:.2f}% < {KABIR_PASS_PCT}%)."
            )
        elif diff_pct > KABIR_FAIL_PCT:
            tier = "FAIL"
            passed = False
            # Template summary: page-level diagnosis first.
            page_hits = []
            for i, (raw_p, llm_p) in enumerate(zip(raw_per_page, llm_per_page)):
                if llm_p == 0 and raw_p > 0:
                    page_hits.append(
                        f"page {i + 1} has {raw_p} raw dated rows but the LLM "
                        f"structure extracted 0"
                    )
            missing_dates = sorted({str(d) for d, _ in
                                    ((r["date"], 1) for r in dated_leftovers)})[:10]
            page_part = "; ".join(page_hits[:6]) if page_hits else (
                "no page is fully empty - the gap is spread across pages"
            )
            dates_part = (
                f" DatedLeftovers on dates {missing_dates}."
                if missing_dates
                else ""
            )
            summary = (
                f"FAIL: raw extraction found {raw_dated} dated rows but the "
                f"LLM structure extracted only {llm_rows_count} "
                f"(diff {diff_pct:.2f}% > {KABIR_FAIL_PCT}%). "
                f"{page_part}.{dates_part} Most likely cause: continuation-"
                f"page band_top/header_top too low, clipping whole pages."
            )
        else:
            tier = "ADJUDICATE"
            if dated_block > 0 and (
                dated_block / raw_dated > KABIR_TRIVIAL_LEFT_BLOCK
            ):
                # Hard evidence: raw rows on dates the agent never covered.
                passed = False
                missing_dates = sorted({str(r["date"]) for r in dated_leftovers})[:10]
                summary = (
                    f"FAIL: the LLM structure missed {dated_block} raw "
                    f"transaction row(s) on dates {missing_dates} that the "
                    f"agent's Date Array never covered (DatedLeftovers) - "
                    f"hard evidence of lost transactions. Likely cause: "
                    f"continuation-page band_top/header_top clipping rows, "
                    f"or a column slice dropping the date cell."
                )
            else:
                # Ambiguous middle: coverage looks complete, leftover is
                # benign debris - hand to the Assessor LLM.
                passed = None
                summary = (
                    f"Kabir diff {diff_pct:.2f}% is inside the "
                    f"{KABIR_PASS_PCT}%-{KABIR_FAIL_PCT}% band - "
                    f"adjudication required."
                )

    return {
        "tier": tier,
        "diff_pct": round(diff_pct, 4) if diff_pct is not None else None,
        "raw_dated": raw_dated,
        "llm_rows": llm_rows_count,
        "raw_per_page": raw_per_page,
        "llm_per_page": llm_per_page,
        "date_coverage": {
            "raw_unique_dates": len(raw_date_counts),
            "raw_per_date_counts": {str(k): v for k, v in raw_date_counts.items()},
            "agent_unique_dates": len(date_array),
            "agent_per_date_counts": {str(k): v for k, v in agent_date_counts.items()},
            "agent_date_parse_failures": agent_failures,
            "raw_cells_not_parsed": raw_cells_not_parsed,
        },
        "dated_leftovers": dated_leftovers[:15],
        "dated_leftover_count": len(dated_leftovers),
        "undated_leftovers": undated_leftovers[:15],
        "undated_leftover_count": len(undated_leftovers),
        "passed": passed,
        "summary": summary,
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _monthly_rollup(date_counts: Dict[_dt.date, int]) -> Dict[str, int]:
    """Roll per-date counts up to per-month totals (multi-year ledgers)."""
    rollup: Dict[str, int] = {}
    for d, n in date_counts.items():
        key = f"{d.year:04d}-{d.month:02d}"
        rollup[key] = rollup.get(key, 0) + n
    return dict(sorted(rollup.items()))


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_assessor_packet(
    assessment: Dict[str, Any],
    kabir: Dict[str, Any],
    raw_rows: List[Dict[str, Any]],
    raw_date_counts: Dict[_dt.date, int],
    columns: List[str],
    header_top: Any,
    band_top: Any,
    rows_dropped: int,
    boundaries: Optional[List[float]],
    date_pattern: str,
    opening_balance: Optional[float],
    reconciliation_type: str,
) -> Dict[str, Any]:
    """Build the context-controlled digest passed to the Assessor LLM.

    No full dumps: the packet is a structured summary - the agent's proposed
    structure, raw + agent date coverage (with monthly rollup for multi-year
    ledgers), per-page counts (catches offsetting errors), capped leftover
    samples, and the Saghir verdict. Caps keep the context bounded regardless
    of statement size.
    """
    cc = assessment.get("cumulative_check") or {}
    fc = assessment.get("final_check") or {}
    return {
        "structure": {
            "columns_pdf": columns,
            "header_words_pdf": [
                h for h in (assessment.get("column_mapping") or {}).keys()
            ] or [],
            "rows_dropped_pdf": rows_dropped,
            "header_top_pdf": header_top,
            "column_boundaries_pdf": boundaries or [],
            "band_top_pdf": band_top,
            "date_pattern_pdf": date_pattern,
            "opening_balance_pdf": opening_balance,
            "reconciliation_type": reconciliation_type,
        },
        "raw_date_coverage": {
            "unique_dates": len(raw_date_counts),
            "per_date_counts": {str(k): v for k, v in raw_date_counts.items()},
            "monthly_rollup": _monthly_rollup(raw_date_counts),
        },
        "agent_date_coverage": {
            "unique_dates": kabir["date_coverage"]["agent_unique_dates"],
            "per_date_counts": kabir["date_coverage"]["agent_per_date_counts"],
            "monthly_rollup": _monthly_rollup(
                {
                    _dt.date.fromisoformat(k): v
                    for k, v in kabir["date_coverage"]["agent_per_date_counts"].items()
                }
            ),
        },
        "per_page": [
            {
                "page": i + 1,
                "raw_dated": rp,
                "llm": lp,
            }
            for i, (rp, lp) in enumerate(
                zip(
                    kabir["raw_per_page"],
                    kabir["llm_per_page"],
                )
            )
        ],
        "dated_leftovers_capped": kabir["dated_leftovers"][:15],
        "undated_leftovers_capped": kabir["undated_leftovers"][:15],
        "saghir": {
            "passed": bool(cc.get("passed") and fc.get("passed")),
            "rows_checked": cc.get("rows_checked"),
            "first_mismatch_row": cc.get("first_mismatch_row"),
        },
        "raw_dated": kabir["raw_dated"],
        "llm_rows": kabir["llm_rows"],
        "diff_pct": kabir["diff_pct"],
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _assessor_instructions() -> str:
    """Classification-only instructions for the Assessor LLM (fail-safe bias)."""
    return """
You are the Kabir adjudicator for a PDF bank/vendor statement structure
assessor. Your ONLY job is to classify whether a row-count difference between
an independently raw-extracted baseline and an LLM-proposed structure is REAL
data/entry loss, or benign structural noise (wrapped sub-lines, merged cells,
headers, footers, subtotals, page numbers).

You must NEVER do entry-level matching or identify individual discrepancies.
You receive a structured digest (the packet). Judge the digest only.

The verdict rules:
- PASS only if the difference is fully explained by benign artifacts
  (wrapping, merged cells, headers, footers, subtotals) AND the date coverage
  is complete (no date range or page appears only on the raw side).
- FAIL on ANY date or page gap, or ANY per-date count anomaly, citing which
  page(s)/date range(s) and the likely structure parameter to fix (e.g.
  "page 4 covers 08-Mar -> 22-Mar, entirely absent -> continuation band_top
  wrong", or "the raw side has 30 unique dates but the agent covered only 8 -
  pages 2-6 are likely missing entirely").
- Cost asymmetry is explicit: a false PASS = silent data loss; a false FAIL =
  one extra agent iteration. When unsure, FAIL.

Output ONLY a JSON object, nothing else:
{"passed": true|false, "summary": "one actionable paragraph"}
""".strip()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def run_assessor_agent(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Run the nested Assessor LLM (OpenAI Agents SDK) on the packet.

    Classification only. Uses settings.AI_MODEL / AI_API_KEY like the main
    structure-detection agent; when no model is configured the SDK falls back
    to the provider's own env var (e.g. GOOGLE_API_KEY). Synchronous by
    design - the assessor itself is a blocking tool.
    """
    import json

    from agents import Agent, Runner

    from src.config import settings

    model = None
    if settings.AI_MODEL or settings.AI_API_KEY:
        from agents.extensions.models.litellm_model import LitellmModel

        model = LitellmModel(model=settings.AI_MODEL or "gemini/gemini-2.0-flash",
                             api_key=settings.AI_API_KEY)

    adjudicator = Agent(
        name="Kabir adjudicator",
        instructions=_assessor_instructions(),
        model=model,
    )

    result = Runner.run_sync(
        adjudicator,
        "Packet:\n" + json.dumps(packet, indent=2, default=str),
        max_turns=25,
    )
    out = (result.final_output or "").strip()
    try:
        parsed = json.loads(out)
    except json.JSONDecodeError:
        # Fail-safe: an unparseable response cannot justify a PASS.
        return {
            "passed": False,
            "summary": "Adjudicator returned an unparseable response: "
            + out[:300],
        }
    return {
        "passed": bool(parsed.get("passed")),
        "summary": str(parsed.get("summary") or ""),
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _ihsan_instructions() -> str:
    """Closing-balance read instructions for the Ihsan agent (fail-safe bias)."""
    return """
You are the Yabluwa al Ihsan reader for a PDF bank/vendor statement. Your ONLY
job is to find and return the statement's CLOSING BALANCE — the final running
balance printed at the end of the statement's transactions — with the page you
read it from.

Rules:
- The closing balance is the LAST Cumulative/Balance/Closing Balance figure
  in the statement, printed after the final transaction (often on the last
  page, or on the last page that actually contains a balance row — signature
  and annex pages carry no balance).
- If the LAST page carries no balance figure (blank page, signature page,
  annex, "End of Statement"), check the page before it, and so on backwards.
- Return the figure EXACTLY as printed, including sign conventions:
  a parenthesized figure (12,345.67) is NEGATIVE; a leading "-" is negative.
  Do NOT drop a trailing decimal separator. Keep the number as a string.
- If NO page in the whole statement carries a closing/balance figure, emit the
  block with `balance: not_found` — do NOT guess or force a figure.

OUTPUT FORMAT (this is critical):
  - Output EXACTLY ONE block, nothing before it and nothing after it, of the
    form:
    ~~~
    [output]
    balance: 1,234,567.89
    ~~~
  - The `balance:` value is the closing figure exactly as printed (a string
    that may contain commas and a leading minus or parentheses).
  - Optional (recommended) extra lines, one per line:
        page: 7
        label: Closing Balance
    `page` is the 1-based page number where the figure was read; `label` is
    the text/context you read the figure from.
  - When no closing balance exists anywhere, the block must be:
    ~~~
    [output]
    balance: not_found
    ~~~
  - The ~~~ [output] ... ~~~ markers are required. Do NOT write any prose,
    explanation, or extra text before or after the block. The block IS your
    entire response.
""".strip()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _ihsan_page_text_tool(pdf_path: str | Path, max_pages: int = 6):
    """Create a tool for the Ihsan agent to read the tail pages of a PDF.

    Returns a callable `read_tail_pages(from_page, to_page)` bound to the
    file, emitting each page's words as plain readable text lines (no word
    geometry - the agent only needs to READ a printed figure, not locate
    columns). The tool shows page numbers in 1-based form to match the agent
    contract.
    """
    import pdfplumber as _pdfplumber

    @tool
    def read_tail_pages(from_page: int = 1, to_page: int = 1) -> str:
        """Read the text of PDF pages [from_page, to_page] (1-based, inclusive).

        Returns each page's words grouped into readable lines. Page numbers
        are 1-based: page 1 is the first page. Use this to find the statement's
        printed CLOSING BALANCE: it is the last Balance/Cumulative figure in
        the transaction table, usually near the end of the PDF.
        """
        with _pdfplumber.open(str(pdf_path)) as pdf:
            total = len(pdf.pages)
            if from_page < 1 or to_page < from_page or from_page > total:
                return (
                    f"Invalid page range [{from_page}, {to_page}]: this PDF has "
                    f"{total} page(s)."
                )
            to_page = min(to_page, total)
            out = []
            for p in range(from_page - 1, to_page):
                words = pdf.pages[p].extract_words()
                visual_lines: dict[float, list[dict]] = {}
                for w in words:
                    visual_lines.setdefault(round(w["top"], 1), []).append(w)
                out.append(f"--- PAGE {p + 1} (1-based) ---")
                for top in sorted(visual_lines):
                    row_words = sorted(visual_lines[top], key=lambda w: w["x0"])
                    out.append(" ".join(w["text"] for w in row_words))
            return "\n".join(out) if out else f"No words found on pages {from_page}-{to_page}."

    return read_tail_pages


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _parse_ihsan_output_block(raw: str) -> Dict[str, Any]:
    """Deterministically parse the Ihsan agent's ~~~ [output] ~~~ block.

    The agent emits exactly one block:
        ~~~
        [output]
        balance: 1,234,567.89
        page: 7
        label: Closing Balance
        ~~~
    `balance` is required. `not_found` means the agent found no closing
    balance anywhere. Returns a dict with found/closing_balance/page/label.
    Raises ValueError when the block or `balance` line is missing/malformed.
    """
    import re as _re

    text = raw.strip()
    m = _re.search(r"~~~\s*\[output\]\s*(.*?)\s*~~~", text, _re.DOTALL)
    if not m:
        m = _re.search(r"\[output\]\s*(.*?)\s*~~~", text, _re.DOTALL)
    if not m:
        raise ValueError(f"No [output] block found in Ihsan response:\n{raw}")

    body = m.group(1).strip()
    data: Dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip().lower()
        value = value.strip()
        if name:
            data[name] = value

    balance_raw = data.get("balance", "").strip().lower()
    if not balance_raw:
        raise ValueError(f"Ihsan block missing 'balance' line:\n{raw}")
    if balance_raw == "not_found":
        return {
            "found": False,
            "closing_balance": None,
            "page": None,
            "label": None,
        }
    page_raw = data.get("page", "").strip()
    page: Optional[int] = None
    try:
        page = int(float(page_raw)) if page_raw else None
    except ValueError:
        page = None
    return {
        "found": True,
        "closing_balance": balance_raw,
        "page": page,
        "label": data.get("label", "").strip() or None,
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def run_ihsan_agent(
    pdf_path: str | Path,
    max_pages: int = 6,
) -> Dict[str, Any]:
    """Run the Ihsan closing-balance reader agent on the PDF's tail pages.

    Nested OpenAI Agents SDK Agent (same model wiring as the Kabir
    adjudicator). It searches the last pages for the statement's printed
    CLOSING BALANCE, falling back backwards through pages when the last page
    carries no balance. The agent emits a ~~~ [output] ~~~ block with a
    `balance:` line; the block is parsed deterministically here. Returns:
        {
          "found": bool,
          "page": int | None,          # 1-based page where the balance was read
          "closing_balance": str | None,  # exactly as printed (signed)
          "label": str | None,
          "passed": bool | None,       # None when inconclusive/not found
          "summary": str,
        }
    Fail-safe: any exception or unparseable response -> INCONCLUSIVE
    (passed=None), never a silent pass or a hard fail.
    """
    from agents import Agent, Runner

    from src.config import settings

    model = None
    if settings.AI_MODEL or settings.AI_API_KEY:
        from agents.extensions.models.litellm_model import LitellmModel

        model = LitellmModel(
            model=settings.AI_MODEL or "gemini/gemini-2.0-flash",
            api_key=settings.AI_API_KEY,
        )

    reader = Agent(
        name="Yabluwa al Ihsan closing-balance reader",
        instructions=_ihsan_instructions(),
        model=model,
        tools=[_ihsan_page_text_tool(pdf_path, max_pages=max_pages)],
    )

    try:
        result = Runner.run_sync(
            reader,
            (
                "Find the CLOSING BALANCE of this bank/vendor statement and "
                "return it in the required [output] block, exactly as printed."
            ),
            max_turns=25,
        )
        parsed = _parse_ihsan_output_block(result.final_output or "")
        if not parsed["found"]:
            return {
                "found": False,
                "page": None,
                "closing_balance": None,
                "label": None,
                "passed": None,
                "summary": (
                    "Ihsan could not find a closing balance anywhere in the "
                    "statement - inconclusive, deferring to Saghir + Kabir."
                ),
            }
        return {
            "found": True,
            "page": parsed["page"],
            "closing_balance": parsed["closing_balance"],
            "label": parsed["label"],
            "passed": None,  # set by the caller after the arithmetic check
            "summary": (
                f"Closing balance {parsed['closing_balance']} read"
                + (f" on page {parsed['page']}" if parsed["page"] else "")
                + (f" (label: {parsed['label']})" if parsed["label"] else "")
            ),
        }
    except Exception as e:
        return {
            "found": False,
            "page": None,
            "closing_balance": None,
            "label": None,
            "passed": None,
            "summary": f"Ihsan reader failed to run: {e}",
        }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def run_ihsan_check(
    opening_balance: Optional[float],
    net_change: Optional[float],
    closing_balance: Optional[float],
    tolerance: float = BALANCE_TOLERANCE,
) -> Dict[str, Any]:
    """Arithmetic comparison for Ihsan: opening + net change vs closing balance.

    `net_change` is already signed under the active reconciliation convention
    (bank: credits - debits; vendor: debits - credits), so this check is
    convention-agnostic. When `closing_balance` is None (inconclusive read),
    the check reports passed=None (defer), never a hard fail.
    """
    if closing_balance is None:
        return {
            "passed": None,
            "diff": None,
            "final_from_opening": None,
            "closing_balance": None,
            "reason": "closing balance not available (inconclusive read)",
        }
    if opening_balance is None or net_change is None:
        return {
            "passed": False,
            "diff": None,
            "final_from_opening": None,
            "closing_balance": closing_balance,
            "reason": "missing opening balance or net change",
        }
    final = opening_balance + net_change
    diff = abs(final - closing_balance)
    return {
        "passed": diff <= tolerance,
        "diff": round(diff, 2),
        "final_from_opening": round(final, 2),
        "closing_balance": closing_balance,
        "reason": "ok",
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _pretty(assessment: Dict[str, Any]) -> str:
    """Render the assessment dict as a readable block for the agent/CLI."""
    lines_out = [
        "========================================",
        " PDF STRUCTURE ASSESSMENT",
        "========================================",
        f"  Rows extracted (LLM structure) : {assessment.get('total_rows', 0)}",
        f"  Pages                          : {assessment.get('page_count', 0)}",
        f"  Date lines                     : {assessment.get('date_matching_count', 0)}",
        f"  Reconciliation type            : {assessment.get('reconciliation_type', 'bank')}",
        f"  Opening balance                : {assessment.get('opening_balance', 'n/a')}",
        f"  Debit total                    : {assessment.get('debit_total', 'n/a')}",
        f"  Credit total                   : {assessment.get('credit_total', 'n/a')}",
        f"  Net change (per convention)    : {assessment.get('net_change', 'n/a')}",
        f"  Final from opening             : {assessment.get('final_from_opening', 'n/a')}",
        f"  Last cumulative                : {assessment.get('last_cumulative', 'n/a')}",
        f"  Overall pass                   : {assessment.get('overall_pass', False)}",
        "----------------------------------------",
    ]
    skip = assessment.get("balance_check_skipped")
    if skip:
        lines_out.append(f"  BALANCE CHECK SKIPPED: {skip}")
        lines_out.append("----------------------------------------")
    else:
        cc = assessment.get("cumulative_check") or {}
        fc = assessment.get("final_check") or {}
        lines_out.append("  Cumulative (per-row sweep) [SAGHIR]:")
        lines_out.append(
            f"    passed={cc.get('passed')}, rows_checked={cc.get('rows_checked')}, "
            f"mismatches={len(cc.get('mismatches') or [])}, "
            f"max_abs_error={cc.get('max_abs_error')}"
        )
        if cc.get("first_mismatch_row"):
            fm = cc["first_mismatch_row"]
            lines_out.append(
                f"    first mismatch: row {fm['row_index']} ('{fm['date']}') "
                f"running={fm['running_balance']} cumulative={fm['cumulative']}"
            )
        lines_out.append("  Final check (opening + net vs last cumulative):")
        lines_out.append(
            f"    passed={fc.get('passed')}, diff={fc.get('diff')}"
        )
        lines_out.append("----------------------------------------")

    kb = assessment.get("kabir_check") or {}
    if kb:
        lines_out.append("  KABIR (completeness) check:")
        lines_out.append(
            f"    tier={kb.get('tier')}, raw_dated={kb.get('raw_dated')}, "
            f"llm_rows={kb.get('llm_rows')}, diff_pct={kb.get('diff_pct')}"
        )
        lines_out.append(
            f"    passed={kb.get('passed')}, "
            f"dated_leftovers={kb.get('dated_leftover_count')}, "
            f"undated_leftovers={kb.get('undated_leftover_count')}"
        )
        if kb.get("date_coverage"):
            dc = kb["date_coverage"]
            lines_out.append(
                f"    raw_unique_dates={dc.get('raw_unique_dates')}, "
                f"agent_unique_dates={dc.get('agent_unique_dates')}, "
                f"agent_parse_failures={dc.get('agent_date_parse_failures')}"
            )
        if kb.get("summary"):
            lines_out.append(f"    summary: {kb['summary']}")
        lines_out.append("----------------------------------------")

    ih = assessment.get("ihsan_check") or {}
    if ih:
        lines_out.append("  IHSAN (closing-balance anchor) check:")
        lines_out.append(
            f"    ran={ih.get('ran')}, found={ih.get('found')}, "
            f"passed={ih.get('passed')}"
        )
        if ih.get("closing_balance") is not None:
            lines_out.append(
                f"    closing_balance={ih.get('closing_balance')}"
                + (f" (page {ih.get('page')})" if ih.get("page") is not None else "")
                + (f" (label: {ih.get('label')})" if ih.get("label") else "")
            )
            lines_out.append(
                f"    final_from_opening={ih.get('final_from_opening')}, "
                f"diff={ih.get('diff')}"
            )
        if ih.get("summary"):
            lines_out.append(f"    summary: {ih['summary']}")
        lines_out.append("----------------------------------------")

    for p in assessment["per_page"]:
        lines_out.append(
            f"  Page {p['page']}: band_top={p['band_top']}, "
            f"header_top={p['header_top']}, in_band_lines={p['in_band_lines']}, "
            f"date_lines={p['date_matching_lines']}, rows={p['row_count']}"
        )
    lines_out.append("----------------------------------------")
    lines_out.append("  Column fill:")
    for cs in assessment["columns"]:
        lines_out.append(
            f"    {cs['name']:<20} {cs['filled']:>4}/{cs['total']:<4} "
            f"({cs['fill_rate'] * 100:>5.1f}%)"
        )

    # Column-name -> physical slice mapping (name-based only).
    mapping = assessment.get("column_mapping") or {}
    if mapping:
        lines_out.append("----------------------------------------")
        lines_out.append("  Column -> physical slice mapping:")
        for name, idx in mapping.items():
            lines_out.append(f"    {name:<20} -> slice[{idx}]")

    # Extracted rows as a clean fixed-width table.
    rows = assessment.get("extracted_rows", [])
    if rows:
        lines_out.append("----------------------------------------")
        lines_out.append("  EXTRACTED ROWS (values as they would be returned):")
        headers = list(rows[0].keys())
        widths = {h: max(len(h), max((len(str(r.get(h, ""))) for r in rows), default=0)) for h in headers}
        def _fmt(h, v):
            return str(v)[:widths[h]].ljust(widths[h])
        lines_out.append("  " + " | ".join(h.ljust(widths[h]) for h in headers))
        lines_out.append("  " + "-+-".join("-" * widths[h] for h in headers))
        for r in rows:
            lines_out.append("  " + " | ".join(_fmt(h, r.get(h, "")) for h in headers))
    else:
        lines_out.append("----------------------------------------")
        lines_out.append("  (no rows extracted - nothing to show in a table)")

    if assessment["issues"]:
        lines_out.append("----------------------------------------")
        lines_out.append("  Issues:")
        for i in assessment["issues"]:
            lines_out.append(f"    - {i}")
    if assessment["suggestions"]:
        lines_out.append("----------------------------------------")
        lines_out.append("  Suggestions:")
        for s in assessment["suggestions"]:
            lines_out.append(f"    - {s}")
    lines_out.append("========================================")
    return "\n".join(lines_out)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _resolve_role(
    columns: List[str],
    role_name: Optional[str],
) -> Optional[int]:
    """Resolve a column ROLE to its index in `columns` by EXACT name.

    The agent names the exact header text for each role (e.g.
    pdf_debit_column="Debit", pdf_balance_column="Closing Balance"), and that
    exact name must be one of the entries in `columns` (columns_pdf). No fuzzy
    substring guessing: a role that is not named (None) or not found in the
    column list resolves to None, and the caller decides how to handle it
    (skip the check with a clear message) rather than matching the wrong
    column silently.
    """
    if not role_name:
        return None
    target = _normalize(role_name)
    if not target:
        return None
    for i, name in enumerate(columns):
        if name == role_name or _normalize(name) == target:
            return i
    return None


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _amount_columns(
    columns: List[str],
    pdf_debit_column: Optional[str] = None,
    pdf_credit_column: Optional[str] = None,
    pdf_debit_credit_combined_column: Optional[str] = None,
    pdf_balance_column: Optional[str] = None,
) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """Locate (debit_idx, credit_idx, balance_idx, combined_idx) for the rows.

    All roles resolve by EXACT name from the agent-provided role columns.
    Exactly one amount form is used:
      - separate: debit_idx and credit_idx are set, combined_idx is None.
      - combined: combined_idx is set, debit_idx and credit_idx are None.
    `balance_idx` resolves from pdf_balance_column by exact name.
    """
    debit_idx = _resolve_role(columns, pdf_debit_column)
    credit_idx = _resolve_role(columns, pdf_credit_column)
    combined_idx = _resolve_role(columns, pdf_debit_credit_combined_column)
    balance_idx = _resolve_role(columns, pdf_balance_column)
    return debit_idx, credit_idx, balance_idx, combined_idx


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _signed_amount(
    row: Dict[str, str],
    debit_idx: int,
    credit_idx: int,
    columns: List[str],
    reconciliation_type: str = "bank",
    combined_idx: Optional[int] = None,
) -> Optional[float]:
    """Signed amount for a row under the chosen sign convention.

    The Debit/Credit columns are always unsigned magnitudes; the sign they
    carry depends on whose books the statement belongs to:

      - bank:    Credit is money in (+) and Debit is money out (-), so the
                 signed amount is credit - debit.
      - vendor:  the roles invert (a vendor ledger records a credit as a
                 debt the vendor owes you, i.e. negative, and a debit as
                 money you owe, i.e. positive), so the signed amount is
                 debit - credit.

    The row's Cumulative Balance column is compared directly, so only the
    sign applied to the two amount columns flips between the two types.

    When `combined_idx` is given (rare combined Debit/Credit column), the
    cell already carries its sign: negative = debit, positive = credit. The
    signed value is the cell itself, sign-normalized to the reconciliation
    convention.
    """
    if combined_idx is not None:
        amount = parse_amount(row.get(columns[combined_idx]))
        if amount is None:
            return None
        # The combined cell's own sign already encodes debit (negative) vs
        # credit (positive) for a bank statement; for a vendor ledger the
        # roles invert, so flip the sign.
        if reconciliation_type == "vendor":
            return -amount
        return amount
    debit = parse_amount(row.get(columns[debit_idx]))
    credit = parse_amount(row.get(columns[credit_idx]))
    if debit is None and credit is None:
        return None
    if reconciliation_type == "vendor":
        return (debit or 0.0) - (credit or 0.0)
    return (credit or 0.0) - (debit or 0.0)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _run_cumulative_check(
    rows: List[Dict[str, str]],
    debit_idx: int,
    credit_idx: int,
    balance_idx: int,
    columns: List[str],
    opening_balance: Optional[float],
    reconciliation_type: str = "bank",
    combined_idx: Optional[int] = None,
) -> Dict[str, Any]:
    """Per-row running-balance sweep against the statement's cumulative column.

    Starting from `opening_balance`, add each row's signed amount and compare
    the running total with that row's Cumulative Balance value. The first row
    whose cumulative diverges pinpoints the first missed/misparsed transaction.

    SPARSE BALANCE SUPPORT (Habib-style statements): the running total ALWAYS
    advances on every row, but the comparison against the Cumulative Balance
    column is performed ONLY on rows that actually carry a printed balance
    cell. Habib prints one balance per day-group (4 rows on 22 May, balance
    only on the 4th) - under the old logic a row with no balance was skipped
    wholesale (running did not advance), so the 4th row compared
    opening + row4 vs its balance and mismatched. Now every transaction
    contributes, and the check fires only where the statement itself printed
    a balance, which is exactly the number of checks that can be made.

    Returns a dict with passed/rows_checked/mismatches/first_mismatch_row/
    max_abs_error, plus the parsed cumulative values for the final check.
    `rows_checked` counts rows where a balance cell was present AND compared.
    """
    mismatches: List[Dict[str, Any]] = []
    parsed_cumulative: List[float] = []
    parsing_errors: List[int] = []

    running = opening_balance
    checked = 0
    for i, row in enumerate(rows):
        signed = _signed_amount(
            row, debit_idx, credit_idx, columns, reconciliation_type, combined_idx
        )
        cum = parse_amount(row.get(columns[balance_idx]))
        if cum is not None:
            parsed_cumulative.append(cum)

        if signed is None:
            parsing_errors.append(i)
            continue

        if running is None:
            running = 0.0
        running += signed

        # Sparse balance support: only COMPARE when this row carries a printed
        # balance cell. The running total has already advanced either way.
        if cum is None:
            continue

        checked += 1
        diff = abs(running - cum)
        if diff > BALANCE_TOLERANCE:
            mismatches.append(
                {
                    "row_index": i,
                    "date": _clean_text(row.get(columns[0])),
                    "running_balance": round(running, 2),
                    "cumulative": cum,
                    "diff": round(diff, 2),
                }
            )

    return {
        "passed": not mismatches,
        "rows_checked": checked,
        "parsing_errors": parsing_errors,
        "mismatches": mismatches,
        "first_mismatch_row": mismatches[0] if mismatches else None,
        "max_abs_error": round(max((m["diff"] for m in mismatches), default=0.0), 2),
        "cumulative_values": parsed_cumulative,
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _run_final_check(
    opening_balance: Optional[float],
    net_change: Optional[float],
    last_cumulative: Optional[float],
) -> Dict[str, Any]:
    """Opening + net change vs the last cumulative balance value.

    `net_change` is already signed under the active reconciliation
    convention (bank: credits - debits; vendor: debits - credits), so this
    check is convention-agnostic.
    """
    if opening_balance is None or last_cumulative is None:
        return {"passed": False, "diff": None, "reason": "missing values"}
    final = opening_balance + net_change
    diff = abs(final - last_cumulative)
    return {
        "passed": diff <= BALANCE_TOLERANCE,
        "diff": round(diff, 2),
        "final_from_opening": round(final, 2),
        "last_cumulative": last_cumulative,
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def assess_pdf_structure(
    pdf_path: str | Path,
    columns: List[str],
    header_top: Optional[float | List[Optional[float]]] = None,
    rows_dropped: int = 0,
    boundaries: Optional[List[float]] = None,
    band_top: Optional[float | List[Optional[float]]] = None,
    date_pattern: str = DEFAULT_DATE_PATTERN,
    name_based: bool = True,
    opening_balance: Optional[float] = None,
    reconciliation_type: str = "bank",
    run_kabir: bool = True,
    use_assessor_llm: bool = True,
    use_ihsan: bool = True,
    request_id: Optional[str] = None,
    # ---- Explicit PDF column roles (agent-provided, replace fuzzy matching) --
    pdf_transaction_date_column: Optional[str] = None,
    pdf_details_column: Optional[str] = None,
    pdf_debit_column: Optional[str] = None,
    pdf_credit_column: Optional[str] = None,
    pdf_debit_credit_combined_column: Optional[str] = None,
    pdf_balance_column: Optional[str] = None,
) -> Dict[str, Any]:
    """Assess how well the proposed structure would extract transaction rows.

    Runs the production extraction logic with the given structure, then
    validates the extracted data against the statement's own arithmetic
    (running balance vs the Cumulative Balance column, and opening + net
    change vs the final cumulative) - Yabluwa al Saghir - and against the
    raw dated row count - Yabluwa al Kabir - and finally against the
    statement's printed CLOSING BALANCE read from the tail pages by a
    nested agent - Yabluwa al Ihsan. Returns a diagnostic dict the
    LLM agent can use to correct its own output.

    Verdict composition (STRICT SHORT-CIRCUIT):
        overall_pass = saghir.passed AND kabir.passed AND ihsan.passed
    Kabir runs only when Saghir passed; Ihsan runs only when Saghir AND
    Kabir both passed. An INCONCLUSIVE Ihsan (closing balance not found)
    defers to the two deterministic checks and does not fail the verdict.

    COLUMN ROLES: the agent names the exact columns_pdf entry for each role
    (pdf_transaction_date_column, pdf_details_column, and the amount columns
    in exactly one of the separate/combined forms, plus an optional
    pdf_balance_column). When the roles are provided they are resolved by
    EXACT name against `columns`; when absent, a legacy fuzzy fallback is
    used (substring matching) so existing callers/tests keep working.

    Args:
        pdf_path: Path to the .pdf bank statement.
        columns: Proposed column names (left-to-right visual order).
        header_top: Proposed header top (scalar or per-page list).
        rows_dropped: Proposed number of visual lines above the header.
        boundaries: Proposed physical x-coordinates of the column edges.
        band_top: Proposed upper vertical boundary of the transaction band.
        date_pattern: Proposed regex for the first-column transaction dates.
        opening_balance: Optional opening balance the agent read from the
            statement header (auto-verified against the first cumulative row).
        reconciliation_type: Which books the statement belongs to. "bank"
            (default) keeps Credit as + and Debit as -; "vendor" inverts
            them (Credit -, Debit +) because a vendor ledger's credit/debit
            roles are reversed relative to a bank statement.
        run_kabir: Whether to run the Kabir completeness check (default True).
        use_assessor_llm: Whether the Kabir adjudicate band may call the
            Assessor LLM (default True; set False in deterministic tests).
        use_ihsan: Whether to run the Ihsan closing-balance check after
            Saghir + Kabir pass (default True).
        request_id: Optional request id for cancellation registry checks.
        pdf_transaction_date_column: Exact name of the date column (optional).
        pdf_details_column: Exact name of the description column (optional).
        pdf_debit_column: Exact name of the Debit column (separate form).
        pdf_credit_column: Exact name of the Credit column (separate form).
        pdf_debit_credit_combined_column: Exact name of the combined
            Debit/Credit column (combined form, rare).
        pdf_balance_column: Exact name of the running Balance/Cumulative
            column (optional).

    Returns:
        A plain dict (JSON-serializable for LLM consumption):
            {
              "total_rows": int,
              "page_count": int,
              "per_page": [...],
              "columns": [...],
              "date_matching_count": int,
              "score": float (0-100),
              "opening_balance": float | None,
              "reconciliation_type": str,
              "debit_total": float | None,
              "credit_total": float | None,
              "net_change": float | None,
              "final_from_opening": float | None,
              "last_cumulative": float | None,
              "cumulative_check": {...},   # Saghir per-row sweep
              "final_check": {...},        # Saghir final check
              "kabir_check": {...},        # Kabir completeness check
              "ihsan_check": {...},        # Ihsan closing-balance check
              "overall_pass": bool,        # saghir AND kabir AND ihsan
              "balance_check_skipped": str | None,
              "parsing_errors": [int],
              "issues": [str],
              "suggestions": [str],
            }
    """
    if not columns:
        return {
            "total_rows": 0,
            "page_count": 0,
            "per_page": [],
            "columns": [],
            "date_matching_count": 0,
            "score": 0.0,
            "opening_balance": opening_balance,
            "debit_total": None,
            "credit_total": None,
            "net_change": None,
            "final_from_opening": None,
            "last_cumulative": None,
            "cumulative_check": None,
            "final_check": None,
            "kabir_check": None,
            "overall_pass": False,
            "balance_check_skipped": "columns list is empty - nothing to assess.",
            "parsing_errors": [],
            "issues": ["columns list is empty - nothing to assess."],
            "suggestions": ["Provide at least one column name (the first column "
                            "must be the transaction-date column)."],
        }

    # Determine the page count first so per-page values can be normalized
    # against the agent's contract (scalar = same on all pages; list = the
    # values for pages 1..N with the LAST as canonical for the rest).
    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)

    # Enforce the per-page contract for the two structural properties that
    # can differ between page 1 and the canonical pages (band/header only -
    # the table columns/boundaries are always global).
    try:
        band_top = normalize_per_page(band_top, page_count, "band_top")
        header_top = normalize_per_page(header_top, page_count, "header_top")
    except ValueError as e:
        return {
            "total_rows": 0,
            "page_count": page_count,
            "per_page": [],
            "columns": [],
            "date_matching_count": 0,
            "score": 0.0,
            "opening_balance": opening_balance,
            "debit_total": None,
            "credit_total": None,
            "net_change": None,
            "final_from_opening": None,
            "last_cumulative": None,
            "cumulative_check": None,
            "final_check": None,
            "kabir_check": None,
            "overall_pass": False,
            "balance_check_skipped": str(e),
            "parsing_errors": [],
            "issues": [str(e)],
            "suggestions": ["Emit band_top and header_top as a single scalar "
                            "when all pages match, or [page1, page2] when "
                            "page 1 differs from the canonical pages."],
        }

    rows, _ = extract_pdf_words(
        pdf_path=pdf_path,
        columns=columns,
        header_top=header_top,
        rows_dropped=rows_dropped,
        boundaries=boundaries,
        band_top=band_top,
        date_pattern=date_pattern,
        name_based=name_based,
    )

    # Column-name -> physical slice index mapping (name-based only).
    column_mapping: Dict[str, Optional[int]] = {}
    if name_based:
        with pdfplumber.open(str(pdf_path)) as pdf:
            first_header = _per_page(header_top, 0)
            column_mapping = _header_slice_mapping(
                pdf.pages[0], first_header, boundaries or [], columns
            )

    compiled = re.compile(date_pattern)
    per_page: List[Dict[str, Any]] = []
    date_matching_count = 0
    issues: List[str] = []
    suggestions: List[str] = []

    # Re-run the production extraction once per page to bucket rows by page.
    per_page_rows = _extract_rows_per_page(
        pdf_path=pdf_path,
        columns=columns,
        header_top=header_top,
        boundaries=boundaries,
        band_top=band_top,
        date_pattern=date_pattern,
        name_based=name_based,
    )

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            page_header_top = _page_header_top(header_top, band_top, page_index)
            page_band_top = _per_page(band_top, page_index)

            words = page.extract_words()
            lines: dict[float, list[dict]] = {}
            for w in words:
                top = round(w["top"], 1)
                in_band = page_band_top is None or top >= page_band_top
                below_header = page_header_top is None or top >= page_header_top + 4.0
                if in_band and below_header:
                    lines.setdefault(top, []).append(w)

            date_lines = sum(
                1
                for top, ws in lines.items()
                if any(re.match(compiled, w["text"].strip()) for w in ws)
            )
            date_matching_count += date_lines

            per_page.append(
                {
                    "page": page_index + 1,
                    "band_top": page_band_top,
                    "header_top": page_header_top,
                    "in_band_lines": len(lines),
                    "date_matching_lines": date_lines,
                    "row_count": per_page_rows[page_index],
                }
            )

    # Per-column fill statistics over the extracted rows.
    col_stats: List[Dict[str, Any]] = []
    for name in columns:
        total = len(rows)
        filled = sum(1 for r in rows if _clean_text(r.get(name, "")))
        col_stats.append(
            {
                "name": name,
                "total": total,
                "filled": filled,
                "fill_rate": round(filled / total, 4) if total else 0.0,
                "empty": total - filled,
            }
        )

    # ---- Structural mismatch: LLM columns vs physical header order ---------
    # The production extractor uses `cells[0]` as the row marker and assigns
    # by list index, so the LLM's `columns` order MUST match the physical
    # left-to-right order of the header line. Name-based extraction rescues
    # misaligned values, but the *structure itself* may still be wrong - the
    # assessor reports that gap so the agent can fix columns_pdf order.
    if name_based and column_mapping:
        # Recover the true physical header cell texts once.
        with pdfplumber.open(str(pdf_path)) as pdf:
            first_header = _per_page(header_top, 0)
            words0 = pdf.pages[0].extract_words()
            header_words0 = [
                w for w in words0
                if abs(round(w["top"], 1) - round(first_header, 1)) <= 1.5
            ] if first_header is not None else []
            physical_cells = (
                _slice_words_to_columns(header_words0, boundaries or [])
                if header_words0 else []
            )

        if physical_cells:
            for i, name in enumerate(columns):
                mapped = column_mapping.get(name)
                if mapped is None:
                    issues.append(
                        f"Column '{name}' (position {i} in columns_pdf) was NOT "
                        f"found in the physical header line. It is likely "
                        f"hallucinated or named differently on the page."
                    )
                    suggestions.append(
                        f"Use the exact header text from read_pdf_words for "
                        f"column '{name}', or remove it if it doesn't exist."
                    )
                elif mapped != i:
                    issues.append(
                        f"Column '{name}' is at position {i} in columns_pdf, "
                        f"but its physical header sits at slice index {mapped} "
                        f"(header cell: '{physical_cells[mapped]}'). The "
                        f"columns_pdf ORDER does not match the physical order."
                    )
                    suggestions.append(
                        f"Reorder columns_pdf so '{name}' is at index {mapped} "
                        f"(physical left-to-right order), or fix the column "
                        f"boundaries so it is."
                    )

            # The row marker in production is cells[0]. If the LLM's first
            # column is not the physical first slice, the date marker is wrong.
            first_mapped = column_mapping.get(columns[0])
            if first_mapped is not None and first_mapped != 0:
                issues.append(
                    f"The first column '{columns[0]}' maps to physical slice "
                    f"{first_mapped}, not slice 0. Production uses cells[0] as "
                    f"the transaction-row date marker, so rows may be missed."
                )
                suggestions.append(
                    f"Ensure columns_pdf[0] is the physical leftmost column "
                    f"(the date column), or pass a date_pattern that matches "
                    f"whatever slice is at physical index 0."
                )

    # ---- Arithmetic balance check (Saghir - the correctness verdict) -------
    # Role columns come from the agent by EXACT name (no fuzzy guessing):
    # debit/credit/combined/balance resolve to their index in `columns` only
    # when the agent named the exact header text for that role.
    (
        debit_idx,
        credit_idx,
        balance_idx,
        combined_idx,
    ) = _amount_columns(
        columns,
        pdf_debit_column=pdf_debit_column,
        pdf_credit_column=pdf_credit_column,
        pdf_debit_credit_combined_column=pdf_debit_credit_combined_column,
        pdf_balance_column=pdf_balance_column,
    )
    balance_check_skipped: Optional[str] = None
    overall_pass = False
    cumulative_check: Dict[str, Any] = {
        "passed": False,
        "rows_checked": 0,
        "parsing_errors": [],
        "mismatches": [],
        "first_mismatch_row": None,
        "max_abs_error": 0.0,
    }
    final_check: Dict[str, Any] = {
        "passed": False,
        "diff": None,
        "final_from_opening": None,
        "last_cumulative": None,
    }
    debit_total = credit_total = net_change = final_from_opening = last_cumulative = None

    # Amount columns: either the separate form (debit + credit both resolved)
    # or the combined form (a single Debit/Credit column). A missing amount
    # form or missing balance role SKIPS the arithmetic check with a clear
    # message (the agent named no such column) - never fuzzy-guessed.
    amount_ok = (debit_idx is not None and credit_idx is not None) or combined_idx is not None

    if not rows:
        balance_check_skipped = "no transaction rows extracted."
        issues.append(
            "No transaction rows extracted. Check band_top (too low clips "
            "rows, too high includes headers), header_top, and date_pattern."
        )
        suggestions.append(
            "Start by identifying the first data row's top coordinate and "
            "set band_top to just below the header line."
        )
    elif not amount_ok:
        balance_check_skipped = (
            "could not resolve the amount columns: provide pdf_debit_column + "
            "pdf_credit_column (separate form) or "
            "pdf_debit_credit_combined_column (combined form) as exact names "
            "present in columns_pdf."
        )
        issues.append(
            f"Balance check skipped: {balance_check_skipped} "
            f"Found columns: {columns}"
        )
        suggestions.append(
            "Name the amount column(s) exactly as they appear in the header "
            "when calling assess_structure."
        )
    elif balance_idx is None:
        balance_check_skipped = (
            "no Cumulative Balance column resolved: provide pdf_balance_column "
            "as the exact name of the running Balance/Cumulative column."
        )
        issues.append(f"Balance check skipped: {balance_check_skipped}")
        suggestions.append(
            "Name the running-balance column exactly as it appears in the "
            "header (e.g. 'Balance', 'Cumulative', 'Closing Balance') to "
            "enable the arithmetic check."
        )
    else:
        # Totals for the final check (net change is signed per convention).
        debits = 0.0
        credits = 0.0
        for row in rows:
            if combined_idx is not None:
                # Combined Debit/Credit column: the sign is already in the
                # cell (negative = debit, positive = credit).
                amount = parse_amount(row.get(columns[combined_idx]))
                if amount is None:
                    continue
                if amount < 0:
                    debits += -amount
                else:
                    credits += amount
            else:
                debit = parse_amount(row.get(columns[debit_idx]))
                credit = parse_amount(row.get(columns[credit_idx]))
                if debit is not None:
                    debits += debit
                if credit is not None:
                    credits += credit
        debit_total = round(debits, 2)
        credit_total = round(credits, 2)
        if reconciliation_type == "vendor":
            net_change = round(debits - credits, 2)
        else:
            net_change = round(credits - debits, 2)

        cumulative_check = _run_cumulative_check(
            rows, debit_idx, credit_idx, balance_idx, columns,
            opening_balance, reconciliation_type, combined_idx,
        )
        parsed_cumulative = cumulative_check["cumulative_values"]
        if parsed_cumulative:
            last_cumulative = parsed_cumulative[-1]

        # Auto-verify the opening balance against the first cumulative row.
        if (
            opening_balance is not None
            and cumulative_check["rows_checked"] > 0
            and not cumulative_check["mismatches"]
        ):
            first_row = rows[0]
            signed = _signed_amount(
                first_row, debit_idx, credit_idx, columns, reconciliation_type, combined_idx
            )
            first_cum = parse_amount(first_row.get(columns[balance_idx]))
            if signed is not None and first_cum is not None:
                expected = opening_balance + signed
                if abs(expected - first_cum) > BALANCE_TOLERANCE:
                    issues.append(
                        f"Opening balance {opening_balance} does not reconcile "
                        f"with the first row: expected {round(expected, 2)} after "
                        f"the first transaction but the statement's first "
                        f"Cumulative Balance is {first_cum}. The opening balance "
                        f"may have been misread from the statement header."
                    )
                    suggestions.append(
                        "Re-read the Opening Balance from the statement header "
                        "(it may be labelled 'Opening Balance', 'B/F', 'Balance "
                        "Brought Forward', etc.) and pass it again."
                    )

        final_check = _run_final_check(
            opening_balance, net_change, last_cumulative
        )
        final_from_opening = final_check.get("final_from_opening")

        # Opening-balance verification when the sweep could not run rows.
        if (
            opening_balance is not None
            and cumulative_check["rows_checked"] == 0
        ):
            balance_check_skipped = (
                "cumulative column present but no rows could be parsed for "
                "the running-balance sweep."
            )

        saghir_passed = cumulative_check["passed"] and final_check["passed"]
        overall_pass = saghir_passed

        if saghir_passed:
            issues.append(
                "Arithmetic balance check PASSED: every row's running balance "
                "matches the Cumulative Balance column and opening + net "
                "change equals the final balance."
            )
        else:
            issues.append(
                "Arithmetic balance check FAILED: the extracted rows are not "
                "self-consistent with the statement's balances."
            )
            if cumulative_check["mismatches"]:
                fm = cumulative_check["mismatches"][0]
                issues.append(
                    f"First cumulative mismatch at row "
                    f"{fm['row_index']} (date '{fm['date']}'): running "
                    f"balance {fm['running_balance']} vs cumulative "
                    f"{fm['cumulative']} (diff {fm['diff']})."
                )
                suggestions.append(
                    "Inspect the row at that index: it may be a missed/mis-"
                    "sliced transaction, a column swap, or a footer/subtotal "
                    "line counted as a row."
                )
            if cumulative_check["parsing_errors"]:
                issues.append(
                    f"{len(cumulative_check['parsing_errors'])} row(s) had "
                    f"amount cells that could not be parsed as numbers "
                    f"(indexes {cumulative_check['parsing_errors'][:5]})."
                )
                suggestions.append(
                    "Check whether the Debit/Credit/Balance boundaries slice "
                    "the amount cells correctly (mis-sliced text does not "
                    "parse as a number)."
                )
            if not final_check["passed"]:
                issues.append(
                    f"Final balance check: opening + net change "
                    f"{final_from_opening} vs last cumulative "
                    f"{last_cumulative} (diff {final_check['diff']})."
                )
                suggestions.append(
                    "If the per-row sweep passed but the final check failed, "
                    "the opening balance is likely wrong or a closing/footer "
                    "balance row is being counted as a transaction."
                )

    # ---- Kabir (completeness check) - the new complementary test -----------
    kabir_check: Optional[Dict[str, Any]] = None
    if run_kabir:
        raw_rows, raw_date_counts, raw_per_page = extract_raw_rows_date_filtered(
            pdf_path
        )
        llm_per_page = [p["row_count"] for p in per_page]
        kabir_check = run_kabir_check(
            raw_rows=raw_rows,
            llm_rows=rows,
            raw_date_counts=raw_date_counts,
            raw_per_page=raw_per_page,
            llm_per_page=llm_per_page,
            date_column=columns[0] if columns else "",
            date_pattern=date_pattern,
        )

        # The adjudicate band fires the Assessor LLM unless Saghir already
        # failed (verdict is fail either way) or a deterministic tier decided.
        if (
            kabir_check["tier"] == "ADJUDICATE"
            and kabir_check["passed"] is None
            and overall_pass
            and use_assessor_llm
        ):
            packet = build_assessor_packet(
                assessment={
                    "cumulative_check": cumulative_check,
                    "final_check": final_check,
                    "column_mapping": column_mapping,
                },
                kabir=kabir_check,
                raw_rows=raw_rows,
                raw_date_counts=raw_date_counts,
                columns=columns,
                header_top=header_top,
                band_top=band_top,
                rows_dropped=rows_dropped,
                boundaries=boundaries,
                date_pattern=date_pattern,
                opening_balance=opening_balance,
                reconciliation_type=reconciliation_type,
            )
            try:
                adjudication = run_assessor_agent(packet)
            except Exception as e:
                # Fail-safe: an adjudicator that cannot run must not produce a
                # silent PASS.
                adjudication = {
                    "passed": False,
                    "summary": f"Adjudicator LLM failed to run: {e}",
                }
            kabir_check["passed"] = adjudication["passed"]
            kabir_check["tier"] = "ADJUDICATE"
            kabir_check["summary"] = adjudication["summary"]
        elif (
            kabir_check["tier"] == "ADJUDICATE"
            and kabir_check["passed"] is None
        ):
            kabir_check["passed"] = True
            kabir_check["tier"] = "INCONCLUSIVE"
            kabir_check["summary"] = (
                "Adjudicate band reached but the Assessor LLM was skipped "
                "(Saghir already failed, or LLM adjudication disabled) - "
                "treating Kabir as inconclusive, deferring to Saghir."
            )

        if kabir_check["passed"] is False:
            overall_pass = False
            issues.append(f"Kabir completeness check FAILED: {kabir_check['summary']}")
            suggestions.append(
                "Re-check band_top/header_top on ALL pages (especially "
                "continuation pages), and verify the date column slice: the "
                "raw extractor found dated rows the LLM structure never "
                "covered."
            )
        elif kabir_check["passed"] is True:
            issues.append(f"Kabir completeness check passed: {kabir_check['summary']}")
        else:
            issues.append(f"Kabir check inconclusive: {kabir_check['summary']}")

    # ---- Yabluwa al Ihsan (closing-balance anchor) --------------------------
    # The final gate. STRICT SHORT-CIRCUIT: Ihsan runs ONLY when Saghir AND
    # Kabir both passed (overall_pass is still true here). It reads the
    # statement's printed CLOSING BALANCE from the tail pages via a nested
    # agent, then compares opening + net_change against it. This is the only
    # check that defeats the self-consistent-subset trap: a dropped final-day
    # group (row 40 of 40 lost while row 39 still carries a balance) fails
    # here even though Saghir + Kabir both pass. An INCONCLUSIVE read (closing
    # balance not found anywhere) defers to the two deterministic checks.
    ihsan_check: Optional[Dict[str, Any]] = None
    if use_ihsan and overall_pass and net_change is not None:
        ihsan_check = {
            "ran": True,
            "found": None,
            "page": None,
            "closing_balance": None,
            "label": None,
            "passed": None,
            "diff": None,
            "final_from_opening": None,
            "summary": "",
        }
        try:
            read_result = run_ihsan_agent(pdf_path)
        except Exception as e:
            # Fail-safe: an Ihsan reader that cannot run must not produce a
            # silent PASS - treat as inconclusive (defer to Saghir + Kabir).
            read_result = {
                "found": False,
                "page": None,
                "closing_balance": None,
                "label": None,
                "passed": None,
                "summary": f"Ihsan reader failed to run: {e}",
            }
        ihsan_check.update(
            {
                "found": read_result.get("found"),
                "page": read_result.get("page"),
                "closing_balance": read_result.get("closing_balance"),
                "label": read_result.get("label"),
                "summary": read_result.get("summary", ""),
            }
        )
        closing_value = None
        if read_result.get("found") and read_result.get("closing_balance"):
            closing_value = parse_amount(read_result["closing_balance"])
        if closing_value is None:
            # No usable closing balance - inconclusive, defer.
            ihsan_check["passed"] = None
            if read_result.get("found"):
                ihsan_check["summary"] = (
                    f"Ihsan read '{read_result.get('closing_balance')}' on "
                    f"page {read_result.get('page')} but it could not be "
                    f"parsed as an amount - inconclusive, deferring to "
                    f"Saghir + Kabir."
                )
            issues.append(f"Ihsan check inconclusive: {ihsan_check['summary']}")
        else:
            check = run_ihsan_check(
                opening_balance=opening_balance,
                net_change=net_change,
                closing_balance=closing_value,
            )
            ihsan_check["passed"] = check["passed"]
            ihsan_check["diff"] = check["diff"]
            ihsan_check["final_from_opening"] = check["final_from_opening"]
            ihsan_check["closing_balance"] = closing_value
            if check["passed"]:
                issues.append(
                    f"Ihsan closing-balance check PASSED: opening + net change "
                    f"{check['final_from_opening']} equals the printed closing "
                    f"balance {closing_value} (diff {check['diff']})."
                )
            else:
                overall_pass = False
                issues.append(
                    f"Ihsan closing-balance check FAILED: opening + net change "
                    f"{check['final_from_opening']} does not match the printed "
                    f"closing balance {closing_value} (diff {check['diff']})."
                    + (
                        f" Ihsan read it on page {read_result.get('page')}"
                        + (f" (label: {read_result.get('label')})" if read_result.get("label") else "")
                        if read_result.get("page") is not None
                        else ""
                    )
                )
                suggestions.append(
                    "Either rows are still being missed at the END of the "
                    "statement (check band_top on the last pages), or the "
                    "closing balance was misread - verify the figure Ihsan "
                    "returned against the statement."
                )
    elif use_ihsan and overall_pass and net_change is None:
        ihsan_check = {
            "ran": False,
            "found": None,
            "page": None,
            "closing_balance": None,
            "label": None,
            "passed": None,
            "diff": None,
            "final_from_opening": None,
            "summary": (
                "Ihsan skipped: net change is unavailable (no Debit/Credit "
                "columns parsed) - cannot compute opening + net change."
            ),
        }
        issues.append(f"Ihsan check skipped: {ihsan_check['summary']}")
    elif use_ihsan:
        ihsan_check = {
            "ran": False,
            "found": None,
            "page": None,
            "closing_balance": None,
            "label": None,
            "passed": None,
            "diff": None,
            "final_from_opening": None,
            "summary": (
                "Ihsan skipped: Saghir and/or Kabir already failed - "
                "short-circuit (strict gating)."
            ),
        }
    elif not use_ihsan:
        ihsan_check = {
            "ran": False,
            "found": None,
            "page": None,
            "closing_balance": None,
            "label": None,
            "passed": None,
            "diff": None,
            "final_from_opening": None,
            "summary": "Ihsan disabled (use_ihsan=False).",
        }

    # ---- Issues & suggestions (structural, kept from the old assessor) -----
    if rows:
        # Column fill: a column that is largely empty is a boundary problem.
        for cs in col_stats:
            if cs["fill_rate"] < 0.5:
                issues.append(
                    f"Column '{cs['name']}' is mostly empty "
                    f"({cs['filled']}/{cs['total']} filled). The boundary "
                    f"between '{cs['name']}' and its neighbors likely cuts "
                    f"through the data."
                )
                suggestions.append(
                    f"Inspect the column boundary around column "
                    f"'{cs['name']}': shift it to the widest empty gap so "
                    f"data words do not straddle it."
                )

        # First column should be the date marker and should be fully filled.
        first = col_stats[0]
        if first["fill_rate"] < 1.0:
            issues.append(
                f"Date column '{first['name']}' is not fully filled "
                f"({first['filled']}/{first['total']}). Some transaction "
                f"rows are missing a date - the band_top or header_top may "
                f"be clipping rows, or the date pattern is wrong."
            )
            suggestions.append(
                "Lower band_top slightly to include the earliest data rows, "
                "or double-check the date_pattern against the actual dates."
            )
    else:
        issues.append(
            "No transaction rows extracted. Check band_top (too low clips "
            "rows, too high includes headers), header_top, and date_pattern."
        )
        suggestions.append(
            "Start by identifying the first data row's top coordinate and "
            "set band_top to just below the header line."
        )

    if date_matching_count > len(rows):
        issues.append(
            f"{date_matching_count} in-band lines match the date pattern but "
            f"only {len(rows)} rows were extracted - some rows are likely "
            f"being dropped by the header_top filter or lost to the "
            f"per-page dedup."
        )

    # ---- Score --------------------------------------------------------------
    # Reward quality: perfect date column fill + no empty cells across the
    # other columns. Start at 100 and penalize; the arithmetic verdict caps
    # the score (a FAILING balance check can never score 100).
    score = 100.0
    if not rows:
        score = 0.0
    else:
        # Date column must be 100% filled for the structure to be trustworthy.
        score -= (1.0 - col_stats[0]["fill_rate"]) * 50.0
        # Penalize empty cells in the remaining columns.
        other_empty = sum(cs["empty"] for cs in col_stats[1:])
        other_total = sum(cs["total"] for cs in col_stats[1:])
        if other_total:
            score -= (other_empty / other_total) * 50.0
        score = max(0.0, min(100.0, score))
        if not overall_pass and balance_check_skipped is None:
            score *= 0.5  # arithmetic failure halves the score

    return {
        "total_rows": len(rows),
        "page_count": page_count,
        "per_page": per_page,
        "columns": col_stats,
        "date_matching_count": date_matching_count,
        "score": round(score, 2),
        "opening_balance": opening_balance,
        "reconciliation_type": reconciliation_type,
        "debit_total": debit_total,
        "credit_total": credit_total,
        "net_change": net_change,
        "final_from_opening": final_from_opening,
        "last_cumulative": last_cumulative,
        "cumulative_check": cumulative_check,
        "final_check": final_check,
        "kabir_check": kabir_check,
        "ihsan_check": ihsan_check,
        "overall_pass": overall_pass,
        "balance_check_skipped": balance_check_skipped,
        "parsing_errors": cumulative_check.get("parsing_errors", []),
        "issues": issues,
        "suggestions": suggestions,
        "extracted_rows": rows,
        "column_mapping": column_mapping,
        "name_based": name_based,
    }


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _extract_rows_per_page(
    pdf_path: str | Path,
    columns: List[str],
    header_top: Optional[float | List[Optional[float]]] = None,
    boundaries: Optional[List[float]] = None,
    band_top: Optional[float | List[Optional[float]]] = None,
    date_pattern: str = DEFAULT_DATE_PATTERN,
    name_based: bool = True,
) -> List[int]:
    """Return the number of extracted rows per page (same extraction logic).

    Mirrors `extract_pdf_words` exactly, including the row marker: when
    `name_based` is True the marker is the slice mapped to the first column
    name (via the header line); when False it is `cells[0]`. This keeps the
    per-page breakdown consistent with the total row count.
    """
    compiled = re.compile(date_pattern)
    counts: List[int] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            page_header_top = _page_header_top(header_top, band_top, page_index)
            page_band_top = _per_page(band_top, page_index)

            slice_map = (
                _header_slice_mapping(page, page_header_top, boundaries or [], columns)
                if name_based
                else {}
            )

            words = page.extract_words()
            lines: dict[float, list[dict]] = {}
            for w in words:
                top = round(w["top"], 1)
                in_band = page_band_top is None or top >= page_band_top
                below_header = page_header_top is None or top >= page_header_top + 4.0
                if in_band and below_header:
                    lines.setdefault(top, []).append(w)

            page_count_rows = 0
            seen_tops: set[float] = set()
            for top in sorted(lines):
                if top in seen_tops:
                    continue
                seen_tops.add(top)
                cells = _slice_words_to_columns(lines[top], boundaries or [])
                if not cells:
                    continue
                if name_based:
                    marker_idx = slice_map.get(columns[0], 0)
                    marker_idx = marker_idx if marker_idx is not None else 0
                    marker = cells[marker_idx] if marker_idx < len(cells) else ""
                else:
                    marker = cells[0]
                if marker and re.match(compiled, marker.strip()):
                    page_count_rows += 1
            counts.append(page_count_rows)

    return counts


def main() -> None:
    """Demo: assess the default MCB structure against the sample statement.

    `header_top` / `band_top` accept either a single scalar (structure
    identical on all pages) or a per-page list [page1, page2] when page 1
    differs from the canonical continuation pages.
    """
    pdf_path = _resolve_path("assets_dev/Customer Ledger 2017-2023.pdf")
    assessment = assess_pdf_structure(
        pdf_path=pdf_path,
        columns=["Date", "Document No", "Details", "Debit", "Credit", "Cumulative"],
        header_top=[60.6, 35.9],
        boundaries=[60.45, 151.6, 563.4, 676.5, 741.6],
        band_top=[80.5, 35.9],
        rows_dropped=5,
        date_pattern=r"^\d{2}/\d{2}/\d{2}$",
        reconciliation_type="vendor",
        opening_balance=24016.0,
    )
    print(_pretty(assessment))
    print()
    # print("RAW DICT:")
    # import json
    # print(json.dumps(assessment, indent=2, default=str))


if __name__ == "__main__":
    main()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
