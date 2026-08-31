# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Data transformation utilities for PDF and Excel processing
Date normalization, debit/credit merging, amount conversion
"""
import re
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# ==================== Date Transformation Patterns ====================

# PDF date pattern: DD-MMM-YY or DD-MMM-YYYY (e.g., "15-JAN-23", "03-Jul-2026").
PDF_DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2,4}$")

# Excel serial date base: Excel dates are stored as days since 1900-01-01
EXCEL_EPOCH = datetime(1899, 12, 30)  # Excel epoch adjusted for Lotus 1-2-3 bug

# Case-insensitive month maps shared with the canonical date parser.
_MONTH_ABBR = {
    m.lower(): i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"],
        1,
    )
}
_MONTH_FULL = {
    m.lower(): i
    for i, m in enumerate(
        ["january", "february", "march", "april", "may", "june",
         "july", "august", "september", "october", "november", "december"],
        1,
    )
}


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def _strip_trailing_time(text: str) -> str:
    """Trim a trailing time component (credit-card statements carry '12:00 AM')."""
    return re.sub(
        r"\s+\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)?$", "", text.strip(), flags=re.IGNORECASE
    ).strip()


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def canonicalize_date(text: Any) -> Optional["datetime.date"]:
    """Parse a date-like cell into a datetime.date, or None.

    This is the canonical date parser used by both the production
    transformers and the structure assessor. It handles:
      - DD-MM-YY / DD/MM/YYYY and friends (numeric, any separator)
      - DD-MMM-YY and DD-MMM-YYYY (e.g. 05-MAY-26, 03-Jul-2026)
      - space-separated forms (Soneri style '23 05 2026')
      - ISO and dotted 4-digit-year forms
      - a trailing time component that is stripped first

    Returns None when the cell cannot be confidently parsed (never guessed).
    """
    if text is None:
        return None
    t = _strip_trailing_time(str(text))
    if not t:
        return None
    t_lower = t.lower()

    def _try(fmt: str) -> Optional["datetime.date"]:
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            return None

    # Fast path: the common 2-digit-year form DD-MM-YY / DD/MM/YY and friends.
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$", t)
    if m:
        a, b, y = m.group(1), m.group(2), m.group(3)
        yyyy = int(y) + (2000 if len(y) == 2 else 0)
        # Try day-month-year first (bank statements are DD/MM/YYYY); if the
        # first field is >12 it can only be a day, if the second is >12 it can
        # only be a month.
        cand = [(int(a), int(b)), (int(b), int(a))]
        for d, mo in cand:
            if 1 <= d <= 31 and 1 <= mo <= 12:
                try:
                    return datetime(yyyy, mo, d).date()
                except ValueError:
                    continue
        return None

    # Month-name forms (abbreviated or full), any separator.
    m = re.match(r"^(\d{1,2})\s*[-/.\s]\s*([a-z]+)\s*[-/.\s]\s*(\d{2,4})$", t_lower)
    if m:
        d, mon, y = m.group(1), m.group(2), m.group(3)
        mo = _MONTH_ABBR.get(mon) or _MONTH_FULL.get(mon)
        if mo:
            yyyy = int(y) + (2000 if len(y) == 2 else 0)
            try:
                return datetime(yyyy, mo, int(d)).date()
            except ValueError:
                return None

    # Space-separated numeric (Soneri style '23 05 2026').
    m = re.match(r"^(\d{1,2}) (\d{1,2}) (\d{2,4})$", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        yyyy = y if len(y) == 4 else "20" + y
        try:
            return datetime(int(yyyy), mo, d).date()
        except ValueError:
            return None

    # ISO and 4-digit-year slash forms, via strptime.
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%d.%m.%y"):
        d = _try(fmt)
        if d:
            return d

    return None


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def parse_amount(value: Any) -> Optional[float]:
    """Strictly parse a cell into a signed float amount.

    This is the canonical amount parser used by both the production
    transformers and the structure assessor. Handles:
      - thousands separators: `1,234,567.89` -> `1234567.89`
      - parenthesized negatives: `(29,880,105.57)` -> `-29880105.57`
      - leading/trailing whitespace and `-`, `−`, `–`, `+` prefixes
      - currency symbols (`Rs.`, `₨`, `$`)
      - mixed decimal separators (`.` or `,`), with a strict documented rule:
        the LAST separator is the decimal point, all earlier ones are
        thousands separators.

    Returns None when the cell cannot be parsed as an amount (never guessed).
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    # Parenthesized amount = negative (Meezan uses this for balances).
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]

    # Strip currency symbols and non-amount punctuation except separators.
    text = text.replace("Rs.", "").replace("rs.", "").replace("₨", "").replace("$", "")
    text = text.replace(" ", "").strip()

    # Reject double signs / multiple signs (e.g. "--5", "+-5") — a strict
    # parser must not guess.
    sign_chars = [c for c in text if c in "-−–+"]
    if len(sign_chars) > 1:
        return None

    # Leading sign.
    sign = 1.0
    if text[:1] in ("-", "−", "–"):
        sign = -1.0
        text = text[1:]
    elif text[:1] == "+":
        text = text[1:]

    if not text:
        return None

    # Mixed separators: last comma/dot is the decimal point, earlier are
    # thousands separators. A plain integer (no separator) also parses.
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            # Last separator is a comma -> it is the decimal point
            # (e.g. 1.234.567,89 -> 1234567,89 -> 1234567.89).
            text = text.replace(".", "").replace(",", ".")
        else:
            # Last separator is a dot -> it is the decimal point
            # (e.g. 1,234,567.89 -> 1234567.89).
            text = text.replace(",", "")
    elif "," in text and "." not in text:
        if text.endswith(","):
            # A single trailing comma is a decimal point (e.g. "123," -> 123.0).
            text = text[:-1] + "."
        else:
            # No dot: all commas are thousands separators (e.g. "1,234" -> 1234).
            text = text.replace(",", "")

    try:
        value = float(text)
    except ValueError:
        return None

    if negative:
        value = -value
    return sign * value


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def normalize_pdf_date(date_str: str) -> Optional[str]:
    """
    Convert PDF date to ISO format (YYYY-MM-DD).

    Delegates to the canonical `canonicalize_date` parser (the same one the
    structure assessor uses), so it accepts both DD-MMM-YY and DD-MMM-YYYY
    (e.g. "15-JAN-23", "03-Jul-2026"), plus the other numeric/space forms the
    assessor handles.

    Args:
        date_str: Date string from a PDF statement.

    Returns:
        ISO formatted date string (YYYY-MM-DD) or None if invalid.

    Examples:
        >>> normalize_pdf_date("15-JAN-23")
        "2023-01-15"
        >>> normalize_pdf_date("03-Jul-2026")
        "2026-07-03"
        >>> normalize_pdf_date("03-DEC-22")
        "2022-12-03"
    """
    try:
        if not date_str or not isinstance(date_str, str):
            return None
        parsed = canonicalize_date(date_str)
        if parsed is None:
            logger.warning(f"Invalid PDF date format: {date_str}")
            return None
        return parsed.isoformat()
    except Exception as e:
        logger.error(f"Error normalizing PDF date {date_str}: {str(e)}")
        return None


