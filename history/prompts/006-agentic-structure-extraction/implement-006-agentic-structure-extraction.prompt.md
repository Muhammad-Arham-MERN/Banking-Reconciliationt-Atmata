---
id: implement-006-agentic-structure-extraction
title: agentic-structure-extraction-implement
stage: misc
date: 2026-08-15
surface: cli
model: claude-sonnet-5
feature: 006-agentic-structure-extraction
branch: 006-agentic-structure-extraction
user: developer
command: /sp.implement
labels: [implement, ai, extraction, structure]
links:
  spec: specs/006-agentic-structure-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/ai_structure_detector.py
  - backend/src/api/ai_routes.py
  - backend/src/utils/structure_assessor.py
  - specs/006-agentic-structure-extraction/tasks.md
  - history/prompts/006-agentic-structure-extraction/implement-006-agentic-structure-extraction.prompt.md
tests:
  - backend/_verify_parse.py (temp, deleted)
  - backend/_verify_tools.py (temp, deleted)
  - backend/_verify_assessor.py (temp, deleted)
---

## Prompt

Execute /sp.implement for feature 006-agentic-structure-extraction (Agentic Structure Extraction Upgrade). Checklist status: requirements.md 16/16 PASS — proceed. Execute all 19 tasks from specs/006-agentic-structure-extraction/tasks.md in dependency order: Phase 1 setup confirmations (T001-T003), Phase 2 foundational (T004-T006: assess_structure tool closure calling assess_pdf_structure with use_ihsan=True and request_id, thread request_id through build_agent_tools/build_agent, add opening_balance_pdf to FileStructureOutput), Phase 3 US1 (T007-T009: evaluation-first AGENT_INSTRUCTIONS mirroring backend/tests/test.py, register the 4th tool, evaluator-failure wiring into the 3-attempt retry loop), Phase 4 US2 (T010-T011: align read_pdf_words to the prototype's two-pages-in-one-call contract and read_pdf per-page), Phase 5 US3 (T012-T014: opening-balance + reconciliation-type guidance in instructions, thread reconciliation_type default "bank" through detect_structure and add reconciliationType Form field to /reconcile-ai), Polish (T015-T019: add opening_balance_pdf + reconciliation_type to ai_metadata.detected_structure, end-to-end verification, no hardcoded credentials, SC-004 timing, docs). The user explicitly instructed: never forget test.py — mirror its tool contracts and instruction text faithfully, not from memory; align production tools to test.py's exact behavior before applying instruction text referencing that behavior. Also: production is hosted on servers, so no directory/cwd issues — the assess_structure closure captures the absolute upload path, never repo-relative.

## Response snapshot

Implemented all 19 tasks. All changes confined to three backend files: ai_structure_detector.py (4th assess_structure tool closure calling assess_pdf_structure(use_ihsan=True, request_id), request_id threaded through build_agent_tools/build_agent, opening_balance_pdf added to FileStructureOutput, AGENT_INSTRUCTIONS rewritten to mirror test.py verbatim including the two-pages-in-one-call read_pdf_words contract, PER-PAGE BAND/HEADER contract, Opening Balance guidance, and VALIDATE-with-assess_structure loop; read_pdf gained per-page param; read_pdf_words aligned to pages-1-and-2-in-one-call), ai_routes.py (reconciliationType Form field default "bank" threaded into detect_structure; opening_balance_pdf + reconciliation_type added to ai_metadata.detected_structure), structure_assessor.py (CRITICAL BUG FIX: added `from agents.decorators import tool` — the Ihsan closing-balance reader used @tool without importing it, a runtime NameError the moment Saghir+Kabir passed; re-verified Ihsan ran=True found=True passed=True). Verification: all modules compile and AST-parse; parse_output_block accepts opening_balance_pdf (9 fields); build_agent_tools registers exactly ['read_excel', 'read_pdf', 'read_pdf_words', 'assess_structure']; assessor correctly rejects a made-up structure with actionable issues and passes a real one (Ihsan closing balance check passed diff 0.0); grep confirms zero hardcoded credentials in backend/src. The user's mid-implementation correction (never forget test.py) redirected the instruction edit to mirror test.py verbatim and align tools first — recorded in taste. Temp verification scripts deleted.

## Outcome

- ✅ Impact: Production agentic structure detector now matches the validated test.py prototype — 4 tools including the three-check assess_structure evaluator, opening-balance + reconciliation-type awareness, self-iterating evaluation loop, and a critical runtime bug in the Ihsan path fixed.
- 🧪 Tests: py_compile + AST parse all modules; parse/tool-registration assertions; live assessor run on the Meezan sample (Ihsan passed); credential grep. No model-credential-dependent end-to-end agent run (needs AI_API_KEY at runtime).
- 📁 Files: backend/src/services/ai_structure_detector.py, backend/src/api/ai_routes.py, backend/src/utils/structure_assessor.py, specs/006-agentic-structure-extraction/tasks.md
- 🔁 Next prompts: /sp.analyze (consistency) or /sp.checklist; commit the work.
- 🧠 Reflection: The most valuable moment was the verification run surfacing the Ihsan NameError — a real production bug that only manifests when Saghir+Kabir pass and Ihsan's nested agent builds its tool. The user's "never forget test.py" instruction was exactly right: my first instruction edit was a reworded approximation; aligning the tools to test.py's exact contract first made the verbatim instruction text true.

## Evaluation notes (flywheel)

- Failure modes observed: (1) name 'tool' is not defined in structure_assessor.py _ihsan_page_text_tool — fixed with the missing import. (2) My initial instruction edit drifted from test.py — corrected by aligning tools first then copying test.py text. (3) Scratch script path resolution bug (repo-relative vs absolute) — production is immune since upload paths are absolute.
- Graders run and results (PASS/FAIL): py_compile PASS; AST parse PASS; tool-registration assertion PASS; parse_output_block assertion PASS; assessor live run PASS (Ihsan verified); credential grep PASS.
- Prompt variant (if applicable): implement-v1
- Next experiment (smallest change to try): Run the full agent against the sample files with AI_API_KEY set to confirm end-to-end iteration and SC-001 (all finalized structures pass all three checks).
