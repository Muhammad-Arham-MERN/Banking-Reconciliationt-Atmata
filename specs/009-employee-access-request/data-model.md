# Phase 1 Data Model — Employee Access Request (Subscription Layer)

One new persistable entity: the **Employee access request**. The **Company** entity already exists (008) and is only read here. Nothing else is stored.

---

## Entity: Employee (access request)

A person who asked a specific company to grant them access, submitted from the subscription page.

### Table: `employees`

```sql
CREATE TABLE IF NOT EXISTS employees (
    id              SERIAL       PRIMARY KEY,
    employee_name   VARCHAR(255) NOT NULL,
    employee_id     VARCHAR(64)  NOT NULL,
    company_id      INTEGER      NOT NULL,
    company_name    VARCHAR(255) NOT NULL,
    account_user_id INTEGER      NOT NULL,
    account_email   VARCHAR(255) NOT NULL DEFAULT '',
    status          VARCHAR(16)  NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_employee_status
        CHECK (status IN ('pending', 'accepted', 'denied')),
    CONSTRAINT chk_employee_id_prefix
        CHECK (employee_id LIKE 'adam-%')
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_employee_id_company
ON employees (employee_id, company_id);
```

Both statements are appended to the ordered `MIGRATIONS` list in `backend/src/models/db_migrations.py` (idempotent, exactly how `companies` was added by 008).

### Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | SERIAL PK | system | Returned to the client as a **string** (CockroachDB `SERIAL` can exceed the JS safe-integer range — 008 research R11) |
| `employee_name` | VARCHAR(255) | ✅ | Trimmed; whitespace-only rejected (FR-008, FR-014). Stored as typed |
| `employee_id` | VARCHAR(64) | ✅ | Canonical `adam-` + 6–12 lowercase alphanumerics, normalized server-side (FR-011). Always starts with `adam-`; the `CHECK` is the backstop |
| `company_id` | INTEGER | ✅ | The requested company's stable id (FR-016). Validated to exist at submit time; **no DB foreign key** so the admin can still hard-delete a company (research R6) |
| `company_name` | VARCHAR(255) | ✅ | Snapshot of the company name exactly as shown in the dropdown at submit time (FR-016) — the record stays readable after a rename or delete |
| `account_user_id` | INTEGER | ✅ | The signed-in account that submitted the request — `request.state.user_id` (the `users.id`) (FR-016) |
| `account_email` | VARCHAR(255) | system | `request.state.user_email`, defaulting to `''` if absent. Not required by the spec; kept so the later company spec can reach the employee without a join |
| `status` | VARCHAR(16) | ✅ (defaults) | One of `pending`, `accepted`, `denied`; new rows always default to **`pending`** (FR-016). Only `pending` is produced by this feature |
| `created_at` | TIMESTAMPTZ | system | Set on insert (FR-016 — "when it was made") |
| `updated_at` | TIMESTAMPTZ | system | Refreshed on every update; unused by this feature, present for the later company decision |

### Derived / non-persisted fields (API response only)

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Stringified SERIAL (above) |
| `company_id` | string | Stringified for the same reason; the request body sends it as a string too |

### Validation rules

1. `employee_name` — required; trimmed; rejected if empty/whitespace-only → **400 `missing_field`** (FR-008, FR-014).
2. `employee_id` — required. Normalization: trim → lowercase → strip one leading `adam-` if present → require `^[a-z0-9]{6,12}$`; store `adam-` + value. Anything else → **400 `invalid_employee_id`** (FR-011). Because the stored value is always lowercase, the unique index needs no expression.
3. `company_id` — required; must parse to an integer and match an existing `companies.id` → otherwise **404 `company_not_found`** (FR-009).
4. Duplicate — the pair (`employee_id`, `company_id`) must not already exist → **409 `employee_id_taken`** (FR-013). The same ID against a *different* company is accepted and recorded (FR-013 + edge case).
5. `status` — not client-settable; always written as `pending` (FR-016). The `CHECK` constraint is the backstop.

### Generated-ID rules (client-side convenience, server-enforced)

- The "Generate" control fills the field with `adam-` + 8 characters from `[a-z0-9]`, produced with `crypto.getRandomValues` (FR-010); the value stays editable.
- Generation is **not** trusted: the server re-normalizes and re-validates whatever arrives, so a typed value and a generated value follow the same rules.

### State transitions

Only `status` is stateful, and this feature only ever writes the first state:

```text
   (submit)
       │
       ▼
  ┌─────────┐   company decision (LATER specification)   ┌──────────┐
  │ pending │ ─────────────────────────────────────────▶ │ accepted │
  └─────────┘                                           └──────────┘
       │
       │                                                ┌────────┐
       └──────────────────────────────────────────────▶ │ denied │
                                                        └────────┘
```

- `pending` is the only state created here (FR-016; spec Assumptions).
- `accepted` / `denied` are declared in the `CHECK` now so the later company specification can set them without an `ALTER TABLE`, but **nothing in this feature transitions a row**.
- No delete path is exposed by this feature.

---

## Entity: Company (existing — read only)

The Developer-onboarded organization (008's `companies` table). This feature reads it and never writes it.

| Attribute used | Source | Notes |
|---|---|---|
| `id` | `companies.id` (SERIAL) | Exposed as a string; used as the dropdown value and stored on the request |
| `name` | `companies.name` | Dropdown label; snapshotted onto the request |
| `logo_filename` | `companies.logo_filename` | `NULL` when no logo → the dropdown shows a placeholder (FR-009) |

Read path: `company_service.list_companies()` for the dropdown; `company_service.get_company(id)` for the logo lookup and the submit-time existence check. **No change to the company record set** (spec Key Entities).

---

## Relationships

```text
employees.company_id     ──logical──▶  companies.id     (no DB FK; R6)
employees.account_user_id──logical──▶  users.id         (no DB FK)
```

- No DB-level foreign keys, matching 008's deliberate "this feature is flat" design (research R6).
- Neither link is ever orphaned in practice: `company_id` is validated on insert, and `users.id` comes from the authenticated session the middleware already resolved.
- The company name is **denormalized on purpose**: the request must still read correctly after the Developer renames or removes a company.

## Uniqueness / identity invariant

- **Employee identity here is the `employee_id` string**, not a user account: two different signed-in accounts could submit the same `adam-` ID for the same company only if the first had not — the composite unique index is the single source of truth.
- The invariant that must hold for the product to work: *within one company, an `adam-` ID appears at most once.*

## Storage layout

No new files or directories. Logos stay where 008 put them:

```text
backend/
└── data/
    └── company_logos/     # EXISTING — read by GET /api/companies/{id}/logo; never written here
```

## Volume & scale

- Tens of companies; a handful of requests per employee. One row per accepted submission, no pagination needed, no listing endpoint in this feature.
- `employees` grows at human speed (one row per submit); no retention or cleanup applies.

## Assumptions carried from the spec

- Employee identity at submit time is the existing Google sign-in; the recorded `account_user_id` is what the company will later grant access to.
- `company_id` + `company_name` are both stored so the later company specification can match by id and display by name.
- New requests start `pending`; acceptance/denial is the later company specification's job.
