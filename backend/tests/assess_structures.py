# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ

"""Dump word geometry of the first 2 pages of both PDFs, grouped into visual
lines exactly like tests/test.py read_pdf_words tool, so the agent structure
(columns_pdf, header_words_pdf, rows_dropped_pdf, header_top_pdf,
column_boundaries_pdf, band_top_pdf, date_pattern_pdf) can be derived
deterministically for each page."""

from pathlib import Path

import pdfplumber

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PDFS = [
    REPO_ROOT / "assets_dev" / "PKMB_STMT_ENT_BOOK_2.pdf",
    REPO_ROOT / "assets_dev" / "getjobid4620060.pdf",
]


def visual_lines(page_obj) -> list[list[dict]]:
    """Group extract_words() output into visual lines by rounded top."""
    words = page_obj.extract_words()
    groups: dict[float, list[dict]] = {}
    for w in words:
        groups.setdefault(round(w["top"], 1), []).append(w)
    out = []
    for top in sorted(groups):
        row_words = sorted(groups[top], key=lambda w: w["x0"])
        out.append((top, row_words))
    return out


def main() -> None:
    for pdf_path in PDFS:
        print("\n" + "=" * 90)
        print(f"PDF: {pdf_path.name}")
        print("=" * 90)
        with pdfplumber.open(str(pdf_path)) as pdf:
            print(f"total pages: {len(pdf.pages)}  page size: {pdf.pages[0].width:.1f} x {pdf.pages[0].height:.1f}")
            for pi, page_obj in enumerate(pdf.pages[:2]):
                print(f"\n---------- PAGE {pi + 1} OF 2 ----------")
                lines = visual_lines(page_obj)
                for top, row_words in lines:
                    cells = " ".join(
                        f"{w['text']!r}[{w['x0']:.1f}-{w['x1']:.1f}]" for w in row_words
                    )
                    print(f"top={top:7.1f} | {cells}")


if __name__ == "__main__":
    main()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
