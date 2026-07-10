# Data Model: Reconciliation Totals & Verification

## Entities

### BankNetTotal
| Field | Type | Description | Source |
|-------|------|-------------|--------|
| value | float | Last non-null Balance value from PDF bank statement | PDF processor raw DataFrame, `Balance` column, last row |
| column_name | string | Always `"Balance"` | Fixed column in PDF statement |
| status | enum | `"found"`, `"missing"`, `"invalid"` | Determined during extraction |

**Validation rules**:
- Value must be numeric (parseable as float after stripping currency symbols and commas)
- If column not found in extracted data → status = `"missing"`
- If last cell is empty or non-numeric → status = `"invalid"`

### CompanyNetTotal
| Field | Type | Description | Source |
|-------|------|-------------|--------|
| value | float | Last non-null value from user-specified Aggregated Total column | Excel processor, user-provided column name, last row |
| column_name | string | User-provided (e.g., `"Grand Total"`, `"Aggregated Total"`) | Frontend POST parameter `aggregatedTotalColumn` |
| status | enum | `"found"`, `"missing"`, `"invalid"` | Determined during extraction |

**Validation rules**:
- Value must be numeric (parseable as float after stripping currency symbols and commas)
- If column name not provided or column not found → status = `"missing"`
- If last cell is empty or non-numeric → status = `"invalid"`

### DiscrepancyAdjustment
| Field | Type | Description |
|-------|------|-------------|
| category | enum | `"uncleared_checks"`, `"unpresented_checks"`, `"bank_debited_not_credited"`, `"bank_credited_not_debited"` |
| amount | float | Sum of all discrepancy amounts in this category |
| count | int | Number of discrepancy items in this category |

**Adjustment rules**:
- Uncleared checks → Added to Bank Net Total
- Unpresented checks → Added to Bank Net Total
- Bank Debited But not credited in cashbook → Added to Company Net Total
- Bank Credited But not debited in cashbook → Added to Company Net Total

### AdjustedTotals
| Field | Type | Description |
|-------|------|-------------|
| adjusted_bank_total | float | Bank Net Total + Uncleared checks + Unpresented checks |
| adjusted_company_total | float | Company Net Total + Bank Debited/Not Credited + Bank Credited/Not Debited |
| difference | float | Adjusted Bank Total - Adjusted Company Total |

### ReconciliationVerdict
| Field | Type | Description |
|-------|------|-------------|
| is_balanced | boolean | True when `difference` = 0 (within floating-point tolerance) |
| difference | float | Absolute difference between adjusted totals |
| message | string | `"Reconciliation Successful, Balanced"` if balanced, otherwise shows difference |
| higher_side | string | `"Bank"` or `"Company"` indicating which adjusted total is larger (when unbalanced) |

**Floating-point tolerance**: Values are considered equal if `abs(difference) < 0.001`.

## State Transitions

```
Extract Balance PDF value    Extract Aggregated Total XLSX value
         |                              |
         ↓                              |
    BankNetTotal found          CompanyNetTotal found
         |                              |
         ↓                              ↓
    Apply discrepancy          Apply discrepancy
    adjustments (+ unchecked   adjustments (+ bank
    checks + unpresented       debited/credited diff)
    checks)                         |
         |                          |
         ↓                          ↓
    Adjusted Bank Total     Adjusted Company Total
         \                          /
          ↓                        ↓
           →     Subtract          ←
                      |
                      ↓
            ReconciliationVerdict
            Balanced / Not Balanced
```

## Data Flow (API Contract)

### Request (additional form field)

```
POST /karwai
Content-Type: multipart/form-data

... existing fields ...
aggregatedTotalColumn: "Aggregated Total"  (NEW)
```

### Response (additional fields)

```json
{
  ... existing response fields ...,
  "bank_net_total": {
    "value": 1250000.50,
    "status": "found"
  },
  "company_net_total": {
    "value": 1250000.00,
    "status": "found"
  }
}
```
