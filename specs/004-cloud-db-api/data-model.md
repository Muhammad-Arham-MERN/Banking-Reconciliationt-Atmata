# Data Model: Cloud Database API

**Feature**: 004-cloud-db-api | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)

## Entities

### User Account

| Field          | Type                  | Source Table | Notes                                    |
|----------------|-----------------------|--------------|------------------------------------------|
| `id`           | INTEGER (PK)          | `users`      | Auto-increment, SERIAL                   |
| `name`         | VARCHAR(255)          | `users`      | Nullable                                 |
| `email`        | VARCHAR(255)          | `users`      | Nullable                                 |
| `emailVerified`| TIMESTAMPTZ           | `users`      | Nullable                                 |
| `image`        | TEXT                  | `users`      | Nullable                                 |
| `files`        | JSONB                 | `users`      | Default `'[]'::jsonb` — list of file name strings |

**Note**: This table already exists and is managed by Auth.js. The `files` column stores file names that reference `reconciliation_data.file_name`. Not managed by SQLModel for the scope of this feature — read/written via raw asyncpg queries to avoid conflicting with Auth.js.

### Reconciliation Record

| Field       | Type           | Source Table              | Constraints                  | Notes                                      |
|-------------|----------------|---------------------------|------------------------------|--------------------------------------------|
| `id`        | INTEGER (PK)   | `reconciliation_data`     | SERIAL, auto-increment       | Internal ID                                |
| `file_name` | VARCHAR(255)   | `reconciliation_data`     | UNIQUE, NOT NULL             | Reference key from `users.files`           |
| `file_data` | JSONB          | `reconciliation_data`     | NOT NULL (maps to `data` column) | Stored as-is, list of dicts           |
| `user_id`   | INTEGER (FK)   | `reconciliation_data`     | REFERENCES users(id)         | Links record to owning user                |
| `created_at`| TIMESTAMPTZ    | `reconciliation_data`     | DEFAULT NOW(), NOT NULL      | Auto-set on creation                       |

**SQLModel Mapping** (`table=True`):

```python
from sqlmodel import SQLModel, Field
from typing import Any

class ReconciliationData(SQLModel, table=True):
    __tablename__: str = "reconciliation_data"

    id: int | None = Field(default=None, primary_key=True)
    file_name: str = Field(max_length=255, unique=True)
    # Maps to the `data` JSONB column in the existing table
    file_data: dict | list = Field(sa_column_kwargs={"name": "data"})
    user_id: int = Field(foreign_key="users(id)")
    created_at: datetime | None = Field(default=None)
```

> **Column Name Note**: The existing CockroachDB table stores the JSON payload in a column named `data`, but the spec refers to it as `file_data`. The SQLModel field is named `file_data` and mapped to the `data` column via `sa_column_kwargs`.

### Users Files List (Logical Relationship)

The `users.files` column (JSONB) stores a list of file name strings. This list is synced when:
- **GET /cloud/files**: Query `users.files` for the authenticated user (using existing asyncpg).
- **POST /cloud/save** (new file_name): Append `file_name` to `users.files`.
- **POST /cloud/save** (existing file_name): No change to `users.files` — only `reconciliation_data` is upserted.

## Validation Rules

### POST /cloud/save

| Field        | Type                                            | Required | Validation                                 |
|-------------|-------------------------------------------------|----------|--------------------------------------------|
| `file_name` | string                                           | Yes      | Non-empty, max 255 chars                   |
| `file_data` | array[object]                                    | Yes      | Must be a non-empty list of objects        |
| Each entry  | `{name: str, description: str, debit_credit_value: float, category: str}` | N/A | Types validated; extra fields allowed (pass-through) |

## State Transitions

**Upsert Logic (POST /cloud/save)**:

```
┌──────────────┐
│  Receive     │
│  POST request│
│  with        │
│  file_name   │
│  + file_data │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Is          │      No       ┌──────────────────┐
│  file_name   ├──────────────►│  INSERT new      │
│  existing?   │               │  reconciliation  │
│              │               │  record          │
└──────┬───────┘               │  + append to     │
       │                       │  users.files     │
       │ Yes                   └──────────────────┘
       │
       ▼
┌──────────────────┐
│  UPDATE existing │
│  reconciliation  │
│  record (upsert) │
│  Keep file_name  │
│  Replace data    │
└──────────────────┘
```

## Key Relationships

- **User 1──* ReconciliationData**: One user can have many reconciliation records (via `reconciliation_data.user_id` FK).
- **ReconciliationData.file_name ↔ Users.files[]**: The string values in `users.files` reference `reconciliation_data.file_name`. This is a loose reference (not a formal FK constraint on the JSONB array).
