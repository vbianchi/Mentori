#!/usr/bin/env python3
"""S514 - D185 (2) P3 and P4: Figure 3's readings on every draw present, key v2.5 judge rows where they exist, and
D76 Q131's missing parts; D188: T1 on D181's concept recall (t1). Provisional while S6 and G7 judging run. Writes new
folders only (G4_fig3c_d185, L2_d135_d181_g7, T1_L2_d181); S476 and S474 are imported, and S476's plate reads the
G4_fig3c_d185 and T1_L2_d181 folders written here (README.md:75-79, S494).

WHY A SCRIPT OF ITS OWN. D185 (2) (experiments/README.md "D185") asks S476 (and S474, S485) to read every draw present
under D98's reading (LIST.md:448-460: G4's and G5's main estimates on draw 1; draws 2 and 3 on the D98 subset give the
run-to-run noise; each table states which of the two a number rests on), and P4 asks for D76 Q131's missing parts
(README.md:195-199). The committed headers of L2/, T1_L2/, G4_fig3c/ and the plates record the sha256 of S476, S474,
S484 and S485, so an edit to any of them changes their default outputs. The readings are therefore built here, from
those scripts' own functions, as S476 itself was built beside S475.

    uv run --frozen python scripts/S514_fig3_d185.py g4c [--copy <pull folder>] [--s6 <folder of the S6 outs>]
                                                         [--out <new or own folder>] [--allow-s476-sha-line]
                                                         [--faults <keys file>]
    uv run --frozen python scripts/S514_fig3_d185.py l2g7 --g5-copy <G5 copy> [--out <new or own folder>]
    uv run --frozen python scripts/S514_fig3_d185.py t1 [--out <new or own folder>] [--allow-s476-sha-line]
                                                                                        (D188: T1 on D181)
    uv run --frozen python scripts/S514_fig3_d185.py t1 --check [--allow-s476-sha-line]
                     (D188: t1 again into a temporary folder; its rows and tables byte-equal to the committed
                      T1_L2_d181/, its header equal but for "code", "gates" and "script_sha256"; writes nothing)
    uv run --frozen python scripts/S514_fig3_d185_test.py                              (offline tests and mutants)

G4C (panel c; P3 and P4). Without --copy it reads S476's frozen copy (S476.frozen_copy(): fig3_inputs and
fig3_g4_inputs.tar, G4 draw 1). With --copy, a pull folder of S476's layout (s3/out_g4, s3/out_g4r38,
g4_collect.jsonl, g4_inputs/) whose answer lines may hold draws 2 and 3. The S6 outs (out_s6_g4, out_s6_g4r38,
out_s6_g7_g4, each with judge/<run>/judge_passages.jsonl and judge_passages_headers.jsonl, and claims.txt or claims/)
are read from --s6, else (no --copy) from findings/recompute/fig3_s6_inputs (D203), else from the copy's s3/; those
absent are skipped and recorded.
  Reproduce first, in this order; any difference exits 2 with nothing written:
  R1  S476.g4_build on the frozen copy into a temporary folder (S476's own gates: grid_gate with D149's anchor on the
      held reading, pre_d156_check, the judge-row check, the G4R38 texts, the frozen-input record), and every file
      it writes byte-equal to the committed findings/recompute/G4_fig3c/. With --allow-s476-sha-line (proposed for
      D188, Valerio's call; off by default) one line may differ: header.json's top-level "script_sha256", the sha256
      of S476 itself, which an edit of S476 changes before G4_fig3c is rewritten (D188 R1); compare_rebuilt then
      allows that line only, the gate records both values and the header's command names the option.
  R2  (a copy other than the frozen one) its draw-1 answer lines equal the frozen copy's, answer by answer, and its
      v2.4 collect equals the frozen g4_collect.jsonl row by row.
  R3  this script's cell builder, on the frozen copy with the v2.4 rows only, gives S476.g4_cells' six-strategy rows
      and units exactly (same JSON); so the reading below differs from S476's only by the rows chosen and the draws.
  The rows. scripts/judge_rows_v25.py (P2): the v2.4 source (g4_collect.jsonl held to s3/out_g4 and out_g4r38,
  check_v24, which also checks key_hash against all_v2_4.json), each S6 source present (s3_guard collect run here into
  a temporary file, then check_v25), and choose(): per answer, draw 1 takes the v2.5 row of a changed question where
  one exists, else the v2.4 row ("awaiting S6"); draws 2 and 3 take the G7 row only. Each source keeps its own single
  run_sha256 (load), which replaces S476:887-889's one-run test.
  The cells: S476.g4_cells' rule at each draw (a pass at correctness 4 and 3; an input failure scores 0, Rule 10; a
  G4R38 key with no judged rerun held out; a failed judge call unscored); a unit (strategy, index) is complete at a
  draw when no claim of the out judging that draw names it, its summary is there, and its judged answers plus its
  failed answers at that draw equal its answer lines at that draw (the per-draw form of S476:874-875); a unit
  complete by those counts whose summary's status counts are not its rows' is refused (S476:876-881). At draw 1 the
  summaries of the 132's S6 outs are counted, not required (a summary is the last run's selection); at draws 2 and 3
  the summary of G7's out (out_s6_g7_g4) is required, as above. The 39 not-answerable questions get a
  cell refused = refusal_accuracy 3 or more under the decline prompt (Rule 9; a failed answer is not refused, Rule
  10), and the ten false-premise questions a cell passed = correctness 4 or 3 against the refutation (Rule 9).
  v25_held_check (the D156 pattern): the draw-1 cells equal the v2.4-only reading's, but for the questions of the 132
  (S512.changed_ids()), whose differing cells are listed; a grid cell may differ only where such a question enters it.
Writes findings/recompute/G4_fig3c_d185/ (refused if it exists and is not this script's). Every table file carries
"provisional" and "awaiting_s6": the draw-1 answers it reads from a key v2.4 row of one of the 132 changed questions
(judge_rows_v25.choose's "v2.4 awaiting S6"), in total and per unit (strategy and index); each grid cell also carries
its own count (awaiting_s6_answers, the strategy's and single pass's cells over the cell's covered questions).
  grid_pairs.jsonl, grid_tables.json  draw 1, every question, the main estimate: S476.grid_tables (D150, D126's covered
                                      questions); each row's key_versions say which key judged each cell
  noise_pairs.jsonl, noise_tables.json  the D98 subset's covered questions (6, 14, 29 and 29 per index) per draw read,
                                      S476.grid_tables on them, and each cell's range over the draws read; a draw is
                                      read only when every one of its 72 units is complete. The range (min_d_pp,
                                      max_d_pp) is null, with range_withheld saying why, when fewer than two draws are
                                      read ("no run-to-run reading yet") or when draw 1's cells for it hold an answer
                                      awaiting S6 (draw 1 on key v2.4 there, draws 2 and 3 on v2.5: the range would mix
                                      a key change with run-to-run noise)
  other_pairs.jsonl, other_noise_pairs.jsonl  (Figure 3e's refusal cells, fig3.md R3) the rows of the 39 and the ten at
                      draw 1, and at each draw read, each with its key_versions, as grid_pairs.jsonl and noise_pairs.jsonl
                      hold the answerable questions'; S522 reads them. --faults names a keys file of failed answers at a
                      later draw, g4r38.py list --draw's (D200, G4's three server faults); it is read as g4r38_keys.txt is
  left_out.json       P4 (a): per core size the questions left out of accuracy (answerable, of the 86) and of the
                      false-premise group (the refuting paper absent), with ids and answer counts; the 39 lose none
  refusal_tables.json P4 (b): Rule 9 on the 39, per strategy and index (the reading: one set-up, Rule 1) the mean over
                      the 39 of each question's refused share, its Rule 2 interval (S463.interval), D133's bounds at 0%
                      and 100%, failures in and left out, with k of n; beside it, per size, pooled_over_ratios: the
                      same over the size's three indexes, which no rule defines (proposed, Valerio's call); the
                      subset's 13 per draw read beside it, each block with its rests_on
  q66_tables.json     P4 (d): D185 (1)'s 66 (experiment.scaling_questions(5) per_size, in scope at every size): the 22
                      answerable (pass rate at 4 and 3, Rule 2 interval, per strategy and index, and pooled_over_ratios
                      as above), the 39 (refusal, as above) and the 5 false premise (Rule 9: k of n passed at 4 and 3,
                      no interval), never pooled; subset noise beside each, each block with its rests_on. The five are
                      scored by Rule 9's correctness against the refutation, which departs from D185 (1)'s word
                      "refusal" (no decline-prompt row exists for them); D200 settles it, and the file says so
  verdicts.json       P4 (e): S393's own verdict functions v_s1 and v_s2 (S393_early_claims.py:1003, :1033) on RLM-10
                      against single pass per index, at score 4 and at 3, failures in and left out; S2, a claim of no
                      difference, says "holds" only when at least 80% of its 9 cells are complete (S393's guard,
                      S393_early_claims.py:70 and decide :1879-1880), else "not enough data"; "holds at both
                      thresholds" only when both are "holds" (LIST.md Rule 5)
  absent_group.json   P4 (c): the "source paper absent" answers counted (no decline-prompt row exists for them, so
                      nothing is scored) and the judge job that would score them, proposed, not run
  header.json         inputs, gates, sources (answers by source, awaiting S6, run_sha256 by source), draws present and
                      read, planned counts, the draw-1 units under S476.g4_cells' field names (units_draw1, which
                      S476's plate needs to recompute grid_tables.json); "provisional": true; "code": the sha256 of each script whose functions
                      this run calls (S514, S476, judge_rows_v25, s3_guard, S512, S393, S463, S474, S470,
                      judge_passages) and whether it equals the file at HEAD (recorded, not refused)

L2G7 (panel a's G5 noise; P3 for S474 and S485). Reads a G5 copy in S474's --g5-copy layout (PULL.json and
results_v4/v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview*.json, each file's sha256 equal to PULL.json's), the
union of the files by answer key (S474.read_g5's rule; G7's draws 2 and 3 ran as four shares). Gates first: S474's G-A
(gate), G-B and G-C (gate_d181), and G-D here: S474.read_g5 and rows_for(d181) on the copy's draw 1 give
findings/recompute/L2_d135_d181/'s 860 G5 rows exactly. Then D181's rows (S474.rows_for, key v2.5) for every draw-2 and
draw-3 answer of the 29 subset questions at the ten caps, and per cap the per-draw means on the 29, failures in and
failures left out (Rule 10), with the range over the draws read (null, "no run-to-run reading yet", when only draw 1
is read).
Writes findings/recompute/L2_d135_d181_g7/ (concept_recall_g7.jsonl, noise_tables.json, header.json); the main
L2_d135_d181/ is not rewritten.

T1 (D188, Figure 3b on key v2.5). Anchor first: S476.t1_build on the frozen copy (fig3_t1.tar, with its frozen-input
record) into a temporary folder gives the committed findings/recompute/T1_L2/ byte for byte (with
--allow-s476-sha-line, header.json but for its script_sha256 line, as R1), with S474.gate (G-A) inside it; then S474.gate_d181 (G-B, G-C) and G-D on T1:
d181_concept_recall.score with an empty question on the v2.4 concepts gives T1_L2's text_recall_loose on all 360
answers. Each answer's text is read again from the copy's results files (its sha256 equal to T1_L2's answer_sha256)
and scored by S474.rows_for in its d181 mode on key v2.5 (concepts and question text), entered as system "G5"
because rows_for reads the cap's stop reasons by system and T1 runs Mentori's RLM (S476.t1_rows reads
S474.CAP_STOPS["G5"] for T1); each row is tied to its T1_L2 row (answer_sha256, status, failed, cap_reached,
stopped_by_cap, turns, stop reason, note flags). concept_recall is the text's value, 0 for a failed answer (Rule 10,
as T1_L2), text_concept_recall the text's value; cap_tables.json is S476.t1_tables on concept_recall.
Writes findings/recompute/T1_L2_d181/ (concept_recall.jsonl, cap_tables.json, header.json with held_to: the sha256 of
the T1_L2 rows and tables it was held to, which S476's plate checks). S476's plate draws b from it and b's
gemini-3-flash-preview reference from L2_d135_d181's G5 rows, and c from G4_fig3c_d185 (D188).

No model call, no network, no Studio access, no ssh.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import hashlib
import io
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
S6_FROZEN = ROOT / "findings" / "recompute" / "fig3_s6_inputs"   # D203: S6G4 and G4R38 on key v2.5 (S528 --add)
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S476 = _load("S476", ROOT / "scripts" / "S476_fig3_d123.py")       # g4_build, g4_cells, grid_tables, coverage_check
S474, S463, S470 = S476.S474, S476.S463, S476.S470
import judge_rows_v25 as JR  # noqa: E402                                 # P2: sources, read_source, choose, report
import S512_s6_rejudge_v25 as S512  # noqa: E402                          # changed_ids, g7_subset

SCRIPT = "scripts/S514_fig3_d185.py"
RECOMPUTE = ROOT / "findings" / "recompute"
OUT_G4 = RECOMPUTE / "G4_fig3c_d185"
OUT_L2G7 = RECOMPUTE / "L2_d135_d181_g7"
OUT_L2D284 = RECOMPUTE / "L2_d135_d181_d284"   # D284: G5 draws 2 and 3 on all 86 (l2g7 --all86)
OUT_T1 = RECOMPUTE / "T1_L2_d181"                                 # D188: t1
L2_D135_D181 = RECOMPUTE / "L2_d135_d181"
G4_FILES = ("pairs.jsonl", "header.json", "point_tables.json", "grid_pairs.jsonl", "grid_tables.json")
G4_ALL, GRID_STRATS, RATIOS = S476.G4_ALL, S476.GRID_STRATS, S476.G4_RATIOS
SIZES = tuple(sorted(S476.COVERED_WANT))
PASS3, PASS4 = S476.PASS3, S476.PASS4
REFUSED_AT = 3                                       # Rule 9: refused = refusal_accuracy 3 or more (decline prompt)
S2_COVERAGE_MIN = 0.8                                # S393's guard on a claim of no difference (S393_early_claims.py:70)
JUDGE_FAILED = S476.JUDGE_FAILED
GROUPS = ("answerable", "not_answerable", "false_premise")
# pins (scripts/S514_fig3_d185_test.py checks each against its source)
SUBSET_COVERED_WANT = {5: 6, 10: 14, 20: 29, 50: 29}           # D98's 45 within each size's covered questions (D126)
LEFT_OUT_WANT = {"answerable": {5: 64, 10: 42, 20: 0, 50: 0}, "false_premise": {5: 5, 10: 3, 20: 0, 50: 0},
                 "not_answerable": {5: 0, 10: 0, 20: 0, 50: 0}}
Q66_WANT = {"answerable": 22, "not_answerable": 39, "false_premise": 5}
SUBSET_Q66_WANT = {"answerable": 6, "not_answerable": 13, "false_premise": 2}
G7_DRAWS = tuple(S512.G7_DRAWS)                                 # (2, 3)
C_NOISE_PLANNED = len(G4_ALL) * len(RATIOS) * sum(SUBSET_COVERED_WANT.values()) * len(G7_DRAWS)   # 2,808
REFUSAL_PER_SIZE = 39 * len(G4_ALL) * len(RATIOS)              # 702 answers of the 39 per core size, per draw
ABSENT_D1_PLANNED = 2052                                       # the "source paper absent" answers at draw 1
G5_SUBSET_N, G5_CAPS_N = 29, 10
A_G5_NOISE_PLANNED = G5_SUBSET_N * G5_CAPS_N * len(G7_DRAWS)    # 580
A_G5_D284_PLANNED = 86 * G5_CAPS_N * len(G7_DRAWS)               # 1,720: D284, draws 2 and 3 on all 86


class Refused(Exception):
    """Refused before anything is written (exit 2)."""


def rel(p) -> str:
    return S476.rel(p)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def dumps(x) -> str:
    return json.dumps(x, indent=1, sort_keys=True, default=str) + "\n"


def jsonl(rows) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def jkey(t) -> str:
    return "|".join(map(str, t))


# ---------------------------------------------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------------------------------------------
def read_claims(out: Path) -> list:
    """A pulled out's claims.txt (S476's pull writes the names), else the names in its live claims/ folder."""
    f = out / "claims.txt"
    if f.is_file():
        return [x for x in f.read_text().splitlines() if x.strip()]
    d = out / "claims"
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


def load_answers(copy) -> tuple[list, dict, dict]:
    """Every answer line of G4's 72 runs in the copy (all draws), each run's file against MANIFEST.sha256 and its line
    count against COPY.json (S476.g4_cells' checks); (answers, by answer_key, info)."""
    inp = copy / "g4_inputs"
    copyj = json.loads((inp / "COPY.json").read_text())
    man = S476.read_manifest(inp / "MANIFEST.sha256")
    lines_want = copyj["answer_lines"]
    indexes = sorted({k.split("__")[2] for k in lines_want if k.split("__")[1] == "rlm_10"}, key=S476.index_parts)
    if len(indexes) != 12 or {S476.index_parts(i) for i in indexes} != {(c, r) for c in SIZES for r in RATIOS}:
        raise Refused(f"COPY.json names {len(indexes)} rlm_10 indexes, not the 12 of 5, 10, 20, 50 x 0, 1, 3")
    answers, by_key = [], {}
    for cfg in G4_ALL:
        for idx in indexes:
            run = S476.G4_RUN.format(config=cfg, index=idx)
            f = inp / "runs" / run / "answers.jsonl"
            if not f.exists() or man.get(f"runs/{run}/answers.jsonl") != S476.sha256_file(f):
                raise Refused(f"G4 inputs: {cfg} {idx} answers missing or not its MANIFEST line")
            L = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
            if len(L) != lines_want.get(run):
                raise Refused(f"G4 inputs: {cfg} {idx} holds {len(L)} answer lines, COPY.json {lines_want.get(run)}")
            for a in L:
                if a["answer_key"] != f"{idx}|{cfg}|{a['question_id']}|d{a['draw']}" or a["config"] != cfg \
                        or a["index_name"] != idx or a.get("run_id") != run:
                    raise Refused(f"G4 inputs: {a['answer_key']} in {cfg} {idx}: key, config, index or run differ")
                if a["answer_key"] in by_key:
                    raise Refused(f"G4 inputs: {a['answer_key']} twice")
                by_key[a["answer_key"]] = a
                answers.append(a)
    info = {"indexes": indexes, "copy": copyj.get("copied"), "copy_from": copyj.get("from"),
            "answer_lines": sum(lines_want.values()),
            "draws_present": sorted({a["draw"] for a in answers}),
            "answers_by_draw": {str(d): n for d, n in sorted(collections.Counter(a["draw"] for a in answers).items())}}
    return answers, by_key, info


def failed_input(a) -> bool:
    gen = a["generation"]
    return bool(gen.get("error") or not (gen.get("answer") or "").strip())


def read_sources(copy, s6_root: Path | None, tmp: Path, quiet=True) -> tuple[list, list]:
    """(Loaded sources, a record per source): the v2.4 source from the copy's g4_collect.jsonl, each S6 source present
    collected here by s3_guard collect into tmp (judge_rows_v25.collect_argv's arguments, called in process)."""
    srcs, recs = [], []
    v24 = JR.sources(copy / "s3", "G4")[0]
    if not v24["present"]:
        raise Refused(f"{v24['outs'][0]} is missing")
    try:
        L = JR.read_source(v24, copy / "g4_collect.jsonl")
    except JR.Refused as e:
        raise Refused(f"the v2.4 source: {e}") from e
    srcs.append(L)
    recs.append({"name": L.name, "kind": L.kind, "present": True, "rows": len(L.rows), "run_sha256": L.run_sha256,
                 "collect": rel(copy / "g4_collect.jsonl"),
                 "collect_sha256": S476.sha256_file(copy / "g4_collect.jsonl"), "headers": len(L.headers)})
    root = Path(s6_root) if s6_root is not None else copy / "s3"
    for s in JR.sources(root, "G4"):
        if s["kind"] == JR.V24:
            continue
        rec = {"name": s["name"], "kind": s["kind"], "present": s["present"], "outs": [rel(o) for o in s["outs"]]}
        if s["present"]:
            dest = tmp / f"collect_{s['name']}.jsonl"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = JR.guard().collect(s["outs"], s["replace"], dest, s["set"])
            if rc:
                raise Refused(f"s3_guard collect refused {s['name']}: {buf.getvalue().strip()[-300:]}")
            try:
                Ls = JR.read_source(s, dest)
            except JR.Refused as e:
                raise Refused(f"source {s['name']}: {e}") from e
            srcs.append(Ls)
            rec.update(rows=len(Ls.rows), run_sha256=Ls.run_sha256, collect_sha256=S476.sha256_file(dest),
                       headers=len(Ls.headers), claims=len(read_claims(s["outs"][0])))
        recs.append(rec)
    return srcs, recs


def choose(answers, srcs) -> dict:
    try:
        return JR.choose(answers, srcs)
    except JR.Refused as e:
        raise Refused(f"judge_rows_v25.choose: {e}") from e


def g7_out(srcs_recs: list) -> Path | None:
    for r in srcs_recs:
        if r["kind"] == JR.V25_ALL and r["present"]:
            o = Path(r["outs"][0])
            return o if o.is_absolute() else ROOT / o
    return None


# ---------------------------------------------------------------------------------------------------------------
# the cells, S476.g4_cells' rule at one draw
# ---------------------------------------------------------------------------------------------------------------
def read_summary(out: Path, run: str) -> dict | None:
    sf = out / "judge" / run / ("judge_" + "passages_summary.json")
    return json.loads(sf.read_text()) if sf.exists() else None


def summary_matches(out: Path, run: str, summ: dict) -> bool:
    """The summary's (a) status counts and rows equal its out's rows at the summary's draws (S476:876-881)."""
    jr = S476.judge_rows(out / "judge" / run)
    sd = set(summ.get("draws") or [])
    got = collections.Counter(d["a"]["status"] for d in jr.values() if d["draw"] in sd)
    return dict(got) == summ.get("status_a", {}) and summ.get("rows") == sum(got.values())


def cell_for(a, pick, r38, judged_r38, unit_complete, group) -> dict:
    """S476.g4_cells' cell (S476:920-945) for an answerable question; the same statuses for the other two groups,
    with refused (not answerable) or the passes against the refutation (false premise)."""
    k = a["answer_key"]
    na = group == "not_answerable"
    cell = ({"status": None, "refusal_accuracy": None, "refused": None, "failed": False} if na else
            {"status": None, "correctness": None, "pass3": None, "pass4": None, "failed": False})
    fail = ({"refused": 0} if na else {"pass3": 0, "pass4": 0})
    if k in r38 and k not in judged_r38:
        cell["status"] = "held_g4r38"
    elif k not in r38 and failed_input(a):
        cell.update(status="failed", failed=True, **fail)
    else:
        d = pick
        if d is None:
            if unit_complete:
                raise Refused(f"S3: {k} answered and not judged in a complete unit")
            cell["status"] = "not_judged"
        else:
            st = d["a"]["status"]
            if st == "ok":
                sc = d["a"].get("scores") or {}
                if na:
                    v = sc.get("refusal_accuracy")
                    if not isinstance(v, (int, float)):
                        raise Refused(f"S3: {k} (a) ok without a refusal_accuracy score")
                    cell.update(status="ok", refusal_accuracy=v, refused=int(v >= REFUSED_AT))
                else:
                    c = sc.get("correctness")
                    if not isinstance(c, (int, float)):
                        raise Refused(f"S3: {k} (a) ok without a correctness score")
                    cell.update(status="ok", correctness=c, pass3=int(c >= PASS3), pass4=int(c >= PASS4))
            elif st in JUDGE_FAILED:
                cell["status"] = "unscored"
            elif st == "no_answer":
                cell.update(status="failed", failed=True, **fail)
            else:
                raise Refused(f"S3: {k} (a) status {st!r}")
    return cell


def cells_at(copy, answers, choice, draw: int, out_for_draw: Path | None, indexes, g4r38_path=S476.G4R38_KEYS,
             g4r38_want=S476.G4R38_WANT_ALL, faults_path: Path | None = None) -> tuple[list, dict, dict]:
    """(rows6, other_rows, info) at one draw. rows6: S476.g4_cells' six-strategy rows (answerable questions of the
    common or per-size set); other_rows: the same shape for the 39 and the ten. out_for_draw: the out whose claims and
    summaries decide completeness at this draw (draw 1: s3/out_g4; draws 2 and 3: out_s6_g7_g4; None: nothing judged
    at this draw, every unit incomplete). faults_path (D200): a keys file of failed answers at a later draw, read as
    g4r38_path is: a key of this draw must be a stored failure, and it counts as G4R38's keys do (its rerun's row when
    judged, else held out)."""
    from experiments.runner import experiment as ex
    from experiments.scorers import records
    common_answerable = {q["id"] for q in ex.questions() if records.group_of(q["id"]) == "answerable"}
    covered = S476.coverage_check(S470.the_key()["questions"], common_answerable)
    g4r38 = S476.read_g4r38(g4r38_path)
    r38 = {k: v for k, v in g4r38.items() if v["config"] in G4_ALL}
    faults = {} if faults_path is None else {k: v for k, v in S476.read_g4r38(faults_path).items()
                                             if v["config"] in G4_ALL}
    r38.update(faults)
    by_ans = {a["answer_key"]: a for a in answers}
    pick = {}
    for a in answers:
        if a["draw"] == draw:
            ch = choice[JR.answer_ident(a)]
            pick[a["answer_key"]] = ch["row"]
    judged_r38 = {k for k in r38 if pick.get(k) is not None}
    for k in faults:
        if not k.endswith(f"|d{draw}"):
            continue
        a = by_ans.get(k)
        if a is None or a["draw"] != draw or not failed_input(a):
            raise Refused(f"the --faults key {k} is not a stored failure in the inputs")
    if draw == 1:
        by_cfg = collections.Counter(v["config"] for k, v in r38.items() if k not in faults)
        if g4r38_want is not None and {c: by_cfg.get(c, 0) for c in G4_ALL} != g4r38_want:
            raise Refused(f"g4r38_keys.txt lists {dict(by_cfg)} keys, not {g4r38_want}")
        for k, v in r38.items():
            if k in faults:
                continue
            a = by_ans.get(k)
            if a is None or not a["generation"].get("error") or a["generation"].get("stop_reason") != v["stop"]:
                raise Refused(f"G4R38 key {k} is not a {v['stop']} failure in the inputs")
    # every chosen row on the prompt Rule 8's group says, under the lock of D88 (S476:890-897)
    for k, d in pick.items():
        if d is None:
            continue
        if bool(d.get("answerable_prompt")) != (records.group_of(d["question_id"]) != "not_answerable"):
            raise Refused(f"rows: {k} judged on the wrong prompt for Rule 8's group")
        if d.get("lock_sha256") not in S476.LOCKS_OK:
            raise Refused(f"rows: {k} under lock {str(d.get('lock_sha256'))[:8]}, not d66daa28 or a lock equal to it (D205)")
    claims = read_claims(out_for_draw) if out_for_draw is not None else []
    units = {}
    for cfg in G4_ALL:
        for idx in indexes:
            run = S476.G4_RUN.format(config=cfg, index=idx)
            L = [a for a in answers if a["run_id"] == run and a["draw"] == draw]
            failed_nj = [a for a in L if failed_input(a)]
            judged = [a for a in L if not failed_input(a) and pick.get(a["answer_key"]) is not None]
            claimed = [c for c in claims if c.endswith("__" + run)]
            summ = read_summary(out_for_draw, run) if out_for_draw is not None else None
            complete = bool(L) and not claimed and summ is not None and len(judged) + len(failed_nj) == len(L)
            if complete and not summary_matches(out_for_draw, run, summ):     # S476:876-881, on a complete unit
                raise Refused(f"S3 {cfg} {idx} draw {draw}: the rows' (a) status counts are not the summary's "
                              f"{summ.get('status_a')} in {out_for_draw.name}")
            units[f"{cfg} {idx}"] = {"complete": complete, "claimed": bool(claimed), "summary": summ is not None,
                                     "judged_rows": len(judged), "failed_not_judged": len(failed_nj),
                                     "answer_lines": len(L)}
    rows6, other = [], []
    for idx in indexes:
        core, ratio = S476.index_parts(idx)
        qrows, orows = {}, {}
        for cfg in G4_ALL:
            for a in answers:
                if a["index_name"] != idx or a["config"] != cfg or a["draw"] != draw:
                    continue
                q = a["question_id"]
                sets = a.get("question_sets") or []
                if not ({"common", "per_size"} & set(sets)):
                    continue
                g = records.group_of(q)
                cell = cell_for(a, pick.get(a["answer_key"]), r38, judged_r38, units[f"{cfg} {idx}"]["complete"], g)
                target = qrows if g == "answerable" else orows
                row = target.setdefault(q, {"index": idx, "core_papers": core, "distractor_ratio": ratio,
                                            "question_id": q, "common": "common" in sets,
                                            "covered": "common" in sets and q in covered[core],
                                            "per_size": "per_size" in sets, "cells": {}}
                                        if g == "answerable" else
                                        {"index": idx, "core_papers": core, "distractor_ratio": ratio,
                                         "question_id": q, "group": g, "common": "common" in sets,
                                         "per_size": "per_size" in sets, "cells": {}})
                if row["common"] != ("common" in sets) or row["per_size"] != ("per_size" in sets):
                    raise Refused(f"G4 {idx} {q}: the strategies carry different question_sets")
                row["cells"][cfg] = cell
        for target, out in ((qrows, rows6), (orows, other)):
            for q in sorted(target):
                r = target[q]
                if set(r["cells"]) != set(G4_ALL):
                    raise Refused(f"G4 {idx} {q} draw {draw}: answered by {sorted(r['cells'])} only")
                r["both_units_complete"] = all(units[f"{c} {idx}"]["complete"] for c in G4_ALL)
                out.append(r)
    info = {"draw": draw, "units": units, "claims": claims, "g4r38_judged_keys": sorted(judged_r38),
            "out": None if out_for_draw is None else str(out_for_draw),
            "units_complete": sum(v["complete"] for v in units.values())}
    return rows6, other, info


def as_s476_units(units: dict) -> dict:
    """A draw-1 units dict under S476.g4_cells' field names (judged_rows_d1)."""
    return {k: {"complete": v["complete"], "claimed": v["claimed"], "summary": v["summary"],
                "judged_rows_d1": v["judged_rows"], "failed_not_judged": v["failed_not_judged"],
                "answer_lines": v["answer_lines"]} for k, v in units.items()}


def r3_gate(copy, answers, choice_v24, indexes) -> dict:
    """R3: on the v2.4 rows only at draw 1, this builder's rows and units equal S476.g4_cells' (six strategies)."""
    mine, _, info = cells_at(copy, answers, choice_v24, 1, copy / "s3" / "out_g4", indexes)
    ref, rinfo = S476.g4_cells(copy, S476.G4R38_KEYS, S476.G4R38_WANT_ALL, configs=G4_ALL)
    if not S476.same_json(mine, ref):
        diff = [f"{a['index']} {a['question_id']}" for a, b in zip(mine, ref) if not S476.same_json(a, b)]
        raise Refused(f"R3: the builder's {len(mine)} rows are not S476.g4_cells' {len(ref)} (first {diff[:2]})")
    if as_s476_units(info["units"]) != rinfo["units"]:
        bad = [k for k, v in as_s476_units(info["units"]).items() if rinfo["units"].get(k) != v]
        raise Refused(f"R3: units differ from S476.g4_cells' ({len(bad)}): {bad[:3]}")
    if info["g4r38_judged_keys"] != rinfo["g4r38_judged_keys"]:
        raise Refused("R3: the judged G4R38 keys differ from S476.g4_cells'")
    return {"rows": len(mine), "units": len(info["units"]), "units_complete": info["units_complete"],
            "what": "this script's cells_at on the v2.4 rows at draw 1 equals S476.g4_cells(configs=G4_ALL): rows "
                    "(same JSON), units and judged G4R38 keys"}


SCRIPT_SHA_LINE = re.compile(rb'^ "script_sha256": "[0-9a-f]{64}",?$')


def compare_rebuilt(name: str, new: bytes, old: bytes, allow_sha_line: bool = False) -> dict | None:
    """A file S476 rebuilt against its committed copy: None when byte-equal. With allow_sha_line (the
    --allow-s476-sha-line option, proposed for D188 R1, off by default), a header.json that differs in one line only,
    its top-level "script_sha256" line (the sha256 of S476 itself, which changes with any edit of S476), gives
    {"committed": .., "rebuilt": ..}; any other difference, and that one without the option, raises Refused."""
    if new == old:
        return None
    a, b = new.split(b"\n"), old.split(b"\n")
    diff = [i for i in range(max(len(a), len(b))) if i >= len(a) or i >= len(b) or a[i] != b[i]]
    if allow_sha_line and name == "header.json" and len(a) == len(b) and len(diff) == 1 and \
            SCRIPT_SHA_LINE.match(a[diff[0]]) and SCRIPT_SHA_LINE.match(b[diff[0]]):
        return {"committed": b[diff[0]].split(b'"')[3].decode(), "rebuilt": a[diff[0]].split(b'"')[3].decode()}
    only_sha = name == "header.json" and len(diff) == 1 and SCRIPT_SHA_LINE.match(a[diff[0]] if diff[0] < len(a) else b"")
    raise Refused(f"{name} differs from the committed file in {len(diff)} lines, first line {diff[0] + 1}"
                  + (" (its script_sha256 line only: --allow-s476-sha-line accepts that, proposed for D188 R1)"
                     if only_sha and not allow_sha_line else ""))


def compare_folder(names, new_dir: Path, old_dir: Path, gate: str, allow_sha_line: bool = False) -> dict:
    """compare_rebuilt on each file: (files byte-equal, the header's script_sha256 change or None)."""
    equal, sha_only = [], None
    for n in names:
        try:
            r = compare_rebuilt(n, (Path(new_dir) / n).read_bytes(), (Path(old_dir) / n).read_bytes(),
                                allow_sha_line)
        except Refused as e:
            raise Refused(f"{gate}: the rebuild differs from the committed {rel(old_dir)}: {e}") from None
        if r is None:
            equal.append(n)
        else:
            sha_only = r
    return {"files_equal": equal, "header_differs_only_in_script_sha256": sha_only,
            "allow_s476_sha_line": allow_sha_line}


def r1_gate(fcopy, allow_sha_line: bool = False) -> dict:
    """R1: S476.g4_build on the frozen copy into a temporary folder, every file byte-equal to the committed one (with
    allow_sha_line, header.json but for its script_sha256 line, compare_rebuilt, which is recorded)."""
    with tempfile.TemporaryDirectory(prefix="S514_r1_") as d:
        r = S476.g4_build(fcopy, Path(d), committed_header=S476.G4_FIG3C / "header.json")
        cmp_ = compare_folder(G4_FILES, Path(d), S476.G4_FIG3C, "R1", allow_sha_line)
    return {**cmp_, "grid_cells_complete": r["grid_cells_complete"],
            "anchor_gate_compared": r["gate"]["compared"], "frozen_check": r["frozen_check"],
            "checks_d160": S476.d160_summary(r["checks_d160"]),
            "what": f"S476.g4_build on the frozen copy reproduces {rel(S476.G4_FIG3C)} byte for byte"
                    + (", header.json but for its script_sha256 line when S476 has changed since "
                       "(--allow-s476-sha-line)" if allow_sha_line else "") + f" (its own gates: grid_gate with "
                    f"D149's anchor on the held reading, pre_d156_check, judge_row_check, the G4R38 texts, the "
                    f"frozen-input record)"}


def r2_gate(fcopy, answers, srcs) -> dict:
    """R2 (a copy other than the frozen one): its draw-1 answer lines equal the frozen ones, and its v2.4 rows equal
    the frozen collect's, row by row."""
    fans, _, _ = load_answers(fcopy)
    f1 = {a["answer_key"]: a for a in fans}
    n1 = {a["answer_key"]: a for a in answers if a["draw"] == 1}
    if set(f1) != set(n1):
        raise Refused(f"R2: the copy's draw-1 answers ({len(n1)}) are not the frozen copy's ({len(f1)})")
    bad = [k for k in f1 if not S476.same_json(f1[k], n1[k])]
    if bad:
        raise Refused(f"R2: {len(bad)} draw-1 answer lines differ from the frozen copy's, first {bad[0]}")
    frows = {tuple(JR.answer_ident(r)): r for r in S476.load_rows(fcopy / "g4_collect.jsonl")}
    v24 = srcs[0].rows
    if set(frows) != set(v24) or any(not S476.same_json(frows[k], v24[k]) for k in frows):
        raise Refused("R2: the copy's v2.4 rows are not the frozen g4_collect.jsonl's, row by row")
    return {"draw1_answers_equal": len(f1), "v24_rows_equal": len(frows)}


# ---------------------------------------------------------------------------------------------------------------
# readings
# ---------------------------------------------------------------------------------------------------------------
def key_versions(rows, choice, answers_by_key, draw) -> list:
    """Each row with key_versions {strategy: "v2.4", "v2.4 awaiting S6", "v2.5" or None}, from choose()."""
    out = []
    for r in rows:
        kv = {}
        for cfg in r["cells"]:
            a = answers_by_key[f"{r['index']}|{cfg}|{r['question_id']}|d{draw}"]
            st = choice[JR.answer_ident(a)]["status"]
            kv[cfg] = st if st in ("v2.4", "v2.4 awaiting S6", "v2.5") else None
        out.append({**r, "draw": draw, "key_versions": kv})
    return out


AWAIT = "v2.4 awaiting S6"
AWAIT_WHAT = ("draw-1 answers this table reads from a key v2.4 row of one of the 132 questions key v2.5 changed "
              "(judge_rows_v25.choose's 'v2.4 awaiting S6'): their cells can move once S6 judges them on v2.5")


def awaiting(rows_kv, qids=None, covered_only=False, strategies=None) -> dict:
    """The answers awaiting S6 among rows_kv (rows with key_versions), in total and per unit "strategy index"."""
    by = collections.Counter()
    for r in rows_kv:
        if (qids is not None and r["question_id"] not in qids) or (covered_only and not r.get("covered")):
            continue
        for cfg, kv in r["key_versions"].items():
            if kv == AWAIT and (strategies is None or cfg in strategies):
                by[f"{cfg} {r['index']}"] += 1
    return {"answers": sum(by.values()), "by_unit": dict(sorted(by.items())), "what": AWAIT_WHAT}


def cell_awaiting(rows_kv, index: str, strategy: str) -> int:
    """A grid cell's answers awaiting S6: the strategy's and single pass's cells over the index's covered questions."""
    return sum((r["key_versions"].get(strategy) == AWAIT) + (r["key_versions"].get("single_pass") == AWAIT)
               for r in rows_kv if r["index"] == index and r.get("covered"))


def v25_held_check(rows_d185: list, rows_v24: list, changed: set) -> dict:
    """The D156 pattern: every draw-1 cell equals the v2.4-only reading's, but for questions of the 132, whose differing
    cells are listed with both values; the grid cells that can move are those such a question enters."""
    a = {(r["index"], r["question_id"]): r for r in rows_d185}
    b = {(r["index"], r["question_id"]): r for r in rows_v24}
    if set(a) != set(b):
        raise Refused("v25_held_check: the two readings hold different question rows")
    bad, diff = [], []
    for k, r in a.items():
        for cfg, c in r["cells"].items():
            if not S476.same_json(c, b[k]["cells"][cfg]):
                if r["question_id"] in changed:
                    diff.append({"index": k[0], "question_id": k[1], "strategy": cfg, "v24": b[k]["cells"][cfg],
                                 "d185": c})
                else:
                    bad.append(f"{k[0]} {k[1]} {cfg}")
        if r["both_units_complete"] != b[k]["both_units_complete"]:
            bad.append(f"{k[0]} {k[1]}: unit completeness differs")
    if bad:
        raise Refused(f"v25_held_check: {len(bad)} cells of unchanged questions differ from the v2.4 reading, e.g. "
                      f"{bad[:3]}")
    return {"rows": len(a), "cells_differing": len(diff), "differing": diff,
            "what": "draw-1 cells equal to the v2.4-only reading but for the 132 changed questions (S512.changed_ids)"}


def grid_diff(g_new: dict, g_old: dict, held: dict) -> list:
    """Grid cells that differ between the readings, each one of an index and strategy (or its single pass) a
    differing cell of v25_held_check belongs to; any other difference refuses."""
    touched = set()
    for d in held["differing"]:
        touched |= {(s, d["index"]) for s in GRID_STRATS} if d["strategy"] == "single_pass" else \
            {(d["strategy"], d["index"])}
    k_ = lambda e: (e["score"], e["strategy"], e["index"])          # noqa: E731
    old = {k_(e): e for e in g_old["cells"]}
    out = []
    for e in g_new["cells"]:
        o = old[k_(e)]
        if not S476.cells_equal(e, o):
            if (e["strategy"], e["index"]) not in touched:
                raise Refused(f"grid cell {k_(e)} differs from the v2.4 reading, and no changed question enters it")
            out.append({"score": e["score"], "strategy": e["strategy"], "index": e["index"],
                        "v24": S476.cell_numbers(o), "d185": S476.cell_numbers(e)})
    return out


def subset_ids() -> set:
    return set(S512.g7_subset())


def q66_ids() -> dict:
    """D185 (1)'s 66: experiment.scaling_questions(5) per_size, by Rule 8's group; each in per_size at every size."""
    from experiments.runner import experiment as ex
    from experiments.scorers import records
    ids = [q["id"] for q in ex.scaling_questions(5)["per_size"]]
    for c in SIZES:
        per = {q["id"] for q in ex.scaling_questions(c)["per_size"]}
        if not set(ids) <= per:
            raise Refused(f"the 66 are not all in scope at {c} core papers")
    by = {g: sorted(q for q in ids if records.group_of(q) == g) for g in GROUPS}
    if {g: len(v) for g, v in by.items()} != Q66_WANT:
        raise Refused(f"the 66 by group {({g: len(v) for g, v in by.items()})}, not {Q66_WANT}")
    return by


def left_out(answers) -> dict:
    """P4 (a), D76 Q131: per core size, the common set's questions left out of that size's reading because a source
    (answerable) or refuting (false premise) paper is not among the index's core papers (D126's rule, S476.covered_set,
    checked against experiment.py's per-size set); the 39 have no source paper and are in scope at every size."""
    from experiments.runner import experiment as ex
    from experiments.scorers import records
    key = S470.the_key()["questions"]
    common = [q["id"] for q in ex.questions()]
    by = {g: [q for q in common if records.group_of(q) == g] for g in GROUPS}
    if any(key[q].get("source_files") for q in by["not_answerable"]):
        raise Refused("a not-answerable question has source_files: Q131's rule for the 39 is not 'no source paper'")
    out = {"sizes": {}, "rests_on": "the key (source_files) and experiment.py's per-size sets; answer counts draw 1",
           "what": "questions of the common set left out at each size; answers: the draw-1 answers of "
                                "the six strategies on the three indexes of the size"}
    for c in SIZES:
        per = {q["id"] for q in ex.scaling_questions(c)["per_size"]}
        e = {}
        for g in ("answerable", "false_premise"):
            cov = S476.covered_set(key, c, by[g])
            if cov != set(by[g]) & per:
                raise Refused(f"{c} core papers, {g}: the covered set is not experiment.py's per-size set")
            lo = sorted(set(by[g]) - cov)
            e[g] = {"in": len(cov), "left_out": len(lo), "left_out_ids": lo}
        if not set(by["not_answerable"]) <= per:
            raise Refused(f"{c} core papers: a not-answerable question is out of scope")
        e["not_answerable"] = {"in": len(by["not_answerable"]), "left_out": 0, "left_out_ids": []}
        n_ans = collections.Counter()
        for a in answers:
            if a["draw"] == 1 and S476.index_parts(a["index_name"])[0] == c:
                g = records.group_of(a["question_id"])
                if a["question_id"] in set(by.get(g, [])) and a["question_id"] in e[g]["left_out_ids"]:
                    n_ans[g] += 1
        for g in GROUPS:
            e[g]["left_out_answers_draw1"] = n_ans.get(g, 0)
        out["sizes"][str(c)] = e
    got = {g: {c: out["sizes"][str(c)][g]["left_out"] for c in SIZES} for g in GROUPS}
    if got != LEFT_OUT_WANT:
        raise Refused(f"left-out counts {got}, not {LEFT_OUT_WANT}")
    return out


def share_rows(rows, size, strat, qids, field, drop_failed=False, index=None) -> tuple[list, dict]:
    """Per question of qids, its share of field (refused, pass3 or pass4) over the size's indexes (or over the one
    index given) where the cell has a value (a failed answer counts 0; with drop_failed it is left out); (values in
    qids' order with None where no value, counts)."""
    by = collections.defaultdict(list)
    cnt = collections.Counter()
    for r in rows:
        if r["core_papers"] != size or r["question_id"] not in qids or (index is not None and r["index"] != index):
            continue
        c = r["cells"][strat]
        cnt[c["status"]] += 1
        if c[field] is None or (drop_failed and c["failed"]):
            continue
        by[r["question_id"]].append(c[field])
    vals = [(sum(by[q]) / len(by[q])) if by[q] else None for q in sorted(qids)]
    return vals, dict(sorted(cnt.items()))


def rate_of(vals, bounds=False) -> dict:
    """Rule 2: the mean over the questions with a value, S463.interval's 95% percentile interval; bounds (Rule 9,
    D133): a 0% rate's one-sided upper bound and a 100% rate's one-sided lower bound over those questions."""
    v = [x for x in vals if x is not None]
    n = len(v)
    out = {"questions": n, "questions_without_value": len(vals) - n}
    if not n:
        return out | {"rate_pct": None}
    m = float(np.mean(v))
    out["rate_pct"] = 100 * m
    out["ci95_pct"] = [100 * x for x in S463.interval(v, [1.0] * n)] if n >= 2 else None
    if bounds:
        out["zero_one_sided_upper_bound_pct"] = 100 * S463.zero_bound(n) if m == 0 else None
        out["full_one_sided_lower_bound_pct"] = 100 * S463.full_bound(n) if m == 1 else None
    return out


POOLED_NOTE = ("proposed, not a defined reading (Valerio's call): the mean over questions of each question's share "
               "over the size's three indexes (0, 1 and 3 times the distractors), so three set-ups are averaged as "
               "if they were draws; Rule 1 (LIST.md:236) defines the summary per question and set-up, and a set-up "
               "here is a strategy on one index (per_index is the reading)")


def refusal_block(rows, qids, sizes=SIZES) -> list:
    """Per size and strategy: per_index (the reading, Rule 1's set-up): k of n refused, statuses, and the Rule 9 rate
    over the questions with its Rule 2 interval and D133's bounds, failures in and left out; pooled_over_ratios: the
    same over the size's three indexes (POOLED_NOTE)."""
    out = []
    for c in sizes:
        for s in G4_ALL:
            v, cnt = share_rows(rows, c, s, qids, "refused")
            vf, _ = share_rows(rows, c, s, qids, "refused", drop_failed=True)
            per_index = []
            for ratio in RATIOS:
                idx = f"exp_v4_s{c}_n{ratio}"
                cs = [r["cells"][s] for r in rows if r["index"] == idx and r["question_id"] in qids]
                have = [x for x in cs if x["refused"] is not None]
                vi, _ = share_rows(rows, c, s, qids, "refused", index=idx)
                vif, _ = share_rows(rows, c, s, qids, "refused", drop_failed=True, index=idx)
                per_index.append({"index": idx, "distractor_ratio": ratio, "answers": len(cs),
                                  "with_value": len(have), "refused": sum(x["refused"] for x in have),
                                  "failed": sum(x["failed"] for x in cs),
                                  "unscored": sum(x["status"] == "unscored" for x in cs),
                                  "not_judged": sum(x["status"] == "not_judged" for x in cs),
                                  "failures_in": rate_of(vi, bounds=True),
                                  "failures_left_out": rate_of(vif, bounds=True)})
            out.append({"core_papers": c, "strategy": s, "answers_by_status": cnt, "per_index": per_index,
                        "pooled_over_ratios": {"status": POOLED_NOTE, "failures_in": rate_of(v, bounds=True),
                                               "failures_left_out": rate_of(vf, bounds=True)}})
    return out


def pass_block(rows, qids, sizes=SIZES) -> list:
    """Per size and strategy, at score 4 and 3: per_index (the reading): the pass rate over the questions with its
    Rule 2 interval, failures in and left out; pooled_over_ratios: the same over the size's three indexes
    (POOLED_NOTE)."""
    out = []
    for c in sizes:
        for s in G4_ALL:
            e = {"core_papers": c, "strategy": s, "per_index": [],
                 "pooled_over_ratios": {"status": POOLED_NOTE}}
            for ratio in RATIOS:
                idx = f"exp_v4_s{c}_n{ratio}"
                pi = {"index": idx, "distractor_ratio": ratio}
                for t, f in ((4, "pass4"), (3, "pass3")):
                    vi, cnt_i = share_rows(rows, c, s, qids, f, index=idx)
                    vif, _ = share_rows(rows, c, s, qids, f, drop_failed=True, index=idx)
                    pi[f"score{t}"] = {"failures_in": rate_of(vi), "failures_left_out": rate_of(vif)}
                    pi["answers_by_status"] = cnt_i
                e["per_index"].append(pi)
            for t, f in ((4, "pass4"), (3, "pass3")):
                v, cnt = share_rows(rows, c, s, qids, f)
                vf, _ = share_rows(rows, c, s, qids, f, drop_failed=True)
                e["pooled_over_ratios"][f"score{t}"] = {"failures_in": rate_of(v), "failures_left_out": rate_of(vf)}
                e["answers_by_status"] = cnt
            out.append(e)
    return out


def k_of_n_block(rows, qids, sizes=SIZES) -> list:
    """Rule 9 on false-premise questions: per size and strategy k passed of n answers with a value, at 4 and 3, per
    index too; no interval, no test, no ranking."""
    out = []
    for c in sizes:
        for s in G4_ALL:
            cs = [r["cells"][s] for r in rows if r["core_papers"] == c and r["question_id"] in qids]
            e = {"core_papers": c, "strategy": s, "answers": len(cs),
                 "answers_by_status": dict(sorted(collections.Counter(x["status"] for x in cs).items()))}
            for t, f in ((4, "pass4"), (3, "pass3")):
                have = [x for x in cs if x[f] is not None]
                e[f"score{t}"] = {"k": sum(x[f] for x in have), "n": len(have)}
            e["per_index"] = []
            for ratio in RATIOS:
                idx = f"exp_v4_s{c}_n{ratio}"
                ci = [r["cells"][s] for r in rows if r["index"] == idx and r["question_id"] in qids]
                e["per_index"].append({"index": idx, **{f"score{t}": {
                    "k": sum(x[f] for x in ci if x[f] is not None), "n": sum(x[f] is not None for x in ci)}
                    for t, f in ((4, "pass4"), (3, "pass3"))}})
            out.append(e)
    return out


def pair_cell(rows, strat, which, drop_failed=False) -> dict:
    """strat minus single pass on one index's covered questions with both cells present (S476.grid_point's pairing);
    drop_failed leaves out a pair where either answer failed (Rule 10's sensitivity)."""
    pairs = []
    for r in sorted(rows, key=lambda x: x["question_id"]):
        if not r["covered"]:
            continue
        a, b = r["cells"][strat], r["cells"]["single_pass"]
        if a[which] is None or b[which] is None or (drop_failed and (a["failed"] or b["failed"])):
            continue
        pairs.append((a[which], b[which]))
    n = len(pairs)
    if not n:
        return {"n_paired": 0}
    diffs = [x - y for x, y in pairs]
    return {"n_paired": n, "pass_strategy_pct": 100 * sum(x for x, _ in pairs) / n,
            "pass_single_pass_pct": 100 * sum(y for _, y in pairs) / n, "d_pp": 100 * float(np.mean(diffs)),
            "p_signflip": S463.signflip_p(diffs)}


def verdicts(rows6, units, grid) -> dict:
    """P4 (e): S393's v_s1 (single pass ahead of RLM-10 at 50 core papers in all three ratios, each Bonferroni x12
    P < 0.05) and v_s2 (no cell at 5, 10 or 20 core papers with Bonferroni P < 0.05), on the draw-1 cells of RLM-10
    against single pass over D126's covered questions; the sign-flip P is Rule 3's (on one draw the exact McNemar).
    Failures in (the grid's cells, checked equal) and left out (Rule 10). S2 is a claim of no difference, so, as S393's
    decide does for such a claim (S393_early_claims.py:70, :1879-1880), its "holds" stands only when at least 80% of
    its 9 cells are complete (S2_COVERAGE_MIN; 8 of 9), else "not enough data"; a "reverses" stands at any coverage.
    Holds at both thresholds only when both verdicts are holds (LIST.md Rule 5)."""
    S393 = _load("S393", ROOT / "scripts" / "S393_early_claims.py")
    by_idx = collections.defaultdict(list)
    for r in rows6:
        by_idx[r["index"]].append(r)
    gcell = {(e["score"], e["index"]): e for e in grid["cells"] if e["strategy"] == "rlm_10"}
    out = {"what": verdicts.__doc__, "rests_on": "draw 1, every covered question (D98's main estimate)",
           "claims": {}, "pairing": "D126's covered questions with both cells present "
           "(S476.grid_point), not S393's 'both answered' on the April exp05 tables (design Q3)"}
    for mode, drop in (("failures_in", False), ("failures_left_out", True)):
        for t, which in ((4, "pass4"), (3, "pass3")):
            cells = {}
            for c in SIZES:
                for ratio in RATIOS:
                    idx = f"exp_v4_s{c}_n{ratio}"
                    complete = units[f"rlm_10 {idx}"]["complete"] and units[f"single_pass {idx}"]["complete"]
                    if not complete:
                        cells[(c, ratio)] = None
                        continue
                    e = pair_cell(by_idx[idx], "rlm_10", which, drop)
                    if not drop:
                        g = gcell[(t, idx)]
                        if e["n_paired"] != g["n_paired"] or abs(e["d_pp"] - g["d_pp"]) > 1e-9 or \
                                abs(e["p_signflip"] - g["p_signflip"]) > 1e-12:
                            raise Refused(f"verdicts: RLM-10 {idx} score {t} is not the grid's cell")
                    cells[(c, ratio)] = {"n": e["n_paired"], "single_pass": e["pass_single_pass_pct"] / 100,
                                         "rlm_10": e["pass_strategy_pct"] / 100,
                                         "sp_minus_rlm": (e["pass_single_pass_pct"] - e["pass_strategy_pct"]) / 100,
                                         "P": e["p_signflip"], "P_bonferroni": min(1.0, 12 * e["p_signflip"])}
            s1c = {f"50 core, {r}x": cells[(50, r)] for r in RATIOS}
            if any(v is None for v in s1c.values()):
                v1 = "not enough data: a unit at 50 core papers is not complete"
            elif any(v["n"] < 10 for v in s1c.values()):
                v1 = "not enough data: a cell with under 10 pairs (S393 s1's minimum)"
            else:
                v1 = S393.v_s1({"cells": s1c}, None)
            s2c = {f"{c} core, {r}x": cells[(c, r)] for c in (5, 10, 20) for r in RATIOS}
            got = {k: v for k, v in s2c.items() if v is not None}
            res2 = {"cells": s2c, "n_cells": len(got), "n_significant": sum(v["P_bonferroni"] < 0.05 for v in got.values()),
                    "min_P_bonferroni": min((v["P_bonferroni"] for v in got.values()), default=None),
                    "coverage": len(got) / len(s2c)}
            if not any(v["n"] >= 10 for v in got.values()):
                v2 = "not enough data: no cell with 10 pairs (S393 s2's minimum)"
            else:
                v2 = S393.v_s2(res2, None)
                if v2 == "holds" and res2["coverage"] < S2_COVERAGE_MIN:
                    v2 = (f"not enough data: a claim of no difference holds only at {S2_COVERAGE_MIN:.0%} coverage "
                          f"(S393_early_claims.py:70); {len(got)} of {len(s2c)} cells complete")
            out["claims"].setdefault("S1", {}).setdefault(mode, {})[f"score{t}"] = {"verdict": v1, "cells": s1c}
            out["claims"].setdefault("S2", {}).setdefault(mode, {})[f"score{t}"] = {"verdict": v2, **res2}
    for cid in ("S1", "S2"):
        for mode in ("failures_in", "failures_left_out"):
            m = out["claims"][cid][mode]
            m["holds_at_both_thresholds"] = m["score4"]["verdict"] == "holds" and m["score3"]["verdict"] == "holds"
        out["claims"][cid]["verdict_differs_when_failures_left_out"] = any(
            out["claims"][cid]["failures_in"][s]["verdict"] != out["claims"][cid]["failures_left_out"][s]["verdict"]
            for s in ("score4", "score3"))
    out["claim_text"] = {c["id"]: {"claim": c["claim"], "rule": c["rule"]} for c in S393.CLAIMS
                         if c["id"] in ("S1", "S2")}
    return out


def absent_group(answers, choice, lo: dict, srcs_recs) -> dict:
    """P4 (c): the draw-1 answers whose question is in the common set and left out at the index's size (its source or
    refuting paper absent), counted; whether a decline-prompt judge row exists for any; and the job that would score
    them (proposed, not run)."""
    from experiments.scorers import records
    sub = subset_ids()
    by_size = {}
    tot = collections.Counter()
    for c in SIZES:
        ids = set(lo["sizes"][str(c)]["answerable"]["left_out_ids"]) | \
            set(lo["sizes"][str(c)]["false_premise"]["left_out_ids"])
        A = [a for a in answers if a["draw"] == 1 and S476.index_parts(a["index_name"])[0] == c
             and a["question_id"] in ids]
        bad = [a["answer_key"] for a in A if "common" not in (a.get("question_sets") or [])
               or "per_size" in (a.get("question_sets") or [])]
        if bad:
            raise Refused(f"absent group: {bad[0]} is not a common-only answer")
        rows = [choice[JR.answer_ident(a)]["row"] for a in A]
        r38 = [a for a, r in zip(A, rows) if failed_input(a) and r is not None]
        e = {"questions": len(ids), "questions_in_subset": len(ids & sub),
             "answers_draw1": len(A), "answered_draw1": sum(not failed_input(a) for a in A),
             "failed_draw1": sum(failed_input(a) for a in A),
             "g4r38_reruns_judged_draw1": len(r38),
             "to_judge_draw1": sum(not failed_input(a) for a in A) + len(r38),
             "rows_answerable_prompt": sum(1 for r in rows if r is not None and r.get("answerable_prompt")),
             "rows_decline_prompt": sum(1 for r in rows if r is not None and not r.get("answerable_prompt")),
             "by_group": dict(collections.Counter(records.group_of(a["question_id"]) for a in A)),
             "subset_answers_planned_draws_2_3": len(ids & sub) * len(G4_ALL) * len(RATIOS) * len(G7_DRAWS)}
        by_size[str(c)] = e
        for k in ("answers_draw1", "answered_draw1", "g4r38_reruns_judged_draw1", "to_judge_draw1",
                  "rows_decline_prompt", "subset_answers_planned_draws_2_3"):
            tot[k] += e[k]
    if tot["answers_draw1"] != ABSENT_D1_PLANNED:
        raise Refused(f"absent group: {tot['answers_draw1']} draw-1 answers, not {ABSENT_D1_PLANNED}")
    return {"sizes": by_size, "total": dict(tot), "scored": tot["rows_decline_prompt"] > 0,
            "to_judge_how": ("the answers with text, and the G4R38 keys whose rerun text S3 judged (their input line "
                             "is the failed call; the text is in findings/recompute/fig3_g4r38_inputs)"),
            "why_not_scored": ("no decline-prompt judge row exists for these answers: S3 judged them on the answerable "
                               "prompt (Rule 8 by the question's group), and the decline prompt "
                               "(scripts/S141_runner/judge.py:86-87) carries only the question and the answer"),
            "proposal": PROPOSAL_S513}


FP_DEPARTS = ("D185 (1) says refusal on the 5 false-premise questions; D200 (Am5, 1 November) calls that word an error: "
              "they are scored by Rule 9's correctness against the refutation. No decline-prompt judge row exists for "
              "them, since S3 judged them on the answerable prompt (Rule 8 by the question's group).")


PROPOSAL_S513 = (
    "Proposed, not run (design Q1, Valerio's call): scripts/S513_absent_decline.py, built as S512 is (judge_passages "
    "imported, the lock's [judge] call), with two things changed: the prompt (the decline prompt, answerable=False) "
    "and the selection (G4's draw-1 answers to answerable and false-premise questions of the common set whose source "
    "or refuting paper is not among the index's core papers: 69 questions x 18 runs at 5 core papers and 45 x 18 at "
    "10, 2,052 answers, those with text judged). Set S7G4A, out out_s7_absent_g4, its run_sha256 hashing the "
    "selection. Gate first: re-judge the 39's decline-prompt answers of one index and require the scores S3 stored. "
    "Optional: the D98 subset's draws 2 and 3 (subset_answers_planned_draws_2_3). Scored as Rule 9's refusal (refused "
    "= refusal_accuracy 3 or more), reported per size as a third group, never pooled (D76 Q131).")


# ---------------------------------------------------------------------------------------------------------------
# g4c
# ---------------------------------------------------------------------------------------------------------------
CODE_FILES = {"S514": SCRIPT, "S476": S476.SCRIPT, "judge_rows_v25": "scripts/judge_rows_v25.py",
              "s3_guard": "findings/recompute/S3_runs/s3_guard.py", "S512": "scripts/S512_s6_rejudge_v25.py",
              "S393": "scripts/S393_early_claims.py", "S463": "scripts/S463_fig2_ranking.py",
              "S474": "scripts/S474_l2_concept_recall.py", "S470": "scripts/S470_l1_signals.py",
              "judge_passages": "experiments/scorers/judge_passages.py"}


def code_record(files: dict | None = None) -> dict:
    """Each file whose functions this run calls (files, default CODE_FILES): its sha256, and whether its bytes equal
    HEAD's blob (git rev-parse HEAD:<path>, read only; null when the file is not in HEAD). Recorded, not refused. One
    call per file, and rev-parse in place of ls-tree (D201 Q9, 2 November 2026): S494's step d181 runs this under the
    read audit, whose allow list holds rev-parse and not ls-tree. The record is the same."""
    import subprocess
    files = CODE_FILES if files is None else files
    head = {}
    for path in files.values():
        r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"HEAD:{path}"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            head[path] = r.stdout.strip()
    out = {}
    for name, path in files.items():
        b = (ROOT / path).read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
        out[name] = {"path": path, "sha256": hashlib.sha256(b).hexdigest(),
                     "equals_head": (blob == head[path]) if path in head else None}
    return out


def out_folder(out: Path) -> Path:
    out = Path(out).expanduser().resolve()
    if out.resolve() in {p.resolve() for p in (S476.G4_FIG3C, S476.T1_L2, S476.L2, S476.L2_D135, L2_D135_D181)}:
        raise Refused(f"{rel(out)} is a committed reading: this script writes new folders only")
    if out.exists() and any(out.iterdir()):
        h = out / "header.json"
        if not h.is_file() or json.loads(h.read_text()).get("script") != SCRIPT:
            raise Refused(f"{out} exists and is not this script's folder: write into a new folder")
    return out


def g4c(copy_dir: Path | None = None, s6_root: Path | None = None, out: Path = OUT_G4, quiet=False,
        r1=True, allow_sha_line: bool = False, faults_path: Path | None = None) -> dict:
    out = out_folder(out)
    fcopy = S476.frozen_copy()
    gates = {}
    gates["R1"] = r1_gate(fcopy, allow_sha_line) if r1 else {"skipped": "fixture"}
    copy = fcopy if copy_dir is None else Path(copy_dir).expanduser().resolve()
    s6_default = s6_root is None and copy_dir is None
    if s6_default:              # D203 (2 Nov): the frozen set S528 holds (out_s6_g4, out_s6_g4r38 since S6G4 ended)
        s6_root = S6_FROZEN
    answers, by_key, ainfo = load_answers(copy)
    with tempfile.TemporaryDirectory(prefix="S514_collect_") as tmp:
        srcs, recs = read_sources(copy, s6_root, Path(tmp))
    if copy_dir is not None:
        gates["R2"] = r2_gate(fcopy, answers, srcs)
    indexes = ainfo["indexes"]
    choice_v24 = choose(answers, srcs[:1])
    choice = choose(answers, srcs)
    if copy_dir is None:
        gates["R3"] = r3_gate(copy, answers, choice_v24, indexes)
    else:
        fans, _, _ = load_answers(fcopy)
        with tempfile.TemporaryDirectory(prefix="S514_collect_") as tmp:
            fsrcs, _ = read_sources(fcopy, None, Path(tmp))
        gates["R3"] = r3_gate(fcopy, fans, choose(fans, fsrcs[:1]), indexes)
    out_g7 = g7_out(recs)
    s6_summaries = collections.Counter()             # each S6 out of the 132 (draw 1): informational, a summary is
    for r in recs:                                   # the last run's selection, so it can lag while S6 runs
        if r["kind"] == JR.V25_CHANGED and r["present"]:
            o = ROOT / r["outs"][0] if not Path(r["outs"][0]).is_absolute() else Path(r["outs"][0])
            for d in sorted((o / "judge").glob("*")):
                sm = read_summary(o, d.name)
                s6_summaries["no summary" if sm is None else
                             "summary equal to its rows" if summary_matches(o, d.name, sm) else
                             "summary not equal to its rows"] += 1
    gates["rows_tie"] = {"what": "judge_rows_v25.load on each source: every collect row is the latest row of its "
                                 "answer in that source's judge_passages.jsonl files, every answer judged there is in "
                                 "the collect, one run_sha256, the sidecar agrees; check_v24 or check_v25 on every "
                                 "row and header", "s6_summaries": dict(s6_summaries)}
    draws = ainfo["draws_present"]
    per_draw = {}
    for d in draws:
        o = copy / "s3" / "out_g4" if d == 1 else out_g7
        per_draw[d] = cells_at(copy, answers, choice, d, o, indexes, faults_path=faults_path)
    rows6, other, info1 = per_draw[1]
    rows6_v24, other_v24, info1_v24 = cells_at(copy, answers, choice_v24, 1, copy / "s3" / "out_g4", indexes)
    changed = set(S512.changed_ids())
    held = v25_held_check(rows6, rows6_v24, changed)
    held_other = v25_held_check(other, other_v24, changed)
    units1 = as_s476_units(info1["units"])
    grid = S476.grid_tables(rows6, indexes, units1)
    grid_v24 = S476.grid_tables(rows6_v24, indexes, as_s476_units(info1_v24["units"]))
    gdiff = grid_diff(grid, grid_v24, held)
    gates["v25_held_check"] = {"answerable": {k: v for k, v in held.items() if k != "differing"},
                               "other_groups": {k: v for k, v in held_other.items() if k != "differing"},
                               "grid_cells_differing": len(gdiff)}
    # noise: D98's subset, per draw read (every unit complete at that draw)
    sub = subset_ids()
    draws_read = [d for d in draws if per_draw[d][2]["units_complete"] == len(G4_ALL) * len(indexes)]
    noise_rows, noise = [], {"draws_present": draws, "draws_read": draws_read,
                             "units_complete_by_draw": {str(d): per_draw[d][2]["units_complete"] for d in draws},
                             "rule": "D98 (LIST.md:458-460): draws 2 and 3 on the subset give the run-to-run noise; a "
                                     "draw is read only when every one of its 72 units is complete", "per_draw": {}}
    for d in draws_read:
        r6 = [r for r in per_draw[d][0] if r["question_id"] in sub]
        noise_rows += key_versions(r6, choice, by_key, d)
        noise["per_draw"][str(d)] = {**S476.grid_tables(r6, indexes, as_s476_units(per_draw[d][2]["units"])),
                                     "rests_on": f"draw {d}, D98's subset within each index's covered questions"}
    cov_sub = {c: len({r["question_id"] for r in rows6 if r["covered"] and r["core_papers"] == c} & sub)
               for c in SIZES}
    if cov_sub != SUBSET_COVERED_WANT:
        raise Refused(f"the subset's covered questions per size {cov_sub}, not {SUBSET_COVERED_WANT}")
    nkv1 = [r for r in noise_rows if r["draw"] == 1]
    for d in draws_read:
        noise["per_draw"][str(d)]["awaiting_s6"] = awaiting([r for r in noise_rows if r["draw"] == d],
                                                            covered_only=True)
    rng = []
    for e in (noise["per_draw"].get("1") or {}).get("cells", []):
        vals = {dd: next((x.get("d_pp") for x in noise["per_draw"][str(dd)]["cells"]
                          if (x["score"], x["index"], x["strategy"]) == (e["score"], e["index"], e["strategy"])
                          and x["complete"]), None) for dd in draws_read}
        have = [v for v in vals.values() if v is not None]
        aw1 = cell_awaiting(nkv1, e["index"], e["strategy"])
        why = (f"no run-to-run reading yet: only draw {draws_read} read" if len(draws_read) < 2 else
               f"draw 1's cells hold {aw1} answers judged on key v2.4 that v2.5 changed (awaiting S6) while draws 2 "
               f"and 3 are on key v2.5: the range would mix a key change with run-to-run noise" if aw1 else None)
        rng.append({"score": e["score"], "index": e["index"], "strategy": e["strategy"],
                    "d_pp_by_draw": {str(k): v for k, v in vals.items()}, "awaiting_s6_answers_draw1": aw1,
                    "range_withheld": why,
                    "min_d_pp": min(have) if have and why is None else None,
                    "max_d_pp": max(have) if have and why is None else None})
    noise["range"] = rng
    noise["run_to_run"] = ("no run-to-run reading yet: only draw 1 read; each per_draw block is one draw's reading "
                           "on the subset" if len(draws_read) < 2 else
                           f"draws {draws_read} read; a cell's range is withheld while draw 1 holds answers awaiting S6")
    noise["subset_covered_per_index"] = {str(c): n for c, n in cov_sub.items()}
    # P4
    lo = left_out(answers)
    q66 = q66_ids()
    na_ids = set(q66["not_answerable"])
    fp_all = {r["question_id"] for r in other if r["group"] == "false_premise"}
    refusal = {"rule": "Rule 9: refused = refusal_accuracy 3 or more under the decline prompt; rate = the mean over "
                       "the 39 of each question's refused share over the size's three indexes (draw 1); Rule 2 "
                       "interval (S463.interval, 10,000 question resamples); D133's one-sided bounds at 0% and 100%; "
                       "a failed answer is not refused (Rule 10), and the rate is also given with failures left out",
               "rests_on": "draw 1, all 39 questions (D98's main estimate)",
               "main": refusal_block(other, na_ids), "noise": {}}
    n39 = sum(1 for r in other if r["question_id"] in na_ids and r["core_papers"] == 5)
    if n39 != 39 * len(RATIOS):
        raise Refused(f"the 39 hold {n39} question rows at 5 core papers, not {39 * len(RATIOS)}")
    okv = {d: key_versions(per_draw[d][1], choice, by_key, d) for d in draws_read}
    other_noise_rows = [r for d in draws_read for r in okv[d] if r["question_id"] in sub]
    r6kv = {d: key_versions(per_draw[d][0], choice, by_key, d) for d in draws_read}
    for d in draws_read:
        refusal["noise"][str(d)] = {"rests_on": f"draw {d}, the subset's 13", "tables": refusal_block(
            per_draw[d][1], na_ids & sub), "awaiting_s6": awaiting(okv[d], na_ids & sub)}
    if len(draws_read) < 2:
        refusal["run_to_run"] = "no run-to-run reading yet: only draw 1 read"
    q66_tab = {"what": "D185 (1): Reviewer 4's Question 1 on the 66 questions in scope at every size "
                       "(experiment.scaling_questions(5) per_size); three groups, each on its own, never pooled "
                       "(D76 Q131)", "ids": q66,
               "rests_on": {"main": "draw 1, every question of each group (D98's main estimate)",
                            "noise": "per draw read, D98's subset within each group (each block's rests_on)"},
               "answerable": {"rule": "pass = correctness 4 (pass rate) and 3 (relaxed), Rule 5; per question the "
                                      "share over the size's three indexes; Rule 2 interval",
                              "main": pass_block(rows6, set(q66["answerable"])), "noise": {}},
               "not_answerable": {"rule": refusal["rule"], "main": refusal["main"], "noise": refusal["noise"]},
               "false_premise": {"rule": "Rule 9: passed = correctness 4 or more against the refutation (3 relaxed); "
                                         "k of n, no interval, no test, no ranking",
                                 "departs_from_decision": FP_DEPARTS,
                                 "main": k_of_n_block(other, set(q66["false_premise"])), "noise": {}}}
    for d in draws_read:
        for g, rr, blk in (("answerable", r6kv[d], pass_block(per_draw[d][0], set(q66["answerable"]) & sub)),
                           ("false_premise", okv[d], k_of_n_block(per_draw[d][1], set(q66["false_premise"]) & sub))):
            qs = set(q66[g]) & sub
            q66_tab[g]["noise"][str(d)] = {"rests_on": f"draw {d}, D98's subset ({len(qs)} questions of the group)",
                                           "tables": blk, "awaiting_s6": awaiting(rr, qs)}
    q66_tab["not_answerable"]["noise_rests_on"] = "as refusal_tables.json's noise blocks (the subset's 13)"
    if len(draws_read) < 2:
        q66_tab["run_to_run"] = "no run-to-run reading yet: only draw 1 read"
    q66_tab["subset_ids"] = {g: sorted(set(v) & sub) for g, v in q66.items()}
    if {g: len(v) for g, v in q66_tab["subset_ids"].items()} != SUBSET_Q66_WANT:
        raise Refused(f"the 66's subset by group {({g: len(v) for g, v in q66_tab['subset_ids'].items()})}, not "
                      f"{SUBSET_Q66_WANT}")
    verd = verdicts(rows6, units1, grid)
    rows6_kv = key_versions(rows6, choice, by_key, 1)
    other_kv = key_versions(other, choice, by_key, 1)
    for e in grid["cells"]:
        e["awaiting_s6_answers"] = cell_awaiting(rows6_kv, e["index"], e["strategy"])
    PROV = True
    grid.update(provisional=PROV, awaiting_s6=awaiting(rows6_kv, covered_only=True))
    noise.update(provisional=PROV, awaiting_s6=awaiting(noise_rows, covered_only=True))
    refusal.update(provisional=PROV, awaiting_s6=awaiting(other_kv, na_ids))
    q66_tab["provisional"] = PROV
    for g, rr in (("answerable", rows6_kv), ("not_answerable", other_kv), ("false_premise", other_kv)):
        q66_tab[g]["awaiting_s6"] = awaiting(rr, set(q66[g]))
    verd.update(provisional=PROV, awaiting_s6=awaiting(rows6_kv, covered_only=True,
                                                       strategies={"rlm_10", "single_pass"}))
    absent = absent_group(answers, choice, lo, recs)
    rep = JR.report(choice)
    rep_small = {k: v for k, v in rep.items() if k not in ("awaiting_s6", "g7_not_judged")}
    rep_small["awaiting_s6"] = {"count": rep["awaiting_s6"]["count"]}
    rep_small["g7_not_judged"] = {"count": rep["g7_not_judged"]["count"]}
    plan = {"c_main_draw1": S476.c_planned(), "c_noise_draws_2_3": C_NOISE_PLANNED,
            "refusal_answers_per_size_draw1": REFUSAL_PER_SIZE, "absent_group_draw1": ABSENT_D1_PLANNED,
            "a_g5_noise_draws_2_3": A_G5_NOISE_PLANNED,
            "how": {"c_noise_draws_2_3": f"{len(G4_ALL)} strategies x {len(RATIOS)} ratios x the subset's covered "
                                         f"questions {SUBSET_COVERED_WANT} summed x draws {list(G7_DRAWS)}",
                    "refusal_answers_per_size_draw1": "39 x 6 strategies x 3 indexes"}}
    shas = S476.frozen_shas(fcopy, tars=("g4_inputs",))
    header = {"script": SCRIPT, "script_sha256": S476.sha256_file(Path(__file__)), "provisional": PROV,
              "code": code_record(),
              "command": "uv run --frozen python " + SCRIPT + " g4c" + ("" if copy_dir is None else " --copy <pull>")
                         + ("" if s6_root is None or s6_default else " --s6 <S6 outs>")
                         + ("" if faults_path is None else f" --faults {rel(faults_path)}")
                         + (" --allow-s476-sha-line" if allow_sha_line else ""),
              "decisions": ["D185 (2) P3 and P4", "D185 (1) (the 66; its false-premise group departs from the "
                            "decision's word 'refusal', settled by D200: q66_tables.json false_premise)",
                            "D184 (1) (G7 judged once on key v2.5)", "D98 (draw 1 main, "
                            "subset noise)", "D76 Q131", "D126", "D150", "D156", "LIST.md Rules 2, 5, 9, 10, 11"],
              "copy": rel(copy) if copy_dir is not None else str(fcopy),
              "frozen_inputs_sha256": shas if copy_dir is None else None,
              "g4_inputs_manifest_sha256": S476.sha256_file(copy / "g4_inputs" / "MANIFEST.sha256"),
              "answers": ainfo, "sources": recs, "choice_report": rep_small,
              "draws": {"present": draws, "read_for_noise": draws_read, "main": 1},
              "units_complete_draw1": info1["units_complete"], "units_draw1": units1,
              "g4r38_judged_keys": info1["g4r38_judged_keys"],
              "gates": gates, "planned": plan,
              "faults": None if faults_path is None else {"path": rel(faults_path),
                                                          "sha256": S476.sha256_file(faults_path)},
              "rows": {"grid_pairs": len(rows6), "noise_pairs": len(noise_rows), "other_groups_draw1": len(other),
                       "other_noise_pairs": len(other_noise_rows)},
              "outputs": ["grid_pairs.jsonl", "grid_tables.json", "noise_pairs.jsonl", "noise_tables.json",
                          "other_pairs.jsonl", "other_noise_pairs.jsonl", "left_out.json", "refusal_tables.json", "q66_tables.json", "verdicts.json",
                          "absent_group.json", "v25_differences.json", "header.json"],
              "s476": {"script_sha256": S476.sha256_file(ROOT / S476.SCRIPT),
                       "judge_rows_v25_sha256": S476.sha256_file(ROOT / "scripts" / "judge_rows_v25.py")}}
    files = {"grid_pairs.jsonl": jsonl(rows6_kv),
             "grid_tables.json": dumps({**grid, "rests_on": "draw 1, every covered question (D98's main estimate)"}),
             "noise_pairs.jsonl": jsonl(noise_rows), "other_pairs.jsonl": jsonl(other_kv),
             "other_noise_pairs.jsonl": jsonl(other_noise_rows),
             "noise_tables.json": dumps(noise), "left_out.json": dumps(lo), "refusal_tables.json": dumps(refusal),
             "q66_tables.json": dumps(q66_tab), "verdicts.json": dumps(verd), "absent_group.json": dumps(absent),
             "v25_differences.json": dumps({"cells": held["differing"] + held_other["differing"], "grid": gdiff}),
             "header.json": dumps(header)}
    stale = [p.name for p in out.iterdir() if p.is_file() and p.name not in files] if out.exists() else []
    if stale:
        raise Refused(f"{out} holds files this script does not write: {stale[:3]}")
    S476.write_files(out, files)
    res = {"out": str(out), "gates": gates, "sources": recs, "report": rep_small, "draws": header["draws"],
           "rows": header["rows"], "planned": plan, "absent_total": absent["total"],
           "units_complete_draw1": info1["units_complete"],
           "left_out_counts": {g: {c: lo["sizes"][str(c)][g]["left_out"] for c in SIZES} for g in GROUPS},
           "grid_cells_differing": len(gdiff), "cells_differing": held["cells_differing"]}
    if not quiet:
        print(f"R1 {len(gates['R1'].get('files_equal', []))} files of {rel(S476.G4_FIG3C)} byte-equal; R3 "
              f"{gates['R3']['rows']} rows and {gates['R3']['units']} units equal to S476.g4_cells")
        print(f"sources: " + "; ".join(f"{r['name']} {'rows ' + str(r.get('rows')) if r['present'] else 'absent'}"
                                       for r in recs))
        print(f"answers by status {rep_small['by_status']}; awaiting S6 {rep_small['awaiting_s6']['count']}; draws "
              f"present {draws}, read for noise {draws_read}; wrote {rel(out)}")
    return res


# ---------------------------------------------------------------------------------------------------------------
# l2g7: G5's draws 2 and 3 on the subset, D181's reading
# ---------------------------------------------------------------------------------------------------------------
def read_g5_all(copy: Path, ids, caps) -> tuple[list, dict]:
    """Every answer of the G5 copy at any draw (S474.read_g5's union and checks, all draws): answer dicts as
    S474.read_g5 builds them."""
    from experiments.runner import experiment as ex
    pull = json.loads((copy / "PULL.json").read_text(encoding="utf-8"))
    files = [f for f in sorted((copy / "results_v4").glob(S474.G5_GLOB)) if not f.name.endswith("_merged.json")]
    if not files:
        raise Refused(f"no G5 results file in {copy / 'results_v4'}")
    rows, shas = {}, {}
    for f in files:
        sha = S470.sha256_file(f)
        if sha != ((pull.get("files") or {}).get(f.name) or {}).get("sha256"):
            raise Refused(f"{f.name}: sha256 {sha[:12]} is not the one PULL.json records")
        shas[f.name] = sha
        for r in json.loads(f.read_text(encoding="utf-8")).get("results", []):
            k = r.get("answer_key")
            if k is None:
                raise Refused(f"{f.name}: a row without an answer_key")
            if k in rows and rows[k][0] != r:
                raise Refused(f"{k}: two different rows ({rows[k][1]} and {f.name})")
            rows.setdefault(k, (r, f.name))
    want = {}
    for d in (1, *G7_DRAWS):
        for q in ids:
            for c in caps:
                want[ex.answer_key(f"rlm_{c}", q, d)] = (c, q, d)
    out = []
    for k, (r, fname) in rows.items():
        if k not in want:
            raise Refused(f"{k}: not an answer of G5's design (draws 1 to 3, the 86, the ten caps)")
        c, q, d = want[k]
        rlm = r.get("rlm") or {}
        if (r.get("question_id"), r.get("depth"), r.get("draw")) != (q, c, d) or rlm.get("max_turns") != c:
            raise Refused(f"{k}: its row says question {r.get('question_id')}, depth {r.get('depth')}, draw "
                          f"{r.get('draw')}, max_turns {rlm.get('max_turns')}")
        ans = r.get("answer") or ""
        out.append({"system": "G5", "answer_key": k, "run_id": r.get("run_id"), "question_id": q, "draw": d,
                    "cap": c, "answer": ans, "error": r.get("error"), "status": S474.status_of(ans, r.get("error")),
                    "stop_reason": r.get("stop_reason"), "turns_used": rlm.get("turns"),
                    "turn_limit_note": rlm.get("turn_limit_note"), "source": f"{fname} {k}"})
    return out, {"files": shas, "rows": len(rows)}


def l2g7(g5_copy: Path, out: Path = OUT_L2G7, quiet=False, gates_ab=True, ref_dir: Path = L2_D135_D181,
         all86: bool = False) -> dict:
    """all86 (D284): draws 2 and 3 cover all 86 questions, not D98's subset alone. Every draw-2 and draw-3 row is scored
    (planned 1,720); the noise table stays on the subset's 29, as before, so the range strip does not change meaning."""
    out = out_folder(out)
    g5_copy = Path(g5_copy).expanduser().resolve()
    key24 = S470.the_key()
    gates = {}
    if gates_ab:
        try:
            gates["G-A"] = S474.gate(key24)
            gates.update(S474.gate_d181(key24))
        except S474.GateFail as e:
            raise Refused(f"S474 gate: {e}") from e
    key25 = S474.D181.the_key_v25(key24)
    ids, caps, _, _ = S474.design()
    d92, _ = S474.read_d92(S474.D92_LIST)
    g5d1, g5info = S474.read_g5(g5_copy, ids, caps)
    rows1 = S474.rows_for(g5d1, key25, d92, d181=True)
    ref = [r for r in S476.load_rows(ref_dir / "concept_recall.jsonl") if r["system"] == "G5"]
    rh = json.loads((ref_dir / "header.json").read_text())
    if rh.get("reading") != "D181" or rh.get("provisional") is not False or rh.get("script") != S474.SCRIPT:
        raise Refused(f"{rel(ref_dir)}/header.json is not S474's D181 reading")
    if jsonl(rows1) != jsonl(ref):
        n = sum(1 for a, b in zip(rows1, ref) if not S476.same_json(a, b))
        raise Refused(f"G-D: the copy's draw-1 rows are not {rel(ref_dir)}'s G5 rows ({len(rows1)} against "
                      f"{len(ref)}, {n} differ)")
    gates["G-D (draw 1)"] = {"reference": rel(ref_dir / "concept_recall.jsonl"), "rows_equal": len(ref)}
    allans, ainfo = read_g5_all(g5_copy, ids, caps)
    sub = sorted(subset_ids() & set(ids))
    if len(sub) != G5_SUBSET_N or len(caps) != G5_CAPS_N:
        raise Refused(f"G5's subset {len(sub)} questions and {len(caps)} caps, not {G5_SUBSET_N} and {G5_CAPS_N}")
    g7 = [a for a in allans if a["draw"] in G7_DRAWS]
    outside = [a["answer_key"] for a in g7 if a["question_id"] not in sub]
    if outside and not all86:
        raise Refused(f"G7: {len(outside)} draw-2 or draw-3 answers outside D98's subset, first {outside[0]}")
    order = {q: i for i, q in enumerate(ids)}
    g7.sort(key=lambda a: (a["draw"], order[a["question_id"]], caps.index(a["cap"])))
    rows7 = S474.rows_for(g7, key25, d92, d181=True)
    none = [r["answer_key"] for r in rows7 if r["concept_recall"] is None]
    if none:
        raise Refused(f"{len(none)} G7 answers have no counted concept under D181 (b)")
    present = {d: sum(r["draw"] == d and r["question_id"] in sub for r in rows7) for d in G7_DRAWS}
    full = len(sub) * len(caps)
    if all86:
        present_all = {d: sum(r["draw"] == d for r in rows7) for d in G7_DRAWS}
        if any(n != len(ids) * len(caps) for n in present_all.values()):
            raise Refused(f"D284: draws 2 and 3 must each hold all {len(ids) * len(caps)} answers, found {present_all}")
    read = [1] + [d for d in G7_DRAWS if present[d] == full]
    tab = {"rule": "D98: G5's main estimate is draw 1 on the 86 (L2_d135_d181); draws 2 and 3 on the subset's 29 give "
                   "the run-to-run noise; a draw is read only when all 290 of its answers are there",
           "draws_present": {str(d): n for d, n in present.items()}, "draws_read": read, "per_cap": {}}
    by = {1: [r for r in ref if r["question_id"] in sub]} | {d: [r for r in rows7 if r["draw"] == d and r["question_id"] in sub]
                                                             for d in G7_DRAWS}
    for c in caps:
        e = {}
        for d in read:
            R = [r for r in by[d] if r["cap"] == c]
            Rk = [r for r in R if not r["failed"]]
            e[str(d)] = {"answers": len(R), "mean": round(float(np.mean([r["concept_recall"] for r in R])), 4),
                         "failed": sum(r["failed"] for r in R),
                         "mean_failures_left_out": (round(float(np.mean([r["concept_recall"] for r in Rk])), 4)
                                                    if Rk else None)}
        ms = [v["mean"] for v in e.values()]
        mk = [v["mean_failures_left_out"] for v in e.values() if v["mean_failures_left_out"] is not None]
        one = len(read) < 2
        tab["per_cap"][str(c)] = {"by_draw": e, "min": None if one else min(ms), "max": None if one else max(ms),
                                  "min_failures_left_out": None if one or not mk else min(mk),
                                  "max_failures_left_out": None if one or not mk else max(mk),
                                  "range_withheld": "no run-to-run reading yet: only draw 1 read" if one else None,
                                  "rests_on": f"draws {read}, the subset's 29"}
    tab["rule_failures"] = ("Rule 10: mean keeps every answer, a failed one (an error stored, S474.status_of) at "
                            "the concept recall of its stored text, 0 when empty; mean_failures_left_out leaves the "
                            "failed answers out, as S474.per_question with drop_failed")
    header = {"script": SCRIPT, "script_sha256": S476.sha256_file(Path(__file__)), "provisional": True,
              "code": code_record(), "reading": "D181 (S474.rows_for with d181, key v2.5)", "command": f"uv run --frozen python {SCRIPT} l2g7 " + ("--all86 " if all86 else "") + 
              "--g5-copy <G5 copy>", "gates": gates, "inputs": {"G5": {"copy": rel(g5_copy), **ainfo},
                                                                 "draw1_files": g5info["files"]},
              "rows": len(rows7), "planned": A_G5_D284_PLANNED if all86 else A_G5_NOISE_PLANNED,
              "all86": all86, "subset": sub, "caps": list(caps),
              "s474_sha256": S476.sha256_file(ROOT / S474.SCRIPT)}
    S476.write_files(out, {"concept_recall_g7.jsonl": jsonl(rows7), "noise_tables.json": dumps(tab),
                           "header.json": dumps(header)})
    if not quiet:
        print(f"G-D: {len(ref)} draw-1 rows equal to {rel(ref_dir)}; G7 rows {len(rows7)} of {A_G5_NOISE_PLANNED} "
              f"planned, by draw {present}; wrote {rel(out)}")
    return {"out": str(out), "rows": len(rows7), "present": present, "read": read, "gates": list(gates)}


# ---------------------------------------------------------------------------------------------------------------
# t1: T1's answers on D181's reading (key v2.5), D188
# ---------------------------------------------------------------------------------------------------------------
T1_FILES = ("concept_recall.jsonl", "cap_tables.json", "header.json")
T1_ANSWERS_WANT = 360                                # D119 Q5: 4 models x 15 questions x 6 caps, draw 1
T1_KEEP = ("model", "cap", "question_id", "draw", "answer_key", "run_id", "status", "failed", "error_kind",
           "stop_reason", "turns_used", "turn_limit_note", "answer_sha256", "cap_reached", "stopped_by_cap",
           "in_complete_question")
T1_FROM_ROWS_FOR = ("note_removed", "scored_text_sha256", "n_concepts", "n_counted", "found", "concept_status",
                    "concept_removed", "found_loose_base", "found_exact_base", "concept_recall_loose_base",
                    "concept_recall_exact_base", "found_by_base", "empty_text")
T1_TIE_ROWS_FOR = ("answer_sha256", "status", "failed", "cap_reached", "stopped_by_cap", "turns_used", "stop_reason",
                   "turn_limit_note", "note_removed")
T1_CODE_FILES = {"S514": SCRIPT, "S476": S476.SCRIPT, "S474": "scripts/S474_l2_concept_recall.py",
                 "S470": "scripts/S470_l1_signals.py", "check_t1": "findings/recompute/T1_runs/check_t1.py"}


def t1_answers(copy, rows24: list) -> list:
    """Each T1_L2 row's stored answer, read again from the copy's results files (check_t1.answers, as S476.t1_rows
    reads them), its text's sha256 equal to the row's answer_sha256, as an answer dict of S474.rows_for's shape.
    rows_for reads the stop reasons that mean "cut by the cap" by system: T1 runs Mentori's RLM as G5 does (S476.t1_rows
    reads S474.CAP_STOPS["G5"] for T1), so each answer goes in as system "G5"; t1() writes the row under the model."""
    results = copy / "t1" / "results_v4"
    stored = {}
    for m in S476.T1_FOUR:
        st, pr = S476.CT.answers(m, False, results)
        if pr:
            raise Refused(f"T1 {m}: {pr[:2]}")
        stored[m] = st
    out = []
    for r in rows24:
        x = stored[r["model"]].get(r["answer_key"])
        if x is None:
            raise Refused(f"T1 {r['model']} {r['answer_key']}: no stored answer in the copy")
        ans = x.get("answer") or ""
        if S470.sha256_text(ans) != r["answer_sha256"]:
            raise Refused(f"T1 {r['model']} {r['answer_key']}: the stored text is not the one T1_L2 scored")
        rlm = x.get("rlm") or {}
        out.append({"system": "G5", "answer_key": r["answer_key"], "run_id": r["run_id"], "question_id": r["question_id"],
                    "draw": r["draw"], "cap": r["cap"], "status": r["status"], "stop_reason": x.get("stop_reason"),
                    "turns_used": rlm.get("turns"), "turn_limit_note": rlm.get("turn_limit_note"),
                    "source": f"T1 {r['model']} {r['answer_key']}", "answer": ans})
    return out


def t1_code_record() -> dict:
    """As code_record(), for the files t1 calls, and d181_concept_recall's own list (S505, the matchers)."""
    return {**code_record(T1_CODE_FILES), "d181": S474.D181.code_sha256()}


def t1(out: Path = None, quiet=False, gates_bc=True, copy=None, anchor_dir: Path | None = None,
       allow_sha_line: bool = False) -> dict:
    """D188 (A1): T1_L2_d181. Anchor first: S476.t1_build on the frozen copy into a temporary folder gives the
    committed T1_L2 (anchor_dir) byte for byte (with allow_sha_line, header.json but for its script_sha256 line,
    compare_rebuilt); then
    S474's G-B and G-C (gate_d181), and G-D on T1: d181_concept_recall.score with an empty question on the v2.4
    concepts equals T1_L2's text_recall_loose on every answer. Then S474.rows_for in its d181 mode on key v2.5 (the
    concepts and the question text), each row tied to T1_L2's (T1_TIE_ROWS_FOR); concept_recall is the text's value,
    0 for a failed answer (Rule 10, as T1_L2's concept_recall_loose); cap_tables.json is S476.t1_tables on
    concept_recall. gates_bc False and copy (a fixture pull) are for the tests."""
    out = out_folder(OUT_T1 if out is None else out)
    anchor_dir = S476.T1_L2 if anchor_dir is None else Path(anchor_dir)
    fcopy = S476.frozen_copy() if copy is None else copy
    key24 = S470.the_key()
    gates = {}
    with tempfile.TemporaryDirectory(prefix="S514_t1_") as d:
        r1 = S476.t1_build(fcopy, Path(d), committed_header=anchor_dir / "header.json" if copy is None else None,
                           gate=copy is None)
        gates["anchor T1_L2"] = {**compare_folder(T1_FILES, Path(d), anchor_dir, "anchor T1_L2", allow_sha_line),
                                 "frozen_check": r1["frozen_check"], "G-A": r1["gate"],
                                 "what": f"S476.t1_build on the frozen copy reproduces {rel(anchor_dir)} byte for "
                                         f"byte" + (", header.json but for its script_sha256 line when S476 has "
                                                    "changed (--allow-s476-sha-line)" if allow_sha_line else "")
                                         + " (its gate G-A: S474.gate reproduces S383)"}
        rows24 = S476.load_rows(Path(d) / "concept_recall.jsonl")
        tab24 = json.loads((Path(d) / "cap_tables.json").read_text())
        head24 = json.loads((Path(d) / "header.json").read_text())
    if len(rows24) != T1_ANSWERS_WANT and copy is None:
        raise Refused(f"T1_L2 holds {len(rows24)} answers, not {T1_ANSWERS_WANT}")
    if gates_bc:
        try:
            gates.update(S474.gate_d181(key24))
        except S474.GateFail as e:
            raise Refused(f"S474 gate_d181: {e}") from e
    key25 = S474.D181.the_key_v25(key24)
    answers = t1_answers(fcopy, rows24)
    differ = [r["answer_key"] for a, r in zip(answers, rows24)
              if S474.D181.score(a["answer"], key24["questions"][a["question_id"]]["expected_concepts"], "",
                                 a["turn_limit_note"])["concept_recall"] != r["text_recall_loose"]]
    if differ:
        raise Refused(f"G-D (T1): the D181 score with an empty question gives T1_L2's loose value on "
                      f"{len(rows24) - len(differ)} of {len(rows24)} answers; first differing {differ[:3]}")
    gates["G-D (T1)"] = {"reproduced": f"{len(rows24)} of {len(rows24)}", "reference": rel(anchor_dir / T1_FILES[0]),
                         "compared": "d181_concept_recall.score(answer, v2.4 concepts, question '', flag)"
                                     ".concept_recall = T1_L2's text_recall_loose, every answer"}
    rf = S474.rows_for(answers, key25, {}, d181=True)
    rows, bad, none = [], [], []
    for r24, x in zip(rows24, rf):
        off = [f for f in T1_TIE_ROWS_FOR if x.get(f) != r24.get(f)]
        if off:
            bad.append(f"{r24['model']} {r24['answer_key']}: {off}")
        if x["concept_recall"] is None:
            none.append(r24["answer_key"])
        row = {k: r24[k] for k in T1_KEEP}
        row.update({k: x[k] for k in T1_FROM_ROWS_FOR})
        row["text_concept_recall"] = x["concept_recall"]
        row["concept_recall"] = 0.0 if r24["failed"] else x["concept_recall"]
        rows.append(row)
    if bad:
        raise Refused(f"rows_for's rows are not tied to T1_L2's ({len(bad)}), first {bad[0]}")
    if none:
        raise Refused(f"{len(none)} T1 answers have no counted concept under D181 (b), first {none[:3]}")
    tables = S476.t1_tables(rows, tab24["models"], tab24["caps"], tab24["complete_questions"], field="concept_recall")
    k24, k25 = S512.keys()
    same_c = {q for q in k24 if k24[q].get("expected_concepts") == k25[q].get("expected_concepts")}
    qs = sorted({r["question_id"] for r in rows})
    header = {"script": SCRIPT, "script_sha256": S476.sha256_file(Path(__file__)), "provisional": False,
              "reading": "D181", "plan_row": "T1",
              "command": f"uv run --frozen python {SCRIPT} t1" + (" --allow-s476-sha-line" if allow_sha_line else ""),
              "what": "D188: T1's stored draw-1 answers of the four local models (T1_L2's 360) on D181's concept "
                      "recall, key v2.5, the reading Figure 3b draws; a failed answer 0 (Rule 10)",
              "matcher": S474.D181.MATCHER_TEXT, "columns": S474.D181.COLUMNS_TEXT + "; text_concept_recall: the "
              "D181 value of the stored text; concept_recall: that value, 0 for a failed answer (Rule 10)",
              "key": {"path": key25["path"], "sha256": key25["sha256"], "version": key25["version"]},
              "gate_key": {"path": key24["path"], "sha256": key24["sha256"], "version": key24["version"]},
              "held_to": {n: {"path": rel(anchor_dir / n), "sha256": S476.sha256_file(anchor_dir / n)}
                          for n in ("concept_recall.jsonl", "cap_tables.json")},
              "frozen_inputs_sha256": head24.get("frozen_inputs_sha256"), "copy": str(fcopy),
              "gates": gates, "code": t1_code_record(), "rows": len(rows), "k": tables["k"],
              "models": list(tab24["models"]), "caps": list(tab24["caps"]),
              "questions": {"all": len(qs), "concepts_unchanged_by_v25": len(set(qs) & same_c)},
              "counts": {"failed": sum(r["failed"] for r in rows), "note_removed": sum(r["note_removed"] for r in rows),
                         "d181": S474.D181.concept_counts(rows)}}
    S476.write_files(out, {"concept_recall.jsonl": jsonl(rows), "cap_tables.json": dumps(tables),
                           "header.json": dumps(header)})
    if not quiet:
        a = gates["anchor T1_L2"]
        print(f"anchor: {len(a['files_equal'])} files of {rel(anchor_dir)} byte-equal"
              + (f", header.json but for its script_sha256 line ({a['header_differs_only_in_script_sha256']['committed'][:8]}"
                 f" committed, {a['header_differs_only_in_script_sha256']['rebuilt'][:8]} now)"
                 if a["header_differs_only_in_script_sha256"] else "")
              + f"; G-D (T1) {gates['G-D (T1)']['reproduced']}; {len(rows)} rows, k {tables['k']}; wrote {rel(out)}")
    return {"out": str(out), "rows": len(rows), "k": tables["k"], "gates": gates, "tables": tables}


T1_CHECK_HEADER_ASIDE = ("code", "gates", "script_sha256", "command")


def t1_check(committed: Path = None, allow_sha_line: bool = False, quiet=False) -> dict:
    """D188 (review of build 1, F1): t1 again, into a temporary folder, held to the committed T1_L2_d181/:
    concept_recall.jsonl and cap_tables.json byte for byte, header.json equal as JSON but for the keys
    T1_CHECK_HEADER_ASIDE (the code record's HEAD flags, the gates' anchor record, this script's sha256 and the
    command change when the code is committed or edited without changing a value). Refused on any other difference;
    writes nothing in the repository. S494 does not run this check: its step d181 (D201 Q9 O1) runs t1 itself and
    compares the rows and tables. S514_fig3_d185_test.py runs this check with allow_sha_line, so that test cannot see a
    header whose S476 sha256 line is stale; S494's d181 step, which runs t1 without the flag, can."""
    committed = OUT_T1 if committed is None else Path(committed)
    if not (committed / "header.json").is_file():
        raise Refused(f"{rel(committed)} holds no header.json: nothing to check")
    with tempfile.TemporaryDirectory(prefix="S514_t1check_") as d:
        r = t1(Path(d) / "T1_L2_d181", quiet=True, allow_sha_line=allow_sha_line)
        new = Path(r["out"])
        bad = [n for n in T1_FILES[:2] if (new / n).read_bytes() != (committed / n).read_bytes()]
        h_new, h_old = (json.loads((x / "header.json").read_text()) for x in (new, committed))
    for h in (h_new, h_old):
        for k in T1_CHECK_HEADER_ASIDE:
            h.pop(k, None)
    if h_new != h_old:
        bad.append("header.json (keys " + ", ".join(sorted(k for k in set(h_new) | set(h_old)
                                                           if h_new.get(k) != h_old.get(k))) + ")")
    if bad:
        raise Refused(f"t1 --check: a rebuild differs from the committed {rel(committed)} in {bad}")
    rec = {"committed": rel(committed), "files_equal": list(T1_FILES[:2]), "rows": r["rows"], "k": r["k"],
           "header_equal_but_for": list(T1_CHECK_HEADER_ASIDE)}
    if not quiet:
        print(f"t1 --check: {rel(committed)} reproduced ({r['rows']} rows, k {r['k']}; concept_recall.jsonl and "
              f"cap_tables.json byte-equal, header.json equal but for {', '.join(T1_CHECK_HEADER_ASIDE)})")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("g4c")
    g.add_argument("--copy", type=Path, default=None)
    g.add_argument("--s6", type=Path, default=None)
    g.add_argument("--out", type=Path, default=OUT_G4)
    g.add_argument("--allow-s476-sha-line", action="store_true")
    g.add_argument("--faults", type=Path, default=None, help="g4r38.py list --draw's keys file (D200)")
    t = sub.add_parser("t1")
    t.add_argument("--out", type=Path, default=None)
    t.add_argument("--check", action="store_true")
    t.add_argument("--allow-s476-sha-line", action="store_true")
    lg = sub.add_parser("l2g7")
    lg.add_argument("--g5-copy", type=Path, required=True)
    lg.add_argument("--out", type=Path, default=None)
    lg.add_argument("--all86", action="store_true", help="D284: draws 2 and 3 on all 86 (default out L2_d135_d181_d284)")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "g4c":
            g4c(a.copy, a.s6, a.out, allow_sha_line=a.allow_s476_sha_line, faults_path=a.faults)
        elif a.cmd == "t1" and a.check:
            if a.out is not None:
                raise Refused("t1 --check writes nothing: no --out")
            t1_check(allow_sha_line=a.allow_s476_sha_line)
        elif a.cmd == "t1":
            t1(a.out, allow_sha_line=a.allow_s476_sha_line)
        elif a.cmd == "l2g7":
            l2g7(a.g5_copy, a.out or (OUT_L2D284 if a.all86 else OUT_L2G7), all86=a.all86)
    except (Refused, S476.Refused, JR.Refused, S474.Refused, S474.D181.Refused,
            S474.turn_limit_note.NoteMismatch) as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    except S474.GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
