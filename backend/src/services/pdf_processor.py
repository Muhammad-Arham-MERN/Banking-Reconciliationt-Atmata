# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
PDF Processing Service
Extract transaction data from PDF bank statements
Uses layout-based column slicing via pdfplumber with explicit column boundaries
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import pdfplumber

from src.utils.data_transformers import (
    normalize_pdf_date,
    standardize_transaction_data, clean_transaction_detail, parse_amount
)
from src.utils.logger import (
    log_pdf_extraction, log_transformation_stats,
    log_performance_warning
)
from src.utils.error_handlers import PDFProcessingError

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# ==================== Helper Functions ====================

# Column boundary x-coordinates (in PDF points) measured from the bank statement
# template. These are the physical column edges of the layout; slicing words by
# these lines is deterministic and independent of whitespace inference,
# which can merge/split columns differently across pages of the same statement.
# Page width for this statement is 612 points.
COLUMN_BOUNDARIES = [45.0, 89.0, 195.0, 246.0, 298.0, 348.0, 440.0, 500.0, 570.0]

# Vertical band (in PDF points) that contains the transaction rows. Everything
# above is the account header, everything below is the summary/footer.
TRANSACTION_BAND_TOP = 170.0
TRANSACTION_BAND_BOTTOM = 765.0


def _slice_words_to_columns(words: list[dict]) -> list[str]:
    """Assign words to the 10 physical columns by their horizontal center."""
    cells = ["" for _ in range(len(COLUMN_BOUNDARIES) + 1)]
    for w in words:
        cx = (w["x0"] + w["x1"]) / 2
        idx = sum(1 for b in COLUMN_BOUNDARIES if cx > b)
        if idx < len(cells):
            cells[idx] = (cells[idx] + " " + w["text"]).strip()
    return cells


