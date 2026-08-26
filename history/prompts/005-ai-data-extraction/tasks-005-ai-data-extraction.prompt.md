---
id: tasks-005-ai-data-extraction
title: ai-data-extraction-tasks
stage: tasks
date: 2026-08-06
surface: cli
model: claude-sonnet-5
feature: 005-ai-data-extraction
branch: 005-ai-data-extraction
user: developer
command: /sp.tasks
labels: [tasks, ai, extraction, planning]
links:
  spec: specs/005-ai-data-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-ai-data-extraction/tasks.md
  - history/prompts/005-ai-data-extraction/tasks-005-ai-data-extraction.prompt.md
tests:
  - null
---

## Prompt

Execute the /sp.tasks workflow for feature 005-ai-data-extraction ("AI-Based Data Extraction / Istikhraj e Data Ma'a AI"). Steps: run check-prerequisites.ps1 to get FEATURE_DIR and AVAILABLE_DOCS; load the design documents (plan.md required, spec.md for user stories, research.md, data-model.md, contracts/, quickstart.md); extract tech stack + project structure from plan.md, user stories with priorities from spec.md (US1 P1 hands-free reconciliation with automatic structure detection, US2 P2 graceful failure handling with 3 retries, US3 P3 current flow unchanged), entities from data-model.md (DetectedFileStructure, AIExtractionResult), endpoints from contracts/ (POST /reconcile-ai, 200 success/partial_success, 422 ai_detection_failed), decisions from research.md (OpenAI Agents SDK, env-var AI_MODEL/AI_API_KEY, 3 tools, parse_output_block, dynamic extract_pdf, 3-retry orchestration, parallel asyncio.gather, /upload-AI frontend); generate tasks.md using tasks-template.md structure — Phase 1 Setup, Phase 2 Foundational, Phase 3-5 user stories in priority order, Phase 6 Polish; each task in strict checklist format `- [ ] T### [P?] [US#] Description with file path`; include test tasks (repo has established pytest conventions); include dependency graph, parallel execution examples, implementation strategy (MVP = US1); validate format; report total task count, count per story, parallel opportunities, independent test criteria, suggested MVP scope.

## Response snapshot

Generated specs/005-ai-data-extraction/tasks.md with 44 tasks in strict checklist format, organized in 6 phases: Phase 1 Setup (T001-T006: openai-agents+litellm deps, AI_MODEL/AI_API_KEY config + .env.example, module scaffolds), Phase 2 Foundational (T007-T010: parse_output_block + FileStructureOutput, dynamic extract_pdf port, router registration, parser tests), Phase 3 US1 P1 MVP (T011-T024: 4 tests + 3 tools, agent, detect_structure, ai_pdf_processor, ai_excel_processor, POST /reconcile-ai, UploadAIConfig, reconcileAi API call, results view, frontend test), Phase 4 US2 P2 (T025-T033: retry orchestration tests + detect_with_retry, AIDetectionError, partial success handling, frontend error banners), Phase 5 US3 P3 (T034-T037: regression tests + no-modification audit, distinct route verification), Phase 6 Polish (T038-T044: env docs, Balance-column heuristic, logging, pytest, npm test, constitution compliance audit, quickstart validation). Dependencies section documents phase and story ordering (US2 builds on US1's detect_structure; US3 is regression-only per FR-012). Parallel opportunities marked across all phases. Independent test criteria per story. MVP = User Story 1. Format validated: all 44 tasks have checkbox + ID + file path; story-phase tasks carry [US#] labels.

## Outcome

- ✅ Impact: Actionable, dependency-ordered tasks.md produced; feature ready for /sp.implement.
- 🧪 Tests: None run (task generation stage only).
- 📁 Files: specs/005-ai-data-extraction/tasks.md
- 🔁 Next prompts: /sp.implement for 005-ai-data-extraction
- 🧠 Reflection: Test tasks included because the repo has established pytest conventions and the plan specified new test files; US3 was scoped as a regression audit (FR-012 forbids modifying the old flow), so its "implementation" tasks are verification tasks, not code changes.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): Format validation PASS — 44/44 tasks match `- [ ] T### [P?] [US#?] Description with file path`; story coverage complete (US1: 14, US2: 9, US3: 4 tasks).
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): None pending — tasks.md complete, ready for /sp.implement.
