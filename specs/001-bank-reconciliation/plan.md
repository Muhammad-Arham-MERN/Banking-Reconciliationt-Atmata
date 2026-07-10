# Implementation Plan: Bank Reconciliation Logic

**Branch**: `001-bank-reconciliation` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bank-reconciliation/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement transaction reconciliation logic for the Banking Reconciliation System that compares bank statements against company records based on opposite sign amounts. The system will identify discrepancies (transactions present in one source but not the other), remove matching opposite-sign pairs, and present a unified discrepancy list with source attribution.

**Technical Approach**: Add reconciliation service module to existing FastAPI backend that processes transaction lists from PDF/Excel pipeline, performs deterministic amount-based comparison, and returns structured discrepancy results via existing karwai endpoint.

## Technical Context

**Language/Version**: Python 3.11+ (existing backend), TypeScript 5.x (existing frontend)
**Primary Dependencies**: FastAPI (existing), Pandas (existing for Excel), Tabula-py (existing for PDF)
**Storage**: File-based temporary storage with automatic cleanup (existing)
**Testing**: pytest (existing backend), Jest (existing frontend)
**Target Platform**: Local Windows machine (user workstation)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 
- Process 26 bank + 20 company transactions in under 10 seconds
- Support concurrent processing of PDF and Excel files
- Maintain sub-second reconciliation logic on top of existing file processing

**Constraints**:
- Must integrate with existing file upload and processing pipeline
- Must preserve deterministic behavior (same inputs = same outputs)
- Must handle edge cases (empty lists, duplicate amounts, large values)
- Must follow strict instruction following and developer stack authority

**Scale/Scope**:
- Single-user local application
- Typical monthly statement: 50-200 transactions per source
- Maximum expected: 500 transactions per source
- Memory footprint: Keep under 100MB during processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation

✅ **Strict Instruction Following**: Reconciliation logic will follow specification exactly - amount-based matching only, no fuzzy matching or creative interpretation of transaction matching rules

✅ **Developer Stack Authority**: Using existing Python/FastAPI backend, no new framework introductions. Reconciliation logic will be pure Python functions that integrate with existing services layer

✅ **Supervised Collaboration**: Technical decisions (algorithm implementation, data structures) will be presented as options for Developer approval, not autonomous choices

✅ **Constructive Objection**: No objections to specification requirements. Amount-based matching is clear and appropriate for banking reconciliation

✅ **Controlled Creativity**: Will use straightforward comparison algorithms. No novel approaches unless explicitly approved by Developer

✅ **Ambiguity Resolution**: Specification is clear on matching logic (amounts only). No assumptions needed beyond explicit requirements

### Code Standards Compliance
- ✅ File headers with بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
- ✅ Logical method markers for reconciliation algorithms
- ✅ File footers with وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ

**Status**: ✅ **PASSED** - No violations, all constitutional requirements satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-bank-reconciliation/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── reconciliation-api.json
│   └── data-structures.json
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── reconciliation_models.py      # NEW: Reconciliation data models
│   ├── services/
│   │   └── reconciliation_service.py     # NEW: Core reconciliation logic
│   ├── api/
│   │   └── routes.py                      # MODIFY: Add reconciliation to karwai endpoint
│   └── utils/
│       └── response_helpers.py           # MODIFY: Add discrepancy formatting
└── tests/
    ├── unit/
    │   └── test_reconciliation_service.py # NEW: Unit tests for reconciliation logic
    └── integration/
        └── test_reconciliation_flow.py     # NEW: End-to-end reconciliation tests

frontend/
├── src/
│   ├── components/
│   │   └── results/
│   │       └── DiscrepancyList.tsx        # NEW: Display discrepancy results
│   ├── types/
│   │   └── reconciliation.types.ts        # NEW: TypeScript types for reconciliation
│   └── lib/
│       └── api/
│           └── reconciliationClient.ts    # NEW: API client for reconciliation results
└── tests/
    └── components/
        └── DiscrepancyList.test.tsx       # NEW: Component tests
