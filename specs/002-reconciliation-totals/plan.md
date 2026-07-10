# Implementation Plan: Reconciliation Totals & Verification

**Branch**: `002-reconciliation-totals` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-reconciliation-totals/spec.md`

## Summary

Extract last-row "Balance" from bank statement PDF and last-row "Aggregated Total" from XLSX (column name user-provided), return both via the `/karwai` API. On the frontend, display as "Bank Net Total" and "Company Net Total", apply discrepancy adjustments (Uncleared checks, Unpresented checks → Bank; Bank Debited/Credited differences → Company), auto-subtract, and show "Reconciliation Successful, Balanced" or the difference.

## Technical Context

**Language/Version**: Python 3.12+ (backend) / TypeScript 5.x (frontend)  
**Primary Dependencies**: FastAPI 0.104+, Pydantic v2, tabula-py 2.9, pandas, openpyxl 3.1 (backend) / Next.js 16, React 19, Tailwind CSS v4, lucide-react (frontend)  
**Storage**: Stateless — no database, temporary file upload with guaranteed cleanup  
**Testing**: pytest with coverage, asyncio mode (backend) / vitest (frontend — single test file exists)  
**Target Platform**: Local web app (http://localhost:8000 backend, http://localhost:3000 frontend)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Sub-10-second total processing for typical bank statement PDFs and XLSX files  
**Constraints**: Stateless processing; no persistent storage; CPU-bound PDF/extraction runs in thread pool  
**Scale/Scope**: Single-user local reconciliation tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Strict Instruction Following | ✅ PASS | Spec is explicit about Balance extraction, Aggregated Total extraction, and display requirements |
| II | Developer Stack Authority | ✅ PASS | Feature uses existing stack (Python/FastAPI, Next.js/React) — no new frameworks introduced |
| III | Supervised Collaboration | ✅ PASS | Technical decisions documented for developer review |
| IV | Constructive Objection | ✅ PASS | No objections — approach is straightforward extension of existing patterns |
| V | Controlled Creativity | ✅ PASS | No novel algorithms — standard column extraction and arithmetic |
| VI | Ambiguity Resolution | ✅ PASS | All requirements are clear from the feature description |

## Project Structure

### Documentation (this feature)

```text
specs/002-reconciliation-totals/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── api_models.py              # + totals fields to ReconciliationResult
│   │   └── processing_models.py       # + Balance, AggregatedTotal to processing results
│   ├── services/
│   │   ├── pdf_processor.py           # + extract last Balance column value
│   │   └── excel_processor.py         # + extract last Aggregated Total column value
│   ├── api/
│   │   └── routes.py                  # + aggregatedTotalColumn form param, totals in response
│   └── ... existing files unchanged
└── tests/
    ├── unit/
    └── integration/

frontend/
├── src/
│   ├── components/
│   │   ├── upload/
│   │   │   └── ColumnMappingFields.tsx # + Aggregated Total column name input
│   │   └── results/
│   │       ├── ReconciliationResults.tsx # + totals section, adjusted totals, verdict
│   │       └── ReconciliationTotals.tsx  # NEW: totals display + adjustment + verdict card
│   ├── lib/
│   │   └── api/
│   │       └── reconciliationClient.ts   # + aggregatedTotalColumn parameter
│   └── types/
│       └── reconciliation.types.ts       # + bank_net_total, company_net_total, etc.
└── tests/
```

**Structure Decision**: Web application with existing backend/ + frontend/ directories. Feature extends existing files with new fields and adds one new frontend component for the totals display section.

## Complexity Tracking

> No Constitution violations to justify. Feature is a straightforward extension of existing patterns.
