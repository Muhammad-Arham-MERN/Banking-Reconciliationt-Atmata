# LLM Contract: File Structure Detection Output

**Branch**: `005-ai-data-extraction` | **Date**: 2026-08-06 | **Spec**: [spec.md](../spec.md)

This contract is between the OpenAI Agents SDK agent and the deterministic system. It is derived verbatim from the validated prototype `test.py`. The agent MUST emit exactly one fenced `[output]` block as its entire response; `parse_output_block` parses it into `FileStructureOutput` (pydantic). Any deviation counts as a failed attempt and triggers a retry (FR-008).

## Output Format (critical)

The agent's ENTIRE response must be exactly one block — no prose, no explanation, nothing before or after:

```text
~~~
[output]
columns_pdf: ["Tran. Date", "Effect Date", "Tran. Narrative", "Remitter IBAN", "Remitter Bank", "Branch Code", "Chq / Ref No", "Debit", "Credit", "Balance"]
columns_excel: ["Date", "Description", "Amount"]
header_words_pdf: ["Tran.", "Date", "Effect", "Date", "Tran.", "Narrative", "Remitter", "IBAN", "Remitter", "Bank", "Chq", "/", "Ref", "No", "Debit", "Credit", "Balance"]
rows_dropped_pdf: 22
header_top_pdf: 167.7
column_boundaries_pdf: [50.5, 95.0, 200.0, 260.0, 305.0, 357.5, 420.0, 490.0, 540.0]
band_top_pdf: 181.3
date_pattern_pdf: "^\\d{2}-[A-Z]{3}-\\d{2}$"
~~~
```

Inside the block: one line per field, `name: value`. Values are parsed JSON-first; regex strings that fail JSON (because `\d` is an invalid JSON escape) fall back to quote-stripping. The `~~~` markers are required.

## Field Semantics

| Field | Required | Meaning | Validation |
|-------|----------|---------|------------|
| `columns_pdf` | yes | Full list of PDF column names from the header line, left-to-right visual order | non-empty `list[str]` |
| `columns_excel` | yes | The required Excel column names in canonical order: `[date, details, Total/Cumulative, amount column(s)]`. 4 names for the combined Debit/Credit case; 5 names for the separate Debit + Credit case | `list[str]` of length 4 or 5 |
| `header_words_pdf` | yes | Exact header word strings from `read_pdf_words`, left-to-right, as they appear | non-empty `list[str]` |
| `rows_dropped_pdf` | yes | Number of visual lines above the header line (header NOT counted) | `int >= 0` |
| `header_top_pdf` | yes | Numeric `top=` coordinate of the header line | `float` |
| `column_boundaries_pdf` | yes | Midpoint x-coordinates of the gaps between adjacent column groups; exactly `len(columns_pdf) - 1` ascending values; each must fall in an empty gap in the data rows (no word straddles) | `list[float]` ascending |
| `band_top_pdf` | yes | `top=` coordinate of the first transaction data row (just below the header) | `float` |
| `date_pattern_pdf` | yes | Regex matching exactly the first-column date strings (e.g. `^\d{2}-[A-Z]{3}-\d{2}$`) | parseable regex string |

## Excel Amount-Column Semantics (canonical)

- **Combined Debit/Credit (norm)**: a single column (e.g. "Debit/Credit") where **positive = debit, negative = credit**. `columns_excel` has 4 entries: `[date, details, total, debit/credit]`.
- **Separate Debit + Credit (edge case)**: two distinct columns, usually unsigned. `columns_excel` has 5 entries: `[date, details, total, debit, credit]`. The deterministic processor merges them with **debit = positive, credit = negative**.
- The LLM is responsible for structuring `columns_excel` in this canonical order regardless of the source file's physical column order.

## Agent Instructions (from test.py, adapted to request-scoped paths)

- **Excel**: use the Excel read tool to find the header row (may require multiple calls with increasing `drop`), then return ONLY the required columns — transaction date, transaction details, debit/credit column(s), total/sum column.
- **PDF**: use the PDF read tool to see table content row by row (dates, details, amounts). Use `read_pdf_words` to see GEOMETRY — every word with its `x0..x1` span and line `top` coordinate. Identify the exact header line; report header words EXACTLY as printed, left-to-right, with the line's `top`. Report `rows_dropped_pdf` (visual lines above the header). Group header words into columns (gap between groups = column boundary). Compute `column_boundaries_pdf` as midpoints between adjacent groups' rightmost `x1` and leftmost `x0` — exactly `len(columns_pdf) - 1` values. VERIFY each boundary against data rows: boundary must fall in an empty gap, no data word straddles it; shift to the widest empty gap if needed. Set `band_top_pdf` to the first data row's `top`. Set `date_pattern_pdf` from the first-column dates.

## Parser (parse_output_block)

```python
m = re.search(r"~~~\s*\[output\]\s*(.*?)\s*~~~", raw, re.DOTALL)  # fallback: r"\[output\]\s*(.*?)\s*~~~"
# for each line "name: value": json.loads(value); on JSONDecodeError strip matching quotes
# then FileStructureOutput(**data)  # pydantic validation
```

## Retry Triggers (FR-008)

A detection attempt FAILS (→ retry, up to 3 total) when any of:
- No `[output]` block found in the response.
- `FileStructureOutput` pydantic validation error (missing field, wrong type, empty list).
- `column_boundaries_pdf` length ≠ `len(columns_pdf) - 1`, or not ascending.
- Detected Excel columns do not exist in the workbook / detected PDF columns not derivable from the header line (deterministic cross-check).
- Agent run raises (network, auth, provider error).

After 3 failed attempts → `AIDetectionError` → HTTP 422 "We couldn't analyze your files. Please try again." (FR-009).
