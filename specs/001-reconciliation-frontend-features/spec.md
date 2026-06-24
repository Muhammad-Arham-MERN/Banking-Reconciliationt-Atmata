# Feature Specification: Reconciliation Frontend Enhancements

**Feature Branch**: `001-reconciliation-frontend-features`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "This is a specification for extra features on top of finished product. 2 features are to be implemented in the Frontend: 1) Categorization of Reconciled data - Once the data after entire reconciliation is presented to user in the table at the end, this feature modifies that table - there will be 4 sections now also table, breaking the single unit of table - The 4 sections will be called UNPRESENTED CHECKS, UNCLEARED CHECKS, BANK DEBITED BUT NOT CREDITED IN CASH BOOK and BANK CEDITED BUT NOT DEBITED IN CASH BOOK - Items in the table that are Related to Bank && Have Positive Value will be assigned to Section BANK DEBITED BUT NOT CREDITED IN CASH BOOK - Items in the table that are Related to Bank && Have Negative Value will be assigned to Section BANK CEDITED BUT NOT DEBITED IN CASH BOOK - Items in the table that are Related to Company && Have Positive Value will be assigned to Section UNCLEARED CHECKS - Items in the table that are Related to Company && Have Negative Value will be assigned to Section UNPRESENTED CHECKS - Each new section will be column wise, not in rows, and will also have same design as before, just categorically split. 2) Manual Reconciliation - This is a feature where a check mark will be placed beside each Item in Discrepancies list - The user can manually select the discrepancies they want to remove manually - Below all the 4 tables will be a manual reconciliation button, that will be disabled unless or until a single value from tables is checked - Once a value is checked, a section will appear above the Manual Reconciliation Button that will indicate how much amount is being removed - The section above the button will also perform calculations for example if user selects -179,000 from Company, +79000 from Bank and +100000 from Bank, then the reconciliation section above button will show 0 as sum is equal to zero - Once the manual reconciliation button is clicked, the final tables (all 4) will also be updated"

## User Scenarios & Testing

### User Story 1 - Transaction Categorization (Priority: P1)

As a finance accountant, I want to see all unreconciled transactions automatically categorized into four logical sections so that I can quickly identify the type of discrepancy without manual analysis.

**Why this priority**: This is foundational functionality that transforms the raw reconciliation data into actionable insights. Without categorization, accountants must manually determine which transactions are unpresented checks, uncleared checks, or bank variances, which is time-consuming and error-prone.

**Independent Test**: Can be fully tested by running the reconciliation process and verifying that all transactions are correctly sorted into the four category sections based on their source (Bank/Company) and value (Positive/Negative). Delivers immediate value by organizing complex data into familiar accounting categories.

**Acceptance Scenarios**:

1. **Given** a completed reconciliation with mixed transaction types, **When** results are displayed, **Then** all transactions are automatically categorized into one of four sections: UNPRESENTED CHECKS, UNCLEARED CHECKS, BANK DEBITED BUT NOT CREDITED IN CASH BOOK, or BANK CREDITED BUT NOT DEBITED IN CASH BOOK

2. **Given** transactions related to Bank with positive values, **When** categorization is applied, **Then** these transactions appear in the BANK DEBITED BUT NOT CREDITED IN CASH BOOK section

3. **Given** transactions related to Bank with negative values, **When** categorization is applied, **Then** these transactions appear in the BANK CREDITED BUT NOT DEBITED IN CASH BOOK section

4. **Given** transactions related to Company with positive values, **When** categorization is applied, **Then** these transactions appear in the UNCLEARED CHECKS section

5. **Given** transactions related to Company with negative values, **When** categorization is applied, **Then** these transactions appear in the UNPRESENTED CHECKS section

6. **Given** any categorized section, **When** viewing the section, **Then** data is displayed in column-wise layout consistent with the original table design

7. **Given** a section with no matching transactions, **When** viewing that section, **Then** the section header is displayed with an empty state or no data indicator

---

### User Story 2 - Manual Reconciliation (Priority: P2)

As a finance accountant, I want to manually select and reconcile specific discrepancy items so that I can remove known explanations or matching items that the automated system couldn't detect.

**Why this priority**: Manual reconciliation is essential for handling edge cases and human-identified matches that automated rules miss. It provides flexibility and control over the final reconciliation state, enabling complete accuracy in financial reporting.

**Independent Test**: Can be fully tested by selecting specific discrepancy items, observing the calculation preview, and executing the reconciliation to verify tables update correctly. Delivers value by allowing users to complete reconciliation when automation falls short.

**Acceptance Scenarios**:

1. **Given** the categorized reconciliation results, **When** viewing any of the four sections, **Then** each transaction item displays a checkbox for selection

2. **Given** no items are selected in any section, **When** viewing the Manual Reconciliation Button, **Then** the button is disabled

3. **Given** one or more items are selected across sections, **When** viewing the Manual Reconciliation Button, **Then** the button is enabled

4. **Given** items are selected, **When** selection is made, **Then** a calculation section appears above the Manual Reconciliation Button showing the total amount being removed

5. **Given** selected items totaling -179,000 (Company), +79,000 (Bank), and +100,000 (Bank), **When** viewing the calculation section, **Then** it displays "0" as the sum equals zero

6. **Given** selected items with net zero sum, **When** the Manual Reconciliation Button is clicked, **Then** all selected items are removed from their respective sections

7. **Given** selected items with non-zero sum, **When** the Manual Reconciliation Button is clicked, **Then** a confirmation or warning is displayed about the imbalance

