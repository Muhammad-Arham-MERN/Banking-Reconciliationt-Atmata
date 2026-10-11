# Phase 0 Research — Employee Access Request (Subscription Layer)

All Technical Context unknowns are resolved below. Each entry records the decision, why it was chosen, and what else was considered. Findings are grounded in the existing code (file paths cited). **No new dependencies are introduced** — backend and frontend both ship with everything this feature needs.

---

## R1. Making sign-in a dedicated route, and where the user lands afterwards

**Decision**: Add `frontend/src/app/login/page.tsx` as the dedicated sign-in page and make the root `frontend/src/app/page.tsx` a pure redirect:
- `/` — `session ? redirect("/subscription") : redirect("/login")`
- `/login` — `session ? redirect("/subscription") : <SignInButton redirectTo="/subscription" />`
- `frontend/src/lib/auth.config.ts` → `pages.signIn` changes from `"/"` to `"/login"`.

**Rationale**: FR-001 requires sign-in on its own dedicated route, reachable directly. Today `app/page.tsx:10` redirects a signed-in visitor to `/upload-ai` and renders the button inline, and `auth.config.ts` declares `pages.signIn: "/"`. Moving the markup into `/login` and repointing both redirect targets at `/subscription` satisfies FR-001/FR-003 with the smallest diff and keeps NextAuth's own sign-in page reference consistent.

**Existing guards keep working**: every other protected page calls `auth()` then `redirect("/")` (e.g. `app/upload-ai/page.tsx`, `app/upload/page.tsx`, `app/tests/page.tsx`). Because `/` now redirects to `/login` for signed-out visitors, those guards need **no edit** — they bounce through `/` to `/login`. Changing them would be churn without behaviour change.

**Alternatives considered**:
- *Keep sign-in at `/` and add `/login` as an alias* — rejected: two sign-in surfaces for no benefit; FR-001 says "rather than being an embedded component".
- *Rewrite every existing `redirect("/")` to `redirect("/login")`* — rejected as unnecessary churn (above).

---

## R2. Removing the "Leave site?" confirmation on Google sign-in

**Decision**: Remove the `<CloseTabWarning />` mount and its import from `frontend/src/app/layout.tsx:8,44`, and delete the now-unused `frontend/src/components/auth/close-tab-warning.tsx`.

