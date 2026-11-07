# Phase 1 Data Model: Agent Tool-Limitation Email Reporting & Blue Technical-Failure Notice

**Feature**: `012-agent-limitation-email` | **Date**: 2026-11-07 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

This feature introduces **no persisted data**. Every entity below is transient — it exists in
memory for the duration of one reconciliation run, or as the delivered email. There is no
table, migration, or file store.

---

## Entity 1 — Tool Limitation Report

The structured content the agent assembles when it decides a failure is a genuine tool/engine
limitation. It is the payload of the notification email and the object recorded on the per-run
holder.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `tool_name` | string | Yes | agent | The tool the limitation concerns (one of the five agent tools, or `engine`). Anchors the proposed solution (FR-004, FR-009). |
| `issue` | string | Yes | agent | One-line statement of the problem/limitation (FR-003a). |
| `details` | string | Yes | agent | What was attempted, where it failed, the observed error (FR-003b). |
| `example` | string | Yes | agent | A concrete, **anonymised / structural** example of the problem (FR-003c, FR-016). |
| `analogy` | string | Yes | agent | A plain-language analogy explaining the issue (FR-003d). |
| `proposed_solution` | string | Yes | agent | The tool upgrade or new tool the agent believes is needed (FR-003e). |
| `reason` | string | Yes | agent | Why the upgrade/new tool is needed, tied to the named tool (FR-003e, FR-007). |
| `run_id` | string | Yes | system (route/request id) | Correlates the report with the failing run (FR-004). |
| `file_type` / `stage` | string | No | agent/system | e.g. `pdf`/`excel`, `structure_detection` (FR-004). |
| `created_at` | ISO-8601 string | Yes | system | When the report was composed. |

**Validation rules (from the FRs)**

- All seven agent fields must be non-empty before an email is composed; a report missing the
  `reason` or the `tool_name` is **not** sent (FR-003e, FR-007).
- The composed email body must contain all five required elements — issue, details, example,
  analogy, proposed solution — verified in the send path (FR-003, SC-002).
- `example` must be a structural/anonymised description; raw rows, account numbers, and balances
  are disallowed (FR-016).
- No field may contain secrets — credentials, API keys, tokens, connection strings (FR-015).
- At most one report per run reaches the send path (FR-006).

**Lifecycle**

```text
(agent detects genuine tool/engine limitation and CALLS report_tool_limitation)
        │
        ▼
recorded on the per-run holder (holder["reported"] = True)          [FR-010]
        │
        ├─(invalid / missing tool-anchored reason)──► no email sent (logged)   [FR-003e, FR-007]
        │
        └─(valid)──► handed to send_agent_limitation_email()   (best-effort)   [FR-005]
        │
        ▼
RAISE ToolLimitationReported → the RUN STOPS: no LLM retries, no guardrail   [FR-006]
re-run; detect_structure turns it into a terminal AIDetectionError
```

---

## Entity 2 — Limitation Notification Email

The delivered message. Transient: it is not stored by this feature; only its delivery outcome
is logged.

| Field | Value | Rule |
|-------|-------|------|
| `from` | `settings.RESEND_FROM_EMAIL` | Existing verified sender (reused). |
| `to` | `settings.AGENT_LIMITATION_NOTIFY_EMAIL` (default `arhambrowser@gmail.com`) | The Developer's inbox (FR-001). |
| `subject` | `f"{AGENT_LIMITATION_SUBJECT_PREFIX}: {tool_name} limitation"` where the prefix is `Reconciliation Atmata` | **Must begin with `Reconciliation Atmata`** so the Gmail rule files it (FR-002). |
| `text` (body) | Sectioned: issue · details · example · analogy · proposed solution + reason · context (tool, file/stage, run id) | All five elements present (FR-003, FR-004). |
| delivery outcome | `sent` / `skipped` (no key/sender) / `failed` | Logged; never raised (FR-005). |

**Invariants**

