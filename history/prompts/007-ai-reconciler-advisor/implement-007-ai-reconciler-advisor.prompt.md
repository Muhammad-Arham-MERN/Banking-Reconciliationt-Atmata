---
id: implement-007-ai-reconciler-advisor
title: ai-reconciler-advisor-implementation
stage: green
date: 2026-08-27
surface: cli
model: claude-sonnet-5
feature: 007-ai-reconciler-advisor
branch: 007-ai-reconciler-advisor
user: developer
command: /sp.implement
labels: [implement, green, ai, reconciliation, agent, advisor, subh-al-baqaya, chat, streaming]
links:
  spec: specs/007-ai-reconciler-advisor/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/reconciliation_service.py
  - backend/src/models/advisor_models.py
  - backend/src/services/advisor_service.py
  - backend/src/api/advisor_routes.py
  - backend/src/main.py
  - frontend/src/types/advisor.types.ts
  - frontend/src/types/reconciliation.types.ts
  - frontend/src/lib/api/advisorClient.ts
  - frontend/src/components/ui/tooltip.tsx
  - frontend/src/components/advisor/AdvisorPanel.tsx
  - frontend/src/components/advisor/AdvisorChat.tsx
  - frontend/src/components/results/ReconciliationResults.tsx
  - specs/007-ai-reconciler-advisor/tasks.md
  - specs/007-ai-reconciler-advisor/contracts/advisor-request.json
  - specs/007-ai-reconciler-advisor/contracts/advisor-response.json
  - specs/007-ai-reconciler-advisor/contracts/advisor-openapi.yaml
  - history/prompts/007-ai-reconciler-advisor/implement-007-ai-reconciler-advisor.prompt.md
tests:
  - "none (user explicitly requested no tests be written)"
---

## Prompt

(Executed via /sp.implement: Execute the implementation plan by processing and executing all tasks defined in tasks.md for feature 007-ai-reconciler-advisor.)

