---
id: plan-010-company-dashboard-onboarding
title: company-dashboard-onboarding-plan
stage: plan
date: 2026-10-01
surface: cli
model: claude-sonnet-4-5
feature: 010-company-dashboard-onboarding
branch: 010-company-dashboard-onboarding
user: developer
command: /sp.plan
labels: [plan, company-dashboard, onboarding, cinematic, company-auth, aceternity, sidebar]
links:
  spec: specs/010-company-dashboard-onboarding/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/010-company-dashboard-onboarding/plan.md
  - specs/010-company-dashboard-onboarding/research.md
  - specs/010-company-dashboard-onboarding/data-model.md
  - specs/010-company-dashboard-onboarding/quickstart.md
  - specs/010-company-dashboard-onboarding/contracts/company-auth-api.yaml
  - CLAUDE.md
  - history/prompts/010-company-dashboard-onboarding/plan-010-company-dashboard-onboarding.prompt.md
tests:
  - null
---

## Prompt

/sp.plan

(No additional input was provided; the plan was generated from specs/010-company-dashboard-onboarding/spec.md and the .specify/memory/constitution.md.)

## Response snapshot

Executed the planning workflow for feature 010-company-dashboard-onboarding. setup-plan.ps1 -Json copied the plan template and returned FEATURE_SPEC/IMPL_PLAN/SPECS_DIR/BRANCH. Loaded the spec, constitution, and the 008/009 plans, research, data-model, contracts, and quickstart for established facts, then read the concrete seams: backend `main.py`, `config.py`, `auth_middleware.py`, `admin_routes.py`, `admin_auth_service.py`, `company_service.py`, `company_crypto_service.py`, `db_migrations.py`, `employee_routes.py`, `employee_service.py`; frontend `AdminDashAccess/page.tsx`, `admin-dashboard.tsx`, `companies-table.tsx`, `adminClient.ts`, `admin-session.ts`, `layout.tsx`, `subscription/page.tsx`, `auth.config.ts`, `typewriter-effect.tsx`, `stars-background.tsx`, `shooting-stars.tsx`, `globals.css`, `package.json`, `components.json`, and the `components/ui/` inventory. Also fetched the Aceternity sidebar registry JSON to confirm its dependencies.

Generated: `research.md` (17 decisions, R1–R17, with alternatives), `data-model.md` (Company read path + credential verification, client-only Company Session, placeholder Company Request and Employee, no new tables), `contracts/company-auth-api.yaml` (OpenAPI 3.1 for the single new endpoint), and `quickstart.md` (manual verification mapped to FRs/SCs). Filled `plan.md` (Technical Context, Constitution Check — PASS with one flagged reversible decision, project structure with concrete backend/frontend trees, and Complexity Tracking). Ran update-agent-context.ps1 -AgentType claude, which appended the 010 entries to CLAUDE.md.

Key decisions: the only backend work is `POST /api/company/login` — verify Company Name (case-insensitive, trimmed) against the existing `companies` table, decrypt the Fernet password, compare constant-time (generic 401 on any failure; 503 if the key/secret is missing), and issue a 24-hour company JWT (`COMPANY_JWT_SECRET`) stored in `localStorage`; a company branch in `auth_middleware` mirrors the admin branch. No new DB tables, no new dependencies (the Aceternity sidebar's `motion` + `@tabler/icons-react` are already installed; the Aceternity text-generate-effect equivalent `TypewriterEffect` already exists). The cinematic overlay is a `motion`-driven phase machine; the bored-boss reference file is ported to a component + CSS module and then deleted. Employees, Company Requests, and the subscription card render from placeholder data with empty states. No tests.

## Outcome

- ✅ Impact: Full planning artifacts for the company dashboard/onboarding feature delivered; constitution gate PASS; ready for /sp.tasks.
- 🧪 Tests: None run (planning stage; "no tests" is the Developer's standing instruction).
- 📁 Files: specs/010-company-dashboard-onboarding/{plan,research,data-model,quickstart}.md, specs/010-company-dashboard-onboarding/contracts/company-auth-api.yaml, CLAUDE.md (agent context updated).
- 🔁 Next prompts: /sp.tasks for 010-company-dashboard-onboarding
- 🧠 Reflection: The hard part was right-sizing the backend. The spec's "one API only" plus "no other APIs" resolved cleanly once the existing 008 primitives (companies table, Fernet, admin JWT idiom) were on the table: the company sign-in is almost entirely reuse. Two decisions are worth the Developer's eye — issuing a signed 24h company JWT rather than a client-only flag (flagged reversible), and reusing a single Aceternity sidebar for both the company dashboard sections and the admin category nav. Everything else is a direct rendering of the Developer's own description plus placeholder data.

## Evaluation notes (flywheel)

- Failure modes observed: `write_file` on `plan.md` was first rejected because only a 10-line preview had been read — the full file must be read before overwriting. `update-agent-context.ps1` ran cleanly on Windows PowerShell 5.1 (unlike `create-new-feature.ps1`); it appended 010 entries to CLAUDE.md as expected.
- Graders run and results (PASS/FAIL): PASS — all Phase 0/Phase 1 artifacts present; Technical Context has no NEEDS CLARIFICATION; Constitution Check PASS with one flagged reversible decision; contract matches the single-endpoint scope.
- Prompt variant (if applicable): plan-v1
- Next experiment (smallest change to try): Confirm whether the Developer wants the signed company JWT (R1) or a purely client-held session before /sp.tasks, so task breakdown does not bake in a reversible choice.
