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

# PDF date pattern: DD-MMM-YY (e.g., "15-JAN-23")
PDF_DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")

# Excel serial date base: Excel dates are stored as days since 1900-01-01
EXCEL_EPOCH = datetime(1899, 12, 30)  # Excel epoch adjusted for Lotus 1-2-3 bug


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def normalize_pdf_date(date_str: str) -> Optional[str]:
    """
    Convert PDF date format (DD-MMM-YY) to ISO format (YYYY-MM-DD)
    Handles 2-digit year conversion with pivot year

    Args:
        date_str: Date string in PDF format (e.g., "15-JAN-23")

    Returns:
        ISO formatted date string (YYYY-MM-DD) or None if invalid

    Examples:
        >>> normalize_pdf_date("15-JAN-23")
        "2023-01-15"
        >>> normalize_pdf_date("03-DEC-22")
        "2022-12-03"
    """
    try:
        if not date_str or not isinstance(date_str, str):
            return None

        # Validate format with pattern
        if not PDF_DATE_PATTERN.match(date_str):
            logger.warning(f"Invalid PDF date format: {date_str}")
            return None

        # Parse components
        parts = date_str.split('-')
        if len(parts) != 3:
            return None

        day, month_abbr, year_short = parts

        # Convert 2-digit year to 4-digit (pivot year: 50)
        year_int = int(year_short)
        if year_int >= 50:
            year = 1900 + year_int
        else:
            year = 2000 + year_int

        # Convert month abbreviation to number
        month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        month = month_map.get(month_abbr.upper())
        if not month:
            return None

        # Convert day to integer
        day_int = int(day)

        # Validate date ranges
        if not (1 <= day_int <= 31) or not (1 <= month <= 12):
            return None

        # Format as ISO date
        try:
            iso_date = f"{year:04d}-{month:02d}-{day_int:02d}"
            # Validate by parsing back
            datetime.strptime(iso_date, "%Y-%m-%d")
            return iso_date
        except ValueError:
            return None

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

        # Both None - invalid
        if debit_value is None and credit_value is None:
            logger.warning("Both debit and credit are None/missing")
            return None

        # Both present - ambiguous, should not happen
        if debit_value is not None and credit_value is not None:
            logger.warning(f"Ambiguous transaction: both debit={debit_value} and credit={credit_value} present")
            return None

        # Debit only - negative float (money out)
        if debit_value is not None:
            try:
                # Handle string values with commas (e.g., "10,200.00")
                if isinstance(debit_value, str):
                    debit_value = debit_value.replace(',', '')

                amount = float(debit_value)
                if amount == 0:
                    return None
                return -abs(amount)
            except (ValueError, TypeError):
                logger.warning(f"Invalid debit value: {debit_value}")
                return None

        # Credit only - positive float (money in)
        if credit_value is not None:
            try:
                # Handle string values with commas (e.g., "22,000.00")
                if isinstance(credit_value, str):
                    credit_value = credit_value.replace(',', '')

                amount = float(credit_value)
                if amount == 0:
                    return None
                return abs(amount)
            except (ValueError, TypeError):
                logger.warning(f"Invalid credit value: {credit_value}")
                return None

        return None

    except Exception as e:
        logger.error(f"Error merging debit/credit: {str(e)}")
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

        # Convert to float
        amount = float(amount_value)

        if amount == 0:
            return None

        # Auto-detect sign from amount value (preserve original sign)
        if sign == 'auto':
            # Preserve the original sign from Excel: negative = debit, positive = credit
            return amount

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
        # Normalize date based on source type
        if source_type == 'pdf':
            normalized_date = normalize_pdf_date(date_value)
        elif source_type == 'excel':
            normalized_date = normalize_excel_date(date_value)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return None

        if not normalized_date:
            return None

        # Clean transaction detail
        transaction_detail = str(detail_value).strip() if detail_value else ""
        if not transaction_detail:
            logger.warning("Empty transaction detail")
            return None

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