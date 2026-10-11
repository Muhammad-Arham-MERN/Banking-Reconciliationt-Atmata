---
id: tasks-008-admin-dashboard
title: admin-dashboard-tasks
stage: tasks
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 008-admin-dashboard
branch: 008-admin-dashboard
user: developer
command: /sp.tasks
labels: [tasks, admin, dashboard, fastapi, nextjs, fernet]
links:
  spec: specs/008-admin-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-admin-dashboard/tasks.md
  - history/prompts/008-admin-dashboard/tasks-008-admin-dashboard.prompt.md
tests:
  - null
---

## Prompt

/sp.tasks

## Response snapshot

Ran `check-prerequisites.ps1 -Json` (FEATURE_DIR = specs/008-admin-dashboard; AVAILABLE_DOCS = research.md, data-model.md, contracts/, quickstart.md), loaded `tasks-template.md` plus the plan, spec, data-model, and contracts already produced, and generated `specs/008-admin-dashboard/tasks.md` with 28 tasks in strict checklist format (checkbox + sequential ID + optional [P] + optional [Story] + description with exact file paths).

Phase breakdown: Setup (T001–T003: add `cryptography`, add the six admin/encryption/logo settings to config.py, document/set env keys) → Foundational (T004–T011: companies table + unique index migration; admin_models.py; company_crypto_service.py; company_logo_service.py; admin_auth_service.py; the /api/admin branch in auth_middleware.py; admin_routes.py skeleton + registration in main.py; frontend adminClient.ts) → US1 (T012–T015: POST /api/admin/login, sign-in form, dashboard shell with the sessionStorage token state machine, the hidden AdminDashAccess page) 🎯 MVP → US2 (T016–T020: company_service create/list, GET+POST /api/admin/companies, companies-table.tsx, company-form-dialog.tsx create mode, dashboard wiring) → US3 (T021–T024: company_service update/delete/reveal, PUT/DELETE + password + logo endpoints, dialog edit mode, table row actions incl. two-step delete) → Polish (T025–T028: route-undiscoverability audit, Code Standards 1–3 check, the manual quickstart pass, the no-billing guard).

No test tasks were generated — explicitly recorded as a deliberate omission per the Developer's instruction, with `quickstart.md` as the verification mechanism. Also documented the critical path, per-story dependencies (US1 needs only Foundational; US2 adds the table + crypto + logo services; US3 extends US2's files), parallel opportunities, and a warning listing the five files touched by more than one task (`admin_routes.py`, `company_service.py`, `companies-table.tsx`, `company-form-dialog.tsx`, `admin-dashboard.tsx`) so they stay sequential despite the [P] markers elsewhere.

## Outcome

- ✅ Impact: 28 executable, dependency-ordered tasks covering all three user stories plus polish; ready for /sp.implement.
- 🧪 Tests: None — no test tasks by design (Developer instruction); verification is quickstart.md (T027).
- 📁 Files: specs/008-admin-dashboard/tasks.md
- 🔁 Next prompts: /sp.implement for 008-admin-dashboard (or /sp.analyze for a consistency pass)
- 🧠 Reflection: The Foundational phase deliberately carries the auth framework and schema rather than the login endpoint, which keeps US1 genuinely independent (the shell renders an empty state without the companies table) while still front-loading everything multiple stories share. Flagging the shared-file list explicitly matters here — naive parallelization of T023/T024 or T017/T022 would cause same-file collisions.

## Evaluation notes (flywheel)

- Failure modes observed: None; `check-prerequisites.ps1 -Json` returned clean JSON (with the usual CLIXML progress noise on Windows PowerShell 5.1).
- Graders run and results (PASS/FAIL): Format validation PASS — all 28 lines match `- [ ] T0NN [P?] [US?] description + file path`; story labels appear only in Phases 3–5; setup/foundational/polish correctly carry no story label.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): Confirm the Next.js exact-case `AdminDashAccess` segment (flagged in the plan as research R12) before T015 locks in the folder name.
