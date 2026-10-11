# Phase 1 Data Model — Admin Dashboard (Camri Desk)

Two entities carry data: the **Admin Credential** (configuration, not a table) and the **Company** (a new table). The company's password is a conceptually distinct **Company Credential** stored as a column on the company row.

---

## Entity: Admin Credential

Not persisted in the database. Supplied entirely through the backend environment, per FR-003.

| Attribute | Source | Rules |
|-----------|--------|-------|
| username | `ADMIN_USERNAME` env | Required for a successful sign-in; compared case-sensitively |
| password | `ADMIN_PASSWORD` env | Required for a successful sign-in; compared with a constant-time comparison |
| token signing secret | `ADMIN_JWT_SECRET` env | Signs the issued admin JWT (HS256) |
| token lifetime | `ADMIN_JWT_TTL_HOURS` (optional, default 12) | Backstop only; `sessionStorage` is what ends the session on browser close |

**Rules**
- There is exactly one admin. No registration, no password reset, no roles (spec Assumptions).
- Credentials are never sent to the browser and never logged.
- A failed sign-in returns one generic message regardless of which field was wrong (FR-004).

**Identity invariant**: a valid admin token authorizes every `/api/admin/*` request except `POST /api/admin/login` itself (FR-005).

---

## Entity: Company

The onboarded client organization (FR-006–FR-020).

### Table: `companies`

```sql
CREATE TABLE IF NOT EXISTS companies (
    id                 SERIAL PRIMARY KEY,
    name               VARCHAR(255) NOT NULL,
    logo_filename      VARCHAR(255),
    password_encrypted TEXT         NOT NULL,
    price_rupees       INTEGER      NOT NULL,
    payment_status     VARCHAR(16)  NOT NULL DEFAULT 'pending',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_company_payment_status
        CHECK (payment_status IN ('pending', 'free_trial', 'paid')),
    CONSTRAINT chk_company_price_non_negative
        CHECK (price_rupees >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_company_name_lower
ON companies (lower(name));
```

Both statements are appended to the ordered `MIGRATIONS` list in `backend/src/models/db_migrations.py` (idempotent, matching how `reconciliation_data` and `pdf_structure_profiles` were added).

### Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | SERIAL PK | system | Returned to the client as a **string** (CockroachDB `SERIAL` can exceed JS safe-integer range — see research R11) |
| `name` | VARCHAR(255) | ✅ | The company's identifier. Unique, case-insensitively (FR-011, edge case) |
| `logo_filename` | VARCHAR(255) | ❌ | Generated filename in `COMPANY_LOGO_DIR`; `NULL` when no logo (FR-009). Never a user-supplied path |
| `password_encrypted` | TEXT | ✅ | Fernet token of the company access password (FR-017). Never plaintext; never returned to the client |
| `price_rupees` | INTEGER | ✅ | Whole Rupees, ≥ 0. Recurring per period. **Stored only — no billing logic** (FR-015) |
| `payment_status` | VARCHAR(16) | ✅ (defaults) | One of `pending`, `free_trial`, `paid`; new rows default to `pending` (FR-014) |
| `created_at` | TIMESTAMPTZ | system | Set on insert |
| `updated_at` | TIMESTAMPTZ | system | Refreshed on every update |

### Derived / non-persisted fields (API only)

| Field | Type | Notes |
|-------|------|-------|
| `has_password` | boolean | Always `true` for a valid row; exists so the list response signals that a password is revealable without shipping the secret (research R5) |
| `logo_url` | string \| null | `/api/admin/companies/{id}/logo` when a logo exists, else `null` — so the client never builds file paths |
| `password` | string | **Only** on the dedicated reveal response, decrypted on demand (FR-018) |

### Validation rules

1. `name` — required; trimmed; rejected if empty/whitespace-only (FR-011); rejected with **409 `company_name_exists`** if it collides case-insensitively with an existing row.
2. `price_rupees` — required; integer; `>= 0`; rejected with **422** otherwise.
3. `payment_status` — must be one of the three identifiers; defaults to `pending` when omitted; anything else rejected with **422** before it reaches the DB (the `CHECK` constraint is the backstop).
4. `password` — required on create; non-empty. Random generation is a *client* convenience (FR-010); the server accepts whatever string it is given and encrypts it.
5. `logo` — optional; extension and content must be PNG, JPG/JPEG, or SVG (FR-009); any other type rejected with **415**; **no size cap** is imposed by this feature (clarification). Stored under a generated filename, never the client-provided name.
6. `FERNET_KEY` — if missing/malformed, create and update fail closed with **503 `encryption_unavailable`** and write nothing (FR-017).

### State transitions

Only one field is stateful — `payment_status`:

```
        (create)
            │
            ▼
       ┌─────────┐   admin / later company dashboard   ┌────────────┐
       │ pending │ ───────────────────────────────────▶ │ free_trial │
       └─────────┘                                      └────────────┘
            │                                                  │
            │                                                  ▼
            │                                            ┌────────┐
            └──────────────────────────────────────────▶ │  paid  │
                                                         └────────┘
```

- All three states are reachable from any other; the admin may set any value from this dashboard (FR-012, FR-014).
- The **later company-facing dashboard is the primary manager** of this field (clarification); this spec only needs it displayed and settable.
- No other lifecycle exists: a company is created, edited any number of times, and deleted (hard delete). Deletion revokes access (FR-013); the logo file is removed best-effort after the row is deleted.

---

## Relationships

None. This feature is deliberately flat — no foreign keys, no membership/employee tables, no tenancy.

- A **Company** has no link to the existing `users` table. The company-facing login and its link to employees are later specs.
- The existing `reconciliation_data.user_id → users.id` relationship is untouched.
- The only cross-entity interaction is that a company's `logo_filename` points into `COMPANY_LOGO_DIR` (a filesystem location, not a DB relationship).

## Storage layout

```text
backend/
├── uploads/                      # EXISTING — reconciliation files, wiped in 20 min / on shutdown
└── data/
    └── company_logos/            # NEW — COMPANY_LOGO_DIR; NOT touched by any cleanup routine
        └── <uuid4>.png|.jpg|.svg # generated names; only the filename is stored in the DB
```

Keeping logos out of `uploads/` is the single most important storage decision in this feature (research R6): the existing retention and shutdown sweeps would otherwise delete every logo.

## Volume & scale

- Tens of companies; a single admin; one row per company. No pagination needed (FR-006 lists all).
- Logo files are small images; no size limit is imposed by this feature, so a logo is streamed to disk on upload rather than buffered wholly in memory.

## Assumptions carried from the spec

- Company name doubles as the later company-facing username (no separate username column).
- `price_rupees` is data only; the Developer builds the price/billing structure in a later spec.
- Company logo is optional; the list shows a placeholder when absent.
