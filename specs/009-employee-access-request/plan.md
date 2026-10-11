# Implementation Plan: Employee Access Request (Subscription Layer)

**Branch**: `009-employee-access-request` | **Date**: 2026-09-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-employee-access-request/spec.md`

## Summary

Insert the subscription layer between sign-in and the application. A signed-in employee no longer lands in the reconciler: they land on a new `/subscription` page titled "Reconciliation AI for Companies" offering **Company Request** (inert), **Employee Request** (the live flow), and an **Individual Plans** panel (inert). Sign-in moves to its own `/login` route and the global "Leave site?" prompt that fires on Google sign-in is removed.

"Employee Request" opens a shadcn dialog capturing **Employee Name**, an **`adam-` prefixed ID** (typed or generated on the spot), and the **Company** (chosen from the Developer's onboarded companies, each with its logo or a placeholder). Submitting stores a row in a new `employees` table — separate from `companies` and from the app's `users` — with status `pending`, and shows the exact confirmation message. Uniqueness is enforced in the database on **(employee ID + company)**, so the same employee can request several companies but never twice the same one.

Backend: one new table via the existing raw-SQL migration list, one new service, two new route modules (three endpoints), **no new dependencies**. Frontend: one new page, one new feature component folder, one new API client, **no new dependencies** (every shadcn primitive needed already exists). No automated tests, per the Developer's standing instruction.

## Technical Context

**Language/Version**: Python 3.13 (backend, `requires-python >=3.13`); TypeScript 5.x on Next.js 16.2.9 / React 19.2.4 (frontend)  
**Primary Dependencies**: Backend — FastAPI, asyncpg, pydantic v2 (all existing). Frontend — Next.js App Router (RSC), NextAuth v5 (Google, JWT session exposing `session.user.access_token`), shadcn `base-nova` on Base UI, Tailwind v4, lucide-react (all existing). **No additions on either side.**  
**Storage**: CockroachDB via raw asyncpg (`db_service`, `$n` placeholders). Company logos stay on the filesystem in `COMPANY_LOGO_DIR`; this feature reads them, never writes them.  
**Testing**: None — automated tests are intentionally omitted per the Developer's explicit instruction ("no tests" in the spec input; 008 precedent); verification is the manual pass in `quickstart.md`  
**Target Platform**: Linux container for the backend (`python:3.13-bookworm-slim`), browser for the frontend  
**Project Type**: Web application (existing `backend/` + `frontend/` split)  
**Performance Goals**: The subscription page loads and the company dropdown populates in well under a second at the expected tens-of-companies scale; an employee submit is a single INSERT  
**Constraints**: No new dependencies; the `adam-` prefix is always system-applied; the ID is `adam-` + 6–12 lowercase alphanumerics with case-insensitive uniqueness; uniqueness is composite on (ID + company); no billing, no company-facing acceptance, and no gating of the existing app pages (all later specs); no automated tests  
**Scale/Scope**: Tens of companies; one new table; three new endpoints; one new page + one dialog; one new API client

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Assessment |
|-----------|--------|------------|
| I. Strict Instruction Following | ✅ PASS | Sign-in moves to its own route and the "Leave site?" prompt is removed (FR-001/002); the confirmation string is reproduced verbatim (FR-012); no tests are written; the inert buttons stay inert (FR-005/018). |
| II. Developer Stack Authority | ✅ PASS | Reuses FastAPI + asyncpg/CockroachDB + Next.js + NextAuth + shadcn. **Zero new dependencies** (research R12); no ORM reintroduced (SQLModel stays removed). |
| III. Supervised Collaboration | ✅ PASS | Every design choice is recorded with alternatives in research.md for Developer review; the Q1–Q5 clarification defaults are explicitly flagged as reversible (research R5). |
| IV. Constructive Objection | ✅ PASS | Two real conflicts are raised with mitigations rather than silently accepted: the clarification's "foreign key" wording versus 008's shipped hard-delete of companies (research R6 — no DB FK, validated at submit); and the admin-pinned logo endpoint being unable to serve employees (research R8 — dedicated authenticated path). |
| V. Controlled Creativity | ✅ PASS | No novel algorithm; the only new behaviour is a random string generator, which reuses the existing `generatePassword()` idiom. |
| VI. Ambiguity Resolution | ✅ PASS | No `NEEDS CLARIFICATION` remains in Technical Context. **Note for the Developer**: the spec's Q1–Q5 answers were applied from the recommended options (not individually confirmed); they are recorded in the spec's clarification session and are cheap to reverse — Q1 would touch only research R5/R6 and one index. |
| Code Standards 1–3 | ⚠️ REQUIRED | Every new Python/TS file MUST begin with the Bismillah header (`# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` / `/* … */`), end with the footer (`# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`), and mark the logical crux inline (`# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`) — applies to the two new route modules, `employee_service.py`, `employee_models.py`, the new page/components, the API client, and the types file, plus the edited `db_migrations.py` and `main.py`. |

