# Consistency Patterns & Data Points

**Purpose**: Document crucial consistency patterns, data points, and alignment requirements across the entire application (frontend, backend, and integration layers).

**Last Updated**: 2025-06-23  
**Status**: Active Living Document

---

## 🔴 Critical Consistency Requirements

### 1. File Upload Constraints

**Status**: ✅ **ALIGNED** (Updated 2025-06-19)

#### Frontend Configuration (`frontend/src/lib/constants.ts`)
```typescript
FILE_VALIDATION = {
  MAX_FILE_SIZE: 50 * 1024 * 1024,  // 50MB (both PDF and Excel)
  WARNING_FILE_SIZE: 10 * 1024 * 1024,  // 10MB warning threshold
}
```

#### Backend Configuration (`backend/src/config.py`)
```python
MAX_PDF_SIZE: int = 50 * 1024 * 1024  # 50MB (must match frontend)
MAX_EXCEL_SIZE: int = 50 * 1024 * 1024  # 50MB (must match frontend)
WARNING_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB (must match frontend)
```

#### Consistency Rules
- ✅ **Both PDF and Excel files**: 50MB maximum
- ✅ **Warning threshold**: 10MB (both frontend and backend)
- ✅ **Validation error messages**: Must use consistent language
- ❌ **DO NOT**: Set different limits for PDF vs Excel (frontend treats both equally)

#### Integration Test Points
```bash
# Test file upload with exactly 50MB file
# Test file upload with 10MB + 1 byte (should warn but allow)
# Test file upload with 50MB + 1 byte (should reject)
```

---

### 2. File Type Validation

#### Frontend Allowed Types
```typescript
BANK_STATEMENT_TYPES: ['application/pdf']
COMPANY_DATA_TYPES: [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel'
]
```

#### Backend Allowed Types
```python
ALLOWED_PDF_TYPES: list = ["application/pdf"]
ALLOWED_EXCEL_TYPES: list = [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]
```

#### Consistency Rules
- ✅ **MIME types**: Must match exactly between frontend and backend
- ✅ **File extensions**: Frontend accepts `.pdf`, `.xlsx`, `.xls`
- ❌ **DO NOT**: Accept types in backend that frontend rejects

---

### 2.5 Automatic File Deletion Requirements

**Status**: ✅ **CRITICAL SECURITY REQUIREMENT** (Updated 2025-06-19)

#### File Cleanup Scenarios

Files MUST be automatically deleted in ALL of the following scenarios:

##### 1. Successful Processing Completion
```python
# After reconciliation processing completes successfully
# Delete both PDF and Excel files immediately
delete_uploaded_files(request_id)
```

##### 2. Processing Error/Failure
```python
# If any error occurs during processing
# Delete files as part of error cleanup
try:
    result = process_files(bank_file, company_file)
except Exception as e:
    delete_uploaded_files(request_id)  # Cleanup on error
    raise
```

##### 3. Backend Function Failure
```python
# If backend function crashes or fails during processing
# Use try-finally or context managers for cleanup
try:
    process_reconciliation(request)
finally:
    delete_uploaded_files(request_id)  # Always cleanup
```

##### 4. Backend Shutdown
```python
# On graceful shutdown (SIGTERM/SIGINT)
# Clean up all uploaded files
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # Application running
    # Shutdown: Delete all files in uploads directory
    cleanup_all_files()
```

##### 5. Time-Based Expiration (20 minutes)
```python
# Delete files 20 minutes after upload
# Regardless of processing status
FILE_RETENTION_MINUTES: int = 20  # 20 minutes
```

#### Configuration Requirements

##### Frontend Configuration (`frontend/src/lib/constants.ts`)
```typescript
// Currently no file retention configuration in frontend
// Backend handles all file cleanup
```

##### Backend Configuration (`backend/src/config.py`)
```python
# File retention time: 20 minutes (updated from 1 hour)
FILE_RETENTION_MINUTES: int = 20
MAX_FILE_RETENTION_SECONDS: int = 20 * 60  # 1200 seconds
```

#### Implementation Requirements

