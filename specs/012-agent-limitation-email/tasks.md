# Tasks: Agent Tool-Limitation Email Reporting & Blue Technical-Failure Notice

**Input**: Design documents from `/specs/012-agent-limitation-email/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: **None** — the project's standing instruction is "no tests"; verification is the manual `quickstart.md` pass. No test tasks are generated.

**Organization**: Tasks are grouped by user story (P1 → P2) so each story can be implemented and validated independently. Every new/edited file MUST carry the constitution's header (`# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ`) and footer (`# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`), with the crux marker (`# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`) on logical-critical methods (the tool, the email send, and the failure-classification branch).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1…US3 (maps to spec.md user stories); omitted in Setup/Foundational/Polish
- Exact file paths are included in every task

## Path Conventions

Web app: `backend/src/...` and `frontend/src/...` (see plan.md).

**⚠️ Same-file caution**: `backend/src/services/ai_structure_detector.py` is edited by T003, T004, T007, T008, and T013 → those MUST run sequentially. `backend/src/api/ai_routes.py` is edited by T005 and T010 → also sequential. No [P] marker is placed on any two tasks that share a file.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The two new configuration values the email needs. Nothing else is added — no dependency, no schema.

- [X] T001 [P] Add `AGENT_LIMITATION_SUBJECT_PREFIX: str = "Reconciliation Atmata"` and `AGENT_LIMITATION_NOTIFY_EMAIL: str = "arhambrowser@gmail.com"` to `backend/src/config.py` (near the existing `RESEND_*` / `COMPANY_REQUEST_NOTIFY_EMAIL` block)
- [X] T002 [P] Document `AGENT_LIMITATION_SUBJECT_PREFIX` and `AGENT_LIMITATION_NOTIFY_EMAIL` in `backend/.env.example` alongside the existing `RESEND_API_KEY` / `RESEND_FROM_EMAIL` entries

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared per-run `limitation_holder` plumbing (mirroring the existing `verdict_holder`), which BOTH the email tool (US1) and the failure classification (US2) write/read.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Add an optional `limitation_holder: Optional[dict] = None` parameter to `build_agent_tools(...)` in `backend/src/services/ai_structure_detector.py` and normalize it ONCE (`if limitation_holder is None: limitation_holder = {}`) so the same object is shared by the tool and the route (the same pattern the file already uses for `verdict_holder`)
- [X] T004 Add an optional `limitation_holder: Optional[dict] = None` parameter to `build_agent(...)` and `detect_structure(...)` in `backend/src/services/ai_structure_detector.py`, forwarding it into `build_agent_tools(...)` (default-normalized once, never `or {}` — an empty dict is falsy and would break sharing)
- [X] T005 In `reconcile_ai` (`backend/src/api/ai_routes.py`) create `limitation_holder: dict = {}` next to `register_run(request_id)` and pass it into the `detect_structure(...)` call

**Checkpoint**: The holder flows route → detect_structure → build_agent → tools; both stories can now build on it.

---

## Phase 3: User Story 1 - The agent reports a tool limitation to the Developer by email (Priority: P1) 🎯 MVP

**Goal**: The extraction agent can email the Developer a well-formed tool/engine-limitation report (issue, details, example, analogy, proposed solution + reason), subject-prefixed `Reconciliation Atmata`, best-effort, at most once per run.

**Independent Test**: Force a run the agent recognises as a genuine tool/engine limitation; confirm exactly one email to the configured inbox whose subject begins with `Reconciliation Atmata` and whose body contains all five elements; confirm a second report in the same run sends nothing.

### Implementation for User Story 1

