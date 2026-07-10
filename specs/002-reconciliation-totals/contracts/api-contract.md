# API Contract: Reconciliation Totals & Verification

## POST /karwai — Extended Reconciliation with Totals

### Request Changes

**New form parameter**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `aggregatedTotalColumn` | string | No | Column name in XLSX containing the Aggregated Total values. If omitted, Company Net Total will not be calculated. |

### Response Changes

**New fields in response root**:

```json
{
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

### Field Specifications

#### `bank_net_total`

| Field | Type | Possible Values | Description |
|-------|------|----------------|-------------|
| `value` | number \| null | float or null | Last non-null Balance value from PDF. null if missing/invalid. |
| `status` | string | `"found"`, `"missing"`, `"invalid"` | Status of the extraction. |

#### `company_net_total`

| Field | Type | Possible Values | Description |
|-------|------|----------------|-------------|
| `value` | number \| null | float or null | Last non-null value from the user-specified Aggregated Total column. null if column not provided, not found, or invalid. |
| `status` | string | `"found"`, `"missing"`, `"invalid"` | Status of the extraction. |

### Error Scenarios

| Condition | Behavior |
|-----------|----------|
| `aggregatedTotalColumn` is omitted | `company_net_total.status` = `"missing"`, `value` = null. Regular reconciliation still proceeds. |
| Balance column is missing from PDF data | `bank_net_total.status` = `"missing"`, `value` = null. Regular reconciliation still proceeds. |
| Last Balance cell is non-numeric/empty | `bank_net_total.status` = `"invalid"`, `value` = null. |
| Aggregated Total column not found in XLSX | `company_net_total.status` = `"missing"`, `value` = null. |
| Last Aggregated Total cell is non-numeric/empty | `company_net_total.status` = `"invalid"`, `value` = null. |

### Full Response Example

```json
{
  "request_id": "f5af9205-7b5b-4ffb-8f56-95cbe292c09e",
  "processing_status": "completed",
  "processing_timestamp": "2026-06-29T10:30:00.000000Z",
  "summary": {
    "total_bank_transactions": 26,
    "total_company_transactions": 20,
    "total_discrepancies": 15,
    "bank_only_discrepancies": 8,
    "company_only_discrepancies": 7,
    "opposite_pairs_removed": 4,
    "processing_duration_ms": 7153,
    "pdf_processing_time_ms": 7151,
    "excel_processing_time_ms": 191,
    "concurrent_processing": true
  },
  "results": {
    "bank_statement": [],
    "company_records": [],
    "discrepancies": []
  },
  "bank_net_total": {
    "value": 1250000.50,
    "status": "found"
  },
  "company_net_total": {
    "value": 1250000.00,
    "status": "found"
  },
  "errors": [],
  "message": "Reconciliation complete - Found 15 discrepancies"
}
```
