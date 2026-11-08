"""house_style: one drawing style for every plot of the Mentori revision (style_1028, 28 October 2026).

Every redraw imports this module and takes its colours, line widths, mark sizes, box plot, strip, bar, estimate,
key and number format from here, so a box plot, a colour or a key looks the same on every plate. The rules in plain
words, the colour table and each figure's deviations are in STYLE.md (findings/scratch_archive/2026-10-30/reports/style_1028/style/).

Values come from experiments/FIGURE_LOCK.toml where the lock has one (fonts, sizes, palette, line minimum); the
module refuses to load when the lock is missing or not agreed. Nothing here computes a statistic the caller has not
given it, except box_stats(), which a redraw uses only when its own script has no summary of its own: a restyle
draws the numbers the plate's script already writes, never new ones.

Anchors: Figure 5 (S497, locked D166) and Figure 2 (S463). Where they differ, STYLE.md says which rule this module
encodes and lists the open question (Q1 whisker rule, Q2 cividis direction).

Coordinates: helpers that place things on the page take millimetres from the plate's top left, as the figure
scripts do (S457, S463, S497).
"""
from __future__ import annotations

import math
import os
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIGURE_LOCK = REPO / "experiments" / "FIGURE_LOCK.toml"
if not FIGURE_LOCK.exists():
    raise SystemExit(f"house_style: {FIGURE_LOCK} is missing; no plate is drawn without the figure lock (D87)")
FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
if FLOCK.get("status") != "agreed":
    raise SystemExit(f"house_style: {FIGURE_LOCK} has status {FLOCK.get('status')!r}, not 'agreed' (D87)")

MM_PT = 25.4 / 72                      # millimetres per point

# ---------------------------------------------------------------------------------------------------------------------
# type (FIGURE_LOCK [type]): one size for every text, the lock's minimum
# ---------------------------------------------------------------------------------------------------------------------
FONT = FLOCK["type"]["font_families"][0]                         # Helvetica
PT = float(FLOCK["type"]["font_min_pt"])                         # 8 pt: ticks, axis labels, keys, numbers in cells
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])              # 8 pt
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]             # bold
LETTER_CASE = str.lower if FLOCK["type"]["panel_letter_case"] == "lowercase" else str.upper
LINE_MIN_PT = float(FLOCK["lines"]["line_min_pt"])               # 0.3 pt
PAGE_W_MM = float(FLOCK["page"]["width_double_mm"])              # 183
PAGE_W1_MM = float(FLOCK["page"]["width_single_mm"])             # 89
PAGE_H_MAX_MM = float(FLOCK["page"]["height_max_mm"])            # 170
CONTRAST_MIN = float(FLOCK["type"]["contrast_min_ratio"])        # 4.5

# ---------------------------------------------------------------------------------------------------------------------
# colours (FIGURE_LOCK [colour]): the eight Okabe-Ito colours, cividis, and five named greys. Nothing else.
# ---------------------------------------------------------------------------------------------------------------------
_CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
OKABE = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"],
                 _CAT))
WHITE, BLACK = "#FFFFFF", "#000000"
GREY = {
    "text": "#595959",     # secondary text (headers, notes): 7.0:1 on white
    "dot": "#8C8C8C",      # data dots without a category (S457.DOT_GREY): 3.4:1 on white, not faint
    "line": "#999999",     # background lines, leader lines, dividers, an "other" fill (Okabe-Ito's grey)
    "fill": "#BBBBBB",     # a neutral fill: tie, judge passes, both passed
    "band": "#E0E0E0",     # a reference band or a cell with no score (never under text that must reach 4.5:1)
}
# Two greys of the locked Figure 5 (D166) stay as drawn there and are allowed only on that plate: "#888888" (b's
# judge fail, papers low) and "#949494" (e's dividers). Both are within S448's grey rule; they look like GREY["dot"]
# and GREY["line"].
LOCKED_GREYS = {"#888888", "#949494"}

# Colour by category. A kind is one family of categories; within a kind a category has one colour on every plate.
# Kinds that share a colour are never drawn on the same plate (D153 Q3: one hue never means two things on one plate);
# check_plate_kinds() refuses a plate that mixes them. Names are as the plates print them.
COLOURS = {
    # generation strategies, where strategies are told apart by colour (lines, overlaid series). A strategy that has
    # its own labelled row or column takes no colour.
    "strategy": {
        "single pass": OKABE["orange"],
        "multi-hop": OKABE["bluish green"],
        "verified pass": OKABE["reddish purple"],
        "RLM-5": OKABE["sky blue"],
        "RLM-10": OKABE["blue"],
        "RLM-20": OKABE["black"],
        "matched budget": OKABE["orange"],          # single pass at matched budget: single pass's colour, open mark
    },
    # the RLM systems compared across turn caps (Figure 3 a, Supplementary 12, 20). Mentori RLM is RLM-10's blue.
    "system": {
        "Mentori RLM": OKABE["blue"],
        "package RLM": OKABE["vermillion"],
        "gemini-3-flash-preview reference": OKABE["blue"],   # Figure 3 b's dashed median line (D146)
    },
    # the evaluation signals (Figure 5 e; Supplementary 8 c)
    "signal": {
        "Judge": OKABE["blue"],
        "Concepts": OKABE["orange"],
        "Papers": OKABE["black"],
        "Faithfulness": OKABE["vermillion"],
    },
    # code-generation prompting families (Figure 6, Supplementary 13 to 19)
    "family": {
        "free-form": OKABE["blue"],
        "introspection": OKABE["reddish purple"],
        "structured": OKABE["orange"],
    },
    # one arm against a reference, per question or pair (Figure 5 d, Figure 2 e, Supplementary 18, Supplementary X):
    # worse in vermillion, the same in grey, better in blue (D200, pick R1d a: these two for better and worse everywhere)
    "comparison": {
        "worse": OKABE["vermillion"],               # single pass higher, harmed, lost, signal wrong
        "tie": GREY["fill"],                        # tie, both passed, signal arguable
        "better": OKABE["blue"],                    # strategy higher, helped, rescued, signal right
        "both failed": WHITE,                       # drawn with a GREY["line"] edge
    },
    # an attempt's outcome in code generation (Figure 6 c, Supplementary 14 b, 15); always with its pattern (PATTERN)
    "outcome": {
        "passed": OKABE["bluish green"],
        "wrong values": OKABE["yellow"],
        "no result": OKABE["sky blue"],
        "tool or call failure, other": OKABE["vermillion"],
        "length stop": OKABE["black"],
        "tools refused by Ollama": "#5A5A5A",       # S447.TOOLS_GREY, as Supplementary 15 draws it
        "other (harness, no code)": GREY["line"],
    },
    # the judge's verdict with Papers precision (Figure 5 b and c, locked D166)
    "verdict": {
        "judge passes, papers high": GREY["fill"],
        "judge passes, papers low": OKABE["reddish purple"],
        "judge fails, papers high": OKABE["sky blue"],
        "judge fails, papers low": "#888888",
        "judge passes": GREY["fill"],
        "judge fails": OKABE["sky blue"],
    },
    # how an RLM answer stopped (Supplementary 12 a)
    "stop": {
        "answer within the cap": OKABE["blue"],
        "answer from the closing call": OKABE["sky blue"],
        "closing call returned code": OKABE["reddish purple"],
        "answer with no text": OKABE["yellow"],
        "closing call failed": OKABE["orange"],
        "a turn's model call failed": OKABE["vermillion"],
        "the package's own code failed": OKABE["black"],     # was bluish green
    },
}
# Marker shapes go with the colour (journal: patterns in addition to colours), as Figure 5 e and Figure 6 b draw them.
MARKERS = {
    "strategy": {"single pass": "o", "multi-hop": "s", "verified pass": "D", "RLM-5": "^", "RLM-10": "v",
                 "RLM-20": "h", "matched budget": "o"},
    "system": {"Mentori RLM": "o", "package RLM": "o"},
    "signal": {"Judge": "o", "Concepts": "s", "Papers": "D", "Faithfulness": "^"},
    "family": {"free-form": "o", "introspection": "s", "structured": "D"},
}
OPEN_MARKS = {("strategy", "matched budget")}           # drawn open: white fill, the colour as a 0.5 pt edge
# a marker's size relative to a circle of the same nominal size, so a square and a diamond weigh the same (S497)
MARKER_SCALE = {"o": 1.0, "s": 0.9, "D": 0.85, "^": 1.0, "v": 1.0, "h": 1.0}

