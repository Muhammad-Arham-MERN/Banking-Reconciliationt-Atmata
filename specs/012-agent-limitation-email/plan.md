# Implementation Plan: Agent Tool-Limitation Email Reporting & Blue Technical-Failure Notice

**Branch**: `012-agent-limitation-email` | **Date**: 2026-11-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-agent-limitation-email/spec.md`

## Summary

Give the AI extraction agent a function tool that emails the Developer when the agent itself determines a failure is caused by a limitation or defect of its own tools/engine (or that a new tool is required) — a subject-prefixed ("Reconciliation Atmata") Resend message to `arhambrowser@gmail.com` carrying the issue, details, an example, an analogy, and a proposed solution with a reason. The tool is best-effort (never fails the run) and is reported at most once per run. When such a limitation is reported and the run ultimately fails, the backend classifies the failure as a technical limitation (`technical_limitation`) instead of an ordinary one, and the frontend renders the failure for the user as a clearly **blue** notice stating the limitation is on our side, the agent has sent it to the developer, and to please wait — while ordinary failures keep their existing red treatment. The agent is also given a short, purpose-only summary of its tools so its proposed solutions stay relevant. Scope is the AI `/reconcile-ai` flow only; the agentless deterministic `/karwai` path is untouched. No new dependency — the existing Resend integration and the existing SSE progress bus are reused.

## Technical Context

**Language/Version**: Python `>=3.13` (backend, FastAPI); TypeScript `^5` on Next.js `16.2.9` / React `19.2.4` App Router (frontend)
**Primary Dependencies**: Backend — `openai-agents[litellm]` (the `Agent`/`Runner`/`@tool` SDK the detector already uses), FastAPI, pydantic v2, pandas/pdfplumber — all existing; the **existing `resend` SDK** is reused through `notification_service.py`, so **no new package** is added. Frontend — Next.js App Router, shadcn `base-nova` on Base UI, Tailwind v4, lucide-react — all existing, **no additions**.
**Storage**: **N/A** — this feature persists nothing. The limitation report exists only as the delivered email plus log entries; there is no new table, file, or cache.
**Testing**: None — per the project's standing "no tests" instruction. Verification is the manual pass in quickstart.md.
**Target Platform**: Local dev — `uvicorn` backend + Next.js frontend (no deployment required).
**Project Type**: Web application (`backend/` + `frontend/`).
**Performance Goals**: The limitation tool must not perceptibly slow the agent run — the Resend send runs off the event loop (`asyncio.to_thread`, mirroring `notification_service.py`) and is fire-and-log; the classification adds no measurable work to the failure path.
**Constraints**: No ORM; every new/edited backend and frontend file carries the constitution's بسم الله header and وَإِنَّ اللَّهَ footer with the وَهُوَ crux marker on key methods; **no new dependency**; the email send must be best-effort and must never alter, abort, or block the run (FR-005); at most **one** email per failing run (FR-006); the classification and blue notice MUST apply **only** to the AI agent's own tool/engine limitations (FR-010) and MUST include **no** secrets and **no** raw financial rows (FR-015/FR-016); the existing red error treatment for ordinary failures must be preserved (FR-013).
**Scale/Scope**: Single-developer tool. A handful of genuine limitation reports over the app's lifetime; one email per failing run; one blue notice per failure.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate I — Strict Instruction Following**: The plan implements the spec (FR-001…FR-016) with nothing beyond it — one message tool, one classification, one user notice. PASS.
- **Gate II — Developer Stack Authority**: **No new dependency is introduced.** The email reuses the `resend` SDK the Developer already requested and that already powers `notification_service.py`; the tool uses the `@tool` decorator the detector already uses; the notice rides the existing SSE bus. PASS.
- **Gate III — Supervised Collaboration / V — Controlled Creativity**: The tool, the limitation classification, and the blue notice are direct implementations of explicit requirements, not novel inventions. PASS.
- **Gate VI — Ambiguity Resolution**: Both clarifications were resolved in `/sp.specify` (Q1 scope = AI agent's own tools/engine, agent-detected and agent-reported; Q2 data = technical detail + anonymised/structural example only). No `[NEEDS CLARIFICATION]` remain. PASS.
- **Code Standards 1–3**: File header + footer, with the وَهُوَ crux marker on the notification function, the tool, and the failure-classification branch. Enforced as a cross-cutting task in `/sp.tasks`. PASS (must remain enforced).
- **No-tests policy**: Honored — no test suites are added. PASS.

No violations → Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/012-agent-limitation-email/
├── plan.md                          # This file
├── research.md                      # Phase 0 output — design decisions + rationale
├── data-model.md                    # Phase 1 output — report/email/signal entities
├── quickstart.md                    # Phase 1 output — manual verification run-through
├── contracts/                       # Phase 1 output
│   ├── agent-tool-contract.md       # the report_tool_limitation tool schema + email contract
│   └── reconcile-ai-limitation.yaml # HTTP error detail + SSE frame extension (technical_limitation)
└── tasks.md                         # Phase 2 output (/sp.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/src/
├── api/
│   └── ai_routes.py                     # EDIT: pass a limitation holder into detect_structure;
│                                        #   classify a failed run as technical_limitation (422 detail
│                                        #   + SSE status/stage marker) when the holder recorded one
├── services/
│   ├── ai_structure_detector.py         # EDIT: AIDetectionError.technical_limitation; new
│   │                                    #   report_tool_limitation tool; limitation holder param
│   │                                    #   threaded through detect_structure/build_agent/
│   │                                    #   build_agent_tools; AGENT_INSTRUCTIONS gains the reporting
│   │                                    #   guidance + the short tool-purpose summary
│   ├── notification_service.py          # EDIT: send_agent_limitation_email(report) — Resend,
│   │                                    #   best-effort, subject prefixed "Reconciliation Atmata"
│   └── progress_events.py               # EDIT: emit_status gains an optional `code` so the
│                                        #   terminal frame can carry "technical_limitation"
└── config.py                            # EDIT: AGENT_LIMITATION_NOTIFY_EMAIL (default
                                         #   arhambrowser@gmail.com) + subject-prefix constant

frontend/src/
├── lib/api/aiReconciliationClient.ts    # EDIT: ReconciliationStatusFrame gains optional `code`
├── components/upload/UploadAIConfig.tsx  # EDIT: blue technical-limitation banner (errorCode ===
│                                        #   'technical_limitation'); existing red path untouched
└── types/reconciliation.types.ts        # (no change — error codes are untyped strings today)
```

