"""The design values the figure scripts read in place of the working files (D2, Valerio, 8 November 2026).

findings/recompute/fig_design_inputs/ holds them, extracted by scripts/S616_figure_editorial.py extract (each source
with its commit, git blob id and sha256 in design_facts.json "sources"); S616 check, an editorial step run in
Mentori-reanalysis and never shipped, holds them to plan.csv, draws.csv, LIST.md, README.md, the reference list and the
human-evaluation protocol. The figure build reads only these two files.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "findings" / "recompute" / "fig_design_inputs"
FACTS = FOLDER / "design_facts.json"     # plan.csv's rows, LIST.md and README.md lines, the reference, the protocol
DRAWS = FOLDER / "draws.csv"             # experiments/draws.csv, every row, the columns S456 and S496 read


@lru_cache(maxsize=None)
def facts() -> dict:
    return json.loads(FACTS.read_text(encoding="utf-8"))