# hosting: told apart by fill, never by colour (Figure 6 d): cloud filled black, open-weight open black. In a dense
# swarm (dots under 1 mm) an open circle cannot be seen, so there open-weight is GREY["dot"] filled.
HOSTING = {
    "cloud": {"mfc": BLACK, "mec": BLACK},
    "open-weight": {"mfc": WHITE, "mec": BLACK},
    "open-weight, dense": {"mfc": GREY["dot"], "mec": GREY["dot"]},
}

# fill patterns for attempt outcomes and failure kinds (S481.OPAT and S447.KIND_PATTERN). Drawn as real lines, dots
# and rings by S447.pattern_marks (pattern() below), in black or white ink by contrast, lines at the lock's minimum
# width, HATCH_MM apart. Never matplotlib hatches: they reach the SVG as url() patterns, which S448 R10 cannot compare.
PATTERN = {"passed": "", "wrong values": "z", "no result": ".", "tool or call failure, other": "\\",
           "length stop": "-", "tools refused by Ollama": "*", "other (harness, no code)": "o"}

# Series with no kind above (Supplementary 2's embedding models and search strategies): this order, colour and
# shape together, the same order on every panel of a plate.
SERIES_ORDER = [(OKABE["blue"], "o"), (OKABE["orange"], "s"), (OKABE["bluish green"], "D"),
                (OKABE["reddish purple"], "^"), (OKABE["sky blue"], "v"), (OKABE["vermillion"], "h"),
                (OKABE["black"], "P"), (OKABE["yellow"], "X")]   # yellow last, and only with a black edge


def colour(kind: str, name: str) -> str:
    """The colour of category `name` of `kind`. An unknown kind or name raises KeyError: a redraw never invents one."""
    return COLOURS[kind][name]


def marker(kind: str, name: str) -> str:
    return MARKERS.get(kind, {}).get(name, "o")


def check_plate_kinds(kinds) -> None:
    """Refuse a plate whose colour kinds share a hex (D153 Q3). kinds: the COLOURS kinds the plate draws."""
    seen = {}
    for k in kinds:
        for nm, hx in COLOURS[k].items():
            if hx in (WHITE, BLACK) or hx in GREY.values():
                continue
            if hx in seen and seen[hx][0] != k:
                raise SystemExit(f"house_style: {hx} means {seen[hx][0]} {seen[hx][1]!r} and {k} {nm!r} on one plate")
            seen.setdefault(hx, (k, nm))


# ---------------------------------------------------------------------------------------------------------------------
# cividis (FIGURE_LOCK [colour] continuous). The larger value takes the lighter, yellow end (Figure 3 c, Figure 5 f,
# Figure 6 a, Supplementary 4 and 16). Q2 in STYLE.md: Figures 2 a, 2 d, 4 a, 4 c and Supplementary 3 a, 8 d, 11 e
# draw the reverse today.
# ---------------------------------------------------------------------------------------------------------------------
def _cividis_hex(i: int) -> str:
    from matplotlib import colormaps
    cm = colormaps[FLOCK["colour"]["continuous"]]
    return "#%02X%02X%02X" % tuple(round(255 * v) for v in cm(int(i))[:3])


def cividis_levels(n: int) -> list[str]:
    """n ordered levels, lowest value first (darkest) to highest value last (lightest). Four levels take Figure 2 a's
    entries (D127: 0, 110, 190, 255); any other count is evenly spaced (Figure 5 f's six: 0, 51, ... 255)."""
    if n < 2:
        raise ValueError("cividis_levels needs at least 2 levels")
    idx = (0, 110, 190, 255) if n == 4 else tuple(round(255 * i / (n - 1)) for i in range(n))
    return [_cividis_hex(i) for i in idx]


def cividis_value(x: float, lo: float, hi: float) -> str:
    """A continuous value on cividis, lo at the dark end and hi at the light end, clipped."""
    t = 0.0 if hi == lo else min(1.0, max(0.0, (x - lo) / (hi - lo)))
    return _cividis_hex(round(255 * t))


