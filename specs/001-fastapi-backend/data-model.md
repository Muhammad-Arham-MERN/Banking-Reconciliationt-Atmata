# Data Model: Backend API for Bank Reconciliation

**Feature**: `001-fastapi-backend`  
**Date**: 2025-06-18  
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data model for the backend API service, including all entities used in file processing, reconciliation logic, and API communication. The model supports the core functionality of accepting PDF bank statements and Excel company data, processing them with appropriate tools, and returning reconciliation results.

## Core Entities

### 1. FileUpload Models

#### BankStatementUpload
Represents an uploaded bank statement PDF file.

**Attributes**:
- `file_id: str` - Unique identifier for the uploaded file instance (UUID)
- `original_filename: str` - Original filename from the upload
- `file_size: int` - File size in bytes (max 10MB = 10,485,760 bytes)
- `mime_type: str` - MIME type, should be 'application/pdf'
- `upload_timestamp: datetime` - Timestamp when file was uploaded
- `storage_path: str` - Local temporary storage path
- `validation_status: FileValidationStatus` - Validation result
- `extraction_metadata: PDFTExtractionMetadata` - PDF-specific extraction information

**Validation Rules**:
- `file_size <= 10_485_760` bytes (10MB limit)
- `mime_type == 'application/pdf'`
- File must be readable by Tabula-py
- Filename must not contain path traversal characters

**State Transitions**:
```
UPLOADED → VALIDATING → VALIDATED → PROCESSING → PROCESSED → CLEANING_UP → REMOVED
                ↓              ↓          ↓
              INVALID         FAILED     ERROR
```

#### CompanyDataUpload
Represents an uploaded company data Excel file.

**Attributes**:
- `file_id: str` - Unique identifier for the uploaded file instance (UUID)
- `original_filename: str` - Original filename from the upload
- `file_size: int` - File size in bytes (max 5MB = 5,242,880 bytes)
- `mime_type: str` - MIME type, should be Excel type
- `upload_timestamp: datetime` - Timestamp when file was uploaded
- `storage_path: str` - Local temporary storage path
- `validation_status: FileValidationStatus` - Validation result
- `extraction_metadata: ExcelExtractionMetadata` - Excel-specific extraction information

