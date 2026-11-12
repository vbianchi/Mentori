#!/usr/bin/env python3
"""S457 - the judge-free generation-strategy plate (outcomes, tokens, time, turns) from the G1, G2 and G6 records.

WHY. D82 (experiments/README.md): every panel is drawn as soon as its data exist, by a committed script from the raw
records, stamped with how much data it holds, and the final panel is the same script run again. D84: the exploratory
phase draws the results as they are, under no new analysis rule. The plate compares Mentori's six generation
strategies (G1: single pass, multi-hop, verified pass, RLM-5, RLM-10, RLM-20; 135 questions x draws 1, 2, 3 each),
the matched-budget arm (G2: single pass given as many passages as RLM-10's input tokens, the same 135 x 3) and the
authors' RLM package at caps 5, 10 and 20 (G6, the same 135 x 3). It draws what the generation records hold, with no
judge score: each answer's outcome (Rule 10), tokens and time per answer (Q117, D78), the verifier's status (Rule 4,
Q78) and the RLM turns. Modelled on S447 (Figure 6).
D95 Q200 (18 October): this plate is a provisional Supplementary draft, and main Figure 3 (Figure 2 at D95) is S463's
plate (scripts/S463_fig2_ranking.py, folder fig3_strategies/), which draws with this script's plate_rc() and
finish_plate().
D95 Q208: every panel is kept drawable as main or Supplementary and the story decides which, so the plate's name is a
parameter (--as, --n); drawn as a main figure, S448's automatic rules pass, but its main-figure mutants are not all
proven on this plate (experiments/FIGURE_RULES.md, Supplementary figures). D95 Q201: panel e (turns used) is to move
beside Supplementary Figure 8; it is kept here, marked so in the legend, until that panel is drawn there with one definition of a
turn for both RLMs.

ONE COMMAND (D155), from the repository root: the committed Supplementary Figure 17, rebuilt from frozen inputs only:

  uv run --frozen python scripts/S457_fig2_panels.py rebuild [--out <dir>]

It writes every file of findings/figures_provisional/supp_fig17_outcomes/ (or of --out) byte-equal to the committed one (26
October: PDF, SVG, PNG, data workbook, caption, legend, numbers and provenance; run twice, the same bytes; claims.md is
--claims-out's since D2;
records_manifest.json is an input and is not written). It reads no Studio and no findings/runs/: the G1 and G2 records
from the frozen mirror s457_mirror_20261022.tar, G6's answers from findings/recompute/L2_inputs/g6/ and its calls from
g6_calls_before_d89.tar (the bytes of 23 October; the D89 rerun of 24 October rewrote findings/runs/), and G6's source
mtimes from findings/recompute/frozen_inputs/g6_before_d89_mtimes.json; each is checked first against the sha256 the
committed provenance records (rebuild()). Every command re-executes itself under PYTHONHASHSEED=0
(fig_repro.pin_hash_seed: a PDF's font subsets depend on it), and the stamp prints its time in Europe/Amsterdam.

THREE STEPS, from the repository root (--as and --n name the plate; the defaults give Supplementary Figure 17):

  1. mirror   uv run --frozen python scripts/S457_fig2_panels.py mirror --to <dir> [--as supplementary|main] [--n N]
     Copies (one ssh session whose script comes on stdin, MIRROR_SH, writing a tar stream; no path or port on any
     command line; read only on the source; the source's mtime kept) each G1 sink's and the G2 sink's
     answers.jsonl and run_identity.json from the Studio's
     ~/projects/mentori-runs/findings/runs/exp_01__<set-up>__exp_v4_s20_n0/ into <dir>/<set-up>/, checks each copy
     against the sha256 the Studio computes, and writes records_manifest.json into the plate's folder: per set-up the
     source host, clone, the clone's HEAD when copied (not the commit the answers ran at), its processes (each process
     id in calls.jsonl matched to the start record run_g1.sh or run_g2.sh wrote for it, live or archived by a restart,
     with that record's commit), path, sha256, size, mtime and lines. For G2 it also copies run_g2.sh's plan, its
     reached file and the three g2_check.py outputs (findings/recompute/G2_runs/g2_matched_budget_{plan,reached}.json,
     g2_{plan,arm,reached}_check.txt) into <dir>/matched_budget/g2_runs/, each checked the same way. The manifest names
     <dir> only when it is inside the repository. Nothing on the Studio is written. The G6 records are the laptop's
     findings/runs/b4_rlm_ref__cap{5,10,20}__all135/answers.jsonl and calls.jsonl, read in place.

  2. figure   uv run --frozen python scripts/S457_fig2_panels.py figure --records <dir> [--as ...] [--n N] [--final]
     Runs the selftest (synthetic records through the plate's calculations), reads the copies named by the manifest
     (each sha256 checked) and the G6 records, keeps each answer key's last line (exp_01 appends, never rewrites;
     chunk_verifier.verifier_status_report reads them the same way), requires every set-up to hold the 135 questions of
     the D5 key (experiments.runner.experiment.questions(), sha256-pinned) x draws 1, 2, 3, checks each answer's times
     add up (clock time = clock time less the wait + the wait), and REPRODUCES FIRST (README.md:75-79), writing nothing
     when a comparison fails: (1) every answer an S455 scan lists (the D92 scans, findings/recompute/Q145/
     S455_d92_affected_studio_g1.json and S455_d92_affected.json, and any scan that read G2's answers) in a file whose
     sha256 S455 recorded and that is unchanged must be found with the stop reason S455 read, and the scans' D92
     actions must be S455_d92_list.json's; if no such file remains, nothing is written; (2) the G1 reruns' stop
     reasons as rerun_d89.sh check read them (experiments/RUNNING.md:181-186), while each file is the one it read;
     (3) G2: every answer made under the plan g2_check read must have that plan's top_k and the reached tokens of
     g2_matched_budget_reached.json, g2_check's COUNTS lines must come out of these records, and the G2 answers
     planned from an out-of-date target must be the 15 experiments/NOW.md:29 names (each while its files are those
     the check read); if no G2 answer is under that plan, nothing is written; (4) the documents' cost numbers (CLAIMS
     below) must be regenerated from findings/recompute/S77_r2q2_cost.json, the artifact the letter cites for them
     (findings/letter_check/question_2.md:16, :26). Then writes into the plate's folder,
     findings/figures_provisional/supp_fig<N>/ (supp_fig17_outcomes/ for Supplementary Figure 17, fig<N>/ for a main
     figure; a folder holding another script's provenance file is refused, and so is a main "Figure 2", which is S531's):
       <name>.{pdf,svg,png}                         <name> is FIGURE_LOCK [files] supplementary_name or name
                                    with --n; one page, every size, font, colour and limit read from
                                    experiments/FIGURE_LOCK.toml (D84, D87): [page] width_double_mm wide, at most
                                    height_max_mm high; the first of [type] font_families, every text at [type]
                                    font_min_pt, panel letters panel_letter_pt and panel_letter_weight, no panel
                                    titles; [colour] categorical (Okabe and Ito) and grey; no line under [lines]
                                    line_min_pt; no ligatures; the PNG is the PDF rasterised at 600 dpi (MuPDF), so
                                    S448 R7 can compare them pixel by pixel; the data state in the stamp only
       the data workbook             a Supplementary figure: "<name> data.xlsx", sheets
                                    "Supplementary Fig. <N>a" and so on (S461's convention; Source Data is a
                                    main-figure rule, editor row 20); a main figure: "Source Data Fig. <N>.xlsx",
                                    sheets "Fig. <N>a" and so on; one sheet per panel, the numbers plotted
       [supplementary_]figure<N>_numbers.json   the same sheets as JSON, "printed": every number printed on the plate,
                                    by its SVG group id, with the sheet, row and format it is written from (S448 R8
                                    (6)); "claims", the letter's cost numbers against these records, until D2
       the workbook's caption, legend_draft.md; with --claims-out DIR (D2, the editorial step S616 claims) claims.json
       (the "claims" key) and claims.md into DIR (every number printed on the plate with its workbook cell;
                                    every sentence of the letter, the main text, the Methods and the Supplementary
                                    Information that gives a number for these panels or that the plate bears on,
                                    with the artifact it came from and what these records give; D82),
                                    [supplementary_]figure<N>_provenance.json
     <n> counts the answers settled of the 4,050 the plate plans (G1 2,430, G2 405, G6 1,215; load() refuses a set-up
     short of its 405, so all are stored): an answer is settled when no rerun of it is owed (S455's D92 list, action
     "rerun", not yet stored again; "stays_failed" answers are settled, D92 Q185), it was not planned from an
     out-of-date token target (G2), and its answers file was checked by S455 for the D89 and D90 Gemini cases (G2: a
     scan of its current file, experiments/NOW.md:29). Files of an earlier data state (the plate's name and the
     workbook's stem) are deleted first. No name carries a "(provisional, ...)" suffix (Q9, Valerio, 11 Nov); --final
     is refused while an answer is not settled. The provenance file's command writes a records folder outside the repository as <records>.

  3. selftest uv run --frozen python scripts/S457_fig2_panels.py selftest
     The plate's calculations on synthetic records (the wait taken off the clock time, the times adding up, the G2
     answers planned from an out-of-date target, the verifier-wait summary, what is still owed, the documents' number
     formats, the command line, and the known-value checks refusing a record that disagrees). Writes nothing outside a
     temporary folder it removes; the figure step runs it first.

THE PANELS (set-ups: the six G1 strategies, the matched-budget arm, then the authors' RLM at caps 5, 10, 20):
  a  a table: per set-up (columns), the answers by stop reason as stored (generation.stop_reason for G1 and G2,
     stop_reason for G6), the answers whose stored text is empty ("no answer text"), and for verified pass the
     verifier status counted by chunk_verifier.verifier_status_report (Rule 4, Q78; its source is executed alone,
     with no Mentori import). A row no answer has is not drawn (its zero is in no cell); a blank cell holds no answer.
  b  tokens per answer (G1 and G2 generation.tokens_used, checked equal to the sum over generation.calls of prompt,
     output and thinking tokens; G6 tokens.total prompt + output + thinking), log scale. Q117's form: per question the
     mean over its draws (one grey dot per question), then per set-up the mean of those (blue point) with Rule 2's
     interval (95% percentile interval over 10,000 resamples of the 135 questions, numpy default_rng(20261013), S407's
     convention; blue bar), and over the dots an unfilled box from the 25th to the 75th percentile of the questions
     with the median inside it (E2; the median's interval in the workbook). Dots that cannot be placed apart within
     their row overlap (their count is in the provenance file). A key to these marks sits under f.
  c  clock time per answer less the time its calls waited for our local server (G1 and G2 generation.latency_s minus
     the sum of waited_for_server_s over generation.calls; G6 wall_s, which has no such wait), the same form. Only the
     verified pass's verifier calls wait (D95 Q200: the wait is our one local verifier server, shown apart in f); the
     workbook also gives the clock time with the wait.
  d  model-call time per answer: the sum of wall_s over generation.calls (G1 and G2 only), the same form; the workbook
     splits it into local (ollama) and API calls and adds the model calls per answer. The authors' RLM is not drawn:
     calls.jsonl times every call, but its sub-calls overlap, so their sum exceeds the clock time (counted in the
     provenance file). Search time is not added: G1 records it on few answers (Q150).
  e  turns used per answer, the six RLM set-ups (G1 generation.rlm.turns, G6 turns_used), a heatmap: a cell per
     set-up and number of turns, coloured by its answers on a log scale ([colour] continuous, reversed; a key beside
     it); no answers, no cell; the cap's cell outlined. To move beside Supplementary Figure 8 (D95 Q201).
  f  verified pass only, linear scale: per question the clock time with the wait (the mean over its draws) and the
     wait for the local verifier server alone, drawn as in b.

No model call. Nothing outside the plate's folder (and the mirror's --to folder) is written.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro as FR  # noqa: E402  (D155: frozen inputs, deterministic files)
FIGURES = ROOT / "findings" / "figures_provisional"
LOCK = ROOT / "experiments" / "LOCK.toml"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
VERIFIER_SRC = ROOT / "experiments" / "mentori" / "backend" / "retrieval" / "chunk_verifier.py"
Q145 = ROOT / "findings" / "recompute" / "Q145"
# The D92 scans (D89, D90 and D92 in one pass; each row carries its D92 action, Q185) and the list merged from them
# (S455 --merge). The D92 scans read the same answers files as the D89 ones (the same sha256), so the comparison is
# unchanged; their actions say which answers are rerun and which stay failed (D92 Q185: 4 of the authors' RLM's 21).
S455_FILES = [Q145 / "S455_d92_affected_studio_g1.json", Q145 / "S455_d92_affected.json"]
S455_LIST = Q145 / "S455_d92_list.json"
OWED = "rerun"                                   # the D92 action of an answer still to be stored again
STUDIO = "10.15.212.253"
STUDIO_CLONE = "projects/mentori-runs"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
INDEX = "exp_v4_s20_n0"

G1 = [("single_pass", "single pass"), ("multi_hop", "multi-hop"), ("verified_pass", "verified pass"),
      ("rlm_5", "RLM-5"), ("rlm_10", "RLM-10"), ("rlm_20", "RLM-20")]
G2 = [("matched_budget", "matched budget")]          # G2 (A12, D36): single pass at RLM-10's input tokens
EXP01 = G1 + G2                                         # the set-ups exp_01 answered, copied from the Studio
JOB = {s: f"g1_{s}" for s, _ in G1} | {"matched_budget": "g2_arm"}   # the start records' "job" per set-up
G6 = [(f"cap{c}", f"Zhang RLM-{c}") for c in (5, 10, 20)]
SETUPS = G1 + G2 + G6
LABEL = dict(SETUPS)
CAP = {"rlm_5": 5, "rlm_10": 10, "rlm_20": 20, "cap5": 5, "cap10": 10, "cap20": 20}
DRAWS = (1, 2, 3)
N_Q = 135
PLANNED = {"G1": 6 * N_Q * 3, "G2": N_Q * 3, "G6": 3 * N_Q * 3}
TOTAL = sum(PLANNED.values())                    # 4,050: the answers this plate plans
N_BOOT, BOOT_SEED = 10000, 20261013              # Rule 2: S407's resamples and seed (scripts/S407:45-57)
SCRIPT = "scripts/S457_fig2_panels.py"
# D291 (Valerio, 7 Nov): the legend prints the paper's name; data and keys keep the API id
GEN_DISPLAY = {"gemini-3-flash-preview": "gemini-3-flash"}
DEFAULT_AS, DEFAULT_N = "supplementary", 17      # D95 Q200: a Supplementary draft. 17 comes from D302 (15 from D257, 6 under FF3 a's one list)
DEFAULT_FOLDER = "supp_fig17_outcomes"            # that plate's folder; any other --n takes supp_fig<N>
S77 = ROOT / "findings" / "recompute" / "S77_r2q2_cost.json"   # the letter's cost numbers (question_2.md:16, :26)
from doc_paths import LETTER, doc  # noqa: E402  the live documents, resubmission/ (Valerio, 4 Nov)
MAIN_TEXT = doc("02_Main_Text.docx")
# D2 (Valerio, 8 Nov): figures are built from data only. The claims list (claims_now, claims_md) reads the documents,
# so it is an editorial check run outside the figure build: figure and rebuild write it only with `--claims-out DIR`
# (scripts/S616_figure_editorial.py claims): claims.md and claims.json (the "claims" key the numbers file carried until
# D2) into DIR. Without it no document is opened, the numbers file has no "claims" key and the provenance lists no
# document and no claims.md.
CLAIMS_OUT: Path | None = None


def g1_run(s):
    """The exp_01 sink of a G1 or G2 set-up."""
    return f"exp_01__{s}__{INDEX}"


# The authors' RLM records (G6) are read in place from the gitignored findings/runs/ by figure; rebuild (D155) points
# these at the frozen copies of the bytes the committed plate read (before the D89 rerun of 24 October rewrote them):
# the answers in findings/recompute/L2_inputs/g6/, the calls in g6_calls_before_d89.tar, and their source mtimes
# (the stamp's "records of") in findings/recompute/frozen_inputs/g6_before_d89_mtimes.json.
G6_ANSWERS_DIR = ROOT / "findings" / "runs"
G6_CALLS_DIR = ROOT / "findings" / "runs"
G6_MTIMES: dict | None = None          # {"findings/runs/<run>/answers.jsonl": mtime}; None: the files' own mtimes
STAMP_TZ = "Europe/Amsterdam"          # the zone every stamp prints its times in (as S447.iso_local, D155)


def g6_run(c):
    return f"b4_rlm_ref__{c}__all135"


def g6_path(c):
    return G6_ANSWERS_DIR / g6_run(c) / "answers.jsonl"


def g6_calls_path(c):
    return G6_CALLS_DIR / g6_run(c) / "calls.jsonl"


G2_RUN = g1_run("matched_budget")
# G2's plan, its per-answer reached tokens, and the COUNTS lines g2_check.py printed on each when run_g2.sh ran it
# (Studio findings/recompute/G2_runs/, 18 October 03:16 and 07:21; experiments/RUNNING.md:127-132)
G2_CHECK_FILES = ("g2_matched_budget_plan.json", "g2_matched_budget_reached.json", "g2_plan_check.txt",
                  "g2_arm_check.txt", "g2_reached_check.txt")


# ---------------------------------------------------------------------------------------------------------------
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_local(ts: float) -> str:
    """A time as the stamps print it, in STAMP_TZ whatever the zone of the computer that builds (D155: one text on
    every machine; the plates of 22 and 23 October were built in this zone)."""
    from zoneinfo import ZoneInfo
    return datetime.fromtimestamp(ts, ZoneInfo(STAMP_TZ)).strftime("%Y-%m-%d %H:%M %Z")


# ---------------------------------------------------------------------------------------------------------------
# mirror
# ---------------------------------------------------------------------------------------------------------------
PROC_PY = r"""
import json, glob, os, sys
out = {"tz": None, "starts": [], "pids": {}}
import time
out["tz"] = time.strftime("%z")
for f in sorted(glob.glob("findings/recompute/G1_runs/g1_*.start.json") + glob.glob("findings/recompute/G1_runs/*/g1_*.start.json")
                + glob.glob("findings/recompute/G2_runs/g2_*.start.json") + glob.glob("findings/recompute/G2_runs/*/g2_*.start.json")):
    j = json.load(open(f)); j["file"] = f; out["starts"].append(j)
for s in sys.argv[1:]:
    first, last, n = {}, {}, {}
    for ln in open("findings/runs/exp_01__%s__exp_v4_s20_n0/calls.jsonl" % s):
        try:
            c = json.loads(ln)
        except ValueError:
            continue
        p, a = c.get("pid"), c.get("at")
        if p is None or a is None:
            continue
        first[p] = min(first.get(p, a), a); last[p] = max(last.get(p, a), a); n[p] = n.get(p, 0) + 1
    out["pids"][s] = {str(p): [first[p], last[p], n[p]] for p in first}
print(json.dumps(out))
"""


def processes(strategies, j=None):
    """Which commit each G1 or G2 process ran: the start records run_g1.sh and run_g2.sh write (the live one and those
    archived by each restart or rerun, findings/recompute/G1_runs/[*/]g1_<strategy>.start.json and
    findings/recompute/G2_runs/[*/]g2_arm.start.json, each with its commit and UTC start) and, per process id in
    calls.jsonl, its first and last call time (local to the Studio). A process is matched to the one start record of
    its set-up's job (JOB) that began at most 600 s before its first call; anything else stops the mirror."""
    if j is None:                    # PROC_PY's output, read by mirror's one stdin session (MIRROR_SH)
        raise SystemExit("processes: PROC_PY's output is read by mirror's stdin session (MIRROR_SH) only")
    tz = j["tz"]
    off = (1 if tz[0] == "+" else -1) * (int(tz[1:3]) * 3600 + int(tz[3:5]) * 60)
    out = {}
    for s in strategies:
        starts = [x for x in j["starts"] if x.get("job") == JOB[s]]
        procs = []
        for pid, (first, last, n) in sorted(j["pids"][s].items(), key=lambda t: t[1][0]):
            t_first = datetime.fromisoformat(first).replace(tzinfo=timezone.utc).timestamp() - off
            hit = [x for x in starts if 0 <= t_first - datetime.fromisoformat(x["start"].replace("Z", "+00:00"))
                   .timestamp() <= 600]
            if len(hit) != 1:
                raise SystemExit(f"{s} pid {pid} (first call {first} {tz}): {len(hit)} start records within 600 s "
                                 f"before it, want 1")
            procs.append({"pid": int(pid), "commit": hit[0]["commit"][:7], "start_utc": hit[0]["start"],
                          "start_record": hit[0]["file"], "cmd": hit[0].get("cmd"), "first_call_local": first,
                          "last_call_local": last, "calls": n, "studio_utc_offset": tz})
        out[s] = procs
    return out


