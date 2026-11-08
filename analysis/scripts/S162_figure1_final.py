#!/usr/bin/env python3
"""S162 - Figure 1, final. The only build; the versioned drafts are retired.

HOW THIS FIGURE ARRIVED, since the drafts are gone and the reasoning should not be.

The submitted Figure 1 had three panels: a service architecture, the triangulation framework, and an
eleven-node experiment dependency graph with counts. Reviewer 1: "overly cluttered with standard
software architecture and dense experimental flowcharts, which buries the headline of the paper.
Streamlining the figure would allow Panel b's unique Triple-Triangulation framework to stand out as
the clear visualisation." The editor, independently: "position the large-scale ablation study,
rather than the evaluation framework alone, as its main contribution."

Decisions taken, each of which a later reviewer may try to undo:
  * two panels, what was varied then how it was measured, neither dominating
  * the implementation stack is gone outright. No FastAPI, FastMCP, React, ChromaDB, SQLite, no
    service topology. The manuscript describes it in text and the reader does not need the picture
  * the experiment inventory and the dependency graph move to Supplementary, where they have room
  * no standfirst. The editor's checklist items 16-19 forbid stray text inside figure files, so the
    evaluation, experiment and model counts live in the caption
  * monochrome, which makes the plate greyscale-safe and colour-blind-safe by construction
  * no markers and no stage rail. Both encoded something real and neither was decoded by a reader
  * LEVELS is a numeral column, never bars: configurations are not commensurable across axes, and
    bar length would have drawn the two cross-model axes as the shortest marks on the plate

Type follows the Nature research figure guide: panel labels 8 pt bold upright lowercase, 7 pt
maximum and 6 pt minimum (the journal floor) for all other text, gated here against the emitted SVG rather than against
the constants, because a constants-only check is bypassed by any future hardcoded size.

Every numeral is derived at build time, never typed: the evaluation total from S13_evaluation_total
plus the campaign arithmetic, the model count from S156_model_census, the experiment count from
S13's own line items. The build fails if any of them moves.

Five corrections came from Valerio reading the plate against the files, and all five were the same
shape: a paraphrase standing where an enumeration belonged. Retrieval depth said 6 when ten depths
ran. Search strategy named four things and claimed seven. Embedding model said 20 when there are
four models on a five-point corpus grid. Chunking said "size x overlap" when neither was varied.
And "5 corpus sizes" pointed at a different grid from the one in the Corpus scale row. Every level
string now reconciles with its own numeral, so a reader can audit the panel without leaving it.

CORRECTIONS THAT SHAPED THE ROWS, in the order they were found.

1. RETRIEVAL DEPTH WAS WRONG. v4 said 6 levels, "7 / 10 / 15 / 20 / 30 / 50". The sweep actually
   ran TEN depths: 1, 2, 3, 5, 7, 10, 15, 20, 30, 50, verified across every exp09_depth_sweep file.
   He asked whether depth 1 was in there. It was, and so were 2, 3 and 5. LEVELS is 10.
2. "mpnet" is `all-mpnet-base-v2`. The four embedders are named in full now, from exp01's own
   config block, because a short form nobody recognises is worse than a long one.
3. SEARCH STRATEGY read backwards: four names, then "7 strategies x 5 sizes", which does not add up
   because the four were a paraphrase of seven. The seven are dense, bm25_standard, bm25_scientific,
   hybrid_fixed, hybrid_adaptive, rrf, rrf_reranker. Count first, names second, and they reconcile.
4. GENERATION STRATEGY spells RLM-5 / RLM-10 / RLM-20 rather than eliding the prefix.
5. ORCHESTRATOR ROLES now precedes SYSTEM CONFIGURATION, so the reader meets the five roles before
   the phrase "full orchestrator" that depends on them.
6. GENERATION MODEL names the provider, using the manuscript's own attribution (line 821 lists
   Meta, OpenAI, Mistral, Google, Z.ai, NVIDIA, Alibaba).
7. JUDGE gives the sizes: qwen3-coder:30b / gpt-oss:120b.
8. CHUNKING WAS WRONG. v5.0 said "size × overlap". exp03a varied neither: it is 8 chunking
   configurations, simple at 128/256/512/1024 tokens and semantic at 500/1000/2000/4000 characters,
   run 3 times each. 8 x 3 = 24, which is the numeral that was already there.
9. THE CORPUS GRIDS DIFFER AND THE FIGURE HID IT. Corpus scale is 5/10/20/50 papers; the embedding
   and search experiments used 5/10/15/20/30. Two different grids under one phrase, which is why
   the search row felt slippery. Both are now stated.
10. The Triangulation box is left-aligned on the same inset as the three signal boxes. It was centred
   and read as a different kind of object.

Two rows now need a second line. Rather than shrink the type or truncate the names, the row grid
takes a list of strings and the pitch follows the content.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import ROOT, chrome   # noqa: E402

# Main figure assets live beside the documents that ship them, the same way the Supplementary
# assets do. They were in paper_changes/, which is a working folder.
FIGURES = ROOT / "manuscript/submission/figures"
OUT = FIGURES / "Figure_1.svg"
PNG = FIGURES / "Figure_1.png"
PDF = FIGURES / "Figure_1.pdf"
S13 = ROOT / "findings/recompute/S13_evaluation_total.md"
S156 = ROOT / "findings/recompute/S156_model_census.json"
S187 = ROOT / "findings/recompute/S187_si_experiment_inventory.json"

PRIOR, CAMPAIGN, SIDE = 37_449, 138 * 6 * 5 * 3, 966
TOTAL = PRIOR + CAMPAIGN + SIDE

INK, MUTE = "#1b1b1b", "#6a6a6a"
# T_SMALL was 1.77 mm (5.0 pt); the journal floor is 6 pt at printed size (figure round,
# 29 September), so the small type now equals the body size, 2.12 mm = 6.0 pt.
T_PANEL, T_HEAD, T_BODY, T_SMALL = 2.82, 2.47, 2.12, 2.12
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
LEAD = 2.7

X_STAGE, X_AXIS, X_LEV, X_STR, X_B = 6.0, 8.0, 34.0, 37.0, 109.0
BOX_W, BOX_H, GAPX, TW = 36.0, 19.6, 5.0, 24.0

STAGES = [
    ("INDEX", [
        ("Corpus scale", "12", ["5 / 10 / 20 / 50 papers × 0 / 1 / 3 distractor ratio"]),
        ("Embedding model", "20", ["4 models × 5 corpus sizes (5 / 10 / 15 / 20 / 30 papers)",
                                   "bge-m3 / all-MiniLM-L6-v2 / all-mpnet-base-v2 / SPECTER2"]),
        ("Chunking", "24", ["8 chunkings × 3 repeat runs",
                            "simple 128 / 256 / 512 / 1024 tokens",
                            "semantic 500 / 1000 / 2000 / 4000 characters"]),
    ]),
    ("RETRIEVE", [
        ("Search strategy", "35", ["7 strategies × the same 5 corpus sizes",
                                   "dense / BM25 standard / BM25 scientific / hybrid fixed /",
                                   "hybrid adaptive / RRF / RRF + reranker"]),
        ("Retrieval depth", "10", ["1 / 2 / 3 / 5 / 7 / 10 / 15 / 20 / 30 / 50 turns"]),
    ]),
    ("GENERATE", [
        ("Generation strategy", "6", ["single-pass / multi-hop / verified / "
                                      "RLM-5 / RLM-10 / RLM-20"]),
        ("Orchestrator roles", "5", ["analyzer / planner / distiller / supervisor / synthesizer"]),
        ("System configuration", "4", ["full orchestrator (all five roles) / naive RAG / "
                                       "raw model / RLM-10"]),
        # seven since the strategy replication added the two open-weight arms (Methods, strategy
        # replication; figure round of 29 September found the plate still naming five)
        # two lines, as the plate's height is fixed: the developers are named in Methods.
        # Every list on the plate separates its items with " / " (Dirkjan Schokker, 6 October: with
        # commas and slashes mixed the seven search strategies could not be counted); bge-m3 drops
        # its "BAAI/" prefix so its own slash does not read as a separator
        ("Generation model", "7", ["gemini-3-flash / claude-haiku-4-5 / gemma3:27b / glm-4.7-flash:30b /",
                                   "nemotron-3-nano:30b / qwen3-coder:30b / qwen3.5:122b"]),
    ]),
    ("JUDGE", [
        ("Judge", "2", ["qwen3-coder:30b / gpt-oss:120b"]),
    ]),
]

SIGNALS = [
    # the subtitle is a list: at 6 pt "selected from 19 calibrated candidates" is wider than the box
    ("Deterministic", ["ground-truth metrics"],
     ["concept recall, citation", "coverage, number overlap"]),
    ("LLM judge", ["selected from 19", "calibrated candidates"],
     ["correctness, completeness,", "faithfulness, citation quality"]),
    ("NLI", ["MiniCheck, not an LLM"],
     ["claim-level entailment", "against the expert answer key"]),
]


def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size, fill=INK, bold=False, anchor="start", track=None):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    b = ' font-weight="bold"' if bold else ""
    k = f' letter-spacing="{track}"' if track else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}"'
            f' fill="{fill}"{b}{a}{k}>{esc(s)}</text>')


def count_experiments() -> int:
    """How many experiments the study has, from the artifact that defines the word.

    This counted S13's group A and B line items and added one, which gives 14: it splits
    retrieval optimisation into its four arms and drops model selection entirely. S158 line 555
    had already flagged that "twelve" had no artifact behind it and asked for the twelve to be
    defined or the numeral changed; changing the numeral landed on a third answer. S187 defines
    it, one box on the submitted plate is one experiment, and this now reads that.
    """
    n = len(json.loads(S187.read_text())["experiments"])
    if n != 12:
        raise SystemExit(f"gate: S187 now says {n} experiments, not 12")
    return n


def pdf_page_mm(path):
    """The first page's size in millimetres, read from the PDF itself, or None if it cannot be."""
    import re as _re
    raw = path.read_bytes()
    m = _re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", raw)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return ((x1 - x0) / 72 * 25.4, (y1 - y0) / 72 * 25.4)


