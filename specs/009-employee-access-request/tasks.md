# Tasks: Employee Access Request (Subscription Layer)

**Input**: Design documents from `/specs/009-employee-access-request/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/employee-api.yaml ✅, quickstart.md ✅

**Tests**: **None.** Automated tests are explicitly excluded by the feature specification ("Keep it concise and simple — no tests") and by the Developer's standing instruction. No test tasks are generated; verification is the manual pass in `quickstart.md`.

**Organization**: Tasks are grouped by user story so each can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Every task names its exact file path

## Path Conventions

Web application — the repo already has two roots:

- Backend: `backend/src/` (`api/`, `models/`, `services/`)
- Frontend: `frontend/src/` (`app/`, `components/`, `lib/`, `types/`)

## Code Standards (apply to EVERY new or edited file)

Per the project constitution, every Python/TS file must begin with the Bismillah header (`# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` / `/* … */`), end with the footer (`# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`), and mark the logical crux inline with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`. Use JS comment blocks (`/** */`) for TS/JSX file headers — never `#`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the feature needs no dependency or environment changes, and prepare the folder it lives in.

- [X] T001 [P] Confirm no dependency or environment changes are required — verify nothing in this feature needs edits to `backend/pyproject.toml`, `backend/requirements.txt`, `backend/src/requirements.prod.txt`, `backend/uv.lock`, or `frontend/package.json` (research R12), and record the result
- [X] T002 [P] Create the frontend feature folder `frontend/src/components/subscription/` and confirm the App Router folders `frontend/src/app/login/` and `frontend/src/app/subscription/` exist

**Checkpoint**: Nothing to install; folder structure ready.

---

## Phase 2: Foundational (Shared Infrastructure)

**Purpose**: The persistence and client-contract layer the Employee Request flow is built on.

**Note on ordering**: US1 is frontend-routing-only and is **not** blocked by this phase. T003–T007 are prerequisites for **US2** (the only story that persists data) and are grouped here because they are shared infrastructure rather than user-facing behaviour.

- [X] T003 Add the `CREATE_EMPLOYEES` statement and the `CREATE_UQ_EMPLOYEE_ID_COMPANY` composite unique index to the `MIGRATIONS` list in `backend/src/models/db_migrations.py` (exact DDL in `data-model.md`; mirror how `CREATE_COMPANIES` was appended)
- [X] T004 [P] Create `backend/src/models/employee_models.py` with the pydantic models `EmployeeRequestCreate`, `EmployeeRequestResponse`, `CompanyOption`, and `CompanyOptionListResponse`, plus the `EmployeeStatus = Literal["pending","accepted","denied"]` alias (mirror `backend/src/models/admin_models.py`)
- [X] T005 Create `backend/src/services/employee_service.py` — `normalize_employee_id()` (trim → lowercase → strip one leading `adam-` → require `^[a-z0-9]{6,12}$` → return `adam-<value>`), `create_employee_request()` (insert over `db_service` with `$n` params, catching `asyncpg.UniqueViolationError` → a `DuplicateEmployeeRequestError`), and an `InvalidEmployeeIdError`; mark the crux method with the inline marker (depends on T003, T004)
- [X] T006 [P] Create `frontend/src/types/employee.types.ts` with `EmployeeStatus`, `CompanyOption`, `CompanyOptionListResponse`, `EmployeeRequestCreate`, and `EmployeeRequestResponse` matching `contracts/employee-api.yaml`
- [X] T007 [P] Create `frontend/src/lib/api/employeeClient.ts` — a `fetch` singleton with `API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`, an `EmployeeApiError` class, and `listCompanies(token)`, `createRequest(token, input)`, `fetchLogoBlob(token, companyId)` (mirror `frontend/src/lib/api/adminClient.ts`, including its `handleResponse`/error-extraction shape) (depends on T006)

**Checkpoint**: The table, models, service, types, and client exist — US2 can be built.

---

## Phase 3: User Story 1 - Sign in and land on the subscription choice page (Priority: P1) 🎯 MVP

**Goal**: Sign-in moves to its own `/login` route, `/` becomes a pure redirect, Google sign-in no longer triggers the browser's "Leave site?" prompt, and a successful sign-in lands on the `/subscription` page showing the title "Reconciliation AI for Companies" and the Employee Request action.

