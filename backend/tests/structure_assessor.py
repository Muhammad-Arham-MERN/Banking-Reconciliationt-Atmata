# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Structure Assessor (Jaaiza e Bunyad)

Deterministic, zero-LLM scoring tool that tells an AI agent how well its
proposed PDF structure parameters would perform in the production extractor.

It runs the EXACT same extraction logic as the production pipeline
(backend/src/services/ai_pdf_processor.py -> extract_pdf, mirrored here by
extract_pdf_words) using the agent's proposed structure, then returns
diagnostics the agent can act on:

    - total rows extracted (its proposed structure)
    - per-page row counts and in-band/date-line counts
    - per-column fill rates (catches bad boundaries slicing cells away)
    - a 0-100 score rewarding QUALITY, not just row count

The purpose is to catch LLM hallucination in structure detection: if the
agent emits band_top/header_top/boundaries that are slightly off, the row
count and fill rates drop, and the agent sees exactly why before committing
to a final [output] block.

Dependencies: pdfplumber (already used by the backend).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

# Default MCB statement layout (same as test_results.py / LLM_run_check.py).
DEFAULT_COLUMN_BOUNDARIES = [45.0, 89.0, 195.0, 246.0, 298.0, 348.0, 440.0, 500.0, 570.0]
DEFAULT_BAND_TOP = 170.0
DEFAULT_DATE_PATTERN = r"^\d{2}-[A-Z]{3}-\d{2}$"

