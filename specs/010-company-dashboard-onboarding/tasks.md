# Tasks: Company Dashboard & Onboarding Flow

**Input**: Design documents from `/specs/010-company-dashboard-onboarding/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/company-auth-api.yaml ✅, quickstart.md ✅

**Tests**: **None.** Automated tests are explicitly excluded by the feature specification ("no tests") and by the Developer's standing instruction. No test tasks are generated; verification is the manual pass in `quickstart.md`.

**Organization**: Tasks are grouped by user story so each can be implemented and verified independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Every task names its exact file path

## Path Conventions

Web application — the repo already has two roots:

- Backend: `backend/src/` (`api/`, `models/`, `services/`)
- Frontend: `frontend/src/` (`app/`, `components/`, `lib/`, `types/`)

## Code Standards (apply to EVERY new or edited file)

Per the project constitution, every Python/TS file must begin with the Bismillah header (`# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` / `/* … */`), end with the footer (`# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`), and mark the logical crux inline with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`. Use JS comment blocks (`/** */`) for TS/JSX file headers — never `#`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the feature needs nothing installed beyond what already exists, and lay out the settings and folders it lives in.

- [X] T001 [P] Confirm this feature adds **no dependencies** — verify `motion` and `@tabler/icons-react` are already in `frontend/package.json` and that nothing in `backend/requirements.txt` / `backend/pyproject.toml` / `frontend/package.json` needs to change (research R16), and record the result
- [X] T002 [P] Add the `COMPANY_JWT_SECRET: str = ""` and `COMPANY_JWT_TTL_HOURS: int = 24` settings to `backend/src/config.py` (mirroring the `ADMIN_JWT_*` block) and the matching `COMPANY_JWT_SECRET=` line to `backend/.env.example`
- [X] T003 [P] Create the feature folders: `frontend/src/components/company-request/`, `frontend/src/components/company-dashboard/`, `frontend/src/lib/company/`, and the route folder `frontend/src/app/CompanyDashboard/`

**Checkpoint**: Nothing to install; settings and folder structure ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared UI primitive, types, placeholder data, and client session store that the company dashboard and admin category are built on.

- [X] T004 [P] Add the Aceternity **sidebar** to `frontend/src/components/ui/sidebar.tsx` via the project registry (`npx shadcn@latest add @aceternity/sidebar`, or write the registry file verbatim) — its only deps (`motion`, `@tabler/icons-react`) are already installed, so **no dependency changes** (research R11). Used by US3 and US4.
- [X] T005 [P] Create `frontend/src/types/company.types.ts` with `CompanyIdentity`, `CompanySession` (`token`, `company`, `expires_at`), `CompanyLoginRequest`/`CompanyLoginResponse` (matching `contracts/company-auth-api.yaml`), plus `PlaceholderEmployee` and `PlaceholderCompanyRequest` shapes
- [X] T006 [P] Create `frontend/src/lib/company/company-placeholder.ts` — a small sample employee list and a sample company-request list, each commented as a deliberate stand-in for the backend specification (FR-024)
- [X] T007 [P] Create `frontend/src/lib/company/company-session.ts` — a `localStorage`-backed session store (`{ token, company, expires_at }`) with `subscribe`/`getSnapshot`/`getServerSnapshot` and `setCompanySession`/`clearCompanySession`, mirroring `frontend/src/lib/admin/admin-session.ts` but using `localStorage` and treating an entry whose `expires_at` is past as signed out (research R3, FR-018)

**Checkpoint**: The sidebar, types, placeholder data, and session store exist — user stories can begin.

---

## Phase 3: User Story 1 - Cinematic "Company Request" onboarding flow (Priority: P1) 🎯 MVP

**Goal**: Clicking **Company Request** on `/subscription` opens a full-screen cinematic overlay (cherry block → center star streaks → growing building → window entry → bored-boss guide → four fading questions → typewriter success → 5s auto-fade, with a skip cross). Nothing is persisted.

**Independent Test**: From `/subscription`, click Company Request → watch the intro, answer the four questions (a malformed answer blocks advancing), see the boss states and the typewriter message, confirm the auto-fade after 5s, and confirm the cross dismisses mid-flow with nothing recorded.

