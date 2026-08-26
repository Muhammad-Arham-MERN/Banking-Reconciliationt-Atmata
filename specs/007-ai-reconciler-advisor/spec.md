# Feature Specification: AI Reconciler Advisor ("Subh al Baqaya")

**Feature Branch**: `007-ai-reconciler-advisor`  
**Created**: 2026-08-25  
**Status**: Draft  
**Input**: User description: "Improvement of the Final Main Feature Implementation Before Production — AI Reconciler Advisor (Subh al Baqaya). After reconciliation, a button 'Reconcile With Agent' lets a chat-based agent (no tools) suggest potential discrepancies from the final discrepancies list (broken cheques/pairs and reversals only). The agent suggests, never auto-removes. Suggestions are displayed in a luxurious table with reason tooltip + Reconcile button per suggestion. User can also ask the agent questions. Agent returns a key/index so the frontend can eliminate chosen pairs from the main list. Additionally a 'What we Removed' button shows all systematically removed pairs (matching pairs, opposite-sign same-date, reversals, broken cheques) to diagnose data for a next feature. Use a new endpoint; keep the existing debit/credit convention for Bank vs Vendor."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Suggest and manually reconcile potential discrepancies (Priority: P1)

After a reconciliation completes and the final discrepancies list is shown, a user clicks **"Reconcile With Agent"**. The system sends the complete final discrepancies list — each with its date, transaction details, and signed Debit/Credit value, along with cumulative totals/balance context — to the Reconciler Agent, which analyzes it strictly for two kinds of potential discrepancies: **broken cheques/pairs** (a bank side broken into parts that sums to a company whole, e.g. +79,000 and +100,000 vs +179,000) and **reversals** (near-dated opposite-signed entries of equal magnitude, typically flagged by words like "reversal" in the transaction details). The agent returns a set of suggestions, each grouping 2+ specific discrepancy items that together form a reconcilable set, with a reason for each. The user reviews the suggestions in a dedicated panel, and for any suggestion they approve, clicks **Reconcile** to remove exactly those items from the live main discrepancies list. The agent never removes anything itself.

**Why this priority**: This is the core of the feature. Large files produce 100+ cluttered discrepancies (400+ items, e.g. vendor files), and the deterministic engine cannot see broken-cheque or reversal patterns — only the agent can, using dates, descriptions, and the cumulative totals/balance as supporting evidence. This is what makes the final list clean and beautiful.

**Independent Test**: Can be fully tested by running a reconciliation that ends with the broken-cheque scenario (bank +79,000 and +100,000, company +179,000), clicking "Reconcile With Agent", verifying the agent receives the discrepancy details with cumulative totals/balance context and returns that group as a suggestion with a reason, then clicking Reconcile on it and verifying exactly those three items disappear from the main discrepancies list while all other items remain.

**Acceptance Scenarios**:

1. **Given** a completed reconciliation with final discrepancies shown, **When** the user clicks "Reconcile With Agent", **Then** the agent receives the complete final discrepancies list (date, details, signed amount, source) and returns suggestions without removing anything from the list.
2. **Given** a broken-cheque pattern in the discrepancies (e.g. bank +79,000 and +100,000 vs company +179,000), **When** the agent analyzes the list, **Then** it returns a suggestion grouping those items with a reason indicating a broken cheque/pair.
3. **Given** a reversal pattern in the discrepancies (e.g. company −45,000 on July 19 and +45,000 on July 24, with "reversal" in a description), **When** the agent analyzes the list, **Then** it returns a suggestion grouping those items with a reason indicating a reversal.
4. **Given** an agent suggestion shown to the user, **When** the user clicks Reconcile on that suggestion, **Then** exactly the items in that suggestion are removed from the main discrepancies list and all other items remain; the agent's own output is not modified.
5. **Given** the agent returns suggestions, **When** the user dismisses or ignores them, **Then** the main discrepancies list is unchanged.

---

### User Story 2 - Ask the agent anything about the reconciliation (Priority: P2)

After the suggestions are presented, the user can keep conversing with the agent in a chat panel — asking questions about the reconciliation, the discrepancies, or the reasoning behind any suggestion — and receive answers. This is conversational in nature but remains advisory: the agent only ever suggests; only the user (via the Reconcile action) changes the list.

**Why this priority**: The user explicitly wants a chat-based model, not just a one-shot suggestion engine. It also builds trust: the user can interrogate why a suggestion exists before acting on it.

**Independent Test**: Can be fully tested by loading a reconciliation with suggestions, sending a follow-up question ("why are these three linked?"), and verifying the agent answers in context of the same discrepancies without altering the suggestions or the discrepancies list.

**Acceptance Scenarios**:

1. **Given** a completed agent session with suggestions, **When** the user sends a follow-up question, **Then** the agent answers using the same discrepancy context and does not remove or alter any items.
2. **Given** a user question unrelated to the two supported suggestion types, **When** the agent responds, **Then** it answers conversationally but does not suggest removing discrepancies outside the two defined cases.

---

### Edge Cases

- What happens when the agent returns no suggestions? The suggestions panel shows an empty state with a clear message, and the main list is unchanged.
- What happens when the agent returns a suggestion referencing a discrepancy that no longer exists (e.g. the user already reconciled it, or refreshed)? The frontend must resolve the referenced items by key, and skip/surface any suggestion whose items cannot be resolved — it must never remove unrelated items.
- What happens when the agent output cannot be parsed (malformed or empty structured output)? The system re-runs the agent; after 3 failed attempts it surfaces a clear, friendly error message to the frontend that the agent is unable to respond due to a technical failure, with no partial state.
- What happens when the model is unreachable or credentials are missing? The same retry rule applies as for malformed output: retry up to 3 attempts, then surface a friendly error message to the frontend with no partial results.
- What happens on very large files (e.g. 400+ data items, 100+ discrepancies)? The agent still receives only the complete final discrepancies list in full — never the raw file data — and the response stays within the size the frontend can parse and render.
- What happens when a broken-cheque grouping is mathematically wrong (parts don't sum to the whole, or signs don't align)? The agent's suggestion is advisory; the user is shown the reason but ultimately decides. The system never auto-applies it.
- What happens if the user reconciles two overlapping suggestions? The first Reconcile removes the items; the second suggestion's items resolve to nothing. Since every agent request sends the latest live list, a follow-up run already excludes reconciled items (root prevention); if the agent still returns a stale suggestion, the frontend hides it and informs the user those discrepancies were already reconciled.
- What happens when there are zero discrepancies? The "Reconcile With Agent" button is disabled or hidden.
- What happens when the user cancels a long agent run? The agent response streams from the model, so the user can cancel mid-stream; the existing 499/cancel-status behavior from the AI flows applies unchanged.
- What happens to suggestions when the user starts a new reconciliation? All agent state (suggestions, chat) resets; nothing carries over.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a new endpoint for the Reconciler Agent that is separate from the reconciliation endpoints, since it runs after reconciliation as an advisor. The endpoint MUST require the same authentication as the rest of the API (Bearer token via the existing auth middleware) — it is NOT exempted like `/karwai`.
- **FR-002**: The endpoint MUST accept the complete final discrepancies list — each item with its date, transaction details, and signed Debit/Credit value, plus the source (Bank or Company). The agent receives ONLY this final discrepancies list (the unmatched items shown on the frontend), never the raw file data or full transaction list. Each discrepancy item MUST carry a stable, backend-generated key assigned during reconciliation so the agent can reference exact items and the frontend can resolve them against the main list. The key is an internal identifier used for processing and resolution only — it is never rendered as part of the frontend UI.
- **FR-002b**: The endpoint MUST also accept cumulative totals/balance context alongside the discrepancy items — running totals/balances (a summed cumulative balance over the discrepancies, broken down by Bank vs Company) — so the agent can evaluate whether a candidate suggestion is mathematically worthy before returning it. The agent MUST use this cumulative totals/balance context when reasoning about suggestions, treating it as a supporting check on top of the primary signed-amount evidence (e.g. the agent should not suggest a broken-cheque group whose sums break the running totals).
- **FR-002a**: The agent MUST return its results as structured output — a typed, validated model with clearly defined fields — rather than free-form text that needs to be parsed on the frontend. The structured output MUST include a chat/text string field for simple conversational messages alongside the suggestions.
- **FR-003**: The Reconciler Agent MUST analyze the discrepancies strictly for the two supported cases only: broken cheques/pairs (a set of items on one side whose signed amounts sum to a single item of opposite sign on the other side, typically near in date) and reversals (opposite-signed items of equal magnitude near in date, with reversal language in the description used as secondary evidence). The agent MUST NOT suggest other kinds of removals.
- **FR-004**: The agent MUST use each item's date, description, and the cumulative totals/balance context as a secondary source of evaluation when forming suggestions, never as the sole basis.
- **FR-005**: The agent's output MUST be purely advisory — it MUST NOT remove, mark, or alter any discrepancy. Only the user can remove items via the frontend Reconcile action.
- **FR-006**: The agent's structured output MUST be delivered to the frontend as a typed JSON payload it can consume directly — a list of suggestions plus a chat/text string field. Any agent failure — malformed/empty structured output, or network/model errors (unreachable model, missing credentials, timeouts) — MUST be retried up to 3 attempts; if all attempts fail, the system MUST send a friendly error message to the frontend indicating the agent is unable to respond due to a technical failure, with no partial state.
- **FR-007**: Each suggestion MUST contain: the stable backend keys identifying the specific discrepancy items involved (resolvable against the main discrepancies list), the items grouped by side (Company vs Bank), and a human-readable reason (e.g. "Broken cheque by company", "Reversal checks") that reflects the mathematical check against the cumulative totals/balance context.
- **FR-008**: Users MUST be able to initiate the agent from a "Reconcile With Agent" button on the discrepancies view, and MUST be able to ask follow-up questions in a chat that carries the same discrepancy context.
- **FR-008a**: The agent chat MUST be stateless on the server: every follow-up message re-sends the CURRENT live discrepancy context (reflecting all reconciles applied so far) plus the conversation history, keyed by the reconciliation `request_id`. No server-side session store exists for the advisor chat. The agent MUST treat the latest provided context as authoritative.
- **FR-008b**: The agent MUST be instructed to respond as concisely as possible — non-creative, no unnecessary narrative; for complex topics it MAY use a short analogy, and it MAY lengthen a response only when the question requires it.
- **FR-008c**: The agent's response MUST stream from the model (token-by-token) and the user MUST be able to cancel a running agent request mid-stream; cancellation uses the existing 499/cancel-status behavior from the AI flows, unchanged.
- **FR-009**: The frontend MUST render agent suggestions in a dedicated, visually distinct panel with a heading that these are the agent's suggestions, and MUST present each suggestion as rows of items (Date, Details, signed Amount, Source) grouped under a Company vs Bank header, with the agent's reason attached, plus the chat/text message from the agent.
- **FR-010**: Against each suggestion the frontend MUST show a reason control (tooltip) and a **Reconcile** action. Clicking Reconcile MUST remove exactly the suggested items from the live main discrepancies list and leave the agent's suggestions unchanged. This removal is frontend-only (identical to the existing manual-reconcile flow) — no backend persistence beyond the existing 'Complete Reconciliation' save.
- **FR-011**: The existing debit/credit convention MUST be preserved exactly: after standardization, a negative value is a debit and a positive value is a credit for both Bank and Company, and the source of each item is its `FROM` value (Bank or Company).
- **FR-012**: The existing manual and AI reconciliation flows MUST remain fully functional and unchanged by this feature.
- **FR-013**: All agent state (suggestions, chat history) MUST reset when a new reconciliation starts, and MUST be empty on a fresh page load.

### Key Entities *(include if feature involves data)*

- **Discrepancy Item**: A final unmatched transaction shown in the results — date, transaction details, signed Debit/Credit (negative = debit, positive = credit), source (`FROM`: Bank or Company), an optional from-past flag, and a stable backend-generated key that the agent references and the frontend resolves against the main list. The key is an internal identifier — never rendered in the UI.
- **Cumulative Totals/Balance Context**: The running totals/balances computed over the final discrepancies list — a summed cumulative balance, broken down by Bank vs Company — sent to the agent alongside the discrepancy items so it can judge whether a candidate suggestion is mathematically consistent before returning it.
- **Agent Suggestion**: A group of 2+ discrepancy items that together form a reconcilable set (broken cheque/pair or reversal), each side labeled by source, with a human-readable reason and the stable backend keys resolving to the exact items in the main discrepancies list.
- **Agent Session (chat)**: The conversation between the user and the Reconciler Agent — the original suggestions plus follow-up Q&A — scoped to a single reconciliation result and reset on a new reconciliation.

### Assumptions

- The Reconciler Agent is a chat-capable model from the same model family already used by the existing AI extraction flows (consistent infrastructure and structured-output handling), configured with custom instructions and no tools; it receives the full final discrepancies list plus the cumulative totals/balance context.
- The agent's structured output is produced by the agent framework's typed structured-output support (a defined data model), not by a hand-written output parser on the frontend; malformed or empty outputs are handled gracefully.
- The agent only ever suggests; all removals are performed manually by the user through the Reconcile action.
- A new, dedicated endpoint is used (per the user's explicit requirement); the existing `/reconcile-ai` endpoint is not reused for this advisor role.
- The existing debit/credit convention is preserved: negative = debit, positive = credit after standardization; `FROM` marks the source.
- The "What we Removed" visibility feature is out of scope for this feature and will be implemented later; this feature does not capture or display removed pairs.
- Model reachability, credentials, and output-parse failures degrade gracefully via a single unified rule: any agent failure (malformed/empty output or transport/model errors) is retried up to 3 attempts, and if all attempts fail the user receives a friendly error message that the agent is unable to respond due to a technical failure (no partial results).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Reconciler Agent returns at least one correct suggestion for each of the two supported cases (broken cheque/pair and reversal) on a test reconciliation that contains them — measured by running the agent against such a reconciliation and confirming the expected groups appear.
- **SC-002**: 100% of suggestions the user chooses to reconcile remove exactly the suggested items from the main discrepancies list — no more, no fewer — verified by comparing the before/after lists.
- **SC-003**: The agent never removes, marks, or alters any discrepancy by itself — the main discrepancies list is byte-identical after an agent run that the user did not act on.
- **SC-004**: Users can complete the full flow — run the agent, review suggestions, reconcile the ones they want — without any manual editing of the final list beyond the Reconcile action; on a 400+ item / 100+ discrepancy file the suggestions panel renders without performance degradation.
- **SC-005**: 100% of agent failures — malformed/empty structured output or network/model errors (unreachable model, missing credentials, timeouts) — are handled by retrying up to 3 attempts, and after all attempts fail the user receives a clear, friendly error message (agent unable to respond due to a technical failure) with no partial state, rather than a crash.
- **SC-006**: The existing manual and AI reconciliation flows behave identically to before this feature — verified by running the same test scenarios against them.
- **SC-007**: The agent's suggestions are consistent with the cumulative totals/balance context — verified by checking that every returned suggestion's sums do not break the running Bank vs Company totals on a test reconciliation (no suggestion that contradicts the provided balance context).

## Clarifications

### Session 2026-08-26

- Q: User Story 3 duplicates User Story 2 (identical text, scenarios, and priority rationale) — how should this be resolved? → A: Remove User Story 3 entirely; User Story 2 already covers all chat follow-up scenarios, and keeping a single chat story avoids duplicating implementation and testing.
- Q: What authentication should the new advisor endpoint use? → A: Standard API authentication — Bearer token via the existing auth middleware; the endpoint is NOT exempted like `/karwai`.
- Q: Which model should the Reconciler Agent use? → A: The same model family already used by the existing AI extraction flows — consistent infrastructure and structured-output handling across the app.
- Q: Does the 3-attempt retry apply to network/model failures too, or only malformed/empty output? → A: The retry is a general rule: any agent failure — whether malformed/empty structured output or network/model errors (unreachable model, missing credentials, timeouts) — is retried up to 3 attempts; if all attempts fail, a friendly error is shown to the frontend user (no partial results).
- Q: Does the advisor endpoint support streaming, and what are its cancellation semantics? → A: The model streams its response token-by-token and the user can cancel mid-stream; cancellation uses the existing 499/cancel-status behavior from the AI flows, unchanged.
- Q: How should the agent chat conversation maintain its context across messages? → A: Stateless — each follow-up message re-sends the full discrepancy context plus the conversation history to the model; no server-side session store. The `request_id` of the reconciliation keys the conversation. Additionally, the agent MUST be instructed to respond as concisely as possible (non-creative, no unnecessary narrative); for genuinely complex topics it MAY use a short analogy, and it MAY lengthen a response only when the question requires it.
- Q: How should the stable per-discrepancy key be generated? → A: The backend assigns the stable key during reconciliation processing (e.g. sequential/dedicated id). It is used server-side for calculations and processing and is never rendered in the frontend UI; the frontend consumes it only for internal resolution/removal, not for display.
- Q: How should the full discrepancy context be handled for very large files? → A: The agent receives ONLY the final discrepancies list (the unmatched items shown to the user on the frontend) — never the entire raw file data or the full transaction list. The complete final discrepancies list is always sent in full on every request, regardless of size; there is no sampling, summarization, or chunking.
- Q: How should the frontend determine that a suggestion's items have already been reconciled (stale suggestion)? → A: (1) Prevent at the root: every agent request (initial "Reconcile With Agent" or follow-up) sends the CURRENT live discrepancies list reflecting any reconciles applied so far (e.g. after the user manually reconciles 10 of 50 items, the agent receives only the remaining 40; after reconciling 3 of 5 suggestions, it receives the updated 32). (2) Fallback: if the agent still returns a suggestion whose keys no longer exist in the current list, the frontend hides those stale suggestions and informs the user that some discrepancies sent by the agent were already reconciled. (3) The agent MUST be instructed to treat the latest provided context as authoritative.
- Q: When the user clicks Reconcile on an agent suggestion, should the removal persist to the backend immediately, or stay frontend-only? → A: Frontend-only — identical to the existing manual-reconcile flow. The removal is applied to the live frontend list; the user completes the session via the existing 'Complete Reconciliation' save button, which persists the final remaining list. No new persistence path. Any subsequent agent request naturally uses the updated frontend list as its latest context.
- Q: Should the agent receive cumulative totals/balance context in addition to the per-item date/details/amounts? → A: Yes — the endpoint sends the cumulative totals/balance (summed running balance over the discrepancies, broken down by Bank vs Company) alongside the discrepancy items, so the agent can judge whether a candidate suggestion is mathematically worthy before returning it. Balance is crucial for the overall logic and understanding of the data; the agent MUST use the cumulative totals as a supporting check on top of the primary signed-amount evidence and MUST NOT suggest a group whose sums break the running totals.

### Session 2026-08-25

- Q: How should the agent's structured output be delivered to the frontend? → A: Structured output delivered as a typed JSON payload the frontend consumes directly; the output schema additionally carries a chat/text string field for simple conversational messages (alongside the suggestions list).
- Q: How should each discrepancy item be identified so the agent's suggestion can be resolved against the main list? → A: Add a stable, backend-generated per-item key assigned during reconciliation; the agent returns these keys and the frontend removes by them.
- Q: For "What we Removed", what should be captured and where should it be shown? → A: Skip this feature entirely for now — implement it later; the "What we Removed" visibility feature and its data capture are out of scope for this feature and removed from the spec.
- Q: What happens if the agent fails to produce structured output? → A: Re-run the agent; if it still fails after 3 attempts, the system sends a friendly error message to the frontend that the agent is unable to respond due to a technical failure (no partial state). *(Superseded on 2026-08-26 by the general retry rule: any agent failure — output-shape or transport/model — is retried up to 3 attempts.)*
