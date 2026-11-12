#!/usr/bin/env python3
"""judge_rows_v25 (D185 (2) P2; D186 (3); D188; D200): for each answer of G1, G2, G3, G4, G5 or G6, the judge row it is
read from, key v2.4 or key v2.5.

WHY. D185 (2) P2 (experiments/README.md "D185"): a reader that takes the key v2.5 judge row of an answer where one
exists, else its key v2.4 row. S476 refuses rows with more than one run_sha256 (scripts/S476_fig3_d123.py:887-889), and
the rows now come from three kinds of out, each with its own run_sha256:
  - key v2.4: S3's judge (experiments/scorers/judge_passages.py, key S373.KEY = all_v2_4.json) in out_<set>, for G4 also
    out_g4r38 as collect's --replace (S476:451-455). D184: G7 is never judged on v2.4, so every v2.4 row of G4 and G5
    is draw 1 (G3's out_g3 also holds v2.4 rows of draws 2 and 3, judged before D184: below);
  - key v2.5, the 132 changed questions (D182): S512's default mode in out_s6_<set> (s3_guard.py SETS "S6<set>"),
    draw 1, rows with "key_version": "v2.5" and no "questions" field. For G4 also out_s6_g4r38 when present (G4R38's
    38 reruns judged as S6G4 with an out of its own, S3_runs/README.md "S6, key v2.5"; that folder name is UNVERIFIED:
    the README says only "S3_OUT of its own");
  - key v2.5, every question (D184 (1)): S512 --questions all in out_s6_g7_<set> (SETS "S6G7<set>"), draws 2 and 3 on
    D98's 45 questions only, rows with "key_version": "v2.5" and "questions": "all".
D186 (3) (Figures 2 and 5 read G1 through this reader): G1 was judged on v2.4 at every draw (draws 1, 2 and 3; no G7),
so its two sources are, each with G1R15's out as collect's --replace (the 15 reruns of 18 October, D93 Q-c):
  - key v2.4: out (s3_guard SETS "G1") with out_g1r15 ("G1R15");
  - key v2.5, the 132 changed questions: out_s6_g1 ("S6G1") with out_s6_g1r15 ("S6G1R15"), S512's default mode at
    every draw G1's phases judge. The source is present only when both folders are: without out_s6_g1r15 the 5
    reruns of changed questions would be read from out_s6_g1's judging of their old, failed versions.
  Under replace_keys (the 15 rerun answer keys, from the caller) read_source also holds every row of a rerun key to the
  replace out's latest row of that answer, and refuses a replace out holding another answer (check_replace).
  choose(..., all_draws=True) applies the draw-1 rule at every draw and refuses any G7 row.
D188 (Figure 4 reads G3 through this reader): G3's out holds rows at draws 1, 2 and 3, judged on v2.4 by S3 before
D184: the draw 1 of every set-up, the draws 2 and 3 of raw_gemini and naive_rag (all 135 questions, stored 19 October,
G3_runs/README.md) and 34 draw-2 answers of orch_no_supervisor (stored before D98's stop). Its three sources:
  - key v2.4: out_g3 (s3_guard SETS "G3"), no --replace, rows of draws 1, 2 and 3;
  - key v2.5, the 132 changed questions: out_s6_g3 ("S6G3"), S512's default mode, rows of draws 1, 2 and 3 (S6G3 runs
    G3's phases 1, 2 and 3, s3_guard.py SETS "G3" "phases": "1 2 3", phase 3 being call (b) at every draw, on the copy
    taken before G7, S3_runs/README.md "G7 on key v2.5 complete" (2));
  - key v2.5, every question: out_s6_g7_g3 ("S6G7G3", s3_guard's G7_G3_SETUPS runs only), draws 2 and 3 on D98's 45.
  choose(..., g7_configs=g7_configs("G3")) applies the rule per configuration: a configuration of G7_G3_SETUPS takes
  the G4/G5 rule (draw 1 as below, draws 2 and 3 from the G7 row only); any other configuration (the baselines) takes
  the draw-1 rule at every draw and has any G7 row refused. So a v2.4 or changed-mode row at draw 2 or 3 of a G7
  set-up (orch_no_supervisor's 34 draw-2 answers, and the 14 of them on changed questions that S6G3's phase 2 judges)
  is refused when read; which row stands for those answers is not settled here. choose(..., read_only=pred) sets
  aside every source row for which pred(row) is false before any rule, and refuses an answer for which pred(answer) is
  false: Figure 4 reads draw 1 of its eight set-ups only (pred: draw 1 and a drawn configuration), so the rows of
  draws 2 and 3 and of the stress set-ups are not read.

D200 (Figure 3a reads G2 and G6 beside G1's six, fig3.md R1): G2 (matched budget) and G6 (the package's RLM at caps 5,
10 and 20) were judged on v2.4 at draws 1, 2 and 3 with no G7 and no rerun pass, so each takes G1's rule with two sources
and no --replace:
  - key v2.4: out_g2 or out_g6 (s3_guard SETS "G2", "G6");
  - key v2.5, the 132 changed questions: out_s6_g2 or out_s6_g6 ("S6G2", "S6G6"), S512's default mode at draws 1, 2, 3.

WHAT IT DOES. Reads; writes nothing; sends no model call; starts no process. S512's and the judge's files at past
commits of HEAD's history are read from their copies pinned in the tree (O3, scripts/pinned_history.py), each held to
the blob id git gave it.
  sources(outs_root, set_name)  the out folders of a set (G1, G2, G3, G4, G5 or G6 only; any other set is refused): each
                                with its kind, its s3_guard set name, the draws its rows may hold, and whether it is
                                present under outs_root (for G1's S6 source: out_s6_g1 and out_s6_g1r15 both; "missing"
                                names the folders absent).
  g7_configs(set_name)          G3's configurations whose draws 2 and 3 are G7's (s3_guard G7_G3_SETUPS), for choose.
  collect_argv(src, dest)       the s3_guard.py collect command line for one source (not run here).
  load(collect, outdirs)        one source's collect file (s3_guard collect's output), held to its outs: every row is
                                the latest row of its answer in one of the outs' judge_passages.jsonl files, every
                                answer of the outs is in the collect, one run_sha256, the sidecar agrees; and the outs'
                                judge_passages_headers.jsonl lines.
  check_v24(loaded, draws)      every row: no key_version, questions or judge field; lock d66daa28; a draw of draws
                                (default draw 1; G1: 1, 2 and 3); key_hash
                                equal to S373.key_hash on all_v2_4.json (the check S476:885-897 does not make); prompt
                                by S373.judged_answerable. Every header: run_sha256 recomputed by judge_passages.
                                run_identity's formula from the header, equal to the rows' one value; main judge; lock.
  check_v25(loaded, mode, draws) every row: key_version "v2.5"; key_hash equal to S512.key_hash25; lock; main judge;
                                prompt by key v2.5's answerable flag; mode "changed": question one of S512.changed_ids(),
                                no "questions" field, a draw of draws (default draw 1; G1: 1, 2 and 3); mode "all": "questions": "all", draw 2 or 3, question one
                                of D98's 45 (S512.g7_subset()). Every header: key_version and S512's pins (KEY25_SHA256,
                                KEY24_SHA256, CHANGED_SHA256, and for "all" G7_SUBSET_SHA256), the mode's question
                                scope, an S6 check kind of the main judge, code.s512_py and code.judge_passages equal to
                                the files at one commit of HEAD's history (pinned, O3), run_sha256 recomputed by S512's formula
                                (S512.run_identity over judge_passages.run_identity) and equal to the rows' one value.
  check_replace(loaded, src, keys)  every row whose answer key is in keys equals the latest row of that answer in the
                                source's replace out, and the replace out holds no answer outside keys.
  choose(answers, srcs, all_draws, g7_configs, read_only)  per answer (its judge identity: run_id, config, question,
                                draw); all_draws (G1): every draw as draw 1 below, and a G7 row is refused; g7_configs
                                (G3; not with all_draws): an answer whose configuration is not one of them as under
                                all_draws, the others as below; read_only: the rows it rejects are set aside first
                                (counted per source in "_sources"), an answer it rejects is refused:
                                  draw 1, a changed question: the v2.5 row if present, else the v2.4 row, counted as
                                    awaiting S6; neither: not judged;
                                  draw 1, an unchanged question: the v2.4 row; none: not judged;
                                  draw 2 or 3: the G7 row only; a question outside D98's 45: outside the subset;
                                    otherwise not judged.
                                It refuses: a source not passed through check_v24 or check_v25; two answers with one
                                identity; a row whose answer is not in answers, or whose answer_key is not the
                                answer's; two v2.5 rows for one answer (in any two sources); two v2.4 rows; a v2.5
                                row of an unchanged question at draw 1; a v2.4 row or a changed-mode row at draw 2 or
                                3; a G7 row at draw 1; a v2.5 row whose answer fields (run, passages, prompt) differ
                                from the v2.4 row of the same answer. Under g7_configs each answer's entry also holds
                                "rule": "every draw" or "G7 at draws 2 and 3".
  report(choice, all_draws)     answers by source and by status, awaiting_s6 (count and keys), g7_not_judged (count
                                and keys: draw-2 and draw-3 answers of D98's 45 with no G7 row; none under all_draws,
                                and none of an answer whose "rule" is "every draw"),
                                run_sha256 by source (a list of one), provisional (true while awaiting_s6 > 0 or
                                g7_not_judged > 0; a failed answer with no row counts in g7_not_judged too, so it can
                                hold provisional true until the caller has told failures apart).

A failed answer (no answer or a generation error) has no row in an answered-only set (G4), so choose gives it "not
judged"; the caller tells failures apart from its answer lines (Rule 10), as S476's g4_cells does.

    uv run --frozen python scripts/judge_rows_v25_test.py
"""
from __future__ import annotations

