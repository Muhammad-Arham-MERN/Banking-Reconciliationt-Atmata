---
id: tasks-007-ai-reconciler-advisor
title: ai-reconciler-advisor-tasks
stage: tasks
date: 2026-08-26
surface: cli
model: claude-sonnet-5
feature: 007-ai-reconciler-advisor
branch: 007-ai-reconciler-advisor
user: developer
command: /sp.tasks
labels: [tasks, ai, reconciliation, agent, advisor, subh-al-baqaya, chat, streaming]
links:
  spec: specs/007-ai-reconciler-advisor/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-ai-reconciler-advisor/tasks.md
  - history/prompts/007-ai-reconciler-advisor/tasks-007-ai-reconciler-advisor.prompt.md
tests:
  - null
---

## Prompt

start 007

(Executed via /sp.tasks: Generate an actionable, dependency-ordered tasks.md for feature 007-ai-reconciler-advisor "AI Reconciler Advisor (Subh al Baqaya)" from the design artifacts.)

The feature: after reconciliation completes, a "Reconcile With Agent" button sends the COMPLETE final discrepancies list (each with date, details, signed Debit/Credit, source FROM, stable backend-generated key) plus cumulative Bank-vs-Company totals/balance context to a no-tools chat agent (same model family as existing AI flows) that returns typed structured output (suggestions for broken cheques/pairs and reversals + a chat/text string), streamed token-by-token, retried up to 3 attempts on any failure. Suggestions are advisory only; the user clicks Reconcile per suggestion to remove exactly those items frontend-only (mirroring the manual-reconcile filter). A stateless streaming chat (US2) re-sends current live context + history keyed by request_id. Endpoint is a NEW dedicated `/advisor/*` requiring normal Bearer auth (NOT exempt like /karwai); preserve negative=debit/positive=credit and FROM; keep existing manual + AI flows unchanged; reset agent state on new reconciliation; "What we Removed" is out of scope. Every created/edited file must carry the constitution prayer bookends (G7) with crux markers on the core suggestion/key/totals logic. Tests ARE requested: quickstart.md and the spec's Independent Tests define pytest scenarios under backend/tests/test_advisor.py.

## Response snapshot

Created specs/007-ai-reconciler-advisor/tasks.md — 35 tasks across 5 phases: Phase 1 Setup (T001–T003, env/dependency verification only, no code), Phase 2 Foundational (T004–T007: stable `<source>:<n>` discrepancy_id + cumulative BalancePoint/bank_balance/company_balance in reconciliation_service.py; confirm processing_cancellation reuse and that /advisor stays OUT of AUTH_EXEMPT_PREFIXES), Phase 3 US1 P1 MVP (T008–T024: 7 failing-first test tasks for broken-cheque/reversal/empty/exact-removal/never-alters/3-retry→friendly-error/cancel→499, then advisor_models.py, advisor_service.py with _build_model + no-tools two-case agent + run_streamed + CancelledError→499, advisor_routes.py both endpoints, main.py mount, advisorClient.ts, shadcn tooltip.tsx, AdvisorPanel.tsx, ReconciliationResults.tsx wire-up via prev.filter), Phase 4 US2 P2 (T025–T030: 3 failing-first test tasks + service question/history fold-in + AdvisorChat.tsx + integration), Phase 5 Polish (T031–T035: full test suite, next build, SC-001/002/004/007 validation, zero-discrepancy/state-reset checks). Verified every integration point against the live repo before writing: final_discrepancies assembly at reconciliation_service.py:63, handleReconcile at ReconciliationResults.tsx:102, AUTH_EXEMPT_PREFIXES at auth_middleware.py:16, include_router at main.py:171-173, existing clients/components directories. Dependencies: Foundational blocks all stories; US1 → US2. MVP = Phase 1 + 2 + US1. No tests were run (task-generation stage); the test tasks themselves are specified to be written failing-first during implementation.

## Outcome

- ✅ Impact: A dependency-ordered, immediately executable task breakdown for the final pre-production AI Reconciler Advisor feature, with strict checklist format (`- [ ] [ID] [P?] [Story] description-with-path`), real file paths verified against the repo, per-story independent test criteria, and an MVP scope of Setup + Foundational + US1.
- 🧪 Tests: None run (tasks stage). test_advisor.py scenarios enumerated as failing-first tasks: broken-cheque, reversal, empty state, exact-item removal, never-alters, 3-retry → friendly error, cancel → 499 (US1); stateless re-send, no-removal follow-up, out-of-scope question (US2).
- 📁 Files: specs/007-ai-reconciler-advisor/tasks.md; PHR at history/prompts/007-ai-reconciler-advisor/tasks-007-ai-reconciler-advisor.prompt.md.
- 🔁 Next prompts: /sp.analyze for 007-ai-reconciler-advisor (project consistency analysis) then /sp.implement (phased implementation).
- 🧠 Reflection: The design docs were unusually complete (plan + spec + research + data-model + contracts + quickstart), so task generation was mapping, not design. Two structural notes: (1) no create-phr.ps1 script exists in .specify/scripts/powershell — the PHR was created manually from phr-template.prompt.md following the existing plan PHR convention; (2) the backend/tests/ dir contains only loose scripts (no pytest suite layout yet), so test tasks target the new backend/tests/test_advisor.py per plan.md while T031 defers to the existing test convention.

## Evaluation notes (flywheel)

- Failure modes observed: The first shell attempt mixed cmd and PowerShell (Select-Object via cmd) and errored; re-ran with the dedicated PowerShell tool. Feature dir also exists under specs/ with 007-ai-reconciler-advisor; the check-prerequisites AVAILABLE_DOCS list omitted plan.md/spec.md (only research.md, data-model.md, contracts/, quickstart.md) even though both exist — read the directory directly to confirm all six design docs.
- Graders run and results (PASS/FAIL): Format validation PASS — all 35 tasks follow the checklist format (checkbox, sequential Task ID, optional [P], story label on US tasks only, exact file paths); per-story test criteria defined; dependencies and parallel examples included.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): None pending — proceed to /sp.analyze for 007-ai-reconciler-advisor.
