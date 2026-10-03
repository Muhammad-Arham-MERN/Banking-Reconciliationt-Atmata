---
id: plan-008-admin-dashboard
title: admin-dashboard-plan
stage: plan
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 008-admin-dashboard
branch: 008-admin-dashboard
user: developer
command: /sp.plan
labels: [plan, admin, dashboard, fastapi, nextjs, fernet, cockroachdb]
links:
  spec: specs/008-admin-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-admin-dashboard/plan.md
  - specs/008-admin-dashboard/research.md
  - specs/008-admin-dashboard/data-model.md
  - specs/008-admin-dashboard/contracts/admin-api.yaml
  - specs/008-admin-dashboard/quickstart.md
  - CLAUDE.md
  - history/prompts/008-admin-dashboard/plan-008-admin-dashboard.prompt.md
tests:
  - null
---

## Prompt

/sp.plan

## Response snapshot

Ran `setup-plan.ps1 -Json` (FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH resolved; plan template copied), loaded the spec and `.specify/memory/constitution.md`, and explored both halves of the codebase with two parallel explore agents plus targeted reads (`main.py`, `db_service.py`, `auth_middleware.py`, `middleware.py`, `file_helpers.py` cleanup routines, `db_migrations.py`, `cloud_routes.py`).

Produced Phase 0 + Phase 1 artifacts:
- **plan.md** — Technical Context (Python 3.13 / FastAPI + asyncpg + PyJWT + NEW cryptography; Next.js 16.2.9 / React 19.2.4 / shadcn base-nova; CockroachDB; no tests by instruction), a Constitution Check table (all six principles pass; Code Standards 1–3 flagged as REQUIRED for every new file), the concrete web-app source tree (backend admin_routes/admin_models/company_service/company_crypto_service/company_logo_service/admin_auth_service + auth_middleware branch + migration; frontend app/AdminDashAccess page + components/admin/* + lib/api/adminClient.ts), Structure Decision, and a Complexity Tracking table recording deliberate scope fences.
- **research.md** — 14 decisions (R1–R14) each with rationale and rejected alternatives, plus a resolved-unknowns summary.
- **data-model.md** — the `companies` DDL with CHECK constraints + `lower(name)` unique index, attribute table, API-only derived fields, validation rules with their status codes, the payment_status state diagram, the no-relationships statement, storage layout, and volume notes.
- **contracts/admin-api.yaml** — OpenAPI 3.1 for the 7 endpoints plus schemas and shared error/parameter components.
- **quickstart.md** — the manual verification pass replacing tests (env setup, stack bring-up, all acceptance scenarios, the security-invariant checks, and the deliberate non-goals).
- Ran `update-agent-context.ps1 -AgentType claude`, which updated `CLAUDE.md`.

Key findings that shaped the design: `auth_middleware` 401s every non-exempt path without a NextAuth Bearer token (so a naive admin endpoint would be unreachable) → the admin auth branch inside the middleware; `cleanup_old_files` (20-min) and `cleanup_all_files` (shutdown) delete files in `UPLOAD_DIR` (so logos need a dedicated directory outside it — the sharpest trap found); no ORM (raw asyncpg + a flat idempotent MIGRATIONS list); `security_middleware` inspects only the URL, not bodies (so credentials/names in JSON are safe, but must not go in the query string); CockroachDB SERIAL ids must be serialized as strings; and the frontend has no Label/AlertDialog/DropdownMenu/Form/toast/react-hook-form (so the UI is built from the primitives that exist).

## Outcome

- ✅ Impact: Full technical plan with Phase 0 research, Phase 1 design artifacts and contracts, and an updated agent context; ready for /sp.tasks.
- 🧪 Tests: None — intentionally omitted per the Developer's explicit instruction (spec + plan Technical Context both record this); verification is quickstart.md.
- 📁 Files: specs/008-admin-dashboard/{plan.md, research.md, data-model.md, contracts/admin-api.yaml, quickstart.md}, CLAUDE.md
- 🔁 Next prompts: /sp.tasks for 008-admin-dashboard
- 🧠 Reflection: The single most valuable output of exploration was catching the upload-cleanup trap — logos in `UPLOAD_DIR` would have been silently deleted within 20 minutes or on the next restart, a bug that would not surface until a customer's logo vanished. Reading `cleanup_old_files`/`cleanup_all_files` rather than assuming file storage was uniform is what caught it. Second: the global auth middleware makes "just add an endpoint" wrong here; the admin branch must live inside the middleware to fail closed.

## Evaluation notes (flywheel)

- Failure modes observed: `setup-plan.ps1 -Json` printed its JSON only after a preceding "Copied plan template" line and emitted a CLIXML progress stream (Windows PowerShell 5.1), but the JSON parsed cleanly. `update-agent-context.ps1` worked correctly on the first try (unlike `create-new-feature.ps1`).
- Graders run and results (PASS/FAIL): Constitution gate PASS (all six principles; no unjustified violations); no NEEDS CLARIFICATION remains in Technical Context; all 14 research unknowns resolved.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): Confirm whether Next.js accepts the exact-case `AdminDashAccess` App Router segment at build time (research R12 risk) before /sp.tasks fixes the folder name in the task list.
