# Quickstart: Agent Tool-Limitation Email Reporting & Blue Technical-Failure Notice

**Feature**: `012-agent-limitation-email` | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

A manual verification pass. **No automated tests** — this is the whole verification (project's
standing "no tests" instruction).

---

## 0. Prerequisites

- Backend running (`uvicorn`) and frontend running (`npm run dev`), signed in with a granted
  employee account so `/upload-ai` is reachable.
- `backend/.env` contains a valid `RESEND_API_KEY` and a verified `RESEND_FROM_EMAIL`.
- Optionally set `AGENT_LIMITATION_NOTIFY_EMAIL` (defaults to `arhambrowser@gmail.com`).
- Access to the inbox that receives the mail (and its **Reconciliation Atmata** Gmail label/rule).
- A PDF/Excel pair that you can make fail on the agent side, plus a normal pair that succeeds.

---

## 1. Happy-path regression (nothing regressed)

1. Upload a normal valid pair via `/upload-ai` and submit.
2. Confirm the loading overlay streams its usual stages and the results appear as before.
3. Confirm **no** blue notice appears and **no** limitation email is sent.

- [ ] Normal reconciliation still succeeds exactly as before (FR unchanged).

---

## 2. The agent reports a genuine tool/engine limitation

Trigger a run the agent recognises as a limitation of its own tools/engine (e.g. a statement the
agent's tools genuinely cannot structure even after its assessor retries).

1. Submit the run.
2. Watch the loading overlay's live feed: a **"limitation reported to the developer"** stage
   should appear (FR-011).
3. Let the run fail.
4. Open the receiving inbox.

- [ ] An email arrived at the configured address (default `arhambrowser@gmail.com`) — FR-001.
- [ ] Its **subject begins with `Reconciliation Atmata`** — FR-002.
- [ ] It is filed under the **Reconciliation Atmata** Gmail label (the Developer's rule) — FR-002.
- [ ] The body contains **all five** elements: issue, details, example, analogy, proposed
      solution (with the reason) — FR-003.
- [ ] The body names the **tool(s)** involved and the run id — FR-004.
- [ ] The example is **anonymised/structural** — no raw rows, account numbers, or balances — FR-016.
- [ ] The body contains **no** credentials, API keys, or tokens — FR-015.

---

## 3. The user sees the blue technical-limitation notice

On the same failed run from §2 (or a repeat):

- [ ] After failure, the error message is rendered **in blue** — FR-012.
- [ ] Its wording states: there is a technical limitation from our side, the agent has sent the
      limitation to the developer for improvement, and to please wait in the meantime — FR-012.
- [ ] The message is non-technical (no stack traces or jargon) and does not block retry or
      navigation — FR-014.
- [ ] Clicking **Try again** returns to a usable form.

---

## 4. Ordinary failures stay red (no false blue)

Cause a failure that is **not** a tool/engine limitation — e.g. an invalid/corrupt file, or a run
that fails without the agent reporting a limitation.

- [ ] The failure is shown with the **existing red** treatment (or the existing partial/amber
      path for an extractor-side partial failure) — FR-013.
- [ ] **No** blue notice appears — FR-013.
- [ ] **No** limitation email is sent — FR-008.

---

## 5. One email per run (no spam)

Trigger a run where the agent could notice more than one issue, or that retries internally.

- [ ] At most **one** limitation email arrives for that run — FR-006.

---

## 6. Best-effort delivery (mail outage cannot break the app)

1. Temporarily blank `RESEND_API_KEY` (or point it at an invalid value) and restart the backend.
2. Repeat §2's failing run.

- [ ] The run fails exactly as it would have — same status, same timing (no hang) — FR-005.
- [ ] The **blue** notice is **still** shown to the user (the notice is tied to the
      classification, not to the send) — FR-005, FR-012.
- [ ] The backend logs a warning about the skipped/failed send; nothing crashes — FR-005.
3. Restore `RESEND_API_KEY`.

---

## 7. Scope check — the deterministic path is untouched

- [ ] A `/karwai` (manual column-mapping) failure behaves exactly as before — no email, no blue
      notice — FR-010, D9.
- [ ] An extractor-side partial success on `/reconcile-ai` keeps its existing amber treatment —
      it is not re-coloured blue — FR-013, D9.

---

## 8. Agent tool summary is present and used

- [ ] Inspect `AGENT_INSTRUCTIONS` in `ai_structure_detector.py`: it contains the short,
      purpose-only tool list and the reporting policy — FR-009.
- [ ] A produced email's proposed solution names a real tool and is consistent with that tool's
      purpose — FR-009, SC-005.

---

## Rollback

Revert `ai_routes.py`, `ai_structure_detector.py`, `notification_service.py`,
`progress_events.py`, `config.py`, `aiReconciliationClient.ts`, and `UploadAIConfig.tsx`.
No data migration to undo (nothing is persisted).
