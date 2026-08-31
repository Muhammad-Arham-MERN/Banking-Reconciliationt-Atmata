# Research: AI Reconciler Advisor ("Subh al Baqaya")

**Phase 0** — resolves all unknowns for `specs/007-ai-reconciler-advisor/plan.md`.
**Date**: 2026-08-26
**Method**: Consolidation of spec clarifications (2026-08-25 / 2026-08-26) + codebase exploration of `backend/` and `frontend/`.

## 1. Backend AI integration pattern

### Decision
Use the existing OpenAI Agents SDK (`openai-agents[litellm]`) with a chat-capable model built from `settings.AI_MODEL` / `settings.AI_API_KEY` (`LitellmModel`), configured via a `_build_model()` helper exactly as `ai_structure_detector.py` does. Structured output is delivered as a typed pydantic model the frontend consumes directly (per clarification "structured output delivered as a typed JSON payload"), with a `chat_message` string alongside the `suggestions` list.

### Rationale
The constitution mandates stack authority (Principle II). The spec assumption states the Reconciler Agent is "a chat-capable model from the same model family already used by the existing AI extraction flows." Reusing the identical SDK/config avoids a second model-provider integration and keeps structured-output handling uniform.

### Alternatives considered
- A hand-written output parser on the frontend — rejected by the spec (assumptions: "not by a hand-written output parser on the frontend") and FR-002a.
- A separate, exempt endpoint reusing `/reconcile-ai` — rejected by FR-001 (dedicated endpoint) and the assumption that a new dedicated endpoint is used rather than `/reconcile-ai`.

## 2. Endpoint & authentication

### Decision
New `POST /advisor/reconcile` (request body = discrepancies + cumulative balance context + chat history) plus `POST /advisor/{request_id}/cancel`, mounted on a new `advisor_router` in `main.py`. **Auth required**: the advisor prefixes MUST NOT be added to `AUTH_EXEMPT_PREFIXES` in `auth_middleware.py`; the frontend sends the Bearer JWT (from the session `access_token`, same as `cloudHistoryClient.saveCloudFile`).

### Rationale
FR-001 is explicit: the advisor endpoint requires the same Bearer auth as the rest of the API and is NOT exempted like `/karwai`. `/reconcile-ai` and `/karwai` are currently in `AUTH_EXEMPT_PREFIXES`, which is exactly why FR-001 calls this out — the advisor must not inherit that exemption.

### Alternatives considered
- Adding `/advisor` to the exempt set (following the `/reconcile-ai` default) — rejected; violates FR-001 and would render the endpoint callable without identifying the user.
- Reusing `/reconcile-ai` — rejected (dedicated endpoint required).

## 3. Stable per-discrepancy key

### Decision
No stable per-discrepancy key exists today. The backend MUST assign a deterministic key at the discrepancy-injection points in `reconciliation_service.py`. Use a stable, collision-free key of the form `"<FROM>:<n>"` where `<n>` is the 1-based positional index over the final assembled list (Bank items enumerated first, then Company items, matching the final array order), i.e. `Bank:1`, `Bank:2`, `Company:1`, … Deterministic given the same inputs.

The key is carried on each discrepancy dict as `discrepancy_id` (matching the already-declared but unused `TransactionDiscrepancy.discrepancy_id` field in `api_models.py`). It is backend-generated, never rendered in the UI, and consumed by the frontend only for resolution/removal.

### Rationale
FR-002 requires each discrepancy to carry a stable backend-generated key assigned during reconciliation. The reconcile output is built as plain dicts from `bank_tx.copy()`/`company_tx.copy()`, so assigning at the assembled `final_discrepancies` step is the least invasive insertion point. Prefix-plus-position keys are stable for a given input and guaranteed unique across both sources; they align with how the frontend synthesizes `itemId`.

### Alternatives considered
- Content hash of `(FROM, Transaction_date, Transaction Detail, Debit/Credit)` — rejected: duplicate rows would share a key, breaking exact-item reference.
- Natural keys `(FROM, date, details, amount)` — rejected for the same duplicate problem.
- A DB/serial auto-increment id — rejected: discrepancies are computed in-memory per request and never persisted as rows; no DB id exists to reuse.

## 4. Cumulative totals / balance context

### Decision
Compute in-order running Bank-vs-Company totals over the resolved `final_discrepancies` list in `reconciliation_service.reconcile()`. Concretely: iterate the list, `running[FROM] += Pre-signedAmount` for the item's own source, and on each item produce a "point" with Bank running, Company running, and Net (Bank + Company). Also include the two final summary totals `bank_balance` and `company_balance`.

### Rationale
No cumulative computation exists today; only whole-source net scalars (`bank_net_total`, `company_net_total`). FR-002b requires running totals/balances broken down by Bank vs Company sent to the agent as a supporting mathematical check. Using the pre-signed `Debit/Credit` (negative=debit, positive=credit) matches FR-011 and ignores what `reconciliation_type` does elsewhere.

### Alternatives considered
- Reusing `bank_net_total`/`company_net_total` raw-file totals — rejected: those are extractor summary scalars from the original statements, not running balances over the discrepancies.
- Computing on the frontend — rejected: the endpoint contract owns the context, and the backend holds the final list authoritatively.

## 5. Reconciler Agent behavior (two cases, advisory only)

