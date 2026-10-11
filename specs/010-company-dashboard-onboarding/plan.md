# Implementation Plan: Company Dashboard & Onboarding Flow

**Branch**: `010-company-dashboard-onboarding` | **Date**: 2026-10-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-company-dashboard-onboarding/spec.md`

## Summary

The final block of the company/employee dashboard system. Two fronts:

**Company onboarding** — the currently-inert **"Company Request"** button on `/subscription` becomes a full-screen cinematic overlay: a cherry-colored block slides in, stars streak from the center toward the viewer, a company-building SVG grows over ~5s and the view enters a window, then a ported bored-boss character guides four one-at-a-time fade-in questions (**Company Name**, **Role**, **Website/Socials**, **Email and Phone Number**) with basic format validation. The boss taps while typing, raises his hands on each advance, and smiles at the end; a typewriter then writes the success line and the overlay auto-fades after 5s, with a top-right cross to skip. **Nothing is persisted** — the submission is a visual confirmation (clarified).

**Company dashboard** — a new `/CompanyDashboard` route with a **Company Name + Password** sign-in verified server-side against the 008 `companies` table (decrypt the Fernet password, compare constant-time), issuing a **24-hour company session**. The dashboard shows a two-section sidebar — **Employees** (a shadcn table with a per-row **Grant Access** checkmark) and **Subscription** (an inert "Start 30 days free trial" card). The Admin Dashboard (`AdminDashAccess`) gains a **"Company Requests"** category with a request detail view.

Backend: **one new endpoint** (`POST /api/company/login`), one new service/model, a company branch in the middleware, and **two new settings** (`COMPANY_JWT_SECRET`, `COMPANY_JWT_TTL_HOURS`). **No new tables, no new dependencies.** Frontend: the cinematic + dashboard components, the Aceternity sidebar (deps already present), and reuse of the existing `TypewriterEffect`. The employees table, the Company Requests view, and the subscription card render from **placeholder data**. **No automated tests** (Developer instruction).

## Technical Context

**Language/Version**: Python 3.13 (backend, `requires-python >=3.13`); TypeScript 5.x on Next.js 16.2.9 / React 19.2.4 (frontend)  
**Primary Dependencies**: Backend — FastAPI, asyncpg, pydantic v2, PyJWT, cryptography (all existing; company login reuses Fernet + admin-auth idioms). Frontend — Next.js App Router (RSC), NextAuth v5 (Google, for the `/subscription` page the button lives on), shadcn `base-nova` on Base UI, Tailwind v4, **motion** (existing), `@tabler/icons-react` (existing, required by the Aceternity sidebar), lucide-react. **No additions on either side.**  
**Storage**: CockroachDB via raw asyncpg (`db_service`, `$n` placeholders) — this feature **reads** the existing `companies` table only; **no new tables or migrations**. Company session lives in browser `localStorage`.  
**Testing**: None — automated tests are intentionally omitted per the Developer's explicit instruction ("no tests"; 008/009 precedent); verification is the manual pass in `quickstart.md`  
**Target Platform**: Linux container for the backend (`python:3.13-bookworm-slim`), browser for the frontend  
**Project Type**: Web application (existing `backend/` + `frontend/` split)  
**Performance Goals**: The cinematic intro plays smoothly (~60fps) with no visible stutter (SC-002); a company sign-in round-trip completes in well under a second at tens-of-companies scale  
**Constraints**: Only the company sign-in touches the backend; the request submission is never persisted; the "Company Request" overlay honours reduced motion; the subscription card is inert; no new dependencies; no new DB tables; no automated tests  
**Scale/Scope**: Tens of companies; one new endpoint; one new route; two new frontend feature folders; one reused UI primitive added (sidebar); the company dashboard has exactly two sections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Assessment |
|-----------|--------|------------|
| I. Strict Instruction Following | ✅ PASS | The Developer asked for exactly one backend piece (company sign-in) and "no other APIs"; the request/employees/requests views are frontend structure with placeholder data (FR-024); no tests are written; "Company Request" gets exactly the described flow (FR-001–FR-014); the boss file is removed after porting (R8). |
| II. Developer Stack Authority | ✅ PASS | Reuses FastAPI + asyncpg/CockroachDB + Next.js + NextAuth + shadcn, plus **`motion` and the Aceternity sidebar the Developer requested** — the sidebar's only deps (`@tabler/icons-react`, `motion`) are already installed, so **zero new dependencies** (R16). No ORM reintroduced. |
| III. Supervised Collaboration | ✅ PASS | Every design choice is recorded with alternatives in `research.md`; the one debatable call (issuing a signed company JWT rather than a client-only flag, R1) is flagged as reversible in Complexity Tracking. |
| IV. Constructive Objection | ✅ PASS | Two risks are raised with mitigations rather than silently accepted: `localStorage` session storage (XSS surface) is chosen only because the clarification requires 24h persistence and the repo is Bearer-token based (R3, objection recorded); and a reusable sidebar changes the admin dashboard layout (R14, noted). |
| V. Controlled Creativity | ✅ PASS | The "novel" pieces are the cinematic timeline and the boss port — both are direct renderings of the Developer's own description and a supplied reference asset, not invented algorithms. |
| VI. Ambiguity Resolution | ✅ PASS | The spec's 2026-10-01 clarification session resolved all five open points (storage, session lifetime, labels, validation, name matching); no `NEEDS CLARIFICATION` remains in Technical Context. |
| Code Standards 1–3 | ⚠️ REQUIRED | Every new Python/TS file MUST begin with the Bismillah header (`# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` / `/* … */`), end with the footer (`# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`), and mark the logical crux inline (`# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`) — applies to `company_auth_service.py`, `company_auth_models.py`, `company_auth_routes.py`, the edited `auth_middleware.py`/`config.py`/`company_service.py`/`main.py`, and every new frontend component/client/types file plus the ported `boss-loader`. |

