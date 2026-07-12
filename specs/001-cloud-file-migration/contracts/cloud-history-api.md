# Cloud History API Contract

## Base URL

`{API_BASE_URL}/api/cloud` — configured via `NEXT_PUBLIC_API_URL` env var.

## Authentication

All endpoints require `Authorization: Bearer <jwt_token>` header. The JWT is the NextAuth session token obtained by exposing the raw token in the `jwt()` → `session()` callbacks.

## Endpoints

### GET /load_files_cloud

Load the authenticated user's saved file names.

**Headers**: `Authorization: Bearer <token>`

**Response 200**:
```json
{
  "files": ["file_name_1", "file_name_2"]
}
```

**Response Example (empty)**:
```json
{
  "files": []
}
```

**Errors**: Returns 401 if auth token missing/invalid.

---

### POST /save_files_cloud

Save reconciliation data for the authenticated user.

**Headers**: `Authorization: Bearer <token>`  
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "file_name": "my-reconciliation-2026-07-11",
  "file_data": [
    {
      "transaction_details": "Payment to Vendor A",
      "transaction_date": "2026-07-10",
      "debit_credit_amount": -5000.00,
      "category": "Unpresented Checks"
    }
  ]
}
```

**Field Requirements**:
- `file_name`: string, 1-255 chars, required
- `file_data`: array of dicts, minimum 1 entry, required
- Each entry has: `transaction_details` (string), `transaction_date` (string), `debit_credit_amount` (number, debits positive credits negative), `category` (string)

**Response 200**:
```json
{
  "success": true,
  "message": "Reconciliation data saved successfully",
  "file_name": "my-reconciliation-2026-07-11"
}
```

**Errors**: Returns 401 (auth), 422 (validation), 500 (server).

## Error Response Shape

```json
{
  "detail": "Error description string"
}
```
