#!/usr/bin/env python3
"""S481 - Figure 6 of D138 and its six Supplementary figures, drawn from the S2 records S447 mirrors.

WHY. D138 (experiments/README.md, Valerio, 25 October): Figure 6 is plate trial 3 (a H-1, b K-1, c X-1, d B-1) and the
ten other chosen panels go to the Supplementary Information (G-4, C-2, B-1b, K-5, X-4, B-4, X-3, C-3, X-2, H-2; B-1b
and its Supplementary Figure 22 dropped by D222, 3 November, its values rows of sheet Supplementary Fig. 15f not drawn). The
panels were drafted as scratch scripts outside the repository (findings/recompute/fig6_options_2026-10-25/ keeps their
images); this script is their committed form (README.md:13-27: no number enters the paper unless a script in scripts/
regenerates it from a raw file in one command). Valerio, 25 October: "Start the build of the figures".

WHAT IS READ. The mirrored S2 sinks only, through S447's own loader (S447.load_mirror, keep_design: the D100, D112 Q15
O-a and D116 design, S477's lung_9 re-score applied inside load_mirror), each answers.json checked by S447 against
records_manifest.json; families (S478.FAM), tiers and datasets (the ground truth's `complexity`, as S479), failure kinds
(S447.fail_kind) and labels (S447) are those scripts' own. Nothing here re-implements them. No model call.
Since D155 (Valerio, 26 October: "it should be all reproducible") every record is read from a frozen copy, never from a
live clone, a scratch folder or the gitignored findings/runs/: S447 reads the tar s2_after_s4_20261105.tar (the copy
records_manifest.json was mirrored from, after S4's reruns; s4_gate() also reads the copy before them,
s2_length_retries_20261021.tar) through scripts/fig_repro.frozen(), which checks the tar against
findings/recompute/frozen_inputs/SHA256SUMS (it is kept outside git, in ~/Mentori_scratch_keep/frozen_2026-10-26 or
the folder env FROZEN_TARS names, and goes to the Zenodo deposit), and S445's anchor files in the committed
findings/recompute/fig6_inputs/. The other inputs are committed files: records_manifest.json, S477's re-score, S478's and
S479's numbers, S447's fig6_numbers.json, the ground truth, LOCK.toml, FIGURE_LOCK.toml, and the drafts' anchors in
findings/recompute/fig6_options_2026-10-25/ (B_numbers.json, G4_numbers.json, C_numbers.json, inputs/coverage_check.json).
Each anchor has its tracked script beside it (draw_B.py, draw_G4.py with draw_G.py, draw_C.py, inputs/coverage_check.py).

ONE COMMAND PER PLATE, from the repository root, rebuilding it from the frozen inputs (S494 calls these):
  Figure 6                          uv run --frozen python scripts/S481_fig6_d138.py figure
  Supplementary Figures 14, 16 and 21 to 24    uv run --frozen python scripts/S481_fig6_d138.py supplementary
  all seven                         uv run --frozen python scripts/S481_fig6_d138.py all
Add --out <folder outside the repository> to write the plates under <folder>/fig6/ and
<folder>/supp_fig<N>_fig6_<slug>/ instead, for comparing with the committed plates: every file but the provenance file
is byte-equal to the committed one, and the provenance file is too when the code and inputs are the committed ones.

REPRODUCIBLE (D155). Before anything is written, each plate's inputs (file name and sha256, plate_inputs()) are held to
the ones its committed provenance file recorded: one that differs, or one recorded on one side only (committed and
not read now, or read now and not committed; D160 (6)), stops the run (exit 2) unless named with
--accept-input <name> (a deliberate change of that input). Nothing written carries a time: the PDF and SVG are saved
with no date or creator (checked by fig_repro.check_pdf_deterministic and check_svg_deterministic), the workbook goes
through fig_repro.deterministic_xlsx (S447.write_source_data), the stamp's time is the records' newest answers.json
time as the manifest records it, printed in Europe/Amsterdam whatever the building computer's zone (S447.iso_local),
and the provenance file records the code (this script's sha256 and that of S447, S457, S478, S479), the package
versions and every input by sha256, with no build time, git HEAD or working-tree state. Two builds of the eight plates
are byte-equal in all 64 files, and so are builds under PYTHONHASHSEED 0 to 5 (26 October).

REPRODUCE FIRST (README.md:75-79): stops (exit 2) before drawing unless S447.reproduce() passes; the copy before S4
(s2_length_retries_20261021.tar) gives the known 2,420 attempts and 1,660 passes and S525's comparison with the copy
after S4 holds (s4_gate(): the 2,255 attempts off S502's list unchanged, the 165 on it run again); the design gives
2,420 attempts and 1,692 passes (S478.WANT); and every number S478 and S479 committed
(findings/recompute/S478_fig6_thinking_gap.json, S479_fig6_by_tier.json) comes out equal from this script's own rows,
on the manifest, ground truth and lung_9 re-score those files name.

THE CONSISTENCY RULES OF THE BUILD (D138; the drafts differed, 25 October):
  - Gemini's lowest thinking setting is labelled "low" everywhere (vlabel()); LOCK.toml [gemini] thinking_off sends
    gemini-3-flash-preview "minimal" and gemini-2.5-pro 128 tokens, so it is not "off".
  - One family palette and one marker per family (FCOL, FMARK: K-1's).
  - One set of outcome names (OUTCOMES, X-1's): passed, wrong values, no result, tool or call failure, other. A panel
    that shows length stops on their own (C-2) names its remaining group the same and says in its legend that length
    stops are shown apart (outcome5()).
  - One order of the variants (FF21): D.blocks, block 1 Gemini and block 2 open-weight, within a block pooled free-form
    pass rate high to low, then overall passes, then D.VARS order (block_rule()); D.block_order is its flat list. Panels
    H1, H2, K5, X2, X4, G4 and B4 draw it. FF32: Figure 6c stacks the two model groups, and the dataset split is on X-2.
  - One house style (scripts/house_style.py, D147, STYLE.md): boxes, keys, estimates, zero lines, bar thickness and
    colours come from there; the words come from scripts/figure_names.py.

COMMANDS, from the repository root (uv run only):

  figure        uv run --frozen python scripts/S481_fig6_d138.py figure [--final]
                Figure 6 into findings/figures_provisional/fig6/ (S447.OUT): "Figure 6 (provisional, <n> of <N>)"
                .pdf/.svg/.png, "Source Data Fig. 6 ...".xlsx (one sheet per panel), its caption, figure6_numbers.json
                (the sheets and the "printed" map S448 R8 (6) reads), figure6_provenance.json, legend_draft.md; files
                of an earlier data state ("Figure 6*", "Source Data Fig. 6*") are deleted first. Then S448 on the folder.
  supplementary uv run --frozen python scripts/S481_fig6_d138.py supplementary [--final]
                The six Supplementary figures, Supplementary Figures 14, 16 and 21 to 24 (D257's numbers; 22 under FF3 a dropped,
                D222), each in its own
                folder findings/figures_provisional/supp_fig<N>_fig6_<slug>/, named by FIGURE_LOCK.toml [files]
                supplementary_name, with "Supplementary Figure <N> data ...".xlsx and its numbers and provenance files
                (S448 side_name()). Then S448 --supplementary on each folder.
  panel         uv run --frozen python scripts/S481_fig6_d138.py panel <ID> --dir <new dir outside the repository>
                One panel alone on a 183 mm page as "Supplementary Figure 99", then S448 --supplementary on it: for
                checking a panel while it is built.
  all           figure, then supplementary.

Every plate: one matplotlib figure (S457.plate_rc, then house_style.rc), each panel drawn by its own function into a Frame, the panel's
slot on the page in millimetres, at the panel's own size (no scaling); 2.5 mm between panels; [page] width_double_mm
wide, at most height_max_mm high. Each panel writes the numbers it plots into its sheet, registers every number it
prints (Sheet.num: the SVG group id of the text, its sheet row and format), and registers read-back checks
(Sheet.check: values taken from the drawn artists, compared with the workbook as written; a difference keeps nothing).
Before saving, hs.check_plate_kinds and hs.check_figure_colours hold the plate's colours to the house table. Then S18 to
S24 end in S457.finish_plate (build_order F4); a plate holding Figure 6a ends in finish_plate_rotated below, which is
S457.finish_plate's steps with rotated text compared by its outline (draw_plate says why).
"""
import argparse
import hashlib
import json
import platform
import re
import shutil
import statistics as stats
import subprocess
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True           # importing scripts/ must not write __pycache__ into the repository
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import S478_fig6_thinking_gap as S478  # noqa: E402  (loads S447 itself; the same module object is used here)
import S479_fig6_by_tier as S479  # noqa: E402
import S457_fig2_panels as S457  # noqa: E402
import house_style as hs  # noqa: E402  (one box, key, colour and line style for every plate)
import figure_names  # noqa: E402  (one name for each thing printed on a plate or in a legend)

S447 = S478.S447
import logging  # noqa: E402
logging.getLogger("fontTools").setLevel(logging.ERROR)
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.text import Text  # noqa: E402

SCRIPT = "scripts/S481_fig6_d138.py"
OUT_MAIN = S447.OUT
SUPP_DIR = ROOT / "findings" / "figures_provisional"
J478 = ROOT / "findings/recompute/S478_fig6_thinking_gap.json"
J479 = ROOT / "findings/recompute/S479_fig6_by_tier.json"
FAM, GT, MANIFEST, WANT = S478.FAM, S478.GT, S478.MANIFEST, S478.WANT
TIERS = ["simple", "medium", "complex"]
TIERS_ALL = S479.TIERS                   # simple, medium, complex, all
FAMS = ["free-form", "introspection", "structured"]
DATASET = {"airway": "RNA-seq", "lung_cancer": "survival"}
DSETS = ["RNA-seq", "survival"]
DHEAD = {"RNA-seq": "airway RNA-seq", "survival": "NCCTG lung survival"}   # D139 Q4: one name for each dataset
PAIRS = {"gemini-3-flash": ["gemini-3-flash-preview+off", "gemini-3-flash-preview+default"],
         "gemini-2.5-pro": ["gemini-2.5-pro+off", "gemini-2.5-pro+default"],
         "gpt-oss:20b": ["gpt-oss-20b+low", "gpt-oss-20b+medium", "gpt-oss-20b+high"]}
COST = ["latency_s", "n_calls", "generator_calls", "llm_calls_d115", "prompt_tokens", "output_tokens",
        "thinking_tokens"]
BOOT_N, BOOT_SEED = 10000, 20261013      # coverage_check's resampling of the 20 operations (B-1, B-1b, B-4)

# ---- the lock's values (FIGURE_LOCK.toml through S447, which reads it; none written here) -------------------------
PT = S447.PT_TEXT
PT_LETTER = S447.PT_LETTER
LW = S447.LINE_MIN_PT
MMPT = S447.MM_PER_PT                    # mm per point
OK = S447.OKABE
PAGE_W = S447.FIG_W_MM
PAGE_H_MAX = S447.FIG_H_MAX_MM
H_ROOM = S447.H_ROOM_MM
GAP_MM = 2.5                             # between panels (plate trial 3, D138)
POS_TOL = 1e-9

# ---- the build's consistency rules (D138) ----------------------------------------------------------------------------
FCOL = {"free-form": OK["blue"], "introspection": OK["reddish purple"], "structured": OK["orange"]}   # K-1's
FMARK = {"free-form": "o", "introspection": "s", "structured": "D"}  # shape as well as colour (journal: patterns)
OUTCOMES = ["passed", "wrong values", "no result", "tool or call failure, other"]                  # X-1's names
# D153 Q3 (Valerio, 26 Oct; audit of 25 Oct F3): the outcomes take hues no family uses (FCOL holds blue, reddish purple
# and orange), so one hue never means a family and an outcome on one plate. Of the Okabe-Ito set, sky blue, vermillion
# and yellow were free; each goes where its neighbours in the bar (passed, wrong values, no result, tool or call
# failure) differ most under simulated deuteranopia, protanopia and tritanopia (bluish green and sky blue, the closest
# pair, never touch). Black ink on each (S447.ink_on): yellow 15.9, sky blue 9.1, vermillion 5.4, all at least 4.5.
OCOL = {"passed": OK["bluish green"], "wrong values": OK["yellow"], "no result": OK["sky blue"],
        "tool or call failure, other": OK["vermillion"], "length stop": OK["black"]}
OPAT = {"passed": "", "wrong values": "z", "no result": ".", "tool or call failure, other": "\\", "length stop": "-"}
GREY_NOTE = S447.GREY_NOTE
TXT_GREY = hs.GREY["text"]
DOT_GREY = S457.DOT_GREY


def vlabel(v):
    """A variant's label on every plate: S447.short_variant(), with Gemini's lowest thinking setting called "low"
    (D138: LOCK.toml [gemini] thinking_off is the lowest each model allows, "minimal" or 128 tokens, not off)."""
    lab = S447.short_variant(v)
    if S447.VMODEL[v].startswith("gemini") and S447.VTHINK[v] == "off":
        lab = lab.replace("(off)", "(low)")
    return lab


def setting_label(v):
    """The thinking setting alone, with the same rule as vlabel()."""
    t = S447.VTHINK[v]
    return "low" if S447.VMODEL[v].startswith("gemini") and t == "off" else t


def is_gemini(v):
    return S447.VMODEL[v].startswith("gemini")


def block_rule(variants, free_form, overall):
    """The one order of variants (FF21): block 1 Gemini, block 2 open-weight; within a block free_form[v] high to low,
    then overall[v] high to low, then their order in `variants`."""
    key = lambda v: (-free_form[v], -overall[v], variants.index(v))
    return [(figure_names.GEMINI, sorted((v for v in variants if is_gemini(v)), key=key)),
            (figure_names.OPEN_WEIGHT, sorted((v for v in variants if not is_gemini(v)), key=key))]


def outcome4(fail_kind, has_results, passed):
    """X-1's four outcomes. S447.fail_kind() unchanged; its "result wrong or missing" split on whether the record's
    actual_results is empty (D138: X-1's split taken up)."""
    if passed:
        return "passed"
    if fail_kind == "result wrong or missing":
        return "wrong values" if has_results else "no result"
    if fail_kind == "code raised or timed out":
        return "no result"
    return "tool or call failure, other"


def outcome5(fail_kind, has_results, passed):
    """outcome4() with length stops apart (C-2): "tool or call failure, other" then holds no length stop."""
    if not passed and fail_kind == "length stop":
        return "length stop"
    return outcome4(fail_kind, has_results, passed)


# =====================================================================================================================
# Data
# =====================================================================================================================
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stop(msg):
    print(f"NOT REPRODUCED: {msg}", file=sys.stderr)
    sys.exit(2)


def tok_sum(calls, key):
    xs = [c.get(key) for c in calls if c.get("role") == "generator"]
    xs = [x for x in xs if isinstance(x, (int, float))]
    return sum(xs) if xs else None


def count(rows, *keys):
    """{key tuple: [passes, attempts]}."""
    t = defaultdict(lambda: [0, 0])
    for r in rows:
        k = tuple(r[x] for x in keys)
        t[k][0] += r["passed"]
        t[k][1] += 1
    return t


J525 = ROOT / "findings/recompute/S525_fig6_s4_check.json"


def s4_gate():
    """REPRODUCE FIRST across S4 (D201 Q2, fig6 spec A8). The copy before S4 (S447.FROZEN_S2_BEFORE_S4, read with the
    records_manifest.json and S477 file of S525.OLD_AT) must give the known number S525.OLD_WANT, 2,420 attempts and
    1,660 passes; then S525's gates (1) to (4) between it and the copy S447.FROZEN_S2 draws: the same keys, the 2,255
    keys off S502's list equal in passed, fail_kind, exec_outcome and actual_results with their ctx_uid kept, and each
    of the 165 listed keys run again. The new copy's totals must be WANT, and the counts and passes per variant, old
    and new, those S525 committed (S525_fig6_s4_check.json). When the old tar is not in the tar folder, only the new
    copy is held to S525's committed new passes per variant, and the record says the old copy was not read."""
    import fig_repro
    import S525_fig6_s4_check as S525
    j525 = json.loads(J525.read_text())
    ls = S525.listed_keys()
    new, nprov = S525.load_copy(S447, S447.FROZEN_S2)
    if S447.FROZEN_S2 == S525.OLD_SET:
        stop(f"S447.FROZEN_S2 is still the copy before S4 ({S525.OLD_SET})")
    try:
        fig_repro.frozen(S525.OLD_SET, S525.OLD_SET)
        have_old = True
    except fig_repro.FrozenInputError as e:
        have_old, why = False, str(e)
    pv_new = S525.per_variant(new)
    got = (len(new), sum(r["passed"] for r in new.values()))
    if got != tuple(WANT):
        stop(f"S4: the copy {S447.FROZEN_S2} gives {got}, not WANT {tuple(WANT)}")
    if pv_new != j525["per_variant"]["new"] or nprov["tar_sha256"] != j525["provenance"]["new"]["tar_sha256"]:
        stop(f"S4: the copy {S447.FROZEN_S2} is not the one {J525.relative_to(ROOT)} checked")
    rec = {"new_copy": S447.FROZEN_S2, "new_tar_sha256": nprov["tar_sha256"], "new_totals": list(got),
           "S525_json_sha256": sha(J525)}
    if not have_old:
        print(f"S4: the copy before S4 is not readable ({why}); the new copy is held to S525's committed passes only")
        return {**rec, "old_copy": None, "old_copy_not_read": why}
    old, oprov = S525.load_copy(S447, S525.OLD_SET, S525.git_show(S525.OLD_AT, S525.MANIFEST_REL),
                            S525.git_show(S525.OLD_AT, S525.Q4_REL))
    bad, counts = S525.compare(old, new, ls)
    if bad:
        stop("S4: " + "; ".join(bad[:4]))
    if counts != j525["counts"] or S525.per_variant(old) != j525["per_variant"]["old"]:
        stop(f"S4: the comparison differs from {J525.relative_to(ROOT)}")
    print(f"reproduced S4: the copy before S4 gives {S525.OLD_WANT}; {counts['outside_the_list_equal']:,} attempts off "
          f"the list equal, {counts['listed_rerun']} listed attempts run again; the copy after S4 gives {got}")
    return {**rec, "old_copy": S525.OLD_SET, "old_tar_sha256": oprov["tar_sha256"], "old_totals": list(S525.OLD_WANT),
            "counts": counts}


class Data:
    """Every attempt of the design as one row, and the tables the panels share. Built once per run."""

    def __init__(self):
        self.reproduced_s445 = S447.reproduce()          # exit 2 before anything is written
        self.reproduced_s4 = s4_gate()                    # the copy before S4, then the one S4 left; exit 2 on a miss
        gt = json.loads(GT.read_text())["datasets"]
        self.tier_of = {k: o["complexity"] for d in gt.values() for k, o in d["operations"].items()}
        dset = {k: DATASET[dn] for dn, d in gt.items() for k in d["operations"]}
        atts, flags, inputs, notes = S447.load_mirror()
        kept, vs, total, left = S447.keep_design(atts)
        got = (len(kept), sum(bool(a["passed"]) for a in kept))
        if got != WANT or total != WANT[0]:
            stop(f"the design gives {got} (total {total}), Figure {S447.FIG_N} has {WANT}")
        if {a["op_id"] for a in kept} - set(self.tier_of):
            stop("operations without a tier")
        self.inputs, self.notes, self.design = inputs, notes, (vs, total, left)
        self.inputs[str(S447.LOCK.relative_to(ROOT))] = sha(S447.LOCK)
        rows, seen = [], set()
        for a in kept:
            v, s = S447.variant_of(a["run_id"]), S447.config_of(a["run_id"])
            if a["dataset"] not in DATASET or dset[a["op_id"]] != DATASET[a["dataset"]]:
                stop(f"the dataset of {a['answer_key']} disagrees with the ground truth")
            if (v, s, a["op_id"]) in seen:
                stop(f"two attempts for {(v, s, a['op_id'])}")
            seen.add((v, s, a["op_id"]))
            calls = a.get("calls") or []
            passed = int(bool(a["passed"]))
            fk = "" if passed else S447.fail_kind(a, flags.get(a.get("ctx_uid"), set()))
            has = bool(a.get("actual_results"))
            lc = S447.llm_calls(a)
            rows.append({
                "variant_id": v, "variant": vlabel(v), "model": S447.VMODEL[v], "setting": setting_label(v),
                "strategy": s, "strategy_label": S447.SLAB[s], "family": FAM[s], "op_id": a["op_id"],
                "dataset": dset[a["op_id"]], "tier": self.tier_of[a["op_id"]], "passed": passed, "fail_kind": fk,
                "has_results": has, "exec_outcome": a.get("exec_outcome"),
                "outcome": outcome4(fk, has, passed), "outcome5": outcome5(fk, has, passed),
                "latency_s": a.get("latency_s"), "n_calls": a.get("n_calls"),
                "generator_calls": sum(1 for c in calls if c.get("role") == "generator"),
                "llm_calls_d115": lc, "prompt_tokens": tok_sum(calls, "prompt_tokens"),
                "output_tokens": tok_sum(calls, "output_tokens"), "thinking_tokens": tok_sum(calls, "thinking_tokens")})
        self.rows = rows
        self.VARS = list(vs)
        self.STRATS = [s for s, _ in S447.STRATEGIES]
        self.SLAB = dict(S447.STRATEGIES)
        self.OPS = sorted({r["op_id"] for r in rows})
        self.ops_of_tier = {t: sorted(o for o in self.OPS if self.tier_of[o] == t) for t in TIERS}
        self.dataset_of = {o: dset[o] for o in self.OPS}
        self.idx = {(r["variant_id"], r["strategy"], r["op_id"]): r for r in rows}
        for v in self.VARS:
            for s in self.STRATS:
                if sum(1 for o in self.OPS if (v, s, o) in self.idx) != S447.PER_CELL:
                    stop(f"{v} {s} does not hold {S447.PER_CELL} attempts")
        self.reproduced = self._reproduce_s478_s479(got)
        self.summary = self._summary()
        pv = self.summary["per_variant"]
        self.blocks = block_rule(self.VARS, {v: Fraction(*pv[v]["by_family"]["free-form"]) for v in self.VARS},
                                 {v: pv[v]["overall"][0] for v in self.VARS})
        self.block_of = {v: b for b, vv in self.blocks for v in vv}
        self.block_order = [v for _, vv in self.blocks for v in vv]
        self.cov = self._coverage()

    # ---- reproduce first ----------------------------------------------------------------------------------------
    def _reproduce_s478_s479(self, got):
        rows = self.rows
        j478, j479 = json.loads(J478.read_text()), json.loads(J479.read_text())
        for j, name in ((j478, "S478"), (j479, "S479")):
            if j["provenance"]["manifest_sha256"] != sha(MANIFEST):
                stop(f"{name}'s JSON was written on another manifest")
            if j["provenance"]["ground_truth_sha256"] != sha(GT):
                stop(f"{name}'s JSON was written on another ground truth")
            if j["provenance"]["q4_lung9_rescore"] != self.notes.get("q4_lung9_rescore"):
                stop(f"{name}'s JSON had another lung_9 re-score")
            if j["reproduced"] != {"attempts": got[0], "passes": got[1]}:
                stop(f"{name}'s JSON reproduced another total")
        vft, vfa = count(rows, "variant_id", "family", "tier"), count(rows, "variant_id", "family")
        cell = lambda v, f, k: list(vft[(v, f, k)]) if k != "all" else list(vfa[(v, f)])
        rate = lambda c: 100 * c[0] / c[1]
        s478 = {}
        for v in S478.PAIRS:
            s478[v] = {k: {"passes": {f: cell(v, f, k) for f in ["structured", "introspection", "free-form"]},
                           "structured_minus_free_form": round(rate(cell(v, "structured", k))
                                                              - rate(cell(v, "free-form", k)), 1),
                           "introspection_minus_free_form": round(rate(cell(v, "introspection", k))
                                                                 - rate(cell(v, "free-form", k)), 1)}
                       for k in TIERS_ALL}
            s478[v]["structured_fail_kinds"] = dict(Counter(r["fail_kind"] for r in rows if r["variant_id"] == v
                                                            and r["family"] == "structured"
                                                            and not r["passed"]).most_common())
        if s478 != j478["variants"]:
            stop(f"S478's table differs for {[v for v in s478 if s478[v] != j478['variants'].get(v)]}")
        pct = lambda c: round(100 * c[0] / c[1], 1)
        st, ft, at = count(rows, "strategy", "tier"), count(rows, "family", "tier"), count(rows, "tier")
        sa, fa = count(rows, "strategy"), count(rows, "family")

        def g(group, k):
            if group == "all":
                c = [sum(r["passed"] for r in rows), len(rows)] if k == "all" else list(at[(k,)])
            elif group in FAMS:
                c = list(fa[(group,)]) if k == "all" else list(ft[(group, k)])
            else:
                c = list(sa[(group,)]) if k == "all" else list(st[(group, k)])
            return {"passes": c, "rate": pct(c)}
        groups = ["all", "free-form", "introspection", "structured"] + self.STRATS
        by_group = {grp: {k: g(grp, k) for k in TIERS_ALL} for grp in groups}
        po = count(rows, "op_id")
        order = list(dict.fromkeys(r["op_id"] for r in rows))
        per_task = [{"task": o, "tier": self.tier_of[o], "passes": list(po[(o,)]), "rate": pct(po[(o,)])}
                    for o in sorted(order, key=lambda o: (TIERS_ALL.index(self.tier_of[o]),
                                                          -po[(o,)][0] / po[(o,)][1]))]
        gap = {v: {k: round(pct(vft[(v, "structured", k)]) - pct(vft[(v, "free-form", k)]), 1) for k in TIERS}
               for v in self.VARS}
        for name, mine in (("by_group", by_group), ("per_task", per_task),
                           ("structured_minus_free_form_per_variant", gap)):
            if mine != j479[name]:
                stop(f"S479's {name} differs")
        self.s478 = s478
        print(f"reproduced: {got[0]:,} attempts, {got[1]:,} passes; S478's table ({len(s478)} variants) and S479's "
              f"tables (by_group {len(by_group)}, per_task {len(per_task)}, gap {len(gap)} variants) equal")
        return {"attempts": got[0], "passes": got[1], "S478_equal": True, "S479_equal": True,
                "S478_json_sha256": sha(J478), "S479_json_sha256": sha(J479), "S445": self.reproduced_s445,
                "S4": self.reproduced_s4}

    # ---- the tables the drafts read as summary.json and coverage_check.json -----------------------------------------
    def _summary(self):
        rows, VARS = self.rows, self.VARS
        vs_, va = count(rows, "variant_id", "strategy"), count(rows, "variant_id")
        vtier, vfa = count(rows, "variant_id", "tier"), count(rows, "variant_id", "family")
        vft = count(rows, "variant_id", "family", "tier")
        per_variant = {v: {"label": vlabel(v), "model": S447.VMODEL[v], "thinking": setting_label(v),
                           "overall": list(va[(v,)]),
                           "by_strategy": {s: list(vs_[(v, s)]) for s in self.STRATS},
                           "by_family": {f: list(vfa[(v, f)]) for f in FAMS},
                           "by_tier": {k: list(vtier[(v, k)]) for k in TIERS},
                           "by_tier_family": {k: {f: list(vft[(v, f, k)]) for f in FAMS} for k in TIERS}}
                       for v in VARS}
        return {"variants_in_order": VARS, "strategies_in_order": self.STRATS, "strategy_labels": self.SLAB,
                "family_of_strategy": dict(FAM), "per_variant": per_variant}

    def _coverage(self):
        """coverage_check.py's tables (the paired best-of-3 contrasts, cost medians, per dataset), from these rows."""
        rows, VARS, OPS, idx = self.rows, self.VARS, self.OPS, self.idx
        num = lambda x: float(x) if x is not None else None
        out = {}
        pairs = {}
        for base, arms in (("free_form", ["free_form_n3_best", "free_form_n3_combined"]),
                           ("coder_v2_n1", ["coder_v2_n1_cell3_best", "coder_v2_n1_cell3_combined", "coder_v2_n3"])):
            for arm in arms:
                rescued = lost = both = neither = 0
                per_op = defaultdict(list)
                ratio = {"latency_s": [], "generator_calls": [], "output_tokens": []}
                sums = {k: [0.0, 0.0] for k in ratio}
                per_var = {}
                for v in VARS:
                    rv = lv = 0
                    for o in OPS:
                        a, b = idx[(v, base, o)], idx[(v, arm, o)]
                        rescued += (not a["passed"]) and b["passed"]
                        lost += a["passed"] and not b["passed"]
                        both += a["passed"] and b["passed"]
                        neither += (not a["passed"]) and not b["passed"]
                        rv += (not a["passed"]) and b["passed"]
                        lv += a["passed"] and not b["passed"]
                        per_op[o].append(b["passed"] - a["passed"])
                        for k in ratio:
                            x, y = num(a[k]), num(b[k])
                            if x is not None and y is not None:
                                sums[k][0] += x
                                sums[k][1] += y
                                if x > 0:
                                    ratio[k].append(y / x)
                    per_var[v] = {"rescued": rv, "lost": lv}
                d_op = {o: 100 * sum(x) / len(x) for o, x in per_op.items()}
                pairs[f"{arm} vs {base}"] = {
                    "n_pairs": len(VARS) * len(OPS), "rescued": rescued, "lost": lost, "both_pass": both,
                    "both_fail": neither, "net_points": round(100 * (rescued - lost) / (len(VARS) * len(OPS)), 1),
                    "interval_95_ops": boot_interval(d_op),
                    "cost_multiple_of_sums": {k: round(sums[k][1] / sums[k][0], 2) for k in sums if sums[k][0]},
                    "cost_multiple_median_paired": {k: round(stats.median(ratio[k]), 2) for k in ratio if ratio[k]},
                    "per_variant": per_var}
        out["gap_best_of_3"] = pairs

        def med(xs):
            xs = [num(x) for x in xs if x is not None]
            return round(stats.median(xs), 1) if xs else None
        out["cost_by_strategy"] = {s: {"pass": [sum(r["passed"] for r in rr), len(rr)],
                                       "median_latency_s": med([r["latency_s"] for r in rr]),
                                       "median_generator_calls": med([r["generator_calls"] for r in rr]),
                                       "median_output_tokens": med([r["output_tokens"] for r in rr])}
                                   for s in self.STRATS for rr in [[r for r in rows if r["strategy"] == s]]}
        out["cost_by_variant"] = {v: {"pass": [sum(r["passed"] for r in rr), len(rr)],
                                      "median_latency_s": med([r["latency_s"] for r in rr]),
                                      "median_output_tokens": med([r["output_tokens"] for r in rr]),
                                      "median_thinking_tokens": med([r["thinking_tokens"] for r in rr]),
                                      "thinking_rows": sum(1 for r in rr if r["thinking_tokens"] is not None)}
                                  for v in VARS for rr in [[r for r in rows if r["variant_id"] == v]]}
        ds = defaultdict(lambda: [0, 0])
        for r in rows:
            for key in [(r["dataset"], r["family"]), (r["dataset"], "all")]:
                ds[key][0] += r["passed"]
                ds[key][1] += 1
        out["by_dataset_family"] = {f"{a} | {b}": v for (a, b), v in sorted(ds.items())}
        tdf = count(rows, "dataset", "tier", "family")
        out["by_dataset_tier_family"] = {" | ".join(k): list(v) for k, v in sorted(tdf.items())}
        split = defaultdict(Counter)
        for r in rows:
            if not r["passed"]:
                split[r["strategy"]][r["outcome"]] += 1
                split[r["family"]][r["outcome"]] += 1
        out["failure_split"] = {s: dict(c.most_common()) for s, c in split.items()}
        return out


def boot_interval(diffs_by_op, n=BOOT_N, seed=BOOT_SEED):
    """coverage_check.py's 95% percentile interval of the mean over operations, resampling the 20 operations with
    random.Random(seed) (the draft's own generator, so the drafts' intervals reproduce)."""
    import random
    rng = random.Random(seed)
    ops = list(diffs_by_op)
    ms = []
    for _ in range(n):
        s = [diffs_by_op[rng.choice(ops)] for _ in ops]
        ms.append(sum(s) / len(s))
    ms.sort()
    return round(ms[int(0.025 * n)], 1), round(ms[int(0.975 * n) - 1], 1)


# =====================================================================================================================
# Page, frames, sheets
# =====================================================================================================================
_TW = {}


def tw(s, bold=False, size=None):
    """Width of a text in mm at the plate's font (one renderer, cached)."""
    size = size or PT
    if "r" not in _TW:
        _TW["f"] = plt.figure()
        _TW["r"] = _TW["f"].canvas.get_renderer()
    t = _TW["f"].text(0, 0, s, fontsize=size, fontweight="bold" if bold else "normal")
    w = t.get_window_extent(_TW["r"]).width / _TW["f"].dpi * 25.4
    t.remove()
    return w


