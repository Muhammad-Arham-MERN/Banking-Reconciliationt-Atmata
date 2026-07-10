# Form Validation Contract: Frontend File Upload Interface

**Feature**: 001-file-upload-ui  
**Date**: 2025-01-17  
**Version**: 1.0

## Contract Overview

This document defines the validation rules, error handling patterns, and form behavior for the frontend file upload interface. All implementations MUST follow these validation rules exactly as specified.

## Validation Rules

### File Upload Validation

#### Bank Statement Upload Zone

**Accept**: Only PDF files  
**Maximum Size**: 50MB (soft limit)  
**Validation Method**: Extension check + MIME type validation

```typescript
// Validation Rules
const BANK_VALIDATION = {
  allowedExtensions: ['.pdf'],
  allowedMimeTypes: ['application/pdf'],
  maxSizeBytes: 50 * 1024 * 1024, // 50MB
  errorMessage: 'Only PDF files are accepted for bank statements'
};
```

**Validation Logic**:
1. Check file extension ends with `.pdf`
2. Check file MIME type is `application/pdf`
3. Check file size < 50MB
4. If all checks pass → Accept file
5. If any check fails → Reject with error message

#### Company Data Upload Zone

**Accept**: Only XLSX files  
**Maximum Size**: 50MB (soft limit)  
**Validation Method**: Extension check + MIME type validation

```typescript
// Validation Rules
const COMPANY_VALIDATION = {
  allowedExtensions: ['.xlsx'],
  allowedMimeTypes: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
  maxSizeBytes: 50 * 1024 * 1024, // 50MB
  errorMessage: 'Only XLSX files are accepted for company data'
};
```

**Validation Logic**:
1. Check file extension ends with `.xlsx`
2. Check file MIME type is Excel MIME type
3. Check file size < 50MB
4. If all checks pass → Accept file
5. If any check fails → Reject with error message

### Format Selection Validation

**Options**: "debit + credit format" or "debit | credit format"  
**Required**: Yes  
**Validation Method**: Dropdown selection check

```typescript
const FORMAT_OPTIONS = [
  'debit + credit format',
  'debit | credit format'
];
```

**Validation Logic**:
1. User MUST select one of the two format options
2. Default state: No format selected
3. After selection: Show conditional fields immediately
4. Format selection can be changed (preserves entered data)

### Column Mapping Field Validation

#### Debit + Credit Format (3 fields required)

**Required Fields**:
1. Transaction Date Column (required, non-empty string)
2. Debit Plus Credit Column (required, non-empty string)
3. Transaction Details Column (required, non-empty string)

```typescript
const DEBIT_PLUS_CREDIT_VALIDATION = {
  transactionDateColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Transaction date column name is required'
  },
  debitPlusCreditColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Debit plus credit column name is required'
  },
  transactionDetailsColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Transaction details column name is required'
  }
};
```

#### Debit | Credit Format (4 fields required)

**Required Fields**:
1. Transaction Date Column (required, non-empty string)
2. Debit Column (required, non-empty string)
3. Credit Column (required, non-empty string)
4. Transaction Details Column (required, non-empty string)

```typescript
const DEBIT_PIPE_CREDIT_VALIDATION = {
  transactionDateColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Transaction date column name is required'
  },
  debitColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Debit column name is required'
  },
  creditColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Credit column name is required'
  },
  transactionDetailsColumn: {
    required: true,
    minLength: 1,
    errorMessage: 'Transaction details column name is required'
  }
};
```

**Field Validation Logic**:
1. All required fields MUST be non-empty strings
2. Minimum length: 1 character
3. No format restrictions (any characters allowed)
4. Trim whitespace before validation
5. Show inline error messages for invalid fields
6. Clear error messages when user corrects field

### Form Submission Validation

**Pre-Submission Checks**:
1. Bank statement file MUST be uploaded and valid
2. Company data file MUST be uploaded and valid
3. Format type MUST be selected
4. All required column mapping fields MUST be filled
5. All validation errors MUST be cleared

```typescript
interface SubmissionValidation {
  canSubmit: boolean;
  errors: string[];
  
  // Check 1: Files uploaded
  bankFileValid: boolean;
  companyFileValid: boolean;
  
  // Check 2: Format selected
  formatSelected: boolean;
  
  // Check 3: Fields complete
  allFieldsComplete: boolean;
}
```

**Submission Logic**:
1. If all pre-submission checks pass → Enable submit button
2. If any check fails → Disable submit button with error message
3. On submit attempt with invalid state → Show validation errors
4. On successful submit → Disable form, show loading state

## Error Handling Patterns

### File Upload Errors

| Error Type | Error Message | User Action |
|------------|---------------|-------------|
| Invalid file type | "Only PDF files are accepted for bank statements" | Upload correct file type |
| File too large | "File size exceeds 50MB limit" | Upload smaller file or compress |
| Corrupted file | "File appears to be corrupted and cannot be processed" | Upload uncorrupted file |
| Network error | "Failed to upload file. Please try again." | Retry upload |

