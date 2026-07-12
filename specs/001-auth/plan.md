# Implementation Plan: Google OAuth Authentication with Auth.js

**Branch**: `001-auth` | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-auth/spec.md`

## Summary

Add Google OAuth authentication using Auth.js (NextAuth v5) on the Next.js frontend, with CockroachDB (PostgreSQL-compatible) for auth tables and reconciliation data storage. Users sign in with Google, get a 24-hour session, and their reconciliation data is isolated per user via the `users.files` and `Reconciliation_data.file_name` association. No existing reconciliation logic is modified.

## Technical Context

**Language/Version**: TypeScript (Next.js 16, React 19) for frontend auth; Python 3 (FastAPI 0.104.1) for backend  
**Primary Dependencies**: Auth.js / NextAuth v5 (frontend), Auth.js PostgreSQL adapter, CockroachDB driver (psycopg2 or asyncpg for Python backend)  
**Storage**: CockroachDB (PostgreSQL-compatible) — auth tables managed by Auth.js adapter, plus new `Reconciliation_data` table  
**Testing**: pytest for backend, Vitest/React Testing Library for frontend  
**Target Platform**: Web (cloud-deployed)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Sign-in <10s, sign-out <2s, 10–20 concurrent users  
**Constraints**: No changes to existing reconciliation logic; no business API endpoints; 24-hour fixed session without refresh  
**Scale/Scope**: 10–20 authenticated users, single deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Check | Phase 0 | Phase 1 | Status |
|-------|---------|---------|--------|
| I. Strict Instruction Following | ✅ Spec clear | ✅ Design follows spec exactly | ✅ PASS |
| II. Developer Stack Authority | ✅ Using Next.js/FastAPI/Auth.js | ✅ Added CockroachDB, `@auth/pg-adapter`, `next-auth@5` | ✅ PASS |
| III. Supervised Collaboration | ✅ Clarifications used | ✅ No autonomous decisions | ✅ PASS |
| IV. Constructive Objection | ✅ JWT strategy chosen over DB sessions | ✅ Documented in research.md | ✅ PASS |
| V. Controlled Creativity | ✅ Standard patterns only | ✅ Auth.js docs patterns followed | ✅ PASS |
| VI. Ambiguity Resolution | ✅ 4 clarifications resolved | ✅ All resolved in spec | ✅ PASS |

### Code Standards Applied

| Standard | Compliance | Notes |
|----------|------------|-------|
| File Header (`بِسْمِ اللّٰهِ...`) | ✅ GATE | Applied to all new source files |
| Logical Marker (`وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ`) | ✅ GATE | Applied to auth middleware/guard logic |
| File Footer (`وَإِنَّ اللَّهَ...`) | ✅ GATE | Applied to all new source files |

**Gate Status: ✅ PASS** — No violations. All phases passed.

## Project Structure

### Documentation (this feature)

```text
specs/001-auth/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── api/auth/[...nextauth]/
│   │   │   └── route.ts         # Auth.js handler route
│   │   ├── login/
│   │   │   └── page.tsx         # Google Sign-In page
│   │   └── layout.tsx           # Session provider wrapper
│   ├── components/
│   │   ├── auth/
│   │   │   ├── sign-in-button.tsx
│   │   │   └── session-status.tsx
│   │   └── providers/
│   │       └── session-provider.tsx
│   └── lib/
│       └── auth.ts              # Auth.js configuration

backend/
├── src/
│   ├── api/
│   │   ├── routes.py            # Add session/user context
│   │   └── middleware.py        # Auth verification middleware
│   ├── models/
│   │   └── db_models.py         # Reconciliation_data model
│   └── services/
│       ├── auth_service.py      # Verify/validate tokens server-side
│       └── db_service.py        # CockroachDB connection + queries

tests/
├── backend/
│   ├── test_auth.py
│   └── test_db_models.py
└── frontend/
    ├── sign-in.test.tsx
    └── auth-flow.test.ts
```

**Structure Decision**: Web application (frontend + backend) using the existing `frontend/` and `backend/` directory layout. Auth.js handles frontend auth; backend verifies session tokens and provides user context to existing services.

## Complexity Tracking

No constitutional violations requiring justification.
