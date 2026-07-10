# Feature Specification: Open de Past — Save & Load Historical Reconciliation Data

**Feature Branch**: `003-open-de-past`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "Open de Past — save reconciliation history, load past discrepancies, and merge them with current results"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Save Completed Reconciliation Results (Priority: P1)

After reviewing reconciliation results and making any desired manual adjustments, the user saves the finalised reconciliation to a local history archive. The save captures every discrepancy with its category, transaction details, date, and amount.

**Why this priority**: This is the foundation of the feature — without saving, nothing else works. It also provides immediate value because the user now has an auditable local record of every reconciliation.

**Independent Test**: Can be fully tested by completing a reconciliation and clicking "Complete Reconciliation" — a file appears in the local "Reconciliation History" folder with all discrepancy data intact.

**Acceptance Scenarios**:

1. **Given** the reconciliation results are displayed on screen, **When** the user clicks "Complete Reconciliation", **Then** all discrepancies are saved to a file in the local "Reconciliation History" folder.
2. **Given** the discrepancy table has entries in all four categories (Unpresented Checks, Uncleared Checks, Bank Debited But not Credited in Cashbook, Bank Credited But not Debited in Cashbook), **When** the user saves, **Then** every entry's category, transaction details, date, and debit/credit amount are stored.
3. **Given** the user has typed a custom name in the name field near the button, **When** they click "Complete Reconciliation", **Then** the saved file uses that custom name instead of the auto-generated date.

---

### User Story 2 — Load and Display Past Reconciliation Discrepancies (Priority: P1)

At the start of a new reconciliation session, the user selects a previously saved history file from the "Open Maazi" dropdown. When the new reconciliation completes, past discrepancies appear alongside current ones, clearly marked as past entries.

**Why this priority**: Both user stories share P1 because saving without loading provides only half the value. The core loop is save → load → merge; both halves must work for the feature to be useful.

**Independent Test**: Can be fully tested by first saving a reconciliation with known discrepancies, then starting a new session, selecting that file, running a new reconciliation, and verifying past discrepancies appear in the results table with the "From Past" indicator.

**Acceptance Scenarios**:

1. **Given** there are saved history files in the "Reconciliation History" folder, **When** the user opens the "Open Maazi" dropdown above the upload section, **Then** all history files are listed and one can be selected.
2. **Given** the user has selected a past history file and completed a new reconciliation, **When** the results are displayed, **Then** discrepancies from the past file appear in their respective category sections within the discrepancy table.
3. **Given** a past discrepancy is displayed alongside current discrepancies, **When** the table renders, **Then** each past discrepancy has a "From Past" column marked with an indicator and a light purple background on that row.

---

### User Story 3 — Name or Auto-Name Saved History Files (Priority: P2)

The user can optionally provide a custom name for each saved reconciliation history file. If no name is provided, the system automatically uses the current date and time.

**Why this priority**: Naming is a convenience feature that improves organisation but is not required for the core save/load cycle to function.

**Independent Test**: Can be tested by saving a reconciliation with no custom name (verify auto-date file appears), then saving another with a custom name (verify custom-named file appears).

**Acceptance Scenarios**:

1. **Given** the user has not typed any custom name, **When** they click "Complete Reconciliation", **Then** the file is saved with the current date-time as its name.
2. **Given** the user has typed a custom name in the input field, **When** they click "Complete Reconciliation", **Then** the file is saved using that custom name.

### Edge Cases

- **Empty history folder**: When the "Reconciliation History" folder does not exist or is empty, the "Open Maazi" dropdown shows a placeholder option like "No history available" and is non-functional.
- **Corrupted history file**: If the selected history file is corrupt or unreadable, the system warns the user and proceeds with the current reconciliation only (no past discrepancies loaded).
- **Custom name collision**: If the user provides a custom name that matches an existing file, the save is skipped and a notification tells the user to choose a different name (see FR-004).
- **No discrepancies in past file**: If the loaded history file contains zero discrepancies, the reconciliation proceeds normally with no past discrepancies displayed.
- **Duplicate transactions across periods**: If a past discrepancy and a current discrepancy share the same transaction details and the same transaction date, they are treated as duplicates — the past entry is suppressed to avoid double-counting. If they share transaction details but have different dates, both entries are displayed independently (they are distinct discrepancies that happen to have the same description) — the past one is marked with the "From Past" indicator.
- **Save failure (disk full, permissions, locked folder)**: If saving the history file fails, the system MUST display a clear error notification. The reconciliation results remain on screen so the user can attempt saving again by clicking "Complete Reconciliation" once the issue is resolved.