class Page:
    def __init__(self, W, H):
        plt.rcParams.update(S457.plate_rc(salt="S481"))
        plt.rcParams.update(hs.rc("S481"))
        self.W, self.H = W, H
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
        self.fig._hs_mm = (W, H)             # house_style places keys and boxes in page mm


class Frame:
    """A panel's slot on the page: (ox, oy) its top-left corner in page mm, (W, H) its size; every coordinate a
    panel passes is in mm from the slot's top-left corner, y downwards."""

    def __init__(self, page, ox, oy, W, H, letter):
        self.page, self.fig, self.ox, self.oy, self.W, self.H, self.letter_ch = page, page.fig, ox, oy, W, H, letter

    def fx(self, x):
        return (self.ox + x) / self.page.W

    def fy(self, y):
        return 1 - (self.oy + y) / self.page.H

    def axes(self, x, y, w, h, **kw):
        return self.fig.add_axes([self.fx(x), self.fy(y + h), w / self.page.W, h / self.page.H], **kw)

    def text(self, x, y, s, **kw):
        return self.fig.text(self.fx(x), self.fy(y), s, **kw)

    def line(self, xs, ys, **kw):
        ln = Line2D([self.fx(x) for x in xs], [self.fy(y) for y in ys], transform=self.fig.transFigure, **kw)
        self.fig.add_artist(ln)
        return ln

    def rect(self, x, y, w, h, **kw):
        r = Rectangle((self.fx(x), self.fy(y + h)), w / self.page.W, h / self.page.H, transform=self.fig.transFigure,
                      **kw)
        self.fig.add_artist(r)
        return r

    def letter(self, x=0.0, y=None):
        """The panel letter (FIGURE_LOCK.toml [type] panel_letter_*) at the slot's top-left; none on a one-panel
        figure."""
        if not self.letter_ch:
            return None
        return self.text(x, y if y is not None else PT_LETTER * MMPT, S447.LETTER_CASE(self.letter_ch),
                         fontsize=PT_LETTER, fontweight=S447.LETTER_WEIGHT, va="baseline", ha="left")


class Book:
    """The plate's data: one sheet per panel, the printed-number map, the read-back checks."""

    def __init__(self, prefix):
        self.prefix, self.sheets, self.printed, self.checks, self._k = prefix, {}, {}, [], 0

    def sheet(self, name):
        self.sheets[name] = Sheet(self, name)
        return self.sheets[name]

    def gid(self, artist):
        self._k += 1
        g = f"{self.prefix}num{self._k}"
        artist.set_gid(g)
        return g

    def fixed(self, artist, why):
        """A text holding a digit that is no number of the data (a "95%", a tier name with a count in a fixed
        sentence...): S448 R8 (6) accepts it as declared fixed."""
        self.printed[self.gid(artist)] = {"fixed": artist.get_text(), "why": why}

    def table(self):
        """(name, columns, rows) per sheet, columns in first-seen order, a missing cell None."""
        out = []
        for name, sh in self.sheets.items():
            cols = list(dict.fromkeys(c for r in sh.rows for c in r))
            out.append((name, cols, [[r.get(c) for c in cols] for r in sh.rows]))
        return out


class Sheet:
    def __init__(self, book, name):
        self.book, self.name, self.rows = book, name, []

    def add(self, **row):
        """One data row; returns its 0-based index (what a printed entry or a check names)."""
        self.rows.append(row)
        return len(self.rows) - 1

    def num(self, artist, row, fmt):
        """A number printed on the plate: the text of `artist` must equal `fmt` filled from this sheet's `row`
        (S448 R8 (6), half away from zero)."""
        want = S447.HALF_UP.format(fmt, **self.rows[row])
        if artist.get_text() != want:
            raise SystemExit(f"{self.name}: printed {artist.get_text()!r}, the format gives {want!r}")
        self.book.printed[self.book.gid(artist)] = {"sheet": self.name, "row": row, "format": fmt}

    def count(self, artist, where, fmt):
        """A number printed as a count of this sheet's rows matching `where` ("{count}")."""
        n = sum(1 for r in self.rows if all(r.get(k) == v for k, v in where.items()))
        want = fmt.format(count=n)
        if artist.get_text() != want:
            raise SystemExit(f"{self.name}: printed {artist.get_text()!r}, the count gives {want!r}")
        self.book.printed[self.book.gid(artist)] = {"sheet": self.name, "where": where, "format": fmt}

    def check(self, what, rows, col, got, tol=POS_TOL):
        """Read-back: `got` (values read from a drawn artist: get_xdata(), a bar's width...) must equal this sheet's
        column `col` at `rows`, as the workbook holds them after it is written."""
        self.book.checks.append((self.name, what, list(rows), col, [float(g) for g in got], tol))


# ---- house style helpers (style_1028/style/STYLE.md) -----------------------------------------------------------------
def hkey(F, items, centre_x, y, max_width=None, diamond=False):
    """house_style.key at frame mm (centre_x, y: the first line's baseline); returns the key's texts in item order.
    diamond: the 'estimate' glyph drawn as a black diamond (Supplementary Figure 15f's net, whose own data marks are circles)."""
    n0, a0 = len(F.fig.texts), len(F.fig.artists)
    if max_width is None:                    # one line: centred on centre_x, moved the least needed to stay inside
        wid = sum(hs._glyph_w(k) + 0.8 + hs._text_width_mm(t) for k, _, t in items) + 2.4 * (len(items) - 1)
        centre_x = min(max(centre_x, wid / 2 + 0.2), F.W - wid / 2 - 0.2)
    lines = hs.key(F.fig, items, centre_x=F.ox + centre_x, y=F.oy + y, max_width=max_width)
    if diamond:
        for a in F.fig.artists[a0:]:
            if isinstance(a, Line2D) and a.get_marker() == "o" and abs(a.get_markersize() - hs.ESTIMATE_MM / hs.MM_PT) < 1e-9:
                a.set_marker("D")
                a.set_markersize(hs.ESTIMATE_MM * hs.MARKER_SCALE["D"] / hs.MM_PT)
    for x0, x1, _ in lines:
        if x0 < F.ox - 0.01 or x1 > F.ox + F.W + 0.01:     # hs.key returns page mm
            raise SystemExit(f"key past its panel: {x0 - F.ox:.1f} to {x1 - F.ox:.1f} mm in a {F.W} mm slot")
    return F.fig.texts[n0:], lines


def _hbox(ax, pos, vals, *, colour, marker, dot_mm, slot, orient="v", zorder=2.0, spread=False):
    """The house box (no fill, 0.5 pt outline and whiskers with caps, 1.0 pt median, BOX_FRAC of the slot) over its
    values as dots placed apart across BAND_FRAC of the slot (house_style.swarm), dots under the lines. Quartiles and
    median by numpy's linear percentiles, whiskers to the range (house_style.box_stats, the rule S481 already
    used). Returns (stats, artists)."""
    mx, my = hs.mm_per_unit(ax)
    along, across = (my, mx) if orient == "v" else (mx, my)
    st = hs.box_stats(vals, "range")
    half = max(0.0, hs.BAND_FRAC * slot * across / 2 - dot_mm / 2)
    pitch = max(hs.DOT_PITCH_MM, dot_mm + 0.05) if dot_mm > hs.DOT_MM else hs.DOT_PITCH_MM
    if spread:                               # tied dots spread sideways as far as they need (draw_K.py's swarm)
        off, over = _K_swarm([v * along for v in vals], dot_mm), 0
    else:
        off, over = hs.swarm([v * along for v in vals], half=half, pitch=pitch, dot=dot_mm)
    cross = [pos + o / across for o in off]
    xs, ys = (cross, list(vals)) if orient == "v" else (list(vals), cross)
    dl = ax.plot(xs, ys, ls="none", marker=marker, ms=dot_mm * hs.MARKER_SCALE.get(marker, 1.0) / MMPT, mfc=colour,
                 mec="none", mew=0, zorder=zorder, clip_on=False)[0]
    art = hs.boxplot(ax, pos, values=None, stats=st, orient=orient, slot=slot, dots=False, zorder=zorder)
    art["dots"], art["overlapping"] = dl, over
    return st, art


def _hbox_read(art, orient="v"):
    """(q1, median, q3, low end, high end) read from the drawn box, median line and caps."""
    get = (lambda ln: ln.get_ydata()) if orient == "v" else (lambda ln: ln.get_xdata())
    med = get(art["median"])[0]
    q1, q3 = (get(art["box"])[0], get(art["box"])[2]) if "box" in art else (med, med)
    return q1, med, q3, get(art["cap_low"])[0], get(art["cap_high"])[0]


# =====================================================================================================================
# Panels (each: SIZE_<ID> = (width, height) mm; draw_<ID>(D, F, S) -> {"legend": str, ...})
# =====================================================================================================================
# ---- panels H ----------------------------------------------------------------------------------------------------------------
# ---- family H: the strategy by variant heat map (H1, Figure 6a) and the operation by variant heat map (H2,
# Supplementary). Ported from the D138 drafts fig6_alt/H_heatmap/draw_H_plate.py (draw_plate) and draw_H.py
# (draw_alt2); every number from D.rows, every draft assertion kept as a reproduce gate.
_H_M = 1.5                               # the drafts' left margin (mm)
_H_COL_ROT = 45.0                        # column labels' angle (H1)
_H_LW_RULE = max(0.5, LW)                # the drafts' axis and rule width (S447's: at least 0.5 pt)


def _H_line_mm():
    return PT * MMPT * 1.2


def _H_cmap():
    from matplotlib import colormaps
    return colormaps[S447.CMAP_NAME]     # FIGURE_LOCK.toml [colour] continuous (cividis)


def _H_bin_mid(cmap, rgba):
    """Read-back of a cell's fill: the middle (in %) of the colour map entry the drawn colour is, or -1e9 when the
    colour is no entry of the map (so the check fails)."""
    lut = cmap(np.arange(cmap.N))
    hit = np.flatnonzero(np.all(np.abs(lut - np.asarray(rgba, dtype=float)) < 1e-12, axis=1))
    return (hit[0] + 0.5) * 100.0 / cmap.N if len(hit) else -1e9


def _H_bin_tol(cmap, want):
    """Half an entry of the map, as S.check's relative tolerance at the workbook value `want`."""
    return (50.0 / cmap.N + 1e-9) / max(1.0, abs(float(want)))


def _H_signed(x):
    """The drafts' signed(): rounded half away from zero, '+' before a positive value, U+2212 before a negative one,
    none on a value that rounds to 0. Returns (sign, format): the sign is a workbook column (gap_sign), so S448 R8
    checks the printed sign against the workbook as well as the size (gap_size_points, |x|); a value that rounds to 0
    prints its size alone and its format names no sign field."""
    q = S447.half_up(x, 0)
    if q == "0":
        return "", "{gap_size_points:.0f}"
    return ("−" if x < 0 else "+"), "{gap_sign}{gap_size_points:.0f}"


def _H_inside(F, artists, axes_list):
    """Every text and axes of the panel inside its slot (so nothing reaches a neighbouring panel)."""
    F.fig.canvas.draw()
    rend = F.fig.canvas.get_renderer()
    x0, x1 = F.ox, F.ox + F.W
    y0, y1 = F.oy, F.oy + F.H
    bad = []
    for a in list(artists) + list(axes_list):
        bb = a.get_window_extent(rend) if isinstance(a, Text) else a.get_tightbbox(rend)
        bx0, bx1 = bb.x0 / F.fig.dpi * 25.4, bb.x1 / F.fig.dpi * 25.4
        by0, by1 = F.page.H - bb.y1 / F.fig.dpi * 25.4, F.page.H - bb.y0 / F.fig.dpi * 25.4
        if bx0 < x0 - 0.01 or bx1 > x1 + 0.01 or by0 < y0 - 0.01 or by1 > y1 + 0.01:
            bad.append(f"{a.get_text() if isinstance(a, Text) else 'axes'!r} x {bx0 - x0:.2f}-{bx1 - x0:.2f} "
                       f"y {by0 - y0:.2f}-{by1 - y0:.2f}")
    if bad:
        raise SystemExit(f"panel past its {F.W} x {F.H} mm slot: {bad[:4]}")


def _H_data(D):
    """The counts both panels draw, with the drafts' gates: draw_H.py (every cell against summary.json, 20 attempts
    a cell, WANT's passes (1,692 after S4; 1,660 before), family counts against summary.json), draw_H_plate.py (80 structured and 60 free-form
    attempts a variant), and gates against committed files: S479's per-variant gap in each tier (all 11 variants),
    S478's overall gap (its 7 variants) and S479's per-operation passes and tiers."""
    rows = D.rows
    if (len(rows), sum(r["passed"] for r in rows)) != tuple(WANT):
        raise SystemExit(f"NOT REPRODUCED: H: {len(rows)} attempts, {sum(r['passed'] for r in rows)} passes; "
                         f"the drafts had {WANT[0]:,} and {WANT[1]:,}")
    cell, opfam, oppool = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for r in rows:
        if FAM[r["strategy"]] != r["family"]:
            raise SystemExit(f"NOT REPRODUCED: H: {r['strategy']} is not in family {r['family']}")
        for d, k in ((cell, (r["variant_id"], r["strategy"])), (opfam, (r["variant_id"], r["family"], r["op_id"])),
                     (oppool, r["op_id"])):
            d[k][0] += r["passed"]
            d[k][1] += 1
    for v in D.VARS:
        for s in D.STRATS:
            if cell[(v, s)] != D.summary["per_variant"][v]["by_strategy"][s] or cell[(v, s)][1] != 20:
                raise SystemExit(f"NOT REPRODUCED: H: cell {v} {s} is {cell[(v, s)]}, summary "
                                 f"{D.summary['per_variant'][v]['by_strategy'][s]} (20 attempts wanted)")
    if sum(c[0] for c in cell.values()) != WANT[1]:
        raise SystemExit(f"NOT REPRODUCED: H: the cells do not hold {WANT[1]:,} passes")
    nstr = {f: sum(1 for s in D.STRATS if FAM[s] == f) for f in FAMS}
    fam_pa = {}
    for v in D.VARS:
        for f in FAMS:
            k = sum(cell[(v, s)][0] for s in D.STRATS if FAM[s] == f)
            n = sum(cell[(v, s)][1] for s in D.STRATS if FAM[s] == f)
            if [k, n] != D.summary["per_variant"][v]["by_family"][f] or n != 20 * nstr[f]:
                raise SystemExit(f"NOT REPRODUCED: H: family {v} {f} is {[k, n]}, summary "
                                 f"{D.summary['per_variant'][v]['by_family'][f]}")
            fam_pa[(v, f)] = (k, n)
            for o in D.OPS:
                if opfam[(v, f, o)][1] != nstr[f]:
                    raise SystemExit(f"NOT REPRODUCED: H: {v} {f} {o} holds {opfam[(v, f, o)][1]} attempts, the "
                                     f"family {nstr[f]} strategies")
        if fam_pa[(v, "structured")][1] != 80 or fam_pa[(v, "free-form")][1] != 60:
            raise SystemExit(f"NOT REPRODUCED: H: {v} has {fam_pa[(v, 'structured')][1]} structured and "
                             f"{fam_pa[(v, 'free-form')][1]} free-form attempts, the drafts 80 and 60")
    rate = {k: Fraction(100 * c[0], c[1]) for k, c in cell.items()}
    fam_rate = {k: Fraction(100 * a, n) for k, (a, n) in fam_pa.items()}
    gap = {v: fam_rate[(v, "structured")] - fam_rate[(v, "free-form")] for v in D.VARS}
    j479 = json.loads(J479.read_text())
    for v in D.VARS:
        # the per-tier gap from this panel's per-operation counts (opfam, summed over each tier's operations), in
        # S479's own expression (each rate rounded to 1 decimal, then the difference), against S479's committed
        # table for all 11 variants; draw_H_plate.py's exact-gap assertion is not kept: after the 80 and 60 attempts
        # gate above it compared the gap with itself
        for t_ in TIERS:
            kn = {f: [sum(opfam[(v, f, o)][i] for o in D.OPS if D.tier_of[o] == t_) for i in (0, 1)]
                  for f in ("structured", "free-form")}
            mine = round(round(100 * kn["structured"][0] / kn["structured"][1], 1)
                         - round(100 * kn["free-form"][0] / kn["free-form"][1], 1), 1)
            if mine != j479["structured_minus_free_form_per_variant"][v][t_]:
                raise SystemExit(f"NOT REPRODUCED: H: the {t_} gap of {v} is {mine}, S479's committed table "
                                 f"{j479['structured_minus_free_form_per_variant'][v][t_]}")
        # S478's own expression (rates as floats, Python's round to 1 decimal), against its committed table
        s478_way = round(100 * fam_pa[(v, "structured")][0] / 80 - 100 * fam_pa[(v, "free-form")][0] / 60, 1)
        if v in D.s478 and s478_way != D.s478[v]["all"]["structured_minus_free_form"]:
            raise SystemExit(f"NOT REPRODUCED: H: the gap of {v} is {s478_way}, S478's committed table "
                             f"{D.s478[v]['all']['structured_minus_free_form']}")
    task = {t["task"]: t for t in j479["per_task"]}
    for o in D.OPS:
        if list(oppool[o]) != task[o]["passes"] or D.tier_of[o] != task[o]["tier"]:
            raise SystemExit(f"NOT REPRODUCED: H: operation {o} is {oppool[o]} ({D.tier_of[o]}), S479's committed "
                             f"per_task {task[o]['passes']} ({task[o]['tier']})")
    # operations (H2): tier, then the pass rate over all variants and strategies high to low, then the operation id
    ops = sorted(D.OPS, key=lambda o: (TIERS.index(D.tier_of[o]), -Fraction(*oppool[o]), o))
    return {"cell": cell, "opfam": opfam, "oppool": oppool, "nstr": nstr, "fam_pa": fam_pa, "rate": rate,
            "fam_rate": fam_rate, "gap": gap, "ops": ops}


def _H_opcode(D, o):
    return ("A" if D.dataset_of[o] == "RNA-seq" else "L") + o.split("_")[1]


def _H_colorbar_h(F, cx, label, w=30.0, h=2.4, x_left=None):
    """The house colour key (hs.vector_colourbar, no image in the PDF or the SVG): a horizontal cividis bar w by h mm,
    its top edge so the label's baseline sits on the panel letter's line, ticks under it. Centred, bar and label
    together, on cx (frame mm); or, with x_left (frame mm), its left edge there, for Figure 6a, whose band above the
    columns holds the block labels."""
    y = PT_LETTER * MMPT - h * 0.8
    ticks = [0, 25, 50, 75, 100]
    place = {"centre_x": F.ox + cx} if x_left is None else {"x_left": F.ox + x_left}
    return hs.vector_colourbar(F.fig, F.oy + y, w, 0, 100, ticks, [str(t) for t in ticks], label, **place)


# =====================================================================================================================
# H1: Figure 6a. 11 strategy rows grouped by family, a bold pooled row closing each family, a gap row (pooled
# structured minus pooled free-form, exact, rounded: D138 Q1); 11 variant columns in two blocks, D.block_order (FF21)
SIZE_H1 = (119.3, 81.73)
_H_BLOCK_GAP = 1.2                       # mm between the columns of the two blocks


def draw_H1(D, F, S):
    H = _H_data(D)
    cmap = _H_cmap()
    cols, RH, GAPR = D.block_order, 2.8, 1.0          # rows 2.8 mm (3.0 before 3 Nov): room for the key centred above the block names
    fam_rows = [(f, [s for s in D.STRATS if FAM[s] == f]) for f in FAMS]
    lab_pool = {f: f"{f}, pooled" for f in FAMS}
    gap_lab = "structured − free-form"                 # Valerio, 3 Nov: no unit in the row label (the legend gives it)
    LA = max([tw(D.SLAB[s]) for s in D.STRATS] + [tw(x, True) for x in lab_pool.values()] + [tw(gap_lab)]) + 1.2
    # house: the columns fill the slot (no colour bar at the side); the two blocks stand _H_BLOCK_GAP apart
    CW = (F.W - _H_M - LA - 0.5 - _H_BLOCK_GAP) / len(cols)
    n_first = len(D.blocks[0][1])
    column_x = [j * CW + (_H_BLOCK_GAP if j >= n_first else 0.0) for j in range(len(cols))]
    column_of = {round(x, 6): j + 1 for j, x in enumerate(column_x)}      # a drawn x back to its column (1-based)
    spans = [(column_x[cols.index(vv[0])], column_x[cols.index(vv[-1])] + CW) for _, vv in D.blocks]
    yrows, y = [], 0.0
    for f, ss in fam_rows:
        for s in ss:
            yrows.append(("s", f, s, y))
            y += RH
        yrows.append(("p", f, None, y))
        y += RH
        y += GAPR
    yrows.append(("g", None, None, y))
    y += RH
    gh = y
    top = 10.6                                       # the colour key above the block names, on the panel letter's line (3 Nov)
    labels = {v: vlabel(v) for v in cols}
    band = (max(tw(labels[v]) for v in cols) * np.sin(np.radians(_H_COL_ROT))
            + _H_line_mm() * np.cos(np.radians(_H_COL_ROT)) + 2.0)
    gw = len(cols) * CW + _H_BLOCK_GAP
    need_w = _H_M + LA + gw + 0.5
    need_h = top + gh + band + 1.0
    if need_w > F.W + 1e-6 or need_h > F.H + 1e-6:
        raise SystemExit(f"H1 needs {need_w:.2f} (before its key's labels) x {need_h:.2f} mm, its slot is "
                         f"{F.W} x {F.H}")
    F.letter()
    ax = F.axes(_H_M + LA, top, gw, gh)
    ax.set_xlim(0, gw)
    ax.set_ylim(gh, 0)
    ax.axis("off")
    ax.set_xticks([])                    # no tick labels on the hidden axes (finish_plate counts them)
    ax.set_yticks([])
    texts = []
    n_rect = 0
    for gi, (kind, f, s, y0) in enumerate(yrows):
        grid_row = gi + 1
        if kind == "g":
            label = gap_lab
        elif kind == "p":
            label = lab_pool[f]
        else:
            label = D.SLAB[s]
        lt = ax.text(-1.2, y0 + RH / 2, label, ha="right", va="center", fontweight="bold" if kind == "p" else "normal")
        texts.append(lt)
        first_row = None
        for j, v in enumerate(cols):
            x0 = column_x[j]
            if kind == "g":
                (ks, ns), (kf, nf) = H["fam_pa"][(v, "structured")], H["fam_pa"][(v, "free-form")]
                g = 100 * ks / ns - 100 * kf / nf
                sign, fmt = _H_signed(g)
                ri = S.add(part="structured minus free-form", grid_row=grid_row, grid_column=j + 1,
                           variant=labels[v], block=D.block_of[v], structured_passes=ks, structured_attempts=ns, free_form_passes=kf,
                           free_form_attempts=nf, gap_points=g, gap_sign=sign, gap_size_points=abs(g))
                t = ax.text(x0 + CW / 2, y0 + RH / 2, S447.HALF_UP.format(fmt, **S.rows[ri]), ha="center",
                            va="center", color="#000000")
                S.num(t, ri, fmt)
                # read-back: the text parsed as a signed number is the exact gap within half a point (so a wrong
                # sign on any gap of half a point or more fails), and the text sits in its cell's row and column
                back = float(t.get_text().replace("−", "-"))
                S.check(f"gap row text, {labels[v]}", [ri], "gap_points", [back],
                        tol=(0.5 + 1e-9) / max(1.0, abs(g)))
                S.check(f"gap row text column, {labels[v]}", [ri], "grid_column",
                        [column_of[round(t.get_position()[0] - CW / 2, 6)]])
                S.check(f"gap row text row, {labels[v]}", [ri], "grid_row",
                        [1 + [yy + RH / 2 for _, _, _, yy in yrows].index(t.get_position()[1])])
            else:
                if kind == "p":
                    k, n = H["fam_pa"][(v, f)]
                    ri = S.add(part="family pooled", grid_row=grid_row, grid_column=j + 1, variant=labels[v],
                               block=D.block_of[v], family=f, passes=k, attempts=n, pass_rate_pct=100 * k / n)
                else:
                    k, n = H["cell"][(v, s)]
                    ri = S.add(part="strategy", grid_row=grid_row, grid_column=j + 1, variant=labels[v],
                               block=D.block_of[v], strategy=D.SLAB[s], family=f, passes=k, attempts=n, pass_rate_pct=100 * k / n)
                val = S.rows[ri]["pass_rate_pct"]
                fc = cmap(val / 100)
                n_rect += 1
                rect = Rectangle((x0, y0), CW, RH, facecolor=fc, edgecolor="#FFFFFF", linewidth=0.6)
                rect.set_gid(f"{S.book.prefix}H1cell{n_rect}")
                ax.add_patch(rect)
                t = ax.text(x0 + CW / 2, y0 + RH / 2, S447.HALF_UP.format("{pass_rate_pct:.0f}", **S.rows[ri]),
                            ha="center", va="center", color=S447.ink_on(fc),
                            fontweight="bold" if kind == "p" else "normal")
                S.num(t, ri, "{pass_rate_pct:.0f}")
                S.book.printed[t.get_gid()]["inside"] = {"gid": rect.get_gid(), "path": 0}
                S.check(f"cell colour, {label}, {labels[v]}", [ri], "pass_rate_pct",
                        [_H_bin_mid(cmap, rect.get_facecolor())], tol=_H_bin_tol(cmap, val))
                S.check(f"cell column, {label}, {labels[v]}", [ri], "grid_column", [column_of[round(rect.get_x(), 6)]])
                S.check(f"cell row, {label}, {labels[v]}", [ri], "grid_row",
                        [1 + [yy for _, _, _, yy in yrows].index(rect.get_y())])
            texts.append(t)
            if first_row is None:
                first_row = ri
        if re.search(r"\d", label):
            S.num(lt, first_row, "{strategy}")
        if kind == "p":
            for a, b in spans:
                ax.plot([a, b], [y0, y0], color="#000000", lw=0.6, solid_capstyle="butt")
    gy = yrows[-1][3]
    for (name, _), (a, b) in zip(D.blocks, spans):
        ax.plot([a, b], [gy - 0.5, gy - 0.5], color="#000000", lw=_H_LW_RULE)
        # the block's name over its columns, a rule under the name (FF21): no digit, so no printed entry
        ax.plot([a, b], [-0.5, -0.5], color="#000000", lw=hs.LW["reference"], solid_capstyle="butt", clip_on=False)
        texts.append(ax.text((a + b) / 2, -1.2, name, ha="center", va="baseline"))
    gap_rows = {r["grid_column"]: i for i, r in enumerate(S.rows) if r["part"] == "structured minus free-form"}
    for j, v in enumerate(cols):
        t = ax.text(column_x[j] + CW / 2 + 0.6, gh + 1.2, labels[v], rotation=_H_COL_ROT, ha="right", va="top",
                    rotation_mode="anchor")
        S.num(t, gap_rows[j + 1], "{variant}")
        S.check(f"column label column, {labels[v]}", [gap_rows[j + 1]], "grid_column",
                [column_of[round(t.get_position()[0] - 0.6 - CW / 2, 6)]])
        texts.append(t)
    cax = _H_colorbar_h(F, _H_M + LA + gw / 2, "Pass rate (%)")   # Valerio, 3 Nov: centred over the heatmap
    _H_inside(F, texts, [ax, cax])
    # Valerio, 28 Oct (Figure 6 O2, accepted): the headline numbers as rows of this sheet, not drawn: one 'all variants
    # pooled' row per family and the pooled structured minus free-form gap, each summed from this sheet's own 'family
    # pooled' rows and held to S479's committed by_group
    j479 = json.loads(J479.read_text())
    pooled = {}
    for f in FAMS:
        fr = [r for r in S.rows if r["part"] == "family pooled" and r["family"] == f]
        k, n = sum(r["passes"] for r in fr), sum(r["attempts"] for r in fr)
        if len(fr) != len(cols) or [k, n] != j479["by_group"][f]["all"]["passes"]:
            raise SystemExit(f"NOT REPRODUCED: H1 pooled {f} {k} of {n} against S479's by_group "
                             f"{j479['by_group'][f]['all']['passes']}")
        pooled[f] = (k, n)
        S.add(part="all variants pooled", family=f, passes=k, attempts=n, pass_rate_pct=100 * k / n)
    (ks, ns), (kf, nf) = pooled["structured"], pooled["free-form"]
    g = 100 * ks / ns - 100 * kf / nf
    sign, _ = _H_signed(g)
    S.add(part="all variants pooled, structured minus free-form", structured_passes=ks, structured_attempts=ns,
          free_form_passes=kf, free_form_attempts=nf, gap_points=g, gap_sign=sign, gap_size_points=abs(g))
    n_ff = H["fam_pa"][(cols[0], "free-form")][1]
    n_in = H["fam_pa"][(cols[0], "introspection")][1]
    n_st = H["fam_pa"][(cols[0], "structured")][1]
    n_cell = H["cell"][(cols[0], D.STRATS[0])][1]
    # 8 Nov (Valerio, editor row 45): a panel with no derived statistics carries no "n ="; each count is said once,
    # in plain words, as part of what the cell shows. Strategies per family = the family's attempts / one cell's.
    k_ff, k_in, k_st = n_ff // n_cell, n_in // n_cell, n_st // n_cell
    return {"legend": (f"Pass rate of each model variant (column) under each prompting strategy (row): each cell is "
                       f"the percentage of its {n_cell} attempts, one per operation, that passed. Bold rows pool the "
                       f"strategies of each family ({k_ff} free-form, {k_in} introspection and {k_st} structured); bottom "
                       f"row, pooled structured minus pooled free-form (percentage points). "
                       f"Columns: {D.blocks[0][0]}, then {D.blocks[1][0]}, each ordered high to low by pooled free-form, "
                       f"then overall, pass rate. "
                       f"Gemini's lowest thinking setting is "
                       f"labelled low.")}


# =====================================================================================================================
# H2: Supplementary. Per variant (rows, D.block_order) and operation (columns, by tier then its
# own pass rate over its 121 attempts), the share of a family's strategies that pass: free-form (3) above, structured
# (4) below; each row's pooled family pass rate in the right column
# Valerio, 28 Oct (Supplementary 16 O1): the cells fill 183 mm, the house colour key horizontal above them, centred
# (7.5 mm more height).
_H2_KEYZ = 7.5
SIZE_H2 = (183.0, 85.47 + _H2_KEYZ)