**Independent Test**: Visit `/` while signed out → redirected to `/login`; start Google sign-in → no "Leave site?" prompt appears; complete sign-in → land on `/subscription` titled "Reconciliation AI for Companies" with the Employee Request action (the remaining menu completes in US3). Visiting `/subscription` while signed out → redirected to sign in.

- [X] T008 [P] [US1] Create `frontend/src/app/login/page.tsx` — the dedicated sign-in route: `export const dynamic = "force-dynamic"`, `const session = await auth(); if (session) redirect("/subscription")`, then render `<SignInButton redirectTo="/subscription" />` inside the existing centered card markup (move it out of `app/page.tsx` verbatim)
- [X] T009 [P] [US1] Rewrite `frontend/src/app/page.tsx` as a pure redirect: `export const dynamic = "force-dynamic"`, `const session = await auth(); redirect(session ? "/subscription" : "/login")` — remove the inline sign-in markup and the `SignInButton` import
- [X] T010 [P] [US1] Repoint the NextAuth sign-in page in `frontend/src/lib/auth.config.ts`: `pages.signIn` from `"/"` to `"/login"`
- [X] T011 [US1] Remove the `<CloseTabWarning />` mount and its import from `frontend/src/app/layout.tsx`, then delete `frontend/src/components/auth/close-tab-warning.tsx` — this is the sole cause of the "Leave site?" prompt (FR-002, research R2). Do **not** touch the unload handler in `frontend/src/components/upload/UploadAIConfig.tsx`
- [X] T012 [P] [US1] Create `frontend/src/components/subscription/subscription-plans.tsx` (`"use client"`) rendering the title **"Reconciliation AI for Companies"** in a `Card`, and an **Employee Request** `Button` whose `onClick` sets a local `dialogOpen` state to `true` (the dialog itself is mounted in US2 — with US1 alone the button simply sets unused state, so nothing breaks)
- [X] T013 [US1] Create `frontend/src/app/subscription/page.tsx` — `export const dynamic = "force-dynamic"`, `const session = await auth(); if (!session) redirect("/login")`, rendering `<SubscriptionPlans />` (depends on T012)

**Checkpoint**: `/` → `/login` → Google (no prompt) → `/subscription` with the title. US1 is independently verifiable.

---

## Phase 4: User Story 2 - Submit an employee access request (Priority: P1)

**Goal**: The Employee Request dialog captures Employee Name, an `adam-` ID (typed or generated, always prefixed, unique per company), and a Company chosen from the Developer's companies with logos; submitting records a pending row and shows the exact confirmation message.

**Independent Test**: From `/subscription`, click Employee Request → fill the form using a generated ID → pick a company with a logo → submit → the exact confirmation message appears and a `pending` row exists in `employees`. Re-submitting the same ID for the same company is rejected; the same ID for a different company is accepted.