## Clarifications

### Session 2026-07-03

- Q: When a past discrepancy and a current discrepancy share the same transaction details, how should duplicates be handled? → A: Compare by date — same transaction details + same date = duplicate (suppress past entry). Same details + different date = two distinct entries (show both, past marked with flag).
- Q: What file format should history files use? → A: SQLite, as originally specified.
- Q: How should past and current entries be ordered within each category section? → A: Interleave by transaction date (ascending), and the column label is "From Past".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST display a "Complete Reconciliation" button positioned below the manual reconciliation button on the results screen.
- **FR-002**: The system MUST provide a text input field near the "Complete Reconciliation" button for an optional custom file name.
- **FR-003**: When the user clicks "Complete Reconciliation", the system MUST save all currently displayed discrepancies (including any manual adjustments) to a file in the local "Reconciliation History" directory.
- **FR-004**: If no custom name is provided, the system MUST auto-generate the file name using the current date and time (e.g., "2026-07-03_14-30-00"). If the user provides a custom name that matches an existing file, the system MUST skip the save and display a notification that a file with that name already exists, prompting the user to choose a different name.
- **FR-005**: Each saved history entry MUST store: category classification (one of: "Unpresented Checks", "Uncleared Checks", "Bank Debited But not Credited in Cashbook", "Bank Credited But not Debited in Cashbook"), transaction details (text), transaction date (date), and debit/credit amount (numeric). The category field acts as a boolean membership indicator — each entry belongs to exactly one category.
- **FR-006**: The front page MUST display a dropdown labelled "Open Maazi" positioned above the file upload section.
- **FR-007**: The "Open Maazi" dropdown MUST list all history files present in the "Reconciliation History" directory. Selecting a file chooses it as the past reconciliation source.
- **FR-008**: Only one history file may be selected per reconciliation session. The selection is optional — the user may proceed without selecting any.
- **FR-009**: When a past history file is selected and a new reconciliation completes, the system MUST merge past discrepancies into the results table. Each past discrepancy appears in the same category section as the new discrepancies belonging to that category. Within each category, all entries (past and current) are sorted together by transaction date in ascending order.
- **FR-010**: The discrepancy display table MUST include a "From Past" column that indicates whether a given entry originated from a past history file.
- **FR-011**: Rows marked as "From Past" MUST have a light purple background to visually distinguish them from current discrepancies.
- **FR-012**: The "Complete Reconciliation" button MUST be disabled when there are no discrepancies to save (i.e., an empty result set).

### Assumptions

- **File format**: History files use SQLite format. Each file is a self-contained SQLite database storing all discrepancy entries for one reconciliation session.
- **Single-user environment**: The system is a local desktop application used by one person at a time. Concurrency and multi-user concerns are out of scope.
- **Local storage only**: All history files are stored on the local filesystem. No cloud sync, network storage, or remote access is required.
- **File size**: History files are expected to be small (hundreds of entries, not millions) — performance optimisation for large datasets is not required.
- **Manual adjustments captured**: Any changes the user makes to discrepancies before clicking "Complete Reconciliation" are saved exactly as displayed on screen.

### Key Entities

- **Reconciliation History File**: A stored record of a completed reconciliation. Contains multiple discrepancy entries, each classified into one of four categories. Has a name (either auto-generated date-time or user-provided custom name). Stored in the "Reconciliation History" directory. The file format is read/written by the system only — users are not expected to open or modify these files manually.
- **Discrepancy Entry**: A single unmatched transaction identified during reconciliation. Attributes: category (one of the four types), transaction details (text description), transaction date, debit/credit amount, and a "from past" boolean flag indicating whether this entry came from a loaded history file.
- **"Reconciliation History" Directory**: A local folder at the project root that stores all saved history files. Created automatically on first save if it does not exist.
- **"Open Maazi" Selector**: A dropdown control on the main page that lists all available history files. Enables the user to choose which past reconciliation data to load for the current session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can save a completed reconciliation in a single click (or two clicks if providing a custom name). The saved file is immediately visible in the "Reconciliation History" folder.
- **SC-002**: All discrepancies from a selected history file are displayed alongside current discrepancies in the results table after a new reconciliation completes, with zero data loss.
- **SC-003**: Past discrepancies are visually distinguishable from current discrepancies 100% of the time via the "From Past" column and light purple background.
- **SC-004**: New users can successfully save and reload a past reconciliation on their first attempt without external guidance, measured by task completion rate exceeding 90%.
- **SC-005**: The "Open Maazi" dropdown loads and displays the correct list of history files within 2 seconds of the page loading.
