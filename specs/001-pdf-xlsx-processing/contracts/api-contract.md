# API Contract: PDF and Excel File Processing

**Feature**: PDF and Excel File Processing for Bank Reconciliation
**Date**: 2025-06-19
**Version**: 1.0.0
**Status**: Phase 1 Design - API specification

## Overview

This document specifies the API contract for the enhanced karwai POST endpoint that processes PDF bank statements and Excel company records. The endpoint supports concurrent file processing, flexible column mapping, and standardized transaction output.

## Base URL

```
POST /api/karwai
```

## Authentication

**Current**: No authentication required (local execution)
**Future**: Consider API key or session-based authentication if needed

---

## Endpoint Specification

### POST /api/karwai

Process PDF bank statement and Excel company record files to extract standardized transaction data for reconciliation.

---

#### Request

**Content-Type**: `multipart/form-data`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bankStatement` | file | Yes | PDF bank statement file |
| `companyData` | file | Yes | Excel company record file (.xlsx, .xls) |
| `formatType` | string | Yes | Format type: `debit-plus-credit` or `debit-pipe-credit` |
| `transactionDateColumn` | string | Yes | Name of transaction date column in Excel |
| `transactionDetailsColumn` | string | Yes | Name of transaction details column in Excel |
| `debitPlusCreditColumn` | string | Conditional* | Name of combined debit/credit column (3-column format) |
| `debitColumn` | string | Conditional* | Name of debit column (4-column format) |
| `creditColumn` | string | Conditional* | Name of credit column (4-column format) |

*Conditional parameters:
- For `debit-plus-credit` format: `debitPlusCreditColumn` required
- For `debit-pipe-credit` format: `debitColumn` and `creditColumn` required

**File Constraints**:
- PDF: Max size 50MB, must be valid PDF format
- Excel: Max size 10MB, must be valid .xlsx or .xls file

---

#### Request Example

**3-Column Format (debit-plus-credit)**:
```http
POST /api/karwai HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="bankStatement"; filename="bank_statement.pdf"
Content-Type: application/pdf

