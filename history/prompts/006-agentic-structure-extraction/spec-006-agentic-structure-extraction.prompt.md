---
id: spec-006-agentic-structure-extraction
title: agentic-structure-extraction-spec
stage: spec
date: 2026-08-15
surface: cli
model: claude-sonnet-5
feature: 006-agentic-structure-extraction
branch: 006-agentic-structure-extraction
user: developer
command: /sp.specify
labels: [spec, ai, extraction, structure, agentic]
links:
  spec: specs/006-agentic-structure-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-agentic-structure-extraction/spec.md
  - specs/006-agentic-structure-extraction/checklists/requirements.md
  - history/prompts/006-agentic-structure-extraction/spec-006-agentic-structure-extraction.prompt.md
tests:
  - null
---

## Prompt

Create a feature specification for "Agentic Structure Extraction Upgrade" in the Bank Reconciliation System. The feature upgrades the production AI structure detection system to match the already-built prototype in backend/tests/test.py. The user's description: the old AI structure detection system had many weak points, limitations, lack of tools, lack of structure, unpredictable implementation flow, low accuracy, and was unusable in most cases. The new agentic system has many more tools (PDF reading tool, Excel read tool, assessment tool), a detailed tester/analysis tool that tests the agent response using Intelligence and 3 Evaluation marks, and constant reiteration of the agent for perfect tip-top structure extraction. The new implementation with substantial accuracy increase is developed in backend/tests/test.py; to implement in production, follow the pattern of how the agent is built in test.py and implement/upgrade it exactly as implemented there in the Production Agentic Structure Assessor. The structure extraction is mainly done by the agent; the new agent extracts just like before and passes the structure to the main system flow for further processing. Everything is already built, just a transfer is needed.

The specification was created on branch 006-agentic-structure-extraction, using the spec-template, with user stories prioritized P1-P3, functional requirements FR-001 to FR-012, key entities, assumptions, and measurable, technology-agnostic success criteria. A quality checklist was generated at specs/006-agentic-structure-extraction/checklists/requirements.md and validated: no [NEEDS CLARIFICATION] markers remain, no implementation details leak, all mandatory sections complete, all checklist items pass.

## Response snapshot

Created the feature specification at specs/006-agentic-structure-extraction/spec.md on new branch 006-agentic-structure-extraction. The spec covers: 3 prioritized user stories (self-correcting structure extraction with three-test evaluation P1, deeper file understanding with dedicated reading tools P2, opening balance and reconciliation-type awareness P3), 8 edge cases, 12 functional requirements (dedicated file-reading tools covering Excel/PDF content/PDF word geometry, three-dimension self-evaluation (arithmetic correctness, completeness, closing-balance anchor), iterative revision until all three pass or a bound is reached, opening-balance reading with graceful degradation, bank/vendor reconciliation-type sign convention, opening balance in the emitted structure, unchanged failure behavior (3 attempts/retry message/cancellation), unchanged manual flow, graceful inconclusive evaluation, actionable feedback, zero new user input), 5 key entities, 6 assumptions, and 6 measurable success criteria. Generated the quality checklist at checklists/requirements.md and validated it — all 16 items pass, no clarification markers remain. Before writing, I grounded the spec in the actual code: the prototype (backend/tests/test.py) uses 4 tools including the assess_structure tool with the 3-check assessor (Saghir/Kabir/Ihsan) and a self-iteration loop; production (backend/src/services/ai_structure_detector.py) currently has only 3 tools and no self-assessment; the assessor engine already exists in production (backend/src/utils/structure_assessor.py), confirming the "transfer" is genuinely feasible and small. Setup had one PowerShell 5.1 incompatibility in create-new-feature.ps1 (Join-Path with 4 args) which was worked around manually; the branch, spec file, and history/prompts directory were created successfully.

## Outcome

- ✅ Impact: Full feature specification delivered; branch 006-agentic-structure-extraction created; quality checklist passed; ready for /sp.clarify or /sp.plan.
- 🧪 Tests: None run (specification stage only).
- 📁 Files: specs/006-agentic-structure-extraction/spec.md, specs/006-agentic-structure-extraction/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 006-agentic-structure-extraction
- 🧠 Reflection: Grounding the spec in the actual prototype and production code (read test.py, ai_structure_detector.py, structure_assessor.py) confirmed the user's claim that this is a transfer — the assessor engine already ships in production — and let me describe the three evaluation dimensions functionally without leaking implementation names into the spec.

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell 5.1 incompatibility in create-new-feature.ps1 (Join-Path with 4 positional args); worked around by manually creating the prompts directory.
- Graders run and results (PASS/FAIL): Spec quality validation PASS (no placeholders, no NEEDS CLARIFICATION, mandatory sections complete, no implementation detail leaks).
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): None pending — spec validated.
