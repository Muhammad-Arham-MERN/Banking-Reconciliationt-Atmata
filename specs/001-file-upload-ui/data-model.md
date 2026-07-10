# Data Model: Frontend File Upload Interface

**Feature**: 001-file-upload-ui  
**Date**: 2025-01-17  
**Status**: Complete

## Entity Overview

This frontend component manages four primary entities during the form session:

1. **BankStatementFile** - Uploaded PDF bank statement
2. **CompanyDataFile** - Uploaded XLSX company data
3. **ColumnMappingConfiguration** - User's column mapping specification
4. **SubmissionPackage** - Combined package for backend submission

## Entity Definitions

### 1. BankStatementFile

**Description**: Represents the official bank records uploaded by the user. Serves as the source of truth for reconciliation.

**Type**: TypeScript Interface

```typescript
interface BankStatementFile {
  id: string;                    // Unique identifier for the file instance
  file: File;                     // Browser File object (PDF format)
  name: string;                  // File name from file.name
  size: number;                  // File size in bytes
  type: string;                  // MIME type: 'application/pdf'
  uploadedAt: Date;              // Timestamp when file was uploaded
  isValid: boolean;              // Validation status
  validationErrors?: string[];   // Array of error messages if invalid
}
```

**Validation Rules**:
- `type` MUST be 'application/pdf'
- `name` MUST end with '.pdf' extension
- `size` SHOULD be < 50MB (soft limit)
- `file` MUST not be corrupted (readable by PDF parser)

**State Transitions**:
1. EMPTY → UPLOADED (user drops/selects valid PDF)
2. UPLOADED → REJECTED (validation fails)
3. REJECTED → UPLOADED (user replaces with valid file)
4. UPLOADED → REMOVED (user removes file)

### 2. CompanyDataFile

**Description**: Represents the internal financial records from the user's organization in spreadsheet format.

**Type**: TypeScript Interface

```typescript
interface CompanyDataFile {
  id: string;                    // Unique identifier for the file instance
  file: File;                     // Browser File object (XLSX format)
  name: string;                  // File name from file.name
  size: number;                  // File size in bytes
  type: string;                  // MIME type: Excel MIME type
  uploadedAt: Date;              // Timestamp when file was uploaded
  isValid: boolean;              // Validation status
  validationErrors?: string[];   // Array of error messages if invalid
}
```

