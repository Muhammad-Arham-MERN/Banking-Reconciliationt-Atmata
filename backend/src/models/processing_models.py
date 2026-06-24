# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Processing models for PDF and Excel file processing
Standardized transaction data structures for bank reconciliation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4


# ==================== Core Transaction Models ====================

class ProcessedTransaction(BaseModel):
    """
    Standardized transaction record from either PDF bank statements or Excel company records
    Primary output entity for downstream reconciliation logic

    Consistency Pattern: Must follow exact field naming (Transaction_date, Transaction Detail, Debit/Credit)
    """
    Transaction_date: str = Field(description="Transaction date in ISO format (YYYY-MM-DD)")
    Transaction_Detail: str = Field(description="Transaction description or narrative")
    Debit_Credit: int = Field(description="Monetary amount (positive=debit, negative=credit)")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "Transaction_date": "2023-01-15",
                    "Transaction_Detail": "Payment from ABC Corporation",
                    "Debit_Credit": 5000
                },
                {
                    "Transaction_date": "2023-01-16",
                    "Transaction_Detail": "Utility bill payment",
                    "Debit_Credit": -250
                }
            ]
        }


# ==================== Processing Metadata Models ====================

class ProcessingMetadata(BaseModel):
    """
    Metadata about the file processing operation
    Includes timing statistics, transaction counts, and file information
    """
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for processing request")
    pdf_processing_time_ms: Optional[int] = Field(default=None, description="Time taken to process PDF (milliseconds)")
    excel_processing_time_ms: Optional[int] = Field(default=None, description="Time taken to process Excel (milliseconds)")
    total_processing_time_ms: int = Field(description="Total processing time (milliseconds)")
    bank_transaction_count: int = Field(default=0, description="Number of bank statement transactions extracted")
    company_transaction_count: int = Field(default=0, description="Number of company record transactions extracted")
    pdf_filename: Optional[str] = Field(default=None, description="Original PDF filename")
    excel_filename: Optional[str] = Field(default=None, description="Original Excel filename")
    processing_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp of processing completion (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "pdf_processing_time_ms": 12500,
                "excel_processing_time_ms": 2700,
                "total_processing_time_ms": 15200,
                "bank_transaction_count": 150,
                "company_transaction_count": 450,
                "pdf_filename": "bank_statement.pdf",
                "excel_filename": "company_records.xlsx",
                "processing_timestamp": "2025-06-19T10:30:45Z"
            }
        }


# ==================== Processing Result Models ====================

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class ProcessingResult(BaseModel):
    """
    Aggregated processing result containing standardized transaction datasets and metadata
    Main output structure for /api/karwai endpoint

    Consistency Pattern: Must match API contract specification
    """
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for processing request")
    processing_status: str = Field(description="Overall status: completed, partial_success, failed")
    processing_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When processing completed (ISO 8601)")
    summary: Dict[str, Any] = Field(description="Processing summary statistics")
    results: Dict[str, List[Dict[str, Any]]] = Field(description="Standardized bank_statement and company_records datasets")
    errors: List[str] = Field(default_factory=list, description="List of non-fatal errors (empty if successful)")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "processing_status": "completed",
                "processing_timestamp": "2025-06-19T10:30:45Z",
                "summary": {
                    "total_bank_transactions": 150,
                    "total_company_transactions": 450,
                    "processing_duration_ms": 15200
                },
                "results": {
                    "bank_statement": [
                        {
                            "Transaction_date": "2023-01-15",
                            "Transaction Detail": "Payment from ABC Corporation",
                            "Debit/Credit": 5000
                        },
                        {
                            "Transaction_date": "2023-01-16",
                            "Transaction Detail": "Utility bill payment",
                            "Debit/Credit": -250
                        }
                    ],
                    "company_records": [
                        {
                            "Transaction_date": "2023-01-15",
                            "Transaction Detail": "Invoice payment received",
                            "Debit/Credit": -5000
                        },
                        {
                            "Transaction_date": "2023-01-16",
                            "Transaction Detail": "Office expenses",
                            "Debit/Credit": 250
                        }
                    ]
                },
                "errors": []
            }
        }


# ==================== Internal Processing Models ====================

class PDFTransaction(BaseModel):
    """
    Raw transaction data extracted from PDF bank statements before standardization
    Used internally during PDF processing pipeline
    """
    Tran_Date: str = Field(description="Original transaction date (DD-MMM-YY)")
    Transaction_Details: str = Field(description="Transaction narrative/details")
    Debit: Optional[float] = Field(default=None, description="Debit amount (null if credit)")
    Credit: Optional[float] = Field(default=None, description="Credit amount (null if debit)")
    Tran_Br: Optional[str] = Field(default=None, description="Transaction branch code")


class ExcelTransaction(BaseModel):
    """
    Raw transaction data extracted from Excel company records before standardization
    Used internally during Excel processing pipeline
    """
    transaction_date: Any = Field(description="Transaction date (various formats)")
    transaction_detail: str = Field(description="Transaction description")
    debit_amount: Optional[float] = Field(default=None, description="Debit amount (null if credit)")
    credit_amount: Optional[float] = Field(default=None, description="Credit amount (null if debit)")
    combined_amount: Optional[float] = Field(default=None, description="Combined amount (3-column format)")


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