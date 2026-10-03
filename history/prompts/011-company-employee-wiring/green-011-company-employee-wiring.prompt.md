---
id: green-011-company-employee-wiring
title: company-employee-wiring-implementation
stage: green
date: 2026-10-03
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.implement
labels: [green, implementation, company-dashboard, employee-access, membership-gate, sign-convention, resend, cascade-delete, manager-role]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/requirements.txt
  - backend/pyproject.toml
  - backend/src/config.py
  - backend/.env.example
  - backend/src/models/db_migrations.py
  - backend/src/services/db_service.py
  - backend/src/models/employee_models.py
  - backend/src/models/admin_models.py
  - backend/src/models/company_request_models.py
  - backend/src/services/employee_service.py
  - backend/src/services/company_service.py
  - backend/src/services/membership_service.py
  - backend/src/services/company_request_service.py
  - backend/src/services/notification_service.py
  - backend/src/api/company_employee_routes.py
  - backend/src/api/company_requests_routes.py
  - backend/src/api/me_routes.py
  - backend/src/api/admin_routes.py
  - backend/src/api/employee_routes.py
  - backend/src/api/auth_middleware.py
  - backend/src/api/ai_routes.py
  - backend/src/main.py
  - backend/src/utils/data_transformers.py
  - backend/src/services/pdf_processor.py
  - backend/src/services/ai_pdf_processor.py
  - backend/src/services/past_files_excel_service.py
  - frontend/src/types/employee.types.ts
  - frontend/src/types/admin.types.ts
  - frontend/src/types/company.types.ts
  - frontend/src/types/categorization.types.ts
  - frontend/src/types/companyRequest.types.ts
  - frontend/src/lib/api/companyClient.ts
  - frontend/src/lib/api/adminClient.ts
  - frontend/src/lib/api/employeeClient.ts
  - frontend/src/lib/api/companyRequestClient.ts
  - frontend/src/lib/membership.ts
  - frontend/src/lib/utils/categorizationUtils.ts
  - frontend/src/components/navigation/navigation.tsx
  - frontend/src/components/company-dashboard/employees-table.tsx
  - frontend/src/components/admin/company-requests-table.tsx
  - frontend/src/components/admin/companies-table.tsx
  - frontend/src/components/results/ReconciliationResults.tsx
  - frontend/src/components/results/ReconciliationTotals.tsx
  - frontend/src/components/results/CategorizedResults.tsx
  - frontend/src/app/layout.tsx
  - frontend/src/app/upload-ai/page.tsx
  - frontend/src/app/subscription/page.tsx
  - specs/011-company-employee-wiring/tasks.md
tests:
  - null
---

## Prompt

/sp.implement start implementation of 011-company-employee-wiring

(Executed the /sp.implement workflow: prerequisites check, checklist gate, load tasks.md/plan.md/research.md/data-model.md/contracts/quickstart.md, then implemented every task phase-by-phase.)

## Response snapshot

Implemented all 54 tasks of `specs/011-company-employee-wiring/tasks.md` (T001–T053; T054 is the manual quickstart pass and was left unchecked). Checklist `checklists/requirements.md` was 16/16 complete (PASS), so implementation proceeded without a stop.

