---
id: tasks-009-employee-access-request
title: employee-access-request-tasks
stage: tasks
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 009-employee-access-request
branch: 009-employee-access-request
user: developer
command: /sp.tasks
labels: [tasks, subscription, employees, access-request, adam-id, nextauth, migration]
links:
  spec: specs/009-employee-access-request/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-employee-access-request/tasks.md
  - history/prompts/009-employee-access-request/tasks-009-employee-access-request.prompt.md
tests:
  - null
---

## Prompt

/sp.tasks

## Response snapshot

Ran check-prerequisites.ps1 -Json, which reported FEATURE_DIR and AVAILABLE_DOCS = [research.md, data-model.md, contracts/, quickstart.md]. Loaded the spec's three user stories (US1 sign-in/landing P1, US2 submit an employee access request P1, US3 see the other plan options P2), the plan, data-model, contract, research decisions, and quickstart, plus the tasks template.

Generated specs/009-employee-access-request/tasks.md with 22 tasks across six phases, all in the strict `- [ ] T0NN [P?] [USn] description + file path` format. Tests are absent by explicit instruction (spec: "no tests"; 008 precedent), so every phase ends with a **Checkpoint** line instead of test tasks, and Polish carries the manual quickstart verification.

Phase 1 Setup (T001–T002): confirm zero dependency/environment changes; create the `components/subscription/` folder. Phase 2 Foundational (T003–T007): the employees DDL + composite unique index in db_migrations.py, employee_models.py, employee_service.py (normalize/validate/crux-marked insert), employee.types.ts, employeeClient.ts — explicitly scoped as gating US2 only, with the note that US1 is frontend-only and does not depend on it. Phase 3 US1 (T008–T013): the dedicated `/login` route, `/` rewritten as a pure redirect, `pages.signIn` repointed, the `CloseTabWarning` mount removed + component deleted (the sole cause of the "Leave site?" prompt), subscription-plans.tsx, and the guarded `/subscription` page. Phase 4 US2 (T014–T018): company_routes.py (`GET /api/companies`, `GET /api/companies/{id}/logo`), employee_routes.py (`POST /api/employees/requests` with 400/404/409 mapping), router registration in main.py, the shadcn request dialog, and wiring it into the page. Phase 5 US3 (T019): the Company Request button + Individual Plans panel. Phase 6 Polish (T020–T022): Code Standards 1–3 audit, the full quickstart.md pass, non-goal confirmation.

Also included: a task-level dependency graph, per-phase parallel opportunities and parallel examples, explicit file-conflict warnings (subscription-plans.tsx is touched by T012 → T018 → T019 and must be sequential), the MVP-first strategy (US1 alone, deliberately bypassing the backend foundation), and the flagged open item that the spec's Q1–Q5 answers were the recommended defaults — Q1 is the only one that would change a task (T003's index and T015's 409 mapping).

## Outcome

- ✅ Impact: Feature 009 is broken into 22 immediately-executable tasks with exact file paths, ordered so each of the three user stories can be completed and hand-verified on its own. MVP (US1) is deliverable without any backend work.
- 🧪 Tests: None generated — deliberate, per the explicit "no tests" instruction; each phase ends with a Checkpoint tied to the corresponding quickstart.md scenario instead.
- 📁 Files: specs/009-employee-access-request/tasks.md
- 🔁 Next prompts: /sp.analyze (consistency check) or /sp.implement (start with Phase 1)
- 🧠 Reflection: The awkward part of this decomposition is that US1 and US3 both touch the same subscription page, and the spec's US1 acceptance scenario 2 lists menu items that US3 owns. Resolved by giving US1 the page shell, title, and Employee Request action and letting US3 add the Company Request button and the plans panel, with the overlap called out explicitly rather than hidden — the alternative (duplicating the page work) would have created same-file conflicts. US2's backend tasks were kept in Foundational rather than inside US2 so the data layer is one reviewable unit.

## Evaluation notes (flywheel)

- Failure modes observed: none blocking. check-prerequisites.ps1 -Json returned cleanly (unlike the create-new-feature defect recorded in the 008 PHR); the create-phr bash script is still absent on this Windows checkout, so the agent-native PHR fallback was used for the third time.
- Graders run and results (PASS/FAIL): Format validation PASS — all 22 tasks carry a checkbox, a sequential T0NN id, a story label exactly where required (US1/US2/US3 phases) and nowhere else, and a concrete path; no test tasks present; no placeholder text left from the template.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): ask the Developer to confirm the Q1–Q5 clarification defaults *before* generating tasks, so the flagged open item in the Notes section never has to be carried into implementation.
