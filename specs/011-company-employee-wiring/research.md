# Phase 0 Research — Company-Employee Dashboard Wiring, Sign Conventions & Edge Cases

**Feature**: `011-company-employee-wiring` | **Date**: 2026-10-02
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document records the design decisions that resolve the plan's unknowns. No `[NEEDS CLARIFICATION]` markers remain (all spec ambiguities were closed in `/sp.specify` and `/sp.clarify`); the items below are engineering choices with rationale and alternatives.

---

## D1. Where company-facing employee-management endpoints live

**Decision**: Add a new router `backend/src/api/company_employee_routes.py` mounted at `/api/company/employees*`, gated by the existing **company-JWT** branch of `auth_middleware` (the middleware already rejects any `/api/company/*` path without a valid company token, supplied by `POST /api/company/login`). The company identity comes from `request.state.company_id` / `company_name` (populated by `_handle_company_request`), never from the request body.

**Rationale**: The Company Dashboard is already its own principal with its own token and branch; putting management routes there means zero new auth surface and the company's identity is unspoofable. It also finally gives the company branch a real protected route (today it gates nothing but login).

**Alternatives considered**:
- *Put them under `/api/admin/*`* — wrong principal; the company has no admin token.
- *Put them under the NextAuth branch with a companyId body param* — the company has no Google session at all, so it cannot authenticate; and trusting a body-supplied companyId would be an IDOR risk.

**Endpoints**: `GET /api/company/employees` (list, with `?q=` optional), `POST /api/company/employees/{id}/grant`, `DELETE /api/company/employees/{id}`, `PATCH /api/company/employees/{id}` (`{ is_manager: bool }`).

---

## D2. How the application gate is enforced

**Decision**: Two layers.
1. **Backend (authoritative)** — extend the NextAuth branch of `auth_middleware` with a membership check: after the user row is resolved, if the path is not on the allow-list and the account has no `accepted` employee row, return `403 {"error":"membership_required", ...}`. Allow-list: `/api/company-requests`, `/api/companies` (and its logos), `/api/me/membership`, `/api/employees/requests`, plus the existing public/admin/company prefixes and health/docs.
2. **Frontend (UX)** — a server helper `requireMembership()` in `frontend/src/lib/membership.ts` fetches `GET /api/me/membership` with the session token and `redirect("/subscription")` when there is none; protected RSC pages (`/upload-ai` and any other application page) call it. The shared header becomes membership-aware.

**Rationale**: The spec requires the *application* to be unusable without a grant (FR-009). A frontend-only redirect is trivially bypassable by calling the API directly, so the backend must refuse too. The allow-list is essential: a naive "gate everything" rule would break the very request/dropdown/membership calls the feature needs.

**Alternatives considered**:
- *Frontend-only guards* — bypassable; violates the spirit of FR-009.
- *Per-route dependency on every existing endpoint* — invasive, easy to miss one, and duplicates the middleware's job.
- *Next.js edge `middleware.ts`* — would still need the backend check for real security, and adds a second place to maintain the allow-list; rejected as duplication.

**Note**: The middleware gate must run only on the NextAuth branch (it needs the resolved `users.id`) and must not apply to the admin or company branches.

---

## D3. Enforcing "one active request / one membership per account"

**Decision**: Enforce in `employee_service.create_employee_request` — before inserting, `SELECT id FROM employees WHERE account_user_id = $1 AND status IN ('pending','accepted') LIMIT 1`; if found, raise a typed `ActiveRequestExistsError` → HTTP `409 {"error":"active_request_exists"}`. Add a **non-unique** index on `employees(account_user_id)` to keep the lookup fast. Do **not** add a database unique constraint on `account_user_id`.

**Rationale**: The clarified rule (FR-017/FR-025) is one active request *per account across all companies*, on top of the pre-existing per-`(employee_id, company_id)` uniqueness. A unique index on `account_user_id` would encode the invariant at the DB level, but legacy rows from spec 009 (which allowed one request per company per ID) may already contain multiple rows for one account, so `CREATE UNIQUE INDEX` could fail the migration. A service-level check plus a lookup index is safe to apply to existing data; the existing composite unique index still protects the race on the same company.

**Alternatives considered**:
- *Unique index on `account_user_id`* — strongest, but risks migration failure on legacy data and would also need `denied` rows cleaned up. Deferred; can be added later once data is known-clean.
- *Keep only the per-`(employee_id, company_id)` rule* — contradicts the clarified "one active request at a time overall".

---

## D4. Cascade delete of employee records when a company is deleted

**Decision**: Extend `company_service.delete_company` to delete the company's employee rows in the same operation — `DELETE FROM employees WHERE company_id = $1` — before/after deleting the company row, returning the logo filename as today. No foreign key is added to `employees.company_id` (the 008 design deliberately keeps the admin delete working without one).