def draw_H2(D, F, S):
    H = _H_data(D)
    cmap = _H_cmap()
    rws, ops, RH, GAPB = D.block_order, H["ops"], 2.7, 2.2
    LINE = _H_line_mm()
    labels = {v: vlabel(v) for v in rws}
    LA = max(tw(labels[v]) for v in rws) + 1.2
    fams = ["free-form", "structured"]
    nstr = H["nstr"]
    blk_h = len(rws) * RH
    gh = 2 * blk_h + GAPB + LINE
    codes = {o: _H_opcode(D, o) for o in ops}
    codes_h = tw("L10") + 2.0                # the draft's band (A10, 0.3 mm longer, still clears the note below)
    top = 4.5 + LINE + _H2_KEYZ
    MARG = tw("100") + 3.0
    CW = (F.W - _H_M - LA - MARG - 0.5) / len(ops)    # the cells fill the slot
    gw = len(ops) * CW
    need_w = _H_M + LA + gw + MARG + 0.5
    need_h = top + gh + codes_h + LINE + 2.5
    if need_w > F.W or need_h > F.H + 1e-6:
        raise SystemExit(f"H2 needs {need_w:.2f} (before its key's labels) x {need_h:.2f} mm, its slot is "
                         f"{F.W} x {F.H}")
    F.letter()
    ax = F.axes(_H_M + LA, top, gw + MARG, gh)
    ax.set_xlim(0, gw + MARG)
    ax.set_ylim(gh, 0)
    ax.axis("off")
    ax.set_xticks([])                    # no tick labels on the hidden axes (finish_plate counts them)
    ax.set_yticks([])
    texts = []
    op_row = {}
    for j, o in enumerate(ops):
        op_row[o] = S.add(part="operation", grid_column=j + 1, op_id=o, op_code=codes[o], dataset=D.dataset_of[o],
                          tier=D.tier_of[o], passes=H["oppool"][o][0], attempts=H["oppool"][o][1],
                          pass_rate_pct=100 * H["oppool"][o][0] / H["oppool"][o][1])
    for f in fams:
        for s in D.STRATS:
            if FAM[s] == f:
                S.add(part="strategy", strategy=D.SLAB[s], family=f)
    xm = gw + MARG / 2 + 0.3
    ftop = [fi * (blk_h + GAPB + LINE) for fi in range(len(fams))]

    def row_at(y_top):
        """Read-back of a row from a drawn top edge: its family block, then its place in the block (1-based, the
        structured block's rows after the free-form block's); 0 when the edge is in no block or between rows."""
        for fi, f0 in enumerate(ftop):
            q = (y_top - f0) / RH
            if -1e-9 < q < len(rws) - 1 + 1e-9 and abs(q - round(q)) < 1e-9:
                return fi * len(rws) + round(q) + 1
        return 0
    for t_ in TIERS:
        idx = [i for i, o in enumerate(ops) if D.tier_of[o] == t_]
        x0, x1 = idx[0] * CW + 0.3, (idx[-1] + 1) * CW - 0.3
        ax.plot([x0, x1], [-1.0 - LINE, -1.0 - LINE], color="#000000", lw=_H_LW_RULE, solid_capstyle="butt",
                clip_on=False)
        t = ax.text((x0 + x1) / 2, -1.6 - LINE, f"{t_} ({len(idx)})", ha="center", va="bottom")
        S.count(t, {"part": "operation", "tier": t_}, t_ + " ({count})")
        texts.append(t)
    texts.append(ax.text(xm, -1.6 - LINE, "all", ha="center", va="bottom"))
    for fi, f in enumerate(fams):
        y = ftop[fi]
        t = ax.text(0, y - 0.6, f"{f}, {nstr[f]} strategies", ha="left", va="bottom", fontweight="bold")
        S.count(t, {"part": "strategy", "family": f}, f + ", {count} strategies")
        texts.append(t)
        if f == fams[0]:
            texts.append(ax.text(xm, y - 0.6, "%", ha="center", va="bottom"))
        for i, v in enumerate(rws):
            yy = y + i * RH
            k, n = H["fam_pa"][(v, f)]
            grid_row = fi * len(rws) + rws.index(v) + 1
            pr = S.add(part="family pooled", grid_row=grid_row, variant=labels[v], family=f, passes=k, attempts=n,
                       pass_rate_pct=100 * k / n)
            lt = ax.text(-1.2, yy + RH / 2, labels[v], ha="right", va="center")
            S.num(lt, pr, "{variant}")
            S.check(f"row label row, {f}, {labels[v]}", [pr], "grid_row", [row_at(lt.get_position()[1] - RH / 2)])
            texts.append(lt)
            for j, o in enumerate(ops):
                kk, nn = H["opfam"][(v, f, o)]
                ri = S.add(part="cell", variant=labels[v], family=f, op_id=o, op_code=codes[o], tier=D.tier_of[o],
                           grid_row=grid_row, grid_column=j + 1, strategies_passing=kk, strategies=nn,
                           strategies_passing_pct=100 * kk / nn)
                val = S.rows[ri]["strategies_passing_pct"]
                rect = Rectangle((j * CW, yy), CW, RH, facecolor=cmap(val / 100), edgecolor="#FFFFFF",
                                 linewidth=0.4)
                ax.add_patch(rect)
                S.check(f"cell colour, {f}, {labels[v]}, {codes[o]}", [ri], "strategies_passing_pct",
                        [_H_bin_mid(cmap, rect.get_facecolor())], tol=_H_bin_tol(cmap, val))
                S.check(f"cell column, {f}, {labels[v]}, {codes[o]}", [ri], "grid_column", [rect.get_x() / CW + 1])
                S.check(f"cell row, {f}, {labels[v]}, {codes[o]}", [ri], "grid_row", [row_at(rect.get_y())])
            t = ax.text(xm, yy + RH / 2, S447.HALF_UP.format("{pass_rate_pct:.0f}", **S.rows[pr]), ha="center",
                        va="center")
            S.num(t, pr, "{pass_rate_pct:.0f}")
            S.check(f"pooled value row, {f}, {labels[v]}", [pr], "grid_row", [row_at(t.get_position()[1] - RH / 2)])
            texts.append(t)
        # a rule between the blocks' rows, on the line between two cells, so it adds no height
        yr = y + len(D.blocks[0][1]) * RH
        ax.plot([0, gw], [yr, yr], color=hs.GREY["line"], lw=hs.LW["divider"], solid_capstyle="butt", zorder=3)
    yb = 2 * blk_h + GAPB + LINE
    for j, o in enumerate(ops):
        t = ax.text(j * CW + CW / 2, yb + 1.0, codes[o], rotation=90, ha="center", va="top")
        S.num(t, op_row[o], "{op_code}")
        S.check(f"operation code column, {codes[o]}", [op_row[o]], "grid_column",
                [(t.get_position()[0] - CW / 2) / CW + 1])
        texts.append(t)
    texts.append(ax.text(0, yb + codes_h + 0.8, "Operation (A, airway RNA-seq; L, NCCTG lung survival)", ha="left",
                         va="top"))
    cax = _H_colorbar_h(F, _H_M + LA + gw / 2, "Strategies passing (%)")
    _H_inside(F, texts, [ax, cax])
    n_ff = H["fam_pa"][(rws[0], "free-form")][1]
    n_st = H["fam_pa"][(rws[0], "structured")][1]
    n_op = {H["oppool"][o][1] for o in ops}
    if n_op != {len(D.VARS) * len(D.STRATS)}:
        raise SystemExit(f"NOT REPRODUCED: H2: operations hold {sorted(n_op)} attempts, "
                         f"{len(D.VARS)} variants x {len(D.STRATS)} strategies wanted")
    return {"legend": (f"Share of a family's strategies passing each operation (cell colour), per model variant "
                       f"(row): free-form, n = {nstr['free-form']} strategies per cell, and structured, "
                       f"n = {nstr['structured']}; the introspection family is not shown. Rows: {D.blocks[0][0]}, then "
                       f"{D.blocks[1][0]}, each by pooled free-form pass rate, high to low, ties by pass rate over all "
                       f"{len(D.STRATS)} strategies. "
                       f"Operations (columns) are grouped by difficulty tier, then ordered by each operation's pass "
                       f"rate over its {n_op.pop()} attempts ({len(D.VARS)} variants by {len(D.STRATS)} strategies), "
                       f"high to low, ties by operation name. The right column is each variant's pooled pass rate in "
                       f"the family (n = {n_ff} free-form and {n_st} structured attempts). {_gemini_low()}")}


# ---- panels K ----------------------------------------------------------------------------------------------------------------
# ---- family K: pass rate by task difficulty (K-1, Figure 6b; K-5, Supplementary) -----------------------------------
# Ported from the scratch drafts draw_K.py (data, gate, helpers), draw_K1_v3.py (K-1 at 61 x 80 mm, key on one line)
# and draw_K5.py (K-1 per variant, 4 x 3 grid). Every number from D.rows; the drafts' reproduce gates kept below.
_K_CACHE = {}
_K_J447 = S447.OUT / "fig6_numbers.json"      # S447's committed per-variant, per-strategy counts (panel_b_cells)
_K_J477 = ROOT / "findings/recompute/S477_lung9_rescore.json"


def _K_stop(msg):
    raise SystemExit(f"NOT REPRODUCED: {msg}")


def _K_data(D):
    """Counts per (family, tier), (operation, family), (variant, operation, family) and the per-variant gaps, with
    draw_K.py's reproduce gates (S479's by_group, per_task and per-variant gaps by tier, S478's per-variant gaps, the
    per-variant overall gap, here against S447's committed fig6_numbers.json where the draft read summary.json),
    each operation's tier against S479's per_task, and draw_K5.py's 3 / 4 / 4 attempts per variant, operation and
    family."""
    if id(D) in _K_CACHE:
        return _K_CACHE[id(D)]
    rows = D.rows
    if len(rows) != WANT[0]:
        _K_stop(f"{len(rows)} attempts, not {WANT[0]}")
    j479, j478 = json.loads(J479.read_text()), json.loads(J478.read_text())
    tier_of = {}
    for r in rows:
        if tier_of.setdefault(r["op_id"], r["tier"]) != r["tier"]:
            _K_stop(f"{r['op_id']} has two tiers")
    tier_479 = {p["task"]: p["tier"] for p in j479["per_task"]}   # the tiers S479 committed, operation by operation
    if tier_of != tier_479:
        _K_stop(f"the operations' tiers differ from S479's per_task: "
                f"{sorted(o for o in set(tier_of) | set(tier_479) if tier_of.get(o) != tier_479.get(o))}")
    ops = {t: [o for o in sorted(tier_of) if tier_of[o] == t] for t in TIERS}
    cnt = defaultdict(lambda: [0, 0])
    for r in rows:
        p = r["passed"]
        for k in [("fam_tier", r["family"], r["tier"]), ("fam_tier", "all", r["tier"]),
                  ("fam_tier", r["family"], "all"), ("fam_tier", "all", "all"), ("op_fam", r["op_id"], r["family"]),
                  ("op", r["op_id"]), ("v_fam_tier", r["variant_id"], r["family"], r["tier"]),
                  ("v_fam", r["variant_id"], r["family"]), ("v_op_fam", r["variant_id"], r["op_id"], r["family"])]:
            cnt[k][0] += p
            cnt[k][1] += 1
    rate = lambda k: 100.0 * cnt[k][0] / cnt[k][1]
    for g in ["all"] + FAMS:                                  # draw_K.py: S479's by_group, all and the families
        for t in TIERS + ["all"]:
            want = j479["by_group"][g][t]
            if list(cnt[("fam_tier", g, t)]) != want["passes"] or round(rate(("fam_tier", g, t)), 1) != want["rate"]:
                _K_stop(f"{g} {t}: {cnt[('fam_tier', g, t)]} is not S479's {want}")
    if sorted(p["task"] for p in j479["per_task"]) != sorted(tier_of):
        _K_stop("S479's per_task does not list the 20 operations")
    for p in j479["per_task"]:
        if list(cnt[("op", p["task"])]) != p["passes"]:
            _K_stop(f"{p['task']}: not S479's {p['passes']}")
    # the per-variant family counts behind K-5's cell order, against S447's committed panel_b_cells (summed over each
    # family's strategies), written on the same records manifest and lung_9 re-score
    j447 = json.loads(_K_J447.read_text())
    for p, name in ((MANIFEST, "records manifest"), (_K_J477, "lung_9 re-score")):
        key = str(p.relative_to(ROOT))
        if j447["provenance"]["inputs_sha256"].get(key) != sha(p):
            _K_stop(f"{_K_J447.name} was written on another {name} ({key})")
    fam447 = defaultdict(lambda: [0, 0])
    for c in j447["panel_b_cells"]:
        fam447[(c["variant"], FAM[c["strategy"]])][0] += c["pass"]
        fam447[(c["variant"], FAM[c["strategy"]])][1] += c["attempts"]
    gap = {}
    for v in D.VARS:
        gap[v] = {t: rate(("v_fam_tier", v, "structured", t)) - rate(("v_fam_tier", v, "free-form", t)) for t in TIERS}
        gap[v]["all"] = rate(("v_fam", v, "structured")) - rate(("v_fam", v, "free-form"))
        for t in TIERS:                                       # S479 rounds each rate before subtracting: equal within 0.1
            if abs(gap[v][t] - j479["structured_minus_free_form_per_variant"][v][t]) > 0.11:
                _K_stop(f"{v} {t}: gap {gap[v][t]:.2f} is not S479's")
        for f in FAMS:
            if list(cnt[("v_fam", v, f)]) != fam447[(v, f)]:
                _K_stop(f"{v} {f}: {cnt[('v_fam', v, f)]} is not {_K_J447.name}'s {fam447[(v, f)]}")
    for v, w in j478["variants"].items():                     # S478: the thinking pairs, with "all"
        for t in TIERS + ["all"]:
            if round(gap[v][t], 1) != w[t]["structured_minus_free_form"]:
                _K_stop(f"{v} {t}: gap {gap[v][t]:.2f} is not S478's {w[t]['structured_minus_free_form']}")
    per = {"free-form": 3, "introspection": 4, "structured": 4}
    for v in D.VARS:                                          # draw_K5.py: 3 / 4 / 4 attempts per operation
        for o in tier_of:
            for f, n in per.items():
                if cnt[("v_op_fam", v, o, f)][1] != n:
                    _K_stop(f"{v} {o} {f}: {cnt[('v_op_fam', v, o, f)][1]} attempts, not {n}")
    pooled = {f: per[f] * len(D.VARS) for f in FAMS}          # 33 / 44 / 44 attempts per operation, all variants
    for o in tier_of:
        for f in FAMS:
            if cnt[("op_fam", o, f)][1] != pooled[f]:
                _K_stop(f"{o} {f}: {cnt[('op_fam', o, f)][1]} attempts pooled, not {pooled[f]}")
    out = {"cnt": cnt, "ops": ops, "gap": gap, "per": per, "pooled": pooled}
    _K_CACHE[id(D)] = out
    print(f"K: reproduced S479 by_group ({1 + len(FAMS)} groups x {len(TIERS) + 1} tiers), per_task "
          f"({len(j479['per_task'])} operations, passes and tiers), {len(D.VARS)} variants' gaps by tier (S479 "
          f"within 0.1, S478's {len(j478['variants'])} at 0.1), {len(D.VARS)} variants x {len(FAMS)} families' counts "
          f"({_K_J447.name}), per-variant attempts {per}")
    return out


def _K_spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _K_swarm(vals_mm, d):
    """draw_K.py's swarm: x offsets (mm) so dots of diameter d at these y positions (mm) do not touch: each dot takes
    the earliest free place in the sequence 0, +p, -p, +2p, ... (p = d + 0.15), lowest values placed before higher."""
    p = d + 0.15
    placed, offs = [], [0.0] * len(vals_mm)
    for i in sorted(range(len(vals_mm)), key=lambda i: vals_mm[i]):
        k = 0
        while True:
            cand = (k + 1) // 2 * p * (1 if k % 2 else -1) if k else 0.0
            if all((cand - x) ** 2 + (vals_mm[i] - y) ** 2 >= p ** 2 - 1e-9 for x, y in placed):
                break
            k += 1
        offs[i] = cand
        placed.append((cand, vals_mm[i]))
    return offs


def _K_cell(ax, S, K, v, ti, t, fi, f, dot, mm_y, mm_x, spread=False):
    """One family's dots and box in one tier: rows into the sheet, marks drawn, read-back registered. v is a variant
    id, or "all" for every variant pooled (K-1)."""
    cnt = K["cnt"]
    x0 = ti * 4 + fi * 1.15
    vname = "all variants" if v == "all" else vlabel(v)
    vals, idx = [], []
    for o in K["ops"][t]:
        p, n = cnt[("op_fam", o, f)] if v == "all" else cnt[("v_op_fam", v, o, f)]
        vals.append(100.0 * p / n)
        idx.append(S.add(part="operation", variant=vname, variant_id=v if v != "all" else None, tier=t, family=f,
                         operation=o, passes=p, attempts=n, pass_rate_pct=100.0 * p / n))
    # house box (style_1028): no fill, caps, 1.0 pt median, 0.40 of the 1.15-unit slot, dots under the lines
    st, art = _hbox(ax, x0, vals, colour=FCOL[f], marker=FMARK[f], dot_mm=dot, slot=1.15, spread=spread)
    dl = art["dots"]
    S.check(f"{vname} {t} {f} dots", idx, "pass_rate_pct", dl.get_ydata())
    q1, med, q3 = st["q1"], st["median"], st["q3"]
    lo, hi = st["whisker_low"], st["whisker_high"]
    b = S.add(part="box", variant=vname, variant_id=v if v != "all" else None, tier=t, family=f,
              n_operations=len(vals), median_pct=med, q1_pct=q1, q3_pct=q3, min_pct=lo, max_pct=hi)
    rq1, rmed, rq3, rlo, rhi = _hbox_read(art)
    S.check(f"{vname} {t} {f} q1", [b], "q1_pct", [rq1])
    S.check(f"{vname} {t} {f} q3", [b], "q3_pct", [rq3])
    S.check(f"{vname} {t} {f} median", [b], "median_pct", [rmed])
    S.check(f"{vname} {t} {f} min", [b], "min_pct", [rlo])
    S.check(f"{vname} {t} {f} max", [b], "max_pct", [rhi])


SIZE_K1 = (61.0, 80.0)


def draw_K1(D, F, S):
    """K-1 (draw_K1_v3.py): pass rate by tier and family, all variants pooled, one dot per operation, open box."""
    K = _K_data(D)
    W, H = SIZE_K1
    F.letter()
    AX_X, AX_Y = 11.0, 8.0                    # house: the key on the letter's line, centred over the axes
    AX_W, AX_H = W - AX_X - 0.6, H - AX_Y - 9.0
    hkey(F, [("mark", (FCOL[f], FMARK[f]), f) for f in FAMS], AX_X + AX_W / 2, PT_LETTER * MMPT)
    ax = F.axes(AX_X, AX_Y, AX_W, AX_H)
    _K_spines(ax)
    XLO, XHI = -0.6, 10.9
    ax.set_ylim(0, 100)
    ax.set_xlim(XLO, XHI)
    mm_y, mm_x = AX_H / 100.0, AX_W / (XHI - XLO)
    for ti, t in enumerate(TIERS):
        for fi, f in enumerate(FAMS):
            _K_cell(ax, S, K, "all", ti, t, fi, f, 1.05, mm_y, mm_x)
    ax.set_xticks([])
    # the tier names with their operation counts, where the draft's tick labels sat (3.5 pt below the axis, the tick
    # pad), drawn as text so each "n =" is tied to its box row in the sheet (S.num)
    pad = plt.rcParams["xtick.major.pad"]
    for ti, t in enumerate(TIERS):
        b = next(i for i, r in enumerate(S.rows) if r["part"] == "box" and r["tier"] == t and r["family"] == FAMS[1])
        lab = ax.annotate(f"{t}\nn = {len(K['ops'][t])}", xy=(ti * 4 + 1.15, 0), xycoords=("data", "axes fraction"),
                          xytext=(0, -pad), textcoords="offset points", ha="center", va="top", fontsize=PT)
        S.num(lab, b, "{tier}\nn = {n_operations}")
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Pass rate (%)", labelpad=2)
    n = {t: len(K["ops"][t]) for t in TIERS}
    pf = K["pooled"]
    # 8 Nov (Valerio, editor row 45): the boxes are derived statistics, so their n is stated in the editor's form,
    # once, inside this panel's description; no "as in" reference to another panel.
    return {"legend": (f"Pass rate of each operation by prompting family (colour and marker) and difficulty, all "
                       f"{len(D.VARS)} variants pooled: each dot is one operation, its pass rate over "
                       f"{pf['free-form']} free-form, {pf['introspection']} introspection or {pf['structured']} "
                       f"structured attempts. Box, median and quartiles of the dots; whiskers, range; n = {n['simple']} "
                       f"simple, {n['medium']} medium and {n['complex']} complex operations per box.")}


SIZE_K5 = (183.0, 96.0)


def _K_main_ref(pid):
    """The main figure's number and the letter draw_plate() gives panel pid there ("Figure 6b" for K1), from MAIN's
    rows read left to right and top to bottom."""
    ids = [p for r in MAIN["rows"] for p in r]
    if pid not in ids:
        raise SystemExit(f"K5's legend names {pid}'s main panel, and MAIN does not hold {pid}")
    return f"Figure {MAIN['n']}{'abcdefgh'[ids.index(pid)]}"


def draw_K5(D, F, S):
    """K-5 (draw_K5.py): K-1 drawn once per variant in a 4 x 3 grid, cells in D.block_order (FF21: the Gemini variants
    fill the first row), the twelfth cell all variants pooled (K-1)."""
    from matplotlib.ticker import FixedLocator
    K = _K_data(D)
    W5, H5 = SIZE_K5
    order = list(D.block_order)
    crow = {}
    for i, v in enumerate(order):                             # the cells' order, into the sheet
        c = K["cnt"]
        crow[v] = S.add(part="cell order", variant=vlabel(v), variant_id=v, block=D.block_of[v], cell=i + 1,
                        structured_passes=c[("v_fam", v, "structured")][0],
                        structured_attempts=c[("v_fam", v, "structured")][1],
                        free_form_passes=c[("v_fam", v, "free-form")][0],
                        free_form_attempts=c[("v_fam", v, "free-form")][1],
                        structured_minus_free_form_points=K["gap"][v]["all"])
    keyed = [S.rows[crow[v]] for v in order]                  # the key recomputed from each row's own counts
    again = [100 * r["structured_passes"] / r["structured_attempts"] - 100 * r["free_form_passes"]
             / r["free_form_attempts"] for r in keyed]
    if any(abs(a - r["structured_minus_free_form_points"]) > 1e-9 for a, r in zip(again, keyed)):
        raise SystemExit("K5: a cell's structured minus free-form gap is not its own counts'")
    if [r["variant_id"] for r in keyed] != D.block_order:
        raise SystemExit("K5: the cell order is not D.block_order")
    order.append("all")
    NC, NR = 4, 3
    key_h = 9.0
    cell_w = (W5 - 13.0) / NC
    ax_w5, ax_h5 = cell_w - 7.0, 19.0
    cell_h = ax_h5 + 4.8 + 4.2
    if abs(key_h + NR * cell_h + 3.0 - H5) > 1e-9:
        raise SystemExit("K5: the grid does not fill the panel's height")
    F.letter()
    # house: the family marks only (D147: the legend defines the box), centred over the grid of cells
    hkey(F, [("mark", (FCOL[f], FMARK[f]), f) for f in FAMS], 13.0 + (NC * cell_w - 7.0) / 2, PT_LETTER * MMPT)
    # 0.75 mm dots; tied dots of one family spread sideways as far as they need, so they do not touch (FF29). _K_swarm
    # sees one family at a time, so a spread dot can still land on a dot of the family beside it. The strict house box
    # (1.0 mm dots inside a band 0.67 of the slot) hid 423 of the 720 dots under another (HOUSE, 28 Oct).
    SPREAD5, DOT5 = True, 0.75
    for i, v in enumerate(order):
        r_, c_ = divmod(i, NC)
        x = 13.0 + c_ * cell_w
        y = key_h + r_ * cell_h + 4.8
        ax = F.axes(x, y, ax_w5, ax_h5)
        _K_spines(ax)
        ax.set_ylim(0, 100)
        ax.set_xlim(-0.6, 10.9)
        mm_y, mm_x = ax_h5 / 100.0, ax_w5 / 11.5
        for ti, t in enumerate(TIERS):
            for fi, f in enumerate(FAMS):
                _K_cell(ax, S, K, v, ti, t, fi, f, DOT5, mm_y, mm_x, spread=SPREAD5)
        ax.set_yticks([0, 50, 100])
        ax.yaxis.set_minor_locator(FixedLocator([25, 75]))
        ax.set_yticklabels(["0", "50", "100"] if c_ == 0 else [])
        if c_ == 0 and r_ == 1:
            ax.set_ylabel("Pass rate (%)")
        ax.set_xticks([ti * 4 + 1.15 for ti in range(3)])
        ax.set_xticklabels(TIERS if r_ == NR - 1 else [])
        ax.tick_params(axis="x", length=0)
        name = f"all variants (Fig. {S447.FIG_N}b)" if v == "all" else vlabel(v)          # Valerio, 25 Oct (Q3)
        t_ = F.text(x + ax_w5 / 2, y - 1.7, name, ha="center", va="baseline",
                    fontweight="bold" if v == "all" else "normal")
        if v == "all":
            S.book.fixed(t_, f"a reference to Figure {S447.FIG_N}b, not a number of the data")
        elif re.search(r"\d", name):
            S.book.fixed(t_, "a model's name with its version or size, not a number of the data")
        if v != "all":                                        # read-back: the cell the drawn axes sit in, and its title
            bb = ax.get_position()
            col = round((bb.x0 * F.page.W - F.ox - 13.0) / cell_w)
            row = round(((1 - bb.y1) * F.page.H - F.oy - key_h - 4.8) / cell_h)
            S.check(f"{name} cell", [crow[v]], "cell", [row * NC + col + 1])
            if t_.get_text() != S.rows[crow[v]]["variant"]:
                raise SystemExit(f"K5: cell {i + 1} is titled {t_.get_text()!r}, its sheet row {crow[v]} holds "
                                 f"{S.rows[crow[v]]['variant']!r}")
    n = {t: len(K["ops"][t]) for t in TIERS}
    per = K["per"]
    ref = _K_main_ref("K1")
    return {"legend": (f"{ref} drawn once per model variant: the {D.blocks[0][0]} variants, then the {D.blocks[1][0]} "
                       f"variants, each by pooled free-form pass rate, high to low; the last cell pools all "
                       f"{len(D.VARS)} variants, as {ref}. In a variant's cell each dot is one operation's share of "
                       f"{per['free-form']} free-form, {per['introspection']} introspection or {per['structured']} "
                       f"structured attempts that passed. Box: median and quartiles; whiskers: range. {_gemini_low()} "
                       f"n = {n['simple']} simple, {n['medium']} medium and {n['complex']} complex operations per box.")}


# ---- panels X ----------------------------------------------------------------------------------------------------------------
# ---- family X: what each attempt became, per strategy, dataset and model (X-1, Figure 6c; X-2, X-3, X-4,
# Supplementary) --------------------------------------------------------------------------------------------------------
# Ported from the scratch drafts draw_X.py (data, gate, helpers; alt2, alt3, alt4) and draw_X1_v3.py (X-1 at
# 99.9 x 84.7 mm, datasets stacked, key on one line). Every number from D.rows. _X_data()'s reproduce gates compare
# with sources computed apart from D.rows: S447's committed fig6_numbers.json (written by `S447 draw` on the same
# records: attempts, passes and failure kinds per variant and strategy, passes per variant and operation), S479's
# by_group and per_task, S478's structured failure kinds, the ground truth's operations per dataset and difficulty,
# and the drafts' own stored numbers (_X_DRAFT). Each panel's counts are also summed a second way, from D.idx by the
# ground truth's operation lists, and compared with the counts drawn.
_X_CACHE = {}
_X_FIG6_NUMBERS = OUT_MAIN / "fig6_numbers.json"     # S447 draw's numbers (committed; S481 writes figure6_numbers.json)
# The drafts' stored numbers: coverage_check.json of 24 October, written by the drafts' coverage_check.py from
# attempts.csv, frozen with both at _X_COVERAGE (D155, INVENTORY A1f); copied here, and _X_data() stops unless the
# frozen file has _X_COVERAGE_SHA256 and holds these values. Written again on 5 November 2026 by prep.py and
# coverage_check.py on the records after S4's reruns with the lung_9 re-score (2,420 attempts, 1,692 passes; fig6 spec
# A6); the values of 24 October (1,660 passes) are in git history.
_X_COVERAGE = ROOT / "findings/recompute/fig6_options_2026-10-25/inputs/coverage_check.json"
_X_COVERAGE_SHA256 = "9b376fd08d45168112b7b7bb35e1c970ceeee9d91ce08af70f6253274c4e3687"
_X_DRAFT = {
    "rwm_split": {("ok", True): 225, ("ok", False): 41, ("error", True): 24},
    "ops_by_dataset_tier": {("RNA-seq", "complex"): 2, ("RNA-seq", "medium"): 5, ("RNA-seq", "simple"): 3,
                            ("survival", "complex"): 4, ("survival", "medium"): 3, ("survival", "simple"): 3},
    "gap_by_dataset_variant": {
        "RNA-seq": {"qwen3-coder-30b+default": -14.2, "qwen3-coder-next-q4_K_M+default": -27.5,
                    "gpt-oss-20b+low": 14.2, "gpt-oss-20b+medium": -12.5, "gpt-oss-20b+high": -30.8,
                    "gemma3-27b+default": -76.7, "devstral-small-2-24b+default": -22.5, "gemini-2.5-pro+default": -0.8,
                    "gemini-2.5-pro+off": 10.0, "gemini-3-flash-preview+default": 7.5,
                    "gemini-3-flash-preview+off": 8.3},
        "survival": {"qwen3-coder-30b+default": -40.8, "qwen3-coder-next-q4_K_M+default": -51.7,
                     "gpt-oss-20b+low": -35.8, "gpt-oss-20b+medium": -10.0, "gpt-oss-20b+high": -29.2,
                     "gemma3-27b+default": -50.0, "devstral-small-2-24b+default": -30.0, "gemini-2.5-pro+default": 7.5,
                     "gemini-2.5-pro+off": -29.2, "gemini-3-flash-preview+default": -5.8,
                     "gemini-3-flash-preview+off": 7.5}}}
# The legends' words for S447.fail_kind()'s kinds; a kind the panels hold with no words here stops the run, so a
# legend never omits a kind the bars count.
_X_KIND_WORDS = {"tool-call parse error": "an unparsable tool call", "tool call written as text": "a tool call written "
                 "as text", "stall": "a stall", "tools refused by Ollama": "tools refused by Ollama",
                 "other call error": "another call error", "length stop": "a length stop",
                 "harness error": "a harness error",
                 "step produced no cell and no error": "a step that produced no cell and no error",
                 "Gemini empty reply": "an empty Gemini reply", "no code": "no code",
                 "other": "a failure of none of these kinds"}
_X_EO_WORDS = {"error": "raised an error", "exec_timeout": "timed out", "step_failed": "failed its step"}
_X_TCF = "tool or call failure, other"
# draw_X.py alt4's split of "tool or call failure, other" (outcome5(), length stops apart): the call failures that
# are not Ollama's tool refusal, and what is left (harness error, Gemini empty reply, no code, other)
_X_MECH_OTHER = ["tool-call parse error", "tool call written as text", "stall", "other call error",
                 "step produced no cell and no error"]
_X_REFUSED = "tools refused by Ollama"
_X_G6 = [("tools refused by Ollama", S447.TOOLS_GREY, "*"),
         ("other tool or call failure", OCOL[_X_TCF], OPAT[_X_TCF]),
         ("length stop", OCOL["length stop"], OPAT["length stop"]),
         ("no result", OCOL["no result"], OPAT["no result"]),
         ("wrong values", OCOL["wrong values"], OPAT["wrong values"]),
         ("other (harness, no code)", S447.OKABE_GREY, "o")]
_X_BLOCK_NAMES = (figure_names.GEMINI, figure_names.OPEN_WEIGHT)


def _X_stop(msg):
    raise SystemExit(f"NOT REPRODUCED: {msg}")


def _X_group6(r):
    """alt4's six failure groups of one failed attempt, from outcome5()."""
    o5 = r["outcome5"]
    if o5 in ("length stop", "no result", "wrong values"):
        return o5
    if o5 != _X_TCF:
        _X_stop(f"{r['variant_id']} {r['strategy']} {r['op_id']}: outcome5 {o5!r} on a failed attempt")
    if r["fail_kind"] == _X_REFUSED:
        return "tools refused by Ollama"
    if r["fail_kind"] in _X_MECH_OTHER:
        return "other tool or call failure"
    return "other (harness, no code)"


def _X_join(words):
    """['a'] -> 'a'; ['a', 'b', 'c'] -> 'a, b or c' (no serial comma)."""
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " or " + words[-1]


def _X_kinds_words(kinds):
    """The legend's words for these fail kinds, in S447.KINDS_ALL's order; a kind with no words stops the run."""
    missing = sorted(set(kinds) - set(_X_KIND_WORDS))
    if missing:
        _X_stop(f"legend: no words for the fail kind(s) {missing}")
    return _X_join([_X_KIND_WORDS[k] for k in S447.KINDS_ALL if k in kinds])


_X_KIND_GROUP = {"tool-call parse error": "a tool or model call failed", "tool call written as text": "a tool or model "
                 "call failed", "stall": "a tool or model call failed", "tools refused by Ollama": "a tool or model "
                 "call failed", "other call error": "a tool or model call failed", "Gemini empty reply": "a tool or "
                 "model call failed", "length stop": "the reply filled its context or output cap",
                 "harness error": "the harness or a step failed", "step produced no cell and no error": "the harness "
                 "or a step failed", "no code": "no code", "other": "another failure"}


def _X_kinds_short(kinds):
    """The short legend words for these fail kinds (Figure 6c, Valerio 25 Oct: captions under 350 words): grouped,
    in S447.KINDS_ALL's order of first appearance; a kind with no group stops the run."""
    missing = sorted(set(kinds) - set(_X_KIND_GROUP))
    if missing:
        _X_stop(f"legend: no short words for the fail kind(s) {missing}")
    return _X_join(list(dict.fromkeys(_X_KIND_GROUP[k] for k in S447.KINDS_ALL if k in kinds)))


