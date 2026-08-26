---
id: clarify-007-ai-reconciler-advisor
title: ai-reconciler-advisor-spec-clarify
stage: spec
date: 2026-08-26
surface: cli
model: claude-sonnet-5
feature: 007-ai-reconciler-advisor
branch: 007-ai-reconciler-advisor
user: developer
command: /sp.clarify
labels: [spec, clarify, ai, reconciliation, agent, advisor, subh-al-baqaya]
links:
  spec: specs/007-ai-reconciler-advisor/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-ai-reconciler-advisor/spec.md
tests:
  - null
---

## Prompt

Run /sp.clarify on the latest 007 spec (specs/007-ai-reconciler-advisor/spec.md). Identify underspecified areas in the AI Reconciler Advisor feature and ask up to 5 highly targeted clarification questions, encoding the answers back into the spec.

## Response snapshot

Two clarify rounds were run on this spec (both 2026-08-26, same Session heading in the spec).

**Round 1** (previous run, 5 questions): (1) chat is stateless with full context per message, keyed by request_id, agent responds concisely/non-creatively; (2) the stable per-discrepancy key is backend-generated during reconciliation and never rendered in the frontend UI; (3) the agent receives ONLY the final discrepancies list in full on every request, never raw file data, no sampling/chunking; (4) stale-suggestion prevention is root-first (every request sends the CURRENT live list) plus a hide-and-notify fallback, agent treats latest context as authoritative; (5) agent Reconcile is frontend-only, identical to the existing manual-reconcile flow, no new backend persistence.

**Round 2** (this run, 5 questions, one at a time, each integrated immediately): (1) User Story 3 was a byte-identical duplicate of User Story 2 — removed entirely to avoid duplicating implementation and testing; (2) the new advisor endpoint MUST use standard Bearer-token auth via the existing auth middleware — NOT exempted like `/karwai` (FR-001 updated); (3) the Reconciler Agent uses the same model family as the existing AI extraction flows for consistent infrastructure and structured-output handling (Assumptions updated); (4) the 3-attempt retry is a GENERAL rule covering any agent failure — malformed/empty output AND network/model errors (unreachable model, missing credentials, timeouts) — then a friendly error surfaces with no partial state (FR-006, Edge Cases, Assumptions, SC-005 updated); (5) the model STREAMS its response token-by-token and the user can cancel mid-stream, using the existing 499/cancel-status behavior unchanged (new FR-008c, Edge Case updated). One prior bullet from Session 2026-08-25 was marked superseded by the general retry rule.

## Outcome

- ✅ Impact: 10 clarifications resolved across two rounds (5 + 5) and integrated into the spec; round 2 removed a duplicated user story, locked endpoint auth, fixed the model family, unified the retry rule to cover transport failures, and added streaming/cancellation semantics.
- 🧪 Tests: None run (clarification stage only).
- 📁 Files: specs/007-ai-reconciler-advisor/spec.md
- 🔁 Next prompts: /sp.plan for 007-ai-reconciler-advisor (or /sp.tasks if already planned)
- 🧠 Reflection: Grounding the questions in the actual backend (via parallel exploration) made the clarifications high-impact: the current frontend itemId is index-based and shifts after removal, so a backend-generated stable key was the right call; the existing reconciliation state is ephemeral React state, so frontend-only reconcile persistence matches the architecture; and the stateless full-context chat avoids inventing a session store the codebase has no pattern for.

## Evaluation notes (flywheel)

- Failure modes observed: None blocking; the user supplied multi-part answers with additional nuance (e.g. concise-response instruction, hide-and-notify fallback) that required encoding all sub-parts faithfully.
- Graders run and results (PASS/FAIL): Spec validation PASS — exactly one bullet per accepted answer, ≤5 questions, no lingering placeholders, markdown structure valid, terminology consistent.
- Prompt variant (if applicable): clarify-v1
- Next experiment (smallest change to try): None pending — spec ready for /sp.plan.