# ---------------------------------------------------------------------------------------------------------------------
# lines (points). Every width at least FIGURE_LOCK [lines] line_min_pt.
# ---------------------------------------------------------------------------------------------------------------------
LW = {
    "axis": 0.5,          # axis lines and ticks
    "box": 0.5,           # box outline
    "whisker": 0.5,       # whiskers and caps
    "median": 1.0,        # the box's median line (Figure 2 b, Figure 5 a)
    "interval": 0.9,      # an estimate's interval (Figure 2 a, Figure 4 a)
    "series": 1.0,        # a data line that is the result (Supplementary 2 a, 2 b; 4 c, d)
    "connector": 0.5,     # a thin line joining summary marks (Figure 3 a's medians; a dumbbell's two ends)
    "background": 0.6,    # one line per item behind a summary (Figure 3 b's question lines, GREY["line"])
    "summary": 1.6,       # the summary line over background lines (Figure 3 b's median)
    "reference": 0.5,     # zero line, a threshold, a cap: black, solid; dashed when it crosses the data
    "divider": 0.5,       # a line between row groups (GREY["line"])
    "hatch": LINE_MIN_PT, # pattern lines inside a bar (S447.draw_pattern: [lines] line_min_pt)
}
assert all(v >= LINE_MIN_PT for v in LW.values()), "a house line width is under FIGURE_LOCK [lines] line_min_pt"
DASH = (3.0, 1.5)         # on, off, in line widths (Figure 3 b's reference); dotted lines are not used (faint)

# ---------------------------------------------------------------------------------------------------------------------
# marks (millimetres)
# ---------------------------------------------------------------------------------------------------------------------
DOT_MM = 0.45             # a dot per item under a box when more than 30 items share the box (Figure 5 a, Figure 2 b)
DOT_SPARSE_MM = 1.0       # a dot per item under a box when 30 or fewer share it (Figure 6 b, Supplementary 13 a)
DOT_PITCH_MM = 0.50       # swarm slot pitch across the row
MARK_MM = 1.25            # a categorical mark in a strip (Figure 5 e)
KEY_MARK_MM = 1.8         # a mark in a key (Figure 5 e's key: larger than the plotted ones)
ESTIMATE_MM = 1.5         # an estimate's dot (mean, rate, net) with its interval (Figure 2 a, Figure 4 a)
SWATCH_MM = (2.6, 2.4)    # a key's colour square for a bar or a tile (width, height)
BOX_FRAC = 0.40           # box thickness, as a share of the slot (the distance between neighbouring boxes)
BAND_FRAC = 0.67          # the dot band under a box, as a share of the slot
CAP_FRAC = 5 / 12         # a whisker cap, as a share of the box thickness (Figure 5 a: 1.0 mm on a 2.4 mm box)
BAR_FRAC = 0.70           # a bar's thickness, as a share of its row
SMALL_N = 5               # fewer values than this: no box; the dots and a 1.0 pt tick at the stated summary


# ---------------------------------------------------------------------------------------------------------------------
# matplotlib settings
# ---------------------------------------------------------------------------------------------------------------------
def rc(salt: str = "house_style") -> dict:
    """matplotlib's settings for a plate: S457.plate_rc's settings (shared by Figures 2, 5, Supplementary 11), plus no
    top or right spine, no grid, no legend frame, butt line ends, black wherever a call names no colour."""
    from cycler import cycler
    lw = LW["axis"]
    return {"font.family": FONT, "font.size": PT, "svg.fonttype": "none", "pdf.fonttype": 42,
            "axes.linewidth": lw, "xtick.major.width": lw, "ytick.major.width": lw,
            "xtick.minor.width": lw, "ytick.minor.width": lw,
            "xtick.major.size": 2, "ytick.major.size": 2, "xtick.minor.size": 1.2, "ytick.minor.size": 1.2,
            "xtick.direction": "out", "ytick.direction": "out",
            "xtick.labelsize": PT, "ytick.labelsize": PT, "axes.labelsize": PT, "axes.titlesize": PT,
            "legend.fontsize": PT, "legend.frameon": False,
            "axes.edgecolor": BLACK, "xtick.color": BLACK, "ytick.color": BLACK,
            "text.color": BLACK, "axes.labelcolor": BLACK,
            "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
            "axes.unicode_minus": False,            # minus signs come from fmt_num(), as U+2212
            "lines.solid_capstyle": "butt", "lines.dash_capstyle": "butt",
            # nothing takes matplotlib's default colours: a call that names no colour draws black
            "axes.prop_cycle": cycler(color=[BLACK]), "lines.color": BLACK, "patch.facecolor": BLACK,
            "patch.edgecolor": BLACK, "lines.markeredgecolor": BLACK, "lines.markerfacecolor": BLACK,
            "image.cmap": FLOCK["colour"]["continuous"],
            "svg.hashsalt": salt}


def apply_rc(salt: str = "house_style") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(rc(salt))


# ---------------------------------------------------------------------------------------------------------------------
# numbers and words
# ---------------------------------------------------------------------------------------------------------------------
MINUS = "−"


