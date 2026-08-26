---
id: spec-005-ai-data-extraction
title: ai-data-extraction-spec
stage: spec
date: 2026-08-06
surface: cli
model: claude-sonnet-5
feature: 005-ai-data-extraction
branch: 005-ai-data-extraction
user: developer
command: /sp.specify
labels: [spec, ai, extraction, reconciliation]
links:
  spec: specs/005-ai-data-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-ai-data-extraction/spec.md
  - specs/005-ai-data-extraction/checklists/requirements.md
  - history/prompts/005-ai-data-extraction/spec-005-ai-data-extraction.prompt.md
tests:
  - null
---

## Prompt

Create a feature specification for "Istikhraj e Data Ma'a AI": an AI-based data extraction feature for the Bank Reconciliation System. The feature replaces manual Excel column-name entry and the single-bank PDF processor with automatic, model-driven file structure detection. The user provided a detailed description including: current system flow (upload files, choose past history, add Excel column names, process, reconcile, save), the two main problems (only MCB Bank PDFs supported; manual column entry is time-consuming and error-prone), the new design (user uploads files, an AI system grasps the exact structure of the PDF and Excel, passes structure/column names to the current deterministic system, and the rest of the pipeline remains unchanged), the AI approach (OpenAI Agents SDK agent with 3 tools accessing the files; the LLM derives pdf column names, dropped lines, band, positional locations, header names, excel column names; a parse_output_block extractor converts the LLM response into structured data; extract_pdf from test_results.py slices PDF words at detected column boundaries), and edge cases (environment variables for model name/API key, 3 retries on failed LLM behavior with a graceful retry error on the frontend, multipart file uploads in production, and keeping the old system intact until the developer approves removal). The new frontend route must be /upload-AI, not /upload.

The specification was created on branch 005-ai-data-extraction, using the spec-template, with user stories prioritized P1-P3, functional requirements FR-001 to FR-015, key entities, assumptions, and measurable, technology-agnostic success criteria. A quality checklist was generated at specs/005-ai-data-extraction/checklists/requirements.md and validated: no [NEEDS CLARIFICATION] markers remain, no implementation details leak, all mandatory sections complete, all checklist items pass.

## Response snapshot

Created the feature specification at specs/005-ai-data-extraction/spec.md on new branch 005-ai-data-extraction. The spec covers: 3 prioritized user stories (hands-free reconciliation with automatic structure detection P1, graceful failure handling with 3 retries P2, current flow unchanged P3), 9 edge cases, 15 functional requirements (automatic PDF structure detection, automatic Excel column detection, automated debit/credit format selection, reuse of the existing reconciliation pipeline, 3 retry attempts with graceful error, env-var configuration of model and API key, separate /upload-AI route, current flow untouched, history save/reload, file cleanup, validation), 5 key entities, 8 assumptions, and 6 measurable success criteria. Generated the quality checklist at checklists/requirements.md and validated it — all items pass, no clarification markers remain. Setup had one PowerShell 5.1 incompatibility in create-new-feature.ps1 (Join-Path with 4 args) which was worked around manually; the branch, spec file, and history/prompts directory were created successfully.

## Outcome

- ✅ Impact: Full feature specification delivered; branch 005-ai-data-extraction created; quality checklist passed; ready for /sp.clarify or /sp.plan.
- 🧪 Tests: None run (specification stage only).
- 📁 Files: specs/005-ai-data-extraction/spec.md, specs/005-ai-data-extraction/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 005-ai-data-extraction
- 🧠 Reflection: The reference implementation (test.py / test_results.py) informed the spec's structure-detection and extraction requirements without leaking implementation details into the spec text.

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell 5.1 incompatibility in create-new-feature.ps1 (Join-Path with 4 positional args); worked around by manually creating the prompts directory.
- Graders run and results (PASS/FAIL): Spec quality validation PASS (no placeholders, no NEEDS CLARIFICATION, mandatory sections complete, no implementation detail leaks).
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): None pending — spec validated.
