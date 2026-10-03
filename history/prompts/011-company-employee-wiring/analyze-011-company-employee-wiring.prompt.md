---
id: analyze-011-company-employee-wiring
title: company-employee-wiring-analysis
stage: misc
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.analyze
labels: [analyze, consistency, coverage, traceability, requirements, read-only]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - history/prompts/011-company-employee-wiring/analyze-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

/sp.analyze

please analyze and check if any requirements from my original requirement are not missed

## Response snapshot

Ran a read-only cross-artifact analysis of spec.md, plan.md, tasks.md, and the constitution, with the specific goal of tracing the Developer's original /sp.specify brief against the artifacts.

Ran `check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` (FEATURE_DIR resolved; AVAILABLE_DOCS includes tasks.md). Built a 25-FR requirements inventory, mapped each FR to tasks, and ran the duplication/ambiguity/underspecification/constitution/coverage/inconsistency passes.

Findings (10): one HIGH — FR-023 (company-delete cascade) has ZERO task despite research D4 specifying the change to `company_service.delete_company`; two MEDIUM — the pending-request cancel action (FR-017) is only implicit, and the "all dummy data" scope is narrower than the original brief (tests-only `DummyResultsViewer.tsx` / `dummyReconciliationData.ts` untasked); several LOW (FR-021 no task, FR-011 linkage indirect, FR-024 negative req untested, "granted" vs "accepted" terminology, FR-016/FR-025 duplication, hover-only admin count).

Metrics: 25 FRs, 53 tasks, 23/25 FRs with ≥1 task (92% coverage), 2 ambiguities, 1 duplication, 0 critical (no constitution violations). Explicitly answered the Developer's question: the original brief maps cleanly except the cascade-delete task omission, the implicit cancel action, and the dummy-data scope question.

Offered (not applied) remediation edits for the top issues. No files modified except this PHR.

## Outcome

- ✅ Impact: Confirmed the feature artifacts are consistent and constitution-compliant; surfaced one HIGH coverage gap (FR-023 cascade has no task) to fix before /sp.implement, plus one scope decision (dummy data) and a small implicit-cancel gap.
- 🧪 Tests: None (analysis is read-only; project has a standing no-tests instruction).
- 📁 Files: none modified in specs/ (read-only analysis); PHR created.
- 🔁 Next prompts: Approve remediation edits (add cascade task, cancel action, dummy-data decision) then /sp.implement
- 🧠 Reflection: The highest-value check was requirement→task tracing, which caught a task that the plan's research explicitly promised but the task list never created (D4 cascade). This is the class of gap a spec/plan/task read-through misses but a coverage pass finds. The remaining findings are small and do not block the MVP.

## Evaluation notes (flywheel)

- Failure modes observed: None blocking. The tasks.md "risk register" note mentioned the cascade delete indirectly (via the transaction helper T004) but no task actually implemented it — wording that implied coverage without providing it.
- Graders run and results (PASS/FAIL): Analysis PASS — artifacts consistent, no constitution violations, coverage 92%, 1 HIGH finding to remediate.
- Prompt variant (if applicable): analyze-v1
- Next experiment (smallest change to try): Add a requirement→task coverage matrix directly in tasks.md so /sp.analyze (and humans) can spot zero-coverage FRs at a glance.
