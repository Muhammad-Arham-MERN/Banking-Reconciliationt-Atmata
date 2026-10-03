# Contract — Finalized Credit/Debit Sign Convention

**Feature**: `011-company-employee-wiring` | **Spec**: FR-012, FR-013, FR-014
**Status**: Canonical end-to-end — presentation, backend reconciliation logic, and database values all use this one mapping.

This is not a network contract; it is the ruleset every layer must obey for the `Debit/Credit` amount of a reconciliation row.

---

## 1. Required category signs (what the user sees)

### Bank mode
| Category | Sign | Basis |
|----------|------|-------|
| Unpresented Checks | **− negative** | credited in cashbook |
| Uncleared Checks | **+ positive** | debited in cashbook |
| Bank Debited but not credited in cashbook | **+ positive** | bank debit |
| Bank Credited but not debited in cashbook | **− negative** | bank credit |

### Vendor mode
| Category | Sign | Basis |
|----------|------|-------|
| Unpresented Checks | **− negative** | credited in cashbook |
| Uncleared Checks | **+ positive** | debited in cashbook |
| Vendor Debits | **− negative** | vendor debit |
| Vendor Credit | **+ positive** | vendor credit |

---

## 2. Canonical source-row mapping (what is produced and stored)

For the `Debit/Credit` value on each row (the value persisted in `reconciliation_data.data`):

| Ledger (`FROM`) | Debit | Credit |
|-----------------|-------|--------|
| Company (cashbook) | **+** | **−** |
| Bank | **+** | **−** |
| Vendor | **−** | **+** |

Category assignment follows from the mapping:
- `Company + (debit)` → Uncleared Checks (+)
- `Company − (credit)` → Unpresented Checks (−)
- `Bank + (debit)` → Bank Debited but not credited (+)
- `Bank − (credit)` → Bank Credited but not debited (−)
- `Vendor + (credit)` → Vendor Credit (+)
- `Vendor − (debit)` → Vendor Debits (−)

> **This flips the previous behaviour** for Bank (was credit +, debit −) and Vendor (was credit −, debit +). Company/cashbook is unchanged.

---

## 3. Enforcement points (must all agree)

| Layer | Location | Change |
|-------|----------|--------|
| Backend engine | reconciliation extractor(s) that assign `Debit/Credit` for Bank and Vendor rows | flip polarity to match §2 |
| Database | `reconciliation_data.data` (`Debit/Credit`), `reconciliation_type` | new saves use §2; existing rows not backfilled |
| Frontend categorization | `frontend/src/lib/utils/categorizationUtils.ts` — `categorizeTransaction`, `getDisplayAmount`, `categoryLabel` | update the `isPositive` tests for bank/vendor per §2 |
| Frontend classification (legacy path) | `frontend/src/components/results/ReconciliationResults.tsx` — `categorizeDiscrepancy` | update per §2 |
| Frontend totals/verdict | `frontend/src/components/results/ReconciliationTotals.tsx` (+ `CategorizedResults.tsx` adjusted-balance block) | recompute adjustment sums and the adjusted balances so the verdict stays consistent with the displayed signs (FR-014) |
| History / export | saved reconciliations rendering + any export | render the stored signs; no per-surface sign flip |

---

## 4. Invariant to verify

> For every surface (results tables, per-category subtotals, adjustment panel, totals & verdict, saved history, export), the displayed sign of each category equals the table in §1, and the computed verdict never contradicts those signs.

---

## 5. Known consequence

Reconciliations saved **before** this change were written with the old Bank/Vendor polarity. They are not backfilled (the original source polarity cannot be reconstructed reliably). Re-viewing a legacy saved file shows its stored values as-is; re-running the reconciliation regenerates it under §2. Accepted per research D6.
