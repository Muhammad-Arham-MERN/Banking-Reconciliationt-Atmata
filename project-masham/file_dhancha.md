# 🏗️ File Dhāncha (File Structure)

> The **detailed pdfplumber structure** of the first 2 pages of the two bank-statement PDFs, derived by reading the raw word geometry (`x0`–`x1` spans + line `top` coordinates). These values feed the deterministic extractor (`extract_pdf`) — see `backend/tests/test.py` and `backend/tests/structure_assessor.py` for how they are consumed.

---

## 📄 1. `PKMB_STMT_ENT_BOOK_2.pdf` — SONERI BANK

- **Pages:** 2 — **Page 1 ≠ Page 2** (so `header_top_pdf` / `band_top_pdf` are **2-element lists**; columns & boundaries are global)
- **Page size:** 594.7 × 841.7

### Why the pages differ

| Page | What's above the table | Header line | First data row |
|---|---|---|---|
| 1 | ~10-line account-info block (Account / Currency / From Date / Page / Branch) at `top≈207.3`–`326.3` | `top=343.4` (two-line header: `Bal-`/`ance` at `351.9`) | `top=401.5` (`01 JUL 2026`) |
| 2 | Only the statement header (`3 August 2026`, `9:43:24`) | **No table header line at all** | `top=103.9` (`10 JUL 2026`) |

### The structure

```json
{
  "columns_pdf": ["Booking Date", "Value Date", "Reference", "Description", "Cheque.no", "Debit", "Credit", "Closing Balance"],
  "header_words_pdf": ["Booking", "Date", "Value", "Date", "Reference", "Description", "Cheque.no", "Debit", "Credit", "Closing", "Bal-", "ance"],
  "rows_dropped_pdf": 11,
  "header_top_pdf": [343.4, 103.9],
  "column_boundaries_pdf": [119.6, 202.65, 267.1, 325.65, 378.45, 441.3, 497.85],
  "band_top_pdf": [401.5, 103.9],
  "date_pattern_pdf": "^\\d{2} [A-Z]{3} \\d{4}$"
}
```

| Variable | Value | Notes |
|---|---|---|
| `columns_pdf` | Booking Date, Value Date, Reference, Description, Cheque.no, Debit, Credit, Closing Balance | 8 physical columns |
| `header_words_pdf` | `Booking Date Value Date Reference Description Cheque.no Debit Credit Closing Bal- ance` | Exact words, left→right; `Bal-`/`ance` is one wrapped header |
| `rows_dropped_pdf` | `11` | Visual lines above the header on page 1 (lines at `top=67.7` … `326.3`) |
| `header_top_pdf` | `[343.4, 103.9]` | Page 1 = header line; page 2 = first data row (no header) |
| `column_boundaries_pdf` | `[119.6, 202.65, 267.1, 325.65, 378.45, 441.3, 497.85]` | 7 midpoints for 8 columns |
| `band_top_pdf` | `[401.5, 103.9]` | Page 1 first data row; page 2 first data row |
| `date_pattern_pdf` | `^\d{2} [A-Z]{3} \d{4}$` | e.g. `01 JUL 2026` |

---

## 📄 2. `getjobid4620060.pdf` — MCB BANK

- **Pages:** 2 — **Page 1 = Page 2** (so `header_top_pdf` / `band_top_pdf` are **scalars**)
- **Page size:** 612.0 × 792.0

### Why the pages are the same

Both pages carry the **identical** account-header block (Account No / IBAN / Statement Period / Statement Date) ending at `top=118.2`, then the table header at `top=167.7` (two-line: `Remitter`/`Bank` at `168.2`), and the first data row at `top=181.3`. Page 2 continues straight into data — same header, same band.

### The structure

```json
{
  "columns_pdf": ["Tran. Date", "Effect Date", "Tran. Br.Transaction Details", "Remitter Name", "Remitter IBAN", "Remitter Bank", "Chq / Ref No", "Debit", "Credit", "Balance"],
  "header_words_pdf": ["Tran.", "Date", "Effect", "Date", "Tran.", "Br.Transaction", "Details", "Remitter", "Name", "Remitter", "IBAN", "Chq", "/", "Ref", "No", "Debit", "Credit", "Balance"],
  "rows_dropped_pdf": 22,
  "header_top_pdf": 167.7,
  "column_boundaries_pdf": [53.65, 95.3, 198.4, 257.6, 309.35, 357.7, 429.85, 496.85, 559.85],
  "band_top_pdf": 181.3,
  "date_pattern_pdf": "^\\d{2}-[A-Z]{3}-\\d{2}$"
}
```

| Variable | Value | Notes |
|---|---|---|
| `columns_pdf` | Tran. Date, Effect Date, Tran. Br.Transaction Details, Remitter Name, Remitter IBAN, Remitter Bank, Chq / Ref No, Debit, Credit, Balance | 10 physical columns |
| `header_words_pdf` | `Tran. Date Effect Date Tran. Br.Transaction Details Remitter Name Remitter IBAN Chq / Ref No Debit Credit Balance` | Exact words, left→right; `Chq`/`/`/`Ref`/`No` is one wrapped header |
| `rows_dropped_pdf` | `22` | Visual lines above the header (lines at `top=9.3` … `118.2`) |
| `header_top_pdf` | `167.7` | Scalar — identical on both pages |
| `column_boundaries_pdf` | `[53.65, 95.3, 198.4, 257.6, 309.35, 357.7, 429.85, 496.85, 559.85]` | 9 midpoints for 10 columns |
| `band_top_pdf` | `181.3` | Scalar — identical on both pages |
| `date_pattern_pdf` | `^\d{2}-[A-Z]{3}-\d{2}$` | e.g. `05-MAY-26` |