- [X] T008 [P] [US1] Create `frontend/src/lib/company/company-validation.ts` — pure validators for the four steps: name/role non-empty; website/socials a web address (URL/domain) or an `@handle`; email email-shaped; phone digits with optional `+ ( ) -` and spaces (FR-008, research R10)
- [X] T009 [P] [US1] Port the bored-boss loader: create `frontend/src/components/company-request/boss-loader.tsx` + `frontend/src/components/company-request/boss-loader.module.css` from `frontend/boss-loader.html` (SVG markup + keyframes verbatim, no JS), exposing idle / hands-up / smile states the parent controls; then **delete `frontend/boss-loader.html`** (FR-006/009/010, research R8)
- [X] T010 [P] [US1] Create `frontend/src/components/company-request/company-building.tsx` — the centered company-building SVG (a simple multi-window facade) that scales up as the "camera" approaches (FR-004)
- [X] T011 [P] [US1] Create `frontend/src/components/company-request/star-field.tsx` — center-origin star streaks conveying motion into the screen (may reuse the technique of `components/ui/stars-background.tsx`/`shooting-stars.tsx`, but streaks radiate outward from the center) (FR-003)
- [X] T012 [US1] Create `frontend/src/components/company-request/cinematic-intro.tsx` — a `motion` sequence: the cherry block (`bg-primary`) slides in with a motion-blur settle, the star field plays, the building grows over ~5s, then the view enters a window and the building fades; skip/park the motion-heavy parts under `useReducedMotion()` (FR-002–FR-005, FR-014) (depends on T010, T011)
- [X] T013 [US1] Create `frontend/src/components/company-request/onboarding-questions.tsx` — the four steps rendered one at a time with a fade (Company Name, Role, Website/Socials, Email and Phone Number), each gated by `companyValidation`, with inline error messages; the same contact step captures email + phone (FR-007, FR-008) (depends on T008)
- [X] T014 [P] [US1] Create `frontend/src/components/company-request/request-success.tsx` — clears the animation and renders the existing `TypewriterEffect` (`components/ui/typewriter-effect.tsx`) with the exact string **"Request Sent Successfully - Please Wait For The Team To Contact Your Representative"** (FR-011, research R9)
- [X] T015 [US1] Create `frontend/src/components/company-request/company-request-flow.tsx` — the full-screen overlay orchestrator: the `intro → questions → success` phase machine, the always-available top-right **cross**, the boss state wiring (tapping → hands-up on advance → smile at the end), and the 5-second auto-close after the success message (FR-012, FR-013, FR-025) (depends on T009, T012, T013, T014)
- [X] T016 [US1] Wire the **Company Request** button in `frontend/src/components/subscription/subscription-plans.tsx` to open `<CompanyRequestFlow/>` (replace the inert handler; mount the overlay so it covers the viewport) (depends on T015) (FR-001)

**Checkpoint**: The cinematic onboarding runs end to end from `/subscription`; nothing is persisted.

---

## Phase 4: User Story 2 - Company sign-in to the Company Dashboard (Priority: P1)

**Goal**: `/CompanyDashboard` shows a Company Name + Password form; valid credentials (checked server-side against the 008 `companies` table) open the dashboard and establish a 24-hour session; invalid credentials are denied generically.

**Independent Test**: Open `/CompanyDashboard` signed out → form; submit an unknown company or wrong password → identical generic denial; submit correct credentials → dashboard opens; reload/reopen the browser within 24h → still signed in; an expired/cleared session returns the form.

