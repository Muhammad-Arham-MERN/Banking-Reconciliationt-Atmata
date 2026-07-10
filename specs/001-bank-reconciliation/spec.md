# Feature Specification: Bank Reconciliation Logic

**Feature Branch**: `001-bank-reconciliation`  
**Created**: 2026-06-23  
**Status**: Draft  
**Input**: User description: "Implement reconciliation logic between bank statements and company records with opposite sign duplicate removal"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Transaction Reconciliation (Priority: P1)

**Scenario**: A finance accountant uploads both a bank statement PDF and company records Excel file. The system processes both files, performs transaction comparison, and displays a unified list of discrepancies showing which transactions exist in one source but not the other.

**User Journey**: 
1. Accountant uploads bank statement (PDF) and company records (Excel)
2. System processes both files concurrently
3. System compares each bank transaction against every company transaction
4. System compares each company transaction against every bank transaction
5. System identifies transactions present in one source but not the other
6. System removes matching opposite-sign transactions (e.g., +22000 in company, -22000 in bank)
7. System displays unified discrepancy list with source attribution

**Why this priority**: This is the core reconciliation functionality that delivers the primary value - automating the tedious manual comparison process that finance professionals currently perform manually.

**Independent Test**: Can be fully tested by uploading sample bank and company files with known discrepancies and verifying the output contains:
- Bank-only transactions marked with FROM:"Bank"
- Company-only transactions marked with FROM:"Company"  
- No opposite sign duplicate pairs present
- All expected discrepancies captured

**Acceptance Scenarios**:

1. **Given** a bank statement with 26 transactions and company records with 20 transactions, **When** both files are uploaded and processed, **Then** the system returns a unified list containing only transactions that don't match between sources, with each transaction marked by its source (FROM:"Bank" or FROM:"Company")

2. **Given** bank transaction of -22000000.0 and company transaction of +22000000.0, **When** reconciliation is performed, **Then** both transactions are removed from the final discrepancy list as they represent the same transaction with opposite signs (matching based on amount only)

3. **Given** a transaction "INWARD CHEQUE" for 10200.0 in bank statement but not in company records, **When** reconciliation is performed, **Then** the transaction appears in the discrepancy list with FROM:"Bank" and all original transaction details preserved

---

### User Story 2 - Performance Optimization for Large Files (Priority: P2)

**Scenario**: Finance department processes monthly statements with hundreds of transactions. The reconciliation completes within 10 seconds regardless of file size, enabling efficient monthly closing processes.

**Why this priority**: Large file processing is critical for real-world usage where monthly statements can contain hundreds of transactions. Slow performance would negate the efficiency gains.

**Independent Test**: Can be tested by uploading files with 100+ transactions each and measuring processing time stays under 10 seconds

**Acceptance Scenarios**:

1. **Given** bank statement with 100 transactions and company records with 80 transactions, **When** reconciliation is performed, **Then** processing completes in under 10 seconds

2. **Given** concurrent processing of both PDF and Excel files, **When** reconciliation is performed, **Then** total processing time is less than the sum of individual processing times

---

### User Story 3 - Data Quality and Validation (Priority: P3)

**Scenario**: System handles various data quality issues including missing fields, malformed dates, invalid amounts, and duplicate entries within the same source file.

**Why this priority**: Real-world financial data often contains quality issues. Graceful handling ensures system reliability and user trust.

**Independent Test**: Can be tested by uploading files with intentional data quality issues and verifying appropriate error messages or handling

**Acceptance Scenarios**:

1. **Given** a transaction with missing date field, **When** reconciliation is performed, **Then** system includes the transaction in discrepancy list with missing field preserved and appropriate flag

2. **Given** duplicate transactions within the same source file, **When** reconciliation is performed, **Then** system treats each instance independently and includes both in appropriate lists

---

### Edge Cases

- What happens when multiple transactions have the same amount but different dates/descriptions?
- How does system handle transactions with the same amount in both sources but same sign (both positive or both negative)?
- What happens when debit/credit signs are inconsistent between sources (e.g., both positive)?
- How does system handle empty transaction lists (one or both sources empty)?
- What happens when transaction details contain special characters or encoding issues?
- How does system handle extremely large monetary values (billions, trillions)?
- What happens when there are multiple transactions with identical opposite amounts in both sources?
- How does system handle transactions with zero amounts (0.0)?
- What happens when Excel file contains multiple sheets with transaction data?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept bank_statement and company_records lists in JSON format with transaction objects containing Transaction_date, Transaction Detail, and Debit/Credit fields