**Rationale**: FR-023 requires cascade; the spec's rule is "the company is the cause, the employee record the effect". Because `company_id` has no FK, the cascade must be explicit in the service. Deleting the employee rows also revokes app access (the gate resolves membership from those rows) and satisfies FR-025's one-membership invariant. The user account is untouched.

**Alternatives considered**:
- *Add `ON DELETE CASCADE` FK on `employees.company_id`* — would need the FK (which 008 intentionally avoided) and could fail on existing orphan rows.
- *Soft-delete employees* — contradicts the clarified hard-delete behavior.

**Consistency**: use a short transaction (add a `db_service.transaction()` helper or run the two statements inside one `async with conn.transaction()`) so a failure cannot leave the company gone but employees orphaned.

---

## D5. Company onboarding requests: storage and Admin listing

**Decision**: New table `company_requests` (view-only): `id, company_name, role, website_socials, email, phone, account_user_id, account_email, submitted_at`. Two endpoints:
- `POST /api/company-requests` (NextAuth branch, signed-in submitter) — persist, then best-effort send the notification email (D7), return `201` with the row.
- `GET /api/admin/company-requests` (admin branch) — list newest-first.
No status, no link to company accounts (per the clarification).

**Rationale**: Matches the clarified "view-only inbox, separate from account creation". A dedicated table keeps `companies` limited to genuinely onboarded clients.

