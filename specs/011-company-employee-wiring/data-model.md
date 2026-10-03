# Data Model — Company-Employee Dashboard Wiring

**Feature**: `011-company-employee-wiring` | **Date**: 2026-10-02 | **Spec**: [spec.md](./spec.md)
**Storage**: CockroachDB via raw `asyncpg` (`db_service`, `$n` placeholders). No ORM.

Existing tables are extended; one table is added. All changes are additive and safe to apply to current data.

---

## 1. `users` (existing — unchanged, now referenced)

Auth.js (NextAuth) adapter account table. `id SERIAL PK`, `name`, `email`, `emailVerified`, `image`, `files JSONB`.

- **Role in this feature**: the sign-in identity. An employee record references a `users.id`; the membership gate resolves `users.id → accepted employees row`.
- **Linkage (FR-011)**: `employees.account_user_id` already stores `users.id` (populated from `request.state.user_id`). This feature makes the linkage traversable both ways: `users.id → employees.account_user_id`.
- **Optional enhancement**: add `FOREIGN KEY (account_user_id) REFERENCES users(id)` to `employees` if no orphan rows exist (guarded migration). Not required for correctness — the middleware already guarantees the `users` row exists — so it is optional.

---

## 2. `companies` (existing — one derived field added to the API payload)

`id SERIAL PK`, `name` (case-insensitively unique), `logo_filename`, `password_encrypted` (Fernet), `price_rupees` (≥0), `payment_status ∈ {pending, free_trial, paid}`, `created_at`, `updated_at`.

- **Change (FR-018)**: the admin list payload gains `employee_count` — computed with a `LEFT JOIN`/scalar subquery over `employees`; **not** stored.
- **Deletion behavior (FR-023)**: `delete_company` also deletes the company's `employees` rows (explicit cascade, since there is no FK on `employees.company_id`).

---

## 3. `employees` (existing — extended)

The access-request record; also the membership/authorization record.

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `employee_name` | VARCHAR(255) NOT NULL | |
| `employee_id` | VARCHAR(64) NOT NULL | canonical `adam-` + 6–12 lowercase alnum |
| `company_id` | INTEGER NOT NULL | **no FK** (keeps admin hard-delete working) |
| `company_name` | VARCHAR(255) NOT NULL | snapshot at request time |
| `account_user_id` | INTEGER NOT NULL | the signed-in `users.id` that submitted it |
| `account_email` | VARCHAR(255) NOT NULL DEFAULT '' | snapshot of the submitter's email |
| `status` | VARCHAR(16) NOT NULL DEFAULT 'pending' | `pending` \| `accepted` \| `denied` |
| **`is_manager`** | **BOOLEAN NOT NULL DEFAULT false** | **NEW** — the Manager flag (FR-019) |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | |

**Indexes / constraints**
- Existing: `UNIQUE (employee_id, company_id)`; `CHECK (employee_id LIKE 'adam-%')`; `CHECK (status IN ('pending','accepted','denied'))`.
- **NEW**: `CREATE INDEX IF NOT EXISTS idx_employees_account_user_id ON employees(account_user_id)` — serves the membership gate and the "one active request" check.
- **NEW (optional)**: `CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees(company_id)` — serves the company dashboard list and the cascade delete.

**State transitions**
```text
(none) --submit request--> pending
pending --company grants--> accepted        # FR-003
pending --company deletes--> (row gone)     # FR-004
accepted --company deletes--> (row gone)    # FR-004, access revoked
accepted --employee leaves (DELETE /api/me/membership)--> (row gone)   # FR-015
* --company is deleted--> (row gone, cascade)                          # FR-023
pending --cancel (employee)--> (row gone)   # FR-017
is_manager: false <--toggle--> true         # FR-019 (any dashboard user)
```

