#!/usr/bin/env python3
"""S474 - plan row L2: concept recall on the depth answers of G5 (Mentori's RLM) and G6 (the authors' RLM), per
answer, on D12's loose matcher, provisional; then a per-cap table for each, with paired differences between caps.

Why. Plan row L2 scores Figure 3a's depth answers for concept recall; exp_06 defines compute_concept_recall and never
calls it, so G5's records store none (plan.csv L2). D75 Q50: G6 answers the same 86 questions, so its depth answers
are scored here too. Valerio, 22 October: "do we have already fresh data that proves there is no gain to go beyond a
certain cap? like above 20?" The matcher is D12's loose one (scripts/concept_match_loose.py), provisional until P2's
labels choose one (D17), as for L3 (S471, D114 Q37 O-a); the exact value (its rule 1, the substring test) is written
beside it (D12). No judge reads these answers here.

The answers.
  G5   exp_06 at turn caps 1, 2, 3, 5, 7, 10, 15, 20, 30, 50 on depth_sweep86, gemini-3-flash-preview, draw 1 (D98):
       860 answers. Read from a read-only copy of the G5 clone's results files (--g5-copy: <dir>/results_v4/
       v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview*.json and <dir>/PULL.json, which records each file's
       sha256 on the Studio; every file must match it). The answers are the union of the files by answer key, as
       exp_06's resume and merge read them (G5_runs/README.md); one key with two different rows is refused. Each row
       must carry the answer key experiment.answer_key("rlm_<depth>", question, draw) and its rlm block's max_turns
       must equal its depth. The 860 keys of draw 1 must all be present.
  G6   the authors' package (rlms 0.1.3) at the same ten caps, three draws: findings/runs/b4_rlm_ref__cap<c>__
       depthsweep86 for caps 1, 2, 3, 7, 15, 30, 50 and __all135 for 5, 10, 20, of which the 86 questions of
       DEPTH_SWEEP86 are kept, as S459 selects them (experiments/rlm_ref/run_rlm_ref.py, read with ast): each
       question once per draw 1, 2, 3, every record's cap its file's. 2,580 answers.
  All 86 questions are answerable (Rule 8), so every answer is scored.

The value of an answer (as S471): the stored answer, with Mentori's fixed turn-limit note removed exactly when the
record flags it (G5: rlm.turn_limit_note; D115 L1e O-a, scripts/turn_limit_note.strip; a flagged answer that does not
end with the note stops the run, nothing written). The authors' package appends no such note, so a G6 answer is read
as stored (its flag is None; the number of G6 answers holding the note's words is counted). concept_recall_loose =
concept_recall_loose(text, the v2.4 key's expected_concepts); concept_recall_exact = the concepts it marks found_by
"exact" / the concepts, four decimals. A failed answer (G5: an error stored, call_error or max_turns_empty; G6: status
failed) is an outcome of the system under test (LIST.md Rule 10): it stays in every denominator, and its stored text
(empty in every case here) scores 0, as concept recall is defined on an empty text.

Turns. turns_used: G5 rlm.turns, G6 turns_used (root calls). cap_reached: turns_used >= the cap. stopped_by_cap: the
record's stop reason is one the cap causes (G5 max_turns_partial, max_turns_auto_generated, max_turns_empty; G6
turn_cap, forced_final_failed).

The tables (LIST.md Rules 1 to 3; descriptive). Per system and cap: answers, questions, the mean concept recall = the
mean over questions of each question's mean over its draws (Rule 1, Rule 2), its 95% interval = the 2.5th and 97.5th
percentiles (numpy linear) over 10,000 question resamples drawn once per system, numpy.random.default_rng(20261013).
integers(0, n, size=(10000, n)) over the n questions sorted (Rule 2: S407's method and seed convention), the per-draw
means beside it (Rule 2's draw-to-draw spread), the status counts, cap_reached and stopped_by_cap shares. Pairs: d =
the mean over questions of (question mean at the higher cap minus at the lower), with the same resamples (Rule 3's
effect and Rule 2's interval), for consecutive caps and for 30 and 50 against each of 7, 10, 15 and 20. No P value
is computed: these pairs are none of Rule 3's named comparisons, so the intervals are unadjusted and say so (Rule
12, last bullet). Rule 10's sensitivity: every table again with the failed answers left out (a question's mean over
its remaining draws; a question with none drops out of that cap and its pairs; resamples are the same matrix, the
mean taken over the drawn questions that have a value).

D92's pending changes to G6 (D92 Q187, D93 Q-a; findings/recompute/B4_runs/rerun_d89.sh, not yet run on 22 October).
S455's list (findings/recompute/Q145/S455_d92_affected.json, --d92) names 131 G6 answers with an action: rebuild (a
failed closing call whose stored reply becomes the answer), rerun (run again under D89 and D90) or stays_failed. Each
G6 row carries its d92_action (None when not listed) and each table counts them per cap, so a reader sees which zeros
and which answers will change. The values are not changed here: the stored answers are scored as they stand.

Gate (README.md:75-79), before anything is written: concept_match_loose.spec_failures() and
turn_limit_note.spec_failures() are empty; S383's CSV names the key this run uses (its sha256); then this script's own
score() on the deposited April depth sweep answers (deposit exp09_depth_sweep_*_merged.json) gives S383's stored v2.4
values on every row S383 rescored, 1,362 of 1,362: concept_recall_loose_v22 for the loose value and concept_recall_v22
(exp_06's compute_concept_recall, the exact substring fraction) for the exact one. The nine deposit files are read from
their frozen copy (D155), findings/recompute/upstream_inputs/publication/results/, through fig_repro.frozen("upstream")
and fig_repro.check_committed (each against frozen_inputs/SHA256SUMS); each must also have the sha256 its line in
data/upstream/MANIFEST.sha256 gives, and there must be exactly nine (GATE_FILES), or the gate fails. The gate record
names each by its deposit path (<upstream>/publication/results/<name>), whose bytes the frozen copy holds.

Outputs, under --outdir (default findings/recompute/L2/):
  concept_recall.jsonl   one row per answer, G5's 860 then G6's 2,580, each in (draw, question order, cap) order
  header.json            provenance: script, matcher and helper sha256s, the key, the inputs and their sha256s, the
                         gate, the counts, the command; "provisional": true. No write time and no git state (D155:
                         the same inputs give the same bytes); with --frozen, frozen_inputs_sha256 names every
                         input file read and its sha256
  cap_tables.json        the tables above, all failed answers in and left out
  cap_tables.md          the same, readable

FROZEN INPUTS (D155; findings/audits/scratch_repro_2026-10-26/INVENTORY.md F2, A4, A7). --frozen reads both systems
from the committed set findings/recompute/L2_inputs/ through scripts/fig_repro.frozen(): G5's draw-1 results file
(G5_DRAW1, sha256 52abab86, the bytes L2 was built from on 22 October) with its PULL.json, and G6's ten answers.jsonl
under g6/<run>/ as they stood before the D92 reruns of 24 October (each the sha256 L2/header.json recorded; the run
sinks in findings/runs/ were rewritten by those reruns and are no longer L2's input). Before anything is read, every
file must have the sha256 findings/recompute/frozen_inputs/SHA256SUMS lists and the one the committed
findings/recompute/L2/header.json recorded (frozen_inputs_sha256, or before it existed the G5 and G6 entries of
inputs); any difference exits 2 with nothing written.

THE ONE COMMAND that rebuilds findings/recompute/L2/ from the frozen inputs (S494 calls it):

    uv run --frozen python scripts/S474_l2_concept_recall.py --frozen

Other commands:

    uv run --frozen python scripts/S474_l2_concept_recall.py --g5-copy <the G5 copy>    (a new pull; G6 from --g6-runs)
    uv run --frozen python scripts/S474_l2_concept_recall.py --gate-only
    uv run --frozen python scripts/S474_l2_concept_recall.py pull --to <a new, empty folder>
    uv run --frozen python scripts/S474_l2_concept_recall.py pull --check <a pulled folder>   (offline: the laptop's checks)
    uv run --no-sync python scripts/check_S474.py                                       # checks and mutants

D181 (--d181; experiments/README.md:1301-1308). The final reading: S505's loose matcher with the question rule, Q-need,
reading (b), on key v2.5, through scripts/d181_concept_recall.py (its docstring gives the rule, the key's checks and
the gates). Without --d181 nothing above changes. With it:
  the inputs   --frozen (G5 draw 1 and G6 before the D135 reruns, as L2/) or --frozen-d135 (G5 draw 1 and G6 after
               the D135 reruns, findings/recompute/g6_d135_inputs, the reading Figure 3a draws through S476's
               L2_d135/; each G6 file checked against SHA256SUMS and against L2_d135/header.json's record), or
               --g5-copy with --held-ref. G5 is draw 1 only (G5_DRAWS, D98): G7's draws 2 and 3 are not read
  the key      key v2.5's concepts and question text (d181_concept_recall.the_key_v25: its question texts and
               answerable flags equal v2.4's); the gates read v2.4
  a row        concept_recall (the D181 value) with n_counted, found, concept_status, concept_removed; the base
               loose and exact values on the same v2.5 concepts beside it, named *_base; no concept_recall_loose
               column. An answer with no counted concept is refused (none on v2.5)
  the tables   as above on concept_recall; exact_mean is the base exact value's, base_loose_mean the base loose's
  the gates    G-A gate() (S383 1,362 of 1,362, v2.4); G-B score() of d181_concept_recall with an empty question
               gives S383's loose value on the same 1,362 rows; G-C S505's stored M4 (d181_concept_recall.gate_m4);
               G-D on this run's answers, the D181 score with an empty question on the v2.4 concepts equals the
               committed reading's concept_recall_loose on every answer (L2/ for --frozen, L2_d135/ for
               --frozen-d135, --held-ref otherwise). Any failure exits 1, nothing written
  the folder   default findings/recompute/L2_d181/ (--frozen) or L2_d135_d181/ (--frozen-d135); L2/ and L2_d135/
               are refused (S475 and S476 read them)
  the header   "provisional": false, "reading": "D181", the matcher, the v2.5 key, the v2.4 key the gates read, the
               helper's and S505's sha256s, the four gates' results, the inputs' sha256s, the counts

    uv run --frozen python scripts/S474_l2_concept_recall.py --d181 --frozen-d135     (Figure 3a's reading)
    uv run --frozen python scripts/S474_l2_concept_recall.py --d181 --frozen          (G6 before the D135 reruns)
    uv run --frozen python scripts/check_d181_L3_L2.py                                  # checks and mutants of --d181

PULL (INVENTORY.md A7; the scratch l2/pull_g5.sh of 22 October, ported; read only on the Studio). One subprocess,
`ssh -o ConnectTimeout=20 10.15.212.253 bash -s`, the remote script on stdin (never on a command line, never written on
the Studio, no port and no results file name in it). The remote script runs /usr/bin/python3 -, reads the G5 clone's
HEAD from its .git folder (no git call: the 23 October machine guards forbid one, INVENTORY.md A8) and writes one tar
stream to stdout holding draw 1's results file only (G5_GLOB, the file whose name ends with the draw-1 run's start
time G5_DRAW1_SUFFIX; the glob also matches _latest.json and, from 1 November, G7's draws 2 and 3, which are left
out) and PULL.json with its sha256, size and mtime taken there from the bytes sent. On the laptop, before anything is
kept: the stream holds exactly those two members, the file's sha256 equals PULL.json's and equals G5_DRAW1_SHA256
(reproduce first: the pull must give the bytes L2 was built from); otherwise the folder is emptied and the pull exits
2. The pulled folder is read with --g5-copy.
"""
from __future__ import annotations