import collections
import functools
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import S373_rejudge_v2 as S373  # noqa: E402
import S512_s6_rejudge_v25 as S512  # noqa: E402
from experiments.scorers import judge_passages as JP  # noqa: E402
import pinned_history as PH  # noqa: E402

GUARD = ROOT / "findings/recompute/S3_runs/s3_guard.py"
LOCK_WANT = "d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12"   # D88; S463 LOCK_WANT; run_s3.sh:89
LOCKS_OK = __import__("lock_equiv").EQUIVALENT   # D205: D88 and the locks lock_equiv proves equal to it in every sent setting
MAIN_JUDGE = "devstral-small-2:24b"                                                 # LOCK.toml [judge] model
COVERED = ("G4", "G5")                       # the sets whose draws 2 and 3 are G7's only (D184; S476, S484 read G4)
ALL_DRAWS = ("G1", "G2", "G6")               # D186 (3), D200: judged on v2.4 at draws 1 to 3, no G7 (S463, S497, S511)
G1_DRAWS = (1, 2, 3)
PER_CONFIG = ("G3",)                         # D188: G3, the draw rule per configuration (g7_configs; S472, S480, S489)
G3_DRAWS = (1, 2, 3)                         # out_g3 and out_s6_g3 hold rows of draws 1 to 3 (module docstring)
EVERY_DRAW, G7_AT_2_3 = "every draw", "G7 at draws 2 and 3"   # choose's "rule" under g7_configs
G1R15_V24_OUT, G1R15_V25_OUT = "out_g1r15", "out_s6_g1r15"   # s3_guard SETS G1R15, S6G1R15 (D93 Q-c)
V24, V25_CHANGED, V25_ALL = "v2.4", "v2.5 changed", "v2.5 all"
G4R38_V24_OUT = "out_g4r38"                  # collect --replace for G4's v2.4 rows (S476:451-455)
G4R38_V25_OUT = "out_s6_g4r38"               # UNVERIFIED name (S3_runs/README.md: "S3_OUT of its own")
S512_PATH = "scripts/S512_s6_rejudge_v25.py"
JP_PATHS = {"judge_passages_py": "experiments/scorers/judge_passages.py",   # judge_passages.code_identity's files
            "s141_judge_py": "scripts/S141_runner/judge.py",
            "s373_rejudge_v2_py": "scripts/S373_rejudge_v2.py",
            "s376_judge_calibration_py": "scripts/S376_judge_calibration.py",
            "records_py": "experiments/scorers/records.py",
            "index_identity_py": "experiments/runner/index_identity.py"}
TIE = ("run_id", "config", "question_id", "draw", "answer_key", "n_passages", "passage_chars", "contexts_capture",
       "passages_kind", "answerable_prompt")         # fields a v2.4 and a v2.5 row of one answer must share


class Refused(Exception):
    """A refusal; code names the check that refused (the tests match on it)."""

    def __init__(self, code: str, msg: str):
        super().__init__(f"REFUSED [{code}]: {msg}")
        self.code = code


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


# ---------------------------------------------------------------- sources