```

**Structure Decision**: Web application structure detected (frontend + backend). Reconciliation logic will be added as new service module to existing backend with corresponding frontend display components. Integration with existing karwai endpoint maintains API consistency while extending functionality.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No constitutional violations | Plan follows all constitutional principles |

---

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **Algorithm Performance Research**: 
   - Task: "Research efficient O(n²) comparison algorithms for transaction reconciliation in Python"
   - Focus: Nested list comparison performance with up to 500 transactions per list
   - Decision needed: Optimize comparison loops or use set-based approaches

2. **Floating Point Comparison Research**:
   - Task: "Research best practices for financial amount comparison in Python"
   - Focus: Handling floating point precision for monetary values (e.g., 10200.0 vs 10200.00)
   - Decision needed: Exact equality vs tolerance-based comparison

3. **Opposite Sign Matching Research**:
   - Task: "Research deterministic approaches to opposite sign duplicate removal"
   - Focus: Ensuring consistent removal of matching pairs without side effects
   - Decision needed: Removal strategy and order preservation

### Technology Choices to Validate

1. **Data Structure Choice**: Lists vs Sets for transaction comparison
   - Lists: Maintain order, simple iteration, O(n²) comparison
   - Sets: Fast lookup, lose order, require hashable transactions
   - Decision: Lists with order preservation (Constitution Principle: reliability)

2. **Comparison Algorithm**: Nested loops vs. list comprehensions
   - Nested loops: Explicit logic, easy to debug, deterministic
   - List comprehensions: Concise, potentially faster, harder to debug
   - Decision: Nested loops for clarity and debuggability (Constitution Principle: accuracy)

3. **Amount Comparison**: Direct equality vs. math.isclose()
   - Direct equality: Exact match, assumes consistent formatting
   - math.isclose(): Handles floating point issues, may hide real discrepancies
   - Decision: Direct equality with decimal conversion (Constitution Principle: strict instruction following)

### Integration Patterns to Research

1. **Service Integration Pattern**: How to call reconciliation from existing karwai endpoint
2. **Error Handling Pattern**: How to handle reconciliation errors in existing pipeline
3. **Data Flow Pattern**: How to pass results between PDF/Excel processing and reconciliation

---

## Phase 1: Design & Contracts

### Data Model Design

**Core Entities**:

1. **BankTransaction**
   - Fields: transaction_date (str), transaction_detail (str), debit_credit (float)
   - Source: Bank statement PDF
   - Validation: Required fields, numeric debit_credit

2. **CompanyTransaction**
   - Fields: transaction_date (str), transaction_detail (str), debit_credit (float)
   - Source: Company records Excel
   - Validation: Required fields, numeric debit_credit

3. **DiscrepancyTransaction**
   - Fields: transaction_date (str), transaction_detail (str), debit_credit (float), from_source (str)
   - Source: Reconciliation output
   - Validation: from_source must be "Bank" or "Company"

4. **ReconciliationResult**
   - Fields: request_id (str), processing_status (str), processing_timestamp (str), summary (dict), discrepancies (list), errors (list)
   - Source: Final reconciliation output
   - Validation: Complete discrepancy list with proper source attribution

**Data Flow**:
```
PDF Processing → BankTransaction List
                              ↓
                        Reconciliation Service → Discrepancy List → ReconciliationResult
                              ↑