##### Automatic Cleanup Strategy
```python
# 1. Immediate cleanup after processing (success or failure)
async def process_with_guaranteed_cleanup(files: List[UploadedFile]):
    request_id = generate_request_id()
    try:
        # Process files
        result = await process_reconciliation(files, request_id)
        return result
    finally:
        # GUARANTEED cleanup: Always delete files
        await delete_files_by_request_id(request_id)

# 2. Time-based cleanup for orphaned files
# Run every 5 minutes to clean files older than 20 minutes
@repeat_every(seconds=300)  # 5 minutes
async def periodic_cleanup():
    cleanup_files_older_than(minutes=20)

# 3. Shutdown cleanup
async def cleanup_on_shutdown():
    delete_all_files_in_upload_directory()
```

#### Consistency Rules
- ✅ **Immediate cleanup**: Delete files immediately after processing (success or failure)
- ✅ **20-minute timeout**: Delete files 20 minutes after upload as failsafe
- ✅ **Shutdown cleanup**: Delete all files when backend shuts down
- ✅ **Error cleanup**: Delete files on any processing error
- ❌ **DO NOT**: Keep files longer than 20 minutes under any circumstances

#### Integration Test Scenarios
```bash
# Test 1: Successful processing → files deleted immediately
# Test 2: Processing error → files deleted in cleanup
# Test 3: Backend crash → files deleted on restart
# Test 4: Normal shutdown → all files deleted
# Test 5: 20-minute timeout → files auto-deleted
# Test 6: Orphaned files → periodic cleanup catches them
```

---

### 3. API Endpoint Contracts

#### Health Check Endpoint

**Frontend expects**:
```typescript
GET /health
// Returns: { status, service, version, timestamp }
```

**Backend provides**:
```python
@app.get("/health")
// Returns: { status, service, version, timestamp }
```

#### Consistency Rules
- ✅ **Response time**: Must respond within 500ms (requirement)
- ✅ **Response structure**: Exact field name matching
- ❌ **DO NOT**: Change field names (camelCase vs snake_case must match)

---

### 4. Reconciliation Processing Endpoint

#### Frontend Submit Format (`frontend/src/components/upload/UploadForm.tsx`)
```typescript
POST /karwai
Content-Type: multipart/form-data

Fields:
- bankStatement: File (PDF)
- companyData: File (Excel)
- formatType: "debit-plus-credit" | "debit-pipe-credit"
- sheetName: string (default: "Sheet1") - Excel worksheet name
- transactionDateColumn: string
- transactionDetailsColumn: string
- debitPlusCreditColumn: string (if formatType === "debit-plus-credit")
- debitColumn: string (if formatType === "debit-pipe-credit")
- creditColumn: string (if formatType === "debit-pipe-credit")
```

#### Backend Expected Format (`backend/src/api/routes.py`)
```python
POST /karwai
Content-Type: multipart/form-data

Expected fields:
- bankStatement: UploadFile (PDF)
- companyData: UploadFile (Excel)
- formatType: str ("debit-plus-credit" | "debit-pipe-credit")
- sheetName: str (default: "Sheet1") - Excel worksheet name
- transactionDateColumn: str
- transactionDetailsColumn: str
- debitPlusCreditColumn: str (conditional)
- debitColumn: str (conditional)
- creditColumn: str (conditional)
```

#### Consistency Rules
- ✅ **Field names**: Must match exactly (case-sensitive)
- ✅ **Format type values**: Must use exact strings from frontend
- ✅ **Conditional fields**: Backend must handle both format types
- ❌ **DO NOT**: Use different field names (e.g., `bank_statement` vs `bankStatement`)

---

### 5. Response Format Consistency

#### Frontend Expected Response Structure
```typescript
{
  request_id: string,
  processing_status: "completed" | "partial_success" | "failed",
  processing_timestamp: string (ISO 8601),
  summary: {
    total_bank_transactions: number,
    total_company_transactions: number,
    matched_transactions: number,
    discrepancies: number,
    processing_duration_ms: number
  },
  results: Array<{
    type: "match" | "discrepancy",
    // ... additional fields
  }>
}
```

