# Feature Specification: PDF and Excel File Processing for Bank Reconciliation

**Feature Branch**: `001-pdf-xlsx-processing`  
**Created**: 2025-06-19  
**Status**: Draft  
**Input**: User description: "This specification deals with the establishment of PDF processing with a tabular-py in the API service and processing of xlsx file with pandas. 2 files pdf and xlsx file will be received at the karwai POST Endpoint in backend FastAPI. The files will be stored locally and file processing that is already established in Backend directory will be applied. Installing pandas and tabula-py and asynchronously processing both files simultaneously."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bank Statement Processing (Priority: P1)

Finance accountants need to upload PDF bank statements that are automatically processed to extract transaction data in a structured format. The system must parse complex PDF layouts where columns are not easily identifiable by standard tools, using professional PDF parsing to accurately extract transaction dates, descriptions, and amounts.

**Why this priority**: This is the core function that enables automated bank reconciliation. Without PDF processing, users cannot extract transaction data from bank statements, making the entire reconciliation system non-functional.

**Independent Test**: Can be fully tested by uploading a sample PDF bank statement and verifying that transaction data (dates, descriptions, amounts) is correctly extracted and returned in a structured format with proper debit/credit sign handling.

**Acceptance Scenarios**:

1. **Given** a valid PDF bank statement file, **When** uploaded via the karwai endpoint, **Then** the system extracts transaction dates, details, and amounts into a standardized format
2. **Given** a PDF with multiple pages, **When** processed, **Then** all transactions across all pages are extracted and combined
3. **Given** a PDF with non-standard column layouts, **When** processed, **Then** the system correctly identifies Tran. Date, Transaction Details, Debit, and Credit columns using positional mapping
4. **Given** extracted debit and credit values, **When** processed, **Then** debit values are stored as positive integers and credit values as negative integers in a combined Debit/Credit field

---

### User Story 2 - Company Record Processing (Priority: P1)

Finance accountants need to upload Excel company records that are automatically processed using column name mapping provided by the user. Since company Excel files have non-standard formats and varying column names, users provide the exact column names for transaction dates, amounts, and descriptions, enabling the system to accurately extract data regardless of file format variations.

**Why this priority**: This is equally critical as PDF processing. Without Excel processing, the system cannot access company transaction data for comparison with bank statements, making reconciliation impossible.

**Independent Test**: Can be fully tested by uploading a sample Excel file with column name parameters and verifying that the correct columns are identified and data is extracted with proper debit/credit handling.

**Acceptance Scenarios**:

1. **Given** a valid Excel company file with 3-column format (date, combined amount, description), **When** uploaded with column names provided, **Then** the system locates the specified columns and extracts transaction data
2. **Given** a valid Excel company file with 4-column format (date, separate debit, separate credit, description), **When** uploaded with column names provided, **Then** the system locates the specified columns and merges debit/credit into a single field with proper sign handling
3. **Given** extracted debit and credit values from separate columns, **When** processed, **Then** debit values are stored as positive integers and credit values as negative integers in a combined Debit/Credit field
4. **Given** an Excel file with varying column names, **When** processed with user-provided column names, **Then** the system correctly identifies and extracts data from the specified columns regardless of their position or naming convention

---

### User Story 3 - Simultaneous Processing (Priority: P2)

Finance accountants need both PDF bank statements and Excel company records to be processed simultaneously to minimize wait time. The system should process both files concurrently rather than sequentially, reducing total processing time and improving user experience.

**Why this priority**: While not as critical as the core processing functionality, simultaneous processing significantly improves efficiency. If this fails, the system still works but processes files sequentially, increasing wait time.

**Independent Test**: Can be tested by uploading both files simultaneously and measuring that processing completes faster than sequential processing would allow, with both datasets returned together.

**Acceptance Scenarios**:

1. **Given** both PDF and Excel files uploaded together, **When** processing starts, **Then** both files are processed concurrently using asynchronous operations
2. **Given** concurrent processing, **When** one file processing completes before the other, **Then** the system waits for both to complete before returning results
3. **Given** simultaneous processing, **When** both files complete, **Then** the system returns both processed datasets together in the response

---

### User Story 4 - Standardized Output Format (Priority: P2)

The system must return processed data from both PDF and Excel sources in an identical, standardized format to enable downstream comparison logic. Both datasets should have the same structure (Transaction_date, Transaction Detail, Debit/Credit) regardless of their original source format.

**Why this priority**: Essential for the reconciliation phase. Without standardization, the comparison logic cannot match transactions between bank statements and company records.

**Independent Test**: Can be tested by processing both file types and verifying that the output structures are identical and contain the same field names and data types.

**Acceptance Scenarios**:

1. **Given** processed PDF bank statement data, **When** returned, **Then** it contains Transaction_date, Transaction Detail, and Debit/Credit fields with appropriate data types
2. **Given** processed Excel company data, **When** returned, **Then** it contains Transaction_date, Transaction Detail, and Debit/Credit fields with appropriate data types
3. **Given** both processed datasets, **When** compared, **Then** they have identical structure and field names, enabling direct transaction comparison

---

### Edge Cases

