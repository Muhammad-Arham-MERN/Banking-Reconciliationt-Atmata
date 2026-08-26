# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ

"""Validate the pdfplumber-derived structures for the two statements by
running the production assessor (structure_assessor.assess_pdf_structure)
against each PDF with the proposed columns/boundaries/band/header/date pattern.

Only reads existing code - creates no changes to any system/backend file."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.structure_assessor import _pretty, assess_pdf_structure

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SONERI = REPO_ROOT / "assets_dev" / "PKMB_STMT_ENT_BOOK_2.pdf"
MCB = REPO_ROOT / "assets_dev" / "getjobid4620060.pdf"
MEEZAN = REPO_ROOT / "assets_dev" / "eStatement_6-1-1-20311-714-5XXXX4.pdf"
VENDOR = REPO_ROOT / "assets_dev" / "Customer Ledger 2017-2023.pdf"

SONERI_DATE = r"^\d{2} [A-Z]{3} \d{4}$"
MCB_DATE = r"^\d{2}-[A-Z]{3}-\d{2}$"
MEEZAN_DATE = r"^\d{2}-[A-Za-z]{3}-\d{4}$"
VENDOR_DATE = r"^\d{2}/\d{2}/\d{2}$"

# Known-good opening balances read from the statement headers.
SONERI_OPENING = 702804.86   # "Balance at Period Start" on page 1
MCB_OPENING = 1736552.32     # "Opening Balance" / Ledger figure on page 1
MEEZAN_OPENING = 5270158.54  # "Opening Balance :" on page 1
VENDOR_OPENING = 24016.0     # "Opening Balance" on page 1


def main() -> None:
    checks = []

    print("=" * 80)
    print("SONERI  (PKMB_STMT_ENT_BOOK_2.pdf)  - header_top [343.4, 99.9]")
    print("=" * 80)
    a = assess_pdf_structure(
        pdf_path=str(SONERI),
        columns=["Booking Date", "Value Date", "Reference", "Description",
                 "Cheque.no", "Debit", "Credit", "Closing Balance"],
        header_top=[343.4, 99.9],
        rows_dropped=11,
        boundaries=[119.6, 202.65, 267.1, 325.65, 378.45, 441.3, 497.85],
        band_top=[401.5, 103.9],
        date_pattern=SONERI_DATE,
        opening_balance=SONERI_OPENING,
    )
    print(_pretty(a))
    checks.append(("SONERI [343.4, 99.9]", a["overall_pass"]))

    print()
    print("=" * 80)
    print("SONERI  - same but header_top[1]=103.9 (as in assessor demo)")
    print("=" * 80)
    b = assess_pdf_structure(
        pdf_path=str(SONERI),
        columns=["Booking Date", "Value Date", "Reference", "Description",
                 "Cheque.no", "Debit", "Credit", "Closing Balance"],
        header_top=[343.4, 103.9],
        rows_dropped=11,
        boundaries=[119.6, 202.65, 267.1, 325.65, 378.45, 441.3, 497.85],
        band_top=[401.5, 103.9],
        date_pattern=SONERI_DATE,
        opening_balance=SONERI_OPENING,
    )
    print(_pretty(b))
    checks.append(("SONERI [343.4, 103.9]", b["overall_pass"]))

    print()
    print("=" * 80)
    print("MCB  (getjobid4620060.pdf)  - scalar header/band")
    print("=" * 80)
    c = assess_pdf_structure(
        pdf_path=str(MCB),
        columns=["Tran. Date", "Effect Date", "Tran. Br.Transaction Details",
                 "Remitter Name", "Remitter IBAN", "Remitter Bank",
                 "Chq / Ref No", "Debit", "Credit", "Balance"],
        header_top=167.7,
        rows_dropped=22,
        boundaries=[53.65, 95.3, 198.4, 257.6, 309.35, 357.7, 429.85, 496.85, 559.85],
        band_top=181.3,
        date_pattern=MCB_DATE,
        opening_balance=MCB_OPENING,
    )
    print(_pretty(c))
    checks.append(("MCB", c["overall_pass"]))

    print()
    print("=" * 80)
    print("MEEZAN  (eStatement_6-1-1-20311-714-5XXXX4.pdf)  - per-page band")
    print("=" * 80)
    d = assess_pdf_structure(
        pdf_path=str(MEEZAN),
        columns=["Date", "Particulars", "Debit", "Credit", "Balance"],
        header_top=[204.4, 203.4],
        rows_dropped=11,
        boundaries=[81.65, 316.25, 385.0, 470.65],
        band_top=[243.0, 251.0],
        date_pattern=MEEZAN_DATE,
        opening_balance=MEEZAN_OPENING,
    )
    print(_pretty(d))
    checks.append(("MEEZAN", d["overall_pass"]))

    print()
    print("=" * 80)
    print("VENDOR LEDGER  (Customer Ledger 2017-2023.pdf)  - the incident file")
    print("=" * 80)
    e = assess_pdf_structure(
        pdf_path=str(VENDOR),
        columns=["Date", "Document No", "Details", "Debit", "Credit", "Cumulative"],
        header_top=[60.6, 35.9],
        rows_dropped=5,
        boundaries=[60.45, 151.6, 563.4, 676.5, 741.6],
        band_top=[80.5, 35.9],
        date_pattern=VENDOR_DATE,
        reconciliation_type="vendor",
        opening_balance=VENDOR_OPENING,
    )
    print(_pretty(e))
    checks.append(("VENDOR (known-good)", e["overall_pass"]))

    print()
    print("=" * 80)
    print("VENDOR LEDGER - BROKEN band (incident repro: pages 2-6 clipped)")
    print("=" * 80)
    f = assess_pdf_structure(
        pdf_path=str(VENDOR),
        columns=["Date", "Document No", "Details", "Debit", "Credit", "Cumulative"],
        header_top=[60.6, 60.6],  # wrong: header top too LOW on continuation pages
        rows_dropped=5,
        boundaries=[60.45, 151.6, 563.4, 676.5, 741.6],
        band_top=[80.5, 60.6],    # wrong: band_top too high on continuation pages
        date_pattern=VENDOR_DATE,
        reconciliation_type="vendor",
        opening_balance=VENDOR_OPENING,
    )
    print(_pretty(f))
    checks.append(("VENDOR (BROKEN - expect False)", f["overall_pass"]))

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for name, ok in checks:
        print(f"  {name:<38} overall_pass = {ok}")
    failed = [name for name, ok in checks if not ok and "BROKEN" not in name]
    if failed:
        print("\n[!] FAILED known-good structures:", failed)
    else:
        print("\n[OK] All known-good structures pass the composed verdict; "
              "the broken structure fails.")


if __name__ == "__main__":
    main()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
