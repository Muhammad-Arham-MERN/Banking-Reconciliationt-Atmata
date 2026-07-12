````md
# Authentication with Auth.js (OAuth)

## Overview

This feature implements **Auth.js** to provide **Google OAuth-based authentication** for the application.

The goal of this feature is **only to introduce authentication and user identity management**. No changes will be made to the existing reconciliation storage or retrieval logic in this specification.

---

# Why are we implementing authentication?

Our application is currently intended for approximately **10–20 users**.

Although the user count is small, we still need a reliable way to distribute and manage the application. Packaging the application inside Docker and asking every user to install Docker introduces unnecessary overhead and is not practical for non-technical users.

Instead, the application will be deployed to the **cloud**.

---

# Problems with a Cloud-Only Deployment

Moving to the cloud introduces a new challenge.

## 1. Historical reconciliation data

The reconciliation workflow relies on previous reconciliation files.

For example:

- When performing the **June** reconciliation, the application should be able to automatically retrieve the **May** reconciliation.
- This historical data improves the reconciliation experience.

## 2. Local history management

If reconciliation history remains stored only on users' local computers, users would have to manually manage and transfer these files between devices, creating unnecessary friction.

---

# Solution

Move the application to the cloud and introduce **user authentication**.

Each authenticated user will have their own isolated reconciliation history stored in the database.

---

# Current Problem

Different users will upload different reconciliation files.

For example:

- User A has May, June, and July reconciliations.
- User B has completely different reconciliation histories.

Currently, there is no mechanism to separate one user's data from another user's data.

---

# Proposed Solution

Use **Auth.js** for authentication and session management.

Each user will authenticate using their Google account. Once authenticated, every reconciliation history stored in the database will belong only to that user.

Auth.js is selected because it automatically handles:

- OAuth authentication
- Session management
- User creation
- Database integration

This significantly reduces the amount of authentication logic we need to implement ourselves.

---

# Authentication Flow

Only **Google Sign-In** will be supported.

Manual email/password authentication will **not** be implemented.

The flow is as follows:

1. When a user opens the application without being authenticated, the main application remains inaccessible.
2. The user is presented with a screen containing a **Google Sign-In** button.
3. After successful authentication:
   - Auth.js creates or retrieves the user.
   - Sessions are managed automatically.
   - User information is stored in CockroachDB through the Auth.js PostgreSQL adapter.

---

# Database Changes

Auth.js automatically creates the required authentication tables in PostgreSQL.

Reference:

https://authjs.dev/getting-started/adapters/pg

## Users Table

The existing `users` table will be extended by adding a new field:

```text
files
```

Originally, the plan was to store files using the following structure:

```python
List[
    {
        "file_name": str,
        "reconciled_file": BYTEA
    }
]
```

However, this approach is not suitable because:

- `JSONB` does not natively support `BYTEA`.
- Binary data must first be Base64 encoded.
- Base64 increases storage size and introduces unnecessary processing overhead.

---

## Reconciliation_data Table

A new table named:

```text
Reconciliation_data
```

will be introduced.

It contains two fields:

| Field | Type | Description |
|--------|------|-------------|
| file_name | String | Unique identifier used as a reference from the `users.files` field |
| data | JSON/List | Stores reconciliation discrepancies |

The `data` field stores:

```python
List[
    {
        "name": str,
        "description": str,
        "debit_credit_value": float,
        "category": str
    }
]
```

Where:

- The **List** represents all discrepancies within a reconciliation.
- Each **Dictionary/Object** represents one discrepancy.

---

# Overall Flow

1. User opens the application.
2. User signs in using Google.
3. Auth.js authenticates the user.
4. Required authentication tables are created (if they do not already exist).
5. The `users` table is extended with the `files` field.
6. The `Reconciliation_data` table is introduced.

This completes the authentication infrastructure.

---

# Scope Boundaries (Do NOT Cross)

The following items are **explicitly out of scope** for this feature.

### 1.

Do **not** modify the current reconciliation history storage implementation.

### 2.

Do **not** modify file retrieval logic on either the frontend or backend.

### 3.

The existing local storage mechanism must remain unchanged.

### 4.

This specification is **only** responsible for implementing authentication.

No additional functionality should be introduced.

### 5.

Any future improvements or migration of reconciliation storage will be covered in separate specifications.

### 6.

No API endpoints should be created as part of this feature.

---

# Documentation

## CockroachDB

https://www.cockroachlabs.com/docs/

## Auth.js

https://authjs.dev/getting-started

---

# Authority

For this project, the developer is the primary source of authority regarding implementation decisions, architectural direction, reasoning, and project steering. Documentation should guide implementation where applicable, but final technical decisions are made by the developer.
````
