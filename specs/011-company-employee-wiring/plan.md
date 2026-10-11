# Implementation Plan: Company-Employee Dashboard Wiring, Finalized Sign Conventions & Edge Cases

**Branch**: `011-company-employee-wiring` | **Date**: 2026-10-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-company-employee-wiring/spec.md`

## Summary

Wire the company-employee dashboard to real data and make company-granted access a real authorization gate, finalize the credit/debit sign convention end-to-end, and cover the listed edge cases. Concretely: employee requests become actionable rows in the Company Dashboard (search by ID then name, grant, delete, assign Manager); a grant unlocks the application (today `/upload-ai` is open to any signed-in user); the Company Dashboard's sign-in is the only surface reachable without a grant, alongside the subscription and sign-in pages; "Company Request" onboarding submissions become persisted rows in the Admin Dashboard plus a Resend notification; the Admin companies table gains a hover-able employee count/modal; and the Bank/Vendor sign convention is made canonical from the backend reconciliation engine through the database to every frontend surface. No new frameworks — only the developer-requested `resend` package on the backend.

## Technical Context

**Language/Version**: Python `>=3.13` (backend, FastAPI); TypeScript `^5` on Next.js `16.2.9` / React `19.2.4` App Router (frontend)
**Primary Dependencies**: Backend — FastAPI, `asyncpg` (raw SQL, no ORM), pydantic v2 + pydantic-settings, PyJWT, `cryptography` (Fernet), all existing; **NEW: `resend`** (email SDK, developer-requested). Frontend — Next.js App Router (RSC), NextAuth v5 (Google; JWT session exposing `session.user.access_token`), shadcn `base-nova` on Base UI, Tailwind v4, `motion`, `lucide-react`, `@tabler/icons-react` (all existing; **no additions**).
**Storage**: CockroachDB via raw `asyncpg` (`db_service`, `$n` placeholders). **NEW table** `company_requests`; **ALTER** `employees` (add `is_manager`, add `account_user_id` index, optional FK to `users`). Company logos stay on the filesystem in `COMPANY_LOGO_DIR` (untouched).
**Testing**: None — per the Developer's standing "no tests" instruction. Verification is a manual pass (quickstart.md).
**Target Platform**: Local dev — `uvicorn` backend + Next.js frontend against CockroachDB (no deployment required).
**Project Type**: Web application (`backend/` + `frontend/`).
**Performance Goals**: Company employee list + the automatic ID/name search stay responsive (sub-second) for a company with up to a few hundred employees; the membership gate adds at most one indexed lookup per gated request.
**Constraints**: No ORM (raw asyncpg only); every new/edited file carries the constitution's بسم الله header + the وَإِنَّ اللَّهَ footer, and crux methods carry the وَهُوَ marker; no automated tests; Resend key and sender/recipient delivered via env; the app gate must not break the request-submission, company-dropdown, or membership endpoints it relies on.
**Scale/Scope**: Small single-developer tool. Order of tens of companies; up to a few hundred employees per company; a handful of onboarding requests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate I — Strict Instruction Following**: The plan implements the spec (FR-001…FR-025) with no scope beyond it. PASS.
- **Gate II — Developer Stack Authority**: The only added dependency is `resend`, which the Developer explicitly requested in the spec ("Resend should be established…"). No other framework/library is introduced; existing patterns (raw asyncpg, the three auth branches, the existing API clients) are reused. PASS.
- **Gate III — Supervised Collaboration / V — Controlled Creativity**: New authorizations (membership gate, Manager role, cascade delete) are direct implementations of clarified requirements, not novel inventions. PASS.
- **Gate VI — Ambiguity Resolution**: All eight clarification points were resolved in `/sp.specify` and `/sp.clarify`; no `[NEEDS CLARIFICATION]` remain. PASS.
- **Code Standards 1–3**: File header/footer + logical-crux markers are mandatory for every new and edited backend/frontend file. Enforced as a cross-cutting task in `/sp.tasks`. PASS (must remain enforced).
- **No-tests policy**: Honored; the plan adds no test suites. PASS.

No violations → Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/011-company-employee-wiring/
├── plan.md              # This file
├── research.md          # Phase 0 output — design decisions + rationale
├── data-model.md        # Phase 1 output — entities, transitions, constraints
├── quickstart.md        # Phase 1 output — manual verification run-through
├── contracts/           # Phase 1 output — OpenAPI per auth branch + sign convention
│   ├── company-api.yaml           # company-JWT branch (company dashboard)
│   ├── membership-api.yaml        # NextAuth branch (gate, leave, requests, onboarding)
│   ├── admin-api.yaml             # admin-JWT additions (company requests, employee counts)
│   └── sign-convention.md         # canonical credit/debit sign table + enforcement points
└── tasks.md             # Phase 2 output (/sp.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/src/
├── api/
│   ├── auth_middleware.py          # EDIT: add membership gate to the NextAuth branch
│   ├── company_employee_routes.py  # NEW: /api/company/employees* (company JWT branch)
│   ├── company_auth_routes.py      # EDIT: fix dangling logo_url; add company logo route
│   ├── company_requests_routes.py  # NEW: POST /api/company-requests (NextAuth branch)
│   ├── me_routes.py                # NEW: GET/DELETE /api/me/membership (NextAuth branch)
│   └── admin_routes.py             # EDIT: company requests list + employee count/roster
├── models/
│   ├── db_migrations.py            # EDIT: company_requests table; employees.is_manager + indexes
│   ├── company_request_models.py   # NEW: request/response models for onboarding requests
│   ├── employee_models.py          # EDIT: membership + employee-management models
│   └── admin_models.py             # EDIT: company employee_count + roster models
├── services/
│   ├── company_request_service.py  # NEW: persist + list onboarding requests
│   ├── membership_service.py       # NEW: resolve/create/count/grant/delete membership
│   ├── notification_service.py     # NEW: Resend email send (fail-soft)
│   ├── employee_service.py         # EDIT: one-active-request rule; grant/delete/manager
│   └── company_service.py          # EDIT: cascade employee delete; employee_count join
└── utils/
    └── (existing)

frontend/src/
├── app/
│   ├── layout.tsx                  # EDIT: membership-aware nav (Leave company / Company Dashboard)
│   ├── upload-ai/page.tsx          # EDIT: require membership server-side
│   ├── subscription/page.tsx       # EDIT: redirect members away (must leave first)
│   └── CompanyDashboard/page.tsx   # (existing; dashboard reads real data)
├── components/
│   ├── company-dashboard/          # EDIT: employees table (real data, search, grant/delete/manager)
│   ├── admin/                      # EDIT: company-requests table (real), companies table (count+modal)
│   ├── company-request/            # EDIT: submit the onboarding flow to the API
│   ├── subscription/               # EDIT: employee-request dialog (one-active-request message)
│   └── navigation/                 # NEW: membership-aware header nav
├── lib/
│   ├── api/                        # EDIT/NEW: employeeClient, companyClient, adminClient, companyRequestClient
│   ├── membership.ts               # NEW: getMembership/requireMembership server helpers
│   └── utils/categorizationUtils.ts# EDIT: finalized sign mapping (see research D6)
└── types/                          # EDIT/NEW: employee, company, admin, companyRequest types
```

