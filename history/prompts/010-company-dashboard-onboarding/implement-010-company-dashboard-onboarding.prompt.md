---
id: implement-010-company-dashboard-onboarding
title: company-dashboard-onboarding-implementation
stage: green
date: 2026-10-01
surface: cli
model: claude-sonnet-4-5
feature: 010-company-dashboard-onboarding
branch: 010-company-dashboard-onboarding
user: developer
command: /sp.implement
labels: [implement, company-dashboard, onboarding, cinematic, company-auth, aceternity, sidebar]
links:
  spec: specs/010-company-dashboard-onboarding/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/010-company-dashboard-onboarding/tasks.md
  - backend/src/config.py
  - backend/.env.example
  - backend/src/models/company_auth_models.py
  - backend/src/services/company_auth_service.py
  - backend/src/api/company_auth_routes.py
  - backend/src/services/company_service.py
  - backend/src/api/auth_middleware.py
  - backend/src/main.py
  - frontend/src/components/ui/sidebar.tsx
  - frontend/src/types/company.types.ts
  - frontend/src/lib/company/company-placeholder.ts
  - frontend/src/lib/company/company-session.ts
  - frontend/src/lib/company/company-validation.ts
  - frontend/src/lib/api/companyClient.ts
  - frontend/src/components/company-request/boss-loader.module.css
  - frontend/src/components/company-request/boss-loader.tsx
  - frontend/src/components/company-request/company-building.tsx
  - frontend/src/components/company-request/star-field.tsx
  - frontend/src/components/company-request/cinematic-intro.tsx
  - frontend/src/components/company-request/onboarding-questions.tsx
  - frontend/src/components/company-request/request-success.tsx
  - frontend/src/components/company-request/company-request-flow.tsx
  - frontend/src/components/subscription/subscription-plans.tsx
  - frontend/src/components/company-dashboard/company-sign-in-form.tsx
  - frontend/src/components/company-dashboard/company-dashboard.tsx
  - frontend/src/components/company-dashboard/company-sidebar.tsx
  - frontend/src/components/company-dashboard/employees-table.tsx
  - frontend/src/components/company-dashboard/subscription-panel.tsx
  - frontend/src/app/CompanyDashboard/page.tsx
  - frontend/src/components/admin/company-requests-table.tsx
  - frontend/src/components/admin/admin-dashboard.tsx
  - frontend/boss-loader.html
  - history/prompts/010-company-dashboard-onboarding/implement-010-company-dashboard-onboarding.prompt.md
tests:
  - null
---

## Prompt

/sp.implement

(No additional input was provided. Note: research R1 — issuing a signed 24-hour company JWT — was left flagged but unconfirmed; the implementation proceeded with the recommended signed-token design, which is reversible.)

## Response snapshot

Executed the full task list for feature 010-company-dashboard-onboarding, 34 of 35 tasks (T035, the live browser walkthrough, needs a running CockroachDB + browser and is left for the Developer).

Phase 1 (T001–T003): confirmed no dependency changes; added `COMPANY_JWT_SECRET`/`COMPANY_JWT_TTL_HOURS` to `config.py` and `.env.example`.
Phase 2 (T004–T007): added the Aceternity sidebar (`components/ui/sidebar.tsx`, vendored + Bismillah bookends), `types/company.types.ts`, `lib/company/company-placeholder.ts`, and the localStorage 24-hour `company-session.ts`.
US1 (T008–T016): the cinematic onboarding — `company-validation.ts`, the ported `boss-loader.tsx` + `.module.css` (reference HTML deleted), `company-building.tsx`, `star-field.tsx`, `cinematic-intro.tsx`, `onboarding-questions.tsx`, `request-success.tsx`, `company-request-flow.tsx`, and wiring the "Company Request" button in `subscription-plans.tsx`.
US2 (T017–T026): the backend company sign-in — `company_auth_models.py`, `get_company_by_name()` in `company_service.py`, `company_auth_service.py` (Fernet decrypt + constant-time compare + 24h JWT), `company_auth_routes.py` (`POST /api/company/login`), the company branch in `auth_middleware.py`, router registration in `main.py`; frontend `companyClient.ts`, `company-sign-in-form.tsx`, `company-dashboard.tsx`, and the `/CompanyDashboard` route.
US3 (T027–T030): `company-sidebar.tsx`, `employees-table.tsx`, `subscription-panel.tsx`, integrated in the shell.
US4 (T031–T032): `company-requests-table.tsx` and the sidebar category nav (Companies / Company Requests) in `admin-dashboard.tsx`.
Polish (T033–T034): code-standards and non-goal checks.

Two lint/type issues were fixed during validation: the vendored `SidebarLink` type was widened to accept anchor props (`onClick`), and the flow's reset-on-open moved from an effect to a render-time seed to satisfy `react-hooks/set-state-in-effect`.

## Outcome

- ✅ Impact: The Company Dashboard and onboarding feature is implemented end to end — the cinematic Company Request flow, the company sign-in (the only new API), the two-section company dashboard, and the admin Company Requests category. 34/35 tasks complete; T035 (live walkthrough) pending the running stack.
- 🧪 Tests: None (per the standing "no tests" instruction). Validation instead: `tsc --noEmit` PASS, `eslint` on all touched files PASS (0 errors), `next build` PASS (`/CompanyDashboard` dynamic, all routes compile), backend `py_compile` + real import of `main` and the company modules PASS, OpenAPI check confirming `/api/company/login` registered with the login path public.
- 📁 Files: 33 touched/created (see frontmatter); `frontend/boss-loader.html` deleted.
- 🔁 Next prompts: Resolve the R1 open item if a client-only session is preferred; otherwise run the live quickstart walkthrough (T035).
- 🧠 Reflection: Front-loading reuse paid off — the sidebar needed no new dependency, the success message reused the existing typewriter, and the sign-in leaned on 008's Fernet + JWT idioms. The only genuinely new backend surface is one endpoint plus a middleware branch. The riskiest piece is the boss-loader port (art fidelity and the tap/lift/smile mode split), which is verified to compile and lint but not yet watched live.

## Evaluation notes (flywheel)

- Failure modes observed: (1) the vendored Aceternity `SidebarLink` prop type did not allow `onClick`, so `tsc` failed until the type was widened with `Omit<React.ComponentProps<"a">, "href" | "className">`; (2) `react-hooks/set-state-in-effect` flagged the flow's reset-on-open effect, fixed with the repo's render-time seed pattern; (3) FastAPI's `app.routes` here exposes `_IncludedRouter` objects without `.path`, so route verification had to go through `app.openapi()['paths']` instead.
- Graders run and results (PASS/FAIL): PASS — build, typecheck, and lint all green; backend imports and the new route verified.
- Prompt variant (if applicable): implement-v1
- Next experiment (smallest change to try): Confirm R1 (signed JWT vs client-only session) before the live walkthrough, so no rework is needed if the simpler option is preferred.
