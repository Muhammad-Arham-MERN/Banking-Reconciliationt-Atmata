# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
AI PDF Processor (Istikhraj e Data Ma'a AI)

Extracts transaction rows from an uploaded PDF bank statement using the
AI-detected layout (columns, header top, rows dropped, column boundaries,
band top, date pattern). Same layout-slicing logic as the production
pdf_processor.py, but fully dynamic — every parameter comes from the AI
structure detector instead of module-level constants, so any bank statement
layout can be extracted without editing the module.

The transformation layer reuses the existing data transformers, so the
standardized output shape is identical to PDFProcessor.process_pdf and the
downstream reconciliation service consumes it unchanged (FR-007).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pdfplumber

from src.services.ai_structure_detector import AIDetectionError, FileStructureOutput
from src.utils.data_transformers import (
    clean_transaction_detail,
    normalize_pdf_date,
    standardize_transaction_data,
)

logger = logging.getLogger(__name__)


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
def _per_page(value, page_index: int):
    """Pick the value for a given page from a per-page list (or a scalar).

    Accepts either a single value (applied to every page) or a list where
    each entry is the value for that page index. Pages beyond the list reuse
    the last entry, so a 2-element list [page1, page2] makes page 2's value
    canonical for pages 3+.
    """
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return value[page_index] if page_index < len(value) else value[-1]
    return value


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _page_header_top(
    header_top: Optional[float | List[float]],
    band_top: Optional[float | List[float]],
    page_index: int,
) -> Optional[float]:
    """Resolve the effective header top for a page (same as the assessor).

    A page whose header line sits at or below its data band has no usable
    header (e.g. a continuation page that starts straight at the data band).
    Returning None there disables the NAME-BASED header mapping for that
    page, so column assignment falls back to index-based - exactly what the
    structure assessor (extract_pdf_words) does.
    """
    page_header_top = _per_page(header_top, page_index)
    if page_header_top is None:
        return None
    page_band_top = _per_page(band_top, page_index)
    if page_band_top is not None and page_header_top >= page_band_top:
        return None
    return page_header_top


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _normalize(text) -> str:
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

    Same name-based lookup the structure assessor uses: the physical header
    line at `page_header_top` is sliced with the same boundaries, and each
    column's normalized name is matched against each slice's normalized
    header text. This lets extraction pull the right physical column even
    when the LLM returns `columns` out of physical order. Columns that cannot
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
def extract_pdf(
    pdf_path: str | Path,
    columns: List[str],
    header_top: Optional[float | List[float]] = None,
    rows_dropped: int = 0,
    boundaries: Optional[List[float]] = None,
    band_top: Optional[float | List[float]] = None,
    date_pattern: str = r"^\d{2}-[A-Z]{3}-\d{2}$",
) -> pd.DataFrame:
    """Extract transaction rows from a PDF by slicing words at column boundaries.

    Mirrors pdf_processor._extract_rows_via_layout, but takes the layout
    parameters instead of reading module-level constants (port of the validated
    extract_pdf from test_results.py).

    Args:
        pdf_path: Path to the .pdf bank statement.
        columns: Column names, in left-to-right visual order. The first column
            is used as the transaction-row marker (must match date_pattern).
        header_top: top coordinate of the header line, as a scalar (applies to
            every page) or a per-page list [page1, page2] where page 2's value
            is canonical for pages 3+. Rows at/below header_top + small
            tolerance are treated as data.
        rows_dropped: Number of visual lines above the header line to skip.
        boundaries: Physical x-coordinates of the column edges. Words are
            assigned by their x-center relative to these.
        band_top: Upper vertical boundary (PDF points) of the transaction band,
            scalar or per-page list. Rows are only taken from lines at/below
            this.
        date_pattern: Regex the first column must match to count as a
            transaction row.

    Returns:
        DataFrame with one column per entry in `columns`.
    """
    compiled = re.compile(date_pattern)
    rows: List[Dict[str, str]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            words = page.extract_words()

            # Per-page layout filters: the header/band positions can differ
            # between page 1 (account header block) and continuation pages
            # (which start straight at the data band).
            page_band_top = _per_page(band_top, page_index)
            page_header_top = _page_header_top(header_top, band_top, page_index)

            # NAME-BASED column assignment (same as the structure assessor's
            # extract_pdf_words): each column NAME is mapped to its physical
            # slice index via the header line, and the row marker is the slice
            # mapped to the first column. A page with no usable header line
            # (header_top >= band_top) gets an empty map -> index-based fallback.
            slice_map = _header_slice_mapping(page, page_header_top, boundaries or [], columns)

            # Group words into visual lines by their top coordinate.
            lines: dict[float, list[dict]] = {}
            for w in words:
                # On the first page the data band starts after the header;
                # on continuation pages the header repeats, so skip lines that
                # lie within the header area too.
                top = round(w["top"], 1)
                in_band = page_band_top is None or top >= page_band_top
                below_header = page_header_top is None or top >= page_header_top + 4.0
                if in_band and below_header:
                    lines.setdefault(top, []).append(w)

            # Dedup is PER-PAGE: the same top coordinate can legitimately hold a
            # transaction row on page 2 even though a row occupied it on page 1
            # (both pages share the same layout). A global set would silently
            # drop page-2 transactions.
            seen_tops: set[float] = set()
            for top in sorted(lines):
                if top in seen_tops:
                    continue
                seen_tops.add(top)
                cells = _slice_words_to_columns(lines[top], boundaries or [])
                # Row marker: name-based uses the slice mapped to the first
                # column name; index-based uses cells[0] (fallback).
                marker_idx = slice_map.get(columns[0], 0)
                marker_idx = marker_idx if marker_idx is not None else 0
                marker = cells[marker_idx] if marker_idx < len(cells) else ""
                # Keep only transaction rows: first column is a statement date.
                if marker and re.match(compiled, marker.strip()):
                    row = {}
                    for i, name in enumerate(columns):
                        idx = slice_map.get(name, i)
                        idx = idx if idx is not None else i
                        row[name] = cells[idx] if idx < len(cells) else ""
                    rows.append(row)

    return pd.DataFrame(rows, columns=columns)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _extract_balance(df: pd.DataFrame, columns_or_structure) -> Dict[str, Any]:
    """Extract the last Balance-column value as bank_net_total (same semantics
    as the production processor; falls back to "missing"/"invalid" status).

    The Balance column is identified by the agent-provided
    pdf_balance_column when a FileStructureOutput is passed, else the last
    detected PDF column whose name suggests a balance/outstanding figure.
    """
    result = {"value": None, "status": "missing"}

    columns = getattr(columns_or_structure, "columns_pdf", columns_or_structure)
    balance_col = getattr(columns_or_structure, "pdf_balance_column", None)

    if balance_col is None:
        for name in reversed(columns):
            if any(k in str(name).lower() for k in ("balance", "outstanding", "closing")):
                balance_col = name
                break

    if balance_col is None or balance_col not in df.columns:
        logger.warning("Balance column not found in extracted PDF data")
        return result

    valid_balance = df[balance_col].dropna()
    if valid_balance.empty:
        result["status"] = "invalid"
        return result

    last_balance = valid_balance.iloc[-1]
    try:
        cleaned = str(last_balance).replace("$", "").replace(",", "").strip()
        if cleaned:
            result["value"] = float(cleaned)
            result["status"] = "found"
        else:
            result["status"] = "invalid"
    except (ValueError, TypeError):
        result["status"] = "invalid"
        logger.warning(f"Could not parse Balance value: {last_balance}")

    return result


class AIPDFProcessor:
    """AI-driven PDF bank statement processor.

    Extracts transactions using the AI-detected structure and transforms them
    to the standardized format consumed by ReconciliationService.
    """

    def __init__(self, request_id: str = "unknown"):
        self.request_id = request_id

    def extract_bank_statement(
        self,
        pdf_path: Path,
        structure: FileStructureOutput,
    ) -> pd.DataFrame:
        """Extract transaction rows using the AI-detected layout.

        Args:
            pdf_path: Path to the uploaded PDF.
            structure: Detected file structure (columns, boundaries, band...).

        Returns:
            DataFrame with the detected columns; empty if no rows matched.

        Raises:
            AIDetectionError: If the detected structure cannot be applied.
        """
        if not pdf_path.exists():
            raise AIDetectionError(f"PDF file not found: {pdf_path}")

        try:
            df = extract_pdf(
                pdf_path=pdf_path,
                columns=structure.columns_pdf,
                header_top=structure.header_top_pdf,
                rows_dropped=structure.rows_dropped_pdf,
                boundaries=structure.column_boundaries_pdf,
                band_top=structure.band_top_pdf,
                date_pattern=structure.date_pattern_pdf,
            )
            if df.empty:
                raise AIDetectionError("No valid transaction data found in PDF")
            return df
        except AIDetectionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting PDF: {e}")
            raise AIDetectionError(f"Unexpected error extracting PDF: {e}")

    def transform_to_standard_format(
        self,
        df: pd.DataFrame,
        columns: List[str],
        structure: Optional[FileStructureOutput] = None,
    ) -> List[Dict[str, Any]]:
        """Transform the extracted DataFrame to standardized transactions.

        The column ROLES come from the agent-provided structure (exact header
        names in columns_pdf): pdf_transaction_date_column, pdf_details_column,
        and the amount columns in exactly one form (pdf_debit_column +
        pdf_credit_column, or the rare combined pdf_debit_credit_combined_column).
        No name guessing - a role the agent did not name is left None and the
        row is skipped with a warning rather than mapped to the wrong column.

        When `structure` is omitted (legacy callers), falls back to the
        previous substring-based role detection so existing behavior is kept.
        """
        if df.empty:
            return []

        if structure is not None:
            date_col = structure.pdf_transaction_date_column or (columns[0] if columns else None)
            detail_col = structure.pdf_details_column
            debit_col = structure.pdf_debit_column
            credit_col = structure.pdf_credit_column
            combined_col = structure.pdf_debit_credit_combined_column
            # The amount columns must be exactly one form. If neither is
            # named, fall back to the old detection so legacy callers work.
            if debit_col is None and credit_col is None and combined_col is None:
                debit_col = next((c for c in columns if str(c).lower().strip() == "debit"), None)
                credit_col = next((c for c in columns if str(c).lower().strip() == "credit"), None)
        else:
            date_col = next((c for c in columns if "date" in str(c).lower()), columns[0] if columns else None)
            detail_col = next(
                (c for c in columns if any(k in str(c).lower() for k in ("narrative", "detail", "desc", "remark"))),
                None,
            )
            debit_col = next((c for c in columns if str(c).lower().strip() == "debit"), None)
            credit_col = next((c for c in columns if str(c).lower().strip() == "credit"), None)
            combined_col = None

        if detail_col is None:
            # Fallback: second column is the detail column (MCB layout).
            detail_col = columns[1] if len(columns) > 1 else None

        standardized: List[Dict[str, Any]] = []
        for idx, row in df.iterrows():
            try:
                date_value = row.get(date_col) if date_col else None
                detail_value = row.get(detail_col) if detail_col else None

                if combined_col is not None:
                    # Combined Debit/Credit column: the cell already carries
                    # its sign (negative = debit, positive = credit).
                    amount_value = row.get(combined_col)
                    debit_value = None
                    credit_value = None
                else:
                    amount_value = None
                    debit_value = row.get(debit_col) if debit_col else None
                    credit_value = row.get(credit_col) if credit_col else None

                cleaned_detail = clean_transaction_detail(str(detail_value)) if detail_value is not None else ""
                transaction = standardize_transaction_data(
                    date_value=date_value,
                    detail_value=cleaned_detail,
                    amount_value=amount_value,
                    debit_value=debit_value,
                    credit_value=credit_value,
                    source_type="pdf",
                )
                if transaction:
                    standardized.append(transaction)
            except Exception as row_error:
                logger.debug(f"Error processing row {idx}: {row_error}")
                continue

        return standardized

    def process_pdf(
        self,
        pdf_path: Path,
        structure: FileStructureOutput,
    ) -> Dict[str, Any]:
        """Complete AI PDF processing pipeline: extract + transform.

        Returns the same result shape as PDFProcessor.process_pdf:
        bank_statement, bank_net_total, processing_metadata.
        """
        import time
        start_time = time.time()

        df = self.extract_bank_statement(pdf_path, structure)
        bank_net_total = _extract_balance(df, structure)
        standardized = self.transform_to_standard_format(df, structure.columns_pdf, structure)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "bank_statement": standardized,
            "bank_net_total": bank_net_total,
            "processing_metadata": {
                "pdf_filename": pdf_path.name,
                "processing_time_ms": processing_time_ms,
                "transaction_count": len(standardized),
                "ai_detected": True,
            },
        }


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