- [X] T017 [P] [US2] Create `backend/src/models/company_auth_models.py` — `CompanyLoginRequest`, `CompanyLoginResponse`, and `CompanyIdentity` pydantic models matching `contracts/company-auth-api.yaml` (mirror `backend/src/models/admin_models.py`)
- [X] T018 [P] [US2] Add `get_company_by_name(name: str)` to `backend/src/services/company_service.py` — a case-insensitive, trimmed lookup (`WHERE lower(name) = lower($1) LIMIT 1`) over `db_service` (research R4)
- [X] T019 [US2] Create `backend/src/services/company_auth_service.py` — `verify_company_credentials(name, password)` (lookup via T018; decrypt with `company_crypto_service.decrypt_password`; compare constant-time via `hmac.compare_digest`; raise `CompanyAuthNotConfiguredError` when the secret/key is absent) and `issue_company_token()` (HS256 JWT signed with `COMPANY_JWT_SECRET`, 24h, returning `(token, expires_at)`); mark the crux method with the inline marker (depends on T017, T018) (research R1, R5)
- [X] T020 [US2] Create `backend/src/api/company_auth_routes.py` — `router = APIRouter(prefix="/api/company", tags=["company"])` with `POST /login`: map missing fields → 400 `missing_field`, bad credentials → **generic** 401 `invalid_credentials` (identical for unknown company and wrong password), missing secret/key → 503; never return password material (depends on T019)
- [X] T021 [US2] Add the company branch to `backend/src/api/auth_middleware.py` — `COMPANY_PREFIX = "/api/company"`, `COMPANY_LOGIN_PATH = "/api/company/login"`; the login path is public, any other `/api/company/*` path is verified against the company JWT (401 otherwise); the admin and NextAuth branches are untouched (depends on T019) (research R2)
- [X] T022 [US2] Register the router in `backend/src/main.py` (`from src.api.company_auth_routes import router as company_auth_router`, then `app.include_router(company_auth_router)`) (depends on T020)
- [X] T023 [P] [US2] Create `frontend/src/lib/api/companyClient.ts` — a `fetch` singleton (`API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`) with a `CompanyApiError` class and `login(name, password)`, mirroring `frontend/src/lib/api/adminClient.ts`'s `handleResponse`/error-extraction shape (depends on T005)
- [X] T024 [US2] Create `frontend/src/components/company-dashboard/company-sign-in-form.tsx` — Company Name + Password inputs, a generic inline error on a failed sign-in, and a submit that calls `companyClient.login()` and writes the session via `setCompanySession()` (depends on T023, T007)
- [X] T025 [US2] Create `frontend/src/components/company-dashboard/company-dashboard.tsx` — the client shell: read the session via `useSyncExternalStore(company-session)`, render `<CompanySignInForm/>` when absent/expired and the dashboard when present, and clear the session + return to the form on any 401 (depends on T024, T007)
- [X] T026 [US2] Create `frontend/src/app/CompanyDashboard/page.tsx` — a thin `export const dynamic = "force-dynamic"` server shell with `robots: { index: false }` metadata rendering `<CompanyDashboard/>` (no NextAuth `auth()` guard — the company session is client-held) (depends on T025) (research R6)

**Checkpoint**: A company can sign in with real credentials and stays signed in for 24 hours; wrong credentials are denied generically.

---

## Phase 5: User Story 3 - Company Dashboard with Employees and Subscription sections (Priority: P2)

**Goal**: After sign-in the dashboard shows a sidebar with exactly two sections — **Employees** (a shadcn table with a per-row **Grant Access** checkmark) and **Subscription** (an inert "Start 30 days free trial" card).

**Independent Test**: Sign in, confirm the two sidebar sections; the Employees table lists rows with a Grant Access action that changes state on click (empty state when none); the Subscription card is present and inert.

- [X] T027 [P] [US3] Create `frontend/src/components/company-dashboard/company-sidebar.tsx` — wraps the Aceternity `Sidebar` (`components/ui/sidebar.tsx`) with exactly two links: **Employees** and **Subscription**, wired to a selected-section state (depends on T004) (FR-019, research R11)
- [X] T028 [P] [US3] Create `frontend/src/components/company-dashboard/employees-table.tsx` — a shadcn `Table` (`components/ui/table.tsx`) listing employees with Employee, Employee ID, Status, and a **Grant Access** checkmark action that toggles a local `granted` state; renders from `company-placeholder.ts` with an explicit empty state (depends on T006) (FR-020, FR-021)
- [X] T029 [P] [US3] Create `frontend/src/components/company-dashboard/subscription-panel.tsx` — a small `Card` reading **"Start 30 days free trial"** with no handler (FR-022)
- [X] T030 [US3] Integrate the sidebar and the two sections into `frontend/src/components/company-dashboard/company-dashboard.tsx` (render the sidebar + the selected section: Employees table or Subscription panel) (depends on T025, T027, T028, T029)

**Checkpoint**: The signed-in dashboard shows exactly the two sections and both work as specified.

---

## Phase 6: User Story 4 - "Company Requests" category in the Admin Dashboard (Priority: P3)

**Goal**: The existing `AdminDashAccess` dashboard gains a **Company Requests** category listing placeholder requests, with a detail view showing the company's submitted details for contacting.

**Independent Test**: Open `/AdminDashAccess`, sign in, confirm the "Company Requests" category alongside the companies list, open a request → its Company Name/Role/Website-Socials/Email/Phone are shown; empty state when none.

