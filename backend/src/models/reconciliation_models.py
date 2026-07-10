# بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
"""
Reconciliation data models for bank reconciliation logic.
Defines Pydantic models for API contracts and validation.
"""

from pydantic import BaseModel, Field
from typing import List


class BankTransaction(BaseModel):
    """Individual transaction from bank statement"""

    Transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    Transaction_Detail: str = Field(..., description="Transaction description")
    Debit_Credit: float = Field(..., description="Amount with sign (positive for credit, negative for debit)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "Transaction_date": "2026-05-05",
                    "Transaction_Detail": "INWARD CHEQUE",
                    "Debit_Credit": 10200.0
                },
                {
                    "Transaction_date": "2026-05-06",
                    "Transaction_Detail": "P2P RECEIVING VIA GREAVES",
                    "Debit_Credit": -22000000.0
                }
            ]
        }
    }


class CompanyTransaction(BaseModel):
    """Individual transaction from company records"""

    Transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    Transaction_Detail: str = Field(..., description="Transaction description")
    Debit_Credit: float = Field(..., description="Amount with sign (positive for credit, negative for debit)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "Transaction_date": "2026-05-04",
                    "Transaction_Detail": "Salaries IIAP mo Apr-26",
                    "Debit_Credit": -17929400.0
                },
                {
                    "Transaction_date": "2026-05-04",
                    "Transaction_Detail": "Fund Transfer Through RTGS from SBL to MCB BANK ISB",
                    "Debit_Credit": 22000000.0
                }
            ]
        }
    }


class DiscrepancyTransaction(BaseModel):
    """Transaction present in one source but not the other"""

    Transaction_date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    Transaction_Detail: str = Field(..., description="Transaction description")
    Debit_Credit: float = Field(..., description="Amount with sign (positive for credit, negative for debit)")
    FROM: str = Field(..., description="Source of this discrepancy: 'Bank' or 'Company'")
    from_past: bool = Field(False, description="Whether this entry originated from a loaded history file")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "Transaction_date": "2026-05-06",
                    "Transaction_Detail": "Payment Suzuki Azim Motors WHT 5.515",
                    "Debit_Credit": -40771.695,
                    "FROM": "Bank"
                },
                {
                    "Transaction_date": "2026-05-06",
                    "Transaction_Detail": "Payment Suzuki Azim Motors WHT 5.515",
                    "Debit_Credit": 6771.238,
                    "FROM": "Company"
                }
            ]
        }
    }


class ReconciliationSummary(BaseModel):
    """Summary statistics for reconciliation process"""

    total_bank_transactions: int = Field(..., description="Total number of transactions in bank statement")
    total_company_transactions: int = Field(..., description="Total number of transactions in company records")
    total_discrepancies: int = Field(..., description="Total number of discrepancies found")
    bank_only_discrepancies: int = Field(..., description="Number of discrepancies only in bank statement")
    company_only_discrepancies: int = Field(..., description="Number of discrepancies only in company records")
    opposite_pairs_removed: int = Field(..., description="Number of opposite sign pairs removed")
    processing_duration_ms: int = Field(..., description="Total processing time in milliseconds")
    pdf_processing_time_ms: int = Field(..., description="PDF processing time in milliseconds")
    excel_processing_time_ms: int = Field(..., description="Excel processing time in milliseconds")
    concurrent_processing: bool = Field(..., description="Whether PDF and Excel were processed concurrently")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_bank_transactions": 26,
                    "total_company_transactions": 20,
                    "total_discrepancies": 15,
                    "bank_only_discrepancies": 8,
                    "company_only_discrepancies": 7,
                    "opposite_pairs_removed": 4,
                    "processing_duration_ms": 7153,
                    "pdf_processing_time_ms": 7151,
                    "excel_processing_time_ms": 191,
                    "concurrent_processing": True
                }
            ]
        }
    }


class ReconciliationResult(BaseModel):
    """Complete reconciliation response containing all processed data"""

    request_id: str = Field(..., description="Unique request identifier for tracking")
    processing_status: str = Field(..., description="Processing status: completed, partial, or error")
    processing_timestamp: str = Field(..., description="ISO 8601 timestamp of processing completion")
    summary: ReconciliationSummary = Field(..., description="ReconciliationSummary object")
    results: dict = Field(..., description="Object containing all transaction lists")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    message: str = Field(..., description="User-friendly status message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "f5af9205-7b5b-4ffb-8f56-95cbe292c09e",
                    "processing_status": "completed",
                    "processing_timestamp": "2026-06-23T03:20:03.251969Z",
                    "summary": {
                        "total_bank_transactions": 26,
                        "total_company_transactions": 20,
                        "total_discrepancies": 15,
                        "bank_only_discrepancies": 8,
                        "company_only_discrepancies": 7,
                        "opposite_pairs_removed": 4,
                        "processing_duration_ms": 7153,
                        "pdf_processing_time_ms": 7151,
                        "excel_processing_time_ms": 191,
                        "concurrent_processing": True
                    },
                    "results": {
                        "bank_statement": [],
                        "company_records": [],
                        "discrepancies": []
                    },
                    "errors": [],
                    "message": "Reconciliation complete - Found 15 discrepancies"
                }
            ]
        }
    }


# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
