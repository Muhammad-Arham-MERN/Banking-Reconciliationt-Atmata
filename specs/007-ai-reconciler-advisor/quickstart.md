# Quickstart: AI Reconciler Advisor ("Subh al Baqaya")

**Date**: 2026-08-26 | **Branch**: `007-ai-reconciler-advisor`
Quick reference for building and validating this feature against `spec.md`. Full detail in `plan.md`, `research.md`, `data-model.md`, and `contracts/`.

## What to build

A new, auth-protected advisory endpoint + a frontend panel/chat that lets the user run a no-tools Reconciler Agent over the final discrepancies list, get typed suggestions for **broken cheques/pairs** and **reversals**, and manually **Reconcile** (frontend-only removal) any they approve. The agent never removes anything itself.

## Prerequisites

- Backend: Python >=3.13, FastAPI, `openai-agents[litellm]`; `.env` has `AI_MODEL` / `AI_API_KEY` (same Gemini family as the existing AI flows) and the CockroachDB `DATABASE_URL`.
- Frontend: Next.js 16 App Router, React 19, Tailwind v4, shadcn/ui (base-nova).

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/advisor/reconcile` | **Bearer** (required, NOT exempt) | Run agent: body = full discrepancies + cumulative Bank/Company context + history; streams response + retries up to 3 on failure. |
| POST | `/advisor/{request_id}/cancel` | Bearer | Cancel a running advisor turn (uses the existing 499/cancel behavior). |

Request/response schemas: `contracts/advisor-openapi.yaml`; example payloads: `contracts/advisor-request.json`, `contracts/advisor-response.json`.

## Backend steps

1. **Stable per-discrepancy key** — in `reconciliation_service.py`, assign `discrepancy_id` (`"<source>:<n>"`) over the final assembled `final_discrepancies`. Carry it on the dict (matches the unused `TransactionDiscrepancy.discrepancy_id` field).
2. **Cumulative Bank/Company totals** — compute running `bank_running` / `company_running` / `net` points over the list + final `bank_balance` / `company_balance`.
3. **Models** — new `backend/src/models/advisor_models.py` with the pydantic v2 request/response schemas from `data-model.md`.
4. **Advisor service** — new `backend/src/services/advisor_service.py` using the OpenAI Agents SDK: build the chat model from `settings`, no tools, strict two-case instructions (+ concise/authoritative rules), structured output into a pydantic model, `Runner.run_streamed`, unified 3-attempt retry, reuse `processing_cancellation` registry + `asyncio.CancelledError` → 499.
5. **Routes** — new `backend/src/api/advisor_routes.py` with `/advisor/reconcile` and `/advisor/{request_id}/cancel`; mount `advisor_router` in `main.py`. Do **NOT** add the advisor prefix to `AUTH_EXEMPT_PREFIXES`.
6. **Tests** — new `backend/tests/test_advisor.py` covering: broken-cheque suggestion, reversal suggestion, no-suggestion empty state, exact-item removal mapping, agent-never-alters (byte-identical list), 3-retry → friendly error, cancellation → 499.

## Frontend steps

1. **Client** — new `frontend/src/lib/api/advisorClient.ts` (plain `fetch` singleton, Bearer `access_token`, streaming consumption).
2. **Tooltip** — add `frontend/src/components/ui/tooltip.tsx` (none exists).
3. **Panel** — new `frontend/src/components/advisor/AdvisorPanel.tsx`: distinct card, Company/Bank headers, reason tooltip, per-suggestion **Reconcile** button, empty state.
4. **Chat** — new `frontend/src/components/advisor/AdvisorChat.tsx`: stateless, re-sends current live discrepancies + history.
5. **Wire-up** — new "Reconcile With Agent" trigger in `ReconciliationResults.tsx`; the suggestion-reconcile callback filters `discrepancies` by the suggested keys, mirroring the existing `handleReconcile`, so the live list + cloud save stay in sync. State resets on new reconciliation / fresh load.

## Verify (success criteria)

- **SC-001** — agent returns ≥1 correct suggestion per supported case on a reconciliation containing them.
- **SC-002** — 100% of user-approved suggestions remove exactly the suggested items.
- **SC-003** — an agent run the user does not act on leaves the list byte-identical.
- **SC-004** — full flow on 400+ items / 100+ discrepancies renders without degradation.
- **SC-005** — 100% of agent failures → 3 retries then friendly error, no partial state.
- **SC-006** — existing manual + AI flows behave unchanged.
- **SC-007** — every returned suggestion's sums do not break the running Bank/Company totals.

## Out of scope

- "What we Removed" visibility (capture/display of removed pairs) — later feature.

## Constitution

- Every edited/created file: `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` header, `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` footer, `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٍ` inline crux marker on the core suggestion logic (`advisor_service.py` crux, `reconciliation_service.py` key/totals crux).