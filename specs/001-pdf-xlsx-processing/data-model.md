# Data Model: PDF and Excel File Processing

**Feature**: PDF and Excel File Processing for Bank Reconciliation
**Date**: 2025-06-19
**Status**: Phase 1 Design - Data structures and validation rules

## Overview

This document defines the data entities, structures, and validation rules for the PDF and Excel file processing feature. All data models are designed to support the standardized transaction format required for downstream reconciliation logic.

## Core Entities

### 1. Processed Transaction

**Description**: Standardized transaction record from either PDF bank statements or Excel company records. This is the primary output entity that enables reconciliation comparison.

**Fields**:

| Field Name | Type | Required | Validation | Description |
|------------|------|----------|------------|-------------|
| `Transaction_date` | string (YYYY-MM-DD) | Yes | Valid ISO date format | Normalized transaction date |
| `Transaction Detail` | string | Yes | Non-empty after trimming | Transaction description or narrative |
| `Debit/Credit` | integer | Yes | Non-zero | Monetary amount (positive=debit, negative=credit) |

**Validation Rules**:
- Date must follow ISO 8601 format (YYYY-MM-DD)
- Transaction Detail cannot be empty or whitespace-only
- Debit/Credit must be non-zero integer (no null values allowed)
- Debit/Credit sign indicates transaction type: positive=debit, negative=credit

**Data Format**:
```python
{
    "Transaction_date": "2023-01-15",
    "Transaction Detail": "Payment from ABC Corporation",
    "Debit/Credit": 5000
}
```

**Collection Format**: List[Dict] - List of transaction dictionaries

---

### 2. PDF Bank Statement Transaction

**Description**: Raw transaction data extracted from PDF bank statements before standardization.

**Fields** (from PDF parsing):

| Field Name | Type | Required | Source | Description |
|------------|------|----------|---------|-------------|
| `Tran. Date` | string | Yes | PDF column | Original transaction date (DD-MMM-YY) |
| `Transaction Details` | string | Yes | PDF column | Transaction narrative/details |
| `Debit` | decimal | Yes | PDF column | Debit amount (null if credit) |
| `Credit` | decimal | Yes | PDF column | Credit amount (null if debit) |

**Extraction Rules** (from test.py pattern):
- Use positional column mapping (CANONICAL_COLUMNS)
- Extract branch and narrative from merged "Tran. Narrative" column
- Validate dates with regex: `^\d{2}-[A-Z]{3}-\d{2}$`
- Skip rows that don't match date pattern

**Transformation**:
```python
# Merge Debit/Credit → Debit/Credit
# Debit: positive integer
# Credit: negative integer
# Date: DD-MMM-YY → YYYY-MM-DD
```

---

### 3. Excel Company Record Transaction

**Description**: Raw transaction data extracted from Excel company records before standardization.

**Fields** (3-column format):

| Field Name | Type | Required | Source | Description |
|------------|------|----------|---------|-------------|
| `{transactionDateColumn}` | varies | Yes | User-specified column | Transaction date |
| `{debitPlusCreditColumn}` | varies | Yes | User-specified column | Combined amount column |
| `{transactionDetailsColumn}` | varies | Yes | User-specified column | Transaction description |

**Fields** (4-column format):

| Field Name | Type | Required | Source | Description |
|------------|------|----------|---------|-------------|
| `{transactionDateColumn}` | varies | Yes | User-specified column | Transaction date |
| `{debitColumn}` | varies | Yes | User-specified column | Debit amount (null if credit) |
| `{creditColumn}` | varies | Yes | User-specified column | Credit amount (null if debit) |
| `{transactionDetailsColumn}` | varies | Yes | User-specified column | Transaction description |

**Extraction Rules**:
- Column names provided by user via form parameters
- Locate columns by exact name match (case-sensitive)
- Handle both Excel serial dates and string date formats
- Skip rows with missing critical data

**Transformation**:
```python
# For 4-column format: Merge Debit/Credit → Debit/Credit
# For 3-column format: Direct conversion (already combined)
# Convert to integer (remove decimals)
# Assign sign based on column type
# Normalize date to ISO format
```

---

### 4. Processing Result

**Description**: Aggregated processing result containing standardized transaction datasets and metadata.

**Fields**:

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `bank_statement` | List[Processed Transaction] | Yes | Standardized bank statement transactions |
| `company_records` | List[Processed Transaction] | Yes | Standardized company record transactions |
| `processing_metadata` | Processing Metadata | Yes | Processing statistics and timestamps |

---

### 5. Processing Metadata

**Description**: Metadata about the file processing operation.