# Repo root = parent of the tests/ folder. Relative file paths like
# "assets_dev/..." are resolved against this so the script works no matter
# which working directory it is run from.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def extract_raw_table_rows(
    pdf_path: str | Path,
    header_top: Optional[float | List[Optional[float]]] = None,
    rows_dropped: int = 0,
    band_top: Optional[float | List[Optional[float]]] = None,
) -> Tuple[List[List[Any]], int]:
    """Extract the RAW transaction rows from the PDF's actual table.

    This is the INDEPENDENT baseline. It uses only the page STRUCTURAL
    properties (band_top, header_top, rows_dropped - exactly the same as
    production) and pdfplumber's own table detection (`extract_table`), NOT
    the LLM's `columns` or `boundaries`. It is the "ground truth" row count
    the LLM structure is compared against.

    Rows are kept only when they lie at/below band_top and at/below
    header_top + tolerance (same vertical cuts the production word-extractor
    applies). `extract_table()` supplies the actual cell text.

    Returns:
        (rows, page_count) where rows is a list of raw cell-lists.
    """
    rows: List[List[Any]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        for page_index, page in enumerate(pdf.pages):
            page_header_top = _page_header_top(header_top, band_top, page_index)
            page_band_top = _per_page(band_top, page_index)

            for table in page.find_tables():
                # table.extract() gives text per cell; table.rows gives geometry.
                extracted = table.extract()
                for row_idx, geom_row in enumerate(table.rows):
                    if row_idx >= len(extracted):
                        break
                    row_top = geom_row.bbox[1]
                    in_band = page_band_top is None or row_top >= page_band_top
                    below_header = page_header_top is None or row_top >= page_header_top + 4.0
                    if in_band and below_header:
                        raw_cells = extracted[row_idx] or []
                        rows.append(["" if c is None else str(c) for c in raw_cells])
    return rows, page_count


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
) -> Dict[str, Any]:
    """Assess how well the proposed structure would extract transaction rows.

    Runs the production extraction logic with the given structure and returns
    a diagnostic dict the LLM agent can use to correct its own output.

    Args:
        pdf_path: Path to the .pdf bank statement.
        columns: Proposed column names (left-to-right visual order).
        header_top: Proposed header top (scalar or per-page list).
        rows_dropped: Proposed number of visual lines above the header.
        boundaries: Proposed physical x-coordinates of the column edges.
        band_top: Proposed upper vertical boundary of the transaction band.
        date_pattern: Proposed regex for the first-column transaction dates.

    Returns:
        A plain dict (JSON-serializable for LLM consumption):
            {
              "total_rows": int,
              "page_count": int,
              "per_page": [{page, band_top, header_top, in_band_lines,
                            date_matching_lines, row_count}],
              "columns": [{name, total, filled, fill_rate, empty}],
              "date_matching_count": int,
              "score": float (0-100),
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

    # Independent baseline: RAW table rows using only the page structural
    # properties (band_top / header_top / rows_dropped), NOT the LLM's
    # columns or boundaries. This is the "ground truth" row count.
    raw_rows, _raw_page_count = extract_raw_table_rows(
        pdf_path=pdf_path,
        header_top=header_top,
        rows_dropped=rows_dropped,
        band_top=band_top,
    )
    raw_row_count = len(raw_rows)
    llm_row_count = len(rows)

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

    # ---- RAW vs LLM row-count comparison (the core verdict) ----------------
    # The raw table rows (using band_top/header_top/rows_dropped) are the
    # ground truth. The LLM's structure-based rows should be close (2-3 is
    # normal, because raw table rows can include wrapped sub-lines). A large
    # gap (e.g. 32 vs 40) means the LLM's structure is wrong.
    delta = llm_row_count - raw_row_count
    if raw_row_count == 0:
        issues.append(
            "Raw table extraction found 0 rows - the band_top/header_top "
            "structural properties may be wrong (clipping the whole table)."
        )
        suggestions.append(
            "Re-check band_top and header_top against read_pdf_words; the "
            "table may start above band_top or below header_top."
        )
    else:
        if abs(delta) <= 3:
            verdict = "OK"
            severity = ""
        else:
            verdict = "MISMATCH"
            severity = " (large gap - LLM structure is likely wrong)"
        issues.append(
            f"RAW table rows: {raw_row_count} vs LLM structure rows: "
            f"{llm_row_count} (delta {delta:+d}) -> {verdict}{severity}"
        )
        if abs(delta) > 3:
            if delta < 0:
                suggestions.append(
                    "LLM structure extracts FEWER rows than the raw table. "
                    "Lower band_top (or raise header_top tolerance) to include "
                    "the missing early rows; also verify boundaries aren't "
                    "slicing rows away."
                )
            else:
                suggestions.append(
                    "LLM structure extracts MORE rows than the raw table. "
                    "Raise band_top (or tighten the date_pattern) to exclude "
                    "header/footer lines that are being counted as rows."
                )

    # ---- Issues & suggestions ---------------------------------------------
    if total_rows := len(rows):
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
    # other columns. Start at 100 and penalize.
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

    return {
        "total_rows": len(rows),
        "page_count": page_count,
        "per_page": per_page,
        "columns": col_stats,
        "date_matching_count": date_matching_count,
        "score": round(score, 2),
        "issues": issues,
        "suggestions": suggestions,
        "extracted_rows": rows,
        "column_mapping": column_mapping,
        "name_based": name_based,
        "raw_row_count": raw_row_count,
        "llm_row_count": llm_row_count,
        "row_delta": delta,
        "raw_rows": raw_rows,
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


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _pretty(assessment: Dict[str, Any]) -> str:
    """Render the assessment dict as a readable block for the agent/CLI."""
    lines_out = [
        "========================================",
        " PDF STRUCTURE ASSESSMENT",
        "========================================",
        f"  Rows extracted (LLM structure) : {assessment.get('llm_row_count', assessment.get('total_rows', 0))}",
        f"  Rows in raw table (ground truth): {assessment.get('raw_row_count', 'n/a')}",
        f"  Row delta                      : {assessment.get('row_delta', 'n/a'):+d}" if isinstance(assessment.get("row_delta"), int) else f"  Row delta                      : {assessment.get('row_delta', 'n/a')}",
        f"  Pages                          : {assessment['page_count']}",
        f"  Date lines                     : {assessment['date_matching_count']}",
        f"  Score                          : {assessment['score']}/100",
        "----------------------------------------",
    ]
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


def main() -> None:
    """Demo: assess the default MCB structure against the sample statement.

    `header_top` / `band_top` accept either a single scalar (structure
    identical on all pages) or a per-page list [page1, page2] when page 1
    differs from the canonical continuation pages.
    """
    pdf_path = _resolve_path("assets_dev/PKMB_STMT_ENT_BOOK_2.pdf")
    assessment = assess_pdf_structure(
        pdf_path=pdf_path,
        columns=[
    "Booking Date",
    "Value Date",
    "Reference",
    "Description",
    "Cheque.no",
    "Debit",
    "Credit",
    "Closing Balance"
  ],
        header_top=[
    343.4,
    103.9
  ],
        boundaries=[
    116.85,
    204.65,
    268.05,
    325.65,
    378.45,
    441.3,
    497.85
  ],
        band_top=[401.5,103.9],
        rows_dropped=11,
        date_pattern="^\\d{2} [A-Z]{3} \\d{4}$",
    )
    print(_pretty(assessment))
    import pandas as pd
    df = pd.DataFrame(assessment["extracted_rows"])
    print("Balance here")
    print(df["Closing Balance"][0])
    print(df["Closing Balance"][1])
    print(df["Closing Balance"][2])
    print(df["Closing Balance"][3])
    print(df["Closing Balance"][4])
    print(df["Closing Balance"][5])
    print("Credit here")
    print(df["Credit"][0])
    print(df["Credit"][1])
    print(df["Credit"][2])
    print(df["Credit"][3])
    print(df["Credit"][4])
    print(df["Credit"][5])
    # print("RAW DICT:")
    # import json
    # print(json.dumps(assessment, indent=2, default=str))


if __name__ == "__main__":
    main()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