- **FR-002**: System MUST compare each bank transaction amount against every company transaction amount to identify matches based on opposite sign amounts (bank_amount == -company_amount)

- **FR-003**: System MUST identify bank transactions NOT present in company records and add them to discrepancy list with FROM:"Bank" attribute

- **FR-004**: System MUST identify company transactions NOT present in bank statement and add them to discrepancy list with FROM:"Company" attribute

- **FR-005**: System MUST merge both discrepancy lists (bank-only and company-only) into a single unified discrepancy list

- **FR-006**: System MUST remove opposite-sign duplicate transactions (e.g., +22000 in company, -22000 in bank) from the final discrepancy list

- **FR-007**: System MUST preserve all original transaction data (date, description, amount) in the output format, adding only the FROM attribute

- **FR-008**: System MUST handle the comparison deterministically with the same inputs always producing the same outputs

- **FR-009**: System MUST support concurrent processing of bank and company data sources for optimal performance

- **FR-010**: System MUST validate that required fields (Transaction_date, Transaction Detail, Debit/Credit) are present in all transaction objects

- **FR-011**: System MUST handle empty transaction lists by returning appropriate empty results with clear status indicators

- **FR-012**: System MUST maintain transaction order from original sources in the discrepancy lists (bank transactions in bank order, company transactions in company order)

### Key Entities

- **Bank Transaction**: Individual entry from bank statement containing date (Transaction_date), description (Transaction Detail), and amount (Debit/Credit with sign indicating debit/credit)

- **Company Transaction**: Individual entry from company financial records containing date (Transaction_date), description (Transaction Detail), and amount (Debit/Credit with sign indicating debit/credit)

- **Discrepancy Transaction**: Transaction present in one source but not the other, with added FROM attribute indicating source ("Bank" or "Company")

- **Opposite Sign Pair**: Two transactions with opposite signed amounts (e.g., bank: +22000.0, company: -22000.0 or vice versa) representing the same transaction recorded from different perspectives (dates and descriptions are preserved for display but not used for matching)

- **Unified Discrepancy List**: Merged list containing all discrepancy transactions from both sources with opposite sign pairs removed

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Finance professionals can complete reconciliation of 26 bank statements and 20 company records in under 10 seconds

- **SC-002**: System accurately identifies 100% of non-matching transactions between bank and company sources

- **SC-003**: Zero false positives - all transactions in discrepancy list are genuine discrepancies, not opposite sign pairs

- **SC-004**: System handles edge cases (empty files, duplicate transactions, large values) without errors or data loss

- **SC-005**: 95% user confidence in reconciliation results - users trust the system to find all discrepancies without manual verification

- **SC-006**: Reduces manual reconciliation time from 30+ minutes to under 1 minute per monthly statement

---

## Out of Scope *(optional)*

The following items are explicitly excluded from this feature:

- Advanced fuzzy matching for transactions with similar but not identical descriptions
- Automatic correction of data entry errors
- Multi-currency support and exchange rate conversion
- Transaction categorization or tagging beyond source attribution
- Historical trend analysis or reporting
- User authentication and authorization for file uploads
- Email notifications or alerts for discrepancies
- Export of discrepancy reports to different formats (PDF, Excel, etc.)
- Machine learning models for transaction matching suggestions
- Integration with accounting software or ERP systems

---

## Dependencies & Assumptions *(optional)*

### Dependencies
- Existing PDF processing pipeline produces bank_statement data in specified JSON format
- Existing Excel processing pipeline produces company_records data in specified JSON format  
- Frontend file upload interface delivers files to backend karwai endpoint
- Data structure from existing karwai endpoint matches provided example format

### Assumptions
- Transaction dates are in ISO format (YYYY-MM-DD) or compatible with date comparison
- Transaction amounts are numeric (float/decimal) with sign indicating debit (-) or credit (+)
- Transaction descriptions are text strings preserved for display purposes only
- "Match" means opposite sign amounts between bank and company transactions (bank_amount == -company_amount)
- Date and description are display fields only and do not affect matching logic
- Opposite sign amounts represent the same transaction from different perspectives (bank vs company view)
- Users have basic understanding of debit/credit accounting principles
- Files uploaded are legitimate financial statements, not malicious inputs
- Processing happens on-demand per user request, not on a schedule
- System runs in single-user environment on local machine, not multi-tenant cloud deployment

---