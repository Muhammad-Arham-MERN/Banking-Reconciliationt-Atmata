# Implementation Plan: Cloud File Migration

**Branch**: `001-cloud-file-migration` | **Date**: 2026-07-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-cloud-file-migration/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Migrate the frontend's file loading and saving from local SQLite storage to cloud API endpoints (`load_files_cloud` GET, `save_files_cloud` POST). Add a personalized "Assalamu Alaikum [name]" greeting on the main upload page. Remove all local file system dependencies — the app becomes cloud-only. Auth uses the existing NextAuth JWT passed as a Bearer token.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: TypeScript 5 / Next.js 16 (frontend), Python 3.11+ / FastAPI (backend)  
**Primary Dependencies**: next-auth v5, @auth/pg-adapter (frontend); fastapi, sqlmodel, asyncpg (backend)  
**Storage**: CockroachDB (PostgreSQL-compatible) — existing `reconciliation_data` table, auth adapter tables  
**Testing**: Jest / React Testing Library (frontend), pytest / httpx (backend)  
**Target Platform**: Web (Vercel/cloud deployment, 5-10 users)
**Project Type**: Web application (Next.js frontend + FastAPI backend)  
**Performance Goals**: Greeting visible within 2s, history loaded within 3s, save confirmation within 2s (normal network)  
**Constraints**: Cloud-only, no offline fallback, auth token required for all cloud API calls  
**Scale/Scope**: 5-10 users, ~50-200 reconciliation files total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Strict Instruction Following | ✅ PASS | All requirements from spec are precisely followed; no improvisation on file format, greeting, or API contracts |
| II. Developer Stack Authority | ✅ PASS | Uses existing Next.js + FastAPI stack; no new frameworks introduced |
| III. Supervised Collaboration | ✅ PASS | All design decisions documented in research.md with rationale |
| IV. Constructive Objection | ✅ PASS | No objections needed — plan respects existing architecture |
| V. Controlled Creativity | ✅ PASS | No novel approaches; standard API client + auth patterns |
| VI. Ambiguity Resolution | ✅ PASS | All clarifications resolved via /sp.clarify session |

**Gate Result**: ✅ PASS — all constitution principles satisfied.

## Code Standards Check

| Standard | Status | Notes |
|----------|--------|-------|
| Standard 1: File Header (بِسْمِ اللَّهِ) | ✅ PASS | Existing files already have it; new files must include it |
| Standard 2: Crux Marker (وَهُوَ) | ✅ PASS | Cloud save/load logic qualifies as critical — marker required in cloud service |
| Standard 3: File Footer (وَإِنَّ اللَّهَ) | ✅ PASS | Existing files have it; new files must include it |

## Project Structure

### Documentation (this feature)

```text
specs/001-cloud-file-migration/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output — 6 decision records
├── data-model.md        # Phase 1 output — User, Cloud File, Entry entities
├── quickstart.md        # Phase 1 output — step-by-step implementation guide
├── contracts/           # Phase 1 output — cloud-history-api.md
│   └── cloud-history-api.md
└── tasks.md             # Phase 2 (/sp.tasks command — NOT created by /sp.plan)
```

### Source Code (repository root)

The feature touches only the frontend. The backend cloud routes are already implemented.

```text
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              ← Greeting + sign-in (no change needed)
│   │   └── upload/
│   │       └── page.tsx          ← ADD "Assalamu Alaikum [name]" greeting
│   ├── components/
│   │   ├── upload/
│   │   │   └── UploadForm.tsx    ← MODIFY: use cloud client for history list
│   │   └── results/
│   │       └── ReconciliationResults.tsx  ← MODIFY: use cloud client for save
│   ├── lib/
│   │   ├── auth.config.ts        ← MODIFY: expose JWT in session
│   │   └── api/
│   │       ├── historyClient.ts   ← REMOVED (or kept for reference)
│   │       └── cloudHistoryClient.ts  ← NEW: cloud API client
│   └── types/
│       ├── history.types.ts      ← UNCHANGED (or partially deprecated)
│       └── cloud-history.types.ts ← NEW: cloud API types

backend/
└── src/
    ├── main.py                   ← UNCHANGED (CORS already configured)
    ├── api/
    │   └── cloud_routes.py       ← UNCHANGED (already implemented)
    ├── models/
    │   └── cloud_models.py       ← UNCHANGED (already implemented)
    └── services/
        └── cloud_service.py      ← UNCHANGED (already implemented)
```

**Structure Decision**: Web application (Next.js frontend + FastAPI backend). Only the frontend needs changes for this feature. The backend cloud endpoints are already live.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
