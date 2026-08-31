---
id: plan-007-ai-reconciler-advisor
title: ai-reconciler-advisor-plan
stage: plan
date: 2026-08-26
surface: cli
model: claude-sonnet-5
feature: 007-ai-reconciler-advisor
branch: 007-ai-reconciler-advisor
user: developer
command: /sp.plan
labels: [plan, ai, reconciliation, agent, advisor, subh-al-baqaya, chat, streaming]
links:
  spec: specs/007-ai-reconciler-advisor/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-ai-reconciler-advisor/plan.md
  - specs/007-ai-reconciler-advisor/research.md
  - specs/007-ai-reconciler-advisor/data-model.md
  - specs/007-ai-reconciler-advisor/quickstart.md
  - specs/007-ai-reconciler-advisor/contracts/advisor-openapi.yaml
  - specs/007-ai-reconciler-advisor/contracts/advisor-request.json
  - specs/007-ai-reconciler-advisor/contracts/advisor-response.json
  - history/prompts/007-ai-reconciler-advisor/plan-007-ai-reconciler-advisor.prompt.md
tests:
  - null
---

## Prompt

start planning 007 spec

(Executed via /sp.plan: Execute the implementation planning workflow using the plan template to generate the design artifacts for feature 007-ai-reconciler-advisor "AI Reconciler Advisor (Subh al Baqaya)".)

The spec (specs/007-ai-reconciler-advisor/spec.md) defines a new, auth-protected advisory endpoint + frontend panel/chat. After reconciliation, a "Reconcile With Agent" button sends the COMPLETE final discrepancies list (each with date, details, signed Debit/Credit, source FROM, and a stable backend-generated key) plus cumulative Bank-vs-Company totals/balance context to a no-tools chat agent (same model family as the existing AI flows) that returns typed structured output (list of suggestions for broken cheques/pairs and reversals + a chat/text string). The agent strictly analyzes two cases only (broken cheques: a set of items whose signed amounts sum to a single opposite-sign item; reversals: near-dated opposite-sign equal-magnitude entries with reversal language in details). Output is purely advisory — the agent never removes. Suggestions render in a luxurious panel (Company/Bank headers, reason tooltip, per-suggestion Reconcile button). Reconcile removes exactly the suggested items frontend-only (mirroring the manual-reconcile filter). User can ask follow-up questions in a stateless streaming chat (re-sends current live context + history, keyed by request_id). Any agent failure (malformed/empty output or transport/model) retries up to 3 attempts then a friendly error. Endpoint must be a NEW dedicated endpoint requiring normal Bearer auth (NOT exempt like /karwai); preserve the negative=debit/positive=credit convention and FROM source; keep manual and AI flows unchanged; reset all agent state on new reconciliation. "What we Removed" is out of scope. Plan must produce: Technical Context, Constitution Check (gate pass), Project Structure, Phase 0 research.md (resolve unknowns), Phase 1 data-model.md + contracts/ + quickstart.md, agent-context update, and a re-evaluated Constitution Check post-design.

## Response snapshot

Created the implementation plan and all Phase 0/1 artifacts on branch 007-ai-reconciler-advisor. Grounded in parallel codebase exploration of backend/ and frontend/, with these key verified facts shaping the design: (1) no stable per-discrepancy key exists today (discrepancies are in-memory dicts; the `discrepancy_id` field in api_models.py is declared but unused) — the design assigns a deterministic `"<source>:<n>"` key at the final_discrepancies assembly point in reconciliation_service.py; (2) no cumulative Bank/Company balance over the discrepancy list exists (only whole-source extractor net scalars bank_net_total/company_net_total) — the design computes running bank_running/company_running/net points in ReconciliationService.reconcile(); (3) the AI pattern is openai-agents SDK + LitellmModel built from settings.AI_MODEL/AI_API_KEY (Gemini), Runner.run_streamed, the processing_cancellation registry, and 499/`asyncio.CancelledError` handling — all reused; (4) /reconcile-ai and /karwai are in AUTH_EXEMPT_PREFIXES, so the new /advisor/* endpoints must be OMITTED from that set to require Bearer auth per FR-001; (5) the frontend has no chat/panel/tooltip component (greenfield) and no global store; the suggestion-Reconcile button mirrors the existing `handleReconcile` `prev.filter(...)` in ReconciliationResults.tsx using the backend key resolved to the live list. Deliverables: plan.md (Technical Context + Constitution Check gate PASS with G1-G7, Project Structure backend/frontend, empty Complexity Tracking + Post-Design Re-evaluation PASS), research.md (8 decisions each with Decision/Rationale/Alternatives — no NEEDS CLARIFICATION remain), data-model.md (Discrepancy Item extended, new Balance Context/BalancePoint, Agent Suggestion/SuggestionItem, stateless Chat, state transitions), contracts/ (advisor-openapi.yaml with /advisor/reconcile + /advisor/{id}/cancel and full schemas; advisor-request.json and advisor-response.json worked examples), quickstart.md (backend/frontend build steps + SC-001..SC-007 verification), and updated CLAUDE.md via update-agent-context.ps1 (new 007 tech-stack + stateless DB entries, prior entries preserved).

## Outcome

- ✅ Impact: Complete, code-grounded Phase 0/1 plan for the final pre-production AI Reconciler Advisor feature; all spec unknowns resolved; design kept to the existing stack with no new dependencies.
- 🧪 Tests: None run (planning stage only). Backend test_advisor.py cases defined in plan/quickstart (broken-cheque, reversal, empty state, exact-item removal, never-alters, 3-retry → friendly error, cancel → 499).
- 📁 Files: specs/007-ai-reconciler-advisor/plan.md, research.md, data-model.md, quickstart.md, contracts/advisor-openapi.yaml, contracts/advisor-request.json, contracts/advisor-response.json, CLAUDE.md (agent-context update).
- 🔁 Next prompts: /sp.tasks for 007-ai-reconciler-advisor (create task breakdown from plan.md)
- 🧠 Reflection: The two clarifications in the prior spec that resolved the hardest questions (stable backend keys, cumulative balance context, dedicated auth-required endpoint, stateless chat, unified 3-attempt retry) left no NEEDS CLARIFICATION markers in Technical Context; exploration confirmed each maps to a real, currently-missing piece of the codebase, which the plan turns into explicit, bounded work items rather than assumptions. The advisor is the first browser-visible streaming endpoint (existing /reconcile-ai streams internally but returns plain JSON) — flagged as the one genuine new pattern, and it is spec-mandated by FR-008c.

## Evaluation notes (flywheel)

- Failure modes observed: The first research.md write reported success but did not land at the expected path (glob for specs/007/**/research.md returned no match); the file was safely re-created at the exact path with no duplicate/loss. update-agent-context.ps1 rendered the tech-stack line as a single concatenated entry (language + framework under one Active Technologies bullet) — script behavior, not a violation; existing manual content preserved.
- Graders run and results (PASS/FAIL): Constitution Check PASS (G1-G7) pre-research and again post-design with no violations; no Complexity Tracking required.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): None pending — proceed to /sp.tasks for 007-ai-reconciler-advisor.