def fmt_num(x: float, nd: int = 0, sign: bool = False, thousands: bool = True) -> str:
    """A number as the plates print it: U+2212 for a minus, a comma every three digits, '+' on request for a
    difference, half-up rounding (S457.half_up), no '-0'."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    body = f"{abs(q):,.{nd}f}" if thousands else f"{abs(q):.{nd}f}"
    if q < 0:
        return MINUS + body
    return ("+" + body) if (sign and q > 0) else body


def axis_label(words: str, unit: str | None = None) -> str:
    """An axis label in sentence case with its unit in parentheses: axis_label('concept recall', '%') gives
    'Concept recall (%)'. A model or package name at the start keeps its own case (gemini-3-flash-preview)."""
    w = words.strip()
    if w and w[0].isalpha() and w[0].islower() and not any(w.startswith(p) for p in _OWN_CASE):
        w = w[0].upper() + w[1:]
    return f"{w} ({unit})" if unit else w


_OWN_CASE = ("gemini", "gpt-", "qwen", "gemma", "devstral", "claude", "olmo", "nemotron", "deepseek", "llama", "glm",
             "bge", "all-", "allenai", "specter", "n ", "n=")


def ink_on(bg: str) -> str:
    """Black or white text on a fill, whichever reaches FIGURE_LOCK [type] contrast_min_ratio (black first)."""
    for ink in (BLACK, WHITE):
        if wcag(ink, bg) >= CONTRAST_MIN:
            return ink
    raise ValueError(f"neither black nor white reaches {CONTRAST_MIN}:1 on {bg}")


def wcag(c1: str, c2: str) -> float:
    def lum(c):
        c = tuple(int(c.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


# ---------------------------------------------------------------------------------------------------------------------
# page geometry
# ---------------------------------------------------------------------------------------------------------------------
def figure(w_mm: float = PAGE_W_MM, h_mm: float = PAGE_H_MAX_MM):
    """A blank plate w_mm by h_mm, white."""
    import matplotlib.pyplot as plt
    if w_mm - PAGE_W_MM > 0.5 or h_mm - PAGE_H_MAX_MM > 1e-9:
        raise SystemExit(f"house_style: a plate of {w_mm} x {h_mm} mm is past FIGURE_LOCK [page]")
    fig = plt.figure(figsize=(w_mm / 25.4, h_mm / 25.4))
    fig.patch.set_facecolor(WHITE)
    fig._hs_mm = (w_mm, h_mm)
    return fig


def axes_mm(fig, x: float, y: float, w: float, h: float, spines_on=("left", "bottom")):
    """Axes at x, y (top left, mm from the plate's top left), w by h mm, with only the named spines."""
    W, H = fig._hs_mm
    ax = fig.add_axes((x / W, 1 - (y + h) / H, w / W, h / H))
    for s in ("left", "right", "top", "bottom"):
        ax.spines[s].set_visible(s in spines_on)
    if "left" not in spines_on:
        ax.tick_params(axis="y", left=False, labelleft=False)
    if "bottom" not in spines_on:
        ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.set_facecolor("none")
    return ax


def mm_per_unit(ax) -> tuple[float, float]:
    """Millimetres per data unit along x and along y, from the axes' size and limits (set the limits first)."""
    fig = ax.figure
    W, H = fig._hs_mm
    pos = ax.get_position()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    return pos.width * W / abs(x1 - x0), pos.height * H / abs(y1 - y0)


def text_mm(fig, x: float, y: float, s: str, **kw):
    """Text at x, y mm from the plate's top left; baseline at y unless va is given."""
    W, H = fig._hs_mm
    kw.setdefault("fontsize", PT)
    kw.setdefault("va", "baseline")
    return fig.text(x / W, 1 - y / H, s, **kw)


def panel_letter(fig, x: float, y: float, ch: str):
    """The panel letter: 8 pt bold lowercase, its baseline on the panel's first key or header line."""
    return text_mm(fig, x, y, LETTER_CASE(ch), fontsize=PT_LETTER, fontweight=LETTER_WEIGHT, ha="left")


# ---------------------------------------------------------------------------------------------------------------------
# dots placed apart (S457.swarm, the same code, so dot positions equal the current plates')
# ---------------------------------------------------------------------------------------------------------------------
def swarm(xs_mm, half=2.0, pitch=DOT_PITCH_MM, dot=DOT_MM):
    """Offsets (mm, across the row) for dots at exact positions xs_mm: each dot in value order takes the slot nearest
    the row's centre (0, +pitch, -pitch, ...) within +-half where no placed dot lies closer than dot + 0.05 mm; a dot
    with no free slot takes the slot farthest from its neighbours and overlaps. Returns (offsets, overlapping).
    Never random: the same values give the same picture."""
    slots = [0.0]
    k = 1
    while k * pitch <= half + 1e-9:
        slots += [k * pitch, -k * pitch]
        k += 1
    order = sorted(range(len(xs_mm)), key=lambda i: xs_mm[i])
    placed, off, over = [], [0.0] * len(xs_mm), 0
    need = dot + 0.05
    for i in order:
        x = xs_mm[i]
        near = [(px, py) for px, py in placed if abs(px - x) < need]
        best = next((s for s in slots if all(math.hypot(px - x, py - s) >= need for px, py in near)), None)
        if best is None:
            best = max(slots, key=lambda s: min(math.hypot(px - x, py - s) for px, py in near))
            over += 1
        off[i] = best
        placed.append((x, best))
    return off, over


# ---------------------------------------------------------------------------------------------------------------------
# the canonical box plot
# ---------------------------------------------------------------------------------------------------------------------
def box_stats(values, whis: str = "range") -> dict:
    """Quartiles (numpy linear, as S457.summary and S481), median and whisker ends. whis 'range': the smallest and
    largest value (the house rule); 'tukey': the most extreme values within 1.5 x IQR of the box (Figure 5 a,
    Supplementary 8 a and b today; Q1). Use the plate script's own summary when it has one."""
    import numpy as np
    v = [float(x) for x in values]
    q1, med, q3 = (float(x) for x in np.percentile(v, [25, 50, 75]))
    if whis == "range":
        lo, hi = min(v), max(v)
    elif whis == "tukey":
        iqr = q3 - q1
        lo = min(x for x in v if x >= q1 - 1.5 * iqr - 1e-9)
        hi = max(x for x in v if x <= q3 + 1.5 * iqr + 1e-9)
    else:
        raise ValueError(f"whis {whis!r}: 'range' or 'tukey'")
    return {"q1": q1, "median": med, "q3": q3, "whisker_low": lo, "whisker_high": hi, "n": len(v), "whis": whis}


def _seg(ax, horiz, a, b, at, **kw):
    """A line from value a to value b at cross position `at` (horizontal box: along x at y=at)."""
    if horiz:
        return ax.plot([a, b], [at, at], **kw)[0]
    return ax.plot([at, at], [a, b], **kw)[0]


def _cross(ax, horiz, v, at, half, **kw):
    """A line across the box at value v, from at-half to at+half."""
    if horiz:
        return ax.plot([v, v], [at - half, at + half], **kw)[0]
    return ax.plot([at - half, at + half], [v, v], **kw)[0]


def boxplot(ax, pos: float, values=None, stats: dict | None = None, *, orient: str = "h", slot: float = 1.0,
            dot_colour: str | None = None, dot_marker: str = "o", dot_mm: float | None = None,
            dot_style: dict | None = None, whis: str = "range", dots: bool = True, zorder: float = 2.0) -> dict:
    """One box at cross position `pos` (a row's y for orient 'h', a column's x for 'v').

    The house box: no fill; a 0.5 pt black outline; a 1.0 pt black median; 0.5 pt black whiskers to the ends in
    `stats` (or computed by `whis`), each with a cap 5/12 of the box thickness; the values as dots under the lines,
    placed apart (swarm) across a band 0.67 of the slot, grey when they carry no category, else the category's colour
    and shape. No mean, no interval, no fliers (every value is a dot). A box whose quartiles are equal is drawn as its
    median line, as long as the dot band and 0.5 mm more on each side (Figure 5 a), so it is not read as one more dot;
    its whiskers still show. Fewer than SMALL_N values: no box (use strip() and summary_tick()).

    slot: the distance between neighbouring boxes, in data units across. Returns the drawn artists and the numbers
    drawn (for the plate's read-back)."""
    horiz = orient == "h"
    if stats is None:
        if values is None:
            raise ValueError("boxplot needs values or stats")
        stats = box_stats(values, whis)
    if values is not None and len(values) < SMALL_N:
        raise ValueError(f"{len(values)} values: under {SMALL_N}, draw strip() and summary_tick(), not a box")
    mx, my = mm_per_unit(ax)
    along_mm, across_mm = (mx, my) if horiz else (my, mx)
    slot_mm = slot * across_mm
    half_box = BOX_FRAC * slot / 2
    half_band_mm = BAND_FRAC * slot_mm / 2
    cap_half = CAP_FRAC * (2 * half_box) / 2
    q1, med, q3 = stats["q1"], stats["median"], stats["q3"]
    lo, hi = stats["whisker_low"], stats["whisker_high"]
    art = {}
    if dots and values is not None:
        dmm = dot_mm if dot_mm is not None else (DOT_MM if len(values) > 30 else DOT_SPARSE_MM)
        off, over = swarm([v * along_mm for v in values], half=max(0.0, half_band_mm - dmm / 2), pitch=max(
            DOT_PITCH_MM, dmm + 0.05) if dmm > DOT_MM else DOT_PITCH_MM, dot=dmm)
        cross = [pos + o / across_mm for o in off]
        st = {"ls": "none", "marker": dot_marker, "ms": dmm * MARKER_SCALE.get(dot_marker, 1.0) / MM_PT,
              "mfc": dot_colour or GREY["dot"], "mec": "none", "mew": 0, "zorder": zorder, "clip_on": False}
        if dot_style:
            st.update(dot_style)
        xs, ys = (list(values), cross) if horiz else (cross, list(values))
        art["dots"] = ax.plot(xs, ys, **st)[0]
        art["overlapping"] = over
    line = {"color": BLACK, "solid_capstyle": "butt", "clip_on": False}
    collapsed = abs(q3 - q1) < 1e-12
    if not collapsed:
        if horiz:
            xs_ = [q1, q3, q3, q1, q1]
            ys_ = [pos - half_box, pos - half_box, pos + half_box, pos + half_box, pos - half_box]
        else:
            xs_ = [pos - half_box, pos + half_box, pos + half_box, pos - half_box, pos - half_box]
            ys_ = [q1, q1, q3, q3, q1]
        art["box"] = ax.plot(xs_, ys_, lw=LW["box"], solid_joinstyle="miter", zorder=zorder + 3, **line)[0]
    if hi > q3:
        art["whisker_high"] = _seg(ax, horiz, q3, hi, pos, lw=LW["whisker"], zorder=zorder + 3, **line)
    if lo < q1:
        art["whisker_low"] = _seg(ax, horiz, lo, q1, pos, lw=LW["whisker"], zorder=zorder + 3, **line)
    art["cap_low"] = _cross(ax, horiz, lo, pos, cap_half, lw=LW["whisker"], zorder=zorder + 3, **line)
    art["cap_high"] = _cross(ax, horiz, hi, pos, cap_half, lw=LW["whisker"], zorder=zorder + 3, **line)
    half_med = (half_band_mm + 0.5) / across_mm if collapsed else half_box
    art["median"] = _cross(ax, horiz, med, pos, half_med, lw=LW["median"], zorder=zorder + 4, **line)
    art["drawn"] = dict(stats)
    art["drawn"]["collapsed"] = collapsed
    return art


# ---------------------------------------------------------------------------------------------------------------------
# strip, summary tick, estimate, bar
# ---------------------------------------------------------------------------------------------------------------------
def strip(ax, pos: float, values, *, orient: str = "h", slot: float = 1.0, colour: str | None = None,
          marker_: str = "o", size_mm: float = MARK_MM, open_: bool = False, edge: str | None = None,
          zorder: float = 3.0) -> dict:
    """One row (or column) of marks at their values, placed apart across a band 0.67 of the slot (swarm, never
    random jitter, never transparency). A categorical mark is MARK_MM, coloured by its kind, with a 0.3 pt white edge
    so touching marks stay apart (Figure 5 e); open_=True draws it white with a 0.5 pt edge in the colour."""
    horiz = orient == "h"
    mx, my = mm_per_unit(ax)
    along_mm, across_mm = (mx, my) if horiz else (my, mx)
    half_band_mm = BAND_FRAC * slot * across_mm / 2
    off, over = swarm([v * along_mm for v in values], half=max(0.0, half_band_mm - size_mm / 2),
                      pitch=size_mm + 0.05, dot=size_mm)
    cross = [pos + o / across_mm for o in off]
    c = colour or GREY["dot"]
    ms = size_mm * MARKER_SCALE.get(marker_, 1.0) / MM_PT
    st = ({"mfc": WHITE, "mec": edge or c, "mew": 0.5} if open_ else {"mfc": c, "mec": edge or WHITE, "mew": 0.3})
    xs, ys = (list(values), cross) if horiz else (cross, list(values))
    ln = ax.plot(xs, ys, ls="none", marker=marker_, ms=ms, zorder=zorder, clip_on=False, **st)[0]
    return {"marks": ln, "overlapping": over}


def summary_tick(ax, pos: float, value: float, *, orient: str = "h", slot: float = 1.0):
    """A small-n summary (n < SMALL_N): a 1.0 pt black tick as long as a box is thick. The legend says whether it is
    the median or the mean."""
    half = BOX_FRAC * slot / 2
    return _cross(ax, orient == "h", value, pos, half, color=BLACK, lw=LW["median"], solid_capstyle="butt",
                  zorder=6, clip_on=False)


def estimate(ax, pos: float, value: float, lo: float | None = None, hi: float | None = None, *, orient: str = "h",
             marker_: str = "o", colour: str = BLACK, size_mm: float = ESTIMATE_MM, zorder: float = 6.0) -> dict:
    """A point estimate (a rate, a mean, a net difference) with its interval: a black dot 1.5 mm and a 0.9 pt black
    line, no caps (Figure 2 a, Figure 4 a). Use marker_ 'D' where the panel's own data marks are circles (Figure 6 d).
    Never drawn on a box plot."""
    horiz = orient == "h"
    art = {}
    if lo is not None and hi is not None:
        art["interval"] = _seg(ax, horiz, lo, hi, pos, color=colour, lw=LW["interval"], solid_capstyle="butt",
                               zorder=zorder, clip_on=False)
    xs, ys = ([value], [pos]) if horiz else ([pos], [value])
    art["mark"] = ax.plot(xs, ys, ls="none", marker=marker_, ms=size_mm * MARKER_SCALE.get(marker_, 1.0) / MM_PT,
                          mfc=colour, mec="none", mew=0, zorder=zorder + 1, clip_on=False)[0]
    return art


def bar(ax, pos: float, segments, colours, *, orient: str = "h", slot: float = 1.0, start: float = 0.0,
        labels=None, patterns=None, edges=None, zorder: float = 2.0) -> dict:
    """A bar of one or more segments laid end to end from `start`: no outline, no gap, BAR_FRAC of the row thick.
    labels: the text inside each segment (None for none), black or white ink by contrast (ink_on). patterns: names in
    PATTERN (or S447 pattern codes) for outcome bars, drawn by pattern(). Set the axes' limits first. edges: per segment an edge colour (only 'both failed', white, gets GREY['line'])."""
    horiz = orient == "h"
    th = BAR_FRAC * slot
    x = start
    rects, texts = [], []
    for k, (w, c) in enumerate(zip(segments, colours)):
        ec = (edges[k] if edges else None) or "none"
        kw = dict(color=c, edgecolor=ec, linewidth=LW["box"] if ec != "none" else 0, zorder=zorder)
        r = ax.barh(pos, w, left=x, height=th, **kw) if horiz else ax.bar(pos, w, bottom=x, width=th, **kw)
        if patterns and patterns[k] and w > 0:
            x0d, x1d, y0d, y1d = ((x, x + w, pos - th / 2, pos + th / 2) if horiz
                                  else (pos - th / 2, pos + th / 2, x, x + w))
            pattern(ax, (x0d, y0d, x1d, y1d), patterns[k], c, zorder=zorder + 0.5)
        rects.append(r)
        if labels and labels[k] is not None and w > 0:
            cx, cy = (x + w / 2, pos) if horiz else (pos, x + w / 2)
            texts.append(ax.text(cx, cy, labels[k], ha="center", va="center", color=ink_on(c), fontsize=PT,
                                 zorder=zorder + 1))
        x += w
    return {"rects": rects, "texts": texts}


def reference_line(ax, value: float, *, orient: str = "v", dashed: bool = False, **kw):
    """A zero line or a threshold: black, 0.5 pt, solid; dashed (DASH) when it crosses the data it refers to."""
    st = {"color": BLACK, "lw": LW["reference"], "zorder": 1}
    if dashed:
        st["dashes"] = DASH
    st.update(kw)
    return ax.axvline(value, **st) if orient == "v" else ax.axhline(value, **st)


def _s447():
    """S447's pattern drawing (pattern_marks, its dot and ring sizes, ink_on), imported from the repository's scripts."""
    import sys
    p = str(REPO / "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True              # never write a .pyc into the repository's scripts/
    try:
        import S447_fig6_panels as S447
    finally:
        sys.dont_write_bytecode = keep
    return S447


def _pattern_on(fig, rect_mm, name, fill, to_xy, plot, zorder):
    S447 = _s447()
    code = PATTERN.get(name, name)
    if not code:
        return []
    ink = ink_on(fill)
    lines, dots, rings = S447.pattern_marks(rect_mm, code)
    out = []
    for pts in lines:
        xs, ys = to_xy(list(pts))
        out.append(plot(xs, ys, color=ink, lw=LW["hatch"], solid_capstyle="butt", solid_joinstyle="miter",
                        zorder=zorder))
    for pts, filled, dmm in ((dots, True, S447.DOT_PATTERN_MM), (rings, False, S447.RING_PATTERN_MM)):
        if pts:
            xs, ys = to_xy(list(pts))
            out.append(plot(xs, ys, ls="none", marker="o", ms=dmm / MM_PT, mfc=ink if filled else "none",
                            mec="none" if filled else ink, mew=0 if filled else LW["hatch"], zorder=zorder))
    return out


def pattern(ax, rect_data, name, fill, zorder=2.5):
    """A fill pattern (PATTERN name or S447 code) inside rect_data (x0, y0, x1, y1 in ax's data units, limits already
    set), as lines and dots in black or white by contrast with fill (S447.draw_pattern's way)."""
    import numpy as np
    fig = ax.figure
    W, H = fig._hs_mm
    dpi = fig.dpi
    (ax0, ay0), (ax1, ay1) = ax.transData.transform([(rect_data[0], rect_data[1]), (rect_data[2], rect_data[3])])
    xs_mm = sorted([ax0 / dpi * 25.4, ax1 / dpi * 25.4])
    ys_mm = sorted([H - ay0 / dpi * 25.4, H - ay1 / dpi * 25.4])
    ins = LW["box"] * MM_PT                     # inside the segment's edge, as S481 draws it
    rect_mm = (xs_mm[0] + ins, ys_mm[0] + ins, xs_mm[1] - ins, ys_mm[1] - ins)
    inv = ax.transData.inverted()

    def to_xy(pts):
        d = inv.transform(np.array([(px / 25.4 * dpi, (H - py) / 25.4 * dpi) for px, py in pts]))
        return list(d[:, 0]), list(d[:, 1])

    def plot(xs, ys, **kw):
        return ax.plot(xs, ys, clip_on=False, **kw)[0]
    return _pattern_on(fig, rect_mm, name, fill, to_xy, plot, zorder)


def pattern_mm(fig, rect_mm, name, fill, zorder=3):
    """The same pattern inside a box given in page mm (a key's swatch)."""
    from matplotlib.lines import Line2D
    W, H = fig._hs_mm

    def to_xy(pts):
        return [px / W for px, _ in pts], [1 - py / H for _, py in pts]

    def plot(xs, ys, **kw):
        return fig.add_artist(Line2D(xs, ys, transform=fig.transFigure, **kw))
    return _pattern_on(fig, rect_mm, name, fill, to_xy, plot, zorder)


# ---------------------------------------------------------------------------------------------------------------------
# the key
# ---------------------------------------------------------------------------------------------------------------------
def _text_width_mm(s: str) -> float:
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    return TextToPath().get_text_width_height_descent(s, FontProperties(family=FONT, size=PT),
                                                      ismath=False)[0] * MM_PT


def _glyph_w(kind: str) -> float:
    return {"swatch": SWATCH_MM[0], "mark": KEY_MARK_MM, "open": KEY_MARK_MM, "line": 4.0, "dash": 4.0,
            "estimate": 3.2, "outline": SWATCH_MM[0]}[kind]


def key(fig, items, *, centre_x: float, y: float, max_width: float | None = None, gap: float = 2.4,
        glyph_gap: float = 0.8, line_pitch: float = 3.7, title: str | None = None):
    """A key, centred on centre_x (mm), its first baseline at y (mm), above the panel it explains (Valerio, 28 Oct,
    Figure 5 d and e: centred). items: (kind, style, text) with kind
      'swatch'  style = fill colour (a bar or tile category), or (fill, pattern)
      'outline' style = edge colour (an outlined cell, Figure 3 c's significant cells)
      'mark'    style = (colour, marker) filled, KEY_MARK_MM
      'open'    style = (colour, marker) open
      'line'    style = (colour, width)
      'dash'    style = (colour, width) dashed
      'estimate' style = None: the black estimate dot on its interval
    Only what a colour, mark or line stands for (D147): never the parts of a box plot. Lines wrap at max_width and
    each line is centred. title: words before the first item ('Draws passed:'), kept on the first line. Returns the
    lines' (x0, x1, y) in mm."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    W, H = fig._hs_mm
    widths = [_glyph_w(k) + glyph_gap + _text_width_mm(t) for k, _, t in items]
    lines, cur, cur_w = [], [], (_text_width_mm(title) + gap if title else 0.0)
    for it, w_ in zip(items, widths):
        add = w_ if not cur else gap + w_
        if cur and max_width is not None and cur_w + add > max_width:
            lines.append((cur, cur_w))
            cur, cur_w = [it], w_
        else:
            cur.append(it)
            cur_w += add
    lines.append((cur, cur_w))
    out = []

    def fx(x):
        return x / W

    def fy(yy):
        return 1 - yy / H
    for li, (its, tot) in enumerate(lines):
        yy = y + li * line_pitch
        x = centre_x - tot / 2
        x_start = x
        if li == 0 and title:
            text_mm(fig, x, yy, title, ha="left")
            x += _text_width_mm(title) + gap
        ym = yy - 0.35 * PT * MM_PT          # the glyphs' centre, at the text's x-height middle
        for kind, style, text in its:
            gw = _glyph_w(kind)
            if kind == "swatch":
                fill, pat = (style if isinstance(style, tuple) else (style, None))
                fig.add_artist(Rectangle((fx(x), fy(ym + SWATCH_MM[1] / 2)), SWATCH_MM[0] / W, SWATCH_MM[1] / H,
                                         transform=fig.transFigure, facecolor=fill,
                                         edgecolor=GREY["line"] if fill == WHITE else "none",
                                         lw=LW["box"] if fill == WHITE else 0))
                if pat:
                    pattern_mm(fig, (x, ym - SWATCH_MM[1] / 2, x + SWATCH_MM[0], ym + SWATCH_MM[1] / 2), pat, fill)
            elif kind == "outline":
                fig.add_artist(Rectangle((fx(x), fy(ym + SWATCH_MM[1] / 2)), SWATCH_MM[0] / W, SWATCH_MM[1] / H,
                                         transform=fig.transFigure, facecolor="none", edgecolor=style,
                                         lw=LW["median"]))
            elif kind in ("mark", "open"):
                c, mk = style
                st = ({"markerfacecolor": WHITE, "markeredgecolor": c, "markeredgewidth": 0.5} if kind == "open"
                      else {"markerfacecolor": c, "markeredgecolor": "none", "markeredgewidth": 0})
                fig.add_artist(Line2D([fx(x + gw / 2)], [fy(ym)], transform=fig.transFigure, ls="none", marker=mk,
                                      markersize=KEY_MARK_MM * MARKER_SCALE.get(mk, 1.0) / MM_PT, **st))
            elif kind in ("line", "dash"):
                c, w_ = style
                kw = {"dashes": DASH} if kind == "dash" else {}
                fig.add_artist(Line2D([fx(x), fx(x + gw)], [fy(ym)] * 2, transform=fig.transFigure, color=c, lw=w_,
                                      solid_capstyle="butt", **kw))
            elif kind == "estimate":
                fig.add_artist(Line2D([fx(x), fx(x + gw)], [fy(ym)] * 2, transform=fig.transFigure, color=BLACK,
                                      lw=LW["interval"], solid_capstyle="butt"))
                fig.add_artist(Line2D([fx(x + gw / 2)], [fy(ym)], transform=fig.transFigure, ls="none", marker="o",
                                      markersize=ESTIMATE_MM / MM_PT, markerfacecolor=BLACK, markeredgewidth=0))
            x += gw + glyph_gap
            text_mm(fig, x, yy, text, ha="left")
            x += _text_width_mm(text) + gap
        out.append((x_start, x - gap, yy))
    return out


def colourbar(fig, x: float, y: float, w: float, lo: float, hi: float, ticks, labels, label: str,
              h: float = 2.4) -> None:
    """A continuous colour key: a horizontal cividis bar w by h mm, top left at (x, y), above the panel and centred
    over it by the caller (Figure 3 c, Supplementary 4); tick labels under it, its label to the right. Vertical bars
    at the panel's side are not used."""
    import numpy as np
    W, H = fig._hs_mm
    ax = fig.add_axes((x / W, 1 - (y + h) / H, w / W, h / H))
    from matplotlib import colormaps
    ax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=colormaps[FLOCK["colour"]["continuous"]],
              extent=(lo, hi, 0, 1), interpolation="nearest")
    ax.set_yticks([])
    ax.set_xticks(list(ticks))
    ax.set_xticklabels(list(labels))
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=2, width=LW["axis"], pad=1)
    text_mm(fig, x + w + 2.0, y + h * 0.8, label, ha="left")
    return ax


