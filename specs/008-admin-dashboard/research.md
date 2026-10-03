# Phase 0 Research — Admin Dashboard (Camri Desk)

All Technical Context unknowns are resolved below. Each entry records the decision, why it was chosen, and what else was considered. Findings are grounded in the existing code (file paths cited).

---

## R1. How the admin signs in (authentication mechanism)

**Decision**: A dedicated admin credential pair (`ADMIN_USERNAME` / `ADMIN_PASSWORD`) in the backend environment, exchanged at `POST /api/admin/login` for a short-lived **admin JWT** (PyJWT, HS256, signed with a separate `ADMIN_JWT_SECRET`). The frontend holds that token in **`sessionStorage`**.

**Rationale**: The spec requires a username/password form on a hidden route, independent of normal application users (FR-002, FR-005). The codebase's only existing auth is NextAuth v5 with **Google** (`frontend/src/lib/auth.config.ts`) verified as an HS256 Bearer JWT by `src/services/auth_service.py` — a Google account cannot satisfy a username/password form, and tying the admin to a Google identity would make it visible/undesirable. PyJWT is already a dependency, so no new auth library is needed.

**Alternatives considered**:
- *NextAuth Google sign-in for the admin* — rejected: contradicts FR-002 (username/password) and FR-005 (admin independent of normal users).
- *Server-side session store / httpOnly cookie* — rejected: the repo has no session store, `db_service` exposes no transaction/session helper, and the API is called cross-origin (localhost:3000 → localhost:8000, and a Vercel origin in production), which would force `SameSite=None; Secure` + credentialed CORS. A Bearer token matches every existing API client.
- *Hashing the admin password (bcrypt/argon2)* — rejected: unnecessary for a single env-configured secret; adds a dependency. Constant-time comparison (below) is the right control here.

## R2. Where admin auth sits relative to the global `auth_middleware`

**Decision**: Add an explicit **admin branch inside `src/api/auth_middleware.py`**, rather than adding paths to `AUTH_EXEMPT_PREFIXES`:
- `POST /api/admin/login` → skipped by the NextAuth check (credentials verified in the handler).
- Any other `/api/admin/*` path → verified against the **admin JWT** and rejected with 401 if absent/invalid; sets `request.state.admin_authenticated = True`.

**Rationale**: `auth_middleware` runs globally and currently 401s every non-exempt path that lacks a valid **NextAuth** Bearer token (`src/api/auth_middleware.py:17-60`). A naive admin endpoint would therefore be unreachable. Putting the branch in the middleware keeps the exemption list semantic (it means "genuinely public", per its own comment) and guarantees no admin route can be forgotten and accidentally left open — the gate is centralized rather than per-endpoint.

**Alternatives considered**:
- *Adding `/api/admin` to `AUTH_EXEMPT_PREFIXES` and checking the admin token per endpoint* — rejected: fail-open by default (a forgotten check silently exposes company data).
- *A FastAPI `Depends(...)` dependency* — rejected: the codebase has **no** auth dependency; auth is middleware-only, and introducing a second, parallel mechanism would fragment the pattern.

**Verification of no conflict**: `security_middleware` (`src/api/middleware.py:70-97`) inspects only the **lowercased URL**, not bodies — so company names, passwords, and prices in JSON/multipart payloads cannot trip it. Consequence recorded: credentials MUST be sent in the JSON body, never in the query string.

## R3. Admin session lifetime (closing the browser ends it)

**Decision**: No "remember me", no refresh token, no server-side session. The admin JWT is kept in **`sessionStorage`**, which the browser clears when the tab/window closes; the token itself also carries a modest `exp` (12 hours) as a backstop.

**Rationale**: The clarification answer was "browser close = session expire, require username password again". `sessionStorage` is precisely browser-session scoped, so the requirement falls out of the storage choice rather than needing bespoke expiry logic — and it satisfies the "no session survives a browser restart" success criterion (SC-008). The `exp` backstop prevents a long-lived open tab from holding a token indefinitely.

