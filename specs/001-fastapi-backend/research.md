# Research Findings: Backend API for Bank Reconciliation

**Feature**: `001-fastapi-backend`  
**Date**: 2025-06-18  
**Phase**: Phase 0 - Research & Investigation

## Overview

This document captures research findings for implementing the backend API service. Research focused on best practices for the specified technology stack (FastAPI, Pandas, Tabula-py) and architectural patterns for file processing, graceful shutdown, and local storage management.

## Technology Stack Research

### 1. FastAPI File Upload Handling

**Decision**: Use FastAPI with `UploadFile` and `python-multipart` for multipart/form-data handling

**Rationale**: 
- FastAPI provides built-in support for file uploads via `UploadFile` class
- `python-multipart` is the standard dependency for handling multipart form data
- Async file handling prevents blocking during large file uploads
- Built-in validation and error handling for file types and sizes

**Best Practices Identified**:
- Use `UploadFile` instead of `bytes` for memory efficiency with large files
- Implement file size validation before processing
- Use async file operations to prevent blocking
- Validate file MIME types in addition to extensions
- Clean up temporary files after processing

**Alternatives Considered**:
- Flask with Flask-Uploads: Rejected due to Developer's explicit FastAPI requirement
- Direct bytes handling: Rejected due to memory constraints with large files

### 2. Pandas Excel Processing for Financial Data

**Decision**: Use Pandas with `read_excel()` for Excel file processing

**Rationale**:
- Pandas provides robust Excel file parsing with multiple engine support
- Built-in data type detection and conversion
- Excellent handling of financial data formats (currency, dates, numerical values)
- Strong error handling for malformed files
- Wide range of data manipulation capabilities for reconciliation logic

**Best Practices Identified**:
- Use `openpyxl` or `xlrd` engines for better compatibility
- Specify column data types explicitly to avoid type inference errors
- Handle missing values appropriately for financial data (NaN vs 0.0)
- Use `dtype` parameter for consistent column types
- Implement error handling for corrupted Excel files

**Alternatives Considered**:
- openpyxl directly: Rejected due to lower-level API and more manual work
- xlrd: Rejected due to limited .xlsx support

### 3. Tabula-py PDF Table Extraction

**Decision**: Use Tabula-py with `read_pdf()` for PDF table extraction

**Rationale**:
- Tabula-py is the Python wrapper for Tabula (Java-based PDF table extraction)
- Specifically designed for extracting tables from PDF files
- Handles complex table layouts better than generic PDF parsers
- Supports multiple extraction modes (lattice, stream)
- Good handling of bank statement formatting

**Best Practices Identified**:
- Use `pages='all'` or specify exact page ranges for better performance
- Try both `lattice` and `stream` modes for different table layouts
- Use `multiple_tables=True` for PDFs with multiple tables
- Handle cases where no tables are detected
- Clean up extracted data (remove headers/footers, handle merged cells)

**Alternatives Considered**:
- PyPDF2: Rejected due to poor table extraction capabilities
- pdfplumber: Considered but Tabula-py has better table detection
- Camelot: Rejected due to more complex setup and dependency requirements

### 4. Graceful Shutdown Patterns in FastAPI

**Decision**: Use FastAPI's lifespan events and signal handling for graceful shutdown

**Rationale**:
- FastAPI provides `lifespan` context manager for startup/shutdown events
- Built-in support for handling SIGTERM and SIGINT signals
- Allows completion of ongoing requests before shutdown
- Clean resource cleanup and file management

**Best Practices Identified**:
- Use `@contextlib.asynccontextmanager` for lifespan management
- Implement request timeout handling to prevent indefinite hanging
- Track active requests and wait for completion during shutdown
- Provide shutdown warnings for frontend operators
- Clean up temporary files during shutdown
- Set maximum shutdown timeout (10 seconds per requirements)

**Alternatives Considered**:
- Manual signal handling: Rejected due to complexity and potential race conditions
- No graceful shutdown: Rejected per requirements for graceful shutdown

### 5. Local File Storage Management

**Decision**: Use temporary file directories with automatic cleanup

**Rationale**:
- Python's `tempfile` module provides secure temporary file handling
- Automatic cleanup on application exit
- Cross-platform compatibility (Windows environment)
- Prevents disk space issues

