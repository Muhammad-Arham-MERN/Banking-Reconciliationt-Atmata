---
id: phr-20260711-004
title: cloud-file-migration-tasks
stage: tasks
date: 2026-07-11
surface: cli
model: gpt-4
feature: cloud-file-migration
branch: 001-cloud-file-migration
user: H.A.R
command: /sp.tasks
labels: [tasks, cloud-migration]
links:
  spec: specs/001-cloud-file-migration/spec.md
  ticket: ""
  adr: ""
  pr: ""
files:
  - specs/001-cloud-file-migration/tasks.md
tests: []
---

## Prompt

/sp.tasks

Generate testable, dependency-ordered tasks for the cloud file migration feature based on spec.md, plan.md, research.md, data-model.md, and contracts/cloud-history-api.md.

## Response snapshot

Generated tasks.md with 14 tasks across 5 phases:

- Phase 1 (Foundational): T001-T003 — cloud types, cloud client, JWT exposure
- Phase 2 (US1 - P1): T004-T006 — greeting, cloud history loading, type adaptation
- Phase 3 (US2 - P1): T007-T008 — cloud file saving, data retention on failure
- Phase 4 (US3 - P2): T009-T010 — end-to-end validation (no code changes needed)
- Phase 5 (Polish): T011-T014 — cleanup, deprecation, deployment config

7 tasks are parallelizable. MVP scope = 6 tasks (Phases 1 + 2). Backend requires zero changes — all cloud routes already live.

## Outcome

- ✅ Impact: 14 tasks generated with dependency graph, parallel opportunities, and MVP scope defined
- 🧪 Tests: N/A (tasks phase — tests not requested in spec)
- 📁 Files: 1 created (tasks.md)
- 🔁 Next prompts: /sp.implement to start implementation
- 🧠 Reflection: US3 requires no code — it's automatically satisfied by US1+US2 working together. Only validation tasks. Backend is already complete.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): Standard /sp.tasks
- Next experiment (smallest change to try): N/A
