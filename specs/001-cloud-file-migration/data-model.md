# Data Model: Cloud File Migration

## Entities

### User

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| id | integer | PostgreSQL (CockroachDB) | Auth.js adapter, from `users` table |
| name | string | Google OAuth | Displayed in greeting |
| email | string | Google OAuth | Unique identifier |
| image | string? | Google OAuth | Avatar URL |

The `user_id` is obtained from the NextAuth session (`session.user.id` = JWT `sub` claim). The backend verifies this via `verify_auth_token()` using the shared `NEXTAUTH_SECRET`.

### Cloud Reconciliation File (persisted)

| Field | Type | Notes |
|-------|------|-------|
| file_name | string (1-255 chars) | User-provided name, unique per user |
| file_data | list[dict] | List of reconciliation entries (see below) |
| user_id | integer | Foreign key to `users(id)` |
| created_at | datetime | Auto-set on insert |

**Storage**: `reconciliation_data` table in CockroachDB. `file_data` stored as JSONB in the `data` column.

### Reconciliation Entry (within file_data)

| Field | Type | Notes |
|-------|------|-------|
| name | string | Transaction description |
| details | string | Additional transaction details |
| amount | number | Debits positive, credits negative |
| category | string | Categorization label |

**State transitions**: N/A (stateless — entries are created during reconciliation and persisted as-is).

### History List (response only)

| Field | Type | Notes |
|-------|------|-------|
| files | list[string] | List of file names for the authenticated user |

**Note**: Unlike the old local history model, cloud history responses contain only file names — no metadata (file_path, entry_count, created_at). The frontend adapts to this simplified shape.

## Entity Relationships

```
User (1) ──── has many ────> Cloud Reconciliation File
Cloud Reconciliation File (1) ──── contains many ────> Reconciliation Entries
```

## Validation Rules

| Rule | Applies To | Constraint |
|------|-----------|------------|
| file_name required | Save request | Non-empty, max 255 chars |
| file_data non-empty | Save request | At least 1 entry in the list |
| Auth token present | All cloud requests | Valid Bearer token in Authorization header |
| user_id injected | All cloud requests | Set by auth_middleware from JWT |

## Key Differences from Legacy Model

| Aspect | Legacy (local history) | Cloud |
|--------|----------------------|-------|
| Storage | SQLite files per entry | Single CockroachDB table |
| History list response | `HistoryFile[]` (name, path, created_at, entry_count) | `list[string]` (file names only) |
| Auth | None (local-only) | Bearer JWT |
| Save target | `/history/save` (POST) | `/api/cloud/save_files_cloud` (POST) |
| Load target | `/history/list` (GET) | `/api/cloud/load_files_cloud` (GET) |