### Field Validation Errors

| Error Type | Error Message | Display Location |
|------------|---------------|------------------|
| Empty required field | "[Field name] is required" | Below the field |
| Invalid input | "Please enter a valid value" | Below the field |

### Submission Errors

| Error Type | Error Message | Display Location |
|------------|---------------|------------------|
| Missing files | "Please upload both bank statement and company data files" | Top of form, inline |
| Incomplete configuration | "Please complete all required column mapping fields" | Top of form, inline |
| Network error | "Submission failed. Please check your connection and try again." | Top of form |
| Server error | "Submission failed. Please try again later." | Top of form |

## Form Behavior Contract

### Drag-and-Drop Behavior

**States**: idle, drag-over, accepted, rejected

```typescript
type DragState = 'idle' | 'drag-over' | 'accepted' | 'rejected';

interface DragBehavior {
  onDragEnter: () => void;    // Change to drag-over state
  onDragLeave: () => void;    // Revert to idle state
  onDrop: (file: File) => void; // Validate and accept/reject
}
```

**Visual Feedback**:
- **Idle**: Default upload zone appearance
- **Drag-over**: Highlight zone with border color change
- **Accepted**: Show file name, size, and success icon
- **Rejected**: Show error message, revert to idle state

### Format Selection Behavior

**State Changes**:
1. User selects format → Conditional fields appear immediately
2. User changes format → Preserve common field values, update UI
3. User clears format → Hide all conditional fields

**Data Preservation**:
- `transactionDateColumn` value preserved when switching formats
- `transactionDetailsColumn` value preserved when switching formats
- Format-specific fields (`debitPlusCreditColumn` vs `debitColumn`/`creditColumn`) cleared when switching

### Submit Button Behavior

**States**: disabled, enabled, loading, success, error

```typescript
type SubmitState = 'disabled' | 'enabled' | 'loading' | 'success' | 'error';

interface SubmitBehavior {
  disabled: boolean;         // true when form invalid
  loading: boolean;           // true during submission
  success: boolean;          // true after successful submission
  error: string | null;      // error message if submission fails
}
```

**State Transitions**:
1. **disabled** → **enabled**: All validation checks pass
2. **enabled** → **loading**: User clicks submit button
3. **loading** → **success**: Backend accepts submission
4. **loading** → **error**: Network or backend error
5. **error** → **enabled**: User fixes issues and retries

## Validation Timing

### Real-Time Validation

**Validated Immediately**:
- File upload on drop/file selection
- Format selection on dropdown change
- Field validation on blur (when user leaves field)

**Validated on Submit Attempt**:
- Complete form validation
- Show all accumulated errors
- Focus first invalid field

### Validation Feedback Timing

| User Action | Validation Feedback | Timing |
|-------------|---------------------|--------|
| Drag file over zone | Visual highlight (drag-over state) | Immediate (<100ms) |
| Drop file | Validate and show result | Immediate (<200ms) |
| Select file via click | Validate and show result | Immediate (<200ms) |
| Change format dropdown | Show/hide conditional fields | Immediate (<100ms) |
| Type in field | Clear field error (if present) | Immediate (<100ms) |
| Leave field (blur) | Validate field and show error if needed | Immediate (<200ms) |
| Click submit | Validate entire form and show errors | Immediate (<300ms) |

## Form Reset Behavior

**Reset Triggers**:
1. Successful submission
2. User manually refreshes page

**Reset Actions**:
1. Clear all file uploads (remove files from state)
2. Reset format selection to default (no selection)
3. Clear all field values
4. Clear all validation errors
5. Reset submit button to disabled state
6. Show success message (if reset after submission)

## Accessibility Requirements

**Keyboard Navigation**:
- Tab key: Navigate between form fields in logical order
- Enter/Space: Activate focused buttons and dropdowns
- Escape: Cancel drag operation or close dropdown

**Screen Reader Support**:
- File upload zones: Label as "Upload bank statement (PDF only)" and "Upload company data (XLSX only)"
- Error messages: Associated with form fields using aria-describedby
- Validation status: Announced to screen readers
- Format dropdown: Label as "Select data format type"

**Visual Indicators**:
- Focus visible on all interactive elements
- Error messages shown with red text and icon
- Success states shown with green indicators
- Drag-over states shown with border highlights

## Performance Requirements

**Validation Performance**:
- File type validation: <50ms
- File size check: <10ms
- Field validation: <20ms per field
- Complete form validation: <200ms

**UI Responsiveness**:
- Drag-over visual feedback: <100ms
- Conditional field show/hide: <100ms
- Error message display: <200ms
- Submit button state change: <100ms

## Contract Compliance

All implementations MUST follow these validation rules exactly. Deviations from this contract constitute a violation of the feature specification and constitutional requirement for "Strict Instruction Following."

**Version Control**:
- This contract is version 1.0
- Changes require explicit Developer approval
- All implementations must reference this contract version