import argparse
import ast
import collections
import csv
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import concept_match_loose  # noqa: E402
import fig_repro  # noqa: E402
import turn_limit_note  # noqa: E402
import S470_l1_signals as S470  # noqa: E402
class _LazyD181:
    """d181_concept_recall, imported on first use: it imports S505, whose import sets KMP_* variables in os.environ,
    which S494's read audit refuses in every git child process; a run without --d181 never imports it."""
    def __getattr__(self, name):
        import d181_concept_recall as m
        globals()["D181"] = m
        return getattr(m, name)


D181 = _LazyD181()  # (--d181 only)
from machine import RECOMPUTE, rel  # noqa: E402

SCRIPT = "scripts/S474_l2_concept_recall.py"
OUTDIR = RECOMPUTE / "L2"
RUNS = ROOT / "findings" / "runs"
RUN_RLM_REF = ROOT / "experiments" / "rlm_ref" / "run_rlm_ref.py"
S383_CSV = RECOMPUTE / "S383_depth_concept_recall_v22.csv"
D92_LIST = RECOMPUTE / "Q145" / "S455_d92_affected.json"
D92_ACTIONS = ("rebuild", "rerun", "stays_failed")
GATE_N = 1362
GATE_FILES = 9                                      # the deposit's exp09_depth_sweep_*_merged.json (D155: frozen)
UPSTREAM_MANIFEST = ROOT / "data" / "upstream" / "MANIFEST.sha256"
G5_GLOB = "v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview*.json"
G5_DRAWS = (1,)                                     # D98: G5's main estimate is draw 1 on every question
G6_DRAWS = (1, 2, 3)
SEED, N_BOOT, PCT = 20261013, 10000, (2.5, 97.5)    # LIST.md Rule 2: S407's convention (S407:190-191, :249)
CAP_STOPS = {"G5": ("max_turns_partial", "max_turns_auto_generated", "max_turns_empty"),
             "G6": ("turn_cap", "forced_final_failed")}
ABOVE = (7, 10, 15, 20)                             # the caps Valerio's question names, each against 30 and 50
NOTE_WORDS = "Analysis reached turn limit"
# D155: the frozen inputs (findings/recompute/L2_inputs/), the one command, and the G5 pull (INVENTORY.md A4, A7)
FROZEN_SET = "L2"
FROZEN_SUMS = RECOMPUTE / "frozen_inputs" / "SHA256SUMS"
FROZEN_COMMAND = "uv run --frozen python scripts/S474_l2_concept_recall.py --frozen"
G5_DRAW1_SUFFIX = "_20261018_095502.json"           # the draw-1 run's start time, G5's results file name
G5_DRAW1 = "v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview_127.0.0.1-11453" + G5_DRAW1_SUFFIX
G5_DRAW1_SHA256 = "52abab8629d54c78902479532b7e28fe0753ef58b66f0c839871961332850779"   # L2/header.json, 22 October
G5_CLONE = "projects/mentori-runs-g5"
G5_RESULTS = "experiments/mentori/publication/scripts/results_v4"
STUDIO = "10.15.212.253"
# --d181: folders of their own; L2/ (S475, S476's held check) and L2_d135/ (S476, Figure 3a) stay as they are
G6_D135_SET = "g6_d135"                             # S476_fig3_d123.py:1196, G6 after the D135 reruns
L2_D135 = RECOMPUTE / "L2_d135"
OUTDIR_D181 = RECOMPUTE / "L2_d181"
OUTDIR_D135_D181 = RECOMPUTE / "L2_d135_d181"
SSH = ["ssh", "-o", "ConnectTimeout=20", STUDIO, "bash", "-s"]        # the one form allowed on the Studio


class Refused(Exception):
    """A refusal before anything is written (exit 2)."""


class GateFail(Exception):
    """The gate did not reproduce (exit 1, nothing written)."""


def score(answer: str, concepts: list, flagged) -> dict:
    """One answer's concept recall on the loose matcher and the exact substring test, after the note's removal."""
    text, removed = turn_limit_note.strip(answer, flagged)
    loose, per = concept_match_loose.concept_recall_loose(text, concepts, detail=True)
    n_exact = sum(1 for x in per if x["found_by"] == "exact")
    return {"note_removed": removed, "scored_text_sha256": S470.sha256_text(text), "n_concepts": len(concepts),
            "found_loose": sum(1 for x in per if x["found_by"] is not None), "found_exact": n_exact,
            "concept_recall_loose": loose, "concept_recall_exact": round(n_exact / len(concepts), 4),
            "found_by": [x["found_by"] for x in per], "empty_text": not text.strip()}