8. **Given** the Manual Reconciliation Button is clicked and reconciliation completes, **When** viewing the four sections, **Then** all sections are updated to reflect the removal of selected items

9. **Given** a user deselects all items, **When** no items remain selected, **Then** the calculation section disappears and the Manual Reconciliation Button becomes disabled

---

### Edge Cases

- What happens when a user selects items but the net sum is non-zero (indicating an incomplete reconciliation)?
- How does the system handle selection of items where only Company side or only Bank side exists (no matching pair)?
- What happens when all items in a section are removed through manual reconciliation (empty section display)?
- How does the system behave if a user tries to manually reconcile while an automated reconciliation is still in progress?
- What happens if the user cancels or navigates away during the manual reconciliation process?
- How are very large amounts formatted in the calculation section to ensure readability?
- What happens if a transaction has a value of exactly zero - which category does it belong to?

## Requirements

### Functional Requirements

- **FR-001**: System MUST automatically categorize all unreconciled transactions into four sections based on transaction source and value
- **FR-002**: System MUST assign transactions to BANK DEBITED BUT NOT CREDITED IN CASH BOOK when source is Bank and value is positive
- **FR-003**: System MUST assign transactions to BANK CREDITED BUT NOT DEBITED IN CASH BOOK when source is Bank and value is negative
- **FR-004**: System MUST assign transactions to UNCLEARED CHECKS when source is Company and value is positive
- **FR-005**: System MUST assign transactions to UNPRESENTED CHECKS when source is Company and value is negative
- **FR-006**: System MUST display each categorized section in column-wise layout consistent with the original table design
- **FR-007**: System MUST provide a checkbox beside every transaction item in all four sections
- **FR-008**: System MUST enable the Manual Reconciliation Button only when one or more items are selected
- **FR-009**: System MUST disable the Manual Reconciliation Button when no items are selected
- **FR-010**: System MUST display a calculation section above the Manual Reconciliation Button when items are selected
- **FR-011**: System MUST calculate and display the sum of all selected transaction values
- **FR-012**: System MUST update all four sections when manual reconciliation is executed
- **FR-013**: System MUST remove selected items from their respective sections after successful manual reconciliation
- **FR-014**: System MUST handle zero-value transactions with a default assignment to Company/Negative (UNPRESENTED CHECKS) category
- **FR-015**: System MUST show empty state indicators for sections with no transactions
- **FR-016**: System MUST display the calculation section only when items are selected, hiding it when deselection occurs
- **FR-017**: System MUST format currency values consistently across all sections and the calculation display
- **FR-018**: System MUST support selection of multiple items across different sections simultaneously
- **FR-019**: System MUST maintain selection state during user interaction until manual reconciliation is executed or cancelled
- **FR-020**: System MUST display section headers even when sections are empty

### Key Entities

- **Transaction Item**: An individual financial entry representing a discrepancy, containing attributes for source (Bank/Company), value (positive/negative amount), and selection state
- **Transaction Category**: One of four classification types (UNPRESENTED CHECKS, UNCLEARED CHECKS, BANK DEBITED BUT NOT CREDITED, BANK CREDITED BUT NOT DEBITED) determined by source and value
- **Discrepancy Selection**: A set of transaction items marked by the user for manual reconciliation, containing references to the items and their aggregate value
- **Reconciliation Calculation**: The computed sum of selected transaction values, displayed to the user before manual reconciliation execution

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can identify transaction types within 10 seconds of results display (compared to manual analysis taking 2+ minutes)
- **SC-002**: 100% of transactions are correctly categorized according to the four-section rules without user intervention
- **SC-003**: Users can complete manual reconciliation of selected items within 30 seconds (selection through execution)
- **SC-004**: Calculation preview displays within 1 second of any item selection or deselection
- **SC-005**: All four sections update within 3 seconds after manual reconciliation execution
- **SC-006**: 95% of users report that categorization improves their ability to identify discrepancies (measured via user feedback)
- **SC-007**: Zero data loss occurs during manual reconciliation process (all non-selected items remain in correct sections)
- **SC-008**: Users can successfully complete manual reconciliation on first attempt without training or documentation

## Assumptions

- The existing reconciliation system produces a single table of unreconciled transactions with source identification (Bank/Company) and monetary values
- The current table design is column-based and this design will be preserved for each categorized section
- Transaction values are stored as signed numeric values (positive for debits, negative for credits) allowing for mathematical operations
- The frontend can maintain selection state across multiple sections simultaneously
- Zero-value transactions are rare and can be assigned to a default category (Company/Negative = UNPRESENTED CHECKS)
- Users understand accounting concepts of unpresented checks, uncleared checks, and bank variances
- Manual reconciliation is a destructive operation (items are removed) and does not require undo functionality
- The system processes manual reconciliation synchronously or provides clear feedback during async operations

## Constraints & Non-Goals

### Constraints
- Must work with existing backend reconciliation output format
- Cannot modify the automated reconciliation logic - only display and manual manipulation of results
- Must maintain visual consistency with existing table design
- Must handle the same volume of data as the current system

### Non-Goals
- Automated re-categorization or re-assignment of transactions to different sections
- Editing transaction values or details
- Saving manual reconciliation state for future sessions
- Bulk selection operations (select all in section)
- Export or printing of categorized results
- Undo/redo functionality for manual reconciliation
- Historical tracking of which items were manually reconciled
- Explanation or audit log of categorization decisions