**Best Practices Identified**:
- Use `tempfile.TemporaryDirectory()` for automatic cleanup
- Implement scheduled cleanup for files older than 1 hour (per requirements)
- Use unique file identifiers (UUIDs) to prevent conflicts
- Implement proper error handling for disk full scenarios
- Store file metadata separately from file contents
- Use absolute paths to avoid path resolution issues

**Alternatives Considered**:
- Database file storage: Rejected due to unnecessary complexity for local application
- Cloud storage: Rejected per local execution requirements
- Permanent file storage: Rejected due to privacy and cleanup requirements

## Architectural Patterns Research

### Service Layer Pattern

**Decision**: Implement service layer for business logic separation

**Rationale**:
- Separates business logic from API controllers
- Improves testability and maintainability
- Follows FastAPI best practices
- Allows easy extension of processing capabilities

**Implementation Approach**:
- `PDFService`: Handles PDF table extraction logic
- `ExcelService`: Handles Excel file parsing logic  
- `ReconciliationService`: Core comparison and discrepancy detection logic
- `FileStorageService`: File storage and cleanup management

### Dependency Injection Pattern

**Decision**: Use FastAPI's dependency injection for service dependencies

**Rationale**:
- Built-in FastAPI feature for dependency management
- Improves testability through easy mocking
- Follows FastAPI conventions
- Clean separation of concerns

### Error Handling Strategy

**Decision**: Implement comprehensive error handling with proper HTTP status codes

**Rationale**:
- FastAPI provides automatic exception handling
- Allows clear error responses to frontend
- Proper logging for debugging and monitoring
- User-friendly error messages

**Error Categories Identified**:
- File validation errors (422 Unprocessable Entity)
- File processing errors (500 Internal Server Error)
- Resource limit errors (413 Payload Too Large)
- Service unavailable errors (503 Service Unavailable)

## Performance Considerations

### File Size Limits
- PDF files: Maximum 10MB per requirements
- Excel files: Maximum 5MB per requirements
- Total request size: ~15MB maximum

### Processing Time Optimization
- Async file operations to prevent blocking
- Efficient PDF table extraction with page-specific processing
- Pandas optimization with specified dtypes
- Early validation to fail fast on invalid inputs

### Concurrent Request Handling
- Use async operations throughout the stack
- Implement proper connection pooling
- Rate limiting for resource protection
- Queue management for concurrent processing

## Security Considerations

### File Upload Security
- Validate file MIME types, not just extensions
- Implement file size limits
- Scan uploaded files for malicious content (basic validation)
- Use secure file naming to prevent path traversal
- Isolate uploaded files from application code

### Data Privacy
- Automatic file cleanup after processing
- No permanent storage of sensitive financial data
- Secure temporary file handling
- Error messages don't expose sensitive information

## Integration with Frontend

### API Contract Analysis
Based on existing frontend code analysis:

**Frontend Expects**:
- Multipart/form-data POST request
- Two files: `bankStatement` (PDF) and `companyData` (Excel)
- Text fields: `formatType`, `transactionDateColumn`, plus 3-4 additional fields based on format
- Response: List of dictionaries with reconciliation results

**Backend Will Provide**:
- `/karwai` POST endpoint accepting multipart/form-data
- File validation and processing
- Structured JSON response matching frontend expectations
- Proper error responses for validation failures

## Dependencies and Versions

### Core Dependencies
- **FastAPI**: ^0.104.0 (latest stable with async support)
- **Uvicorn**: ^0.24.0 (ASGI server for FastAPI)
- **Pandas**: ^2.1.0 (Excel processing)
- **Tabula-py**: ^2.9.0 (PDF table extraction)
- **python-multipart**: ^0.0.6 (Multipart form handling)
- **openpyxl**: ^3.3.0 (Excel engine for Pandas)
- **pytest**: ^7.4.0 (Testing framework)
- **pytest-asyncio**: ^0.21.0 (Async testing support)

### Python Version
- **Python**: 3.11+ (as per technical context)

## Summary and Next Steps

**Research Complete**: All technical areas researched and decisions documented

**Key Decisions Made**:
1. FastAPI with UploadFile for file handling
2. Pandas for Excel processing  
3. Tabula-py for PDF table extraction
4. Service layer pattern for business logic
5. Graceful shutdown via lifespan events
6. Temporary file storage with automatic cleanup

**Ready for Phase 1**: Data model and API contracts design can proceed with these research findings as foundation.

**No Clarifications Needed**: All technical requirements were clear and research successfully identified best practices for implementation.