def _X_outcome_2(r):
    """X-1's outcome a second way, for the second count: from S447.fail_kind() and the returned values as the core's
    outcome4() defines them, written apart from the row's own "outcome" field."""
    if r["passed"]:
        return "passed"
    return {("result wrong or missing", True): "wrong values", ("result wrong or missing", False): "no result",
            ("code raised or timed out", False): "no result",
            ("code raised or timed out", True): "no result"}.get((r["fail_kind"], r["has_results"]), _X_TCF)


def _X_data(D):
    """The counts the four panels draw, gated against sources computed apart from D.rows."""
    if id(D) in _X_CACHE:
        return _X_CACHE[id(D)]
    rows = D.rows
    if (len(rows), sum(r["passed"] for r in rows)) != WANT:
        _X_stop(f"{len(rows)} attempts and {sum(r['passed'] for r in rows)} passes, not {WANT}")
    # (0) _X_DRAFT is the frozen coverage_check.json's own numbers (D155)
    if sha(_X_COVERAGE) != _X_COVERAGE_SHA256:
        _X_stop(f"{_X_COVERAGE.relative_to(ROOT)} is not the drafts' coverage_check.json (sha256 {sha(_X_COVERAGE)})")
    cov = json.loads(_X_COVERAGE.read_text())
    cov_rwm = {(eo, hr == "True"): n for k, n in cov["result_wrong_or_missing_by_exec_outcome_and_has_results"].items()
               for eo, hr in [k.split(" | has_results=")]}
    cov_ops = {tuple(k.split(" | ")): n for k, n in cov["operations_by_dataset_tier"].items()}
    if cov_rwm != _X_DRAFT["rwm_split"] or cov_ops != _X_DRAFT["ops_by_dataset_tier"] or \
            cov["structured_minus_free_form_by_dataset_variant"] != _X_DRAFT["gap_by_dataset_variant"]:
        _X_stop(f"_X_DRAFT differs from {_X_COVERAGE.relative_to(ROOT)}")
    # (1) S447's committed fig6_numbers.json, on the same records: per variant and strategy the attempts, passes and
    # failure kinds; per variant and operation the passes over the 11 strategies.
    j447 = json.loads(_X_FIG6_NUMBERS.read_text())
    for k, h in j447["provenance"]["inputs_sha256"].items():
        # a findings/runs/ name is the mirror's (gitignored, not read since D155): it is held to the frozen bytes
        # read (D.inputs) on the next line, never to whatever that folder holds on this computer
        # D160 (6), Q18 (audit 27 Oct F10): a recorded input that cannot be read is refused, never skipped
        # "frozen <set>.tar" is load_mirror's name for the tar it read (outside the repository): held to D.inputs too
        read_only = k.startswith("findings/runs/") or (k.startswith("frozen ") and k.endswith(".tar"))
        if not read_only and not (ROOT / k).exists():
            _X_stop(f"{_X_FIG6_NUMBERS.name} records {k}, which is not in the repository")
        if read_only and k not in D.inputs:
            _X_stop(f"{_X_FIG6_NUMBERS.name} records {k}, which the frozen records read (D.inputs) do not hold")
        if not read_only and sha(ROOT / k) != h and not (
                k == "experiments/LOCK.toml" and {h, sha(ROOT / k)} <= _lock_equiv().EQUIVALENT):   # D204
            _X_stop(f"{_X_FIG6_NUMBERS.name} was written on another {k}")
        if k in D.inputs and D.inputs[k] != h and not (
                k == "experiments/LOCK.toml" and {h, D.inputs[k]} <= _lock_equiv().EQUIVALENT):          # D204
            _X_stop(f"{_X_FIG6_NUMBERS.name} was written on another {k} than these rows")
    if set(j447["design"]["variant_list"]) != set(D.VARS):
        _X_stop(f"{_X_FIG6_NUMBERS.name}'s design is not these {len(D.VARS)} variants")
    cells = {(c["variant"], c["strategy"]): c for c in j447["panel_b_cells"] if c["variant"] in D.VARS}
    for v in D.VARS:
        for s in D.STRATS:
            rr = [D.idx[(v, s, o)] for o in D.OPS]
            c = cells.get((v, s))
            kinds = Counter(r["fail_kind"] for r in rr if not r["passed"])
            if c is None or (c["attempts"], c["pass"]) != (len(rr), sum(r["passed"] for r in rr)) or \
                    dict(kinds) != {k[6:]: n for k, n in c.items() if k.startswith("kind: ") and n}:
                _X_stop(f"{v} {s}: attempts, passes or failure kinds are not {_X_FIG6_NUMBERS.name}'s")
    per_op = {w["variant"]: w["per_operation"] for m in j447["panel_c_thinking"].values() for w in m["variants"]}
    for v in D.VARS:
        for o in D.OPS:
            rr = [D.idx[(v, s, o)] for s in D.STRATS]
            if [sum(r["passed"] for r in rr), len(rr)] != per_op[v].get(o):
                _X_stop(f"{v} {o}: passes are not {_X_FIG6_NUMBERS.name}'s {per_op[v].get(o)}")
    # (2) the drafts' split of "result wrong or missing" by exec_outcome and returned values (X-1's wrong values and
    # no result)
    split_eo = Counter((r["exec_outcome"], r["has_results"]) for r in rows
                       if not r["passed"] and r["fail_kind"] == "result wrong or missing")
    if dict(split_eo) != _X_DRAFT["rwm_split"]:
        _X_stop(f"'result wrong or missing' split {dict(split_eo)}, the drafts stored {_X_DRAFT['rwm_split']}")
    cnt = defaultdict(lambda: [0, 0])
    for r in rows:
        for k in [("d_f", r["dataset"], r["family"]), ("d_t_f", r["dataset"], r["tier"], r["family"]),
                  ("v_d_f", r["variant_id"], r["dataset"], r["family"]), ("v_f", r["variant_id"], r["family"]),
                  ("o_f", r["op_id"], r["family"]), ("o", r["op_id"]), ("s", r["strategy"]), ("f", r["family"])]:
            cnt[k][0] += r["passed"]
            cnt[k][1] += 1
    o_sb = Counter((r["strategy"], D.block_of[r["variant_id"]], r["outcome"]) for r in rows)
    n_sb = Counter((r["strategy"], D.block_of[r["variant_id"]]) for r in rows)
    # (3) a second count: each dataset's operations and their difficulty read from the ground truth file itself,
    # strategies by S478.FAM, every attempt looked up in D.idx; the operations' difficulty also against S479's per_task
    gt = json.loads(GT.read_text())["datasets"]
    ops_gt = {DATASET[dn]: {o: x["complexity"] for o, x in d_["operations"].items()} for dn, d_ in gt.items()}
    j479, j478 = json.loads(J479.read_text()), json.loads(J478.read_text())
    tier479 = {p["task"]: p["tier"] for p in j479["per_task"]}
    ops_dt = {(d, t): sorted(o for o in D.ops_of_tier[t] if D.dataset_of[o] == d) for d in DSETS for t in TIERS}
    for d in DSETS:
        for t in TIERS:
            two = sorted(o for o, c in ops_gt[d].items() if c == t)
            if ops_dt[(d, t)] != two or sorted(o for o in two if tier479.get(o) == t) != two or \
                    len(two) != _X_DRAFT["ops_by_dataset_tier"][(d, t)]:
                _X_stop(f"{d} {t}: operations {ops_dt[(d, t)]}, the ground truth {two}, S479 or the drafts differ")
    strats_f = {f: [s for s in D.STRATS if FAM[s] == f] for f in FAMS}
    for d in DSETS:
        for v in D.VARS:
            for f in FAMS:
                rr = [D.idx[(v, s, o)] for s in strats_f[f] for o in ops_gt[d]]
                if [sum(r["passed"] for r in rr), len(rr)] != list(cnt[("v_d_f", v, d, f)]):
                    _X_stop(f"X-2: {v} {d} {f}: the second count differs")
    for b, vv in D.blocks:
        for s in D.STRATS:
            rr = [D.idx[(v, s, o)] for v in vv for o in D.OPS]
            if len(rr) != n_sb[(s, b)] or any(sum(1 for r in rr if _X_outcome_2(r) == o) != o_sb[(s, b, o)]
                                              for o in OUTCOMES):
                _X_stop(f"X-1: {s} {b}: the second count differs")
    for o in D.OPS:
        for f in FAMS:
            rr = [D.idx[(v, s, o)] for v in D.VARS for s in strats_f[f]]
            if [sum(r["passed"] for r in rr), len(rr)] != list(cnt[("o_f", o, f)]):
                _X_stop(f"X-3: {o} {f}: the second count differs")
    # (4) committed: S479's passes per strategy and family and per operation; S478's structured failure kinds
    for g in D.STRATS + FAMS:
        if list(cnt[("s", g)] if g in D.STRATS else cnt[("f", g)]) != j479["by_group"][g]["all"]["passes"]:
            _X_stop(f"{g}: passes not S479's {j479['by_group'][g]['all']['passes']}")
    if sorted(p["task"] for p in j479["per_task"]) != D.OPS:
        _X_stop("S479's per_task does not list the operations")
    for p in j479["per_task"]:
        if list(cnt[("o", p["task"])]) != p["passes"] or \
                [sum(cnt[("o_f", p["task"], f)][i] for f in FAMS) for i in (0, 1)] != p["passes"]:
            _X_stop(f"{p['task']}: not S479's {p['passes']}")
    fails = [r for r in rows if not r["passed"]]
    g6 = Counter((r["variant_id"], r["family"], _X_group6(r)) for r in fails)
    for v, w in j478["variants"].items():             # S478's structured failure kinds, folded to alt4's six
        k = w["structured_fail_kinds"]
        want = {"tools refused by Ollama": k.get(_X_REFUSED, 0), "length stop": k.get("length stop", 0),
                "other tool or call failure": sum(k.get(x, 0) for x in _X_MECH_OTHER),
                "no result or wrong values": k.get("result wrong or missing", 0) + k.get("code raised or timed out", 0),
                "other (harness, no code)": sum(n for x, n in k.items() if x not in _X_MECH_OTHER + [
                    _X_REFUSED, "length stop", "result wrong or missing", "code raised or timed out"])}
        got = {g: g6[(v, "structured", g)] for g in want if g in {n for n, _, _ in _X_G6}}
        got["no result or wrong values"] = g6[(v, "structured", "no result")] + g6[(v, "structured", "wrong values")]
        if got != want:
            _X_stop(f"{v} structured: failure groups {got} are not S478's kinds folded {want}")
    if sum(g6.values()) != len(fails):
        _X_stop("alt4: the six groups do not hold every failed attempt once")
    for v in D.VARS:                                  # every variant and family: the six groups against S447's kinds
        for f in FAMS:
            k = Counter()
            for s in strats_f[f]:
                k.update({x[6:]: n for x, n in cells[(v, s)].items() if x.startswith("kind: ")})
            want = {"tools refused by Ollama": k[_X_REFUSED], "length stop": k["length stop"],
                    "other tool or call failure": sum(k[x] for x in _X_MECH_OTHER),
                    "no result or wrong values": k["result wrong or missing"] + k["code raised or timed out"]}
            want["other (harness, no code)"] = sum(k.values()) - sum(want.values())
            got = {g: g6[(v, f, g)] for g in want if g in {n for n, _, _ in _X_G6}}
            got["no result or wrong values"] = g6[(v, f, "no result")] + g6[(v, f, "wrong values")]
            if got != want:
                _X_stop(f"X-4: {v} {f}: failure groups {got} are not {_X_FIG6_NUMBERS.name}'s kinds folded {want}")
    # structure: one n per block's X-1 bars; equal attempts per variant, a whole number per operation (X-2); equal attempts
    # per operation and family (X-3)
    for b, _ in D.blocks:
        per_bar = {n_sb[(s, b)] for s in D.STRATS}
        if len(per_bar) != 1:
            _X_stop(f"X-1: {b} bars of {sorted(per_bar)} attempts, not one n")
    for d in DSETS:
        nd = sum(len(ops_dt[(d, t)]) for t in TIERS)
        for f in FAMS:
            per_v = {cnt[("v_d_f", v, d, f)][1] for v in D.VARS}
            if len(per_v) != 1:
                _X_stop(f"X-2: {d} {f} attempts differ between variants: {per_v}")
            if per_v.pop() % nd:
                _X_stop(f"X-2: {d} {f} attempts are not a whole number per operation")
    pooled = {f: {cnt[("o_f", o, f)][1] for o in D.OPS} for f in FAMS}
    if any(len(x) != 1 for x in pooled.values()):
        _X_stop(f"X-3: operations hold different numbers of attempts per family: {pooled}")
    rate = lambda c: 100.0 * c[0] / c[1]
    GAPD = {d: {v: rate(cnt[("v_d_f", v, d, "structured")]) - rate(cnt[("v_d_f", v, d, "free-form")])
                for v in D.VARS} for d in DSETS}
    # (5) X-2's printed gaps against the drafts' stored ones (rounded to 0.1 there)
    for d in DSETS:
        if set(_X_DRAFT["gap_by_dataset_variant"][d]) != set(D.VARS) or \
                any(abs(GAPD[d][v] - _X_DRAFT["gap_by_dataset_variant"][d][v]) > 0.05 + 1e-9 for v in D.VARS):
            _X_stop(f"X-2: {d}: the structured minus free-form gaps are not the drafts' stored ones")
    cloud = [v for v in D.VARS if is_gemini(v)]
    opens = [v for v in D.VARS if v not in cloud]
    ffall = {v: rate(cnt[("v_f", v, "free-form")]) for v in D.VARS}
    key_ = lambda v: (-ffall[v], -D.summary["per_variant"][v]["overall"][0])
    blocks = [(_X_BLOCK_NAMES[0], sorted(cloud, key=key_)), (_X_BLOCK_NAMES[1], sorted(opens, key=key_))]
    if blocks != D.blocks:                            # D.blocks, this key's one home (FF21), from this table's counts
        _X_stop(f"the blocks from these counts {blocks} are not D.blocks {D.blocks}")
    ties = any(ffall[a] == ffall[b] for _, vv in blocks for a, b in zip(vv, vv[1:]))
    print(f"X: reproduced {_X_FIG6_NUMBERS.relative_to(ROOT)} (attempts, passes and failure kinds of "
          f"{len(cells)} variant x strategy cells; passes of {len(D.VARS) * len(D.OPS)} variant x operation cells), "
          f"the drafts' 'result wrong or missing' split {dict(sorted(split_eo.items()))}, operations per dataset and "
          f"difficulty (ground truth, S479, drafts), the {sum(len(x) for x in GAPD.values())} dataset gaps (drafts), "
          f"S479's passes per strategy, family and operation, S478's structured failure kinds ({len(j478['variants'])} "
          f"variants) and S447's failure kinds ({len(D.VARS)} variants x {len(FAMS)} families) folded to X-4's six "
          f"groups; X-1, X-2 and X-3 counts equal a second count from the ground truth's operation lists")
    out = {"cnt": cnt, "o_sb": o_sb, "n_sb": n_sb, "GAPD": GAPD, "blocks": blocks, "ops_dt": ops_dt, "g6": g6,
           "split_eo": split_eo, "ties": ties}
    _X_CACHE[id(D)] = out
    return out


# ---- drawing helpers (draw_X.py's Page, into the panel's Frame) -------------------------------------------------
def _X_mm_data(F, ax, pts):
    p = np.asarray(pts, dtype=float).reshape(-1, 2)
    dpi = F.fig.dpi
    disp = np.column_stack([(F.ox + p[:, 0]) / 25.4 * dpi, (F.page.H - F.oy - p[:, 1]) / 25.4 * dpi])
    return ax.transData.inverted().transform(disp)


def _X_data_mm(F, ax, pts):
    p = ax.transData.transform(np.asarray(pts, dtype=float).reshape(-1, 2))
    dpi = F.fig.dpi
    return np.column_stack([p[:, 0] / dpi * 25.4 - F.ox, F.page.H - p[:, 1] / dpi * 25.4 - F.oy])


def _X_pattern(F, ax, rect, pat, fill, z=3):
    """S447's fill pattern inside rect (slot mm), in black or white lines (ink_on) of [lines] line_min_pt."""
    if not pat:
        return
    ink = S447.ink_on(fill)
    lines, dots, rings = S447.pattern_marks(rect, pat)
    for pts in lines:
        a = _X_mm_data(F, ax, list(pts))
        ax.plot(a[:, 0], a[:, 1], color=ink, lw=LW, solid_capstyle="butt", solid_joinstyle="miter", zorder=z)
    for pts, filled, dmm in ((dots, True, S447.DOT_PATTERN_MM), (rings, False, S447.RING_PATTERN_MM)):
        if pts:
            a = _X_mm_data(F, ax, pts)
            ax.plot(a[:, 0], a[:, 1], ls="", marker="o", ms=S447.ms_pt(dmm), mfc=ink if filled else "none",
                    mec="none" if filled else ink, mew=0 if filled else LW, zorder=z)


def _X_bar(F, ax, y, left, width, col, pat, h=hs.BAR_FRAC):
    """One bar segment with its pattern; returns the drawn Rectangle (read back). House: no outline, no gap between
    segments, BAR_FRAC of the row thick."""
    rect = ax.barh(y, width, left=left, color=col, height=h, edgecolor="none", linewidth=0, zorder=2).patches[0]
    (x0, y0), (x1, y1) = _X_data_mm(F, ax, [(left, y - h / 2), (left + width, y + h / 2)])
    ins = LW * MMPT
    _X_pattern(F, ax, (min(x0, x1) + ins, min(y0, y1) + ins, max(x0, x1) - ins, max(y0, y1) - ins), pat, col)
    return rect


def _X_key_room(F, cx):
    """The widest key that stays inside the slot when centred on cx (frame mm)."""
    return 2 * min(cx, F.W - cx) - 0.4


def _X_strip_y(ax):
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=2)


def _X_rows_y(X):
    """alt2's and alt4's rows: a heading row per block (Gemini, open-weight), 0.4 rows apart, then its variants. X needs
    only "blocks", so draw_G4 passes D.blocks alone."""
    rows_y, heads, yy = [], [], 0.0
    for bi, (b, vv) in enumerate(X["blocks"]):
        if bi:
            yy += 0.4
        heads.append((b, yy))
        yy += 1.0
        for v in vv:
            rows_y.append((v, b, yy))
            yy += 1.0
    return rows_y, heads, yy


# ---- X-1 (Figure 6c): outcome bars per strategy, Gemini above open-weight (FF32; D138's datasets moved to X-2) ------
SIZE_X1 = (183.0, 85.7)                     # house: 1 mm taller so 0.70-row bars still hold their digits; D299 (7 Nov):
                                            # the page's width, since d (B1) left the row


def draw_X1(D, F, S):
    X = _X_data(D)
    W, H = SIZE_X1
    F.letter()
    STRATS = D.STRATS
    BAR_FRAC, FGAP = hs.BAR_FRAC, 0.30                 # bar height in rows (house 0.70); gap between families
    CAP = 0.717 * PT * MMPT                            # Helvetica digit height, mm: the pass % on the bar's centre
    LAB = max(tw(D.SLAB[s]) for s in STRATS) + 2.0
    RIGHT = tw("100") / 2 + 0.3
    ypos, yy = {}, 0.0
    for i, s in enumerate(STRATS):
        if i and FAM[s] != FAM[STRATS[i - 1]]:
            yy += FGAP
        ypos[s] = yy
        yy += 1.0
    NROWS = yy
    cw = W - LAB - RIGHT
    # house key: swatches with their patterns on one line, centred over the bars and moved the least needed to stay
    # inside the slot (two lines would leave the bars too thin for their numbers within the 170 mm page)
    _, klines = hkey(F, [("swatch", (OCOL[o], OPAT[o] or None), o) for o in OUTCOMES], LAB + cw / 2,
                     PT_LETTER * MMPT)
    HEAD1 = klines[-1][2] - F.oy + 4.2
    TOP1 = HEAD1 + 0.9
    PH = (H - 4.8 - TOP1 - 3.6 - 0.9) / 2              # the two model groups fill the slot
    PITCH = PH / NROWS
    if PITCH * BAR_FRAC < CAP:
        raise SystemExit(f"X1: a bar {PITCH * BAR_FRAC:.2f} mm thick cannot hold its {CAP:.2f} mm digits")
    HEAD2 = TOP1 + PH + 3.6
    TOP2 = HEAD2 + 0.9
    BOT = TOP2 + PH
    n_bar = None
    for j, ((b, _), top, head) in enumerate(zip(D.blocks, (TOP1, TOP2), (HEAD1, HEAD2))):
        ax = F.axes(LAB, top, cw, PH)
        ax.set_xlim(0, 100)
        ax.set_ylim(NROWS - 0.5 + 0.12, -0.5)
        first = None
        for s in STRATS:
            n = X["n_sb"][(s, b)]
            left = 0.0
            pass_row = None
            for o in OUTCOMES:
                k = X["o_sb"][(s, b, o)]
                w_ = 100.0 * k / n
                ri = S.add(model_group=b, strategy=D.SLAB[s], strategy_id=s, family=FAM[s], outcome=o,
                           attempts=k, attempts_in_bar=n, share_pct=w_, start_pct=left)
                first = ri if first is None else first
                if o == "passed":
                    pass_row = ri
                if w_:
                    rect = _X_bar(F, ax, ypos[s], left, w_, OCOL[o], OPAT[o], h=BAR_FRAC)
                    S.check(f"{b} {s} {o} width", [ri], "share_pct", [rect.get_width()])
                    S.check(f"{b} {s} {o} start", [ri], "start_pct", [rect.get_x()])
                left += w_
            if abs(left - 100.0) > 1e-9:
                raise SystemExit(f"X1: {b} {s} outcomes sum to {left}%")
            pr = S.rows[pass_row]["share_pct"]
            t = ax.text(2.0, ypos[s] + CAP / 2 / PITCH, S447.HALF_UP.format("{share_pct:.0f}", share_pct=pr),
                        va="baseline", ha="left", fontsize=PT, color=S447.ink_on(OCOL["passed"]), zorder=6)
            S.num(t, pass_row, "{share_pct:.0f}")
        ax.set_yticks([ypos[s] for s in STRATS], [D.SLAB[s] for s in STRATS])
        ax.set_xticks([0, 50, 100])
        if j == 0:
            ax.set_xticklabels([])
        _X_strip_y(ax)
        t = F.text(0.5, head, f"{b}, n = {X['n_sb'][(STRATS[0], b)]} per bar", va="baseline", ha="left")
        S.num(t, first, b + ", n = {attempts_in_bar} per bar")
    F.text(LAB - 2.0, BOT + (plt.rcParams["xtick.major.size"] + plt.rcParams["xtick.major.pad"]) * MMPT,
           "Attempts (% of n)", va="top", ha="right")
    (g_name, g_v), (o_name, o_v) = D.blocks
    # 8 Nov (Valerio, editor row 45): no derived statistics here, so no "n ="; the attempts per bar are said once,
    # as what each bar holds and as the plate prints them.
    return {"legend": (f"Outcome of the attempts of each prompting strategy (row), as percentages: each {g_name} bar "
                       f"holds {X['n_sb'][(STRATS[0], g_name)]} attempts ({len(g_v)} variants on {len(D.OPS)} "
                       f"operations) and each {o_name} bar {X['n_sb'][(STRATS[0], o_name)]} ({len(o_v)} variants); the number on each bar is the percentage passed. "
                       f"{_X_outcome_words(D, short=True)}")}


def _X_outcome_words(D, short=False):
    """X-1's definitions of its three failure outcomes, from what outcome4() puts in each (S447.fail_kind(), the
    record's exec_outcome and whether it returned values): a case the words do not cover stops the run."""
    fails = [r for r in D.rows if not r["passed"]]
    wv = [r for r in fails if r["outcome"] == "wrong values"]
    nr = [r for r in fails if r["outcome"] == "no result"]
    tcf = [r for r in fails if r["outcome"] == _X_TCF]
    if {(r["fail_kind"], r["has_results"]) for r in wv} != {("result wrong or missing", True)}:
        _X_stop("X-1 legend: wrong values holds other kinds")
    wv_err = Counter(r["exec_outcome"] for r in wv if r["exec_outcome"] != "ok")
    raised_nr = sorted({r["exec_outcome"] for r in nr if r["fail_kind"] == "code raised or timed out"},
                       key=list(_X_EO_WORDS).index)
    ran_nr = {r["exec_outcome"] for r in nr if r["fail_kind"] == "result wrong or missing"}
    if set(wv_err) - set(_X_EO_WORDS) or ran_nr - {"ok"} or \
            {r["fail_kind"] for r in nr} - {"code raised or timed out", "result wrong or missing"}:
        _X_stop("X-1 legend: an exec_outcome or kind the words do not cover")
    w = "Wrong values: the code returned values that did not match the reference"
    if wv_err and not short:           # the short form leaves this to Source Data Fig. 6's caption (_X_wrong_error_clause)
        w += (f" ({sum(wv_err.values())} of these {len(wv)} also "
              f"{_X_join([_X_EO_WORDS[e] for e in _X_EO_WORDS if e in wv_err])})")
    if short:                          # every no-result attempt returned no values (the guard above holds it)
        w += ". No result: the code returned no values"
    else:
        w += f". No result: the code {_X_join([_X_EO_WORDS[e] for e in raised_nr])} and returned no values"
        if ran_nr:
            w += ", or ran without error and returned none"
    kinds = {r['fail_kind'] for r in tcf}
    w += f". Tool or call failure, other: {_X_kinds_short(kinds) if short else _X_kinds_words(kinds)}."
    return w


def _X_wrong_error_clause(D):
    """The clause Figure 6c's legend leaves out (FF32), for sheet Fig. 6c's caption words: the wrong-values attempts
    whose code also raised an error, timed out or failed its step."""
    wv = [r for r in D.rows if not r["passed"] and r["outcome"] == "wrong values"]
    err = Counter(r["exec_outcome"] for r in wv if r["exec_outcome"] != "ok")
    if set(err) - set(_X_EO_WORDS):
        _X_stop(f"Fig. {S447.FIG_N}c caption: an exec_outcome the words do not cover")
    if not err:
        return ""
    return (f"Of the {len(wv)} wrong-values attempts, {sum(err.values())} also "
            f"{_X_join([_X_EO_WORDS[e] for e in _X_EO_WORDS if e in err])}.")


# ---- X-2 (Supplementary, model by model): free-form and structured pass rate per variant and dataset (alt2); the
# dataset split lives here since Figure 6c shows the model groups (FF32) ----------------------------------------------
SIZE_X2 = (183.0, 77.36)


def draw_X2(D, F, S):
    X = _X_data(D)
    W, H = SIZE_X2
    cnt, GAPD = X["cnt"], X["GAPD"]
    rows_y, heads, NR = _X_rows_y(X)
    LAB = max(tw(vlabel(v)) for v in D.VARS) + 2.0
    GAPW = tw("−76.7") + 1.5                     # the draft's gap column, as wide as its widest text
    ROWH, HEAD_Y = 3.9, 10.5
    TOP = HEAD_Y + 3.4 + 1.2
    PH = ROWH * NR
    if abs(TOP + PH + 10.0 - H) > 1e-9:
        raise SystemExit(f"X2: the layout needs {TOP + PH + 10.0:.2f} mm, the panel is {H} mm high")
    F.letter()
    rate = lambda c: 100.0 * c[0] / c[1]
    idx = {}
    for d in DSETS:
        for v, b, _ in rows_y:
            ff, st = cnt[("v_d_f", v, d, "free-form")], cnt[("v_d_f", v, d, "structured")]
            g = GAPD[d][v]
            idx[(d, v)] = S.add(dataset=DHEAD[d], block=b, variant=vlabel(v), variant_id=v,
                                free_form_passes=ff[0], free_form_attempts=ff[1], free_form_pass_rate_pct=rate(ff),
                                structured_passes=st[0], structured_attempts=st[1], structured_pass_rate_pct=rate(st),
                                structured_minus_free_form_points=g, free_form_minus_structured_points=-g)
    r0 = idx[(DSETS[0], rows_y[0][0])]
    ffn, stn = S.rows[r0]["free_form_attempts"], S.rows[r0]["structured_attempts"]
    if {(r["free_form_attempts"], r["structured_attempts"]) for r in S.rows} != {(ffn, stn)}:
        raise SystemExit("X2: the key's n is not every dot's n")
    gap = 2.0
    cw = (W - LAB - 2 * GAPW - gap - 1.0) / 2
    # house key: free-form a filled blue circle (as Figure 6b), centred over the two dataset columns
    (k1, k2), _ = hkey(F, [("mark", (FCOL["free-form"], FMARK["free-form"]), f"free-form (n = {ffn})"),
                           ("mark", (FCOL["structured"], FMARK["structured"]), f"structured (n = {stn})")],
                       LAB + (2 * cw + GAPW + gap) / 2, PT_LETTER * MMPT)
    S.num(k1, r0, "free-form (n = {free_form_attempts})")
    S.num(k2, r0, "structured (n = {structured_attempts})")
    r_ring_mm = S447.ms_pt(1.5) * MMPT / 2              # the filled circle's radius (house: 1.5 mm marks)
    for j, d in enumerate(DSETS):
        x = LAB + j * (cw + GAPW + gap)
        ax = F.axes(x, TOP, cw, PH)
        ax.set_xlim(-3, 103)
        ax.set_ylim(NR - 0.5, -0.5)
        r_ring = r_ring_mm * 106 / cw
        for v, _, y in rows_y:
            ri = idx[(d, v)]
            ff, st = S.rows[ri]["free_form_pass_rate_pct"], S.rows[ri]["structured_pass_rate_pct"]
            if abs(st - ff) > r_ring:
                step = r_ring if st > ff else -r_ring
                ax.plot([ff + step, st], [y, y], color=hs.GREY["line"], lw=hs.LW["connector"], zorder=2,
                        solid_capstyle="butt")
            # house: free-form a filled circle, drawn under the structured diamond so both show where they meet
            sm = ax.plot(st, y, ls="none", marker=FMARK["structured"], ms=S447.ms_pt(1.5), mfc=FCOL["structured"],
                         mec="#FFFFFF", mew=0.3, zorder=6)[0]
            fm = ax.plot(ff, y, ls="none", marker=FMARK["free-form"], ms=S447.ms_pt(1.5), mfc=FCOL["free-form"],
                         mec="#FFFFFF", mew=0.3, zorder=5)[0]
            S.check(f"{d} {v} structured", [ri], "structured_pass_rate_pct", sm.get_xdata())
            S.check(f"{d} {v} free-form", [ri], "free_form_pass_rate_pct", fm.get_xdata())
            g = S.rows[ri]["structured_minus_free_form_points"]
            txt = S447.half_up(g, 1, sign=True)
            if txt.startswith("-"):
                txt, fmt = "−" + txt[1:], "−{free_form_minus_structured_points:.1f}"
            else:
                fmt = "{structured_minus_free_form_points:+.1f}"
            t = ax.text(103 + 1.0 * 106 / cw, y, txt, va="center", ha="left", fontsize=PT, clip_on=False)
            S.num(t, ri, fmt)
        ax.set_yticks([y for _, _, y in rows_y], [vlabel(v) for v, _, _ in rows_y] if j == 0 else [])
        ax.set_xticks([0, 50, 100])
        _X_strip_y(ax)
        F.text(x, HEAD_Y, DHEAD[d], va="baseline", ha="left")
        F.text(x + cw + GAPW, HEAD_Y + 3.4, "gap (percentage points)", va="baseline", ha="right", color=GREY_NOTE)
        if j == 0:
            for b, y in heads:
                F.text(0.5, TOP + PH * (y + 0.5) / NR, b, va="center", ha="left", color=GREY_NOTE)
    F.text(LAB + (2 * cw + GAPW + gap) / 2, H - 2.0, "Pass rate (%)", va="baseline", ha="center")
    nd = len(D.OPS) // len(DSETS)
    # Valerio, 8 Nov (editor row 45): pass rates with no spread drawn derive no statistics, so no n tag; the attempt
    # counts stay in words and the rows are written out (no reference to another panel)
    if ffn % nd or stn % nd:
        raise SystemExit(f"X2 legend: {ffn} free-form or {stn} structured attempts are not whole strategies of {nd} "
                         f"operations")
    rows = _rows_words16(D)
    return {"legend": (f"Pass rate per model variant and dataset (left, {DHEAD[DSETS[0]]}; right, "
                       f"{DHEAD[DSETS[1]]}; {nd} operations each) under free-form (circle; {ffn // nd} "
                       f"strategies, {ffn} attempts) and structured prompting (diamond; {stn // nd} strategies, {stn} "
                       f"attempts), joined by a grey line where the diamond's centre lies outside the circle. Gap, "
                       f"structured minus free-form (percentage points). {rows}")}


