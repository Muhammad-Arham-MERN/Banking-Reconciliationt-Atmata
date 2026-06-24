# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Logging infrastructure for file processing operations
Structured logging with processing metrics and error tracking
"""
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

# ==================== Logging Configuration ====================

class ProcessingFormatter(logging.Formatter):
    """
    Custom formatter for processing logs
    Adds structured fields for better log analysis
    """
    def format(self, record: logging.LogRecord) -> str:
        # Add timestamp if not present
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.now().isoformat()

        # Add process info
        if hasattr(record, 'request_id'):
            base_msg = f"[{record.request_id}] {record.getMessage()}"
        else:
            base_msg = record.getMessage()

        # Format with timestamp, level, and message
        return f"{record.timestamp} | {record.levelname:8} | {base_msg}"


def setup_processing_logger(
    name: str = "processing",
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup and configure a processing logger
    Creates logger with file and console handlers

    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance

    Examples:
        >>> logger = setup_processing_logger("pdf_processor", "logs/pdf_processing.log")
        >>> logger.info("Processing started", extra={"request_id": "123-456"})
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Clear existing handlers
    logger.propagate = False  # Don't propagate to root logger

    # Create formatter
    formatter = ProcessingFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# ==================== Structured Logging Functions ====================

def log_processing_start(
    logger: logging.Logger,
    request_id: str,
    pdf_filename: Optional[str] = None,
    excel_filename: Optional[str] = None
) -> None:
    """
    Log processing start with file information

    Args:
        logger: Logger instance
        request_id: Request identifier
        pdf_filename: Optional PDF filename
        excel_filename: Optional Excel filename
    """
    files = []
    if pdf_filename:
        files.append(f"PDF: {pdf_filename}")
    if excel_filename:
        files.append(f"Excel: {excel_filename}")

    logger.info(
        f"Processing started - {', '.join(files)}",
        extra={"request_id": request_id}
    )


def log_processing_complete(
    logger: logging.Logger,
    request_id: str,
    pdf_time_ms: Optional[int] = None,
    excel_time_ms: Optional[int] = None,
    total_time_ms: int = 0,
    bank_count: int = 0,
    company_count: int = 0
) -> None:
    """
    Log processing completion with performance metrics

    Args:
        logger: Logger instance
        request_id: Request identifier
        pdf_time_ms: PDF processing time (milliseconds)
        excel_time_ms: Excel processing time (milliseconds)
        total_time_ms: Total processing time (milliseconds)
        bank_count: Number of bank transactions extracted
        company_count: Number of company transactions extracted
    """
    timing_parts = []
    if pdf_time_ms is not None:
        timing_parts.append(f"PDF: {pdf_time_ms}ms")
    if excel_time_ms is not None:
        timing_parts.append(f"Excel: {excel_time_ms}ms")
    timing_parts.append(f"Total: {total_time_ms}ms")

    logger.info(
        f"Processing completed - {', '.join(timing_parts)}, "
        f"Bank: {bank_count} transactions, Company: {company_count} transactions",
        extra={"request_id": request_id}
    )


def log_pdf_extraction(
    logger: logging.Logger,
    request_id: str,
    pdf_filename: str,
    pages_processed: int,
    tables_extracted: int,
    rows_extracted: int,
    processing_time_ms: int
) -> None:
    """
    Log PDF extraction statistics

    Args:
        logger: Logger instance
        request_id: Request identifier
        pdf_filename: PDF filename
        pages_processed: Number of pages processed
        tables_extracted: Number of tables extracted
        rows_extracted: Number of rows extracted
        processing_time_ms: Processing time (milliseconds)
    """
    logger.info(
        f"PDF extraction complete - {pdf_filename}: "
        f"{pages_processed} pages, {tables_extracted} tables, {rows_extracted} rows, {processing_time_ms}ms",
        extra={"request_id": request_id}
    )


def log_excel_extraction(
    logger: logging.Logger,
    request_id: str,
    excel_filename: str,
    sheets_processed: int,
    rows_extracted: int,
    columns_mapped: Dict[str, str],
    processing_time_ms: int
) -> None:
    """
    Log Excel extraction statistics

    Args:
        logger: Logger instance
        request_id: Request identifier
        excel_filename: Excel filename
        sheets_processed: Number of sheets processed
        rows_extracted: Number of rows extracted
        columns_mapped: Column name mappings
        processing_time_ms: Processing time (milliseconds)
    """
    column_info = ", ".join([f"{k}→{v}" for k, v in columns_mapped.items()])

    logger.info(
        f"Excel extraction complete - {excel_filename}: "
        f"{sheets_processed} sheets, {rows_extracted} rows, "
        f"columns: [{column_info}], {processing_time_ms}ms",
        extra={"request_id": request_id}
    )


def log_transformation_stats(
    logger: logging.Logger,
    request_id: str,
    source_type: str,
    total_input: int,
    successfully_transformed: int,
    transformation_errors: int
) -> None:
    """
    Log data transformation statistics

    Args:
        logger: Logger instance
        request_id: Request identifier
        source_type: Data source type ('pdf' or 'excel')
        total_input: Total input records
        successfully_transformed: Number successfully transformed
        transformation_errors: Number of transformation errors
    """
    logger.info(
        f"{source_type.upper()} transformation: {successfully_transformed}/{total_input} successful, "
        f"{transformation_errors} errors",
        extra={"request_id": request_id}
    )


def log_error_details(
    logger: logging.Logger,
    request_id: str,
    error_type: str,
    error_message: str,
    error_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log detailed error information with context

    Args:
        logger: Logger instance
        request_id: Request identifier
        error_type: Type of error that occurred
        error_message: Error message
        error_context: Additional error context
    """
    context_str = ""
    if error_context:
        context_str = f" | Context: {json.dumps(error_context)}"

    logger.error(
        f"{error_type}: {error_message}{context_str}",
        extra={"request_id": request_id}
    )


