# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# imports
- Import utility functions (categorizeTransaction, generateItemId, getDisplayAmount, formatAmount) from @/lib/utils/categorizationUtils, not from @/types/categorization.types. Confidence: 0.75

# typescript
- Use `export type { ... }` syntax when re-exporting types from other modules to satisfy isolatedModules constraint. Confidence: 0.70

# code-style
- Use `/** */` JS comment blocks for file headers, never `#` hash-prefix (invalid in TypeScript/JSX files). Confidence: 0.70

# shadcn
- Prefer using official shadcn UI components over custom hand-rolled implementations. Confidence: 0.60

# nextjs-auth
- Use inline Google sign-in button on protected pages (e.g., /upload) instead of a separate /login sign-in page. Confidence: 0.65

# project-conventions
- Every Python and TypeScript file must begin with `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` and end with `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` (Islamic Prayer Bookends). Confidence: 0.85

# database
- Remove SQLModel entirely from backend projects; use raw asyncpg for all CockroachDB queries instead. Confidence: 0.75

# python
- Use pandas for general data manipulation; for PDF table extraction specifically, prefer tabula-py (see pdf-extraction section). Confidence: 0.6

# pdf-extraction
- Removed tabula-py (and the Java runtime it requires) from the project entirely — it is no longer a wanted dependency; all PDF table extraction is done with pdfplumber instead. Confidence: 0.85
- Rejects hardcoding column-count/layout branches in PDF extraction (e.g., special-casing a 10-column vs 11-column table); wants a strong, layout-agnostic extraction method that survives month-to-month layout changes (headers merging differently, new columns collapsing) instead of patching each known failure. Confidence: 0.8
- For bank statement PDFs with a fixed, canonical template, endorses explicit column-location mapping (physical x-coordinate boundaries sliced word-by-word) instead of tabula's whitespace-based column inference — rationale: the bank's layout is stable and won't change, and tabula's column splits vary across pages of the same file; views this as a temporary stopgap (coordinates kept as a single clearly-labeled constant) until his AI-driven extraction system replaces it. He praised the positioning system as the fix for the regex-based extraction he was stuck on ("beautiful positioning system"). Confidence: 0.85

- Uses pdfplumber for PDF table extraction (now a declared production dependency in requirements files, used in the main PDF processing code path) and wants extracted tables displayed as pandas DataFrames so the results can be inspected. Confidence: 0.85
- The AI-driven extraction agent's output contract is per-file-type: for Excel it must output the required column names; for PDFs it must output the full column list plus the required ones, a precise location map (physical x-coordinate boundaries), and the number of rows dropped to reach the header row — these are fed to the deterministic extractor (drop-line and columns already exist; the location map is the remaining piece). Confidence: 0.65

# reconciliation
- Core reconciliation semantics: compare the bank statement (PDF) against the company ledger (Excel); values present in both files are matched and must be excluded from the final array — the discrepancies array should contain only items unique to one side (company values not in the bank and bank values not in the company). The user treats any deviation (e.g., all items showing up as discrepancies) as a regression of established logic. Confidence: 0.7
- Matching must be 1:1 with consumption tracking: when a bank amount matches a company amount, BOTH entries are removed together — the user explicitly rejects a semantics where the bank side is removed but its paired company entry survives. Each entry can only be consumed once, so a single bank amount must not be reused to cancel multiple company rows (or vice versa); this is the "correct accounting view," after which true leftovers are netted by opposite-sign cancellation. The user has restated this exact 1:1-consume-both semantics unprompted multiple times (Record A finds Record B → both removed; unmatched leftovers C/D flow to discrepancies where opposite signs cancel) and asks for confirmation before a fix proceeds. Confidence: 0.9
- Enforces an explicit sign convention for reconciliation categories in every frontend calculation/presentation layer (totals and manual reconciliation): UNPRESENTED CHECKS → negative, UNCLEARED CHECKS → positive, Bank Debited but not credited in cashbook → positive, Bank Credited but not debited in cashbook → negative; displayed amounts must be forced to these signs. Confidence: 0.85
- Bank statement data semantics: positive value = credit (money in), negative value = debit (money out) — verified in `data_transformers.py` and sample statements (positive = INWARD CHEQUE / money in). Category assignment must follow this (Bank positive → BANK_CREDITED_NOT_DEBITED, Bank negative → BANK_DEBITED_NOT_CREDITED), and the convention must be consistent end-to-end (backend data → categorization → display → history), including enum docstrings/comments — self-contradictory docs caused a swapped categorization. Confidence: 0.75

# agents
See [agents/taste.md](agents/taste.md)
# workflow
See [workflow/taste.md](workflow/taste.md)
hat simple"). Confidence: 0.85
- Wants agents defined with explicit function tools for file extraction (e.g., read_excel, read_pdf). Confidence: 0.6

# workflow
See [workflow/taste.md](workflow/taste.md)