**Initial gate: PASS.** One flagged, reversible decision for the Developer (not a blocker): issuing a signed 24-hour company JWT (R1) versus a purely client-held session flag.

## Project Structure

### Documentation (this feature)

```text
specs/010-company-dashboard-onboarding/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (decisions + alternatives)
├── data-model.md        # Phase 1 output (entities, read paths, validation)
├── quickstart.md        # Phase 1 output (manual verification)
├── contracts/
│   └── company-auth-api.yaml  # Phase 1 output (OpenAPI 3.1 — POST /api/company/login)
├── checklists/
│   └── requirements.md  # Spec quality checklist (/sp.specify + /sp.clarify)
└── tasks.md             # Phase 2 output (/sp.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── .env.example                                    # + COMPANY_JWT_SECRET
└── src/
    ├── config.py                                   # + COMPANY_JWT_SECRET, COMPANY_JWT_TTL_HOURS
    ├── main.py                                     # + register company_auth router
    ├── api/
    │   ├── auth_middleware.py                      # + company branch (login public, rest company-JWT gated)
    │   └── company_auth_routes.py                  # NEW — POST /api/company/login
    ├── models/
    │   └── company_auth_models.py                  # NEW — login request/response pydantic + CompanyIdentity
    └── services/
        ├── company_auth_service.py                 # NEW — verify name+password (decrypt + constant-time) + issue company JWT
        └── company_service.py                      # + get_company_by_name() case-insensitive read

frontend/
├── boss-loader.html                                # DELETED — ported into the component below
└── src/
    ├── app/
    │   ├── CompanyDashboard/
    │   │   └── page.tsx                            # NEW — thin force-dynamic shell → <CompanyDashboard/>
    │   └── subscription/ …                         # (page unchanged)
    ├── components/
    │   ├── subscription/
    │   │   └── subscription-plans.tsx              # MODIFIED — "Company Request" opens the overlay
    │   ├── company-request/                        # NEW feature folder — the cinematic onboarding
    │   │   ├── company-request-flow.tsx            #   phase machine (intro → questions → success), cross, auto-close
    │   │   ├── cinematic-intro.tsx                 #   cherry block + building growth + window entry (motion)
    │   │   ├── star-field.tsx                      #   center-origin star streaks
    │   │   ├── company-building.tsx                #   the building SVG
    │   │   ├── onboarding-questions.tsx            #   four fade-in steps + format validation
    │   │   ├── request-success.tsx                 #   TypewriterEffect message + 5s auto-close
    │   │   ├── boss-loader.tsx                     #   ported SVG (no JS)
    │   │   └── boss-loader.module.css              #   ported keyframes
    │   ├── company-dashboard/                      # NEW feature folder — the company surface
    │   │   ├── company-dashboard.tsx               #   client shell: session store → sign-in or dashboard
    │   │   ├── company-sign-in-form.tsx            #   Company Name + Password
    │   │   ├── company-sidebar.tsx                 #   wraps the Aceternity sidebar (Employees / Subscription)
    │   │   ├── employees-table.tsx                 #   shadcn Table + Grant Access toggle
    │   │   └── subscription-panel.tsx              #   inert "Start 30 days free trial" card
    │   ├── admin/
    │   │   ├── admin-dashboard.tsx                 # MODIFIED — category nav (Companies / Company Requests)
    │   │   └── company-requests-table.tsx          # NEW — placeholder requests + detail dialog
    │   └── ui/
    │       └── sidebar.tsx                         # NEW — Aceternity sidebar (registry; no new deps)
    ├── lib/
    │   ├── company/
    │   │   ├── company-session.ts                  # NEW — localStorage session store (24h), external-store pattern
    │   │   ├── company-placeholder.ts              # NEW — sample employees + requests (stand-in data)
    │   │   └── company-validation.ts               # NEW — onboarding value validation helpers
    │   └── api/
    │       └── companyClient.ts                    # NEW — login()
    └── types/
        └── company.types.ts                        # NEW — session, identity, placeholder shapes
```

