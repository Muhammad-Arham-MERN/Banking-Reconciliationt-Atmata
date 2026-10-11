---
id: plan-011-company-employee-wiring
title: company-employee-wiring-plan
stage: plan
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.plan
labels: [plan, architecture, company-dashboard, employee-access, membership-gate, sign-convention, resend, contracts, data-model]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-company-employee-wiring/plan.md
  - specs/011-company-employee-wiring/research.md
  - specs/011-company-employee-wiring/data-model.md
  - specs/011-company-employee-wiring/quickstart.md
  - specs/011-company-employee-wiring/contracts/company-api.yaml
  - specs/011-company-employee-wiring/contracts/membership-api.yaml
  - specs/011-company-employee-wiring/contracts/admin-api.yaml
  - specs/011-company-employee-wiring/contracts/sign-convention.md
  - CLAUDE.md
  - history/prompts/011-company-employee-wiring/plan-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

/sp.plan

(No additional input was provided. The plan was generated from specs/011-company-employee-wiring/spec.md and the project constitution.)

## Response snapshot

Ran the planning workflow for 011-company-employee-wiring.

1. **Setup**: `setup-plan.ps1 -Json` copied the template to `specs/011-company-employee-wiring/plan.md` and returned FEATURE_SPEC / IMPL_PLAN / SPECS_DIR / BRANCH. Loaded `.specify/memory/constitution.md` (v1.0.0 — six principles, three code standards, no-tests policy).
2. **Context grounding**: read the real backend (db_migrations, employee/company models + services + routes, auth_middleware's three branches, db_service, config, main) and frontend (layout header, /upload-ai page, the four API clients, types, company-dashboard components, admin dashboard + company-requests table, subscription plans + employee-request dialog, company onboarding flow, NextAuth session config).
3. **plan.md**: filled Technical Context (Python 3.13 + FastAPI + asyncpg/no-ORM; TS/Next 16.2.9; NEW dependency `resend` only; CockroachDB; web app), Constitution Check (all gates PASS — only developer-requested Resend added; file header/footer standards enforced; no tests), the concrete source tree, and design highlights.
4. **Phase 0 — research.md**: 12 decisions with rationale + alternatives: D1 company-facing endpoints on the company-JWT branch; D2 two-layer membership gate with an exact allow-list (backend authoritative + frontend RSC guard); D3 one-active-request enforced in the service + index (no unique index, legacy-data safety); D4 explicit cascade delete on company removal; D5 view-only `company_requests` table + admin list; D6 canonical sign convention (flips current Bank and Vendor polarity end-to-end, no legacy backfill); D7 Resend best-effort after persistence; D8 `is_manager` boolean; D9 fix the dangling company logo URL; D10 client-side ID-then-name search; D11 leave-company + membership-aware nav; D12 admin employee_count + hover roster.
5. **Phase 1 — data-model.md**: table-by-table model (users, companies, employees extended with `is_manager`, new company_requests), indexes, state transitions, validation, the derived membership, and the idempotent migration SQL.
6. **Phase 1 — contracts/**: `company-api.yaml` (company JWT: list/grant/patch-manager/delete employees + company logo), `membership-api.yaml` (NextAuth: GET/DELETE /api/me/membership, POST /api/company-requests, tightened POST /api/employees/requests, /api/companies), `admin-api.yaml` (company-requests list, companies with employee_count, company roster), and `sign-convention.md` (the canonical table + every enforcement point).
7. **Phase 1 — quickstart.md**: manual verification run-through mapping every user story/FR/SC to steps.
8. **Agent context**: ran `update-agent-context.ps1 -AgentType claude`, which updated CLAUDE.md with the feature's tech context.
9. **Re-evaluated the Constitution Check** post-design: no violations; Complexity Tracking left empty. Validated the artifacts: plan/research/data-model/quickstart + 4 contracts present, no unresolved template placeholders.

## Outcome

- ✅ Impact: Full plan set for 011-company-employee-wiring — plan.md, research.md (12 decisions), data-model.md, 4 contracts, quickstart.md; CLAUDE.md updated; constitution gates pass. Ready for /sp.tasks.
- 🧪 Tests: None (planning stage; project has a standing no-tests instruction).
- 📁 Files: specs/011-company-employee-wiring/{plan.md, research.md, data-model.md, quickstart.md, contracts/{company-api.yaml, membership-api.yaml, admin-api.yaml, sign-convention.md}}, CLAUDE.md.
- 🔁 Next prompts: /sp.tasks for 011-company-employee-wiring
- 🧠 Reflection: Grounding the plan in the actual code surfaced two things a spec-level read would have missed: (a) the sign flip is a real behavioural change (the frontend currently encodes the opposite Bank/Vendor polarity in categorizationUtils, ReconciliationResults, and ReconciliationTotals), and (b) the company-JWT branch currently gates no protected route and the login returns a dangling logo URL. Both are now explicit decisions. The membership allow-list is flagged as the top implementation risk because getting it wrong would lock the feature's own endpoints out.

## Evaluation notes (flywheel)

- Failure modes observed: `update-agent-context.ps1` ran cleanly on Windows PowerShell 5.1 and appended the feature's tech context to CLAUDE.md (unlike create-new-feature.ps1, which fails on a multi-arg Join-Path). The admin contract initially had a duplicated `employee_id` key in the AdminEmployee schema; caught and fixed before completion.
- Graders run and results (PASS/FAIL): PASS — Technical Context fully specified (no NEEDS CLARIFICATION), Constitution Check passes with no violations, all Phase 0/1 artifacts generated, no unresolved template placeholders, agent context updated.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): When a feature flips an existing wire convention, add a short "blast radius" checklist to research.md enumerating every file that encodes the old convention, so /sp.tasks can turn it into granular edit tasks.
