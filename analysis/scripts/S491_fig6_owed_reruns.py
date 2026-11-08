#!/usr/bin/env python3
"""S491 - D155 A13, option O2 (findings/audits/scratch_repro_2026-10-26/INVENTORY.md F12): Figure 6's failed attempts
that owe a rerun, how far the structured minus free-form gap rests on them and on two variants, and what the gpt-oss:20b
high failures are, from the frozen S2 records.

WHY. The audit of 25 October stated, from scratch code only (SCR/audit_1025/fig6_verify/verify.py,
SCR/audit_1025/story_skeptic/fig6_check.py, SCR/fig6_alt/STORY.md:160): that all 108 failed attempts owing the D80 V1
or D81 rerun are structured; the pooled gap -22.4 points, -18.3 without gemma3:27b, -14.1 also without gpt-oss:20b high;
tier gaps -1.2, -17.2 and -22.7 in that last design, without gemma3:27b and gpt-oss:20b high (the full design's are
-14.9, -24.6 and -26.9; audit 27 Oct F9); and "66 of 69" gpt-oss:20b high structured failures mechanical, where S481's
Supplementary Figure 16b counts 67 "tool or call failure, other" for that variant. D155: no number without a committed
script. S481 is not edited (O2); this script reads S481's rows.

WHAT IS READ. The frozen copy of the four S2 clones' sinks after the S4 reruns, s2_after_s4_20261105.tar, the copy
Figure 7 reads (D287 O4, 7 Nov; s2_length_retries_20261021.tar, INVENTORY.md A1c, before), through
scripts/fig_repro.frozen(), which checks the tar's sha256 against findings/recompute/frozen_inputs/SHA256SUMS and every
extracted file against its member list. Every run of the committed records_manifest.json is located in it (machine,
clone, run id) and every file the manifest lists must equal the manifest's sha256 there, else exit 2. S447's own loader
then reads it, through S481's Data (S447.load_mirror, keep_design, fail_kind; S478's families; the ground truth's
tiers): nothing here re-implements them. Two cases, printed (not written, so the output is the same
bytes in both):
  - S447 of D155 (it has frozen_copy()): S447 reads the frozen copy itself and S445's anchor runs; nothing is changed.
  - S447 before D155 (it reads the gitignored findings/runs/): a temporary folder lays the copy out as findings/runs/
    <run id>, with records_manifest.json and S477's lung_9 re-score, all as symbolic links to the frozen or committed
    files, and S447 is pointed at it. S447.reproduce() (S445's attempt counts) is not run there: 3 of the 70 studio and
    1 of the 10 laptop answers.json S445 read are not in the s2 tar (S445's own paths are outside the repository).
The anchors below hold either way. No model call; no ssh; no live pull.

REPRODUCE FIRST (README.md:75-79). Exit 2, nothing written, unless:
  (1) S481's Data reproduces itself on the frozen copy (2,420 attempts), and every table of
      findings/recompute/S478_fig6_thinking_gap.json and S479_fig6_by_tier.json equal (S481's own check);
  (2) S447.rerun_tally() on these attempts equals findings/figures_provisional/fig6/fig6_numbers.json
      claims_support.reruns_owed (every count, in total and per variant), and the owed set built here holds exactly
      the tally's failed with a D80 V1 event + with add_cell written as text (D81) - with both;
  (3) the pooled gap from these rows equals the gap from S479 by_group's committed counts;
  (4) gpt-oss:20b (high)'s outcome counts over its 220 attempts equal S481's committed Supplementary Figure 16b sheet.
  On s2_length_retries_20261021 (before D287 O4) these were 1,660 passes, 37 + 75 - 4 = 108 owed, a gap of -22.4
  (483 of 880 minus 510 of 660) and 13b's passed 112, wrong values 3, no result 38, tool or call failure, other 67.

DEFINITIONS.
  owed       a failed attempt with a D80 V1 event on any generator call (a tool-call parse error, a stall, or an
             Ollama HTTP 500 or dropped connection; never Gemini) or with add_cell written as text (D81), as
             S447.rerun_tally() counts them.
  gap        100 x (structured passes / attempts - free-form passes / attempts), pooled over the variants named.
  bound      the gap if every owed failed attempt passed on its rerun (the most the reruns can move it).
  tool or call failure   S481's _X_MECH_OTHER kinds: tool-call parse error, tool call written as text, stall, other
             call error, step produced no cell and no error. "No code" is apart: the attempt stored no code, which
             the records do not tie to a call.

COMMANDS (repository root):
  uv run python scripts/S491_fig6_owed_reruns.py            reproduce, then write
                                                            findings/recompute/S491_fig6_owed_reruns/
                                                            S491_fig6_owed_reruns.json (no write time in it)
  uv run python scripts/S491_fig6_owed_reruns.py selftest   gap, owed and split functions on synthetic rows (no file)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro  # noqa: E402

SCRIPT = "scripts/S491_fig6_owed_reruns.py"
SET = "s2_after_s4_20261105"   # D287 O4 (7 Nov): the records Figure 7 reads (S447 FROZEN_S2); s2_length_retries_20261021 before
MANIFEST_REL = "findings/figures_provisional/fig6/records_manifest.json"
Q4_REL = "findings/recompute/S477_lung9_rescore.json"
FIG6_NUMBERS = ROOT / "findings/figures_provisional/fig6/fig6_numbers.json"
SUPP19 = ROOT / "findings/figures_provisional/supp_fig16_fig6_models/supplementary_figure16_numbers.json"
J478 = ROOT / "findings/recompute/S478_fig6_thinking_gap.json"
J479 = ROOT / "findings/recompute/S479_fig6_by_tier.json"
GT = ROOT / "experiments/mentori/tests/experiments_v2/datasets/coder_ground_truth.json"
OUT = ROOT / "findings/recompute/S491_fig6_owed_reruns/S491_fig6_owed_reruns.json"
IMPORTED = ["scripts/S447_fig6_panels.py", "scripts/S478_fig6_thinking_gap.py", "scripts/S479_fig6_by_tier.py",
            "scripts/S481_fig6_d138.py", "scripts/S457_fig2_panels.py", "scripts/fig_repro.py"]

GEMMA = "gemma3-27b+default"
GPT_HIGH = "gpt-oss-20b+high"
TIERS = ["simple", "medium", "complex"]
SUBSETS = [("all 11 variants", ()), ("without gemma3:27b", (GEMMA,)),
           ("without gemma3:27b and gpt-oss:20b (high)", (GEMMA, GPT_HIGH))]
TOOL_OR_CALL = ["tool-call parse error", "tool call written as text", "stall", "other call error",
                "step produced no cell and no error"]          # S481._X_MECH_OTHER, checked equal at run time
INVENTORY_F12 = {   # INVENTORY.md:77 (AUDIT_2026-10-25.md:22,444,578; audit result.json:33,93)
    "owed": 108, "owed_structured": 108, "gap_all": -22.4, "bound_all": -10.1, "gap_without_gemma3": -18.3,
    "gap_without_gemma3_and_gpt_oss_high": -14.1, "tier_gaps": [-1.2, -17.2, -22.7],
    "gpt_oss_high_structured_mechanical": "66 of 69", "supp19b_tool_or_call_failure_other": 67}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stop(msg: str):
    print(f"NOT REPRODUCED: {msg}; nothing written", file=sys.stderr)
    sys.exit(2)


def r1(x: float) -> float:
    """Half away from zero at one decimal, after removing float noise (S447.half_up's rule)."""
    x = round(x, 9)
    s = 1 if x >= 0 else -1
    return s * int(abs(x) * 10 + 0.5) / 10


# ------------------------------------------------------------------------------------------------- pure functions
def gap(rows, drop=(), tier=None) -> float:
    """Structured minus free-form pass rate in points over the rows of the variants not dropped (one tier or all)."""
    rr = [r for r in rows if r["variant_id"] not in drop and (tier is None or r["tier"] == tier)]
    st = [r["passed"] for r in rr if r["family"] == "structured"]
    ff = [r["passed"] for r in rr if r["family"] == "free-form"]
    return 100 * (sum(st) / len(st) - sum(ff) / len(ff))


def is_owed(passed: bool, gen_model: str, fl: set) -> bool:
    """S447.rerun_tally()'s rule for one failed attempt: a D80 V1 event (not Gemini) or add_cell as text (D81)."""
    if passed:
        return False
    ev = [] if gen_model.startswith("gemini::") else [e for e in ("parse", "stall", "retry_call_error") if e in fl]
    return bool(ev) or "as_text" in fl


def split(kinds: Counter) -> dict:
    tc = sum(n for k, n in kinds.items() if k in TOOL_OR_CALL)
    return {"failed": sum(kinds.values()), "by_kind": dict(sorted(kinds.items(), key=lambda x: (-x[1], x[0]))),
            "tool_or_call_failure": tc, "no_code": kinds.get("no code", 0),
            "tool_or_call_failure_or_no_code": tc + kinds.get("no code", 0),
            "code_ran_raised_or_wrong": kinds.get("code raised or timed out", 0)
            + kinds.get("result wrong or missing", 0)}


# ------------------------------------------------------------------------------------------------- frozen records
def check_copy(copy: Path, man: dict) -> dict:
    """{run id: its folder in the frozen copy}, every file the manifest lists for the run checked by sha256."""
    dirs = {}
    for rid, info in sorted(man["runs"].items()):
        src = copy / info["machine"] / Path(info["clone"]).name / "runs" / rid
        if not src.is_dir():
            stop(f"{rid} ({info['machine']} {info['clone']}) is not in {SET}")
        for name, f in info["files"].items():
            if sha(src / name) != f["sha256"]:
                stop(f"{src / name} differs from records_manifest.json")
        dirs[rid] = src
    return dirs


def stage(dirs: dict, tmp: Path):
    """The frozen copy laid out as S447 before D155 reads it: findings/runs/<run id>, the manifest and S477's
    re-score, as symbolic links in a temporary folder."""
    runs = tmp / "findings" / "runs"
    runs.mkdir(parents=True)
    for rid, src in dirs.items():
        (runs / rid).symlink_to(src, target_is_directory=True)
    for rel in (MANIFEST_REL, Q4_REL):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).symlink_to(ROOT / rel)


