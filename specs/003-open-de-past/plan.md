# Implementation Plan: Open de Past — Save & Load Historical Reconciliation Data

**Branch**: `003-open-de-past` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-open-de-past/spec.md`

## Summary

Add the ability to save completed bank reconciliation results as local SQLite history files, optionally name them, and load past discrepancies into new reconciliation sessions via an "Open Maazi" dropdown. Past entries are merged into the existing four-category result table with a "From Past" column and light purple visual distinction. This is a full-stack feature touching the frontend results display, upload page, and a new backend service for SQLite file management.

## Technical Context

**Language/Version**: TypeScript 5 (frontend), Python 3.11+ (backend)  
**Primary Dependencies**: better-sqlite3 or sqlite3 (backend), existing FastAPI + Next.js stack  
**Storage**: SQLite files saved to `Reconciliation History/` directory at project root, one `.sqlite` file per saved reconciliation  
**Testing**: pytest (backend), Vitest (frontend)  
**Target Platform**: Local desktop app via web browser (localhost)
**Project Type**: Web (frontend + backend)  
**Performance Goals**: Save/load completes in under 3 seconds for typical data (<1000 entries)  
**Constraints**: Running entirely locally, no network storage; file collisions handled by skip+notify  
**Scale/Scope**: Single-user, single-machine; hundreds of discrepancy entries per file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Notes |
|-----------|-------|-------|
| I. Strict Instruction Following | ✅ PASS | Spec fully defined with 12 FRs and 3 clarifications; no ambiguities remain |
| II. Developer Stack Authority | ✅ PASS | Using existing FastAPI/Next.js stack; SQLite is a standard Python library component (stdlib sqlite3) |
| III. Supervised Collaboration | ✅ PASS | Plan follows established project patterns from existing components |
| IV. Constructive Objection | ✅ PASS | No objections — SQLite is the right local format for structured financial data |
| V. Controlled Creativity | ✅ PASS | No novel approaches; straightforward CRUD on SQLite files |
| VI. Ambiguity Resolution | ✅ PASS | All 3 clarifications resolved: SQLite format locked, date-based dedup, "From Past" column label |

**Pre-Phase-0**: ✅ ALL GATES PASS  
**Post-Phase-1**: ✅ ALL GATES PASS — Design artifacts generated: research.md (Phase 0), data-model.md + contracts/ + quickstart.md (Phase 1); agent context updated.

## Project Structure

### Documentation (this feature)

```text
specs/003-open-de-past/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — technology decisions
├── data-model.md        # Phase 1 — SQLite schema & entity definitions
├── quickstart.md        # Phase 1 — setup guide
├── contracts/           # Phase 1 — API contracts
│   ├── save-reconciliation.json
│   ├── list-history.json
│   └── load-history.json
└── tasks.md             # Phase 2 — task breakdown (from /sp.tasks)
```

### Source Code (repository root)

```text
backend/src/
├── api/
│   └── routes.py              # NEW endpoints for history save/list/load
├── models/
│   └── reconciliation_models.py # UPDATE DiscrepancyTransaction to accept fromPast flag
├── services/
│   └── history_service.py     # NEW — SQLite file management service
└── utils/
    └── file_helpers.py        # UPDATE — add history file helpers if needed

frontend/src/
├── app/
│   └── upload/
│       └── page.tsx           # UPDATE — pass history state to UploadForm
├── components/
│   ├── results/
│   │   ├── ReconciliationResults.tsx  # UPDATE — add "Complete Reconciliation" button
│   │   ├── CategorizedResults.tsx     # UPDATE — add "From Past" column + purple background
│   │   └── ManualReconciliation.tsx   # No change expected
│   └── upload/
│       └── UploadForm.tsx     # UPDATE — add "Open Maazi" dropdown above upload zones
├── lib/
│   └── api/
│       └── reconciliationClient.ts  # UPDATE — add save/list/load API calls
└── types/
    ├── reconciliation.types.ts # UPDATE — add fromPast flag to DiscrepancyTransaction
    └── history.types.ts        # NEW — types for history file metadata, save request
```

**Structure Decision**: Web (frontend + backend). Feature spans both layers:
- **Backend**: New `history_service.py` service for SQLite CRUD + new API routes
- **Frontend**: New UI components/elements added to existing pages/components with minimal refactoring
- **Shared**: Types updated to support the `fromPast` discrepancy flag