### Decision
The agent is configured with **no tools** and custom system instructions that restrict it to exactly two suggestion types, enforced in the prompt AND re-checked:
1. **Broken cheque/pair** — a set of items on one side whose signed amounts sum to a single item of opposite sign on the other side, typically near in date. The suggestion groups 2+ items. Must not break the running Bank/Company totals.
2. **Reversal** — opposite-signed items of equal magnitude near in date, with reversal language in the description as secondary evidence.

The agent MUST NOT suggest other removals; output is purely advisory (FR-005). The system instruction also enforces the concise-response rule (FR-008b) and "latest context is authoritative" (FR-008a). No tool is registered on the `Agent`.

### Rationale
FR-003 and FR-004 fix the allowed case set and the required evidence hierarchy (signed amounts primary; dates/descriptions/balance secondary). FR-005 fixes advisory-only. No-tools matches the user input ("a chat-based agent (no tools)") and the spec.

### Alternatives considered
- A broad "find any discrepancy" agent — rejected: FR-003 is explicit that the two cases are the only permitted ones.
- Agent with tool functions (e.g. `read_excel`/`read_pdf`) — rejected: violates the no-tools requirement and the "never the raw file data" edge case.

## 6. Streaming, cancellation & retry

### Decision
Stream the model turn internally with `Runner.run_streamed` and surface token chunks to the client over a streaming (SSE-style) response — the advisor is the first browser-visible streaming endpoint (existing `/reconcile-ai` streams internally but returns plain JSON). Reuse the existing `processing_cancellation` registry (`register_run`/`is_cancelled`/`cancel_run`) and a `POST /advisor/{request_id}/cancel` route; honor a 499 JSON for cancelled runs and catch `asyncio.CancelledError` explicitly (it is a `BaseException` in Python 3.8+).

Unified retry rule (per 2026-08-26 clarification superseding the older one): any agent failure — malformed/empty structured output, unreachable model, missing credentials, timeout — is retried up to 3 attempts; if all fail, send a friendly error (agent unable to respond due to a technical failure) with no partial state (FR-006/SC-005).

### Rationale
FR-008c and the cancellation clarification already mandate streaming and 499-style cancel. The 499/`CancelledError` pattern and cancel registry are proven in the existing AI flows; reusing them keeps behavior unchanged (FR-012).

### Alternatives considered
- Plain JSON (like `/reconcile-ai`) — rejected: the advisor is explicitly streaming (FR-008c) and the user must be able to cancel mid-turn.
- Fresh cancellation logic — rejected: reuses existing registry, avoids drift.

## 7. Frontend UI & data flow

### Decision
New components under `frontend/src/components/advisor/`:
- `AdvisorPanel.tsx` — dedicated, visually distinct card panel headed "Agent Suggestions". Each suggestion renders rows (Date, Details, signed Amount, Source) grouped under a **Company / Bank** header, with the agent's reason and a chat/text message. Per suggestion: an **info tooltip** showing the reason and a **Reconcile** button.
- `AdvisorChat.tsx` — stateless streaming chat (messages list; follow-ups re-send the current live discrepancies + history).

A new shadcn `tooltip.tsx` is required (none exists). Wire "Reconcile With Agent" into `ReconciliationResults.tsx` and implement the suggestion-reconcile callback to filter `discrepancies` by the suggested keys, mirroring the existing `handleReconcile` (`prev.filter(...)`) so the live list, manual reconcile, and "Complete Reconciliation" save stay in sync. New client `frontend/src/lib/api/advisorClient.ts` following the plain-`fetch` singleton pattern with the `access_token` Bearer.

Removal is **frontend-only** (FR-010) — identical to the manual-reconcile flow; "Complete Reconciliation" persists the final list through the existing cloud save.

### Rationale
The frontend survey confirms no chat/panel/tooltip exists, so these are greenfield but must follow the existing `frontend/src/components/` and `frontend/src/lib/api/` conventions. The backend key (`discrepancy_id`) resolves against the live list, so the Reconcile filter can target exact rows. FR-010 explicitly says frontend-only removal identical to the manual-reconcile flow.

### Alternatives considered
- Server-side removal — rejected by FR-005/FR-010 (agent never removes; removal is frontend-only).
- Reusing an existing chat library/component — rejected: none exists and the spec wants a bespoke panel; keeps dependency footprint flat (stack authority).

## 8. State reset & stale-suggestion handling

### Decision
All advisor state (suggestions, chat) is component-local in `ReconciliationResults`/`AdvisorPanel`/`AdvisorChat` and resets on new reconciliation and on fresh page load (FR-013). Every agent request sends the CURRENT live discrepancies (after any manual/agent reconciles applied) so stale suggestions are prevented at the root (key clarification); as a fallback, the frontend resolves suggestion keys against the live list and hides+informs on any suggestion whose items are gone.

### Rationale
FR-013 and the stale-suggestion clarification both mandate root prevention (send latest context) plus a fallback (hide stale). Component-local state matches the existing no-global-store architecture.

### Alternatives considered
- Server-side session store — rejected: FR-008a explicitly forbids it (stateless server chat).

## Consolidated open decisions (none pending)

All items in Technical Context had no `NEEDS CLARIFICATION`; every decision above is grounded in an FR, an edge case, a clarification, or an existing codebase convention. No research tasks remain.