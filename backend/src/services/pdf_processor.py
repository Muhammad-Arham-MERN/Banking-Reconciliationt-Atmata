# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
PDF Processing Service
Extract transaction data from PDF bank statements using tabula-py
Following test.py pattern with positional column mapping
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import tabula

from src.utils.data_transformers import (
    normalize_pdf_date,
    standardize_transaction_data, clean_transaction_detail
)
from src.utils.logger import (
    log_pdf_extraction, log_transformation_stats,
    log_performance_warning
)
from src.utils.error_handlers import PDFProcessingError

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# ==================== Helper Functions from test.py Pattern ====================

def _process_raw_table(raw: pd.DataFrame | str) -> pd.DataFrame:
    """Skip header rows, map columns, and keep valid transaction rows."""
    # Handle case where tabula returns strings instead of DataFrames
    if not isinstance(raw, pd.DataFrame):
        return pd.DataFrame()

    if raw.empty or len(raw) <= 3:
        return pd.DataFrame()

    df = raw.iloc[3:].copy()
    df.columns = CANONICAL_COLUMNS
    df = df.drop(columns=["_unused_1", "_unused_2"])

    branch_and_details = df["Tran. Narrative"].astype(str).str.extract(
        BRANCH_NARRATIVE_PATTERN
    )
    df["Tran. Br."] = branch_and_details[0]
    df["Transaction Details"] = branch_and_details[1]

    return df[df["Tran. Date"].astype(str).str.match(DATE_PATTERN, na=False)]


def _process_area_fallback_table(raw: pd.DataFrame | str) -> pd.DataFrame:
    """Parse tabula area-extracted rows where columns collapse on continuation pages."""
    # Handle case where tabula returns strings instead of DataFrames
    if not isinstance(raw, pd.DataFrame):
        return pd.DataFrame()

    rows = []
    for _, row in raw.iterrows():
        header = str(row.iloc[0] or "").strip()
        header_match = AREA_ROW_PATTERN.match(header)
        if not header_match:
            continue

        tran_date, effect_date, narrative = header_match.groups()
        amount_cell = str(row.iloc[4] if len(row) > 4 else "").strip()
        amount_match = REF_AMOUNT_PATTERN.match(amount_cell)
        if not amount_match:
            continue

        chq_ref, debit = amount_match.groups()
        branch_match = BRANCH_NARRATIVE_PATTERN.match(narrative)
        rows.append(
            {
                "Tran. Date": tran_date,
                "Effect Date": effect_date,
                "Tran. Narrative": narrative,
                "Remitter IBAN": pd.NA,
                "Remitter Bank": pd.NA,
                "Chq / Ref No": chq_ref,
                "Debit": debit,
                "Credit": pd.NA,
                "Balance": row.iloc[5] if len(row) > 5 else pd.NA,
                "Tran. Br.": branch_match.group(1) if branch_match else pd.NA,
                "Transaction Details": branch_match.group(2) if branch_match else narrative,
            }
        )

    return pd.DataFrame(rows)


def _dedupe_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate transactions based on key fields."""
    if df.empty:
        return df
    return df.drop_duplicates(
        subset=["Tran. Date", "Chq / Ref No", "Debit", "Credit"],
        keep="first",
    ).reset_index(drop=True)


def _extract_continuation_pages(pdf_path: str) -> list[pd.DataFrame]:
    """Extract transactions from page 2+ when stream mode truncates at a page break."""
    continuation = []
    page = 2
    max_pages = 50  # Safety limit

    while page <= max_pages:
        try:
            tables = tabula.read_pdf(pdf_path, pages=str(page), **AREA_EXTRACTION)
        except Exception:
            break
        page_dfs = [_process_area_fallback_table(raw) for raw in tables]
        page_dfs = [df for df in page_dfs if not df.empty]
        if not page_dfs:
            break
        continuation.extend(page_dfs)
        page += 1
    return continuation

# ==================== Constants from test.py Pattern ====================

# Tabula merges several PDF header cells into one column name. Map by position instead.
CANONICAL_COLUMNS = [
    "Tran. Date",
    "Effect Date",
    "Tran. Narrative",  # merged: Tran. Br. + Transaction Details + Remitter Name in PDF
    "_unused_1",
    "Remitter IBAN",
    "Remitter Bank",
    "Chq / Ref No",
    "Debit",
    "Credit",
    "_unused_2",
    "Balance",
]

# Date pattern for PDF bank statements
DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")

# Pattern to extract branch and narrative from merged column
BRANCH_NARRATIVE_PATTERN = re.compile(r"^(\d{4})\s+(.+)$")

# Page 2+ continuation rows: tabula stream mode merges page 1 but truncates the tail
AREA_ROW_PATTERN = re.compile(
    r"^(\d{2}-[A-Z]{3}-\d{2})\s+(\d{2}-[A-Z]{3}-\d{2})\s+(.+)$"
)
REF_AMOUNT_PATTERN = re.compile(r"^(\d+)\s+([\d,]+\.\d{2})$")
AREA_EXTRACTION = {
    "area": [5, 0, 95, 100],
    "relative_area": True,
    "stream": True,
    "pandas_options": {"header": None},
    "multiple_tables": True,
}


# ==================== PDF Processor Class ====================

class PDFProcessor:
    """
    Process PDF bank statements to extract transaction data
    Following test.py pattern with tabula-py integration
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
        Following test.py pattern: tabula.read_pdf, column mapping, branch/narrative extraction

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

            # Extract tables from all pages using multiple_tables mode
            tables = tabula.read_pdf(str(pdf_path), pages="all", multiple_tables=True)

            if not tables:
                raise PDFProcessingError(
                    f"PDF file does not contain extractable transaction table",
                    details={"pdf_path": str(pdf_path)},
                    error_type="no_transactions"
                )

            logger.info(f"Tabula found {len(tables)} table(s)")
            for i, raw in enumerate(tables):
                if isinstance(raw, pd.DataFrame):
                    logger.info(f"  table {i + 1}: {raw.shape[0]} rows x {raw.shape[1]} cols")
                else:
                    logger.info(f"  table {i + 1}: {type(raw).__name__} (skipped)")

            # Process main tables using helper function
            processed = [_process_raw_table(raw) for raw in tables]

            # Extract continuation pages (page 2+) using area extraction fallback
            continuation_pages = _extract_continuation_pages(str(pdf_path))
            processed.extend(continuation_pages)

            # Filter out empty DataFrames
            processed = [df for df in processed if not df.empty]

            if not processed:
                raise PDFProcessingError(
                    f"No valid transaction data found in any table from PDF",
                    details={"pdf_path": str(pdf_path), "tables_found": len(tables)},
                    error_type="no_transactions"
                )

            # Combine all processed tables and deduplicate
            df = _dedupe_transactions(pd.concat(processed, ignore_index=True))
            logger.info(f"Combined {len(processed)} tables with total {len(df)} unique transactions")

            # Reset index (already done by _dedupe_transactions)
            df = df.reset_index(drop=True)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log extraction statistics
            pages_processed = len(tables)
            tables_extracted = len(tables)
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

            # Transform to standard format
            standardized_transactions = self.transform_to_standard_format(df)

            total_processing_time_ms = int((time.time() - total_start_time) * 1000)

            # Build result
            result = {
                "bank_statement": standardized_transactions,
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