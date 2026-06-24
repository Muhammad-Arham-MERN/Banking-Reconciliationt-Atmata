# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
API response models and error schemas
Consistent data structures for frontend/backend communication
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from decimal import Decimal

# ==================== Health Check Models ====================

class HealthResponse(BaseModel):
    """Health check endpoint response model"""
    status: Literal["healthy", "unhealthy"] = Field(description="Service health status")
    service: str = Field(description="Service name identifier")
    version: str = Field(description="API version")
    timestamp: str = Field(description="Current server timestamp (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "Backend Reconciliation API",
                "version": "1.0.0",
                "timestamp": "2025-06-19T10:30:00Z"
            }
        }

# ==================== Error Response Models ====================

class ErrorResponse(BaseModel):
    """
    Standard error response format
    Consistency Pattern: Must match frontend error expectations
    """
    error: str = Field(description="Error code identifier")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "error": "bad_request",
                    "message": "Invalid request data",
                    "details": {"field": "format_type", "issue": "Invalid format type"}
                },
                {
                    "error": "file_too_large",
                    "message": "File size exceeds maximum allowed size",
                    "details": {"field": "bankStatement", "max_size_mb": 50, "actual_size_mb": 55}
                }
            ]
        }

# ==================== Reconciliation Processing Models ====================

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class ProcessingStatus:
    """
    Processing status enumeration
    Consistency Pattern: Must match frontend ProcessingStatus enum exactly
    """
    RECEIVED = "received"
    VALIDATING = "validating"
    VALIDATED = "validated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    CLEANING_UP = "cleaning_up"
    REMOVED = "removed"

class TransactionType:
    """
    Transaction type enumeration
    Consistency Pattern: Must match frontend TransactionType enum exactly
    """
    CREDIT = "credit"  # Money coming into the account (positive amount)
    DEBIT = "debit"    # Money going out of the account (negative amount)

class TransactionDetails(BaseModel):
    """
    Common transaction details structure
    Consistency Pattern: Must include amount, debit_amount, and credit_amount fields
    """
    transaction_id: str = Field(description="Unique identifier for the transaction")
    date: str = Field(description="Transaction date (YYYY-MM-DD format)")
    description: str = Field(description="Transaction description/details")
    amount: Decimal = Field(description="Net transaction amount")
    debit_amount: Optional[Decimal] = Field(default=None, description="Debit amount (if applicable)")
    credit_amount: Optional[Decimal] = Field(default=None, description="Credit amount (if applicable)")
    type: Literal["credit", "debit"] = Field(description="Transaction type")

class TransactionMatch(BaseModel):
    """
    Matched transaction between bank and company records
    Consistency Pattern: Must include debit/credit values in both transactions
    """
    transaction_id: str = Field(description="Unique identifier for this match")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for the match")
    bank_transaction: TransactionDetails = Field(description="Bank transaction details with debit/credit amounts")
    company_transaction: TransactionDetails = Field(description="Company transaction details with debit/credit amounts")

class TransactionDiscrepancy(BaseModel):
    """
    Unmatched or discrepant transaction
    Consistency Pattern: Must include debit/credit values, NO possible_matches field
    """
    discrepancy_id: str = Field(description="Unique identifier for this discrepancy")
    source: Literal["bank", "company"] = Field(description="Which file the discrepancy is from")
    discrepancy_type: Literal["unmatched", "amount_mismatch", "date_mismatch", "duplicate"] = Field(description="Type of discrepancy")
    transaction: TransactionDetails = Field(description="The unmatched transaction with debit/credit amounts")

class ProcessingSummary(BaseModel):
    """Processing summary statistics"""
    total_bank_transactions: int = Field(description="Total transactions extracted from bank statement")
    total_company_transactions: int = Field(description="Total transactions extracted from company data")
    matched_transactions: int = Field(description="Number of successfully matched transactions")
    discrepancies: int = Field(description="Number of unmatched/discrepant transactions")
    processing_duration_ms: int = Field(description="Processing time in milliseconds")

class ReconciliationResult(BaseModel):
    """
    Complete reconciliation result response
    Consistency Pattern: Must match frontend expectations for response format
    """
    request_id: str = Field(description="Unique identifier for the processing request")
    processing_status: str = Field(description="Overall processing status (from ProcessingStatus enum)")
    processing_timestamp: str = Field(description="When processing was completed (ISO 8601)")
    summary: ProcessingSummary = Field(description="High-level summary of results")
    results: List[Dict[str, Any]] = Field(description="List of reconciliation results (matches and discrepancies)")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "processing_status": "completed",
                "processing_timestamp": "2025-06-19T10:35:00Z",
                "summary": {
                    "total_bank_transactions": 45,
                    "total_company_transactions": 42,
                    "matched_transactions": 38,
                    "discrepancies": 7,
                    "processing_duration_ms": 4500
                },
                "results": [
                    {
                        "type": "match",
                        "match_id": "match_001",
                        "confidence": 0.95,
                        "bank_transaction": {
                            "transaction_id": "bank_001",
                            "date": "2025-06-15",
                            "description": "ACH ELECTRONIC CREDIT",
                            "amount": "1500.00",
                            "debit_amount": None,
                            "credit_amount": "1500.00",
                            "type": "credit"
                        },
                        "company_transaction": {
                            "transaction_id": "company_001",
                            "date": "2025-06-15",
                            "description": "Client Payment - ABC Corp",
                            "amount": "1500.00",
                            "debit_amount": None,
                            "credit_amount": "1500.00",
                            "type": "credit"
                        }
                    },
                    {
                        "type": "discrepancy",
                        "discrepancy_id": "disc_001",
                        "source": "bank",
                        "discrepancy_type": "unmatched",
                        "transaction": {
                            "transaction_id": "bank_045",
                            "date": "2025-06-16",
                            "description": "UNKNOWN DEBIT",
                            "amount": "-250.00",
                            "debit_amount": "250.00",
                            "credit_amount": None,
                            "type": "debit"
                        }
                    }
                ]
            }
        }

# ==================== Validation Response Models ====================

class ValidationResult(BaseModel):
    """File validation result"""
    is_valid: bool = Field(description="Whether the file passed validation")
    validation_errors: Optional[List[str]] = Field(default=None, description="List of validation error messages")
    warnings: Optional[List[str]] = Field(default=None, description="List of warning messages")

class FileUploadResponse(BaseModel):
    """File upload response"""
    file_id: str = Field(description="Unique identifier for the uploaded file")
    original_filename: str = Field(description="Original filename from the upload")
    file_size: int = Field(description="File size in bytes")
    validation: ValidationResult = Field(description="Validation result")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when file was uploaded")

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