# ---- X-3 (Supplementary, difficulty in detail): operations by tier and family, per dataset (alt3) ----------------
SIZE_X3 = (183.0, 63.5)
# draw_X.py drew no median bar over 2 operations. Every group now draws a box (Valerio, 28 Oct), so this only sets which
# box medians draw_X3 holds to numpy's: a box over 2 operations has their mean as its median.
_X_MIN_OPS_MEDIAN = 3


def draw_X3(D, F, S):
    X = _X_data(D)
    W, H = SIZE_X3
    cnt, ops_dt = X["cnt"], X["ops_dt"]
    HEAD_Y, TOP, PH = 10.0, 13.0, 40.0
    if abs(TOP + PH + 10.5 - H) > 1e-9:
        raise SystemExit(f"X3: the layout needs {TOP + PH + 10.5:.2f} mm, the panel is {H} mm high")
    F.letter()
    YL, gap = 12.5, 6.0
    cw = (W - YL - gap - 1.0) / 2
    hkey(F, [("mark", (FCOL[f], FMARK[f]), f) for f in FAMS], YL + cw + gap / 2, PT_LETTER * MMPT)   # house key
    DOT = 1.0                                         # house: 1.0 mm for 30 or fewer values (was 1.35)
    tier_row = {(d, t): S.add(part="tier", dataset=DHEAD[d], tier=t, n_operations=len(ops_dt[(d, t)]))
                for d in DSETS for t in TIERS}
    for j, d in enumerate(DSETS):
        x = YL + j * (cw + gap)
        ax = F.axes(x, TOP, cw, PH)
        ax.set_ylim(0, 100)
        ax.set_xlim(-0.6, 10.9)
        mm_y, mm_x = PH / 100, cw / 11.5
        for ti, t in enumerate(TIERS):
            for fi, f in enumerate(FAMS):
                x0 = ti * 4 + fi * 1.15
                ri, vals = [], []
                for o in ops_dt[(d, t)]:
                    p, n = cnt[("o_f", o, f)]
                    vals.append(100.0 * p / n)
                    ri.append(S.add(part="operation", dataset=DHEAD[d], tier=t, family=f, operation=o, passes=p,
                                    attempts=n, pass_rate_pct=100.0 * p / n))
                # Valerio, 28 Oct: "Make panel b with boxplots overlayed over": the house box over every group's
                # dots, whatever its number of operations (STYLE.md's exception to the fewer-than-5 rule)
                st, art = _hbox(ax, x0, vals, colour=FCOL[f], marker=FMARK[f], dot_mm=DOT, slot=1.15)
                dl = art["dots"]
                S.check(f"{d} {t} {f} dots", ri, "pass_rate_pct", dl.get_ydata())
                if len(vals) >= _X_MIN_OPS_MEDIAN and abs(st["median"] - float(np.median(vals))) > 1e-12:
                    raise SystemExit(f"X3: {d} {t} {f} box median is not numpy's median")
                mi = S.add(part="box", dataset=DHEAD[d], tier=t, family=f, n_operations=len(vals),
                           median_pct=st["median"], q1_pct=st["q1"], q3_pct=st["q3"], min_pct=st["whisker_low"],
                           max_pct=st["whisker_high"])
                rq1, rmed, rq3, rlo, rhi = _hbox_read(art)
                for col_, got_ in (("q1_pct", rq1), ("median_pct", rmed), ("q3_pct", rq3), ("min_pct", rlo),
                                   ("max_pct", rhi)):
                    S.check(f"{d} {t} {f} {col_}", [mi], col_, [got_])
        ax.set_xticks([ti * 4 + 1.15 for ti in range(3)])
        labs = ax.set_xticklabels([f"{t}\n(n = {len(ops_dt[(d, t)])} operations)" for t in TIERS])
        for lab, t in zip(labs, TIERS):              # each tick label's count is its tier row's n_operations
            S.num(lab, tier_row[(d, t)], "{tier}\n(n = {n_operations} operations)")
        ax.tick_params(axis="x", length=0)
        ax.set_yticks([0, 25, 50, 75, 100])
        if j:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("Pass rate (%)", labelpad=2)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        F.text(x, HEAD_Y, DHEAD[d], va="baseline", ha="left")
    per = {f: cnt[("o_f", D.OPS[0], f)][1] for f in FAMS}
    return {"legend": (f"Pass rate of each operation under each prompting family, all {len(D.VARS)} model variants "
                       f"pooled, by task difficulty, for each dataset. One mark per operation: its share of "
                       f"{per['free-form']} free-form, {per['introspection']} introspection or {per['structured']} "
                       f"structured attempts passed. Box: median and quartiles over the operations; whiskers: range. "
                       f"n: operations per difficulty, under each group.")}


# ---- X-4 (Supplementary, failures per model): failed attempts per variant and family, six groups (alt4) ----------
SIZE_X4 = (183.0, 90.66)                   # Valerio, 28 Oct (Supplementary 15 O1): the columns fill 183 mm


def draw_X4(D, F, S):
    X = _X_data(D)
    W, H = SIZE_X4
    cnt, g6 = X["cnt"], X["g6"]
    rows_y, heads, NR = _X_rows_y(X)
    LAB = max(tw(vlabel(v)) for v in D.VARS) + 2.0
    F.letter()
    gap = 6.0
    cw = (W - LAB - 3.0 - 2 * gap) / 3
    # house key: swatches with their patterns, centred over the three columns, wrapped inside the slot
    cx = LAB + (3 * cw + 2 * gap) / 2
    _, klines = hkey(F, [("swatch", (col, pat or None), lab) for lab, col, pat in _X_G6], cx, PT_LETTER * MMPT,
                     max_width=_X_key_room(F, cx))
    HEAD_Y = klines[-1][2] - F.oy + 5.4
    TOP = HEAD_Y + 3.4 + 1.5
    BH = H - 10.0 - TOP                               # the rows fill the slot
    ROWH = BH / NR
    if ROWH < 4.0:
        raise SystemExit(f"X4: rows of {ROWH:.2f} mm")
    for j, f in enumerate(FAMS):
        x = LAB + j * (cw + gap)
        ax = F.axes(x, TOP, cw, BH)
        ax.set_xlim(0, 100)
        ax.set_ylim(NR - 0.5, -0.5)
        nn = {cnt[("v_f", v, f)][1] for v in D.VARS}
        if len(nn) != 1:
            raise SystemExit(f"X4: {f} attempts differ between variants: {nn}")
        nn = nn.pop()
        first = None
        for v, b, y in rows_y:
            left = 0.0
            for g, col, pat in _X_G6:
                k = g6[(v, f, g)]
                w_ = 100.0 * k / nn
                ri = S.add(block=b, variant=vlabel(v), variant_id=v, family=f, failure_group=g, attempts_failed=k,
                           attempts=nn, share_pct=w_, start_pct=left)
                first = ri if first is None else first
                if w_:
                    rect = _X_bar(F, ax, y, left, w_, col, pat)
                    S.check(f"{v} {f} {g} width", [ri], "share_pct", [rect.get_width()])
                    S.check(f"{v} {f} {g} start", [ri], "start_pct", [rect.get_x()])
                left += w_
            if left > 100.0 + 1e-9 or abs(left - 100.0 * (nn - cnt[("v_f", v, f)][0]) / nn) > 1e-9:
                raise SystemExit(f"X4: {v} {f}: the groups hold {left:.3f}%, not the failed share")
        ax.set_yticks([y for _, _, y in rows_y], [vlabel(v) for v, _, _ in rows_y] if j == 0 else [])
        ax.set_xticks([0, 50, 100])
        _X_strip_y(ax)
        F.text(x, HEAD_Y, f, va="baseline", ha="left")
        t = F.text(x, HEAD_Y + 3.4, f"n = {nn}", va="baseline", ha="left")
        S.num(t, first, "n = {attempts}")
        if j == 0:
            for b, y in heads:
                F.text(0.5, TOP + BH * (y + 0.5) / NR, b, va="center", ha="left", color=GREY_NOTE)
    F.text(LAB + (3 * cw + 2 * gap) / 2, H - 2.0, "Attempts failed (% of n)", va="baseline", ha="center")
    n = {f: cnt[("v_f", D.VARS[0], f)][1] for f in FAMS}
    kinds = defaultdict(set)                          # the fail kinds each group holds in this panel
    for r in D.rows:
        if not r["passed"]:
            kinds[_X_group6(r)].add(r["fail_kind"])
    if kinds["tools refused by Ollama"] - {_X_REFUSED}:
        _X_stop("X-4 legend: the tool refusal group holds other kinds")
    # Valerio, 8 Nov (editor row 45): no statistics are derived here, so no n tag; every term written out, no
    # reference to another figure. The family sizes are counted from the rows (nn per family above, one per
    # strategy and operation), so the words cannot drift from the plate.
    per_f = {f: n[f] // len(D.OPS) for f in FAMS}
    if any(per_f[f] * len(D.OPS) != n[f] for f in FAMS):
        _X_stop(f"X-4 legend: a family's attempts are not whole strategies of {len(D.OPS)} operations: {n}")
    return {"legend": (f"Each bar is the share of one model variant's attempts (row) that failed under one prompting "
                       f"family (column: free-form, {per_f['free-form']} strategies; introspection, "
                       f"{per_f['introspection']}; structured, {per_f['structured']}), one attempt per strategy and "
                       f"operation; x axis, attempts failed as a percentage of that variant's attempts in that family. The bar is split by kind of failure (colour and "
                       f"pattern, key above). Wrong values: the code returned values that did not match the "
                       f"reference. No result: the code returned no values. Length stop: the reply filled its "
                       f"context or output cap. Tools refused by Ollama: the model as served has no tool support. "
                       f"Other tool or call failure: {_X_kinds_words(kinds['other tool or call failure'])}. Other: "
                       f"{_X_kinds_words(kinds['other (harness, no code)'])}. Rows: {D.blocks[0][0]}, then "
                       f"{D.blocks[1][0]}, each ordered high to low by free-form pass rate, ties by pass rate over "
                       f"all {len(D.STRATS)} strategies. {_gemini_low()}")}


# ---- panels B ----------------------------------------------------------------------------------------------------------------
# ---- Family B: repeated attempts against a single attempt, paired by variant and operation (draw_B.py, D138) -------
# B1 (Figure 7d until D299, 7 Nov; since then Supplementary Figure 15f, drawn by draw_B4 in the slot beside e): the
# five repeated-attempt contrasts as a forest (draw_B1_plate_v3.py), and as rows not drawn the
# contrasts of every other strategy against free-form with their Gemini and open-weight boxes' statistics (D222: the
# values of B1b, Supplementary Figure 22 until 3 Nov, which drew them). B4 (Supplementary 23): every pair of the five contrasts as a tile, panel letters a to e (draw_B.py tiles()). Each contrast pairs the same variant and operation (11 x 20 = 220 pairs):
# rescued (base failed, arm passed), lost (base passed, arm failed), net = 100 (rescued - lost) / 220 points, its 95%
# percentile interval resampling the 20 operations (boot_interval(), coverage_check.py's), and cost multiples = summed
# arm / summed base over the 220 pairs for generator calls, wall time and output tokens.
# D299 (Valerio, 7 Nov, "O1"): B1 is no longer a panel of its own (no SIZE_B1, so _collect_panels() does not list it);
# draw_B4 draws it as Supplementary Figure 15f in the slot right of e, under d, at that slot's size. Upright since
# 4 Nov (Valerio): five two-line strategy names side by side, unrotated.

_B_MAIN = [("free_form_n3_best", "free_form"), ("free_form_n3_combined", "free_form"),
           ("coder_v2_n1_cell3_best", "coder_v2_n1"), ("coder_v2_n1_cell3_combined", "coder_v2_n1"),
           ("coder_v2_n3", "coder_v2_n1")]
_B_COSTS = ["generator_calls", "latency_s", "output_tokens"]
# The reproduce gate's reference: the drafts' own stored numbers (draw_B.py's B_numbers.json, 24 October: all 13
# contrasts, computed by another script from ../attempts.csv, which prep.py wrote from the mirror). Its committed home
# is _B_REFS[0], committed beside G4_numbers.json; missing, the run stops. The file read and its sha256 go into the provenance (D.inputs).
_B_REFS = [ROOT / "findings/recompute/fig6_options_2026-10-25/B_numbers.json"]
_B_HF = 0.6                              # a group header line, as a share of a row
_B_MINUS = "−"
_B_TIMES = "×"
_B_CACHE = {}


def _B_ms(mm):
    return mm / MMPT


def _B_tick(t):
    return "0" if not t else f"{t:+d}".replace("-", _B_MINUS)


def _B_contrast(VARS, OPS, idx, arm, base):
    """One contrast of family B: every (variant, operation) pair of base's attempt and arm's attempt, classed rescued,
    lost, both passed or both failed, in total and per variant (D225 Q3: the per-variant both passed and both failed
    from the same pairs as its rescued and lost), with the net, its interval and the cost sums."""
    c = {"arm": arm, "base": base, "rescued": 0, "lost": 0, "both_pass": 0, "both_fail": 0, "tiles": {},
         "per_variant": {}}
    per_op = defaultdict(list)
    sums = {k: [0.0, 0.0] for k in _B_COSTS}
    for v in VARS:
        pv = {"rescued": 0, "lost": 0, "both_pass": 0, "both_fail": 0}
        for o in OPS:
            a, b = idx[(v, base, o)], idx[(v, arm, o)]
            pa, pb = a["passed"], b["passed"]
            kind = ("rescued" if pb else "both_fail") if not pa else ("both_pass" if pb else "lost")
            c[kind] += 1
            c["tiles"][(v, o)] = kind
            pv[kind] += 1
            per_op[o].append(pb - pa)
            for k in _B_COSTS:
                x, y = a[k], b[k]
                if x is None or y is None:
                    raise SystemExit(f"NOT REPRODUCED: no {k} for {v} {o} ({base} or {arm}); draw_B.py had a "
                                     f"value on every row")
                sums[k][0] += float(x)
                sums[k][1] += float(y)
        pv["gain_points"] = 100 * (pv["rescued"] - pv["lost"]) / len(OPS)
        c["per_variant"][v] = pv
    n = len(VARS) * len(OPS)
    c["n_pairs"] = n
    c["net_points"] = 100 * (c["rescued"] - c["lost"]) / n
    c["interval_95_ops"] = boot_interval({o: 100 * sum(x) / len(x) for o, x in per_op.items()})
    c["cost_multiple_of_sums"] = {k: sums[k][1] / sums[k][0] for k in _B_COSTS}
    c["cost_sums"] = {k: {"base": sums[k][0], "arm": sums[k][1]} for k in _B_COSTS}
    return c


_B_KINDS = ("rescued", "lost", "both_pass", "both_fail")


def _B_variant_identity(c, n_ops):
    """D225 Q3: every variant's four kinds add up to its n_ops pairs, and summed over the variants each kind equals the
    contrast's total. Returns the list of what fails (empty when the identity holds)."""
    bad = [f"{v}: {sum(pv[k] for k in _B_KINDS)} pairs, not {n_ops}" for v, pv in c["per_variant"].items()
           if sum(pv[k] for k in _B_KINDS) != n_ops]
    bad += [f"{k}: variants sum to {sum(pv[k] for pv in c['per_variant'].values())}, the contrast has {c[k]}"
            for k in _B_KINDS if sum(pv[k] for pv in c["per_variant"].values()) != c[k]]
    return bad


def _B_data(D):
    """The contrasts of family B, computed once per Data from D.rows, with draw_B.py's reproduce gates."""
    if id(D) in _B_CACHE:
        return _B_CACHE[id(D)]
    VARS, OPS, STRATS, idx = D.VARS, D.OPS, D.STRATS, D.idx
    got = (len(D.rows), sum(r["passed"] for r in D.rows))
    if got != tuple(WANT):
        raise SystemExit(f"NOT REPRODUCED: the rows give {got}, Figure {S447.FIG_N} has {tuple(WANT)}")
    if (len(VARS), len(OPS), len(STRATS), len(idx)) != (11, 20, 11, len(D.rows)):
        raise SystemExit(f"NOT REPRODUCED: {len(VARS)} variants, {len(OPS)} operations, {len(STRATS)} strategies, "
                         f"{len(idx)} distinct attempts; draw_B.py had 11, 20, 11 and one per row")

    def contrast(arm, base):
        return _B_contrast(VARS, OPS, idx, arm, base)

    all_ff = [(s, "free_form") for s in STRATS if s != "free_form"]
    C = {k: contrast(*k) for k in _B_MAIN + all_ff}
    # REPRODUCE: every contrast equal to the drafts' stored B_numbers.json (an independent computation, see _B_REFS)
    ref_path = next((p for p in _B_REFS if p.is_file()), None)
    if ref_path is None:
        raise SystemExit(f"NOT REPRODUCED: no reference for family B; copy the drafts' B_numbers.json to {_B_REFS[0]}")
    ref = json.loads(ref_path.read_text())["contrasts"]
    if set(ref) != {f"{a} vs {b}" for a, b in C}:
        raise SystemExit(f"NOT REPRODUCED: contrasts {sorted(f'{a} vs {b}' for a, b in C)}, B_numbers.json has "
                         f"{sorted(ref)}")
    for (arm, base), c in C.items():
        r = ref[f"{arm} vs {base}"]
        diffs = [k for k in ("n_pairs", "rescued", "lost", "both_pass", "both_fail") if c[k] != r[k]]
        if round(c["net_points"], 2) != r["net_points"]:
            diffs.append("net_points")
        if list(c["interval_95_ops"]) != list(r["interval_95_ops"]):
            diffs.append("interval_95_ops")
        for k in _B_COSTS:
            if round(c["cost_multiple_of_sums"][k], 3) != r["cost_multiple_of_sums"][k]:
                diffs.append(f"cost_multiple_of_sums {k}")
            for side in ("base", "arm"):
                want = r["cost_sums"][k][side]
                if abs(c["cost_sums"][k][side] - want) > 1e-9 * max(1.0, abs(want)):
                    diffs.append(f"cost_sums {k} {side}")
        for v in VARS:
            rv, mv = r["per_variant"][S447.short_variant(v)], c["per_variant"][v]
            if (mv["rescued"], mv["lost"]) != (rv["rescued"], rv["lost"]) or \
                    abs(mv["gain_points"] - rv["gain_points"]) > 1e-9:
                diffs.append(f"per_variant {v}")
        if diffs:
            raise SystemExit(f"NOT REPRODUCED: {arm} vs {base} differs from {ref_path.name} in {diffs}")
    # REPRODUCE, counted a second way: for every contrast, the arm's and the base's passes (D.summary, the core's
    # count() over D.rows) equal both-passed plus rescued and both-passed plus lost, and the four kinds add up to n
    for (arm, base), c in C.items():
        pa = sum(D.summary["per_variant"][v]["by_strategy"][arm][0] for v in VARS)
        pb = sum(D.summary["per_variant"][v]["by_strategy"][base][0] for v in VARS)
        if (c["both_pass"] + c["rescued"], c["both_pass"] + c["lost"],
                c["rescued"] + c["lost"] + c["both_pass"] + c["both_fail"]) != (pa, pb, c["n_pairs"]):
            raise SystemExit(f"NOT REPRODUCED: {arm} against {base}: the pair kinds give {pa} and {pb} passes "
                             f"otherwise, or do not add up to {c['n_pairs']}")
    # internal consistency, not a reproduction: the five contrasts equal the core's own D.cov["gap_best_of_3"]
    # (_coverage(), from the same D.rows), which other panels read
    for arm, base in _B_MAIN:
        c, ref = C[(arm, base)], D.cov["gap_best_of_3"][f"{arm} vs {base}"]
        mine = {"n_pairs": c["n_pairs"], "rescued": c["rescued"], "lost": c["lost"], "both_pass": c["both_pass"],
                "both_fail": c["both_fail"], "net_points": round(c["net_points"], 1),
                "interval_95_ops": list(c["interval_95_ops"]),
                "cost_multiple_of_sums": {k: round(c["cost_multiple_of_sums"][k], 2) for k in _B_COSTS},
                "per_variant": {v: {"rescued": c["per_variant"][v]["rescued"], "lost": c["per_variant"][v]["lost"]}
                                for v in VARS}}
        theirs = {k: ref[k] for k in mine}
        theirs["interval_95_ops"] = list(ref["interval_95_ops"])
        theirs["cost_multiple_of_sums"] = {k: ref["cost_multiple_of_sums"].get(k) for k in _B_COSTS}
        if mine != theirs:
            raise SystemExit(f"B: {arm} vs {base} differs from the core's D.cov\n mine   {mine}\n theirs {theirs}")
    print(f"B reproduced: {len(C)} contrasts equal to {ref_path} (sha256 {sha(ref_path)[:12]}) and to the pass "
          f"counts of D.summary")
    out = {"C": C, "groups_main": [("against free-form", _B_MAIN[:2]), ("against structured", _B_MAIN[2:])],
           "groups_all": [("against free-form", all_ff), ("against structured", _B_MAIN[2:])]}
    _B_CACHE[id(D)] = out
    return out


def _B_marker(ax, x, y, v, d_mm, col):
    """draw_B.py's variant_marker(): Gemini filled, open-weight open, both in col (the forest's g["dot"])."""
    if is_gemini(v):
        return ax.plot(x, y, "o", ms=_B_ms(d_mm), mfc=col, mec=col, mew=0.4, ls="", zorder=5)[0]
    return ax.plot(x, y, "o", ms=_B_ms(d_mm - 0.15), mfc="#FFFFFF", mec=col, mew=0.5, ls="", zorder=5)[0]


def _B_forest(D, F, S, groups, g):
    """draw_B.py forest() (CENTRE "mean", no counts beside squeezed stacks), turned upright (Valerio, 4 Nov: "the
    strategies are x-axis and the change in pass rate is y-axis", to fill the slot's height): one column per contrast,
    its strategy's name under the axis, each group's name over its columns with a rule, the change in pass rate up the
    y axis, the zero line horizontal. Every value, mark and colour as the forest of B1 plate v3."""
    import math
    from matplotlib.colors import to_hex
    B = _B_data(D)
    C, VARS, SLAB = B["C"], D.VARS, D.SLAB
    W, H = g["size"]
    lab_w, plot_w, head_h, foot_h = g["lab_w"], g["plot_w"], g["head_h"], g["foot_h"]
    dot_mm, pitch_mm = g["dot_mm"], g["pitch_mm"]
    n_cols = sum(len(gg) for _, gg in groups)
    col_mm = plot_w / n_cols
    plot_h = H - head_h - foot_h
    if plot_h <= 0 or lab_w + plot_w > W + 1e-6:
        raise SystemExit(f"B forest: {lab_w + plot_w:.2f} x {head_h + foot_h:.2f} mm around the plot, the slot {W} x {H}")
    F.letter(g.get("letter_x", 0.0))
    ax = F.axes(lab_w, head_h, plot_w, plot_h)
    dots, diam, ints, first_row = [], [], [], None
    vals, labels, heads = [], [], []
    off = g["line_off_mm"] / col_mm                      # the interval's column offset right of the column centre
    x = 0
    for gname, items in groups:
        x0, x1 = x - 0.5, x - 0.5 + len(items)
        heads.append((ax.text((x0 + x1) / 2, 1 + g["head_text_mm"] / plot_h, gname,
                              transform=ax.get_xaxis_transform(), ha="center", va="baseline", color=GREY_NOTE,
                              fontstyle="italic", clip_on=False),
                      ax.plot([x0 + 0.08, x1 - 0.08], [1 + g["head_rule_mm"] / plot_h] * 2, color=GREY_NOTE,
                              lw=hs.LW["reference"], solid_capstyle="butt", transform=ax.get_xaxis_transform(),
                              clip_on=False)[0]))
        for arm, base in items:
            c = C[(arm, base)]
            lo, hi = c["interval_95_ops"]
            row = dict(part="contrast", strategy=SLAB[arm], against=SLAB[base], variant=None, model=None,
                       setting=None, gemini=None, n_pairs=c["n_pairs"], rescued=c["rescued"], lost=c["lost"],
                       both_passed=c["both_pass"], both_failed=c["both_fail"], n_operations=None,
                       change_pct_points=None, net_change_pct_points=c["net_points"],
                       interval_95_low_pct_points=lo, interval_95_high_pct_points=hi)
            ri = S.add(**row)
            if first_row is None:
                first_row = ri
            xc = x + off                                     # the interval line; dots stacked leftward from it
            ea = hs.estimate(ax, xc, c["net_points"], lo, hi, orient="v", marker_="D")   # house estimate: black
            ln, dm = ea["interval"], ea["mark"]                                      # diamond on a 0.9 pt line
            ints.append((ri, ln))
            diam.append((ri, dm))
            vrow = {}
            for v in VARS:
                pv = c["per_variant"][v]
                vrow[v] = S.add(part="variant", strategy=SLAB[arm], against=SLAB[base], variant=vlabel(v),
                                model=S447.VMODEL[v], setting=setting_label(v), gemini=int(is_gemini(v)),
                                rescued=pv["rescued"], lost=pv["lost"], n_operations=len(D.OPS),
                                change_pct_points=pv["gain_points"])
            grp = defaultdict(list)
            for v in VARS:
                grp[c["per_variant"][v]["gain_points"]].append(v)
            band = col_mm / 2 + g["line_off_mm"] - 1.0 - dot_mm - 0.4   # room left of the line, in mm
            for yv, vv in grp.items():
                vv.sort(key=lambda v: (not is_gemini(v), VARS.index(v)))
                k = len(vv)
                step = pitch_mm if (k - 1) * pitch_mm <= band else band / max(k - 1, 1)
                for j, v in enumerate(vv):
                    dots.append((vrow[v], v, _B_marker(ax, xc - (1.0 + dot_mm / 2 + j * step) / col_mm, yv, v,
                                                       dot_mm, g["dot"])))
                vals.append(yv)
            vals += [lo, hi]
            a_, _, b_ = SLAB[arm].partition(" ")
            t = ax.text(x, -g["label_pad_mm"] / plot_h, f"{a_}\n{b_}" if b_ else a_, transform=ax.get_xaxis_transform(),
                        ha="center", va="top", multialignment="center", linespacing=1.0)
            labels.append((ri, t))
            if re.search(r"\d", t.get_text()):
                S.book.fixed(t, "a strategy's name, not a number of the data")
            x += 1
    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_xticks([])
    lo = 10 * math.floor(min(vals) / 10)
    hi = 10 * math.ceil(max(vals) / 10)
    lo, hi = min(lo, -10), max(hi, 10)
    ax.set_ylim(lo - 2, hi + 2)
    step = 10 if hi - lo <= 50 else 20
    ax.set_yticks(range(int(math.ceil(lo / step) * step), int(hi) + 1, step))
    ax.set_yticklabels([_B_tick(t) for t in ax.get_yticks().astype(int)])
    hs.reference_line(ax, 0, orient="h")              # house: zero line black 0.5 pt
    ax.set_ylabel(g["ylabel"], labelpad=2, linespacing=1.1)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    # the key (Gemini filled, open-weight open, the net with its interval)
    first = S.rows[first_row]
    labs = [g["key"][0].format(count=sum(map(is_gemini, VARS))),
            g["key"][1].format(count=sum(not is_gemini(v) for v in VARS))]
    items = [("mark", (g["dot"], "o"), labs[0]), ("open", (g["dot"], "o"), labs[1])]
    if len(g["key"]) > 2:                             # a third entry: the net as a black diamond on its interval
        labs.append(_B_fill(g["key"][2], first))
        items.append(("estimate", None, labs[2]))
    # house key: centred over the plot, wrapped inside the slot
    cx = lab_w + plot_w / 2
    lt, _ = hkey(F, items, cx, PT_LETTER * MMPT, max_width=2 * min(cx, W - cx) - 0.4, diamond=True)
    where = {"part": "variant", "strategy": first["strategy"], "against": first["against"]}
    S.count(lt[0], {**where, "gemini": 1}, g["key"][0])
    S.count(lt[1], {**where, "gemini": 0}, g["key"][1])
    if len(g["key"]) <= 2:
        pass                                          # 3 Nov (Valerio): the net and its interval are the legend's
    elif "{" in g["key"][2]:
        S.num(lt[2], first_row, g["key"][2])
    else:
        S.book.fixed(lt[2], "the interval's coverage (95%), not a number of the data")
    # read-back: every dot at its variant's change and filled for Gemini, every diamond at its net, every interval's
    # ends at the workbook's interval
    S.check("variant dot, y (change in points)", [r for r, _, _ in dots], "change_pct_points",
            [m.get_ydata()[0] for _, _, m in dots])
    S.check("variant dot, filled (Gemini)", [r for r, _, _ in dots], "gemini",
            [1.0 if to_hex(m.get_markerfacecolor()) != "#ffffff" else 0.0 for _, _, m in dots])
    S.check("net diamond, y", [r for r, _ in diam], "net_change_pct_points", [m.get_ydata()[0] for _, m in diam])
    S.check("interval line, low end", [r for r, _ in ints], "interval_95_low_pct_points",
            [min(ln.get_ydata()) for _, ln in ints])
    S.check("interval line, high end", [r for r, _ in ints], "interval_95_high_pct_points",
            [max(ln.get_ydata()) for _, ln in ints])
    # placement read-back: every dot, diamond and interval lies in the column of its own contrast. The column is read
    # from the drawn strategy name (a column spans 0.5 either side of the name's centre, in columns) and the
    # comparison from the group rule drawn over it; both must equal the sheet row's strategy and "against". A dot
    # stacked past its column stops the run.
    slots = [(t.get_position()[0] - 0.5, t.get_position()[0] + 0.5, t.get_text().replace("\n", " ")) for _, t in
             labels]
    spans = [(min(r.get_xdata()) - 0.08, max(r.get_xdata()) + 0.08, h.get_text()) for h, r in heads]
    def read_col(xv):
        hit = [nm for a, b, nm in slots if a - 1e-9 <= xv < b]
        over = [nm for a, b, nm in spans if a - 1e-9 <= xv < b]
        if len(hit) != 1 or len(over) != 1:
            return None, None
        return hit[0], over[0]
    placed = ([(r, m.get_xdata()[0], "dot") for r, _, m in dots] + [(r, m.get_xdata()[0], "diamond") for r, m in diam]
              + [(r, xv, "interval") for r, ln in ints for xv in ln.get_xdata()])
    for r, xv, what in placed:
        got = read_col(xv)
        want = (S.rows[r]["strategy"], f"against {S.rows[r]['against']}")
        if got != want:
            raise SystemExit(f"B forest: a {what} of {want} is drawn in the column of {got}")
    print(f"B forest: {len(placed)} dots, diamonds and interval ends read back in their contrast's column")
    return B


def _B_fill(fmt, row):
    return S447.HALF_UP.format(fmt, **row)


# D161 (10) (F6-R r1, Valerio, 27 Oct): the variant dots, which carry no category, are black, as Supplementary Figure
# 23's variant marks are (draw_B4). D299: B1 is drawn by draw_B4 as Supplementary Figure 15f, at the slot's size.
def draw_B1(D, F, S, size, letter_x=0.0):
    B = _B_forest(D, F, S, _B_data(D)["groups_main"], {
        "size": size, "lab_w": 11.0, "plot_w": size[0] - 11.0 - 0.3, "head_h": 11.0, "foot_h": 8.5,
        "head_text_mm": 3.2, "head_rule_mm": 2.0, "label_pad_mm": 1.4, "line_off_mm": 2.6, "letter_x": letter_x,
        "dot_mm": 1.0, "pitch_mm": 1.1, "dot": OK["black"],
        "key": [figure_names.GEMINI + " ({count})", figure_names.OPEN_WEIGHT + " ({count})"],   # 3 Nov (Valerio): the net
        "ylabel": "Change in pass rate (points)"})                                             # and its interval: legend
    _B1_not_drawn(D, S, B)
    nv, no = len(D.VARS), len(D.OPS)
    # Valerio, 8 Nov (editor row 45): f draws derived statistics (the interval), so it states its n once; the panel
    # is described in full, with no reference to another panel.
    return {"legend": (f"change in pass rate (points) of each repeated-attempt strategy (column) over the "
                       f"single-attempt strategy of its family, same variant and operation. Dot, one variant over "
                       f"{no} operations (filled, Gemini; open, open-weight); diamond, net change over all pairs; line, "
                       f"two-sided 95% percentile interval from {BOOT_N:,} resamples of the {no} operations; "
                       f"n = {nv * no} pairs per strategy.")}


def _B1_not_drawn(D, S, B):
    """D222 and D224 Q6 (Valerio, 3 Nov): every value Supplementary Figure 22 (B1b) drew that the drawn rows of sheet
    Supplementary Fig. 15f (Fig. 6d until D299) do not hold, as rows after the drawn ones, nothing drawn from them, in B1b's order (every strategy against
    free-form, then the three repeated structured strategies against structured). For a contrast 23f does not draw
    (every strategy against free-form but the two 23f draws): a 'contrast (not drawn)' row (pairs, rescued, lost, both
    passed, both failed, the net and its 95% interval, as the drawn 'contrast' rows) and its 'variant (not drawn)' rows
    (per variant, B1b's columns: model, setting, Gemini or not, rescued, lost, operations and the change in points, as
    the drawn 'variant' rows; D224; and both passed and both failed from the same pairs, which add up with rescued and
    lost to the operations and over the variants to the contrast's four totals, else the run stops; D225 Q3). For every contrast, drawn or not: per model group (Gemini, open-weight) a 'box (not
    drawn)' row with the variants' change summarised as B1b's boxes were (hs.box_stats, whiskers to the range; D222
    the 16 of the contrasts not drawn, D224 the 10 of the five drawn)."""
    C, VARS, SLAB = B["C"], D.VARS, D.SLAB
    drawn = {k for _, items in B["groups_main"] for k in items}
    every = [k for _, items in B["groups_all"] for k in items]
    rest = [k for k in every if k not in drawn]
    if len(rest) != len(D.STRATS) - 1 - sum(1 for _, b in drawn if b == "free_form") or not drawn <= set(every) \
            or any(b != "free_form" for _, b in rest):
        raise SystemExit(f"23f not drawn: {len(rest)} contrasts against free-form left, {len(D.STRATS)} strategies")
    counts = defaultdict(int)
    for arm, base in every:
        c = C[(arm, base)]
        if (arm, base) not in drawn:
            lo_i, hi_i = c["interval_95_ops"]
            S.add(part="contrast (not drawn)", strategy=SLAB[arm], against=SLAB[base], variant=None, model=None,
                  setting=None, gemini=None, n_pairs=c["n_pairs"], rescued=c["rescued"], lost=c["lost"],
                  both_passed=c["both_pass"], both_failed=c["both_fail"], n_operations=None, change_pct_points=None,
                  net_change_pct_points=c["net_points"], interval_95_low_pct_points=lo_i,
                  interval_95_high_pct_points=hi_i)
            counts["contrast"] += 1
            bad = _B_variant_identity(c, len(D.OPS))
            if bad:
                raise SystemExit(f"23f not drawn: {SLAB[arm]} against {SLAB[base]}, the per-variant pairs do not add "
                                 f"up: {bad}")
            for v in VARS:
                pv = c["per_variant"][v]
                S.add(part="variant (not drawn)", strategy=SLAB[arm], against=SLAB[base], variant=vlabel(v),
                      model=S447.VMODEL[v], setting=setting_label(v), gemini=int(is_gemini(v)),
                      rescued=pv["rescued"], lost=pv["lost"], both_passed=pv["both_pass"],
                      both_failed=pv["both_fail"], n_operations=len(D.OPS),
                      change_pct_points=pv["gain_points"])
                counts["variant"] += 1
        for gem in (1, 0):
            xs = [c["per_variant"][v]["gain_points"] for v in VARS if int(is_gemini(v)) == gem]
            st = hs.box_stats(xs, "range")
            S.add(part="box (not drawn)", strategy=SLAB[arm], against=SLAB[base], gemini=gem, n_variants=len(xs),
                  box_q1_pct_points=st["q1"], box_median_pct_points=st["median"], box_q3_pct_points=st["q3"],
                  box_min_pct_points=st["whisker_low"], box_max_pct_points=st["whisker_high"])
            counts["box"] += 1
    print(f"23f: {counts['contrast']} contrasts against free-form not drawn with their {counts['variant']} variant "
          f"rows, and {counts['box']} boxes of all {len(every)} contrasts, as rows not drawn (D222, D224)")


# Supplementary Figure 22 (B1b) dropped, 3 Nov (D222, Valerio: "drop it and move the values as you mentioned in
# figure 6d"): its values are rows of sheet Supplementary Fig. 15f not drawn (draw_B1, _B1_not_drawn). The Supplementary numbers
# close up in one final pass.


# Supplementary Figure 15: the paired tiles, letters a to e for the five contrasts (Valerio, 28 Oct, O1a), blue and
# vermillion for better and worse (D200, R1d), no patterns, rows in D.block_order (FF21)
_S23 = {"lab_w": 33.0, "gap": 6.0, "tile_h": 3.1, "head_h": 4.6, "foot_h": 8.0, "vgap": 2.0, "key_h": 10.0}
SIZE_B4 = (183.0, round(_S23["key_h"] + 3 * (_S23["head_h"] + _S23["tile_h"] * 11 + _S23["foot_h"] + _S23["vgap"]), 2))


def draw_B4(D, F, S):
    from matplotlib.colors import to_hex
    B = _B_data(D)
    C, SLAB = B["C"], D.SLAB
    order = D.block_order
    W, H = SIZE_B4
    g = _S23
    lab_w, gap, tile_h = g["lab_w"], g["gap"], g["tile_h"]
    grid_w = (W - lab_w - gap - 2.0) / 2
    grid_h = tile_h * len(order)
    block_h = g["head_h"] + grid_h + g["foot_h"] + g["vgap"]
    key_h = g["key_h"]
    if len(order) != 11 or abs(key_h + 3 * block_h - H) > 1e-6:
        raise SystemExit(f"S23: {key_h + 3 * block_h:.2f} mm high, the slot {H}")
    TILE = {"rescued": (hs.colour("comparison", "better"), hs.colour("comparison", "better")),
            "lost": (hs.colour("comparison", "worse"), hs.colour("comparison", "worse")),
            "both_pass": (hs.colour("comparison", "tie"), hs.colour("comparison", "tie")),
            "both_fail": (hs.colour("comparison", "both failed"), hs.GREY["line"])}
    NAME = {"rescued": "rescued", "lost": "lost", "both_pass": "both passed", "both_fail": "both failed"}
    PASS = {"rescued": (0, 1), "lost": (1, 0), "both_pass": (1, 1), "both_fail": (0, 0)}
    BACK = {to_hex(TILE[k][0]): PASS[k] for k in TILE}                 # a tile's colour -> (base, arm) passed
    if len(BACK) != len(TILE):
        raise SystemExit("S23: two tile kinds share a colour")
    num = {o: int(re.match(r"^[a-z]+_(\d+)_", o).group(1)) for o in D.OPS}
    ops = sorted(D.OPS, key=lambda o: (D.dataset_of[o] != "RNA-seq", num[o]))
    if [D.dataset_of[o] for o in ops] != ["RNA-seq"] * 10 + ["survival"] * 10 or \
            [num[o] for o in ops] != list(range(1, 11)) * 2:
        raise SystemExit(f"S23: the operations are not 10 RNA-seq and 10 survival numbered 1 to 10: {ops}")
    vrow = {v: S.add(part="variant", panel=None, variant=vlabel(v), model=S447.VMODEL[v], setting=setting_label(v),
                     gemini=int(is_gemini(v))) for v in order}        # shared by the five grids, so no letter
    slots = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]
    letters = "abcde"
    contrast_of_letter = {}
    tiles = []
    ax_letter, ax_block, left_ax, captions = {}, {}, {}, []
    for li, ((arm, base), (r_, c_)) in enumerate(zip(_B_MAIN, slots)):
        cc = C[(arm, base)]
        ci = S.add(part="contrast", panel=letters[li], strategy=SLAB[arm], against=SLAB[base], n_pairs=cc["n_pairs"],
                   rescued=cc["rescued"], lost=cc["lost"], both_passed=cc["both_pass"], both_failed=cc["both_fail"])
        x0 = lab_w + c_ * (grid_w + gap)
        top = key_h + r_ * block_h + g["head_h"]
        ax = F.axes(x0, top, grid_w, grid_h)
        ax_block[ax] = r_
        if c_ == 0:
            left_ax[r_] = ax
        seen = Counter()
        for i, v in enumerate(order):
            for j, o in enumerate(ops):
                kind = cc["tiles"][(v, o)]
                seen[kind] += 1
                bp, ap = PASS[kind]
                ri = S.add(part="tile", panel=letters[li], strategy=SLAB[arm], against=SLAB[base], variant=vlabel(v),
                           model=S447.VMODEL[v], setting=setting_label(v), gemini=int(is_gemini(v)), operation=o,
                           dataset=D.dataset_of[o], operation_number=num[o], base_passed=bp, arm_passed=ap,
                           pair_outcome=NAME[kind])
                fc, ec = TILE[kind]
                p = Rectangle((j + 0.06, i + 0.08), 0.88, 0.84, fc=fc, ec=ec, lw=0.4)
                ax.add_patch(p)
                tiles.append((ri, ax, p))
        if dict(seen) != {k: cc[k] for k in TILE if cc[k]}:
            raise SystemExit(f"S23: tiles {dict(seen)} against the contrast's counts for {arm} vs {base}")
        ax.set_xlim(0, len(ops))
        ax.set_ylim(len(order), 0)
        ax.set_yticks(np.arange(len(order)) + 0.5, [vlabel(v) for v in order] if c_ == 0 else [])
        ax.set_xticks(np.arange(len(ops)) + 0.5, [str(num[o]) for o in ops])
        ax.tick_params(length=0, pad=1.5)
        for s_ in ax.spines.values():
            s_.set_visible(False)
        ax.axvline(10, color=hs.BLACK, lw=hs.LW["reference"])
        # the panel letter, on the line of the panel's one header line (no title: FIGURE_LOCK titles_in_figure)
        lt = hs.panel_letter(F.fig, 0.0 if c_ == 0 else x0 - 4.0, top - 1.2, letters[li])   # at the panel's left edge
        ax_letter[ax] = lt
        contrast_of_letter[letters[li]] = f"{SLAB[arm]} against {SLAB[base]}"
        fmt = "rescued {rescued}, lost {lost} of {n_pairs} pairs"
        t = F.text(x0, top - 1.2, S447.HALF_UP.format(fmt, **S.rows[ci]), ha="left", va="baseline", color=TXT_GREY)
        S.num(t, ci, fmt)
        captions.append(F.text(x0 + grid_w / 4, top + grid_h + 4.0, DHEAD["RNA-seq"], ha="center", va="top",
                               color=TXT_GREY))
        captions.append(F.text(x0 + 3 * grid_w / 4, top + grid_h + 4.0, DHEAD["survival"], ha="center", va="top",
                               color=TXT_GREY))
    marks = []
    for r_ in range(3):
        top = key_h + r_ * block_h + g["head_h"]
        for i, v in enumerate(order):
            yy = top + (i + 0.5) * tile_h
            st = hs.HOSTING["cloud" if is_gemini(v) else "open-weight"]
            m = F.line([1.6], [yy], ls="", marker="o", ms=_B_ms(1.2 if is_gemini(v) else 1.05), mfc=st["mfc"],
                       mec=st["mec"], mew=0 if is_gemini(v) else 0.5)
            marks.append((vrow[v], m))
    hkey(F, [("swatch", TILE["rescued"][0], "rescued (single failed, repeated passed)"),
             ("swatch", TILE["lost"][0], "lost (single passed, repeated failed)"),
             ("swatch", TILE["both_pass"][0], "both passed"), ("swatch", TILE["both_fail"][0], "both failed"),
             ("mark", (hs.BLACK, "o"), figure_names.GEMINI), ("open", (hs.BLACK, "o"), figure_names.OPEN_WEIGHT)],
         lab_w + (W - 2.0 - lab_w) / 2, 3.0, max_width=W - lab_w - 4.0)
    S.check("tile colour, base passed", [r for r, _, _ in tiles], "base_passed",
            [BACK[to_hex(p.get_facecolor())][0] for _, _, p in tiles])
    S.check("tile colour, arm passed", [r for r, _, _ in tiles], "arm_passed",
            [BACK[to_hex(p.get_facecolor())][1] for _, _, p in tiles])
    S.check("tile column, operation number (its tick label)", [r for r, _, _ in tiles], "operation_number",
            [int(ax.get_xticklabels()[int(p.get_x())].get_text()) for _, ax, p in tiles])
    S.check("row marker, filled (Gemini)", [r for r, _ in marks], "gemini",
            [1.0 if to_hex(m.get_markerfacecolor()) != "#ffffff" else 0.0 for _, m in marks])
    # placement read-back, from the drawn artists against the sheet rows: each tile's contrast from its panel letter,
    # its variant from the row name on the left grid of its block at the tile's row, its dataset from the nearer of the
    # two dataset captions; each row marker's variant from the row name at the marker's height
    fig = F.fig
    disp = lambda xy, tr: tr.transform(xy)
    row_name = lambda r_, i: left_ax[r_].get_yticklabels()[i].get_text() if 0 <= i < len(order) else None
    bad = []
    for ri, ax, p in tiles:
        row = S.rows[ri]
        i, j = int(p.get_y()), int(p.get_x())
        cx = disp((j + 0.5, i + 0.5), ax.transData)[0]
        cap = min(captions, key=lambda t: abs(disp(t.get_position(), fig.transFigure)[0] - cx))
        lt = ax_letter[ax].get_text()
        got = (lt, contrast_of_letter[lt], row_name(ax_block[ax], i), cap.get_text())
        if got != (row["panel"], f"{row['strategy']} against {row['against']}", row["variant"], DHEAD[row["dataset"]]):
            bad.append(f"tile {row['strategy']} {row['variant']} {row['operation']}: drawn as {got}")
    for ri, m in marks:
        dxy = disp((m.get_xdata()[0], m.get_ydata()[0]), fig.transFigure)
        names = [row_name(r_, int(np.floor(left_ax[r_].transData.inverted().transform(dxy)[1]))) for r_ in left_ax]
        names = [nm for nm in names if nm is not None]
        if names != [S.rows[ri]["variant"]]:
            bad.append(f"row marker of {S.rows[ri]['variant']}: beside {names}")
    if bad:
        raise SystemExit(f"S23: drawn in the wrong place: {bad[:5]}")
    print(f"S23: {len(tiles)} tiles (contrast by panel letter, variant, dataset) and {len(marks)} row markers in place")
    # D299 (Valerio, 7 Nov, "O1"): panel f, the five contrasts' net change (B1, Figure 7d until then), in the slot the
    # grid leaves free right of e and under d. Its letter stands where b's and d's do, its baseline on e's header line;
    # it fills the slot to the page's right and bottom edges. Its own sheet, '<this sheet>f'.
    free = [(r_, c_) for r_ in range(3) for c_ in range(2) if (r_, c_) not in slots]
    if free != [(2, 1)]:
        raise SystemExit(f"S23: f wants the one free slot right of e, the grid leaves {free}")
    f_in = 2.0                              # 7 Nov review: the slot starts 2 mm further left, its letter where it was,
    fx0 = lab_w + grid_w + gap - 4.0 - f_in  # so the five strategy names under f stand apart
    fy0 = key_h + 2 * block_h + g["head_h"] - 1.2 - PT_LETTER * MMPT
    f_size = (round(W - fx0, 2), round(H - fy0, 2))
    Ff = Frame(F.page, F.ox + fx0, F.oy + fy0, f_size[0], f_size[1], "f")
    out_f = draw_B1(D, Ff, S.book.sheet(f"{S.name}f"), f_size, letter_x=f_in)
    nv, no = len(order), len(D.OPS)
    n_ds = Counter(D.dataset_of[o] for o in D.OPS)
    # D303 (manuscript tab rev 3688): one sentence per panel, each opening with a capital
    named = ". ".join(f"**{lt}**, {contrast_of_letter[lt][:1].upper()}{contrast_of_letter[lt][1:]}: each tile is one "
                      f"pair, coloured by outcome (key above); header, pairs rescued and lost" for lt in letters)
    return {"sheets_note": (f"Two sheets. Sheet {S.name}, the {len(letters)} panels {letters[0]} to {letters[-1]}: the "
                            f"column 'panel' gives the letter of each 'contrast' and 'tile' row; the 'variant' rows give "
                            f"the row order all {len(letters)} panels share and have no letter. Sheet {S.name}f, panel "
                            f"f: {_B1_SHEET_TXT}"),
            # Valerio, 8 Nov (editor row 45): a to e derive no statistics, so no n tag; each panel says in full
            # what a tile is and what its colour means, with no reference to another panel.
            "legend": (f"In grids {letters[0]} to {letters[-1]}, rows are variants ({D.blocks[0][0]}, then "
                       f"{D.blocks[1][0]}, each by pooled free-form pass rate, high to low; filled dot, Gemini; open "
                       f"dot, open-weight; low, the lowest thinking setting) and columns are operations, numbered "
                       f"within each dataset ({n_ds['RNA-seq']} {DHEAD['RNA-seq']} and {n_ds['survival']} "
                       f"{DHEAD['survival']}). {named}. **f**, "
                       f"{out_f['legend'][:1].upper()}{out_f['legend'][1:]}")}


