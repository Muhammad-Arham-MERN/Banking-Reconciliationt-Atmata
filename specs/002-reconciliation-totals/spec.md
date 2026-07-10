# Feature Specification: Reconciliation Totals & Verification

**Feature Branch**: `002-reconciliation-totals`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: "A new feature to implement bank reconciliation totals — extract Balance (last item from bank statement PDF) and Aggregated Total (last item from XLSX), display as Bank Net Total and Company Net Total, apply discrepancy adjustments, auto-subtract to show reconciliation success or failure."

## User Scenarios & Testing

### User Story 1 - Run Full Reconciliation with Totals and Verification (Priority: P1)

A user uploads a bank statement (PDF) and company records (XLSX), maps the columns (date, details, debit, credit), and also provides the "Aggregated Total" column name from the XLSX. The system extracts the last Balance value from the bank statement PDF and the last Aggregated Total value from the XLSX. After discrepancies are identified, the user sees both totals, their adjusted values, and an automatic verification of whether the books are balanced.

**Why this priority**: This is the primary value of the feature — giving users a complete reconciliation outcome with a clear pass/fail verdict.

**Independent Test**: Can be tested by uploading a bank statement PDF and an XLSX with known last-row Balance and Aggregated Total values, applying known discrepancy amounts, and verifying the displayed adjusted totals and reconciliation verdict match manual calculation.

**Acceptance Scenarios**:

1. **Given** a bank statement PDF with a Balance column and an XLSX with an Aggregated Total column, **When** the user completes the column mapping step and submits for processing, **Then** the system extracts the last Balance value and the last Aggregated Total value and displays them as "Bank Net Total" and "Company Net Total" respectively.
2. **Given** a successful processing with known discrepancy amounts, **When** the results page loads, **Then** the "Uncleared checks" and "Unpresented checks" amounts are added to the Bank Net Total and displayed as "Adjusted Bank Total".
3. **Given** a successful processing with known discrepancy amounts, **When** the results page loads, **Then** the "Bank Debited But not credited in cashbook" and "Bank credited but not debited in cashbook" amounts are added to the Company Net Total and displayed as "Adjusted Company Total".
4. **Given** both adjusted totals are calculated, **When** the page renders, **Then** the system automatically subtracts the adjusted totals, and if the result is zero, displays "Reconciliation Successful, Balanced".
5. **Given** both adjusted totals are calculated and are not equal, **When** the page renders, **Then** the system displays the difference with a message indicating the books are not balanced.

---

### User Story 2 - Handle Missing or Invalid Data Gracefully (Priority: P2)

A user uploads files where the Balance column or Aggregated Total column has missing values, non-numeric entries, or fewer than expected rows. The system handles these cases gracefully, notifying the user without crashing.

**Why this priority**: Robust error handling ensures users get useful feedback rather than cryptic failures.

**Independent Test**: Can be tested by uploading files with intentionally missing or invalid data in the last row of the Balance and Aggregated Total columns.

**Acceptance Scenarios**:

1. **Given** the last row of the Balance column has a non-numeric or empty value, **When** processing completes, **Then** the system displays a clear error message indicating the Balance value could not be determined.
2. **Given** the last row of the Aggregated Total column has a non-numeric or empty value, **When** processing completes, **Then** the system displays a clear error message indicating the Aggregated Total could not be determined.
3. **Given** either the Balance column or Aggregated Total column is not found in the uploaded files, **When** processing completes, **Then** the system displays an appropriate warning and omits the corresponding total section.

---

### User Story 3 - Verify Reconciliation Outcome with Different Scenarios (Priority: P3)

A user runs multiple reconciliations with different data sets and observes the verdict change between "Balanced" and "Not Balanced" depending on whether the adjusted totals match.

**Why this priority**: Demonstrates the correctness of the reconciliation logic across varied scenarios.

**Independent Test**: Can be tested with three known datasets: one perfectly balanced, one with a known difference, and one with zero discrepancies.

**Acceptance Scenarios**:

1. **Given** a dataset where the adjusted Bank Total equals the adjusted Company Total, **When** the results page loads, **Then** the verdict shows "Reconciliation Successful, Balanced".
2. **Given** a dataset where the adjusted totals differ by a specific amount, **When** the results page loads, **Then** the verdict shows the difference amount and indicates the books are not balanced.

### Edge Cases

- What happens when the uploaded files have only one row of data (the last item is the only item)?
- What happens when all discrepancy values are zero — the adjusted totals should equal the raw totals.
- What happens when discrepancy values are negative or zero — should still be added (zero has no effect, negative reduces the total).
- What happens when the user does not provide the "Aggregated Total" column name — the Company Net Total section is omitted or shows a relevant message.
- What happens when the Balance column or Aggregated Total column is entirely empty or missing from the data.
- What happens when non-numeric characters are mixed with numbers in a cell (e.g., "$1,000.50").
- What happens when the subtraction yields a negative result — should still display the absolute difference with a label indicating which side is higher.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract the value from the last row of the "Balance" column from the bank statement PDF data.
- **FR-002**: The system MUST accept a user-specified "Aggregated Total" column name from the frontend during the POST request.
- **FR-003**: The system MUST extract the value from the last row of the Aggregated Total column from the XLSX data.
- **FR-004**: The API MUST return both the last Balance value and the last Aggregated Total value to the frontend.
- **FR-005**: The frontend MUST display "Bank Net Total" showing the last Balance value from the bank statement.
- **FR-006**: The frontend MUST display "Company Net Total" showing the last Aggregated Total value from the XLSX.
- **FR-007**: The frontend MUST add the "Uncleared checks" discrepancy amount to the Bank Net Total and display the result as "Adjusted Bank Total".
- **FR-008**: The frontend MUST add the "Unpresented checks" discrepancy amount to the Bank Net Total and display the result as "Adjusted Bank Total".
- **FR-009**: The frontend MUST add the "Bank Debited But not credited in cashbook" discrepancy amount to the Company Net Total and display the result as "Adjusted Company Total".
- **FR-010**: The frontend MUST add the "Bank credited but not debited in cashbook" discrepancy amount to the Company Net Total and display the result as "Adjusted Company Total".
- **FR-011**: The frontend MUST automatically calculate the difference between the Adjusted Bank Total and the Adjusted Company Total.
- **FR-012**: The frontend MUST display "Reconciliation Successful, Balanced" when the difference is zero.
- **FR-013**: The frontend MUST display the difference amount with an imbalance message when the difference is non-zero.
- **FR-014**: The system MUST handle non-numeric values in Balance and Aggregated Total columns gracefully with appropriate error messages.

### Key Entities

- **Bank Statement**: Contains the Balance column from which the last row value is extracted as the Bank Net Total.
- **XLSX Company Records**: Contains the Aggregated Total column from which the last row value is extracted as the Company Net Total.
- **Discrepancy**: Individual items identified during reconciliation (Uncleared checks, Unpresented checks, Bank Debited But not credited, Bank credited but not debited) that adjust the net totals.
- **Bank Net Total**: The raw final balance from the bank statement (last Balance column value).
- **Company Net Total**: The raw final aggregated total from company records (last Aggregated Total column value).
- **Adjusted Bank Total**: Bank Net Total adjusted by adding Uncleared checks and Unpresented checks.
- **Adjusted Company Total**: Company Net Total adjusted by adding Bank Debited But not credited and Bank credited but not debited.
- **Reconciliation Verdict**: The final outcome — "Balanced" if adjusted totals match, "Not Balanced" otherwise.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can see the Bank Net Total and Company Net Total clearly displayed on the results page immediately after processing completes.
- **SC-002**: Users can verify whether the reconciliation is successful within seconds by reading the clearly displayed verdict.
- **SC-003**: The system correctly calculates the adjusted totals and reconciliation verdict 100% of the time when valid numeric data is provided.
- **SC-004**: Users receive clear error messages instead of crashes when invalid or missing data is encountered in the Balance or Aggregated Total columns.