**Rationale**: FR-002 is caused by exactly one thing. `close-tab-warning.tsx` registers an unconditional `beforeunload` listener for the whole app; the browser hand-off from `signIn("google")` to `accounts.google.com` is an unload, so the native "Leave site?" prompt fires. There is no prop or flag gating it — it is mounted globally in the root layout. Removing the mount removes the prompt everywhere (including the header's plain `<a href>` navigations).

**Not the cause, do not touch**: `frontend/src/components/upload/UploadAIConfig.tsx` (~lines 289–303) registers its own `beforeunload`/`pagehide` listener, but it only calls `aiReconciliationClient.cancelProcessing(...)` without `preventDefault`, so it shows no dialog and its in-flight-cancellation behaviour must be preserved.

**Alternatives considered**:
- *Add a pathname/flag guard inside `CloseTabWarning` so it skips the sign-in page* — rejected: keeps a global listener with a special case, and leaves the header navigation popup in place.
- *Delete the import but keep the file* — rejected: leaves dead code (contrary to the project's no-dead-code preference); the file is re-creatable from git history if a future page wants it.

---

## R3. Where the Employees data lives and how the schema is created

**Decision**: A new `employees` table added as two idempotent DDL strings to the existing `MIGRATIONS` list in `backend/src/models/db_migrations.py` (`CREATE_EMPLOYEES` and its unique index), exactly as `companies` was added by 008. All access goes through a new `backend/src/services/employee_service.py` using `db_service.fetch/fetchrow/execute` with `$n` placeholders.

**Rationale**: The repo has **no ORM** — SQLModel was removed (`models/cloud_models.py:5`). `db_service.run_migrations()` executes the ordered `MIGRATIONS` list at startup, which is the established way to add a table here. Mirroring `company_service.py` keeps the new code indistinguishable from the existing style (FR-015 asks for a dedicated, separate record set that survives restarts — a real table in CockroachDB does that).

**Alternatives considered**: *SQLModel/SQLAlchemy* — rejected, explicitly removed from this project. *Alembic* — rejected, inconsistent machinery for one table.

---

## R4. The `adam-` ID: shape, normalization, and where the value is produced

**Decision**: A single validation/normalization helper in `employee_service.py`:
- Trim the input, lowercase it, and strip a leading `adam-` if the employee typed it.
- Require the remainder to match `^[a-z0-9]{6,12}$`; reject otherwise with **400 `invalid_employee_id`**.
- Store the canonical value as `f"adam-{value}"`.

The **generated** ID is produced **client-side** with `crypto.getRandomValues`, mirroring `generatePassword()` in `components/admin/company-form-dialog.tsx`: 8 characters from `[a-z0-9]`, rendered as `adam-xxxxxxxx`, placed in the field and left editable (FR-010).

**Rationale**: FR-011 and the clarification fix the shape, the prefix is always system-applied, and case-insensitive comparison is achieved by normalizing to lowercase before storage — which then makes the composite unique index a plain (non-expression) index. Client-side generation needs no new endpoint and matches the existing random-password precedent; the server remains the authority because it re-normalizes and re-validates on submit, so a client that skips the generator or tampers with the value cannot bypass the rules.

**Alternatives considered**:
- *Digits only / arbitrary characters* — rejected by the clarification (Q3).
- *A server "generate ID" endpoint* — rejected: an extra round trip for a value the employee is allowed to edit anyway; the generator is a convenience, not a guarantee.
- *Server-side availability pre-check endpoint* — rejected: submit-time rejection (FR-013) already covers it and keeps the flow to one request.

---

## R5. Uniqueness: composite on (employee ID + company)

**Decision**: `CREATE UNIQUE INDEX uq_employee_id_company ON employees (employee_id, company_id)`. A submit that collides is rejected with **409 `employee_id_taken`** (`asyncpg.UniqueViolationError` caught in the service, translated at the route boundary exactly as `DuplicateCompanyNameError` → 409 is handled today). The employee may request a **different** company with the same ID — that is a new, recorded row.

**Rationale**: This is the clarification that resolves the spec's internal contradiction: FR-011/FR-013/FR-017 speak of a globally unique ID, while the Edge Case "the same employee submits more than one request over time → each request is recorded" requires more than one row per ID. Composite uniqueness keeps the ID meaningful as the lookup handle the company is told about ("provide them your ID"), blocks true duplicates (one employee, twice to the same company), and keeps FR-017's "unique reference" true *within a company*. Enforcing it in the database (not just the service) makes the guarantee hold under concurrent submits without a transaction.

**Alternatives considered**: *Global unique index on `employee_id` alone* — rejected: contradicts the Edge Case and would silently make a second request impossible with no explanation. *Pending-only uniqueness* — rejected: a resolved request would free the ID for a different person to claim, which breaks the "tell the company your ID" mechanism.

> **Flag for the Developer**: the Q1–Q5 resolutions applied to the spec were the *recommended* options; the spec's `## Clarifications` session records them as settled. If Q1 should instead be globally-unique (option B), the only change is this index and the 409 message.

---

## R6. What the stored request references about the company

**Decision**: Store **both** `company_id INTEGER NOT NULL` and `company_name VARCHAR(255) NOT NULL` (a snapshot of the name as shown in the dropdown at submit time). **No database-level foreign key constraint** is added.

**Rationale**: The clarification chose "stable ID plus a name snapshot". The snapshot is what makes the record readable years later without a join, and the ID is what the later company dashboard will match on. The **deliberate absence of an FK** follows 008's explicit "no foreign keys, this feature is deliberately flat" design and, concretely, preserves the admin's ability to hard-delete a company (`delete_company` is a plain `DELETE`) — a restrictive FK would make that delete start failing with a 500 the moment any employee had requested access. The route validates that the `company_id` exists at submit time (404 `company_not_found`), so no dangling reference is created in practice.

**Alternatives considered**: *`REFERENCES companies(id) ON DELETE CASCADE`* — rejected: silently destroys access requests when a company is removed. *`ON DELETE RESTRICT`* — rejected: breaks the existing, shipped admin delete flow (008 FR-013). *Name only, no ID* — rejected by the clarification (renames would orphan the link).

---

## R7. Endpoint placement and which auth branch guards them

**Decision**: Two new route modules, both automatically guarded by the **existing NextAuth branch** of `src/api/auth_middleware.py` (no middleware edit needed, because neither path starts with `/api/admin` and neither is in `AUTH_EXEMPT_PREFIXES`):

| Method & path | Purpose |
|---|---|
| `GET /api/companies` | The dropdown list: `id`, `name`, `logo_url` for every company the Developer has added |
| `GET /api/companies/{company_id}/logo` | Streams a company logo to a signed-in employee |
| `POST /api/employees/requests` | Creates an employee access request |

Handlers read identity from `request.state.user_id` (the `users.id`) and `request.state.user_email`, the pattern used by every existing NextAuth-protected route (`cloud_routes.py:list_past_files`).

**Rationale**: FR-004/FR-008/FR-009/FR-012 are performed by a **signed-in employee**, not by the admin, so they must not sit under `/api/admin` (the admin branch would 401 them without an admin token). Placing them on ordinary paths means the global middleware verifies the Google-issued `access_token` and confirms the user exists — zero new auth code, and fail-closed by default.

**Alternatives considered**: *Reuse `/api/admin/companies`* — rejected: employees cannot hold an admin token, and widening the admin branch would expose the whole admin surface. *Add these paths to `AUTH_EXEMPT_PREFIXES`* — rejected: would make the employee endpoint and the company list publicly reachable.

---

## R8. Letting a signed-in employee see company logos

**Decision**: Serve logos through the new authenticated `GET /api/companies/{company_id}/logo`, reusing `logo_path()` / `logo_content_type()` from `src/utils/company_logo_service.py` and the same hard headers the admin endpoint uses (`X-Content-Type-Options: nosniff`, `Content-Disposition: inline`, `FileResponse`). The client fetches it **with the Bearer token as a blob** and renders an object URL, exactly as `components/admin/companies-table.tsx` already does via `adminClient.fetchLogoBlob`.

**Rationale**: The admin logo endpoint lives at `/api/admin/companies/{id}/logo`, which the middleware pins behind an admin token — an employee would get 401. A parallel path on the NextAuth branch is the only way to serve the image without weakening the admin gate. A blob fetch is required (not a bare `<img src>`), because an `<img>` cannot carry an `Authorization` header, and this is already the established pattern in the codebase.

**Alternatives considered**: *Inline base64 data URLs in the list response* — rejected: inconsistent with the shipped admin pattern and inflates the list payload. *Make the logo endpoint public (exempt)* — rejected: company logos are client data and should not be anonymously addressable. *Reuse the admin endpoint with a NextAuth fallback* — rejected: would blur the admin gate.

---

## R9. The subscription page and the request dialog

**Decision**:
- `frontend/src/app/subscription/page.tsx` — a thin **server** component: `export const dynamic = "force-dynamic"`, `const session = await auth(); if (!session) redirect("/login")`, then renders the client component. (FR-006 is satisfied by the page's own guard plus the new `/` redirect; see R1.)
- `frontend/src/components/subscription/subscription-plans.tsx` (`"use client"`) — the page body: the title "Reconciliation AI for Companies", the **Company Request** button, the **Employee Request** button, and the **Individual Plans** panel with `Rs 300 - 1 day` / `Rs 1500 - 1 month`. All inert buttons are plain buttons whose handler is a no-op (FR-005, FR-018).
- `frontend/src/components/subscription/employee-request-dialog.tsx` (`"use client"`) — the shadcn `Dialog` with Employee Name (`Input`), ID (`Input` + a "Generate" button), and Company (`Select` rendering each item's logo or a placeholder), plus the submit flow.
- `frontend/src/types/employee.types.ts` and `frontend/src/lib/api/employeeClient.ts` (`listCompanies`, `createRequest`, `fetchLogoBlob`) modelled on `adminClient.ts`.

**Rationale**: Matches the repo precisely — App Router page + `components/<feature>/` folder + a standalone `lib/api` fetch singleton with `API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`. The primitives needed (`Dialog*`, `Select*`, `Input`, `Button`, `Card`, `Badge`, `Skeleton`) **already exist** in `frontend/src/components/ui/` (built on Base UI, `base-nova` style), so there is nothing to install and no hand-rolled widget (per the Developer's standing shadcn preference). Plain `useState` + inline banner feedback matches the admin components; there is no toast/react-query/react-hook-form in this project and none is added.

**Alternatives considered**: *Hand-rolled modal* — rejected (shadcn `Dialog` exists). *Adding react-hook-form/zod/sonner* — rejected: new dependencies against the project's actual conventions. *A client page with `useSession`* — rejected: every protected page here is a server component that calls `auth()`.

---

## R10. Confirmation, validation feedback, and empty/error states

**Decision**:
- On success the dialog switches to an inline success panel carrying the exact string from FR-012 ("Your request has been sent to the designated company successfully, you may contact them to grant you access by providing them your ID or Name") with a Close control.
- Missing Employee Name or ID or Company blocks submit in the dialog **and** is re-checked server-side (FR-014 → 400 `missing_field`).
- A 409 renders inline next to the ID field: the ID has already requested that company; the dialog stays open with the values intact so the employee can edit or regenerate.
- The Company `Select` shows the current company list; when the list is empty it shows a disabled "No companies available" state with submit disabled; when the fetch **fails** it shows a distinct "Couldn't load companies" message with a Retry control and submit stays disabled (FR-009 + the clarification's error-state answer).

**Rationale**: Keeps the interaction honest at the three points the spec calls out (empty list, fetch failure, duplicate ID) while reusing the inline-banner idiom already used by `admin-sign-in-form.tsx` / `company-form-dialog.tsx`. Distinguishing "empty" from "failed" is what makes FR-009's requirement falsifiable during manual verification.

**Alternatives considered**: *A toast for errors* — rejected: no toast library. *Closing the dialog on duplicate* — rejected: forces the employee to re-enter everything.

---

## R11. Generated ID collision at submit time

**Decision**: Rely on the composite unique index and the 409 path (R5). No pre-check, no retry loop.

**Rationale**: With an 8-character `[a-z0-9]` space, a collision between the same company's pending requests is negligible, and the failure mode is already handled with a clear, recoverable message. Adding an availability endpoint or an automatic regenerate-and-retry would add a round trip and hide a decision the employee should see.

**Alternatives considered**: *Server auto-retry on collision* — rejected: silently changes a value the employee may have noted down. *Availability pre-check* — rejected (R4).

---

## R12. Dependencies

**Decision**: **None added**, on either side.

**Rationale**: Backend needs nothing new (asyncpg, pydantic, FastAPI, the existing `company_logo_service` helpers). Frontend needs nothing new: `Dialog`, `Select`, `Input`, `Button`, `Badge`, `Skeleton`, `Card` are already in `frontend/src/components/ui/`, `crypto.getRandomValues` is a platform API, and `session.user.access_token` already exists from `auth.config.ts`. Constitution Principle II (Developer Stack Authority) is satisfied by adding no framework or library.

**Alternatives considered**: none warranted.

---

## R13. Automated tests

**Decision**: **None.** No pytest, no Playwright, and no test tasks in `/sp.tasks`. Verification is the manual pass in `quickstart.md`.

**Rationale**: The Developer instructed "Keep it concise and simple — no tests" in the spec input, 008 set the precedent, and Constitution Principles I/II make that the correct reading. Recorded here so the omission is a deliberate, reviewable decision rather than an oversight.

---

## Resolved unknowns summary

| # | Unknown | Resolution |
|---|---------|------------|
| R1 | Dedicated sign-in route | New `/login`; `/` redirects out; post-sign-in → `/subscription` |
| R2 | "Leave site?" prompt | Remove the global `CloseTabWarning` mount; leave the unload-cancel logic in `UploadAIConfig` alone |
| R3 | Employee storage | New `employees` table via the raw-SQL `MIGRATIONS` list + `employee_service.py` |
| R4 | ID shape / generation | `adam-` + 6–12 lowercase alphanumerics; client-side generator; server re-normalizes |
| R5 | Uniqueness | Composite unique index on (employee_id, company_id) → 409 on duplicate |
| R6 | Company reference | `company_id` + `company_name` snapshot, no DB foreign key (preserves admin delete) |
| R7 | API surface & auth | `/api/companies`, `/api/companies/{id}/logo`, `/api/employees/requests`, all on the NextAuth branch |
| R8 | Logo access for employees | Authenticated logo endpoint + Bearer blob fetch + object URL |
| R9 | Page & components | `app/subscription/page.tsx` + `components/subscription/*` + `lib/api/employeeClient.ts`, existing shadcn primitives |
| R10 | Feedback states | Inline success panel, inline 409, distinct empty vs. failed company list |
| R11 | Collision handling | Submit-time 409 only |
| R12 | Dependencies | None added |
| R13 | Tests | None, per explicit Developer instruction |
