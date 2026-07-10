# Research: Open de Past Technology Decisions

**Branch**: `003-open-de-past` | **Date**: 2026-07-03 | **Phase**: 0

## Technology Decisions

### Storage Format: SQLite
- **Decision**: Use SQLite, one `.sqlite` file per reconciliation save
- **Rationale**: User explicitly specified SQLite. It's the right format for structured financial data on a local filesystem — self-contained, ACID-compliant, no server needed. Python's stdlib `sqlite3` module means zero additional dependencies.
- **Alternatives considered**: JSON (no query capability, risk of corruption), CSV (no schema enforcement, no type safety), pickle (Python-only, opaque)

### SQLite Library: Python stdlib sqlite3
- **Decision**: Use Python's built-in `sqlite3` module in the backend
- **Rationale**: Zero dependencies to install. The backend already runs on Python/FastAPI. SQLite files are created and managed server-side via the API.
- **Alternatives considered**: `better-sqlite3` (faster, but requires native compilation — adds deployment complexity)

### History File Storage Location
- **Decision**: `Reconciliation History/` at the project root directory
- **Rationale**: User explicitly specified this. It keeps history separate from source code in `backend/` and `frontend/`. The backend needs write access to this path.
- **Note**: The backend will resolve the project root via a configurable path setting (default: one level up from `backend/`)

### Duplicate Detection Strategy
- **Decision**: Compare by (transaction details + transaction date). Same details + same date = duplicate (suppress). Same details + different date = distinct entries (show both).
- **Rationale**: Clarified with user in session 2026-07-03. The date component is the critical differentiator — same transaction may recur legitimately across months.

### Merge Ordering
- **Decision**: Interleave past and current entries by transaction date ascending within each category
- **Rationale**: Clarified with user. Provides a true chronological view of all discrepancies.

### UI Column Label
- **Decision**: "From Past" column with light purple row background
- **Rationale**: Clarified with user. "From Past" is the exact label requested.

## Dependencies

### Backend (new)
- **Python stdlib `sqlite3`**: No installation needed — part of Python 3.11+
- **`pathlib` to `Path`**: Already used in the project (file_helpers.py)

### Frontend (new)
- No new npm packages needed. Existing Tailwind CSS supports custom colors for the purple background. Existing table components can be extended.

## Integration Patterns

### API Design
- Follow existing FastAPI patterns: `POST` for creating, `GET` for listing/reading
- Reuse the existing `ErrorResponse` model for error cases
- Files are managed server-side (backend reads/writes SQLite files); frontend sends only metadata + discrepancy data

### Frontend State Flow
1. **UploadForm** — new `Open Maazi` dropdown at the top; selected file stored as state
2. **ReconciliationResults** — new `Complete Reconciliation` button + name input below manual reconciliation button
3. **CategorizedResults** — new `From Past` column added to the discrepancy table, past rows get purple background
4. Selected history file ID passed from UploadForm → ReconciliationResults → API call merges past discrepancies