**Alternatives considered**:
- *httpOnly cookie with no `Max-Age`* (also browser-session scoped) — rejected: cross-origin credentialed-CORS complexity (see R1).
- *`localStorage`* — rejected: survives browser restart, contradicting the requirement.
- *No expiry at all* — rejected: leaves an indefinitely valid token.

## R4. Company password encryption at rest

**Decision**: `cryptography`'s **Fernet** (AES-128-CBC + HMAC) with the key supplied as `FERNET_KEY` in the environment. Passwords are encrypted on create/update and decrypted only on the explicit reveal request. Plaintext is never persisted and never logged. If `FERNET_KEY` is missing or malformed, the create/update returns a clear configuration error (503) and **no** row is written.

**Rationale**: Explicitly mandated by the Developer (FR-017). Fernet is *reversible*, which is required because the plaintext must eventually be handed to the company and used by the later company-login spec — a hash would be one-way and therefore unusable. Fail-closed on a missing key guarantees the tool can never silently degrade to plaintext storage (spec edge case).

**Alternatives considered**:
- *Hashing (bcrypt/argon2)* — rejected: irreversible; the admin must be able to read the password back (FR-018).
- *Application-level AES-GCM by hand* — rejected: Fernet is the mandated, misuse-resistant primitive (authenticated, versioned, timestamped).
- *Storing plaintext* — rejected outright (FR-017).

## R5. Retrieving a company's password (reveal/copy)

**Decision**: A dedicated **`GET /api/admin/companies/{id}/password`** endpoint that decrypts and returns `{ "password": "..." }`. The **list endpoint never returns the password or its ciphertext** — only a boolean `has_password`, so the encrypted blob is not needlessly shipped to the browser.

**Rationale**: FR-007/FR-018 require a masked value with reveal + copy. Keeping decryption behind its own endpoint means the list payload (the common case) carries no secret material, and the reveal is an explicit, auditable action. Expressed in the frontend as a masked cell with an eye/copy control.

**Alternatives considered**:
- *Including the decrypted password in the list response* — rejected: every list load would spill all company secrets.
- *Including the Fernet ciphertext in the list* — rejected: pointless exposure with no benefit; the client cannot decrypt it.

## R6. Where company logos are stored

**Decision**: A **dedicated directory outside `UPLOAD_DIR`** — a new `COMPANY_LOGO_DIR` setting (env-overridable, default `backend/data/company_logos`). Only the generated filename is stored in the `companies` row.

**Rationale**: This is the sharpest trap in the codebase. `cleanup_old_files()` deletes files in `UPLOAD_DIR` older than `FILE_RETENTION_MINUTES` (20 minutes) and runs **on every startup**; `cleanup_all_files()` deletes **all** files in `UPLOAD_DIR` **on every shutdown** (`src/utils/file_helpers.py:140-205`; wired at `src/main.py:65` and `src/main.py:100-104`). A logo parked in `UPLOAD_DIR` would be erased within 20 minutes — or on the next deploy/restart — silently breaking FR-007.

**Alternatives considered**:
- *Reuse `UPLOAD_DIR`* — rejected: guaranteed data loss (above).
- *A subdirectory under `UPLOAD_DIR`* (technically survives, because the cleanup loops only delete top-level `is_file()` entries) — rejected: it relies on an incidental detail of the cleanup loop and would break the moment that loop becomes recursive. An explicit separate directory is intentional and self-documenting.
- *Store logo bytes in CockroachDB (JSONB/BYTEA)* — rejected: bloats rows, breaks the repo's file-on-disk convention, and complicates listing.

## R7. Serving logos safely (SVG risk)

**Decision**: Serve a logo through **`GET /api/admin/companies/{id}/logo`**, streaming the stored file with an explicit `Content-Type` derived from the validated extension, `X-Content-Type-Options: nosniff`, and `Content-Disposition: inline`. The frontend renders it only via `<img src=...>`.

