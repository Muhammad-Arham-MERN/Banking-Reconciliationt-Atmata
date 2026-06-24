# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Error handling framework for file processing operations
Consistent error responses and exception management
"""
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ==================== Error Response Builders ====================

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def bad_request_error(
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create a 400 Bad Request error
    Used for invalid input parameters

    Args:
        message: Human-readable error message
        details: Additional error details

    Returns:
        HTTPException with 400 status code

    Examples:
        >>> raise bad_request_error("Invalid format type", {"provided": "invalid", "valid": ["debit-plus-credit", "debit-pipe-credit"]})
    """
    error_details = details or {}
    logger.warning(f"Bad request: {message} - {error_details}")

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "bad_request",
            "message": message,
            "details": error_details
        }
    )


def processing_error(
    message: str,
    file_type: Optional[str] = None,
    error_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create a 422 Unprocessable Entity error
    Used for file processing errors (invalid files, column mapping, etc.)

    Args:
        message: Human-readable error message
        file_type: Type of file that caused error ('pdf' or 'excel')
        error_type: Specific error category ('no_transactions', 'column_not_found', etc.)
        details: Additional error details

    Returns:
        HTTPException with 422 status code

    Examples:
        >>> raise processing_error("Column not found", "excel", "column_not_found", {"column": "Amount", "available": ["Date", "Value"]})
    """
    error_details = details or {}
    if file_type:
        error_details["file_type"] = file_type
    if error_type:
        error_details["error_type"] = error_type

    logger.error(f"Processing error ({file_type}/{error_type}): {message} - {error_details}")

    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "processing_error",
            "message": message,
            "details": error_details
        }
    )


def internal_error(
    message: str = "An unexpected error occurred during file processing",
    request_id: Optional[str] = None,
    error_details: Optional[str] = None
) -> HTTPException:
    """
    Create a 500 Internal Server Error
    Used for unexpected system errors

    Args:
        message: Human-readable error message
        request_id: Request identifier for debugging
        error_details: Technical error details (logged but not shown to user)

    Returns:
        HTTPException with 500 status code

    Examples:
        >>> raise internal_error("Database connection failed", request_id="123-456", error_details="Connection timeout")
    """
    details: Dict[str, Any] = {}
    if request_id:
        details["request_id"] = request_id
    if error_details:
        logger.error(f"Internal error (request {request_id}): {error_details}")
        # Don't expose technical details to client
        details["help"] = "Please try again or contact support with this request ID"

    logger.error(f"Internal server error: {message} - {details}")

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "internal_error",
            "message": message,
            "details": details
        }
    )


def service_unavailable(
    message: str = "Server is shutting down. Please try again later.",
    retry_after: Optional[int] = None
) -> HTTPException:
    """
    Create a 503 Service Unavailable error
    Used when server is shutting down or unavailable

    Args:
        message: Human-readable error message
        retry_after: Seconds after which client should retry

    Returns:
        HTTPException with 503 status code

    Examples:
        >>> raise service_unavailable("Server maintenance", retry_after=60)
    """
    details = {
        "shutdown_in_progress": True
    }
    if retry_after:
        details["retry_after"] = retry_after

    logger.warning(f"Service unavailable: {message}")

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "service_unavailable",
            "message": message,
            "details": details
        },
        headers={"Retry-After": str(retry_after)} if retry_after else {}
    )


# ==================== Specific Error Handlers ====================

class FileProcessingError(Exception):
    """Base exception for file processing errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PDFProcessingError(FileProcessingError):
    """Exception raised during PDF processing"""
    pass


class ExcelProcessingError(FileProcessingError):
    """Exception raised during Excel processing"""
    pass


class DataValidationError(FileProcessingError):
    """Exception raised during data validation"""
    pass


class ColumnMappingError(ExcelProcessingError):
    """Exception raised when column mapping fails"""
    pass


def handle_pdf_processing_error(error: Exception, pdf_filename: str) -> HTTPException:
    """
    Convert PDF processing error to appropriate HTTP response

    Args:
        error: Exception that occurred during PDF processing
        pdf_filename: Name of PDF file being processed

    Returns:
        HTTPException with appropriate status code
    """
    error_message = f"Error processing PDF file: {pdf_filename}"

    if isinstance(error, PDFProcessingError):
        return processing_error(
            message=error.message,
            file_type="pdf",
            error_type="pdf_processing_failed",
            details={
                "filename": pdf_filename,
                **error.details
            }
        )
    else:
        logger.error(f"Unexpected PDF processing error: {str(error)}")
        return internal_error(
            message=error_message,
            error_details=str(error)
        )


def handle_excel_processing_error(error: Exception, excel_filename: str) -> HTTPException:
    """
    Convert Excel processing error to appropriate HTTP response

    Args:
        error: Exception that occurred during Excel processing
        excel_filename: Name of Excel file being processed

    Returns:
        HTTPException with appropriate status code
    """
    error_message = f"Error processing Excel file: {excel_filename}"

    if isinstance(error, ColumnMappingError):
        return processing_error(
            message=error.message,
            file_type="excel",
            error_type="column_not_found",
            details={
                "filename": excel_filename,
                **error.details
            }
        )
    elif isinstance(error, ExcelProcessingError):
        return processing_error(
            message=error.message,
            file_type="excel",
            error_type="excel_processing_failed",
            details={
                "filename": excel_filename,
                **error.details
            }
        )
    else:
        logger.error(f"Unexpected Excel processing error: {str(error)}")
        return internal_error(
            message=error_message,
            error_details=str(error)
        )


def handle_validation_error(error: Exception, field_name: Optional[str] = None) -> HTTPException:
    """
    Convert data validation error to appropriate HTTP response

    Args:
        error: Exception that occurred during validation
        field_name: Name of field that failed validation

    Returns:
        HTTPException with appropriate status code
    """
    if isinstance(error, DataValidationError):
        details = error.details.copy()
        if field_name:
            details["field"] = field_name

        return processing_error(
            message=error.message,
            error_type="validation_failed",
            details=details
        )
    else:
        logger.error(f"Unexpected validation error: {str(error)}")
        return internal_error(
            message="Data validation failed",
            error_details=str(error)
        )


def create_partial_success_response(
    successful_data: Dict[str, Any],
    failure_info: Dict[str, str],
    request_id: str
) -> Dict[str, Any]:
    """
    Create partial success response when one file processes but other fails
    Returns successful data with error information

    Args:
        successful_data: Successfully processed data
        failure_info: Information about failed processing
        request_id: Request identifier

    Returns:
        Partial success response dictionary

    Examples:
        >>> create_partial_success_response(
        ...     {"bank_statement": [...]},
        ...     {"file": "company_records.xlsx", "error": "Column not found"},
        ...     "123-456"
        ... )
    """
    return {
        "request_id": request_id,
        "processing_status": "partial_success",
        "processing_timestamp": datetime.now().isoformat(),
        "summary": {
            **successful_data.get("summary", {}),
            "partial_success": True,
            "failed_file": failure_info.get("file", "unknown"),
            "failure_reason": failure_info.get("error", "unknown")
        },
        "results": successful_data,
        "errors": [f"{failure_info.get('file', 'Unknown file')}: {failure_info.get('error', 'Unknown error')}"]
    }


def build_error_help_text(error_type: str, details: Dict[str, Any]) -> str:
    """
    Build helpful error message text based on error type
    Provides actionable guidance for users

    Args:
        error_type: Type of error that occurred
        details: Error details for context

    Returns:
        Helpful error message text

    Examples:
        >>> build_error_help_text("column_not_found", {"column": "Amount", "available": ["Date", "Value"]})
        "Check column name spelling and ensure it exists in the Excel file"
    """
    help_texts = {
        "no_transactions": "Ensure PDF is a valid bank statement with transaction data in tabular format",
        "column_not_found": "Check column name spelling and ensure it exists in the Excel file",
        "invalid_date_format": "Ensure date values follow expected format for this file type",
        "invalid_amount": "Ensure amount values are numeric and non-zero",
        "ambiguous_transaction": "Transaction has both debit and credit values - check data entry",
        "empty_file": "File appears to be empty or corrupted",
        "file_too_large": "File size exceeds maximum allowed size",
        "invalid_file_type": "File format not recognized or corrupted"
    }

    base_help = help_texts.get(error_type, "Please check your file and try again")

    # Add specific guidance based on details
    if error_type == "column_not_found" and "available_columns" in details:
        base_help += f". Available columns: {', '.join(details['available_columns'])}"

    if error_type == "invalid_date_format" and "expected_format" in details:
        base_help += f". Expected format: {details['expected_format']}"

    return base_help


def enhance_error_response(error_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance error response with helpful information
    Adds help text and additional context

    Args:
        error_response: Base error response dictionary

    Returns:
        Enhanced error response with help text
    """
    if "details" in error_response and "error_type" in error_response["details"]:
        error_type = error_response["details"]["error_type"]
        details = error_response["details"]
        error_response["details"]["help"] = build_error_help_text(error_type, details)

    return error_response


def log_error_with_context(error: Exception, context: Dict[str, Any]) -> None:
    """
    Log error with additional context information
    Helps with debugging and error tracking

    Args:
        error: Exception that occurred
        context: Additional context information (request_id, file_name, etc.)
    """
    context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
    logger.error(f"Error occurred [{context_str}]: {str(error)}", exc_info=error)


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