**Structure Decision**: Web application (Option 2) — the repo already has separate `backend/` and `frontend/` roots, so the feature is added along the existing seams: one new route module (`company_auth_routes.py`) registered in `main.py` mirroring `admin_routes.py`; one new service (`company_auth_service.py`) mirroring `admin_auth_service.py`; one new pydantic module mirroring `admin_models.py`; and two new `components/<feature>/` folders mirroring `components/admin/`. The Aceternity `sidebar.tsx` is added to the existing `components/ui/` set via the project's registry. No new top-level projects, no ORM, no new state/data-fetching library, no new UI dependency.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. The table records a deliberate, flagged decision plus the Developer-directed scope fences:

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|--------------------------------------|
| Signed 24-hour company JWT (`COMPANY_JWT_SECRET`) rather than a client-only session flag | The spec frames sign-in as establishing a *session* with a 24-hour lifetime (FR-018); a server-issued, expiring token is the honest, pattern-consistent implementation and the next (backend) spec needs it | A client-held flag would misrepresent a `localStorage` write as an authenticated session and would have to be replaced as soon as company-scoped endpoints exist. **Reversible**: dropping the token changes only `company_auth_service.py`, one branch in the middleware, and one config value. |
| `localStorage` for the company session | The clarification requires the session to survive browser restarts for 24h; `sessionStorage` (008's choice) ends at browser close | httpOnly cookies would force credentialed CORS on a cross-origin Bearer-token API; `sessionStorage` contradicts the 24h clarification |
| No new DB tables | There is no request storage and no employee/company-scoped data in this spec (FR-024); the dashboard and admin views use placeholder data | Adding tables now would build the data model the next specification is explicitly meant to design |
| Inert "Start 30 days free trial" card and inert plan buttons | Spec fences billing/payment to later specifications (FR-022, Assumptions) | Wiring payments now builds unrequested flows and would be rework |
| Admin dashboard gains a sidebar-based "Company Requests" category | FR-023 asks for a new *category*; reusing the sidebar already added for the company dashboard keeps one navigation idiom | A second nav pattern (tabs/toggle) would duplicate and diverge from the company dashboard |
| No automated tests | Developer instructed "no tests"; 008/009 precedent (Constitution Principle I) | Adding pytest/Playwright contradicts the explicit instruction and expands scope |
