# API Contract: Backend Reconciliation Service

**Feature**: `001-fastapi-backend`  
**Date**: 2025-06-18  
**Phase**: Phase 1 - Design & Contracts  
**Version**: 1.0.0

## Overview

This document defines the API contract for the backend reconciliation service. The service provides two REST endpoints: a health check endpoint and a main reconciliation processing endpoint. All communication uses HTTP with JSON responses, and file uploads use multipart/form-data encoding.

## Base URL

**Development**: `http://localhost:8000`  
**Production**: `http://localhost:8000` (local application)

## Endpoints

### 1. Health Check Endpoint

#### GET /health

**Description**: Returns service health status for monitoring and availability checks.

**Request**: No request body required

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "service": "backend-reconciliation-api",
  "version": "1.0.0",
  "timestamp": "2025-06-18T10:30:00Z"
}
```

**Response Schema**:
```yaml
type: object
properties:
  status:
    type: string
    enum: [healthy, unhealthy]
    description: Service health status
  service:
    type: string
    description: Service name identifier
  version:
    type: string
    description: API version
  timestamp:
    type: string
    format: date-time
    description: Current server timestamp
required: [status, service, version, timestamp]
```

**Error Responses**: None (endpoint always returns 200)

**Examples**:

```bash
# Request
curl -X GET http://localhost:8000/health

# Response
{
  "status": "healthy",
  "service": "backend-reconciliation-api",
  "version": "1.0.0",
  "timestamp": "2025-06-18T10:30:00Z"
}
```

---

### 2. Reconciliation Processing Endpoint

#### POST /karwai

**Description**: Processes bank reconciliation requests by accepting uploaded files and column mapping configuration, then returning reconciliation results.

**Request**: `multipart/form-data`

**Form Data Fields**:

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `bankStatement` | File | Yes | PDF bank statement file (max 10MB) |
| `companyData` | File | Yes | Excel company data file (max 5MB) |
| `formatType` | string | Yes | Column mapping format type |
| `transactionDateColumn` | string | Yes | Column name for transaction dates |
| `transactionDetailsColumn` | string | Yes | Column name for transaction details |
| `debitPlusCreditColumn` | string | Conditional* | Combined debit/credit column (for debit-plus-credit format) |
| `debitColumn` | string | Conditional* | Debit column name (for debit-pipe-credit format) |
| `creditColumn` | string | Conditional* | Credit column name (for debit-pipe-credit format) |

**Conditional Fields**:
- For `formatType = "debit-plus-credit"`: `debitPlusCreditColumn` is required
- For `formatType = "debit-pipe-credit"`: `debitColumn` and `creditColumn` are required

**File Constraints**:
- `bankStatement`: PDF file, max size 10MB (10,485,760 bytes)
- `companyData`: Excel file (.xls, .xlsx), max size 5MB (5,242,880 bytes)

**Response**: `200 OK`

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_status": "completed",
  "processing_timestamp": "2025-06-18T10:35:00Z",
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
        "amount": 1500.00,
        "type": "credit"
      },
      "company_transaction": {
        "transaction_id": "company_001",
        "date": "2025-06-15",
        "description": "Client Payment - ABC Corp",
        "amount": 1500.00,
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
        "amount": -250.00,
        "type": "debit"
      },
      "possible_matches": []
    }
  ]
}
```

**Response Schema**:
```yaml
type: object
properties:
  request_id:
    type: string
    format: uuid
    description: Unique identifier for the processing request
  processing_status:
    type: string
    enum: [completed, partial_success, failed]
    description: Overall processing status
  processing_timestamp:
    type: string
    format: date-time
    description: When processing was completed
  summary:
    type: object
    properties:
      total_bank_transactions:
        type: integer
        description: Total transactions extracted from bank statement
      total_company_transactions:
        type: integer
        description: Total transactions extracted from company data
      matched_transactions:
        type: integer
        description: Number of successfully matched transactions
      discrepancies:
        type: integer
        description: Number of unmatched/discrepant transactions
      processing_duration_ms:
        type: integer
        description: Processing time in milliseconds
    required: [total_bank_transactions, total_company_transactions, matched_transactions, discrepancies, processing_duration_ms]
  results:
    type: array
    items:
      oneOf:
        - $ref: '#/components/schemas/MatchResult'
        - $ref: '#/components/schemas/DiscrepancyResult'
    description: List of reconciliation results (matches and discrepancies)
required: [request_id, processing_status, processing_timestamp, summary, results]
```