def log_performance_warning(
    logger: logging.Logger,
    request_id: str,
    operation: str,
    duration_ms: int,
    threshold_ms: int
) -> None:
    """
    Log performance warning when operations exceed thresholds

    Args:
        logger: Logger instance
        request_id: Request identifier
        operation: Operation name
        duration_ms: Actual duration
        threshold_ms: Threshold duration
    """
    logger.warning(
        f"Performance warning - {operation} took {duration_ms}ms (threshold: {threshold_ms}ms)",
        extra={"request_id": request_id}
    )


def log_file_validation(
    logger: logging.Logger,
    request_id: str,
    filename: str,
    file_type: str,
    validation_passed: bool,
    validation_details: Optional[str] = None
) -> None:
    """
    Log file validation results

    Args:
        logger: Logger instance
        request_id: Request identifier
        filename: File name
        file_type: Type of file ('pdf' or 'excel')
        validation_passed: Whether validation passed
        validation_details: Additional validation details
    """
    status = "PASSED" if validation_passed else "FAILED"
    detail_str = f" - {validation_details}" if validation_details else ""

    logger.info(
        f"File validation {status} - {filename} ({file_type}){detail_str}",
        extra={"request_id": request_id}
    )


def log_cleanup_operation(
    logger: logging.Logger,
    request_id: str,
    files_deleted: int,
    cleanup_time_ms: int
) -> None:
    """
    Log file cleanup operation results

    Args:
        logger: Logger instance
        request_id: Request identifier
        files_deleted: Number of files deleted
        cleanup_time_ms: Cleanup duration
    """
    logger.info(
        f"Cleanup complete - {files_deleted} files deleted, {cleanup_time_ms}ms",
        extra={"request_id": request_id}
    )


# ==================== Logger Instances ====================

# Create default processing loggers
pdf_logger = setup_processing_logger("pdf_processor")
excel_logger = setup_processing_logger("excel_processor")
api_logger = setup_processing_logger("api_processing")


def get_logger(logger_name: str = "processing") -> logging.Logger:
    """
    Get or create a processing logger

    Args:
        logger_name: Name of logger to retrieve

    Returns:
        Logger instance
    """
    if logger_name == "pdf_processor":
        return pdf_logger
    elif logger_name == "excel_processor":
        return excel_logger
    elif logger_name == "api_processing":
        return api_logger
    else:
        return setup_processing_logger(logger_name)


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