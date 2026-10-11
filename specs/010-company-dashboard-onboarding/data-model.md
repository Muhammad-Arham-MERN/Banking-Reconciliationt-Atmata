# Phase 1 Data Model — Company Dashboard & Onboarding Flow

**This specification adds no database tables and no migrations.** The only persisted domain state it touches is the existing `companies` table (008), which it reads to authenticate a company. Everything else the spec describes — the company request submission, the Company Requests category, the employees table, and the subscription card — is frontend structure rendered from placeholder data, exactly as FR-024 and the Clarifications state.

The entities below therefore fall into three kinds: **existing (read)**, **client-only (not persisted)**, and **placeholder (demo data, not persisted at all)**.

---

## Entity: Company (existing — read + credential verification)

The Developer-onboarded organization from 008's `companies` table. This feature **reads** it to verify a sign-in and does not change its shape.

| Attribute used | Source | Notes |
|---|---|---|
| `id` | `companies.id` (SERIAL) | Returned to the client as a **string** (008 research R11 — SERIAL can exceed the JS safe-integer range) |
| `name` | `companies.name` | The company's identifier at sign-in; matched **case-insensitively, trimmed** (FR-027) |
| `password_encrypted` | `companies.password_encrypted` | Fernet token (008). Decrypted only to compare at sign-in; **never returned to the client** |
| `logo_filename` | `companies.logo_filename` | Used to build `logo_url` so the dashboard can show the company's mark; `NULL` → no logo |

### Authentication read path (new)

```sql
SELECT id, name, logo_filename, password_encrypted
FROM companies
WHERE lower(name) = lower($1)   -- $1 = trimmed input; served by uq_company_name_lower
LIMIT 1;
```

**Rules**
- The input name is **trimmed**, then matched case-insensitively (FR-027). An empty input is a missing field, not a lookup.
- The stored ciphertext is decrypted with `company_crypto_service.decrypt_password` and compared **constant-time** (`hmac.compare_digest`) against the submitted password (R5).
- **An unknown company and a wrong password produce the identical generic 401** — the response never discloses which field failed (FR-017).
- A missing/invalid `FERNET_KEY` fails closed with **503 `encryption_unavailable`**; nothing is written (008 precedent).

### Validation rules

1. `company_name` — required; trimmed; rejected if empty → **400 `missing_field`**.
2. `password` — required; rejected if empty → **400 `missing_field`** (same generic path as a wrong password at the boundary).

---

## Entity: Company Session (client-only — not persisted server-side)

The authenticated company context, established by a successful sign-in and required to view the dashboard (FR-018). Held in the browser, mirroring 008's admin session store.

| Field | Type | Notes |
|---|---|---|
| `token` | string | The company JWT (HS256, signed with `COMPANY_JWT_SECRET`) issued by `POST /api/company/login` |
| `company.id` | string | Stringified company id |
| `company.name` | string | The company's name as stored (echoed back for the sidebar header) |
| `company.logo_url` | string \| null | Optional; the dashboard may show the mark in the sidebar |
| `expires_at` | string (ISO-8601) | Sign-in time + **24 hours** (FR-018 + clarification) |

**Storage**: `localStorage` under a single key (e.g. `camri_company_session`), because the clarification requires the session to **survive browser restarts** for 24 hours (R3). The frontend reads it through an external store (`useSyncExternalStore` + a cached snapshot + a server snapshot of `null`), exactly like `frontend/src/lib/admin/admin-session.ts`, to avoid a hydration mismatch.

**Lifecycle**

```text
  (sign in)                24h elapse / cleared
      │                            │
      ▼                            ▼
 ┌──────────┐               ┌───────────┐
 │ signed in│ ────────────▶ │ signed out│ ──▶ sign-in form shown
 └──────────┘               └───────────┘
       ▲
       │  any 401 from the API also clears the session and returns the form
       └──────────────────────────────────────────────────────────────────
```

- The dashboard content is shown **only** while a non-expired session exists; otherwise the sign-in form is shown (FR-015/FR-018).
- Expiry is enforced on read: an entry whose `expires_at` is in the past is treated as signed out and cleared.
- There is no refresh token and no "remember me" toggle — the 24-hour window is the whole rule.

---

## Entity: Company Request (placeholder — never persisted)

A submission from the cinematic onboarding flow. Per FR-026 and the clarification, **nothing is stored** — not on the client, not on the server.

| Field | Type | Notes |
|---|---|---|
| `company_name` | string | Question 1 |
| `role` | string | Question 2 — what the company does |
| `website_socials` | string | Question 3 — a URL/domain or an `@handle` |
| `email` | string | Question 4 (contact step) |
| `phone` | string | Question 4 (contact step) |
| `submitted_at` | string (ISO-8601) | Captured in memory for the session only; discarded on close |

**Rules**
- Validation mirrors the onboarding checks (R10): name/role non-empty; website/socials a web address or handle; email email-shaped; phone digits with optional separators (FR-008).
- **No storage of any kind.** The success message (FR-011) is the only outcome; the Admin Dashboard's Company Requests view renders **placeholder** rows (R14/R15) with an empty state.

---

## Entity: Employee (existing — read-only, placeholder in this spec)

The employee access request from 009's `employees` table. This specification **does not read or write that table**; it only mirrors the shape for the dashboard's placeholder rows.

| Attribute displayed | Mirrors (009) | Notes |
|---|---|---|
| Employee name | `employees.employee_name` | Table column |
| Employee ID | `employees.employee_id` | `adam-` prefixed handle |
| Status | `employees.status` | `pending` / `accepted` / `denied`; shown as a badge |
| Grant Access | — | A **local** toggle this spec adds; persistence is deferred (FR-021) |

**Rules**
- "Grant Access" flips a row's local `granted` state only; it is **not** a write to 009's table (FR-021 + spec Assumptions).
- Rows come from `company-placeholder.ts`; an **empty state** is shown when there are none (FR-020/024).

---

## Entity: Company Dashboard Sidebar Item

One of exactly two navigation entries (FR-019): **Employees** and **Subscription**. Rendered by the Aceternity sidebar (R11). Purely navigational — it selects which section the main area shows.

---

## Relationships

```text
Company (008)      ──verifies──▶  Company Session (client)        [read-only on the server]
Company Session    ──shows──▶     Employee rows (placeholder)     [no DB read]
Company Request    ──(none)──▶    nothing                        [never persisted]
```

- **No foreign keys, no joins, no writes.** The backend touches only the existing `companies` SELECT for sign-in.
- The company session is scoped to the Company Dashboard and is independent of the admin session and the Google-user session.

## Storage layout

No new files on the backend. The only new client storage is the `localStorage` session key described above.

```text
backend/
└── data/company_logos/     # EXISTING (008) — not written by this feature
```

## Volume & scale

- Tens of companies; one sign-in request per company session. No pagination, no listing endpoint beyond the existing admin one.
- The dashboard's tables render a handful of placeholder rows; scale is a non-issue.

## Assumptions carried from the spec

- The company name is the company's sign-in identifier (no separate username) — consistent with 008's decision.
- The 24-hour company session is client-held; a signed token is issued now so the later backend specification can add company-scoped endpoints without a redesign.
- Requests, employees, and the subscription card are frontend structure with placeholder data; real data wiring is the next specification's job.
