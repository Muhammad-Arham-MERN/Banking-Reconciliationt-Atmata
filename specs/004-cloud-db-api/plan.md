# Implementation Plan: Cloud Database API Endpoints

**Branch**: `004-cloud-db-api` | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-cloud-db-api/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement two cloud database API endpoints — GET to retrieve the authenticated user's stored file names and POST (upsert) to save reconciliation data — using SQLModel for schema/query operations against the existing CockroachDB instance, behind the existing JWT auth middleware and request logging pipeline.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLModel (NEW), asyncpg, PyJWT, Pydantic v2  
**Storage**: CockroachDB (PostgreSQL-compatible) via existing asyncpg connection pool  
**Testing**: pytest, httpx (for TestClient endpoint tests)  
**Target Platform**: Linux server (same as existing backend)  
**Project Type**: Web (backend-only; frontend is a separate spec)  
**Performance Goals**: GET < 500ms for up to 1000 files (SC-001); POST < 3s for up to 5000 entries (SC-002)  
**Constraints**: Write-after-read consistency within 1s (SC-005); use SQLModel for all new DB operations (FR-005)  
**Scale/Scope**: Single-user/small-team reconciliation tool

### NEEDS CLARIFICATION

1. **SQLModel + existing asyncpg setup**: FR-005 mandates SQLModel for DB operations, but the existing codebase uses raw asyncpg with a connection pool. SQLModel's async support (`sqlmodel.ext.asyncio.session`) requires SQLAlchemy's async engine, which is a separate connection path from the existing `asyncpg.create_pool`. Need to determine: (a) layer SQLModel async sessions alongside the existing pool, (b) migrate the existing pool to SQLAlchemy's async engine, or (c) use SQLModel's sync sessions in async endpoints via `run_in_executor`.
2. **Existing table schema alignment**: The `reconciliation_data` table currently lacks a `user_id` NOT NULL constraint and has `data` as JSONB (not `file_data`). The `users.files` column is JSONB, not a native array. Need to confirm whether ALTER TABLE migrations are acceptable vs. dropping/recreating tables.
3. **Test strategy for DB endpoints**: Existing tests are unit/service-level only, no DB integration tests. Need to confirm whether to (a) use an in-memory SQLite for testing, (b) spin up a test CockroachDB instance, or (c) mock the database layer entirely.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gates (Post-Design)

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| G1 | II. Developer Stack Authority | SQLModel is a new dependency not in the existing stack. Must justify its introduction or seek Developer approval. | ✅ RESOLVED — FR-005 explicitly mandates SQLModel. Async SQLModel is layered alongside the existing asyncpg pool (see research.md). Both coexist without breaking existing code. |
| G2 | I. Strict Instruction Following | FR-005 mandates SQLModel. Must follow as written, but must also align with existing asyncpg architecture. | ✅ RESOLVED — SQLModel async engine uses `sqlalchemy.ext.asyncio` which is compatible with the existing CockroachDB/asyncpg stack. The sync engine is used only for metadata (table creation). |
| G3 | VI. Ambiguity Resolution | The relationship between `reconciliation_data` and `users.files` has multiple valid interpretations (foreign key vs. reference name). Must clarify before design. | ✅ RESOLVED — Confirmed by spec clarifications session (2026-07-10): `reconciliation_data.file_name` is the reference key. `users.files` stores file names that point to records in `reconciliation_data`. Upsert updates `reconciliation_data` and syncs `users.files` when new. |
| G4 | Standard 1 & 3 (File Header/Footer) | All new files MUST start with `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ` and end with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`. | ✅ PASS — standard practice, no violation |
| G5 | Standard 2 (Crux Marker) | The upsert logic and the reference-name sync between `reconciliation_data.file_name` and `users.files` are logically critical. Must be marked with `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`. | ✅ PASS — will apply to critical sections in cloud_service.upsert_recording() |

### Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| G1: New dependency (SQLModel) | FR-005 explicitly mandates SQLModel; the spec requires it for schema definition and queries | Raw asyncpg queries could work but violate the spec requirement |
| G1: Dual DB patterns (asyncpg + SQLAlchemy async) | Existing codebase uses raw asyncpg pool; SQLModel needs SQLAlchemy async engine; both must coexist during transition | Migrating all existing code to SQLAlchemy is out of scope for this feature |

## Project Structure

### Documentation (this feature)

```text
specs/004-cloud-db-api/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output — resolved technical unknowns
├── data-model.md        # Phase 1 output — entity definitions & relationships
├── quickstart.md        # Phase 1 output — implementation steps & reference
├── contracts/
│   └── cloud-api.yaml   # Phase 1 output — OpenAPI 3.0 specification
└── tasks.md             # Phase 2 output (/sp.tasks command — NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── db/                       # NEW directory — SQLModel async engine + session
│   │   └── session.py
│   ├── models/
│   │   ├── cloud_models.py       # NEW — SQLModel table + Pydantic models
│   │   └── ... (existing)
│   ├── services/
│   │   ├── cloud_service.py       # NEW — cloud DB business logic
│   │   └── ... (existing)
│   ├── api/
│   │   ├── cloud_routes.py        # NEW — GET /api/cloud/files, POST /api/cloud/save
│   │   └── ... (existing)
│   └── main.py                    # MODIFIED — register cloud_router
├── tests/
│   └── contract/
│       └── test_cloud_api.py      # NEW — integration tests
└── requirements.prod.txt          # MODIFIED — add sqlmodel, asyncpg, psycopg2-binary, greenlet
```

**Structure Decision**: Backend-only feature. New files follow existing `backend/src/{api,models,services}/` conventions. A new `backend/src/db/` package is added for the SQLModel async session setup (keeps it separate from the raw asyncpg `db_service.py`). All test files go under `backend/tests/contract/` (contract tests == endpoint-level).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
