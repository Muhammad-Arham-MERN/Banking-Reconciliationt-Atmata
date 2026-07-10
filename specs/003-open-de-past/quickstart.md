# Quickstart: Open de Past

**Branch**: `003-open-de-past` | **Date**: 2026-07-03 | **Phase**: 1

## What This Feature Does

1. **Save** — After reviewing reconciliation results, click "Complete Reconciliation" to save all discrepancies to a SQLite file in the `Reconciliation History/` directory. Optionally provide a custom name.
2. **Load** — On the upload page, use the "Open Maazi" dropdown to select a past history file.
3. **Merge** — When a new reconciliation completes, past discrepancies appear alongside current ones, sorted by date within each category, with a "From Past" column and light purple background.

## How It Works

### Backend (New: `history_service.py`)

- `POST /history/save` — Accepts JSON with discrepancies array + optional custom name. Creates a SQLite database at `Reconciliation History/{name}.sqlite`, writes all entries to a `discrepancies` table.
- `GET /history/list` — Scans `Reconciliation History/` for `.sqlite` files, returns list with metadata (file name, entry count, created date).
- `POST /history/load` — Accepts a filename, reads all entries from the SQLite file, returns them as JSON (frontend marks them with `fromPast=true` during merge).

### Frontend Changes

- **UploadForm.tsx** — Add "Open Maazi" dropdown above upload zones (fetched from `GET /history/list` on mount).
- **ReconciliationResults.tsx** — Add "Complete Reconciliation" button + name input below manual reconciliation section. On click, calls `POST /history/save`. Also sends selected history file to reconciliation endpoint.
- **CategorizedResults.tsx** — Add "From Past" column to discrepancy table. Rows with `fromPast=true` get a light purple background (`bg-purple-50` or similar).
- **Reconciliation flow** — When a history file is selected and reconciliation completes, past discrepancies are loaded via `POST /history/load` and merged into the results array client-side, with date-based deduplication.

## Setup

No additional setup required. The existing project (Python 3.11+, FastAPI backend, Next.js frontend) already has all dependencies. SQLite is built into Python's standard library.

## Key Files

### New files:
- `backend/src/services/history_service.py` — SQLite CRUD operations
- `frontend/src/types/history.types.ts` — TypeScript types for history API
- `specs/003-open-de-past/contracts/*.json` — API contract specifications

### Files to modify:
- `backend/src/api/routes.py` — Add 3 new endpoints
- `backend/src/models/reconciliation_models.py` — Add `fromPast` field to discrepancy model
- `frontend/src/components/upload/UploadForm.tsx` — Add "Open Maazi" dropdown
- `frontend/src/components/results/ReconciliationResults.tsx` — Add save button + name input
- `frontend/src/components/results/CategorizedResults.tsx` — Add "From Past" column + purple styling
- `frontend/src/lib/api/reconciliationClient.ts` — Add save/list/load API methods
- `frontend/src/types/reconciliation.types.ts` — Add `fromPast` field
