---
id: plan-006-agentic-structure-extraction
title: agentic-structure-extraction-plan
stage: plan
date: 2026-08-15
surface: cli
model: claude-sonnet-5
feature: 006-agentic-structure-extraction
branch: 006-agentic-structure-extraction
user: developer
command: /sp.plan
labels: [plan, ai, extraction, structure]
links:
  spec: specs/006-agentic-structure-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-agentic-structure-extraction/plan.md
  - specs/006-agentic-structure-extraction/spec.md
  - specs/006-agentic-structure-extraction/checklists/requirements.md
  - history/prompts/006-agentic-structure-extraction/plan-006-agentic-structure-extraction.prompt.md
tests:
  - null
---

## Prompt

Create the implementation plan (/sp.plan) for feature 006-agentic-structure-extraction (Agentic Structure Extraction Upgrade). The spec upgrades the production AI structure-detection agent (backend/src/services/ai_structure_detector.py) to match the validated prototype (backend/tests/test.py): add the fourth assess_structure evaluation tool scoring proposals on three dimensions (arithmetic correctness with a fixed 50-unit tolerance, completeness vs. an independent raw dated-row count, closing-balance anchor read by a nested agent), wire the opening balance into the agent's output contract, make the agent iterate until its structure passes all three checks (constant reiteration), and fail gracefully (same friendly retry message) if the evaluator itself cannot run — never emit an unverified structure. Preserve the existing route, deterministic extractors, 3-attempt retry, cancellation handling, and frontend; keep the current manual flow unchanged. Plan must use the plan-template, be grounded in the actual production code (ai_structure_detector.py, ai_routes.py, config.py, structure_assessor.py, ai_pdf_processor.py), and verify: opening_balance_pdf is unused by the extractors (non-breaking), reconciliation_type is not surfaced in the frontend today (default "bank"), the assessor engine already ships in production with Saghir/Kabir/Ihsan checks, and no hardcoded credentials from the prototype may be copied (use settings.AI_MODEL/AI_API_KEY). Structure: Summary, Technical Context, Constitution Check, Project Structure, Phase 0 research findings, Phase 1 design (output contract + agent construction + failure behavior + route integration + contracts), Phase 2 task breakdown (handled by /sp.tasks), Risks & Mitigations, Success Criteria traceability.

## Response snapshot

Created the implementation plan at specs/006-agentic-structure-extraction/plan.md. Phase 0 research confirmed the transfer is genuinely small: the assessor engine (structure_assessor.py) already ships in production with the three checks (Saghir arithmetic with 50.0 tolerance, Kabir completeness, Ihsan closing-balance anchor), so the plan's changes are confined to ai_structure_detector.py — add the assess_structure tool closure (with request_id plumbing for cancellation), add opening_balance_pdf to FileStructureOutput (backward-compatible, extractors ignore it — verified), extend AGENT_INSTRUCTIONS with the evaluation-first iterate-until-pass workflow, and wire evaluator failures into the existing 3-attempt retry loop (fail gracefully, never emit unverified). Route integration is minimal: optionally thread a reconciliationType Form field (default "bank") into detect_structure; frontend unchanged (reconciliation_type not surfaced today — verified). Constitution Check passed (no hardcoded credentials from the prototype, sign convention parameterized, cancellation handling preserved, file header convention preserved). Success criteria mapped to plan coverage; the main risk flagged is agent cost/latency, mitigated by the assessor's strict short-circuit (Kabir only after Saghir, Ihsan only after both) and the existing 2-minute bound. The plan explicitly delegates Phase 2 task decomposition to /sp.tasks.

## Outcome

- ✅ Impact: Technical plan delivered — production path for the agentic upgrade confined to one service module; plan grounded in verified code facts (non-breaking output contract, existing assessor reuse, default bank convention).
- 🧪 Tests: None run (planning stage only); regression checks defined in the task breakdown.
- 📁 Files: specs/006-agentic-structure-extraction/plan.md
- 🔁 Next prompts: /sp.tasks for 006-agentic-structure-extraction
- 🧠 Reflection: Reading the actual route and extractor code confirmed the output-contract addition is non-breaking and that reconciliation_type is not yet surfaced in the frontend — both facts kept the plan minimal and de-risked the transfer. The constitution check caught the prototype's hardcoded keys as a must-not-copy item, which is now an explicit risk mitigation.

## Evaluation notes (flywheel)

- Failure modes observed: None significant; prerequisites script emits CLIXML progress noise on PowerShell 5.1 but returns valid JSON.
- Graders run and results (PASS/FAIL): Constitution Check PASS; no violations.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): None pending — proceed to /sp.tasks.
