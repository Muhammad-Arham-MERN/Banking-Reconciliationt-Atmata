# Implementation Plan: Reconciliation Frontend Enhancements

**Branch**: `001-reconciliation-frontend-features` | **Date**: 2026-06-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-reconciliation-frontend-features/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature enhances the existing Bank Reconciliation System with two frontend-only capabilities:
1. **Automatic Categorization**: Transform single reconciliation results table into four categorized sections based on transaction source (Bank/Company) and value polarity (positive/negative)
2. **Manual Reconciliation**: Enable users to selectively remove discrepancy items with real-time calculation preview

**Technical Approach**: Frontend-only implementation leveraging existing backend reconciliation API output, maintaining visual consistency with current column-based table design, and implementing client-side categorization logic and selection state management.

## Technical Context

**Language/Version**: Frontend: TypeScript (Next.js 15+), Backend: Python 3.11+ (existing, no changes required)
**Primary Dependencies**: Frontend: Next.js, React 19+, TypeScript, Tailwind CSS, shadcn/ui components; Backend: FastAPI, Pydantic (existing)
**Storage**: N/A - Frontend state management only; Backend data served via existing API endpoints
**Testing**: Frontend: Vitest/Playwright, React Testing Library; Backend: pytest (existing)
**Target Platform**: Web browser (local execution)
**Project Type**: Web application (frontend + backend backend)
**Performance Goals**: Categorization within 500ms for typical datasets (100-500 transactions); calculation preview updates within 100ms; manual reconciliation execution within 2s
**Constraints**: Must work with existing backend API format; <3s page load time for full results; support up to 1000 transactions; maintain exact visual design consistency
**Scale/Scope**: Single-page results display; typical 100-500 transactions per reconciliation; local execution only (no cloud deployment)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance Analysis

**I. Strict Instruction Following** ✅ PASS
- All functional requirements (FR-001 through FR-020) will be implemented exactly as specified
- No improvisation beyond explicit spec requirements
- All categorization rules will be implemented precisely: Bank+Positive → BANK DEBITED BUT NOT CREDITED IN CASH BOOK, etc.

