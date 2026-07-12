# Feature Specification: Cloud Database API Endpoints

**Feature Branch**: `004-cloud-db-api`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Implement cloud database API endpoints for file info retrieval and update using CockroachDB via SQLModel"

## User Scenarios & Testing

### User Story 1 - Retrieve user's cloud-stored reconciliation files (Priority: P1)

The system exposes a GET endpoint that returns a list of file names associated with the authenticated user. These file names represent previously saved reconciliation records stored in the cloud database. The frontend (handled in a separate spec) uses this list to let users select which past reconciliation to load.

**Why this priority**: This is the foundational read operation. Without retrieving stored file names, no other cloud-database workflow is possible.

**Independent Test**: Can be fully tested by calling the GET endpoint with valid authentication and verifying the response returns a list of strings representing available file names.

**Acceptance Scenarios**:

1. **Given** an authenticated user has saved reconciliation files in the cloud, **When** the user calls the GET endpoint, **Then** the system returns a list of file name strings corresponding to those saved records.
2. **Given** an authenticated user has no saved files, **When** the user calls the GET endpoint, **Then** the system returns an empty list.
3. **Given** an unauthenticated request, **When** the GET endpoint is called, **Then** the system returns a 401/403 unauthorized error.

---

### User Story 2 - Save reconciliation data to the cloud database (Priority: P1)

The system exposes a POST endpoint that accepts a file name and a list of structured data entries and persists them to the cloud database. The frontend (handled in a separate spec) calls this endpoint after completing a reconciliation to store results permanently in the cloud.

**Why this priority**: This is the foundational write operation. Without persisting data, there is nothing to retrieve later.

**Independent Test**: Can be fully tested by calling the POST endpoint with a sample file name and data payload, then verifying the data is stored and retrievable.

**Acceptance Scenarios**:

1. **Given** valid POST data (file_name string + file_data list of dictionaries), **When** the user submits the data, **Then** the system stores it and returns a success confirmation.
2. **Given** a POST request with an empty file_name, **When** the user submits, **Then** the system returns a validation error.
3. **Given** a POST request with malformed file_data (missing required fields or incorrect types), **When** the user submits, **Then** the system returns a validation error.
4. **Given** a POST request with a file_name that already exists, **When** the user submits, **Then** the system overwrites the existing record (upsert) and returns a success confirmation.

---

### Edge Cases

- What happens when the cloud database is unreachable or returns an error? The API should return a 503 Service Unavailable error.
- What happens when the List[str] in the users table is extremely large? The endpoint should handle pagination or reasonable size limits.
- What happens when file_data contains unexpected additional fields beyond the defined structure? The system should store them as-is without rejecting, given the field description states "as is, without modification".
- What happens if the database connection pool is exhausted? Requests should queue or fail gracefully with a retryable error.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a GET endpoint to retrieve the authenticated user's list of stored file names from the cloud database.
- **FR-002**: System MUST provide a POST endpoint that accepts `file_name` (string) and `file_data` (list of dictionaries) and persists them to the cloud database.
- **FR-003**: System MUST validate that POST requests contain both required fields (`file_name` and `file_data`) with correct types before processing.
- **FR-004**: System MUST authenticate all requests to both endpoints — unauthenticated requests MUST be rejected with 401/403.
- **FR-005**: System MUST use SQLModel for database connection, schema definition, and query operations.
- **FR-006**: System MUST connect to a serverless cloud-based PostgreSQL database.
- **FR-007**: The `reconciliation_data` table MUST store `file_name` as a string and `file_data` as the raw list-of-dictionaries structure without modification.
- **FR-008**: System MUST return appropriate HTTP status codes for success (200), validation errors (422), authentication failures (401/403), and server errors (500 or 503).
- **FR-009**: When a POST request arrives with a `file_name` that already exists for the authenticated user, the system MUST overwrite the existing record with the new data (upsert behavior).
- **FR-010**: System MUST log all API requests to these endpoints through the existing request logging pipeline, recording timestamps, authenticated user, endpoint called, response status, and duration.

### Key Entities

- **User Account**: Represents an authenticated user. Contains a `files` field (list of strings) that references available reconciliation file names associated with that user.
- **Reconciliation Record**: A saved reconciliation result consisting of a `file_name` (unique identifier string) and `file_data` (a list of structured entries, each containing name, description, debit_credit_value, and category).

### Assumptions

- The authenticated user is identified via the existing JWT-based auth middleware already implemented in the project.
- The `users` table already exists with a `files` column of type array/list of strings.
- Both endpoints sit behind the existing authentication middleware.
- The `reconciliation_data` table maps each record to a user via a foreign key relationship to the `users` table.
- The data payload structure for each entry in `file_data` is: `{"name": "string", "description": "string", "debit_credit_value": 0.0, "category": "string"}`.
- The `reconciliation_data` table includes a `file_name` field that serves as the reference key. The `users.files` column stores file names that point to records in `reconciliation_data`. When a file_name is updated, the corresponding reference in `users.files` is also updated to stay in sync.
- When a `file_name` already exists, the POST endpoint overwrites the record (upsert behavior) rather than rejecting.

## Clarifications

### Session 2026-07-10

- Q: How do `users.files` and `reconciliation_data` relate? → A: `reconciliation_data.file_name` is the reference key. `users.files` stores file names that point to records in `reconciliation_data`. When a file_name is updated, the reference in `users.files` updates to stay in sync.
- Q: Conflict behavior when POST receives a duplicate file_name? → A: Overwrite (upsert) — new data replaces the old record for the same file_name.
- Q: Should API calls be logged? → A: Yes, through the existing request logging middleware (log_requests) for duration, status, user, and endpoint metadata.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Authenticated users can retrieve their stored file list from the GET endpoint with a response time under 500ms for up to 1000 files.
- **SC-002**: Users can successfully store a reconciliation record via the POST endpoint with up to 5000 data entries in under 3 seconds.
- **SC-003**: The system handles invalid or missing POST fields by returning a clear validation error without persisting partial data.
- **SC-004**: Both endpoints return 401/403 for requests without valid authentication tokens.
- **SC-005**: Reconciliation data stored via the POST endpoint is immediately retrievable via the GET endpoint (write-after-read consistency within 1 second).