- [X] T006 [US1] Add `send_agent_limitation_email(report: dict) -> bool` to `backend/src/services/notification_service.py`: read `settings.RESEND_API_KEY` / `RESEND_FROM_EMAIL`, lazily `import resend`, `await asyncio.to_thread(resend.Emails.send, email)`, subject `f"{settings.AGENT_LIMITATION_SUBJECT_PREFIX}: {report['tool_name']} limitation"`, recipient `settings.AGENT_LIMITATION_NOTIFY_EMAIL`, plain-text body with the ISSUE / DETAILS / EXAMPLE / ANALOGY / PROPOSED SOLUTION / WHY sections + `tool_name`/`run_id`; catch-all, log, return bool, **never raise** (per `contracts/agent-tool-contract.md` §2)
- [X] T007 [US1] Add the `report_tool_limitation(tool_name, issue, details, example, analogy, proposed_solution, reason) -> str` `@tool` to `build_agent_tools` in `backend/src/services/ai_structure_detector.py`: validate all fields non-empty and `reason` references `tool_name` (else return `"skipped: incomplete report"`, send nothing); if `limitation_holder.get("reported")` return `"skipped: already reported this run"`; otherwise set the flag + store the report, `progress_events.emit_stage(request_id, "limitation_reported", "A technical limitation was found on our side — our agent has notified the developer.", sentiment="neutral", emoji="🛠️")`, call `notification_service.send_agent_limitation_email(...)`, and return `"sent"`/`"skipped: email not sent"` — never raise (docstring per `contracts/agent-tool-contract.md` §1, including the anonymised-example and no-secrets instruction)
- [X] T008 [US1] Append `report_tool_limitation` to the returned tool list at the end of `build_agent_tools` in `backend/src/services/ai_structure_detector.py` (after `assess_structure`), confirming it closes over `request_id` (for the stage frame) and `limitation_holder` (for the flag)

**Checkpoint**: The email half works and is independently verifiable (email arrives; one-per-run holds).

---

## Phase 4: User Story 2 - The user is shown a blue "technical limitation" notice (Priority: P1)

**Goal**: A reported tool/engine limitation that fails the run is classified distinctly, so the loading screen shows a live update and the failure message renders in BLUE; every other failure keeps the existing red treatment.

**Independent Test**: Cause a tool-limitation failure → confirm the live "reported to the developer" stage and the blue, correctly-worded final error; cause an ordinary failure → confirm no blue notice and the existing red/amber path.

**Depends on**: US1 (the classification reads the holder the US1 tool writes; the live stage is emitted by the US1 tool).

### Implementation for User Story 2