**Alternatives considered**:
- *Reuse `companies` with a pending flag* — rejected by the clarification; would clutter the clients list.
- *No persistence (keep 010's visual-only behavior)* — rejected by FR-006.

**Frontend**: the onboarding flow (`company-request-flow.tsx`) currently discards the answers; it will now collect them and POST on completion, then show the existing success message (the flow keeps its cinematic behavior).

---

## D6. Canonical credit/debit sign convention (FR-012…FR-014)

**Decision**: Define one canonical mapping and enforce it in three places — the reconciliation engine that produces `Debit/Credit`, the value persisted in `reconciliation_data`, and the frontend categorization/display/totals. The finalized mapping:

| Ledger | Debit | Credit | Resulting category sign |
|--------|-------|--------|-------------------------|
| Company cashbook | **+** | **−** | Unpresented Checks (credit) = −, Uncleared Checks (debit) = + |
| Bank statement | **+** | **−** | Bank Debited-not-Credited = +, Bank Credited-not-Debited = − |
| Vendor ledger | **−** | **+** | Vendor Debits = −, Vendor Credit = + |

This flips the **current** bank convention (today: bank credit +, debit −) and the **current** vendor convention (today: vendor credit −, debit +). The company/cashbook convention is unchanged.

**Rationale**: The spec gives the required *category* signs; the source rows must be signed so the categories land on those signs. Today's `categorizationUtils.ts` and `ReconciliationTotals.tsx` encode the old bank/vendor polarity, so the change is real and cross-cutting, not cosmetic.

**Implementation touchpoints**:
- **Backend**: the extractor(s) that assign `Debit/Credit` (Bank and Vendor paths) — flip the sign for bank and vendor rows so the canonical mapping holds. Locate via the reconciliation/extraction pipeline (`backend/src/services/*` and the extraction utilities) during `/sp.tasks`.
- **Frontend**: `categorizationUtils.categorizeTransaction` (the `isPositive` tests for bank/vendor), `getDisplayAmount`, `categoryLabel`; `ReconciliationResults.categorizeDiscrepancy`; `ReconciliationTotals` adjustment sums and the adjusted-balance formula. The adjusted totals/verdict must be recomputed so they stay consistent with the displayed signs (FR-014).
- **Persistence**: newly saved reconciliations store the canonical signs; the `reconciliation_type` column already distinguishes bank vs vendor.

**Legacy data**: rows saved before this change were written with the old polarity. No automated backfill is attempted (the original source polarity cannot be reconstructed reliably after the fact). Re-opening a legacy saved file displays its stored values as-is; the Developer can re-run to regenerate under the new convention. Documented as an accepted consequence in the plan/data-model.

**Alternatives considered**:
- *Flip only in the frontend display layer* — rejected: the spec makes the convention canonical through the database, and a display-only flip would make stored values disagree with what history shows.
- *Backfill existing rows* — rejected: ambiguous, risky, and unnecessary for a local tool.

---

## D7. Resend notification email

**Decision**: Add the `resend` Python package. New `notification_service.py` with `send_company_request_notification(request)`. Config (env, added to `config.py`): `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `COMPANY_REQUEST_NOTIFY_EMAIL` (default `ArhamBrowser@gmail.com`). Called **after** the row is stored; wrapped so any failure is logged and swallowed — the API still returns `201` (FR-007). When `RESEND_API_KEY` is unset, the send is skipped with a warning (dev-friendly, never blocks).

**Rationale**: The Developer named Resend explicitly. Fail-soft ordering guarantees a mail outage cannot lose a request — the request is the source of truth, the email a convenience.

**Alternatives considered**:
- *Send before persisting* — a mail failure could 500 and lose the request.
- *SMTP/other provider* — not requested; stack authority.

---

## D8. Representing the Manager role

**Decision**: Add `is_manager BOOLEAN NOT NULL DEFAULT false` to `employees`. The "Company Dashboard" nav entry renders only when the signed-in account is **both** an `accepted` member **and** `is_manager = true` (FR-019/FR-020). Any caller with dashboard access (company account or an existing manager) may toggle it (FR-019).

**Rationale**: The clarified model makes Manager an additive flag on the account's employee record, not a separate principal. A boolean on the row is the smallest change and keeps the single-membership invariant.

**Alternatives considered**:
- *Separate `managers` table* — overkill for one boolean and complicates the "one membership" rule.
- *Reuse `role` varchar* — no second role exists; a boolean is simpler and self-documenting.

---

## D9. Fix the dangling company logo URL

**Decision**: `POST /api/company/login` currently returns `logo_url = /api/company/{id}/logo`, but no such route exists. Add `GET /api/company/{company_id}/logo` on the company-JWT branch (mirroring the admin/employee logo endpoints' safety headers) and keep the login response pointing at it.

**Rationale**: A dangling URL is a latent bug on the company branch this feature activates; the dashboard may render the company logo. Smallest fix that makes the company branch consistent.

**Alternatives considered**:
- *Point login at `/api/companies/{id}/logo`* — wrong branch: a company principal has no NextAuth token, so it would 401.

---

## D10. Employee search: ID-then-name, no mode

**Decision**: Filter client-side over the fetched employee list. Normalize the query (trim, lowercase) and match an employee when either the `employee_id` **or** the `employee_name` contains it, but sort/rank so **ID matches take precedence** over name-only matches (FR-002). The backend `GET /api/company/employees` also accepts an optional `?q=` for parity but the dashboard uses client filtering for instant response.

**Rationale**: Company employee rosters are small (a few hundred), so client filtering is instant and avoids a round-trip per keystroke. "Evaluated against ID and then name" is satisfied by the precedence rule.

**Alternatives considered**:
- *Server-side search per keystroke* — unnecessary chatter at this scale, and debouncing adds latency.

---

## D11. Leave-company and the membership-aware navigation

**Decision**:
- `GET /api/me/membership` (NextAuth) returns `{ membership: {...} | null }` — company id/name, employee_id, status, is_manager.
- `DELETE /api/me/membership` (NextAuth) deletes the account's employee row (hard delete) — this single operation serves **both** cancelling a `pending` request (FR-017) and leaving a granted company (FR-015); access is revoked either way.
- The shared header (`layout.tsx`) renders via a new client `Navigation` component: when a member, show the company name + **Leave company** (with a confirm dialog) and, if `is_manager`, a **Company Dashboard** entry; when not a member, show only the minimal links (and the app links are hidden).
- `/subscription` redirects a current member away (they must leave first, FR-016).

**Rationale**: Directly implements FR-015/FR-016/FR-020 and the clarified nav behavior. A confirm step is required by the spec.

**Alternatives considered**:
- *A dedicated nav route/URL for the dashboard revealed to everyone* — rejected; FR-020 requires the address stay hidden from non-managers.

---

## D12. Admin employees count + hover modal

**Decision**: Extend the admin company payload with `employee_count` (a `LEFT JOIN (SELECT company_id, COUNT(*) ...)`, so it is one query, not N+1). Add `GET /api/admin/companies/{id}/employees` for the hover modal's roster (name, employee_id, status, is_manager). The Admin `companies-table.tsx` shows the count as a hover target that opens the modal.

**Rationale**: FR-018 needs a per-company count and a roster popover; computing the count in the list query keeps the table fast, and the roster loads only when the Developer hovers.

**Alternatives considered**:
- *Count via a separate request per row* — N+1; slow and chatty.

---

## Dependency & risk summary

- **New dependency**: `resend` (backend) — developer-requested; add to `requirements.txt` / `pyproject.toml`.
- **Schema changes**: one new table (`company_requests`), one new column (`employees.is_manager`), two indexes — all additive and safe on existing data.
- **Behavioral flip**: bank/vendor sign polarity changes end-to-end; legacy saved reconciliations keep their old signs (accepted).
- **Gate risk**: the membership allow-list must be exact, or the request/dropdown/membership endpoints would lock themselves out. Called out as the top task risk.