**II. Developer Stack Authority** ✅ PASS
- Using existing Next.js + Python FastAPI stack (Developer's chosen technology)
- No framework changes proposed
- Frontend enhancements only, respecting existing backend architecture
- shadcn/ui components already in use (component library present in frontend/)

**III. Supervised Collaboration** ✅ PASS
- All technical decisions framed as options for Developer consideration
- No autonomous architectural decisions without explicit approval
- Recommendations only for implementation approach within constraints

**IV. Constructive Objection** ✅ PASS
- No ambiguities or concerns requiring objections at this stage
- Spec is clear and implementable as written
- All edge cases documented in spec

**V. Controlled Creativity** ✅ PASS
- Implementation follows established patterns from existing codebase
- No novel approaches proposed beyond standard React state management
- All design decisions maintain consistency with existing UI

**VI. Ambiguity Resolution** ✅ PASS
- Spec is comprehensive with no vague requirements
- All functional requirements are testable and unambiguous
- Technical approach is straightforward: client-side categorization + selection state

### Code Standards Compliance Plan

- **Standard 1 (File Headers)**: All new TypeScript/React files will begin with `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ`
- **Standard 2 (Logical Markers)**: Critical categorization logic and calculation preview will include `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`
- **Standard 3 (File Footers)**: All files will conclude with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`

### Gate Result: ✅ **APPROVED** - No constitutional violations, ready to proceed

## Project Structure

### Documentation (this feature)

```text
specs/001-reconciliation-frontend-features/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── frontend-types.ts # TypeScript interfaces for categorization
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure (existing)
backend/
├── src/
│   ├── api/            # Existing FastAPI endpoints (no changes required)
│   ├── models/         # Existing data models (no changes required)
│   ├── services/       # Existing reconciliation logic (no changes required)
│   └── utils/          # Existing utilities (no changes required)
└── tests/              # Existing backend tests (no changes required)

frontend/
├── src/
│   ├── app/
│   │   └── upload/     # Existing upload/results page (enhancements here)
│   ├── components/
│   │   ├── results/    # NEW: CategorizedResults, ManualReconciliation controls
│   │   ├── upload/     # Existing upload components
│   │   └── ui/         # Existing shadcn/ui components
│   ├── lib/
│   │   ├── api/        # Existing API client (no changes required)
│   │   └── utils/      # NEW: categorizationUtils.ts, calculationUtils.ts
│   └── types/
│       └── reconciliation.ts  # NEW: Extended types for categorization
└── tests/
    ├── integration/    # NEW: End-to-end categorization + manual reconciliation tests
    └── unit/           # NEW: Unit tests for categorization logic, calculations
```

**Structure Decision**: Web application structure confirmed (frontend + backend). This is a frontend-only feature working with existing backend API output. No backend changes required as reconciliation results API already provides transaction source and value data needed for categorization.

## Complexity Tracking

> **No constitutional violations requiring justification - this section not applicable**

All implementation follows existing patterns and uses current technology stack. No additional complexity introduced beyond standard React state management and TypeScript interfaces.

---

# Phase 0: Research & Technical Decisions

## Research Summary

**Status**: ✅ **COMPLETE** - All research tasks resolved successfully.

Detailed findings documented in [`research.md`](research.md) including:

### Research 1: Existing Backend API Output Format ✅ RESOLVED
- **Finding**: Backend FastAPI provides `DiscrepancyTransaction[]` with all required fields
- **Contract**: `FROM` field (Bank/Company) + `Debit/Credit` field (signed number)
- **Decision**: No backend changes required - frontend categorization sufficient

### Research 2: Current Table Design Implementation ✅ RESOLVED
- **Finding**: `DiscrepancyList.tsx` uses shadcn/ui Table components
- **Pattern**: Column layout with specific styling (badges, color-coded amounts)
- **Decision**: Reuse existing design patterns across four categorized sections

### Research 3: Frontend State Management Patterns ✅ RESOLVED
- **Finding**: Existing codebase uses standard React hooks (useState, useMemo)
- **Pattern**: No external state management libraries
- **Decision**: Use React useState + Set for selection tracking

### Research 4: Testing Framework and Patterns ✅ RESOLVED
- **Finding**: Minimal test coverage, manual testing approach
- **Decision**: QA checklist-based manual testing (test framework out of scope)

---

# Phase 1: Design & Contracts

## Design Summary

**Status**: ✅ **COMPLETE** - All design artifacts created.

### Data Model ([`data-model.md`](data-model.md))
Three new entities designed for frontend presentation:

1. **TransactionCategory** (Enum): Four accounting-specific categories
   - UNPRESENTED CHECKS (Company + Negative)
   - UNCLEARED CHECKS (Company + Positive)
   - BANK DEBITED BUT NOT CREDITED (Bank + Positive)
   - BANK CREDITED BUT NOT DEBITED (Bank + Negative)

2. **CategorizedTransaction** (Interface): Extended transaction model
   - Extends `DiscrepancyTransaction` with category, itemId, display fields
   - Enables selection tracking and organized display

3. **DiscrepancySelectionState** (Interface): React component state
   - Tracks selected items across four categories
   - Manages calculation preview for manual reconciliation

### Type Contracts ([`contracts/frontend-types.ts`](contracts/frontend-types.ts))
Complete TypeScript definitions including:
- `TransactionCategory` enum with four values
- `CategorizedTransaction` interface extending base types
- `DiscrepancySelectionState` for state management
- Type guards and utility types
- Default configurations and empty states

### Implementation Guide ([`quickstart.md`](quickstart.md))
Step-by-step implementation instructions:
- Phase 1: Core utilities (categorization + calculation)
- Phase 2: Enhanced TypeScript types
- Phase 3: Component implementation (CategorizedResults + ManualReconciliation)
- Phase 4: Integration and constitutional compliance
- Verification checklist and troubleshooting guide

---

## Post-Design Constitution Check

*GATE: Re-verify constitutional compliance after Phase 1 design completion.*

### Updated Principle Compliance

**I. Strict Instruction Following** ✅ PASS (POST-DESIGN)
- Design follows spec exactly - no additional features or scope creep
- Categorization rules match spec requirements precisely
- Manual reconciliation workflow implements spec requirements only
- **Verification**: All design artifacts reference specific FR numbers

**II. Developer Stack Authority** ✅ PASS (POST-DESIGN)
- Design uses existing Next.js + shadcn/ui patterns exclusively
- No new frameworks or libraries introduced
- React hooks (useState, useMemo, useCallback) match existing patterns
- **Verification**: Type definitions extend existing interfaces

**III. Supervised Collaboration** ✅ PASS (POST-DESIGN)
- Design recommendations align with Developer's established architecture
- No autonomous architectural decisions made
- All technical choices justified in research.md
- **Verification**: Quickstart provides implementation options, not mandates

**IV. Constructive Objection** ✅ PASS (POST-DESIGN)
- No ambiguities or concerns identified during design phase
- All unknowns from research successfully resolved
- No technical debt or architectural risks introduced
- **Verification**: Research.md confirms no blockers or risks

**V. Controlled Creativity** ✅ PASS (POST-DESIGN)
- Design uses established React component patterns
- No novel architectural approaches proposed
- Categorization logic is straightforward conditional logic
- **Verification**: Data model uses standard TypeScript interfaces

**VI. Ambiguity Resolution** ✅ PASS (POST-DESIGN)
- All design decisions based on concrete code analysis
- No assumptions made about existing system behavior
- Type safety ensured through TypeScript contracts
- **Verification**: Research.md includes code examples and API contracts

### Code Standards Compliance Verification

**Standard 1 (File Headers)**: ✅ Planned
- All new files will begin with `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ`
- Quickstart.md Phase 4 includes verification step

**Standard 2 (Logical Markers)**: ✅ Planned
- Critical categorization logic marked with `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`
- Contract file includes marker at categorization logic section

**Standard 3 (File Footers)**: ✅ Planned
- All new files conclude with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`
- Quickstart.md Phase 4 includes compliance verification

### Updated Gate Result: ✅ **APPROVED** - Design phase complete, ready for implementation

---

## Architectural Decision Consideration

### 📋 Architectural Decision Detected: Frontend-Only Categorization Approach

**Context**: During research and design phases, decision made to implement transaction categorization entirely in the frontend rather than extending backend API.

**Decision Characteristics**:
- **Impact**: Establishes system boundary between presentation layer and business logic
- **Alternatives Considered**: Backend categorization endpoint vs. frontend categorization
- **Scope**: Cross-cutting - affects data flow architecture, separation of concerns, and API contract evolution

**Rationale for Current Decision**:
- Existing API already provides all necessary data (source + value fields)
- Categorization is presentation concern for user organization
- Frontend-only approach maintains API simplicity and backward compatibility
- Reduces backend complexity and deployment requirements

**Trade-offs**:
- **Pros**: No backend changes needed, faster implementation, simpler API contract
- **Cons**: Categorization logic not reusable across clients, must recalculate on each page load

**Documentation Recommendation**: This decision establishes system architectural boundaries and could benefit from ADR documentation for future reference.

**Suggested Action**: Run `/sp.adr frontend-categorization-architecture` to document this decision with full rationale and alternatives if you anticipate future architectural discussions or if this becomes a precedent for other features.

*Note*: ADR creation is optional but recommended for significant architectural decisions that may influence future development.

---

## Implementation Readiness

### ✅ All Planning Phases Complete

**Phase 0 (Research)**: ✅ Complete
- All unknowns resolved through code analysis
- No architectural blockers identified
- Technical approach confirmed feasible

**Phase 1 (Design)**: ✅ Complete
- Data model designed with 3 entities
- Type contracts created in TypeScript
- Implementation guide with step-by-step phases
- Agent context updated successfully

### Ready for Implementation

The planning phase is complete. The implementation can proceed using:

1. **Quickstart Guide**: [`quickstart.md`](quickstart.md) - Step-by-step implementation phases
2. **Type Contracts**: [`contracts/frontend-types.ts`](contracts/frontend-types.ts) - TypeScript definitions
3. **Data Model**: [`data-model.md`](data-model.md) - Entity relationships and validation
4. **Research Findings**: [`research.md`](research.md) - Technical context and decisions

### Next Steps

1. **Option A**: Begin implementation following quickstart.md phases
2. **Option B**: Generate task breakdown with `/sp.tasks` for detailed task tracking
3. **Option C**: Document architectural decision with `/sp.adr frontend-categorization-architecture`

**Recommendation**: Use `/sp.tasks` to generate detailed, actionable task list from this plan.