#### Backend Response Structure
```python
{
  "request_id": str,
  "processing_status": Literal["completed", "partial_success", "failed"],
  "processing_timestamp": str (ISO 8601),
  "summary": {
    "total_bank_transactions": int,
    "total_company_transactions": int,
    "matched_transactions": int,
    "discrepancies": int,
    "processing_duration_ms": int
  },
  "results": List[Union[MatchResult, DiscrepancyResult]]
}
```

#### Consistency Rules
- ✅ **Field names**: Exact match (snake_case in JSON)
- ✅ **Enum values**: Must use exact string values
- ✅ **Timestamp format**: ISO 8601 format
- ❌ **DO NOT**: Return different structures or field names

---

### 6. Error Response Consistency

#### Frontend Expected Error Format
```typescript
{
  error: string,
  message: string,
  details?: {
    [key: string]: any
  }
}
```

#### Backend Error Response
```python
{
  "error": str,
  "message": str,
  "details": Optional[Dict[str, Any]]
}
```

#### Consistency Rules
- ✅ **Error codes**: Must match frontend expectations
- ✅ **HTTP status codes**: Must align with error types
- ✅ **Error messages**: User-friendly and actionable
- ❌ **DO NOT**: Expose internal implementation details in error messages

---

## 🔵 Performance Requirements Consistency

### Processing Time Constraints

**Requirement**: Both frontend and backend must respect 30-second processing limit

#### Frontend Behavior
```typescript
// Frontend should show loading state
// Should handle timeout gracefully
// Should provide user feedback during processing
```

#### Backend Behavior
```python
MAX_PROCESSING_TIME: int = 30  // seconds
// Backend must enforce this limit
// Must return proper timeout error if exceeded
```

#### Consistency Rules
- ✅ **Timeout value**: 30 seconds (both sides)
- ✅ **Error handling**: Both sides handle timeout gracefully
- ❌ **DO NOT**: Allow indefinite processing

---

### Concurrent Request Handling

**Requirement**: System must support 10 concurrent requests

#### Configuration
```python
MAX_CONCURRENT_REQUESTS: int = 10
```

#### Consistency Rules
- ✅ **Rate limiting**: Implement if exceeded
- ✅ **Resource management**: Prevent system overload
- ❌ **DO NOT**: Allow unlimited concurrent requests

---

### PDF Processing Capabilities

**Status**: ✅ **FULLY FUNCTIONAL** (Updated 2025-06-23)

#### Multi-Page PDF Processing
```python
# PDF processor handles continuation pages (page 2+) automatically
# Uses area extraction fallback for page breaks
# Implements proper deduplication across all pages
```

#### Performance Benchmarks
- **Small PDFs (<5 pages)**: 3-5 seconds processing time
- **Medium PDFs (5-15 pages)**: 5-10 seconds processing time
- **Large PDFs (15+ pages)**: 7-15 seconds processing time

#### Test Results (2025-06-23)
```bash
# Actual performance from production testing:
PDF: 26 bank statements extracted in 7.1 seconds
Excel: 20 company records extracted in 191 milliseconds
Total: 7.1 seconds for complete reconciliation
```

#### PDF Processing Features
- ✅ **Multi-page extraction**: Handles PDFs with multiple pages
- ✅ **Continuation page detection**: Automatic page break handling
- ✅ **Transaction deduplication**: Removes duplicate entries across pages
- ✅ **Sign detection**: Proper negative (debit) and positive (credit) amounts
- ✅ **Branch/narrative extraction**: Parses merged transaction details

#### Consistency Rules
- ✅ **Processing time**: Must complete within 30 seconds
- ✅ **Accuracy**: Must extract all transactions from all pages
- ✅ **Sign handling**: Debits must be negative, credits must be positive
- ❌ **DO NOT**: Skip pages or truncate transactions

---

---

## 🟢 Data Format Consistency

### Processing Status Enum

**Requirement**: Processing status values must be consistent between frontend and backend

**Enum Values**:
```typescript
// Frontend and Backend must use exact same values:
const ProcessingStatus = {
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
}
```

