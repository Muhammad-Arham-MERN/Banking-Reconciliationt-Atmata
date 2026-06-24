import re

import pandas as pd
import tabula

pdf_path = "getjobid4620060.pdf"

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


def extract_bank_statement(pdf_path: str) -> pd.DataFrame:
    tables = tabula.read_pdf(pdf_path, pages="all")
    if not tables:
        return pd.DataFrame()

    raw = tables[0]
    df = raw.iloc[3:].copy()
    df.columns = CANONICAL_COLUMNS
    df = df.drop(columns=["_unused_1", "_unused_2"])

    branch_and_details = df["Tran. Narrative"].astype(str).str.extract(
        BRANCH_NARRATIVE_PATTERN
    )
    df["Tran. Br."] = branch_and_details[0]
    df["Transaction Details"] = branch_and_details[1]

    df = df[df["Tran. Date"].astype(str).str.match(DATE_PATTERN, na=False)]
    return df.reset_index(drop=True)


df = extract_bank_statement(pdf_path)

print(df.columns.tolist())
print()
print(df[["Tran. Date", "Transaction Details", "Debit", "Credit"]])
