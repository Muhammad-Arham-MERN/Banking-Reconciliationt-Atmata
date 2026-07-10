# Research & Technology Decisions: Frontend File Upload Interface

**Feature**: 001-file-upload-ui  
**Date**: 2025-01-17  
**Status**: Complete

## Research Tasks Completed

### 1. File Upload Best Practices for Next.js

**Research Focus**: react-dropzone library integration patterns, file size validation, type checking, error handling, progress feedback

**Key Findings**:
- react-dropzone provides comprehensive drag-and-drop functionality out of the box
- Built-in file type validation via `accept` prop
- onDrop callbacks provide immediate user feedback
- File size limits easily enforced in validator functions
- Error messages customizable via fileRejections

**Best Practices Identified**:
- Validate file extensions first for fast feedback
- Provide clear error messages for rejected files
- Show file preview when possible (file name, size, type)
- Handle drag enter/leave states for visual feedback
- Support keyboard navigation for accessibility

### 2. ShadCN UI Component Integration

**Research Focus**: ShadCN UI Input component customization, styling overrides, theme integration, accessibility

**Key Findings**:
- ShadCN UI components are built on Radix UI primitives
- Components are copied into project (full control over styling)
- Tailwind CSS classes can be customized for theme colors
- Input components support validation states and error messages
- Form components integrate well with React state management

**Best Practices Identified**:
- Use ShadCN's CSS variables for theme customization
- Peach-red theme can be applied via Tailwind config
- Components support controlled/uncontrolled patterns
- Built-in accessibility (ARIA labels, keyboard navigation)
- Consistent styling across all form elements

### 3. Conditional Form State Management

**Research Focus**: React state management for dynamic forms, state preservation during format switches

**Key Findings**:
- useState sufficient for 6 fields with simple validation
- useReducer provides better state transitions for conditional logic
- State must be preserved when switching between "debit + credit" and "debit | credit" formats
- Validation state needs to be tracked separately from form state

**Best Practices Identified**:
- Store format selection separately from field values
- Use conditional rendering based on format type
- Preserve field values when switching formats (some fields overlap)
- Clear validation errors when user makes corrections
- Track touched state for each field

### 4. File Validation Strategies

**Research Focus**: Client-side file type validation, user feedback patterns

**Key Findings**:
- Extension checking (`.pdf`, `.xlsx`) provides fast user feedback
- MIME type validation (`application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) adds security layer
- File size validation should happen before upload attempt
- Error messages should be specific about rejection reason

**Best Practices Identified**:
- Validate on file drop and file input change
- Show inline error messages near upload zone
- Use clear language: "Only PDF files accepted" vs generic "Invalid file"
- Reset error state when valid file uploaded
- Support drag-and-drop and click-to-upload interactions

### 5. Form Data Submission Patterns

**Research Focus**: Multipart/form-data submission in Next.js, large file handling

**Key Findings**:
- FormData API native to browsers, no dependencies needed
- fetch API supports FormData for multipart submissions
- Next.js server actions or API routes can handle multipart/form-data
- Large files may need timeout configuration
- Network errors should be handled gracefully

**Best Practices Identified**:
- Collect all form data (files + text fields) into single FormData
- Set appropriate timeouts for large file uploads
- Show loading state during submission
- Handle network errors with retry mechanism or clear error messages
- Reset form on successful submission

## Technology Decisions

### Decision 1: File Upload Library
**Choice**: react-dropzone  
**Rationale**: Industry standard, excellent documentation, built-in accessibility, active maintenance  
**Alternatives Considered**: Native HTML5 API (more control but more code), Dropzone.js (not React-specific)

### Decision 2: Form State Management
**Choice**: React useState + useReducer pattern  
**Rationale**: Sufficient for this scope, no external dependencies, predictable state updates  
**Alternatives Considered**: React Hook Form (overkill for 6 fields), Zustand (unnecessary complexity)

### Decision 3: File Validation Strategy
**Choice**: Multi-layer validation (extension + MIME type)  
**Rationale**: Fast user feedback + security layer, clear error messages  
**Alternatives Considered**: Magic number validation (overkill), server-side only (poor UX)

### Decision 4: Form Submission Approach
**Choice**: Native FormData API with fetch  
**Rationale**: Built-in browser support, no dependency overhead, Next.js compatible  
**Alternatives Considered**: Axios (extra dependency), custom HTTP client (unnecessary)

### Decision 5: Component Organization
**Choice**: Atomic design with feature-based organization  
**Rationale**: Independent components, reusable format selector, clear orchestration  
**Alternatives Considered**: Monolithic component (hard to maintain), page-level (limited reusability)

## Final Technology Stack

**Core Framework**: Next.js 14+ (App Router), React 18+, TypeScript 5+  
**UI Components**: ShadCN UI, react-dropzone  
**Styling**: Tailwind CSS (included with ShadCN)  
**State Management**: React useState + useReducer  
**Form Submission**: FormData API with fetch  
**No Storage Required**: Browser memory during session only