@functools.lru_cache(maxsize=1)
def guard():
    """s3_guard.py, imported from its file (it is not a package module), for SETS."""
    spec = importlib.util.spec_from_file_location("s3_guard_for_judge_rows_v25", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sources_g1(outs_root: Path) -> list[dict]:
    """G1's two sources (module docstring, D186 (3)): v2.4 out with out_g1r15 as --replace; v2.5 out_s6_g1 with
    out_s6_g1r15 as --replace, present only when both folders are."""
    S = guard().SETS
    want = {"G1": ("out", None), "G1R15": (G1R15_V24_OUT, None), "S6G1": ("out_s6_g1", S512.SCRIPT),
            "S6G1R15": (G1R15_V25_OUT, S512.SCRIPT)}
    for k, (out, js) in want.items():
        st = S[k]
        if st["out"] != out or st.get("questions") is not None or st.get("judge_script") != js:
            raise Refused("sets_layout", f"s3_guard SETS {k}: out {st['out']!r}, questions {st.get('questions')!r}, "
                                         f"judge {st.get('judge_script')!r}; this reader expects {out!r}, None, {js}")
    root = Path(outs_root)
    v24r = root / G1R15_V24_OUT
    out = [{"name": "G1", "kind": V24, "set": "G1", "outs": [root / "out"], "replace": v24r if v24r.is_dir() else None,
            "draws": G1_DRAWS},
           {"name": "S6G1", "kind": V25_CHANGED, "set": "S6G1", "outs": [root / "out_s6_g1"],
            "replace": root / G1R15_V25_OUT, "draws": G1_DRAWS}]
    for s in out:
        need = list(s["outs"]) + ([s["replace"]] if s["kind"] != V24 else [])
        s["missing"] = [str(o) for o in need if not o.is_dir()]
        s["present"] = not s["missing"]
    return out


def sources_two(outs_root: Path, set_name: str) -> list[dict]:
    """G2's or G6's two sources (module docstring, D200): v2.4 out_g2 or out_g6, v2.5 out_s6_g2 or out_s6_g6, draws 1 to
    3, neither with a --replace. Refuses an s3_guard layout other than the one read here."""
    S, low = guard().SETS, set_name.lower()
    want = {set_name: ("out_" + low, None), "S6" + set_name: ("out_s6_" + low, S512.SCRIPT)}
    for k, (out, js) in want.items():
        st = S[k]
        if st["out"] != out or st.get("questions") is not None or st.get("judge_script") != js:
            raise Refused("sets_layout", f"s3_guard SETS {k}: out {st['out']!r}, questions {st.get('questions')!r}, "
                                         f"judge {st.get('judge_script')!r}; this reader expects {out!r}, None, {js}")
    root = Path(outs_root)
    out = [{"name": set_name, "kind": V24, "set": set_name, "outs": [root / ("out_" + low)], "replace": None,
            "draws": G1_DRAWS},
           {"name": "S6" + set_name, "kind": V25_CHANGED, "set": "S6" + set_name, "outs": [root / ("out_s6_" + low)],
            "replace": None, "draws": G1_DRAWS}]
    for s in out:
        s["missing"] = [str(o) for o in s["outs"] if not o.is_dir()]
        s["present"] = not s["missing"]
    return out


def sources_g3(outs_root: Path) -> list[dict]:
    """G3's three sources (module docstring, D188): v2.4 out_g3, v2.5 out_s6_g3 (the 132), v2.5 out_s6_g7_g3 (G7);
    none with a --replace. Refuses an s3_guard layout other than the one read here."""
    S = guard().SETS
    want = {"G3": ("out_g3", None, None), "S6G3": ("out_s6_g3", None, S512.SCRIPT),
            "S6G7G3": ("out_s6_g7_g3", "all", S512.SCRIPT)}
    for k, (out, q, js) in want.items():
        st = S[k]
        if st["out"] != out or st.get("questions") != q or st.get("judge_script") != js:
            raise Refused("sets_layout", f"s3_guard SETS {k}: out {st['out']!r}, questions {st.get('questions')!r}, "
                                         f"judge {st.get('judge_script')!r}; this reader expects {out!r}, {q!r}, {js}")
    root = Path(outs_root)
    out = [{"name": "G3", "kind": V24, "set": "G3", "outs": [root / "out_g3"], "replace": None, "draws": G3_DRAWS},
           {"name": "S6G3", "kind": V25_CHANGED, "set": "S6G3", "outs": [root / "out_s6_g3"], "replace": None,
            "draws": G3_DRAWS},
           {"name": "S6G7G3", "kind": V25_ALL, "set": "S6G7G3", "outs": [root / "out_s6_g7_g3"], "replace": None,
            "draws": S512.G7_DRAWS}]
    for s in out:
        s["missing"] = [str(o) for o in s["outs"] if not o.is_dir()]
        s["present"] = not s["missing"]
    return out


def g7_configs(set_name: str) -> tuple:
    """The configurations of set_name whose draws 2 and 3 are G7's, for choose's g7_configs: G3's are s3_guard's
    G7_G3_SETUPS (the six wave-1 ablations and the two stress set-ups; raw_gemini and naive_rag are not among them)."""
    if set_name not in PER_CONFIG:
        raise Refused("set", f"{set_name!r} has no per-configuration rule (only {', '.join(PER_CONFIG)})")
    return tuple(guard().G7_G3_SETUPS)


def sources(outs_root: Path, set_name: str) -> list[dict]:
    """The out folders of set_name under outs_root (a clone's findings/recompute/S3_runs, or a pull's s3/). Each:
    name, kind, set (the s3_guard set, for collect --set), outs, replace, draws, present, missing."""
    if set_name == "G1":
        return sources_g1(outs_root)
    if set_name in ALL_DRAWS:
        return sources_two(outs_root, set_name)
    if set_name in PER_CONFIG:
        return sources_g3(outs_root)
    if set_name not in COVERED:
        raise Refused("set", f"{set_name!r} is not one of {', '.join(COVERED + ALL_DRAWS + PER_CONFIG)} (D184: G4's "
                             f"and G5's draws 2 and 3 are G7's only; D186 (3), D200: G1, G2 and G6 at every draw; "
                             f"D188: G3 per configuration)")
    S = guard().SETS
    v24, s6, g7 = S[set_name], S["S6" + set_name], S["S6G7" + set_name]
    low = set_name.lower()
    want = {set_name: (v24, "out_" + low, None), "S6" + set_name: (s6, "out_s6_" + low, None),
            "S6G7" + set_name: (g7, "out_s6_g7_" + low, "all")}
    for k, (st, out, q) in want.items():
        if st["out"] != out or st.get("questions") != q or (k != set_name and st.get("judge_script") != S512.SCRIPT):
            raise Refused("sets_layout", f"s3_guard SETS {k}: out {st['out']!r}, questions {st.get('questions')!r}, "
                                         f"judge {st.get('judge_script')!r}; this reader expects {out!r}, {q!r}, S512")
    root = Path(outs_root)
    out = [{"name": set_name, "kind": V24, "set": set_name, "outs": [root / v24["out"]],
            "replace": (root / G4R38_V24_OUT) if set_name == "G4" and (root / G4R38_V24_OUT).is_dir() else None},
           {"name": "S6" + set_name, "kind": V25_CHANGED, "set": "S6" + set_name, "outs": [root / s6["out"]],
            "replace": None}]
    if set_name == "G4":
        out.append({"name": "S6G4R38", "kind": V25_CHANGED, "set": "S6G4", "outs": [root / G4R38_V25_OUT],
                    "replace": None})
    out.append({"name": "S6G7" + set_name, "kind": V25_ALL, "set": "S6G7" + set_name, "outs": [root / g7["out"]],
                "replace": None})
    for s in out:
        s["draws"] = (1,) if s["kind"] != V25_ALL else S512.G7_DRAWS
        s["missing"] = [str(o) for o in s["outs"] if not o.is_dir()]
        s["present"] = not s["missing"]
    return out


def collect_argv(src: dict, dest: Path, python: str = sys.executable) -> list[str]:
    """s3_guard.py collect for one source (its outs, its --replace, its set): what makes the file load reads."""
    argv = [python, str(GUARD), "collect", "--out", *map(str, src["outs"])]
    if src.get("replace") is not None:
        argv += ["--replace", str(src["replace"])]
    return argv + ["--set", src["set"], "--dest", str(dest)]


# ---------------------------------------------------------------- load

@dataclass
class Loaded:
    collect: Path
    rows: dict                                   # judge_passages.ident -> row
    headers: list
    run_sha256: str | None
    kind: str | None = None                      # set by check_v24 / check_v25
    mode: str | None = None
    name: str | None = None
    extra: dict = field(default_factory=dict)


def read_jsonl(f: Path) -> list[dict]:
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]


def load(collect: Path, outdirs, name: str | None = None) -> Loaded:
    """One source's collect file, held to the outs it was collected from (outdirs: one folder or a list, a --replace
    folder last), and those outs' header lines."""
    outdirs = [Path(outdirs)] if isinstance(outdirs, (str, Path)) else [Path(o) for o in outdirs]
    collect = Path(collect)
    rows = {}
    for d in read_jsonl(collect):
        k = JP.ident(d)
        if k in rows:
            raise Refused("collect_dup", f"{collect}: answer {k} twice")
        rows[k] = d
    latest_by_file = []
    for o in outdirs:
        for f in sorted(o.glob("judge/*/judge_passages.jsonl")):
            lat = {}
            for d in read_jsonl(f):
                lat[JP.ident(d)] = d                 # the latest row of an answer in a file (collect's rule)
            latest_by_file.append(lat)
    in_outs = set().union(*latest_by_file) if latest_by_file else set()
    for k, d in rows.items():
        if not any(lat.get(k) == d for lat in latest_by_file):
            raise Refused("collect_not_in_outs", f"{collect}: the row of {k} is not the latest row of that answer in "
                                                 f"any judge_passages.jsonl under {[str(o) for o in outdirs]}")
    missing = in_outs - set(rows)
    if missing:
        raise Refused("outs_not_in_collect", f"{len(missing)} answers judged in the outs are not in {collect} (first "
                                             f"{sorted(missing, key=str)[0]})")
    runs = {d.get("run_sha256") for d in rows.values()}
    if len(runs) > 1:
        raise Refused("run_sha_many", f"{collect}: {len(runs)} run_sha256 values ({sorted(map(str, runs))})")
    run = next(iter(runs), None)
    side = collect.with_name(collect.name + ".json")
    if side.exists():
        s = json.loads(side.read_text())
        if s.get("rows") != len(rows) or (rows and s.get("run_sha256") != run):
            raise Refused("sidecar", f"{side}: rows {s.get('rows')}, run_sha256 {str(s.get('run_sha256'))[:12]}; the "
                                     f"collect holds {len(rows)}, {str(run)[:12]}")
    headers = []
    for o in outdirs:
        for f in sorted(o.glob("judge/*/judge_passages_headers.jsonl")):
            headers += [dict(h, _file=str(f)) for h in read_jsonl(f)]
    return Loaded(collect=collect, rows=rows, headers=headers, run_sha256=run, name=name)