- [X] T031 [P] [US4] Create `frontend/src/components/admin/company-requests-table.tsx` — a shadcn `Table` listing placeholder requests (Company, Role, Website/Socials, Email, Phone) with a row action opening a shadcn `Dialog` that shows the full submitted details; renders from `company-placeholder.ts` with an explicit empty state (depends on T006) (FR-023, FR-024)
- [X] T032 [US4] Add the category navigation to `frontend/src/components/admin/admin-dashboard.tsx` — reuse the Aceternity `Sidebar` (`components/ui/sidebar.tsx`) with **Companies** (the existing table, unchanged) and **Company Requests** (T031); default to Companies (depends on T004, T031) (FR-023)

**Checkpoint**: The Developer can reach the new category and read a request's details.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Project-wide checks that span all four stories.

- [X] T033 [P] Verify Code Standards 1–3 on every file created or edited by this feature — Bismillah header, footer, and the inline crux marker on the logical crux methods (at minimum: `company_auth_service.verify_company_credentials`/`issue_company_token`, and `company-request-flow.tsx`'s phase machine)
- [X] T034 [P] Confirm the deliberate non-goals hold — no new dependencies (`git diff backend/requirements.txt backend/pyproject.toml frontend/package.json`), **no new DB tables/migrations** (`backend/src/models/db_migrations.py` unchanged), no automated tests added (`backend/tests`, `frontend/src/app/tests`), and `frontend/boss-loader.html` deleted
- [ ] T035 Run the full `quickstart.md` manual verification pass (sections 1–6), including the tricky paths (malformed answer blocks advancing, session expiry on read, identical generic denial, no request stored anywhere, fail-closed 503s) and the non-regression checks (admin surface unchanged; `/api/company/*` non-login paths 401)

**Verification status (2026-10-01)**: T033 and T034 are done — every new or edited file carries the Bismillah header and footer (including the vendored `sidebar.tsx` and the ported `boss-loader`), the crux methods in `company_auth_service.py` carry the inline marker, no dependency or migration file was touched by this feature (the `M` entries on `package.json`/`requirements*`/`db_migrations.py` are pre-existing from 008/009), no tests were added, and `frontend/boss-loader.html` is deleted. For T035 the automated substitute pass was run and passed: `tsc --noEmit`; `eslint` on every touched file (0 errors); `next build` (all routes compile, `/CompanyDashboard` dynamic); a backend byte-compile plus a real import of `main` and the company modules; and an OpenAPI check confirming `/api/company/login` is registered with `COMPANY_LOGIN_PATH` public. The **live** browser walkthrough — a real company sign-in against CockroachDB, the cinematic timing, and the fail-closed 503 probes — still needs the stack up, so T035 is left unchecked.
**Checkpoint**: The feature matches the spec and `quickstart.md` exactly, with no scope creep.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup. Blocks US2–US4; **US1 is not blocked** (it needs only `company-validation.ts` from T008)
- **US1 (Phase 3)**: Depends on Setup only — the cinematic flow is frontend-only
- **US2 (Phase 4)**: Depends on Foundational (T005, T007) and Setup (T002)
- **US3 (Phase 5)**: Depends on Foundational (T004, T006) and on US2's shell (T025)
- **US4 (Phase 6)**: Depends on Foundational (T004, T006) — independent of US2/US3
- **Polish (Phase 7)**: Depends on US1 + US2 + US3 + US4

### Task-Level Dependencies

```text
T002 ─▶ T019
T017 ─┐
T018 ─┴─▶ T019 ─▶ T020 ─▶ T022
                └▶ T021

T005 ─▶ T023 ─▶ T024 ─▶ T025 ─▶ T026
T007 ──────────────────┘  │
                          ▼
T004 ─┬────────────────▶ T027 ─┐
T006 ─┼─▶ T028 ─────────────────┼─▶ T030
      ├─▶ T029 ─────────────────┘
      └─▶ T031 ─▶ T032

T008 ─▶ T013 ─┐
T010 ─┐        │
T011 ─┴─▶ T012 ┼─▶ T015 ─▶ T016
T009 ─────────┤
T014 ─────────┘
```

### Suggested order

1. T001, T002, T003 (setup)
2. T004, T005, T006, T007 (foundation)
3. T008 → T009, T010, T011, T014 (parallel) → T012 → T013 → T015 → T016 → **validate US1 (MVP)**
4. T017, T018 → T019 → T020, T021 → T022; T023 → T024 → T025 → T026 → **validate US2**
5. T027, T028, T029 → T030 → **validate US3**
6. T031 → T032 → **validate US4**
7. T033, T034, T035

### Parallel Opportunities

- **Setup**: T001 + T002 + T003 together
- **Foundational**: T004 + T005 + T006 + T007 together (four different files)
- **US1**: T009 + T010 + T011 + T014 together once T008 exists (four independent files)
- **US2 backend**: T017 + T018 together; then T020 + T021 together once T019 exists
- **US2 frontend**: T023 once T005 exists (parallel with the backend chain)
- **US3**: T027 + T028 + T029 together
- **Polish**: T033 + T034 together

### File-conflict warnings

- `frontend/src/components/subscription/subscription-plans.tsx` is edited only by T016
- `frontend/src/components/company-dashboard/company-dashboard.tsx` is created by T025 and edited by T030 — run in that order
- `frontend/src/components/admin/admin-dashboard.tsx` is edited only by T032
- `backend/src/api/auth_middleware.py` is edited only by T021; `backend/src/main.py` only by T022
- `frontend/src/components/ui/sidebar.tsx` is created by T004 and only imported by T027/T032

---

## Parallel Example: User Story 1

```text
# Independent asset/component files — launch together after T008:
Task: "Port the boss loader to frontend/src/components/company-request/boss-loader.tsx + .module.css and delete frontend/boss-loader.html"
Task: "Create frontend/src/components/company-request/company-building.tsx"
Task: "Create frontend/src/components/company-request/star-field.tsx"
Task: "Create frontend/src/components/company-request/request-success.tsx"

# Then, sequentially:
Task: "Create cinematic-intro.tsx (composes building + star field)"
Task: "Create onboarding-questions.tsx"
Task: "Create company-request-flow.tsx (composes intro + questions + success + boss)"
Task: "Wire Company Request into subscription-plans.tsx"
```

## Parallel Example: User Story 2

```text
# Backend models + service read, together:
Task: "Create backend/src/models/company_auth_models.py"
Task: "Add get_company_by_name() to backend/src/services/company_service.py"

# Then the service, then the two wiring points (parallel):
Task: "Create backend/src/services/company_auth_service.py"
Task: "Create backend/src/api/company_auth_routes.py"
Task: "Add the company branch to backend/src/api/auth_middleware.py"

# Frontend client chain, parallel with the backend:
Task: "Create frontend/src/lib/api/companyClient.ts"
Task: "Create frontend/src/components/company-dashboard/company-sign-in-form.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → Phase 2: Foundational
2. Complete Phase 3: User Story 1 (the cinematic onboarding — the headline feature)
3. **STOP and VALIDATE**: run the US1 section of `quickstart.md` from `/subscription`
4. Deploy/demo if ready — this alone replaces the inert button with the full onboarding experience

> US2 is also P1; the two are independent and can be built in either order. US1 is chosen as the first demo because it is purely frontend and has no backend prerequisite.

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → validate → the cinematic onboarding is live (MVP)
3. US2 → validate → companies can sign in to the dashboard (24h session)
4. US3 → validate → the dashboard shows Employees + Subscription
5. US4 → validate → the admin can see Company Requests
6. Polish → `quickstart.md` pass

### Checkpoint discipline

There are no automated tests, so each phase's **Checkpoint** line is the verification gate. Do not start the next phase until the current checkpoint's scenario from `quickstart.md` passes by hand.

---

## Notes

- `[P]` = different files, no dependency on an incomplete task
- Tests are absent by explicit instruction — do not add pytest/Playwright tasks
- Commit after each task or logical group
- The company sign-in endpoint is the **only** new backend route; the request submission, employees table, Company Requests view, and subscription card are frontend structure with placeholder data (FR-024)
- The Aceternity sidebar requires **no** dependency install — `motion` and `@tabler/icons-react` are already present (research R11)
- ⚠️ **Open item for the Developer**: research R1 recommends issuing a signed 24-hour company JWT (`COMPANY_JWT_SECRET`) rather than a client-only session flag, because the spec frames sign-in as establishing a session (FR-018). It is flagged reversible; if you prefer a client-only flag before starting Phase 4, drop T002's secret, T019's token issuance, and T021's branch — the rest is unchanged.