# ---- panels G ----------------------------------------------------------------------------------------------------------------
# ---- G-4 (D138, "G4 OK!"; Supplementary, model by model): per-operation gap of structured over free-form prompting,
# one box per variant in Figure 2b's form (D128: quartiles, median, whiskers to the range, every operation a grey dot
# over the box by S457.swarm; no mean, no interval), rows in D.block_order under two block heads (FF21, W9), a right
# column of operations below / above 0, no counts beside stacks. Port of draw_G4.py (+ draw_G.py's data part);
# its committed numbers (findings/recompute/fig6_options_2026-10-25/G4_numbers.json) are the reproduce gate.
SIZE_G4 = (89.0, 88.65)                  # a row keeps 58 / 11 mm; the rows and the two block heads take 13.4 rows
_G_G4_JSON = ROOT / "findings/recompute/fig6_options_2026-10-25/G4_numbers.json"


def _G_opdiff(D):
    """draw_G.py's tables from D.rows: per variant the family counts, per (variant, operation) the structured share
    (of 4) minus the free-form share (of 3) in points, its mean the pooled gap. Gates, each against a source other
    than this computation: S479's committed by_group (each family over all variants) and per-variant, per-tier gap
    (summed from the operation cells); S478's committed table (7 variants, all three families and the pooled gap);
    4 and 3 attempts per operation; the pooled gap a second way, as the mean of the operation differences. draw_G.py
    compared the family counts with the prep agent's summary.json; D.summary is built from these same rows, so that
    comparison could not fail and is replaced by the S479 ones."""
    fam = count(D.rows, "variant_id", "family")
    opf = count(D.rows, "variant_id", "family", "op_id")
    j479 = json.loads(J479.read_text())
    pct = lambda c: round(100 * c[0] / c[1], 1)
    for f in FAMS:                                 # S479's committed by_group: each family over all variants
        if [sum(fam[(v, f)][k] for v in D.VARS) for k in (0, 1)] != j479["by_group"][f]["all"]["passes"]:
            raise SystemExit(f"NOT REPRODUCED: G4 {f} passes over all variants against S479's by_group")
    for v in D.VARS:
        for k in TIERS:                            # S479's committed per-variant, per-tier gap, from the operation cells
            c = {f: [sum(opf[(v, f, o)][i] for o in D.ops_of_tier[k]) for i in (0, 1)] for f in FAMS}
            if round(pct(c["structured"]) - pct(c["free-form"]), 1) != \
                    j479["structured_minus_free_form_per_variant"][v][k]:
                raise SystemExit(f"NOT REPRODUCED: G4 {v} {k} gap from the operation cells against S479's")
        for o in D.OPS:
            if opf[(v, "structured", o)][1] != 4 or opf[(v, "free-form", o)][1] != 3:
                raise SystemExit(f"NOT REPRODUCED: G4 {v} {o} does not hold 4 structured and 3 free-form attempts")
    rate = lambda c: 100 * c[0] / c[1]
    FF = {v: rate(fam[(v, "free-form")]) for v in D.VARS}
    ST = {v: rate(fam[(v, "structured")]) for v in D.VARS}
    GAP = {v: ST[v] - FF[v] for v in D.VARS}
    j478 = json.loads(J478.read_text())["variants"]
    for v, t in j478.items():                      # S478's committed table (7 variants, all three families)
        if round(GAP[v], 1) != t["all"]["structured_minus_free_form"] or \
                t["all"]["passes"] != {f: list(fam[(v, f)]) for f in t["all"]["passes"]}:
            raise SystemExit(f"NOT REPRODUCED: G4 {v} pooled gap {GAP[v]:.3f} and family passes "
                             f"{ {f: list(fam[(v, f)]) for f in FAMS} } against S478's "
                             f"{t['all']['structured_minus_free_form']} and {t['all']['passes']}")
    OPD = {v: [100 * (opf[(v, "structured", o)][0] / 4 - opf[(v, "free-form", o)][0] / 3) for o in D.OPS]
           for v in D.VARS}
    for v in D.VARS:
        if abs(sum(OPD[v]) / len(OPD[v]) - GAP[v]) > 1e-9:
            raise SystemExit(f"NOT REPRODUCED: G4 the mean of {v}'s per-operation differences is not its gap")
    # the row-order gate (W9): D.block_order against the block rule on this table's own free-form rates
    rule = block_rule(D.VARS, FF, {v: D.summary["per_variant"][v]["overall"][0] for v in D.VARS})
    order = [v for _, vv in rule for v in vv]
    if order != D.block_order:
        raise SystemExit(f"NOT REPRODUCED: G4 row order {[S447.short_variant(v) for v in order]} against D.block_order "
                         f"{[S447.short_variant(v) for v in D.block_order]}")
    return fam, opf, FF, ST, GAP, OPD, order


def draw_G4(D, F, S):
    fam, opf, FF, ST, GAP, OPD, order = _G_opdiff(D)
    rows_y, heads, NR = _X_rows_y({"blocks": D.blocks})
    y_of = {v: y for v, _, y in rows_y}
    row_mm = 58.0 / len(order)                     # the row pitch of draw_G4.py, so its overlapping counts hold
    top, h, w = 7.0, row_mm * NR, 41.0
    ax = F.axes(35.0, top, w, h)
    dot = 0.45                                     # Figure 2b's form (draw_G4.py)
    xlo, xhi = -105.0, 105.0
    ax.set_xlim(xlo, xhi)                          # before the boxes: hs.boxplot measures the axes
    ax.set_ylim(NR - 0.5, -0.5)
    mm_x = w / (xhi - xlo)                         # mm per point on the x axis
    want = json.loads(_G_G4_JSON.read_text())
    if set(want) != {S447.short_variant(v) for v in order}:     # the row order is _G_opdiff's gate (W9)
        raise SystemExit(f"NOT REPRODUCED: G4 variants {sorted(S447.short_variant(v) for v in order)} against "
                         f"the draft's {sorted(want)}")
    for i, v in enumerate(order):
        d = OPD[v]
        q = S447.quantiles(d)
        arr = np.array(d)
        below, above, zero = int((arr < 0).sum()), int((arr > 0).sum()), int((arr == 0).sum())
        off, over = S457.swarm([x * mm_x for x in d], half=0.40 * row_mm, pitch=0.5, dot=dot)
        mine = {"q1": round(q["q1"], 1), "median": round(q["median"], 1), "q3": round(q["q3"], 1),
                "min": round(q["min"], 1), "max": round(q["max"], 1), "below": below, "above": above, "zero": zero,
                "overlapping": over}
        if mine != want[S447.short_variant(v)]:
            raise SystemExit(f"NOT REPRODUCED: G4 {v} {mine} against the draft's {want[S447.short_variant(v)]}")
        op_rows = []
        for o, x in zip(D.OPS, d):
            op_rows.append(S.add(part="operation", variant=vlabel(v), variant_id=v, op_id=o,
                                 structured_passed=opf[(v, "structured", o)][0],
                                 structured_attempts=opf[(v, "structured", o)][1],
                                 free_form_passed=opf[(v, "free-form", o)][0],
                                 free_form_attempts=opf[(v, "free-form", o)][1], difference_points=x))
        b = S.add(part="box", variant=vlabel(v), variant_id=v, row_from_top=i + 1, row_y=y_of[v], n_operations=len(d),
                  q1_points=q["q1"], median_points=q["median"], q3_points=q["q3"], min_points=q["min"],
                  max_points=q["max"], operations_below_0=below, operations_at_0=zero, operations_above_0=above,
                  free_form_passed=fam[(v, "free-form")][0], free_form_attempts=fam[(v, "free-form")][1],
                  structured_passed=fam[(v, "structured")][0], structured_attempts=fam[(v, "structured")][1],
                  free_form_rate_pct=FF[v], structured_rate_pct=ST[v], pooled_gap_points=GAP[v],
                  dots_overlapping=over, all_strategies_passed=D.summary["per_variant"][v]["overall"][0])
        y = y_of[v]
        # house box over the dots: no fill, caps, 1.0 pt median, 0.40 of the row. The dots keep their places and
        # their 0.45 mm (up to 15 operations tie at one value in a row; at 1.0 mm most of them would be hidden)
        dots, = ax.plot(d, [y + o / row_mm for o in off], ls="none", marker="o", ms=dot / MMPT, mfc=DOT_GREY, mew=0,
                        mec="none", zorder=3)
        art = hs.boxplot(ax, y, values=None, orient="h", slot=1.0, dots=False, zorder=3,
                         stats={"q1": q["q1"], "median": q["median"], "q3": q["q3"], "whisker_low": q["min"],
                                "whisker_high": q["max"]})
        rq1, rmed, rq3, rlo, rhi = _hbox_read(art, "h")
        S.check(f"{v} box left", [b], "q1_points", [rq1])
        S.check(f"{v} box right", [b], "q3_points", [rq3])
        S.check(f"{v} median", [b], "median_points", [rmed])
        S.check(f"{v} lower whisker", [b], "min_points", [rlo])
        S.check(f"{v} upper whisker", [b], "max_points", [rhi])
        S.check(f"{v} operation dots", op_rows, "difference_points", list(dots.get_xdata()))
        S.check(f"{v} row", [b], "row_y", [art["median"].get_ydata().mean()])
        t = ax.text(1.03, y, f"{below} / {above}", transform=ax.get_yaxis_transform(), va="center", ha="left")
        S.num(t, b, "{operations_below_0} / {operations_above_0}")
        S.check(f"{v} right column row", [b], "row_y", [t.get_position()[1]])
    hd = ax.text(1.03, -0.75, "below /\nabove 0", transform=ax.get_yaxis_transform(), va="bottom", ha="left",
                 color=GREY_NOTE, linespacing=1.0)
    S.book.fixed(hd, "column header: operations below and above 0 points")
    hs.reference_line(ax, 0)                       # house: zero line black 0.5 pt
    ax.set_yticks([y_of[v] for v in order], [vlabel(v) for v in order])
    boxes = [r for r in S.rows if r.get("part") == "box"]
    got = [(float(y), t.get_text()) for y, t in zip(ax.get_yticks(), ax.get_yticklabels())]
    if got != [(r["row_y"], r["variant"]) for r in boxes]:
        raise SystemExit(f"G4: the row labels {got} are not the workbook's rows")
    for name, y in heads:                          # the block heads, as X-2's
        F.text(0.5, top + h * (y + 0.5) / NR, name, va="center", ha="left", color=GREY_NOTE)
    ax.tick_params(axis="y", length=0, pad=2)
    ax.set_xticks(range(-100, 101, 50), [hs.fmt_num(t) for t in range(-100, 101, 50)])
    ax.set_xlabel("Structured minus free-form, per operation\n(percentage points)", labelpad=2)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    S.add(part="key", n_operations=len(D.OPS))       # the row stays (numbers unchanged); house: no key here (D147)
    F.letter()
    n_st = sum(1 for x in D.STRATS if FAM[x] == "structured")
    n_ff = sum(1 for x in D.STRATS if FAM[x] == "free-form")
    # Valerio, 8 Nov (editor row 45): the boxes derive statistics, so n is stated once, as "n = X <unit>"; the rows
    # are written out here (no reference to another panel)
    legend = (f"Per model variant, grey dots, one per operation: its pass share under the {n_st} structured "
              f"strategies minus under the {n_ff} free-form ones (percentage points). Box, quartiles; thick line, "
              f"median; whiskers, range; n = {len(D.OPS)} operations per box. Right, operations below / above 0. "
              f"{_rows_words16(D)}")
    return {"legend": legend}


# ---- panels C ----------------------------------------------------------------------------------------------------------------
# ---- family C: the thinking ladder (C2) and the cost per strategy (C3), ported from draw_C.py (alt2, alt3) ----------
_C_COST = ["generator_calls", "output_tokens", "latency_s"]
_C_GROUPS = OUTCOMES + ["length stop"]          # outcome5(): length stops apart
_C_LADDER = ["gpt-oss:20b", "gemini-2.5-pro", "gemini-3-flash"]   # the draft's order (PAIRS holds the variants)


def _C_med(xs):
    return stats.median(xs) if xs else None


def _C_int_half_up(x):
    """A median printed as a whole number with thousands separators: S447.half_up() to 0 decimals (half away from
    zero, 12,282.5 prints 12,283). Neither HalfUpFormatter rounds a ",.0f" field half up (they hand it to format(),
    which rounds half to even), so the sheet carries this integer beside the median and the plate prints "{...:,}"."""
    return None if x is None else int(S447.half_up(x, 0))


def _C_cost_rows(D):
    """The draft's float() over every cost field: an attempt without one stops the run."""
    for r in D.rows:
        for k in _C_COST:
            if not isinstance(r[k], (int, float)) or isinstance(r[k], bool):
                raise SystemExit(f"NOT REPRODUCED: {r['variant_id']} {r['strategy']} {r['op_id']} has no {k}")


# The reproduce gate's independent source: the numbers the D138 draft (draw_C.py) drew, C_numbers.json, computed from
# the drafts' attempts.csv (prep.py's extraction of tokens and wall time, whose token sum is the same rule as this
# script's tok_sum, so the gate tests the counting and the drawing, not that rule) and the draft's own outcome split.
# Its sha256 is pinned; it is committed beside G4_numbers.json. Written again by draw_C.py on 5 November 2026 on the
# records after S4's reruns (fig6 spec A6); the pin of the records before S4 was 7d97d137.
_C_DRAFT_SHA256 = "c13507d1335aadf20ca0871bac29cf0bd9f6c9c3d25106983d753bc64834a8ae"
_C_DRAFT_PATHS = [ROOT / "findings/recompute/fig6_options_2026-10-25/C_numbers.json"]
_C_DRAFT_GROUP = {"passed": "passed", "wrong values": "wrong values", "no result": "no result",
                  "tool or call failure, other": "machinery", "length stop": "length stop"}   # draw_C.py's GROUPS
_C_DRAFT_BOX = {"minimum": "min", "quartile_25": "q1", "median": "median", "quartile_75": "q3", "maximum": "max"}


def _C_draft():
    for p in _C_DRAFT_PATHS:
        if p.exists():
            if sha(p) != _C_DRAFT_SHA256:
                raise SystemExit(f"NOT REPRODUCED: {p} is not the draft's C_numbers.json (sha256 {sha(p)})")
            return json.loads(p.read_text())
    raise SystemExit(f"NOT REPRODUCED: the draft's C_numbers.json is at none of {[str(p) for p in _C_DRAFT_PATHS]}")


def _C_same(a, b):
    """Equal, None with None, or two numbers within 1e-9 of each other (relative above 1)."""
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))


def _C_pattern(F, rect, pat, fill, z=3):
    """X-1's fill patterns (S447.pattern_marks, OPAT's codes) inside rect (x0, y0, x1, y1), frame mm, y downward.
    Returns the number of marks drawn: 0 when the box is narrower than one whole mark (S447.pattern_min_mm)."""
    if not pat:
        return 0
    ink = S447.ink_on(fill)
    lines, dots, rings = S447.pattern_marks(rect, pat)
    for pts in lines:
        F.line([p[0] for p in pts], [p[1] for p in pts], color=ink, lw=LW, solid_capstyle="butt",
               solid_joinstyle="miter", zorder=z)
    for pts, filled, dmm in ((dots, True, S447.DOT_PATTERN_MM), (rings, False, S447.RING_PATTERN_MM)):
        if pts:
            F.line([p[0] for p in pts], [p[1] for p in pts], ls="", marker="o", ms=S447.ms_pt(dmm),
                   mfc=ink if filled else "none", mec="none" if filled else ink, mew=0 if filled else LW, zorder=z)
    return len(lines) + len(dots) + len(rings)


_C_KIND_WORDS = {"tool call written as text": "a tool call as text", "step produced no cell and no error": "a step with no cell",
                 "tool-call parse error": "an unparsed tool call", "no code": "no code",
                 "harness error": "a harness error", "other call error": "another call error",
                 "stall": "a stalled call", "tools refused by Ollama": "tools refused by Ollama"}