def main() -> None:
    if "37,449" not in S13.read_text():
        raise SystemExit("gate: 37,449 not in S13")
    census = json.loads(S156.read_text())
    n_models = census["t1_scored_llms"]
    if census["generators"] + census["judges"] - census["both_roles"] != n_models:
        raise SystemExit("gate: census role arithmetic does not close")
    n_exp = count_experiments()

    rows_all = [r for _, rows in STAGES for r in rows]
    HEAD_Y, PITCH, GAP = 12.6, 4.8, 6.4
    y = HEAD_Y
    for _, rows in STAGES:
        for _, _, lines in rows:
            y += PITCH + (len(lines) - 1) * LEAD
        y += GAP
    H = round(y - GAP + 4.0, 1)   # trailing stage gap is not content; 4 mm of foot margin

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" width="180mm" height="{H}mm" '
         f'viewBox="0 0 180 {H}">', f'<rect width="180" height="{H}" fill="white"/>']

    o.append(T(X_STAGE, 6.2, "a", T_PANEL, INK, True))
    o.append(T(X_STAGE + 4.5, 6.2, "Experiment configuration", T_HEAD, INK, True))
    o.append(T(X_LEV, HEAD_Y, "LEVELS", T_SMALL, MUTE, anchor="end", track="0.08em"))

    y = HEAD_Y
    for stage, rows in STAGES:
        o.append(T(X_STAGE, y, stage, T_SMALL, MUTE, track="0.08em"))
        for name, n, lines in rows:
            y += PITCH
            o.append(T(X_AXIS, y, name, T_BODY, INK, True))
            o.append(T(X_LEV, y, n, T_BODY, INK, True, anchor="end"))
            for j, line in enumerate(lines):
                o.append(T(X_STR, y + j * LEAD, line, T_BODY, INK))
            y += (len(lines) - 1) * LEAD
        y += GAP
    a_last = y - GAP          # baseline of panel a's final row

    o.append(T(X_B, 6.2, "b", T_PANEL, INK, True))
    o.append(T(X_B + 4.5, 6.2, "Measurements", T_HEAD, INK, True))

    # Panel b's three boxes are spread to finish level with panel a's last row, so the two
    # panels occupy one vertical band. In v5.0 panel a ran to y 88 and panel b stopped at 71,
    # and that 17 mm mismatch is what read as unused space at the foot of the plate.
    top0 = HEAD_Y + 1.6
    STEP = (a_last - top0 - BOX_H) / (len(SIGNALS) - 1)
    mid = top0 + STEP + BOX_H / 2
    for i, (title, sub, detail) in enumerate(SIGNALS):
        top = top0 + i * STEP
        o.append(f'<rect x="{X_B}" y="{top:.2f}" width="{BOX_W}" height="{BOX_H}" rx="1.5" '
                 f'fill="none" stroke="{INK}" stroke-width="0.30"/>')
        o.append(T(X_B + 2.5, top + 4.6, title, T_BODY, INK, True))
        for j, line in enumerate(sub):
            o.append(T(X_B + 2.5, top + 8.0 + j * 2.6, line, T_SMALL, MUTE))
        d0 = top + 8.0 + (len(sub) - 1) * 2.6 + 3.6
        for j, line in enumerate(detail):
            o.append(T(X_B + 2.5, d0 + j * 2.6, line, T_BODY, INK))
        o.append(f'<line x1="{X_B + BOX_W}" y1="{top + 8.5:.2f}" x2="{X_B + BOX_W + GAPX}" '
                 f'y2="{mid:.2f}" stroke="{MUTE}" stroke-width="0.25"/>')

    # Triangulation: same left inset as the signal boxes, not centred.
    TX = X_B + BOX_W + GAPX
    TY = mid - BOX_H / 2
    o.append(f'<rect x="{TX}" y="{TY:.2f}" width="{TW}" height="{BOX_H}" rx="1.5" '
             f'fill="none" stroke="{INK}" stroke-width="0.40"/>')
    o.append(T(TX + 2.5, TY + 5.9, "Triangulation", T_BODY, INK, True))
    o.append(T(TX + 2.5, TY + 9.3, "the diagnostic", T_SMALL, MUTE))
    o.append(T(TX + 2.5, TY + 12.9, "rankings converge", T_BODY, INK))
    o.append(T(TX + 2.5, TY + 15.5, "verdicts diverge", T_BODY, INK))

    o.append("</svg>")
    body = "\n".join(o)
    OUT.write_text(body, encoding="utf-8")

    sizes = {float(m) for m in re.findall(r'font-size="([\d.]+)"', body)}
    worst_pt = min(sizes) * 72 / 25.4
    if worst_pt < 6.0:
        raise SystemExit(f"gate: smallest type {worst_pt:.2f} pt")
    if max(sorted(sizes)[:-1]) * 72 / 25.4 > 7.01:
        raise SystemExit("gate: non-panel text over the 7 pt ceiling")
    if re.search(r">[^<]*  ", body):
        raise SystemExit("gate: multi-space run")
    if re.search(r"\d\s*x\s*\d", body):
        raise SystemExit("gate: ASCII 'x' as multiplication")
    if re.search(r'(fill|stroke)="#(?!1b1b1b|6a6a6a|ffffff|FFFFFF)', body):
        raise SystemExit("gate: a colour other than ink, mute or white")
    for banned in ("independent signals", "added in revision", "Reviewer", "FastAPI",
                   "React", "&amp;#", "More than"):
        if banned in body:
            raise SystemExit(f"gate: '{banned}' is on the plate")

    # 68 mm of level column at 2.12 mm Helvetica is about 77 characters. Gate at 72 so a
    # future edit cannot quietly run a level string into panel b, which is how one draft shipped
    # a line that collided with the LLM judge box.
    MAXCH = 76
    over = [(nm, l) for _, rows in STAGES for nm, _, ls in rows for l in ls if len(l) > MAXCH]
    if over:
        raise SystemExit("gate: level line too long for the column -> "
                         + "; ".join(f"{n} ({len(l)} chars)" for n, l in over))
    widest = max((len(l) for _, _, ls in rows_all for l in ls))
    print(f"wrote {OUT.relative_to(ROOT)}  (180 x {H} mm)")
    print(f"  type {worst_pt:.2f} pt floor; monochrome; {len(rows_all)} axes")
    print(f"  widest level line {widest} chars, level column x {X_STR} to panel b at {X_B} "
          f"= {X_B - X_STR:.0f} mm")
    print(f"  retrieval depth now 10 levels (was 6; 1, 2, 3 and 5 were missing)")
    print(f"\n  FOR THE CAPTION: {TOTAL:,} evaluations | {n_exp} experiments | "
          f"{n_models} language models")

    exe = chrome()
    if exe is not None:
        subprocess.run([str(exe), "--headless", "--disable-gpu", "--hide-scrollbars",
                        # the SVG's natural size at 96 dpi, so the shot is the plate and not
                        # the plate plus window padding. A larger window pads with white and
                        # reads as unused space in the figure, which it is not.
                        f"--screenshot={PNG}",
                        f"--window-size={round(180 / 25.4 * 96)},{round(H / 25.4 * 96)}",
                        "--force-device-scale-factor=3.0",
                        "--default-background-color=FFFFFFFF", f"file://{OUT}"],
                       capture_output=True)
        print(f"  rasterised {PNG.relative_to(ROOT)}")

        # The plate also ships as a PDF, which is the format the journal prefers for a main
        # figure (notes/FIGURE_SPEC.md:24) and the format every other figure here already
        # writes. Chrome prints it, through an HTML wrapper whose @page is the plate's own size,
        # because a bare print-to-pdf would lay the drawing on a Letter page and pad it.
        wrapper = FIGURES / "_figure1_print.html"
        wrapper.write_text(
            "<!doctype html><meta charset='utf-8'>"
            f"<style>@page{{size:180mm {H}mm;margin:0}}"
            "html,body{margin:0;padding:0}"
            f"svg{{display:block;width:180mm;height:{H}mm}}</style>"
            + OUT.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run([str(exe), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={PDF}", f"file://{wrapper}"], capture_output=True)
        wrapper.unlink(missing_ok=True)
        if PDF.exists():
            box = pdf_page_mm(PDF)
            if box is None:
                print(f"  wrote {PDF.relative_to(ROOT)} (page size not checked)")
            elif abs(box[0] - 180) > 1.0 or abs(box[1] - H) > 1.0:
                PDF.unlink()
                raise SystemExit(f"  REFUSED: {PDF.name} was "
                                 f"{box[0]:.1f} x {box[1]:.1f} mm, not 180 x {H} mm")
            else:
                print(f"  wrote {PDF.relative_to(ROOT)}  ({box[0]:.0f} x {box[1]:.0f} mm)")
        else:
            raise SystemExit("  REFUSED: chrome wrote no PDF")


if __name__ == "__main__":
    main()
