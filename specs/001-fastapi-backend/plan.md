# Implementation Plan: Backend API for Bank Reconciliation

**Branch**: `001-fastapi-backend` | **Date**: 2025-06-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-fastapi-backend/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a FastAPI-based backend service that processes bank reconciliation requests by accepting PDF bank statements and Excel company data files via multipart/form-data, storing files locally, extracting tabular data using Tabula-py and Pandas, and returning reconciliation results as a list of dictionaries. The system includes two endpoints: a health check endpoint and the main "karwai" processing endpoint with graceful shutdown capabilities.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI (web framework), Pandas (Excel processing), Tabula-py (PDF table extraction), Uvicorn (ASGI server), python-multipart (file upload handling)  
**Storage**: Local file system (temporary storage for uploaded files during processing)  
**Testing**: pytest (standard Python testing framework), pytest-asyncio (async endpoint testing), pytest-mock (mocking external dependencies)  
**Target Platform**: Local server (Windows 10 Pro environment)  
**Project Type**: Web backend (REST API service)  
**Performance Goals**: 30 seconds max processing time per request, support 10 concurrent requests, 500ms health check response time  
**Constraints**: Must be conformable to frontend requests during startup, graceful shutdown within 10 seconds, local execution only (no cloud deployment), files ≤10MB (PDF) and ≤5MB (Excel)  
**Scale/Scope**: Small local application, typical usage 1-5 concurrent users, 10-100 reconciliation requests per day, single processing operation at a time preferred

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Gate Status: ✅ PASS

**I. Strict Instruction Following**: ✅ COMPLIANT
- Implementation follows spec exactly: FastAPI backend, file processing, two endpoints
- No unauthorized assumptions about functionality
- All functional requirements addressed as specified

**II. Developer Stack Authority**: ✅ COMPLIANT
- Using exact stack specified by Developer: FastAPI, Pandas, Tabula-py
- No alternative frameworks proposed
- Technology choices match Developer requirements exactly

**III. Supervised Collaboration**: ✅ COMPLIANT
- All architectural decisions presented as implementation choices
- No autonomous decisions beyond standard patterns
- Following established FastAPI conventions for file uploads

**IV. Constructive Objection**: ✅ NOT APPLICABLE
- No objections needed - requirements are clear and achievable
- Following standard patterns for the specified technology stack

**V. Controlled Creativity**: ✅ COMPLIANT
- No novel approaches proposed
- Using established FastAPI file upload patterns
- Standard Pandas/Tabula-py data extraction methods

**VI. Ambiguity Resolution**: ✅ COMPLIANT
- Spec was comprehensive and clear on requirements
- No assumptions made about unclear functionality
- All requirements were testable and well-defined

### Code Standards Compliance: ✅ PASS

**Standard 1 (File Headers)**: ✅ PLANNED
- All Python files will begin with `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ`

**Standard 2 (Logical Markers)**: ✅ PLANNED
- Core reconciliation logic methods will include `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`

**Standard 3 (File Footers)**: ✅ PLANNED
- All files will end with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`

### Re-check After Phase 1 Design: ✅ PASS

**I. Strict Instruction Following**: ✅ COMPLIANT
- Data model follows spec exactly for entities and relationships
- API contracts implement exact endpoints specified
- No unauthorized features or functionality added
- All file size limits and validation rules match requirements

**II. Developer Stack Authority**: ✅ COMPLIANT
- Used exact stack: FastAPI, Pandas, Tabula-py as specified
- No alternative frameworks proposed in implementation plan
- Technology choices aligned with research findings and Developer requirements
- Dependencies and versions selected appropriately

**III. Supervised Collaboration**: ✅ COMPLIANT
- Implementation plan presents established patterns only
- No autonomous decisions beyond standard FastAPI practices
- Quick start guide follows Developer's exact requirements
- Project structure aligns with standard FastAPI conventions

**IV. Constructive Objection**: ✅ NOT APPLICABLE
- No objections needed - design phase completed successfully
- All requirements were implementable with specified stack

**V. Controlled Creativity**: ✅ COMPLIANT
- Used standard FastAPI file upload patterns
- Followed established Pandas/Tabula-py documentation
- No novel algorithms or approaches introduced
- Reconciliation logic will follow standard financial practices

**VI. Ambiguity Resolution**: ✅ COMPLIANT
- All technical decisions based on research and best practices
- No assumptions made about unclear requirements
- API contracts align exactly with frontend expectations

### Code Standards Compliance: ✅ PASS

**Standard 1 (File Headers)**: ✅ PLANNED
- Quick start guide includes `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ` in code examples
- Implementation will follow this standard

**Standard 2 (Logical Markers)**: ✅ PLANNED
- Core reconciliation logic will include `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`
- Implementation plan identifies this requirement

**Standard 3 (File Footers)**: ✅ PLANNED
- All files will end with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`
- Quick start guide demonstrates this pattern

### Overall Assessment: ✅ READY FOR IMPLEMENTATION

All constitution gates passed. Design phase completed successfully with full compliance to constitutional principles. Ready to proceed to `/sp.tasks` for detailed task breakdown.

## Project Structure

### Documentation (this feature)

```text
specs/001-fastapi-backend/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure (backend + frontend)
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── file_models.py        # File upload and processing models
│   │   ├── reconciliation_models.py  # Reconciliation result models
│   │   └── api_models.py         # Request/response models for API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py        # Tabula-py PDF processing service
│   │   ├── excel_service.py      # Pandas Excel processing service
│   │   ├── file_storage_service.py  # Local file storage management
│   │   └── reconciliation_service.py  # Core reconciliation logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py             # FastAPI route definitions
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   └── middleware.py         # Custom middleware (logging, error handling)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py         # Input validation utilities
│   │   ├── file_helpers.py       # File processing helpers
│   │   └── response_helpers.py   # Response formatting utilities
│   ├── config.py                 # Application configuration
│   └── main.py                   # FastAPI application entry point
├── tests/
│   ├── __init__.py
│   ├── contract/
│   │   ├── __init__.py
│   │   ├── test_api_contracts.py  # API contract tests
│   │   └── test_data_contracts.py  # Data contract tests
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_file_upload_integration.py  # End-to-end file upload tests
│   │   └── test_reconciliation_integration.py  # Full reconciliation flow tests
│   └── unit/
│       ├── __init__.py
│       ├── test_pdf_service.py     # PDF processing unit tests
│       ├── test_excel_service.py   # Excel processing unit tests
│       ├── test_reconciliation_service.py  # Reconciliation logic unit tests
│       └── test_file_storage_service.py    # File storage unit tests
├── uploads/                         # Temporary file storage directory
├── requirements.txt                # Python dependencies
└── pytest.ini                      # Pytest configuration

frontend/ (existing)
├── src/
│   ├── components/
│   │   └── upload/                 # File upload components
│   ├── app/
│   │   ├── page.tsx               # Home page
│   │   └── upload/
│   │       └── page.tsx           # Upload page
│   ├── types/
│   │   └── upload.ts              # TypeScript type definitions
│   └── lib/
│       ├── validation.ts          # Form validation utilities
│       └── constants.ts           # Application constants
└── tests/
```

**Structure Decision**: Web application structure selected because the feature involves both frontend (existing Next.js application) and backend (new FastAPI service) components. The backend is organized following FastAPI best practices with separation of concerns between models, services, and API layers. The frontend structure remains unchanged as it was previously implemented.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