**Structure Decision**: Existing web layout (`backend/` FastAPI + `frontend/` Next.js App Router). No new modules, projects, or dependencies. The tool is another closure in the detector's existing `build_agent_tools`; the email is another function beside the existing Resend sender; the notice is a new branch in the existing error banner. The per-run state needed to classify the failure is threaded through the same channel the guardrail verdict already uses (a shared holder dict).

## Complexity Tracking

> No constitution violations. Nothing to justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Design Highlights (detail in research.md)

- **The tool (FR-001…FR-004, FR-006, FR-009)**: a `report_tool_limitation` function tool added to `build_agent_tools` and thus available to the detection agent. It takes structured fields (`tool_name`, `issue`, `details`, `example`, `analogy`, `proposed_solution`, `reason`), sends the email, records the report on the shared per-run `limitation_holder`, emits a live stage frame, and returns a short acknowledgement. A holder flag makes it idempotent per run.
- **The email (FR-002, FR-003, FR-015, FR-016)**: `notification_service.send_agent_limitation_email(report)` reuses the existing Resend pattern (lazy import, `asyncio.to_thread`, never raises), with a subject beginning `Reconciliation Atmata` and a body that lays out the five required elements. It refuses to compose if the report carries no valid, tool-anchored reason, and it never includes secrets or raw financial rows.
- **The classification (FR-010, FR-013)**: the route creates the holder and passes it to `detect_structure`; when the run fails with `AIDetectionError` **and** the holder recorded a limitation, the route returns a `technical_limitation` error detail and marks the SSE status frame; otherwise it keeps the existing `agent_failed` / `agent_internal_error` handling unchanged.
- **The blue notice (FR-011, FR-012, FR-013, FR-014)**: the SSE stage frame shows the live "limitation occurred, reported to the developer" update during processing; on failure the frontend keys on `errorCode === 'technical_limitation'` to render the blue banner (the module's existing `bg-blue-50 … text-blue-800` convention) with the required wording, leaving every other failure on the red path.
- **The tool summary (FR-009)**: `AGENT_INSTRUCTIONS` gains a short, purpose-only list of the agent's tools (judge_structure_by_cover, read_excel, read_pdf, read_pdf_words, assess_structure) plus the reporting guidance — no internal logic.