# ---------------------------------------------------------------- identity

def jp_run_sha(h: dict, code: dict) -> str:
    """judge_passages.run_identity (judge_passages.py:687-694) from a header, for the main judge (no "judge" key)."""
    return sha(json.dumps({"lock": h["lock_sha256"], "code": code, "options": h["options"], "fields": h["fields"],
                           "system": h["system_prompt_sha256"]}, sort_keys=True))


def s512_run_sha(h: dict, mode: str) -> str:
    """S512.run_identity (S512_s6_rejudge_v25.py:260-269) from a header S512 run wrote: its "code" is S512's
    code_identity, whose "judge_passages" is judge_passages' code identity."""
    d = {"judge_passages_run_identity": jp_run_sha(h, h["code"]["judge_passages"]), "s6": h["code"]}
    if mode == "all":
        d["scope"] = {"questions": "all", "draws": list(S512.G7_DRAWS), "subset_sha256": S512.G7_SUBSET_SHA256}
    return sha(json.dumps(d, sort_keys=True))


@functools.lru_cache(maxsize=1)
def main_identities() -> frozenset:
    """(sha256 of S512's file, judge_passages code identity as sorted JSON) at every commit of HEAD's history that
    touched S512 or one of judge_passages' code files, back to S512's first commit. A file's state between two such
    commits is its state at the earlier one, so these are all the pairs a clone of a commit could have run. Each file's
    sha256 is of its bytes at the commit; template_file is the V4_COMMON_SHA256 constant in S141_runner/judge.py at
    that commit, as judge_passages.code_identity reads it.
    O3 (8 Nov): no git. The walk (`git log --format=%H -- S512 + JP_PATHS`, newest first, to the first commit with no
    S512) and every file of every commit it visits are pinned in the tree (scripts/S617_pin_history.py, walk
    "judge_rows_v25.main_identities"), and pinned_history.show holds each copy to the blob id git gave <commit>:<path>.
    The pairs are computed from those bytes exactly as from git show. What the pin cannot prove in a tree with no
    history: that the walk lists every such commit of HEAD's history (S617 verify checks that against git here)."""
    if set(JP.code_identity()) != set(JP_PATHS) | {"template_file"}:
        raise Refused("code_layout", f"judge_passages.code_identity's keys {sorted(JP.code_identity())} are not "
                                     f"{sorted(JP_PATHS)} + template_file")
    try:
        walk = PH.log_paths("judge_rows_v25.main_identities")
    except PH.PinError as e:
        raise Refused("git", f"pinned walk: {e}") from None
    if walk["paths"] != [S512_PATH, *JP_PATHS.values()]:
        raise Refused("git", f"the pinned walk is over {walk['paths']}, not S512 and judge_passages' code files")

    def show(c: str, p: str):
        if not PH.has(c, p):
            return None                              # git show failed at that commit (the file was not there)
        try:
            return PH.show(c, p)
        except PH.PinError as e:
            raise Refused("git", str(e)) from None

    out = set()
    for c in walk["commits"]:
        s = show(c, S512_PATH)
        if s is None:
            break                                    # before S512's first commit
        ci, judge_py = {}, b""
        for k, p in JP_PATHS.items():
            f = show(c, p)
            if f is None:
                ci = None
                break
            ci[k] = sha(f)
            judge_py = f if k == "s141_judge_py" else judge_py
        if ci is None:
            continue
        m = re.search(rb'^V4_COMMON_SHA256 = "([0-9a-f]{64})"', judge_py, re.M)
        if m is None:
            continue                                 # no template pin in judge.py at that commit
        ci["template_file"] = m.group(1).decode()    # the constant judge.py held at that commit
        out.add((sha(s), json.dumps(ci, sort_keys=True)))
    return frozenset(out)


# ---------------------------------------------------------------- checks

@functools.lru_cache(maxsize=1)
def _keys24() -> tuple[dict, dict]:
    v2 = {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]}
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
    return v1, v2


def _row_common(k, d: dict, where: str) -> None:
    if d.get("lock_sha256") not in LOCKS_OK:
        raise Refused("lock", f"{where} {k}: lock {str(d.get('lock_sha256'))[:8]}, not d66daa28 (D88) or a lock equal to it (D205)")
    if d.get("judge") is not None:
        raise Refused("second_judge", f"{where} {k}: a second-judge row (judge {d.get('judge')!r}); this reader reads "
                                      f"the main judge only")
    if d.get("draw") not in (1, 2, 3):
        raise Refused("draw", f"{where} {k}: draw {d.get('draw')!r}")


def _headers_common(L: Loaded, where: str) -> None:
    if L.rows and not L.headers:
        raise Refused("header_missing", f"{where}: rows but no judge_passages_headers.jsonl line in its outs")
    for h in L.headers:
        if h.get("model") != MAIN_JUDGE:
            raise Refused("header_model", f"{h['_file']}: model {h.get('model')!r}, not the main judge {MAIN_JUDGE}")
        if h.get("lock_sha256") not in LOCKS_OK:
            raise Refused("lock", f"{h['_file']}: lock {str(h.get('lock_sha256'))[:8]}, not d66daa28 (D88) or a lock equal to it (D205)")
        if L.rows and h.get("run_sha256") != L.run_sha256:
            raise Refused("header_rows", f"{h['_file']}: run_sha256 {str(h.get('run_sha256'))[:12]}, the rows' "
                                         f"{str(L.run_sha256)[:12]}")


def check_v24(L: Loaded, draws=(1,)) -> Loaded:
    """Key v2.4 rows of S3's judge (judge_passages.py on all_v2_4.json), draw 1 only (D184) unless draws says more
    (G1: 1, 2 and 3, D186 (3))."""
    v1, v2 = _keys24()
    where = f"v2.4 {L.name or L.collect}"
    for k, d in L.rows.items():
        for f in ("key_version", "questions"):
            if f in d:
                raise Refused("key_version", f"{where} {k}: carries {f!r} {d[f]!r}, an S512 field")
        _row_common(k, d, where)
        if d["draw"] not in draws:
            raise Refused("draw", f"{where} {k}: draw {d['draw']}, not one of {list(draws)}; D184: G7 (draws 2 and 3 "
                                  f"of G3, G4 and G5) is never judged on v2.4")
        q = d["question_id"]
        if q not in v2:
            raise Refused("key_hash", f"{where} {k}: {q} is not in key v2.4")
        if d.get("key_hash") != S373.key_hash(q, v2):
            raise Refused("key_hash", f"{where} {k}: key_hash {d.get('key_hash')} is not S373.key_hash on "
                                      f"all_v2_4.json ({S373.key_hash(q, v2)})")
        if bool(d.get("answerable_prompt")) != S373.judged_answerable(q, v1, v2):
            raise Refused("prompt", f"{where} {k}: answerable_prompt {d.get('answerable_prompt')}, the judge's rule "
                                    f"says {S373.judged_answerable(q, v1, v2)}")
    _headers_common(L, where)
    for h in L.headers:
        if "key_version" in h:
            raise Refused("key_version", f"{h['_file']}: a v2.4 out holds a header with key_version {h['key_version']!r}")
        if jp_run_sha(h, h["code"]) != h.get("run_sha256"):
            raise Refused("header_run_sha", f"{h['_file']}: run_sha256 {str(h.get('run_sha256'))[:12]} is not "
                                            f"judge_passages.run_identity of the header's own fields")
    L.kind, L.mode = V24, None
    return L


