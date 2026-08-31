# Data Model: AI Reconciler Advisor ("Subh al Baqaya")

**Date**: 2026-08-26
Entities and relationships derived from `specs/007-ai-reconciler-advisor/spec.md` and grounded in the existing backend schemas (`reconciliation_models.py`, `api_models.py`). No new database tables or persistence — the advisor is stateless (FR-008a); all entities here are request/response payloads and in-memory reconcile-time facts.

## 1. Discrepancy Item (existing, extended)

A single final unmatched transaction shown on the results view. Already produced by `ReconciliationService.reconcile()`; this feature adds a stable backend-generated key (FR-002).

| Field | Type | Notes / Validation |
|-------|------|--------------------|
| `discrepancy_id` | `string` | **NEW.** Stable backend key, `"<source>:<n>"` (`Bank:1`, `Bank:2`, `Company:1`, …); assigned over the final assembled list. Never rendered in the UI (FR-002). Resolves against the frontend's live `itemId`. |
| `Transaction_date` | `string` (ISO `YYYY-MM-DD`) | Existing. |
| `Transaction Detail` | `string` | Existing cleaned detail text. |
| `Debit/Credit` | `float` | Existing. Signed: **negative = debit, positive = credit**, for both Bank and Company (FR-011). |
| `FROM` | enum `Bank` \| `Company` | Existing source; the item's origin. |
| `from_past` | `boolean?` | Optional existing flag for history-merged entries. |
| `category` (frontend only) | enum | Frontend categorization (UNPRESENTED_CHECKS, etc.) for rendering; not sent to the agent. |

Relationships: grouped into **Agent Suggestion** groups (2+ items) by the agent; each item belongs to exactly one live list.

## 2. Cumulative Totals / Balance Context (new)

Running totals/balances over the final discrepancy list, broken down by Bank vs Company (FR-002b). Computed in `ReconciliationService.reconcile()` over the resolved `final_discrepancies`.

| Field | Type | Notes |
|-------|------|-------|
| `points` | `BalancePoint[]` | One per discrepancy item, in list order. |
| `bank_balance` | `float` | Final Company-side running sum. |
| `company_balance` | `float` | Final Bank-side running sum. |

### BalancePoint
| Field | Type | Notes |
|-------|------|-------|
| `index` | `int` | 1-based position in the list. |
| `discrepancy_id` | `string` | The item this point belongs to. |
| `bank_running` | `float` | Cumulative Bank total up to and including this item. |
| `company_running` | `float` | Cumulative Company total up to and including this item. |
| `net` | `float` | `bank_running + company_running`. |

**Invariant**: every discrepancy's `Debit/Credit` is added to its own `FROM` bucket only; `net` = Bank + Company. The agent MUST NOT propose a suggestion whose sums break these running totals (FR-002b).

## 3. Agent Suggestion (new, agent output)

A group of 2+ discrepancy items that together form a reconcilable set. Returned in the agent's structured output (FR-007). The agent only suggests; it never removes (FR-005).

| Field | Type | Notes / Validation |
|-------|------|--------------------|
| `keys` | `string[]` | Stable `discrepancy_id`s for the involved items. Length ≥ 2 (FR-007: "2+ specific discrepancy items"). Each key must resolve in the current live list. |
| `type` | enum `BROKEN_CHEQUE` \| `REVERSAL` | One of the two supported cases (FR-003). |
| `company_items` | `SuggestionItem[]` | The involved items from the Company side. |
| `bank_items` | `SuggestionItem[]` | The involved items from the Bank side. |
| `reason` | `string` | Human-readable reason reflecting the mathematical check (e.g. "Broken cheque by company", "Reversal checks"). |

Validation rules:
- `keys.length == company_items.length + bank_items.length` and `keys.length >= 2`.
- Every `discrepancy_id` in `keys` must appear exactly once across the grouped items.
- For `BROKEN_CHEQUE`: the items on one side's signed amounts sum to a single opposite-sign item on the other side.
- For `REVERSAL`: opposite-signed, equal-magnitude items near in date.
- Suggestion sums must not break the running Bank/Company totals (FR-002b). This is advisory — surfaced to the user, never auto-applied.

### SuggestionItem
| Field | Type | Notes |
|-------|------|-------|
| `discrepancy_id` | `string` | Reference into the live list. |
| `date` | `string` | `Transaction_date`. |
| `details` | `string` | `Transaction Detail`. |
| `debit_credit` | `float` | Signed amount. |
| `source` | enum `Bank` \| `Company` | `FROM`. |

## 4. Agent Session / Chat (new, stateless)

The conversation between the user and the Reconciler Agent for one reconciliation result. **No server-side store** (FR-008a). Each message round-trips the current live discrepancy context + history.

| Field | Type | Notes |
|-------|------|-------|
| `request_id` | `string` | The reconciliation `request_id`, the conversation key. |
| `messages` | `ChatMessage[]` | Conversational history (excluding the large discrepancy context, which is re-sent whole each turn). |
| `suggestions` | `AgentSuggestion[]` | Results of the latest run (rendered in the panel). |
| `chat_message` | `string` | Free-text response alongside suggestions (FR-002a). |

### ChatMessage
| Field | Type | Notes |
|-------|------|-------|
| `role` | enum `user` \| `assistant` | Sender. |
| `content` | `string` | Message text. |

State lifecycle (FR-013): resets on new reconciliation start and on fresh page load; component-local, never persisted.

## 5. State Transitions

```
[Reconcile Complete] --click "Reconcile With Agent"--> [Agent Running (streaming)]
        |                                                   | success / fail after 3 retries
        v                                                   v
[Live Discrepancies] <--- advisory ------------------- [Suggestions + chat_message]
        |                                                   |
        | click Reconcile (frontend-only removal)           v
        +-----------------------------------------> [Items removed from live list]
        |                                                   |
        | "Complete Reconciliation" (existing cloud save)   v (agent state resets)
        v                                           [New reconciliation begins]
[Persisted final list] <-------------------------------------+
```

- Removal is **frontend-only** (FR-010), identical to the manual-reconcile flow.
- Every subsequent agent request re-sends the updated live list (root prevention vs stale suggestions).
- A cancelled/streaming run uses the existing 499 / cancel-status behavior.

## 6. Backend Pydantic Models (target)

New module `backend/src/models/advisor_models.py` (validated with pydantic v2):

- `AdvisorReconcileRequest` — `request_id: str`, `discrepancies: list[AdvisorDiscrepancy]`, `context: BalanceContext`, `history: list[ChatMessage]`, `question: str | None = None`.
- `AdvisorDiscrepancy` — `discrepancy_id`, `Transaction_date`, `Transaction Detail`, `Debit/Credit`, `FROM`, optional `from_past`.
- `BalanceContext` / `BalancePoint` — as above.
- `AdvisorSuggestion` / `AdvisorSuggestionItem` — as above.
- `AdvisorResponse` — `suggestions: list[AdvisorSuggestion]`, `chat_message: str`.
- `ChatMessage` — `role`, `content`.

These mirror the existing pydantic convention (`reconciliation_models.py`, `api_models.py`) and the structured-output pattern used for `FileStructureOutput`.