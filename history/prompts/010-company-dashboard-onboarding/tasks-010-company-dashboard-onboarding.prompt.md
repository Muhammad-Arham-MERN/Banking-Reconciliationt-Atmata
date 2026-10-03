---
id: tasks-010-company-dashboard-onboarding
title: company-dashboard-onboarding-tasks
stage: tasks
date: 2026-10-01
surface: cli
model: claude-sonnet-4-5
feature: 010-company-dashboard-onboarding
branch: 010-company-dashboard-onboarding
user: developer
command: /sp.tasks
labels: [tasks, company-dashboard, onboarding, cinematic, company-auth, aceternity, sidebar]
links:
  spec: specs/010-company-dashboard-onboarding/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/010-company-dashboard-onboarding/tasks.md
  - history/prompts/010-company-dashboard-onboarding/tasks-010-company-dashboard-onboarding.prompt.md
tests:
  - null
---

## Prompt

/sp.tasks

(No additional input was provided; the task list was generated from specs/010-company-dashboard-onboarding/plan.md, spec.md, research.md, data-model.md, contracts/company-auth-api.yaml, and quickstart.md.)

## Response snapshot

Ran check-prerequisites.ps1 -Json (FEATURE_DIR resolved; AVAILABLE_DOCS: research.md, data-model.md, contracts/, quickstart.md) and loaded the plan, spec, research, data-model, contract, quickstart, and the 009 tasks.md for format reference. Generated `specs/010-company-dashboard-onboarding/tasks.md` with 35 tasks in the required checklist format (`- [ ] Txxx [P?] [USx] description + file path`), organized by user story:

- Phase 1 Setup (T001–T003): confirm no dependency changes; add `COMPANY_JWT_SECRET`/`COMPANY_JWT_TTL_HOURS` to config + .env.example; create the feature folders.
- Phase 2 Foundational (T004–T007): add the Aceternity sidebar (`components/ui/sidebar.tsx`); company types; placeholder data; the `localStorage` 24h session store.
- Phase 3 US1 — cinematic Company Request onboarding (T008–T016): validation helpers, boss-loader port (+ delete `boss-loader.html`), building SVG, star field, cinematic intro, questions, success, the flow orchestrator, and wiring the subscription button. MVP.
- Phase 4 US2 — company sign-in (T017–T026): backend models, `get_company_by_name`, auth service (decrypt + constant-time + JWT), login route, middleware company branch, router registration; frontend client, sign-in form, dashboard shell, `/CompanyDashboard` route.
- Phase 5 US3 — Employees + Subscription sections (T027–T030).
- Phase 6 US4 — admin "Company Requests" category (T031–T032).
- Phase 7 Polish (T033–T035): code-standards check, non-goal/dependency check, full quickstart pass.

Included phase/task dependency graph, suggested order, parallel opportunities and examples, file-conflict warnings, MVP-first and incremental-delivery strategy, and a note flagging the reversible R1 decision (signed company JWT vs client-only flag) with exactly which tasks it would change.

## Outcome

- ✅ Impact: Executable, dependency-ordered task list for feature 010 delivered; ready for /sp.analyze or /sp.implement.
- 🧪 Tests: None run (planning stage; "no tests" is the Developer's standing instruction).
- 📁 Files: specs/010-company-dashboard-onboarding/tasks.md
- 🔁 Next prompts: /sp.analyze (consistency check) or /sp.implement
- 🧠 Reflection: Grouping by user story mapped cleanly onto the two-front feature: US1 is a self-contained frontend story (excellent MVP), while US2 carries the only backend work. The one real coupling is US3's dependency on US2's dashboard shell; keeping the session store and sidebar in Foundational made that the only cross-story edge. Task count stayed modest because the plan front-loads reuse (existing TypewriterEffect, sidebar deps, admin patterns) and placeholder data.

## Evaluation notes (flywheel)

- Failure modes observed: `.specify/scripts/bash/create-phr.sh` does not exist in this repo (only `.specify/scripts/powershell/`), so the agent-native write path was used, per the command's fallback instruction. The bash create-phr remains unavailable on Windows.
- Graders run and results (PASS/FAIL): PASS — 35 tasks, all matching `- [ ] Txxx [P?] [USx] … path`; setup/foundational/polish tasks carry no story label; every user-story phase has a Goal, Independent Test, and Checkpoint; dependency graph and parallel examples present.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): Resolve the flagged R1 decision (signed company JWT vs client-only flag) before /sp.implement so Phase 4 does not build the reversible machinery twice.
