# Research Findings: PDF and Excel File Processing

**Feature**: PDF and Excel File Processing for Bank Reconciliation
**Date**: 2025-06-19
**Status**: Phase 0 Complete - All technical decisions resolved

## Overview

This document consolidates research findings on best practices, technical patterns, and implementation approaches for the PDF and Excel file processing feature. All research items have been investigated and decisions documented with rationale.

## Research Topics

### 1. Async File Processing Patterns in FastAPI

**Decision**: Use `asyncio.gather()` with separate async processing functions for PDF and Excel files

**Rationale**: 
- FastAPI's async capabilities work seamlessly with `asyncio.gather()` for concurrent I/O operations
- File processing (CPU-bound) should run in thread pool via `asyncio.to_thread()` to avoid blocking event loop
- Clean error handling with `asyncio.gather(return_exceptions=True)` allows one file failure to not crash entire request
- Natural fit for existing FastAPI route structure

**Implementation Pattern**:
```python
# Pseudo-code structure
async def process_files(pdf_file, excel_file, params):
    pdf_task = asyncio.create_task(process_pdf_async(pdf_file))
    excel_task = asyncio.create_task(process_excel_async(excel_file, params))
    
    results = await asyncio.gather(pdf_task, excel_task, return_exceptions=True)
    
    # Handle results and exceptions
    pdf_result, excel_result = results
    if isinstance(pdf_result, Exception):
        # Handle PDF processing error
    if isinstance(excel_result, Exception):
        # Handle Excel processing error
```

**Alternatives Considered**:
- **Sequential processing**: Rejected due to performance requirements (SC-003)
- **Multiprocessing**: Rejected due to complexity and limited benefit for I/O-bound operations
- **Background tasks**: Rejected as user needs immediate results (synchronous request pattern)

---

### 2. Error Handling for Corrupted/Malformed Files

**Decision**: Multi-layered validation with comprehensive error messages and graceful degradation

**Rationale**:
- Bank reconciliation requires accurate processing - better to fail explicitly than silently corrupt data
- Users need clear, actionable error messages for troubleshooting
- System must remain stable even when processing completely invalid files

**Implementation Strategy**:

**PDF Error Handling**:
```python
# Validation layers
1. File type validation (magic bytes, not just extension)
2. PDF structure validation (tabula-py ability to read pages)
3. Transaction table detection (at least one table found)
4. Column mapping validation (expected columns exist)
5. Data validation (reasonable values, proper formats)

# Error responses
- 400: Invalid file format or structure
- 422: Unprocessable entity (PDF exists but no transaction table found)
- 500: Internal processing error (with safe error details)
```

**Excel Error Handling**:
```python
# Validation layers
1. File type validation (valid .xlsx/.xls file)
2. Column existence validation (user-specified columns found)
3. Data type validation (numeric columns contain numbers)
4. Empty row handling (skip rows with missing critical data)

# Error responses
- 400: Invalid file or missing required columns
- 422: Column mapping failure (columns not found or contain invalid data)
```

**Alternatives Considered**:
- **Silent skipping of invalid rows**: Rejected due to accuracy requirements (zero data loss)
- **Attempt repair of malformed files**: Rejected due to complexity and risk of introducing errors

---

### 3. Memory-Efficient Large File Processing

**Decision**: Chunked reading with pandas `chunksize` parameter and streaming PDF processing

**Rationale**:
- Excel files with 1000+ transactions can consume significant memory if loaded entirely
- Chunked processing maintains constant memory usage regardless of file size
- Aligns with performance goals (SC-002: 500+ transactions in <10 seconds)

**Implementation Strategy**:

**Excel Processing**:
```python
# Process Excel in chunks
chunksize = 100  # Process 100 rows at a time
excel_chunks = pd.read_excel(excel_path, chunksize=chunksize)

all_transactions = []
for chunk in excel_chunks:
    # Process chunk with column mapping
    processed_chunk = process_chunk(chunk, column_mapping)
    all_transactions.extend(processed_chunk)

# Final result as List[Dict]
result = [dict(row) for row in all_transactions]
```

**PDF Processing**:
- Tabula-py processes pages individually (built-in chunking by pages)
- Process page-by-page and accumulate results
- Each page results in a DataFrame, process sequentially

**Memory Management**:
- Delete intermediate DataFrames after processing
- Use generators for large datasets
- Clear file handles immediately after processing

**Alternatives Considered**:
- **Load entire file into memory**: Rejected for files with 500+ transactions
- **Database-backed processing**: Rejected due to local execution requirements and complexity

---

### 4. Testing Patterns for File Processing Services

**Decision**: Three-layer testing approach with fixtures and sample files

**Rationale**:
- File processing has multiple failure modes requiring comprehensive test coverage
- Deterministic tests with known file samples ensure reliability
- Integration tests validate end-to-end processing workflows

**Testing Strategy**:

**Unit Tests** (`tests/unit/`):
```python
# Test individual functions in isolation
test_pdf_processor.py:
  - test_extract_bank_statement_success()
  - test_extract_bank_statement_no_tables()
  - test_merge_debit_credit_columns()
  - test_date_pattern_validation()

test_excel_processor.py:
  - test_process_excel_3_column_format()
  - test_process_excel_4_column_format()
  - test_column_not_found_error()
  - test_invalid_numeric_data_handling()

test_data_transformers.py:
  - test_standardize_transaction_format()
  - test_validate_transaction_date()
  - test_convert_to_integer_amounts()
```

