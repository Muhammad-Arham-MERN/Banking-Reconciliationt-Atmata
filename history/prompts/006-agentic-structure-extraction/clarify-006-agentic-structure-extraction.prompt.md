---
id: clarify-006-agentic-structure-extraction
title: agentic-structure-extraction-clarify
stage: clarify
date: 2026-08-15
surface: cli
model: claude-sonnet-5
feature: 006-agentic-structure-extraction
branch: 006-agentic-structure-extraction
user: developer
command: /sp.clarify
labels: [clarify, ai, extraction, structure]
links:
  spec: specs/006-agentic-structure-extraction/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-agentic-structure-extraction/spec.md
  - specs/006-agentic-structure-extraction/checklists/requirements.md
  - history/prompts/006-agentic-structure-extraction/clarify-006-agentic-structure-extraction.prompt.md
tests:
  - null
---

## Prompt

Run the /sp.clarify workflow on the feature specification at specs/006-agentic-structure-extraction/spec.md for feature 006-agentic-structure-extraction (Agentic Structure Extraction Upgrade). The spec upgrades the production AI structure detection system to match the prototype in backend/tests/test.py: a 4-tool agent with an assess_structure tool scoring proposals on three dimensions (arithmetic correctness, completeness, closing-balance anchor) with iterative self-correction, opening-balance reading, and bank/vendor sign conventions. The workflow requires: (1) run check-prerequisites.ps1 -Json -PathsOnly to confirm FEATURE_DIR/FEATURE_SPEC; (2) load the spec and perform a structured ambiguity & coverage scan across taxonomy categories (Functional Scope, Domain & Data Model, Interaction & UX, Non-Functional Quality Attributes, Integration, Edge Cases, Constraints & Tradeoffs, Terminology, Completion Signals, Misc); (3) generate a prioritized queue of up to 5 candidate questions, each answerable by multiple-choice or <=5 words, covering the highest (Impact * Uncertainty) unresolved categories; (4) present questions ONE at a time with a recommended option and reasoning, then a markdown table of options, and integrate each accepted answer incrementally into the spec (create ## Clarifications > ### Session YYYY-MM-DD, append one bullet per answer, update the relevant section, replace obsolete statements, save after each); (5) validate after each write (one bullet per answer, no vague placeholders left, no contradictory statements, markdown structure valid); (6) report completion with questions asked/answered, spec path, sections touched, and a coverage summary table.

## Response snapshot

Ran the /sp.clarify workflow on specs/006-agentic-structure-extraction/spec.md. Prerequisites confirmed the feature branch and spec path. Coverage scan: Functional Scope, Interaction & UX, Edge Cases, and Terminology were Clear; Domain & Data Model, Non-Functional Quality Attributes, and Constraints & Tradeoffs were Partial. Two high-impact questions were asked and answered sequentially: (Q1) arithmetic-correctness tolerance — the user chose a fixed per-row tolerance of 50 currency units (option A), which was integrated into FR-003 (per-row and closing-balance anchor both use 50 units), the P1 user story ("within the same tolerance"), and the Clarifications section; (Q2) fallback when the evaluator cannot run — the user chose fail-gracefully (option A), integrated into FR-008 (never emit an unverified structure) and the Edge Cases section, plus recorded in Clarifications. The Clarifications section (Session 2026-08-15) contains exactly one bullet per accepted answer. Validation passed: no lingering vague placeholders, no contradictory statements, markdown structure valid, only the allowed new headings added. The requirements checklist was updated to note the two resolved clarifications. Coverage summary: 7 categories Clear/Resolved, 3 Deferred (scalability/data-volume, observability, accessibility/localization) as low-impact and better suited to planning; no Outstanding items.

## Outcome

- ✅ Impact: Spec ambiguity reduced — tolerance and evaluator-failure behavior are now explicit and testable; spec ready for /sp.plan.
- 🧪 Tests: None run (clarification stage only).
- 📁 Files: specs/006-agentic-structure-extraction/spec.md, specs/006-agentic-structure-extraction/checklists/requirements.md
- 🔁 Next prompts: /sp.plan for 006-agentic-structure-extraction
- 🧠 Reflection: The two questions targeted the only materially-ambiguous decisions: a quantified tolerance (unquantified "within tolerance" in FR-003) and the evaluator-failure fallback (the existing retry loop guards the agent, not the new evaluator). Both were already answered by domain conventions in the underlying code (50.0 tolerance constant, fail-safe bias), which validates the user's choices as the natural defaults.

## Evaluation notes (flywheel)

- Failure modes observed: None significant; the prerequisite script emitted CLIXML progress noise on PowerShell 5.1 but returned valid JSON.
- Graders run and results (PASS/FAIL): Spec validation PASS — no placeholders, one bullet per clarification, no contradictions, valid markdown; requirements checklist updated.
- Prompt variant (if applicable): clarify-v1
- Next experiment (smallest change to try): None pending — proceed to /sp.plan.