def _C_outcome_words(D, vs, n_len):
    """The legend's definitions of the outcome groups, each checked against the rows of variants vs before it is
    written (S447.fail_kind's kinds, outcome5()'s grouping)."""
    rr = [r for r in D.rows if r["variant_id"] in vs and not r["passed"]]
    wv = [r for r in rr if r["outcome5"] == "wrong values"]
    nr = [r for r in rr if r["outcome5"] == "no result"]
    tc = [r for r in rr if r["outcome5"] == "tool or call failure, other"]
    if not all(r["has_results"] and r["fail_kind"] == "result wrong or missing" for r in wv):
        raise SystemExit("C2 legend: a wrong-values attempt returned no values")
    if any(r["has_results"] for r in nr):
        raise SystemExit("C2 legend: a no-result attempt returned values")
    w = ("Wrong values: values returned that did not match the reference"
         + (", with or without a run error" if any(r["exec_outcome"] != "ok" for r in wv) else "") + ". ")
    how = [x for x, k in (("raised or timed out", "code raised or timed out"),
                          ("ran without any", "result wrong or missing")) if any(r["fail_kind"] == k for r in nr)]
    if {r["fail_kind"] for r in nr} - {"code raised or timed out", "result wrong or missing"}:
        raise SystemExit("C2 legend: a no-result attempt of another kind")
    w += "No result: no values returned (" + ", or ".join(how) + "). "
    kinds = []
    for k, _ in Counter(r["fail_kind"] for r in tc).most_common():
        if k == "other":
            if not all(r["exec_outcome"] == "exec_timeout" and r["has_results"] for r in tc if r["fail_kind"] == k):
                raise SystemExit("C2 legend: S447's \"other\" kind holds an attempt the legend does not describe")
            kinds.append("a timeout after returning values")
        elif k in _C_KIND_WORDS:
            kinds.append(_C_KIND_WORDS[k])
        else:
            raise SystemExit(f"C2 legend: no words for the kind {k!r}")
    if kinds:
        w += ("Tool or call failure, other: " + (", ".join(kinds[:-1]) + " or " + kinds[-1] if len(kinds) > 1
                                                  else kinds[0]) + ". ")
    w += ("Length stops are shown apart, in black." if n_len else "Length stops are shown apart; there are none here.")
    return w


def _C_cost16(ladder, N):
    """Supplementary Figure 16b's right-hand columns in one sentence (Valerio, 8 Nov: the legend under 300 words);
    _C_cost_words is kept as the guard on which models record no thinking count and which ran locally."""
    _C_cost_words(ladder, N)
    none_ = [m for m, vv in ladder if all(N[v]["thinking_rows"] == 0 for v in vv)]
    local = [m for m, vv in ladder if not any(is_gemini(v) for v in vv)]
    if none_ != local or len(local) != 1:
        raise SystemExit(f"C2 legend: no thinking count for {none_}, run locally {local}; the words name one model "
                         f"for both")
    m = local[0]
    return (f"Right: medians per attempt of output tokens ({m}'s may include thinking, which it does not count), "
            f"thinking tokens (n.r., not recorded) and wall time (s; {m} local, Gemini through Google's API).")


def _C_cost_words(ladder, N):
    """The legend's caution on the right-hand medians, its model names from the rows: which models record no thinking
    count in any setting, and which ran locally and which through Google's API (is_gemini)."""
    none_ = [m for m, vv in ladder if all(N[v]["thinking_rows"] == 0 for v in vv)]
    local = [m for m, vv in ladder if not any(is_gemini(v) for v in vv)]
    api = [m for m, vv in ladder if all(is_gemini(v) for v in vv)]
    if sorted(local + api) != sorted(m for m, _ in ladder) or not api:
        raise SystemExit("C2 legend: a model is neither local nor Gemini")
    j = lambda xs: " and ".join(xs)
    w = "Thinking tokens where recorded (n.r., not recorded). "
    if none_:
        w += f"{j(none_)} records no thinking count, so its output tokens may include thinking. "
    if local:
        w += f"Wall time: {j(local)} local, Gemini through Google's API."
    return w.strip()


# ---------------------------------------------------------------------------------------------------------------------
# C2: the thinking ladder (draw_C.py draw_alt2)
# ---------------------------------------------------------------------------------------------------------------------
SIZE_C2 = (82.0, 79.1)


def draw_C2(D, F, S):
    _C_cost_rows(D)
    ladder = [(m, PAIRS[m]) for m in _C_LADDER]
    if {v for vv in PAIRS.values() for v in vv} != {v for _, vv in ladder for v in vv}:
        raise SystemExit("NOT REPRODUCED: the ladder's models are not PAIRS'")
    for m, vv in ladder:
        if any(S447.VMODEL[v] != m for v in vv) or any(v not in D.VARS for v in vv):
            raise SystemExit(f"NOT REPRODUCED: the ladder's {m} variants are not the design's")
    N = {}
    for v in D.VARS:                                   # all 11, as the draft gated them; the ladder draws 7
        rr = [r for r in D.rows if r["variant_id"] == v]
        th = [r["thinking_tokens"] for r in rr if r["thinking_tokens"] is not None]
        gc = Counter(r["outcome5"] for r in rr)
        if set(gc) - set(_C_GROUPS):
            raise SystemExit(f"NOT REPRODUCED: {v} has outcomes {sorted(set(gc) - set(_C_GROUPS))}")
        if sum(gc.values()) != len(rr) or gc["passed"] != sum(r["passed"] for r in rr):
            raise SystemExit(f"NOT REPRODUCED: {v}'s outcomes do not add up to its attempts")
        if len(rr) != len(D.STRATS) * len(D.OPS):
            raise SystemExit(f"NOT REPRODUCED: {v} holds {len(rr)} attempts")
        N[v] = {"n": len(rr), "passes": sum(r["passed"] for r in rr), "groups": {g: gc.get(g, 0) for g in _C_GROUPS},
                "median_output_tokens": _C_med([r["output_tokens"] for r in rr]),
                "median_thinking_tokens": _C_med(th), "thinking_rows": len(th),
                "median_latency_s": _C_med([r["latency_s"] for r in rr]),
                "median_generator_calls": _C_med([r["generator_calls"] for r in rr])}
    # reproduce: every count and median drawn equals the draft's C_numbers.json (see _C_DRAFT_PATHS)
    dv = _C_draft()["variant"]
    if list(dv) != list(D.VARS):
        raise SystemExit(f"NOT REPRODUCED: the draft's variants {list(dv)} are not the design's {D.VARS}")
    for v, d in N.items():
        w = dv[v]
        bad = [k for k in ("median_output_tokens", "median_thinking_tokens", "median_latency_s",
                           "median_generator_calls") if not _C_same(d[k], w[k])]
        if [d["passes"], d["n"]] != w["pass"] or d["thinking_rows"] != w["thinking_rows"]:
            bad.append("pass or thinking_rows")
        if {_C_DRAFT_GROUP[g]: c for g, c in d["groups"].items()} != w["groups"] or is_gemini(v) != w["cloud"]:
            bad.append("outcome groups or cloud")
        if bad:
            raise SystemExit(f"NOT REPRODUCED: {v}: {bad} differ from the draft's C_numbers.json")
    used = [g for g in _C_GROUPS if any(N[v]["groups"][g] for _, vv in ladder for v in vv)]
    n_len = sum(N[v]["groups"]["length stop"] for _, vv in ladder for v in vv)

    W, H = SIZE_C2
    row, name_h, gap_m, key_h, head_h = 4.6, 4.4, 1.6, 13.0, 7.0
    n_rows = sum(len(vv) for _, vv in ladder)
    plot_h = n_rows * row + len(ladder) * name_h + (len(ladder) - 1) * gap_m
    top = key_h + head_h
    if abs(top + plot_h + 10.5 - H) > 1e-9:
        raise SystemExit(f"C2: the layout needs {top + plot_h + 10.5:.2f} mm, SIZE_C2 says {H}")
    F.letter()

    # key, two columns read down (the draft's fig.legend: swatch 4.6 x 2.5 mm from x 4.9, text 2.25 mm after it,
    # 2.8 mm between columns, rows at 3.8 and 7.4 mm)
    LAB = 14.0
    bx, bw = 1.0 + LAB, 30.0
    # house key: swatches with their patterns, no outline, centred over the bars and their medians, wrapped
    cxk = (bx + W - 0.5) / 2
    _, klines = hkey(F, [("swatch", (OCOL[g], OPAT[g] or None), g) for g in used], cxk, PT_LETTER * MMPT,
                     max_width=_X_key_room(F, cxk))
    if klines[-1][2] - F.oy > key_h - 3.0:
        raise SystemExit(f"C2: the key needs {len(klines)} lines, more than its {key_h} mm")
    heads = [("output", "tokens", "median_output_tokens"), ("thinking", "tokens", "median_thinking_tokens"),
             ("wall", "time (s)", "median_latency_s")]
    cx0 = bx + bw + 3.0
    cw = (W - cx0 - 0.5) / len(heads)
    for j, (l1, l2, _) in enumerate(heads):
        xr = cx0 + (j + 1) * cw - 1.0
        F.text(xr, key_h + 3.3, l1, ha="right", va="baseline")
        F.text(xr, key_h + 6.5, l2, ha="right", va="baseline")

    half = hs.BAR_FRAC / 2
    bars, widths, lefts, plain = [], [], [], []
    y = top
    axes = []
    first_bar = None
    for m, vv in ladder:
        t = F.text(bx, y + name_h - 0.9, m, ha="left", va="bottom")
        S.book.fixed(t, "a model's name")
        y += name_h
        h = len(vv) * row
        ax = F.axes(bx, y, bw, h)
        for i, v in enumerate(vv):
            d = N[v]
            n = d["n"]
            left = 0.0
            for g in _C_GROUPS:
                c = d["groups"][g]
                if not c:
                    continue
                share = 100 * c / n
                ri = S.add(part="bar", model=m, setting=setting_label(v), variant=vlabel(v), outcome=g,
                           attempts=c, attempts_n=n, share_pct=share, share_start_pct=left)
                if first_bar is None:
                    first_bar = ri
                rect = ax.barh(i, share, left=left, height=hs.BAR_FRAC, color=OCOL[g], lw=0, zorder=2)[0]
                bars.append(ri)
                widths.append(rect.get_width())
                lefts.append(rect.get_x())
                x0m, x1m = bx + bw * left / 100, bx + bw * (left + share) / 100
                ins = LW * MMPT / 2       # half a line's width: no pattern ink crosses into the next segment (the
                yc = y + (i + 0.5) * row  # draft's bars have no edge, so X-1's inset for its white edge is not used)
                marks = _C_pattern(F, (x0m + ins, yc - half * row + ins, x1m - ins, yc + half * row - ins), OPAT[g],
                                   OCOL[g])
                if OPAT[g] and not marks:
                    plain.append((v, g, c))
                left += share
            if sum(d["groups"].values()) != n:
                raise SystemExit(f"NOT REPRODUCED: {v}'s bar does not hold its {n} attempts")
            ax.text(-1.5, i, setting_label(v), ha="right", va="center", transform=ax.transData)
            ri = S.add(part="medians", model=m, setting=setting_label(v), variant=vlabel(v), attempts_n=n,
                       passes=d["passes"],
                       median_output_tokens=d["median_output_tokens"],
                       median_output_tokens_printed=_C_int_half_up(d["median_output_tokens"]),
                       median_thinking_tokens=d["median_thinking_tokens"],
                       median_thinking_tokens_printed=_C_int_half_up(d["median_thinking_tokens"]),
                       thinking_tokens_recorded_attempts=d["thinking_rows"],
                       median_wall_time_s=d["median_latency_s"],
                       median_wall_time_s_printed=_C_int_half_up(d["median_latency_s"]))
            for j, (_, _, key) in enumerate(heads):
                col = {"median_output_tokens": "median_output_tokens_printed",
                       "median_thinking_tokens": "median_thinking_tokens_printed",
                       "median_latency_s": "median_wall_time_s_printed"}[key]
                val = S.rows[ri][col]
                tx = F.text(cx0 + (j + 1) * cw - 1.0, y + (i + 0.5) * row, "n.r." if val is None else f"{val:,}",
                            ha="right", va="center")
                if val is not None:
                    S.num(tx, ri, "{" + col + ":,}")
        ax.set_ylim(len(vv) - 0.5, -0.5)
        ax.set_xlim(0, 100)
        ax.set_yticks([])
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.set_xticks([0, 25, 50, 75, 100])
        if m != ladder[-1][0]:
            ax.set_xticklabels([])
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(axis="x", length=0)
        axes.append(ax)
        y += h + gap_m
    S.check("bar width (% of the setting's attempts)", bars, "share_pct", widths)
    S.check("bar start (% of the setting's attempts)", bars, "share_start_pct", lefts)
    ns = {S.rows[i]["attempts_n"] for i in bars}
    if len(ns) != 1:
        raise SystemExit(f"C2: the settings hold {sorted(ns)} attempts, the axis title states one n")
    axes[-1].set_xlabel(f"Attempts (% of n = {ns.pop()} per setting)", labelpad=2)
    S.num(axes[-1].xaxis.label, first_bar, "Attempts (% of n = {attempts_n} per setting)")

    n_set = S.rows[first_bar]["attempts_n"]
    # Valerio, 8 Nov (editor row 45): shares and medians with no spread drawn derive no statistics, so no n tag; the
    # outcomes are defined here (_C_outcome_words, guarded on the rows), not by reference to Figure 7c
    vs = [v for _, vv in ladder for v in vv]
    _C_outcome_words(D, vs, n_len)                 # its guards: each group holds only what these words say
    tc = {r["fail_kind"] for r in D.rows if r["variant_id"] in vs and not r["passed"]
          and r["outcome5"] == "tool or call failure, other"}
    told = {"tool call written as text", "other call error", "tool-call parse error", "stall", "no code",
            "step produced no cell and no error", "harness error", "other"}
    if tc - told or n_len:
        raise SystemExit(f"C2 legend: outcome kinds {sorted(tc - told)} or {n_len} length stops the words do not name")
    legend = (f"One bar per thinking setting of {', '.join(m for m, _ in ladder[:-1])} and {ladder[-1][0]}, its "
              f"{n_set} attempts split by outcome (% of attempts). Wrong values: values returned, not matching the "
              f"reference. No result: no values returned. Tool or call failure, other: a malformed or failed call, "
              f"no code, a harness error or a timeout after returning values. "
              + f"{_gemini_low()} " + _C_cost16(ladder, N))
    return {"legend": legend}


# ---------------------------------------------------------------------------------------------------------------------
# C3: cost per attempt, Gemini and open-weight apart (draw_C.py draw_alt3), house boxes over every attempt; tokens count
# Gemini's thinking (Valerio, 28 Oct, O1a). The sheet's group value stays "cloud": the gate against C_numbers.json maps it.
# ---------------------------------------------------------------------------------------------------------------------
_C3_ROW, _C3_FAM_GAP, _C3_KEY_H, _C3_HEAD_H, _C3_FOOT_H = 11.0, 2.5, 6.0, 7.5, 13.0
SIZE_C3 = (183.0, round(_C3_KEY_H + _C3_HEAD_H + 11 * _C3_ROW + 2 * _C3_FAM_GAP + _C3_FOOT_H, 2))
_C3_TOK = "generated_tokens"
_C3_COST = ["generator_calls", _C3_TOK, "latency_s"]
_C3_XLAB = {"generator_calls": "Model calls\nper attempt", _C3_TOK: "Output and thinking\ntokens per attempt",
            "latency_s": "Wall time\nper attempt (s)"}
_C3_UNIT = {"generator_calls": "model calls", _C3_TOK: "tokens", "latency_s": "s"}


def _C_box(xs):
    return {"minimum": min(xs), "quartile_25": float(np.percentile(xs, 25)), "median": _C_med(xs),
            "quartile_75": float(np.percentile(xs, 75)), "maximum": max(xs)}


def _c3_tokens(r):
    """O1a (Valerio, 28 Oct): every token the generator produced. Gemini's API reports its thinking apart
    (usageMetadata.thoughtsTokenCount, recorded per call as thinking_tokens, experiments/runner/gemini_client.py:301-302),
    so it is added to the output tokens where recorded (a variant with none, _c3_no_thinking_clause, counts output
    tokens only); the open-weight variants record no thinking count apart (checked here)."""
    if is_gemini(r["variant_id"]):
        return r["output_tokens"] + (r["thinking_tokens"] or 0)
    if r["thinking_tokens"]:
        raise SystemExit(f"S24: an open-weight attempt records thinking tokens apart: {r['variant_id']} {r['op_id']}")
    return r["output_tokens"]


def _c3_no_thinking_clause(rows):
    """The legend's clause on the Gemini attempts _c3_tokens adds nothing to: they record no thinking count, counted
    from the rows. The words hold only when one Gemini variant has none on every attempt and the others have one on
    every attempt; anything else stops the run."""
    gem = [r for r in rows if is_gemini(r["variant_id"])]
    none = [r for r in gem if r["thinking_tokens"] is None]
    vs = {r["variant_id"] for r in none}
    if len(vs) != 1 or len(none) != sum(r["variant_id"] in vs for r in gem):
        raise SystemExit(f"S24 legend: {len(none)} Gemini attempts with no thinking count in {sorted(vs)}; "
                         f"the clause covers every attempt of one variant")
    return (f"{vlabel(vs.pop())} records no thinking count on any of its attempts ({len(none)} of the {len(gem)} Gemini "
            f"attempts), so those attempts count output tokens only.")


def _c3_log_axis(ax, lo_dec, hi_dec, width_mm):
    """Whole decades, one tick each, labelled with every digit and a comma every three ("1,000"); where the labels
    would touch, every other decade is labelled, counted down from the top one, so the top end always has its label and
    the low end may not (S24's wall-time axis: 1 has none)."""
    from matplotlib.ticker import FixedLocator, NullLocator
    ticks = [10.0 ** e for e in range(lo_dec, hi_dec + 1)]
    lab = [hs.fmt_num(t) for t in ticks]
    ax.set_xscale("log")
    ax.set_xlim(ticks[0] / 10 ** 0.12, ticks[-1])
    span = np.log10(ticks[-1]) - np.log10(ticks[0] / 10 ** 0.12)
    per_dec = width_mm / span
    need = max(tw(a) / 2 + tw(b) / 2 for a, b in zip(lab, lab[1:])) + 1.5
    every = 1 if per_dec >= need else 2
    keep = [i for i in range(len(ticks)) if (len(ticks) - 1 - i) % every == 0]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([lab[i] if i in keep else "" for i in range(len(ticks))])


def draw_C3(D, F, S):
    import matplotlib.patheffects as pe
    import matplotlib.transforms as mtrans
    _C_cost_rows(D)
    STR, SLAB_, FAM_ = D.STRATS, D.SLAB, FAM
    cloud_v = [v for v in D.VARS if is_gemini(v)]
    open_v = [v for v in D.VARS if not is_gemini(v)]
    groups = {"cloud": cloud_v, "open-weight": open_v}
    tok = {id(r): _c3_tokens(r) for r in D.rows}
    val = lambda r, k: tok[id(r)] if k == _C3_TOK else r[k]
    N, VALS = {}, {}
    for s in STR:
        rr = [r for r in D.rows if r["strategy"] == s]
        N[s] = {"all": {"pass": [sum(r["passed"] for r in rr), len(rr)]}}
        for grp, gv in groups.items():
            gg = [r for r in rr if r["variant_id"] in gv]
            N[s][grp] = {"pass": [sum(r["passed"] for r in gg), len(gg)],
                         **{k: _C_box([r[k] for r in gg]) for k in _C_COST},          # the committed counting's boxes
                         _C3_TOK: _C_box([tok[id(r)] for r in gg])}
            VALS[(s, grp)] = {k: [val(r, k) for r in gg] for k in _C3_COST}
    nc, no = N[STR[0]]["cloud"]["pass"][1], N[STR[0]]["open-weight"]["pass"][1]
    if not all(N[s]["cloud"]["pass"][1] == nc and N[s]["open-weight"]["pass"][1] == no for s in STR):
        raise SystemExit("NOT REPRODUCED: the strategies' boxes do not hold the same n")
    if nc != len(cloud_v) * len(D.OPS) or no != len(open_v) * len(D.OPS):
        raise SystemExit("NOT REPRODUCED: a group's box does not hold its variants' attempts")
    # reproduce first, on the committed counting: every pass count and every box equals the draft's C_numbers.json
    dr = _C_draft()
    if dr["cloud_variants"] != cloud_v or dr["open_variants"] != open_v or list(dr["strategy"]) != STR:
        raise SystemExit("NOT REPRODUCED: the draft's cloud and open-weight variants or strategies differ")
    for s in STR:
        w = dr["strategy"][s]
        bad = [] if N[s]["all"]["pass"] == w["pass"] else ["all pass"]
        for grp, dg in (("cloud", "cloud"), ("open-weight", "open")):
            if N[s][grp]["pass"] != w[dg]["pass"]:
                bad.append(f"{grp} pass")
            bad += [f"{grp} {k} {q}" for k in _C_COST for q, dq in _C_DRAFT_BOX.items()
                    if not _C_same(N[s][grp][k][q], w[dg][k][dq])]
        if bad:
            raise SystemExit(f"NOT REPRODUCED: {s}: {bad} differ from the draft's C_numbers.json")
        if N[s]["open-weight"][_C3_TOK] != N[s]["open-weight"]["output_tokens"]:
            raise SystemExit(f"S24: {s}: the open-weight token box moved; only Gemini's should")

    W, H = SIZE_C3
    row = _C3_ROW
    fams = list(dict.fromkeys(FAM_[s] for s in STR))
    plot_h = len(STR) * row + (len(fams) - 1) * _C3_FAM_GAP
    top = _C3_KEY_H + _C3_HEAD_H
    if abs(top + plot_h + _C3_FOOT_H - H) > 1e-9:
        raise SystemExit(f"S24: the layout needs {top + plot_h + _C3_FOOT_H:.2f} mm, SIZE_C3 says {H}")
    OFF = {"cloud": -0.2, "open-weight": +0.2}              # Gemini above open-weight, closer than the next strategy
    DOT = {"cloud": {"mfc": hs.HOSTING["cloud"]["mfc"], "mec": "none", "mew": 0},
           "open-weight": {"mfc": hs.HOSTING["open-weight, dense"]["mfc"], "mec": "none", "mew": 0}}
    gr = {grp: S.add(part="group", group=grp, variants=len(gv), attempts_per_box=nc if grp == "cloud" else no)
          for grp, gv in groups.items()}
    yrow, yv = {}, 0.0
    for i, s in enumerate(STR):
        if i and FAM_[s] != FAM_[STR[i - 1]]:
            yv += _C3_FAM_GAP / row
        yrow[s] = yv
        yv += 1
    span = (-0.5, yv - 0.5)
    LAB = 33.0
    x0, pw, gap = 1.0 + LAB, 31.0, 7.0
    mx = x0 + 3 * pw + 2 * gap + 3.0
    mcols = [("cloud", figure_names.GEMINI), ("open-weight", "open-\nweight"), ("all", "all")]
    mw = (W - mx - 1.0) / len(mcols)
    key_g = figure_names.GEMINI + ", {variants} variants (n = {attempts_per_box} attempts per box)"
    key_o = figure_names.OPEN_WEIGHT + ", {variants} variants (n = {attempts_per_box})"
    kt, _ = hkey(F, [("mark", (hs.BLACK, "o"), key_g.format(variants=len(cloud_v), attempts_per_box=nc)),
                     ("mark", (hs.GREY["dot"], "o"), key_o.format(variants=len(open_v), attempts_per_box=no))],
                 x0 + (3 * pw + 2 * gap) / 2, 3.2)
    S.num(kt[0], gr["cloud"], key_g)
    S.num(kt[1], gr["open-weight"], key_o)
    F.text(mx + (len(mcols) * mw) / 2, _C3_KEY_H + 0.4, "Passed (%)", ha="center", va="baseline")
    for j, (_, lab) in enumerate(mcols):
        F.text(mx + (j + 1) * mw - 1.0, top - 0.6, lab, ha="right", va="bottom", linespacing=1.0)
    rb = {q: [] for q in ("minimum", "quartile_25", "median", "quartile_75", "maximum")}
    rows_b, dot_checks = [], []
    overlapping = 0                                        # dots hs.swarm could not place apart; on no sheet (manual list)
    for i, k in enumerate(_C3_COST):
        ax = F.axes(x0 + i * (pw + gap), top, pw, plot_h)
        allx = [val(r, k) for r in D.rows]
        _c3_log_axis(ax, int(np.floor(np.log10(min(allx)))), int(np.ceil(np.log10(max(allx)))), pw)
        ax.set_ylim(span[1], span[0])
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        x_lo, x_hi = ax.get_xlim()
        mm_dec = pw / (np.log10(x_hi) - np.log10(x_lo))
        my = plot_h / (span[1] - span[0])
        slot = 2 * abs(OFF["cloud"])                       # the distance between the two boxes of a strategy
        for s in STR:
            for grp in ("cloud", "open-weight"):
                b = N[s][grp][k]
                ri = S.add(part="box", strategy=SLAB_[s], family=FAM_[s], group=grp, metric=_C3_XLAB[k].replace("\n", " "),
                           unit=_C3_UNIT[k], attempts=N[s][grp]["pass"][1], **b)
                yc = yrow[s] + OFF[grp]
                xs = VALS[(s, grp)][k]
                # dots: hs.swarm on the log axis (positions in mm along it), 0.45 mm, under the box's lines
                half = max(0.0, hs.BAND_FRAC * slot * my / 2 - hs.DOT_MM / 2)
                off, over = hs.swarm([np.log10(x) * mm_dec for x in xs], half=half, pitch=hs.DOT_PITCH_MM, dot=hs.DOT_MM)
                overlapping += over
                ln = ax.plot(xs, [yc + o / my for o in off], ls="none", marker="o", ms=hs.DOT_MM / hs.MM_PT,
                             zorder=2, clip_on=False, **DOT[grp])[0]
                dot_checks.append((sorted(xs), ln))
                st = {"q1": b["quartile_25"], "median": b["median"], "q3": b["quartile_75"],
                      "whisker_low": b["minimum"], "whisker_high": b["maximum"]}
                art = hs.boxplot(ax, yc, stats=st, slot=slot, dots=False, orient="h")
                if grp == "cloud":                         # black lines over black dots: a white edge keeps them read
                    for kk in ("box", "median", "whisker_low", "whisker_high", "cap_low", "cap_high"):
                        if kk in art:
                            a_ = art[kk]
                            a_.set_path_effects([pe.Stroke(linewidth=a_.get_linewidth() + 1.0, foreground=hs.WHITE),
                                                 pe.Normal()])
                q1, med, q3, lo_, hi_ = _hbox_read(art, "h")
                rows_b.append(ri)
                rb["minimum"].append(lo_)
                rb["quartile_25"].append(q1)
                rb["median"].append(med)
                rb["quartile_75"].append(q3)
                rb["maximum"].append(hi_)
        ax.set_xlabel(_C3_XLAB[k], labelpad=2, linespacing=1.0)
        if i == 0:
            bt = mtrans.blended_transform_factory(ax.transAxes, ax.transData)
            for s in STR:
                t = ax.text(-0.04, yrow[s], SLAB_[s], transform=bt, ha="right", va="center")
                if re.search(r"\d", SLAB_[s]):
                    S.book.fixed(t, "a strategy's name")
        if i == 2:
            tr = mtrans.blended_transform_factory(F.fig.transFigure, ax.transData)
            for s in STR:
                for j, (grp, _) in enumerate(mcols):
                    c = N[s][grp]["pass"]
                    ri = S.add(part="passed", strategy=SLAB_[s], family=FAM_[s], group=grp, passes=c[0],
                               attempts=c[1], passed_pct=100 * c[0] / c[1])
                    t = ax.text(F.fx(mx + (j + 1) * mw - 1.0), yrow[s], S447.half_up(100 * c[0] / c[1], 1),
                                transform=tr, ha="right", va="center")
                    S.num(t, ri, "{passed_pct:.1f}")
    for q, got in rb.items():
        S.check(f"box {q}", rows_b, q, got)
    for xs, ln in dot_checks:                              # every attempt drawn as a dot, at its value
        if sorted(ln.get_xdata()) != xs:
            raise SystemExit("S24: a box's dots are not its attempts' values")
    print(f"S24: {overlapping} of {sum(len(xs) for xs, _ in dot_checks)} dots overlap another dot (hs.swarm)")
    n_all = N[STR[0]]["all"]["pass"][1]
    legend = (f"Cost per attempt of each prompting strategy on log axes: model calls (generator calls only), output "
              f"and thinking tokens, and wall time (s). Gemini's API reports its thinking tokens apart from its "
              f"output tokens, and they are added here where recorded. {_c3_no_thinking_clause(D.rows)} The "
              f"open-weight models record no thinking count apart. "
              f"Two boxes per strategy: Gemini, the {len(cloud_v)} variants (n = {nc} attempts per box), and "
              f"open-weight, the {len(open_v)} local variants (n = {no}). A dot is one attempt. Box, quartiles; line, "
              f"median; whiskers, minimum to maximum. Right: attempts passed (%) per group and for all "
              f"{len(D.VARS)} variants (n = {n_all} per strategy).")
    return {"legend": legend}


# =====================================================================================================================
# Plates
# =====================================================================================================================
PANELS = {}                              # filled from the module's SIZE_<ID> / draw_<ID> pairs below


def _collect_panels():
    g = globals()
    for k, v in list(g.items()):
        if k.startswith("draw_") and callable(v) and f"SIZE_{k[5:]}" in g:
            PANELS[k[5:]] = (g[f"SIZE_{k[5:]}"], v)


def lead_main(D):
    """Figure 6's opening sentences (D138 Q9, as advised: pass by execution, one draw, n, both datasets, lock settings,
    the dropped model named); every count from the rows. 6 Nov (legend under 320 words): the scoring tolerances and the
    Ollama version, context and output limit are Methods detail and left to Methods. 6 Nov: the S4 re-run clause
    (_rerun_clause), in the manuscript tab's words."""
    return (f"An attempt is one model variant (a model at one thinking setting), one prompting strategy and one of "
            f"{len(D.OPS)} data-analysis operations on two datasets (airway RNA-seq and NCCTG lung survival), run once "
            f"({_rerun_clause()}); "
            f"{len(D.rows):,} attempts in all ({len(D.VARS)} variants {_B_TIMES} {len(D.STRATS)} strategies {_B_TIMES} "
            f"{len(D.OPS)} operations). An attempt passes when its code returns values matching the reference.")
    # D303 (manuscript tab rev 3688, accepted by Valerio): the gemma3:27b sentence (_no_tools_clause) is deleted from
    # the legend. _no_tools_clause is no longer called; it is kept so the sentence can return if the tab restores it.


def _gemini_low():
    """FF29's clause (FD43), what the label "low" sends: LOCK.toml [gemini] thinking_off, read from the
    lock file. Supplementary Figures 14, 16, 21 and 22 print it."""
    import tomllib
    off = tomllib.loads(S447.LOCK.read_text())["gemini"]["thinking_off"]
    return (f"Gemini low: gemini-2.5-pro with a thinking budget of {off['gemini-2.5-pro']} tokens per call, "
            f"gemini-3-flash at the {off['gemini-3-flash-preview']} level.")


def _no_tools_clause(D):
    """D153 Q3 (audit of 25 Oct F2): the variant Ollama refuses tools for, counted from the rows (S447.fail_kind()'s
    "tools refused by Ollama": HTTP 400 "does not support tools"). The words hold only when one variant has that kind,
    only in the structured family, and passed none of its structured attempts; anything else stops the run."""
    ref = [r for r in D.rows if not r["passed"] and r["fail_kind"] == _X_REFUSED]
    vs = {r["variant_id"] for r in ref}
    if len(vs) != 1 or {r["family"] for r in ref} != {"structured"}:
        raise SystemExit(f"Figure {S447.FIG_N} legend: tools refused for {sorted(vs)} in {sorted({r['family'] for r in ref})}; "
                         f"the gemma3 clause covers one variant's structured attempts")
    v = vs.pop()
    st = [r for r in D.rows if r["variant_id"] == v and r["family"] == "structured"]
    if any(r["passed"] for r in st):
        raise SystemExit(f"Figure {S447.FIG_N} legend: {v} passed structured attempts; the clause says it failed all")
    return f"{vlabel(v)} failed all {len(st)} structured attempts, {len(ref)} because Ollama does not support tools for it"


def _rescore(D):
    """(operation, flips applied): S447.apply_q4_rescore's count, as load_mirror recorded it, and S477's operation."""
    return json.loads(_K_J477.read_text())["operation"], D.notes["q4_lung9_rescore"]["applied"]


