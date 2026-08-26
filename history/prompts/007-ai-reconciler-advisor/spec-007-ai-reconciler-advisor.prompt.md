---
id: spec-007-ai-reconciler-advisor
title: ai-reconciler-advisor-spec
stage: spec
date: 2026-08-25
surface: cli
model: claude-sonnet-5
feature: 007-ai-reconciler-advisor
branch: 007-ai-reconciler-advisor
user: developer
command: /sp.specify
labels: [spec, ai, reconciliation, agent, advisor, subh-al-baqaya]
links:
  spec: specs/007-ai-reconciler-advisor/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-ai-reconciler-advisor/spec.md
  - specs/007-ai-reconciler-advisor/checklists/requirements.md
  - history/prompts/007-ai-reconciler-advisor/spec-007-ai-reconciler-advisor.prompt.md
tests:
  - null
---

## Prompt

Create a feature specification for "AI Reconciler Advisor (Subh al Baqaya)" in the Bank Reconciliation System. The feature is the final main feature before production, tied to improving the UX of the entire reconciliation flow. The user's description: after reconciliation, a "Reconcile With Agent" button lets a chat-based agent (no tools) suggest potential discrepancies from the final discrepancies list, strictly for two cases: broken cheques/pairs (e.g. bank +79,000 and +100,000 vs company +179,000) and reversals (opposite-signed equal-magnitude near-dated entries, using descriptions like "reversal" as secondary evidence). The agent only suggests — it never auto-removes; the user manually reconciles via the frontend. The agent's output must be extractable by the frontend without JSON schema support (Deepseek). Use a NEW endpoint (not /reconcile-ai). Keep the existing debit/credit convention (Bank vs Vendor differ). Also a "What we Removed" button showing systematically removed pairs (matching pairs, opposite-sign same-date, reversals, broken cheques) to diagnose data for a next feature.

The specification was created on branch 007-ai-reconciler-advisor, using the spec-template, with user stories prioritized P1-P3, functional requirements FR-001 to FR-013, key entities, assumptions, and measurable, technology-agnostic success criteria. A quality checklist was generated at specs/007-ai-reconciler-advisor/checklists/requirements.md and validated.

## Response snapshot

Created the feature specification at specs/007-ai-reconciler-advisor/spec.md on new branch 007-ai-reconciler-advisor. The spec covers: 3 prioritized user stories (suggest and manually reconcile potential discrepancies P1, ask the agent anything about the reconciliation P2, follow-up questions to the agent about the reconciliation P3), 10 edge cases, 13 functional requirements (new endpoint, complete final discrepancies list context, structured output with a chat/text string field, strictly two supported cases (broken cheques/pairs, reversals), date+description as secondary evidence, purely advisory output, typed JSON payload delivered directly, suggestions with stable backend keys + reason, Reconcile With Agent button + follow-up chat, luxurious suggestions table with reason tooltip + Reconcile action, preserved debit/credit convention, unchanged manual/AI flows, reset agent state), 3 key entities, 6 assumptions, and 6 measurable success criteria. Generated the quality checklist at checklists/requirements.md and validated it — all items pass, no [NEEDS CLARIFICATION] markers remain. Before writing, I grounded the spec in the actual code via parallel exploration: the backend has no stable per-discrepancy ID (frontend synthesizes one client-side), removed pairs are tracked only as counts (no per-pair records), the live reconciliation response has no removed-items array, /reconcile-ai and /karwai are auth-exempt, and the debit/credit convention is negative=debit, positive=credit after standardization with FROM marking source. During the run the user gave two clarifications: (1) structured output via the agent framework's typed output (Pydantic model) rather than an output parser, adding a chat/text string field to the output schema, and (2) stable backend-generated per-item keys for the agent to reference. The user then removed the "What we Removed" feature entirely ("skip this feature entirely for now, we will implement this later on... completely remove this feature"), so I stripped FR-011, the Removed Pair Record entity, User Story 3 (replaced with follow-up questions), SC-006, and the related edge case, and documented the decision in Clarifications and Assumptions. Setup hit the known PowerShell 5.1 incompatibility in create-new-feature.ps1 (Join-Path with 4 args) which was worked around manually by creating the prompts directory; the branch, spec file, and history/prompts directory were created successfully.

## Outcome

- ✅ Impact: Full feature specification delivered; branch 007-ai-reconciler-advisor created; quality checklist passed; ready for /sp.clarify or /sp.plan.
- 🧪 Tests: None run (specification stage only).
- 📁 Files: specs/007-ai-reconciler-advisor/spec.md, specs/007-ai-reconciler-advisor/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 007-ai-reconciler-advisor
- 🧠 Reflection: Grounding the spec in the actual code (parallel exploration of backend and frontend) confirmed key facts that shaped the spec: no stable per-discrepancy IDs exist (so the agent needs backend-generated keys), removed pairs are only counted (so the "What we Removed" feature would require new data capture — which the user chose to defer), and the Deepseek JSON-schema limitation motivated the user's structured-output choice. The user's decision to remove the "What we Removed" feature kept scope tight and avoided designing data capture the user didn't want yet.

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell 5.1 incompatibility in create-new-feature.ps1 (Join-Path with 4 positional args); worked around by manually creating the prompts directory.
- Graders run and results (PASS/FAIL): Spec quality validation PASS (no placeholders, no NEEDS CLARIFICATION, mandatory sections complete, no implementation detail leaks).
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): None pending — spec validated.
