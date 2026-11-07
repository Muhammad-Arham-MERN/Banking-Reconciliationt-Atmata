---
id: tasks-012-agent-limitation-email
title: agent-limitation-email-tasks
stage: tasks
date: 2026-11-07
surface: cli
model: claude-sonnet-4-5
feature: 012-agent-limitation-email
branch: 012-agent-limitation-email
user: developer
command: /sp.tasks
labels: [tasks, agent-tools, email-notification, resend, tool-limitation, frontend-notice, blue-banner, sse]
links:
  spec: specs/012-agent-limitation-email/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/012-agent-limitation-email/tasks.md
  - history/prompts/012-agent-limitation-email/tasks-012-agent-limitation-email.prompt.md
tests:
  - null
---

## Prompt

/sp.tasks

## Response snapshot

Generated specs/012-agent-limitation-email/tasks.md — 16 tasks across 6 phases, organized by the three user stories from spec.md. Setup (2): new `AGENT_LIMITATION_SUBJECT_PREFIX` / `AGENT_LIMITATION_NOTIFY_EMAIL` settings + .env.example. Foundational (3): a per-run `limitation_holder` threaded route → detect_structure → build_agent → build_agent_tools (mirroring the existing `verdict_holder` sharing). US1 (P1, 3 tasks): `send_agent_limitation_email` in notification_service.py; the `report_tool_limitation` `@tool` (validates fields + tool-anchored reason, idempotent per run, emits a live stage, sends best-effort); wire it into the returned tool list. US2 (P1, 4 tasks): optional `code` on `emit_status`; the `technical_limitation` classification branch in ai_routes.py (422 detail + marked status frame, ordinary failures unchanged); optional `code` on the frontend `ReconciliationStatusFrame`; the blue banner branch in UploadAIConfig.tsx. US3 (P2, 1 task): the reporting policy + short purpose-only `YOUR TOOLS` summary in AGENT_INSTRUCTIONS. Polish (3): constitution header/footer/crux-marker verification, the full quickstart manual pass, and a no-new-dependency + CLAUDE.md context check.

Confirmed all tasks follow the strict checklist format (`- [ ] T### [P?] [US?] … with file path`). Ran `.specify/scripts/powershell/check-prerequisites.ps1 -Json` (FEATURE_DIR + AVAILABLE_DOCS confirmed). No test tasks (standing "no tests" instruction). Same-file caution documented: ai_structure_detector.py (T003/T004/T007/T008/T013) and ai_routes.py (T005/T010) are sequential, so no [P] marker sits on two tasks sharing a file.

## Outcome

- ✅ Impact: Dependency-ordered, immediately-executable task list for 012; MVP = Setup + Foundational + US1 (the email tool).
- 🧪 Tests: None (standing "no tests" instruction); verification is the quickstart.md manual pass.
- 📁 Files: specs/012-agent-limitation-email/tasks.md
- 🔁 Next prompts: /sp.analyze for consistency, then /sp.implement (or /sp.implement directly)
- 🧠 Reflection: The only real sequencing hazard is that five tasks touch ai_structure_detector.py and two touch ai_routes.py, so the value was in naming that explicitly and withholding [P] on those rather than inflating parallelism. US2 genuinely depends on US1 (it reads the holder US1's tool writes and relies on US1's live stage frame), which the phase dependencies state up front so implementation does not try to build the notice before the tool exists.

## Evaluation notes (flywheel)

- Failure modes observed: none; check-prerequisites.ps1 ran clean (no multi-arg Join-Path). The template's sample tasks were fully replaced with feature-specific ones.
- Graders run and results (PASS/FAIL): Format validation PASS — every task has a checkbox, a sequential T-id, [P] only on different-file tasks, [US#] on all user-story tasks (and none in Setup/Foundational/Polish), and an exact file path.
- Prompt variant (if applicable): tasks-v1
- Next experiment (smallest change to try): During /sp.implement, execute US1 end-to-end first and stop to validate the email before starting US2, honoring the MVP checkpoint rather than batching all phases.