def check_v25(L: Loaded, mode: str, draws=(1,)) -> Loaded:
    """Key v2.5 rows of S512: mode "changed" (the 132, out_s6_<set>, at draw 1 unless draws says more: G1's at 1, 2
    and 3, D186 (3)) or "all" (G7, draws 2 and 3 on D98's 45, out_s6_g7_<set>; draws is not read)."""
    if mode not in ("changed", "all"):
        raise Refused("mode", f"mode {mode!r} is neither changed nor all")
    changed, subset = set(S512.changed_ids()), S512.g7_subset()
    _, k25 = S512.keys()
    v2 = S512.v2_records()
    where = f"v2.5 {mode} {L.name or L.collect}"
    for k, d in L.rows.items():
        if d.get("key_version") != S512.KEY_VERSION:
            raise Refused("key_version", f"{where} {k}: key_version {d.get('key_version')!r}, not {S512.KEY_VERSION}")
        _row_common(k, d, where)
        q = d["question_id"]
        if q not in k25:
            raise Refused("key_hash", f"{where} {k}: {q} is not in key v2.5")
        if d.get("key_hash") != S512.key_hash25(q, v2):
            raise Refused("key_hash", f"{where} {k}: key_hash {d.get('key_hash')} is not S512.key_hash25 "
                                      f"({S512.key_hash25(q, v2)})")
        if bool(d.get("answerable_prompt")) != (k25[q]["answerable"] in (True, "true", "True")):
            raise Refused("prompt", f"{where} {k}: answerable_prompt {d.get('answerable_prompt')}, key v2.5 says "
                                    f"{k25[q]['answerable']}")
        if mode == "changed":
            if "questions" in d:
                raise Refused("scope", f"{where} {k}: carries \"questions\": {d['questions']!r}, a G7 row")
            if q not in changed:
                raise Refused("scope", f"{where} {k}: {q} is not one of the {S512.N_CHANGED} changed questions")
            if d["draw"] not in draws:
                raise Refused("draw", f"{where} {k}: draw {d['draw']}; the 132's rows of this set are draw(s) "
                                      f"{list(draws)} (D184: G4's and G5's draws 2 and 3 are G7's, judged once in "
                                      f"out_s6_g7_)")
        else:
            if d.get("questions") != "all":
                raise Refused("scope", f"{where} {k}: \"questions\" {d.get('questions')!r}, not \"all\"")
            if d["draw"] not in S512.G7_DRAWS:
                raise Refused("draw", f"{where} {k}: draw {d['draw']}; G7 judges draws 2 and 3 only (D184)")
            if q not in subset:
                raise Refused("scope", f"{where} {k}: {q} is not one of D98's 45")
    _headers_common(L, where)
    ids = main_identities() if L.headers else frozenset()
    want_q = ({"scope": "all", "draws": list(S512.G7_DRAWS), "subset_sha256": S512.G7_SUBSET_SHA256} if mode == "all"
              else {"changed": S512.N_CHANGED, "sha256": S512.CHANGED_SHA256})
    for h in L.headers:
        code = h.get("code") or {}
        if h.get("key_version") != S512.KEY_VERSION:
            raise Refused("key_version", f"{h['_file']}: header key_version {h.get('key_version')!r}")
        pins = {"key25_sha256": S512.KEY25_SHA256, "key24_sha256": S512.KEY24_SHA256,
                "changed_sha256": S512.CHANGED_SHA256}
        bad = {p: code.get(p) for p, v in pins.items() if code.get(p) != v}
        if bad:
            raise Refused("header_pin", f"{h['_file']}: code pins {bad} are not S512's")
        if h.get("questions") != want_q:
            raise Refused("header_scope", f"{h['_file']}: questions {h.get('questions')!r}, mode {mode} wants {want_q}")
        if mode == "all" and (not h.get("draws") or any(x not in S512.G7_DRAWS for x in h["draws"])):
            raise Refused("header_scope", f"{h['_file']}: draws {h.get('draws')!r}, G7 judges 2 and 3 only")
        if (h.get("check") or {}).get("kind") not in S512.KINDS["main"]:
            raise Refused("header_check", f"{h['_file']}: check kind {(h.get('check') or {}).get('kind')!r} is not "
                                          f"an S6 check of the main judge {S512.KINDS['main']}")
        pair = (code.get("s512_py"), json.dumps(code.get("judge_passages"), sort_keys=True))
        if pair not in ids:
            raise Refused("header_blob", f"{h['_file']}: code.s512_py {str(code.get('s512_py'))[:12]} with its "
                                         f"judge_passages code identity is not S512 and the judge's files at any "
                                         f"commit of HEAD's history")
        if s512_run_sha(h, mode) != h.get("run_sha256"):
            raise Refused("header_run_sha", f"{h['_file']}: run_sha256 {str(h.get('run_sha256'))[:12]} is not "
                                            f"S512.run_identity of the header's own fields (mode {mode})")
    L.kind, L.mode = (V25_ALL if mode == "all" else V25_CHANGED), mode
    return L


def check_replace(L: Loaded, replace: Path, keys) -> dict:
    """Every row of L whose answer_key is in keys equals the latest row of that answer in replace's
    judge_passages.jsonl files (collect --replace took it from there), and replace holds no answer outside keys.
    Returns {"keys": len(keys), "rows_from_replace": the rows of L held to it}."""
    keys = set(keys)
    latest = {}
    for f in sorted(Path(replace).glob("judge/*/judge_passages.jsonl")):
        for d in read_jsonl(f):
            latest[JP.ident(d)] = d
    extra = sorted(str(d.get("answer_key")) for d in latest.values() if d.get("answer_key") not in keys)
    if extra:
        raise Refused("replace_extra", f"{replace}: {len(extra)} answers that are not rerun keys, first {extra[0]}")
    n = 0
    for k, d in L.rows.items():
        if d.get("answer_key") in keys:
            if latest.get(k) != d:
                raise Refused("replace_row", f"{L.name or L.collect} {k}: the row of a rerun key is not the latest "
                                             f"row of that answer in {replace} (the old version's judging?)")
            n += 1
    return {"keys": len(keys), "rows_from_replace": n}


def read_source(src: dict, collect: Path, replace_keys=None) -> Loaded:
    """load and the check of the source's kind (sources' dict, the collect file collect_argv made); with replace_keys
    and a replace out, check_replace too (its counts in Loaded.extra["replace"])."""
    outs = list(src["outs"]) + ([src["replace"]] if src.get("replace") is not None else [])
    L = load(collect, outs, name=src["name"])
    draws = tuple(src.get("draws") or (1,))
    if src["kind"] == V24:
        L = check_v24(L, draws)
    else:
        L = check_v25(L, "all" if src["kind"] == V25_ALL else "changed", draws)
    if replace_keys is not None and src.get("replace") is not None:
        L.extra["replace"] = check_replace(L, src["replace"], replace_keys)
    return L


# ---------------------------------------------------------------- choose

def answer_ident(a: dict) -> tuple:
    """An answer line's judge identity, judge_passages.ident's (run_id, config, question, draw)."""
    return a["run_id"], a["config"], a["question_id"], a["draw"]


