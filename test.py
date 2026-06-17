import pandas as pd
import tabula
import re

pdf_path = "getjobid4620060.pdf"

tables = tabula.read_pdf(pdf_path, pages="all")

if tables:
    df = tables[0]
    df = tables[0]
    df.columns = df.iloc[2]   # or df.iloc[2].tolist()
    df = df.iloc[3:].reset_index(drop=True)
    # df = df[df["Tran. Date"].str.match(r"\d{2}-[A-Z]{3}-\d{2}", na=False)]
    df = df[df["Tran. Date"].notna()]


print(df["Balance"])