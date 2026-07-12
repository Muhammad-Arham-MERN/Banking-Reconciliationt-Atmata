# Data Model: Google OAuth Authentication

## Auth.js Managed Tables (auto-created by `@auth/pg-adapter`)

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| name | VARCHAR(255) | nullable |
| email | VARCHAR(255) | nullable |
| emailVerified | TIMESTAMPTZ | nullable |
| image | TEXT | nullable |
| files | JSONB | nullable, default `[]`, array of file_name strings referencing Reconciliation_data |

### accounts
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| userId | INTEGER | NOT NULL, FK -> users.id |
| type | VARCHAR(255) | NOT NULL |
| provider | VARCHAR(255) | NOT NULL |
| providerAccountId | VARCHAR(255) | NOT NULL |
| refresh_token | TEXT | nullable |
| access_token | TEXT | nullable |
| expires_at | BIGINT | nullable |
| id_token | TEXT | nullable |
| scope | TEXT | nullable |
| session_state | TEXT | nullable |
| token_type | TEXT | nullable |

### sessions
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| userId | INTEGER | NOT NULL, FK -> users.id |
| expires | TIMESTAMPTZ | NOT NULL |
| sessionToken | VARCHAR(255) | NOT NULL |

### verification_token
| Column | Type | Constraints |
|--------|------|-------------|
| identifier | TEXT | NOT NULL, part of composite PK |
| expires | TIMESTAMPTZ | NOT NULL |
| token | TEXT | NOT NULL, part of composite PK |
| PRIMARY KEY | (identifier, token) | composite |

## Custom Table

### reconciliation_data
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment internal ID |
| file_name | VARCHAR(255) | UNIQUE NOT NULL | Referenced from users.files array |
| data | JSONB | NOT NULL | Array of discrepancy objects |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | Record creation timestamp |

**reconciliation_data.data structure** (JSON array):
```json
[
  {
    "name": "string",
    "description": "string",
    "debit_credit_value": 0.0,
    "category": "string"
  }
]
```

## Relationships

- **User** 1---* **Reconciliation_data** (via `users.files[]` referencing `reconciliation_data.file_name`)
  - No formal FK constraint; association is application-level by matching file_name strings
- **User** 1---* **Session** (Auth.js managed, FK via userId)
- **User** 1---* **Account** (Auth.js managed, FK via userId)

## Session Model

- **Strategy**: JWT (encoded, self-contained)
- **Duration**: 24 hours from sign-in (`maxAge: 86400`)
- **Refresh**: None — user must re-authenticate after expiry
- **Storage**: JWT in HTTP-only cookie, no server-side session table used (JWT strategy)