# The remote half of mirror, sent on ssh's stdin (never on a command line, 22 October: no file name, path or port is
# on a command line on either machine, so no K1 or S3 guard that reads command lines is tripped by the copy). In the
# Studio clone it reads, read only, what PROC_PY reads (the start records and each sink's calls.jsonl process ids),
# each exp_01 sink's answers.jsonl and run_identity.json, its calls' lock_sha256 counts, and G2's check files; it
# writes one tar stream: META.json (HEAD, PROC_PY's output, per file its sha256, size and mtime, the lock counts) and
# each file under <set-up>/ (G2's checks under matched_budget/g2_runs/), the bytes hashed being the bytes sent.
MIRROR_SH = r"""set -e
cd "$HOME/__CLONE__"
/usr/bin/python3 - <<'PY'
import collections, hashlib, io, json, os, re, subprocess, sys, tarfile
SETUPS = __SETUPS__
G2_FILES = __G2FILES__
meta = {"head": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "files": {}, "locks": {}, "calls": {}}
import contextlib
buf = io.StringIO()
sys.argv = ["proc"] + SETUPS
with contextlib.redirect_stdout(buf):
    exec(__PROC__, {"__name__": "proc"})
meta["proc"] = json.loads(buf.getvalue())
blobs = []
def take(src, arc):
    st = os.stat(src)
    b = open(src, "rb").read()
    meta["files"][arc] = {"path": src, "sha256": hashlib.sha256(b).hexdigest(), "size": len(b), "mtime": int(st.st_mtime)}
    blobs.append((arc, b, st.st_mtime))
for s in SETUPS:
    d = "findings/runs/exp_01__%s__exp_v4_s20_n0" % s
    for f in ("answers.jsonl", "run_identity.json"):
        take(d + "/" + f, s + "/" + f)
    n = collections.Counter()
    cb = open(d + "/calls.jsonl", "rb").read()
    meta["calls"][s] = {"path": d + "/calls.jsonl", "sha256": hashlib.sha256(cb).hexdigest(),
                        "lines": cb.count(b"\n")}
    for ln in cb.decode(errors="replace").splitlines():
        for m in re.finditer(r'"lock_sha256": "([0-9a-f]*)"', ln):
            n[m.group(1)] += 1
    meta["locks"][s] = dict(n)
for f in G2_FILES:
    take("findings/recompute/G2_runs/" + f, "matched_budget/g2_runs/" + f)
tf = tarfile.open(fileobj=sys.stdout.buffer, mode="w|")
mb = json.dumps(meta).encode()
ti = tarfile.TarInfo("META.json"); ti.size = len(mb); tf.addfile(ti, io.BytesIO(mb))
for arc, b, mt in blobs:
    ti = tarfile.TarInfo(arc); ti.size = len(b); ti.mtime = mt; tf.addfile(ti, io.BytesIO(b))
tf.close()
PY
"""


def mirror(args):
    nm = naming(args.kind, args.n)
    to = Path(args.to).resolve()
    if to.exists() and any(to.iterdir()):
        raise SystemExit(f"{to} exists and is not empty: mirror into a new folder")
    import io
    import tarfile
    setups = [s for s, _ in EXP01]
    proc_src = PROC_PY
    script = (MIRROR_SH.replace("__CLONE__", STUDIO_CLONE).replace("__SETUPS__", json.dumps(setups))
              .replace("__G2FILES__", json.dumps(list(G2_CHECK_FILES))).replace("__PROC__", repr(proc_src)))
    r = subprocess.run(SSH + [STUDIO, "bash", "-s"], input=script.encode(), capture_output=True)
    if r.returncode:
        raise SystemExit(f"{STUDIO}: mirror failed (exit {r.returncode}): {r.stderr.decode(errors='replace')[:300]}")
    to.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:") as tf:
        names = tf.getnames()
        ok = {"META.json"} | {f"{s}/{f}" for s in setups for f in ("answers.jsonl", "run_identity.json")} | \
            {f"matched_budget/g2_runs/{f}" for f in G2_CHECK_FILES}
        if set(names) != ok:
            raise SystemExit(f"mirror: the stream holds {sorted(set(names) ^ ok)[:4]} beyond or short of what was sent for")
        tf.extractall(to, filter="data")
    meta = json.loads((to / "META.json").read_text())
    (to / "META.json").unlink()
    for arc, v in meta["files"].items():
        if sha256_file(to / arc) != v["sha256"]:
            raise SystemExit(f"{arc}: the copy's sha256 is not the one the Studio computed on the bytes it sent")
    commit = meta["head"]
    procs = processes(setups, meta["proc"])
    runs = {}
    for s in setups:
        v = meta["files"][f"{s}/answers.jsonl"]
        runs[s] = {"group": "G2" if s == "matched_budget" else "G1", "run": g1_run(s), "host": STUDIO,
                   "clone": STUDIO_CLONE, "clone_head_when_copied": commit,
                   "processes": procs[s], "path": f"{STUDIO_CLONE}/{v['path']}",
                   "calls_lock_sha256": meta["locks"][s], "calls_sha256": meta["calls"][s]["sha256"],
                   "calls_lines": meta["calls"][s]["lines"],
                   "sha256": v["sha256"], "size": v["size"], "mtime": v["mtime"], "mtime_local": iso_local(v["mtime"]),
                   "lines": sum(1 for _ in open(to / s / "answers.jsonl"))}
    g2c = {}
    for f in G2_CHECK_FILES:
        v = meta["files"][f"matched_budget/g2_runs/{f}"]
        g2c[f] = {"path": f"{STUDIO_CLONE}/{v['path']}", "sha256": v["sha256"], "size": v["size"],
                  "mtime": v["mtime"], "mtime_local": iso_local(v["mtime"])}
    runs["matched_budget"]["g2_runs"] = g2c
    # the copy's folder is named only when it is inside the repository: a temporary path would ship with the commit
    copied = str(to.relative_to(ROOT)) if to.is_relative_to(ROOT) else "outside the repository (mirror --to)"
    man = {"what": "the G1 and G2 records the plate reads, copied read-only from the Studio by S457 mirror",
           "written_utc": utc_now(), "copied_to": copied, "exp01": runs}
    nm["out"].mkdir(parents=True, exist_ok=True)
    nm["manifest"].write_text(json.dumps(man, indent=1) + "\n")
    print(f"mirrored {len(runs)} exp_01 sinks (G1 and G2) from {STUDIO} (clone at {commit}) into {to}: "
          + ", ".join(f"{s} {v['lines']} lines" for s, v in runs.items())
          + f"; manifest {nm['manifest'].relative_to(ROOT)}")


# ---------------------------------------------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------------------------------------------
def last_lines(path: Path):
    """{answer_key: record}, a key's last line (exp_01 and the B4 runner append, never rewrite)."""
    out = {}
    with open(path) as fh:
        for ln in fh:
            if ln.strip():
                r = json.loads(ln)
                out[r["answer_key"]] = r
    return out


def verifier_report_fn():
    """chunk_verifier.verifier_status_report, its source executed alone (the module imports Mentori's lock adapter,
    which this environment does not load); Rule 4 Q78 names this function as the count."""
    from typing import Any, Dict
    src = VERIFIER_SRC.read_text()
    fn = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "verifier_status_report"]
    if len(fn) != 1:
        raise SystemExit(f"{VERIFIER_SRC.relative_to(ROOT)}: verifier_status_report not found once")
    ns = {"Dict": Dict, "Any": Any}
    exec(compile(ast.Module(fn, []), str(VERIFIER_SRC), "exec"), ns)
    return ns["verifier_status_report"]


def exp01_row(k, r, setup):
    """One Mentori answer (G1 or G2) as the plate reads it. Clock time less the wait: generation.latency_s minus the sum
    of waited_for_server_s over generation.calls (the time a call waited for our one local server before it was sent,
    inside latency_s and outside the call's wall_s; D95 Q200). The selftest checks it on synthetic records."""
    g = r["generation"]
    calls = g.get("calls") or []
    summed = sum((c.get("prompt_tokens") or 0) + (c.get("output_tokens") or 0)
                 + (c.get("thinking_tokens") or 0) for c in calls)
    if summed != g["tokens_used"]:
        raise SystemExit(f"{k}: tokens_used {g['tokens_used']} is not the sum over its calls {summed}")
    rlm = g.get("rlm") or {}
    waits = [c["waited_for_server_s"] for c in calls if c.get("waited_for_server_s") is not None]
    wait = sum(waits)
    mb = (g.get("matched_budget") or {}) if setup == "matched_budget" else None
    one = calls[0].get("prompt_tokens") if len(calls) == 1 else None
    return {"key": k, "q": r["question_id"], "draw": r["draw"], "stop": g["stop_reason"],
            "status": None, "answer": g.get("answer") or "", "ctx": r.get("ctx_uid"), "error": g.get("error"),
            "calls_n": len(calls), "tokens": g["tokens_used"], "top_k": g.get("top_k"),
            "sources": [x["answer_key"] for x in mb.get("sources", [])] if mb is not None else None,
            "sources_full": mb.get("sources", []) if mb is not None else None, "mb": mb,
            # g2_check reached's "reached tokens": the prompt tokens of the answer's one counted call
            "reached_tokens": one if isinstance(one, int) else None,
            "prompt": g.get("prompt_tokens"), "output": g.get("output_tokens"),
            "thinking": g.get("thinking_tokens"), "tokens_missing": g.get("calls_without_tokens"),
            "clock": g["latency_s"], "model": sum(c.get("wall_s") or 0.0 for c in calls),
            "clock_less_wait": g["latency_s"] - wait,
            "model_calls_no_wall": sum(1 for c in calls if c.get("wall_s") is None),
            "wait": wait, "waits": waits,
            "model_local": sum(c.get("wall_s") or 0.0 for c in calls if c.get("provider") == "ollama"),
            "model_api": sum(c.get("wall_s") or 0.0 for c in calls if c.get("provider") != "ollama"),
            "local_models": sorted({c.get("model") for c in calls if c.get("provider") == "ollama"}),
            "pid": r.get("pid"), "gen_model": r.get("gen_model"),
            "turns": rlm.get("turns") if setup.startswith("rlm") else None,
            "pool": (r.get("pool") or {}).get("size"),
            "verification": g.get("verification"), "raw": r if setup == "verified_pass" else None,
            "search_timed": '"search_s"' in json.dumps(r)}


def check_times(rows):
    """Each answer's times hold together: clock time = clock time less the wait + the wait, and the wait is the sum of
    its calls' waits (a Mentori answer), or no wait (the authors' RLM). Raises on the first that does not."""
    for x in rows:
        w = x.get("wait") or 0.0
        if abs(x["clock"] - x["clock_less_wait"] - w) > 1e-6 or abs(w - sum(x.get("waits") or [])) > 1e-6:
            raise SystemExit(f"{x['key']}: clock {x['clock']}, clock less wait {x['clock_less_wait']}, wait {w}, "
                             f"calls' waits {x.get('waits')}: they do not add up")


def load(rec_dir: Path, nm):
    """The answers of the ten set-ups, as {setup: [record, ...]} each a normalised dict, plus the inputs hashed."""
    from experiments.runner.experiment import questions, KEY_D5, KEY_V24
    qs = questions()
    qtype = {q["id"]: q["answer_type"] for q in qs}
    if len(qtype) != N_Q:
        raise SystemExit(f"{len(qtype)} questions from the key, want {N_Q}")
    manifest = nm["manifest"]
    if not manifest.exists():
        raise SystemExit(f"{manifest.relative_to(ROOT)} missing: run 'mirror --to <dir>' with the same --as and --n "
                         f"first")
    man = json.loads(manifest.read_text())
    if set(man.get("exp01", {})) != {s for s, _ in EXP01}:
        raise SystemExit(f"{manifest.relative_to(ROOT)} does not name the {len(EXP01)} exp_01 sinks (G1 and G2): "
                         f"run mirror again")
    inputs, mtimes, raw = {}, [], {}
    frozen_rec = rec_dir.resolve().is_relative_to(ROOT)   # the frozen mirror (rebuild): named by its frozen label
    for s, _ in EXP01:
        p = rec_dir / s / "answers.jsonl"
        sha = sha256_file(p)
        if sha != man["exp01"][s]["sha256"]:
            raise SystemExit(f"{p}: sha256 {sha[:12]} is not the manifest's {man['exp01'][s]['sha256'][:12]}")
        inputs[FR.frozen_label(p) if frozen_rec else f"Studio:{man['exp01'][s]['path']}"] = sha
        mtimes.append(man["exp01"][s]["mtime"])
        raw[s] = (p, sha, last_lines(p))
    g6_calls = {}
    for c, _ in G6:
        p = g6_path(c)
        sha = sha256_file(p)
        inputs[FR.frozen_label(p)] = sha
        if G6_MTIMES is None:
            mtimes.append(p.stat().st_mtime)
        else:                                            # a frozen copy keeps no mtime: the source's, as recorded
            mtimes.append(G6_MTIMES[f"findings/runs/{g6_run(c)}/answers.jsonl"])
        raw[c] = (p, sha, last_lines(p))
        pc = g6_calls_path(c)                            # the authors' RLM's calls, joined by (ctx_uid, seq)
        inputs[FR.frozen_label(pc)] = sha256_file(pc)
        g6_calls[c] = {}
        with open(pc) as fh:
            for ln in fh:
                if ln.strip():
                    x = json.loads(ln)
                    g6_calls[c][(x["ctx_uid"], x["seq"])] = {"wall_s": x.get("wall_s"), "at": x.get("at")}
    for p in (KEY_D5, KEY_V24, VERIFIER_SRC, LOCK, FIGURE_LOCK, manifest, *S455_FILES, S455_LIST, S77):
        inputs[str(Path(p).relative_to(ROOT))] = sha256_file(Path(p))
    if G6_MTIMES is not None:                            # rebuild: the recorded mtimes the stamp's time comes from
        inputs[str(G6_MTIMES_JSON.relative_to(ROOT))] = sha256_file(G6_MTIMES_JSON)
    g2c = man["exp01"]["matched_budget"].get("g2_runs") or {}
    if set(g2c) != set(G2_CHECK_FILES):
        raise SystemExit(f"{manifest.relative_to(ROOT)} does not name G2's plan and checks {G2_CHECK_FILES}: run "
                         f"mirror again")
    for f, e in g2c.items():
        p = rec_dir / "matched_budget" / "g2_runs" / f
        if sha256_file(p) != e["sha256"]:
            raise SystemExit(f"{p}: sha256 is not the manifest's {e['sha256'][:12]}")
        inputs[FR.frozen_label(p) if frozen_rec else f"Studio:{e['path']}"] = e["sha256"]
    data = {}
    for setup, _ in SETUPS:
        p, sha, recs = raw[setup]
        rows = []
        for k, r in recs.items():
            if setup in CAP and setup.startswith("cap"):
                t = r["tokens"]["total"]
                missing = sum(r["tokens"][part][f"{m}_missing"] for part in ("root", "forced_final", "sub")
                              for m in ("prompt_tokens", "output_tokens", "thinking_tokens"))
                cs = [g6_calls[setup].get((r["ctx_uid"], q)) for q in r["calls"]["seqs"]]
                if any(x is None or x["wall_s"] is None or x["at"] is None for x in cs):
                    raise SystemExit(f"{k}: a call of this answer has no record, wall_s or at in calls.jsonl")
                ats = [datetime.fromisoformat(x["at"]).timestamp() for x in cs]
                rows.append({"key": k, "q": r["question_id"], "draw": r["draw"], "stop": r["stop_reason"],
                             "status": r["status"], "answer": r.get("answer") or "", "ctx": r.get("ctx_uid"),
                             "calls_n": len(r["calls"]["seqs"]), "sources": None,
                             "tokens": t["prompt_tokens"] + t["output_tokens"] + t["thinking_tokens"],
                             "prompt": t["prompt_tokens"], "output": t["output_tokens"],
                             "thinking": t["thinking_tokens"], "tokens_missing": missing, "clock": r["wall_s"],
                             "clock_less_wait": r["wall_s"],          # the package waits for no local server
                             "model": None, "turns": r.get("turns_used"), "lock": r.get("lock_sha256"),
                             "pid": r.get("pid"), "calls_wall_sum": sum(x["wall_s"] for x in cs),
                             "gen_model": r.get("model"), "pkg": f"{r['package']['name']} {r['package']['version']}",
                             "max_iterations": r["package"]["rlm_kwargs"]["max_iterations"],
                             # gemini_client._record stamps "at" when the call's record is made, before it is sent:
                             # the answer's calls span from its first call's start to its last call's end
                             "span": (min(ats), max(a + x["wall_s"] for a, x in zip(ats, cs)))})
            else:
                rows.append(exp01_row(k, r, setup))
        check_times(rows)
        got = Counter((x["q"], x["draw"]) for x in rows)
        want = {(q, d) for q in qtype for d in DRAWS}
        if set(got) != want or any(v != 1 for v in got.values()):
            raise SystemExit(f"{setup}: {len(got)} (question, draw) pairs, want the {len(want)} of the key x draws "
                             f"{DRAWS}; extra {sorted(set(got) - want)[:3]}, missing {sorted(want - set(got))[:3]}")
        data[setup] = rows
    return data, qs, qtype, inputs, max(mtimes), man, {s: raw[s][1] for s in raw}


# ---------------------------------------------------------------------------------------------------------------
# reproduce first
# ---------------------------------------------------------------------------------------------------------------
# Known values from the runs' own checks, each compared only while the file it was read from is unchanged (sha256).
# rerun_d89.sh check, 18 October 08:17 (experiments/RUNNING.md:181-186): of G1's 15 D89/D90 reruns, rlm_5
# 15_rabies_tanzania_TE3 d3 ended max_turns_partial, verified_pass 19_hpai_canada_TE3 d3 blocked, the other 13 final;
# the four answers files as that check read them (each file's mtime is its rerun's end, RUNNING.md:181).
G1_RERUN_CHECK = {
    "files": {"verified_pass": "1ce4b1052912d8592b912da29ed987df9c2a4baca575cf80cc2b9d33334f8148",
              "rlm_5": "cc10c9eb881fa9618ff2fb8ec7a3f1bb9cf58662827cd67b326e47f67b51d42c",
              "rlm_10": "ecb6de5343d172894fd56d57997e3301d70ca3fb509ae2cd65f8e47eb8c268b7",
              "rlm_20": "1e5b124d8bbd98640c87051916305ed0c04d668447967c60a08d6945fca32c62"},
    "stop": {"exp_v4_s20_n0|rlm_5|15_rabies_tanzania_TE3|d3": "max_turns_partial",
             "exp_v4_s20_n0|verified_pass|19_hpai_canada_TE3|d3": "blocked"},
    "other": "final"}
# G2's answers whose token target was set before an RLM-10 answer of their question was stored again: the five
# questions experiments/NOW.md:29 names (from experiments/RUNNING.md:186), x draws 1 to 3, while G2's answers file is
# the arm's of 07:21 and RLM-10's is the rerun's of 08:06 (RUNNING.md:131, :181).
G2_STALE_KNOWN = {"files": {"matched_budget": "6b4c46531eca233b1bd73a5cb56819874e1807e9ee6c80152e9ce904a2d32728",
                            "rlm_10": G1_RERUN_CHECK["files"]["rlm_10"]},
                  "questions": ["01_sarek_CO2", "07_salmon_FR1", "OOD_024", "OOD_025", "OOD_035"]}


def scan_shas(j):
    """{run: sha256 of its answers.jsonl} as an S455 scan read it."""
    out = {}
    for i in j["provenance"]["inputs"]:
        for a in i.get("answers", []):
            out[a["path"].split("/")[2]] = a["sha256"]
    return out


def scan_calls(j):
    """{run: sha256 of its calls.jsonl} as an S455 scan read it (a run with no affected call lists no answers file)."""
    out = {}
    for i in j["provenance"]["inputs"]:
        if str(i.get("path", "")).endswith("/calls.jsonl"):
            out[i["path"].split("/")[2]] = i["sha256"]
    return out


def g2_scans():
    """S455 scans (findings/recompute/Q145/S455_*.json, not the merged list) whose inputs hold G2's answers file, or
    its calls file (S455 reads every run's calls.jsonl and lists an answers file only for a run with an affected call;
    the G2 scan of 22 October, 0 of 405 affected): S455 over G2's 405 answers for the D89/D90 Gemini cases
    (experiments/NOW.md:29; none on 18 October)."""
    out = []
    for f in sorted(Q145.glob("S455_*.json")):
        if f == S455_LIST or f.name.endswith("_list.json"):
            continue
        try:
            j = json.loads(f.read_text())
        except ValueError:
            continue
        if isinstance(j, dict) and "provenance" in j and "rows" in j and (G2_RUN in scan_shas(j)
                                                                          or G2_RUN in scan_calls(j)):
            out.append((f, j))
    return out


def reproduce(data, shas, man=None):
    """REPRODUCE FIRST (README.md:75-79). Every answer an S455 scan lists, in an answers file whose sha256 the scan
    recorded and which is unchanged, must be read here with the stop reason S455 read. The scans are the D92 ones
    (G1 and the authors' RLM; S455_FILES) and any that read G2's answers (G2's rows only). Their actions must be the
    merged list's (S455_LIST), the list the reruns follow. Returns what was compared, {set-up: {answer: action}} and
    {set-up: answers stored again since} (the record's ctx_uid is no longer the one S455 read: a rerun stores a new
    context), and the G2 scans' state."""
    run_of = {g1_run(s): s for s, _ in EXP01} | {f"b4_rlm_ref__{c}__all135": c for c, _ in G6}
    by_key = {s: {x["key"]: x for x in rows} for s, rows in data.items()}
    compared, skipped, bad = 0, 0, []
    named, again = defaultdict(dict), defaultdict(set)
    g2 = g2_scans()
    calls_now = ((man or {}).get("exp01", {}).get("matched_budget") or {}).get("calls_sha256")
    g2_current = [str(f.relative_to(ROOT)) for f, j in g2 if scan_shas(j).get(G2_RUN) == shas["matched_budget"]
                  or (calls_now is not None and scan_calls(j).get(G2_RUN) == calls_now)]
    sources = [(f, json.loads(f.read_text()), None) for f in S455_FILES] + [(f, j, "matched_budget") for f, j in g2]
    for f, j, only in sources:
        s455_sha = scan_shas(j)
        for row in j["rows"]:
            setup = run_of.get(row["run"])
            if setup is None or (only and setup != only) or (not only and setup == "matched_budget"):
                continue
            if "action" not in row:
                raise SystemExit(f"{f.relative_to(ROOT)}: row {row['answer_key']} has no D92 action; point S455_FILES "
                                 f"at a D92 scan")
            named[setup][row["answer_key"]] = row["action"]
            now = by_key[setup].get(row["answer_key"])
            if now is not None and now["ctx"] != row["ctx_uid"]:
                again[setup].add(row["answer_key"])
            if s455_sha.get(row["run"]) != shas[setup]:
                skipped += 1
                continue
            compared += 1
            if now is None or now["stop"] != row["stop_reason"]:
                bad.append(f"{row['answer_key']}: S455 {row['stop_reason']!r}, here {now and now['stop']!r}")
    if bad:
        raise SystemExit(f"reproduce FAILED, nothing written: {len(bad)} of {compared} S455 answers read differently, "
                         f"e.g. {bad[:3]}")
    gated = ((G6_READINGS or {}).get("gate_reproduce") or {}).get("compared")
    if not compared and not gated:
        raise SystemExit("reproduce: no S455 answers file is unchanged, so no known value can be reproduced; nothing "
                         "written (point S455_FILES at a newer S455 run)")
    # D160 Q23: on the records after the D135 reruns no G6 file is the one S455 read; rebuild's gate reproduced the
    # S455 answers on the records before them (G6_READINGS["gate_reproduce"]), so none here is not a refusal
    # the scans' actions are the merged list's, and the list was merged from these scans as they are
    lst = json.loads(S455_LIST.read_text())
    merged = {Path(x["path"]).name: x["sha256"] for x in lst["provenance"]["scans"]}
    for f in S455_FILES:
        if merged.get(f.name) != sha256_file(f):
            raise SystemExit(f"{S455_LIST.relative_to(ROOT)} was not merged from {f.relative_to(ROOT)} as it is now: "
                             f"run S455 --merge again or point S455_FILES at the scans it merged")
    in_list = {(run_of[r["run"]], r["answer_key"], r["action"]) for r in lst["rows"]
               if r["run"] in run_of and run_of[r["run"]] != "matched_budget"}
    in_scans = {(s, k, a) for s, d in named.items() if s != "matched_budget" for k, a in d.items()}
    if in_list != in_scans:
        raise SystemExit(f"{S455_LIST.relative_to(ROOT)} and the scans differ for this plate's runs: "
                         f"{sorted(in_list ^ in_scans)[:3]}")
    print(f"reproduce: {compared} answers S455 lists for D89, D90 and D92 read with S455's stop reason ({skipped} in "
          f"files changed since S455, not compared); their actions are {S455_LIST.name}'s")
    return {"compared": compared, "skipped_changed_files": skipped,
            "s455_files": [str(f.relative_to(ROOT)) for f in S455_FILES], "s455_list": str(S455_LIST.relative_to(ROOT)),
            "named_by_setup": {s: dict(Counter(d.values())) for s, d in named.items()},
            "stored_again_by_setup": {s: len(v) for s, v in again.items()},
            "g2_scans": [str(f.relative_to(ROOT)) for f, _ in g2],
            "g2_scans_of_the_current_file": g2_current}, named, again


