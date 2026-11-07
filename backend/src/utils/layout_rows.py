# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Row assembly shared by the PDF extractors (Istikhraj e Data Ma'a AI).

Words that belong to ONE logical table row are not always printed on exactly
the same 'top' coordinate: some writers baseline-jitter a row's amount/balance
cells by ~0.1pt relative to the row's date/description cells. Grouping words
strictly by an exact rounded top therefore splits one visual row into two — the
amount cells land on a "dateless phantom line" that the extractor discards,
producing empty Debit/Credit/Balance cells and a false arithmetic failure.

`group_words_into_lines` clusters words whose 'top' falls within a small
vertical tolerance into a single logical line, so a jittered row is reassembled
BEFORE column slicing. The tolerance is far smaller than any real row pitch
(rows are typically >= ~10pt apart), so genuinely distinct rows are never
merged.

Both the production extractor (ai_pdf_processor.extract_pdf) and the structure
assessor (structure_assessor.extract_pdf_words / _extract_rows_per_page / its
per-page and Kabir counters) use this ONE helper, so the assessor and the
pipeline always measure the same rows.
"""

from __future__ import annotations

from typing import List, Tuple

# Vertical tolerance (PDF points) for merging words into one logical row.
# Baseline jitter is ~0.1pt; real row pitch is >= ~10pt, so 1.0pt is safely
# below any true row separation while absorbing rendering noise.
ROW_TOP_TOLERANCE_PDF = 1.0


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def group_words_into_lines(
    words: List[dict],
    tolerance: float = ROW_TOP_TOLERANCE_PDF,
) -> List[Tuple[float, List[dict]]]:
    """Cluster words into logical visual lines by vertical position.

    Words are ordered by (top, x0). A word joins the current line when its top
    is within `tolerance` of that line's anchor top (its first word's top);
    otherwise it starts a new line.

    Args:
        words: pdfplumber word dicts (each with 'top', 'x0', 'x1', 'text').
        tolerance: Max vertical difference (points) for two words to count as
            the same logical row.

    Returns:
        [(line_top, [words...]), ...] in ascending top order, where line_top is
        the anchor (first word's) rounded top. Shape matches the previous
        `sorted(lines.items())` so callers stay unchanged.
    """
    ordered = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
    lines: List[Tuple[float, List[dict]]] = []
    for w in ordered:
        top = round(w["top"], 1)
        if lines and abs(top - lines[-1][0]) <= tolerance:
            lines[-1][1].append(w)
        else:
            lines.append((top, [w]))
    return lines

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