def load(copy: Path):
    """S481's Data on the frozen copy, plus the call flags S447's loader built. Returns (S481, S447, D, attempts kept,
    flags, notes, files checked, how S447 was pointed at the copy)."""
    import S481_fig6_d138 as S481
    S447 = S481.S447
    if S481._X_MECH_OTHER != TOOL_OR_CALL:
        stop(f"S481's tool or call kinds are {S481._X_MECH_OTHER}, not {TOOL_OR_CALL}")
    man = json.loads((ROOT / MANIFEST_REL).read_text())
    dirs = check_copy(copy, man)
    checked = sum(len(info["files"]) for info in man["runs"].values())
    saved = {k: getattr(S447, k) for k in ("ROOT", "RUNS", "MANIFEST", "Q4_RESCORE", "reproduce", "load_mirror")}
    cache = {}

    def load_mirror():
        cache["m"] = saved["load_mirror"]()
        return cache["m"]
    cwd = os.getcwd()
    try:
        S447.load_mirror = load_mirror
        if hasattr(S447, "frozen_copy"):
            # S447 of D155 reads the frozen copy itself (run_dirs()) and finds S445's files in frozen sets only:
            # nothing staged, S445's anchor runs
            mode = "S447 reads the frozen copy itself (frozen_copy, run_dirs); S445 anchor run by S481 Data"
            D = S481.Data()
        else:
            mode = ("S447 before D155: the frozen copy staged as findings/runs/ in a temporary folder; S445 anchor "
                    "not run (4 of the 80 answers.json S445 read are in no frozen set at this S447)")
            with tempfile.TemporaryDirectory(prefix="S491_") as t:
                tmp = Path(t)
                stage(dirs, tmp)
                S447.ROOT, S447.RUNS = tmp, tmp / "findings" / "runs"
                S447.MANIFEST, S447.Q4_RESCORE = tmp / MANIFEST_REL, tmp / Q4_REL
                S447.reproduce = lambda: [{"S445": "not run"}]
                os.chdir(tmp)
                D = S481.Data()
    finally:
        os.chdir(cwd)
        for k, v in saved.items():
            setattr(S447, k, v)
    atts, flags, inputs, notes = cache["m"]
    kept = S447.keep_design(atts)[0]
    want_inputs = {f"findings/runs/{rid}/{n}": f["sha256"] for rid, info in man["runs"].items()
                   for n, f in info["files"].items() if n in ("answers.json", "calls.jsonl")}
    got_inputs = {k: v for k, v in inputs.items() if k.startswith("findings/runs/")}
    if got_inputs != want_inputs:
        stop("S447's loader read other files than the manifest's answers.json and calls.jsonl")
    return S481, S447, D, kept, flags, notes, checked, mode


