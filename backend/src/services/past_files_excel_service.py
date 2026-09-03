# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Excel template generation + parsing for Past Reconciliations.

Creates a 4-section workbook (one block per discrepancy category) with
Date | Details | Amount columns, prefilled with existing discrepancies for
Edit or left empty for Create. Parses an uploaded template back into the
stored wire format (category, transaction_details, transaction_date,
debit_credit_amount), applying the settled per-category sign convention.
"""
import logging
import re
import io
from datetime import date, datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category labels — MUST match exactly what the frontend stores in files
# (see categorizeDiscrepancy in ReconciliationResults.tsx).
# ---------------------------------------------------------------------------

BANK_CATEGORIES = [
    "Unpresented Checks",
    "Uncleared Checks",
    "Bank Debited But not Credited in Cashbook",
    "Bank Credited But not Debited in Cashbook",
]

VENDOR_CATEGORIES = [
    "Unpresented Checks",
    "Uncleared Checks",
    "Vendor Debited but not Credited in Cashbook",
    "Vendor Credited But not Debited in Cashbook",
]

# Settled sign convention: the wire value carries the pure source-specific
# sign. The Excel Amount column is UNSIGNED; the sign is applied per section.
#   Bank:      credit = +, debit = -
#   Company:   credit = -, debit = +   (Unpresented = -, Uncleared = +)
#   Vendor:    credit = -, debit = +   (source-side rows)
_SIGN_BY_CATEGORY = {
    "Unpresented Checks": -1.0,
    "Uncleared Checks": 1.0,
    "Bank Debited But not Credited in Cashbook": -1.0,
    "Bank Credited But not Debited in Cashbook": 1.0,
    "Vendor Debited but not Credited in Cashbook": 1.0,
    "Vendor Credited But not Debited in Cashbook": -1.0,
}

INSTRUCTIONS = [
    "Instructions (read before editing):",
    "1. Do NOT put any signs (+/-) on amounts — they are applied automatically per category.",
    "2. Do NOT change the structure of this file — add/remove rows only inside the 4 category blocks.",
    "3. Keep the date pattern consistent across all discrepancies (e.g. DD-MM-YYYY).",
]

_DARK_GREEN = "14532D"
_HEADER_GREEN = "166534"
_LIGHT_ROW = "F0FDF4"
_SUBTLE_GRAY = "F4F4F5"


def categories_for_type(reconciliation_type: str) -> list[str]:
    return VENDOR_CATEGORIES if reconciliation_type == "vendor" else BANK_CATEGORIES


def sign_for_category(category: str) -> float:
    return _SIGN_BY_CATEGORY.get(category, 1.0)


def _format_cell_date(value) -> str:
    """Render a stored date string (or datetime) into a consistent DD-MM-YYYY form."""
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%d-%m-%Y")
    return str(value)


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_template(reconciliation_type: str, discrepancies: list[dict]) -> bytes:
    """
    Build an xlsx template in memory.

    - For Edit: pre-fills each category block with that category's existing
      discrepancies (date, details, unsigned amount).
    - For Create: empty category blocks.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Past Reconciliation"

    for col, width in (("A", 16), ("B", 60), ("C", 18)):
        ws.column_dimensions[col].width = width

    # --- Instruction rows ---------------------------------------------------
    for i, text in enumerate(INSTRUCTIONS, start=1):
        cell = ws.cell(row=i, column=1, value=text)
        cell.font = Font(italic=True, color="6B7280", size=10)
        if i == 1:
            cell.font = Font(bold=True, italic=True, color="374151", size=10)

    # Group incoming discrepancies by their stored category label.
    by_category: dict[str, list[dict]] = {c: [] for c in categories_for_type(reconciliation_type)}
    for entry in discrepancies or []:
        cat = entry.get("category") or ""
        if cat in by_category:
            by_category[cat].append(entry)
        else:
            # Unknown category label — keep it under the closest section by
            # keyword so no data is silently dropped when a file predates the
            # current category strings.
            cat_lower = cat.lower()
            if "vendor" in cat_lower or "debited" in cat_lower and "cashbook" in cat_lower and "bank" not in cat_lower:
                by_category["Vendor Debited but not Credited in Cashbook"].append(entry)
            elif "vendor" in cat_lower or "credited" in cat_lower and "cashbook" in cat_lower and "bank" not in cat_lower:
                by_category["Vendor Credited But not Debited in Cashbook"].append(entry)
            elif "debited" in cat_lower:
                by_category["Bank Debited But not Credited in Cashbook"].append(entry)
            else:
                by_category["Bank Credited But not Debited in Cashbook"].append(entry)

    row_idx = len(INSTRUCTIONS) + 2  # blank spacer row after instructions

    for category in categories_for_type(reconciliation_type):
        # --- Category block header (dark green) ------------------------------
        cat_cell = ws.cell(row=row_idx, column=1, value=category.upper())
        cat_cell.font = Font(bold=True, color="FFFFFF", size=12)
        cat_cell.fill = PatternFill("solid", fgColor=_DARK_GREEN)
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=3)
        cat_cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[row_idx].height = 22
        row_idx += 1

        # --- Column headers ----------------------------------------------------
        for col, header in (("A", "Date"), ("B", "Details"), ("C", "Amount")):
            cell = ws.cell(row=row_idx, column=1 if col == "A" else 2 if col == "B" else 3, value=header)
            cell.font = Font(bold=True, color="FFFFFF", size=10)
            cell.fill = PatternFill("solid", fgColor=_HEADER_GREEN)
        row_idx += 1

        # --- Data rows ----------------------------------------------------------
        for entry in by_category[category]:
            amount = entry.get("debit_credit_amount") or 0
            unsigned = abs(float(amount))
            ws.cell(row=row_idx, column=1, value=_format_cell_date(entry.get("transaction_date")))
            ws.cell(row=row_idx, column=2, value=entry.get("transaction_details") or "")
            amount_cell = ws.cell(row=row_idx, column=3, value=round(unsigned, 2))
            amount_cell.number_format = "#,##0.00"
            row_idx += 1

        # A blank spacer row between blocks keeps the structure easy to read.
        row_idx += 1

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def parse_template(file_bytes: bytes) -> list[dict]:
    """
    Parse an uploaded template back into wire-format discrepancy dicts.

    Reads row by row, tracking the current category section via the dark-green
    block headers. Skips instructions, column headers, and blank rows. Amounts
    are read as unsigned and signed per section. Raises ValueError with a
    section/row-specific message when an amount cannot be parsed.
    """
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    all_categories = BANK_CATEGORIES + VENDOR_CATEGORIES
    header_labels = {"date", "details", "amount"}

    current_category: str | None = None
    in_data_block = False
    discrepancies: list[dict] = []
    section_errors: list[str] = []

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row or 0, max_col=3):
        values = []
        for cell in row:
            v = cell.value
            if isinstance(v, str):
                v = v.strip()
            values.append(v)

        # Category block header (dark green label row) — a single cell A
        # containing one of the known labels (case-insensitive).
        first_text = str(values[0] or "").strip()
        first_upper = first_text.upper()
        matched = next((c for c in all_categories if c.upper() == first_upper), None)
        if matched is not None and all(v is None or str(v).strip() == "" for v in values[1:]):
            current_category = matched
            in_data_block = True
            continue

        # Column header row inside a block ("Date | Details | Amount").
        if current_category and in_data_block:
            normalized = {str(v).strip().lower() for v in values if v is not None and str(v).strip()}
            if normalized and normalized.issubset(header_labels) and len(normalized) >= 2:
                continue

        # Data row: only capture rows while inside a block and not blank.
        if current_category and in_data_block:
            if all(v is None or str(v).strip() == "" for v in values):
                continue

            details = str(values[1] or "").strip()
            if values[0] is None and not details:
                continue

            raw_amount = values[2] if len(values) > 2 else None
            if raw_amount is None or str(raw_amount).strip() == "":
                continue

            try:
                amount = _parse_amount(raw_amount)
            except ValueError:
                section_errors.append(
                    f"Section '{current_category}' — row {row[0].row}: "
                    f"could not parse amount '{raw_amount}'. Use plain numbers "
                    f"without signs (e.g. 49000 or 49,000)."
                )
                continue

            discrepancies.append({
                "category": current_category,
                "transaction_details": details,
                "transaction_date": _format_cell_date(values[0]) if values[0] is not None else "",
                "debit_credit_amount": round(amount * sign_for_category(current_category), 2),
            })

    if section_errors:
        raise ValueError("; ".join(section_errors))

    return discrepancies


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _parse_amount(value) -> float:
    """Parse an unsigned amount, tolerating commas and currency symbols."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        raise ValueError("empty amount")
    # Strip currency symbols / letters, keep digits, dots, commas, minus (in
    # case the user ignored the "no signs" instruction — the category sign
    # overrides any typed sign to keep the book convention consistent).
    cleaned = re.sub(r"[^0-9.,\-]", "", text)
    cleaned = cleaned.replace(",", "")
    try:
        parsed = float(cleaned)
    except ValueError:
        raise ValueError(f"could not parse amount '{text}'")
    return abs(parsed)


def safe_filename_part(name: str) -> str:
    """Sanitize a file name for use in an xlsx download filename."""
    safe = re.sub(r'[^\w\-. ]+', '', name).strip()
    return safe or "past-reconciliation"

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