# ---------------------------------------------------------------------------------------------------------------------
# a plate's colours, checked before saving (the same palette S448 R5 holds a plate to)
# ---------------------------------------------------------------------------------------------------------------------
def allowed(hex_: str) -> bool:
    """True when hex_ is a lock colour, white, a grey (channels within FIGURE_LOCK grey_tol) or a cividis entry
    (within continuous_tol)."""
    h = hex_.upper()
    if h in _CAT or h in (WHITE, BLACK):
        return True
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    if max(r, g, b) - min(r, g, b) <= int(FLOCK["colour"]["grey_tol"]):
        return True
    from matplotlib import colormaps
    cm = colormaps[FLOCK["colour"]["continuous"]]
    tol = int(FLOCK["colour"]["continuous_tol"])
    for i in range(256):
        cr, cg, cb = (round(255 * v) for v in cm(i)[:3])
        if max(abs(cr - r), abs(cg - g), abs(cb - b)) <= tol:
            return True
    return False


def check_figure_colours(fig) -> list[str]:
    """Every face and edge colour drawn on fig that allowed() refuses (an alpha-blended colour counts as drawn)."""
    from matplotlib.colors import to_hex, to_rgba
    bad = set()

    def chk(c):
        if c is None or (isinstance(c, str) and c == "none"):
            return
        try:
            rgba = to_rgba(c)
        except (ValueError, TypeError):
            return
        if rgba[3] == 0:
            return
        if rgba[3] < 1:
            bad.add(f"{to_hex(rgba[:3]).upper()} at alpha {rgba[3]:.2f} (no transparency)")
            return
        h = to_hex(rgba[:3]).upper()
        if not allowed(h):
            bad.add(h)
    for a in fig.findobj():
        for getter in ("get_color", "get_facecolor", "get_edgecolor", "get_markerfacecolor", "get_markeredgecolor"):
            f = getattr(a, getter, None)
            if f is None:
                continue
            try:
                c = f()
            except Exception:
                continue
            if hasattr(c, "shape") and len(getattr(c, "shape", ())) == 2:
                for row in c:
                    chk(tuple(row))
            else:
                chk(c)
    return sorted(bad)


