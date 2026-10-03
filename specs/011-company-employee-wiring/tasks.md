# Tasks: Company-Employee Dashboard Wiring, Finalized Sign Conventions & Edge Cases

**Input**: Design documents from `/specs/011-company-employee-wiring/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: **None** — the Developer's standing instruction is "no tests"; verification is the manual `quickstart.md` pass. No test tasks are generated.

**Organization**: Tasks are grouped by user story (P1 → P3) so each story can be implemented and validated independently. Every new/edited file MUST carry the constitution's header (`# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ`) and footer (`# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`), with the crux marker (`# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`) on logical-critical methods.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1…US7 (maps to spec.md user stories); omitted in Setup/Foundational/Polish
- Exact file paths are included in every task

## Path Conventions

Web app: `backend/src/...` and `frontend/src/...` (see plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, configuration, and the additive schema this feature needs.

- [X] T001 Add the `resend` package to `backend/requirements.txt` and `backend/pyproject.toml`
- [X] T002 [P] Add `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `COMPANY_REQUEST_NOTIFY_EMAIL` (default `ArhamBrowser@gmail.com`) to `backend/src/config.py` and document them in `backend/.env.example`
- [X] T003 Edit `backend/src/models/db_migrations.py`: add the `company_requests` table + `idx_company_requests_submitted_at`, `ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_manager`, `idx_employees_account_user_id`, and `idx_employees_company_id`; append every statement to `MIGRATIONS`
- [X] T004 Add an async `transaction()` context manager (or a `run_in_transaction` helper) to `backend/src/services/db_service.py` for multi-statement operations (used by the cascade delete in T041)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared request/response schemas and API contracts that the story endpoints consume. No user-story work should start until these compile.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 [P] Extend `backend/src/models/employee_models.py` with `CompanyEmployee`, `EmployeeListResponse`, `EmployeeManagerUpdate`, `Membership`, and `MembershipResponse` (stringify ids, per existing style)
- [X] T006 [P] Create `backend/src/models/company_request_models.py` with `CompanyRequestCreate`, `CompanyRequest`, and `CompanyRequestListResponse`
- [X] T007 [P] Extend `backend/src/models/admin_models.py`: add `employee_count` to `Company`, plus `AdminEmployee` and `AdminEmployeeListResponse`
- [X] T008 [P] Extend frontend types: `frontend/src/types/employee.types.ts` (membership + company-employee shapes) and create `frontend/src/types/companyRequest.types.ts`
- [X] T009 [P] Extend `frontend/src/types/admin.types.ts` with `employee_count` and `AdminEmployee`
- [X] T010 [P] Extend the API clients to match the contracts: `frontend/src/lib/api/companyClient.ts` (listEmployees/grant/delete/setManager), `frontend/src/lib/api/adminClient.ts` (listCompanyRequests/listCompanyEmployees), `frontend/src/lib/api/employeeClient.ts` (`getMembership` and `removeMembership` — the latter serves both cancelling a pending request and leaving a granted company — plus `createCompanyRequest`), and create `frontend/src/lib/api/companyRequestClient.ts`

**Checkpoint**: Schemas and clients are ready — user stories can now start.

---

## Phase 3: User Story 1 - A company sees, searches, grants, and deletes employee requests (Priority: P1) 🎯 MVP

**Goal**: A company signs in and manages its employee requests as real, searchable rows.

**Independent Test**: Submit a request, sign in as the company, confirm it appears, search by ID and by name, grant one, delete another.

### Implementation for User Story 1

- [X] T011 [US1] Extend `backend/src/services/employee_service.py` with `list_employees_for_company`, `grant_access`, and `delete_employee` (raw asyncpg, `$n`)
- [X] T012 [US1] Create `backend/src/api/company_employee_routes.py` with `GET /api/company/employees` (optional `?q=`), `POST /api/company/employees/{id}/grant`, and `DELETE /api/company/employees/{id}` — company identity from `request.state.company_id`
- [X] T013 [US1] Register the company-employee router in `backend/src/main.py`
- [X] T014 [US1] Add `GET /api/company/{company_id}/logo` to `backend/src/api/company_employee_routes.py` and point the login response's `logo_url` at it in `backend/src/api/company_auth_routes.py` (fixes the dangling URL)
- [X] T015 [US1] Rewrite `frontend/src/components/company-dashboard/employees-table.tsx` to fetch real data via `companyClient`, filter with ID-then-name precedence, and render Grant/Delete actions with loading/empty/error states
- [X] T016 [US1] Update `frontend/src/components/company-dashboard/company-dashboard.tsx` to pass the company session token into the employees table and refresh after grant/delete

**Checkpoint**: User Story 1 is fully functional and testable on its own.

---

## Phase 4: User Story 2 - Granted access gates the application, and can be cancelled/left (Priority: P1)

**Goal**: No application access without a granted membership; a pending request can be cancelled; a granted membership can be left with confirmation; the request flow enforces one active request.

**Independent Test**: A no-grant account is blocked everywhere except subscription/sign-in; after a grant it works; leaving revokes; a second request is blocked until the pending one is cancelled.

### Implementation for User Story 2

- [X] T017 [US2] Extend `backend/src/services/employee_service.py` `create_employee_request` to reject when the account already has a `pending`/`accepted` row (new `ActiveRequestExistsError`)
- [X] T018 [US2] Return `409 active_request_exists` from `backend/src/api/employee_routes.py`
- [X] T019 [P] [US2] Create `backend/src/services/membership_service.py` (`get_accepted_membership`, `delete_membership` — deletes the account's employee row for either cancel or leave, `count_for_company`)
- [X] T020 [US2] Create `backend/src/api/me_routes.py` with `GET /api/me/membership` and `DELETE /api/me/membership` (deletes the account's employee row — serves **both** cancelling a `pending` request and leaving a granted company, per FR-017 and FR-015), and register it in `backend/src/main.py`
- [X] T021 [US2] Add the membership gate + exact allow-list to the NextAuth branch of `backend/src/api/auth_middleware.py` (allow: `/api/company-requests`, `/api/companies`, `/api/me/membership`, `/api/employees/requests`, plus existing public/admin/company prefixes)
- [X] T022 [P] [US2] Create `frontend/src/lib/membership.ts` with `getMembership(token)` and `requireMembership()` (server helper redirecting to `/subscription`)
- [X] T023 [US2] Guard `frontend/src/app/upload-ai/page.tsx` with `requireMembership()`
- [X] T024 [US2] Update `frontend/src/app/subscription/page.tsx` to redirect a current member back to the app (must leave first)
- [X] T025 [US2] Create `frontend/src/components/navigation/navigation.tsx` (membership-aware header with the company name + a confirmed **Leave company** action calling `removeMembership`, app links hidden when not a member) and use it in `frontend/src/app/layout.tsx`
- [X] T026 [US2] Update `frontend/src/components/subscription/employee-request-dialog.tsx` to surface the `active_request_exists` message with a **Cancel request** action (calls `removeMembership` to delete the pending row, per FR-017), and to refresh membership after a successful submit

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Company onboarding requests reach the Admin Dashboard and the Developer's inbox (Priority: P2)

**Goal**: "Company Request" submissions are persisted, listed in the Admin Dashboard, and email the Developer.

**Independent Test**: Submit the onboarding flow → a real row appears in Admin → Company Requests and a notification email is sent (and an email failure still stores the request).

### Implementation for User Story 3

- [X] T027 [P] [US3] Create `backend/src/services/notification_service.py` with `send_company_request_notification` (Resend; skips with a warning when `RESEND_API_KEY` is empty; never raises into the route)
- [X] T028 [P] [US3] Create `backend/src/services/company_request_service.py` with `create_company_request` and `list_company_requests`
- [X] T029 [US3] Create `backend/src/api/company_requests_routes.py` with `POST /api/company-requests` (persist, then best-effort email, return 201) and register it in `backend/src/main.py`
- [X] T030 [US3] Add `GET /api/admin/company-requests` to `backend/src/api/admin_routes.py`
- [X] T031 [US3] Rewrite `frontend/src/components/admin/company-requests-table.tsx` to fetch real requests (loading/empty/error, detail dialog)
- [X] T032 [US3] Update `frontend/src/components/company-request/company-request-flow.tsx` and `frontend/src/components/company-request/onboarding-questions.tsx` to collect the four answers and POST them on completion (keep the existing cinematic behavior/success message)
- [X] T033 [US3] Remove the now-unused placeholder company requests from `frontend/src/lib/company/company-placeholder.ts` and its imports

**Checkpoint**: Onboarding requests flow to the Admin Dashboard and the inbox.

---

## Phase 6: User Story 6 - One finalized sign convention everywhere (Priority: P2)

**Goal**: The canonical credit/debit mapping holds from the backend engine through storage to every frontend surface.

**Independent Test**: Run Bank and Vendor reconciliations and confirm every category's sign matches `contracts/sign-convention.md` §1 on results, subtotals, adjustments, verdict, history, and export.

### Implementation for User Story 6

- [X] T034 [US6] Flip the Bank and Vendor `Debit/Credit` sign assignment in the backend reconciliation extractor(s) so stored values match `contracts/sign-convention.md` §2 (locate the assignment sites under `backend/src/services/`)
- [X] T035 [US6] Update `frontend/src/lib/utils/categorizationUtils.ts` (`categorizeTransaction`, `getDisplayAmount`, `categoryLabel`) for the finalized mapping
- [X] T036 [US6] Update `categorizeDiscrepancy` in `frontend/src/components/results/ReconciliationResults.tsx`
- [X] T037 [US6] Recompute the adjustment sums and adjusted balances in `frontend/src/components/results/ReconciliationTotals.tsx` and the adjusted-balance block in `frontend/src/components/results/CategorizedResults.tsx` so the verdict stays consistent with the displayed signs
- [X] T038 [US6] Verify saved/history/export surfaces render the stored canonical signs (no per-surface flip) and note the legacy-data consequence in code comments

**Checkpoint**: Signs are consistent end-to-end in both modes.

---

## Phase 7: User Story 4 - Admin employee count, roster, and company-delete cascade (Priority: P3)

**Goal**: The Admin companies table shows a per-company employee count with a hover roster, and deleting a company removes its employee records.

**Independent Test**: A company with employees shows a count; hovering opens a modal listing exactly its employees; zero shows an empty state; deleting the company removes its employees and revokes their access.

### Implementation for User Story 4

- [X] T039 [US4] Extend `backend/src/services/company_service.py`: include `employee_count` in `list_companies` (LEFT JOIN / subquery) and add `list_employees_for_company` (admin roster)
- [X] T040 [US4] Add `GET /api/admin/companies/{company_id}/employees` to `backend/src/api/admin_routes.py`
- [X] T041 [US4] Edit `backend/src/services/company_service.py` `delete_company` to also `DELETE FROM employees WHERE company_id = $1` inside the transaction helper from T004, so deleting a company removes its employee records and revokes their application access **without deleting the user accounts** (FR-023 — HIGH; must not be deferred)
- [X] T042 [US4] Update `frontend/src/components/admin/companies-table.tsx` to show the employee count and a hover-triggered modal listing the company's employees

**Checkpoint**: Admin employee count + roster work, and company deletion cascades.

---

## Phase 8: User Story 5 - Manager role and a hidden Company Dashboard entry (Priority: P3)

**Goal**: A company marks accounts as Manager; a manager who is also using the app gets a "Company Dashboard" nav entry; the address stays hidden otherwise.

**Independent Test**: Toggle Manager on an accepted member → their nav gains the dashboard entry; a non-manager sees none.

### Implementation for User Story 5

- [X] T043 [US5] Add `PATCH /api/company/employees/{id}` (`{ is_manager }`) to `backend/src/api/company_employee_routes.py`, calling `employee_service.set_manager`
- [X] T044 [US5] Add a Manager toggle (and manager badge) to `frontend/src/components/company-dashboard/employees-table.tsx`
- [X] T045 [US5] Add the conditional **Company Dashboard** entry (only for a member whose `is_manager` is true) to `frontend/src/components/navigation/navigation.tsx`

**Checkpoint**: Manager role + nav entry work; the dashboard address stays undiscovered.

---

## Phase 9: User Story 7 - Smoother animations app-wide (Priority: P3)

**Goal**: A consistent, smooth polish pass over existing transitions.

**Independent Test**: Key transitions play smoothly and consistently; reduced motion skips/softens motion-heavy parts while screens stay usable.

### Implementation for User Story 7

- [X] T046 [P] [US7] Polish the onboarding overlay transitions in `frontend/src/components/company-request/` (intro, question fades, success)
- [X] T047 [P] [US7] Polish the sidebar + section transitions in `frontend/src/components/company-dashboard/` and `frontend/src/components/admin/`
- [X] T048 [P] [US7] Polish list/table reveals and loaders in `frontend/src/components/ui/` and the dashboard tables
- [X] T049 [US7] Ensure every polished animation honors `prefers-reduced-motion` (skip/soften) with screens fully usable

**Checkpoint**: Animations are smooth, consistent, and reduced-motion safe.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and end-to-end validation across stories.

- [X] T050 Remove all remaining dummy/placeholder data backing the company dashboard, company requests, and admin views (FR-008) — audit `frontend/src/lib/company/company-placeholder.ts` and its importers
- [X] T051 Verify every new/edited file (e.g. `backend/src/api/company_employee_routes.py`, `backend/src/services/membership_service.py`, `backend/src/services/notification_service.py`, `frontend/src/components/navigation/navigation.tsx`) carries the header + footer, with the crux marker on the sign-mapping and notification-send methods
- [X] T052 [P] Update `backend/.env.example` and any docs for the three new Resend env vars
- [X] T053 Confirm the membership allow-list does not lock out `/api/employees/requests`, `/api/companies`, `/api/me/membership`, or `/api/company-requests`, and that the Individual Plans "coming soon" items are unchanged (FR-021)
- [ ] T054 Run the full `quickstart.md` manual pass end-to-end and record the results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately
- **Foundational (Phase 2)**: depends on Setup — BLOCKS all user stories
- **User Stories (Phases 3–9)**: depend on Foundational; within the priority order below
- **Polish (Phase 10)**: depends on all desired stories

### User Story Dependencies

- **US1 (P1)**: after Foundational — no other story needed
- **US2 (P1)**: after Foundational — independent of US1 (gate + membership); integrates with US1 only at the nav/leave layer
- **US3 (P2)**: after Foundational — independent
- **US6 (P2)**: after Foundational — independent (signs); touches different files than US1–US3
- **US4 (P3)**: after Foundational — best after US1 (employees exist) but not blocked by it; the cascade (T041) also protects US2's gate from orphaned rows
- **US5 (P3)**: after US1 (uses the employees table) and US2 (nav + membership)
- **US7 (P3)**: after the components it polishes exist (US1–US3)

### Within Each User Story

- Shared models/clients (Phase 2) before services; services before routes/endpoints; endpoints before frontend components.

### Parallel Opportunities

- Setup: T002 ∥ T003 ∥ T004 (T001 first)
- Foundational: T005 ∥ T006 ∥ T007 ∥ T008 ∥ T009 ∥ T010
- US2: T019 ∥ T022
- US3: T027 ∥ T028
- US6: T034 ∥ T035 (different files)
- US7: T046 ∥ T047 ∥ T048

---

## Parallel Example: Foundational

```text
Task: "Extend backend/src/models/employee_models.py with membership + management schemas"
Task: "Create backend/src/models/company_request_models.py"
Task: "Extend backend/src/models/admin_models.py with employee_count + AdminEmployee"
Task: "Extend frontend/src/types/employee.types.ts and create companyRequest.types.ts"
Task: "Extend the frontend API clients for the new endpoints"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational
2. Phase 3 (US1: real, searchable, grant/delete employee requests)
3. **STOP and VALIDATE** via quickstart §A
4. Demo if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → validate (MVP)
3. US2 → validate (the gate + cancel/leave) — this is the security milestone
4. US3 → validate (onboarding → admin + email)
5. US6 → validate (signs)
6. US4 → validate (admin count/modal + cascade)
7. US5 → validate (manager + nav)
8. US7 → validate (animation polish)
9. Polish → full quickstart pass

### Notes

- [P] = different files, no dependency on an incomplete task
- No tests per the standing instruction; every story's "Independent Test" maps to a `quickstart.md` section
- Commit after each task or logical group
- Highest risk: T021 (membership allow-list) — a wrong allow-list locks out the feature's own endpoints; T053 checks it explicitly
- Sign-flip blast radius: T034–T038 must land together to avoid a half-flipped UI
- **Cascade (T041)** must land before a company can be safely deleted once the US2 gate is live, so an orphaned employee row never silently keeps access
- **Cancel vs leave**: both delete the account's employee row through `DELETE /api/me/membership` — cancel (pending) and leave (granted) are the same operation from the account's perspective
