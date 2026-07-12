# Feature Specification: Cloud File Migration

**Feature Branch**: `001-cloud-file-migration`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description from frontend-cloud-prompt.md: Migrate frontend file loading and saving from local file system to cloud API endpoints (load_files_cloud and save_files_cloud).

## Clarifications

### Session 2026-07-11

- Q: How are "debit/credit amounts" represented in the file_data dictionaries? → A: Single `amount` field where debits are positive numbers and credits are negative numbers.
- Q: How does the frontend authenticate with load_files_cloud and save_files_cloud? → A: Bearer token passed in the `Authorization` header, obtained from the sign-in flow.
- Q: What loading state should the history area show while the cloud API call is in-flight? → A: A spinner/skeleton placeholder in the history area until data arrives.
- Q: How should the frontend handle retries when the cloud API fails? → A: Manual retry via a "Retry" button shown on the error message.
- Q: Should local file loading/saving remain as a fallback, or be removed entirely? → A: Remove local file loading/saving entirely — cloud-only going forward.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cloud-Based Welcome & History Loading (Priority: P1)

After signing in, the user is greeted with their name and sees their previously saved reconciliation history fetched from the cloud instead of from local files.

**Why this priority**: This is the entry point of the application. Users must be able to access their history from any device, which is the core value of cloud migration. Without this, users only see local data.

**Independent Test**: A user signs in, sees the greeting "Assalamu Alaikum [Name]" at the top, and below it a list of reconciliation histories sourced from the cloud. The list contains files from cloud storage, not only locally available files.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** the main page loads, **Then** the greeting "Assalamu Alaikum [user's name]" appears prominently at the top of the page
2. **Given** a signed-in user with saved cloud files, **When** the main page loads, **Then** the history list shows file names returned by the load_files_cloud API
3. **Given** a signed-in user with no saved files, **When** the main page loads, **Then** the history list displays an appropriate empty state message

---

### User Story 2 - Cloud-Based File Saving (Priority: P1)

When a user completes a reconciliation, the reconciled data is saved to the cloud instead of local storage.

**Why this priority**: Saving is the second half of the cloud migration — without it, users cannot persist their work across sessions or devices. Both loading and saving must work together for the migration to be complete.

**Independent Test**: A user completes a reconciliation, provides a file name, and the reconciled data is saved via the cloud API. On a subsequent login, that file appears in the history list.

**Acceptance Scenarios**:

1. **Given** a user has completed reconciliation, **When** they save the result with a file name, **Then** the save_files_cloud API is called with user_id, file_name, and file_data (list of dictionaries containing transaction_details, transaction_date, debit_credit_amount, and category)
2. **Given** a save_files_cloud API call succeeds, **When** the response returns, **Then** the user sees a success confirmation
3. **Given** a save_files_cloud API call fails, **When** the response returns an error, **Then** the user sees a clear error message and the data is not lost

---

### User Story 3 - Cloud History Continues to Display Previously Saved Files (Priority: P2)

Users can resume work on previously saved reconciliations, now loaded from the cloud across any device.

**Why this priority**: While essential for full cloud migration, this builds on the previous two stories. The user can already see and save files; this story connects them into a seamless round-trip experience.

**Independent Test**: A user saves a reconciliation on one device, signs in on another device, and sees that same file in their history list.

**Acceptance Scenarios**:

1. **Given** a user has saved files via save_files_cloud, **When** they sign in on any device, **Then** those files appear in the history list loaded via load_files_cloud
2. **Given** a user has saved a file today, **When** they sign in next week, **Then** the same file still appears in their history list (data persists in cloud)

### Edge Cases

- What happens when the load_files_cloud API is in-flight? — A spinner or skeleton placeholder appears in the history area while the request completes.
- What happens when the load_files_cloud API returns an error (network issue, server down)? — The history list should show a retry-friendly error message with a "Retry" button, not a blank crash.
- What happens when the save_files_cloud API is called with an empty file_data list? — The API should still accept it; the frontend should prevent saving empty/nonsensical data.
- What happens when the user session expires between loading and saving? — The save attempt should fail gracefully with a re-authentication prompt.
- What happens if load_files_cloud returns a very large number of files? — The list should still render without performance degradation (reasonable pagination or virtual list behavior).

## Requirements *(mandatory)*

### Out of Scope

- Local file system loading and saving are removed entirely — the application is cloud-only going forward. There is no fallback to local directories.
- No offline mode is provided.

### Functional Requirements

- **FR-001**: System MUST display "Assalamu Alaikum [user name]" prominently at the top of the page content (above the upload area, in a heading-size font) after sign-in.
- **FR-002**: System MUST load the user's reconciliation history from the load_files_cloud API instead of local directories.
- **FR-003**: System MUST call save_files_cloud POST API with user_id in the request and file_name + file_data (list of dictionaries: transaction_details, transaction_date, debit_credit_amount, category) in the body.
- **FR-004**: System MUST show a success message when save_files_cloud completes successfully.
- **FR-005**: System MUST show a user-friendly error message when load_files_cloud or save_files_cloud fail, with a "Retry" button for the user to manually re-attempt the operation.
- **FR-010**: System MUST detect 401 (Unauthorized) responses from cloud API calls and prompt the user to re-authenticate (redirect to sign-in).
- **FR-006**: System MUST display an appropriate empty state when load_files_cloud returns an empty list.
- **FR-007**: System MUST NOT lose the user's reconciled data if save_files_cloud fails — the data must remain accessible for retry.
- **FR-008**: System MUST prevent saving empty or invalid reconciliation data.
- **FR-009**: System MUST include a Bearer token in the `Authorization` header when calling load_files_cloud and save_files_cloud, obtained from the user's sign-in session.

### Key Entities *(include if feature involves data)*

- **User**: Identified by user_id; has a name displayed in the greeting. Interacts with files through the cloud APIs.
- **Reconciliation File**: Named by the user; contains a list of reconciliation entries. Each entry has: transaction_details, transaction_date, debit_credit_amount (debits positive, credits negative), category.
- **History List**: A list of file names (strings) returned by load_files_cloud, representing the user's past reconciliation sessions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After sign-in, the greeting "Assalamu Alaikum [name]" appears on screen within 2 seconds of page load.
- **SC-002**: Users see their cloud reconciliation history within 3 seconds of page load (assuming normal network conditions).
- **SC-003**: 100% of reconciliation saves are persisted to cloud storage (verified by loading them back in a subsequent session).
- **SC-004**: Users can access and view their reconciliation history from any device after signing in.
- **SC-005**: Users are clearly informed of success or failure within 2 seconds of attempting to save.
