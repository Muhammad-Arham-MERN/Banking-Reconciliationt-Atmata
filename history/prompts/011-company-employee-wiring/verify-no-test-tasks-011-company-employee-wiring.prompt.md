---
id: verify-no-test-tasks-011-company-employee-wiring
title: verify-no-test-tasks
stage: misc
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.tasks (follow-up verification)
labels: [verification, tasks, no-tests, read-only]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/011-company-employee-wiring/verify-no-test-tasks-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

make sure there are no tasks related to writing tests

## Response snapshot

Verified `tasks.md` read-only. Grepped all 54 task lines (`^- \[ \] T\d{3}`) for test/pytest/vitest/jest/assert/TDD — "No matches found". The only occurrences of "test" in the file are non-tasks: the `**Tests**: None` header, the per-story `**Independent Test**` descriptions (manual verification steps), and the Notes line. Confirmed there are no tasks that write test files, suites, or cases.

No files modified (verification only).

## Outcome

- ✅ Impact: Confirmed the task list contains zero test-writing tasks, consistent with the spec's Testing Policy.
- 🧪 Tests: N/A (verification request).
- 📁 Files: none modified.
- 🔁 Next prompts: /sp.implement
- 🧠 Reflection: The template's per-story "Independent Test" heading can look like a test task at a glance; the distinguishing factor is that these are prose manual-verification descriptions, not checklist tasks with IDs.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): PASS — 0/54 task lines reference tests.
- Prompt variant (if applicable): verify-v1
- Next experiment (smallest change to try): none.