- The send is **best-effort**: a skipped or failed send leaves the reconciliation outcome, the
  run, and the user-facing behaviour unchanged (FR-005, SC-004).
- The subject prefix is credential-free and information-only — no secrets travel in the subject
  or body (FR-002, FR-015).
- The body is composed from the validated report fields; it never attaches or dumps the user's
  file (FR-016).

---

## Entity 3 — Technical-Limitation Failure Signal

The classification the route attaches to a failed run when the holder recorded a report. It is
what drives the blue user notice and distinguishes a limitation failure from an ordinary one.

| Field | Location | Value | Rule |
|-------|----------|-------|------|
| `reported` (holder flag) | per-run `limitation_holder` dict | `True` once a report is recorded | Idempotency + classification input (FR-006, FR-010). |
| `error` code | HTTP 422 `detail.error` | `"technical_limitation"` | Only when `reported` is set on a failed run (FR-010, FR-013). |
| `message` | HTTP 422 `detail.message` + SSE status frame | The blue notice wording: there is a technical limitation from our side, the agent has sent it to the developer for improvement, please wait in the meantime | User-facing, non-technical, jargon-free (FR-012, FR-014). |
| status frame `code` | SSE terminal `status` frame | `"technical_limitation"` (new optional field) | Lets the overlay reflect the same classification (FR-011). |
| live stage | SSE `stage` frame emitted by the tool | A neutral "limitation found / reported to the developer" message | Shown while processing (FR-011). |

**State transitions**

```text
run start ──► holder.reported = False
   │
   ├─ tool reports ──► holder.reported = True  (+ live stage frame)
   │
   ├─ run SUCCEEDS ──► no blue notice; existing success/partial handling unchanged
   │                   (an email may still have been sent for a reported limitation)
   │
   └─ run FAILS (AIDetectionError)
            ├─ holder.reported = True  ──► error code = "technical_limitation" ──► BLUE notice
            └─ holder.reported = False ──► existing agent_failed / agent_internal_error ──► RED
```

**Invariants**

- `technical_limitation` is emitted **only** for failures of the AI agent's own tools/engine
  (FR-010); deterministic `/karwai` failures and extractor partial-failures never produce it
  (D9).
- Ordinary failures keep the existing red treatment — the blue colour is exclusive to this
  signal (FR-013).
- The notice never blocks retry or navigation (FR-014).

---

## Entity 4 — Tool Purpose Summary

The short, purpose-only description of the agent's tools, supplied in the agent's instructions.

| Item | Purpose (what it is for — never how it works) |
|------|-----------------------------------------------|
| `judge_structure_by_cover` | Recall a known bank/vendor's stored PDF structure. |
| `read_excel` | Read rows from the Excel ledger. |
| `read_pdf` | Read table rows from the PDF statement. |
| `read_pdf_words` | Read word geometry (column positions) of the first two pages. |
| `assess_structure` | Score a proposed structure against the statement. |
| `report_tool_limitation` | (New) Email the Developer about a tool/engine limitation or a needed new tool. |

**Rules (FR-009)**

- Purpose only — the summary MUST NOT describe internal logic or implementation.
- It lives in the agent's instructions (its working context), not as a user-facing surface.
- Its purpose is to keep the agent's proposed solutions relevant to the tools that exist.

---

## Relationships

```text
Reconciliation run ──1:0..1──► Tool Limitation Report        (at most one per run, FR-006)
Tool Limitation Report ──1:1──► Limitation Notification Email (unless send is skipped/failed)
Reconciliation run ──1:0..1──► Technical-Limitation Failure Signal (only on a failed run)
Tool Purpose Summary ──guides──► Tool Limitation Report.proposed_solution
```

## Explicit non-entities

- **No database table / migration** — nothing is persisted (D10).
- **No stored limitation history** — the report lives in the inbox, not the app.
- **No user-facing "report list"** — the user only sees the blue notice.
