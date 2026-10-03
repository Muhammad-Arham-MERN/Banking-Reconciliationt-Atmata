# Tasks: Admin Dashboard (Camri Desk)

**Input**: Design documents from `/specs/008-admin-dashboard/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: **None.** The Developer explicitly instructed "Dont do any tests, just finish the task", and the spec repeats it. No test tasks are generated. Verification is the manual pass in `quickstart.md` (see T027).

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task

## Path Conventions

Web app: `backend/src/...` and `frontend/src/...` (per plan.md Structure Decision).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the one new dependency and the environment/configuration surface the whole feature reads from.

- [ ] T001 Add the `cryptography` dependency to `backend/pyproject.toml` and `backend/src/requirements.prod.txt` (and `backend/requirements.txt`), then run `uv sync` from `backend/` to refresh `backend/uv.lock`
- [ ] T002 Add admin/encryption/logo settings to `backend/src/config.py`: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_JWT_SECRET`, `ADMIN_JWT_TTL_HOURS` (default 12), `FERNET_KEY`, `COMPANY_LOGO_DIR` (default `backend/data/company_logos`); create the logo directory on import, mirroring how `UPLOAD_DIR` is created
- [ ] T003 [P] Add the six new keys to `backend/.env.example` (documented, including the `Fernet.generate_key()` generation command) and set real values in `backend/.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure every story depends on — schema, encryption, logo storage, the admin auth framework, routing, and the frontend API client.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Add `CREATE_COMPANIES` (with the `chk_company_payment_status` and `chk_company_price_non_negative` CHECK constraints) and `CREATE_UQ_COMPANY_NAME_LOWER` (unique index on `lower(name)`) to `backend/src/models/db_migrations.py`, and append both to the ordered `MIGRATIONS` list — DDL exactly as specified in `data-model.md`
- [ ] T005 [P] Create the pydantic request/response models in `backend/src/models/admin_models.py`: `AdminLoginRequest`, `AdminLoginResponse`, `PaymentStatus` (enum of `pending`/`free_trial`/`paid`), `CompanyWriteRequest`, `Company`, `CompanyListResponse`, `CompanyPasswordResponse`, `DeleteResponse` — matching `contracts/admin-api.yaml`
- [ ] T006 [P] Implement `backend/src/services/company_crypto_service.py`: `encrypt_password(plaintext) -> str` and `decrypt_password(token) -> str` over Fernet, constructing the cipher from `settings.FERNET_KEY`; raise a typed configuration error when the key is missing/malformed so callers can fail closed (never store plaintext, never log plaintext)
- [ ] T007 [P] Implement `backend/src/utils/company_logo_service.py`: `validate_logo(filename, content)` (PNG/JPG/SVG only, extension + signature/sniff), `save_logo(content) -> filename` (streamed write with a `uuid4` generated name into `COMPANY_LOGO_DIR` — never the client-supplied name, no size cap), `logo_path(filename)`, and `delete_logo(filename)` (best-effort)
- [ ] T008 Implement `backend/src/services/admin_auth_service.py`: `verify_admin_credentials(username, password)` using a constant-time comparison against `settings.ADMIN_USERNAME` / `settings.ADMIN_PASSWORD` (returning one generic failure regardless of which field was wrong), plus `issue_admin_token() -> (token, expires_at)` and `verify_admin_token(token) -> bool` using PyJWT HS256 signed with `settings.ADMIN_JWT_SECRET`
- [ ] T009 Add the admin branch to `backend/src/api/auth_middleware.py` (depends on T008): keep `POST /api/admin/login` public, and for every other `/api/admin/*` path verify the admin JWT from the `Authorization` header, returning the existing 401 JSON shape on failure and setting `request.state.admin_authenticated = True` on success. Leave all existing NextAuth behavior for non-admin paths byte-identical
- [ ] T010 Create `backend/src/api/admin_routes.py` with `router = APIRouter(prefix="/api/admin", tags=["admin"])` and register it in `backend/src/main.py` (import alongside the other routers and `app.include_router(admin_router)`) — depends on T009
- [ ] T011 [P] Create `frontend/src/lib/api/adminClient.ts` mirroring `frontend/src/lib/api/cloudHistoryClient.ts`: `API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`, a `handleResponse<T>` helper, an `AdminApiError` class, and methods `login`, `listCompanies`, `createCompany`, `updateCompany`, `deleteCompany`, `revealPassword`, plus `logoUrl(company)` — using `FormData` (no manual `Content-Type`) when a logo file is attached, per `contracts/admin-api.yaml`

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Sign in to the hidden admin dashboard (Priority: P1) 🎯 MVP

**Goal**: A private, unlinked `AdminDashAccess` route where the Developer signs in with the environment-configured username/password and lands on the dashboard shell; the session ends when the browser closes.

**Independent Test**: Visit `/AdminDashAccess` directly → sign-in form, no data. Submit wrong credentials twice → the same generic denial. Submit correct credentials → the dashboard shell renders. Close the browser, reopen the route → sign-in is required again. Browse every page → nothing links to the route.

- [ ] T012 [US1] Implement `POST /api/admin/login` in `backend/src/api/admin_routes.py`: validate the body with `AdminLoginRequest`, call `verify_admin_credentials`, return `AdminLoginResponse` (token + `expires_at`), and 401 with the generic message on failure and 503 when the admin credentials are not configured — depends on T008, T010
- [ ] T013 [P] [US1] Build the sign-in form in `frontend/src/components/admin/admin-sign-in-form.tsx`: `"use client"`, username + password with plain `<label>` elements + shadcn `Input`/`Button`, plain `useState`, an inline error banner (no toast library exists), and a `Loader2` submitting state
- [ ] T014 [US1] Build the dashboard shell in `frontend/src/components/admin/admin-dashboard.tsx`: `"use client"`, an admin-token state machine that reads/writes `sessionStorage`, renders `AdminSignInForm` when no token is present and the dashboard shell (header + Sign out + empty-state placeholder) when it is, and treats a 401 from any call as "signed out"
- [ ] T015 [US1] Create the hidden route page at `frontend/src/app/AdminDashAccess/page.tsx`: a thin server component with `export const dynamic = "force-dynamic"` that renders `AdminDashboard`. Do **not** use the `auth() -> redirect("/")` guard (the admin is not a NextAuth user), and do **not** add any link to it anywhere — depends on T014

**Checkpoint**: User Story 1 is fully functional and independently verifiable — the MVP.

---

## Phase 4: User Story 2 - Register a new client company (Priority: P1)

**Goal**: From the dashboard, add a company via a popup form (name, optional logo, generated-or-manual password, Rupees price) and see it appear immediately in the list, defaulting to Payment Status Pending.

**Independent Test**: Click "+ Add Companies", submit with only a name + price and a generated password → the row appears with a logo placeholder and status Pending; repeat with a manual password and an uploaded PNG/JPG/SVG → the logo renders; submit an empty name → blocked; submit a duplicate name → rejected.

- [ ] T016 [US2] Implement `create_company(...)` and `list_companies()` in `backend/src/services/company_service.py` over `db_service` with `$n` placeholders: encrypt the password via the crypto service before insert, store only the generated logo filename, default `payment_status` to `pending`, return ids as strings, and map a name-uniqueness violation to a typed duplicate error — depends on T004, T006, T007
- [ ] T017 [US2] Implement `GET /api/admin/companies` (list, no password/ciphertext in the payload, `logo_url` + `has_password` only) and `POST /api/admin/companies` (multipart: name, password, price_rupees, payment_status, optional logo) in `backend/src/api/admin_routes.py`, with 409 for a duplicate name, 415 for a bad logo type, 422 for validation, and 503 when encryption is unavailable — depends on T016
- [ ] T018 [P] [US2] Build `frontend/src/components/admin/companies-table.tsx`: `"use client"`, shadcn `Table` with columns for logo (placeholder when absent), name, masked password, price in Rupees, payment status `Badge`, and an actions cell; include the empty state and a skeleton/loading state — depends on T005, T011
- [ ] T019 [P] [US2] Build `frontend/src/components/admin/company-form-dialog.tsx`: `"use client"`, shadcn `Dialog` (create mode), plain `<label>` + `Input`, a `react-dropzone` picker for the optional logo, a random-password generator button whose result stays editable, a Rupees price input, a status `Select` defaulting to Pending, and inline validation + error/success banners — depends on T005, T011
- [ ] T020 [US2] Wire list + create into `frontend/src/components/admin/admin-dashboard.tsx`: fetch the company list once a token exists, host the "+ Add Companies" control opening `CompanyFormDialog`, and refresh the list after a successful create — depends on T014, T016, T017, T018, T019

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Manage and review registered companies (Priority: P2)

**Goal**: Review every company at a glance and act on any row — edit its details, reveal/copy its password, change its status, or delete it.

**Independent Test**: With a company present, edit its name/price/status → the row updates; reveal its password → it matches what was set and copies; delete it → it disappears; send a duplicate name on edit → rejected.

- [ ] T021 [US3] Extend `backend/src/services/company_service.py` with `get_company(id)`, `update_company(id, ...)` (partial update; re-encrypt only when a new password is supplied; replace the logo and delete the old file best-effort; refresh `updated_at`), `delete_company(id)` (row first, logo file best-effort after), and `reveal_password(id)` (decrypt on demand) — depends on T016
- [ ] T022 [US3] Implement `PUT /api/admin/companies/{company_id}`, `DELETE /api/admin/companies/{company_id}`, `GET /api/admin/companies/{company_id}/password` (the only endpoint that returns plaintext), and `GET /api/admin/companies/{company_id}/logo` (streamed with an explicit content type, `X-Content-Type-Options: nosniff`, `Content-Disposition: inline`) in `backend/src/api/admin_routes.py`, with 404 handling — depends on T021
- [ ] T023 [P] [US3] Add edit mode to `frontend/src/components/admin/company-form-dialog.tsx`: when a company is supplied, prefill every field, make the password field optional ("leave blank to keep"), allow replacing the logo, and submit to the update endpoint — depends on T019, T021, T022
- [ ] T024 [US3] Add row actions to `frontend/src/components/admin/companies-table.tsx`: reveal/copy the password via the on-demand endpoint, an Edit trigger opening the dialog in edit mode, and a two-step inline delete confirm (mirroring `PastReconciliationsDrawer.tsx`) — depends on T018, T021, T022

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T025 [P] Audit that the admin route is undiscoverable: search `frontend/src/app/layout.tsx` and every component for any link, href, or reference to `AdminDashAccess` — expect zero hits (SC-002)
- [ ] T026 [P] Verify Constitution Code Standards 1–3 on every new file: Bismillah header at the top, `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` footer at the end, and the inline crux marker on the logically critical methods (credential verification, password encryption/decryption, company create/update)
- [ ] T027 Run the full manual verification pass in `specs/008-admin-dashboard/quickstart.md` (no automated tests by instruction) — including the security invariants: ciphertext-only passwords in the DB, no plaintext in logs, no secrets in the list response, fail-closed when `FERNET_KEY` is missing, and **logos still present in `COMPANY_LOGO_DIR` after a restart**
- [ ] T028 [P] Confirm no billing/invoicing/charging code was introduced and that `price_rupees` is stored and displayed only (FR-015 guard)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Foundational
- **Polish (Phase 6)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational (T001–T011). Needs the admin auth framework (T008, T009) and the router (T010). Does **not** need the `companies` table or the crypto/logo services — the shell renders an empty state.
- **US2 (P1)**: Depends on Foundational + the route/shell from US1 (T014, T015). First story to need the `companies` table, crypto, and logo services.
- **US3 (P2)**: Depends on Foundational + US2 (it extends `company_service.py`, `admin_routes.py`, `companies-table.tsx`, and `company-form-dialog.tsx`).

### Critical path

`T001 → T002 → T008 → T009 → T010 → T012 → T014 → T015 → T016 → T017 → T020 → T021 → T022 → T024 → T027`

### Within Each User Story

- Services before endpoints
- Backend endpoints before the frontend wiring that consumes them
- Core implementation before integration

### Parallel Opportunities

- **Setup**: T003 can run alongside T001/T002
- **Foundational**: T004, T005, T006, T007 and T011 are all different files → fully parallel; T008→T009→T010 are strictly sequential
- **US2**: T018 and T019 touch different files → parallel; both precede the T020 wiring
- **US3**: T023 (dialog) and T024 (table) touch different files → parallel after T022
- **Polish**: T025, T026, T028 are independent audits → parallel

---

## Parallel Example: Foundational phase

```bash
# After Setup, launch the independent foundational pieces together:
Task: "Add companies table + unique index migrations in backend/src/models/db_migrations.py"
Task: "Create pydantic models in backend/src/models/admin_models.py"
Task: "Implement Fernet encrypt/decrypt in backend/src/services/company_crypto_service.py"
Task: "Implement logo storage in backend/src/utils/company_logo_service.py"
Task: "Create the admin API client in frontend/src/lib/api/adminClient.ts"

# Then the sequential auth chain:
Task: "Implement admin_auth_service.py" → "Add /api/admin branch to auth_middleware.py" → "Create + register admin_routes.py"
```

## Parallel Example: User Story 2

```bash
Task: "Create companies-table.tsx (list, empty, loading states)"
Task: "Create company-form-dialog.tsx (create mode)"
# then
Task: "Wire list + create into admin-dashboard.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup
2. Phase 2: Foundational (CRITICAL — blocks all stories)
3. Phase 3: US1 → **STOP and VALIDATE** the hidden-route sign-in end to end
4. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → the admin can sign in at a private route (MVP)
3. US2 → the admin can onboard a company
4. US3 → the admin can manage and review companies
5. Polish → audits + the manual quickstart pass

Each story adds value without breaking the previous one.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task
- The `[Story]` label maps each task to its user story for traceability
- No test tasks exist in this list — deliberate, per the Developer's instruction; `quickstart.md` is the verification mechanism
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- Avoid: editing the same file from two parallel tasks (`admin_routes.py`, `company_service.py`, `companies-table.tsx`, `company-form-dialog.tsx`, and `admin-dashboard.tsx` are each touched by more than one task — keep those sequential)
