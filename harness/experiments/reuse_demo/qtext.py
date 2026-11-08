"""Find a quote on a page of experiments/reuse_demo/text/<stem>.pdf.pages.json (pypdf, one string per page).

Whitespace runs are collapsed on both sides. A word broken across a line by a hyphen is tried joined
('se-\\nquences' -> 'sequences') and with its hyphen kept ('NB-\\nderived' -> 'NB-derived').
Returns 'raw', 'joined' or 'kept' (the first form that matches), or None.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent / "text"


def pages(stem):
    return json.loads((BASE / f"{stem}.pdf.pages.json").read_text())


def variants(p):
    raw = re.sub(r"\s+", " ", p).strip()
    joined = re.sub(r"\s+", " ", re.sub(r" ?-[ \t]*\n\s*", "", p)).strip()
    kept = re.sub(r"\s+", " ", re.sub(r" ?-[ \t]*\n\s*", "-", p)).strip()
    return {"raw": raw, "joined": joined, "kept": kept}


def find(stem, page, quote):
    v = variants(pages(stem)[page - 1])
    q = re.sub(r"\s+", " ", quote).strip()
    for k in ("raw", "joined", "kept"):
        if q in v[k]:
            return k
    return None