def choose(answers, srcs: list[Loaded], ident=answer_ident, all_draws: bool = False, g7_configs=None,
           read_only=None) -> dict:
    """{ident: {"status", "source", "row"}} for every answer, by the rule in the module docstring; "_sources" holds
    each source's name, kind and run_sha256 for report. all_draws (G1, D186 (3)): every draw takes the draw-1 rule,
    and a G7 row is refused. g7_configs (G3, D188): an answer whose "config" is not one of them takes the draw-1 rule
    at every draw (a G7 row refused), one whose "config" is takes the G4/G5 rule; each entry then holds its "rule".
    read_only (a function of a row or an answer): rows it rejects are set aside before any rule ("_sources"
    "set_aside"), and an answer it rejects is refused."""
    if all_draws and g7_configs is not None:
        raise Refused("rule", "all_draws and g7_configs given together: one rule per set")
    g7c = None if g7_configs is None else frozenset(g7_configs)
    got = {}
    for a in answers:
        k = ident(a)
        if k in got:
            raise Refused("answer_dup", f"answer {k} twice in the inputs given")
        if read_only is not None and not read_only(a):
            raise Refused("answer_set_aside", f"answer {k} is one read_only sets aside: its rows would not be read")
        got[k] = a
    answers = got
    changed, subset = set(S512.changed_ids()), S512.g7_subset()
    by = collections.defaultdict(lambda: {V24: [], V25_CHANGED: [], V25_ALL: []})
    names, set_aside = set(), collections.Counter()
    for s in srcs:
        if s.kind not in (V24, V25_CHANGED, V25_ALL):
            raise Refused("unchecked", f"source {s.name or s.collect} was not passed through check_v24 or check_v25")
        if (s.name or str(s.collect)) in names:
            raise Refused("unchecked", f"source {s.name or s.collect} given twice")
        names.add(s.name or str(s.collect))
        for k, d in s.rows.items():
            if read_only is not None and not read_only(d):
                set_aside[s.name or str(s.collect)] += 1
                continue
            a = answers.get(k)
            if a is None:
                raise Refused("row_without_answer", f"{s.name}: row {k} is not an answer of the inputs given")
            if d.get("answer_key") is not None and a.get("answer_key") is not None and d["answer_key"] != a["answer_key"]:
                raise Refused("row_answer_differs", f"{s.name}: row {k} answer_key {d['answer_key']}, the answer's "
                                                    f"{a['answer_key']}")
            by[k][s.kind].append((s, d))
    out = {}
    for k, a in answers.items():
        rs = by.get(k) or {V24: [], V25_CHANGED: [], V25_ALL: []}
        v24, v5c, v5a = rs[V24], rs[V25_CHANGED], rs[V25_ALL]
        if len(v5c) + len(v5a) > 1:
            raise Refused("two_v25", f"{k}: v2.5 rows in {[s.name for s, _ in v5c + v5a]}")
        if len(v24) > 1:
            raise Refused("two_v24", f"{k}: v2.4 rows in {[s.name for s, _ in v24]}")
        q, dr = a["question_id"], a["draw"]
        every = g7c is not None and a.get("config") not in g7c          # G3's baselines: the draw-1 rule at every draw
        if dr == 1 or (all_draws and dr in G1_DRAWS) or (every and dr in G3_DRAWS):
            if v5a:
                raise Refused("choose_draw", f"{k}: a G7 row at draw {dr} ({v5a[0][0].name})")
            if q not in changed and v5c:
                raise Refused("choose_scope", f"{k}: a v2.5 row of an unchanged question ({v5c[0][0].name})")
            if v5c and v24:
                d5, d4 = v5c[0][1], v24[0][1]
                diff = [f for f in TIE if d5.get(f) != d4.get(f)]
                if diff:
                    raise Refused("tie", f"{k}: the v2.5 row ({v5c[0][0].name}) and the v2.4 row differ in {diff}")
            if v5c:
                pick, status = v5c[0], "v2.5"
            elif v24:
                pick, status = v24[0], ("v2.4 awaiting S6" if q in changed else "v2.4")
            else:
                pick, status = None, "not judged"
        elif dr in S512.G7_DRAWS:
            if v24:
                raise Refused("choose_draw", f"{k}: a v2.4 row at draw {dr} ({v24[0][0].name}); D184: G7 is judged on v2.5 only")
            if v5c:
                raise Refused("choose_draw", f"{k}: a changed-mode v2.5 row at draw {dr} ({v5c[0][0].name})")
            if q not in subset:
                pick, status = None, "outside subset"
            elif v5a:
                pick, status = v5a[0], "v2.5"
            else:
                pick, status = None, "not judged"
        else:
            raise Refused("draw", f"{k}: draw {dr!r}")
        out[k] = {"status": status, "source": pick[0].name if pick else None, "row": pick[1] if pick else None,
                  "draw": dr, "question_id": q}
        if g7c is not None:
            out[k]["rule"] = EVERY_DRAW if every else G7_AT_2_3
    out["_sources"] = {s.name or str(s.collect): {"kind": s.kind, "run_sha256": s.run_sha256, "rows": len(s.rows)}
                       for s in srcs}
    if read_only is not None:
        for n, v in out["_sources"].items():
            v["set_aside"] = set_aside[n]
    return out


def report(choice: dict, all_draws: bool = False) -> dict:
    """Counts of a choice: by source, by status (and by draw), awaiting_s6, g7_not_judged (none under all_draws: G1
    has no G7), run_sha256 by source, provisional (either count above 0)."""
    items = {k: v for k, v in choice.items() if k != "_sources"}
    awaiting = sorted((k for k, v in items.items() if v["status"] == "v2.4 awaiting S6"), key=lambda t: tuple(map(str, t)))
    g7_nj = [] if all_draws else sorted(
        (k for k, v in items.items() if v["draw"] in S512.G7_DRAWS and v["status"] == "not judged"
         and v.get("rule") != EVERY_DRAW),
        key=lambda t: tuple(map(str, t)))
    by_draw = collections.defaultdict(collections.Counter)
    for v in items.values():
        by_draw[v["draw"]][v["status"]] += 1
    return {"answers": len(items),
            "by_source": dict(collections.Counter(v["source"] for v in items.values() if v["source"])),
            "by_status": dict(collections.Counter(v["status"] for v in items.values())),
            "by_draw": {d: dict(c) for d, c in sorted(by_draw.items())},
            "awaiting_s6": {"count": len(awaiting), "keys": [list(k) for k in awaiting]},
            "g7_not_judged": {"count": len(g7_nj), "keys": [list(k) for k in g7_nj]},
            "run_sha256": {n: ([s["run_sha256"]] if s["run_sha256"] else []) for n, s in choice["_sources"].items()},
            "provisional": len(awaiting) > 0 or len(g7_nj) > 0}


# ---------------------------------------------------------------- T2 (D256; fig3.md section 7, R9)
#
# D256 (Valerio, 5 November 18:46, "Q1: ok, Q2: ok"): this reader opened to T2, for Supplementary Figure 7 a and b. Each
# T2 generator and gemini-3-flash-preview (G1) is read from committed collect files, all six strategies, draws 1 to 3,
# on the final key: the key v2.5 row of an answer where one exists, else its key v2.4 row (D185 (2) P2). A key v2.4
# row of a changed question with no v2.5 row is read only when it is a failed answer (no answer: a fail on either key);
# any other is refused. The judge-code rule (S463.panel_f_judge_codes, widened by D256 Q1) is the caller's: t2_source
# returns each file's run_sha256 and, where the outs are committed, the v2.5 headers held to the rows (run_sha256
# recomputed from the header's own fields), which the rule compares.
#   gemini-3-flash-preview  base fig2_inputs/g1_collect.jsonl (v2.4, held to S511.G1_COLLECT_SHA); v2.5
#                           fig3_s6_inputs/s6_g1_collect.jsonl held to its outs out_s6_g1 and out_s6_g1r15 (check_v25,
#                           changed mode, draws 1 to 3): G1's headers.
#   claude-haiku-4-5, gemini-2.5-pro  base and v2.5 collects in S518_inputs/<source>/ (S518's frozen copies, held to
#                           their SHA256SUMS); no outs committed, so no header: their v2.5 run_sha256 must equal G1's.
#   gemma3, qwen3-coder     t2_local_v25_inputs/ (S585, after D209's draws 2 and 3): whole-key v2.5 collects held to
#                           their outs (check_whole), no base. Reproduce first: every row of S518's earlier copy
#                           (S518_inputs/<source>/collect.jsonl) gives the same cell in the new file.
RECOMPUTE = ROOT / "findings" / "recompute"
T2_INPUTS = RECOMPUTE / "S518_inputs"
T2_LOCAL = RECOMPUTE / "t2_local_v25_inputs"
G1_V25_DIR = RECOMPUTE / "fig3_s6_inputs"
T2_CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
FLASH = "gemini-3-flash-preview"
T2_SOURCES = {
    FLASH: {"tag": "", "base": RECOMPUTE / "fig2_inputs" / "g1_collect.jsonl", "base_pin": "S511.G1_COLLECT_SHA",
            "v25": G1_V25_DIR / "s6_g1_collect.jsonl", "mode": "changed",
            "outs": [G1_V25_DIR / "out_s6_g1", G1_V25_DIR / G1R15_V25_OUT]},
    "claude-haiku-4-5": {"tag": "+claude-haiku-4-5", "base": T2_INPUTS / "claude-haiku-4-5" / "t2_v24_collect.jsonl",
                         "v25": T2_INPUTS / "claude-haiku-4-5" / "s6t2_collect.jsonl", "mode": "changed", "outs": None},
    "gemini-2.5-pro": {"tag": "+gemini-2.5-pro", "base": T2_INPUTS / "gemini-2.5-pro" / "t2g_collect.jsonl",
                       "v25": T2_INPUTS / "gemini-2.5-pro" / "s6t2g_collect.jsonl", "mode": "changed", "outs": None},
    "gemma3": {"tag": "+gemma3-27b", "base": None, "v25": T2_LOCAL / "t2lgemma_collect.jsonl", "mode": "whole:t2lgemma",
               "outs": [T2_LOCAL / "out_s6_w_t2lgemma_laptop", T2_LOCAL / "out_s6_w_t2lgemma_studio"],
               "earlier": T2_INPUTS / "gemma3" / "collect.jsonl"},
    "qwen3-coder": {"tag": "+qwen3-coder-30b", "base": None, "v25": T2_LOCAL / "t2lqcoder_collect.jsonl",
                    "mode": "whole:t2lqcoder", "outs": [T2_LOCAL / "out_s6_w_t2lqcoder"],
                    "earlier": T2_INPUTS / "qwen3-coder" / "collect.jsonl"},
}
JUDGE_FAILED_T2 = {"error", "stalled", "length", "cancelled", "unparseable"}   # S511.JUDGE_FAILED (S511:142)


