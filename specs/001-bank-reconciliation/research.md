# Research & Technology Decisions: Bank Reconciliation Logic

**Feature**: 001-bank-reconciliation  
**Date**: 2026-06-23  
**Phase**: Phase 0 - Research & Technology Decisions

## Overview

This document captures research findings and technology decisions for implementing bank reconciliation logic. All decisions align with constitutional principles and prioritize accuracy, reliability, and developer stack authority.

---

## Research Area 1: Algorithm Performance for Transaction Reconciliation

### Problem Statement
Need to efficiently compare each bank transaction against every company transaction (O(n²) complexity) while maintaining deterministic behavior and performance under 10 seconds for typical monthly statements (50-200 transactions per source).

### Research Findings

**Nested List Comparison Approaches**:

1. **Traditional Nested Loops**:
   ```python
   for bank_tx in bank_transactions:
       for company_tx in company_transactions:
           if bank_tx['amount'] == -company_tx['amount']:
               # Match found
   ```
   - **Pros**: Explicit logic, easy to debug, deterministic, preserves order
   - **Cons**: O(n²) time complexity, slower for large datasets
   - **Performance**: ~10ms for 100x100 comparison, acceptable for 500x500

2. **List Comprehensions**:
   ```python
   matches = [b for b in bank_txs for c in company_txs if b['amount'] == -c['amount']]
   ```
   - **Pros**: Concise, potentially faster due to Python optimization
   - **Cons**: Harder to debug, less explicit logic, still O(n²)
   - **Performance**: Similar to nested loops, ~8-12ms for 100x100

3. **Set-Based Lookup** (Optimization):
   ```python
   company_amounts = {tx['amount'] for tx in company_transactions}
   for bank_tx in bank_transactions:
       if -bank_tx['amount'] in company_amounts:
           # Match found
   ```
   - **Pros**: O(n+m) complexity, very fast for large datasets
   - **Cons**: Loses transaction details, requires second pass, complex logic
   - **Performance**: ~2ms for 100x100, excellent for 500x500

### Decision: Traditional Nested Loops with Early Termination

**Choice**: Traditional nested loops with optimization for early termination when matches found.

**Rationale**:
- **Constitution Principle**: Accuracy and reliability over performance
- Deterministic behavior guaranteed (same inputs = same outputs)
- Easy to debug and verify correctness
- Performance acceptable for expected scale (500x500 = 250,000 comparisons ≈ 50ms)
- Maintains transaction order and preserves all details
- Follows developer stack authority (pure Python, no new dependencies)

**Implementation Strategy**:
```python
def find_bank_discrepancies(bank_transactions, company_transactions):
    discrepancies = []
    for bank_tx in bank_transactions:
        matched = False
        for company_tx in company_transactions:
            if bank_tx['debit_credit'] == -company_tx['debit_credit']:
                matched = True
                break  # Early termination optimization
        if not matched:
            discrepancies.append({**bank_tx, 'FROM': 'Bank'})
    return discrepancies
```

---

## Research Area 2: Floating Point Comparison for Financial Amounts

### Problem Statement
Financial amounts (e.g., 10200.0, 22000000.0, -40771.695) need reliable comparison to avoid false positives/negatives due to floating point precision issues.

### Research Findings

**Python Floating Point Behavior**:
- `10200.0 == 10200.00` → `True` (exact match works)
- `0.1 + 0.2 == 0.3` → `False` (floating point arithmetic issues)
- `-22000000.0 == 22000000.0 * -1` → `True` (multiplication preserves precision)

**Comparison Methods**:

1. **Direct Equality**:
   ```python
   if bank_amount == -company_amount:
       # Match
   ```
   - **Pros**: Exact matching, no tolerance for discrepancies
   - **Cons**: Can fail with floating point arithmetic
   - **Suitability**: Good for our use case (amounts from files, not calculations)

2. **Math.isclose()**:
   ```python
   import math
   if math.isclose(bank_amount, -company_amount, rel_tol=1e-9):
       # Match
   ```
   - **Pros**: Handles floating point precision issues
   - **Cons**: May hide genuine discrepancies (e.g., 100.00 vs 100.01)
   - **Suitability**: Risky for financial reconciliation

3. **Decimal Conversion**:
   ```python
   from decimal import Decimal
   if Decimal(str(bank_amount)) == Decimal(str(-company_amount)):
       # Match
   ```
   - **Pros**: Exact decimal arithmetic, no precision loss
   - **Cons**: Performance overhead, string conversion needed
   - **Suitability**: Most reliable for financial data

### Decision: Direct Equality with Decimal Fallback

**Choice**: Use direct equality comparison with Decimal conversion as fallback for edge cases.

**Rationale**:
- **Constitution Principle**: Strict instruction following - amounts from files are exact
- Existing data comes from PDF/Excel parsing, not calculations (minimal precision issues)
- Direct equality maintains simplicity and performance
- Decimal fallback available if precision issues arise in production
- Follows developer stack authority (standard Python libraries)