def reproduce_g1_reruns(data, shas, named, again):
    """The G1 reruns' stop reasons as rerun_d89.sh check read them (G1_RERUN_CHECK), in each file that check read."""
    by_key = {s: {x["key"]: x for x in data[s]} for s, _ in G1}
    compared, bad = 0, []
    for s, sha in G1_RERUN_CHECK["files"].items():
        if shas[s] != sha:
            continue
        for k, a in named.get(s, {}).items():
            if a != OWED:
                continue
            want = G1_RERUN_CHECK["stop"].get(k, G1_RERUN_CHECK["other"])
            compared += 1
            if k not in again.get(s, set()) or by_key[s][k]["stop"] != want:
                bad.append(f"{k}: the check read a rerun ending {want!r}, here {by_key[s][k]['stop']!r}, stored again "
                           f"{k in again.get(s, set())}")
    if bad:
        raise SystemExit(f"reproduce FAILED, nothing written: {bad[:3]}")
    print(f"reproduce: {compared} G1 reruns read with the stop reason rerun_d89.sh check read (RUNNING.md:181-186)"
          + ("" if compared else "; none compared (every file changed since that check)"))
    return {"compared": compared, "source": "experiments/RUNNING.md:181-186 (rerun_d89.sh check, 18 October 08:17)"}


def g2_stale_answers(data, again):
    """G2's answers whose token target is out of date. G2's target is set per question from that question's RLM-10
    answers (matched_budget.scope "question"; a failed draw is left out of its sources): it is out of date when a source
    no longer reads as the RLM-10 answer stored now (input tokens, stop reason, calls), or when a draw left out was
    stored again since S455. The selftest checks each branch on synthetic records."""
    r10 = {x["key"]: x for x in data["rlm_10"]}
    r10_again = again.get("rlm_10", set())

    def stale(x):
        src = {s_["answer_key"]: s_ for s_ in x["sources_full"]}
        moved = any(k not in r10 or (r10[k]["prompt"], r10[k]["stop"], r10[k]["calls_n"]) !=
                    (s_["input_tokens"], s_["stop_reason"], s_["n_calls"]) for k, s_ in src.items())
        left_out = any(k in r10_again and k not in src for k, y in r10.items() if y["q"] == x["q"])
        return moved or left_out
    return [x for x in data["matched_budget"] if stale(x)]


def reproduce_g2(data, shas, rec_dir, man, g2_from):
    """G2's known values (README.md:75-79): each answer made under the plan g2_check read must have that plan's top_k
    and the reached tokens g2_matched_budget_reached.json gives it (matched_budget.reached: the prompt tokens of the
    answer's one call); when every answer is under that plan and the answers file is no newer than the checks, the
    COUNTS lines g2_check printed (plan: top_k median and max; arm: stored, errors, empty; reached: at the planned
    tokens, at or above the target, without a count) must come out of these records; and while G2's and RLM-10's files
    are those of G2_STALE_KNOWN, the answers planned from an old target must be that list's."""
    import statistics
    d = rec_dir / "matched_budget" / "g2_runs"
    plan_p = d / "g2_matched_budget_plan.json"
    plan, plan_sha = json.loads(plan_p.read_text()), sha256_file(plan_p)
    reached = json.loads((d / "g2_matched_budget_reached.json").read_text())
    if reached.get("plan_made") != plan.get("made"):
        raise SystemExit(f"reproduce G2: the reached file was computed against the plan made "
                         f"{reached.get('plan_made')}, the plan was made {plan.get('made')}")
    rrow = {x["answer_key"]: x for x in reached["answers"]}
    rows = data["matched_budget"]
    under = [x for x in rows if (x["mb"] or {}).get("plan_sha256") == plan_sha]
    bad = []
    for x in under:
        e, rr = plan["questions"][x["q"]], rrow.get(x["key"])
        got = (x["top_k"], x["mb"].get("target_tokens"), x["mb"].get("planned_tokens"), x["reached_tokens"])
        want = (e["top_k"], e["target_tokens"], e["planned_tokens"], rr and rr["reached_tokens"])
        if rr is None or got != want:
            bad.append(f"{x['key']}: top_k, target, planned, reached {got}, the plan and reached file {want}")
    if bad:
        raise SystemExit(f"reproduce G2 FAILED, nothing written: {len(bad)} of {len(under)}, e.g. {bad[:2]}")
    if not under:
        raise SystemExit("reproduce G2: no G2 answer was made under the plan g2_check read, so no known value can be "
                         "reproduced; nothing written (mirror again once run_g2.sh has checked the new plan)")
    counts = None
    g2c = man["exp01"]["matched_budget"]["g2_runs"]
    # the checks that read the answers file (the plan's check read the plan)
    read_answers = min(g2c[f]["mtime"] for f in ("g2_arm_check.txt", "g2_reached_check.txt"))
    if len(under) == len(rows) and man["exp01"]["matched_budget"]["mtime"] <= read_answers:
        txt = {f: (d / f).read_text() for f in G2_CHECK_FILES if f.endswith(".txt")}
        mp = re.search(r"COUNTS: plan .*top_k median (\S+) max (\d+)", txt["g2_plan_check.txt"])
        ma = re.search(r"COUNTS: arm (\d+) of \d+ stored .*?, (\d+) errors, (\d+) empty", txt["g2_arm_check.txt"])
        mr = re.search(r"COUNTS: reached (\d+) answers, (\d+) at the planned tokens, (\d+) without a count",
                       txt["g2_reached_check.txt"])
        ma2 = re.search(r"at or above the target (\d+)", txt["g2_reached_check.txt"])
        if not (mp and ma and mr and ma2):
            raise SystemExit("reproduce G2: a COUNTS line of g2_check is not where it was (g2_*_check.txt)")
        ks = {x["q"]: x["top_k"] for x in rows}
        got = {"top_k median": str(statistics.median(ks.values())), "top_k max": str(max(ks.values())),
               "stored": str(len(rows)), "errors": str(sum(1 for x in rows if x["error"])),
               "empty": str(sum(1 for x in rows if not x["answer"])),
               "reached answers": str(len(rows)),
               "at the planned tokens": str(sum(1 for x in rows if x["reached_tokens"] is not None
                                                and x["reached_tokens"] == x["mb"]["planned_tokens"])),
               "at or above the target": str(sum(1 for x in rows if x["reached_tokens"] is not None
                                                 and x["mb"]["target_tokens"] is not None
                                                 and x["reached_tokens"] >= x["mb"]["target_tokens"])),
               "without a count": str(sum(1 for x in rows if x["reached_tokens"] is None))}
        want = dict(zip(got, [*mp.groups(), *ma.groups(), *mr.groups()[:2], ma2.group(1), mr.group(3)]))
        if got != want:
            raise SystemExit(f"reproduce G2 FAILED, nothing written: g2_check printed {want}, these records give {got}")
        counts = got
    stale = None
    if all(shas[s] == sha for s, sha in G2_STALE_KNOWN["files"].items()):
        want = sorted(f"exp_v4_s20_n0|matched_budget|{q}|d{dr}" for q in G2_STALE_KNOWN["questions"] for dr in DRAWS)
        got = sorted(x["key"] for x in g2_from)
        if got != want:
            raise SystemExit(f"reproduce G2 FAILED, nothing written: the answers planned from an old target are "
                             f"{len(got)} ({sorted({x['q'] for x in g2_from})}), experiments/NOW.md:29 names "
                             f"{len(want)} ({G2_STALE_KNOWN['questions']})")
        stale = len(got)
    print(f"reproduce: G2, {len(under)} answers read with the plan's top_k and the reached tokens g2_check read"
          + (f"; g2_check's COUNTS lines regenerated ({', '.join(f'{k} {v}' for k, v in counts.items())})"
             if counts else "; COUNTS not compared (answers stored after g2_check read them)")
          + (f"; the {stale} answers planned from an old target are those NOW.md:29 names" if stale is not None
             else "; the old-target list not compared (files changed since NOW.md:29)"))
    return {"answers_compared": len(under), "plan_sha256": plan_sha, "counts": counts,
            "old_target_answers_compared": stale}


# ---------------------------------------------------------------------------------------------------------------
# numbers
# ---------------------------------------------------------------------------------------------------------------
def boot_matrix(n):
    import numpy as np
    return np.random.default_rng(BOOT_SEED).integers(0, n, size=(N_BOOT, n))


def per_question(rows, field):
    """{question: mean over its draws of field}, None when a draw lacks it."""
    by = defaultdict(list)
    for x in rows:
        by[x["q"]].append(x[field])
    return {q: (None if any(v is None for v in vs) else sum(vs) / len(vs)) for q, vs in by.items()}


def summary(values):
    """Mean and median over the questions, each with Rule 2's 95% percentile interval (10,000 question resamples)."""
    import numpy as np
    v = np.array(values, dtype=float)
    B = v[boot_matrix(len(v))]
    means, meds = B.mean(axis=1), np.median(B, axis=1)
    return {"questions_n": len(v), "mean": float(v.mean()), "mean_lo": float(np.percentile(means, 2.5)),
            "mean_hi": float(np.percentile(means, 97.5)), "median": float(np.median(v)),
            "median_lo": float(np.percentile(meds, 2.5)), "median_hi": float(np.percentile(meds, 97.5)),
            "quartile_25": float(np.percentile(v, 25)), "quartile_75": float(np.percentile(v, 75))}


OUTCOME_ROWS = [  # (row label as printed, how it is counted, value, family); a line is drawn between families
    ("ok", "stop", "ok", 0), ("blocked", "stop", "blocked", 0), ("error", "stop", "error", 0),
    ("final_answer", "stop", "final_answer", 1), ("closing_final_answer", "stop", "closing_final_answer", 1),
    ("no_protocol", "stop", "no_protocol", 1), ("closing_no_protocol", "stop", "closing_no_protocol", 1),
    ("final", "stop", "final", 2), ("max_turns_partial", "stop", "max_turns_partial", 2),
    ("max_turns_empty", "stop", "max_turns_empty", 2), ("call_error", "stop", "call_error", 2),
    ("answer_ready", "stop", "answer_ready", 3), ("turn_cap", "stop", "turn_cap", 3),
    ("root_call_failed", "stop", "root_call_failed", 3),
    ("no answer text", "empty", None, 4),
    ("verifier ok", "verifier", "ok", 5), ("verifier empty", "verifier", "empty", 5),
    ("verifier length", "verifier", "length", 5), ("verifier unparsed", "verifier", "unparsed", 5),
    ("verifier error", "verifier", "error", 5)]


def outcome_count(data, vrep, setup, kind, val):
    if kind == "stop":
        return sum(1 for x in data[setup] if x["stop"] == val)
    if kind == "empty":
        return sum(1 for x in data[setup] if not x["answer"].strip())
    return vrep["status_counts"].get(val, 0) if setup == "verified_pass" else 0


def vp_wait_summary(vp, others):
    """Verified pass: the wait for the one local server before a verifier call (inside clock time, outside the call's
    wall_s), over its answers; and, per other Mentori set-up, its calls that waited at all. The selftest checks it on
    synthetic rows."""
    waits = [w for x in vp for w in x["waits"]]
    mean_clock = sum(x["clock"] for x in vp) / len(vp)
    mean_wait = sum(x["wait"] for x in vp) / len(vp)
    return {"calls_with_a_wait_record": len(waits), "calls_waiting_over_10_s": sum(1 for w in waits if w > 10),
            "longest_wait_s": max(waits), "mean_wait_per_answer_s": mean_wait,
            "mean_clock_per_answer_s": mean_clock, "wait_share_of_mean_clock": mean_wait / mean_clock,
            "mean_local_model_call_s_per_answer": sum(x["model_local"] for x in vp) / len(vp),
            "mean_api_model_call_s_per_answer": sum(x["model_api"] for x in vp) / len(vp),
            "other_exp01_calls_with_a_wait_over_0_s": {s: sum(1 for x in rows for w in x["waits"] if w > 0)
                                                       for s, rows in others.items()}}


A_GROUPS = [("answered", ("ok", "final_answer", "no_protocol", "final", "answer_ready")),
            ("answered by the closing call", ("closing_final_answer", "closing_no_protocol", "turn_cap")),
            ("cap reached, partial answer kept", ("max_turns_partial",)),
            ("cap reached, no answer", ("max_turns_empty",)),
            ("failed or blocked", ("blocked", "error", "root_call_failed", "call_error"))]
A_GROUP_STYLE = {"answered": ("#0072B2", ""), "answered by the closing call": ("#56B4E9", "."),
                 "cap reached, partial answer kept": ("#CC79A7", "-"), "cap reached, no answer": ("#F0E442", "z"),
                 "failed or blocked": ("#D55E00", "\\")}


def plate_label(setup):
    """A set-up's name on this plate and in its sheets: Mentori's three RLM rows read Mentori RLM-n beside Zhang RLM-n
    (Valerio, 2 November: one name for each). G1, S463 and the numbers files keep their short labels."""
    import figure_names as FN
    return FN.MENTORI_RLM_N.format(n=CAP[setup]) if LABEL[setup] in (FN.RLM_5, FN.RLM_10, FN.RLM_20) else LABEL[setup]


def a_groups(fn):
    """Per set-up the answers of each plain kind (sums of sheet a's stop-reason rows), the answers with no text and the
    verifier's statuses, as rows of the added sheet 'groups'. Refuses a stop reason no kind names, or a set-up whose
    kinds do not add to its answers."""
    rows = []
    for setup, lab in SETUPS:
        mine = [r for r in fn["a"] if r["setup"] == setup]
        stops = [r for r in mine if r["field"] in ("generation.stop_reason", "stop_reason")]
        named = {c for _, cs in A_GROUPS for c in cs}
        bad = [r["outcome"] for r in stops if r["outcome"] not in named]
        if bad:
            raise SystemExit(f"a groups: {setup} stop reasons {bad} have no plain kind")
        tot = 0
        for g, cs in A_GROUPS:
            k = sum(r["answers_n"] for r in stops if r["outcome"] in cs)
            tot += k
            rows.append({"setup": setup, "setup_label": lab, "kind": g, "stop_reasons": "; ".join(
                r["outcome"] for r in stops if r["outcome"] in cs), "answers_n": k, "of_answers": mine[0]["of_answers"]})
        if tot != mine[0]["of_answers"]:
            raise SystemExit(f"a groups: {setup} kinds add to {tot}, not {mine[0]['of_answers']}")
        nt = sum(r["answers_n"] for r in mine if r["outcome"] == "no answer text")
        rows.append({"setup": setup, "setup_label": lab, "kind": "no answer text (any ending)",
                     "stop_reasons": "answer text empty", "answers_n": nt, "of_answers": mine[0]["of_answers"]})
        for r in mine:
            if r["outcome"].startswith("verifier"):
                rows.append({"setup": setup, "setup_label": lab, "kind": r["outcome"], "stop_reasons": r["field"],
                             "answers_n": r["answers_n"], "of_answers": r["of_answers"]})
    return rows


# the split of panel a's last two columns (M05, O04; AR:386): on the out-of-scope questions, the answers the judge scored as
# refused, of the answers cut at the turn limit and of the others. The stop reasons that mean "cut" per set-up: RLM-5's
# cap, and multi-hop's closing turn, whose answer then comes from that turn (experiments/runner/check_retrieval.py:614).
CUT_STOPS = {"rlm_5": ("max_turns_partial", "max_turns_empty"), "multi_hop": ("closing_final_answer", "closing_no_protocol")}
G1_COLLECT = ROOT / "findings" / "recompute" / "fig2_inputs" / "g1_collect.jsonl"
REFUSED_AT = 3                                 # Rule 9 (experiments/LIST.md:364): refusal accuracy 3 or more
CUT_SPLIT_WANT = {("rlm_5", "cut at limit"): (33, 63), ("rlm_5", "not cut"): (49, 54),
                  ("multi_hop", "cut at limit"): (103, 116), ("multi_hop", "not cut"): (0, 1)}   # counted 1 November


def cut_split(data, collect):
    """Per set-up of CUT_STOPS: of its answers to the questions G1's judge rows mark out of scope (answerable_prompt
    false), the answers cut at the limit and the others, and how many of each the judge scored as refused (refusal
    accuracy REFUSED_AT or more). An answer with no judge row counts as not refused (Rule 10). Refuses a doubled row or
    a count other than the gate's."""
    rows = {}
    for r in collect:
        if r["config"] in CUT_STOPS and r.get("answerable_prompt") is False:
            if r["answer_key"] in rows:
                raise SystemExit(f"cut_split: two judge rows for {r['answer_key']}")
            rows[r["answer_key"]] = r
    out_of_scope = {r["question_id"] for r in rows.values()}
    out = []
    for setup, stops in CUT_STOPS.items():
        answers = [x for x in data[setup] if x["q"] in out_of_scope]
        for cut, keep in (("cut at limit", lambda x: x["stop"] in stops), ("not cut", lambda x: x["stop"] not in stops)):
            mine = [x for x in answers if keep(x)]
            refused = 0
            for x in mine:
                row = rows.get(x["key"])
                v = ((row or {}).get("a") or {}).get("scores", {}).get("refusal_accuracy")
                refused += v is not None and v >= REFUSED_AT
            out.append({"row": "cut_split", "setup": setup, "setup_label": LABEL[setup], "cut": cut,
                        "refused_n": refused, "answers_n": len(mine),
                        "stop_reasons": "; ".join(f"{k} {n}" for k, n in sorted(Counter(x["stop"] for x in mine).items())),
                        "questions_n": len(out_of_scope)})
    got = {(r["setup"], r["cut"]): (r["refused_n"], r["answers_n"]) for r in out}
    if got != CUT_SPLIT_WANT:
        raise SystemExit(f"cut_split: {got}, the gate holds {CUT_SPLIT_WANT}; nothing written")
    return out


