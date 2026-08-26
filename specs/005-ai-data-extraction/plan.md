# Implementation Plan: AI-Based Data Extraction (Istikhraj e Data Ma'a AI)

**Branch**: `005-ai-data-extraction` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-ai-data-extraction/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a parallel AI-driven reconciliation flow ("Istikhraj e Data Ma'a AI"). A user uploads a PDF bank statement (from any bank) and an Excel company ledger, selects a past reconciliation history, and submits — with no manual column names, format, or sheet selection. An OpenAI Agents SDK agent (3 tools: `read_excel`, `read_pdf`, `read_pdf_words`) inspects both files and emits a strict `[output]` block describing the PDF layout (columns, header top, rows dropped, column boundaries, band top, date pattern) and the Excel column mapping. A deterministic extractor (`extract_pdf` from `test_results.py`, adapted) slices PDF words at the detected boundaries; Excel processing uses the detected columns. The rest of the pipeline (reconciliation, discrepancies, history save/load, file cleanup) is unchanged. Exposed on a new `/upload-AI` frontend route and a new backend endpoint; the old flow stays intact. Model + API key come from environment variables; detection retries up to 3 times with a graceful retry error; detection runs in parallel for both files; a step-by-step progress indicator shows detection → extraction → reconciliation; no review/correct step.

## Technical Context

**Language/Version**: Python 3.11 (backend, FastAPI); TypeScript/Next.js 14 (frontend, App Router)  
**Primary Dependencies**: `openai-agents` (OpenAI Agents SDK), `litellm` (model provider abstraction, already referenced in test.py), `pdfplumber` (PDF word geometry + extraction), `pandas`/`openpyxl` (Excel), `pydantic` (response parsing), `fastapi`, `python-multipart` (uploads), `asyncio` (parallel detection)  
**Storage**: Existing temporary upload directory (`uploads/`, 20-min retention) + existing history storage (unchanged)  
**Testing**: `pytest` + `pytest-asyncio` + `pytest-mock` (backend); frontend tests under `frontend/tests`  
**Target Platform**: Linux server (backend), Vercel/Next.js (frontend)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Structure detection + results within 2 minutes per submission (SC-003); parallel PDF+Excel detection (FR-019); extraction + reconciliation reuse existing pipeline  
**Constraints**: Env-var model name + API key (FR-010); 3 retries max (FR-008); no review step (FR-017); graceful partial success (FR-018); old flow unmodified (FR-012); step-by-step progress indicator (FR-016)  
**Scale/Scope**: 3 new backend service modules + 1 new backend route + 1 new frontend route; ~50MB max file sizes unchanged

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Strict Instruction Following | ✅ | Spec mandates separate-file implementation, env-var config, 3 retries, no removal of old flow — all encoded in FR-001..FR-019 |
| II. Developer Stack Authority | ✅ | Uses OpenAI Agents SDK + LiteLLM as specified in test.py; no new framework proposals |
| III. Supervised Collaboration | ✅ | All decisions framed as options; no autonomous stack choices |
| IV. Constructive Objection | ✅ | Plan flags risks (data transmission, detection accuracy) with alternatives |
| V. Controlled Creativity | ✅ | The AI detection is a novel approach — but it is developer-specified and prototype-validated (test.py), not AI-proposed |
| VI. Ambiguity Resolution | ✅ | All ambiguities resolved via `/sp.clarify` session (5 Q&A) — none remain |

**Standard compliance** (Code Standards 1-3): All new Python and TypeScript files MUST begin with `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` (or `/** ... */` for TS) and end with `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`; logical crux methods (the agent orchestration and extractor) MUST be marked with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`.

**Gate: PASS** — no violations. Complexity Tracking section not required.

## Project Structure

### Documentation (this feature)

```text
specs/005-ai-data-extraction/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── api-contract.md
│   └── llm-contract.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   ├── ai_structure_detector.py   # NEW: OpenAI Agents SDK agent + 3 tools + retry orchestration
│   │   ├── ai_pdf_processor.py        # NEW: dynamic extract_pdf (from test_results.py) + transform pipeline
│   │   └── ai_excel_processor.py      # NEW: Excel extraction using LLM-detected columns
│   ├── api/
│   │   └── ai_routes.py               # NEW: POST /reconcile-ai endpoint
│   └── config.py                      # MODIFIED: + AI model env vars (AI_MODEL, AI_API_KEY)
├── tests/
│   ├── test_ai_structure_detector.py  # NEW
│   ├── test_ai_pdf_processor.py       # NEW
│   ├── test_ai_excel_processor.py     # NEW
│   └── test_ai_routes.py              # NEW
└── requirements.txt                   # MODIFIED: + openai-agents, litellm

frontend/
├── src/
│   ├── app/
│   │   └── upload-ai/
│   │       └── page.tsx               # NEW: /upload-AI route
│   ├── components/
│   │   └── upload/
│   │       └── UploadAIConfig.tsx     # NEW: AI flow form (file upload + history select + submit)
│   └── lib/
│       └── api.ts                     # MODIFIED: + reconcile-ai API call
└── tests/
    └── upload-ai.test.tsx             # NEW
```

**Structure Decision**: Web application (frontend + backend) per existing repo layout. New AI code is isolated in `backend/src/services/ai_*` modules and one new API router — the existing `pdf_processor.py`, `excel_processor.py`, `routes.py`, and `/upload` route are NOT touched, satisfying FR-012.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

None — Constitution Check passes.

