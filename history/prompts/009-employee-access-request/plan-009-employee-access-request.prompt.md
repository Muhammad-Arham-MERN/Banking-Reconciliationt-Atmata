---
id: plan-009-employee-access-request
title: employee-access-request-plan
stage: plan
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 009-employee-access-request
branch: 009-employee-access-request
user: developer
command: /sp.plan
labels: [plan, subscription, employees, access-request, adam-id, nextauth, asyncpg, migration]
links:
  spec: specs/009-employee-access-request/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-employee-access-request/plan.md
  - specs/009-employee-access-request/research.md
  - specs/009-employee-access-request/data-model.md
  - specs/009-employee-access-request/contracts/employee-api.yaml
  - specs/009-employee-access-request/quickstart.md
  - CLAUDE.md
  - history/prompts/009-employee-access-request/plan-009-employee-access-request.prompt.md
tests:
  - null
---

## Prompt

/sp.plan start

## Response snapshot

Executed the planning workflow for feature 009. Setup-plan.ps1 copied the plan template to specs/009-employee-access-request/plan.md and reported the branch/feature paths. Loaded the constitution (v1.0.0 — six core principles plus three Code Standards requiring the Bismillah header, the crux marker, and the footer in every new file), the spec, the plan template, and the 008 plan/research/data-model/quickstart as precedent. Two parallel explore agents documented the frontend (NextAuth v5 + Google with `session.user.access_token`, no middleware, per-page `auth() → redirect("/")` guards, `CloseTabWarning` mounted globally in layout.tsx as the sole cause of the "Leave site?" prompt, admin components/client/types as the pattern to mirror) and the backend (raw asyncpg `db_service` with `$n` params and a raw-SQL `MIGRATIONS` list, middleware-only auth with a NextAuth branch that sets `request.state.user_id`/`user_email` and an admin branch pinned to `/api/admin`, `company_service.list_companies`, `company_logo_service` helpers, the structured `{"error","message","details"}` HTTPException envelope).

Phase 0 (research.md, 13 decisions R1–R13): sign-in moves to a new `/login` with `/` redirecting out and `pages.signIn` repointed; the "Leave site?" prompt is removed by dropping the global `CloseTabWarning` mount (leaving `UploadAIConfig`'s cancel-on-unload handler intact); the new `employees` table goes into the raw-SQL migration list; the `adam-` ID is `adam-` + 6–12 lowercase alphanumerics, normalized server-side, generated client-side; uniqueness is composite on (employee_id, company_id) resolving the spec's contradiction; the company is stored as id + name snapshot with **no DB foreign key** so the admin's hard delete keeps working; three endpoints (`GET /api/companies`, `GET /api/companies/{id}/logo`, `POST /api/employees/requests`) ride the existing NextAuth middleware branch because employees hold no admin token, and a dedicated logo path is required since the admin logo endpoint is admin-pinned; the subscription page + dialog reuse existing shadcn primitives; zero new dependencies; no automated tests.

Phase 1: data-model.md (employees DDL with the composite unique index and CHECK constraints, attribute table, validation rules 1–5, the pending→accepted/denied state diagram, relationships, volume); contracts/employee-api.yaml (OpenAPI 3.1 for the three endpoints with the CompanyOption/EmployeeRequestCreate/EmployeeRequestResponse/ErrorResponse schemas and 400/401/404/409 responses); quickstart.md (31-step manual verification pass with SQL checks, curl 401 probes and the deliberate non-goals). Ran update-agent-context.ps1 -AgentType claude, which appended the feature's language/framework/database lines to CLAUDE.md. Constitution Check passes both pre-Phase 0 and post-Phase 1; the only flagged (non-blocking) item is that the spec's Q1–Q5 clarifications were applied from the recommended options and remain cheap to reverse.

## Outcome

- ✅ Impact: Feature 009 is fully planned and ready for task decomposition. The design resolves the spec's ID-uniqueness contradiction in the database schema, avoids two integration traps (the admin-pinned logo endpoint; a foreign key that would break the shipped company delete), and adds zero dependencies on either side.
- 🧪 Tests: None run and none specified — deliberate, per the Developer's standing "no tests" instruction (Constitution Principle I); verification is quickstart.md's manual pass.
- 📁 Files: specs/009-employee-access-request/{plan.md, research.md, data-model.md, contracts/employee-api.yaml, quickstart.md}, CLAUDE.md (agent context updated by script)
- 🔁 Next prompts: /sp.tasks for 009-employee-access-request
- 🧠 Reflection: Grounding the plan in two parallel explore agents (rather than assuming) surfaced the details that decide the design — `CloseTabWarning` being the single cause of FR-002's popup, and the middleware's path-based admin branch making the admin logo endpoint unusable by employees. Both would have been discovered late and expensively during implementation. The one open loop is that the clarification answers were defaults, flagged in the plan rather than silently baked in.

## Evaluation notes (flywheel)

- Failure modes observed: the mandate to read a file in full before overwriting tripped the first plan.md write (setup-plan.ps1 had just created it from the template) — the fix was a full read, then the write. The 008 PHR's noted defect (create-new-feature.ps1's multi-arg Join-Path) did not recur because no new feature branch was created. The PHR script (.specify/scripts/bash/create-phr.sh) remains absent on this Windows checkout, so the agent-native fallback was used again.
- Graders run and results (PASS/FAIL): Constitution Check PASS (pre-Phase 0 and post-Phase 1); no NEEDS CLARIFICATION left in Technical Context; all four Phase 0/1 artifacts present with concrete file paths and no Option labels in the delivered structure tree.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): have the plan explicitly restate the applied clarification defaults as a one-line "confirm before implementation" block at the top, so an unconfirmed default can never reach /sp.tasks unnoticed.