**Integration Tests** (`tests/integration/`):
```python
test_file_processing_flow.py:
  - test_end_to_end_pdf_processing()
  - test_end_to_end_excel_processing()
  - test_concurrent_processing_performance()
  - test_error_recovery_flow()
```

**Test Fixtures**:
```python
# Sample files for testing
fixtures/
├── sample_bank_statement.pdf       # Valid PDF with 20 transactions
├── sample_bank_statement_multi.pdf # Multi-page PDF (5 pages)
├── malformed.pdf                   # Corrupted PDF
├── sample_company_3col.xlsx       # 3-column Excel format
├── sample_company_4col.xlsx       # 4-column Excel format
├── sample_company_large.xlsx      # Large file (500+ transactions)
└── invalid_column_names.xlsx      # Columns don't match user input
```

**Coverage Goals**:
- 90%+ code coverage for processing services
- All edge cases from spec covered
- All error paths tested

---

### 5. Date Format Validation and Normalization

**Decision**: Multi-format date parsing with normalization to standard ISO format

**Rationale**:
- Bank statements and Excel files may use different date formats
- Consistent date format required for downstream comparison logic
- Robust date handling prevents data corruption

**Implementation Strategy**:

**PDF Date Processing** (following test.py pattern):
```python
# Validate DD-MMM-YY pattern (e.g., "15-JAN-23")
DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")

# Validate and normalize
def validate_and_normalize_date(date_str):
    if not DATE_PATTERN.match(date_str):
        raise ValueError(f"Invalid date format: {date_str}")
    
    # Convert to standard format (e.g., "2023-01-15")
    return datetime.strptime(date_str, "%d-%b-%y").strftime("%Y-%m-%d")
```

**Excel Date Processing**:
```python
# Handle Excel serial dates and various string formats
def parse_excel_date(date_value):
    # Excel serial date (number)
    if isinstance(date_value, (int, float)):
        return (datetime(1899, 12, 30) + timedelta(days=date_value)).strftime("%Y-%m-%d")
    
    # String date - try common formats
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%y"]:
        try:
            return datetime.strptime(str(date_value), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    raise ValueError(f"Unrecognized date format: {date_value}")
```

**Normalization Standard**:
- All dates normalized to `YYYY-MM-DD` format (ISO 8601)
- Time components stripped (date-only for reconciliation)
- Invalid dates raise clear errors with format examples

---

## Additional Technical Decisions

### 6. File Storage and Cleanup Strategy

**Decision**: Organized subdirectories with automatic cleanup based on existing infrastructure

**Implementation**:
```text
uploads/
├── pdfs/                    # PDF bank statements
└── excels/                  # Excel company records

# Naming: {uuid}.{ext}
# Cleanup: Follow existing FILE_RETENTION_MINUTES setting
```

**Rationale**: 
- Clear separation prevents file type confusion
- UUID naming prevents collisions
- Reuses existing cleanup infrastructure

---

### 7. Debit/Credit Sign Handling

**Decision**: Strict sign assignment with validation

**Implementation**:
```python
def merge_debit_credit(debit_value, credit_value):
    # Both present - error
    if debit_value and credit_value:
        raise ValueError("Transaction cannot have both debit and credit")
    
    # Neither present - error  
    if not debit_value and not credit_value:
        raise ValueError("Transaction must have either debit or credit")
    
    # Debit - positive
    if debit_value:
        return abs(int(float(debit_value)))
    
    # Credit - negative
    if credit_value:
        return -abs(int(float(credit_value)))
```

**Rationale**: 
- Prevents data corruption from ambiguous entries
- Integer conversion meets FR-015 requirement
- Absolute value prevents sign inversion bugs

---

### 8. API Response Structure

**Decision**: Enhanced existing placeholder response with actual processing results

**Response Format**:
```json
{
  "request_id": "uuid",
  "processing_status": "completed",
  "processing_timestamp": "2025-06-19T10:30:00Z",
  "summary": {
    "total_bank_transactions": 150,
    "total_company_transactions": 450,
    "processing_duration_ms": 15200
  },
  "results": {
    "bank_statement": [
      {"Transaction_date": "2023-01-15", "Transaction Detail": "Payment from ABC Corp", "Debit/Credit": 5000}
    ],
    "company_records": [
      {"Transaction_date": "2023-01-15", "Transaction Detail": "Invoice payment", "Debit/Credit": -5000}
    ]
  },
  "errors": []
}
```

**Rationale**: 
- Maintains existing API contract
- Clear separation of bank vs company data
- Includes metadata for performance tracking

---

## Summary

**All technical research completed**. Key decisions:

1. **Async Processing**: `asyncio.gather()` with thread pool for CPU-bound work
2. **Error Handling**: Multi-layered validation with clear error messages
3. **Memory Management**: Chunked processing for large files
4. **Testing**: Three-layer approach with fixtures and sample files
5. **Date Handling**: Multi-format parsing with ISO normalization
6. **File Storage**: Organized subdirectories with automatic cleanup
7. **Sign Assignment**: Strict validation to prevent data corruption
8. **API Response**: Enhanced existing structure with actual results

**No NEEDS CLARIFICATION items remain**. Ready for Phase 1: Design & Contracts.