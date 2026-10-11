---
id: remediate-011-company-employee-wiring
title: company-employee-wiring-remediate-c1-c2
stage: misc
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.analyze (follow-up remediation)
labels: [remediation, analyze, tasks, coverage, cascade, cancel-request]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-company-employee-wiring/tasks.md
  - specs/011-company-employee-wiring/contracts/membership-api.yaml
  - specs/011-company-employee-wiring/research.md
  - history/prompts/011-company-employee-wiring/remediate-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

ok do C1 and C2

## Response snapshot

Applied the two approved remediation items from the /sp.analyze findings.

**C1 (HIGH — FR-023 cascade had no task):** Added task **T041 [US4]** in `tasks.md` — "Edit `backend/src/services/company_service.py` `delete_company` to also `DELETE FROM employees WHERE company_id = $1` inside the transaction helper from T004 … (FR-023 — HIGH; must not be deferred)". Renumbered all subsequent tasks (old T041→T042, US5 T042–T044→T043–T045, US7 T045–T048→T046–T049, Polish T049–T053→T050–T054); total is now 54 tasks. Updated the US4 phase title/goal/independent-test, the dependency note (cascade also protects US2's gate), the parallel example (US7 T046∥T047∥T048), the risk note (allow-list check is now T053), and added a cascade note.

**C2 (MEDIUM — pending-request cancel was only implicit):** Made cancel explicit end-to-end:
- `tasks.md` T010: client method named `removeMembership`, described as serving both cancel and leave.
- `tasks.md` T019/T020: `delete_membership` / `DELETE /api/me/membership` documented as serving **both** cancelling a pending request (FR-017) and leaving a granted company (FR-015).
- `tasks.md` T026: the dialog now surfaces the `active_request_exists` message **with a Cancel request action** that calls `removeMembership`; US2 goal/independent-test updated to mention cancel.
- `contracts/membership-api.yaml`: DELETE /api/me/membership summary/description updated to "Cancel a pending request, or leave a granted company".
- `research.md` D11: the DELETE bullet now states it serves both cancel and leave.

Not addressed (still open from the analysis, none blocking): C3 (FR-021 verification folded into T053 — actually done incidentally), C4 (FR-011 linkage verification), C5 (FR-024 negative-req assertion), C6 (the "all dummy data" scope decision — tests-only viewer), C7 ("granted" vs "accepted" wording), C8 (FR-016/FR-025 overlap), C9 (hover-only admin count). C3's verification was folded into the renumbered T053.

## Outcome

- ✅ Impact: The HIGH coverage gap (cascade delete) and the implicit cancel action are resolved; tasks.md is now 54 tasks with consistent IDs/references; contract and research align.
- 🧪 Tests: None (documentation edits; project has a standing no-tests instruction).
- 📁 Files: specs/011-company-employee-wiring/{tasks.md, contracts/membership-api.yaml, research.md}
- 🔁 Next prompts: /sp.implement (or decide C6's dummy-data scope first)
- 🧠 Reflection: Renumbering on insert is the cost of strict sequential task IDs; a full-file rewrite was cleaner and less error-prone than a dozen small edits. Both fixes were documentation-level, so no code risk — but the cascade task (T041) now carries an explicit "must not be deferred" note because it becomes security-relevant once the US2 gate ships.

## Evaluation notes (flywheel)

- Failure modes observed: The write tool required a full single-window read of tasks.md before overwrite (a multi-window read did not satisfy it); resolved by reading the whole file in one call.
- Graders run and results (PASS/FAIL): PASS — T041 added, all IDs sequential (T001–T054), cancel documented consistently across tasks/contract/research.
- Prompt variant (if applicable): remediate-v1
- Next experiment (smallest change to try): Reserve a gap (e.g., renumber in 5s) when authoring tasks so insertions do not cascade renumbering.