# ---------------------------------------------------------------- the gate

def gate_files() -> list[Path]:
    """The deposit's April depth sweep files, from their frozen copy (D155): every file of upstream_inputs/publication/
    results/ checked against frozen_inputs/SHA256SUMS, the nine exp09_depth_sweep_*_merged.json each equal to its line
    in data/upstream/MANIFEST.sha256. Any difference, or another number of files, fails the gate."""
    try:
        res = fig_repro.check_committed(fig_repro.frozen("upstream", "publication/results"))
    except fig_repro.FrozenInputError as e:
        raise GateFail(f"frozen deposit records: {e}") from e
    files = sorted(res.glob("exp09_depth_sweep_*_merged.json"))
    man = {}
    for line in UPSTREAM_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            man[name.strip()] = h
    bad = [f.name for f in files if man.get(f"publication/results/{f.name}") != S470.sha256_file(f)]
    if len(files) != GATE_FILES or bad:
        raise GateFail(f"frozen deposit records: {len(files)} exp09_depth_sweep_*_merged.json (want {GATE_FILES}); "
                       f"not the sha256 {rel(UPSTREAM_MANIFEST)} gives: {bad[:3]}")
    return files


def gate(key: dict) -> dict:
    """The rule cases, then score() on the April depth sweep's answers against S383's v2.4 values."""
    fails = list(concept_match_loose.spec_failures()) + list(turn_limit_note.spec_failures())
    if fails:
        raise GateFail(f"rule cases fail: {fails[:3]}")
    lines = S383_CSV.read_text(encoding="utf-8").splitlines()
    head = " ".join(x for x in lines if x.startswith("#"))
    if f"sha256 {key['sha256']}" not in head:
        raise GateFail(f"{rel(S383_CSV)} does not name the key {key['sha256'][:12]} in its header")
    ref = list(csv.DictReader(x for x in lines if not x.startswith("#")))
    files = gate_files()
    dep, shas = {}, {}
    for f in files:
        shas[f"<upstream>/publication/results/{f.name}"] = S470.sha256_file(f)
        model = os.path.basename(f)[len("exp09_depth_sweep_"):-len("_merged.json")]
        doc = json.loads(Path(f).read_text(encoding="utf-8"))
        for r in doc.get("results") or doc.get("per_question_results") or []:
            dep.setdefault((model, int(r["depth"]), r["question_id"]), []).append(r)
    n, bad = 0, []
    for r in ref:
        if r["status"] != "rescored":
            continue
        n += 1
        recs = dep.get((r["model"], int(r["depth"]), r["question_id"])) or []
        if len(recs) != 1:
            bad.append(f"{r['model']} {r['depth']} {r['question_id']} ({len(recs)} records)")
            continue
        got = score(recs[0]["answer"], key["questions"][r["question_id"]]["expected_concepts"], None)
        if (got["concept_recall_loose"], got["concept_recall_exact"]) != \
                (float(r["concept_recall_loose_v22"]), float(r["concept_recall_v22"])):
            bad.append(f"{r['model']} {r['depth']} {r['question_id']}")
    if n != GATE_N or bad:
        raise GateFail(f"S383 reproduced on {n - len(bad)} of {n} rescored rows (want {GATE_N} of {GATE_N}); "
                       f"first differing {bad[:3]}")
    return {"reference": rel(S383_CSV), "reference_sha256": S470.sha256_file(S383_CSV), "answers": shas,
            "reproduced": f"{n} of {GATE_N}",
            "compared": "concept_recall_loose = concept_recall_loose_v22, concept_recall_exact = concept_recall_v22 "
                        "(exp_06's compute_concept_recall), on every row S383 rescored against the v2.4 key"}


def gate_d181(key24: dict) -> dict:
    """G-B and G-C (module docstring, D181), after gate() (G-A) passed: d181_concept_recall's rule cases; its score()
    with an empty question on the 1,362 rows S383 rescored gives S383's loose value on each; S505's M4 reproduced."""
    try:
        fails = D181.spec_failures()
        if fails:
            raise GateFail(f"D181 rule cases fail: {fails[:3]}")
        lines = S383_CSV.read_text(encoding="utf-8").splitlines()
        ref = list(csv.DictReader(x for x in lines if not x.startswith("#")))
        dep = {}
        for f in gate_files():
            model = os.path.basename(f)[len("exp09_depth_sweep_"):-len("_merged.json")]
            doc = json.loads(Path(f).read_text(encoding="utf-8"))
            for r in doc.get("results") or doc.get("per_question_results") or []:
                dep.setdefault((model, int(r["depth"]), r["question_id"]), []).append(r)
        count, differ = 0, []
        for r in ref:
            if r["status"] == "rescored":
                count += 1
                recs = dep.get((r["model"], int(r["depth"]), r["question_id"])) or []
                got = D181.score(recs[0]["answer"], key24["questions"][r["question_id"]]["expected_concepts"], "",
                                 None)["concept_recall"] if len(recs) == 1 else None
                if got != float(r["concept_recall_loose_v22"]):
                    differ.append(f"{r['model']} {r['depth']} {r['question_id']}")
        if count != GATE_N or differ:
            raise GateFail(f"G-B: the D181 score with an empty question gives S383's loose value on "
                           f"{count - len(differ)} of {count} rescored rows (want {GATE_N} of {GATE_N}); first "
                           f"differing {differ[:3]}")
        m4 = D181.gate_m4(key24)
    except D181.GateFail as e:
        raise GateFail(str(e)) from None
    return {"G-B": {"reference": rel(S383_CSV), "reproduced": f"{count} of {GATE_N}",
                    "compared": "d181_concept_recall.score(answer, v2.4 concepts, question '', None).concept_recall "
                                "= concept_recall_loose_v22"},
            "G-C": m4}