- [X] T014 [P] [US2] Create `backend/src/api/company_routes.py` with `router = APIRouter(prefix="/api/companies", tags=["companies"])`: `GET /api/companies` returning `CompanyOptionListResponse` (reuse `company_service.list_companies()`, expose `id` as a string and `logo_url` as `/api/companies/{id}/logo` or `null`), and `GET /api/companies/{company_id}/logo` returning a `FileResponse` via `logo_path()` / `logo_content_type()` with `X-Content-Type-Options: nosniff`, 404 when the company or logo is missing (contract: `contracts/employee-api.yaml`)
- [X] T015 [P] [US2] Create `backend/src/api/employee_routes.py` with `router = APIRouter(prefix="/api/employees", tags=["employees"])`: `POST /api/employees/requests` reading `request.state.user_id` / `request.state.user_email`, validating the company exists (404 `company_not_found`), and mapping `InvalidEmployeeIdError` → 400 `invalid_employee_id`, missing/blank fields → 400 `missing_field`, `DuplicateEmployeeRequestError` → 409 `employee_id_taken`, using the `{"error","message","details"}` HTTPException envelope (depends on T005)
- [X] T016 [US2] Register both routers in `backend/src/main.py` (`from src.api.company_routes import router as company_router`, `from src.api.employee_routes import router as employee_router`, then `app.include_router(...)` for each — the paths must **not** start with `/api/admin`, so the existing NextAuth middleware branch guards them with no middleware edit) (depends on T014, T015)
- [X] T017 [US2] Create `frontend/src/components/subscription/employee-request-dialog.tsx` using the existing shadcn `Dialog*`, `Input`, `Select*`, `Button`, and `Badge` primitives: Employee Name input, ID input with a **Generate** button (`crypto.getRandomValues` → `adam-` + 8 chars of `[a-z0-9]`, left editable, mirroring `generatePassword()` in `components/admin/company-form-dialog.tsx`), a Company `Select` rendering each option's logo (blob from `fetchLogoBlob`) or a placeholder, client-side required-field checks, an inline 409 message beside the ID, the distinct empty vs. failed company-list states with a Retry control and submit disabled, and an inline success panel carrying the verbatim confirmation string from FR-012 (depends on T006, T007)
- [X] T018 [US2] Wire the dialog into `frontend/src/components/subscription/subscription-plans.tsx`: mount `<EmployeeRequestDialog open={dialogOpen} onClose={…} />`, fetch the company options on open via `employeeClient.listCompanies(session.user.access_token)`, and refresh the list after a successful submit (depends on T012, T017)

**Checkpoint**: A request can be submitted end to end and is recorded with `status = 'pending'`; duplicates are rejected, different companies are accepted.

---

## Phase 5: User Story 3 - See the other plan options (Priority: P2)

**Goal**: The subscription page shows a **Company Request** action and an **Individual Plans** panel with "Rs 300 - 1 day" and "Rs 1500 - 1 month" — visible and clickable, doing nothing.

**Independent Test**: On `/subscription`, click Company Request and both plan buttons → no navigation and no state change. The panel shows exactly the two specified options.

- [X] T019 [US3] Add the **Company Request** `Button` and the **Individual Plans** `Card` (options "Rs 300 - 1 day" and "Rs 1500 - 1 month", each a `Button`) to `frontend/src/components/subscription/subscription-plans.tsx`, all with explicit no-op handlers, completing the menu required by US1 acceptance scenario 2 (FR-005, FR-018)

**Checkpoint**: The full subscription menu renders and every inert control is genuinely inert.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Project-wide checks that span all three stories.

- [X] T020 [P] Verify Code Standards 1–3 on every file created or edited by this feature — Bismillah header, footer, and the inline crux marker on the logical crux methods (at minimum: `employee_service.create_employee_request`, `employee_routes.create_employee_request`, and the ID generator in `employee-request-dialog.tsx`)
- [ ] T021 Run the full `quickstart.md` manual verification pass (steps 1–31), including the tricky paths (duplicate ID, same ID + different company, bad ID shape, empty vs. failed company list, case-insensitive duplicate), the 401 probes on all three new endpoints, and the non-regression checks (admin surface still 401s with an employee token; the `UploadAIConfig` unload cancellation still works after `CloseTabWarning` was removed)
- [X] T022 [P] Confirm the deliberate non-goals hold — no gating of `/upload-ai` or `/upload`, no accept/deny action, no billing, no automated tests added, and no new dependencies (`git diff backend/requirements.txt backend/pyproject.toml frontend/package.json`)

**Verification status (2026-09-30)**: T020 and T022 are done — every new/edited file carries the Bismillah header and the footer (the vendored `glare-card.tsx` needed both added), and no dependency, test, gating or billing scope crept in. For T021 the automated substitute pass was run and passed: `tsc --noEmit`, `eslint` on every touched file (**0 errors**), `next build` (all routes compile; `/` and `/subscription` dynamic), a backend byte-compile, a real import of both new route modules, and OpenAPI path verification confirming `/api/companies`, `/api/companies/{company_id}/logo` and `/api/employees/requests` alongside the untouched `/api/admin/*`. The **live** browser walkthrough — Google sign-in, the migration applying, the 401 probes on a running server, and the visual hover checks — still needs the stack up, so T021 is left unchecked.