**Fields**:

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| `request_id` | string (UUID) | Yes | Unique identifier for processing request |
| `pdf_processing_time_ms` | integer | Yes | Time taken to process PDF (milliseconds) |
| `excel_processing_time_ms` | integer | Yes | Time taken to process Excel (milliseconds) |
| `total_processing_time_ms` | integer | Yes | Total processing time (milliseconds) |
| `bank_transaction_count` | integer | Yes | Number of bank statement transactions extracted |
| `company_transaction_count` | integer | Yes | Number of company record transactions extracted |
| `pdf_filename` | string | Yes | Original PDF filename |
| `excel_filename` | string | Yes | Original Excel filename |
| `processing_timestamp` | string (ISO) | Yes | Timestamp of processing completion |

---

## Relationships

```
PDF Bank Statement (Raw)
    ↓ [extract & transform]
Processed Transaction (Bank)
    ↓ [include in]
Processing Result
    
Excel Company Record (Raw)
    ↓ [extract & transform]
Processed Transaction (Company)
    ↓ [include in]
Processing Result
```

**Key Relationships**:
- One PDF file → Many Processed Transactions (Bank)
- One Excel file → Many Processed Transactions (Company)
- One Processing Result → Two transaction datasets (Bank + Company)

---

## Validation Patterns

### Date Validation

**PDF Date Pattern**:
```python
DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")  # DD-MMM-YY
# Examples: "15-JAN-23", "03-DEC-22"
```

**Excel Date Handling**:
```python
# Excel serial date: Number (e.g., 44927 = 2023-01-15)
# String date: Various formats
# Normalization: All → YYYY-MM-DD
```

**Standardized Date Format**:
```python
ISO_8601 = "%Y-%m-%d"  # YYYY-MM-DD
# Examples: "2023-01-15", "2023-12-03"
```

---

### Amount Validation

**Debit/Credit Rules**:
```python
# Both debit and credit present → ERROR
if debit_value and credit_value:
    raise ValueError("Cannot have both debit and credit")

# Neither present → ERROR
if not debit_value and not credit_value:
    raise ValueError("Must have either debit or credit")

# Sign assignment
debit → POSITIVE (+)
credit → NEGATIVE (-)

# Integer conversion
abs(int(float(value)))  # Remove decimals, prevent sign inversion
```

---

### Text Validation

**Transaction Detail Rules**:
```python
# Cannot be empty or whitespace
if not detail or detail.strip() == "":
    raise ValueError("Transaction detail cannot be empty")

# Trim whitespace
detail = detail.strip()

# Max length (optional)
if len(detail) > 500:
    detail = detail[:500]  # Truncate if too long
```

---

## Error States

### Invalid Data States

1. **Invalid Date Format**: Date string doesn't match expected pattern
2. **Invalid Amount**: Non-numeric value in debit/credit column
3. **Ambiguous Transaction**: Both debit and credit present
4. **Missing Transaction Detail**: Empty or whitespace-only description
5. **Column Not Found**: User-specified column name doesn't exist in Excel
6. **No Transaction Table**: PDF doesn't contain extractable table data

### Error Response Format

```python
{
    "error": "processing_error",
    "message": "User-friendly error description",
    "details": {
        "file_type": "pdf" | "excel",
        "error_type": "invalid_date_format" | "column_not_found" | "no_transactions",
        "row_number": 123,  # If applicable
        "field_name": "Transaction Date",  # If applicable
        "provided_value": "invalid_value",  # If applicable
        "expected_format": "DD-MMM-YY"  # If applicable
    }
}
```

---

## Data Flow

```
File Upload
    ↓
[PDF Processing] ←→ [Excel Processing]  (Concurrent)
    ↓                    ↓
Raw PDF Data        Raw Excel Data
    ↓                    ↓
[Transform & Validate] ←→ [Transform & Validate]
    ↓                    ↓
Processed Transactions (Bank)  Processed Transactions (Company)
    ↓                    ↓
    └──────── [Combine] ────────┘
              ↓
        Processing Result
              ↓
        API Response
```

---

## Summary

**Data Model Characteristics**:
- **Primary Entity**: Processed Transaction (standardized format)
- **Source Entities**: PDF Bank Statement Transaction, Excel Company Record Transaction
- **Output Entity**: Processing Result (aggregated dataset with metadata)
- **Validation**: Comprehensive validation for dates, amounts, and text fields
- **Transformation**: Consistent normalization (dates, amounts, formats)
- **Error Handling**: Clear error states with detailed responses

All data structures support the core requirement: enabling accurate transaction comparison between bank statements and company records for reconciliation.