def held_d181(answers: list[dict], key24: dict, ref_path: Path) -> dict:
    """G-D: on this run's answers, the D181 score with an empty question on the v2.4 concepts equals the committed
    reading's concept_recall_loose on every answer (keyed by system and answer key), and the reading holds no other."""
    ref = {}
    for line in Path(ref_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            ref[(r["system"], r["answer_key"])] = r
    differ = [a["answer_key"] for a in answers
              if (a["system"], a["answer_key"]) not in ref or D181.score(
                  a["answer"], key24["questions"][a["question_id"]]["expected_concepts"], "",
                  a["turn_limit_note"])["concept_recall"] != ref[(a["system"], a["answer_key"])]["concept_recall_loose"]]
    if differ or len(ref) != len(answers):
        raise GateFail(f"G-D: the D181 score with an empty question reproduces {rel(ref_path)} on "
                       f"{len(answers) - len(differ)} of {len(answers)} answers ({len(ref)} rows there); first "
                       f"differing {differ[:3]}")
    return {"reference": rel(ref_path), "reference_sha256": S470.sha256_file(Path(ref_path)),
            "reproduced": f"{len(answers)} of {len(ref)}",
            "compared": "d181_concept_recall.score(answer, v2.4 concepts, question '', flag).concept_recall = the "
                        "reference row's concept_recall_loose, every answer"}


def frozen_inputs_d135() -> tuple[Path, Path, dict]:
    """(the G5 copy, G6 after the D135 reruns, {file: sha256}): G5 as frozen_inputs() gives it, G6 from the frozen
    set g6_d135 checked against SHA256SUMS; the whole set must be the one L2_d135/header.json recorded."""
    g5_copy, _, g5_shas = frozen_inputs()
    g6 = frozen_checked(G6_D135_SET)
    shas = {k: v for k, v in g5_shas.items() if "/g6/" not in k}
    shas.update({f.resolve().relative_to(ROOT).as_posix(): S470.sha256_file(f) for f in sorted(g6.glob("*/answers.jsonl"))})
    recorded = json.loads((L2_D135 / "header.json").read_text(encoding="utf-8")).get("frozen_inputs_sha256") or {}
    if recorded != shas:
        diff = sorted(k for k in set(recorded) | set(shas) if recorded.get(k) != shas.get(k))
        raise Refused(f"frozen inputs differ from those {rel(L2_D135 / 'header.json')} recorded: {diff[:3]}")
    return g5_copy, g6, shas


# ---------------------------------------------------------------- frozen inputs (D155)

def read_sums(path: Path = FROZEN_SUMS) -> dict:
    """{name: sha256} of frozen_inputs/SHA256SUMS: each committed frozen file by its repository path, each tar by its
    file name."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, name = line.split("  ", 1)
            out[name] = h
    return out


def frozen_checked(set_name: str, rel_path: str = ".") -> Path:
    """fig_repro.frozen(set_name, rel_path), and for a committed set every file under the path checked against its
    line in frozen_inputs/SHA256SUMS (fig_repro checks a tar and its extracted files itself). Refused: a file with no
    line or another sha256."""
    try:
        p = fig_repro.frozen(set_name, rel_path)
    except fig_repro.FrozenInputError as e:
        raise Refused(str(e)) from e
    base = RECOMPUTE / f"{set_name}_inputs"
    if base.resolve() == p.resolve() or base.resolve() in p.resolve().parents:
        sums = read_sums()
        for f in ([p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file())):
            k = f.resolve().relative_to(ROOT).as_posix()
            got = S470.sha256_file(f)
            if sums.get(k) != got:
                raise Refused(f"frozen input {k}: sha256 {got[:12]} is not the {str(sums.get(k))[:12]} "
                              f"{FROZEN_SUMS.relative_to(ROOT)} lists")
    return p


def frozen_inputs(committed_header: Path = OUTDIR / "header.json") -> tuple[Path, Path, dict]:
    """(the G5 copy, the G6 runs folder, {file: sha256}) of the frozen L2 inputs, each file checked against
    SHA256SUMS and against what the committed L2/header.json recorded; any difference is refused."""
    base = frozen_checked(FROZEN_SET)
    g5 = base
    g6 = base / "g6"
    files = [g5 / "PULL.json", g5 / "results_v4" / G5_DRAW1] + sorted(g6.glob("*/answers.jsonl"))
    shas = {f.resolve().relative_to(ROOT).as_posix(): S470.sha256_file(f) for f in files}
    if shas[f"findings/recompute/{FROZEN_SET}_inputs/results_v4/{G5_DRAW1}"] != G5_DRAW1_SHA256:
        raise Refused(f"frozen G5 draw-1 file is not {G5_DRAW1_SHA256[:8]}")
    if committed_header.exists():
        h = json.loads(committed_header.read_text(encoding="utf-8"))
        rec = h.get("frozen_inputs_sha256")
        if rec is not None:
            if rec != shas:
                diff = sorted(k for k in set(rec) | set(shas) if rec.get(k) != shas.get(k))
                raise Refused(f"frozen inputs differ from those {rel(committed_header)} recorded: {diff[:3]}")
        else:                                        # the header of 22 October: G5 by file name, G6 by run folder
            g5rec = (h.get("inputs") or {}).get("G5", {}).get("files", {})
            g6rec = {Path(k).parent.name: v["sha256"] for k, v in (h.get("inputs") or {}).get("G6", {}).items()}
            bad = [] if g5rec.get(G5_DRAW1) == G5_DRAW1_SHA256 else [G5_DRAW1]
            for f in files[2:]:
                if g6rec.get(f.parent.name) != shas[f.resolve().relative_to(ROOT).as_posix()]:
                    bad.append(f.parent.name)
            if bad or {f.parent.name for f in files[2:]} != set(g6rec):
                raise Refused(f"frozen inputs differ from those {rel(committed_header)} recorded: {bad[:3]}")
    return g5, g6, shas


PULL_SH = r"""set -e
cd ~/__CLONE__
/usr/bin/python3 - <<'PY'
import glob, hashlib, io, json, os, sys, tarfile, time
def head():
    # HEAD read from the .git folder: no git process (the machine guards of 23 October)
    h = open(".git/HEAD").read().strip()
    if not h.startswith("ref: "):
        return h
    ref = h[5:]
    if os.path.isfile(os.path.join(".git", ref)):
        return open(os.path.join(".git", ref)).read().strip()
    for line in open(".git/packed-refs"):
        if line.strip().endswith(" " + ref):
            return line.split()[0]
    raise SystemExit("HEAD not found")
d = "__RESULTS__"
fs = sorted(f for f in glob.glob(d + "/__GLOB__") if f.endswith("__SUFFIX__"))
if len(fs) != 1:
    raise SystemExit("draw 1's results file: %d found" % len(fs))
rec = {"from": "Studio ~/__CLONE__/" + d, "g5_clone_head": head(),
       "pulled_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": {}}
out = tarfile.open(fileobj=sys.stdout.buffer, mode="w|")
for f in fs:
    b = open(f, "rb").read()
    rec["files"][os.path.basename(f)] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
                                         "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(f)))}
    ti = tarfile.TarInfo("results_v4/" + os.path.basename(f)); ti.size = len(b); ti.mtime = int(os.path.getmtime(f))
    out.addfile(ti, io.BytesIO(b))
j = (json.dumps(rec, indent=1) + "\n").encode()
ti = tarfile.TarInfo("PULL.json"); ti.size = len(j); ti.mtime = int(time.time())
out.addfile(ti, io.BytesIO(j))
out.close()
PY
"""


def pull_script() -> str:
    txt = (PULL_SH.replace("__CLONE__", G5_CLONE).replace("__RESULTS__", G5_RESULTS).replace("__GLOB__", G5_GLOB)
           .replace("__SUFFIX__", G5_DRAW1_SUFFIX))
    import re
    if re.search(r"1145\d|11441", txt) or G5_DRAW1 in txt:
        raise Refused("the remote script would carry a Studio port or a results file name")
    return txt


def check_pull(to: Path) -> dict:
    """The laptop's checks on a pulled G5 folder (also run offline on the frozen copy): one draw-1 results file, its
    sha256 PULL.json's and G5_DRAW1_SHA256 (reproduce first)."""
    pull = json.loads((to / "PULL.json").read_text(encoding="utf-8"))
    have = sorted(p.name for p in (to / "results_v4").glob(G5_GLOB))
    if have != [G5_DRAW1]:
        raise Refused(f"pull: results_v4 holds {have}, not draw 1's {G5_DRAW1_SUFFIX} file alone")
    got = S470.sha256_file(to / "results_v4" / G5_DRAW1)
    want = (pull.get("files") or {}).get(G5_DRAW1, {}).get("sha256")
    if got != want:
        raise Refused(f"pull: {G5_DRAW1_SUFFIX} file sha256 {got[:12]} is not PULL.json's {str(want)[:12]}")
    if got != G5_DRAW1_SHA256:
        raise Refused(f"pull: draw 1's file is {got[:12]}, not {G5_DRAW1_SHA256[:8]} (the bytes L2 was built from): "
                      f"G5 draw 1 changed on the Studio")
    return {"file": G5_DRAW1, "sha256": got, "g5_clone_head": pull.get("g5_clone_head"),
            "pulled_utc": pull.get("pulled_utc")}


def pull(to: Path) -> int:
    """Read-only G5 pull, draw 1 only, kept only when it reproduces G5_DRAW1_SHA256."""
    import subprocess
    import tarfile
    to = to.expanduser().resolve()
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    to.mkdir(parents=True, exist_ok=True)
    script = pull_script()
    stream = to / ".stream.tar"
    try:
        with open(stream, "wb") as fh:
            r = subprocess.run(SSH, input=script.encode(), stdout=fh, stderr=subprocess.PIPE)
        if r.returncode:
            raise Refused(f"pull: ssh exit {r.returncode}: {r.stderr.decode(errors='replace').strip()[:300]}")
        with tarfile.open(stream, mode="r:") as tf:
            names = sorted(tf.getnames())
            if names != sorted(["PULL.json", f"results_v4/{G5_DRAW1}"]):
                raise Refused(f"pull: the stream holds {names[:4]}, not PULL.json and draw 1's file")
            tf.extractall(to, filter="data")
        stream.unlink()
        info = check_pull(to)
    except BaseException:
        shutil.rmtree(to, ignore_errors=True)
        raise
    print(f"pulled G5 draw 1 into {to}: {info['file']} sha256 {info['sha256'][:12]} = L2's input (reproduced); "
          f"clone {str(info['g5_clone_head'])[:7]}; read it with --g5-copy {to}")
    return 0


# ---------------------------------------------------------------- reading the answers

def design() -> tuple:
    """(the 86 ids in order, the ten caps, G6's Figure 2 caps, G6's experiment name) from run_rlm_ref.py, read with
    ast as S459 reads it."""
    want = {"DEPTH_SWEEP86", "FIGURE2_CAPS", "DEPTH_SWEEP_CAPS", "DEPTH_SWEEP_SIZE", "EXPERIMENT"}
    got = {}
    for node in ast.parse(RUN_RLM_REF.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in want:
            got[node.targets[0].id] = eval(compile(ast.Expression(node.value), str(RUN_RLM_REF), "eval"),
                                           {"__builtins__": {"range": range}}, {})
    if want - set(got):
        raise Refused(f"{rel(RUN_RLM_REF)}: {sorted(want - set(got))} not found as plain assignments")
    ids = tuple(got["DEPTH_SWEEP86"])
    if len(ids) != got["DEPTH_SWEEP_SIZE"] or len(set(ids)) != len(ids):
        raise Refused(f"DEPTH_SWEEP86 holds {len(ids)} ids, not {got['DEPTH_SWEEP_SIZE']} distinct")
    caps = tuple(sorted(set(got["FIGURE2_CAPS"]) | set(got["DEPTH_SWEEP_CAPS"])))
    return ids, caps, set(got["FIGURE2_CAPS"]), got["EXPERIMENT"]


def status_of(answer, error) -> str:
    """records.py's rule: error when an error is stored, no_answer when the text is empty, else ok."""
    if error:
        return "error"
    return "ok" if (answer or "").strip() else "no_answer"


def read_g5(copy: Path, ids, caps) -> tuple[list[dict], dict]:
    from experiments.runner import experiment as ex
    pull = json.loads((copy / "PULL.json").read_text(encoding="utf-8"))
    files = sorted((copy / "results_v4").glob(G5_GLOB))
    files = [f for f in files if not f.name.endswith("_merged.json")]
    if not files:
        raise Refused(f"no G5 results file in {copy / 'results_v4'}")
    info = {"copy": str(copy), "pull": pull, "files": {}}
    rows = {}
    for f in files:
        sha = S470.sha256_file(f)
        want = (pull.get("files") or {}).get(f.name, {}).get("sha256")
        if sha != want:
            raise Refused(f"{f.name}: sha256 {sha[:12]} is not the one PULL.json records ({str(want)[:12]})")
        info["files"][f.name] = sha
        for r in json.loads(f.read_text(encoding="utf-8")).get("results", []):
            k = r.get("answer_key")
            if k is None:
                raise Refused(f"{f.name}: a row without an answer_key")
            if k in rows and rows[k][0] != r:
                raise Refused(f"{k}: two different rows ({rows[k][1]} and {f.name})")
            rows.setdefault(k, (r, f.name))
    expected = {ex.answer_key(f"rlm_{c}", q, d): (c, q, d) for d in G5_DRAWS for q in ids for c in caps}
    missing = [k for k in expected if k not in rows]
    if missing:
        raise Refused(f"G5: {len(missing)} of the {len(expected)} draw-1 answers missing, first {missing[:3]}")
    out = []
    for k, (c, q, d) in expected.items():
        r, fname = rows[k]
        rlm = r.get("rlm") or {}
        if (r.get("question_id"), r.get("depth"), r.get("draw")) != (q, c, d) or rlm.get("max_turns") != c:
            raise Refused(f"{k}: its row says question {r.get('question_id')}, depth {r.get('depth')}, draw "
                          f"{r.get('draw')}, max_turns {rlm.get('max_turns')}")
        ans = r.get("answer") or ""
        turns = rlm.get("turns")
        out.append({"system": "G5", "answer_key": k, "run_id": r.get("run_id"), "question_id": q, "draw": d,
                    "cap": c, "answer": ans, "error": r.get("error"), "status": status_of(ans, r.get("error")),
                    "stop_reason": r.get("stop_reason"), "turns_used": turns,
                    "turn_limit_note": rlm.get("turn_limit_note"), "source": f"{fname} {k}"})
    info["rows_in_files"] = len(rows)
    info["rows_outside_draw_1"] = sum(1 for k in rows if k not in expected)
    return out, info


def read_g6(runs: Path, ids, caps, fig2_caps, experiment) -> tuple[list[dict], dict]:
    want = set(ids)
    info, out = {}, []
    for c in caps:
        path = runs / f"{experiment}__cap{c}__{'all135' if c in fig2_caps else 'depthsweep86'}" / "answers.jsonl"
        recs = [(n, json.loads(x)) for n, x in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                if x.strip()]
        keys = collections.Counter(r["answer_key"] for _, r in recs)
        if any(v > 1 for v in keys.values()):
            raise Refused(f"{rel(path)}: an answer key stored twice")
        sel = [(n, r) for n, r in recs if r["question_id"] in want]
        got = collections.Counter((r["question_id"], r["draw"]) for _, r in sel)
        if set(got) != {(q, d) for q in ids for d in G6_DRAWS} or any(v != 1 for v in got.values()):
            raise Refused(f"cap {c}: the records do not hold each of the {len(ids)} questions once per draw 1, 2, 3")
        if c not in fig2_caps and len(sel) != len(recs):
            raise Refused(f"cap {c}: {len(recs) - len(sel)} records outside DEPTH_SWEEP86")
        if any(r["cap"] != c for _, r in sel):
            raise Refused(f"cap {c}: a record of another cap in {rel(path)}")
        info[rel(path)] = {"sha256": S470.sha256_file(path), "records": len(recs), "kept": len(sel)}
        for n, r in sel:
            ans = r.get("answer") or ""
            err = r.get("error") or (None if r.get("status") == "ok"
                                     else f"status {r.get('status')} ({r.get('stop_reason')})")
            out.append({"system": "G6", "answer_key": r["answer_key"], "run_id": r.get("run_id"),
                        "question_id": r["question_id"], "draw": r["draw"], "cap": c, "answer": ans, "error": err,
                        "status": status_of(ans, err), "stop_reason": r.get("stop_reason"),
                        "turns_used": r.get("turns_used"), "turn_limit_note": None, "source": f"{rel(path)}:{n}"})
    pos = {q: i for i, q in enumerate(ids)}
    out.sort(key=lambda a: (a["draw"], pos[a["question_id"]], a["cap"]))
    return out, info


def read_d92(path: Path) -> tuple[dict, dict]:
    """{(cap, question, draw): action} for S455's G6 rows (runs b4_rlm_ref__cap<c>__...), and the file's provenance."""
    import re
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for r in doc.get("rows") or []:
        m = re.match(r"b4_rlm_ref__cap(\d+)__", str(r.get("run")))
        if not m:
            continue
        if r.get("action") not in D92_ACTIONS:
            raise Refused(f"{rel(path)}: {r.get('answer_key')} has action {r.get('action')!r}")
        k = (int(m.group(1)), r["item"], int(r["draw"]))
        if k in out and out[k] != r["action"]:
            raise Refused(f"{rel(path)}: {k} listed with two actions")
        out[k] = r["action"]
    return out, {"path": rel(path), "sha256": S470.sha256_file(path), "g6_keys": len(out),
                 "by_action": dict(collections.Counter(out.values()))}


def rows_for(answers: list[dict], key: dict, d92: dict, d181: bool = False) -> list[dict]:
    """One row per answer. d181: the value is d181_concept_recall.score() with the key's question text."""
    out = []
    for a in answers:
        row = {k: a[k] for k in ("system", "answer_key", "run_id", "question_id", "draw", "cap", "status",
                                 "stop_reason", "turns_used", "turn_limit_note", "source")}
        row["group"] = "answerable"
        row["answer_sha256"] = S470.sha256_text(a["answer"])
        row["cap_reached"] = a["turns_used"] is not None and a["turns_used"] >= a["cap"]
        row["stopped_by_cap"] = a["stop_reason"] in CAP_STOPS[a["system"]]
        row["failed"] = a["status"] == "error"
        row["d92_action"] = d92.get((a["cap"], a["question_id"], a["draw"])) if a["system"] == "G6" else None
        q = key["questions"][a["question_id"]]
        row.update(D181.score(a["answer"], q["expected_concepts"], q["question"], a["turn_limit_note"]) if d181
                   else score(a["answer"], q["expected_concepts"], a["turn_limit_note"]))
        out.append(row)
    return out


def counts(rows: list[dict], answers: list[dict]) -> dict:
    by_key = {(a["system"], a["answer_key"]): a for a in answers}
    c = {}
    for s in ("G5", "G6"):
        R = [r for r in rows if r["system"] == s]
        c[s] = {"rows": len(R), "status": dict(collections.Counter(r["status"] for r in R)),
                "stop_reason": dict(collections.Counter(str(r["stop_reason"]) for r in R)),
                "flagged": sum(r["turn_limit_note"] is True for r in R),
                "note_removed": sum(r["note_removed"] for r in R),
                "note_removed_by_cap": dict(collections.Counter(str(r["cap"]) for r in R if r["note_removed"])),
                "unflagged_holding_note_text": sum(r["turn_limit_note"] is not True
                                                   and NOTE_WORDS in by_key[(s, r["answer_key"])]["answer"]
                                                   for r in R),
                "empty_text_scored": sum(r["empty_text"] for r in R),
                "failed_with_text": sum(r["failed"] and not r["empty_text"] for r in R),
                "d92_action_by_failed": {x: [sum(r["d92_action"] == x and r["failed"] for r in R),
                                             sum(r["d92_action"] == x and not r["failed"] for r in R)]
                                         for x in D92_ACTIONS}}
    return c


# ---------------------------------------------------------------- the tables (Rules 1 to 3)

def resamples(n: int) -> np.ndarray:
    return np.random.default_rng(SEED).integers(0, n, size=(N_BOOT, n))


def per_question(rows: list[dict], cap: int, qorder: list, drop_failed: bool,
                 field: str = "concept_recall_loose") -> np.ndarray:
    """Each question's mean concept recall (field, loose by default) over its draws at the cap; NaN where no draw is
    left."""
    vals = collections.defaultdict(list)
    for r in rows:
        if r["cap"] == cap and not (drop_failed and r["failed"]):
            vals[r["question_id"]].append(r[field])
    return np.array([np.mean(vals[q]) if vals[q] else np.nan for q in qorder])


def boot(vec: np.ndarray, res: np.ndarray) -> dict:
    """The mean over the questions that have a value, and its percentile interval over the question resamples."""
    have = ~np.isnan(vec)
    drawn = have[res]
    sums = np.where(drawn, np.nan_to_num(vec)[res], 0.0).sum(axis=1)
    cnt = drawn.sum(axis=1)
    keep = cnt > 0
    means = sums[keep] / cnt[keep]
    lo, hi = np.percentile(means, PCT)
    return {"questions": int(have.sum()), "mean": round(float(np.nanmean(vec)), 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)], "resamples_left_out": int((~keep).sum())}


def pairs(caps) -> list[tuple[int, int]]:
    out = [(caps[i], caps[i + 1]) for i in range(len(caps) - 1)]
    for lo in ABOVE:
        for hi in (30, 50):
            if lo in caps and hi in caps and (lo, hi) not in out:
                out.append((lo, hi))
    return out


def tables(rows: list[dict], caps, ids, d181: bool = False) -> dict:
    """The per-cap tables on concept_recall_loose; d181: on concept_recall, the exact and base loose means beside."""
    field, exact = ("concept_recall", "concept_recall_exact_base") if d181 else \
        ("concept_recall_loose", "concept_recall_exact")
    qorder = sorted(ids)                                   # S407: the block's questions, sorted
    res = resamples(len(qorder))
    out = {"method": {"seed": SEED, "n_boot": N_BOOT, "percentiles": list(PCT), "questions": len(qorder),
                      "unit": "the question (Rule 1): each question's mean over its draws at a cap",
                      "pairs": "d = mean over questions of (higher cap minus lower cap); no P value (not a Rule 3 "
                               "comparison; unadjusted, Rule 12)"}}
    for s in ("G5", "G6"):
        R = [r for r in rows if r["system"] == s]
        draws = sorted({r["draw"] for r in R})
        for mode, drop in (("all", False), ("failed_left_out", True)):
            per_cap = {}
            vec = {c: per_question(R, c, qorder, drop, field) for c in caps}
            for c in caps:
                C = [r for r in R if r["cap"] == c]
                kept = [r for r in C if not (drop and r["failed"])]
                b = boot(vec[c], res)
                per_cap[str(c)] = {
                    "answers": len(kept), **b,
                    "per_draw_mean": {str(d): round(float(np.mean([r[field] for r in kept if r["draw"] == d])), 4)
                                      for d in draws if any(r["draw"] == d for r in kept)},
                    "exact_mean": round(float(np.nanmean(per_question(R, c, qorder, drop, exact))), 4),
                    "failed": sum(r["failed"] for r in C), "status": dict(collections.Counter(r["status"] for r in C)),
                    "cap_reached_share": round(sum(r["cap_reached"] for r in C) / len(C), 4),
                    "stopped_by_cap_share": round(sum(r["stopped_by_cap"] for r in C) / len(C), 4),
                    "note_removed": sum(r["note_removed"] for r in C),
                    "d92": {x: {"failed": sum(r.get("d92_action") == x and r["failed"] for r in C),
                                "not_failed": sum(r.get("d92_action") == x and not r["failed"] for r in C)}
                            for x in D92_ACTIONS}}
                if d181:
                    per_cap[str(c)]["base_loose_mean"] = round(float(np.nanmean(per_question(
                        R, c, qorder, drop, "concept_recall_loose_base"))), 4)
            pr = {}
            for lo, hi in pairs(caps):
                diff = vec[hi] - vec[lo]
                b = boot(diff, res)
                pr[f"{hi} - {lo}"] = {"questions": b["questions"], "d": b["mean"], "ci95": b["ci95"],
                                      "ci_includes_0": b["ci95"][0] <= 0 <= b["ci95"][1],
                                      "resamples_left_out": b["resamples_left_out"],
                                      "questions_higher_lower_equal": [int(np.nansum(diff > 0)),
                                                                       int(np.nansum(diff < 0)),
                                                                       int(np.nansum(diff == 0))]}
            out.setdefault(s, {})[mode] = {"draws": draws, "per_cap": per_cap, "pairs": pr}
    return out


def pct(x) -> str:
    return f"{100 * x:.1f}"


def tables_md(t: dict, caps, d181: bool = False) -> str:
    title = ("# L2: concept recall (D181: loose with the question rule, Q-need (b), S505; key v2.5) per turn cap, G5 "
             "and G6; the exact mean is D12's exact rule on the same concepts" if d181 else
             "# L2: concept recall (loose, D12; provisional) per turn cap, G5 and G6")
    md = [title, "",
          "Per question first (mean over its draws), then the mean over the 86 questions (LIST.md Rules 1, 2). "
          "Interval: 95% percentile over 10,000 question resamples (seed 20261013, S407's convention). d: the mean "
          "over questions of (higher cap minus lower cap), percentage points, same resamples. Descriptive: no P "
          "value, intervals unadjusted (Rule 12). No judge.", ""]
    for s, name in (("G5", "G5, Mentori's RLM, gemini-3-flash-preview, draw 1 (D98)"),
                    ("G6", "G6, the authors' RLM (rlms 0.1.3), gemini-3-flash-preview, draws 1 to 3")):
        for mode, label in (("all", "every answer (failed answers score 0, Rule 10)"),
                            ("failed_left_out", "failed answers left out (Rule 10 sensitivity)")):
            b = t[s][mode]
            md += [f"## {name}: {label}", "",
                   "| cap | answers | questions | mean % | 95% interval | per-draw means | exact mean % | failed | "
                   "cap reached % | stopped by cap % |", "|---|---|---|---|---|---|---|---|---|---|"]
            for c in caps:
                r = b["per_cap"][str(c)]
                md.append(f"| {c} | {r['answers']} | {r['questions']} | {pct(r['mean'])} | {pct(r['ci95'][0])} to "
                          f"{pct(r['ci95'][1])} | {', '.join(pct(v) for v in r['per_draw_mean'].values())} | "
                          f"{pct(r['exact_mean'])} | {r['failed']} | {pct(r['cap_reached_share'])} | "
                          f"{pct(r['stopped_by_cap_share'])} |")
            md += ["", "| pair | questions | d (pp) | 95% interval (pp) | questions higher, lower, equal |",
                   "|---|---|---|---|---|"]
            for k, r in b["pairs"].items():
                md.append(f"| {k} | {r['questions']} | {100 * r['d']:+.1f} | {100 * r['ci95'][0]:+.1f} to "
                          f"{100 * r['ci95'][1]:+.1f} | {', '.join(map(str, r['questions_higher_lower_equal']))} |")
            md.append("")
        if s == "G6":
            md += ["## G6: answers D92 changes (rebuild, rerun) or keeps failed, per cap", "",
                   "S455's list (D92 Q187, D93 Q-a), not yet applied: the tables above score the stored answers. A "
                   "rebuilt answer becomes the text of its failed closing call; a rerun answer is run again.", "",
                   "| cap | failed | of which rebuild | rerun | stays failed | answers not failed, rerun |",
                   "|---|---|---|---|---|---|"]
            for c in caps:
                r = t[s]["all"]["per_cap"][str(c)]
                md.append(f"| {c} | {r['failed']} | {r['d92']['rebuild']['failed']} | {r['d92']['rerun']['failed']} | "
                          f"{r['d92']['stays_failed']['failed']} | {r['d92']['rerun']['not_failed']} |")
            md.append("")
    return "\n".join(md) + "\n"


# ---------------------------------------------------------------- writing

def write(outdir: Path, files: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        tmp = outdir / f".{name}.tmp"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, outdir / name)


def main_pull(argv) -> int:
    ap = argparse.ArgumentParser(prog="S474 pull", description="G5 draw 1, read only on the Studio (INVENTORY.md A7)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--to", type=Path, help="a new, empty folder")
    g.add_argument("--check", type=Path, help="run the laptop's checks only on a pulled (or the frozen) folder")
    a = ap.parse_args(argv)
    try:
        if a.check is not None:
            info = check_pull(a.check.expanduser().resolve())
            print(f"pull checks PASS on {a.check}: {info['file']} sha256 {info['sha256'][:12]} (= G5_DRAW1_SHA256)")
            return 0
        return pull(a.to)
    except Refused as e:
        print(f"REFUSED, nothing kept: {e}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["pull"]:
        return main_pull(args[1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--frozen", action="store_true",
                    help="read G5 and G6 from the frozen findings/recompute/L2_inputs (D155): the one command")
    ap.add_argument("--g5-copy", type=Path, help="a read-only copy of G5's results files with PULL.json")
    ap.add_argument("--g6-runs", type=Path, default=RUNS, help="the folder holding G6's run sinks")
    ap.add_argument("--outdir", type=Path, default=None,
                    help="default findings/recompute/L2/ (with --d181: L2_d181/, or L2_d135_d181/ with --frozen-d135)")
    ap.add_argument("--d92", type=Path, default=D92_LIST, help="S455's list of G6 answers D92 rebuilds or reruns")
    ap.add_argument("--gate-only", action="store_true", help="run the gate and stop")
    ap.add_argument("--d181", action="store_true",
                    help="D181's final reading: S505's loose Q-need (b) on key v2.5 (module docstring, D181)")
    ap.add_argument("--frozen-d135", action="store_true",
                    help="with --d181: G5 draw 1 frozen and G6 after the D135 reruns (Figure 3a's reading)")
    ap.add_argument("--held-ref", type=Path, default=None,
                    help="--d181 G-D: the committed rows of the same answers (default L2/ or L2_d135/)")
    a = ap.parse_args(argv)
    try:
        if (a.frozen_d135 or a.held_ref is not None) and not a.d181:
            raise Refused("--frozen-d135 and --held-ref belong to --d181")
        key = S470.the_key()
        g = gate(key)
        print(f"gate: S383 reproduced on {g['reproduced']} rescored April depth answers (loose and exact, v2.4 key); "
              f"rule cases of the loose matcher and the note's removal hold")
        if a.d181:
            return main_d181(a, args, key, g)
        if a.outdir is None:
            a.outdir = OUTDIR
        if a.gate_only:
            return 0
        frozen_shas = None
        if a.frozen:
            if a.g5_copy is not None or a.g6_runs != RUNS:
                raise Refused("--frozen reads G5 and G6 from findings/recompute/L2_inputs: no --g5-copy or --g6-runs")
            g5_copy, g6_runs, frozen_shas = frozen_inputs()
        elif a.g5_copy is None:
            raise Refused("--frozen or --g5-copy is required unless --gate-only")
        else:
            g5_copy, g6_runs = a.g5_copy.expanduser(), a.g6_runs.expanduser()
        ids, caps, fig2_caps, experiment = design()
        g5, g5_info = read_g5(g5_copy, ids, caps)
        if a.frozen:
            if sorted(g5_info["files"]) != [G5_DRAW1]:
                raise Refused(f"frozen G5: read {sorted(g5_info['files'])}, not draw 1's file alone")
            g5_info["copy"] = rel(g5_copy)
        g6, g6_info = read_g6(g6_runs, ids, caps, fig2_caps, experiment)
        d92, d92_info = read_d92(a.d92.expanduser())
        answers = g5 + g6
        groups = collections.Counter(group_of(q) for q in ids)
        if set(groups) != {"answerable"}:
            raise Refused(f"the 86 questions are not all answerable: {dict(groups)}")
        rows = rows_for(answers, key, d92)
        c = counts(rows, answers)
        t = tables(rows, caps, ids)
        header = {"script": SCRIPT, "script_sha256": S470.sha256_file(Path(__file__)),
                  "command": FROZEN_COMMAND if a.frozen else "uv run --frozen python " + " ".join([SCRIPT] + args),
                  "frozen_inputs_sha256": frozen_shas, "plan_row": "L2", "provisional": True,
                  "matcher": "loose (D12, scripts/concept_match_loose.py), provisional until P2's labels choose one "
                             "(D17); exact = its rule 1, the substring test, beside it (D12)",
                  "turn_limit_note": "removed exactly before matching where G5's rlm.turn_limit_note is True (D115 "
                                     "L1e O-a, scripts/turn_limit_note.py); G6's package appends no note",
                  "failed_answers": "LIST.md Rule 10: in every denominator, the stored (empty) text scored 0; "
                                    "cap_tables also gives every table with them left out",
                  "code_sha256": {"scripts/concept_match_loose.py": S470.sha256_file(SCRIPTS / "concept_match_loose.py"),
                                  "scripts/turn_limit_note.py": S470.sha256_file(SCRIPTS / "turn_limit_note.py"),
                                  "scripts/S470_l1_signals.py": S470.sha256_file(SCRIPTS / "S470_l1_signals.py"),
                                  "experiments/rlm_ref/run_rlm_ref.py": S470.sha256_file(RUN_RLM_REF),
                                  "concept_recall_loose (source)":
                                      S470.source_sha(concept_match_loose.concept_recall_loose),
                                  "turn_limit_note.strip (source)": S470.source_sha(turn_limit_note.strip)},
                  "key": {"path": key["path"], "sha256": key["sha256"], "version": key["version"],
                          "source": key["source"]},
                  "inputs": {"G5": g5_info, "G6": g6_info, "D92_list": d92_info},
                  "d92_pending": "G6 rows carry d92_action from S455's list (D92 Q187, D93 Q-a); not applied: the "
                                 "stored answers are scored as they stand", "caps": list(caps), "questions": len(ids),
                  "gate": g, "counts": c}
        write(a.outdir, {"concept_recall.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                         "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n",
                         "cap_tables.json": json.dumps(t, indent=1, sort_keys=True) + "\n",
                         "cap_tables.md": tables_md(t, caps)})
        for s in ("G5", "G6"):
            print(f"{s}: {c[s]['rows']} rows, status {c[s]['status']}; turn-limit note flagged {c[s]['flagged']}, "
                  f"removed {c[s]['note_removed']}; unflagged answers holding its words "
                  f"{c[s]['unflagged_holding_note_text']}; empty texts scored {c[s]['empty_text_scored']}")
        print(f"wrote {rel(a.outdir / 'concept_recall.jsonl')}, header.json, cap_tables.json and cap_tables.md "
              f"(provisional)")
        return 0
    except (Refused, S470.Refused, turn_limit_note.NoteMismatch) as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    except GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 1
    except D181.Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2


def main_d181(a, args: list, key24: dict, g: dict) -> int:
    """--d181 (module docstring, D181): the gates G-B, G-C and G-D, then the rows and tables on key v2.5, into a
    folder of their own. Exceptions are main()'s."""
    if sum([a.frozen, a.frozen_d135, a.g5_copy is not None]) != 1:
        raise Refused("--d181 reads one of --frozen, --frozen-d135 or --g5-copy")
    if a.g5_copy is not None and a.held_ref is None:
        raise Refused("--d181 --g5-copy needs --held-ref: G-D reproduces a committed reading of the same answers")
    if (a.frozen or a.frozen_d135) and a.g6_runs != RUNS:
        raise Refused("--frozen and --frozen-d135 read G6 from their frozen set: no --g6-runs")
    outdir = (a.outdir or (OUTDIR_D135_D181 if a.frozen_d135 else OUTDIR_D181)).expanduser()
    if outdir.resolve() in (OUTDIR.resolve(), L2_D135.resolve()):
        raise Refused(f"--d181 does not write {rel(outdir)}: S475 and S476 read it as the provisional reading")
    held_ref = a.held_ref or ((L2_D135 if a.frozen_d135 else OUTDIR) / "concept_recall.jsonl")
    try:
        key25 = D181.the_key_v25(key24)
    except D181.Refused as e:
        raise Refused(str(e)) from None
    gd = gate_d181(key24)
    print(f"D181 gates: G-B S383 reproduced on {gd['G-B']['reproduced']} with an empty question; G-C S505's M4 "
          f"{D181.M4_COLUMN} reproduced, all {gd['G-C']['reproduced']['all']}")
    if a.gate_only:
        return 0
    frozen_shas = None
    if a.frozen:
        g5_copy, g6_runs, frozen_shas = frozen_inputs()
    elif a.frozen_d135:
        g5_copy, g6_runs, frozen_shas = frozen_inputs_d135()
    else:
        g5_copy, g6_runs = a.g5_copy.expanduser(), a.g6_runs.expanduser()
    ids, caps, fig2_caps, experiment = design()
    g5, g5_info = read_g5(g5_copy, ids, caps)
    if a.frozen or a.frozen_d135:
        if sorted(g5_info["files"]) != [G5_DRAW1]:
            raise Refused(f"frozen G5: read {sorted(g5_info['files'])}, not draw 1's file alone")
        g5_info["copy"] = rel(g5_copy)
    g6, g6_info = read_g6(g6_runs, ids, caps, fig2_caps, experiment)
    d92, d92_info = read_d92(a.d92.expanduser())
    answers = g5 + g6
    groups = collections.Counter(group_of(q) for q in ids)
    if set(groups) != {"answerable"} or not all(key25["questions"][q].get("answerable") for q in ids):
        raise Refused(f"the 86 questions are not all answerable: {dict(groups)}")
    held = held_d181(answers, key24, held_ref.expanduser())
    print(f"D181 gate G-D: {held['reference']} reproduced on {held['reproduced']} answers")
    rows = rows_for(answers, key25, d92, d181=True)
    none = [r["answer_key"] for r in rows if r["concept_recall"] is None]
    if none:
        raise Refused(f"{len(none)} answers have no counted concept under D181 (b), first {none[:3]}: this run does "
                      f"not decide their value")
    c = counts(rows, answers)
    for s in ("G5", "G6"):
        c[s]["d181"] = D181.concept_counts([r for r in rows if r["system"] == s])
    t = tables(rows, caps, ids, d181=True)
    header = {"script": SCRIPT, "script_sha256": S470.sha256_file(Path(__file__)),
              "command": "uv run --frozen python " + " ".join([SCRIPT] + args),
              "frozen_inputs_sha256": frozen_shas, "plan_row": "L2", "provisional": False, "reading": "D181",
              "matcher": D181.MATCHER_TEXT, "columns": D181.COLUMNS_TEXT,
              "g6": ("after the D135 reruns (frozen set g6_d135, Figure 3a's reading)" if a.frozen_d135 else
                     "before the D135 reruns (frozen set L2, L2/'s reading)" if a.frozen else rel(g6_runs)),
              "g5_draws": list(G5_DRAWS),
              "turn_limit_note": "removed exactly before matching where G5's rlm.turn_limit_note is True (D115 "
                                 "L1e O-a, scripts/turn_limit_note.py); G6's package appends no note",
              "failed_answers": "LIST.md Rule 10: in every denominator, the stored (empty) text scored 0; "
                                "cap_tables also gives every table with them left out",
              "code_sha256": {**D181.code_sha256(),
                              "scripts/S470_l1_signals.py": S470.sha256_file(SCRIPTS / "S470_l1_signals.py"),
                              "experiments/rlm_ref/run_rlm_ref.py": S470.sha256_file(RUN_RLM_REF)},
              "key": {"path": key25["path"], "sha256": key25["sha256"], "version": key25["version"],
                      "source": key25["source"]},
              "gate_key": {"path": key24["path"], "sha256": key24["sha256"], "version": key24["version"],
                           "read_for": "the gates G-A to G-D"},
              "inputs": {"G5": g5_info, "G6": g6_info, "D92_list": d92_info},
              "d92_pending": "G6 rows carry d92_action from S455's list (D92 Q187, D93 Q-a); with --frozen-d135 the "
                             "stored answers are those after the D135 reruns", "caps": list(caps),
              "questions": len(ids), "gate": {"G-A": g, **gd, "G-D": held}, "counts": c}
    write(outdir, {"concept_recall.jsonl": "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                   "header.json": json.dumps(header, indent=1, sort_keys=True) + "\n",
                   "cap_tables.json": json.dumps(t, indent=1, sort_keys=True) + "\n",
                   "cap_tables.md": tables_md(t, caps, d181=True)})
    for s in ("G5", "G6"):
        print(f"{s}: {c[s]['rows']} rows, status {c[s]['status']}; answer-concept pairs by status "
              f"{c[s]['d181']['pairs_by_status']}, of which the concept loses a word to the question "
              f"{c[s]['d181']['pairs_with_a_removed_word']}")
    print(f"wrote {rel(outdir / 'concept_recall.jsonl')}, header.json, cap_tables.json and cap_tables.md (D181)")
    return 0


def group_of(qid: str) -> str:
    """Rule 8's group of a question, from the runner's D5 key (records.group_of)."""
    from experiments.scorers import records
    return records.group_of(qid)


if __name__ == "__main__":
    raise SystemExit(main())