**Checkpoint**: The feature matches the spec and quickstart.md end state exactly, with no scope creep.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup. It gates **US2 only**; US1 can be built before or alongside it
- **US1 (Phase 3)**: Depends on Setup only (frontend routing, no backend)
- **US2 (Phase 4)**: Depends on Foundational (T003–T007) and on US1's T012 (the component it edits)
- **US3 (Phase 5)**: Depends on US1's T012 (same file). Independent of the backend
- **Polish (Phase 6)**: Depends on US1 + US2 + US3

### Task-Level Dependencies

```text
T003 ─┬─▶ T005 ─┬─▶ T015 ─┐
T004 ─┘         │         ├─▶ T016
                │         │
T014 ───────────┴─────────┘

T006 ─┬─▶ T007 ─▶ T017 ─▶ T018
      │                    ▲
T012 ─┴────────────────────┘  (T012 also feeds T019)

T008, T009, T010, T011  — independent of each other
T013 ─▶ needs T012
```

### Suggested order

1. T001 → T002
2. T003 → T004 → T005 (backend foundation)
3. T006 → T007 (frontend foundation)
4. T008, T009, T010, T011 (parallel) → T012 → T013 → **validate US1**
5. T014, T015 → T016 → T017 → T018 → **validate US2**
6. T019 → **validate US3**
7. T020, T021, T022

### Parallel Opportunities

- **Phase 1**: T001 and T002 together
- **Phase 2**: T004 + T006 + T007 together (T004 has no dependency; T006/T007 are one chain)
- **Phase 3**: T008 + T009 + T010 together (three different files); T012 alongside them
- **Phase 4**: T014 + T015 together once T005 is done (two new route modules, no shared file)
- **Phase 6**: T020 + T022 together

### File-conflict warnings

- `frontend/src/components/subscription/subscription-plans.tsx` is touched by **T012 → T018 → T019** — these must run in that order, never in parallel
- `backend/src/main.py` is edited only by T016
- `frontend/src/components/subscription/employee-request-dialog.tsx` is created by T017 and only imported by T018

---

## Parallel Example: User Story 1

```text
# Independent route files — launch together:
Task: "Create frontend/src/app/login/page.tsx (dedicated sign-in route)"
Task: "Rewrite frontend/src/app/page.tsx as a pure redirect"
Task: "Repoint pages.signIn to /login in frontend/src/lib/auth.config.ts"
Task: "Create frontend/src/components/subscription/subscription-plans.tsx"

# Then, sequentially:
Task: "Remove the CloseTabWarning mount and delete the component (FR-002)"
Task: "Create frontend/src/app/subscription/page.tsx"
```

## Parallel Example: User Story 2

```text
# Two new backend route modules — launch together once the service exists:
Task: "Create backend/src/api/company_routes.py"
Task: "Create backend/src/api/employee_routes.py"

# Then, sequentially:
Task: "Register both routers in backend/src/main.py"
Task: "Create frontend/src/components/subscription/employee-request-dialog.tsx"
Task: "Wire the dialog into subscription-plans.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (routing + landing page)
3. **STOP and VALIDATE**: `/` → `/login` → Google with no "Leave site?" → `/subscription`; signed-out visits to `/subscription` redirect
4. Deploy/demo if ready — this alone fixes the sign-in landing and the popup

> Phase 2 is deliberately **not** in the MVP path: US1 needs no database work.

### Incremental Delivery

1. Setup + US1 → validate → the new sign-in/landing gate is live (MVP)
2. Foundational → US2 → validate → the access request can actually be submitted and recorded
3. US3 → validate → the full product menu renders
4. Polish → quickstart.md pass

### Checkpoint discipline

There are no automated tests, so each phase's **Checkpoint** line is the verification gate. Do not start the next phase until the current checkpoint's scenario from `quickstart.md` passes by hand.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task
- Tests are absent by explicit instruction — do not add pytest/Playwright tasks
- Commit after each task or logical group
- The three new endpoints are guarded by the **existing** NextAuth middleware branch; no middleware file changes are needed (research R7)
- ⚠️ **Open item for the Developer**: the spec's Q1–Q5 answers were applied from the recommended options and were never individually confirmed. Q1 (composite vs. global ID uniqueness) is the only one that changes a task materially — it would alter T003's index and T015's 409 mapping. Confirm before starting Phase 2.
