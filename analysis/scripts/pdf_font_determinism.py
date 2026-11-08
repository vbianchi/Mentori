"""pdf_font_determinism.py: make the embedded font subsets of a plate's PDF the same on every run.

Importing this module patches one method of fontTools (4.63.0): the subsetting of the AAT 'prop' table, which
macOS's Helvetica (/System/Library/Fonts/Helvetica.ttc) carries. fontTools picks the table's new default property
with Counter(...).most_common(1) over a dict built from a set of glyph names, so when two property values tie, the
winner follows the set's order, which follows PYTHONHASHSEED. A subset holding a Greek letter (the rho of D301,
7 November 2026) has such a tie, and the PDF then differed between two builds of the same plate (Supplementary
Figure 10: 48,418 or 48,428 bytes; matplotlib's pdf.fonttype 42 subsets each font through fontTools). Here a tie
goes to the smallest value. Without a tie the choice and the table are what fontTools gives (the table is compiled
in glyph order, so the dict's order never reached the file), so every plate without a tie keeps its bytes.

    import pdf_font_determinism  # noqa: F401  (before any figure is saved)
"""
from __future__ import annotations

from collections import Counter

from fontTools import subset as _subset
from fontTools import ttLib as _ttLib

_PROP = _ttLib.getTableClass("prop")


def _subset_glyphs(self, s):
    prop = self.table.GlyphProperties
    if prop.Format == 0:
        return prop.DefaultProperties != 0
    if prop.Format == 1:
        props = {g: prop.Properties.get(g, prop.DefaultProperties) for g in s.glyphs}
        counts = Counter(props.values())
        top = max(counts.values())
        most_common = min(v for v, c in counts.items() if c == top)
        prop.DefaultProperties = most_common
        prop.Properties = {g: v for g, v in props.items() if v != most_common}
        if not prop.Properties:
            del prop.Properties
            prop.Format = 0
            return prop.DefaultProperties != 0
        return True
    raise AssertionError(f"unknown 'prop' format {prop.Format}")


_PROP.subset_glyphs = _subset_glyphs
assert _subset is not None   # the subset module defines the method this replaces; importing it first keeps ours
