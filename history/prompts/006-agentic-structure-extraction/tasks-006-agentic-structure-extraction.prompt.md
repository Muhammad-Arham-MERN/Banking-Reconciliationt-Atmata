---
id: tasks-006-agentic-structure-extraction
title: agentic-structure-extraction-tasks
stage: tasks
date: 2026-08-15
surface: cli
model: claude-sonnet-5
feature: 006-agentic-structure-extraction
branch: 006-agentic-structure-extraction
user: developer
command: /sp.tasks
labels: [tasks, ai, extraction, structure]
links:
  spec: specs/006-agentic-structure-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-agentic-structure-extraction/tasks.md
  - specs/006-agentic-structure-extraction/plan.md
  - specs/006-agentic-structure-extraction/spec.md
  - history/prompts/006-agentic-structure-extraction/tasks-006-agentic-structure-extraction.prompt.md
tests:
  - null
---

## Prompt

Generate the actionable, dependency-ordered tasks.md for feature 006-agentic-structure-extraction (Agentic Structure Extraction Upgrade) using the /sp.tasks workflow. Inputs: the spec at specs/006-agentic-structure-extraction/spec.md (3 user stories: P1 self-correcting structure extraction with a three-dimension evaluation loop, P2 deeper file understanding with dedicated reading tools, P3 opening balance and reconciliation-type awareness) and the plan at specs/006-agentic-structure-extraction/plan.md (Phase 2 task breakdown: add assess_structure tool closure + request_id plumbing, add opening_balance_pdf to FileStructureOutput, extend AGENT_INSTRUCTIONS with evaluation-first workflow, thread reconciliation_type default "bank" through detect_structure and the route, wire evaluator failures into the retry loop, add opening_balance_pdf/reconciliation_type to ai_metadata, verify with the prototype's sample files, regression-check /reconcile-ai and /karwai). This is a transfer feature: the assessor engine (backend/src/utils/structure_assessor.py) already ships in production, so Setup/Foundational are minimal and the real work is confined to backend/src/services/ai_structure_detector.py. Tasks must follow the strict checklist format (- [ ] [TaskID] [P?] [Story?] Description with exact file path), be organized by user story (US1 P1 MVP, US2 P2, US3 P3), include parallel opportunities, dependency graph, implementation strategy (MVP first), and a final polish phase. Tests are optional and not requested by the spec. Do NOT modify backend/tests/test.py and do NOT copy its hardcoded credentials — settings.AI_MODEL/AI_API_KEY drive the model.

## Response snapshot

Created specs/006-agentic-structure-extraction/tasks.md with 19 tasks across 6 phases: Phase 1 Setup (T001-T003, baseline confirmation that the assessor is production-ready and the route/config need no re-wiring), Phase 2 Foundational (T004-T006, the assess_structure tool closure + request_id plumbing + opening_balance_pdf output field — the one blocking prerequisite), Phase 3 User Story 1 (T007-T009, AGENT_INSTRUCTIONS evaluation-first workflow, tool registration, evaluator-failure wiring into the 3-attempt retry loop), Phase 4 User Story 2 (T010-T011, align read_pdf_words/read_excel to the prototype's drop/lines/page contract), Phase 5 User Story 3 (T012-T014, opening-balance + reconciliation-type guidance and reconciliationType route field defaulting to "bank"), and Polish (T015-T019, ai_metadata observability, end-to-end verification on the prototype's sample files, /reconcile-ai + /karwai regression, SC-004 timing check, docs update). All tasks follow the checklist format with exact file paths. Parallel opportunities: T006 with T004/T005; T010/T011; T018. Shared-file caution flagged: US1/US2/US3 all touch AGENT_INSTRUCTIONS, so sequential execution avoids conflicts. MVP is User Story 1. The plan's 8-task breakdown was expanded to 19 to separate verification/regression/polish tasks.

## Outcome

- ✅ Impact: Dependency-ordered, immediately-executable task list delivered — 19 tasks, 3 user-story phases + setup/foundational/polish, clear MVP scope (User Story 1).
- 🧪 Tests: None requested by spec; verification tasks T016-T018 cover end-to-end, regression, and timing.
- 📁 Files: specs/006-agentic-structure-extraction/tasks.md
- 🔁 Next prompts: /sp.analyze (consistency) or /sp.implement for 006-agentic-structure-extraction
- 🧠 Reflection: Because this is a transfer into one existing module, the template's Setup/Foundational scaffolding was adapted to baseline-confirmation tasks rather than project init — the assessor already exists, so the only true blocking prerequisite is the assess_structure tool closure (T004-T006).

## Evaluation notes (flywheel)

- Failure modes observed: None significant; prerequisites script emits CLIXML progress noise on PowerShell 5.1 but returns valid JSON.
- Graders run and results (PASS/FAIL): Format validation PASS — all 19 tasks use the checklist format with TaskID, P/Story markers, and exact file paths.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): None pending — proceed to /sp.analyze or /sp.implement.