**Rationale**: SVG is an accepted format per the clarification, and SVG can carry script. Rendering SVG via `<img>` blocks script execution in the SVG context, and `nosniff` prevents content-type confusion. Validation is by extension + content sniffing at upload (PNG/JPG signatures; SVG identified as XML/`<svg`), matching the spirit of the existing `validate_upload_file` in `src/utils/file_helpers.py`.

**Alternatives considered**:
- *Reject SVG entirely* — rejected: the Developer explicitly asked for SVG support.
- *Sanitize SVG server-side* — deferred as over-engineering for a single-admin tool where only the admin uploads files; the `<img>` + `nosniff` combination is the proportionate control (documented, not silent).

## R8. Company identity and uniqueness

**Decision**: `companies.name` is required and unique, enforced by a **unique index on `lower(name)`** so "Acme Ltd" and "acme ltd" collide; the service surfaces a 409 `company_name_exists` error.

**Rationale**: The spec declares the name the company's identifier and rejects duplicates (edge case). Case-insensitive uniqueness prevents two records that would be indistinguishable at the later company sign-in. This mirrors the existing 409 duplicate handling in `cloud_routes.py`.

**Alternatives considered**: *Case-sensitive uniqueness* — rejected: leaves the ambiguity the spec set out to avoid. *Allowing duplicates* — rejected by the spec.

## R9. Payment Status and Price representation

**Decision**: `payment_status VARCHAR(16) NOT NULL DEFAULT 'pending'` with a `CHECK` constraint over `('pending','free_trial','paid')`; the API uses these **snake_case identifiers** and the UI renders "Pending" / "Free Trial" / "Paid". `price_rupees INTEGER NOT NULL` (whole Rupees), validated `>= 0`.