- What happens when PDF file is password-protected or corrupted?
- How does system handle Excel files with missing or empty rows in the specified columns?
- What happens when user-provided column names don't match any columns in the Excel file?
- How does system handle PDF files where the expected transaction table cannot be found or parsed?
- What happens when debit or credit values contain non-numeric data or special characters?
- How does system handle files with extremely large numbers of transactions (performance considerations)?
- What happens when date formats vary between PDF and Excel sources?
- How does system handle transactions where debit and credit values are both present or both empty?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept PDF bank statement files via the karwai POST endpoint and store them locally for processing
- **FR-002**: System MUST accept Excel company record files via the karwai POST endpoint and store them locally for processing  
- **FR-003**: System MUST process PDF files using tabula-py library with positional column mapping as defined in test.py implementation
- **FR-004**: System MUST extract four specific columns from PDF files: Tran. Date, Transaction Details, Debit, and Credit
- **FR-005**: System MUST extract transaction data from all pages of multi-page PDF files
- **FR-006**: System MUST process Excel files using pandas library with user-provided column name mappings
- **FR-007**: System MUST accept 3-column format parameters (transactionDateColumn, debitPlusCreditColumn, transactionDetailsColumn) for Excel files
- **FR-008**: System MUST accept 4-column format parameters (transactionDateColumn, debitColumn, creditColumn, transactionDetailsColumn) for Excel files
- **FR-009**: System MUST use user-provided column names to locate and extract specific columns from Excel files regardless of their position
- **FR-010**: System MUST process PDF and Excel files asynchronously and simultaneously
- **FR-011**: System MUST merge separate Debit and Credit columns from PDF into a single Debit/Credit column
- **FR-012**: System MUST merge separate Debit and Credit columns from Excel (when in 4-column format) into a single Debit/Credit column
- **FR-013**: System MUST assign POSITIVE values (+) to debit entries in the Debit/Credit column
- **FR-014**: System MUST assign NEGATIVE values (-) to credit entries in the Debit/Credit column
- **FR-015**: System MUST store Debit/Credit values as integers (not floating point or strings)
- **FR-016**: System MUST return processed PDF data in List[Dict] format with keys: Transaction_date, Transaction Detail, Debit/Credit
- **FR-017**: System MUST return processed Excel data in List[Dict] format with keys: Transaction_date, Transaction Detail, Debit/Credit
- **FR-018**: System MUST ensure both processed datasets have identical structure and field names
- **FR-019**: System MUST validate that extracted transaction dates follow expected format (DD-MMM-YY pattern)
- **FR-020**: System MUST handle and log errors during file processing without crashing the entire request
- **FR-021**: System MUST follow the exact PDF parsing implementation pattern shown in test.py file (canonical column mapping, branch narrative extraction, date pattern validation)

### Key Entities

- **Bank Statement Transaction**: Represents individual financial transactions from PDF bank statements, containing transaction date, description/narrative, and monetary amount (debit or credit). Source: PDF file parsed with tabula-py.

- **Company Record Transaction**: Represents individual financial transactions from Excel company records, containing transaction date, description, and monetary amount (debit or credit). Source: Excel file parsed with pandas. Column mappings are user-provided and vary between companies.

- **Processed Transaction Dataset**: Standardized collection of transactions from either source, formatted as List[Dict] with consistent structure (Transaction_date, Transaction Detail, Debit/Credit) to enable comparison and reconciliation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully process a typical 10-page PDF bank statement with 100+ transactions in under 30 seconds
- **SC-002**: Users can successfully process an Excel company file with 500+ transactions in under 10 seconds  
- **SC-003**: Simultaneous processing of both PDF and Excel files completes in less time than sequential processing (measured performance improvement)
- **SC-004**: 95% of PDF bank statements from major banks are successfully parsed with accurate transaction extraction
- **SC-005**: 100% of Excel files with valid column mappings are successfully processed with accurate data extraction
- **SC-006**: Zero data loss occurs during the debit/credit merging process (all original amounts preserved with correct sign assignment)
- **SC-007**: Processed datasets from both sources have 100% structural consistency (identical field names and data types)
- **SC-008**: System handles malformed or corrupted files gracefully with clear error messages, returning appropriate error status codes
- **SC-009**: Users can successfully process files from 5 different bank formats (demonstrating flexibility of PDF parsing approach)
- **SC-010**: Processing completes successfully for both 3-column and 4-column Excel formats with 100% accuracy in column identification

## Assumptions

- PDF bank statements follow a general tabular structure that can be parsed with tabula-py, even if column headers are unclear
- Excel company files always contain the data columns specified by users, even if column names and positions vary
- Debit and Credit values in both file types are numeric and can be converted to integers
- Transaction dates in PDFs follow a recognizable date pattern that can be validated with regex
- Users will provide accurate column names that exist in their Excel files
- The test.py implementation pattern is the proven approach for PDF processing and should be followed exactly
- Processing will happen on a single server with sufficient resources for concurrent file operations
- Files are uploaded via the existing karwai POST endpoint with the current parameter structure

## Dependencies

- Existing karwai POST endpoint structure and parameter validation
- test.py file containing the working PDF implementation pattern
- pandas and tabula-py libraries already listed in requirements.txt
- Existing upload directory and file handling infrastructure
- Current column mapping validation logic in routes.py
- FastAPI framework for asynchronous processing capabilities