The feature: after a reconciliation completes, a "Reconcile With Agent" button sends the COMPLETE final discrepancies list (each with a stable backend-generated key, date, details, signed Debit/Credit, source FROM) plus cumulative Bank-vs-Company totals/balance context to a no-tools chat agent (openai-agents SDK + LiteLLM, same family as existing AI flows) that returns typed structured output — suggestions for broken cheques/pairs and reversals plus a chat/text string — streamed token-by-token, with a unified 3-attempt retry on any failure (malformed/empty output or transport/model errors), then a friendly error with no partial state. Suggestions are advisory only; the user clicks Reconcile per suggestion to remove exactly those items frontend-only (mirroring the manual-reconcile filter). A stateless streaming chat (US2) re-sends the CURRENT live discrepancies + history keyed by request_id; no server-side session store. Endpoint is a NEW dedicated /advisor/* requiring normal Bearer auth (NOT exempt like /karwai). Preserve negative=debit/positive=credit and FROM source; keep existing manual + AI flows unchanged (FR-012); reset agent state on new reconciliation (FR-013). "What we Removed" is out of scope. Every created/edited file carries the constitution prayer bookends (G7) with crux markers on the core suggestion/key/totals logic.

## Response snapshot

Implemented the full AI Reconciler Advisor (Subh al Baqaya) across backend and frontend. Backend: (1) reconciliation_service.py now assigns stable `<source>:<n>` discrepancy_id over the assembled final_discrepancies and exposes compute_balance_context() producing per-item BalancePoints + final bank_balance/company_balance (verified against the contract example: Bank:1..2 / Company:1..3, bank +179,000 / company -179,000); (2) new advisor_models.py (pydantic v2 request/response models, wire format Transaction_Detail underscore key + Debit/Credit slash alias); (3) new advisor_service.py — no-tools Reconciler Agent with strict two-case instructions (FR-003), evidence hierarchy (FR-004), concise rule (FR-008b), latest-context-authoritative (FR-008a), structured output into AdvisorResponse, Runner.run_streamed + unified 3-attempt retry (FR-006), cancellation via the existing processing_cancellation registry + explicit asyncio.CancelledError → 499 (FR-008c); (4) new advisor_routes.py — POST /advisor/reconcile (SSE-style stream: token frames + final typed result frame; 401/422/499/503) + POST /advisor/{request_id}/cancel; (5) main.py mounts advisor_router (verified in OpenAPI: /advisor/reconcile, /advisor/{request_id}/cancel). Frontend: new advisor.types.ts, advisorClient.ts (fetch singleton, Bearer token, SSE stream parsing, cancel via sendBeacon), shadcn tooltip.tsx (base-nova Tooltip.Root/Trigger/Portal/Positioner/Popup), AdvisorPanel.tsx (distinct card, Company/Bank headers, reason tooltip, per-suggestion Reconcile button, empty + stale-suggestion states), AdvisorChat.tsx (stateless streaming chat with stop button), and ReconciliationResults.tsx wiring (Reconcile With Agent button, advisor state, balance-context builder, exact-key removal callback, chat card). The user directed a contract improvement mid-flight: replace the fragile spaced "Transaction Detail" key with the safe underscore Transaction_Detail end-to-end (backend model field + frontend type + mapper + contract JSONs/YAML), keeping Debit/Credit as-is — implemented and validated.

## Outcome

- ✅ Impact: Complete green implementation of the final pre-production AI Reconciler Advisor feature; typed structured agent output, advisory-only suggestions, exact-item frontend removal, stateless streaming chat, unified retry, auth-protected dedicated endpoint.
- 🧪 Tests: None written — the user explicitly instructed "dont write any tests" mid-session, so T008-T014 and T025-T027 were skipped (marked [x] SKIPPED in tasks.md) and T031 adjusted. Validation instead via: python import checks, reconcile + balance-context unit checks, frontend npx tsc --noEmit (clean), npm run build (✓ compiled), live uvicorn smoke test (401 on /advisor without Bearer — FR-001 verified), OpenAPI schema check for both advisor paths, existing reconcile behavior unchanged (SC-006).
- 📁 Files: backend/src/services/reconciliation_service.py, backend/src/models/advisor_models.py, backend/src/services/advisor_service.py, backend/src/api/advisor_routes.py, backend/src/main.py; frontend/src/types/advisor.types.ts, frontend/src/types/reconciliation.types.ts, frontend/src/lib/api/advisorClient.ts, frontend/src/components/ui/tooltip.tsx, frontend/src/components/advisor/AdvisorPanel.tsx, frontend/src/components/advisor/AdvisorChat.tsx, frontend/src/components/results/ReconciliationResults.tsx; specs contracts updated to the underscore wire format; tasks.md marked off.
- 🔁 Next prompts: Manual end-to-end validation (T033-T035): run uvicorn + next dev, reconcile a file with the broken-cheque + reversal scenarios, click Reconcile With Agent, verify suggestions/Reconcile removal and the chat; optionally record a PHR for that validation.
- 🧠 Reflection: The wire-key decision was the session's key correction — the user pushed back on the spaced "Transaction Detail" key ("don't you think the Transaction_Detail is far more secure than Transaction Detail with space"), and it was resolved as a full end-to-end contract change (backend pydantic field + alias, frontend type, mapper, and the three contract files) rather than a one-sided model tweak. Two tooling notes: shell_command runs cmd.exe on this machine (Select-Object fails there — must use the PowerShell tool), and `python -c` one-liners importing src.main hang past 30s (likely DB/agents SDK init) while -X faulthandler with direct module imports works.

## Evaluation notes (flywheel)

- Failure modes observed: (1) pydantic ValidationError when the test payload used the spaced "Transaction Detail" key against the underscore field — led to the user-directed wire-format decision; (2) tooltip.tsx first draft used TooltipPrimitive.Props which does not exist in @base-ui/react 1.5 (parts are Root/Trigger/Portal/Positioner/Popup; side lives on Positioner) — fixed after reading the package .d.ts; (3) duplicate `export { AdvisorApiError }` alongside `export class` (TS2323) — removed the trailing re-export; (4) Set<string | undefined> narrowing (TS2322) — added an explicit type predicate; (5) main.py mount initially used prefix="/advisor" which would have doubled the path — removed it (routes already carry /advisor).
- Graders run and results (PASS/FAIL): tsc --noEmit PASS; next build PASS; backend imports + OpenAPI advisor paths PASS; live 401 smoke test PASS (FR-001); reconcile + balance-context unit checks PASS; SC-006 (existing behavior unchanged) PASS. T033-T035 (manual/performance) not run — need a live browser session.
- Prompt variant (if applicable): implement-v1
- Next experiment (smallest change to try): None pending — manual end-to-end validation next.