def summed_sha(path: Path) -> str | None:
    """The sha256 that the nearest SHA256SUMS above path (up to findings/recompute) records for it, or None."""
    path = Path(path)
    for d in path.parents:
        s = d / "SHA256SUMS"
        if s.is_file():
            rel = str(path.relative_to(d))
            for line in s.read_text().splitlines():
                parts = line.split(None, 1)
                if len(parts) == 2 and parts[1].strip().lstrip("*") == rel:
                    return parts[0]
            return None
        if d == RECOMPUTE:
            break
    return None


def held_sha(path: Path, pin: str | None = None) -> str:
    """The file's sha256, refused unless it equals its SHA256SUMS line (or, for pin "S511.G1_COLLECT_SHA", S511's
    pinned G1 collect)."""
    got = sha(Path(path).read_bytes())
    if pin == "S511.G1_COLLECT_SHA":
        import S511_g2_matched_budget as S511
        want = S511.G1_COLLECT_SHA
    else:
        want = summed_sha(path)
    if want is None or got != want:
        raise Refused("t2_sha", f"{path}: sha256 {got[:12]}, its record {str(want)[:12]}")
    return got


def check_whole(L: Loaded, mode: str) -> Loaded:
    """Key v2.5 rows of S512's whole-key scope (B17; mode "whole:<set>"), every draw, held to their outs' headers:
    every row's "questions" is mode and its question in key v2.5 (key_hash, prompt as check_v25); every header names the
    main judge, the lock, S512's pins, the set's whole_scope, an S6 check kind of the main judge, a code pair at a
    commit of HEAD's history, and a run_sha256 recomputed by S512.run_identity's whole-key formula equal to the rows'."""
    name = S512.whole_name(mode)
    if name is None or name not in S512.WHOLE:
        raise Refused("mode", f"mode {mode!r} is not a whole-key set of S512")
    _, k25 = S512.keys()
    v2 = S512.v2_records()
    subset = S512.g7_subset()
    cover = S512.whole_scope(name)["cover"]
    where = f"v2.5 {mode} {L.name or L.collect}"
    for k, d in L.rows.items():
        if S512.KEY_VERSION != d.get("key_version"):
            raise Refused("key_version", f"{where} {k}: key_version {d.get('key_version')!r}, not {S512.KEY_VERSION}")
        _row_common(k, d, where)
        if d.get("questions") != mode:
            raise Refused("scope", f"{where} {k}: \"questions\" {d.get('questions')!r}, not {mode!r}")
        q = d["question_id"]
        if q not in k25:
            raise Refused("key_hash", f"{where} {k}: {q} is not in key v2.5")
        if S512.key_hash25(q, v2) != d.get("key_hash"):
            raise Refused("key_hash", f"{where} {k}: key_hash {d.get('key_hash')} is not S512.key_hash25")
        if bool(d.get("answerable_prompt")) != (k25[q]["answerable"] in (True, "true", "True")):
            raise Refused("prompt", f"{where} {k}: answerable_prompt {d.get('answerable_prompt')}, key v2.5 says "
                                    f"{k25[q]['answerable']}")
        c = (cover.get(d["run_id"]) or {}).get(str(d["draw"]))
        if c is None or (c == "d98" and q not in subset):
            raise Refused("scope", f"{where} {k}: run {d['run_id']} draw {d['draw']} question {q} is outside the set's "
                                   f"cover ({c})")
    _headers_common(L, where)
    ids = main_identities() if L.headers else frozenset()
    for h in L.headers:
        code = h.get("code") or {}
        if h.get("key_version") != S512.KEY_VERSION:
            raise Refused("key_version", f"{h['_file']}: header key_version {h.get('key_version')!r}")
        pins = {"key25_sha256": S512.KEY25_SHA256, "key24_sha256": S512.KEY24_SHA256,
                "changed_sha256": S512.CHANGED_SHA256}
        bad = {p: code.get(p) for p, v in pins.items() if code.get(p) != v}
        if bad:  # whole key
            raise Refused("header_pin", f"{h['_file']}: code pins {bad} are not S512's")
        if h.get("questions") != S512.whole_scope(name):
            raise Refused("header_scope", f"{h['_file']}: questions is not S512.whole_scope({name!r})")
        if not (h.get("check") or {}).get("kind") in S512.KINDS["main"]:  # noqa: E713
            raise Refused("header_check", f"{h['_file']}: check kind {(h.get('check') or {}).get('kind')!r}")
        pair = (code.get("s512_py"), json.dumps(code.get("judge_passages"), sort_keys=True))
        if not pair in ids:  # noqa: E713
            raise Refused("header_blob", f"{h['_file']}: code.s512_py {str(code.get('s512_py'))[:12]} with its "
                                         f"judge_passages code identity is not at any commit of HEAD's history")
        want = sha(json.dumps({"judge_passages_run_identity": jp_run_sha(h, code["judge_passages"]), "s6": code,
                               "scope": h["questions"]}, sort_keys=True))
        if want != h.get("run_sha256"):
            raise Refused("header_run_sha", f"{h['_file']}: run_sha256 {str(h.get('run_sha256'))[:12]} is not "
                                            f"S512.run_identity (whole key) of the header's own fields")
    L.kind, L.mode = "v2.5 whole", mode
    return L


