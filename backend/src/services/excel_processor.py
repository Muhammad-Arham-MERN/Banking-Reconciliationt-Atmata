# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Excel Processing Service
Extract transaction data from Excel company records using pandas
Supports 3-column and 4-column formats with user-provided column mappings
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from src.utils.data_transformers import (
    normalize_excel_date, merge_debit_credit, convert_combined_amount,
    standardize_transaction_data, clean_transaction_detail
)
from src.utils.logger import (
    log_excel_extraction, log_transformation_stats,
    log_error_details, log_performance_warning
)
from src.utils.error_handlers import ExcelProcessingError, ColumnMappingError

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# ==================== Excel Processor Class ====================

class ExcelProcessor:
    """
    Process Excel company records to extract transaction data
    Supports both 3-column and 4-column formats with flexible column mapping
    """

    def __init__(self, request_id: str = "unknown"):
        """
        Initialize Excel processor

        Args:
            request_id: Request identifier for logging
        """
        self.request_id = request_id
        self.processing_logger = logging.getLogger(__name__)

    def extract_company_records(
        self,
        excel_path: Path,
        transaction_date_column: str,
        transaction_details_column: str,
        format_type: str,
        sheet_name: str = "Sheet1",
        debit_plus_credit_column: Optional[str] = None,
        debit_column: Optional[str] = None,
        credit_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract transaction data from Excel company records
        Supports 3-column (combined amount) and 4-column (separate debit/credit) formats

        Args:
            excel_path: Path to Excel file
            transaction_date_column: Name of date column
            transaction_details_column: Name of transaction details column
            format_type: 'debit-plus-credit' (3-col) or 'debit-pipe-credit' (4-col)
            sheet_name: Name of Excel sheet to read (default: "Sheet1")
            debit_plus_credit_column: Combined amount column name (3-col format)
            debit_column: Debit column name (4-col format)
            credit_column: Credit column name (4-col format)

        Returns:
            DataFrame with extracted transaction data

        Raises:
            ExcelProcessingError: If Excel processing fails
            ColumnMappingError: If column mapping fails
        """
        import time
        start_time = time.time()

        try:
            # Validate Excel path exists
            if not excel_path.exists():
                raise ExcelProcessingError(
                    f"Excel file not found: {excel_path}",
                    details={"file_path": str(excel_path)}
                )

            # Read Excel file with specified sheet
            logger.info(f"Reading Excel sheet: {sheet_name}")
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            if df.empty:
                raise ExcelProcessingError(
                    "Excel file is empty or contains no data",
                    details={"excel_path": str(excel_path)},
                    error_type="no_transactions"
                )

            # Validate column names exist
            available_columns = df.columns.tolist()

            # Check required columns
            missing_columns = []
            if transaction_date_column not in available_columns:
                missing_columns.append(transaction_date_column)
            if transaction_details_column not in available_columns:
                missing_columns.append(transaction_details_column)

            # Check format-specific columns
            if format_type == 'debit-plus-credit':
                if not debit_plus_credit_column or debit_plus_credit_column not in available_columns:
                    if debit_plus_credit_column:
                        missing_columns.append(debit_plus_credit_column)
                    else:
                        missing_columns.append("debit_plus_credit_column (required for 3-column format)")
            elif format_type == 'debit-pipe-credit':
                if not debit_column or debit_column not in available_columns:
                    if debit_column:
                        missing_columns.append(debit_column)
                    else:
                        missing_columns.append("debit_column (required for 4-column format)")
                if not credit_column or credit_column not in available_columns:
                    if credit_column:
                        missing_columns.append(credit_column)
                    else:
                        missing_columns.append("credit_column (required for 4-column format)")

            if missing_columns:
                raise ColumnMappingError(
                    f"Required columns not found in Excel file: {', '.join(missing_columns)}",
                    details={
                        "missing_columns": missing_columns,
                        "available_columns": available_columns
                    }
                )

            # Extract only needed columns
            columns_to_extract = [transaction_date_column, transaction_details_column]

            if format_type == 'debit-plus-credit' and debit_plus_credit_column:
                columns_to_extract.append(debit_plus_credit_column)
            elif format_type == 'debit-pipe-credit' and debit_column and credit_column:
                columns_to_extract.extend([debit_column, credit_column])

            try:
                df_extracted = df[columns_to_extract].copy()
            except KeyError as e:
                raise ColumnMappingError(
                    f"Error extracting columns: {str(e)}",
                    details={"requested_columns": columns_to_extract, "available": available_columns}
                )

            # Rename columns to standard names for processing
            column_mapping = {
                transaction_date_column: 'transaction_date',
                transaction_details_column: 'transaction_detail'
            }

            if format_type == 'debit-plus-credit' and debit_plus_credit_column:
                column_mapping[debit_plus_credit_column] = 'combined_amount'
            elif format_type == 'debit-pipe-credit':
                if debit_column:
                    column_mapping[debit_column] = 'debit_amount'
                if credit_column:
                    column_mapping[credit_column] = 'credit_amount'

            df_extracted = df_extracted.rename(columns=column_mapping)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log extraction statistics
            log_excel_extraction(
                logger,
                self.request_id,
                str(excel_path),
                sheets_processed=1,  # Assuming single sheet for now
                rows_extracted=len(df_extracted),
                columns_mapped=column_mapping,
                processing_time_ms=processing_time_ms
            )

            # Performance warning if processing took too long
            if processing_time_ms > 10000:  # 10 seconds threshold
                log_performance_warning(
                    logger,
                    self.request_id,
                    "Excel extraction",
                    processing_time_ms,
                    10000
                )

            return df_extracted

        except (ColumnMappingError, ExcelProcessingError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error extracting Excel data: {str(e)}"
            logger.error(error_msg)
            raise ExcelProcessingError(
                error_msg,
                details={"excel_path": str(excel_path), "error": str(e)}
            )

    def transform_to_standard_format(
        self,
        df: pd.DataFrame,
        format_type: str
    ) -> List[Dict[str, Any]]:
        """
        Transform extracted Excel data to standardized transaction format
        Handle both 3-column and 4-column formats

        Args:
            df: DataFrame from extract_company_records()
            format_type: 'debit-plus-credit' (3-col) or 'debit-pipe-credit' (4-col)

        Returns:
            List of standardized transaction dictionaries

        Raises:
            ExcelProcessingError: If transformation fails
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
                    date_value = row.get('transaction_date')
                    detail_value = row.get('transaction_detail')

                    # Debug logging to trace data types and values
                    logger.info(f"ROW {idx}: date_value={date_value} (type: {type(date_value).__name__}), detail_value={detail_value}")

                    # Clean transaction detail
                    cleaned_detail = clean_transaction_detail(str(detail_value))

                    # Create standardized transaction based on format type
                    if format_type == 'debit-plus-credit':
                        # 3-column format: combined amount
                        amount_value = row.get('combined_amount')
                        transaction = standardize_transaction_data(
                            date_value=date_value,
                            detail_value=cleaned_detail,
                            amount_value=amount_value,
                            debit_value=None,
                            credit_value=None,
                            source_type='excel'
                        )
                    else:  # debit-pipe-credit
                        # 4-column format: separate debit/credit
                        debit_value = row.get('debit_amount')
                        credit_value = row.get('credit_amount')
                        transaction = standardize_transaction_data(
                            date_value=date_value,
                            detail_value=cleaned_detail,
                            amount_value=None,
                            debit_value=debit_value,
                            credit_value=credit_value,
                            source_type='excel'
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

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log transformation statistics
            log_transformation_stats(
                logger,
                self.request_id,
                'excel',
                len(df),
                len(standardized_transactions),
                transformation_errors
            )

            return standardized_transactions

        except Exception as e:
            error_msg = f"Unexpected error transforming Excel data: {str(e)}"
            logger.error(error_msg)
            raise ExcelProcessingError(
                error_msg,
                details={"error": str(e)}
            )

    def _normalize_date(self, date_value: Any) -> Optional[str]:
        """
        Normalize Excel date to ISO format (YYYY-MM-DD)
        Handles Excel serial dates and various string formats
        Wrapper for data_transformers.normalize_excel_date

        Args:
            date_value: Excel date value (serial number or string)

        Returns:
            ISO formatted date string or None if invalid
        """
        return normalize_excel_date(date_value)

    def process_excel(
        self,
        excel_path: Path,
        transaction_date_column: str,
        transaction_details_column: str,
        format_type: str,
        sheet_name: str = "Sheet1",
        debit_plus_credit_column: Optional[str] = None,
        debit_column: Optional[str] = None,
        credit_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete Excel processing pipeline: extract and transform
        Main entry point for Excel processing

        Args:
            excel_path: Path to Excel file
            transaction_date_column: Name of date column
            transaction_details_column: Name of transaction details column
            format_type: 'debit-plus-credit' (3-col) or 'debit-pipe-credit' (4-col)
            sheet_name: Name of Excel sheet to read (default: "Sheet1")
            debit_plus_credit_column: Combined amount column name (3-col format)
            debit_column: Debit column name (4-col format)
            credit_column: Credit column name (4-col format)

        Returns:
            Dictionary with processed data and metadata

        Raises:
            ExcelProcessingError: If processing fails
            ColumnMappingError: If column mapping fails
        """
        import time
        total_start_time = time.time()

        print(f"[EXCEL DEBUG] Starting Excel processing for {excel_path.name}")

        try:
            # Extract raw data
            df = self.extract_company_records(
                excel_path,
                transaction_date_column,
                transaction_details_column,
                format_type,
                sheet_name,
                debit_plus_credit_column,
                debit_column,
                credit_column
            )

            # Transform to standard format
            print(f"[EXCEL DEBUG] DataFrame has {len(df)} rows, columns: {df.columns.tolist()}")
            print(f"[EXCEL DEBUG] First 3 rows:\n{df.head(3)}")

            standardized_transactions = self.transform_to_standard_format(df, format_type)

            print(f"[EXCEL DEBUG] Got {len(standardized_transactions)} standardized transactions")

            total_processing_time_ms = int((time.time() - total_start_time) * 1000)

            # Build result
            result = {
                "company_records": standardized_transactions,
                "processing_metadata": {
                    "excel_filename": excel_path.name,
                    "processing_time_ms": total_processing_time_ms,
                    "transaction_count": len(standardized_transactions)
                }
            }

            logger.info(
                f"Excel processing complete: {len(standardized_transactions)} transactions "
                f"extracted in {total_processing_time_ms}ms"
            )

            return result

        except (ColumnMappingError, ExcelProcessingError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error in Excel processing pipeline: {str(e)}"
            logger.error(error_msg)
            raise ExcelProcessingError(
                error_msg,
                details={"excel_path": str(excel_path), "error": str(e)}
            )


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