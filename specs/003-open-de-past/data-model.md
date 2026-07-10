# Data Model: Open de Past

**Branch**: `003-open-de-past` | **Date**: 2026-07-03 | **Phase**: 1

## Entities

### ReconciliationHistoryFile

A single SQLite database file stored on disk representing one saved reconciliation session.

| Attribute | Type | Notes |
|-----------|------|-------|
| file_name | string | Auto-generated date-time (e.g. `2026-07-03_14-30-00`) or user-provided custom name. Used as the SQLite filename with `.sqlite` extension. |
| file_path | string | Full path: `Reconciliation History/{file_name}.sqlite` |
| created_at | datetime | Timestamp when the file was saved |
| entry_count | integer | Number of discrepancy entries in this file |

### DiscrepancyEntry

A single row inside a ReconciliationHistoryFile SQLite database.

| Attribute | Type | Details |
|-----------|------|---------|
| id | INTEGER | Auto-increment primary key |
| category | TEXT | One of: `"Unpresented Checks"`, `"Uncleared Checks"`, `"Bank Debited But not Credited in Cashbook"`, `"Bank Credited But not Debited in Cashbook"` |
| transaction_details | TEXT | Transaction description (from the original statement) |
| transaction_date | TEXT | Transaction date stored as ISO-8601 string (e.g. `2026-06-15`) |
| debit_credit_amount | REAL | Numeric amount. Debits are positive, credits are negative, or follow the existing sign convention from the reconciliation system. |
| from_past | INTEGER | Boolean: 0 = current reconciliation, 1 = loaded from history |

### ReconciliationHistoryDirectory

A logical entity representing the `Reconciliation History/` folder at the project root.

| Attribute | Value |
|-----------|-------|
| location | `<project-root>/Reconciliation History/` |
| created_on | First save if directory doesn't exist |

## SQLite Schema

Each history file is a self-contained SQLite database with a single table:

```sql
CREATE TABLE IF NOT EXISTS discrepancies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK (category IN (
        'Unpresented Checks',
        'Uncleared Checks',
        'Bank Debited But not Credited in Cashbook',
        'Bank Credited But not Debited in Cashbook'
    )),
    transaction_details TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    debit_credit_amount REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discrepancies_category ON discrepancies(category);
CREATE INDEX IF NOT EXISTS idx_discrepancies_date ON discrepancies(transaction_date);
```

Note: `from_past` is NOT stored in the SQLite file — it's assigned at query time when discrepancies are loaded from a history file during a new reconciliation session. This keeps history files clean and reusable.

## State Transitions

```
[Reconciliation Complete]
         |
         v
[User clicks "Complete Reconciliation"]
         |
         ├── Custom name provided? → Validate uniqueness
         │                            ├── Name exists → Show notification, abort save
         │                            └── Name unique → Use custom name
         │
         └── No custom name → Auto-generate date-time name
         |
         v
[Save discrepancies to SQLite file]
         |
         ├── Success → Confirm saved
         └── Failure → Show error, keep results on screen (user can retry)
```

```
[New Session: User selects Open Maazi]
         |
         v
[Selected history file loaded → discrepancies cached]
         |
         v
[User uploads files, runs reconciliation]
         |
         v
[Merge: past discrepancies + new discrepancies]
         |
         ├── Same (details + date) → Suppress past duplicate
         └── Different (details only) or unique → Include both, mark past with fromPast=true
         |
         v
[Display merged results: entries sorted by date within each category]
```

## Validation Rules

- **category**: Must be exactly one of the four valid values
- **transaction_details**: Must be non-empty
- **transaction_date**: Must be a valid ISO-8601 date string
- **debit_credit_amount**: Must be a finite number (not NaN, not infinity)
- **file_name**: Must not collide with an existing file (skip + notify rather than overwrite)