def main(argv):
    if argv[1:] == ["selftest"]:
        sys.exit(0 if selftest() else 1)
    if argv[1:]:
        sys.exit(f"usage: uv run python {SCRIPT} [selftest]")
    copy = fig_repro.frozen(SET, SET)
    S481, S447, D, kept, flags, notes, checked, mode = load(copy)
    rows = D.rows
    print(f"frozen copy: {checked} manifest files equal; S481 Data reproduced on it; {mode}")

    # (2) the owed tally against the committed one
    tally = S447.rerun_tally(kept, flags, notes["attempts_by_machine"])
    cs = json.loads(FIG6_NUMBERS.read_text())["claims_support"]["reruns_owed"]
    ints = lambda d: {k: v for k, v in d.items() if isinstance(v, int) and not isinstance(v, bool)}
    if ints(tally["totals"]) != ints(cs["totals"]):
        stop(f"rerun totals {ints(tally['totals'])} are not fig6_numbers.json's {ints(cs['totals'])}")
    for v, x in cs["by_variant"].items():
        if ints(tally["by_variant"].get(v, {})) != ints(x):
            stop(f"{v}: rerun counts differ from fig6_numbers.json")
    t = tally["totals"]
    owed_n = t["failed_with_d80v1_event"] + t["failed_with_add_cell_as_text"] \
        - t["failed_with_add_cell_as_text_and_d80v1_event"]
    owed_keys = {(S447.variant_of(a["run_id"]), S447.config_of(a["run_id"]), a["op_id"]) for a in kept
                 if is_owed(bool(a["passed"]), a["gen_model"], flags.get(a.get("ctx_uid"), set()))}
    if len(owed_keys) != owed_n:
        stop(f"owed set {len(owed_keys)}, tally {owed_n}")

    # (3) the pooled gap
    g_all = gap(rows)
    s479 = json.loads(J479.read_text())["by_group"]
    st, ff = s479["structured"]["all"]["passes"], s479["free-form"]["all"]["passes"]
    g479 = 100 * (st[0] / st[1] - ff[0] / ff[1])
    if abs(g_all - g479) > 1e-9:
        stop(f"pooled gap {g_all} is not S479's {g479}")

    # (4) Supplementary Figure 16b, gpt-oss:20b (high)
    s19 = json.loads(SUPP19.read_text())["sheets"]["Supplementary Fig. 16b"]
    s19 = [dict(zip(s19["columns"], r)) for r in s19["rows"]]
    want19 = {r["outcome"]: r["attempts"] for r in s19 if r["part"] == "bar" and r["variant"] == "gpt-oss:20b (high)"}
    hi = [r for r in rows if r["variant_id"] == GPT_HIGH]
    got19 = dict(Counter(r["outcome5"] for r in hi))
    if got19 != want19:
        stop(f"gpt-oss:20b (high) outcomes {got19} are not Supplementary Fig. 16b's {want19}")
    print(f"reproduced: {len(rows):,} attempts, {sum(r['passed'] for r in rows):,} passes; owed {t['failed_with_d80v1_event']} + "
          f"{t['failed_with_add_cell_as_text']} - {t['failed_with_add_cell_as_text_and_d80v1_event']} = {owed_n} "
          f"(fig6_numbers.json equal); pooled gap {r1(g_all)} (S479 equal); Supp. Fig. 16b gpt-oss:20b (high) {want19}")

    # ---- the new numbers
    by_key = {(r["variant_id"], r["strategy"], r["op_id"]): r for r in rows}
    owed_rows = [by_key[k] for k in sorted(owed_keys)]
    owed_family = dict(Counter(r["family"] for r in owed_rows))
    owed_variant_family = {f"{v} | {f}": n for (v, f), n in sorted(Counter((r["variant_id"], r["family"])
                                                                          for r in owed_rows).items())}
    owed_kind = dict(Counter(r["fail_kind"] for r in owed_rows).most_common())
    up = [dict(r, passed=1) if (r["variant_id"], r["strategy"], r["op_id"]) in owed_keys else r for r in rows]
    gaps = []
    for name, drop in SUBSETS:
        gaps.append({"variants": name, "left_out": list(drop),
                     "gap_points": gap(rows, drop), "gap_printed": r1(gap(rows, drop)),
                     "by_tier_points": {k: gap(rows, drop, k) for k in TIERS},
                     "by_tier_printed": {k: r1(gap(rows, drop, k)) for k in TIERS},
                     "bound_if_every_owed_failure_passed": gap(up, drop),
                     "bound_printed": r1(gap(up, drop)),
                     "bound_by_tier_printed": {k: r1(gap(up, drop, k)) for k in TIERS}})
    hi_st = Counter(r["fail_kind"] for r in hi if r["family"] == "structured" and not r["passed"])
    hi_all = Counter(r["fail_kind"] for r in hi if not r["passed"])
    tcf = [r for r in hi if r["outcome5"] == "tool or call failure, other"]
    j478 = json.loads(J478.read_text())["variants"][GPT_HIGH]["structured_fail_kinds"]
    if dict(hi_st) != j478:
        stop(f"gpt-oss:20b (high) structured failure kinds {dict(hi_st)} are not S478's {j478}")
    failure = {
        "gpt_oss_20b_high_structured": split(hi_st) | {"equal_to_S478_structured_fail_kinds": True},
        "gpt_oss_20b_high_all_strategies": split(hi_all),
        "supp19b_tool_or_call_failure_other": {
            "count": len(tcf),
            "what": "S481.outcome5(): every failed attempt whose kind is not code raised or timed out, result wrong "
                    "or missing, or length stop (Supplementary Fig. 16b's 'tool or call failure, other')",
            "by_family": dict(Counter(r["family"] for r in tcf)),
            "by_kind": dict(Counter(r["fail_kind"] for r in tcf).most_common())},
    }

    # ---- against the inventory's values
    ga, gg, gh = gaps
    hs = failure["gpt_oss_20b_high_structured"]
    found_tiers = {g["variants"]: [g["by_tier_printed"][k] for k in TIERS] for g in gaps}
    tier_match = [n for n, v in found_tiers.items() if v == INVENTORY_F12["tier_gaps"]]
    cmp_ = [
        ("owed", INVENTORY_F12["owed"], owed_n),
        ("owed_structured", INVENTORY_F12["owed_structured"], owed_family.get("structured", 0)),
        ("gap_all", INVENTORY_F12["gap_all"], ga["gap_printed"]),
        ("bound_all", INVENTORY_F12["bound_all"], ga["bound_printed"]),
        ("gap_without_gemma3", INVENTORY_F12["gap_without_gemma3"], gg["gap_printed"]),
        ("gap_without_gemma3_and_gpt_oss_high", INVENTORY_F12["gap_without_gemma3_and_gpt_oss_high"],
         gh["gap_printed"]),
        ("tier_gaps (simple, medium, complex)", INVENTORY_F12["tier_gaps"],
         {"subset whose tier gaps equal": tier_match, "all subsets": found_tiers}),
        ("gpt_oss_high_structured_mechanical", INVENTORY_F12["gpt_oss_high_structured_mechanical"],
         f"{hs['tool_or_call_failure']} of {hs['failed']} tool or call failures; "
         f"{hs['tool_or_call_failure_or_no_code']} of {hs['failed']} with no code counted"),
        ("supp19b_tool_or_call_failure_other", INVENTORY_F12["supp19b_tool_or_call_failure_other"], len(tcf)),
    ]
    against = [{"number": n, "inventory": a, "S491": b,
                "equal": (a == b) if not isinstance(b, (dict, str)) else None} for n, a, b in cmp_]

    for g in gaps:
        print(f"{g['variants']}: gap {g['gap_printed']} (tiers {g['by_tier_printed']}), bound {g['bound_printed']}")
    print(f"owed {owed_n}: by family {owed_family}")
    print(f"gpt-oss:20b (high) structured: {hs['tool_or_call_failure']} of {hs['failed']} tool or call failures, "
          f"{hs['tool_or_call_failure_or_no_code']} with no code; Supp 13b's {len(tcf)}: {failure['supp19b_tool_or_call_failure_other']['by_family']}")

    inputs = [(fig_repro.RECOMPUTE / "frozen_inputs" / "members" / f"{SET}.sha256", "the tar's member list"),
              (ROOT / MANIFEST_REL, "records manifest: the runs read and every file's sha256"),
              (ROOT / Q4_REL, "S477's lung_9 re-score, applied by S447's loader"),
              (GT, "ground truth: operation tiers"),
              (J478, "anchor: S478 (S481 Data's check; gpt-oss:20b high structured kinds)"),
              (J479, "anchor: S479 (S481 Data's check; the pooled gap)"),
              (FIG6_NUMBERS, "anchor: claims_support.reruns_owed"),
              (SUPP19, "anchor: Supplementary Fig. 16b")]
    sums = fig_repro._read_sums(fig_repro.RECOMPUTE / "frozen_inputs" / "SHA256SUMS")
    out = {
        "provenance": {
            "script": SCRIPT, "script_sha256": sha(Path(__file__)),
            "command": f"uv run python {SCRIPT}",
            "frozen_set": {"tar": f"{SET}.tar", "sha256": sums[f"{SET}.tar"],
                           "manifest_files_checked": checked, "read_through": "scripts/fig_repro.py frozen()"},
            "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "role": role} for p, role in inputs],
            "code_imported": IMPORTED,
            "model_calls": 0,
            "ported_from": ["SCR/audit_1025/fig6_verify/verify.py", "SCR/audit_1025/story_skeptic/fig6_check.py"]},
        "definitions": {k: " ".join(v.split()) for k, v in (
            ("owed", "a failed attempt with a D80 V1 event on any generator call (tool-call parse error, stall, or "
                     "an Ollama HTTP 500 or dropped connection; never Gemini) or add_cell written as text (D81), as "
                     "S447.rerun_tally() counts them"),
            ("gap", "100 x (structured passes / attempts - free-form passes / attempts), pooled over the variants"),
            ("bound", "the gap if every owed failed attempt passed on its rerun"),
            ("tool_or_call_failure", "S481._X_MECH_OTHER: " + ", ".join(TOOL_OR_CALL)))},
        "reproduced": {"attempts": len(rows), "passes": sum(r["passed"] for r in rows),
                       "S478_S479_equal": D.reproduced["S478_equal"] and D.reproduced["S479_equal"],
                       "reruns_owed_totals": ints(tally["totals"]), "owed": owed_n,
                       "equal_to": "fig6_numbers.json claims_support.reruns_owed (totals and per variant)",
                       "pooled_gap_points": g_all, "pooled_gap_printed": r1(g_all),
                       "supp19b_gpt_oss_20b_high": want19},
        "owed": {"count": owed_n, "by_family": owed_family, "structured_share": owed_family.get("structured", 0) / owed_n,
                 "by_variant_and_family": owed_variant_family, "by_fail_kind": owed_kind},
        "gaps": gaps,
        "failure_split": failure,
        "against_inventory_F12": against,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


# ------------------------------------------------------------------------------------------------- test
def selftest() -> bool:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok &= bool(cond)

    def row(v, f, t, p):
        return {"variant_id": v, "family": f, "tier": t, "passed": p}
    rows = ([row("A", "structured", "simple", 1)] * 3 + [row("A", "structured", "simple", 0)]
            + [row("A", "free-form", "simple", 1)] * 2 + [row("B", "structured", "medium", 0)] * 2
            + [row("B", "free-form", "medium", 1)] * 2)
    check("gap pooled: 3/6 - 4/4 = -50", abs(gap(rows) + 50) < 1e-9)
    check("gap without B: 3/4 - 2/2 = -25", abs(gap(rows, ("B",)) + 25) < 1e-9)
    check("gap by tier: medium 0/2 - 2/2 = -100", abs(gap(rows, (), "medium") + 100) < 1e-9)
    check("owed: a parse error on Ollama", is_owed(False, "ollama::x", {"parse"}))
    check("not owed: a parse error on Gemini", not is_owed(False, "gemini::x", {"parse"}))
    check("owed: add_cell as text on Gemini (D81)", is_owed(False, "gemini::x", {"as_text"}))
    check("not owed: a passing attempt", not is_owed(True, "ollama::x", {"parse", "as_text"}))
    check("not owed: a length stop alone", not is_owed(False, "ollama::x", {"length"}))
    s = split(Counter({"tool call written as text": 40, "step produced no cell and no error": 26, "no code": 1,
                       "code raised or timed out": 1, "result wrong or missing": 1}))
    check("split: 66 tool or call, 67 with no code, 2 code ran, 69 failed",
          (s["tool_or_call_failure"], s["tool_or_call_failure_or_no_code"], s["code_ran_raised_or_wrong"],
           s["failed"]) == (66, 67, 2, 69))
    check("r1 rounds half away from zero: -22.35 to -22.4, 10.05 to 10.1, -0.04 to -0.0",
          (r1(-22.35), r1(10.05), r1(-0.04)) == (-22.4, 10.1, 0.0))
    print(f"selftest {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    main(sys.argv)