Excel Processing → CompanyTransaction List
```

### API Contract Design

**Modified Endpoint**: `POST /karwai`

**Request**: (Existing - no changes)
```json
{
  "bank_statement": "file.pdf",
  "company_records": "file.xlsx",
  "sheetName": "Sheet1"  // optional
}
```

**Response**: (Extended)
```json
{
  "request_id": "uuid",
  "processing_status": "completed|partial|error",
  "processing_timestamp": "ISO8601",
  "summary": {
    "total_bank_transactions": 26,
    "total_company_transactions": 20,
    "total_discrepancies": 15,
    "bank_only_discrepancies": 8,
    "company_only_discrepancies": 7,
    "processing_duration_ms": 7153,
    "concurrent_processing": true
  },
  "results": {
    "bank_statement": [...],      // Existing: Raw bank transactions
    "company_records": [...],      // Existing: Raw company transactions
    "discrepancies": [             // NEW: Unified discrepancy list
      {
        "Transaction_date": "2026-05-06",
        "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515",
        "Debit/Credit": -40771.695,
        "FROM": "Bank"
      },
      {
        "Transaction_date": "2026-05-04",
        "Transaction Detail": "Payment Suzuki Azim Motors WHT 5.515",
        "Debit/Credit": 6771.238,
        "FROM": "Company"
      }
    ]
  },
  "errors": [],
  "message": "Reconciliation complete - Found 15 discrepancies"
}
```

### Quick Start Guide

**Local Development Setup**:

1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Testing Reconciliation**:
   - Upload test bank statement PDF and company records Excel
   - Check `/docs` endpoint for API documentation
   - Review discrepancy results in frontend display

**Implementation Order**:
1. Create reconciliation service module
2. Add unit tests for core logic
3. Integrate with existing karwai endpoint
4. Add frontend display components
5. End-to-end integration testing

---

## Implementation Phases

### Phase 1: Core Reconciliation Service (Priority: P1)

**Files to Create**:
- `backend/src/services/reconciliation_service.py`
- `backend/src/models/reconciliation_models.py`
- `backend/tests/unit/test_reconciliation_service.py`

**Implementation Tasks**:
1. Implement amount-based transaction comparison
2. Implement opposite sign duplicate removal
3. Implement deterministic discrepancy list generation
4. Add comprehensive unit tests

**Success Criteria**:
- All unit tests pass
- Reconciliation produces consistent results for same inputs
- Performance: <100ms for 100x100 transaction comparison

### Phase 2: API Integration (Priority: P1)

**Files to Modify**:
- `backend/src/api/routes.py`
- `backend/src/utils/response_helpers.py`

**Implementation Tasks**:
1. Extend karwai endpoint to call reconciliation service
2. Add reconciliation results to API response
3. Update response formatting with discrepancy summary
4. Add integration tests

**Success Criteria**:
- Existing file upload continues to work
- Reconciliation results appear in API response
- Error handling works correctly

### Phase 3: Frontend Display (Priority: P2)

**Files to Create**:
- `frontend/src/components/results/DiscrepancyList.tsx`
- `frontend/src/types/reconciliation.types.ts`
- `frontend/src/lib/api/reconciliationClient.ts`

**Implementation Tasks**:
1. Create TypeScript types for reconciliation results
2. Build discrepancy list display component
3. Add source attribution (FROM: Bank/Company) highlighting
4. Add sorting and filtering options
5. Component tests

**Success Criteria**:
- Discrepancies display correctly with source attribution
- Users can easily identify bank-only vs company-only transactions
- Performance: Smooth rendering of 100+ discrepancies

### Phase 4: Edge Cases & Error Handling (Priority: P3)

**Files to Modify**:
- `backend/src/services/reconciliation_service.py`
- `backend/src/api/routes.py`

**Implementation Tasks**:
1. Handle empty transaction lists
2. Handle malformed transaction data
3. Handle extremely large monetary values
4. Add comprehensive error messages
5. Add edge case tests

**Success Criteria**:
- All edge cases handled gracefully
- Clear error messages for users
- No crashes on unusual data

---

## Risk Analysis & Mitigation

### Technical Risks

1. **Performance Risk**: O(n²) comparison might be slow for large files
   - **Mitigation**: Optimize inner loop with early termination, consider set-based lookups for amounts
   - **Fallback**: Implement transaction count limits with user feedback

2. **Floating Point Risk**: Amount comparison precision issues
   - **Mitigation**: Convert to Decimal for comparison, standardize precision
   - **Fallback**: Implement tolerance-based comparison if precision issues arise

3. **Integration Risk**: Breaking existing file processing pipeline
   - **Mitigation**: Add reconciliation as optional step, preserve existing response structure
   - **Fallback**: Feature flag to disable reconciliation if issues arise

### Architectural Risks

1. **Complexity Risk**: Adding logic to existing endpoint
   - **Mitigation**: Separate service module keeps logic isolated and testable
   - **Fallback**: Rollback to existing endpoint structure if needed

2. **Data Consistency Risk**: Reconciliation results not matching expectations
   - **Mitigation**: Comprehensive test suite with known good/bad cases
   - **Fallback**: Provide raw transaction data alongside discrepancies for manual verification

---

## Success Metrics

### Functional Metrics
- ✅ 100% of opposite sign pairs correctly removed
- ✅ 100% of genuine discrepancies identified
- ✅ Zero false positives in discrepancy list
- ✅ Deterministic behavior (same inputs = same outputs)

### Performance Metrics
- ✅ Reconciliation completes in <100ms for typical monthly statements (50-200 transactions)
- ✅ Total processing time (PDF + Excel + reconciliation) under 10 seconds
- ✅ Memory usage stays under 100MB during processing

### Quality Metrics
- ✅ All unit tests pass with >90% code coverage
- ✅ All integration tests pass
- ✅ No regression in existing file processing functionality
- ✅ Clear error messages for all failure scenarios

---

## Next Steps

1. **Phase 0 Research**: Complete technology research and decision documentation in `research.md`
2. **Phase 1 Design**: Create detailed data model and API contracts in `data-model.md` and `/contracts/`
3. **Phase 1 Quickstart**: Generate developer quickstart guide
4. **Phase 2 Tasks**: Use `/sp.tasks` to generate actionable implementation tasks

**Immediate Action**: Run Phase 0 research to resolve algorithm and technology decisions before implementation begins.