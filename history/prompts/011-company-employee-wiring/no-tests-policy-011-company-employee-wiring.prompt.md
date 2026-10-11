---
id: no-tests-policy-011-company-employee-wiring
title: no-tests-policy-in-spec
stage: spec
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.specify (follow-up edit)
labels: [spec, testing-policy, no-tests, constraint]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-company-employee-wiring/spec.md
  - history/prompts/011-company-employee-wiring/no-tests-policy-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

also specify this in specification to write no tests

## Response snapshot

Made the no-tests rule explicit in `spec.md`:
- Added a `**Testing Policy**` block right after the feature `**Input**` line, at the top of the document: "**No tests are to be written for this feature.** No test files, test suites, test cases, or test tasks MUST be added on either the backend or the frontend — this is the Developer's standing instruction. Verification is entirely the manual pass documented in quickstart.md."
- Strengthened the existing Assumptions bullet to the same effect (now names test files, suites, cases, and test tasks explicitly).

The plan (Constitution Check), tasks.md header, and quickstart already state no tests are written; the spec now carries it explicitly too.

## Outcome

- ✅ Impact: The no-tests requirement is now stated prominently in the specification, not only implied by the Assumptions and downstream docs.
- 🧪 Tests: None (documentation edit; the project's standing instruction is no tests).
- 📁 Files: specs/011-company-employee-wiring/spec.md
- 🔁 Next prompts: /sp.implement
- 🧠 Reflection: The rule previously lived only in Assumptions and the constitution; promoting it to a visible policy block near the top removes any chance an implementer infers tests are expected from the FR/SC structure.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): PASS — spec states the no-tests policy explicitly; no [NEEDS CLARIFICATION] markers introduced; structure intact.
- Prompt variant (if applicable): spec-edit-v1
- Next experiment (smallest change to try): Surface the testing policy as a row in the requirements checklist so it is validated like other mandatory constraints.
