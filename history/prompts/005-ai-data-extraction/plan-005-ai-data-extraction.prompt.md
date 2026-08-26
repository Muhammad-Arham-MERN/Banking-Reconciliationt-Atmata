---
id: plan-005-ai-data-extraction
title: ai-data-extraction-plan
stage: plan
date: 2026-08-06
surface: cli
model: claude-sonnet-5
feature: 005-ai-data-extraction
branch: 005-ai-data-extraction
user: developer
command: /sp.plan
labels: [plan, ai, extraction, architecture]
links:
  spec: specs/005-ai-data-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-ai-data-extraction/plan.md
  - specs/005-ai-data-extraction/research.md
  - specs/005-ai-data-extraction/data-model.md
  - specs/005-ai-data-extraction/quickstart.md
  - specs/005-ai-data-extraction/contracts/api-contract.md
  - specs/005-ai-data-extraction/contracts/llm-contract.md
  - CLAUDE.md
tests:
  - null
---

## Prompt

Execute the /sp.plan workflow for feature 005-ai-data-extraction ("AI-Based Data Extraction / Istikhraj e Data Ma'a AI"). Steps: run setup-plan.ps1 to copy the plan template; load the spec, the constitution, and the plan template; fill Technical Context; run the Constitution Check gate (must pass before Phase 0); Phase 0: generate research.md resolving all NEEDS CLARIFICATION (agent framework = OpenAI Agents SDK from test.py, env-var AI_MODEL/AI_API_KEY config, 3 tools, LLM output contract + parse_output_block, dynamic extract_pdf from test_results.py, Excel via detected columns, 3-retry orchestration, parallel asyncio.gather detection, POST /reconcile-ai endpoint, /upload-AI frontend route, openai-agents + litellm deps); Phase 1: generate data-model.md (DetectedFileStructure, AIExtractionResult, reused entities), contracts/ (api-contract.md + llm-contract.md), quickstart.md; update agent context via update-agent-context.ps1 -AgentType claude; re-evaluate Constitution Check post-design; stop and report branch, plan path, and generated artifacts.

## Response snapshot

Completed the /sp.plan workflow on branch 005-ai-data-extraction. Ran setup-plan.ps1 (copied template to plan.md). Wrote plan.md (Summary, Technical Context, Constitution Check PASS, Project Structure — web app layout with 3 new backend service modules ai_structure_detector.py / ai_pdf_processor.py / ai_excel_processor.py, new ai_routes.py POST /reconcile-ai, modified config.py + requirements.txt, new frontend /upload-AI route with UploadAIConfig, 4 new backend test files + 1 frontend test). Wrote research.md with 10 decisions (agent SDK, model config, tool design, LLM output contract, PDF extraction, Excel extraction, retry orchestration, API surface, frontend, dependencies) plus deferred items. Wrote data-model.md (no new persisted entities; DetectedFileStructure pydantic + AIExtractionResult dict + reused entities; validation rules; state transition diagram). Wrote contracts/api-contract.md (multipart request, 200 success + partial_success shapes, 422 ai_detection_failed, error table) and contracts/llm-contract.md (exact [output] block format, 8 field semantics, parser regex, retry triggers). Wrote quickstart.md (env config, install, run, /upload-AI usage, tests, curl smoke test, troubleshooting). Updated CLAUDE.md with Active Technologies + Recent Changes (script parsed plan.md but targeted nonexistent sections; added manually). Constitution re-check PASS — all 6 principles satisfied, no violations, no Complexity Tracking needed.

## Outcome

- ✅ Impact: Full implementation plan + Phase 0/1 artifacts generated; Constitution Check passes; feature ready for /sp.tasks.
- 🧪 Tests: None run (planning stage only).
- 📁 Files: specs/005-ai-data-extraction/{plan,research,data-model,quickstart}.md, contracts/{api-contract,llm-contract}.md, CLAUDE.md
- 🔁 Next prompts: /sp.tasks for 005-ai-data-extraction
- 🧠 Reflection: update-agent-context.ps1 reported success but its parser only targets "## Active Technologies"/"## Recent Changes" sections which the project's CLAUDE.md lacked — the script silently no-op'd. Verified via grep and added the sections manually, preserving existing content.

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.ps1 silent no-op (target sections missing in CLAUDE.md); setup-plan.ps1 blocked in plan mode earlier (resolved by entering plan mode, approving plan, then running scripts).
- Graders run and results (PASS/FAIL): Constitution Check PASS; artifacts validated for coverage of FR-001..FR-019 and SC-001..SC-006.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): None pending — plan complete, ready for /sp.tasks.