**Validation rules**
- `employee_id` normalized by `employee_service.normalize_employee_id` (prefix added if missing, lowercased, 6–12 `[a-z0-9]`).
- **One active request/membership per account (FR-017/FR-025)**: a new request is rejected when the account already has a row with `status IN ('pending','accepted')`. Enforced in `employee_service` (lookup by `account_user_id`); see research D3 for why this is not a DB unique index.
- `is_manager` is only meaningful on an `accepted` row (a non-member manager is an edge case guarded by the nav logic, and is preserved only if the row exists).

---

## 4. `company_requests` (NEW — onboarding inbox, view-only)

A "Company Request" onboarding submission. Stored so the Developer can read it in the Admin Dashboard. **No status; no link to account creation** (per clarification).

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `company_name` | VARCHAR(255) NOT NULL | |
| `role` | VARCHAR(255) NOT NULL DEFAULT '' | what the company does |
| `website_socials` | VARCHAR(255) NOT NULL DEFAULT '' | URL or social handle |
| `email` | VARCHAR(255) NOT NULL DEFAULT '' | |
| `phone` | VARCHAR(64) NOT NULL DEFAULT '' | |
| `account_user_id` | INTEGER | submitter's `users.id` (nullable; informational) |
| `account_email` | VARCHAR(255) NOT NULL DEFAULT '' | submitter's email snapshot |
| `submitted_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | ordering key |

**Index**
- `CREATE INDEX IF NOT EXISTS idx_company_requests_submitted_at ON company_requests(submitted_at DESC)`.

**Validation (server-side, FR-006)**: `company_name` required (non-empty, ≤255); the remaining fields are captured as submitted (the cinematic flow already applies basic format checks in the browser). `email`/`phone`/`role`/`website_socials` are stored as `''` when blank.

---

## 5. Membership (derived — not a table)

The authorization that gates the application (FR-009/FR-010/FR-024) and drives the nav (FR-015/FR-016/FR-020). Derived from `employees`:

```text
membership(account_user_id) :=
  SELECT e.id, e.employee_id, e.status, e.is_manager, e.company_id, e.company_name
  FROM employees e
  WHERE e.account_user_id = $1 AND e.status = 'accepted'
  LIMIT 1
```

- **Application access** ⇔ a membership exists (server-enforced on the NextAuth branch).
- **Data scope** ⇔ none: the membership is a *gate only*; the employee's reconciliation data stays their own (FR-024).
- **Browse/leave**: leaving deletes the `employees` row → membership resolves to null.

---

## 6. Relationship map

```text
users 1 ──── 0..1 employees (per account, at most one active row)   # FR-025
companies 1 ── * employees (company_id, no FK; explicit cascade on delete)  # FR-023
companies 1 ── * company_requests? (none — separate inbox)          # clarification
employees.status = accepted  ==>  Access Grant (derived)            # FR-003/FR-009
employees.is_manager = true  ==>  "Company Dashboard" nav entry (when accepted)  # FR-019/FR-020
```

---

## 7. Sign convention (data-level)

The canonical credit/debit mapping is defined in [contracts/sign-convention.md](./contracts/sign-convention.md). At the data layer it means: the `reconciliation_data.data` JSONB `Debit/Credit` values for **Bank** and **Vendor** source rows must be written with the new polarity (Bank debit +, credit −; Vendor debit −, credit +) from this feature onward. Existing rows are not backfilled (research D6). The stored `reconciliation_type` (`bank` | `vendor`) already distinguishes the two ledgers.

---

## 8. Migration summary (added to `backend/src/models/db_migrations.py`, appended to `MIGRATIONS`)

```sql
-- NEW: onboarding requests (view-only inbox)
CREATE TABLE IF NOT EXISTS company_requests ( ... );

CREATE INDEX IF NOT EXISTS idx_company_requests_submitted_at
  ON company_requests(submitted_at DESC);

-- EXTEND: employees
ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_manager BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_employees_account_user_id ON employees(account_user_id);
CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees(company_id);

-- OPTIONAL (guarded): link to the sign-in account
-- ALTER TABLE employees ADD CONSTRAINT fk_employees_account_user
--   FOREIGN KEY (account_user_id) REFERENCES users(id);
```

All statements are idempotent (`IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`), matching the existing migration style.
