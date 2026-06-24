# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Response formatting utilities for consistent API responses
Standard response builders, error handlers, and formatters
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.models.api_models import ErrorResponse, ProcessingStatus, ProcessingSummary

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def build_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """
    Build a standard success response
    Consistency Pattern: Consistent success response format

    Args:
        data: Response data
        message: Success message

    Returns:
        Formatted success response
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

def build_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Build a standard error response
    Consistency Pattern: Must match frontend error expectations

    Args:
        error_code: Error code identifier
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code

    Returns:
        Formatted error response
    """
    error_response = ErrorResponse(
        error=error_code,
        message=message,
        details=details
    )

    return JSONResponse(
        content=error_response.model_dump(),
        status_code=status_code
    )

def build_health_response(
    status: str = "healthy",
    service: str = "Backend Reconciliation API",
    version: str = "1.0.0"
) -> Dict[str, Any]:
    """
    Build health check response
    Consistency Pattern: Must match frontend health endpoint expectations

    Args:
        status: Service health status
        service: Service name
        version: API version

    Returns:
        Formatted health check response
    """
    return {
        "status": status,
        "service": service,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

def build_validation_error_response(validation_errors: Dict[str, str]) -> JSONResponse:
    """
    Build validation error response
    Consistency Pattern: Consistent validation error format

    Args:
        validation_errors: Dictionary of field names to error messages

    Returns:
        Formatted validation error response
    """
    return build_error_response(
        error_code="validation_error",
        message="Request validation failed",
        details={"validation_errors": validation_errors},
        status_code=422
    )

def build_file_validation_response(
    field_name: str,
    error_message: str,
    max_size_mb: Optional[float] = None,
    actual_size_mb: Optional[float] = None
) -> JSONResponse:
    """
    Build file validation error response
    Consistency Pattern: Must match frontend file validation expectations

    Args:
        field_name: Name of the field that failed validation
        error_message: Error message
        max_size_mb: Maximum allowed file size in MB
        actual_size_mb: Actual file size in MB

    Returns:
        Formatted file validation error response
    """
    details = {"field": field_name}

    if max_size_mb is not None:
        details["max_size_mb"] = max_size_mb

    if actual_size_mb is not None:
        details["actual_size_mb"] = actual_size_mb

    return build_error_response(
        error_code="invalid_file",
        message=error_message,
        details=details,
        status_code=422
    )

def build_file_size_error_response(
    field_name: str,
    max_size_mb: float,
    actual_size_mb: float
) -> JSONResponse:
    """
    Build file size error response
    Consistency Pattern: Must match frontend file size error expectations

    Args:
        field_name: Name of the field that exceeded size limit
        max_size_mb: Maximum allowed file size in MB
        actual_size_mb: Actual file size in MB

    Returns:
        Formatted file size error response
    """
    return build_error_response(
        error_code="file_too_large",
        message=f"File size exceeds maximum allowed size",
        details={
            "field": field_name,
            "max_size_mb": max_size_mb,
            "actual_size_mb": actual_size_mb
        },
        status_code=413
    )

def build_processing_error_response(
    error_type: str,
    error_message: str
) -> JSONResponse:
    """
    Build processing error response
    Consistency Pattern: Consistent processing error format

    Args:
        error_type: Type of processing error
        error_message: Error message

    Returns:
        Formatted processing error response
    """
    return build_error_response(
        error_code="processing_error",
        message="Error processing files",
        details={
            "error_type": error_type,
            "error_message": error_message
        },
        status_code=500
    )

def build_timeout_response(
    max_duration_seconds: int,
    actual_duration_seconds: float
) -> JSONResponse:
    """
    Build timeout error response
    Consistency Pattern: Consistent timeout error format

    Args:
        max_duration_seconds: Maximum allowed processing time
        actual_duration_seconds: Actual processing time

    Returns:
        Formatted timeout error response
    """
    return build_error_response(
        error_code="timeout",
        message="Processing exceeded maximum time limit",
        details={
            "max_duration_seconds": max_duration_seconds,
            "actual_duration_seconds": actual_duration_seconds
        },
        status_code=504
    )

def build_reconciliation_response(
    request_id: str,
    processing_status: str,
    summary: ProcessingSummary,
    results: List[Dict[str, Any]],
    processing_duration_ms: int
) -> Dict[str, Any]:
    """
    Build reconciliation processing response
    Consistency Pattern: Must match frontend reconciliation response expectations

    Args:
        request_id: Unique request identifier
        processing_status: Processing status (from ProcessingStatus enum)
        summary: Processing summary statistics
        results: List of reconciliation results (matches and discrepancies)
        processing_duration_ms: Processing time in milliseconds

    Returns:
        Formatted reconciliation response
    """
    return {
        "request_id": request_id,
        "processing_status": processing_status,
        "processing_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": summary.model_dump(),
        "results": results
    }

def format_transaction_match(
    match_id: str,
    confidence: float,
    bank_transaction: Dict[str, Any],
    company_transaction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format a transaction match result
    Consistency Pattern: Consistent match format with debit/credit amounts

    Args:
        match_id: Unique match identifier
        confidence: Match confidence score (0.0-1.0)
        bank_transaction: Bank transaction details
        company_transaction: Company transaction details

    Returns:
        Formatted transaction match
    """
    return {
        "type": "match",
        "match_id": match_id,
        "confidence": confidence,
        "bank_transaction": bank_transaction,
        "company_transaction": company_transaction
    }

def format_transaction_discrepancy(
    discrepancy_id: str,
    source: str,
    discrepancy_type: str,
    transaction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format a transaction discrepancy result
    Consistency Pattern: Consistent discrepancy format without possible_matches

    Args:
        discrepancy_id: Unique discrepancy identifier
        source: Which file the discrepancy is from ("bank" or "company")
        discrepancy_type: Type of discrepancy
        transaction: Transaction details with debit/credit amounts

    Returns:
        Formatted transaction discrepancy
    """
    return {
        "type": "discrepancy",
        "discrepancy_id": discrepancy_id,
        "source": source,
        "discrepancy_type": discrepancy_type,
        "transaction": transaction
    }

def handle_generic_exception(exception: Exception) -> JSONResponse:
    """
    Handle generic exceptions
    Consistency Pattern: Consistent error handling

    Args:
        exception: The exception to handle

    Returns:
        Formatted error response
    """
    return build_processing_error_response(
        error_type=type(exception).__name__,
        error_message=str(exception)
    )

def create_http_exception(
    status_code: int,
    detail: str,
    error_code: Optional[str] = None
) -> HTTPException:
    """
    Create HTTP exception with consistent format
    Consistency Pattern: Consistent HTTP exception format

    Args:
        status_code: HTTP status code
        detail: Error message
        error_code: Optional error code

    Returns:
        HTTPException instance
    """
    if error_code:
        return HTTPException(
            status_code=status_code,
            detail={
                "error": error_code,
                "message": detail
            }
        )
    else:
        return HTTPException(
            status_code=status_code,
            detail=detail
        )

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