**Structure Decision**: Existing web layout (`backend/` FastAPI + `frontend/` Next.js App Router). No new top-level projects. Backend work stays inside the existing module folders and reuses the three auth branches already defined in `auth_middleware.py`; frontend work extends existing components/clients rather than introducing new patterns.

## Complexity Tracking

> No constitution violations. Nothing to justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Design Highlights (detail in research.md)

- **Membership is the gate (FR-009/FR-010/FR-025)**: a granted `employees` row is the authorization; the NextAuth branch of `auth_middleware` gains a membership check with an allow-list (subscription/auth, `/api/company-requests`, `/api/companies`, `/api/me/*`, `/api/employees/requests`), so every other application route is refused without an accepted membership. Frontend RSC pages additionally guard for UX.
- **Company dashboard endpoints live on the company-JWT branch** (`/api/company/employees*`), matching the existing principal model; the manager nav entry calls the same endpoints from inside the app.
- **Cascade + one-membership (FR-023/FR-025)**: `company_service.delete_company` also deletes that company's employee rows; `employee_service` rejects a second active request for an account, and `DELETE /api/me/membership` (leave) deletes the row.
- **Onboarding requests (FR-006/FR-007)**: new persisted view-only table + admin list; Resend email sent best-effort after the row is stored, never blocking the submission.
- **Sign convention (FR-012…FR-014)**: one canonical mapping enforced in the reconciliation engine, the stored `Debit/Credit` value, and the frontend categorization/display/totals (contracts/sign-convention.md).
- **Manager role (FR-019/FR-020)**: an `is_manager` flag on the employee row; the nav entry renders only for an account that is both a member and a manager; the Company Dashboard address stays undiscoverable otherwise.