#### Consistency Rules
- ✅ **Exact strings**: Must match character-for-character
- ✅ **Case sensitivity**: Use lowercase with underscores
- ✅ **Meaning**: Each status has specific semantic meaning
- ❌ **DO NOT**: Add new statuses without updating both sides

#### Status Flow
```
RECEIVED → VALIDATING → VALIDATED → PROCESSING → COMPLETED → CLEANING_UP → REMOVED
              ↓            ↓          ↓          ↓
            INVALID      FAILED     ERROR     TIMEOUT
```

---

### Transaction Type Enum

**Requirement**: Transaction types must be consistent

**Enum Values**:
```typescript
const TransactionType = {
  CREDIT = "credit"  // Money coming into the account (positive amount)
  DEBIT = "debit"    // Money going out of the account (negative amount)
}
```

#### Consistency Rules
- ✅ **Values**: "credit" and "debit" (exact strings)
- ✅ **Amount signs**: Credit = positive, Debit = negative
- ❌ **DO NOT**: Use different transaction type names

---

### Match and Discrepancy Data Structure

**Requirement**: Transaction data must include debit/credit values consistently

#### Match Structure (TransactionMatch)
```typescript
{
  transaction_id: string,
  confidence: number (0.0-1.0),
  bank_transaction: {
    transaction_id: string,
    date: string (YYYY-MM-DD),
    description: string,
    amount: number,          // ✅ REQUIRED: Transaction amount
    debit_amount: number,    // ✅ REQUIRED: Debit amount (if applicable)
    credit_amount: number,   // ✅ REQUIRED: Credit amount (if applicable)
    type: "credit" | "debit"
  },
  company_transaction: {
    transaction_id: string,
    date: string (YYYY-MM-DD),
    description: string,
    amount: number,          // ✅ REQUIRED: Transaction amount
    debit_amount: number,    // ✅ REQUIRED: Debit amount (if applicable)
    credit_amount: number,   // ✅ REQUIRED: Credit amount (if applicable)
    type: "credit" | "debit"
  }
}
```

#### Discrepancy Structure (TransactionDiscrepancy)
```typescript
{
  discrepancy_id: string,
  source: "bank" | "company",
  discrepancy_type: "unmatched" | "amount_mismatch" | "date_mismatch" | "duplicate",
  transaction: {
    transaction_id: string,
    date: string (YYYY-MM-DD),
    description: string,
    amount: number,          // ✅ REQUIRED: Transaction amount
    debit_amount: number,    // ✅ REQUIRED: Debit amount (if applicable)
    credit_amount: number,   // ✅ REQUIRED: Credit amount (if applicable)
    type: "credit" | "debit"
  }
  // ❌ REMOVED: possible_matches field (not required)
}
```

#### Consistency Rules
- ✅ **Amount fields**: Always include amount, debit_amount, credit_amount
- ✅ **Type consistency**: "credit" or "debit" must match amount sign
- ✅ **No possible_matches**: Discrepancy model should not include possible_matches
- ❌ **DO NOT**: Omit debit/credit amount fields from transaction data

---

### Column Mapping Format Types

**Frontend constants**:
```typescript
const FORMAT_OPTIONS = [
  { value: 'debit-plus-credit', label: 'Debit + Credit' },
  { value: 'debit-pipe-credit', label: 'Debit | Credit' }
]
```

**Backend validation**:
```python
ALLOWED_FORMAT_TYPES = ["debit-plus-credit", "debit-pipe-credit"]
```

#### Consistency Rules
- ✅ **Format strings**: Must match exactly
- ✅ **Field counts**: Debit+Credit = 3 fields, Debit|Credit = 4 fields
- ❌ **DO NOT**: Add new format types without updating both sides

---

### Transaction Date Format

**Requirement**: Dates must be consistent across frontend and backend

#### Format
```typescript
// Frontend: ISO 8601 string format
"2025-06-19" (YYYY-MM-DD)
```

```python
# Backend: ISO 8601 string format
"2025-06-19" (YYYY-MM-DD)
```

#### Consistency Rules
- ✅ **Date format**: ISO 8601 (YYYY-MM-DD)
- ✅ **Time zone**: UTC or explicitly specified
- ❌ **DO NOT**: Use locale-specific date formats

