# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
LLM Run Check (Jaaiza e Natija e AI)
====================================

Standalone check tool for AI/LLM extraction results - NO LLM, NO API key
required. You supply the exact structure parameters the AI would detect
(the same ones test.py / test_results.py use) and this script runs the
SAME deterministic extraction logic as the production AI pipeline
(backend/src/services/ai_pdf_processor.py + ai_excel_processor.py):

    1. PDF   -> extracts transaction rows from ALL pages, then prints every
                column's values one by one.
    2. Excel -> reads the sheet via pandas and prints every column's values
                one by one.
    3. Excel debit + credit columns are combined into ONE list, with
                debits POSITIVE (+) and credits NEGATIVE (-).

Output is numbered and sectioned so LLM results can be eyeballed easily.
The same data is also returned as a plain dict for further checking.

Dependencies: pdfplumber + pandas (already used by the backend).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pdfplumber

# Default MCB statement layout (same as test_results.py).
DEFAULT_COLUMN_BOUNDARIES = [45.0, 89.0, 195.0, 246.0, 298.0, 348.0, 440.0, 500.0, 570.0]
DEFAULT_BAND_TOP = 170.0

DATE_PATTERN = r"^\d{2}-[A-Z]{3}-\d{2}$"

WIDTH = 76

# Repo root = parent of the tests/ folder. Relative file paths like
# "assets_dev/..." are resolved against this so the script works no matter
# which working directory it is run from.
REPO_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(path: str | Path) -> Path:
    """Resolve a relative path against the repo root."""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def _per_page(value: Any, page_index: int) -> Any:
    """Pick the value for a given page from a per-page list (or a scalar).

    Accepts either a single value (applied to every page) or a list where
    each entry is the value for that page index (None entries disable the
    filter for that page). Pages beyond the list reuse the last entry.
    """
    if isinstance(value, (list, tuple)):
        if page_index < len(value):
            return value[page_index]
        return value[-1] if value else None
    return value


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
def extract_pdf(
    pdf_path: str | Path,
    columns: List[str],
    header_top: Optional[float] = None,
    rows_dropped: int = 0,
    boundaries: Optional[List[float]] = None,
    band_top: Optional[float] = None,
    date_pattern: str = DATE_PATTERN,
) -> Tuple[List[Dict[str, Any]], int]:
    """Extract transaction rows from ALL pages of a PDF.

    Exactly mirrors the production extractor
    (backend/src/services/ai_pdf_processor.py -> extract_pdf): words are
    grouped into visual lines and sliced at the given column boundaries;
    only lines whose first column matches `date_pattern` count as rows.
    Deduplication is PER-PAGE (as in production) so transaction rows on
    continuation pages are never dropped.

    Args:
        pdf_path: Path to the .pdf bank statement.
        columns: Column names, in left-to-right visual order. The first
            column is used as the transaction-row marker (must match
            date_pattern).
        header_top: Top coordinate(s) of the header line; rows at/below
            header_top + small tolerance are treated as data. A scalar
            applies to every page; a list applies per page (None disables
            the filter for that page).
        rows_dropped: Number of visual lines above the header to skip
            (kept for signature parity with production).
        boundaries: Physical x-coordinates of the column edges.
        band_top: Upper vertical boundary(ies) of the transaction band,
            scalar or per-page list (None disables for that page).
        date_pattern: Regex the first column must match to count as a row.

    Returns:
        (rows, page_count) where rows is a list of {column: value} dicts.
    """
    compiled = re.compile(date_pattern)
    rows: List[Dict[str, str]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        for page_index, page in enumerate(pdf.pages):
            words = page.extract_words()

            # Per-page layout filters: the header/band positions can differ
            # between page 1 (account header block) and continuation pages
            # (which start straight at the data band).
            page_header_top = _per_page(header_top, page_index)
            page_band_top = _per_page(band_top, page_index)

            # Table lines (extract_table rows) with the SAME structural
            # filters applied: only rows whose top is at/below band_top and
            # at/below header_top + tolerance are kept, per page.
            page_tables = page.find_tables()
            table_lines: List[List[Any]] = []
            for t in page_tables:
                for row in t.rows:
                    row_top = row.bbox[1]
                    in_band = page_band_top is None or row_top >= page_band_top
                    below_header = page_header_top is None or row_top >= page_header_top + 4.0
                    if in_band and below_header:
                        table_lines.append([cell.text for cell in row.cells])

            # Group words into visual lines by their top coordinate.
            lines: dict[float, list[dict]] = {}
            for w in words:
                top = round(w["top"], 1)
                in_band = page_band_top is None or top >= page_band_top
                below_header = page_header_top is None or top >= page_header_top + 4.0
                if in_band and below_header:
                    lines.setdefault(top, []).append(w)

            # Print the structural filter results for this page, clearly
            # distinguishable, before the word rows are printed.
            _print_title(f"PAGE {page_index + 1} OF {page_count}")
            print(f"  band_top   : {page_band_top}")
            print(f"  header_top : {page_header_top}")
            print(f"  LINES (extract_table) : {len(table_lines)}")
            print(f"  WORDS (visual lines)  : {len(lines)}")
            print("-" * WIDTH)

            # Dedup is PER-PAGE: the same top coordinate can legitimately
            # hold a transaction row on page 2 even though a row occupied it
            # on page 1 (both pages share the same layout).
            seen_tops: set[float] = set()
            for top in sorted(lines):
                if top in seen_tops:
                    continue
                seen_tops.add(top)
                cells = _slice_words_to_columns(lines[top], boundaries or [])
                # Keep only transaction rows: first column is a statement date.
                if cells and re.match(compiled, cells[0].strip()):
                    row: Dict[str, str] = {}
                    for i, name in enumerate(columns):
                        row[name] = cells[i] if i < len(cells) else ""
                    rows.append(row)

    return rows, page_count


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _clean_value(value: Any) -> str:
    """Convert a cell value into a readable string (NaN -> '(empty)')."""
    if value is None:
        return "(empty)"
    try:
        if pd.isna(value):
            return "(empty)"
    except (TypeError, ValueError):
        pass
    s = str(value).strip()
    return s if s else "(empty)"


def _to_float(value: Any) -> Optional[float]:
    """Parse an amount into a float, stripping currency symbols/commas."""
    try:
        if pd.isna(value):
            return None
        cleaned = (
            str(value)
            .replace(",", "")
            .replace("$", "")
            .replace("PKR", "")
            .replace("Rs.", "")
            .strip()
        )
        if not cleaned:
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_combined_debit_credit(
    df: pd.DataFrame,
    amount_column: str,
) -> List[Dict[str, Any]]:
    """Combine the Excel amount column into one signed list.

    Sign convention requested by the user:
        debits  -> POSITIVE (+)
        credits -> NEGATIVE (-)

    The amount column carries the file's own sign (positive = debit,
    negative = credit), so values are kept as-is and labelled by sign.
    """
    combined: List[Dict[str, Any]] = []

    if amount_column not in df.columns:
        return combined

    for v in df[amount_column].tolist():
        amount = _to_float(v)
        if amount is not None:
            combined.append(
                {
                    "amount": amount,
                    "side": "Debit" if amount > 0 else "Credit",
                }
            )

    return combined


# -------------------- Pretty printing --------------------


def _print_rule(char: str = "=", width: int = WIDTH) -> None:
    print(char * width)


def _print_title(title: str) -> None:
    _print_rule()
    print(title.center(WIDTH))
    _print_rule()


def _print_column(name: str, values: list) -> None:
    count = len(values)
    label = "value" if count == 1 else "values"
    print(f"\n  COLUMN: {name}   ({count} {label})")
    print("-" * WIDTH)
    for i, v in enumerate(values, start=1):
        print(f"   [{i:>3}]  {v}")


def _print_combined(combined: list) -> None:
    count = len(combined)
    label = "value" if count == 1 else "values"
    print(f"\n  COMBINED DEBIT/CREDIT (Excel)   ({count} {label})")
    print("  debits = POSITIVE (+)  |  credits = NEGATIVE (-)")
    print("-" * WIDTH)
    for i, entry in enumerate(combined, start=1):
        print(f"   [{i:>3}]  {entry['amount']:>+,.2f}   ({entry['side']})")


# -------------------- Main entry point --------------------


def run_llm_check(
    pdf_path: Optional[str | Path] = None,
    pdf_columns: Optional[List[str]] = None,
    header_top: Optional[float | List[Optional[float]]] = None,
    rows_dropped: int = 0,
    boundaries: Optional[List[float]] = None,
    band_top: Optional[float | List[Optional[float]]] = None,
    date_pattern: str = DATE_PATTERN,
    excel_path: Optional[str | Path] = None,
    sheet_name: str = "Sheet1",
    excel_columns: Optional[List[str]] = None,
    excel_amount_column: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the LLM-result check with the given PDF/Excel structure parameters.

    All arguments are optional; sections are skipped when the matching file
    path is not provided. `excel_columns` (list of strings) is the canonical
    4-column layout: [date, details, debit/credit amount, total].

    `header_top` / `band_top` accept either a single value (applied to every
    page) or a list with one entry per page (None disables the filter for
    that page), for statements whose layout differs between page 1 and the
    continuation pages.

    Returns:
        A plain dict:
            {
              "pdf":   {"file", "pages", "row_count", "rows"} | {"error"},
              "excel": {"file", "sheet", "columns", "combined_debit_credit"} | {"error"},
            }
    """
    _print_title("LLM RESULT CHECK  |  PDF + EXCEL EXTRACTION (column-wise)")

    result: Dict[str, Any] = {"pdf": None, "excel": None}

    # ---------------- PDF section ----------------
    if pdf_path:
        pdf_file = _resolve_path(pdf_path)
        if not pdf_columns:
            print("\n  [!] pdf_columns not provided - skipping PDF extraction.")
        else:
            try:
                rows, page_count = extract_pdf(
                    pdf_path=pdf_file,
                    columns=pdf_columns,
                    header_top=header_top,
                    rows_dropped=rows_dropped,
                    boundaries=boundaries,
                    band_top=band_top,
                    date_pattern=date_pattern,
                )
                print(f"\n  PDF  : {pdf_file.name}  ({page_count} page(s))")
                print(f"  Rows : {len(rows)} transaction row(s) extracted from ALL pages")
                for col in pdf_columns:
                    _print_column(col, [r.get(col, "") for r in rows])
                result["pdf"] = {
                    "file": str(pdf_file),
                    "pages": page_count,
                    "row_count": len(rows),
                    "rows": rows,
                }
            except Exception as e:
                print(f"\n  [!] PDF extraction failed: {e}")
                result["pdf"] = {"file": str(pdf_file), "error": str(e)}
    else:
        print("\n  (no pdf_path given - PDF section skipped)")

    # ---------------- Excel section ----------------
    if excel_path:
        excel_file = _resolve_path(excel_path)
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            show = excel_columns if excel_columns else df.columns.tolist()

            print(f"\n  EXCEL: {excel_file.name}  (sheet: {sheet_name})")
            print(f"  Columns: {len(show)}  {show}")
            column_values: Dict[str, List[str]] = {}
            for col in show:
                if col not in df.columns:
                    print(f"\n  COLUMN: {col}   (NOT FOUND in sheet)")
                    column_values[col] = []
                    continue
                values = [_clean_value(v) for v in df[col].tolist()]
                column_values[col] = values
                _print_column(col, values)

            # Combined debit/credit list: amount column is index 2 of the
            # canonical 4-column layout [date, details, amount, total],
            # overridable via excel_amount_column.
            amount_column = excel_amount_column or (
                show[2] if len(show) >= 3 else None
            )
            if amount_column:
                combined = build_combined_debit_credit(df, amount_column)
                if combined:
                    _print_combined(combined)
                else:
                    print(f"\n  (no numeric values found in amount column '{amount_column}')")
            else:
                print("\n  (no amount column given - combined section skipped)")

            result["excel"] = {
                "file": str(excel_file),
                "sheet": sheet_name,
                "columns": column_values,
                "combined_debit_credit": combined if amount_column else [],
            }
        except Exception as e:
            print(f"\n  [!] Excel extraction failed: {e}")
            result["excel"] = {"file": str(excel_file), "error": str(e)}
    else:
        print("\n  (no excel_path given - Excel section skipped)")

    # ---------------- Summary ----------------
    _print_rule()
    print("  SUMMARY".center(WIDTH))
    _print_rule()
    if result.get("pdf"):
        if "rows" in result["pdf"]:
            print(f"   PDF   : {result['pdf']['row_count']} rows across {result['pdf']['pages']} page(s)")
        else:
            print(f"   PDF   : FAILED - {result['pdf'].get('error')}")
    else:
        print("   PDF   : skipped")
    if result.get("excel"):
        if "columns" in result["excel"]:
            print(
                f"   EXCEL : {len(result['excel']['columns'])} column(s) shown, "
                f"{len(result['excel'].get('combined_debit_credit', []))} combined debit/credit value(s)"
            )
        else:
            print(f"   EXCEL : FAILED - {result['excel'].get('error')}")
    else:
        print("   EXCEL : skipped")
    _print_rule()

    return result


def main() -> None:
    """Demo run against the sample files in assets_dev (repo root)."""
    run_llm_check(
        pdf_path="assets_dev/getjobid4981240-july.pdf",
        pdf_columns=[
            "Tran. Date", "Debit", "Credit"
        ],
        header_top=167.7,
        boundaries=DEFAULT_COLUMN_BOUNDARIES,
        band_top=181.3,
        rows_dropped=22,
        date_pattern=r"^\d{2}-[A-Z]{3}-\d{2}$",
        excel_path="assets_dev/Recon-July-2026.xlsx",
        sheet_name="Sheet1",
        excel_columns=[
            "Posting Date"
        ],
        excel_amount_column="Cumulative Balance (LC)",
    )


if __name__ == "__main__":
    main()

# ============================================================================
# OLD CONFIGURATION - Soneri Bank (PKMB_STMT_ENT_BOOK_2.pdf) - kept for reference
# ============================================================================
# pdf_path      : assets_dev/PKMB_STMT_ENT_BOOK_2.pdf
# pdf_columns   : ["Booking Date", "Value Date", "Reference", "Description",
#                  "Cheque.no", "Debit", "Credit", "Closing Bal-"]
# header_top    : [343.4, None]      # per page: page 1 header, page 2 none
# band_top      : [401.5, 103.9]     # per page
# rows_dropped  : 11
# date_pattern  : ^\d{2} [A-Z]{3} \d{4}$
# boundaries    : [116.85, 204.65, 268.05, 325.65, 375.9, 439.35, 497.85]
# excel_path    : assets_dev/Soneri Bank Data July-26.xlsx
# excel_columns : ["Posting Date", "Details", "Cumulative Balance (LC)",
#                  "Debit (LC)", "Credit (LC)"]
# excel_amount  : "Cumulative Balance (LC)"
# ============================================================================

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