def _rescore_clause(D):
    """Audit 27 Oct F2 (fig4_6): the attempts whose pass comes from S477's re-score, not from the run record. Figure
    6's legend stood at 348 words of the lock's under 350 ([legend] words_under), so for Figure 6 this goes in the
    Source Data caption (every data caption carries it); Supplementary Figures 16, 21, 22 and 15 also give it in
    their legend."""
    op, n = _rescore(D)
    return (f"{n} {op} attempts pass on re-scoring: the harness could not read that operation's boolean field, and "
            f"S477 ran each attempt's stored code again with the fixed extraction, no model call "
            f"({_K_J477.relative_to(ROOT)}).")


def _rerun_clause():
    """The attempts S4 ran again (D75, D80 V1, D81; S502's list), as the manuscript tab words it (Methods, Figure 6
    and Supplementary Figures 14 and 16, 5 Nov). The count is S525's committed listed_rerun (s4_gate() holds the copy
    drawn to that file), and it must equal the attempts whose own calls record a code commit in records_manifest.json
    (D252: only the S4 re-runs record one); any difference stops the run."""
    c = json.loads(J525.read_text())["counts"]
    n = c["listed_rerun"]
    own = json.loads(S447.MANIFEST.read_text())["attempts_by_own_code_commit"]
    n_own = sum(v for k, v in own.items() if not k.startswith("none"))
    if n != c["listed"] or n != n_own:
        stop(f"S4 re-run clause: S525 listed {c['listed']}, ran again {n}, records_manifest.json has {n_own} "
             f"attempts with their own code commit")
    return f"{n:,} attempts run again after a rule change, the later run counted"


def lead_supp(D, rescored=False):
    op, n = _rescore(D)
    return (f"Attempts as in Figure {S447.FIG_N}: one model variant, one prompting strategy and one of {len(D.OPS)} operations, "
            f"run once ({_rerun_clause()}; n = {len(D.rows):,} attempts)"
            + (f"; {n} attempts on one {D.dataset_of[op]} operation are re-scored by running their stored code "
               f"again (no model call)"
               if rescored else "") + ".")


def lead_supp15(D):
    """Supplementary Figure 15's opening (Valerio, 8 Nov, editor row 45): the attempt and the pair defined in full
    (the plate's key defines the four pair outcomes), with no reference to Figure 7 and no n tag (only panel f derives statistics, and states
    its n); every count from the rows."""
    op, n = _rescore(D)
    return (f"An attempt is one model variant (a model at one thinking setting), one prompting strategy and one of "
            f"{len(D.OPS)} data-analysis operations on two datasets (airway RNA-seq and NCCTG lung survival), run once "
            f"({_rerun_clause()}); {n} attempts on one {D.dataset_of[op]} operation are re-scored by running their "
            f"stored code again. A pair is one variant on one operation under a repeated-attempt strategy and under "
            f"the single-attempt strategy of its family.")


def lead_supp14(D):
    """Supplementary Figure 14's opening (Valerio, 8 Nov, editor row 45): the attempt defined in full, with no
    reference to Figure 7 and no n tag (the plate derives no statistics); every count from the rows."""
    return (f"An attempt is one model variant (a model at one thinking setting), one prompting strategy and one of "
            f"{len(D.OPS)} data-analysis operations on two datasets (airway RNA-seq and NCCTG lung survival), run once "
            f"({_rerun_clause()}); {len(D.rows):,} attempts in all ({len(D.VARS)} variants {_B_TIMES} "
            f"{len(D.STRATS)} strategies {_B_TIMES} {len(D.OPS)} operations). An attempt passes when its code returns "
            f"values matching the reference.")


def lead_supp16(D):
    """Supplementary Figure 16's opening (Valerio, 8 Nov, editor row 45): the attempt and the three prompting families
    defined in full, with no reference to Figure 7 and no n tag (each panel states its own n where it derives
    statistics); the re-score named (audit 27 Oct F2); every count from the rows."""
    op, n_rs = _rescore(D)
    return (f"An attempt is one model variant (a model at one thinking setting), one prompting strategy and one of "
            f"{len(D.OPS)} data-analysis operations, run once ({_rerun_clause()}). An attempt passes when its code returns values matching the reference; {n_rs} attempts on one "
            f"{D.dataset_of[op]} operation pass on running their stored code again (no model call).")


def _rows_words16(D):
    """Supplementary Figure 16, panels a and c: the row order in full, each panel's own words (no 'as in a')."""
    return f"Rows: {D.blocks[0][0]}, then {D.blocks[1][0]} variants, each high to low by free-form pass rate."


# D299: sheet Supplementary Fig. 15f (B1, sheet Fig. 7d until 7 Nov), its columns and the words that describe them
_B1_SHEET_COLS = ("part", "strategy", "against", "variant", "model", "setting", "gemini", "n_pairs", "rescued", "lost",
                  "both_passed", "both_failed", "n_operations", "change_pct_points", "net_change_pct_points",
                  "interval_95_low_pct_points", "interval_95_high_pct_points", "n_variants", "box_q1_pct_points",
                  "box_median_pct_points", "box_q3_pct_points", "box_min_pct_points", "box_max_pct_points")
_B1_SHEET_TXT = ("'contrast' rows, per repeated-attempt strategy and the strategy it is compared with the pairs, those "
                f"rescued, lost, both passed and both failed, the net change in percentage points (the diamond) and "
                f"its two-sided 95% percentile interval from {BOOT_N:,} resamples of the operations (seed "
                f"{BOOT_SEED}); 'variant' rows, per contrast and model variant (model, thinking setting, Gemini or "
                f"not) the pairs rescued and lost over its operations and its change in percentage points (the dot); "
                "'contrast (not drawn)' and 'variant (not drawn)' rows, the same as the 'contrast' and 'variant' rows "
                "for every other strategy against free-form, a 'variant (not drawn)' row also holding the pairs both "
                "passed and both failed over its operations; 'box (not drawn)' rows, per contrast (drawn or not) and "
                "model group (Gemini 1, open-weight 0) the variants, the median, quartiles (numpy's linear "
                "percentiles), minimum and maximum of their changes in percentage points.")
# draw_plate() stops when a Supplementary sheet named here has other columns, so its words cannot drift from it either
SUPP_SHEET_COLS = {"Supplementary Fig. 15f": _B1_SHEET_COLS}

# Source Data Fig. 6's caption, sheet by sheet (consistency audit F9, 25 Oct: the form of Figures 1 to 5's captions).
# draw_plate() stops when a sheet's columns differ from the ones named here, so the words cannot drift from the sheet.
SD_MAIN_SHEETS = {
    S447.sheet_name("a"): (("part", "grid_row", "grid_column", "variant", "block", "strategy", "family", "passes", "attempts",
                 "pass_rate_pct", "structured_passes", "structured_attempts", "free_form_passes", "free_form_attempts",
                 "gap_points", "gap_sign", "gap_size_points"),
                "one row per cell of the grid with its place on the plate (grid row and column) and its model group "
                "('block': Gemini or open-weight, blank on the 'all variants pooled' rows): 'strategy' rows, per "
                "model variant and strategy the passes, attempts and pass rate (%); 'family pooled' rows, the same "
                "pooled over each family's strategies; 'structured minus free-form' rows, per variant the structured "
                "and free-form passes and attempts, the difference in percentage points and the sign and size "
                "printed; 'all variants pooled' rows (not drawn), per family the passes, attempts and pass rate (%) "
                "over all variants, and the same structured minus free-form difference over all variants."),
    S447.sheet_name("b"): (("part", "variant", "variant_id", "tier", "family", "operation", "passes", "attempts",
                 "pass_rate_pct", "n_operations", "median_pct", "q1_pct", "q3_pct", "min_pct", "max_pct"),
                "'operation' rows, per difficulty tier, family and operation the passes, attempts and pass rate (%) "
                "with all variants pooled, the dots; 'box' rows, per tier and family the operations, the median, quartiles "
                "(numpy's linear percentiles), minimum and maximum of those pass rates."),
    S447.sheet_name("c"): (("model_group", "strategy", "strategy_id", "family", "outcome", "attempts", "attempts_in_bar",
                 "share_pct", "start_pct"),
                "per model group (Gemini or open-weight), strategy and outcome the attempts, the attempts in the bar, "
                "their share (%) and where the segment starts (%)."),
}

# D299 (Valerio, 7 Nov, "O1"): panel d (B1) left for Supplementary Figure 15f; c (X1) spans the row
MAIN = {"n": S447.FIG_N, "rows": [["H1", "K1"], ["X1"]], "lead": lead_main, "kinds": ("family", "outcome"),
        "title": "Code-generation pass rates by prompting strategy, task difficulty and outcome"}
SUPP = [   # D302 (Valerio, 7 Nov, "Q1: drop them"): the manuscript's order of first citation, 14 to 16 (12, 23 and 13
    # under D257); difficulty, operations and cost (21, 22, 24, not cited) dropped
    {"n": 14, "slug": "failures", "rows": [["X4"]], "kinds": ("outcome",), "lead": lead_supp14,
     "title": "How code-generation attempts failed, per model variant"},
    # B1b ("best_of_3", 22 before D257) dropped, 3 Nov (D222): its values are rows of sheet Supplementary Fig. 15f not drawn
    {"n": 15, "rescored": True, "slug": "pairs", "rows": [["B4"]], "kinds": ("comparison",), "lead": lead_supp15,   # f: B1 (D299)
     "title": "Paired outcomes and net change of repeated against single attempts"},
    {"n": 16, "rescored": True, "slug": "models", "rows": [["G4", "C2"], ["X2"]], "kinds": ("family", "outcome"),
     "lead": lead_supp16,
     "title": "Structured prompting, thinking setting and dataset, model by model"},
]


def layout(rows):
    """Slots (x, y) per panel id, and the page height: panels at their own size, GAP_MM apart, rows top to bottom."""
    place, y = {}, 0.0
    for r in rows:
        x = 0.0
        for pid in r:
            place[pid] = (x, y)
            x += PANELS[pid][0][0] + GAP_MM
        if x - GAP_MM > PAGE_W + 1e-6:
            raise SystemExit(f"row {r} is {x - GAP_MM:.2f} mm wide, the page {PAGE_W}")
        y += max(PANELS[pid][0][1] for pid in r) + GAP_MM
    return place, y - GAP_MM


def stamp_of(D, final):
    vs, total, left = D.design
    n = len(D.rows)
    if final and n != total:
        raise SystemExit(f"--final: {n} of {total} attempts of the design stored; the plate is still provisional")
    done = sum(1 for v in vs if sum(1 for r in D.rows if r["variant_id"] == v) == S447.PER_VARIANT)
    when = S447.iso_local(D.notes["newest_answers_mtime"])
    if final:
        return f"FINAL: {n:,} of {total:,} attempts, records of {when}", ""
    return (f"PROVISIONAL: {n:,} of {total:,} attempts, {done} of {len(vs)} variants complete, records of {when}; "
            f"after the S4 reruns (D75, D80 V1, D81)", f" (provisional, {n} of {total})")


# D155: the files each panel family reads beside Data's own inputs, recorded in the provenance of every plate that
# holds such a panel (by the panel id's first letter), so a plate's recorded inputs never depend on which plates were
# drawn before it in the same run (they did until 26 October: B_numbers.json entered every later plate's record).
PANEL_READS = {"H": [], "K": [_K_J447], "X": [_X_FIG6_NUMBERS, _X_COVERAGE], "B": [_B_REFS[0]], "G": [_G_G4_JSON],
               "C": [_C_DRAFT_PATHS[0]]}
CODE = ["scripts/S447_fig6_panels.py", "scripts/S457_fig2_panels.py", "scripts/S478_fig6_thinking_gap.py",
        "scripts/S479_fig6_by_tier.py", "scripts/house_style.py",
        "scripts/figure_names.py"]        # the code that computes and draws; fig_repro (checks and byte normalising,
                                          # shared by every figure) is held by the plates' own byte equality instead


def plate_inputs(D, ids):
    """{file: sha256} of every input of a plate: Data's (the frozen records by the manifest's names, the manifest,
    S477's re-score, the frozen tar, LOCK.toml), S478's and S479's numbers, the ground truth, FIGURE_LOCK.toml, and
    the files its own panels read (PANEL_READS)."""
    rel = lambda p: str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    out = {**D.inputs, rel(J478): sha(J478), rel(J479): sha(J479), rel(GT): sha(GT),
           rel(S447.FIGURE_LOCK): sha(S447.FIGURE_LOCK)}
    for pid in ids:
        for p in PANEL_READS[pid[0]]:
            out[rel(p)] = sha(p)
    return out


def provenance(cmd, D, inputs):
    """No build time, HEAD or working-tree state (D155): the code that ran and every input are named by sha256 and
    the package versions are given, so the same code on the same frozen inputs writes this file byte for byte."""
    import matplotlib as _mpl
    import openpyxl as _ox
    import fitz as _fz
    return {"script": SCRIPT, "script_sha256": sha(Path(__file__)),
            "command": cmd,
            "code_sha256": {c: sha(ROOT / c) for c in CODE},
            "python": platform.python_version(),
            "packages": {"matplotlib": _mpl.__version__, "openpyxl": _ox.__version__, "pymupdf": _fz.VersionBind,
                         "numpy": np.__version__},
            "inputs_sha256": inputs,
            "model_calls": 0}


def committed_dir(spec, main):
    """The plate's folder in the repository: where its committed files are."""
    return OUT_MAIN if main else SUPP_DIR / f"supp_fig{spec['n']}_fig6_{spec['slug']}"


def _lock_equiv():
    """D204: scripts/lock_equiv.py, the locks equal to d66daa28 but for the second judge's machines."""
    import lock_equiv
    return lock_equiv


def check_committed_inputs(spec, main, inputs, accept):
    """D155: refuse (exit 2, nothing written) when an input the committed plate recorded has another sha256 now,
    unless its name is in accept (--accept-input, a deliberate change of that input). D160 (6), Q18 (audit 27 Oct
    F10): an input recorded on one side only (in the committed plate's provenance and not read now, or read now and
    not in the committed provenance) is refused the same way, unless its name is in accept. Returns the lines to
    print."""
    pf = committed_dir(spec, main) / (f"figure{spec['n']}_provenance.json" if main else
                                      f"supplementary_figure{spec['n']}_provenance.json")
    if not pf.exists():
        return [f"no committed provenance at {pf.relative_to(ROOT)}: nothing to compare"]
    old = json.loads(pf.read_text())["provenance"]["inputs_sha256"]
    import lock_equiv                       # D204: a lock equal to d66daa28 but for the second judge's machines
    same_lock = {"experiments/LOCK.toml"} if {old.get("experiments/LOCK.toml"), inputs.get("experiments/LOCK.toml")} \
        <= lock_equiv.EQUIVALENT else set()
    differ = sorted(k for k in old if k in inputs and old[k] != inputs[k] and k not in same_lock)
    refused = [k for k in differ if k not in accept]
    if refused:
        stop(f"plate {spec['n']}: {len(refused)} input(s) differ from what the committed plate recorded "
             f"({pf.relative_to(ROOT)}): " + "; ".join(f"{k} {old[k][:12]} now {inputs[k][:12]}" for k in refused[:5])
             + " (give --accept-input <name> for a deliberate change)")
    only_old, only_new = sorted(set(old) - set(inputs)), sorted(set(inputs) - set(old))
    one_side = [k for k in only_old + only_new if k not in accept]
    if one_side:
        stop(f"plate {spec['n']}: {len(one_side)} input(s) recorded on one side only "
             f"({pf.relative_to(ROOT)} against this build): "
             + "; ".join(f"{k} ({'only in the committed plate' if k in old else 'only now'})" for k in one_side[:5])
             + " (give --accept-input <name> for a deliberate change)")
    same = sum(1 for k in old if k in inputs and old[k] == inputs[k])
    lines = [f"inputs against {pf.relative_to(ROOT)}: {same} equal, {len(differ)} accepted as changed {differ}"]
    if only_old or only_new:
        lines.append(f"  accepted, recorded only in the committed plate: {only_old}; only now: {only_new}")
    return lines


def _quad(t, rend, fig):
    """A text's outline in mm: its unrotated box turned by its angle about the centre of its window extent."""
    import math
    bb = t.get_window_extent(rend)
    cx, cy = (bb.x0 + bb.x1) / 2 / fig.dpi * 25.4, (bb.y0 + bb.y1) / 2 / fig.dpi * 25.4
    r = t.get_rotation()
    if r % 360 == 0:
        return [(bb.x0 / fig.dpi * 25.4, bb.y0 / fig.dpi * 25.4), (bb.x1 / fig.dpi * 25.4, bb.y0 / fig.dpi * 25.4),
                (bb.x1 / fig.dpi * 25.4, bb.y1 / fig.dpi * 25.4), (bb.x0 / fig.dpi * 25.4, bb.y1 / fig.dpi * 25.4)]
    t.set_rotation(0)
    b0 = t.get_window_extent(rend)
    t.set_rotation(r)
    w, h = b0.width / fig.dpi * 25.4, b0.height / fig.dpi * 25.4
    c, s_ = math.cos(math.radians(r)), math.sin(math.radians(r))
    return [(cx + dx * c - dy * s_, cy + dx * s_ + dy * c) for dx, dy in
            ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def _overlap(p, q, pad):
    """Separating-axis test on two convex outlines: True when they overlap by more than pad on every axis. For two
    unrotated texts it is S457.finish_plate's box test exactly."""
    import math
    for poly in (p, q):
        for i in range(4):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % 4]
            nx, ny = y1 - y2, x2 - x1
            L = math.hypot(nx, ny) or 1.0
            pa = [(x * nx + y * ny) / L for x, y in p]
            qa = [(x * nx + y * ny) / L for x, y in q]
            if max(pa) <= min(qa) + pad or max(qa) <= min(pa) + pad:
                return False
    return True


def finish_plate_rotated(fig, W, H, paths, title):
    """S457.finish_plate's steps (ligatures off; every text inside the page and none on another, else no plate; PDF
    and SVG with no date or creator; the PNG the PDF rasterised at 600 dpi by MuPDF), with one difference: texts are
    compared by their rotated outlines (_quad, _overlap), so two 45-degree column labels whose screen-aligned boxes
    intersect but whose letters are apart (Figure 6a) are not refused. For unrotated texts the test is S457's. Only
    a plate holding a panel of ROTATED_LABEL_PANELS ends here (draw_plate)."""
    fig.canvas.draw()
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    off_page, crowded, boxes = [], [], []
    for t_ in fig.findobj(Text):
        if t_.get_visible() and t_.get_text().strip():
            bb = t_.get_window_extent(rend)
            x0_, x1_ = bb.x0 / fig.dpi * 25.4, bb.x1 / fig.dpi * 25.4
            y0_, y1_ = H - bb.y1 / fig.dpi * 25.4, H - bb.y0 / fig.dpi * 25.4
            if x0_ < -0.01 or y0_ < -0.01 or x1_ > W + 0.01 or y1_ > H + 0.01:
                off_page.append(f"{t_.get_text()!r} x {x0_:.1f}-{x1_:.1f} y {y0_:.1f}-{y1_:.1f}")
            boxes.append((t_.get_text(), _quad(t_, rend, fig)))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if _overlap(a[1], b[1], 0.05):
                crowded.append(f"{a[0]!r} / {b[0]!r}")
    if off_page or crowded:
        plt.close(fig)
        raise SystemExit(f"{title}: texts past the page {off_page[:3]} or on each other {crowded[:3]}; no plate")
    meta_pdf = {"Title": title, "Author": None, "Subject": None, "Keywords": None, "Creator": None,
                "Producer": None, "CreationDate": None, "ModDate": None}
    fig.savefig(paths["pdf"], facecolor="#FFFFFF", metadata=meta_pdf)
    fig.savefig(paths["svg"], facecolor="#FFFFFF", metadata={"Title": title, "Date": None, "Creator": None})
    plt.close(fig)
    import fitz
    pix = fitz.open(paths["pdf"])[0].get_pixmap(dpi=600, alpha=False)
    pix.set_dpi(600, 600)
    pix.save(paths["png"])


# build_order F4: every plate ends in S457.finish_plate. Figure 6a is the one exception, awaiting Valerio's ruling. Its
# column labels are rotated 45 degrees and S457.finish_plate compares each text's upright screen box, so it refuses the
# plate: Figure 6: texts past the page [] or on each other ["'gemini-3-flash (default)' / 'gemini-3-flash (low)'", ...];
# no plate. The letters of neighbouring labels are apart, so the refusal comes from the upright boxes alone. S457's
# function may not change during this build (build_order section 5), so a plate holding one of these panels ends in
# finish_plate_rotated.
ROTATED_LABEL_PANELS = {"H1"}


def precheck_digits(fig, printed):
    """Fail fast before saving: every visible text holding a digit is a tick label or in the printed map (S448 R8
    (6) holds the saved SVG to the same rule)."""
    ticks = set()
    for ax in fig.axes:
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            ticks.add(id(t))
    loose = [t.get_text() for t in fig.findobj(Text) if t.get_visible() and re.search(r"\d", t.get_text())
             and id(t) not in ticks and t.get_gid() not in printed]
    if loose:
        raise SystemExit(f"texts holding a digit with no printed entry: {loose[:6]}")


def run_checks(book, xlsx):
    wb = S447.read_sheets(xlsx)
    probs, n = [], 0
    for name, what, rows, col, got, tol in book.checks:
        want = [wb[name][i][col] for i in rows]
        for i, g, w in zip(rows, got, want):
            n += 1
            if w is None or abs(float(w) - g) > tol * max(1.0, abs(float(w))):
                probs.append(f"{name} {what}: row {i} {col} drawn {g!r}, workbook {w!r}")
        if len(got) != len(want):
            probs.append(f"{name} {what}: {len(got)} drawn, {len(want)} rows")
    return probs, n


def draw_plate(D, spec, out_dir, final, cmd, main, accept=()):
    """One plate: draw, save, workbook, numbers, legend, caption, provenance; read-back checks (a failure keeps
    nothing). cmd is the one command that builds the plate (recorded in its provenance). Before anything is written,
    every input the committed plate recorded must have the same sha256 now (check_committed_inputs(); D155). Returns
    the folder and the S448 command."""
    import fig_repro
    S447.figure_lock_agreed()
    n_fig = spec["n"]
    stamp, tag = stamp_of(D, final)
    ids0 = [pid for r in spec["rows"] for pid in r]
    inputs = plate_inputs(D, ids0)
    if spec["n"] != 99:
        for ln in check_committed_inputs(spec, main, inputs, accept):
            print(ln)
    hs.check_plate_kinds(spec.get("kinds", ()))          # one hue never means two things on one plate (D153 Q3)
    place, H = layout(spec["rows"])
    if H > PAGE_H_MAX - H_ROOM:
        raise SystemExit(f"plate {n_fig}: {H:.2f} mm high, the lock allows {PAGE_H_MAX}")
    ids = [pid for r in spec["rows"] for pid in r]
    multi = len(ids) > 1
    page = Page(PAGE_W, H)
    book = Book(prefix="" if main else f"s{n_fig}")
    legends = {}
    sheets_note = None                                  # a panel whose sheet is not one per letter says so (S23)
    for i, pid in enumerate(ids):
        (w, h), fn = PANELS[pid]
        letter = "abcdefgh"[i] if multi else ""
        F = Frame(page, place[pid][0], place[pid][1], w, h, letter)
        if main:
            name = S447.sheet_name(letter)
        else:
            name = f"Supplementary Fig. {n_fig}{letter}"
        out = fn(D, F, book.sheet(name)) or {}
        legends[pid] = (letter, out.get("legend", ""))
        sheets_note = out.get("sheets_note", sheets_note)
    precheck_digits(page.fig, book.printed)
    bad_colours = hs.check_figure_colours(page.fig)
    if bad_colours:
        raise SystemExit(f"plate {n_fig}: colours outside the house palette: {bad_colours}")
    base = f"Figure {n_fig}" if main else f"Supplementary Figure {n_fig}"
    sd_stem = f"Source Data Fig. {n_fig}" if main else f"Supplementary Figure {n_fig} data"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in set(out_dir.glob(f"{base}*")) | set(out_dir.glob(f"{sd_stem}*")):   # a Supplementary figure's two
        old.unlink()                                                                    # patterns overlap
    paths = {x: out_dir / f"{base}{tag}.{x}" for x in ("pdf", "svg", "png")}
    finish = finish_plate_rotated if ROTATED_LABEL_PANELS & set(ids) else S457.finish_plate
    finish(page.fig, PAGE_W, H, paths, title=base)
    fig_repro.check_pdf_deterministic(paths["pdf"])      # D155: no date in the PDF or the SVG
    fig_repro.check_svg_deterministic(paths["svg"])
    sheets = book.table()
    sd = out_dir / f"{sd_stem}{tag}.xlsx"
    S447.write_source_data(sheets, sd)                   # deterministic (fig_repro.deterministic_xlsx)
    fig_repro.check_xlsx_deterministic(sd)
    side = lambda what: out_dir / (f"figure{n_fig}_{what}.json" if main else
                                   f"supplementary_figure{n_fig}_{what}.json")
    numbers = side("numbers")
    numbers.write_text(json.dumps({"stamp": stamp, "what": f"every number the plate draws, sheet by sheet as "
                                   f"{sd.name} holds them (S448 R8 compares the workbook with this file)",
                                   "sheets": {nm: {"columns": c, "rows": r} for nm, c, r in sheets},
                                   "printed": book.printed}, indent=1, default=str) + "\n")
    probs, n_checked = run_checks(book, sd)
    title = spec["title"]
    # audit 27 Oct F2 (fig4_6): Supplementary Figures 16, 21, 22 and 15 name the lung_9 re-score ("rescored")
    lead = spec["lead"](D) if "lead" in spec else lead_supp(D, spec.get("rescored", False))
    head = f"**{base} | {title}.** {lead}"
    body = " ".join((f"**{lt}**, {txt}" if lt else txt) for lt, txt in legends.values())
    legend = (f"# {base}, title and legend (draft)\n\nWritten by `{SCRIPT}` from the plotted numbers. Data stamp: "
              f"{stamp}.\n\n{head} {body}\n")
    (out_dir / "legend_draft.md").write_text(legend)
    capf = out_dir / f"{sd_stem} caption{tag}.md"
    if main:                                       # the sheets described column by column, as Figures 1 to 5's
        got = {nm: tuple(c) for nm, c, _ in sheets}
        if got != {nm: cols for nm, (cols, _) in SD_MAIN_SHEETS.items()}:
            raise SystemExit(f"{sd_stem}: the sheets' columns are not the ones its caption describes: {got}")
        more = {S447.sheet_name("c"): _X_wrong_error_clause(D)}       # the clause FF32 moved here from Figure 6c's legend
        sheets_txt = "One sheet per panel. " + " ".join(f"Sheet {nm}: {txt}" + (f" {more[nm]}" if more.get(nm) else "")
                                                         for nm, (_, txt) in SD_MAIN_SHEETS.items())
        avail = (f"\n\nProposed Data Availability sentence: \"The source data for Figure {n_fig} is in "
                 f"Supplementary Data {n_fig + 1}.\"")   # D303: Data n + 1 (D302)
    else:
        bad_cols = {nm: tuple(c) for nm, c, _ in sheets if nm in SUPP_SHEET_COLS and tuple(c) != SUPP_SHEET_COLS[nm]}
        names = {nm for nm, _, _ in sheets}            # a sheet SUPP_SHEET_COLS names, missing from its figure's workbook
        bad_cols.update({nm: "missing" for nm in SUPP_SHEET_COLS
                         if re.sub(r"[a-z]+$", "", nm) in names and nm not in names})
        if bad_cols:
            raise SystemExit(f"{sd_stem}: the sheets' columns are not the ones its caption describes: {bad_cols}")
        sheets_txt, avail = sheets_note or f"One sheet per panel ({', '.join(nm for nm, _, _ in sheets)}).", ""
    capf.write_text(f"# {sd_stem}, caption\n\n**{sd_stem} | Numerical values plotted in {base}.** "
                    f"{'Provisional: drawn' if not final else 'Drawn'} from all {len(D.rows):,} attempts of the design "
                    f"({len(D.VARS)} model and thinking-setting variants), after the S4 reruns (D75, D80 V1, D81); every value "
                    f"will be redrawn from the full records by the same script. Data stamp: {stamp}. {sheets_txt} "
                    f"{_rescore_clause(D)} Generated by `uv run --frozen python {SCRIPT} "
                    f"{'figure' if main else 'supplementary'}` from the run records and S477's re-score.{avail}\n")
    prov = {"provenance": provenance(cmd, D, inputs), "reproduced": D.reproduced, "stamp": stamp, "page_mm": [PAGE_W, H],
            "panels": {pid: {"letter": legends[pid][0], "slot_mm": place[pid], "size_mm": PANELS[pid][0]}
                       for pid in ids},
            "figure_lock": {"path": str(S447.FIGURE_LOCK.relative_to(ROOT)), "sha256": sha(S447.FIGURE_LOCK)},
            "read_back": f"{n_checked} drawn values equal to the workbook" + (f"; FAILED: {probs[:5]}" if probs
                                                                               else ""),
            "files": {p.name: sha(p) for p in list(paths.values()) + [sd, capf, numbers, out_dir / "legend_draft.md"]}}
    side("provenance").write_text(json.dumps(prov, indent=1, default=str) + "\n")
    if probs:
        for p in list(paths.values()) + [sd, capf, numbers, side("provenance"), out_dir / "legend_draft.md"]:
            p.unlink(missing_ok=True)
        raise SystemExit(f"{base}: read-back FAILED, nothing kept: {probs[:5]}")
    words = len(re.sub(r"\*", "", f"{head} {body}").split())
    print(f"{base}: {PAGE_W:g} x {H:.1f} mm, panels {', '.join(f'{lt or chr(8211)} {pid}' for pid, (lt, _) in legends.items())}; "
          f"{n_checked} drawn values read back equal; {len(book.printed)} printed numbers mapped; legend {words} words")
    cmd = ["uv", "run", "--frozen", "python", "scripts/S448_figure_rules_check.py", "--figure", str(n_fig),
           "--dir", str(out_dir.relative_to(ROOT) if out_dir.is_relative_to(ROOT) else out_dir)]
    if not main:
        cmd.insert(-2, "--supplementary")
    return out_dir, cmd


def s448(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    lines = (r.stdout + r.stderr).strip().splitlines()
    verdicts = [ln for ln in lines if re.match(r"^\s*R\d+", ln) or "VERDICT" in ln.upper() or ln.startswith("S448")]
    print("  " + "\n  ".join((verdicts or lines)[-16:]))
    return r.returncode


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["figure", "supplementary", "all", "panel"])
    ap.add_argument("panel_id", nargs="?")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--dir")
    ap.add_argument("--out", help="write the plates under this folder (fig6/ and supp_fig<N>_fig6_<slug>/) instead of "
                                  "findings/figures_provisional/: a rebuild to compare with the committed plates")
    ap.add_argument("--accept-input", action="append", default=[], metavar="NAME",
                    help="an input (as the provenance names it) whose sha256 may differ from the committed plate's")
    a = ap.parse_args(argv)
    if a.out and Path(a.out).resolve().is_relative_to(ROOT):
        raise SystemExit("--out must be outside the repository (the plates' own place is the default)")
    _collect_panels()
    D = Data()
    rc = 0
    if a.command == "panel":
        if a.panel_id not in PANELS:
            raise SystemExit(f"no panel {a.panel_id!r}; have {sorted(PANELS)}")
        d = Path(a.dir).resolve()
        if d.is_relative_to(ROOT):
            raise SystemExit("panel --dir must be outside the repository")
        out, cmd = draw_plate(D, {"n": 99, "rows": [[a.panel_id]], "title": f"Panel {a.panel_id} alone"}, d,
                              False, f"uv run --frozen python {SCRIPT} panel {a.panel_id} --dir <dir>", main=False)
        return s448(cmd)
    jobs = []
    if a.command in ("figure", "all"):
        jobs.append((MAIN, True))
    if a.command in ("supplementary", "all"):
        jobs += [(s, False) for s in SUPP]
    for spec, is_main in jobs:
        missing = [p for r in spec["rows"] for p in r if p not in PANELS]
        if missing:
            raise SystemExit(f"figure {spec['n']}: panels not built yet: {missing}")
        d = committed_dir(spec, is_main)
        if a.out:
            d = Path(a.out).resolve() / d.name
        cmd = (f"uv run --frozen python {SCRIPT} {'figure' if is_main else 'supplementary'}"
               + (" --final" if a.final else ""))           # the plate's own command, however this run was called
        out, cmd = draw_plate(D, spec, d, a.final, cmd, main=is_main, accept=set(a.accept_input))
        rc |= s448(cmd)
    return rc


if __name__ == "__main__":
    sys.exit(main())