def t2_check_rows(rows: dict, path: Path, kind: str, tag: str) -> None:
    """Rows of a collect read without its outs (S518's frozen copies, G1's v2.4 collect): one lock lock_equiv accepts,
    the main judge, one run_sha256 (the sidecar's, with its row count), draws 1 to 3, run ids of the source's
    generator, a strategy of T2_CONFIGS; kind "v2.4": no key_version or questions, key_hash S373's on key v2.4, the
    prompt by S373.judged_answerable; kind "v2.5 changed": key_version v2.5, no questions, one of the changed questions,
    key_hash S512's, the prompt by key v2.5."""
    v1, k24 = _keys24()
    _, k25 = S512.keys()
    v2 = S512.v2_records()
    changed = set(S512.changed_ids())
    where = f"{kind} {path}"
    for k, d in rows.items():
        _row_common(k, d, where)
        if not str(d.get("run_id", "")).endswith(tag) or (not tag and "+" in str(d.get("run_id"))):
            raise Refused("t2_run", f"{where} {k}: run {d.get('run_id')!r} is not of generator {tag or 'G1'!r}")
        if str(d.get("config", "")).split("+")[0] not in T2_CONFIGS:
            raise Refused("t2_config", f"{where} {k}: config {d.get('config')!r}")
        q = d["question_id"]
        if kind == V24:
            if "key_version" in d or "questions" in d:
                raise Refused("key_version", f"{where} {k}: carries an S512 field")
            if q not in k24 or d.get("key_hash") != S373.key_hash(q, k24):
                raise Refused("key_hash", f"{where} {k}: key_hash {d.get('key_hash')} is not S373's on key v2.4")
            if bool(d.get("answerable_prompt")) != S373.judged_answerable(q, v1, k24):
                raise Refused("prompt", f"{where} {k}: answerable_prompt {d.get('answerable_prompt')}")
        else:
            if d.get("key_version") != S512.KEY_VERSION or "questions" in d:
                raise Refused("key_version", f"{where} {k}: key_version {d.get('key_version')!r}, questions "
                                             f"{d.get('questions')!r}; a changed-mode v2.5 row wanted")
            if not q in changed:  # noqa: E713
                raise Refused("scope", f"{where} {k}: {q} is not one of the changed questions")
            if S512.key_hash25(q, v2) != d.get("key_hash"):
                raise Refused("key_hash", f"{where} {k}: key_hash {d.get('key_hash')} is not S512.key_hash25")
            if bool(d.get("answerable_prompt")) != (k25[q]["answerable"] in (True, "true", "True")):
                raise Refused("prompt", f"{where} {k}: answerable_prompt {d.get('answerable_prompt')}")
    runs = {d.get("run_sha256") for d in rows.values()}
    if len(runs) != 1:
        raise Refused("run_sha_many", f"{path}: {len(runs)} run_sha256 values")
    side = Path(path).with_name(Path(path).name + ".json")
    s = json.loads(side.read_text()) if side.is_file() else {}
    if s.get("rows") != len(rows) or s.get("run_sha256") != next(iter(runs)):
        raise Refused("sidecar", f"{side}: rows {s.get('rows')}, run_sha256 {str(s.get('run_sha256'))[:12]}; the "
                                 f"collect holds {len(rows)}")


def t2_cell(d: dict) -> dict:
    """A row's cell, as S511.read_collect and S518.read_rows make it: scored (correctness), failed (no answer: a fail,
    Rule 10) or unscored (a judge failure, counted in neither direction)."""
    st = (d.get("a") or {}).get("status")
    if st == "ok":
        v = (d["a"].get("scores") or {}).get("correctness")
        return ({"kind": "scored", "score": v} if isinstance(v, (int, float)) and not isinstance(v, bool)
                else {"kind": "unscored", "why": "ok, no score"})
    if st == "no_answer":
        return {"kind": "failed"}
    if st in JUDGE_FAILED_T2:
        return {"kind": "unscored", "why": st}
    raise Refused("t2_status", f"{d.get('run_id')} {d.get('question_id')} d{d.get('draw')}: (a) status {st!r}")


def t2_source(name: str, spec: dict | None = None) -> dict:
    """One generator's cells on the final key, all six strategies, draws 1 to 3 (D256): {"cells": {(config, question,
    draw): cell}, "files": {path: sha256}, "run_sha256": {"v2.4": sha or None, "v2.5": sha}, "headers_v25": [the
    v2.5 outs' headers, held to the rows] or [], "counts": {...}, "reproduced": str or None}. Refuses as the module's
    checks refuse, a doubled answer, a v2.5 row that differs from its v2.4 row in TIE, a non-failed v2.4 row of a
    changed question with no v2.5 row, and (local sources) an earlier S518 copy whose cells the new file does not give."""
    sp = spec or T2_SOURCES[name]
    files, out = {}, {}
    v25p = Path(sp["v25"])
    files[str(v25p)] = held_sha(v25p)
    if sp.get("outs"):
        L = load(v25p, sp["outs"], name=name)
        L = check_whole(L, sp["mode"]) if sp["mode"].startswith(S512.WHOLE_PREFIX) else check_v25(L, "changed", G1_DRAWS)
        for o in sp["outs"]:
            for f in sorted(Path(o).glob("judge/*/judge_passages*.jsonl")):
                files[str(f)] = held_sha(f)
        over, headers = L.rows, [{k: v for k, v in h.items() if k != "_file"} for h in L.headers]
        for k, d in over.items():
            if not str(d.get("run_id", "")).endswith(sp["tag"]) or (not sp["tag"] and "+" in str(d.get("run_id"))):
                raise Refused("t2_run", f"{name} {k}: run {d.get('run_id')!r} is not of generator {sp['tag'] or 'G1'!r}")
            if str(d.get("config", "")).split("+")[0] not in T2_CONFIGS:
                raise Refused("t2_config", f"{name} {k}: config {d.get('config')!r}")
    else:
        over, headers = {}, []
        for d in read_jsonl(v25p):
            k = JP.ident(d)
            if k in over:
                raise Refused("collect_dup", f"{v25p}: answer {k} twice")
            over[k] = d
        t2_check_rows(over, v25p, V25_CHANGED, sp["tag"])
    base = {}
    if sp.get("base"):
        bp = Path(sp["base"])
        files[str(bp)] = held_sha(bp, sp.get("base_pin"))
        for d in read_jsonl(bp):
            k = JP.ident(d)
            if k in base:
                raise Refused("collect_dup", f"{bp}: answer {k} twice")
            base[k] = d
        t2_check_rows(base, bp, V24, sp["tag"])
    changed = set(S512.changed_ids())
    whole = sp["mode"].startswith(S512.WHOLE_PREFIX)
    awaiting_failed = 0
    for k in set(base) | set(over):
        d5, d4 = over.get(k), base.get(k)
        if d5 is not None and d4 is not None:
            diff = [f for f in TIE if d5.get(f) != d4.get(f)]
            if diff:
                raise Refused("tie", f"{name} {k}: the v2.5 row and the v2.4 row differ in {diff}")
        if d5 is None and not whole and d4["question_id"] in changed:
            if (d4.get("a") or {}).get("status") != "no_answer":
                raise Refused("t2_awaiting", f"{name} {k}: a changed question judged on key v2.4 only "
                                             f"({(d4.get('a') or {}).get('status')}); its v2.5 row is missing")
            awaiting_failed += 1
        d = d5 if d5 is not None else d4
        c = (str(d["config"]).split("+")[0], d["question_id"], int(d["draw"]))
        if c in out:
            raise Refused("answer_dup", f"{name}: {c} twice")
        out[c] = t2_cell(d)
    reproduced = None
    if sp.get("earlier"):
        ep = Path(sp["earlier"])
        files[str(ep)] = held_sha(ep)
        old = [json.loads(x) for x in ep.read_text().splitlines() if x.strip()]
        bad = [(r["config"], r["question_id"], r["draw"]) for r in old
               if out.get((str(r["config"]).split("+")[0], r["question_id"], int(r["draw"]))) != t2_cell(r)]
        if bad:
            raise Refused("t2_reproduce", f"{name}: {len(bad)} rows of S518's copy {ep.name} give another cell in "
                                          f"{v25p.name} (first {bad[0]})")
        rel = lambda x: str(x.relative_to(ROOT)) if x.is_relative_to(ROOT) else str(x)  # noqa: E731
        reproduced = f"{len(old)} of {len(old)} rows of {rel(ep)} give the same cell in {rel(v25p)}"
    runs4 = {d.get("run_sha256") for d in base.values()}
    return {"cells": out, "files": files,
            "run_sha256": {"v2.4": next(iter(runs4)) if runs4 else None,
                           "v2.5": next(iter({d.get("run_sha256") for d in over.values()}))},
            "headers_v25": headers,
            "counts": {"v24_rows": len(base), "v25_rows": len(over), "cells": len(out),
                       "v24_failed_awaiting_v25": awaiting_failed},
            "reproduced": reproduced}