def save(fig, folder: Path, stem: str, title: str) -> dict:
    """PDF and SVG with no date or creator, and the PNG as the PDF rasterised at 600 dpi by MuPDF (S457.finish_plate's
    way, so S448 R7 holds them equal). Refuses colours allowed() refuses."""
    import matplotlib.pyplot as plt
    from matplotlib.text import Text
    bad = check_figure_colours(fig)
    if bad:
        raise SystemExit(f"house_style.save: colours outside the house palette: {bad}")
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    folder.mkdir(parents=True, exist_ok=True)
    paths = {k: folder / f"{stem}.{k}" for k in ("pdf", "svg", "png")}
    fig.savefig(paths["pdf"], facecolor=WHITE, metadata={"Title": title, "Author": None, "Subject": None,
                                                         "Keywords": None, "Creator": None, "Producer": None,
                                                         "CreationDate": None, "ModDate": None})
    fig.savefig(paths["svg"], facecolor=WHITE, metadata={"Title": title, "Date": None, "Creator": None})
    plt.close(fig)
    import fitz
    pix = fitz.open(paths["pdf"])[0].get_pixmap(dpi=600, alpha=False)
    pix.set_dpi(600, 600)
    pix.save(paths["png"])
    return paths


# ---------------------------------------------------------------------------------------------------------------------
# the continuous colour key as vector shapes. colourbar() above draws with imshow, which FIGURE_LOCK [colour]
# vector_only refuses (build_order.md F11), so a plate's key comes from here.
# ---------------------------------------------------------------------------------------------------------------------
def vector_colourbar(fig, y: float, w: float, lo: float, hi: float, ticks, labels, label: str | None = None, *,
                     centre_x: float | None = None, x_left: float | None = None, h: float = 2.4, n: int = 128):
    """A horizontal cividis key w by h mm, its top edge at y mm, drawn as n filled rectangles with no edge, so the
    PDF and the SVG hold no image. lo takes the dark end and hi the light end (cividis_value). Returns the bar's axes.

    Exactly one of centre_x and x_left places it; anything else raises ValueError. centre_x centres the bar and its
    label together on that x. x_left puts the bar's left edge at that x, for a key that cannot sit centred (Figure 6 a).
    label, when given, starts 2 mm right of the bar with its baseline 0.8 h below the bar's top; with no label nothing
    is written beside the bar, for a plate that places its own words (Figure 2 d). ticks and labels go under the bar,
    and empty lists give no tick. n is the number of rectangles. Each rectangle but the last runs one step past its
    right end, under the next one, so no background shows through between neighbours when the PDF is rasterised."""
    if (centre_x is None) == (x_left is None):
        raise ValueError("vector_colourbar: give exactly one of centre_x and x_left")
    from matplotlib.patches import Rectangle
    W, H = fig._hs_mm
    if x_left is not None:
        x = x_left
    else:
        x = centre_x - (w + (2.0 + _text_width_mm(label) if label else 0.0)) / 2
    ax = fig.add_axes((x / W, 1 - (y + h) / H, w / W, h / H))
    ax.set_facecolor("none")
    step = (hi - lo) / n
    for i in range(n):
        v = lo + i * step
        ax.add_patch(Rectangle((v, 0), step * (2 if i < n - 1 else 1), 1, facecolor=cividis_value(v + step / 2, lo, hi),
                               edgecolor="none", lw=0))
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks(list(ticks))
    ax.set_xticklabels(list(labels))
    for s in ("left", "right", "top", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", length=2, width=LW["axis"], pad=1)
    if label:
        text_mm(fig, x + w + 2.0, y + h * 0.8, label, ha="left")
    return ax