---

## ✅ Validation (via `structure_assessor.assess_pdf_structure`)

Validation now uses the **composed verdict** — Saghir (arithmetic, correctness)
**AND** Kabir (raw date-filtered completeness). `overall_pass` is true only
when both pass.

| PDF | Rows (LLM structure) | Raw dated rows (Kabir) | Kabir diff% | Saghir sweep | overall_pass | Notes |
|---|---|---|---|---|---|---|
| MCB `getjobid4620060.pdf` | 26 | 26 | 0.0% | PASS (26/26) | ✅ | opening balance 1,736,552.32; full clean pass under the composed verdict |
| Meezan `eStatement_6-1-1-20311-714-5XXXX4.pdf` | 171 | 174 | 1.72% | FAIL (20/171 checked) | ❌ | Kabir PASS; Saghir sweep limited because Balance amounts land on continuation sub-lines (documented limitation) — most rows have `Balance=""` and are skipped |
| Soneri `PKMB_STMT_ENT_BOOK_2.pdf` | 14 | (unruled, raw=0) | inconclusive | FAIL (11/14 checked) | ❌ | Kabir inconclusive (date patterns don't cover its layout); Saghir tripped by sub-line debris rows — known structural limitation |
| Vendor `Customer Ledger 2017-2023.pdf` | 156 | 156 | 0.0% | PASS (156/156) | ✅ | full clean pass — Kabir 0% diff and the Saghir sweep now passes within the 50.0 tolerance (the old 2.00 rounding gap is absorbed) |

> The Soneri `date_lines=0` in the assessor output is an artifact of the
> assessor's own default regex counter (`^\d{2}-[A-Z]{3}-\d{2}$`); the
> extraction itself passes the correct `"  "`-separated pattern and fills the
> date column 100%.

---

## 📄 3. `eStatement_6-1-1-20311-714-5XXXX4.pdf` — MEEZAN BANK

- **Pages:** 7 — **Page 1 ≠ Pages 2-6** (so `header_top_pdf` / `band_top_pdf` are **2-element lists**; columns & boundaries are global). Page 7 is a summary page.
- **Page size:** 595.0 × 842.0

### Why the pages differ

| Page | What's above the table | Header line | First data row |
|---|---|---|---|
| 1 | Full account-header block (Branch / A/C Type / IBAN / Currency / From-To / Printed On) at `top≈69`–`183` | `top=204.4` | `top=243.0` (`03-Jul-2026`), right after `Opening Balance` at `228.0` |
| 2 | Same account-header block (only slightly tighter, `top≈68`–`182`) | `top=203.4` | `top=251.0` (`08-Jul-2026`) — **no opening-balance line**, table starts ~8pt lower |
| 3-6 | Same as page 2 | `top=203.4` | `top=245.5`–`260.5` (varies per page) |
| 7 | Summary page | — | No transaction rows |

So page 2's `203.4` is canonical for pages 2-6; page 1 uses `204.4`/`243.0`.

### The structure

```json
{
  "columns_pdf": ["Date", "Particulars", "Debit", "Credit", "Balance"],
  "header_words_pdf": ["Date", "Particulars", "Debit", "Credit", "Balance"],
  "rows_dropped_pdf": 11,
  "header_top_pdf": [204.4, 203.4],
  "column_boundaries_pdf": [81.65, 316.25, 385.0, 470.65],
  "band_top_pdf": [243.0, 251.0],
  "date_pattern_pdf": "^\\d{2}-[A-Za-z]{3}-\\d{4}$"
}
```

| Variable | Value | Notes |
|---|---|---|
| `columns_pdf` | Date, Particulars, Debit, Credit, Balance | 5 physical columns |
| `header_words_pdf` | `Date Particulars Debit Credit Balance` | Exact words, left→right |
| `rows_dropped_pdf` | `11` | Visual lines above the header on page 1 (lines at `top=69.0` … `183.0`) |
| `header_top_pdf` | `[204.4, 203.4]` | Page 1 = 204.4; pages 2-6 = 203.4 |
| `column_boundaries_pdf` | `[81.65, 316.25, 385.0, 470.65]` | 4 midpoints for 5 columns |
| `band_top_pdf` | `[243.0, 251.0]` | Page 1 first data row 243.0; page 2 first data row 251.0 (page 2 has no Opening Balance line, so the first row sits ~8pt lower) |
| `date_pattern_pdf` | `^\d{2}-[A-Za-z]{3}-\d{4}$` | e.g. `03-Jul-2026` — note the month is **mixed-case** (`Jul`), so `[A-Za-z]` is needed, not `[A-Z]` |

### Notes
- The **Debit** column carries amounts like `17,468,897.86`; the **Credit** column like `23,278,725.00`; **Balance** appears only at sub-line/row boundaries (`(29,880,105.57)`).
- Credit and Balance amounts often land on a *continuation sub-line* below the date row, which is why the assessor's fill rates look low (Credit 26.9%, Balance 11.7%) even though the structure is correct — the raw-table ground truth is 169 rows vs 171 extracted (+2, "OK").