---

## 🟡 Validation Consistency

### Field Validation Rules

#### Common Validation Pattern
```typescript
// Frontend validation (validation.ts)
export function validateTextField(value: string): { isValid: boolean; error?: string }
```

```python
# Backend validation (validators.py)
def validate_text_field(value: str) -> ValidationResult
```

#### Consistency Rules
- ✅ **Validation logic**: Same rules on both sides
- ✅ **Error messages**: Consistent language
- ✅ **Field length limits**: Match on both sides (max 100 chars for column names)
- ❌ **DO NOT**: Allow backend to accept what frontend rejects

---

## 🟠 CORS and Security Consistency

### CORS Configuration

#### Frontend Expectations
```typescript
// Frontend runs on: http://localhost:3000
// Backend runs on: http://localhost:8000
```

#### Backend CORS Settings
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  // Must match frontend origin
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

#### Consistency Rules
- ✅ **Allowed origins**: Must match frontend URL
- ✅ **Allowed methods**: Must include all frontend HTTP methods
- ❌ **DO NOT**: Use wildcard origins in production

---

## 🔵 Testing Consistency

### Integration Test Scenarios

#### File Upload Flow
```bash
# Test 1: Valid small files (< 10MB)
# Expected: Success, no warnings

# Test 2: Medium files (10MB - 50MB)
# Expected: Success with warnings

# Test 3: Large files (> 50MB)
# Expected: Rejection with error

# Test 4: Invalid file types
# Expected: Rejection with specific error
```

#### Reconciliation Processing
```bash
# Test 1: debit-plus-credit format
# Expected: Successful processing

# Test 2: debit-pipe-credit format
# Expected: Successful processing

# Test 3: Missing required columns
# Expected: Clear error message
```

---

## 📋 Consistency Checklist

### Before Deploying Changes

- [ ] **File size limits**: Frontend and backend match
- [ ] **MIME types**: Both sides accept same types
- [ ] **API contracts**: Request/response formats match
- [ ] **Error codes**: Consistent across both sides
- [ ] **Field names**: Exact match (case-sensitive)
- [ ] **Validation rules**: Same logic on both sides
- [ ] **Performance limits**: Timeout values match
- [ ] **CORS settings**: Origins and methods aligned
- [ ] **Date formats**: ISO 8601 across both sides
- [ ] **Enum values**: Exact string matches

### When Adding New Features

1. **Frontend changes**: Update backend to match
2. **Backend changes**: Update frontend to match
3. **API changes**: Update this document
4. **Validation changes**: Sync both sides
5. **Performance changes**: Update limits consistently

---

## 🚨 Common Consistency Issues

### Issue 1: Field Name Mismatches
**Problem**: Frontend uses `bankStatement`, backend expects `bank_statement`  
**Solution**: Use exact field names (case-sensitive)  
**Prevention**: API contract testing

### Issue 2: File Size Limit Mismatches  
**Problem**: Frontend allows 50MB, backend only 10MB  
**Solution**: Keep file size limits in sync (see above)  
**Prevention**: Integration tests with boundary files

### Issue 3: Response Format Differences
**Problem**: Backend returns `processingStatus`, frontend expects `processing_status`  
**Solution**: Use consistent naming conventions (snake_case in JSON)  
**Prevention**: Contract tests and API documentation

### Issue 4: Validation Rule Differences
**Problem**: Frontend allows 100-char column names, backend only 50  
**Solution**: Keep validation logic identical  
**Prevention**: Shared validation constants

---

## 📊 Version History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-06-23 | 1.1.0 | Added PDF processing capabilities, sheetName parameter, performance benchmarks | System |
| 2025-06-19 | 1.0.0 | Initial document with file size consistency pattern | System |

---

## 🔄 Maintenance Process

### Weekly Review
- Check for new consistency patterns
- Update any changed requirements
- Verify no drift between frontend/backend

### Monthly Audit
- Complete consistency check
- Update all test scenarios
- Review integration test results

### On Major Changes
- Update relevant section immediately
- Run full integration test suite
- Update version history

---

**وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ**