# Phase 0 Research: Agent Tool-Limitation Email Reporting & Blue Technical-Failure Notice

**Feature**: `012-agent-limitation-email` | **Date**: 2026-11-07 | **Plan**: [plan.md](./plan.md)

This document resolves every open question in the plan's Technical Context. No
`[NEEDS CLARIFICATION]` remains after it.

---

## D1 — Where the email tool lives and how it reaches the agent

**Decision**: Add one function tool, `report_tool_limitation`, inside the existing
`build_agent_tools(...)` in `backend/src/services/ai_structure_detector.py`, and return it
from that function alongside `judge_structure_by_cover`, `read_excel`, `read_pdf`,
`read_pdf_words`, `assess_structure`. The agent therefore receives it as a first-class SDK
tool with no change to `build_agent`'s `Agent(...)` construction beyond the tool list.

**Rationale**: `build_agent_tools` is already the single place the agent's tools are created
and closed over the per-request file paths; the SDK's `@tool` decorator derives the tool
schema from the function signature + docstring, so the agent gets a typed, self-describing
tool for free. This mirrors how every existing tool is wired.

**Alternatives considered**: (a) A separate "reporter" agent the main agent calls — heavier,
and the spec wants the *detection agent itself* to report (Q1); (b) a plain Python callback
registered elsewhere — the agent cannot invoke a non-tool, so this fails the core requirement.

---

## D2 — How the agent's determination reaches the backend so the failure can be classified

**Decision**: Thread a per-run shared `limitation_holder: dict` from the route
(`ai_routes.reconcile_ai`) into `detect_structure(...)` → `build_agent(...)` →
`build_agent_tools(...)`, exactly the way the existing `verdict_holder` is shared between the
`assess_structure` tool and the output guardrail. The `report_tool_limitation` tool writes the
report into the holder (and sets a `reported` flag for idempotency); the route reads the holder
in its failure path.

**Rationale**: The route already owns a per-request lifecycle and already passes a shared
holder (`verdict_holder`) through this exact channel; reusing it is the smallest, most
consistent change. It keeps the classification per-run and thread-safe (the SDK runs sync tools
in worker threads — a plain dict write is what the existing guardrail/holder already relies on).

**Alternatives considered**: (a) A module-level global keyed by request id — needs its own
lifecycle and cleanup, duplicating what the holder gives for free; (b) inferring the
limitation from log text in the route — brittle and indirect.

---

## D3 — Surfacing the limitation to the user's loading screen and failure message

**Decision**: Two coordinated signals, both on infrastructure that already exists:
1. **Live, during processing**: the tool calls `progress_events.emit_stage(request_id, ...)`
   with a neutral "technical limitation found / reported to the developer" message, so the
   loading overlay's live feed and gauge reflect it (FR-011).
2. **At failure**: the route classifies the failed run and (a) returns a JSON error body with
   `error: "technical_limitation"` and the user-facing message (FR-012), and (b) emits the
   terminal SSE `status` frame carrying the same marker (via a new optional `code` on
   `emit_status`).

**Rationale**: The frontend already streams stage frames over SSE and already keys its error
banner off the HTTP error body's `detail.error` (`err.code` in `UploadAIConfig.handleSubmit`).
So the blue banner needs no new transport — only a new error code and one new rendering branch.
The extra `code` on the status frame keeps the overlay honest if it is the last thing to settle.

**Alternatives considered**: (a) A new dedicated endpoint/poll for "was a limitation
reported?" — unnecessary; the error body and the SSE stream already carry the answer;
(b) encoding the notice purely in the free-text message and having the frontend string-match —
fragile, so a structured `error` code is used instead.

---

## D4 — Email transport, fail-soft behaviour, and delivery semantics

**Decision**: Add `send_agent_limitation_email(report: dict) -> bool` to
`backend/src/services/notification_service.py`, following the exact pattern of the existing
`send_company_request_notification`: read `settings.RESEND_API_KEY` / `RESEND_FROM_EMAIL`,
lazily `import resend`, `await asyncio.to_thread(resend.Emails.send, email)`, catch everything,
log, and return a bool — **never raise**.

**Rationale**: This is the Developer-requested "Resend API tool" (spec Input), and the repo
already has a proven, fail-soft Resend sender. Reusing its shape guarantees a mail outage cannot
change the reconciliation outcome (FR-005) and requires no new dependency.

**Alternatives considered**: (a) SMTP/`sendgrid` — a new dependency and a different provider
than the one already configured and requested; (b) raising on send failure — violates FR-005.

---

## D5 — Subject, recipient, and the "Reconciliation Atmata" Gmail label

**Decision**: New settings in `backend/src/config.py`:
`AGENT_LIMITATION_NOTIFY_EMAIL: str = "arhambrowser@gmail.com"` and a
`AGENT_LIMITATION_SUBJECT_PREFIX: str = "Reconciliation Atmata"`. The subject is
`f"{prefix}: {tool_name} limitation"` (prefix first, so the Gmail rule matches), and the
recipient falls back to the default when the setting is blank. The existing
`RESEND_API_KEY` / `RESEND_FROM_EMAIL` are reused as-is.

**Rationale**: The Developer created a Gmail rule keyed on the subject starting with
"Reconciliation Atmata"; making it a constant keeps the wire format exact and testable
(FR-002). A dedicated recipient setting (rather than reusing `COMPANY_REQUEST_NOTIFY_EMAIL`)
keeps the two notification streams independent while defaulting to the same inbox.

**Alternatives considered**: (a) Hardcoding the address/prefix in the service — contradicts the
project's env-driven config pattern; (b) reusing `COMPANY_REQUEST_NOTIFY_EMAIL` — couples two
unrelated notifications.

---

## D6 — When the agent may report, and how loudly

**Decision**: `AGENT_INSTRUCTIONS` gains a short, explicit reporting policy: use
`report_tool_limitation` **only** when the agent itself determines the failure is a genuine
limitation/defect of its tools or engine, or when it is confident a new tool is needed — with a
stated, tool-anchored reason. It must **not** report ordinary failures (malformed/unsupported
input, ordinary mismatches, user error). The tool is idempotent per run (the holder's flag), so
multiple discoveries still yield one email.

**Rationale**: FR-007/FR-008 require the always-when-genuine / never-when-ordinary discipline,
and FR-006 caps it at one email per run. An instruction-level policy plus a mechanical
one-per-run guard is the smallest way to hold that line.

**Alternatives considered**: (a) A separate classifier step — over-engineered for a
single-agent decision the spec explicitly assigns to the agent; (b) no idempotency guard —
would let a retried attempt or a multi-limit run spam the inbox.

---

## D7 — What the agent knows about its tools (the purpose summary)

**Decision**: Append to `AGENT_INSTRUCTIONS` a very short, purpose-only list — one line per
tool, describing *what it is for* and nothing about how it works:
`judge_structure_by_cover` (recall a known bank/vendor's stored structure), `read_excel`
(read Excel rows), `read_pdf` (read PDF table rows), `read_pdf_words` (read word
geometry/column positions of the first two pages), `assess_structure` (score a proposed
structure). The agent is told to keep its proposed solutions consistent with these purposes.

**Rationale**: FR-009 — the Developer asked for "a very short and precise summary of what its
tools are made of, not the logic". Keeping it purpose-only both satisfies the requirement and
avoids leaking internals into a message that leaves the system.

**Alternatives considered**: (a) Dumping the tool docstrings/code — too long and logic-leaking;
(b) omitting it — the spec requires it, and it is what makes proposed solutions relevant.

---

## D8 — Data safety in the report (no secrets, no raw financial rows)

**Decision**: The email body is composed from the agent-supplied structured fields only
(`issue`, `details`, `example`, `analogy`, `proposed_solution`, `reason`, `tool_name`, plus
run/file metadata). The tool's docstring instructs the agent to pass an **anonymised /
structural** example (column names, layout, the nature of the failure) and the service never
echoes request headers, environment, or file contents. `run_id` (the request id) is included for
correlation.

**Rationale**: FR-015 forbids secrets unconditionally; FR-016 (Q2 = A) permits technical detail
plus an anonymised/structural example but no raw rows, account numbers, or balances. Composing
from validated fields (never free-form file dumps) is the enforceable version of that rule.

**Alternatives considered**: (a) Attaching the failing file — explicitly out of scope and a
privacy hazard; (b) letting the agent paste rows into `example` — mitigated by the docstring
instruction (documented residual risk; a stricter redaction pass is a possible future
experiment).

---

## D9 — Scope boundary: the AI flow only

**Decision**: The tool is added to the AI detection agent and the classification/notice live on
`/reconcile-ai` only. The deterministic `/karwai` path and the deterministic extractors
(`ai_pdf_processor`, `ai_excel_processor`) are untouched: a partial-success caused by those
extractors is **not** an agent tool/engine limitation (no agent is involved), so it keeps its
current behaviour and is not re-coloured blue.

**Rationale**: Q1 = A — the Developer confirmed the agent itself detects and reports, i.e. the
AI flow. `/karwai` has no agent to write or send such a report.

**Alternatives considered**: (a) Extending to the deterministic engine — no agent exists there
to compose the issue/example/analogy, and the spec (and Q1) exclude it; (b) also colouring
extractor partial-failures blue — conflates a different cause and dilutes the "this one is on
us *technically*" meaning of blue.

---

## D10 — Why no persistence and no new dependency

**Decision**: Persist nothing; add no package. The report is delivered as an email and recorded
in logs; the classification lives only in the request's in-memory holder.

**Rationale**: The spec introduces no stored entity (its Key Entities are transient), and the
`resend` SDK plus the SSE bus already exist. This keeps the change small, avoids a migration,
and respects Gate II (stack authority).

**Alternatives considered**: (a) A `tool_limitation_reports` table — not required by any FR, and
the Developer wants the report in the inbox; (b) a new email SDK — violates Gate II.

---

## Consolidated decisions

| # | Decision | Primary FRs |
|---|----------|-------------|
| D1 | `report_tool_limitation` function tool in `build_agent_tools` | FR-001, FR-003 |
| D2 | Shared per-run `limitation_holder` threaded from the route | FR-010 |
| D3 | SSE stage frame + `technical_limitation` error code | FR-011, FR-012, FR-013 |
| D4 | `send_agent_limitation_email` reuse of the Resend pattern, fail-soft | FR-005 |
| D5 | Subject prefix + recipient settings | FR-002 |
| D6 | Reporting policy in instructions + one-email-per-run guard | FR-006, FR-007, FR-008 |
| D7 | Short purpose-only tool summary in instructions | FR-009 |
| D8 | Compose from validated fields; anonymised example; no secrets/raw rows | FR-015, FR-016 |
| D9 | AI flow only; deterministic path untouched | FR-010 |
| D10 | No persistence, no new dependency | — (Gate II) |