**Validation Rules**:
- `file_size <= 5_242_880` bytes (5MB limit)
- `mime_type` in allowed Excel types ('application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
- File must be readable by Pandas
- Filename must not contain path traversal characters

**State Transitions**:
```
UPLOADED → VALIDATING → VALIDATED → PROCESSING → PROCESSED → CLEANING_UP → REMOVED
                ↓              ↓          ↓
              INVALID         FAILED     ERROR
```

### 2. Configuration Models

#### ColumnMappingConfiguration
Represents the user's specification of how their company data is structured.

**Attributes**:
- `format_type: FormatType` - Selected format type ('debit-plus-credit' or 'debit-pipe-credit')
- `transaction_date_column: str` - Column name for transaction dates
- `transaction_details_column: str` - Transaction description/details column

**Conditional Attributes** (based on `format_type`):

For `debit-plus-credit` format:
- `debit_plus_credit_column: str` - Combined debit/credit column name

For `debit-pipe-credit` format:
- `debit_column: str` - Separate debit column name  
- `credit_column: str` - Separate credit column name

**Validation Rules**:
- All column names must be non-empty strings
- Column names must exist in the uploaded Excel file
- `format_type` must be one of the allowed values
- Column mapping configuration must be complete before processing

#### FormatType
Enumeration of supported column mapping formats.

**Values**:
- `debit-plus-credit` - Format where debits and credits are in a single column
- `debit-pipe-credit` - Format where debits and credits are in separate columns

### 3. Processing Models

#### ProcessingRequest
Represents a complete reconciliation request with files and configuration.

**Attributes**:
- `request_id: str` - Unique identifier for the processing request (UUID)
- `bank_statement: BankStatementUpload` - Uploaded bank statement file
- `company_data: CompanyDataUpload` - Uploaded company data file
- `column_mapping: ColumnMappingConfiguration` - Column mapping configuration
- `request_timestamp: datetime` - When the request was received
- `processing_status: ProcessingStatus` - Current processing status
- `processing_metadata: ProcessingMetadata` - Additional processing information

**Validation Rules**:
- Both files must be present and validated
- Column mapping configuration must be complete
- File size limits must be respected
- Files must be in correct formats (PDF for bank, Excel for company)

**State Transitions**:
```
RECEIVED → VALIDATING → VALIDATED → PROCESSING → COMPLETED → CLEANING_UP → REMOVED
              ↓            ↓          ↓          ↓
            INVALID      FAILED     ERROR     TIMEOUT
```

#### ProcessingStatus
Enumeration of processing request statuses.

**Values**:
- `RECEIVED` - Request received, awaiting validation
- `VALIDATING` - Validating files and configuration
- `VALIDATED` - Files and configuration validated successfully
- `PROCESSING` - Currently processing reconciliation
- `COMPLETED` - Processing completed successfully
- `FAILED` - Processing failed (non-timeout error)
- `ERROR` - System error during processing
- `TIMEOUT` - Processing exceeded time limits
- `CLEANING_UP` - Cleaning up temporary files
- `REMOVED` - Request and files removed from system

### 4. Result Models

#### ReconciliationResult
Represents the results of reconciliation processing.

**Attributes**:
- `result_id: str` - Unique identifier for the result (UUID)
- `request_id: str` - Associated processing request ID
- `processing_timestamp: datetime` - When reconciliation was completed
- `summary: ReconciliationSummary` - High-level summary of results
- `matches: list[TransactionMatch]` - Matched transactions
- `discrepancies: list[TransactionDiscrepancy]` - Unmatched/discrepant transactions
- `statistics: ProcessingStatistics` - Processing performance statistics

**Output Format**: List of dictionaries as per requirements, each containing match/discrepancy information.

#### TransactionMatch
Represents a matched transaction between bank and company records.

**Attributes**:
- `match_id: str` - Unique identifier for this match
- `bank_transaction: BankTransaction` - Transaction from bank statement
- `company_transaction: CompanyTransaction` - Transaction from company data
- `match_confidence: float` - Confidence score for the match (0.0 to 1.0)
- `match_type: MatchType` - Type of match (exact, amount_only, date_range, etc.)

#### TransactionDiscrepancy
Represents an unmatched or discrepant transaction.

**Attributes**:
- `discrepancy_id: str` - Unique identifier for this discrepancy
- `source: DiscrepancySource` - Which file the discrepancy is from
- `transaction: BankTransaction | CompanyTransaction` - The unmatched transaction
- `discrepancy_type: DiscrepancyType` - Type of discrepancy
- `possible_matches: list[PossibleMatch]` - Potential matches if any

#### BankTransaction
Transaction record extracted from bank statement PDF.

**Attributes**:
- `transaction_id: str` - Unique identifier for this transaction
- `transaction_date: date` - Transaction date
- `transaction_description: str` - Transaction description/details
- `amount: decimal.Decimal` - Transaction amount (positive for credit, negative for debit)
- `balance: decimal.Decimal | None` - Balance after transaction (if available)

#### CompanyTransaction
Transaction record extracted from company data Excel.

**Attributes**:
- `transaction_id: str` - Unique identifier for this transaction
- `transaction_date: date` - Transaction date
- `transaction_description: str` - Transaction description/details
- `debit_amount: decimal.Decimal | None` - Debit amount (if separate)
- `credit_amount: decimal.Decimal | None` - Credit amount (if separate)
- `net_amount: decimal.Decimal` - Net amount (credit - debit)

### 5. Metadata Models

#### FileValidationStatus
File validation result.

**Values**:
- `PENDING` - Validation not yet started
- `VALIDATING` - Currently validating
- `VALID` - File validated successfully
- `INVALID_FORMAT` - Invalid file format
- `INVALID_SIZE` - File size exceeds limits
- `CORRUPTED` - File is corrupted or unreadable
- `EMPTY` - File contains no data

#### ProcessingMetadata
Additional information about the processing request.

**Attributes**:
- `client_ip: str | None` - Client IP address (if available)
- `user_agent: str | None` - Client user agent (if available)
- `processing_duration_ms: int` - Processing time in milliseconds
- `files_processed: int` - Number of files successfully processed
- `error_count: int` - Number of errors encountered

#### PDFTExtractionMetadata
PDF-specific extraction information.

**Attributes**:
- `pages_processed: int` - Number of pages processed
- `tables_extracted: int` - Number of tables extracted
- `extraction_method: str` - Method used ('lattice' or 'stream')
- `extraction_quality_score: float` - Quality score (0.0 to 1.0)

#### ExcelExtractionMetadata  
Excel-specific extraction information.

**Attributes**:
- `sheets_processed: int` - Number of sheets processed
- `rows_extracted: int` - Total number of rows extracted
- `columns_identified: int` - Number of columns identified
- `data_types_confirmed: bool` - Whether expected data types were confirmed

## Data Relationships

```
ProcessingRequest
├── BankStatementUpload
│   └── PDFTExtractionMetadata
├── CompanyDataUpload
│   └── ExcelExtractionMetadata
├── ColumnMappingConfiguration
├── ReconciliationResult
│   ├── ReconciliationSummary
│   ├── list[TransactionMatch]
│   │   ├── BankTransaction
│   │   └── CompanyTransaction
│   ├── list[TransactionDiscrepancy]
│   │   └── (BankTransaction OR CompanyTransaction)
│   └── ProcessingStatistics
└── ProcessingMetadata
```

## Validation Rules Summary

### File Validation
- PDF files must be ≤10MB, Excel files must be ≤5MB
- MIME types must match expected formats
- Files must be readable by respective processing libraries
- Filenames must be secure (no path traversal)

### Configuration Validation
- Column names must be non-empty strings
- Format type must be valid
- All required fields for selected format must be present
- Column names must exist in uploaded Excel file

### Processing Validation
- Both files must be present and validated
- Configuration must be complete
- Processing must complete within 30 seconds
- Results must be properly formatted

## State Management

### File Lifecycle
1. **Upload**: File received from client
2. **Validate**: File format and size validation
3. **Process**: Extract data using appropriate library
4. **Clean**: Remove temporary files
5. **Remove**: Complete cleanup

### Request Lifecycle
1. **Receive**: Accept request with files and configuration
2. **Validate**: Validate all components
3. **Process**: Execute reconciliation logic
4. **Complete**: Return results
5. **Cleanup**: Remove temporary data
6. **Expire**: Complete removal after timeout

## Error Handling

### Validation Errors
- Invalid file formats → 422 Unprocessable Entity
- File size exceeded → 413 Payload Too Large
- Missing required fields → 400 Bad Request
- Invalid configuration → 422 Unprocessable Entity

### Processing Errors
- File extraction failure → 500 Internal Server Error
- Reconciliation logic error → 500 Internal Server Error
- Processing timeout → 504 Gateway Timeout
- Resource exhaustion → 503 Service Unavailable

### System Errors
- Disk full → 503 Service Unavailable
- Service unavailable → 503 Service Unavailable
- Internal system error → 500 Internal Server Error

## Performance Considerations

### Memory Management
- Stream file uploads instead of loading entirely into memory
- Process files incrementally when possible
- Clean up resources immediately after use

### Processing Optimization  
- Use async operations throughout
- Implement early validation to fail fast
- Process files in parallel where safe
- Cache repetitive operations

### Cleanup Strategy
- Remove files within 1 hour of processing completion
- Implement periodic cleanup of orphaned files
- Use secure deletion for sensitive financial data

## Security Considerations

### Data Protection
- No permanent storage of sensitive financial data
- Automatic cleanup of temporary files
- Secure temporary file handling
- Error messages don't expose sensitive information

### Input Validation
- Validate all file uploads
- Sanitize all user inputs
- Prevent path traversal attacks
- Implement rate limiting

### Access Control
- No authentication required (local application)
- Consider basic authentication if needed in future
- Implement CORS if frontend/backend on different domains

## Next Steps

1. **API Contracts**: Define detailed API contracts in OpenAPI format
2. **Implementation**: Create service classes based on these models
3. **Testing**: Define test cases for each entity and relationship
4. **Documentation**: Create API documentation based on these models