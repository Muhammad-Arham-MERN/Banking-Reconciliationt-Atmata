# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
File upload and processing models
Data structures for file handling, validation, and metadata
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# ==================== File Validation Status ====================

class FileValidationStatus(str, Enum):
    """File validation result status"""
    PENDING = "pending"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_SIZE = "invalid_size"
    CORRUPTED = "corrupted"
    EMPTY = "empty"

# ==================== File Upload Models ====================

class BankStatementUpload(BaseModel):
    """
    Represents an uploaded bank statement PDF file
    Consistency Pattern: Must match frontend BankStatementFile structure
    """
    file_id: str = Field(description="Unique identifier for the uploaded file instance (UUID)")
    original_filename: str = Field(description="Original filename from the upload")
    file_size: int = Field(description="File size in bytes (max 50MB)")
    mime_type: str = Field(description="MIME type, should be 'application/pdf'")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when file was uploaded")
    storage_path: str = Field(description="Local temporary storage path")
    validation_status: FileValidationStatus = Field(default=FileValidationStatus.PENDING, description="Validation result")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "file-1234567890-abcdefgh",
                "original_filename": "bank_statement.pdf",
                "file_size": 1048576,
                "mime_type": "application/pdf",
                "upload_timestamp": "2025-06-19T10:30:00Z",
                "storage_path": "/uploads/file-1234567890-abcdefgh.pdf",
                "validation_status": "valid"
            }
        }

class CompanyDataUpload(BaseModel):
    """
    Represents an uploaded company data Excel file
    Consistency Pattern: Must match frontend CompanyDataFile structure
    """
    file_id: str = Field(description="Unique identifier for the uploaded file instance (UUID)")
    original_filename: str = Field(description="Original filename from the upload")
    file_size: int = Field(description="File size in bytes (max 50MB)")
    mime_type: str = Field(description="MIME type, should be Excel type")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when file was uploaded")
    storage_path: str = Field(description="Local temporary storage path")
    validation_status: FileValidationStatus = Field(default=FileValidationStatus.PENDING, description="Validation result")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "file-0987654321-zyxwvuts",
                "original_filename": "company_data.xlsx",
                "file_size": 524288,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "upload_timestamp": "2025-06-19T10:30:00Z",
                "storage_path": "/uploads/file-0987654321-zyxwvuts.xlsx",
                "validation_status": "valid"
            }
        }

# ==================== Configuration Models ====================

class FormatType(str, Enum):
    """Supported column mapping formats"""
    DEBIT_PLUS_CREDIT = "debit-plus-credit"
    DEBIT_PIPE_CREDIT = "debit-pipe-credit"

class ColumnMappingConfiguration(BaseModel):
    """
    Column mapping configuration model
    Consistency Pattern: Must match frontend column mapping structure
    """
    format_type: FormatType = Field(description="Selected format type")

    # For debit-plus-credit format (3 fields)
    transaction_date_column: str = Field(description="Column name for transaction dates")
    debit_plus_credit_column: Optional[str] = Field(default=None, description="Combined debit/credit column name")
    transaction_details_column: str = Field(description="Transaction description/details column")

    # For debit-pipe-credit format (4 fields)
    debit_column: Optional[str] = Field(default=None, description="Debit column name")
    credit_column: Optional[str] = Field(default=None, description="Credit column name")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "format_type": "debit-plus-credit",
                    "transaction_date_column": "Date",
                    "debit_plus_credit_column": "Amount",
                    "transaction_details_column": "Description"
                },
                {
                    "format_type": "debit-pipe-credit",
                    "transaction_date_column": "Transaction Date",
                    "debit_column": "Debit",
                    "credit_column": "Credit",
                    "transaction_details_column": "Details"
                }
            ]
        }

# ==================== Processing Request Models ====================

class ProcessingRequest(BaseModel):
    """
    Complete reconciliation request with files and configuration
    Consistency Pattern: Must match frontend submission package structure
    """
    request_id: str = Field(description="Unique identifier for the processing request (UUID)")
    bank_statement: BankStatementUpload = Field(description="Uploaded bank statement file")
    company_data: CompanyDataUpload = Field(description="Uploaded company data file")
    column_mapping: ColumnMappingConfiguration = Field(description="Column mapping configuration")
    request_timestamp: datetime = Field(default_factory=datetime.now, description="When the request was received")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "bank_statement": {
                    "file_id": "file-1234567890-abcdefgh",
                    "original_filename": "bank_statement.pdf",
                    "file_size": 1048576,
                    "mime_type": "application/pdf",
                    "storage_path": "/uploads/file-1234567890-abcdefgh.pdf",
                    "validation_status": "valid"
                },
                "company_data": {
                    "file_id": "file-0987654321-zyxwvuts",
                    "original_filename": "company_data.xlsx",
                    "file_size": 524288,
                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "storage_path": "/uploads/file-0987654321-zyxwvuts.xlsx",
                    "validation_status": "valid"
                },
                "column_mapping": {
                    "format_type": "debit-plus-credit",
                    "transaction_date_column": "Date",
                    "debit_plus_credit_column": "Amount",
                    "transaction_details_column": "Description"
                }
            }
        }

# ==================== Metadata Models ====================

class PDFExtractionMetadata(BaseModel):
    """PDF-specific extraction information"""
    pages_processed: int = Field(description="Number of pages processed")
    tables_extracted: int = Field(description="Number of tables extracted")
    extraction_method: str = Field(description="Method used ('lattice' or 'stream')")
    extraction_quality_score: float = Field(ge=0.0, le=1.0, description="Quality score (0.0 to 1.0)")

class ExcelExtractionMetadata(BaseModel):
    """Excel-specific extraction information"""
    sheets_processed: int = Field(description="Number of sheets processed")
    rows_extracted: int = Field(description="Total number of rows extracted")
    columns_identified: int = Field(description="Number of columns identified")
    data_types_confirmed: bool = Field(description="Whether expected data types were confirmed")

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

# Extended file upload models with extraction metadata
class BankStatementUploadWithMetadata(BankStatementUpload):
    """Bank statement upload with PDF extraction metadata"""
    extraction_metadata: Optional[PDFExtractionMetadata] = Field(default=None, description="PDF-specific extraction information")

class CompanyDataUploadWithMetadata(CompanyDataUpload):
    """Company data upload with Excel extraction metadata"""
    extraction_metadata: Optional[ExcelExtractionMetadata] = Field(default=None, description="Excel-specific extraction information")

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