**Validation Rules**:
- `type` MUST be Excel MIME type (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
- `name` MUST end with '.xlsx' extension
- `size` SHOULD be < 50MB (soft limit)
- `file` MUST not be corrupted (readable by Excel parser)

**State Transitions**:
1. EMPTY → UPLOADED (user drops/selects valid XLSX)
2. UPLOADED → REJECTED (validation fails)
3. REJECTED → UPLOADED (user replaces with valid file)
4. UPLOADED → REMOVED (user removes file)

### 3. ColumnMappingConfiguration

**Description**: Represents the user's specification of how their company data is structured. Enables the system to correctly interpret spreadsheet data.

**Type**: TypeScript Interface with Discriminated Union

```typescript
type FormatType = 'debit-plus-credit' | 'debit-pipe-credit';

interface ColumnMappingConfiguration {
  formatType: FormatType;        // Selected format type
  // Fields for debit+credit format
  debitPlusCreditFields?: {
    transactionDateColumn: string;     // Column name for transaction dates
    debitPlusCreditColumn: string;     // Combined debit/credit column name
    transactionDetailsColumn: string;   // Transaction description/details column
  };
  // Fields for debit|credit format
  debitPipeCreditFields?: {
    transactionDateColumn: string;     // Column name for transaction dates
    debitColumn: string;               // Separate debit column name
    creditColumn: string;              // Separate credit column name
    transactionDetailsColumn: string;  // Transaction description/details column
  };
  isComplete: boolean;            // Whether all required fields are filled
  validationErrors?: Record<string, string>; // Field-specific error messages
}
```

**Validation Rules**:
- `formatType` MUST be one of: 'debit-plus-credit', 'debit-pipe-credit'
- If `formatType === 'debit-plus-credit'`, all `debitPlusCreditFields` MUST be non-empty strings
- If `formatType === 'debit-pipe-credit'`, all `debitPipeCreditFields` MUST be non-empty strings
- Field values SHOULD be valid column names from uploaded spreadsheet (validated on backend)
- Field values MUST be preserved when switching format types

**State Transitions**:
1. UNCONFIGURED → CONFIGURING (user selects format type)
2. CONFIGURING → COMPLETE (all required fields filled)
3. COMPLETE → INCOMPLETE (user clears required field)
4. INCOMPLETE → COMPLETE (user fills missing fields)

### 4. SubmissionPackage

**Description**: Represents the complete collection of files and configuration needed to process a reconciliation request.

**Type**: TypeScript Interface

```typescript
interface SubmissionPackage {
  id: string;                    // Unique submission identifier
  bankStatement: BankStatementFile;
  companyData: CompanyDataFile;
  columnMapping: ColumnMappingConfiguration;
  submittedAt: Date;             // Timestamp of submission
  status: 'pending' | 'uploading' | 'success' | 'error';
  errorMessage?: string;         // Error message if status === 'error'
}
```

**Validation Rules**:
- `bankStatement.isValid` MUST be true
- `companyData.isValid` MUST be true
- `columnMapping.isComplete` MUST be true
- All files MUST be accessible (not revoked by browser)
- Form data MUST be convertible to multipart/form-data

**State Transitions**:
1. PENDING → UPLOADING (user initiates submission)
2. UPLOADING → SUCCESS (backend accepts submission)
3. UPLOADING → ERROR (network error, backend rejection, timeout)
4. ERROR → PENDING (user retries submission)

## Component State Model

### UploadFormState

**Description**: Top-level state managed by the main UploadForm component.

```typescript
interface UploadFormState {
  // File upload states
  bankStatement: BankStatementFile | null;
  companyData: CompanyDataFile | null;
  
  // Column mapping state
  columnMapping: ColumnMappingConfiguration;
  
  // Form interaction states
  isSubmitting: boolean;
  submissionStatus: 'idle' | 'success' | 'error';
  submissionError?: string;
  
  // Drag-and-drop states
  dragOverZone: 'bank' | 'company' | null;
}
```

**State Management Pattern**:
- Use `useReducer` for complex state transitions (format switches, validation)
- Use individual `useState` hooks for simple boolean flags
- Derive validation state from file and configuration states
- Persist field values when switching format types (copy common fields)

## Form Data Flow

### Data Collection Sequence

1. **User uploads bank statement (PDF)**
   - Validate file type and size
   - Create `BankStatementFile` entity
   - Update `bankStatement` state

2. **User uploads company data (XLSX)**
   - Validate file type and size
   - Create `CompanyDataFile` entity
   - Update `companyData` state

3. **User selects format type**
   - Update `columnMapping.formatType`
   - Show appropriate conditional fields

4. **User fills column mapping fields**
   - Validate required fields based on format type
   - Update `columnMapping` state
   - Track field-specific validation errors

5. **User submits form**
   - Validate all entities (both files valid, mapping complete)
   - Create `SubmissionPackage` entity
   - Convert to FormData for backend submission

### FormData Structure

**Final multipart/form-data payload**:

```typescript
const formData = new FormData();
formData.append('bankStatement', bankStatement.file);
formData.append('companyData', companyData.file);
formData.append('formatType', columnMapping.formatType);

if (formatType === 'debit-plus-credit') {
  formData.append('transactionDateColumn', columnMapping.debitPlusCreditFields!.transactionDateColumn);
  formData.append('debitPlusCreditColumn', columnMapping.debitPlusCreditFields!.debitPlusCreditColumn);
  formData.append('transactionDetailsColumn', columnMapping.debitPlusCreditFields!.transactionDetailsColumn);
} else {
  formData.append('transactionDateColumn', columnMapping.debitPipeCreditFields!.transactionDateColumn);
  formData.append('debitColumn', columnMapping.debitPipeCreditFields!.debitColumn);
  formData.append('creditColumn', columnMapping.debitPipeCreditFields!.creditColumn);
  formData.append('transactionDetailsColumn', columnMapping.debitPipeCreditFields!.transactionDetailsColumn);
}
```

## Validation Rules Summary

### Client-Side Validation

| Entity | Validation Rules | Error Handling |
|--------|-----------------|----------------|
| BankStatementFile | PDF format, <50MB, not corrupted | Inline error message, file rejection |
| CompanyDataFile | XLSX format, <50MB, not corrupted | Inline error message, file rejection |
| ColumnMappingConfiguration | All required fields non-empty | Field-specific error messages |
| SubmissionPackage | All files valid, mapping complete | Disable submit button, show errors |

### Backend Validation (Future)

- Column names exist in uploaded spreadsheet
- Files are parseable (PDF readable, XLSX readable)
- File sizes within backend limits
- Format type matches expected values

## Data Persistence

**No client-side persistence required**:
- All data held in browser memory during form session
- Files cleared from memory after submission or page refresh
- No localStorage or sessionStorage needed
- Backend will handle permanent storage and processing

**Session lifecycle**:
1. User opens page → Empty form state
2. User uploads files and fills fields → State held in memory
3. User submits → FormData sent to backend
4. Success/error response → Form reset or error display
5. User refreshes page → All state cleared (fresh form)