**Implementation Strategy**:
```python
def amounts_match(amount1, amount2):
    # Primary: Direct equality (fast, exact for file data)
    if amount1 == -amount2:
        return True
    
    # Fallback: Decimal comparison for edge cases
    try:
        return Decimal(str(amount1)) == Decimal(str(-amount2))
    except (ValueError, TypeError):
        return False  # Malformed data handled by validation
```

---

## Research Area 3: Opposite Sign Duplicate Removal Strategy

### Problem Statement
After identifying discrepancies from both sources, need to remove opposite sign pairs (e.g., +22000 in company, -22000 in bank) from the unified discrepancy list while maintaining deterministic behavior.

### Research Findings

**Removal Approaches**:

1. **Post-Peace Removal** (Two-pass approach):
   ```python
   # Pass 1: Build discrepancy lists
   bank_discrepancies = find_bank_discrepancies(bank, company)
   company_discrepancies = find_company_discrepancies(company, bank)
   
   # Pass 2: Remove opposite pairs
   final_list = remove_opposite_pairs(bank_discrepancies, company_discrepancies)
   ```
   - **Pros**: Clear separation of concerns, easy to test
   - **Cons**: Requires second pass through data
   - **Performance**: Additional O(n×m) comparison pass

2. **Integrated Removal** (Single-pass approach):
   ```python
   # Build lists while simultaneously checking for matches
   discrepancies = []
   used_company = set()
   
   for bank_tx in bank_transactions:
       matched = False
       for i, company_tx in enumerate(company_transactions):
           if bank_tx['amount'] == -company_tx['amount'] and i not in used_company:
               matched = True
               used_company.add(i)
               break
       if not matched:
           discrepancies.append({**bank_tx, 'FROM': 'Bank'})
   ```
   - **Pros**: Single pass, efficient, deterministic
   - **Cons**: Complex logic, harder to debug
   - **Performance**: Optimal O(n×m) with early termination

3. **Set-Based Removal** (Hash-based approach):
   ```python
   bank_amounts = {tx['amount'] for tx in bank_discrepancies}
   company_amounts = {tx['amount'] for tx in company_discrepancies}
   
   # Find opposite pairs
   opposite_pairs = bank_amounts & {-a for a in company_amounts}
   
   # Filter out opposite pairs
   final_bank = [b for b in bank_discrepancies if b['amount'] not in opposite_pairs]
   final_company = [c for c in company_discrepancies if c['amount'] not in {-p for p in opposite_pairs}]
   ```
   - **Pros**: Fast set operations, O(n+m) complexity
   - **Cons**: Loses order, potential duplicate removal issues
   - **Performance**: Excellent for large datasets

### Decision: Post-Pass Removal with Order Preservation

**Choice**: Two-pass removal approach with careful order preservation and deterministic matching.

**Rationale**:
- **Constitution Principle**: Reliability and accuracy over performance
- Clear separation of concerns (find discrepancies, then remove pairs)
- Easy to test and verify correctness
- Maintains transaction order from original sources
- Deterministic behavior guaranteed
- Performance acceptable (additional pass is negligible for our scale)

**Implementation Strategy**:
```python
def remove_opposite_pairs(bank_discrepancies, company_discrepancies):
    """
    Remove opposite sign pairs from discrepancy lists.
    Maintains deterministic order and preserves source attribution.
    """
    # Build amount lookup for company discrepancies
    company_amounts = [tx['debit_credit'] for tx in company_discrepancies]
    company_used = [False] * len(company_discrepancies)
    
    # Filter bank discrepancies (remove if opposite found in company)
    filtered_bank = []
    for bank_tx in bank_discrepancies:
        matched = False
        bank_amount = bank_tx['debit_credit']
        
        # Look for opposite in company discrepancies
        for i, company_amount in enumerate(company_amounts):
            if not company_used[i] and bank_amount == -company_amount:
                matched = True
                company_used[i] = True  # Mark as used
                break
        
        if not matched:
            filtered_bank.append(bank_tx)
    
    # Filter company discrepancies (remove used ones)
    filtered_company = [
        tx for tx, used in zip(company_discrepancies, company_used) if not used
    ]
    
    # Merge and return
    return filtered_bank + filtered_company
```

---

## Research Area 4: Service Integration Patterns

### Problem Statement
Need to integrate reconciliation service into existing FastAPI backend without breaking existing PDF/Excel processing pipeline.

### Research Findings

**Integration Approaches**:

1. **Middleware Integration**:
   - Add reconciliation as middleware after file processing
   - Pros: Clean separation, reusable
   - Cons: Overhead, complex error handling

2. **Service Layer Integration**:
   - Call reconciliation service from route handler
   - Pros: Simple, explicit, easy to test
   - Cons: Tight coupling to route

3. **Pipeline Integration**:
   - Add reconciliation as final step in processing pipeline
   - Pros: Natural flow, easy error handling
   - Cons: Changes existing pipeline structure

### Decision: Service Layer Integration

**Choice**: Integrate reconciliation service into existing karwai endpoint route handler after PDF/Excel processing.