**Initial gate: PASS.** One flagged item for the Developer, not a blocker: the reversible Q1–Q5 defaults.

## Project Structure

### Documentation (this feature)

```text
specs/009-employee-access-request/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (decisions + alternatives)
├── data-model.md        # Phase 1 output (entities, table, validation)
├── quickstart.md        # Phase 1 output (manual verification)
├── contracts/
│   └── employee-api.yaml # Phase 1 output (OpenAPI 3.1)
├── checklists/
│   └── requirements.md  # Spec quality checklist (/sp.specify + /sp.clarify)
└── tasks.md             # Phase 2 output (/sp.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
└── src/
    ├── main.py                              # + register company_router and employee_router
    ├── api/
    │   ├── company_routes.py                # NEW — GET /api/companies, GET /api/companies/{id}/logo
    │   ├── employee_routes.py               # NEW — POST /api/employees/requests
    │   ├── auth_middleware.py               # UNCHANGED — new paths ride the existing NextAuth branch
    │   └── admin_routes.py                  # UNCHANGED
    ├── models/
    │   ├── db_migrations.py                 # + CREATE_EMPLOYEES + uq_employee_id_company
    │   └── employee_models.py               # NEW — pydantic request/response models
    └── services/
        ├── employee_service.py              # NEW — normalize/validate ID + insert over db_service
        └── company_service.py               # UNCHANGED — reused for the dropdown list

frontend/
└── src/
    ├── app/
    │   ├── page.tsx                         # MODIFIED — pure redirect: signed-in → /subscription, else → /login
    │   ├── login/
    │   │   └── page.tsx                     # NEW — dedicated sign-in route
    │   ├── subscription/
    │   │   └── page.tsx                     # NEW — guarded (auth() → redirect("/login")) page shell
    │   └── layout.tsx                       # MODIFIED — remove <CloseTabWarning /> mount + import
    ├── components/
    │   ├── subscription/
    │   │   ├── subscription-plans.tsx       # NEW — title, Company Request, Employee Request, Individual Plans
    │   │   └── employee-request-dialog.tsx  # NEW — the request dialog (name, ID, company)
    │   └── auth/
    │       └── close-tab-warning.tsx        # DELETED — source of the "Leave site?" prompt (FR-002)
    ├── lib/
    │   ├── auth.config.ts                   # MODIFIED — pages.signIn: "/" → "/login"
    │   └── api/
    │       └── employeeClient.ts            # NEW — listCompanies / createRequest / fetchLogoBlob
    └── types/
        └── employee.types.ts                # NEW — EmployeeRequest, CompanyOption, request/response shapes
```

**Structure Decision**: Web application (Option 2) — the repo already has separate `backend/` and `frontend/` roots, so the feature is added along the existing seams: two new route modules registered in `main.py` mirroring `admin_routes.py`; one new service mirroring `company_service.py`; one new pydantic module mirroring `admin_models.py`; one new App Router page plus a `components/subscription/` feature folder mirroring `components/admin/`; and one new `lib/api/employeeClient.ts` mirroring `adminClient.ts`. No new top-level projects, no ORM, no new state/data-fetching library, no new UI primitives.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. The table records deliberate, Developer-directed scope fences instead:

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|--------------------------------------|
| No automated tests | Developer instructed "Keep it concise and simple — no tests"; 008 precedent (Constitution Principle I) | Adding pytest/Playwright contradicts the explicit instruction and expands scope beyond the request |
| No DB foreign key from `employees.company_id` | The admin's company delete is a hard `DELETE`; a restrictive FK would make it start failing (008 FR-013) | An FK with `ON DELETE CASCADE` would silently destroy employees' access requests when a company is removed; the route already validates the company exists at submit time |
| Dedicated `/api/companies/{id}/logo` instead of reusing the admin endpoint | The admin logo endpoint is pinned behind the admin token by the middleware; employees hold no admin token | Making the admin logo path public would expose company data; widening the admin branch would expose the whole admin surface |
| Inert Company Request / Individual Plans buttons | Spec fences them to later specifications (FR-005, FR-018) | Wiring them now builds unrequested flows and would be rework |
| No gating of `/upload-ai` and `/upload` yet | Spec defers application gating to the later company specification | Gating now would lock users out before the company-side grant flow exists |
