---
id: tasks-011-company-employee-wiring
title: company-employee-wiring-tasks
stage: tasks
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.tasks
labels: [tasks, company-dashboard, employee-access, membership-gate, sign-convention, resend, admin-dashboard, mvp]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-company-employee-wiring/tasks.md
  - history/prompts/011-company-employee-wiring/tasks-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

/sp.tasks

(No additional input was provided. Tasks were generated from the design documents in specs/011-company-employee-wiring/.)

## Response snapshot

Ran `check-prerequisites.ps1 -Json` (FEATURE_DIR = specs/011-company-employee-wiring; AVAILABLE_DOCS = research.md, data-model.md, contracts/, quickstart.md) and generated `specs/011-company-employee-wiring/tasks.md`.

Structure: 53 tasks in the strict `- [ ] T### [P?] [Story?] description + file path` format, organized by user story in priority order, with NO test tasks (project has a standing no-tests instruction):

- Phase 1 Setup (T001–T004): add `resend`; add the three Resend env vars; additive migrations (`company_requests` table, `employees.is_manager`, two indexes); a `db_service.transaction()` helper.
- Phase 2 Foundational (T005–T010): shared backend models, frontend types, and API clients matching the contracts.
- Phase 3 US1 (T011–T016, P1, MVP): company employee list/grant/delete service + company-JWT routes; company logo fix; real-data employees table with ID-then-name search; dashboard wiring.
- Phase 4 US2 (T017–T026, P1): one-active-request rule; `409 active_request_exists`; membership service + `/api/me/membership`; the NextAuth membership gate with its allow-list; frontend `requireMembership`, `/upload-ai` guard, `/subscription` redirect, the membership-aware nav (Leave company), and the dialog's active-request message.
- Phase 5 US3 (T027–T033, P2): notification service (Resend, fail-soft), company-request service + `POST /api/company-requests`, admin list, real Company Requests table, onboarding-flow submission, placeholder removal.
- Phase 6 US6 (T034–T038, P2): flip the backend Bank/Vendor sign assignment; update `categorizationUtils`, `ReconciliationResults`, `ReconciliationTotals`/`CategorizedResults`; verify history/export.
- Phase 7 US4 (T039–T041, P3): admin `employee_count` + roster endpoint + hover modal.
- Phase 8 US5 (T042–T044, P3): Manager toggle endpoint/ui + conditional "Company Dashboard" nav entry.
- Phase 9 US7 (T045–T048, P3): app-wide animation polish honoring reduced motion.
- Phase 10 Polish (T049–T053): remove residual dummy data; constitution header/footer/marker audit; env docs; allow-list lock-out check; full quickstart pass.

Also included: dependency graph, parallel opportunities (Setup, Foundational, US2 T019∥T022, US3 T027∥T028, US6 T034∥T035, US7 T045–T047), a parallel example, and an MVP-first incremental delivery strategy. Validation: 53/53 task lines carry a checkbox, sequential ID, and file references; story phases carry [US#] labels; risk call-outs for the membership allow-list (T021/T052) and the sign-flip blast radius (T034–T038).

## Outcome

- ✅ Impact: Actionable, dependency-ordered task list for 011-company-employee-wiring — MVP is US1 (real, searchable employee request management); the security milestone is US2 (membership gate). Ready for /sp.analyze or /sp.implement.
- 🧪 Tests: None generated (standing no-tests instruction); each story's Independent Test maps to a quickstart.md section.
- 📁 Files: specs/011-company-employee-wiring/tasks.md
- 🔁 Next prompts: /sp.analyze (consistency) or /sp.implement for 011-company-employee-wiring
- 🧠 Reflection: The story-per-phase structure fit this feature well because the three concerns (dashboard wiring, the access gate, and the sign flip) touch largely disjoint files, so US1/US2/US6 are genuinely parallelizable. The main sequencing constraint is that the membership gate must land with its allow-list atomically or the feature's own endpoints lock out — called out as T021 with an explicit verification task (T052).

## Evaluation notes (flywheel)

- Failure modes observed: None blocking. A grep-format check needed a second pass to confirm every task line carries a file reference; T050 was tightened to name explicit files.
- Graders run and results (PASS/FAIL): PASS — all tasks use the required checklist format (checkbox + T### + optional [P] + [Story] + description with path), tasks are grouped by user story, no test tasks (correct per instructions), dependencies and parallel opportunities documented.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): Keep a short "risk register" table near the top of tasks.md (risk → task id → mitigation) so the two flagged risks are visible without reading the notes.