[PDF binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="companyData"; filename="company_records.xlsx"
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

[Excel binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="formatType"

debit-plus-credit
------WebKitFormBoundary
Content-Disposition: form-data; name="transactionDateColumn"

Transaction Date
------WebKitFormBoundary
Content-Disposition: form-data; name="transactionDetailsColumn"

Description
------WebKitFormBoundary
Content-Disposition: form-data; name="debitPlusCreditColumn"

Amount
------WebKitFormBoundary--
```

**4-Column Format (debit-pipe-credit)**:
```http
POST /api/karwai HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="bankStatement"; filename="bank_statement.pdf"
Content-Type: application/pdf

[PDF binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="companyData"; filename="company_records.xlsx"
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

[Excel binary data]
------WebKitFormBoundary
Content-Disposition: form-data; name="formatType"

debit-pipe-credit
------WebKitFormBoundary
Content-Disposition: form-data; name="transactionDateColumn"

Date
------WebKitFormBoundary
Content-Disposition: form-data; name="transactionDetailsColumn"

Details
------WebKitFormBoundary
Content-Disposition: form-data; name="debitColumn"

Debit
------WebKitFormBoundary
Content-Disposition: form-data; name="creditColumn"

Credit
------WebKitFormBoundary--
```

---

#### Response

**Content-Type**: `application/json`

**Success Response** (200 OK):

```json
{
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
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string (UUID) | Unique identifier for this processing request |
| `processing_status` | string | Status: "completed", "partial_success", "failed" |
| `processing_timestamp` | string (ISO) | Timestamp when processing completed |
| `summary.total_bank_transactions` | integer | Number of transactions extracted from PDF |
| `summary.total_company_transactions` | integer | Number of transactions extracted from Excel |
| `summary.processing_duration_ms` | integer | Total processing time in milliseconds |
| `results.bank_statement` | array | Standardized bank statement transactions |
| `results.company_records` | array | Standardized company record transactions |
| `errors` | array | List of non-fatal errors (empty if successful) |

**Transaction Object Structure**:

```json
{
  "Transaction_date": "YYYY-MM-DD",
  "Transaction Detail": "string description",
  "Debit/Credit": integer
}
```

- `Transaction_date`: ISO 8601 date format (YYYY-MM-DD)
- `Transaction Detail`: Transaction description or narrative
- `Debit/Credit`: Integer amount (positive=debit, negative=credit)

---

#### Error Responses

**400 Bad Request** - Invalid input parameters:

```json
{
  "error": "bad_request",
  "message": "Invalid format type provided. Must be either 'debit-plus-credit' or 'debit-pipe-credit'.",
  "details": {
    "provided_format": "invalid_format",
    "valid_formats": ["debit-plus-credit", "debit-pipe-credit"],
    "help": "Check your format type spelling and try again"
  }
}
```

**400 Bad Request** - Missing required fields:

```json
{
  "error": "bad_request",
  "message": "Missing required field for debit-plus-credit format.",
  "details": {
    "format_type": "debit-plus-credit",
    "missing_field": "debitPlusCreditColumn",
    "required_fields": [
      "formatType",
      "transactionDateColumn",
      "debitPlusCreditColumn",
      "transactionDetailsColumn"
    ],
    "help": "For debit-plus-credit format, provide a combined debit/credit column name"
  }
}
```

**422 Unprocessable Entity** - File processing error:

```json
{
  "error": "processing_error",
  "message": "PDF file does not contain extractable transaction table",
  "details": {
    "file_type": "pdf",
    "error_type": "no_transactions",
    "filename": "bank_statement.pdf",
    "help": "Ensure PDF is a valid bank statement with transaction data in tabular format"
  }
}
```

**422 Unprocessable Entity** - Column mapping error:

```json
{
  "error": "processing_error",
  "message": "Column 'Amount' not found in Excel file",
  "details": {
    "file_type": "excel",
    "error_type": "column_not_found",
    "missing_column": "Amount",
    "available_columns": ["Date", "Description", "Value"],
    "help": "Check column name spelling and ensure it exists in the Excel file"
  }
}
```

**500 Internal Server Error** - Unexpected processing error:

```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred during file processing",
  "details": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "error_details": "Detailed error message for debugging",
    "help": "Please try again or contact support with this request ID"
  }
}
```

**503 Service Unavailable** - Server shutting down:

```json
{
  "error": "service_unavailable",
  "message": "Server is shutting down. Please try again later.",
  "details": {
    "shutdown_in_progress": true,
    "retry_after": 60
  }
}
```

---

## Behavior Specifications

### Processing Behavior

1. **Concurrent Processing**: Both files processed simultaneously using async operations
2. **Validation First**: Validate all parameters before processing files
3. **Graceful Degradation**: One file failure doesn't crash entire request (returns partial success)
4. **File Storage**: Files stored locally during processing, cleaned up after completion
5. **Performance Monitoring**: Track and return processing time for each file type

### Error Handling Behavior

1. **Parameter Validation**: Immediate 400 response for invalid parameters
2. **File Validation**: 422 response for corrupted or invalid files
3. **Processing Errors**: Detailed error messages indicating specific failure points
4. **Partial Success**: If one file processes successfully but other fails, return partial success with error details

### Performance Expectations

- **PDF Processing**: <30 seconds for 10-page statement with 100+ transactions
- **Excel Processing**: <10 seconds for file with 500+ transactions
- **Concurrent Processing**: Total time < sum of individual processing times

---

## OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: Bank Reconciliation API
  version: 1.0.0
  description: API for processing bank statements and company records

paths:
  /api/karwai:
    post:
      summary: Process bank statement and company records
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - bankStatement
                - companyData
                - formatType
                - transactionDateColumn
                - transactionDetailsColumn
              properties:
                bankStatement:
                  type: string
                  format: binary
                  description: PDF bank statement file
                companyData:
                  type: string
                  format: binary
                  description: Excel company record file
                formatType:
                  type: string
                  enum: [debit-plus-credit, debit-pipe-credit]
                  description: Format type for Excel columns
                transactionDateColumn:
                  type: string
                  description: Name of transaction date column
                transactionDetailsColumn:
                  type: string
                  description: Name of transaction details column
                debitPlusCreditColumn:
                  type: string
                  description: Combined debit/credit column name (3-column format)
                debitColumn:
                  type: string
                  description: Debit column name (4-column format)
                creditColumn:
                  type: string
                  description: Credit column name (4-column format)
      responses:
        '200':
          description: Processing completed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProcessingResult'
        '400':
          description: Bad request - invalid parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Unprocessable entity - file processing error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '503':
          description: Service unavailable - server shutting down
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    ProcessingResult:
      type: object
      properties:
        request_id:
          type: string
          format: uuid
        processing_status:
          type: string
          enum: [completed, partial_success, failed]
        processing_timestamp:
          type: string
          format: date-time
        summary:
          type: object
          properties:
            total_bank_transactions:
              type: integer
            total_company_transactions:
              type: integer
            processing_duration_ms:
              type: integer
        results:
          type: object
          properties:
            bank_statement:
              type: array
              items:
                $ref: '#/components/schemas/Transaction'
            company_records:
              type: array
              items:
                $ref: '#/components/schemas/Transaction'
        errors:
          type: array
          items:
            type: string

    Transaction:
      type: object
      required:
        - Transaction_date
        - Transaction Detail
        - Debit/Credit
      properties:
        Transaction_date:
          type: string
          format: date
          pattern: ^\\d{4}-\\d{2}-\\d{2}$
        Transaction Detail:
          type: string
        Debit/Credit:
          type: integer

    Error:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
        message:
          type: string
        details:
          type: object
```

---

## Summary

**API Contract Characteristics**:
- **Endpoint**: Single POST endpoint with comprehensive file processing
- **Content-Type**: Multipart/form-data for file uploads
- **Response Format**: JSON with standardized transaction structure
- **Error Handling**: Detailed error responses with actionable guidance
- **Performance**: Concurrent processing with performance metrics
- **Validation**: Multi-layered validation (parameters, files, data)
- **Extensibility**: Support for both 3-column and 4-column Excel formats

This API contract enables comprehensive file processing while maintaining backward compatibility with existing endpoint structure and parameter validation.