def normalize_excel_date(date_value: Any) -> Optional[str]:
    """
    Convert Excel date to ISO format (YYYY-MM-DD)
    Handles Excel serial dates and various string formats

    Args:
        date_value: Excel date value (serial number or string)

    Returns:
        ISO formatted date string (YYYY-MM-DD) or None if invalid

    Examples:
        >>> normalize_excel_date(44927)  # Excel serial date
        "2023-01-15"
        >>> normalize_excel_date("2023-01-15")  # ISO string
        "2023-01-15"
        >>> normalize_excel_date("15/01/2023")  # UK format
        "2023-01-15"
    """
    try:
        if pd.isna(date_value):
            return None

        # Handle Excel serial dates (numeric)
        if isinstance(date_value, (int, float)):
            try:
                # Convert Excel serial date to datetime
                # Excel dates are days since 1899-12-30 (adjusted for Lotus bug)
                delta = pd.Timedelta(days=float(date_value))
                excel_date = EXCEL_EPOCH + delta
                return excel_date.strftime("%Y-%m-%d")
            except (ValueError, OverflowError, TypeError):
                return None

        # Handle string dates
        if isinstance(date_value, str):
            date_str = date_value.strip()

            logger.debug(f"Parsing string date: '{date_str}' (len={len(date_str)})")

            if not date_str:
                return None

            # Try common date formats
            date_formats = [
                "%Y-%m-%d",    # ISO: 2023-01-15
                "%d/%m/%Y",    # UK: 15/01/2023
                "%m/%d/%Y",    # US: 01/15/2023
                "%Y/%m/%d",    # Alternative: 2023/01/15
                "%d-%m-%Y",    # Alternative: 15-01-2023
                "%m-%d-%Y",    # Alternative: 01-15-2023
                "%d.%m.%y",    # DD.MM.YY: 05.05.26 (IMPORTANT: Excel format)
                "%d.%m.%Y",    # DD.MM.YYYY: 05.05.2026
                "%d %b %Y",    # 15 Jan 2023
                "%d %B %Y",    # 15 January 2023
                "%b %d, %Y",   # Jan 15, 2023
                "%B %d, %Y",   # January 15, 2023
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    logger.debug(f"Successfully parsed date '{date_str}' with format '{fmt}'")
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # If none of the formats matched
            logger.warning(f"Unable to parse Excel date: {date_value}")
            return None

        return None

    except Exception as e:
        logger.error(f"Error normalizing Excel date {date_value}: {str(e)}")
        return None


def merge_debit_credit(debit_value: Optional[float], credit_value: Optional[float]) -> Optional[float]:
    """
    Merge separate debit and credit columns into single Debit/Credit value
    Debit: negative float, Credit: positive float

    Args:
        debit_value: Debit amount (can be None/NaN)
        credit_value: Credit amount (can be None/NaN)

    Returns:
        Float amount (negative=debit, positive=credit) or None if invalid

    Examples:
        >>> merge_debit_credit(100.50, None)
        -100.50
        >>> merge_debit_credit(None, 25.75)
        25.75
        >>> merge_debit_credit(100, 50)  # Both present - ERROR
        None
    """
    try:
        # Handle NaN values from pandas
        if pd.isna(debit_value):
            debit_value = None
        if pd.isna(credit_value):
            credit_value = None

        # Treat blank/whitespace strings as missing (e.g. layout extractor
        # produces "" for empty cells)
        if isinstance(debit_value, str) and not debit_value.strip():
            debit_value = None
        if isinstance(credit_value, str) and not credit_value.strip():
            credit_value = None

        # A literal zero cell is a BLANK amount cell, not a value: in a
        # debit/credit layout only one of the two columns carries an amount
        # per row, and the opposite column prints "0" (or "0.00") for empty.
        # Treating 0 as "present" made every row look ambiguous and dropped
        # the whole statement. A zero amount is not a transaction.
        if debit_value is not None and (
            debit_value == 0
            or (isinstance(debit_value, str) and parse_amount(debit_value) == 0)
        ):
            debit_value = None
        if credit_value is not None and (
            credit_value == 0
            or (isinstance(credit_value, str) and parse_amount(credit_value) == 0)
        ):
            credit_value = None

        # Both None - invalid
        if debit_value is None and credit_value is None:
            logger.warning("Both debit and credit are None/missing")
            return None

        # Both present - ambiguous, should not happen
        if debit_value is not None and credit_value is not None:
            logger.warning(f"Ambiguous transaction: both debit={debit_value} and credit={credit_value} present")
            return None

        # Debit only - negative float (money out). Uses the canonical
        # parse_amount so parenthesized negatives "(1,234.56)" and comma/
        # currency formats parse correctly (same parser as the assessor).
        if debit_value is not None:
            amount = parse_amount(debit_value)
            if amount is None or amount == 0:
                logger.warning(f"Invalid debit value: {debit_value}")
                return None
            return -abs(amount)

        # Credit only - positive float (money in)
        if credit_value is not None:
            amount = parse_amount(credit_value)
            if amount is None or amount == 0:
                logger.warning(f"Invalid credit value: {credit_value}")
                return None
            return abs(amount)

        return None

    except Exception as e:
        logger.error(f"Error merging debit/credit: {str(e)}")
        return None


def merge_company_debit_credit(debit_value: Optional[Any], credit_value: Optional[Any]) -> Optional[float]:
    """
    Merge separate company cash-book debit and credit columns into a single
    Debit/Credit value under the COMPANY convention.

    The company cash book records a debit (money out, e.g. a cheque issued) as
    a POSITIVE figure and a credit (money in) as a NEGATIVE figure. This is the
    direct convention used end-to-end for company records:
        Debit: positive float, Credit: negative float.

    Args:
        debit_value: Debit amount from the company file (can be None/NaN).
        credit_value: Credit amount from the company file (can be None/NaN).

    Returns:
        Float amount (negative=credit, positive=debit) or None if invalid.
    """
    try:
        # Handle NaN values from pandas
        if pd.isna(debit_value):
            debit_value = None
        if pd.isna(credit_value):
            credit_value = None

        # Treat blank/whitespace strings as missing
        if isinstance(debit_value, str) and not debit_value.strip():
            debit_value = None
        if isinstance(credit_value, str) and not credit_value.strip():
            credit_value = None

        # A literal zero cell is a BLANK amount cell, not a value.
        if debit_value is not None and (
            debit_value == 0
            or (isinstance(debit_value, str) and parse_amount(debit_value) == 0)
        ):
            debit_value = None
        if credit_value is not None and (
            credit_value == 0
            or (isinstance(credit_value, str) and parse_amount(credit_value) == 0)
        ):
            credit_value = None

        # Both None - invalid
        if debit_value is None and credit_value is None:
            return None

        # Both present - ambiguous, should not happen
        if debit_value is not None and credit_value is not None:
            return None

        # Debit only - positive float (money out, company convention)
        if debit_value is not None:
            amount = parse_amount(debit_value)
            if amount is None or amount == 0:
                return None
            return abs(amount)

        # Credit only - negative float (money in, company convention)
        if credit_value is not None:
            amount = parse_amount(credit_value)
            if amount is None or amount == 0:
                return None
            return -abs(amount)

        return None

    except Exception as e:
        logger.error(f"Error merging company debit/credit: {str(e)}")
        return None


def convert_combined_amount(amount_value: Any, sign: str) -> Optional[float]:
    """
    Convert combined amount column to float with proper sign
    For 3-column format where debit/credit are in one column

    Args:
        amount_value: Amount value (numeric or string)
        sign: Sign indicator ('debit', 'credit', or auto-detected)

    Returns:
        Float amount (negative=debit, positive=credit) or None if invalid

    Examples:
        >>> convert_combined_amount(100.50, 'debit')
        -100.50
        >>> convert_combined_amount(25.75, 'credit')
        25.75
        >>> convert_combined_amount(-100, 'auto')  # Preserves Excel sign as-is
        -100.0
    """
    try:
        if pd.isna(amount_value):
            return None

        # Auto-detect sign from amount value (preserve original sign). Uses
        # the canonical parse_amount so parenthesized/commas/currency parse.
        if sign == 'auto':
            parsed = parse_amount(amount_value)
            if parsed is None or parsed == 0:
                return None
            return parsed

        amount = parse_amount(amount_value)
        if amount is None:
            return None

        if amount == 0:
            return None

        # Apply explicit sign (debit=negative, credit=positive)
        if sign == 'credit':
            return abs(amount)   # Credit = positive (money in)
        elif sign == 'debit':
            return -abs(amount)  # Debit = negative (money out)
        else:
            logger.warning(f"Invalid sign specification: {sign}")
            return None

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid amount value: {amount_value} - {str(e)}")
        return None


def standardize_transaction_data(
    date_value: Any,
    detail_value: Any,
    amount_value: Any,
    debit_value: Optional[Any] = None,
    credit_value: Optional[Any] = None,
    source_type: str = 'pdf'
) -> Optional[Dict[str, Any]]:
    """
    Standardize transaction data to common format
    Transforms various input formats to standardized ProcessedTransaction format

    Args:
        date_value: Date value (various formats)
        detail_value: Transaction description/narrative
        amount_value: Combined amount (for 3-column format)
        debit_value: Debit amount (for 4-column format)
        credit_value: Credit amount (for 4-column format)
        source_type: Data source ('pdf' or 'excel')

    Returns:
        Standardized transaction dict or None if invalid

    Examples:
        >>> standardize_transaction_data("15-JAN-23", "Payment", None, 100, None, 'pdf')
        {"Transaction_date": "2023-01-15", "Transaction Detail": "Payment", "Debit/Credit": 100}
    """
    try:
        # Normalize date based on source type. A missing/unparseable date is
        # OPTIONAL - the row is kept with an empty date rather than dropped
        # (reconciliation matches on amount + detail, not date alone).
        if source_type == 'pdf':
            normalized_date = normalize_pdf_date(date_value)
        elif source_type == 'excel':
            normalized_date = normalize_excel_date(date_value)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return None

        if not normalized_date:
            logger.warning("Empty transaction date - keeping row with empty date")

        # Clean transaction detail. Missing detail is OPTIONAL - the row is
        # kept with an empty detail rather than dropped.
        transaction_detail = str(detail_value).strip() if detail_value else ""
        if not transaction_detail:
            logger.warning("Empty transaction detail - keeping row with empty detail")

        # Handle debit/credit merging
        debit_credit = None
        if debit_value is not None or credit_value is not None:
            # 4-column format: separate debit/credit
            debit_credit = merge_debit_credit(debit_value, credit_value)
        elif amount_value is not None:
            # 3-column format: combined amount (preserve original sign)
            if pd.isna(amount_value):
                amount_value = None
            if amount_value is not None:
                # Use 'auto' to preserve the original sign from Excel data
                debit_credit = convert_combined_amount(amount_value, 'auto')

        if debit_credit is None or debit_credit == 0:
            logger.warning(f"Invalid or zero debit/credit amount")
            return None

        # Build standardized transaction
        return {
            "Transaction_date": normalized_date,
            "Transaction Detail": transaction_detail,
            "Debit/Credit": debit_credit
        }

    except Exception as e:
        logger.error(f"Error standardizing transaction data: {str(e)}")
        return None


def validate_standardized_transaction(transaction: Dict[str, Any]) -> bool:
    """
    Validate that a transaction meets all requirements
    Check field types, values, and constraints

    Args:
        transaction: Transaction dict to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields exist
        required_fields = ["Transaction_date", "Transaction Detail", "Debit/Credit"]
        for field in required_fields:
            if field not in transaction:
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate Transaction_date format (YYYY-MM-DD)
        date_str = transaction["Transaction_date"]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            logger.warning(f"Invalid date format: {date_str}")
            return False

        # Validate Transaction Detail is non-empty
        detail = transaction["Transaction Detail"]
        if not detail or not isinstance(detail, str) or not detail.strip():
            logger.warning("Empty or invalid Transaction Detail")
            return False

        # Validate Debit/Credit is non-zero float
        amount = transaction["Debit/Credit"]
        if not isinstance(amount, (int, float)) or amount == 0:
            logger.warning(f"Invalid Debit/Credit: {amount}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating transaction: {str(e)}")
        return False


def clean_transaction_detail(detail: str) -> str:
    """
    Clean and normalize transaction detail text
    Remove extra whitespace, special characters, normalize length

    Args:
        detail: Raw transaction detail string

    Returns:
        Cleaned transaction detail
    """
    try:
        if not detail or not isinstance(detail, str):
            return ""

        # Strip leading/trailing whitespace
        cleaned = detail.strip()

        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Remove special characters that might cause issues
        # Keep alphanumeric, basic punctuation, and common currency symbols
        cleaned = re.sub(r'[^\w\s\.\,\-\£\€\$\#\(\)]+', '', cleaned)

        # Truncate if too long (max 500 chars)
        if len(cleaned) > 500:
            cleaned = cleaned[:500]

        return cleaned.strip()

    except Exception as e:
        logger.error(f"Error cleaning transaction detail: {str(e)}")
        return str(detail).strip() if detail else ""


def create_processing_summary(
    bank_transactions: List[Dict[str, Any]],
    company_transactions: List[Dict[str, Any]],
    processing_time_ms: int
) -> Dict[str, Any]:
    """
    Create processing summary statistics
    Consolidate transaction counts and timing information

    Args:
        bank_transactions: List of bank statement transactions
        company_transactions: List of company record transactions
        processing_time_ms: Total processing time in milliseconds

    Returns:
        Summary statistics dictionary
    """
    return {
        "total_bank_transactions": len(bank_transactions),
        "total_company_transactions": len(company_transactions),
        "processing_duration_ms": processing_time_ms
    }

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