**Match Result Schema**:
```yaml
MatchResult:
  type: object
  properties:
    type:
      type: string
      enum: [match]
    match_id:
      type: string
      description: Unique identifier for this match
    confidence:
      type: number
      format: float
      minimum: 0.0
      maximum: 1.0
      description: Confidence score for the match
    bank_transaction:
      type: object
      properties:
        transaction_id:
          type: string
        date:
          type: string
          format: date
        description:
          type: string
        amount:
          type: number
          format: decimal
        type:
          type: string
          enum: [credit, debit]
      required: [transaction_id, date, description, amount, type]
    company_transaction:
      type: object
      properties:
        transaction_id:
          type: string
        date:
          type: string
          format: date
        description:
          type: string
        amount:
          type: number
          format: decimal
        type:
          type: string
          enum: [credit, debit]
      required: [transaction_id, date, description, amount, type]
  required: [type, match_id, confidence, bank_transaction, company_transaction]
```

**Discrepancy Result Schema**:
```yaml
DiscrepancyResult:
  type: object
  properties:
    type:
      type: string
      enum: [discrepancy]
    discrepancy_id:
      type: string
      description: Unique identifier for this discrepancy
    source:
      type: string
      enum: [bank, company]
      description: Which file the discrepancy is from
    discrepancy_type:
      type: string
      enum: [unmatched, amount_mismatch, date_mismatch, duplicate]
      description: Type of discrepancy
    transaction:
      type: object
      properties:
        transaction_id:
          type: string
        date:
          type: string
          format: date
        description:
          type: string
        amount:
          type: number
          format: decimal
        type:
          type: string
          enum: [credit, debit]
      required: [transaction_id, date, description, amount, type]
    possible_matches:
      type: array
      items:
        type: object
        properties:
          transaction_id:
            type: string
          confidence:
            type: number
            format: float
          reason:
            type: string
        required: [transaction_id, confidence, reason]
      description: Potential matches if any
  required: [type, discrepancy_id, source, discrepancy_type, transaction, possible_matches]
```

**Error Responses**:

**400 Bad Request** - Invalid input data:
```json
{
  "error": "bad_request",
  "message": "Invalid request data",
  "details": {
    "format_type": "Invalid format type. Must be 'debit-plus-credit' or 'debit-pipe-credit'"
  }
}
```

**413 Payload Too Large** - File size exceeded:
```json
{
  "error": "file_too_large",
  "message": "File size exceeds maximum allowed size",
  "details": {
    "field": "bankStatement",
    "max_size_mb": 10,
    "actual_size_mb": 12.5
  }
}
```

**422 Unprocessable Entity** - File validation failed:
```json
{
  "error": "invalid_file",
  "message": "File validation failed",
  "details": {
    "field": "bankStatement",
    "reason": "Uploaded file is not a valid PDF file"
  }
}
```

**500 Internal Server Error** - Processing error:
```json
{
  "error": "processing_error",
  "message": "Error processing files",
  "details": {
    "error_type": "PDFExtractionError",
    "error_message": "Failed to extract tables from PDF file"
  }
}
```

**504 Gateway Timeout** - Processing timeout:
```json
{
  "error": "timeout",
  "message": "Processing exceeded maximum time limit",
  "details": {
    "max_duration_seconds": 30,
    "actual_duration_seconds": 32
  }
}
```

**Examples**:

```bash
# Example 1: debit-plus-credit format
curl -X POST http://localhost:8000/karwai \
  -F "bankStatement=@bank_statement.pdf" \
  -F "companyData=@company_data.xlsx" \
  -F "formatType=debit-plus-credit" \
  -F "transactionDateColumn=Date" \
  -F "debitPlusCreditColumn=Amount" \
  -F "transactionDetailsColumn=Description"

# Example 2: debit-pipe-credit format  
curl -X POST http://localhost:8000/karwai \
  -F "bankStatement=@bank_statement.pdf" \
  -F "companyData=@company_data.xlsx" \
  -F "formatType=debit-pipe-credit" \
  -F "transactionDateColumn=Transaction Date" \
  -F "debitColumn=Debit" \
  -F "creditColumn=Credit" \
  -F "transactionDetailsColumn=Details"
```

