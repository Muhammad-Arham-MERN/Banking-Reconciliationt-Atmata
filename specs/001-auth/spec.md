# Feature Specification: Google OAuth Authentication with Auth.js

**Feature Branch**: `001-auth`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Implement Auth.js to provide Google OAuth-based authentication. Users authenticate via Google Sign-In. Auth.js manages sessions automatically. Data stored in CockroachDB. New Reconciliation_data table introduced."

## Clarifications

### Session 2026-07-10

- Q: Are Auth.js OAuth callback/handler routes permitted despite FR-011 forbidding new API endpoints? → A: Yes — everything related to OAuth (callback routes, session endpoints, sign-in/sign-out routes) is permitted. FR-011 only forbids business/reconciliation API endpoints.
- Q: What error feedback should be shown when Google OAuth fails? → A: Show a user-friendly error message on the sign-in page explaining the failure (e.g., "Sign-in failed. Please try again.").
- Q: Should Reconciliation_data have a direct user_id foreign key or rely on users.files for association? → A: No user_id FK needed. The `users.files` field referencing `Reconciliation_data.file_name` is sufficient for the current scope.
- Q: What behavior when session expires mid-use? → A: 24-hour session duration from sign-in. No refresh/extension mechanism. If expired mid-use, the user is redirected to the sign-in page to re-authenticate.

## User Scenarios & Testing

### User Story 1 - User Signs In with Google (Priority: P1)

A user opens the application for the first time. They are not authenticated, so they see a Google Sign-In button instead of the main application. They click the button and grant permission via their Google account. Auth.js authenticates the user, creates or retrieves their user record, and grants them access to the application.

**Why this priority**: P1 — Without the ability to sign in, no user can access the cloud-deployed application. This is the foundational capability of the feature.

**Independent Test**: A brand-new user can open the app in a private browser session, click the Google Sign-In button, complete the OAuth flow, and immediately see the main application with their own empty reconciliation state.

**Acceptance Scenarios**:

1. **Given** the user is not authenticated, **When** they open the application, **Then** they see a Google Sign-In button and the main application is inaccessible.
2. **Given** the user clicks the Google Sign-In button, **When** they complete the Google OAuth flow, **Then** Auth.js creates or retrieves their user record and they gain access to the application.
3. **Given** the user has an active session, **When** they revisit the application, **Then** they are automatically signed in without re-authentication.

---

### User Story 2 - User Signs Out (Priority: P2)

An authenticated user decides to sign out of the application. They click a sign-out option, Auth.js terminates their session, and they are returned to the sign-in screen.

**Why this priority**: P2 — Sign-out is important for security but the service is usable without it (users can close the browser or rely on session expiry).

**Independent Test**: A signed-in user can click the sign-out option, be redirected to the sign-in screen, and see the Google Sign-In button again.

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** they click the sign-out option, **Then** Auth.js terminates the session and the user is returned to the sign-in screen.
2. **Given** the user has signed out, **When** they attempt to access the application URL directly, **Then** they are redirected to the sign-in screen.

---

### Edge Cases

- What happens when Google OAuth returns an error (e.g., the user denies permission, network failure)?
- What happens when the database connection fails during authentication (tables cannot be created or queried)?
- What happens when a user's session expires mid-use (they are redirected to re-authenticate and lose current page state)?
- What happens if a user who previously authenticated returns after their session has expired?
- What happens to user data if the authentication provider (Google) is temporarily unavailable?
- How does the system handle OAuth errors (user denies permission, network timeout, provider unavailable)? The sign-in page MUST display a user-friendly error message explaining the failure with an option to retry.

## Requirements

### Functional Requirements

- **FR-001**: System MUST authenticate users exclusively through Google Sign-In. Manual email/password authentication MUST NOT be implemented.
- **FR-002**: System MUST prevent unauthenticated users from accessing the main application. They MUST be shown a sign-in screen with a Google Sign-In button.
- **FR-003**: System MUST automatically create Auth.js authentication tables in CockroachDB (via the PostgreSQL adapter) on first run if they do not already exist.
- **FR-004**: System MUST automatically create or retrieve a user record upon successful Google authentication.
- **FR-005**: System MUST manage user sessions via Auth.js with automatic session handling.
- **FR-006**: System MUST allow authenticated users to sign out, terminating their session.
- **FR-007**: The existing `users` table MUST be extended with a `files` field to reference reconciliation history.
- **FR-008**: A new `Reconciliation_data` table MUST be introduced with fields: `file_name` (String, unique identifier) and `data` (JSON/List containing discrepancy records).
- **FR-009**: Each discrepancy record in `Reconciliation_data.data` MUST contain: `name`, `description`, `debit_credit_value`, and `category`.
- **FR-010**: System MUST NOT modify existing reconciliation storage, retrieval logic, or local storage mechanisms.
- **FR-011**: System MUST NOT create any new business/reconciliation API endpoints as part of this feature. Auth.js OAuth routes (sign-in, callback, sign-out, session) are permitted and are not considered business endpoints.

### Key Entities

- **User**: Represents an authenticated person. Contains profile information from Google (name, email, avatar) and an extended `files` field that references associated reconciliation file names. Managed by Auth.js.
- **Reconciliation_data**: Stores the detailed discrepancy records for each reconciliation. Each record has a `file_name` (unique, referenced from the user's `files` field) and `data` (a list of discrepancy objects, each with name, description, debit_credit_value, and category).
- **Session**: Auth.js-managed session representing an authenticated user's active session. Persisted in CockroachDB and managed automatically by Auth.js.

## Success Criteria

### Measurable Outcomes

- **SC-001**: New users can complete the Google OAuth sign-in flow from opening the app to accessing the main application in under 10 seconds (assuming stable internet connection).
- **SC-002**: Unauthenticated users are consistently prevented from accessing the main application and see only the sign-in screen.
- **SC-003**: Authenticated users only see their own data; no user can access another user's reconciliation records.
- **SC-004**: Session duration is 24 hours from sign-in. Users returning within 24 hours are automatically authenticated; after 24 hours they must re-authenticate via Google Sign-In.
- **SC-005**: Sign-out completes within 2 seconds and the user is returned to the sign-in screen.
- **SC-006**: Authentication tables are created automatically on first application startup without manual database setup steps.
