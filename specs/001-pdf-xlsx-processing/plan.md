# Implementation Plan: PDF and Excel File Processing for Bank Reconciliation

**Branch**: `001-pdf-xlsx-processing` | **Date**: 2025-06-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pdf-xlsx-processing/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement comprehensive file processing capabilities for bank reconciliation by enabling the system to extract transaction data from PDF bank statements (using tabula-py) and Excel company records (using pandas). The system will process both file types asynchronously and simultaneously, merge debit/credit columns with proper sign handling, and return standardized transaction datasets for downstream reconciliation logic.

**Technical Approach**: Follow the proven test.py implementation pattern for PDF processing with positional column mapping, implement pandas-based Excel processing with user-provided column name mappings, and leverage FastAPI's async capabilities for concurrent file processing.

## Technical Context

**Language/Version**: Python 3.11+ (existing backend environment)
**Primary Dependencies**: FastAPI 0.104.1, pandas 2.1.4, tabula-py 2.9.0, openpyxl 3.3.0 (all already in requirements.txt)
**Storage**: Local file system via existing uploads/ directory infrastructure
**Testing**: pytest 7.4.3 with async support (pytest-asyncio 0.21.1)
**Target Platform**: Local Windows/Linux server execution (no cloud deployment required)
**Project Type**: Web application backend (enhancing existing FastAPI service)
**Performance Goals**: 
- PDF processing: <30 seconds for 10-page statements with 100+ transactions
- Excel processing: <10 seconds for files with 500+ transactions  
- Concurrent processing: Faster total completion time than sequential processing
**Constraints**:
- MUST follow test.py implementation pattern exactly for PDF processing
- Must maintain existing karwai POST endpoint structure and parameter validation
- Must handle malformed files gracefully without crashing
- Must ensure zero data loss during debit/credit merging process
**Scale/Scope**: Single server local execution, typical reconciliation workloads (10-50 transactions per statement), support for multiple bank statement formats

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Assessment

**✅ Strict Instruction Following**: Implementation will follow spec.md requirements exactly, particularly FR-021 (follow test.py pattern precisely) and FR-011 through FR-015 (debit/credit merging logic with sign handling).

**✅ Developer Stack Authority**: Using existing tech stack (FastAPI, pandas, tabula-py) as chosen by Developer Muhammad Arham. No alternative frameworks proposed.

**✅ Supervised Collaboration**: All technical decisions (e.g., async processing patterns, error handling approaches) will be framed for Developer approval.

**✅ Constructive Objection**: Will identify any ambiguities in edge cases (e.g., malformed PDF handling, date format variations) with constructive alternatives.

**✅ Controlled Creativity**: Novel approaches for error handling or performance optimization will be explicitly proposed for approval.

**✅ Ambiguity Resolution**: Will immediately clarify any vague requirements, particularly around error handling scenarios for corrupted files or invalid column mappings.

### Code Standards Compliance

**✅ File Headers**: All new files will begin with `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ`

**✅ Logical Method Markers**: Critical file processing logic (PDF extraction, Excel parsing, debit/credit merging) will begin with `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`

**✅ File Footers**: All files will conclude with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`

**GATE RESULT**: ✅ PASS - All constitutional requirements met. Ready for Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-xlsx-processing/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── api-contract.md  # API specification
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── routes.py              # Enhanced with file processing logic
│   ├── services/
│   │   ├── pdf_processor.py      # NEW: PDF processing service (tabula-py)
│   │   ├── excel_processor.py    # NEW: Excel processing service (pandas)
│   │   └── file_validator.py     # NEW: File validation and error handling
│   ├── models/
│   │   ├── api_models.py          # Existing: API response models
│   │   └── processing_models.py  # NEW: Processing result models
│   └── utils/
│       ├── file_helpers.py       # Existing: File upload/download utilities
│       └── data_transformers.py  # NEW: Data transformation utilities
└── tests/
    ├── unit/
    │   ├── test_pdf_processor.py
    │   ├── test_excel_processor.py
    │   └── test_data_transformers.py
    └── integration/
        └── test_file_processing_flow.py

uploads/                            # Existing: Local file storage
├── pdfs/                           # NEW subdirectory for PDF files
└── excels/                         # NEW subdirectory for Excel files

test.py                             # Existing: PDF implementation reference pattern
```

**Structure Decision**: Enhancing existing backend structure with new service layer for file processing. Following established patterns (models/, services/, utils/) while introducing dedicated processing services to maintain separation of concerns and testability.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A - No violations | All requirements align with constitution | Monolithic approach rejected for maintainability and testability requirements |