---

## Common Components

### Error Response Schema
```yaml
ErrorResponse:
  type: object
  properties:
    error:
      type: string
      description: Error code identifier
    message:
      type: string
      description: Human-readable error message
    details:
      type: object
      description: Additional error details
      additionalProperties: true
  required: [error, message]
```

### Format Type Enum
```yaml
FormatType:
  type: string
  enum: [debit-plus-credit, debit-pipe-credit]
  description:
    debit-plus-credit: Combined debit/credit column format
    debit-pipe-credit: Separate debit and credit columns format
```

### Transaction Type Enum
```yaml
TransactionType:
  type: string
  enum: [credit, debit]
  description:
    credit: Money coming into the account (positive amount)
    debit: Money going out of the account (negative amount)
```

---

## HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request processed successfully |
| 400 | Bad Request | Invalid input data or missing required fields |
| 413 | Payload Too Large | File size exceeds maximum limits |
| 422 | Unprocessable Entity | File validation failed or invalid configuration |
| 500 | Internal Server Error | Server error during processing |
| 503 | Service Unavailable | Service is temporarily unavailable |
| 504 | Gateway Timeout | Processing exceeded time limit |

---

## Performance Requirements

- **Health Check**: Must respond within 500ms
- **Processing**: Must complete within 30 seconds for standard file sizes
- **Concurrent Requests**: Must support 10 concurrent requests without degradation

---

## Rate Limiting

Currently no rate limiting implemented (local application). Future versions may implement rate limiting based on:
- Requests per minute per client
- Concurrent request limits per client
- File upload throughput limits

---

## CORS Policy

For local development with frontend/backend separation:
```yaml
Access-Control-Allow-Origin: "*"
Access-Control-Allow-Methods: "GET, POST, OPTIONS"
Access-Control-Allow-Headers: "Content-Type, Authorization"
Access-Control-Max-Age: "3600"
```

---

## Authentication

Currently no authentication required (local application). Future versions may implement:
- Basic authentication for local access
- API key authentication
- JWT tokens if user management is added

---

## Versioning

Current version: `v1.0.0`

Versioning strategy:
- Major version: Breaking changes to API contract
- Minor version: New features added without breaking changes
- Patch version: Bug fixes and improvements

---

## Testing Endpoints

For development and testing, the following endpoints may be available:

### GET /docs
Interactive API documentation (Swagger UI)

### GET /redoc
Alternative API documentation (ReDoc)

### GET /openapi.json
OpenAPI schema in JSON format

---

## Future Enhancements

Potential future endpoints:
- `POST /karwai/validate` - Validate files without full processing
- `GET /karwai/status/{request_id}` - Check processing status for long-running requests
- `DELETE /karwai/{request_id}` - Cancel processing request
- `POST /karwai/batch` - Batch processing multiple reconciliation requests
- `GET /karwai/history` - Retrieve processing history (if persistence is added)

---

## Integration Examples

### Python Requests
```python
import requests

files = {
    'bankStatement': open('bank_statement.pdf', 'rb'),
    'companyData': open('company_data.xlsx', 'rb')
}

data = {
    'formatType': 'debit-plus-credit',
    'transactionDateColumn': 'Date',
    'debitPlusCreditColumn': 'Amount',
    'transactionDetailsColumn': 'Description'
}

response = requests.post('http://localhost:8000/karwai', files=files, data=data)
results = response.json()
```

### JavaScript Fetch
```javascript
const formData = new FormData();
formData.append('bankStatement', fileInput1.files[0]);
formData.append('companyData', fileInput2.files[0]);
formData.append('formatType', 'debit-plus-credit');
formData.append('transactionDateColumn', 'Date');
formData.append('debitPlusCreditColumn', 'Amount');
formData.append('transactionDetailsColumn', 'Description');

fetch('http://localhost:8000/karwai', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Monitoring and Logging

All requests should be logged with:
- Timestamp
- Client IP (if available)
- Request ID
- Processing status
- Processing duration
- Error details (if applicable)

Monitoring metrics:
- Request success rate
- Average processing duration
- Error rate by type
- Active concurrent requests