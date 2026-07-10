import re

import pandas as pd
import tabula

pdf_path = "assets_dev/getjobid4620060.pdf"

# Tabula merges several PDF header cells into one column name. Map by position instead.
CANONICAL_COLUMNS = [
    "Tran. Date",
    "Effect Date",
    "Tran. Narrative",  # merged: Tran. Br. + Transaction Details + Remitter Name in PDF
    "_unused_1",
    "Remitter IBAN",
    "Remitter Bank",
    "Chq / Ref No",
    "Debit",
    "Credit",
    "_unused_2",
    "Balance",
]

DATE_PATTERN = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")
BRANCH_NARRATIVE_PATTERN = re.compile(r"^(\d{4})\s+(.+)$")
# Page 2+ continuation rows: tabula stream mode merges page 1 but truncates the tail.
AREA_ROW_PATTERN = re.compile(
    r"^(\d{2}-[A-Z]{3}-\d{2})\s+(\d{2}-[A-Z]{3}-\d{2})\s+(.+)$"
)
REF_AMOUNT_PATTERN = re.compile(r"^(\d+)\s+([\d,]+\.\d{2})$")
AREA_EXTRACTION = {
    "area": [5, 0, 95, 100],
    "relative_area": True,
    "stream": True,
    "pandas_options": {"header": None},
    "multiple_tables": True,
}


def _process_raw_table(raw: pd.DataFrame) -> pd.DataFrame:
    """Skip header rows, map columns, and keep valid transaction rows."""
    if raw.empty or len(raw) <= 3:
        return pd.DataFrame()

    df = raw.iloc[3:].copy()
    df.columns = CANONICAL_COLUMNS
    df = df.drop(columns=["_unused_1", "_unused_2"])

    branch_and_details = df["Tran. Narrative"].astype(str).str.extract(
        BRANCH_NARRATIVE_PATTERN
    )
    df["Tran. Br."] = branch_and_details[0]
    df["Transaction Details"] = branch_and_details[1]

    return df[df["Tran. Date"].astype(str).str.match(DATE_PATTERN, na=False)]


def _process_area_fallback_table(raw: pd.DataFrame) -> pd.DataFrame:
    """Parse tabula area-extracted rows where columns collapse on continuation pages."""
    rows = []
    for _, row in raw.iterrows():
        header = str(row.iloc[0] or "").strip()
        header_match = AREA_ROW_PATTERN.match(header)
        if not header_match:
            continue

        tran_date, effect_date, narrative = header_match.groups()
        amount_cell = str(row.iloc[4] if len(row) > 4 else "").strip()
        amount_match = REF_AMOUNT_PATTERN.match(amount_cell)
        if not amount_match:
            continue

        chq_ref, debit = amount_match.groups()
        branch_match = BRANCH_NARRATIVE_PATTERN.match(narrative)
        rows.append(
            {
                "Tran. Date": tran_date,
                "Effect Date": effect_date,
                "Tran. Narrative": narrative,
                "Remitter IBAN": pd.NA,
                "Remitter Bank": pd.NA,
                "Chq / Ref No": chq_ref,
                "Debit": debit,
                "Credit": pd.NA,
                "Balance": row.iloc[5] if len(row) > 5 else pd.NA,
                "Tran. Br.": branch_match.group(1) if branch_match else pd.NA,
                "Transaction Details": branch_match.group(2) if branch_match else narrative,
            }
        )

    return pd.DataFrame(rows)


def _dedupe_transactions(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.drop_duplicates(
        subset=["Tran. Date", "Chq / Ref No", "Debit", "Credit"],
        keep="first",
    ).reset_index(drop=True)


def _extract_continuation_pages(pdf_path: str) -> list[pd.DataFrame]:
    """Extract transactions from page 2+ when stream mode truncates at a page break."""
    continuation = []
    page = 2
    while page <= 50:
        try:
            tables = tabula.read_pdf(pdf_path, pages=str(page), **AREA_EXTRACTION)
        except Exception:
            break
        page_dfs = [_process_area_fallback_table(raw) for raw in tables]
        page_dfs = [df for df in page_dfs if not df.empty]
        if not page_dfs:
            break
        continuation.extend(page_dfs)
        page += 1
    return continuation


def extract_bank_statement(pdf_path: str) -> pd.DataFrame:
    # read_pdf always returns a list of DataFrames (one per detected table)
    tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)
    if not tables:
        return pd.DataFrame()

    print(f"Tabula found {len(tables)} table(s)")
    for i, raw in enumerate(tables):
        print(f"  table {i + 1}: {raw.shape[0]} rows x {raw.shape[1]} cols")

    processed = [_process_raw_table(raw) for raw in tables]
    processed.extend(_extract_continuation_pages(pdf_path))
    processed = [df for df in processed if not df.empty]
    if not processed:
        return pd.DataFrame()

    return _dedupe_transactions(pd.concat(processed, ignore_index=True))


df = extract_bank_statement(pdf_path)

print(df.columns.tolist())
print()
print(df[["Tran. Date", "Transaction Details", "Debit", "Credit","Balance"]])