def compute(data, qtype, affected, collect=None):
    vrep = verifier_report_fn()([x["raw"] for x in data["verified_pass"]])
    stops = {s: Counter(x["stop"] for x in rows) for s, rows in data.items()}
    known = {v for _, k, v, _ in OUTCOME_ROWS if k == "stop"}
    unknown = {s: sorted(set(c) - known) for s, c in stops.items() if set(c) - known}
    if unknown:
        raise SystemExit(f"stop reasons with no row in panel a: {unknown}; add them to OUTCOME_ROWS")
    vknown = {v for _, k, v, _ in OUTCOME_ROWS if k == "verifier"}
    if set(vrep["status_counts"]) - vknown:
        raise SystemExit(f"verifier statuses with no row in panel a: {sorted(set(vrep['status_counts']) - vknown)}")
    # the rows drawn: those at least one set-up has an answer in, in OUTCOME_ROWS's order
    drawn = [r for r in OUTCOME_ROWS if any(outcome_count(data, vrep, s, r[1], r[2]) for s, _ in SETUPS)]
    a = []
    for j, (setup, lab) in enumerate(SETUPS):
        for i, (row, kind, val, fam) in enumerate(drawn):
            n = outcome_count(data, vrep, setup, kind, val)
            if n:
                a.append({"setup": setup, "setup_label": lab, "column": j, "outcome": row, "outcome_row": i,
                          "field": {"stop": "generation.stop_reason" if setup in dict(EXP01) else "stop_reason",
                                    "empty": "answer text empty", "verifier": "generation.verification.status "
                                    "(verifier_status_report)"}[kind],
                          "answers_n": n, "of_answers": len(data[setup]), "s455_listed_answers": None})
    for setup, _ in SETUPS:              # the set-up's first row carries how many of its answers S455 named
        next(r for r in a if r["setup"] == setup)["s455_listed_answers"] = len(affected.get(setup, ()))
    # Q117 panels: per question the mean over draws; per set-up mean and median with Rule 2's interval
    panels = {}
    for letter, field, unit in (("b", "tokens", "tokens"), ("c", "clock_less_wait", "s"), ("d", "model", "s")):
        rows_out, summ = [], {}
        for setup, lab in SETUPS:
            if field == "model" and setup not in dict(EXP01):
                continue
            pq = per_question(data[setup], field)
            extra = {f"{f}_tokens": per_question(data[setup], f) for f in ("prompt", "output", "thinking")} \
                if letter == "b" else {}
            extra_sum = {}
            if letter == "c":                 # the clock time with the wait, and the wait (D95 Q200; F1 of 18 Oct)
                extra = {"clock": per_question(data[setup], "clock")}
                if setup in dict(EXP01):
                    extra["server_wait_s"] = per_question(data[setup], "wait")
                extra_sum = {"clock_with_wait_mean": extra["clock"]}
            if letter == "d":                 # local (the verifier) and API (Gemini) calls apart; the calls counted
                extra = {"local_model_call_s": per_question(data[setup], "model_local"),
                         "api_model_call_s": per_question(data[setup], "model_api"),
                         "model_calls": per_question(data[setup], "calls_n")}
                extra_sum = {"model_calls_mean": extra["model_calls"]}
            for q in sorted(pq):
                r = {"setup": setup, "setup_label": lab, "row": "question", "question_id": q,
                     "answer_type": qtype[q], "draws_n": len(DRAWS), f"{field}_mean_over_draws": pq[q]}
                for f, d in extra.items():
                    r[f"{f}_mean_over_draws"] = d[q]
                rows_out.append(r)
            sm = summary([pq[q] for q in sorted(pq)])
            for k_, d in extra_sum.items():       # a mean over the questions of another per-question value
                sm[k_] = sum(d[q] for q in sorted(d)) / len(d)
            summ[setup] = sm
            rows_out.append({"setup": setup, "setup_label": lab, "row": "set-up", **sm, "resamples": N_BOOT,
                             "resample_seed": BOOT_SEED})
        r10 = summ["rlm_10"]["mean"] / summ["single_pass"]["mean"]
        cols = []
        for r in rows_out:
            for c in r:
                if c not in cols:
                    cols.append(c)
        cols.append("ratio_of_means_rlm_10_to_single_pass")
        for r in rows_out:
            r["ratio_of_means_rlm_10_to_single_pass"] = r10 if (r["row"] == "set-up" and r["setup"] == "rlm_10") \
                else None
        panels[letter] = {"rows": [{c: r.get(c) for c in cols} for r in rows_out], "summary": summ, "ratio": r10,
                          "unit": unit}
    e = []
    for setup, lab in SETUPS:
        if setup not in CAP:
            continue
        c = Counter(x["turns"] for x in data[setup])
        for t in sorted(k for k in c if k is not None):
            e.append({"setup": setup, "setup_label": lab, "cap": CAP[setup], "turns_used": t, "answers_n": c[t],
                      "of_answers": len(data[setup]), "share_pct": 100 * c[t] / len(data[setup])})
        if c.get(None):
            e.append({"setup": setup, "setup_label": lab, "cap": CAP[setup], "turns_used": None,
                      "answers_n": c[None], "of_answers": len(data[setup]), "share_pct": 100 * c[None] / len(data[setup])})
    e_max = max(r["answers_n"] for r in e if r["turns_used"] is not None)
    for r in e:                                  # the cell's colour: cividis, log of the answers, many answers yellow
        r["colour_index_of_256"] = colour_index(r["answers_n"], e_max) if r["turns_used"] is not None else None
        r["colour_hex"] = cividis_up()[r["colour_index_of_256"]] if r["turns_used"] is not None else None
    # f: verified pass, its clock time with the wait and the wait for the one local verifier server, per question
    vp = data["verified_pass"]
    f_rows, f_summ = [], {}
    for part, field in (("clock time", "clock"), ("waiting for the verifier server", "wait")):
        pq = per_question(vp, field)
        for q in sorted(pq):
            f_rows.append({"setup": "verified_pass", "part": part, "row": "question", "question_id": q,
                           "answer_type": qtype[q], "draws_n": len(DRAWS), "s_mean_over_draws": pq[q]})
        sm = summary([pq[q] for q in sorted(pq)])
        f_summ[part] = sm
        f_rows.append({"setup": "verified_pass", "part": part, "row": "set-up", **sm, "resamples": N_BOOT,
                       "resample_seed": BOOT_SEED})
    fcols = []
    for r in f_rows:
        for c in r:
            if c not in fcols:
                fcols.append(c)
    f_panel = {"rows": [{c: r.get(c) for c in fcols} for r in f_rows], "summary": f_summ, "unit": "s"}
    vp_wait = vp_wait_summary(vp, {s: data[s] for s, _ in EXP01 if s != "verified_pass"})
    if abs(vp_wait["mean_wait_per_answer_s"] - f_summ["waiting for the verifier server"]["mean"]) > 1e-6:
        raise SystemExit("the verifier wait per answer and f's mean over the questions differ")     # 3 draws each
    f_less = f_summ["clock time"]["mean"] - f_summ["waiting for the verifier server"]["mean"]
    if abs(panels["c"]["summary"]["verified_pass"]["mean"] - f_less) > 1e-6:
        raise SystemExit("c's verified pass is not f's clock time less f's wait")
    # the authors' RLM: per-call times exist (calls.jsonl), but sub-calls overlap; processes and answers in flight
    spans = [(x["span"][0], x["span"][1]) for c, _ in G6 for x in data[c]]
    ev = sorted([(s0, 1) for s0, _ in spans] + [(s1, -1) for _, s1 in spans])
    cur = g6_in_flight = 0
    for _, dlt in ev:
        cur += dlt
        g6_in_flight = max(g6_in_flight, cur)
    g6_time = {"answers_whose_summed_call_time_exceeds_clock": {c: sum(1 for x in data[c] if x["calls_wall_sum"]
                                                                       > x["clock"]) for c, _ in G6},
               "processes": {c: len({x["pid"] for x in data[c]}) for c, _ in G6},
               "answers_per_process": {c: dict(Counter(x["pid"] for x in data[c])) for c, _ in G6},
               "most_answers_in_flight_across_the_three_caps": g6_in_flight,
               "how": "an answer spans from its first call's 'at' (stamped by gemini_client._record before the call "
                      "is sent) to its last call's 'at' plus that call's wall_s; 'at' is to the second"}
    g6_empty_ok = {c: dict(Counter(x["stop"] for x in data[c] if x["status"] == "ok" and not x["answer"].strip()))
                   for c, _ in G6}
    g6_missing = {s: sum(1 for x in data[s] if x["tokens_missing"]) for s, _ in G6}
    g1_no_tokens = {s: sum(1 for x in data[s] if x["tokens_missing"]) for s, _ in EXP01}
    pools = {s: sorted({x["pool"] for x in data[s]}) for s, _ in EXP01}
    no_wall = {s: sum(x["model_calls_no_wall"] for x in data[s]) for s, _ in EXP01}
    vp_unverified = sum(1 for x in data["verified_pass"] if (x["verification"] or {}).get("counts", {})
                        .get("UNVERIFIED", 0) > 0)
    out = {"a": a, "a_rows": drawn, "b": panels["b"], "c": panels["c"], "d": panels["d"], "e": e, "e_max": e_max,
            "f": f_panel, "vrep": vrep, "stops": stops, "g6_tokens_missing": g6_missing,
            "g1_calls_without_tokens": g1_no_tokens, "pools": pools, "g1_calls_without_wall": no_wall,
            "tokens_missing_answers": {s: sum(1 for x in data[s] if x["tokens_missing"]) for s, _ in SETUPS},
            "vp_some_passage_unverified": vp_unverified, "vp_wait": vp_wait, "g6_time": g6_time,
            "g6_empty_ok": g6_empty_ok}
    out["a_groups"] = a_groups(out) if collect is not None else []     # the plate's a; the selftest's rows have none
    out["a_split"] = cut_split(data, collect) if collect is not None else []
    return out


def g1_commits(data, man):
    """{set-up: {commit: answers}} for G1 and G2: each stored answer's process id matched to the commit its process
    ran (records_manifest.json, written by mirror from the Studio's start records)."""
    out = {}
    for s, _ in EXP01:
        by_pid = {p["pid"]: p["commit"] for p in man["exp01"][s].get("processes", [])}
        clash = sorted(set(G13_PROCESSES.get(s, {})) & set(by_pid))
        if clash:      # a G13 pid equal to a G2 manifest pid would relabel G2's answers with G13's commit
            raise SystemExit(f"{s}: G13 process id(s) {clash} also in the manifest's processes")
        by_pid.update(G13_PROCESSES.get(s, {}))           # merge_g13: G13's process, its start record not copied here
        if not by_pid:
            raise SystemExit(f"the manifest has no processes for {s}: run mirror again")
        miss = {x["pid"] for x in data[s]} - set(by_pid)
        if miss:
            raise SystemExit(f"{s}: answers from process(es) {sorted(miss)} that no start record matches")
        out[s] = dict(Counter(by_pid[x["pid"]] for x in data[s]))
    return out


# ---------------------------------------------------------------------------------------------------------------
# the plate
# ---------------------------------------------------------------------------------------------------------------
import tomllib  # noqa: E402

FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
PT = float(FLOCK["type"]["font_min_pt"])
PT_LETTER = float(FLOCK["type"]["panel_letter_pt"])
LETTER_WEIGHT = FLOCK["type"]["panel_letter_weight"]
LETTER_CASE = str.lower if FLOCK["type"]["panel_letter_case"] == "lowercase" else str.upper
FONT = FLOCK["type"]["font_families"][0]
LINE_MIN_PT = float(FLOCK["lines"]["line_min_pt"])
FIG_W_MM = float(FLOCK["page"]["width_double_mm"])
FIG_H_MAX_MM = float(FLOCK["page"]["height_max_mm"])
CONTRAST_MIN = float(FLOCK["type"]["contrast_min_ratio"])
_CAT = [c.upper() for c in FLOCK["colour"]["categorical"]]
OKABE = dict(zip(["black", "orange", "sky blue", "bluish green", "yellow", "blue", "vermillion", "reddish purple"],
                 _CAT))
DOT_GREY = "#8C8C8C"                     # S447's grey for data dots (3.4:1 on white, not faint)
MM_PT = 25.4 / 72
DOT_MM, DOT_PITCH_MM, DOT_HALF_MM = 0.45, 0.50, 2.00
BOX_HALF_MM = 1.20                       # the quartile box's half height around the row's centre
MEAN_OFF_MM = 2.55                       # the mean and its interval, below the row's dots


def _cividis_r():
    """The 256 entries of [colour] continuous (cividis), reversed so few answers are light and many are dark, as
    hex strings from matplotlib's own table (S448 R5 checks every colour against that table)."""
    from matplotlib import colormaps
    cm = colormaps[FLOCK["colour"]["continuous"]]
    return [("#%02X%02X%02X" % tuple(round(255 * v) for v in cm(255 - i)[:3])) for i in range(256)]


def cividis_up():
    """The 256 entries with few answers dark and many answers yellow (D171 (1); supp.md C8)."""
    return list(reversed(CIVIDIS_R))


def colour_index(n, n_max):
    """A count from 1 to n_max on a log scale, as an entry of the 256 (0 for 1 answer, 255 for n_max)."""
    import math
    return int(round(255 * math.log(n) / math.log(n_max))) if n_max > 1 else 255


CIVIDIS_R = None
H_ROOM_MM = 0.05


def figure_lock_agreed():
    if FLOCK.get("status") != "agreed":
        raise SystemExit(f"{FIGURE_LOCK.relative_to(ROOT)} has status {FLOCK.get('status')!r}, not 'agreed' (D87)")


def naming(kind, n):
    """The plate's names (D95 Q208: drawable as main or Supplementary, the name a parameter), from FIGURE_LOCK [files]
    name or supplementary_name and [source_data] workbook_name, as S448 finds them: the plate, the data workbook's
    stem, a sheet's name per panel letter, the numbers and provenance files' stem, the folder and its manifest."""
    if kind not in ("supplementary", "main") or not isinstance(n, int) or n < 1:
        raise SystemExit(f"--as {kind!r} --n {n!r}: want --as supplementary or main and a figure number")
    supp = kind == "supplementary"
    if not supp and n == 2:
        raise SystemExit("main 'Figure 2' is S531's plate (findings/figures_provisional/fig2_human/), and S463's plate "
                         "is main Figure 3 (D95 Q200: findings/figures_provisional/fig3_strategies/); "
                         "this plate is drawn as a Supplementary figure or as another main figure number")
    plate = FLOCK["files"]["supplementary_name" if supp else "name"].format(n=n)
    stem = f"{plate} data" if supp else re.sub(r"\.[A-Za-z0-9]+$", "",
                                               FLOCK["source_data"]["workbook_name"].format(n=n))
    out = FIGURES / ((DEFAULT_FOLDER if n == DEFAULT_N else f"supp_fig{n}") if supp else f"fig{n}")
    for p in sorted(out.glob("*_provenance.json")) if out.exists() else []:   # never another script's folder
        try:
            j = json.loads(p.read_text())
            other = (j.get("provenance") or {}).get("script") or j.get("script")
        except ValueError:
            other = None
        if other != SCRIPT:
            raise SystemExit(f"{out.relative_to(ROOT)} holds {p.name}, written by {other!r}, not {SCRIPT}: pick "
                             f"another --n")
    return {"kind": kind, "n": n, "supp": supp, "plate": plate, "stem": stem,
            "sheet_prefix": f"{'Supplementary ' if supp else ''}Fig. {n}",
            "side": f"{'supplementary_' if supp else ''}figure{n}", "out": out,
            "manifest": out / "records_manifest.json"}