- [X] T009 [US2] Extend `emit_status(request_id, state, message="", code="")` in `backend/src/services/progress_events.py` to include an optional `code` field in the emitted status frame (default empty/omitted)
- [X] T010 [US2] In the `except AIDetectionError as e` branch of `reconcile_ai` (`backend/src/api/ai_routes.py`): if `limitation_holder.get("reported")` is truthy, build `detail = {"error": "technical_limitation", "message": TECHNICAL_LIMITATION_MESSAGE, "details": {"tool_name": ..., "run_id": request_id, "retries_used": e.retries_used}}`, call `progress_events.emit_status(request_id, "error", TECHNICAL_LIMITATION_MESSAGE, code="technical_limitation")`, and raise `HTTPException(422, detail)`; otherwise keep the existing `agent_failed` / `agent_internal_error` handling exactly as-is. Define `TECHNICAL_LIMITATION_MESSAGE` (the blue, non-technical wording: technical limitation from our side / agent has sent it to the developer for improvement / please wait in the meantime) at module scope
- [X] T011 [P] [US2] Add an optional `code?: string` field to `ReconciliationStatusFrame` in `frontend/src/lib/api/aiReconciliationClient.ts` (no other client change — the error body's `detail.error` already becomes `err.code`)
- [X] T012 [US2] In `frontend/src/components/upload/UploadAIConfig.tsx`, when `errorCode === 'technical_limitation'` render the failure in a **blue** banner (`bg-blue-50 border border-blue-200 … dark:bg-blue-950/40 dark:border-blue-900`, `text-blue-800 dark:text-blue-200`) showing the blue wording, with the existing Try-again action; leave the current red block for all other error codes (FR-013)

**Checkpoint**: Both P1 stories work; a limitation failure is blue + emailed, an ordinary failure is red + silent.

---

## Phase 5: User Story 3 - The agent reports only genuine limitations, guided by a concise tool summary (Priority: P2)

**Goal**: The agent's instructions carry the reporting discipline (always report genuine tool/engine limitations, never ordinary failures) and a short, purpose-only summary of its tools so proposed solutions stay relevant.

**Independent Test**: Inspect `AGENT_INSTRUCTIONS` for the policy + purpose-only tool list; run a genuine-limitation case and an ordinary-failure case and confirm only the genuine one produces an email.

### Implementation for User Story 3

- [X] T013 [US3] Append to `AGENT_INSTRUCTIONS` in `backend/src/services/ai_structure_detector.py`: (a) the reporting policy — use `report_tool_limitation` only when the agent itself determines a genuine tool/engine limitation (or a needed new tool, with a valid tool-anchored reason); never for malformed/unsupported input, ordinary mismatches, or user error; always report when a failure is caused by a tool/engine limitation; (b) the short, purpose-only `YOUR TOOLS` list from `contracts/agent-tool-contract.md` §3 (no internal logic)

**Checkpoint**: Reporting is disciplined and the proposed solutions reference real tools.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Constitution compliance, no-dependency confirmation, and the manual end-to-end pass.

- [X] T014 Verify every new/edited file (`backend/src/config.py`, `backend/.env.example`, `backend/src/services/progress_events.py`, `backend/src/services/notification_service.py`, `backend/src/services/ai_structure_detector.py`, `backend/src/api/ai_routes.py`, `frontend/src/lib/api/aiReconciliationClient.ts`, `frontend/src/components/upload/UploadAIConfig.tsx`) carries the header + footer, with the crux marker on `report_tool_limitation`, `send_agent_limitation_email`, and the classification branch
- [X] T015 [P] Run the full `quickstart.md` manual pass (§1–§8), including the mail-outage case (`RESEND_API_KEY` blanked) and the scope checks (`/karwai` untouched; extractor partial-success stays amber) — **code-level pass done** (module imports, `report_tool_limitation` registered on the agent, fail-soft send returns `False` without raising, email body contains all five sections); the live inbox/Gmail-label and browser-rendering portions remain for the Developer's manual run
- [X] T016 [P] Confirm no new dependency was added (`resend` already present) and that `CLAUDE.md`'s 012 tech-context lines match the plan

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational.
  - **US1 (P1)** can start right after Foundational.
  - **US2 (P1)** depends on US1 (reads the holder US1's tool writes; the live stage is US1's).
  - **US3 (P2)** is independent of US1/US2 in code (own text block) but only meaningfully verifiable once US1 exists (so the agent can act on the policy).
- **Polish (Final Phase)**: Depends on all desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: after Foundational — no dependency on other stories.
- **US2 (P1)**: after Foundational + US1 (shares the `limitation_holder` and the tool-emitted stage frame).
- **US3 (P2)**: after Foundational; interacts with US1 (policy + summary printed into the same instructions the agent uses).

### Within Each Story

- Config (Setup) before the notification service and tool.
- Notification service before the tool (the tool calls it).
- The tool before wiring it into the tool list.
- The classification (T010) after the tool (T007) writes the holder.
- Frontend banner (T012) after the client type (T011).

### Parallel Opportunities

- T001 ∥ T002 (different files).
- T011 ∥ T009/T010 (different files, frontend vs backend).
- T015 ∥ T016 (independent verifications).
- **Not parallel**: T003/T004/T007/T008/T013 (all `ai_structure_detector.py`) and T005/T010 (both `ai_routes.py`).

---

## Parallel Example: User Story 2

```bash
# Different-file tasks that can run together once Foundational + US1 are done:
Task: "T009 Extend emit_status with optional code in backend/src/services/progress_events.py"
Task: "T011 Add code?: string to ReconciliationStatusFrame in frontend/src/lib/api/aiReconciliationClient.ts"

# Then sequentially (same files):
Task: "T010 Classify technical_limitation in backend/src/api/ai_routes.py"
Task: "T012 Render the blue notice in frontend/src/components/upload/UploadAIConfig.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 + its Foundational prerequisites)

1. Complete Phase 1: Setup (T001–T002).
2. Complete Phase 2: Foundational (T003–T005) — CRITICAL.
3. Complete Phase 3: US1 (T006–T008).
4. **STOP and VALIDATE**: confirm the email arrives with the `Reconciliation Atmata` subject, all five body elements, and one-per-run.
5. This alone delivers the Developer's core ask (agent → email).

### Incremental Delivery

1. Setup + Foundational → holder plumbing ready.
2. US1 → the email tool works (MVP) → validate.
3. US2 → the blue user notice + classification → validate (blue vs red).
4. US3 → reporting discipline + tool summary → validate (genuine vs ordinary).
5. Polish → constitution markers, no-dependency check, full quickstart.

### Notes

- **No tests** per the standing instruction; each story's Independent Test maps to a `quickstart.md` section.
- No new dependency, no persistence, no migration.
- Scope held to the AI `/reconcile-ai` flow; `/karwai` and the deterministic extractors are untouched (T015 checks this).
