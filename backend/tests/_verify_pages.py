# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""Temp: verify read_pdf_words returns both pages in one call via invoke()."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests"))

import test  # noqa: F401

print("tool type:", type(test.read_pdf_words))
# FunctionTool has .invoke() for the function and .params for the schema.
try:
    out = test.read_pdf_words.invoke({"drop": 20, "lines": 6})
    print(out)
except AttributeError as e:
    print("invoke not available:", e)
    print("params:", test.read_pdf_words.params)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