def wcag(c1, c2):
    def lum(c):
        c = tuple(int(c.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def half_up(x, nd=0):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return f"{abs(q) if q == 0 else q:.{nd}f}"


def swarm(xs_mm, half=DOT_HALF_MM, pitch=DOT_PITCH_MM, dot=DOT_MM):
    """Offsets (mm, across the row) for dots at exact positions xs_mm: each dot in value order takes the slot nearest
    the row's centre (0, +pitch, -pitch, ...) within +-half where no placed dot lies closer than dot + 0.05 mm; a dot
    with no free slot takes the slot farthest from its neighbours and overlaps. Returns (offsets, overlapping)."""
    import math
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


def plate_rc(salt="S457"):
    """matplotlib's settings for a plate under FIGURE_LOCK.toml: [type] font and size, [lines] line_min_pt (axes and
    ticks at least 0.5 pt), black text and axes, fonts kept as text (SVG) and embedded as TrueType (PDF, type 42).
    Shared with S463 (Figure 3's ranking), so both plates are drawn alike."""
    lw = max(0.5, LINE_MIN_PT)
    return {"font.family": FONT, "font.size": PT, "svg.fonttype": "none", "pdf.fonttype": 42,
            "axes.linewidth": lw, "xtick.major.width": lw, "ytick.major.width": lw,
            "xtick.minor.width": lw, "ytick.minor.width": lw,
            "xtick.major.size": 2, "ytick.major.size": 2, "xtick.minor.size": 1.2,
            "xtick.labelsize": PT, "ytick.labelsize": PT, "axes.labelsize": PT,
            "axes.edgecolor": "#000000", "xtick.color": "#000000", "ytick.color": "#000000",
            "text.color": "#000000", "axes.labelcolor": "#000000", "svg.hashsalt": salt}


def text_outline(t, rend, fig):
    """A text's outline in mm (D224 Q3): its window extent when its angle is a multiple of 90 degrees (the box the
    test always used), else its unrotated box turned by its angle about the centre of its window extent (the centre
    of a turned rectangle is the centre of its upright bounding box)."""
    import math
    bb = t.get_window_extent(rend)
    k = 25.4 / fig.dpi
    r = t.get_rotation()
    if r % 90 == 0:
        return [(bb.x0 * k, bb.y0 * k), (bb.x1 * k, bb.y0 * k), (bb.x1 * k, bb.y1 * k), (bb.x0 * k, bb.y1 * k)]
    cx, cy = (bb.x0 + bb.x1) / 2 * k, (bb.y0 + bb.y1) / 2 * k
    t.set_rotation(0)
    b0 = t.get_window_extent(rend)
    t.set_rotation(r)
    w, h = b0.width * k, b0.height * k
    c, s_ = math.cos(math.radians(r)), math.sin(math.radians(r))
    return [(cx + dx * c - dy * s_, cy + dx * s_ + dy * c) for dx, dy in
            ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def outlines_overlap(p, q, pad=0.05):
    """Separating-axis test on two convex outlines: True when they overlap by more than pad along every edge normal
    of both. For two upright boxes it is the box test finish_plate used before D224 Q3: overlap by more than pad in
    x and in y."""
    import math
    for poly in (p, q):
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            nx, ny = y1 - y2, x2 - x1
            L = math.hypot(nx, ny) or 1.0
            pa = [(x * nx + y * ny) / L for x, y in p]
            qa = [(x * nx + y * ny) / L for x, y in q]
            if max(pa) <= min(qa) + pad or max(qa) <= min(pa) + pad:
                return False
    return True


def finish_plate(fig, W, H, paths, title="Figure 2"):
    """The last step of a plate (shared with S463): ligatures off; every text inside the page and none on another
    (else no plate is written); the PDF and the SVG saved with no date or creator in them; the PNG the PDF rasterised
    at 600 dpi by MuPDF, so S448 R7 can compare them pixel by pixel. Texts are compared by their outlines
    (text_outline, outlines_overlap; D224 Q3): a text turned by an angle that is not a multiple of 90 degrees is
    measured by its turned box, so two 45-degree labels whose upright boxes intersect but whose letters are apart pass;
    every other text is measured by its upright box, as before."""
    import matplotlib.pyplot as plt
    from matplotlib.text import Text
    for t_ in fig.findobj(Text):
        t_.set_fontfeatures(["-liga"])
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    off_page, crowded = [], []
    boxes = []
    for t_ in fig.findobj(Text):
        if t_.get_visible() and t_.get_text().strip():
            bb = t_.get_window_extent(rend)
            x0_, x1_ = bb.x0 / fig.dpi * 25.4, bb.x1 / fig.dpi * 25.4
            y0_, y1_ = H - bb.y1 / fig.dpi * 25.4, H - bb.y0 / fig.dpi * 25.4
            if x0_ < -0.01 or y0_ < -0.01 or x1_ > W + 0.01 or y1_ > H + 0.01:
                off_page.append(f"{t_.get_text()!r} x {x0_:.1f}-{x1_:.1f} y {y0_:.1f}-{y1_:.1f}")
            boxes.append((t_.get_text(), text_outline(t_, rend, fig)))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if outlines_overlap(a[1], b[1], 0.05):
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


def dot_row(ax, vals_mm, vals, s, y, pitch, overlaps, key):
    """One row of b, c, d or f: a grey dot per question (placed apart across the row), the quartile box with the
    median line over them, and below them the mean with Rule 2's interval in blue (S447's marks, shared with S463)."""
    off, over = swarm(vals_mm)
    overlaps[key] = over
    ax.plot(vals, [y - o / pitch for o in off], ls="none", marker="o", ms=DOT_MM / MM_PT, mfc=DOT_GREY, mew=0,
            zorder=2)
    hb = BOX_HALF_MM / pitch
    ax.plot([s["quartile_25"], s["quartile_75"], s["quartile_75"], s["quartile_25"], s["quartile_25"]],
            [y - hb, y - hb, y + hb, y + hb, y - hb], color="#000000", lw=0.5, solid_joinstyle="miter", zorder=5)
    ax.plot([s["median"], s["median"]], [y - hb, y + hb], color="#000000", lw=1.0, solid_capstyle="butt", zorder=5)
    yb = y + MEAN_OFF_MM / pitch
    ax.plot([s["mean_lo"], s["mean_hi"]], [yb, yb], color=OKABE["blue"], lw=0.9, solid_capstyle="butt", zorder=3)
    ax.plot([s["mean"]], [yb], ls="none", marker="o", ms=1.5 / MM_PT, mfc=OKABE["blue"], mew=0, zorder=4)


def draw_plate(fn, paths, nm):
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import math
    import house_style as hs
    hs.apply_rc("S457")
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.transforms import blended_transform_factory

    W = FIG_W_MM
    sheet = lambda L: f"{nm['sheet_prefix']}{L}"
    printed = {}

    def num(artist, entry):
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = entry
        return artist

    ROWPOS = [0, 1, 2, 3, 4, 5, 6.5, 8, 9, 10]          # G1 rows, a half-row gap, G2, a gap, then G6
    B_LIM = (-0.6, ROWPOS[-1] + 0.7)
    A_KEY_Y = 1.5 + hs.PT * hs.MM_PT
    A_TOP, A_PITCH = A_KEY_Y + 3.7 + 4.6, 3.0
    A_BOT = A_TOP + (B_LIM[1] - B_LIM[0]) * A_PITCH + 8.0      # x axis and its label
    E_POS = [0, 1, 2, 3.5, 4.5, 5.5]
    E_PITCH, E_LIM = 3.3, (-0.6, 6.1)
    E_H = (E_LIM[1] - E_LIM[0]) * E_PITCH
    E_KEY = 7.8                                           # e's key band above its axes: the colour bar; the legend says what the black outline marks (Valerio, 2 November)
    F_LIM = (-0.6, 1.7)
    B_GAP, BE_GAP = 7.0, 10.0

    def bottom(p):
        return max(E_KEY + E_H + 8.5, (F_LIM[1] - F_LIM[0]) * p + 8.0)
    B_PITCH = 5.5
    while A_BOT + B_GAP + (B_LIM[1] - B_LIM[0]) * B_PITCH + BE_GAP + bottom(B_PITCH) > FIG_H_MAX_MM - H_ROOM_MM \
            and B_PITCH > 4.0:
        B_PITCH = round(B_PITCH - 0.05, 2)
    B_TOP = A_BOT + B_GAP
    B_BOT = B_TOP + (B_LIM[1] - B_LIM[0]) * B_PITCH
    E_BAND = B_BOT + BE_GAP                               # top of e's key band (and of f's axes)
    E_TOP = E_BAND + E_KEY
    E_BOT = E_TOP + E_H
    H = round(E_BAND + bottom(B_PITCH), 1)
    if H > FIG_H_MAX_MM - H_ROOM_MM:
        raise SystemExit(f"{nm['plate']} is {H} mm high at a row pitch of {B_PITCH} mm, over the lock's "
                         f"{FIG_H_MAX_MM} mm")
    fig = hs.figure(W, H)

    # ---- a: stacked bars of the endings other than a plain answer; right, the number columns
    groups = fn["a_groups"]
    gsheet = f"{nm['sheet_prefix']} groups"
    asheet = sheet("a")
    gi = {(r["setup"], r["kind"]): i for i, r in enumerate(groups)}
    LAB, COLS_X = 29.0, 112.0
    colw = (W - 3.0 - COLS_X) / 4                 # each number column at the right
    kinds = [g for g, _ in A_GROUPS[1:]]          # the endings other than a plain answer, stacked
    AW = COLS_X - 4.0 - LAB
    axa = hs.axes_mm(fig, LAB, A_TOP, AW, (B_LIM[1] - B_LIM[0]) * A_PITCH)
    axa.set_ylim(B_LIM[1], B_LIM[0])
    other = [sum(groups[gi[(s, g)]]["answers_n"] for g in kinds) for s, _ in SETUPS]
    xmax = 25 * math.ceil(max(other) / 25 + 1e-9)
    axa.set_xlim(0, xmax)
    axa.set_xticks(list(range(0, xmax + 1, 25)))
    axa.set_xticklabels([f"{t:,}" for t in range(0, xmax + 1, 25)])
    axa.set_xlabel(hs.axis_label("answers that did not end in a plain answer", "n"), labelpad=2)
    axa.set_yticks(ROWPOS)
    axa.set_yticklabels([plate_label(s) for s, _ in SETUPS])
    axa.tick_params(axis="y", length=0, pad=2)
    for j, (s, _) in enumerate(SETUPS):
        segs = [groups[gi[(s, g)]]["answers_n"] for g in kinds]
        hs.bar(axa, ROWPOS[j], segs, [A_GROUP_STYLE[g][0] for g in kinds], orient="h", slot=1.0,
               patterns=[A_GROUP_STYLE[g][1] for g in kinds])
    # the number columns: plain answers and answers with no text, of the set-up's 405, then the split on the
    # out-of-scope questions (RLM-5 and multi-hop only, blank on the other rows)
    tr = blended_transform_factory(fig.transFigure, axa.transData)
    head_y = 1 - (A_TOP - 1.2) / H

    def xcol(c):
        return (COLS_X + colw * (c + 0.5)) / W
    for c, (head, kind) in enumerate((("answered", "answered"), ("no text", "no answer text (any ending)"))):
        fig.text(xcol(c), head_y, head, ha="center", va="baseline")
        for j, (s, _) in enumerate(SETUPS):
            i = gi[(s, kind)]
            t = fig.text(xcol(c), ROWPOS[j], f"{groups[i]['answers_n']}", transform=tr, ha="center", va="center")
            num(t, {"sheet": gsheet, "row": i, "format": "{answers_n}"})
    xs_ = (xcol(2) + xcol(3)) / 2
    fig.text(xs_, 1 - (A_TOP - 1.2 - 2 * 3.4) / H, "Refused, out-of-scope", ha="center", va="baseline")
    fig.text(xs_, 1 - (A_TOP - 1.2 - 3.4) / H, "questions", ha="center", va="baseline")
    n_a = len(fn["a"])
    for c, cut in ((2, "cut at limit"), (3, "not cut")):
        fig.text(xcol(c), head_y, cut, ha="center", va="baseline")
        for j, (s, _) in enumerate(SETUPS):
            hit = [i for i, r in enumerate(fn["a_split"]) if r["setup"] == s and r["cut"] == cut]
            if hit:
                r = fn["a_split"][hit[0]]
                t = fig.text(xcol(c), ROWPOS[j], f"{r['refused_n']} of {r['answers_n']}", transform=tr, ha="center",
                             va="center")
                num(t, {"sheet": asheet, "row": n_a + hit[0], "format": "{refused_n} of {answers_n}"})
    hs.panel_letter(fig, 0.4, A_KEY_Y, "a")
    # the key, left-aligned on the bars' axis (Valerio, 2 November): one hs.key per line, each centred on its own middle
    key_rows, cur, cur_w = [], [], 0.0
    for g in kinds:
        it = ("swatch", (A_GROUP_STYLE[g][0], A_GROUP_STYLE[g][1] or None), g)
        w_ = hs._glyph_w("swatch") + 0.8 + hs._text_width_mm(g)
        add = w_ + (2.4 if cur else 0.0)
        if cur and cur_w + add > AW:
            key_rows.append((cur, cur_w))
            cur, cur_w = [it], w_
        else:
            cur, cur_w = cur + [it], cur_w + add
    key_rows.append((cur, cur_w))
    for li, (items, tot) in enumerate(key_rows):
        hs.key(fig, items, centre_x=LAB + tot / 2, y=A_KEY_Y + li * 3.7)

    # ---- b, c, d: one dot per question, the house box over them (no mean, no interval: Valerio, 28 October)
    LAB_B = 29.0
    spans = [("b", LAB_B, 52.0, (1e3, 2e6), [1e3, 1e4, 1e5, 1e6], "Number of tokens per answer"),
             ("c", LAB_B + 52.0 + 6.0, 45.0, (5.0, 5e3), [10, 100, 1000], "Clock time less wait (s)"),
             ("d", LAB_B + 52.0 + 6.0 + 45.0 + 6.0, W - (LAB_B + 52.0 + 6.0 + 45.0 + 6.0) - 1.0, (0.5, 2e3),
              [1, 10, 100, 1000], "Model-call time per answer (s)")]
    field = {"b": "tokens_mean_over_draws", "c": "clock_less_wait_mean_over_draws", "d": "model_mean_over_draws"}
    overlaps = {}

    def house_row(ax, vals_mm, vals, s, y, pitch, key):
        dmm = hs.DOT_MM if len(vals) > 30 else hs.DOT_SPARSE_MM
        off, over = hs.swarm(vals_mm, half=hs.BAND_FRAC * pitch / 2 - dmm / 2, pitch=hs.DOT_PITCH_MM, dot=dmm)
        overlaps[key] = over
        ax.plot(vals, [y - o / pitch for o in off], ls="none", marker="o", ms=dmm / hs.MM_PT, mfc=hs.GREY["dot"],
                mec="none", mew=0, zorder=2, clip_on=False)
        st = {"q1": s["quartile_25"], "median": s["median"], "q3": s["quartile_75"], "whisker_low": min(vals),
              "whisker_high": max(vals)}
        hs.boxplot(ax, y, stats=st, orient="h", slot=1.0, dots=False)

    for L, x0, w, lim, ticks, xlabel in spans:
        ax = hs.axes_mm(fig, x0, B_TOP, w, B_BOT - B_TOP)
        ax.set_xscale("log")
        ax.set_xlim(*lim)
        ax.set_ylim(B_LIM[1], B_LIM[0])
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t:,.0f}" for t in ticks])
        ax.xaxis.set_minor_locator(matplotlib.ticker.LogLocator(subs=range(2, 10)))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_xlabel(xlabel, labelpad=2)
        ax.set_yticks(ROWPOS)
        ax.set_yticklabels([plate_label(s) for s, _ in SETUPS] if L == "b" else [])
        ax.tick_params(axis="y", length=0, pad=2)
        rows = fn[L]["rows"]
        lx = lambda v: (math.log10(v) - math.log10(lim[0])) / (math.log10(lim[1]) - math.log10(lim[0])) * w  # noqa
        for j, (setup, _) in enumerate(SETUPS):
            qrows = [r for r in rows if r["setup"] == setup and r["row"] == "question"]
            srow = [r for r in rows if r["setup"] == setup and r["row"] == "set-up"]
            if not qrows:
                if L == "d" and setup == G6[0][0]:
                    mid = sum(ROWPOS[-len(G6):]) / len(G6)
                    ax.text(math.sqrt(lim[0] * lim[1]), mid, "sub-calls run in parallel", ha="center", va="center",
                            color="#000000")
                continue
            vals = [r[field[L]] for r in qrows]
            if any(v is None or v <= 0 for v in vals) or min(vals) < lim[0] or max(vals) > lim[1]:
                raise SystemExit(f"panel {L} {setup}: a value outside the axis {lim}: {min(vals)} to {max(vals)}")
            house_row(ax, [lx(v) for v in vals], vals, srow[0], ROWPOS[j], B_PITCH, f"{L} {setup}")
        hs.panel_letter(fig, 0.4 if L == "b" else x0 - 4.0, B_TOP - 2.6, L)

    # ---- e: turns used, a heat strip; the colour bar above it, centred; the black outline on each set-up's cap cell
    # is said in the legend, not in a key (Valerio, 2 November)
    rlm = [(s, lab) for s, lab in SETUPS if s in CAP]
    E_W = 44.0
    axe = hs.axes_mm(fig, LAB_B, E_TOP, E_W, E_BOT - E_TOP)
    axe.set_xlim(0.5, 20.5)
    axe.set_ylim(E_LIM[1], E_LIM[0])
    axe.set_xticks([1, 5, 10, 15, 20])
    axe.set_xticklabels(["1", "5", "10", "15", "20"])
    axe.set_xlabel("Turns used", labelpad=2)
    axe.set_yticks(E_POS)
    axe.set_yticklabels([plate_label(s) for s, _ in rlm])
    axe.tick_params(axis="y", length=0, pad=2)
    CH = 0.40
    cmap = cividis_up()
    for j, (setup, _) in enumerate(rlm):
        for r in fn["e"]:
            if r["setup"] != setup or r["turns_used"] is None:
                continue
            axe.add_patch(Rectangle((r["turns_used"] - 0.46, E_POS[j] - CH), 0.92, 2 * CH,
                                    facecolor=cmap[r["colour_index_of_256"]], edgecolor="none", lw=0, zorder=2))
        axe.add_patch(Rectangle((CAP[setup] - 0.5, E_POS[j] - CH - 0.06), 1.0, 2 * CH + 0.12, facecolor="none",
                                edgecolor="#000000", lw=hs.LW["median"], zorder=3))
    ecx = LAB_B + E_W / 2
    key_y = E_BAND + hs.PT * hs.MM_PT
    hs.panel_letter(fig, 0.4, key_y, "e")
    nmax = fn["e_max"]
    lab_w = hs._text_width_mm("Answers (n)")
    CBW, CBH = 24.0, 2.0
    cbx = ecx - (CBW + 2.0 + lab_w) / 2
    cby = key_y + 1.6 - 3.7
    axk = fig.add_axes((cbx / W, 1 - (cby + CBH) / H, CBW / W, CBH / H))
    axk.set_xscale("log")
    axk.set_xlim(1, nmax)
    axk.set_ylim(0, 1)
    for i in range(256):
        lo, hi = nmax ** (i / 256), nmax ** ((i + 1) / 256)
        axk.add_patch(Rectangle((lo, 0), hi - lo, 1, facecolor=cmap[i], edgecolor="none", lw=0))
    axk.set_yticks([])
    axk.set_xticks([t for t in (1, 10, 100, 1000) if t <= nmax])
    axk.set_xticklabels([f"{t:,}" for t in (1, 10, 100, 1000) if t <= nmax])
    axk.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    axk.tick_params(axis="x", length=2, width=hs.LW["axis"], pad=1)
    for sp in axk.spines.values():
        sp.set_visible(False)
    hs.text_mm(fig, cbx + CBW + 2.0, cby + CBH * 0.85, "Answers (n)", ha="left")

    # ---- f: verified pass, clock time with the wait and the wait alone, linear scale
    F_LAB = 31.0
    fx0 = LAB_B + E_W + 15.0 + F_LAB
    fw = W - fx0 - 3.5
    F_H = E_BOT - E_BAND                                   # top at e's key band, bottom at e's axis (supp.md section 6)
    F_PITCH = F_H / (F_LIM[1] - F_LIM[0])
    axf = hs.axes_mm(fig, fx0, E_BAND, fw, F_H)
    frows = fn["f"]["rows"]
    parts = list(fn["f"]["summary"])
    fmax = max(r["s_mean_over_draws"] for r in frows if r["row"] == "question")
    flim = (0.0, 100.0 * math.ceil(fmax / 100.0))
    step = 100 if flim[1] <= 600 else 200
    axf.set_xlim(*flim)
    axf.set_ylim(F_LIM[1], F_LIM[0])
    axf.set_xticks(list(range(0, int(flim[1]) + 1, step)))
    axf.set_xticklabels([f"{t:,}" for t in range(0, int(flim[1]) + 1, step)])
    axf.set_xlabel("Verified pass, time per answer (s)", labelpad=2)
    axf.set_yticks(range(len(parts)))
    axf.set_yticklabels(["clock time" if p_ == "clock time" else "waiting for verifier" for p_ in parts])
    axf.tick_params(axis="y", length=0, pad=2)
    lxf = lambda v: (v - flim[0]) / (flim[1] - flim[0]) * fw     # noqa: E731
    for j, part in enumerate(parts):
        vals = [r["s_mean_over_draws"] for r in frows if r["part"] == part and r["row"] == "question"]
        house_row(axf, [lxf(v) for v in vals], vals, fn["f"]["summary"][part], j, F_PITCH, f"f {part}")
    hs.panel_letter(fig, fx0 - F_LAB, key_y, "f")

    bad_c = hs.check_figure_colours(fig)
    if bad_c:
        plt.close(fig)
        raise SystemExit(f"{nm['plate']}: colours outside the house palette: {bad_c}")
    finish_plate(fig, W, H, paths, nm["plate"])
    return W, H, printed, overlaps, B_PITCH


# ---------------------------------------------------------------------------------------------------------------
# Source Data, legend, caption
# ---------------------------------------------------------------------------------------------------------------
def sheets_of(fn, nm):
    out = []
    for L in "abcdef":
        rows = fn[L]["rows"] if isinstance(fn[L], dict) else fn[L]
        if L == "a":
            rows = rows + fn["a_split"]            # the split of a's last two columns, rows "cut_split"
        cols = []
        for r in rows:
            for c in r:
                if c not in cols:
                    cols.append(c)
        rows = [{**r, "setup_label": plate_label(r["setup"])} if r.get("setup_label") else r for r in rows]
        out.append((f"{nm['sheet_prefix']}{L}", cols, [[r.get(c) for c in cols] for r in rows]))
    cols = list(fn["a_groups"][0]) if fn["a_groups"] else []
    groups = [{**r, "setup_label": plate_label(r["setup"])} for r in fn["a_groups"]]
    out.append((f"{nm['sheet_prefix']} groups", cols, [[r.get(c) for c in cols] for r in groups]))
    return out


def write_source_data(sheets, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for name, cols, rows in sheets:
        ws = wb.create_sheet(name)
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in rows:
            ws.append([("" if x is None else x) for x in r])
    wb.save(path)


def fmt_int(x):
    return f"{x:,}"


def rerun_status(data, named, again, g2_from, g2_checked):
    """What is still owed, from what the records hold. Per group (Mentori's six strategies, the matched-budget arm, the
    authors' RLM): the answers S455's D92 list names, those to be rerun (action OWED), how many of those are stored
    again, and those it leaves as they are (D92 Q185: "stays_failed", the stored failure stands). An answer is settled
    when it is stored, no rerun of it is owed, it was not planned from an out-of-date token target (G2), and its file
    was checked by S455 for the D89 and D90 Gemini cases (G2: a scan of its current answers file; G1 and the authors'
    RLM: the D92 scans). --final needs every answer settled. The selftest checks the counts on synthetic records."""
    groups = {"G1": [s for s, _ in G1], "G2": [s for s, _ in G2], "G6": [c for c, _ in G6]}
    out, unsettled = {}, set()
    for grp, setups in groups.items():
        owed = {(s, k) for s in setups for k, a in named.get(s, {}).items() if a == OWED}
        done = {(s, k) for s, k in owed if k in again.get(s, set())}
        left = Counter(a for s in setups for a in named.get(s, {}).values() if a != OWED)
        out[grp] = {"listed": sum(len(named.get(s, {})) for s in setups), "rerun": len(owed),
                    "stored_again": len(done), "not_rerun": dict(left)}
        unsettled |= owed - done
    unsettled |= {("matched_budget", x["key"]) for x in g2_from}
    if not g2_checked:
        unsettled |= {("matched_budget", x["key"]) for x in data["matched_budget"]}
    out.update({"g2_checked_by_s455": g2_checked, "g2_from_again": len(g2_from),
                "g2_questions": sorted({x["q"] for x in g2_from}),
                "g2_answers_from_again": sorted(x["key"] for x in g2_from),
                "unsettled": sorted(f"{s}:{k}" for s, k in unsettled), "settled": TOTAL - len(unsettled)})
    return out


def rerun_state(rerun):
    """One sentence on what is still owed (D89, D90, D92 Q185, D93 Q-a, G2's targets), from what the records hold."""
    def grp(name, g):
        left = "; ".join((f"{n} more stay failed (D92 Q185)" if a == "stays_failed" else f"{n} more: {a}")
                         for a, n in sorted(g["not_rerun"].items()))
        return f"{name} {g['stored_again']} of {g['rerun']}" + (f", {left}" if left else "")
    g2q = ", ".join(rerun["g2_questions"]) or "none"
    authors = "Zhang RLM"
    return (f"of the answers S455's D92 list gives to rerun, stored again since: "
            f"{grp('Mentor::i', rerun['G1'])}; {grp(authors, rerun['G6'])}"
            + (f"; {grp('matched budget', rerun['G2'])}" if rerun["G2"]["listed"] else "")
            + f"; matched-budget answers whose token target was set before an RLM-10 answer of their question was "
            f"stored again: {rerun['g2_from_again']} (questions {g2q}); matched-budget answers checked by S455 for the "
            f"D89 and D90 Gemini cases: {'yes' if rerun['g2_checked_by_s455'] else 'not yet'}")


def legend_and_caption(fn, stamp, n_in, extra, nm, rerun, command=None):
    vr = fn["vrep"]
    g6m = fn["g6_tokens_missing"]
    pools = fn["pools"]
    pool_txt = "; ".join(f"{LABEL[x]} {', '.join(map(str, v))}" for x, v in pools.items())
    title = f"**{nm['plate']} | Outcomes, tokens, time and turns per answer for each generation strategy.**"
    vw, gt = fn["vp_wait"], fn["g6_time"]
    g1nt = fn["g1_calls_without_tokens"]
    lst = lambda d, f: "; ".join(f"{LABEL[k]} {f(v)}" for k, v in d.items())
    commits = []
    for x, _ in EXP01:
        cm = extra["commits"][x]
        commits.append(f"{LABEL[x]} all {sum(cm.values())} at {next(iter(cm))}" if len(cm) == 1 else
                       f"{LABEL[x]} " + ", ".join(f"{n} at {c}" for c, n in cm.items()))
    # each count named for what it counts (22 Oct review: "authors' RLM-5: 2 turn_cap" read as the set-up's turn_cap
    # count, which panel a gives as 7): the answers returned ok with no text, by their stop reason
    empty_ok = "; ".join(f"{LABEL[c]} " + ", ".join(f"{n}, stop reason {k}" for k, n in d.items())
                         for c, d in fn["g6_empty_ok"].items() if d) or "none"
    drawn = {r[0] for r in fn["a_rows"]}
    not_drawn = [r[0] for r in OUTCOME_ROWS if r[0] not in drawn]
    v_zero = [r[2] for r in OUTCOME_ROWS if r[1] == "verifier" and not vr["status_counts"].get(r[2])]
    other_waits = {k: v for k, v in vw["other_exp01_calls_with_a_wait_over_0_s"].items() if v}
    n_oos = fn["a_split"][0]["questions_n"]
    no_wall = {k: v for k, v in fn["g1_calls_without_wall"].items() if v}
    box_txt = "Grey dots, question means over three draws; box, interquartile range; line, median; whiskers, range; "
    legend = (
        f"# {nm['plate']}, title and legend (draft)\n\n"
        f"Written by `{SCRIPT} figure` from the plotted numbers.\n\n"
        f"{title} Each set-up answered the {N_Q} questions three times with {GEN_DISPLAY.get(extra['gen_model'], extra['gen_model'])} "
        # editor row 45 (Valerio, 8 Nov): n = X only in the panels that draw boxes (b, c, d, f); a and e draw
        # counts, so their counts stay in words; every panel described in full, no "as in b"
        f"on the 20-paper index ({N_Q * len(DRAWS)} answers). Matched budget is a single pass with passages "
        f"matching RLM-10's input tokens; RLM is Mentor::i's own and Zhang RLM the method authors' package "
        f"({extra['pkg']}), each with its turn cap ({extra['max_iter']}) after the dash. "
        f"**a**, Answers that did not end in a plain answer, stacked by kind. Right: answers that "
        f"did; answers with no text; and, of the {n_oos * len(DRAWS)} answers per set-up to the "
        f"{n_oos} out-of-scope questions, those judged refused (refusal score {REFUSED_AT} or "
        f"more), among those cut at the turn limit (RLM-5) or by the closing turn (multi-hop), "
        f"and the rest (no judge row: not refused). "
        f"**b**, Tokens per answer (prompt, output and thinking, verifier's included), log scale. " + box_txt + f"n = {N_Q} questions per set-up. "
        f"**c**, Clock time per answer (s) less the local verifier wait, log scale. " + box_txt + f"n = {N_Q} questions per set-up. "
        f"**d**, Model-call time per answer (s), summed over calls, log scale; blank for Zhang RLM (parallel "
        f"sub-calls). " + box_txt + f"n = {N_Q} questions per set-up. "
        f"**e**, Turns used by the six RLM set-ups: cell colour, answers of the set-up's "
        f"{N_Q * len(DRAWS)} using that many turns (log scale); no cell, none; black "
        f"outline, turn cap. "
        f"**f**, Verified pass, time per answer (s), linear scale: clock time with the verifier wait, "
        f"and the wait alone. " + box_txt + f"n = {N_Q} questions.\n")
    cap_name = f"{nm['stem']}"
    sh = nm["sheet_prefix"]
    cap = (
        f"# {cap_name}, caption\n\n"
        f"**{cap_name} | Numerical values plotted in {nm['plate']}.** Drawn from {fmt_int(n_in)} of the "
        f"{fmt_int(TOTAL)} answers the plate plans, {fmt_int(rerun['settled'])} of them settled, judged only in a's "
        f"split columns. Data stamp: {stamp}. One sheet per panel. Sheet {sh}a: per set-up and "
        f"outcome (stop reason as stored, empty answer text, verifier status), the answers counted and the set-up's "
        f"answers; the set-up's first row also gives how many of its answers S455's D92 list names "
        f"(to rerun or left as stored). "
        f"Rows 'cut_split' of the same sheet: on the out-of-scope questions, the answers the judge scored as refused, of "
        f"those cut at the limit and of the others (RLM-5 and multi-hop). Sheet {sh} groups: per set-up, its answers by "
        f"plain kind of ending, as a's bars and columns draw them. "
        f"Sheets {sh}b, {sh}c and {sh}d: per set-up, one row per question (rows 'question': its answer type in the key "
        f"and the mean over its three draws of tokens (with prompt, output and thinking tokens), clock time less the "
        f"wait for the local server (with the clock time and the wait) or model-call time (with local and API "
        f"model-call time and the model calls)) and one summary row (rows 'set-up': questions n, mean and median over "
        f"the questions, each with its 95% percentile interval over 10,000 resamples of the questions, seed 20261013, "
        f"the 25th and 75th percentiles the box is drawn from, the mean clock time with the wait ({sh}c) or the mean "
        f"model calls per answer ({sh}d); on RLM-10's row the ratio of its mean to single pass's). Sheet {sh}e: per "
        f"RLM set-up, its cap, the answers that used each number of turns, their share, and the cell's colour (its "
        f"entry of the 256 of cividis on the log scale, many answers yellow, and its hex code). Sheet {sh}f: verified pass, per "
        f"question and part (clock time with the wait; the wait for the local verifier server) the mean over its "
        f"three draws, and a summary row per part as in {sh}b. "
        # audit 27 Oct F4 (fig1_2_5): the counts the legend rewrite of 23 Oct (d2ec2c73) dropped, each computed by
        # this script and recorded in the provenance's notes
        f"Counted, not drawn: in a, outcome rows that no answer falls in are not drawn "
        f"({', '.join(not_drawn) or 'none'}), and no verified-pass answer has the verifier status "
        f"{', '.join(v_zero) or 'none'}; answers Zhang RLM returned as ok with no text, by stop reason: "
        f"{empty_ok}. In b, answers that lack a token count for at least one call are drawn with the counts "
        f"recorded: {lst({k: v for k, v in g1nt.items() if v}, str) or 'Mentor::i none'}; "
        + "; ".join(f"{LABEL[c]} {g6m[c]}" for c, _ in G6) + " (of 405 each). "
        f"In c, each answer's clock time was measured while other answers ran: Mentor::i's set-ups in a pool of at "
        f"most this many answers at once (the record's pool size), {pool_txt}; Zhang RLM in "
        + ", ".join(f"{gt['processes'][c]} processes ({LABEL[c]})" for c, _ in G6)
        + f", at most {gt['most_answers_in_flight_across_the_three_caps']} of its answers in flight at once across "
        f"the three caps; calls other than verified pass's verifier calls with a wait over 0 s: "
        f"{lst(other_waits, str) if other_waits else 'none'}. In d, Zhang RLM's summed call time exceeds the "
        f"answer's clock time in "
        + ", ".join(f"{gt['answers_whose_summed_call_time_exceeds_clock'][c]} ({LABEL[c]})" for c, _ in G6)
        + f" of 405 answers, so its rows are blank; calls without a recorded time: "
        f"{lst(no_wall, str) if no_wall else 'none'}; search time is not included (it is recorded on "
        f"{extra['search_n']} of the {fmt_int(PLANNED['G1'] + PLANNED['G2'])} Mentor::i answers). "
        + (f"Generated by `{command}` (the figure command on the frozen copies of the run records)."
           if command else f"Generated by `uv run --frozen python {SCRIPT} figure --records <copied G1 and G2 records> "
                           f"--as {nm['kind']} --n {nm['n']}` from the run records.") + "\n")
    if not nm["supp"]:
        cap += (f"\nProposed Data Availability sentence: \"The source data for Figure {nm['n']} is in Supplementary "
                f"Data {nm['n'] + 1}.\"\n")   # D303 follow-up: Data n + 1 (D302)
    return legend, cap


# ---------------------------------------------------------------------------------------------------------------
# the claims list (D82): every number the plate prints, and every sentence of the letter and the manuscript that
# gives a number for these panels or that the plate bears on, against what these records give
# ---------------------------------------------------------------------------------------------------------------
SIX_EIGHT = ("At the scale of the generation-strategy experiment (88 answerable questions over 20 core papers), RLM-10 "
             "exceeded single-pass retrieval by 12.5 percentage points (two-sided exact McNemar P = 0.019), at roughly "
             "six times the model calls and eight times the wall-clock time per answer (Supplementary Table 8).")
NO_COUNTER = ("Single-pass, multi-hop and passage verification had no token counter, so these three have no comparable "
              "token figure.")
COMPARABLE = ("Comparable is yes for the four with a measured token counter; the other three store a whitespace word "
              "count (single_pass), LLM calls times 1,500 (multi_hop) or a hard-coded 0 (verified_pass).")
CALLS = ("mean", "d", "model_calls_mean")
CLOCK = ("mean", "c", "clock_with_wait_mean")
CALLS_R = ("ratio", "d", "model_calls_mean")
CLOCK_R = ("ratio", "c", "clock_with_wait_mean")
NO_NAIVE = ("absent", "no naive RAG arm among these set-ups")
NO_NAIVE_R = ("absent", "no naive RAG arm among these set-ups; RLM-10 to single pass, tokens, here", "b")
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}
# Each claim: the document, the sentence (as the document reads with every tracked change accepted), and per number:
# the words printed, what it says, the S77 cell it was written from (the letter cites S77 for its cost numbers:
# findings/letter_check/question_2.md:16, :26; None for a number the agreed text prints from these records), how it is
# printed, what these records give for it (OURS), and, for a table cell, (row label, cell's place after the label) in
# the paragraphs after the sentence. Every sentence of the letter, the main text, the Methods and the Supplementary
# Information that gives a number for these panels or that the plate bears on (audit of 18 October, defect 3: the
# builder's list had 5). D304 (8 November): C1 to C13 re-anchored on the sentence of the agreed text (Claude Docs rev
# 3688, the live documents with every mark accepted) that now states each claim; the letter's on the letter with every
# mark accepted, provisional until the letter round is rebuilt. C14 to C18 retired with the reason ("retired"): their
# submitted words and S77 numbers are kept, reproduced from S77 and still set against these records.
GONE_T8 = ("Supplementary Table 8 is not in the agreed Supplementary Information (it holds Tables 1 to 3); the letter's "
           "Table R4.1 gives these set-ups' cost from this plate (C4, C5)")
R4_OPEN = "Every answer record now keeps each model call with its tokens"
R4_TABLE = ("Table R4.1 gives every strategy over all 135 questions in scope, out-of-scope questions included, from the "
            "Source Data of Supplementary Figure 17.")
TOK = ("mean", "b", "mean")
CLK = ("mean", "c", "mean")
CLAIMS = [
    {"id": "C1", "doc": "letter", "opening": "We thank Reviewer 4 for a review specific enough",
     "sentence": "Every strategy now reports tokens, model calls and time, and the matched-budget comparison is run "
                 "(Question 2).", "numbers": [],
     "bears": "sheets b to d give every set-up's tokens, model calls and time per answer, and the matched-budget arm "
              "(G2) is one of its set-ups"},
    {"id": "C2", "doc": "letter", "opening": R4_OPEN,
     "sentence": "On the 86 answerable questions, RLM-10 used about six times the model calls and ten times the tokens "
                 "of single pass per answer", "numbers": [],
     "judged": "the ratios on the 86 answerable questions are Figure 3d's, checked in Figure 3's claims list (S463 "
               "C22); these records give all 135 questions (C4, C5)"},
    {"id": "C3", "doc": "letter", "opening": R4_OPEN,
     "sentence": "Every answer record now keeps each model call with its tokens, stop reason and timings.", "numbers": [],
     "bears": "sheets b to d are counted from those call records"},
    {"id": "C4", "doc": "letter", "opening": R4_OPEN, "sentence": R4_TABLE,
     "numbers": [("7.29", "RLM-10, model calls per answer", None, "{:.2f}", CALLS + ("rlm_10",), ("RLM-10", 1)),
                 ("1.00", "single pass, model calls per answer", None, "{:.2f}", CALLS + ("single_pass",),
                  ("single pass", 1)),
                 ("2.76", "multi-hop, model calls per answer", None, "{:.2f}", CALLS + ("multi_hop",), ("multi-hop", 1)),
                 ("137.2", "RLM-10, clock time per answer less the wait (s)", None, "{:.1f}", CLK + ("rlm_10",),
                  ("RLM-10", 2)),
                 ("41.4", "single pass, clock time per answer less the wait (s)", None, "{:.1f}",
                  CLK + ("single_pass",), ("single pass", 2))]},
    {"id": "C5", "doc": "letter", "opening": R4_OPEN, "sentence": R4_TABLE,
     "numbers": [("82,590", "RLM-10, tokens per answer", None, "{:,.0f}", TOK + ("rlm_10",), ("RLM-10", 3)),
                 ("6,817", "single pass, tokens per answer", None, "{:,.0f}", TOK + ("single_pass",),
                  ("single pass", 3)),
                 ("42,580", "matched budget, tokens per answer", None, "{:,.0f}", TOK + ("matched_budget",),
                  ("matched budget", 3))],
     "bears": "single pass now records tokens: every one of its answers has a token count for each call (sheet b)"},
    {"id": "C6", "doc": "letter", "opening": "Retrieval calls follow from each design",
     "sentence": "Input, output and thinking tokens are stored separately for every call, so a reader can price any "
                 "model.", "numbers": [],
     "bears": "every set-up here records prompt, output and thinking tokens apart (sheet b)"},
    {"id": "C7", "doc": "letter", "opening": "Table R4.1 | Cost per answer by strategy",
     "sentence": "135 questions in scope, three draws, 405 answers per strategy.",
     "numbers": [("405", "RLM-10, answers averaged", None, "digits", ("answers", "rlm_10"))]},
    {"id": "C8", "doc": "letter", "opening": R4_OPEN,
     "sentence": "Cost is therefore counted from the same runs that are scored", "numbers": [],
     "bears": "the plate's set-ups are the answers the judge scored (135 questions x 3 draws)"},
    {"id": "C9", "doc": "letter", "opening": "Retrieval calls follow from each design",
     "sentence": "Multi-hop retrieval is our multi-query baseline: on the answerable questions it passed 78.7% of "
                 "answers, against 74.0% for RLM-10.", "numbers": [],
     "judged": "78.7% against 74.0%: judged results, not on this plate (Figure 3, S463 C49); multi-hop's model calls "
               "are C4"},
    {"id": "C10", "doc": "letter", "opening": "Matched budget. We gave single pass",
     "sentence": "We gave single pass, in one call, as many input tokens as RLM-10 used on the same question, by adding "
                 "passages.", "numbers": [],
     "bears": "the matched-budget arm drawn here (405 answers) gives single pass the input tokens RLM-10 used, by "
              "adding passages; its tokens per answer are C5"},
    {"id": "C11", "doc": "letter", "opening": "In question answering, single pass mostly gives the same pass or fail",
     "sentence": "So a second single-pass sample would rarely change a failure.", "numbers": [],
     "bears": "the matched-budget arm drawn here (405 answers) gives single pass the input tokens RLM-10 used, by "
              "adding passages; it does not sample repeatedly"},
    {"id": "C12", "doc": "main text", "opening": "RLM-10 also cost more",
     "sentence": "RLM-10 also cost more, with about six times the model calls and ten times the tokens per answer",
     "numbers": [],
     "judged": "the ratios are Figure 3d's, checked in Figure 3's claims list (S463 C22); these records give all 135 "
               "questions (the letter's Table R4.1, C4, C5)"},
    {"id": "C13", "doc": "methods", "opening": "Compute cost.",
     "sentence": "Every answer record keeps each model call with its tokens, stop reason and timings, so the cost of an "
                 "answer is counted from the same runs that are scored (Fig. 3d and Supplementary Fig. 17).",
     "numbers": [], "bears": "sheets b to d are counted from those call records"},
    {"id": "C14", "doc": "SI", "opening": "Supplementary Table 8 | Compute cost", "sentence": COMPARABLE,
     "retired": GONE_T8,
     "numbers": [("four", "arms with a measured token counter", ("arms", "measured"), "count", ("measured",)),
                 ("three", "arms with a word count, a constant or 0", ("arms", "unmeasured"), "count",
                  ("no_tokens",))]},
    {"id": "C15", "doc": "SI", "opening": "Token comparability:",
     "sentence": "Token comparability: 4 of 7 arms carry a measured token counter (naive_RAG, rlm_5, rlm_10, "
                 "rlm_20); 3 carry a proxy or no figure at all (single_pass, multi_hop, verified_pass) and may not be "
                 "compared with the measured arms or with each other.",
     "retired": GONE_T8,
     "numbers": [("4", "arms with a measured token counter", ("arms", "measured"), "digits", ("measured",)),
                 ("7", "arms", ("arms", "n"), "digits", ("setups",)),
                 ("3", "arms with a proxy or no figure", ("arms", "unmeasured"), "digits", ("no_tokens",))]},
    {"id": "C16", "doc": "SI", "opening": "LLM calls, RLM-10 over single-pass",
     "sentence": "LLM calls, RLM-10 over single-pass: 5.9 times.",
     "retired": GONE_T8,
     "numbers": [("5.9", "RLM-10 against single pass, model calls per answer", ("ratios", "llm_calls"), "{:.1f}",
                  CALLS_R)]},
    {"id": "C17", "doc": "SI", "opening": "Latency, RLM-10 over single-pass",
     "sentence": "Latency, RLM-10 over single-pass: 8.0 times.",
     "retired": GONE_T8,
     "numbers": [("8.0", "RLM-10 against single pass, wall-clock time per answer", ("ratios", "latency_s"), "{:.1f}",
                  CLOCK_R)]},
    {"id": "C18", "doc": "SI", "opening": "Input and output split is logged",
     "sentence": "Input and output split is logged for naive_RAG only: 2,372.3 prompt and 195.6 completion tokens per "
                 "answer, 92.4 per cent input.",
     "retired": GONE_T8,
     "numbers": [("2,372.3", "naive RAG, prompt tokens per answer", ("naive_RAG", "prompt_tokens"), "{:,.1f}",
                  NO_NAIVE),
                 ("195.6", "naive RAG, output tokens per answer", ("naive_RAG", "completion_tokens"), "{:.1f}",
                  NO_NAIVE),
                 ("92.4", "naive RAG, input share of tokens (%)", ("naive_RAG", "input_share_pct"), "{:.1f}",
                  NO_NAIVE)],
     "bears": "every set-up here records prompt, output and thinking tokens apart (sheet b)"},
]
DOCS = {"letter": LETTER, "main text": MAIN_TEXT, "methods": doc("03_Methods.docx"),
        "SI": doc("06_Supplementary_Information.docx")}   # SI: the submitted Supplementary Table 8 the retired rows name


def docx_paragraphs(path: Path):
    """[(text, style, is heading)], each paragraph's text with every tracked change accepted (w:del runs left out)."""
    import zipfile
    import xml.etree.ElementTree as ET
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    out = []
    for par in root.iter(w + "p"):
        parts = []

        def walk(el, deleted):
            deleted = deleted or el.tag == w + "del"
            if el.tag == w + "t" and not deleted:
                parts.append(el.text or "")
            for c in el:
                walk(c, deleted)
        walk(par, False)
        st = par.find(f"{w}pPr/{w}pStyle")
        style = st.get(w + "val") if st is not None else ""
        out.append(("".join(parts), style))
    return out


def s77_values():
    """S77's cost_table by strategy, its ratios, and the counts the claims quote: the arms (7), those whose token
    figure is not a measured counter (3) and those whose is (4), the three Mentori strategies among them, and whether
    a matched-budget pair was available (no)."""
    j = json.loads(S77.read_text())
    t = {r["strategy"]: r for r in j["cost_table"]}
    measured = sum(1 for r in j["cost_table"] if r["token_provenance"] == "measured_token_counter")
    t["ratio"] = {"llm_calls": t["rlm_10"]["llm_calls"] / t["single_pass"]["llm_calls"],
                  "latency_s": t["rlm_10"]["latency_s"] / t["single_pass"]["latency_s"]}
    t["ratios"] = {k: v["value"] for k, v in j["ratios"].items()}
    t["unmeasured"] = {"token_provenance": sum(1 for s, _ in G1 if t[s]["token_provenance"] != "measured_token_counter")}
    t["arms"] = {"n": len(j["cost_table"]), "measured": measured, "unmeasured": len(j["cost_table"]) - measured}
    t["matched"] = {"available": j["matched_budget_available"]}
    return t


def printed_as(fmt, v):
    """A value as the documents print it: "count" a number word, "digits" an integer, "words" "N times", "no" a
    yes-no ("no" for false), "{:.Nf}" or "{:,.Nf}" rounded half up (with thousands commas)."""
    if fmt == "count":
        return WORDS.get(v, str(v)) if v else "none"
    if fmt == "digits":
        return str(int(v))
    if fmt == "no":
        return "no" if not v else "yes"
    if fmt == "words":
        return f"{WORDS.get(int(half_up(v, 0)), half_up(v, 0))} times"
    m = re.fullmatch(r"\{:(,?)\.(\d)f\}", fmt)
    if not m:
        return str(v)
    s = half_up(v, int(m.group(2)))
    if m.group(1):
        whole, _, frac = s.partition(".")
        s = f"{int(whole):,}" + (f".{frac}" if frac else "")
    return s


def claims_reproduce():
    """REPRODUCE (README.md:75-79): every number the claims quote from the submitted run must be regenerated from S77,
    the artifact the letter cites for it; otherwise nothing is written."""
    t = s77_values()
    bad, n = [], 0
    for c in CLAIMS:
        for words, _, src, fmt, *_ in c["numbers"]:
            if src is None:                     # D304: printed by the agreed text from these records, not from S77
                continue
            got = printed_as(fmt, t[src[0]][src[1]])
            n += 1
            if got != words:
                bad.append(f"{c['id']} {words!r}: S77 {src[0]}.{src[1]} = {t[src[0]][src[1]]!r} prints {got!r}")
    if bad:
        raise SystemExit(f"claims reproduce FAILED, nothing written: {bad}")
    print(f"reproduce: {n} numbers the letter and the manuscript quote from the submitted run regenerated from "
          f"{S77.relative_to(ROOT)}")
    return {"compared": n, "artifact": str(S77.relative_to(ROOT)), "sha256": sha256_file(S77)}


def ours(spec, fmt, fn, data):
    """What these records give for a quoted number: (value, as printed, from where), or (None, None, why not)."""
    kind = spec[0]
    lacking = {s: fn["tokens_missing_answers"][s] for s, _ in SETUPS}
    if kind == "mean":
        _, L, col, setup = spec
        v = fn[L]["summary"][setup][col]
        return v, printed_as(fmt, v), f"sheet {L}, set-up row {setup}, column {col}"
    if kind == "ratio":
        _, L, col = spec
        v = fn[L]["summary"]["rlm_10"][col] / fn[L]["summary"]["single_pass"][col]
        return v, printed_as(fmt, v), f"sheet {L}, set-up rows rlm_10 and single_pass, column {col} (their ratio)"
    if kind == "answers":
        v = len(data[spec[1]])
        return v, printed_as(fmt, v), f"the answers of {spec[1]}, 135 questions x 3 draws"
    if kind == "g1_no_tokens":
        v = sum(1 for s, _ in G1 if lacking[s] == len(data[s]))
        return v, printed_as(fmt, v), ("Mentori's six strategies in which every answer has a call with no token count "
                                       "(generation.calls_without_tokens above 0)")
    if kind == "no_tokens":
        v = sum(1 for s, _ in SETUPS if lacking[s] == len(data[s]))
        return v, printed_as(fmt, v), "the ten set-ups in which every answer has a call with no token count"
    if kind == "measured":
        v = sum(1 for s, _ in SETUPS if lacking[s] == 0)
        return v, printed_as(fmt, v), "the ten set-ups in which no answer has a call without a token count"
    if kind == "setups":
        v = len(SETUPS)
        return v, printed_as(fmt, v), "the plate's set-ups (no naive RAG among them)"
    if kind == "g2":
        v = len(data["matched_budget"])
        return v, f"{v} answers", "the matched-budget arm's answers (G2)"
    if kind == "absent":
        why = spec[1]
        if len(spec) > 2:
            r = fn[spec[2]]["ratio"]
            why += f" {half_up(r, 1)} (sheet {spec[2]}, set-up rows rlm_10 and single_pass)"
        return None, None, why
    raise SystemExit(f"claims: no rule for {spec}")


def claims_now(fn, data):
    """Each claim: where the sentence stands now, its numbers from the submitted run (S77) and from these records."""
    t = s77_values()
    paras = {k: docx_paragraphs(p) for k, p in DOCS.items()}
    out = []
    for c in CLAIMS:
        ps = paras[c["doc"]]
        where, at = None, None
        for i, (txt, _) in enumerate(ps):
            if c.get("retired"):                # D304: not searched; the agreed text no longer states it
                break
            if c["sentence"] in txt:            # the nearest heading above it; a document with no heading style (the
                #                                 manuscript) gives its nearest short line with no full stop
                head = next((ps[j][0] for j in range(i - 1, -1, -1) if ps[j][1].lower().startswith("heading")), None)
                head = head or next((ps[j][0] for j in range(i - 1, -1, -1)
                                     if 0 < len(ps[j][0]) < 60 and not ps[j][0].rstrip().endswith(".")), "")
                where = {"section": head, "paragraph_opening": " ".join(txt.split()[:8])}
                at = i
                break
        nums = []
        for words, what, src, fmt, spec, *cell in c["numbers"]:
            v, p, from_ = ours(spec, fmt, fn, data)
            in_text = None
            if cell and at is not None:         # D304: a table cell, (row label, its place after the label)
                label, k = cell[0]
                j = next((j for j in range(at + 1, len(ps) - k) if ps[j][0].strip() == label), None)
                in_text = j is not None and ps[j + k][0].strip().split(" ")[0] == words
            if src is None:
                nums.append({"printed": words, "what": what, "submitted_value": None, "s77_cell": None,
                             "submitted_from": "the agreed text, from these records", "these_records": v,
                             "these_records_from": from_, "these_records_printed": p,
                             "same": None if p is None else p == words, "cell_in_text": in_text})
                continue
            sub = t[src[0]][src[1]]
            nums.append({"printed": words, "what": what, "submitted_value": sub, "s77_cell": f"{src[0]}.{src[1]}",
                         "submitted_from": f"{S77.relative_to(ROOT)} " + (
                             f"cost_table rlm_10.{src[1]} / single_pass.{src[1]}" if src[0] == "ratio" else
                             f"ratios.{src[1]}.value" if src[0] == "ratios" else
                             "cost_table: the six Mentori strategies whose token_provenance is not "
                             "measured_token_counter" if src[0] == "unmeasured" else
                             "cost_table: its arms, by token_provenance" if src[0] == "arms" else
                             "matched_budget_available" if src[0] == "matched" else
                             f"cost_table {src[0]}.{src[1]}"),
                         "these_records": v, "these_records_from": from_, "these_records_printed": p,
                         "same": None if p is None else p == words})
        out.append({"id": c["id"], "doc": str(DOCS[c["doc"]].relative_to(ROOT)), "doc_sha256": sha256_file(DOCS[c["doc"]]),
                    "found": where is not None, "where": where, "opening": c["opening"], "sentence": c["sentence"],
                    "numbers": nums, "judged_numbers": c.get("judged"), "bears": c.get("bears"),
                    "retired": c.get("retired")})
    return out


def claims_tally(claims):
    """Quoted numbers that differ from these records, that have no counterpart here, and the total; per quotation and
    per submitted value (the same S77 cell quoted in several sentences counted once)."""
    q = [x for c in claims for x in c["numbers"]]
    cells = {}
    for x in q:
        if x["s77_cell"] is not None:
            cells.setdefault(x["s77_cell"], []).append(x["same"])
    per_cell = [("absent" if any(v is None for v in vs) else "differ" if not all(vs) else "same")
                for vs in cells.values()]
    return {"quoted": len(q), "differ": sum(1 for x in q if x["same"] is False),
            "absent": sum(1 for x in q if x["same"] is None),
            "values": len(cells), "values_differ": per_cell.count("differ"), "values_absent": per_cell.count("absent"),
            "no_number": [c["id"] for c in claims if not c["numbers"]],
            "retired": [c["id"] for c in claims if c.get("retired")],
            "not_found": [c["id"] for c in claims if not c["found"] and not c.get("retired")]}


def claims_md(nm, stamp, printed, sheets, claims, rep):
    """claims.md: the plate's printed numbers with their workbook cells, then the documents' sentences."""
    rows = {name: [dict(zip(cols, r)) for r in rs] for name, cols, rs in sheets}
    lines = [f"# {nm['plate']}: claims list (D82)", "",
             f"Written by `{SCRIPT} figure` with the plate; regenerated on every run. Data stamp: {stamp}.", "",
             "## 1. Every number printed on the plate", "",
             "Each is the SVG text S448 R8 (6) holds to its workbook cell (the `printed` map of the numbers file).", "",
             "| SVG id | printed | sheet, row | set-up | what | value |", "|---|---|---|---|---|---|"]
    for gid, e in printed.items():
        if "fixed" in e:
            lines.append(f"| {gid} | {e['fixed']} | fixed text | | {e['why']} | |")
            continue
        r = rows[e["sheet"]][e["row"]]
        lines.append(f"| {gid} | {e['format'].format(**r)} | {e['sheet']}, row {e['row'] + 2} | {r.get('setup_label')} "
                     f"| {r.get('outcome')} | {r.get('answers_n')} of {r.get('of_answers')} |")
    lines += ["", "The legend draft and the workbook caption are written by the same run from the same values, so "
              "their numbers are these records' by construction (legend_draft.md).", "",
              "## 2. Sentences of the letter and the manuscript that give a number for these panels or that the plate "
              "bears on", "",
              f"The submitted run's numbers are regenerated from `{rep['artifact']}` (sha256 {rep['sha256'][:12]}) "
              f"before anything is written ({rep['compared']} numbers). The letter cites that file for them "
              "(findings/letter_check/question_2.md:16, :26). These records: 135 questions x 3 draws per set-up; the "
              "submitted run: one answer per question on the 138-question index. A sentence is found in the "
              "document with every tracked change accepted. D304 (8 November): every sentence is the agreed text's "
              "(Claude Docs rev 3688) or the letter's with every mark accepted (provisional: the letter round will be "
              "rebuilt), or is retired with the reason; a number the agreed text prints from these records has no "
              "submitted value ('-'), and a table cell of the letter is held to the cell's text.", ""]
    for c in claims:
        loc = (f"{c['doc']}, under \"{c['where']['section']}\", paragraph opening \"{c['where']['paragraph_opening']}\""
               if c["found"] else f"{c['doc']}: retired, {c['retired']}" if c.get("retired")
               else f"{c['doc']}: NOT FOUND with every tracked change accepted (the text changed; re-read it)")
        lines += [f"### {c['id']}. {loc}", "", f"> {c['sentence']}", ""]
        if c["numbers"]:
            lines += ["| printed | what | submitted run (source) | these records (source) | as printed now | same |",
                      "|---|---|---|---|---|---|"]
        for x in c["numbers"]:
            sv, tv = x["submitted_value"], x["these_records"]
            sv = "-" if sv is None else sv if isinstance(sv, (bool, int)) else round(sv, 3)
            tv = "not in these records" if tv is None else tv if isinstance(tv, int) else round(tv, 3)
            lines.append(f"| {x['printed']} | {x['what']} | {sv} ({x['submitted_from']}) | {tv} "
                         f"({x['these_records_from']}) | {x['these_records_printed'] or '-'} | "
                         f"{'n/a' if x['same'] is None else 'yes' if x['same'] else 'no'}"
                         + ("" if x.get("cell_in_text") is None else
                            "; the letter's cell reads it" if x["cell_in_text"] else "; NOT the letter's cell") + " |")
        if c["bears"]:
            lines += ["", f"These records bear on it: {c['bears']}."]
        if c["judged_numbers"]:
            lines += ["", f"Not on this plate: {c['judged_numbers']}."]
        lines.append("")
    t = claims_tally(claims)
    lines += ["## 3. For W1", "",
              f"Sentences: {len(claims)}, retired {len(t['retired'])} ({', '.join(t['retired']) or 'none'}), not found "
              f"{len(t['not_found'])} ({', '.join(t['not_found']) or 'none'}). "
              f"{t['differ']} of {t['quoted']} quoted numbers differ from these records and {t['absent']} have no "
              f"counterpart here (naive RAG is not among these set-ups). Counting each submitted value once (the same "
              f"S77 cell quoted in several sentences): {t['values_differ']} of {t['values']} differ, "
              f"{t['values_absent']} have no counterpart. {', '.join(t['no_number']) or 'None'} gives no number; "
              "what the plate draws bears on it (its note above). Each such sentence describes the submitted run and is "
              "to be rewritten from the re-run's numbers once the plate is final (the runs it waits for are in the data "
              "stamp). Supplementary Table 8 (C7 and C14 to C18 are its caption and notes; C2 and C12 cite it) holds "
              "the submitted run's cost table (S77).", ""]
    return "\n".join(lines)


def public_argv(argv):
    """The command line as it may ship with the commit: a folder outside the repository (the mirror's copy, a
    temporary path) is written as <records>."""
    out = []
    for a in argv:
        p = Path(a)
        out.append("<records>" if p.is_absolute() and not p.resolve().is_relative_to(ROOT) else a)
    return out


def selftest(quiet=False):
    """Synthetic records through the plate's own calculations (audit of 18 October, defect 4): the wait taken off the
    clock time, the times adding up, the G2 answers planned from an out-of-date target, the verifier-wait summary, what
    is still owed, the documents' number formats, the command line kept free of temporary paths, and the known-value
    checks refusing records that disagree with them. Run by itself and at the start of every figure step; any failure
    stops the run before anything is written."""
    checks = []

    def ok(name, cond):
        checks.append((name, bool(cond)))

    def answer(lat, calls, q="q1", dr=1):
        g = {"stop_reason": "ok", "answer": "x", "latency_s": lat, "calls": calls,
             "tokens_used": sum((c.get("prompt_tokens") or 0) + (c.get("output_tokens") or 0)
                                + (c.get("thinking_tokens") or 0) for c in calls)}
        return {"question_id": q, "draw": dr, "ctx_uid": "c", "pid": 1, "generation": g}
    calls = [{"prompt_tokens": 10, "output_tokens": 5, "thinking_tokens": 1, "wall_s": 20.0, "provider": "ollama",
              "model": "m", "waited_for_server_s": 30.0},
             {"prompt_tokens": 10, "output_tokens": 5, "wall_s": 10.0, "provider": "gemini",
              "waited_for_server_s": 10.0},
             {"prompt_tokens": 2, "output_tokens": 0, "wall_s": 1.0, "provider": "gemini"}]
    x = exp01_row("k", answer(100.0, calls), "verified_pass")
    ok("clock less wait = latency - the calls' waits (100 - 30 - 10)", abs(x["clock_less_wait"] - 60.0) < 1e-9)
    ok("wait = the calls' waits, a call with no wait record adds none", abs(x["wait"] - 40.0) < 1e-9
       and x["waits"] == [30.0, 10.0])
    ok("model-call time = the calls' wall_s; local and API apart", (x["model"], x["model_local"], x["model_api"])
       == (31.0, 20.0, 11.0))
    ok("tokens = the sum over the calls", x["tokens"] == 33)
    try:
        check_times([x])
        ok("check_times passes times that add up", True)
    except SystemExit:
        ok("check_times passes times that add up", False)
    for name, bad in (("clock less wait not reduced", {"clock_less_wait": 100.0}), ("wait halved", {"wait": 20.0})):
        try:
            check_times([dict(x, **bad)])
            ok(f"check_times refuses: {name}", False)
        except SystemExit:
            ok(f"check_times refuses: {name}", True)
    y = exp01_row("k2", answer(50.0, calls[2:]), "single_pass")
    ok("an answer whose calls never waited: clock less wait = clock", y["clock_less_wait"] == 50.0 and y["wait"] == 0)
    # G2: the answers planned from an out-of-date target
    r10 = [{"key": f"r|{q}|d{dr}", "q": q, "prompt": 100, "stop": "final", "calls_n": 3}
           for q in ("q1", "q2", "q4", "q5") for dr in (1, 2)]
    r10[2]["prompt"] = 999                                       # q2 d1 reads differently now

    def src(q, dr=1):
        return {"answer_key": f"r|{q}|d{dr}", "input_tokens": 100, "stop_reason": "final", "n_calls": 3}
    g2 = [{"key": "m1", "q": "q1", "sources_full": [src("q1")]}, {"key": "m2", "q": "q2", "sources_full": [src("q2")]},
          {"key": "m3", "q": "q3", "sources_full": [src("q3")]}, {"key": "m4", "q": "q4", "sources_full": [src("q4")]},
          {"key": "m5", "q": "q5", "sources_full": [src("q5")]}]
    st = [z["key"] for z in g2_stale_answers({"rlm_10": r10, "matched_budget": g2}, {"rlm_10": {"r|q4|d2"}})]
    ok("G2 stale: a source read differently (m2), a source gone (m3), a left-out draw stored again (m4); not m1, m5",
       st == ["m2", "m3", "m4"])
    ok("G2 stale: nothing stored again, nothing changed: none",
       g2_stale_answers({"rlm_10": [dict(z, prompt=100) for z in r10], "matched_budget": [g2[0], g2[4]]}, {}) == [])
    # the verifier-wait summary
    vp = [{"clock": c_, "wait": sum(w), "waits": w, "model_local": ml, "model_api": ma}
          for c_, w, ml, ma in ((100.0, [50.0], 1.0, 4.0), (200.0, [0.0, 20.0], 2.0, 5.0), (300.0, [5.0], 3.0, 6.0))]
    v = vp_wait_summary(vp, {"x": [{"waits": [0.0, 0.5]}], "y": [{"waits": []}]})
    ok("verifier wait summary: calls, over 10 s, longest", (v["calls_with_a_wait_record"], v["calls_waiting_over_10_s"],
                                                            v["longest_wait_s"]) == (4, 2, 50.0))
    ok("verifier wait summary: mean wait 25 of mean clock 200 (12.5%)",
       abs(v["mean_wait_per_answer_s"] - 25.0) < 1e-9 and abs(v["mean_clock_per_answer_s"] - 200.0) < 1e-9
       and abs(v["wait_share_of_mean_clock"] - 0.125) < 1e-9)
    ok("verifier wait summary: local 2 s and API 5 s per answer; other set-ups' waiting calls",
       (v["mean_local_model_call_s_per_answer"], v["mean_api_model_call_s_per_answer"],
        v["other_exp01_calls_with_a_wait_over_0_s"]) == (2.0, 5.0, {"x": 1, "y": 0}))
    # what is still owed
    mb = [{"key": f"m{i}", "q": f"q{i}"} for i in range(3)]
    named = {"rlm_10": {"k1": OWED, "k2": OWED}, "cap5": {"a": OWED, "b": "stays_failed"}}
    again = {"rlm_10": {"k1"}, "cap5": {"b"}}
    r1 = rerun_status({"matched_budget": mb}, named, again, [mb[0]], False)
    ok("owed: Mentor::i 1 of 2 stored again, Zhang RLM 0 of 1 and 1 stays failed",
       (r1["G1"]["rerun"], r1["G1"]["stored_again"], r1["G6"]["rerun"], r1["G6"]["stored_again"],
        r1["G6"]["not_rerun"]) == (2, 1, 1, 0, {"stays_failed": 1}))
    ok("settled: G2 not yet checked by S455 leaves all its answers unsettled", r1["settled"] == TOTAL - 5)
    r2 = rerun_status({"matched_budget": mb}, named, again, [mb[0]], True)
    ok("settled: G2 checked; one planned from an old target, two reruns owed", r2["settled"] == TOTAL - 3)
    r3 = rerun_status({"matched_budget": mb}, {"cap5": {"b": "stays_failed"}}, {}, [], True)
    ok("settled: an answer that stays failed is settled", r3["settled"] == TOTAL and not r3["unsettled"])
    # what these records give for a quoted number
    fake = {s_: [{}] * 3 for s_, _ in SETUPS}
    fn_ = {"tokens_missing_answers": {s_: (3 if s_ == "single_pass" else 1 if s_ == "cap5" else 0) for s_, _ in SETUPS},
           "b": {"summary": {"rlm_10": {"mean": 120.0}, "single_pass": {"mean": 10.0}}, "ratio": 12.0}}
    ok("claims, these records: Mentori strategies and set-ups with no token count, set-ups with every count, set-ups, "
       "G2 answers", [ours((k,), "digits" if k != "g2" else "", fn_, fake)[1] for k in
                      ("g1_no_tokens", "no_tokens", "measured", "setups", "g2")] == ["1", "1", "8", "10", "3 answers"])
    ok("claims, these records: a mean, a ratio, a number with no counterpart",
       (ours(("mean", "b", "mean", "rlm_10"), "{:,.0f}", fn_, fake)[1],
        ours(("ratio", "b", "mean"), "{:.1f}", fn_, fake)[1], ours(("absent", "none here", "b"), "{:.1f}", fn_, fake))
       == ("120", "12.0", (None, None, "none here 12.0 (sheet b, set-up rows rlm_10 and single_pass)")))
    # the known-value checks refuse a record that disagrees with them (a weakened check would let it through)
    import contextlib
    import io
    import tempfile

    def refuses(f, *a):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                f(*a)
            return False
        except SystemExit:
            return True
    k5 = "exp_v4_s20_n0|rlm_5|15_rabies_tanzania_TE3|d3"
    g1d = {s_: [] for s_, _ in G1}
    g1d["rlm_5"] = [{"key": k5, "stop": "max_turns_partial"}]
    sh = {s_: G1_RERUN_CHECK["files"].get(s_, "") for s_, _ in G1}
    nm1, ag1 = {"rlm_5": {k5: OWED}}, {"rlm_5": {k5}}
    ok("G1 reruns: the stop reason the check read passes", not refuses(reproduce_g1_reruns, g1d, sh, nm1, ag1))
    ok("G1 reruns: another stop reason is refused",
       refuses(reproduce_g1_reruns, dict(g1d, rlm_5=[{"key": k5, "stop": "final"}]), sh, nm1, ag1))
    ok("G1 reruns: a rerun not stored again is refused", refuses(reproduce_g1_reruns, g1d, sh, nm1, {}))
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "matched_budget" / "g2_runs"
        d.mkdir(parents=True)
        plan = {"made": "t0", "questions": {"q1": {"top_k": 20, "target_tokens": 100.0, "planned_tokens": 110},
                                            "q2": {"top_k": 30, "target_tokens": 200.0, "planned_tokens": 200}}}
        (d / "g2_matched_budget_plan.json").write_text(json.dumps(plan))
        psha = sha256_file(d / "g2_matched_budget_plan.json")
        rows = [("m1", "q1", 110), ("m2", "q2", 200)]             # m1 at its planned tokens; m2 exactly at its target
        (d / "g2_matched_budget_reached.json").write_text(json.dumps({"plan_made": "t0", "answers": [
            {"answer_key": k_, "reached_tokens": r_} for k_, _, r_ in rows]}))
        (d / "g2_plan_check.txt").write_text("COUNTS: plan 2 questions, floor bound 0, unreachable 0, excluded 0, "
                                             "top_k median 25.0 max 30\n")
        (d / "g2_arm_check.txt").write_text("COUNTS: arm 2 of 2 stored (0 earlier attempts), 0 errors, 0 empty\n")
        (d / "g2_reached_check.txt").write_text("reached x: 2 answers; reached = planned 2; at or above the target 2; "
                                                "no single counted call 0\nCOUNTS: reached 2 answers, 2 at the planned "
                                                "tokens, 0 without a count\n")
        man_ = {"exp01": {"matched_budget": {"mtime": 1, "g2_runs": {f: {"mtime": 2} for f in G2_CHECK_FILES}}}}

        def g2rows(reach_m1=110):
            return {"matched_budget": [{"key": k_, "q": q_, "top_k": plan["questions"][q_]["top_k"], "error": None,
                                        "answer": "x", "reached_tokens": reach_m1 if k_ == "m1" else r_,
                                        "mb": dict(plan["questions"][q_], plan_sha256=psha)} for k_, q_, r_ in rows]}
        ok("G2: records that agree with the plan, the reached file and g2_check's COUNTS pass (a reply exactly at its "
           "target counts as at or above it)", not refuses(reproduce_g2, g2rows(), {"matched_budget": "x"}, Path(td),
                                                            man_, []))
        late = {"exp01": {"matched_budget": dict(man_["exp01"]["matched_budget"], mtime=3)}}   # COUNTS not compared
        ok("G2: reached tokens other than the reached file's are refused, COUNTS aside",
           refuses(reproduce_g2, g2rows(111), {"matched_budget": "x"}, Path(td), late, []))
    # the documents' number formats, and the command line
    ok("printed as the documents print", [printed_as(f, v_) for f, v_ in
                                          (("{:,.0f}", 44762.8), ("{:,.1f}", 2372.3), ("{:.1f}", 7.95), ("words", 7.95),
                                           ("words", 5.867), ("no", False), ("count", 0), ("count", 3), ("digits", 7.0),
                                           ("{:.2f}", 1))]
       == ["44,763", "2,372.3", "8.0", "eight times", "six times", "no", "none", "three", "7", "1.00"])
    ok("a temporary records folder is written as <records>",
       public_argv(["figure", "--records", "/private/tmp/x", "--n", "11"]) == ["figure", "--records", "<records>",
                                                                              "--n", "11"])
    bad = [n_ for n_, c_ in checks if not c_]
    if bad:
        raise SystemExit(f"selftest FAILED, nothing written: {bad}")
    if not quiet:
        print(f"selftest: {len(checks)} of {len(checks)} checks pass")
    return len(checks)


# ---------------------------------------------------------------------------------------------------------------
def merge_g13(rec_dir: Path, data: dict) -> tuple[dict, dict, float]:
    """G13 (D236, D237): data with G2's 15 replanned answers read from G13's records (scripts/g13_merge.py merge_answers,
    which refuses unless exactly those 15 keys change), each made by exp01_row as G2's are. Returns (data, report with
    the inputs' sha256, the time of G13's last call end as a POSIX time, the 15's "records of" time)."""
    import g13_merge as M
    try:
        sums = M.check_sums()
        merged, mrep = M.merge_answers(last_lines(rec_dir / "matched_budget" / "answers.jsonl"))
        s455 = M.s455_clean()
    except M.Refused as e:
        raise SystemExit(f"G13: {e}") from None
    old = {x["key"]: x for x in data["matched_budget"]}
    if set(old) != set(merged):
        raise SystemExit(f"G13: the plate's matched-budget keys are not the merge's ({len(set(old) ^ set(merged))} differ)")
    new = set(mrep["replaced_keys"])
    rows = [exp01_row(k, merged[k], "matched_budget") if k in new else x for k, x in old.items()]
    check_times(rows)
    uids = {merged[k]["ctx_uid"] for k in new}
    ends = []
    with open(M.ANSWERS.parent / "calls.jsonl") as fh:
        for ln in fh:
            if ln.strip():
                c = json.loads(ln)
                if c.get("ctx_uid") in uids and c.get("at"):
                    ends.append(datetime.fromisoformat(c["at"]).timestamp() + (c.get("wall_s") or 0.0))
    if not ends:
        raise SystemExit("G13: no call record of the 15 holds a time")
    out = dict(data)
    out["matched_budget"] = rows
    G13_PROCESSES["matched_budget"] = {merged[k]["pid"]: G13_COMMIT for k in new}
    return out, {**{k: v for k, v in mrep.items() if k != "replaced_keys"}, "replaced_keys": sorted(new),
                 "s455": s455, "inputs_sha256": {**sums, "scripts/g13_merge.py": sha256_file(ROOT / "scripts/g13_merge.py"),
                                                 s455["scan"]: s455["scan_sha256"]}}, max(ends)


def figure(args):
    global CIVIDIS_R
    figure_lock_agreed()
    print(f"selftest: {selftest(quiet=True)} checks pass")
    nm = naming(args.kind, args.n)
    CIVIDIS_R = _cividis_r()
    data, qs, qtype, inputs, newest, man, shas = load(Path(args.records).resolve(), nm)
    rep, named, again = reproduce(data, shas, man)
    rep["g1_reruns"] = reproduce_g1_reruns(data, shas, named, again)
    g2_from = g2_stale_answers(data, again)
    rep["g2"] = reproduce_g2(data, shas, Path(args.records).resolve(), man, g2_from)
    if G13_MERGE:                       # D236, D237: the gate above read G2's own file; the plate reads the arm as now
        data, rep["g13"], g13_end = merge_g13(Path(args.records).resolve(), data)
        g2_from = g2_stale_answers(data, again)
        if g2_from:
            raise SystemExit(f"G13: {len(g2_from)} matched-budget answers still planned from an out-of-date target "
                             f"after the merge, first {g2_from[0]['key']}")
        rep["g13"]["out_of_date_after_merge"] = 0
        inputs.update(rep["g13"]["inputs_sha256"])
        newest = max(newest, g13_end)
    rep["claims"] = claims_reproduce()                 # S77 only (the submitted run's artifact), no document
    collect = [json.loads(x) for x in G1_COLLECT.read_text().splitlines() if x.strip()]
    inputs[str(G1_COLLECT.relative_to(ROOT))] = sha256_file(G1_COLLECT)
    fn = compute(data, qtype, named, collect)
    g1_n = sum(len(data[s]) for s, _ in G1)
    g2_n = sum(len(data[s]) for s, _ in G2)
    g6_n = sum(len(data[c]) for c, _ in G6)
    n_in = g1_n + g2_n + g6_n               # load() refuses a set-up short of its 405 answers, so this is TOTAL
    rerun = rerun_status(data, named, again, g2_from, bool(rep["g2_scans_of_the_current_file"]))
    if args.final and rerun["unsettled"]:
        raise SystemExit(f"--final: {rerun['settled']} of {TOTAL} answers settled; {rerun_state(rerun)}; the plate "
                         f"stays provisional")
    final = args.final
    stamp = (                               # Q9 (Valerio, 11 Nov): no PROVISIONAL in any stamp
        f"{rerun['settled']:,} of {TOTAL:,} answers settled (all {n_in:,} stored: G1 {g1_n:,}, G2 {g2_n}, G6 "
        f"{g6_n:,}; settled: no rerun owed, no matched-budget token target out of date, checked by S455 for the D89 "
        f"and D90 Gemini cases), judged only in a's split columns, records of {iso_local(newest)}; {rerun_state(rerun)}")
    tag = ""                                # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    out = Path(args.out).resolve() if getattr(args, "out", None) else nm["out"]    # rebuild --out (D155)
    out.mkdir(parents=True, exist_ok=True)
    for old in sorted(set(out.glob(f"{nm['plate']}*")) | set(out.glob(f"{nm['stem']}*"))):   # the data's name
        old.unlink()                                                                          # starts with the plate's
    paths = {x: out / f"{nm['plate']}{tag}.{x}" for x in ("pdf", "svg", "png")}
    W, H, printed, overlaps, pitch = draw_plate(fn, paths, nm)
    FR.check_pdf_deterministic(paths["pdf"])            # D155: finish_plate saves no date; refuse one
    FR.check_svg_deterministic(paths["svg"])
    sheets = sheets_of(fn, nm)
    sd = out / f"{nm['stem']}{tag}.xlsx"
    write_source_data(sheets, sd)
    FR.deterministic_xlsx(sd)                           # D155: no write time; every cell as written
    tc = Counter(qtype.values())
    types = {"extractive": "extractive", "synthesis": "synthesis", "refutation": "false premise",
             "not_answerable": "not answerable"}
    extra = {"types": ", ".join(f"{tc[k]} {v}" for k, v in types.items()) + f" ({tc['extractive'] + tc['synthesis']} "
                      f"answerable)", "search_n": sum(1 for s_, _ in EXP01 for x in data[s_] if x["search_timed"]),
             "tc": dict(tc), "commits": g1_commits(data, man)}
    vm = sorted({m for x in data["verified_pass"] for m in x["local_models"]})
    extra["verifier"] = " and ".join(vm) + (" (gpt-oss:20b with the date fixed, LOCK [date])"
                                            if vm == ["gpt-oss:20b-date20261010"] else "")
    ks = sorted(x["top_k"] for x in data["matched_budget"])
    extra["g2_topk"] = f"median {half_up(float(__import__('statistics').median(ks)), 0)}, smallest {ks[0]}, " \
                       f"largest {ks[-1]}"
    for k_, fld in (("gen_model", "gen_model"), ("pkg", "pkg"), ("max_iter", "max_iterations")):
        vals = sorted({str(x[fld]).split("::")[-1] for s_, _ in (SETUPS if k_ == "gen_model" else G6) for x in data[s_]},
                      key=lambda v: (len(v), v))
        if k_ != "max_iter" and len(vals) != 1:
            raise SystemExit(f"{k_}: more than one value in the records: {vals}")
        extra[k_] = ", ".join(vals[:-1]) + " and " + vals[-1] if len(vals) > 1 else vals[0]
    legend, cap = legend_and_caption(fn, stamp, n_in, extra, nm, rerun, getattr(args, "command", None))
    claims = claims_now(fn, data) if CLAIMS_OUT is not None else None   # D2: the editorial step only
    numbers = out / f"{nm['side']}_numbers.json"
    numbers.write_text(json.dumps({"stamp": stamp, "what": f"every number the plate draws, sheet by sheet as the data "
                                   f"workbook {sd.name} holds them (S448 R8 compares the workbook with this file)",
                                   "sheets": {nm_: {"columns": c, "rows": r} for nm_, c, r in sheets},
                                   "printed": printed,
                                   "printed_what": "every number printed on the plate: the SVG group id of its text, "
                                                   "and the workbook sheet and row and format it is written "
                                                   "from (S448 R8 (6))"}, indent=1, default=str) + "\n")
    (out / "legend_draft.md").write_text(legend)
    capf = out / f"{nm['stem']} caption{tag}.md"
    capf.write_text(cap)
    if CLAIMS_OUT is not None:                         # D2: the editorial step's folder, never the plate's
        CLAIMS_OUT.mkdir(parents=True, exist_ok=True)
        (CLAIMS_OUT / "claims.md").write_text(claims_md(nm, stamp, printed, sheets, claims, rep["claims"]))
        (CLAIMS_OUT / "claims.json").write_text(json.dumps(
            {"stamp": stamp, "what": f"the claims list of {nm['plate']} (D82): each sentence of the documents with its "
             "numbers, from the submitted run (S77) and from these records; the numbers file's \"claims\" key until D2",
             "documents_sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in DOCS.values()},
             "claims": claims}, indent=1, default=str) + "\n")
    prov = {
        "provenance": {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
                       "command": getattr(args, "command", None)
                       or "uv run --frozen python " + SCRIPT + " " + " ".join(public_argv(sys.argv[1:])),
                       "python": platform.python_version(),
                       "deterministic": "D155: no build time and no repository HEAD are recorded; the script's and "
                                        "every input's sha256 identify the build",
                       "inputs_sha256": inputs, "model_calls": 0},
        "stamp": stamp, "named": f"{nm['plate']}: FIGURE_LOCK [files] "
                                 f"{'supplementary_name' if nm['supp'] else 'name'} with --n {nm['n']} (D95 Q200, Q208)",
        "reproduced": rep, "reruns": rerun, "page_mm": [W, H], "dot_row_pitch_mm": pitch,
        **({"g6_readings": G6_READINGS} if G6_READINGS is not None else {}),
        "lock": {"path": "experiments/LOCK.toml", "sha256": sha256_file(LOCK),
                 "records": {"G1 and G2 (calls.jsonl, calls per lock sha256, read by mirror)":
                             {s_: man["exp01"][s_]["calls_lock_sha256"] for s_, _ in EXP01},
                             "G6": sorted({x["lock"] for c, _ in G6 for x in data[c]})}},
        "figure_lock": {"path": str(FIGURE_LOCK.relative_to(ROOT)), "sha256": sha256_file(FIGURE_LOCK),
                        "status": FLOCK.get("status")},
        "font": FONT, "type_pt": {"panel letters": PT_LETTER, "all other text": PT},
        "records_manifest": man,
        "dots_overlapping": overlaps,
        "notes": {"verifier_status_report": fn["vrep"]["status_counts"],
                  "verifier_not_ok": fn["vrep"]["not_ok"],
                  "verified_pass_answers_with_some_passage_unverified": fn["vp_some_passage_unverified"],
                  "g6_answers_with_a_missing_token_count": fn["g6_tokens_missing"],
                  "exp01_answers_with_a_call_without_tokens": fn["g1_calls_without_tokens"],
                  "exp01_calls_without_wall_s": fn["g1_calls_without_wall"], "exp01_pool_size": fn["pools"],
                  "s455_listed_by_setup": {s: dict(sorted(v.items())) for s, v in named.items()},
                  "d89_d90_stored_again_by_setup": {s: sorted(v) for s, v in again.items()},
                  "verified_pass_server_wait": fn["vp_wait"], "g6_time": fn["g6_time"],
                  "g6_answers_ok_with_no_text_by_stop_reason": fn["g6_empty_ok"],
                  "exp01_answers_per_commit": extra["commits"],
                  "exp01_clone_head_when_copied_is_not_the_run_commit": "records_manifest.json exp01.<set-up>."
                  "processes gives each process's commit from the Studio's start records"},
        "files": {p.name: sha256_file(p) for p in list(paths.values()) + [sd, capf, numbers, out / "legend_draft.md"]},
    }
    (out / f"{nm['side']}_provenance.json").write_text(json.dumps(prov, indent=1, default=str) + "\n")
    print(stamp)
    print(f"wrote {', '.join(p.name for p in paths.values())} ({W:.0f} x {H:.1f} mm, dot rows {pitch} mm apart), "
          f"{sd.name}, {capf.name}, {numbers.name}, legend_draft.md, {nm['side']}_provenance.json into "
          f"{out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print(f"dots overlapping per panel and set-up: {overlaps}")
    if claims is None:
        return
    t = claims_tally(claims)
    print(f"claims: {len(claims)} sentences ({sum(1 for c in claims if c['found'])} found in their document); of "
          f"{t['quoted']} quoted numbers {t['differ']} differ from these records and {t['absent']} have no counterpart "
          f"here (per submitted value: {t['values_differ']} of {t['values']} differ, {t['values_absent']} no "
          f"counterpart); {len(t['no_number'])} with no number (claims.md)")


REBUILD_CMD = "uv run --frozen python scripts/S457_fig2_panels.py rebuild"
MIRROR_TAR = "s457_mirror_20261022"            # A1d: the mirror the committed plate read (records_manifest.json)
G6_CALLS_TAR = "g6_calls_before_d89"
G6_MTIMES_JSON = ROOT / "findings" / "recompute" / "frozen_inputs" / "g6_before_d89_mtimes.json"
# D160 (7) Q23 (Valerio, 27 October, "Yes, as D156"): the plate draws G6's records after the D135 reruns, frozen by
# frozen_inputs/freeze_g6_d135.py (answers in findings/recompute/g6_d135_inputs/, their source mtimes in its
# SOURCE_MTIMES.json, the calls of caps 5, 10 and 20 in g6_calls_after_d135.tar); reproduce() first runs on the
# records before them (S455's listed G6 answers read with S455's stop reasons, the files S455 read), the gate. Until
# the set is frozen the plate draws the records before the reruns, as before D160.
G6_D135 = ROOT / "findings" / "recompute" / "g6_d135_inputs"
G6_D135_CALLS_TAR = "g6_calls_after_d135"
G6_READINGS: dict | None = None        # rebuild: which G6 reading was gated and which drawn, into the provenance
G13_MERGE = False                      # rebuild: G2's 15 replanned answers from G13 (D236, D237; merge_g13)
G13_PROCESSES: dict = {}               # merge_g13: {"matched_budget": {pid: commit label}} for g1_commits
G13_COMMIT = "the G13 clone's commit (g13_arm.start.json, on the Studio, not copied)"


def recorded_as_frozen(key: str) -> str:
    """The frozen label of an input the committed provenance (22-23 October, before D155) names: the Studio records
    by the mirror's copy of them, G6's by their frozen copies; any other key unchanged."""
    m = re.fullmatch(r"Studio:projects/mentori-runs/findings/runs/exp_01__(\w+)__" + INDEX + r"/answers\.jsonl", key)
    if m:
        return f"frozen:{MIRROR_TAR}.tar/{MIRROR_TAR}/{m.group(1)}/answers.jsonl"
    m = re.fullmatch(r"Studio:projects/mentori-runs/findings/recompute/G2_runs/([\w.]+)", key)
    if m:
        return f"frozen:{MIRROR_TAR}.tar/{MIRROR_TAR}/matched_budget/g2_runs/{m.group(1)}"
    m = re.fullmatch(r"findings/runs/(b4_rlm_ref__cap\d+__all135)/(answers|calls)\.jsonl", key)
    if m:
        return (f"frozen:L2/g6/{m.group(1)}/answers.jsonl" if m.group(2) == "answers"
                else f"frozen:{G6_CALLS_TAR}.tar/{G6_CALLS_TAR}/{m.group(1)}/calls.jsonl")
    return key


def rebuild(args):
    """D155: Supplementary Figure 17 again from the frozen copies only, checked against the committed record.

    G13 (D236, D237): after the gate has read G2's own file (reproduce_g2: its plan, reached file, COUNTS and the 15
    answers planned from an old target), G2's 15 replanned answers are read from G13's records (merge_g13), and none
    may still be planned from an out-of-date target.
    Reads: the G1 and G2 records from the frozen mirror (s457_mirror_20261022.tar, A1d; each file also checked
    against records_manifest.json, as figure does); G6's answers from findings/recompute/L2_inputs/g6/ (committed,
    each against frozen_inputs/SHA256SUMS) and its calls from g6_calls_before_d89.tar, the bytes of 23 October (the
    D89 rerun of 24 October rewrote findings/runs/); G6's source mtimes from g6_before_d89_mtimes.json (committed).
    Before anything is drawn, every frozen input the committed supplementary_figure17_provenance.json records must have
    that sha256 (fig_repro.check_recorded; its keys of 22-23 October translated by recorded_as_frozen). --out (default
    the plate's folder) is where the files go. D160 (7) Q23: when findings/recompute/g6_d135_inputs is frozen, the gate
    runs reproduce() on the G6 records before the D135 reruns, then the plate is drawn from the records after them
    (answers there, calls in g6_calls_after_d135.tar, mtimes in its SOURCE_MTIMES.json); provenance g6_readings."""
    global G6_ANSWERS_DIR, G6_CALLS_DIR, G6_MTIMES, G6_READINGS, G13_MERGE
    G13_MERGE = True
    nm = naming(DEFAULT_AS, DEFAULT_N)
    prov_p = nm["out"] / f"{nm['side']}_provenance.json"
    if not prov_p.exists():
        raise SystemExit(f"{prov_p.relative_to(ROOT)} is missing: there is no committed plate to rebuild")
    recorded = json.loads(prov_p.read_text())["provenance"]["inputs_sha256"]
    rec_dir = FR.frozen(MIRROR_TAR, MIRROR_TAR)
    G6_ANSWERS_DIR = FR.check_committed(FR.frozen("L2", "g6"))
    G6_CALLS_DIR = FR.frozen(G6_CALLS_TAR, G6_CALLS_TAR)
    mt = json.loads(FR.check_committed(G6_MTIMES_JSON).read_text())["files"]
    G6_MTIMES = {k: v["mtime"] for k, v in mt.items()}
    now = {}
    for c, _ in G6:
        for q in (g6_path(c), g6_calls_path(c)):
            want = mt[f"findings/runs/{g6_run(c)}/{q.name}"]["sha256"]
            got = sha256_file(q)
            if got != want:
                raise SystemExit(f"{q}: sha256 {got[:12]} is not the {want[:12]} {G6_MTIMES_JSON.name} records")
            now[FR.frozen_label(q)] = got
    for q in [rec_dir / s_ / "answers.jsonl" for s_, _ in EXP01] + [rec_dir / "matched_budget" / "g2_runs" / f
                                                                    for f in G2_CHECK_FILES]:
        now[FR.frozen_label(q)] = sha256_file(q)        # the mirror's files load() reads
    now[FR.frozen_label(G6_MTIMES_JSON)] = sha256_file(G6_MTIMES_JSON)
    post = FR.check_committed(FR.frozen("g6_d135")) if G6_D135.exists() else None
    if post is not None:                           # D160 Q23: the records after the D135 reruns, each file checked
        post_calls = FR.frozen(G6_D135_CALLS_TAR, G6_D135_CALLS_TAR)
        mt_post = json.loads((post / "SOURCE_MTIMES.json").read_text())["files"]
        for c, _ in G6:
            for q in (post / g6_run(c) / "answers.jsonl", post_calls / g6_run(c) / "calls.jsonl"):
                want = mt_post[f"findings/runs/{g6_run(c)}/{q.name}"]["sha256"]
                if sha256_file(q) != want:
                    raise SystemExit(f"{q}: not the file SOURCE_MTIMES.json records")
                now[FR.frozen_label(q)] = want
        now[FR.frozen_label(post / "SOURCE_MTIMES.json")] = sha256_file(post / "SOURCE_MTIMES.json")
    try:
        seen = FR.check_recorded(now, recorded, recorded_as_frozen)
    except FR.FrozenInputError as e:
        raise SystemExit(f"REFUSED: {e}") from None
    print(f"frozen inputs: {seen['compared']} recorded by the committed plate, each equal; "
          f"{len(seen['not_recorded_before'])} read and not recorded before")
    if post is None:
        G6_READINGS = {"gated": "findings/recompute/L2_inputs/g6 and g6_calls_before_d89.tar (G6 before the D135 "
                                "reruns)",
                       "drawn": f"the same: G6 after the reruns not frozen yet (findings/recompute/g6_d135_inputs missing)"}
    else:
        # the gate: the records before the reruns, where every G6 answer S455 lists is read with S455's stop reason
        data0, _, _, _, _, man0, shas0 = load(rec_dir.resolve(), nm)
        rep0, _, _ = reproduce(data0, shas0, man0)
        G6_ANSWERS_DIR, G6_CALLS_DIR = post, post_calls
        G6_MTIMES = {k: v["mtime"] for k, v in mt_post.items()}
        G6_READINGS = {"gated": "findings/recompute/L2_inputs/g6 and g6_calls_before_d89.tar (G6 before the D135 "
                                "reruns): reproduce() on them",
                       "gate_reproduce": rep0,
                       "drawn": f"findings/recompute/g6_d135_inputs and {G6_D135_CALLS_TAR}.tar (G6 after the D135 reruns, "
                                f"D160 Q23): every panel, sheet and the stamp"}
    figure(argparse.Namespace(kind=DEFAULT_AS, n=DEFAULT_N, records=str(rec_dir), final=False, out=args.out,
                              command=REBUILD_CMD))


def main(argv=None):
    FR.pin_hash_seed()                              # D155: PDF font subsets depend on the string-hash seed
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    name = argparse.ArgumentParser(add_help=False)
    name.add_argument("--as", dest="kind", choices=("supplementary", "main"), default=DEFAULT_AS,
                      help=f"the plate's kind (D95 Q208); default {DEFAULT_AS}")
    name.add_argument("--n", type=int, default=DEFAULT_N, help=f"the figure number; default {DEFAULT_N}")
    m = sub.add_parser("mirror", parents=[name])
    m.add_argument("--to", required=True, help="folder for the G1 and G2 copies (outside the repository is fine)")
    f = sub.add_parser("figure", parents=[name])
    f.add_argument("--records", "--g1", dest="records", required=True,
                   help="the folder mirror copied the G1 and G2 records into")
    f.add_argument("--final", action="store_true")
    f.add_argument("--claims-out", help="D2: also write the claims list (claims.md, claims.json) into this folder")
    sub.add_parser("selftest", help="the plate's calculations on synthetic records; writes nothing")
    rb = sub.add_parser("rebuild", help="Supplementary Figure 17 from the frozen inputs (D155)")
    rb.add_argument("--out", help="default the plate's folder, findings/figures_provisional/supp_fig17_outcomes")
    rb.add_argument("--claims-out", help="D2: also write the claims list (claims.md, claims.json) into this folder")
    args = ap.parse_args(argv)
    global CLAIMS_OUT
    if getattr(args, "claims_out", None):
        CLAIMS_OUT = Path(args.claims_out).resolve()
    {"mirror": mirror, "figure": figure, "rebuild": rebuild, "selftest": lambda a: selftest()}[args.cmd](args)


if __name__ == "__main__":
    main()
