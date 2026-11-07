---
id: plan-012-agent-limitation-email
title: agent-limitation-email-plan
stage: plan
date: 2026-11-07
surface: cli
model: claude-sonnet-4-5
feature: 012-agent-limitation-email
branch: 012-agent-limitation-email
user: developer
command: /sp.plan
labels: [plan, agent-tools, email-notification, resend, tool-limitation, frontend-notice, blue-banner, sse]
links:
  spec: specs/012-agent-limitation-email/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-agent-limitation-email/plan.md
  - specs/012-agent-limitation-email/research.md
  - specs/012-agent-limitation-email/data-model.md
  - specs/012-agent-limitation-email/quickstart.md
  - specs/012-agent-limitation-email/contracts/agent-tool-contract.md
  - specs/012-agent-limitation-email/contracts/reconcile-ai-limitation.yaml
  - CLAUDE.md
  - history/prompts/012-agent-limitation-email/plan-012-agent-limitation-email.prompt.md
tests:
  - null
---

## Prompt

/sp.plan

Q1: The AI Agent itself determines the tool failure, i had a previous case before, the agent knew the exact issue, so it will be agent that will report to the email and inform about the issue   ----   Q2: A

## Response snapshot

Resolved the two spec clarifications (Q1 = AI agent itself determines and reports the tool/engine limitation, AI flow only; Q2 = A, technical detail + anonymised/structural example) and folded them into spec.md (Clarifications section, FR-010, FR-016, Assumptions) and the quality checklist (now fully green). Then executed /sp.plan.

Generated Phase 0/1 artifacts under specs/012-agent-limitation-email/: plan.md (Technical Context, Constitution Check — all gates PASS with no new dependency, project structure, design highlights), research.md (10 decisions D1–D10), data-model.md (4 transient entities — Tool Limitation Report, Limitation Notification Email, Technical-Limitation Failure Signal, Tool Purpose Summary — with validation rules and lifecycle diagrams; explicitly no persistence/migration), quickstart.md (8-step manual verification), and two contracts: contracts/agent-tool-contract.md (the `report_tool_limitation` tool signature, derived schema, behaviour, and the email format) and contracts/reconcile-ai-limitation.yaml (the 422 `technical_limitation` error body + the SSE status-frame `code` extension, with the unchanged cases preserved).

Design (grounded in the actual code): add a `report_tool_limitation` function tool to `build_agent_tools` in backend/src/services/ai_structure_detector.py; thread a per-run shared `limitation_holder` from ai_routes.reconcile_ai through detect_structure → build_agent → build_agent_tools (the same channel the existing `verdict_holder` uses); the tool emails via a new `send_agent_limitation_email` in notification_service.py (reusing the existing fail-soft Resend pattern, subject prefixed "Reconciliation Atmata" via new config `AGENT_LIMITATION_SUBJECT_PREFIX`, recipient `AGENT_LIMITATION_NOTIFY_EMAIL` default ArhamrBrowser@gmail.com), emits a live SSE stage frame, and is idempotent per run; on failure the route classifies the run as `technical_limitation` (422 detail + SSE status `code`) only when the holder recorded a report, otherwise keeps the existing agent_failed/agent_internal_error red handling; the frontend keys on `errorCode === 'technical_limitation'` to render the blue banner (existing `bg-blue-50 … text-blue-800` convention) in UploadAIConfig.tsx; AGENT_INSTRUCTIONS gains the reporting policy + a short, purpose-only tool summary (FR-009). Scope is the AI `/reconcile-ai` flow only; `/karwai` and the deterministic extractors are untouched.

Ran `.specify/scripts/powershell/setup-plan.ps1 -Json` (copied the plan template) and `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude` (appended the 012 tech-context lines to CLAUDE.md and bumped "Last updated").

## Outcome

- ✅ Impact: Complete plan for the agent tool-limitation email tool + blue technical-failure notice; all Phase 0/1 artifacts produced; no new dependency; ready for /sp.tasks.
- 🧪 Tests: None run (planning stage only, per the project's standing "no tests" instruction).
- 📁 Files: specs/012-agent-limitation-email/{plan.md,research.md,data-model.md,quickstart.md,contracts/agent-tool-contract.md,contracts/reconcile-ai-limitation.yaml}; CLAUDE.md updated.
- 🔁 Next prompts: /sp.tasks for 012-agent-limitation-email (optionally /sp.checklist first)
- 🧠 Reflection: The feature is small in surface acres but hinged on one real design question — how the agent's private determination reaches the failure response so the user notice can be blue only when it should be. Reusing the existing `verdict_holder` sharing channel (route → detect_structure → build_agent → tools) made that a one-dict change instead of a new global/registry, and reusing the existing SSE bus plus the existing error-code plumbing meant the frontend needed only a new `errorCode` branch and one blue banner. Keeping the email in notification_service.py (reusing the proven fail-soft Resend pattern) satisfied Gate II with zero new packages. The two clarifications were load-bearing: they fixed the scope to the AI flow (so /karwai and extractor partial-failures stay out) and forbade raw financial rows in the email, which is why the report is composed only from validated fields with an anonymised example.

## Evaluation notes (flywheel)

- Failure modes observed: none new in /sp.plan; both spec-kit PowerShell scripts ran clean (setup-plan.ps1 and update-agent-context.ps1 do not use the multi-arg Join-Path that breaks create-new-feature.ps1 on Windows PowerShell 5.1).
- Graders run and results (PASS/FAIL): Constitution Check PASS — Gates I/II/III/V/VI plus Code Standards 1–3 and the no-tests policy all pass; Complexity Tracking empty; no [NEEDS CLARIFICATION] remain after the two answers were folded in.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): In /sp.tasks, add one explicit cross-cutting task enforcing the constitution's بسم الله header + وَإِنَّ اللَّهَ footer + وَهُوَ crux marker on every new/edited backend and frontend file, so it is never missed during implementation.