- **Phase 1 (Setup)** — added `resend` to requirements/pyproject; added the three Resend env vars to `config.py` and `.env.example`; appended the `company_requests` table + index, `employees.is_manager`, and the two employee indexes to `MIGRATIONS`; added an async `transaction()` context manager to `db_service`.
- **Phase 2 (Foundational)** — extended the pydantic models (`CompanyEmployee`, `EmployeeListResponse`, `EmployeeManagerUpdate`, `Membership`, `MembershipResponse`, `DeleteResponse`; new `company_request_models`; `Company.employee_count` + `AdminEmployee`), the frontend types, and the API clients (company/admin/employee + new `companyRequestClient`).
- **Phase 3 (US1)** — company employee service (list/grant/delete/manager) + company-JWT routes + the missing `/api/company/{id}/logo`; real, searchable employees table with grant/delete and ID-then-name precedence.
- **Phase 4 (US2)** — one-active-request rule (`ActiveRequestExistsError` → 409), `membership_service`, `me_routes` (GET/DELETE `/api/me/membership`), the authoritative NextAuth-branch membership gate with an exact allow-list, `lib/membership` server guard, `/upload-ai` guard, `/subscription` member redirect, membership-aware `Navigation` header with Confirm-leave, and the dialog's cancel-active-request flow.
- **Phase 5 (US3)** — `company_request_service`, best-effort `notification_service` (Resend, fail-soft), `POST /api/company-requests`, admin `GET /api/admin/company-requests`, real company-requests table, and the onboarding flow now POSTs its answers; deleted the placeholder data file.
- **Phase 6 (US6)** — finalized the sign convention end-to-end: threaded `reconciliation_type` into the PDF statement extractors and flipped the BANK polarity (`flip_sign`), inverted the past-file wire sign map, and updated the frontend categorization/labels/manual-add/totals so the displayed signs and the verdict stay consistent.
- **Phase 7 (US4)** — `employee_count` via LEFT JOIN, admin roster endpoint, transactional cascade delete of a company's employee records, and the hover-roster UI.
- **Phase 8 (US5)** — manager PATCH endpoint/service, manager toggle + badge, and the conditional Company Dashboard nav entry (landed with Phases 3–4).
- **Phase 9 (US7)** — reduced-motion support + smoother transitions on the onboarding overlay, star field, and both sidebars.
- **Phase 10** — removed all placeholder data, audited headers/footers, updated env docs, and confirmed the allow-list.

Also fixed a real routing bug found during implementation: `path.startswith("/api/company")` also matched `/api/company-requests`, so that NextAuth endpoint would have been routed to the company-JWT branch; replaced with `_is_company_path()`.

## Outcome

- ✅ Impact: The company-employee dashboard is wired to real data; a granted membership is a real backend-enforced gate; onboarding requests persist and notify; the admin gains employee counts/rosters and a company-delete cascade; and the finalized credit/debit sign convention is canonical from extraction to storage to every surface.
- 🧪 Tests: None written (standing no-tests policy). Verified with `python -m compileall backend/src` (OK), a runtime sanity check of the sign functions, `tsc --noEmit` (0 errors), and `eslint` on every changed file (clean; pre-existing repo lint errors in untouched files remain).
- 📁 Files: 7 new backend files, 1 new frontend feature module, 3 new frontend lib modules, plus edits across backend models/services/routes/middleware and frontend types/clients/components; `company-placeholder.ts` deleted.
- 🔁 Next prompts: Run the `/sp.implement` T054 manual `quickstart.md` pass against a live CockroachDB + Resend key; then commit the feature.
- 🧠 Reflection: `merge_debit_credit` was the cleanest single flip point, but the deeper finding is that `reconciliation_type` never reached extraction — bank and vendor statements were producing identical signs — so the vendor target required no change while the bank target required threading the type through. The verdict identity in `CategorizedResults` becomes correct under the new canonical signs (the old polarity was internally inconsistent for bank-only items).

## Evaluation notes (flywheel)

- Failure modes observed: (1) a prefix-collision bug where `/api/company-requests` matched the company branch; (2) the new `react-hooks/set-state-in-effect` ESLint rule flagged the tables that called a setState-ing `load()` from a mount effect — refactored to the existing fetch-in-callbacks pattern; (3) `npx tsc` tried to install a bogus `tsc` package — used the local compiler binary instead.
- Graders run and results (PASS/FAIL): PASS — backend compileall clean, TS typecheck 0 errors, changed-file lint clean, tasks.md T001–T053 marked `[X]`.
- Prompt variant (if applicable): implement-v1
- Next experiment (smallest change to try): When a feature flips a wire convention, have `/sp.tasks` require a paired "flip + verify" test in the same commit; here the sign work is deliberately split across T034–T038 to avoid a half-flipped UI.