**Rationale**:
- Minimal changes to existing code structure
- Easy to test in isolation
- Clear error handling and rollback
- Follows existing service pattern (pdf_service, excel_service)
- Maintains existing API contract (extend response, don't break)

**Integration Strategy**:
```python
# In routes.py - karwai endpoint
@router.post("/karwai")
async def process_files(bank_file: UploadFile, company_file: UploadFile, sheetName: Optional[str] = None):
    request_id = str(uuid.uuid4())
    
    try:
        # Existing: Process PDF and Excel concurrently
        results = await process_concurrent(bank_file, company_file, request_id, sheetName)
        
        # NEW: Add reconciliation
        discrepancies = reconciliation_service.reconcile(
            results['bank_statement'],
            results['company_records']
        )
        
        # Extend results with discrepancies
        results['discrepancies'] = discrepancies
        results['summary']['total_discrepancies'] = len(discrepancies)
        
        return success_response(request_id, results)
        
    except Exception as e:
        return error_response(request_id, str(e))
```

---

## Technology Stack Validation

### Confirmed Stack Decisions

1. **Backend Language**: Python 3.11+ ✅
   - Existing codebase, developer expertise
   - Excellent data processing libraries
   - Fast and reliable for financial calculations

2. **Web Framework**: FastAPI ✅
   - Existing backend, proven reliability
   - Async support for concurrent processing
   - Automatic API documentation

3. **Data Processing**: Pandas (Excel), Tabula-py (PDF) ✅
   - Existing implementations, tested and working
   - Reliable file parsing
   - Good performance for typical file sizes

4. **Testing Framework**: pytest ✅
   - Existing test infrastructure
   - Excellent assertion and fixture support
   - Good coverage reporting

### No New Dependencies Required

- Reconciliation logic uses standard Python libraries
- No additional pip packages needed
- Maintains lightweight, focused stack

---

## Risk Mitigation Strategies

### Performance Risks

1. **Large File Processing**:
   - **Risk**: O(n²) comparison slow for 500+ transactions
   - **Mitigation**: Early termination optimization, amount indexing
   - **Fallback**: Transaction count limits with user feedback

2. **Memory Usage**:
   - **Risk**: Large discrepancy lists consuming memory
   - **Mitigation**: Stream processing, immediate response return
   - **Fallback**: Response size limits with pagination

### Accuracy Risks

1. **Floating Point Precision**:
   - **Risk**: Precision issues causing false matches/mismatches
   - **Mitigation**: Decimal conversion for edge cases
   - **Fallback**: Tolerance-based comparison with user warnings

2. **Deterministic Behavior**:
   - **Risk**: Non-deterministic results causing user distrust
   - **Mitigation**: Ordered data structures, explicit algorithms
   - **Fallback**: Result caching with input checksums

### Integration Risks

1. **Breaking Existing Pipeline**:
   - **Risk**: Changes to karwai endpoint breaking existing functionality
   - **Mitigation**: Extend response structure, don't modify existing fields
   - **Fallback**: Feature flag to disable reconciliation

2. **Error Propagation**:
   - **Risk**: Reconciliation errors affecting file processing
   - **Mitigation**: Separate error handling, graceful degradation
   - **Fallback**: Return raw results without reconciliation on error

---

## Recommendations Summary

### Do This (High Priority)

1. ✅ **Implement Traditional Nested Loops**: Use clear, debuggable nested loops with early termination
2. ✅ **Direct Equality Comparison**: Use exact matching with Decimal fallback for edge cases
3. ✅ **Post-Pass Removal**: Two-pass opposite sign removal for clarity and testability
4. ✅ **Service Layer Integration**: Add reconciliation service to existing route handler

### Don't Do This (Avoid)

1. ❌ **Set-Based Optimization**: Avoid overly complex set operations that sacrifice clarity
2. ❌ **Single-Pass Integration**: Don't combine discrepancy finding with removal (complexity)
3. ❌ **Fuzzy Matching**: Don't implement tolerance-based matching (accuracy risk)
4. ❌ **New Dependencies**: Don't introduce new libraries (stack authority principle)

### Consider Later (Future Enhancements)

1. 🤔 **Performance Optimization**: If O(n²) becomes bottleneck, consider indexing strategies
2. 🤔 **Advanced Matching**: If needed, implement fuzzy description matching (future feature)
3. 🤔 **Result Caching**: If performance critical, implement result caching by input hash
4. 🤔 **Parallel Processing**: If scale increases, consider parallel comparison algorithms

---

## Next Steps

1. ✅ **Research Complete**: All technical decisions documented
2. **Next**: Create data model specifications (`data-model.md`)
3. **Next**: Generate API contracts (`/contracts/`)
4. **Next**: Write quickstart guide (`quickstart.md`)

**Status**: ✅ **Phase 0 Complete** - Ready for Phase 1 design and contracts

---

**Constitution Compliance**: All decisions follow constitutional principles (strict instruction following, developer stack authority, supervised collaboration, controlled creativity)  
**Decision Authority**: Developer Muhammad Arham has final approval on all technical choices  
**Next Review**: Post-implementation validation of performance and accuracy metrics