def _extract_rows_via_layout(pdf_path: str) -> pd.DataFrame:
    """Extract transaction rows by slicing words at explicit column boundaries.

    Uses pdfplumber to get word-level geometry, then assigns each word to one of
    the 10 physical columns by its x-center. This is robust to whitespace
    inference, which can merge/split columns differently across pages.
    """
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            # Group words into visual lines by their top coordinate
            lines: dict[float, list[dict]] = {}
            for w in words:
                if TRANSACTION_BAND_TOP <= w["top"] <= TRANSACTION_BAND_BOTTOM:
                    lines.setdefault(round(w["top"], 1), []).append(w)

            for top in sorted(lines):
                cells = _slice_words_to_columns(lines[top])
                # Keep only transaction rows: first column is a statement date
                if re.match(DATE_PATTERN, cells[0]):
                    rows.append(
                        {
                            "Tran. Date": cells[0],
                            "Effect Date": cells[1],
                            "Tran. Narrative": cells[2],
                            "Remitter IBAN": cells[3],
                            "Remitter Bank": cells[4],
                            "Chq / Ref No": cells[6],
                            "Debit": cells[7],
                            "Credit": cells[8],
                            "Balance": cells[9],
                        }
                    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Split the merged "Tran. Br. + Transaction Details" column (branch code prefix)
    branch_and_details = df["Tran. Narrative"].astype(str).str.extract(
        BRANCH_NARRATIVE_PATTERN
    )
    df["Tran. Br."] = branch_and_details[0]
    df["Transaction Details"] = branch_and_details[1]

    return df


def _dedupe_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate transactions based on key fields."""
    if df.empty:
        return df
    return df.drop_duplicates(
        subset=["Tran. Date", "Chq / Ref No", "Debit", "Credit"],
        keep="first",
    ).reset_index(drop=True)


# ==================== Constants ====================

# Date pattern for PDF bank statements
DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")

# Pattern to extract branch and narrative from merged column
BRANCH_NARRATIVE_PATTERN = re.compile(r"^(\d{4})\s+(.+)$")


# ==================== PDF Processor Class ====================

class PDFProcessor:
    """
    Process PDF bank statements to extract transaction data
    Uses layout-based column slicing via pdfplumber
    """

    def __init__(self, request_id: str = "unknown"):
        """
        Initialize PDF processor

        Args:
            request_id: Request identifier for logging
        """
        self.request_id = request_id
        self.processing_logger = logging.getLogger(__name__)

    def extract_bank_statement(self, pdf_path: Path) -> pd.DataFrame:
        """
        Extract transaction data from PDF bank statement
        Uses layout-based slicing: words are cut at the statement's physical
        column boundaries (see COLUMN_BOUNDARIES), independent of whitespace
        inference.

        Args:
            pdf_path: Path to PDF file

        Returns:
            DataFrame with extracted transaction data

        Raises:
            PDFProcessingError: If PDF processing fails
        """
        import time
        start_time = time.time()

        try:
            # Validate PDF path exists
            if not pdf_path.exists():
                raise PDFProcessingError(
                    f"PDF file not found: {pdf_path}",
                    details={"file_path": str(pdf_path)}
                )

            # Extract transaction rows by slicing words at explicit column boundaries
            df = _extract_rows_via_layout(str(pdf_path))

            if df.empty:
                raise PDFProcessingError(
                    f"No valid transaction data found in PDF",
                    details={"pdf_path": str(pdf_path)},
                    error_type="no_transactions"
                )

            # Deduplicate identical transactions
            df = _dedupe_transactions(df)
            logger.info(f"Extracted {len(df)} unique transactions")

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log extraction statistics
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages_processed = len(pdf.pages)
            tables_extracted = 1
            rows_extracted = len(df)

            log_pdf_extraction(
                logger,
                self.request_id,
                str(pdf_path),
                pages_processed,
                tables_extracted,
                rows_extracted,
                processing_time_ms
            )

            # Performance warning if processing took too long
            if processing_time_ms > 30000:  # 30 seconds threshold
                log_performance_warning(
                    logger,
                    self.request_id,
                    "PDF extraction",
                    processing_time_ms,
                    30000
                )

            return df

        except PDFProcessingError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error extracting PDF: {str(e)}"
            logger.error(error_msg)
            raise PDFProcessingError(
                error_msg,
                details={"pdf_path": str(pdf_path), "error": str(e)}
            )

    def transform_to_standard_format(
        self,
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Transform extracted PDF data to standardized transaction format
        Merge debit/credit columns, convert to integer, normalize dates

        Args:
            df: DataFrame from extract_bank_statement()

        Returns:
            List of standardized transaction dictionaries

        Raises:
            PDFProcessingError: If transformation fails
        """
        import time
        start_time = time.time()

        try:
            if df.empty:
                logger.warning(f"Empty DataFrame provided for transformation")
                return []

            standardized_transactions = []
            transformation_errors = 0

            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Extract row data
                    date_value = row.get("Tran. Date")
                    detail_value = row.get("Transaction Details")
                    debit_value = row.get("Debit")
                    credit_value = row.get("Credit")

                    # Clean transaction detail
                    cleaned_detail = clean_transaction_detail(str(detail_value))

                    # Create standardized transaction
                    transaction = standardize_transaction_data(
                        date_value=date_value,
                        detail_value=cleaned_detail,
                        amount_value=None,  # Not used for 4-column format
                        debit_value=debit_value,
                        credit_value=credit_value,
                        source_type='pdf'
                    )

                    if transaction:
                        standardized_transactions.append(transaction)
                    else:
                        transformation_errors += 1
                        logger.debug(
                            f"Failed to standardize transaction at row {idx}: "
                            f"date={date_value}, detail={detail_value}"
                        )

                except Exception as row_error:
                    transformation_errors += 1
                    logger.debug(f"Error processing row {idx}: {str(row_error)}")
                    continue

            # Log transformation statistics
            processing_time_ms = int((time.time() - start_time) * 1000)
            log_transformation_stats(
                logger,
                self.request_id,
                'pdf',
                len(df),
                len(standardized_transactions),
                transformation_errors
            )

            return standardized_transactions

        except Exception as e:
            error_msg = f"Unexpected error transforming PDF data: {str(e)}"
            logger.error(error_msg)
            raise PDFProcessingError(
                error_msg,
                details={"error": str(e)}
            )

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize PDF date format (DD-MMM-YY) to ISO format (YYYY-MM-DD)
        Wrapper for data_transformers.normalize_pdf_date

        Args:
            date_str: Date string in PDF format

        Returns:
            ISO formatted date string or None if invalid
        """
        return normalize_pdf_date(date_str)

    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline: extract and transform
        Main entry point for PDF processing

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with processed data and metadata

        Raises:
            PDFProcessingError: If processing fails
        """
        import time
        total_start_time = time.time()

        try:
            # Extract raw data
            df = self.extract_bank_statement(pdf_path)

            # Extract last Balance column value from raw DataFrame
            # Balance is the final column sliced by the layout boundaries
            bank_net_total = {"value": None, "status": "missing"}
            if not df.empty and "Balance" in df.columns:
                # Drop rows where Balance is NaN/None before getting last
                valid_balance = df["Balance"].dropna()
                if not valid_balance.empty:
                    last_balance = valid_balance.iloc[-1]
                    try:
                        # Parse with the canonical parse_amount: handles
                        # parenthesized negatives like "(1,234.56)" -> -1234.56
                        # (some PDF writers print a negative balance in
                        # brackets), currency symbols, and thousands
                        # separators — the naive float()/replace() path marked
                        # those "invalid".
                        parsed = parse_amount(last_balance)
                        if parsed is not None:
                            bank_net_total["value"] = parsed
                            bank_net_total["status"] = "found"
                        else:
                            bank_net_total["status"] = "invalid"
                    except (ValueError, TypeError):
                        bank_net_total["status"] = "invalid"
                        logger.warning(f"Could not parse Balance value: {last_balance}")
                else:
                    bank_net_total["status"] = "invalid"
                    logger.warning("Balance column found but no valid values")
            else:
                logger.warning("Balance column not found in extracted PDF data")

            # Transform to standard format
            standardized_transactions = self.transform_to_standard_format(df)

            total_processing_time_ms = int((time.time() - total_start_time) * 1000)

            # Build result
            result = {
                "bank_statement": standardized_transactions,
                "bank_net_total": bank_net_total,
                "processing_metadata": {
                    "pdf_filename": pdf_path.name,
                    "processing_time_ms": total_processing_time_ms,
                    "transaction_count": len(standardized_transactions)
                }
            }

            logger.info(
                f"PDF processing complete: {len(standardized_transactions)} transactions "
                f"extracted in {total_processing_time_ms}ms"
            )

            return result

        except PDFProcessingError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error in PDF processing pipeline: {str(e)}"
            logger.error(error_msg)
            raise PDFProcessingError(
                error_msg,
                details={"pdf_path": str(pdf_path), "error": str(e)}
            )


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