**Rationale**: FR-014 fixes the three states and the Pending default; FR-015 fixes whole-Rupee, recurring-per-period semantics with **no billing logic**. A DB-level `CHECK` prevents an out-of-range status from ever being stored. Identifiers are kept as safe, unspaced keys (consistent with the project's preference for underscore-form contract keys).

**Alternatives considered**: *Free-text status* — rejected: unfalsifiable and untestable. *Decimal price* — rejected in clarifications (whole Rupees). *Building billing/invoicing* — explicitly out of scope; the Developer implements it later.

## R10. Schema change and DB access approach

**Decision**: Add `CREATE_COMPANIES` (plus its unique index) as raw SQL strings to `MIGRATIONS` in `src/models/db_migrations.py`, and implement all access with `db_service.fetch/fetchrow/execute` using `$n` placeholders in a new `company_service.py`.

**Rationale**: The repo has **no ORM** — `cloud_models.py:5` states "SQLModel has been removed — all DB operations use raw asyncpg via db_service." The flat, idempotent `MIGRATIONS` list runs on startup (`db_service.run_migrations`), which is exactly how `reconciliation_data` and `pdf_structure_profiles` were added.

**Alternatives considered**: *SQLModel/SQLAlchemy* — rejected: explicitly removed from this project. *A separate migration tool (Alembic)* — rejected: adds machinery inconsistent with the established pattern for a single-table addition.

**Note — no transactions needed**: create/update/delete are each single-statement operations, so the absence of a transaction helper in `db_service` is not a gap for this feature. Logo file deletion on company delete is best-effort *after* the row delete succeeds.

## R11. Serializing CockroachDB `SERIAL` ids

**Decision**: The API returns company `id` as a **string**.

**Rationale**: `cloud_service.get_user_files_meta` already stringifies ids (`"file_id": str(row["id"])`) because CockroachDB's `SERIAL` can exceed JavaScript's safe-integer range, silently corrupting ids in the browser. Consistency avoids a real, hard-to-diagnose bug.

## R12. The hidden frontend route

**Decision**: Create the App Router page at `frontend/src/app/AdminDashAccess/page.tsx`, giving the path `/AdminDashAccess` exactly as specified in FR-001. It is added **nowhere** in `layout.tsx` or any nav. The page is a thin server component (`export const dynamic = "force-dynamic"`) rendering a `'use client'` dashboard shell.

**Rationale**: The route must be reachable only by direct address (FR-001, SC-002). The app's nav lives in `src/app/layout.tsx` and uses plain `<a href>` links, so simply not adding an entry keeps it hidden while the page still inherits the global header. **Note**: it must **not** use the existing `auth() -> redirect("/")` guard (`src/app/tests/page.tsx` pattern), because the admin is not a NextAuth user; its gate is the sign-in form plus the admin token.

**Risk / fallback**: Next.js may warn about (or object to) an uppercase route segment on some toolchains. If the build complains, the fallback is a lowercase folder (`admin-dash-access`) with the exact-cased path preserved via a rewrite/redirect — to be confirmed during implementation and reported to the Developer rather than decided silently.

## R13. Frontend data flow, state, and UI primitives

**Decision**: Mirror the existing conventions precisely:
- `src/lib/api/adminClient.ts` — a plain `fetch` singleton with a `handleResponse<T>` helper, `API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`, and an `Authorization: Bearer <adminToken>` header; `FormData` (with **no** manual `Content-Type`) for create/update when a logo file is attached. Modeled on `cloudHistoryClient.ts`.
- **Plain `useState`** for form/loading state, with **inline banner** (`error`/`success`) feedback — there is no toast library and no react-hook-form/zod in the project.
- **shadcn primitives**, confirmed present: `Table`, `Dialog`, `Input`, `Select`, `Badge`, `Button`, `Card`, `Tooltip`. Confirmed **absent**: `Label`, `AlertDialog`, `DropdownMenu`, `Form`. Therefore use a plain `<label>`, an inline two-step delete confirm (as `PastReconciliationsDrawer.tsx` does), and a `Select` for status — no new dependencies.
- `react-dropzone` (already used) for the optional logo picker.

**Rationale**: Matching the established patterns means the feature needs zero new frontend dependencies and reads like the rest of the app. Adding react-hook-form/zod/sonner/AlertDialog would contradict the project's actual conventions.

## R14. Automated tests

**Decision**: **None.** No pytest, no Playwright, no test tasks in `/sp.tasks`. Verification is the manual smoke test in `quickstart.md`.

**Rationale**: The Developer instructed "Dont do any tests, just finish the task" and the spec repeats it. Constitution Principle I (Strict Instruction Following) and II (Developer Stack Authority) make this the correct reading; the "Quality Standards / reliability" language is satisfied through fail-closed error handling and the manual verification pass rather than an automated suite.

**Alternatives considered**: *A minimal happy-path test for the crypto round-trip* — rejected as contrary to the explicit instruction; noted here so the omission is a recorded, deliberate choice rather than an oversight.

---

## Resolved unknowns summary

| # | Unknown | Resolution |
|---|---------|------------|
| R1 | Admin auth mechanism | Env credentials → admin JWT, held in `sessionStorage` |
| R2 | Middleware integration | Admin branch inside `auth_middleware`; login exempt, rest verified |
| R3 | Session lifetime | Browser-session via `sessionStorage` + 12 h `exp` backstop |
| R4 | Password at rest | Fernet with env `FERNET_KEY`; fail closed if absent |
| R5 | Password reveal | Dedicated decrypt-on-demand endpoint; list omits secrets |
| R6 | Logo storage | Dedicated `COMPANY_LOGO_DIR` outside `UPLOAD_DIR` |
| R7 | SVG serving | Streamed via controlled endpoint + `nosniff`; rendered in `<img>` |
| R8 | Name uniqueness | Unique index on `lower(name)`; 409 on duplicate |
| R9 | Status/price shape | `CHECK`-constrained snake_case status; integer Rupees |
| R10 | Schema/DB access | Raw SQL migration + `db_service` (`$n` params) |
| R11 | Id serialization | Ids returned as strings |
| R12 | Hidden route | `app/AdminDashAccess/page.tsx`, unlinked; fallback noted |
| R13 | Frontend patterns | Existing client/state/shadcn conventions; no new deps |
| R14 | Tests | None, per explicit Developer instruction |
