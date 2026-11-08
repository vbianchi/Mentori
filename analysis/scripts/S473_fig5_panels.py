#!/usr/bin/env python3
"""S473 - Figure 5, comparing the signals: the first provisional plate, from the rows scored so far on G1's answers.

WHY. Figure 5 compares signals measured against two references (D35, experiments/LIST.md "Figure 5"): the answer key
(the judge's correctness, concept recall) and the papers (MiniCheck grounding against the whole source papers). D95
Q210 fixed the panels and their order: the trade-off between the key and the papers first, the ranks under each signal
with Kendall's W on the six Figure 3 strategies (D95 Q210 also named the matched-budget arm G2 and the authors' RLM
G6 as extra points outside W; this script reads neither and the plate draws neither, audit 27 Oct F13), faithfulness
last, and only from the judge with passages (D75 Q97). The figure story review
(findings/audits/FIGURE_STORY_REVIEW_2026-10-18.md, "Figure 5") lists the same panels: a per strategy, pass rate
against the key beside MiniCheck grounding against the papers; b each answer as a dot, key on x and papers on y, with
one labelled example (15_rabies_tanzania_FR1); c ranks under each signal and W by Rule 7; d faithfulness from the
judge with passages. The paper's faithfulness claims (S393 E8 ceiling, E9 and E10 grounding by judge score) sit on d
and e. RAGAS and RAGChecker (K1, D28, D80 V10) are read and counted here, not drawn (the review puts them in the
Supplementary; a question for Valerio). D106 and D114 Q32: the analysis starts on the rows done, labelled
provisional, and is rerun with the same command when the scorers end. D84: exploratory phase, no new analysis rule;
each statistic is one LIST.md states (Rules 2, 7, 8, 10), cited where computed. D116: nemotron-3-nano:30b is in no
Figure 5 data (G1's generator is gemini-3-flash-preview, D27).

THE SIGNALS, per answer of the 86 answerable questions (Rule 8; the 39 not-answerable and the ten false-premise
questions are outside every Figure 5 statistic, D11):
  judge correctness   S3's plain call (a), devstral-small-2:24b (LOCK [judge]); read through S463's own reader of the
                      collect output, so every check S463 makes on Figure 3's scores is made here too. Pass = score 4
                      or more (Rule 5, D154: the pass rate); score 3 or more is the relaxed threshold, written to
                      Source Data (sheet a's relaxed rows, sheet b's judge_pass_relaxed_3), not drawn. Every text
                      that names a threshold (axis label, sheet a's signal names, sheet b's relaxed column, legend,
                      caption, claim F5-6) is written
                      from PASS_T and PASS_RELAXED (D160 (6), Q18; selftest checks it with the two set to 3 and 2).
                      Sheet a's pass rates, intervals and questions at both thresholds must equal Figure 3's committed
                      sheet 3a for the same answers (check_fig2: Figure 3 written from the same G1 collect), or
                      nothing is written (D160 (6), Q18). Rule 10: an answer with no text is a
                      fail (score 0 in the mean), a judge call that gave no score is left out and counted.
  concept recall      plan row L3 (S471, findings/recompute/L3/concept_recall.jsonl), D12's loose matcher,
                      provisional until P2's labels choose the matcher (D114 Q37 O-a). Rule 10: an empty answer 0.
  grounding (papers)  plan row L1, papers stage (S470): MiniCheck precision of the answer's claims against its whole
                      source papers, draw 1 only (D114 Q32 O-a), on the Beelink. Rule 10: null with a reason when the
                      answer has no claim or an input over MiniCheck's 2,048-token cut; nulls counted.
  faithfulness        S3's call with passages (b), the judge's faithfulness score 0 to 5 (D75 Q97), phase 3. Panel d
                      counts scored calls only: an answer with no text gets no call (status no_answer,
                      experiments/scorers/judge_passages.py:272) and a call that gave no score (error) are left out,
                      not scored 0, and counted per strategy in sheet d (left_out_no_text, left_out_unscored) and in
                      the legend (audit 27 Oct F3).

THE STATISTICS (LIST.md):
  Rule 2   a strategy's rate is the mean over questions of the question's share over its draws; its interval the
           95% percentile interval of 10,000 question resamples (S463.interval, S407's seed and counts).
  Rule 7   a signal's score for a strategy is its mean over the strategy's answers, every question weighted equally
           over its draws; W, the 3 x 3 Spearman matrix, mean pairwise rho, PC1 share and participation ratio on those
           means as S26 and S318 computed them; W's P exact over every ordering (raters 2 and 3 over the 720 orderings
           of six, S318 _w_p_untied_null); intervals from 10,000 question resamples, all draws and strategies of a
           question together; answer-level correlations (faithfulness against grounding, S393 E10) with a question
           bootstrap interval and no plain Spearman P. The judge's signal in W is its mean correctness score (0 to 5),
           as S26's "judge" mean, and the papers' signal MiniCheck precision, D35's reference in place of S26's
           MiniCheck F1 against the key.
  Provisional: while L1's papers stage is partial, every W statistic is computed on the questions whose six draw-1
  answers all have an L1 papers row (L1 scores a question's six strategies together, S470 "Order and shards"); at the
  end that is all 86 and the statistic is Rule 7's as written. The questions are listed in the numbers file.

REPRODUCE BEFORE WRITING (README.md:75-79). Before any new number, this script's own W, Spearman matrix, PC1 share
and participation ratio give the published one-run values from S26's and S30's deposited inputs (W 0.927, mean rho
0.9037, PC1 0.9361, participation ratio 1.137, LIST.md "Analysis rules", S318 g3_ranking), W's exact P equals S318's
own function, the question bootstrap counts equal S463's (S407's seed), and the L3 rows read here give L3's header
counts (1,728 scored, by status). A mismatch stops the run, nothing written.

COMMANDS, from the repository root (uv run only; no model call, nothing written on any other machine):
  pull     uv run --frozen python scripts/S473_fig5_panels.py pull --to <new dir>
           Read-only copies: S3's G1 outs through S463's own pull (ssh with the script on stdin) and its collect;
           from the Studio L1's header and rows (L1 runs there since 24 Oct, D134) and the K1 rows of its two
           workers; from the Beelink the K1 rows of its two workers; from the laptop the K1 worker's rows. Each remote reader is a script sent on stdin (no
           folder of a running job and no port on any command line, K1 README "busy guard"); a file still being
           appended is cut after its last whole line. PULL.json records what came from where and when. The laptop's
           reader runs under this script's own interpreter (uv's), never the system python3 (INVENTORY A8, the
           26 October inventory, findings/audits/scratch_repro_2026-10-26/INVENTORY.md); the Studio and the
           Beelink run it with their own python3 over ssh. S463's pull (its S3 part) is S463's code.
  figure   uv run --frozen python scripts/S473_fig5_panels.py figure [--from <dir>] --out <folder>
           D166 (28 October): findings/figures_provisional/fig5/ holds the locked Figure 5, which
           scripts/S497_fig5_d166.py draws (S494 calls S497 for Figure 5). This command draws S473's own plate of 26
           October (the design before D166) and refuses to run without --out, so it never overwrites the locked plate.
           Reproduces, reads, checks, computes and writes into --out:
           "Figure 5 (provisional, <n> of <m>).{pdf,svg,png}", "Source Data Fig. 5 (...).xlsx" and its caption,
           figure5_numbers.json, figure5_provenance.json and legend_draft.md (what S448 reads). n of m: n counts the
           draw-1 answerable answers with a final row from all four scorers (a null or an unscored row with a final
           status counts; see compute's all4), m the 516 planned for MiniCheck against the papers (PLANNED["papers"]).
           Without --from it reads the frozen inputs (below); --from <dir> reads a new pull's folder instead.
  selftest uv run --frozen python scripts/S473_fig5_panels.py selftest
           The frozen-input checks pass on the frozen copies and refuse each of five altered inputs (mutants); every
           threshold text follows PASS_T and PASS_RELAXED (set to 3 and 2, no text still names 4), and a typed
           axis label or sheet b column is refused; check_fig2
           passes on this script's plate of 26 October and the committed Figure 3 and refuses a moved rate and another
           G1 collect (D160 (6), Q18). Its figure5_numbers.json is read from git at a16b2460 (FIG5_S473_AT), the last
           commit that changed that file, since D166 replaced the files in fig5/.

THE ONE COMMAND of this script's plate (D155), from the repository root, with the two tars below in FROZEN_TARS
(default ~/Mentori_scratch_keep/frozen_2026-10-26, or the Zenodo deposit's data files):
    uv run --frozen python scripts/S473_fig5_panels.py figure --out <folder>
It rebuilds the plate of 26 October (PDF, SVG, PNG, Source Data workbook, its caption, figure5_numbers.json,
figure5_provenance.json, fig5_data_state.json, legend_draft.md, claims.md) into <folder>; until D166 these were the
committed files of findings/figures_provisional/fig5/ (last changed at ace13d12; figure5_numbers.json, the one file the
selftest reads, last changed at a16b2460). S497 imports this script's pull, readers,
checks, reproduce(), compute(), build_sheets() and check_fig2().

D201 Q2 (Valerio, 2 November 2026, yes). Figure 3 moved to key v2.5 and Figure 5 has not, so check_fig2 would compare key
v2.4 rows with key v2.5 rows and refuse. It now reads figure3_provenance.json and figure3_numbers.json at commit
FIG3_V24_AT (94262a0e, the last one on key v2.4) through git show, as S511 and S532 pin Figure 3, so this script's selftest
and build and S497's D166 fallback keep testing the same 48 values on key v2.4. S497's D200 path, which reads key v2.5
rows, passes at=None and compares with the plate's current files. The pin stops proving the v2.4 numbers against the live
plate, which is the point: the selftest kills a run read through the live files, and a revision that does not resolve.

FROZEN INPUTS (D155, through scripts/fig_repro.frozen(); no scratch folder, no live pull; the tars from FROZEN_TARS):
  findings/recompute/fig5_inputs/      PULL.json, l1/, k1/ and s3/'s two files that differ from Figure 3's pull (the
                                       collect's sidecar g1_collect.jsonl.json and PULL.json); s3/IDENTICAL_FILES.tsv
                                       names the rest of the 23 October pull's s3/ by sha256 and where the same bytes
                                       are frozen, and every one of those is checked here.
  findings/recompute/fig2_inputs/      g1_collect.jsonl (f5ff75bc) and the outs out/ and out_g1r15/ it was collected
                                       from (S463.read_collect checks their start files, headers and rechecks).
  k1_inputs_runs.tar                   K1's copy of G1's generation records (formerly ~/k1_inputs/runs); S463's
                                       MANIFEST.sha256 beside it is written from the tar's committed member list.
  fig2_g1r15_inputs.tar                the 15 G1R15 reruns' records, with their MANIFEST.sha256.
  repository files                     L3's rows and header, S26's and S30's deposited inputs, G1's rerun list.
The collect's sidecar names the folders it was collected from (the 23 October pull's s3/out and s3/out_g1r15);
S463.read_collect finds those folders through it, so the build reads a copy of the sidecar with that one folder
prefix replaced by fig2_inputs/ (proved byte-equal by IDENTICAL_FILES.tsv), in a temporary folder. Every input's
sha256 is recorded in figure5_provenance.json ("inputs_sha256") and must equal FROZEN_SHA256 below, the values the
committed plate of 26 October (a9ea9ad7) recorded, or, for a file it did not record, findings/recompute/
frozen_inputs/SHA256SUMS (or the tar's member list); one that differs stops the build, nothing written.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import itertools
import json
import re
import subprocess
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S457 = _load("S457", ROOT / "scripts" / "S457_fig2_panels.py")
S463 = _load("S463", ROOT / "scripts" / "S463_fig2_ranking.py")
FR = _load("fig_repro", ROOT / "scripts" / "fig_repro.py")      # D155: frozen inputs, deterministic files

SCRIPT = "scripts/S473_fig5_panels.py"
OUT = ROOT / "findings" / "figures_provisional" / "fig5"
L3_DIR = ROOT / "findings" / "recompute" / "L3"
S26_JSON = ROOT / "findings" / "recompute" / "S26_signal_redundancy.json"
S30_CSV = ROOT / "findings" / "recompute" / "S30_baseline_scores_full.csv"
MJ_CSV = ROOT / "findings" / "recompute" / "master_join.csv"
STUDIO = S463.STUDIO
BEELINK = ["-p", "2222", "valeriob@100.105.190.7"]
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
CONFIGS = list(S463.CONFIGS)
LABEL = dict(S463.LABEL)
INDEX = S463.INDEX
DRAWS = (1, 2, 3)
N_ANSWERABLE = 86
EXAMPLE = ("verified_pass", "15_rabies_tanzania_FR1", 1)        # LIST.md "Figure 5", Found: the labelled example
PASS_T = 4                                                       # Rule 5 (D154): the pass rate, drawn in a and b
PASS_RELAXED = 3                                                 # Rule 5 (D154): the relaxed threshold, Source Data
N_BOOT, SEED = S463.N_BOOT, S463.SEED                           # Rule 2 and Rule 7: 10,000 question resamples
PUBLISHED = {"W": 0.927, "rho": 0.9037, "pc1": 0.9361, "pr": 1.137}   # LIST.md "Analysis rules": the one-run values
# What the final plate plans, as signal values on the answerable answers (Rule 8): the judge's plain call and concept
# recall on all three draws (6 x 86 x 3 = 1,548 each), MiniCheck against the papers and the judge with passages on
# draw 1 and on all draws respectively (D114 Q32 O-a: papers draw 1 only, 516; S3 phase 3 on every draw, 1,548).
PLANNED = {"judge": 6 * N_ANSWERABLE * 3, "concept": 6 * N_ANSWERABLE * 3, "papers": 6 * N_ANSWERABLE,
           "faith": 6 * N_ANSWERABLE * 3}
K1_WORKERS = {"studio": ("studio", "projects/mentori-runs-k1"),
              "studio_1145" + "6": ("studio", "projects/mentori-runs-k1-1145" + "6"),
              "beelink": ("beelink", "projects/mentori-runs"),
              "beelink_1143" + "5": ("beelink", "projects/mentori-runs-k1-1143" + "5"),
              "laptop": ("laptop", "projects/mentori-runs-k1")}
K1_FILES = ("ragchecker/ragchecker.jsonl", "ragchecker/ragchecker_headers.jsonl", "ragas/ragas.jsonl",
            "ragas/ragas_headers.jsonl")


class Refused(SystemExit):
    pass


def sha256_file(p) -> str:
    return S457.sha256_file(Path(p))


def utc_now():
    return S457.utc_now()


# ---------------------------------------------------------------------------------------------------------------
# pull: read-only copies, every remote reader a script on stdin
# ---------------------------------------------------------------------------------------------------------------
# A python reader sent on stdin: it writes one tar stream to stdout of the files named in WANT (paths relative to the
# home folder, arcname given), each cut after its last whole line when it is a .jsonl (a file still being appended),
# and of every file under each folder in TREES whose name matches. Nothing is opened for writing.
READER_PY = r'''
import io, json, os, sys, tarfile, fnmatch
spec = json.loads(__SPEC__)
home = os.path.expanduser("~")
tf = tarfile.open(fileobj=sys.stdout.buffer, mode="w|")
def add(path, arc):
    with open(path, "rb") as fh:
        b = fh.read()
    cut = 0
    if path.endswith(".jsonl") and b and not b.endswith(b"\n"):
        keep = b.rfind(b"\n") + 1
        cut, b = len(b) - keep, b[:keep]
    ti = tarfile.TarInfo(arc)
    ti.size, ti.mtime = len(b), int(os.path.getmtime(path))
    tf.addfile(ti, io.BytesIO(b))
    return cut
log = {"files": {}, "missing": [], "cut": {}}
for rel, arc in spec["want"]:
    p = os.path.join(home, rel)
    if os.path.isfile(p):
        c = add(p, arc)
        log["files"][arc] = os.path.getmtime(p)
        if c:
            log["cut"][arc] = c
    else:
        log["missing"].append(arc)
for rel, arc, pats in spec["trees"]:
    base = os.path.join(home, rel)
    for dp, dn, fn in os.walk(base):
        dn.sort()
        for n in sorted(fn):
            if any(fnmatch.fnmatch(n, x) for x in pats):
                p = os.path.join(dp, n)
                a = arc + "/" + os.path.relpath(p, base)
                c = add(p, a)
                log["files"][a] = os.path.getmtime(p)
                if c:
                    log["cut"][a] = c
b = json.dumps(log).encode()
ti = tarfile.TarInfo("READ_LOG.json"); ti.size = len(b)
tf.addfile(ti, io.BytesIO(b))
tf.close()
'''


def reader_script(want, trees) -> str:
    return READER_PY.replace("__SPEC__", repr(json.dumps({"want": want, "trees": trees})))


def fetch(where: str, want, trees, dest: Path) -> dict:
    """Run the reader on a machine (the script on stdin: ssh ... python3 - for the Studio and the Beelink, this
    script's own interpreter for the laptop, INVENTORY A8) and unpack its tar into dest. Returns its READ_LOG."""
    script = reader_script(want, trees).encode()
    if where == "studio":
        cmd = SSH + [STUDIO, "python3", "-"]
    elif where == "beelink":
        cmd = SSH + BEELINK + ["python3", "-"]
    elif where == "laptop":
        cmd = [sys.executable, "-"]               # INVENTORY A8: uv's interpreter, never the system python3
    else:
        raise Refused(f"no machine {where!r}")
    r = subprocess.run(cmd, input=script, capture_output=True)
    if r.returncode:
        raise Refused(f"read on {where}: exit {r.returncode}: {r.stderr.decode(errors='replace').strip()[:400]}")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:") as tf:
        for m in tf.getmembers():
            if m.name.startswith("/") or ".." in Path(m.name).parts or not m.isfile():
                raise Refused(f"read on {where}: unexpected member {m.name!r}")
        tf.extractall(dest, filter="data")
    log = json.loads((dest / "READ_LOG.json").read_text())
    return log


def pull(args):
    to = Path(args.to).expanduser().resolve()
    if to.exists() and any(to.iterdir()):
        raise Refused(f"{to} exists and is not empty: pull into a new folder")
    to.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    # S3's G1 outs and their collect, through S463's own pull (its reader is a script on ssh's stdin)
    S463.pull(argparse.Namespace(to=str(to / "s3")))
    logs = {"s3": json.loads((to / "s3" / "PULL.json").read_text())}
    # L1 on the Studio since 24 Oct 23:14 (D134; 28 Oct: the Beelink holds no L1 folder any more): the header and every
    # row file of the three stages
    l1 = "projects/mentori-runs-l1/findings/recompute/L1"
    logs["l1"] = fetch("studio", [[f"{l1}/header.json", "header.json"]],
                       [[f"{l1}/{s}", s, ["*.jsonl"]] for s in ("key", "papers", "overlap")], to / "l1")
    # K1's rows and headers, per worker, on its machine
    logs["k1"] = {}
    for w, (machine, clone) in K1_WORKERS.items():
        base = f"{clone}/findings/recompute/" + "K1" + f"/{w}"
        logs["k1"][w] = fetch(machine, [[f"{base}/{f}", f] for f in K1_FILES], [], to / "k1" / w)
    (to / "PULL.json").write_text(json.dumps({"script": SCRIPT, "started_utc": started, "ended_utc": utc_now(),
                                              "sources": {"s3": f"{STUDIO}: S3 clone (S463 pull)",
                                                          "l1": f"{STUDIO}: ~/" + l1,
                                                          "k1": {w: f"{m} ~/{c}" for w, (m, c) in K1_WORKERS.items()}},
                                              "logs": logs}, indent=1) + "\n")
    print(f"pulled into {to}: S3 collect, L1 {len(logs['l1']['files'])} files, K1 "
          + ", ".join(f"{w} {len(v['files'])} files" for w, v in logs["k1"].items()))
    print(f"next: uv run --frozen python {SCRIPT} figure --from {to}")


# ---------------------------------------------------------------------------------------------------------------
# D155: the frozen inputs (module docstring, FROZEN INPUTS)
# ---------------------------------------------------------------------------------------------------------------
FIG5_SET, FIG2_SET, K1_TAR, G1R15_TAR = "fig5", "fig2", "k1_inputs_runs", "fig2_g1r15_inputs"
K1_READ = ("ragchecker/ragchecker.jsonl", "ragas/ragas.jsonl")          # what read_k1 reads of each worker
REPO_INPUTS = (L3_DIR / "concept_recall.jsonl", L3_DIR / "header.json", S26_JSON, S30_CSV, S463.RERUN_SH)
# Every input of the frozen build that is pinned here, with its sha256. P: the value the committed plate of
# 26 October (a9ea9ad7) recorded in figure5_provenance.json ("inputs": s3_collect, answers, l3, l1_files, k1_files).
# S: the value findings/recompute/frozen_inputs/SHA256SUMS lists (8082cc23), or the tar's member list in
# frozen_inputs/members/. R: a repository file as committed at 8082cc23. The 31 files of fig2_inputs/out and
# out_g1r15 and G1R15's MANIFEST.sha256 are not listed: each is checked against s3/IDENTICAL_FILES.tsv (pinned S).
FROZEN_SHA256 = {
    "fig2_inputs/g1_collect.jsonl": "f5ff75bc244cda492a48e7e11f54f2007ed7d586a8f49e78921edd7244b28965",       # P
    "fig5_inputs/PULL.json": "afb434173076bc6f90de15ca4cb5ee9ae4677ac978ed9ae5f10244581f9cb962",              # S
    "fig5_inputs/s3/g1_collect.jsonl.json": "febfd866f802427bdd3e6ba574e581f1b40ade30003e4a8c1faf12598d3d13b2",  # S
    "fig5_inputs/s3/IDENTICAL_FILES.tsv": "863a7314b96193d5e68de2737e273e28dff64507c04a95c37d542bec7ef08fb5",  # S
    "fig5_inputs/l1/header.json": "afe287fa28a78a9b9812bd8bf2c3bafd677af98a8e71602e41b461d0e92a55d1",         # S
    "fig5_inputs/l1/key/key.shard0of1.jsonl": "61d23940fd94f2fc1c2b4e3ce920398ca21b44157b682d7e27cefbeb5e28b426",  # P
    "fig5_inputs/l1/overlap/overlap.shard0of1.jsonl":
        "277bbfe9e65d0917febba6d06365803dbd10c411376fa64322cad4bae536ddd3",                                    # P
    "fig5_inputs/l1/papers/papers.shard0of3.jsonl":
        "34f8c37a111bc409c6b4de5de0aea2995460286c1a53fdfa9d51e57390d5c75d",                                    # P
    "fig5_inputs/l1/papers/papers.shard1of3.jsonl":
        "ebbf47b7cc0deadaf237d8ed34a54370df1794ce0eaf0ef93d1f1c9ca22a36df",                                    # P
    "fig5_inputs/l1/papers/papers.shard2of3.jsonl":
        "cfe9852b5a930bf9549f17f4ff9de94cae87070f90df2a030400ac179da57d2f",                                    # P
    "fig5_inputs/k1/studio/ragchecker/ragchecker.jsonl":
        "58b4764c93eef107e02eca87725e12ddff28c0ab9b2085ddb4dfc9f8bc764ede",                                    # P
    "fig5_inputs/k1/studio/ragas/ragas.jsonl": "b81aba7b18cb027723e3e72a8d0e73490d9fec9133b5416c5a3946a12d477a0e",  # P
    "fig5_inputs/k1/studio_11456/ragchecker/ragchecker.jsonl":
        "0cf23b063c7371b2733a5a57afe381c47a1de5e6dbe2b9529e4cd864235cd4dc",                                    # P
    "fig5_inputs/k1/beelink/ragchecker/ragchecker.jsonl":
        "f7244f8cfe92cc70e29336d98dcf044caa3e365caca93c35478a11a4e48ef1eb",                                    # P
    "fig5_inputs/k1/beelink/ragas/ragas.jsonl": "46c68cdd8112da57a9909d54dee52007ab5e8b81283467b372c35a12e7bbdf63",  # P
    "fig5_inputs/k1/beelink_11435/ragchecker/ragchecker.jsonl":
        "1a54dfb17b5ac35e60ecae6482a46c3301be68bccac3c722bf3d4016668d745a",                                    # P
    "fig5_inputs/k1/laptop/ragchecker/ragchecker.jsonl":
        "5355054388984d4f38b191e382c86f4a2ee02a660e54d504468592833fb0afee",                                    # P
    "fig5_inputs/k1/laptop/ragas/ragas.jsonl": "7265b322b2f371513ea9c4f21f05de186eb32a0c047af5c2e9e957f1963c6249",  # P
    "k1_inputs_runs.tar:k1_inputs_runs/exp_01__single_pass__exp_v4_s20_n0/answers.jsonl":
        "bc43f45f211b64ad625db677110d6346dfd6d5bdda9387a6647d0d957cc5dccd",                                    # P
    "k1_inputs_runs.tar:k1_inputs_runs/exp_01__multi_hop__exp_v4_s20_n0/answers.jsonl":
        "518b0efefd170ec4e172b8ba1d8218aa25612a4eaf27ebab98a824343864ad42",                                    # P
    "k1_inputs_runs.tar:k1_inputs_runs/exp_01__verified_pass__exp_v4_s20_n0/answers.jsonl":
        "8489392b4723a8d4fa8bd3727e83853256d8d68d30e7d44c8d81bbf4beb2e6b7",                                    # P
    "k1_inputs_runs.tar:k1_inputs_runs/exp_01__rlm_5__exp_v4_s20_n0/answers.jsonl":
        "fa8a221fd22f11e516d8204116a8a25b51e4eabe654615d16516456373276b81",                                    # P
    "k1_inputs_runs.tar:k1_inputs_runs/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl":
        "7d5d2651b0111d96cc863af5a5e9349d07466d6028be2407c1644ef31e7ab90b",                                    # P
    "k1_inputs_runs.tar:k1_inputs_runs/exp_01__rlm_20__exp_v4_s20_n0/answers.jsonl":
        "18ba730cee1865455aa5ce7481ffdb205271791a35d67a71a222819f924e27dc",                                    # P
    "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__verified_pass__exp_v4_s20_n0/answers.jsonl":
        "1ce4b1052912d8592b912da29ed987df9c2a4baca575cf80cc2b9d33334f8148",                                    # P
    "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__rlm_5__exp_v4_s20_n0/answers.jsonl":
        "cc10c9eb881fa9618ff2fb8ec7a3f1bb9cf58662827cd67b326e47f67b51d42c",                                    # P
    "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl":
        "ecb6de5343d172894fd56d57997e3301d70ca3fb509ae2cd65f8e47eb8c268b7",                                    # P
    "fig2_g1r15_inputs.tar:fig2_g1r15_inputs/runs/exp_01__rlm_20__exp_v4_s20_n0/answers.jsonl":
        "1e5b124d8bbd98640c87051916305ed0c04d668447967c60a08d6945fca32c62",                                    # P
    "findings/recompute/L3/concept_recall.jsonl": "56f0f23b3415169a2ec5a79f6fb9cbf427939054279b9ebc32b21cf07c6e2f36",  # P
    "findings/recompute/L3/header.json": "01597d0c39704f1e1abfa132231eee57a9a839b111340ea0b5a85b2482bf0b5f",  # R
    "findings/recompute/S26_signal_redundancy.json":
        "07dd836183ddedda293f203488058a1ab31101bafd821e4ba012a2e19f218951",                                    # R
    "findings/recompute/S30_baseline_scores_full.csv":
        "6bfb240e74fae89d713279227eed9eff529262819ff5a2492cd17de0ac713256",                                    # R
    "findings/recompute/G1_runs/rerun_d89.sh": "8549210c7e829229ba83b0dd5afcc804454cda00aed665ce586ede5e24d98260",  # R
}


def identical_files(tsv: Path) -> dict:
    """s3/IDENTICAL_FILES.tsv as {input name (as inputs_sha256 names it): sha256} for every file of the 23 October
    pull's s3/ frozen elsewhere: "findings/recompute/fig2_inputs/X" is fig2_inputs/X, "<t>.tar: <m>" is <t>.tar:<m>."""
    out = {}
    for ln in tsv.read_text().splitlines():
        if not ln.strip() or ln.startswith("#") or ln.startswith("path\t"):
            continue
        f = ln.split("\t")
        if len(f) != 3 or not re.fullmatch(r"[0-9a-f]{64}", f[1]):
            raise Refused(f"{tsv.name}: not a 'path, sha256, same_bytes_at' line: {ln!r}")
        at = f[2].strip()
        if at.startswith("findings/recompute/"):
            name = at[len("findings/recompute/"):]
        elif ".tar: " in at:
            t, m = at.split(": ", 1)
            name = f"{t}:{m}"
        else:
            raise Refused(f"{tsv.name}: same_bytes_at {at!r} is neither a committed file nor a tar member")
        out[name] = f[1]
    return out


def check_frozen(sha: dict, tsv_sha: dict, complete: bool = True) -> list[str]:
    """Each recorded input sha256 equal to its pin (FROZEN_SHA256) or to its IDENTICAL_FILES.tsv line; with complete,
    every pin read and every input read pinned one way or the other. A difference stops the build."""
    bad = [f"{k}: {sha[k][:12]}, pinned {v[:12]}" for k, v in FROZEN_SHA256.items() if k in sha and sha[k] != v]
    bad += [f"{k}: {sha[k][:12]}, IDENTICAL_FILES.tsv {v[:12]}" for k, v in tsv_sha.items() if k in sha and sha[k] != v]
    if complete:
        bad += [f"{k}: pinned, not read" for k in FROZEN_SHA256 if k not in sha]
        bad += [f"{k}: read, pinned nowhere" for k in sha if k not in FROZEN_SHA256 and k not in tsv_sha]
    if bad:
        raise Refused(f"{len(bad)} frozen input(s) differ from what the committed plate recorded (D155), first: "
                      + "; ".join(bad[:3]) + "; nothing written")
    return [f"{len(sha)} inputs, each equal to its pin (FROZEN_SHA256, {sum(k in sha for k in FROZEN_SHA256)}) or "
            f"to s3/IDENTICAL_FILES.tsv ({sum(k in sha and k not in FROZEN_SHA256 for k in tsv_sha)})"]


def _k1_view(tmp: Path, sha: dict, labels: list) -> Path:
    """K1's copy of G1's records (k1_inputs_runs.tar) as S463.read_answers reads one: <tmp>/k1_inputs/runs (a link
    to the extracted tar) with a MANIFEST.sha256 beside it, its lines the answers files' sha256 just checked."""
    runs = FR.frozen(K1_TAR, K1_TAR)
    view = tmp / "k1_inputs"
    view.mkdir()
    (view / "runs").symlink_to(runs, target_is_directory=True)
    lines = []
    for p in sorted(runs.glob("*/answers.jsonl")):
        name = f"{K1_TAR}.tar:{K1_TAR}/{p.relative_to(runs).as_posix()}"
        sha[name] = FR.sha256_file(p)
        lines.append(f"{sha[name]}  runs/{p.relative_to(runs).as_posix()}")
    (view / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    labels.append((view / "runs", f"{K1_TAR}.tar:{K1_TAR}"))
    return view / "runs"


def frozen_sources(tmp: Path) -> dict:
    """D155: Figure 5's inputs from the frozen copies, every one's sha256 recorded and checked (check_frozen). The
    collect is read through <tmp>/s3: a link to fig2_inputs/g1_collect.jsonl beside a copy of the Figure 5 pull's
    sidecar whose two input folders (the pull's s3/out and s3/out_g1r15) are re-pointed at fig2_inputs/out and
    out_g1r15, byte-equal to them by IDENTICAL_FILES.tsv; S463.read_collect finds those folders through the sidecar."""
    sha, labels = {}, []

    def rec(name, p):
        sha[name] = FR.sha256_file(p)
        return p

    f5, f2 = FR.frozen(FIG5_SET), FR.frozen(FIG2_SET)
    pull_json = rec("fig5_inputs/PULL.json", FR.frozen(FIG5_SET, "PULL.json"))
    side_f = rec("fig5_inputs/s3/g1_collect.jsonl.json", FR.frozen(FIG5_SET, "s3/g1_collect.jsonl.json"))
    tsv = rec("fig5_inputs/s3/IDENTICAL_FILES.tsv", FR.frozen(FIG5_SET, "s3/IDENTICAL_FILES.tsv"))
    l1, k1 = FR.frozen(FIG5_SET, "l1"), FR.frozen(FIG5_SET, "k1")
    rec("fig5_inputs/l1/header.json", l1 / "header.json")
    for p in sorted(l1.rglob("*.jsonl")):
        rec(f"fig5_inputs/{p.relative_to(f5).as_posix()}", p)
    for w in K1_WORKERS:
        for t in K1_READ:
            if (k1 / w / t).exists():
                rec(f"fig5_inputs/k1/{w}/{t}", k1 / w / t)
    collect = rec("fig2_inputs/g1_collect.jsonl", FR.frozen(FIG2_SET, "g1_collect.jsonl"))
    for o in ("out", "out_g1r15"):
        for p in sorted(FR.frozen(FIG2_SET, o).rglob("*")):
            if p.is_file():
                rec(f"fig2_inputs/{p.relative_to(f2).as_posix()}", p)
    g1r15 = FR.frozen(G1R15_TAR, G1R15_TAR)
    rec(f"{G1R15_TAR}.tar:{G1R15_TAR}/MANIFEST.sha256", g1r15 / "MANIFEST.sha256")
    for p in sorted((g1r15 / "runs").glob("*/answers.jsonl")):
        rec(f"{G1R15_TAR}.tar:{G1R15_TAR}/{p.relative_to(g1r15).as_posix()}", p)
    labels.append((g1r15 / "runs", f"{G1R15_TAR}.tar:{G1R15_TAR}/runs"))
    k1_runs = _k1_view(tmp, sha, labels)
    for p in REPO_INPUTS:
        rec(p.relative_to(ROOT).as_posix(), p)
    tsv_sha = identical_files(tsv)
    checked = check_frozen(sha, tsv_sha)
    # the sidecar, its two input folders moved from the 23 October pull's s3/ to fig2_inputs/
    side = json.loads(side_f.read_text())
    ins = (side.get("_provenance") or {}).get("inputs") or []
    old = str(Path(ins[0]).parent) if ins else ""
    if [Path(x).name for x in ins] != ["out", "out_g1r15"] or any(str(Path(x).parent) != old for x in ins):
        raise Refused(f"the frozen sidecar's inputs are {ins}, not one pull's s3/out and s3/out_g1r15")

    def move(p):
        if p != old and not p.startswith(old + "/"):
            raise Refused(f"the frozen sidecar names {p}, outside its pull's s3/ ({old})")
        return str(f2) + p[len(old):]
    moved = dict(side)
    moved["_provenance"] = {**side["_provenance"], "inputs": [move(x) for x in ins]}
    moved["from"] = {move(k): v for k, v in (side.get("from") or {}).items()}
    for k in moved["from"]:
        name = Path(k).relative_to(f2.parent).as_posix()
        if name not in sha or tsv_sha.get(name) != sha[name]:
            raise Refused(f"the sidecar takes rows from {name}, not a frozen file equal to the pull's")
    view = tmp / "s3"
    view.mkdir()
    (view / collect.name).symlink_to(collect)
    (view / side_f.name).write_text(json.dumps(moved, indent=1) + "\n")
    labels.append((view / collect.name, "fig2_inputs/g1_collect.jsonl"))
    return {"pull": pull_json, "collect": view / collect.name, "collect_name": "fig2_inputs/g1_collect.jsonl",
            "side": side, "l1": l1, "k1": k1, "ans_dirs": [k1_runs, g1r15 / "runs"], "sha": sha, "labels": labels,
            "checked": checked}


def pull_sources(src: Path, tmp: Path) -> dict:
    """A new pull's folder (pull --to <dir>): its PULL.json, s3/, l1/ and k1/, with K1's copy of G1's records from
    the frozen tar (as frozen_sources). Every input's sha256 is recorded; only the tar's are pinned (a new pull is
    new data)."""
    sha, labels = {}, []
    for p in sorted(x for x in src.rglob("*") if x.is_file()):
        sha[f"pull:{p.relative_to(src).as_posix()}"] = FR.sha256_file(p)
    labels.append((src, "pull:"))
    k1_runs = _k1_view(tmp, sha, labels)
    for p in REPO_INPUTS:
        sha[p.relative_to(ROOT).as_posix()] = FR.sha256_file(p)
    checked = check_frozen({k: v for k, v in sha.items() if k.startswith(K1_TAR)}, {}, complete=False)
    return {"pull": src / "PULL.json", "collect": src / "s3" / "g1_collect.jsonl",
            "collect_name": "pull:s3/g1_collect.jsonl",
            "side": json.loads((src / "s3" / "g1_collect.jsonl.json").read_text()), "l1": src / "l1",
            "k1": src / "k1", "ans_dirs": [k1_runs, src / "s3" / "g1r15_inputs" / "runs"], "sha": sha,
            "labels": labels, "checked": checked}


def label_of(path, labels) -> str:
    """An input's name in the provenance: its frozen set or tar member, never a temporary or scratch path."""
    p = str(path)
    for base, name in labels:
        b = str(base)
        if p == b:
            return name
        if p.startswith(b + "/"):
            return name.rstrip("/:") + ("/" if not name.endswith(":") else ":") + p[len(b) + 1:]
    raise Refused(f"no frozen name for the input {p}")



# ---------------------------------------------------------------------------------------------------------------
# Rule 7's statistics on configuration means (S26 and S318's construction), own code, reproduced before use
# ---------------------------------------------------------------------------------------------------------------
def rankdata(v):
    from scipy import stats
    return stats.rankdata(v)


def kendall_w(R) -> float:
    """W without tie correction (stats_full.kendall_w, S318 _w): k raters by n objects, average ranks for ties."""
    import numpy as np
    R = np.asarray(R, float)
    k, n = R.shape
    s = R.sum(0)
    return 12 * float(((s - s.mean()) ** 2).sum()) / (k * k * (n ** 3 - n))


def w_p_untied(R) -> float:
    """W's exact upper-tail P as S318 _w_p_untied_null (S34's null): rater 1 fixed, raters 2..k over every untied
    ordering of 1..n (720 for six), whatever ties the observed ranks carry. Vectorised over the last rater."""
    import numpy as np
    R = np.asarray(R, float)
    k, n = R.shape
    obs = kendall_w(R)
    perms = np.array(list(itertools.permutations(range(1, n + 1))), float)
    m = len(perms)
    ge = 0
    base = R[0]
    if k == 2:
        s = base + perms
        ss = ((s - s.mean(1, keepdims=True)) ** 2).sum(1)
        ge = int((12 * ss / (k * k * (n ** 3 - n)) >= obs - 1e-12).sum())
        return ge / m
    for combo in itertools.product(range(m), repeat=k - 2):
        s0 = base + sum(perms[i] for i in combo)
        s = s0 + perms
        ss = ((s - s.mean(1, keepdims=True)) ** 2).sum(1)
        ge += int((12 * ss / (k * k * (n ** 3 - n)) >= obs - 1e-12).sum())
    return ge / m ** (k - 1)


def corr3(vecs):
    """S318 _corr3: the 3 x 3 Spearman matrix over the configuration means; mean pairwise rho, PC1 share and
    participation ratio of its eigenvalues."""
    import numpy as np
    from scipy import stats
    corr = np.ones((3, 3))
    for i, j in itertools.combinations(range(3), 2):
        corr[i, j] = corr[j, i] = stats.spearmanr(vecs[i], vecs[j]).statistic
    eig = np.sort(np.linalg.eigvalsh(corr))
    return (float(np.mean([corr[0, 1], corr[0, 2], corr[1, 2]])), float(eig[-1] / eig.sum()),
            float(eig.sum() ** 2 / np.sum(eig ** 2)), corr)


def reproduce() -> list[str]:
    """Reproduce before writing: this script's W, P, Spearman matrix, PC1 and participation ratio give the published
    one-run values from the deposited inputs S26 and S30 used; the resample counts are S463's (S407's seed)."""
    import csv
    import numpy as np
    done = []
    m = json.loads(S26_JSON.read_text())["per_config_means"]
    R = [rankdata([m[s][c] for c in CONFIGS]) for s in ("det", "judge", "mc")]
    w = kendall_w(R)
    p = w_p_untied(R)
    if S457.half_up(w, 3) != f"{PUBLISHED['W']:.3f}" or abs(p - 0.000181) > 5e-7:
        raise Refused(f"reproduce: W {w!r} and P {p!r} on S26's means, want W {PUBLISHED['W']} and P 0.000181 "
                      f"(S318 kendall_w_three_signals_legend); nothing written")
    done.append(f"W {S457.half_up(w, 3)} and exact P {p:.6f} on S26's per-configuration means (S318: W 0.927, "
                f"P 0.000181 under the untied null)")
    cols = {"det": "det_score_correctness_fullsim", "judge": "judge_correctness_full", "mc": "mc_f1"}
    with open(S30_CSV) as fh:
        rows = list(csv.DictReader(r for r in fh if not r.startswith("#")))
    if len(rows) != 528:
        raise Refused(f"reproduce: S30 holds {len(rows)} rows, want 528")
    per = {s: {c: defaultdict(list) for c in CONFIGS} for s in cols}
    for r in rows:
        for s, col in cols.items():
            if r[col] not in ("", None):
                per[s][r["config"]][r["question_id"]].append(float(r[col]))
    vecs = [np.array([np.mean([np.mean(v) for v in per[s][c].values()]) for c in CONFIGS]) for s in cols]
    rho, pc1, pr, _ = corr3(vecs)
    got = {"rho": S457.half_up(rho, 4), "pc1": S457.half_up(pc1, 4), "pr": S457.half_up(pr, 3)}
    want = {"rho": f"{PUBLISHED['rho']:.4f}", "pc1": f"{PUBLISHED['pc1']:.4f}", "pr": f"{PUBLISHED['pr']:.3f}"}
    if got != want:
        raise Refused(f"reproduce: on S30's answers this script gives {got}, the published {want}; nothing written")
    done.append(f"mean pairwise rho {got['rho']}, PC1 share {got['pc1']}, participation ratio {got['pr']} on S30's "
                f"528 answers (S26, S318 _triangulation)")
    for n in (7, 10, 86):
        a = S463.resample_counts(n)
        b = np.stack([np.bincount(r, minlength=n) for r in S457.boot_matrix(n)]).astype(float)
        if not np.array_equal(a, b):
            raise Refused(f"reproduce: resample counts for n = {n} differ between S463 and S457; nothing written")
    done.append(f"question resample counts equal in S463 and S457 for n = 7, 10, 86 (seed {SEED}, {N_BOOT} "
                f"resamples)")
    return done


# ---------------------------------------------------------------------------------------------------------------
# reading: S3 through S463's reader, L3, L1, K1
# ---------------------------------------------------------------------------------------------------------------
def read_jsonl(p: Path):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def read_l3(groups) -> dict:
    """L3's rows (S471), checked against its header's counts; {(config, question, draw): row}."""
    hdr = json.loads((L3_DIR / "header.json").read_text())
    rows = read_jsonl(L3_DIR / "concept_recall.jsonl")
    cnt = hdr["counts"]
    got = {"rows": len(rows), "scored": sum(1 for r in rows if r.get("group") != "not_answerable"),
           "status_scored": dict(Counter(r["status"] for r in rows if r.get("group") != "not_answerable")),
           "by_group": dict(Counter(r["group"] for r in rows))}
    want = {"rows": cnt["rows"], "scored": cnt["scored"], "status_scored": cnt["status_scored"],
            "by_group": cnt["by_group"]}
    if got != want:
        raise Refused(f"reproduce: L3's rows give {got}, its header {want}; nothing written")
    out = {}
    for r in rows:
        k = (r["config"], r["question_id"], r["draw"])
        if k in out:
            raise Refused(f"L3: {k} twice")
        if groups.get(r["question_id"]) != r["group"]:
            raise Refused(f"L3: {k} group {r['group']}, the D5 key's {groups.get(r['question_id'])}")
        out[k] = r
    return {"rows": out, "header": hdr, "reproduced": f"L3 rows equal to L3's header counts ({cnt['rows']} rows, "
                                                       f"{cnt['scored']} scored, {cnt['status_scored']})"}


def read_l1(l1_dir: Path, l3_header, groups) -> dict:
    """L1's papers, key and overlap rows from the pull (S470's files): the latest row per answer_key per stage, the
    header's inputs equal to L3's (the same answers), each answer's sha256 equal to L3's."""
    hdr = json.loads((l1_dir / "header.json").read_text())
    if hdr["identity"]["inputs"]["manifest_sha256"] != l3_header["inputs"]["manifest_sha256"]:
        raise Refused("L1 and L3 read different answer copies (inputs manifest sha256 differ)")
    st = {}
    for stage in ("papers", "key", "overlap"):
        rows = {}
        for f in sorted((l1_dir / stage).glob("*.jsonl")):
            for r in read_jsonl(f):
                k = (r["config"], r["question_id"], r["draw"])
                if k in rows:
                    raise Refused(f"L1 {stage}: {k} in two rows (S470 writes an answer once)")
                if groups.get(r["question_id"]) != r["group"]:
                    raise Refused(f"L1 {stage}: {k} group {r['group']}, the D5 key's {groups.get(r['question_id'])}")
                rows[k] = r
        st[stage] = rows
    return {"stages": st, "header": hdr}


def check_same_answers(l1, l3):
    bad = [k for s in l1["stages"].values() for k, r in s.items()
           if k in l3["rows"] and r.get("answer_sha256") != l3["rows"][k].get("answer_sha256")]
    if bad:
        raise Refused(f"{len(bad)} answers differ between L1 and L3, first {bad[0]}")


def answer_text_sha(dirs) -> dict:
    """sha256 of each answer's text in the generation records S3 judged (K1's copy, then the G1R15 copy over it),
    to tie S3's rows to the answers L1 and L3 scored (both read ~/l1_inputs)."""
    out = {}
    for d in dirs:
        for c in CONFIGS:
            p = Path(d) / S463.run_of(c) / "answers.jsonl"
            if not p.exists():
                continue
            for raw in p.read_text().splitlines():
                if raw.strip():
                    r = json.loads(raw)
                    a = ((r.get("generation") or {}).get("answer")) or ""
                    out[r["answer_key"]] = hashlib.sha256(a.encode()).hexdigest()
    return out


def read_k1(k1_dir: Path) -> dict:
    """K1's rows per worker and tool: the latest row per answer_key, status counts, answerable means. Not drawn."""
    tools = {"ragchecker": "ragchecker/ragchecker.jsonl", "ragas": "ragas/ragas.jsonl"}
    latest = {t: {} for t in tools}
    files = {}
    for w in K1_WORKERS:
        for t, rel in tools.items():
            p = k1_dir / w / rel
            if not p.exists():
                continue
            rows = read_jsonl(p)
            files[f"{w}/{rel}"] = {"rows": len(rows), "sha256": sha256_file(p)}
            for r in rows:
                k = r["answer_key"]
                prev = latest[t].get(k)
                if prev is not None and prev[0] != w:
                    raise Refused(f"K1 {t}: {k} scored by two workers ({prev[0]}, {w})")
                latest[t][k] = (w, r)
    summ = {}
    for t in tools:
        rows = [r for _, r in latest[t].values()]
        st = Counter((r.get("group"), r.get("status")) for r in rows)
        means = {}
        for c in CONFIGS:
            ok = [r for r in rows if r.get("config") == c and r.get("group") == "answerable"
                  and r.get("status") in ("ok", "ok_with_nulls")]
            vals = defaultdict(list)
            for r in ok:
                m = r.get("metrics") if t == "ragchecker" else r.get("scores")
                for kk, v in (m or {}).items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        vals[kk].append(float(v))
            means[c] = {"answers": len(ok), **{kk: round(sum(v) / len(v), 6) for kk, v in sorted(vals.items())}}
        summ[t] = {"answers_with_a_row": len(rows), "status_by_group": {f"{g} {s}": n for (g, s), n in sorted(
            st.items(), key=lambda z: (str(z[0][0]), str(z[0][1])))}, "answerable_means_by_strategy": means}
    return {"files": files, "summary": summ,
            "planned": "D80 V10: draw 1 of the six strategies, the 96 questions with a reference answer (86 "
                       "answerable and 10 false premise), 576 answers per tool"}


# ---------------------------------------------------------------------------------------------------------------
# compute
# ---------------------------------------------------------------------------------------------------------------
def boot_rows(n):
    """Rule 2 and Rule 7: the 10,000 question resamples as counts per question (S463.resample_counts)."""
    return S463.resample_counts(n)


def pct_interval(samples):
    import numpy as np
    a = np.asarray(samples, float)
    a = a[~np.isnan(a)]
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))] if len(a) else [None, None]


def spearman(x, y):
    from scipy import stats
    return float(stats.spearmanr(x, y).statistic)


def answer_rho(points):
    """Rule 7: answer-level Spearman rho over all answers, its interval from 10,000 question resamples (every
    answer of a question drawn together), no plain Spearman P. points: [(question, x, y)]."""
    import numpy as np
    if len(points) < 3:
        return {"rho": None, "lo": None, "hi": None, "answers": len(points), "questions": len({q for q, _, _ in points})}
    qs = sorted({q for q, _, _ in points})
    by = {q: [(x, y) for qq, x, y in points if qq == q] for q in qs}
    rho = spearman([x for _, x, _ in points], [y for _, _, y in points])
    W_ = boot_rows(len(qs))
    out = []
    for w in W_:
        xs, ys = [], []
        for i, q in enumerate(qs):
            k = int(w[i])
            if k:
                for x, y in by[q]:
                    xs += [x] * k
                    ys += [y] * k
        out.append(spearman(xs, ys) if len(set(xs)) > 1 and len(set(ys)) > 1 else float("nan"))
    lo, hi = pct_interval(out)
    return {"rho": rho, "lo": lo, "hi": hi, "answers": len(points), "questions": len(qs),
            "resamples_undefined": int(np.isnan(np.asarray(out)).sum())}


def compute(read, l3, l1, faith_rows, groups):
    import numpy as np
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    cells = read["cells"]
    # the judge's plain call (a): Rule 10, a failed answer (no text) scores 0 and fails; an unscored call is left out
    judge = {}
    for (c, q, d), cell in cells.items():
        if groups[q] != "answerable":
            continue
        judge[(c, q, d)] = (cell["score"] if cell["kind"] == "scored" else 0 if cell["kind"] == "failed" else None,
                            cell["kind"], cell.get("why"))
    concept = {}
    for (c, q, d), r in l3["rows"].items():
        if groups[q] == "answerable":
            concept[(c, q, d)] = (r["concept_recall_loose"] if r["status"] in ("ok", "no_answer", "error") else None,
                                  r["status"], r.get("reason"))
    papers = {}
    for (c, q, d), r in l1["stages"]["papers"].items():
        if groups[q] == "answerable":
            papers[(c, q, d)] = ((r.get("signals") or {}).get("precision"), r["status"],
                                 (r.get("null_reasons") or {}).get("precision"))
    faith = {}
    for (c, q, d), (st, v, why) in faith_rows.items():
        if groups[q] == "answerable":
            faith[(c, q, d)] = (v, st, why)
    # the W question set: answerable questions whose six draw-1 answers all have an L1 papers row
    qw = [q for q in qa if all((c, q, 1) in papers for c in CONFIGS)]
    partial_blocks = sorted({q for (c, q, d) in papers} - set(qw))

    # ---- a: per strategy, Figure 3's pass rate on the 86 (all draws) and MiniCheck against the papers on qw
    sh = S463.shares(cells, qa, list(DRAWS), PASS_T, True)
    sh3 = S463.shares(cells, qa, list(DRAWS), PASS_RELAXED, True)     # D154: the relaxed threshold, Source Data only
    a = {}
    for c in CONFIGS:
        pv = [100 * float(sh[c][q][0]) for q in qa if sh[c][q][0] is not None]
        mv = [(q, papers[(c, q, 1)][0]) for q in qw if papers[(c, q, 1)][0] is not None]
        a[c] = {"pass": {"per_q": [(q, 100 * float(sh[c][q][0])) for q in qa if sh[c][q][0] is not None],
                         "s": S457.summary(pv),
                         "answers": sum(1 for q in qa for d in DRAWS if cells[(c, q, d)]["kind"] in ("scored", "failed")),
                         "unscored": sum(1 for q in qa for d in DRAWS if cells[(c, q, d)]["kind"] == "unscored")},
                "pass3": {"per_q": [(q, 100 * float(sh3[c][q][0])) for q in qa if sh3[c][q][0] is not None],
                          "s": S457.summary([100 * float(sh3[c][q][0]) for q in qa if sh3[c][q][0] is not None]),
                          "answers": sum(1 for q in qa for d in DRAWS if cells[(c, q, d)]["kind"] in ("scored", "failed")),
                          "unscored": sum(1 for q in qa for d in DRAWS if cells[(c, q, d)]["kind"] == "unscored")},
                "papers": {"per_q": mv, "s": S457.summary([v for _, v in mv]) if len(mv) >= 2 else None,
                           "answers": len(mv), "null": sum(1 for q in qw if papers[(c, q, 1)][0] is None)}}

    # ---- c: configuration means on qw (Rule 7: each question weighted equally over its draws)
    def qmean(sig, c, q, draws):
        v = [sig[(c, q, d)][0] for d in draws if (c, q, d) in sig and sig[(c, q, d)][0] is not None]
        return float(np.mean(v)) if v else None

    sigs = {"judge": (judge, DRAWS), "concept": (concept, DRAWS), "papers": (papers, (1,))}
    V = {s: np.array([[qmean(sig, c, q, dr) if qmean(sig, c, q, dr) is not None else np.nan for c in CONFIGS]
                      for q in qw], float) for s, (sig, dr) in sigs.items()}

    def conf_means(w=None):
        out = []
        for s in ("judge", "concept", "papers"):
            M = V[s]
            ok = ~np.isnan(M)
            wq = np.ones(len(qw)) if w is None else w
            num = (np.nan_to_num(M) * wq[:, None]).sum(0)
            den = (ok * wq[:, None]).sum(0)
            out.append(np.where(den > 0, num / np.where(den > 0, den, 1), np.nan))
        return out

    c_out = {"questions": qw, "partial_blocks_left_out": partial_blocks}
    if len(qw) >= 2:
        means = conf_means()
        R = [rankdata(m) for m in means]
        rho, pc1, pr, corr = corr3(means)
        Wv = kendall_w(R)
        Pv = w_p_untied(R)
        Bw = boot_rows(len(qw))
        bw, brho, bpc, bpr = [], [], [], []
        for w in Bw:
            m = conf_means(w)
            if any(np.isnan(x).any() for x in m):
                bw.append(np.nan); brho.append(np.nan); bpc.append(np.nan); bpr.append(np.nan)
                continue
            bw.append(kendall_w([rankdata(x) for x in m]))
            with np.errstate(all="ignore"):
                try:
                    r_, p_, q_, _ = corr3(m)
                except Exception:              # noqa: BLE001  a resample with a constant signal has no rho
                    r_ = p_ = q_ = np.nan
            brho.append(r_); bpc.append(p_); bpr.append(q_)
        c_out.update(means={s: dict(zip(CONFIGS, map(float, m))) for s, m in zip(("judge", "concept", "papers"), means)},
                     ranks_low1={s: dict(zip(CONFIGS, map(float, r))) for s, r in zip(("judge", "concept", "papers"), R)},
                     W=Wv, P=Pv, W_ci=pct_interval(bw), rho=rho, rho_ci=pct_interval(brho), pc1=pc1,
                     pc1_ci=pct_interval(bpc), pr=pr, pr_ci=pct_interval(bpr),
                     corr={f"{a_}_{b_}": float(corr[i, j]) for (i, a_), (j, b_) in itertools.combinations(
                         enumerate(("judge", "concept", "papers")), 2)},
                     resamples_undefined=int(np.isnan(np.asarray(brho, float)).sum()),
                     answers={s: int((~np.isnan(V[s])).sum()) for s in V})
    # ---- b: each draw-1 answer on qw with a papers value: concept recall (x), papers (y), the judge's pass (marker)
    b = []
    for q in qw:
        for c in CONFIGS:
            pv = papers[(c, q, 1)][0]
            cv = concept.get((c, q, 1), (None,))[0]
            jv = judge.get((c, q, 1), (None,))[0]
            if pv is None or cv is None or jv is None:
                continue
            b.append({"strategy": c, "question_id": q, "draw": 1, "concept_recall": cv, "papers_precision": pv,
                      "judge_correctness": jv, "judge_pass": int(jv >= PASS_T),
                      b_relaxed_col(): int(jv >= PASS_RELAXED),
                      "example": int((c, q, 1) == EXAMPLE)})
    # ---- d: the judge with passages, faithfulness 0 to 5, every draw, answerable answers with a score
    d = {}
    for c in CONFIGS:
        sc = [faith[(c, q, dd)][0] for q in qa for dd in DRAWS if (c, q, dd) in faith and faith[(c, q, dd)][1] == "ok"]
        st = Counter(faith[(c, q, dd)][1] for q in qa for dd in DRAWS if (c, q, dd) in faith)
        d[c] = {"counts": {k: sc.count(k) for k in range(6)}, "n": len(sc), "status": dict(st)}
    all_sc = [faith[k][0] for k in faith if faith[k][1] == "ok"]
    d_all = {"n": len(all_sc), "at5": all_sc.count(5), "counts": {k: all_sc.count(k) for k in range(6)}}
    # ---- e: draw-1 answers with both a faithfulness score (with passages) and a papers value (all of L1's rows,
    # not only qw: an answer-level statistic needs no complete block)
    e_pts = []
    for (c, q, dd), (pv, pst, _) in papers.items():
        f = faith.get((c, q, dd))
        if dd == 1 and pv is not None and f is not None and f[1] == "ok":
            e_pts.append({"strategy": c, "question_id": q, "draw": 1, "faithfulness": f[0], "papers_precision": pv})
    e_all = answer_rho([(p["question_id"], p["faithfulness"], p["papers_precision"]) for p in e_pts])
    e_35 = answer_rho([(p["question_id"], p["faithfulness"], p["papers_precision"]) for p in e_pts
                       if p["faithfulness"] >= 3])
    five = [p["papers_precision"] for p in e_pts if p["faithfulness"] == 5]
    e9 = {"rated_5": len(five), "below_half": sum(1 for v in five if v < 0.5),
          "median": float(np.median(five)) if five else None, "mean": float(np.mean(five)) if five else None}
    # counts per signal (planned and in hand) for the stamp
    def n_rows(sig, draws):
        return sum(1 for q in qa for c in CONFIGS for dd in draws if (c, q, dd) in sig)
    have = {"judge": sum(1 for (c, q, dd), v in judge.items() if v[1] in ("scored", "failed")),
            "judge_failed": sum(1 for v in judge.values() if v[1] == "failed"),
            "judge_unscored": sum(1 for v in judge.values() if v[1] == "unscored"),
            "concept": n_rows(concept, DRAWS),
            "papers": n_rows(papers, (1,)),
            "papers_null": sum(1 for v in papers.values() if v[0] is None),
            "faith": sum(1 for v in faith.values() if v[1] in ("ok", "no_answer", "error")),
            "faith_ok": sum(1 for v in faith.values() if v[1] == "ok"),
            "faith_status": dict(Counter(v[1] for v in faith.values())),
            "faith_error_over_context": sum(1 for v in faith.values() if v[1] == "error"
                                            and "exceeds the available context" in str(v[2])),
            "papers_null_reasons": dict(Counter(v[2] for v in papers.values() if v[0] is None)),
            "judge_failed_why": dict(Counter(v[2] for v in judge.values() if v[1] == "failed"))}
    all4 = sum(1 for q in qa for c in CONFIGS
               if (c, q, 1) in papers and (c, q, 1) in concept and judge.get((c, q, 1), (None, "unscored"))[1] != "unscored"
               and faith.get((c, q, 1), (None, "deferred"))[1] in ("ok", "no_answer", "error"))
    return {"qa": qa, "a": a, "b": b, "c": c_out, "d": d, "d_all": d_all, "e": {"points": e_pts, "rho_all": e_all,
            "rho_3to5": e_35, "e9": e9}, "have": have, "all4": all4}


# ---------------------------------------------------------------------------------------------------------------
# Source Data: one sheet per panel; the plate prints only numbers tied to a cell (S448 R8 (6))
# ---------------------------------------------------------------------------------------------------------------
def a_signal(sig: str) -> str:
    """Sheet a's signal names, the thresholds written from PASS_T and PASS_RELAXED (D160 (6) Q18: no typed threshold;
    D154: PASS_T drawn, PASS_RELAXED in Source Data only)."""
    return {"pass": f"judge pass rate, score {PASS_T} or more (the pass rate)",
            "pass3": f"judge pass rate, score {PASS_RELAXED} or more (relaxed threshold, Source Data only)",
            "papers": "MiniCheck precision against the papers"}[sig]


SIG_LABEL = {"judge": "judge correctness, plain call (key)", "concept": "concept recall (key)",
             "papers": "MiniCheck precision (papers)"}


def r9(x, nd=9):
    return None if x is None else round(float(x), nd)


def b_point(p):
    """Panel b's marker for an answer: its position and its marker kind; answers with the same one share a marker."""
    return (r9(p["concept_recall"]), r9(p["papers_precision"]), p["judge_pass"])


def pass_axis_label() -> str:
    """Panel a's axis label, the threshold written from PASS_T (D151's wording, D160 (6) Q18)."""
    return f"Pass rate {PASS_T}+ (%)"


FIG2_DIR = ROOT / "findings" / "figures_provisional" / "fig3_strategies"
FIG2_TOL = 1e-6                     # both workbooks round to 9 decimals
FIG3_V24_AT = "94262a0e"            # D201 Q2: the last commit whose Figure 3 is on key v2.4 (S511, S532)


def fig3_text(name: str, fig2_dir: Path, at: str | None) -> str:
    """Figure 3's file name: at commit at through git show (read only), or the working file when at is None."""
    if at is None:
        return (fig2_dir / name).read_text()
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{at}:{(fig2_dir / name).relative_to(ROOT)}"],
                       capture_output=True, text=True)
    if r.returncode:
        raise Refused(f"check_fig2: git show {at}:{name}: {r.stderr.strip()[:200]}")
    return r.stdout


def check_fig2(sheets: dict, collect_sha: str, fig2_dir: Path = FIG2_DIR, at: str | None = FIG3_V24_AT) -> str:
    """D160 (6), Q18: sheet a's judge pass rows (PASS_T and PASS_RELAXED: rate, interval, questions) equal Figure 3's
    sheet 3a 'strategy' rows at the same threshold (pass_rate_pct, ci95_lo_pct, ci95_hi_pct, questions_with_a_share),
    strategy by strategy, Figure 3 written from the same G1 collect (its figure3_provenance.json lists collect_sha
    among inputs_sha256). Refused (nothing written) on any difference; returns what was compared. D201 Q2: Figure 3 as
    it stood at commit at (default FIG3_V24_AT, key v2.4); at=None reads the plate's current files (key v2.5)."""
    prov = json.loads(fig3_text("figure3_provenance.json", fig2_dir, at))
    if collect_sha not in ((prov.get("provenance") or {}).get("inputs_sha256") or {}).values():
        raise Refused(f"check_fig2: {fig2_dir.name}/figure3_provenance.json lists no input with the G1 collect's "
                      f"sha256 {collect_sha[:12]}: Figure 3 was not written from these answers; nothing written")
    f2 = json.loads(fig3_text("figure3_numbers.json", fig2_dir, at))["sheets"]["Fig. 3a"]
    rows2 = [dict(zip(f2["columns"], r)) if isinstance(r, list) else r for r in f2["rows"]]
    want = {(r["strategy"], r["threshold"]): r for r in rows2 if r.get("row_kind") == "strategy"}
    s5 = sheets["Fig. 5a"]
    rows5 = [dict(zip(s5["columns"], r)) for r in s5["rows"]]
    by_label = {LABEL[c]: c for c in CONFIGS}
    bad, n = [], 0
    for sig, t in (("pass", PASS_T), ("pass3", PASS_RELAXED)):
        for r in (x for x in rows5 if x["row"] == "summary" and x["signal"] == a_signal(sig)):
            c = by_label[r["strategy"]]
            w = want.get((c, t))
            if w is None:
                bad.append(f"{r['strategy']} at {t}: no Figure 3 row")
                continue
            for mine, theirs in (("value", "pass_rate_pct"), ("ci_low", "ci95_lo_pct"), ("ci_high", "ci95_hi_pct"),
                                 ("n_questions", "questions_with_a_share")):
                n += 1
                if r[mine] is None or w[theirs] is None or abs(float(r[mine]) - float(w[theirs])) > FIG2_TOL:
                    bad.append(f"{r['strategy']} at {t}: {mine} {r[mine]}, Figure 3 {theirs} {w[theirs]}")
    if n != 2 * 4 * len(CONFIGS):
        bad.append(f"compared {n} values, want {2 * 4 * len(CONFIGS)} (six strategies, two thresholds, four values)")
    if bad:
        raise Refused(f"check_fig2: {len(bad)} of sheet a's judge pass values differ from Figure 3's for the same "
                      f"answers, first: " + "; ".join(bad[:3]) + "; nothing written")
    return (f"sheet a's judge pass rate, interval and questions at {PASS_T} and {PASS_RELAXED} equal Figure 3's sheet "
            f"3a for all {len(CONFIGS)} strategies ({n} values; Figure 3 written from the same G1 collect, "
            f"{collect_sha[:12]}{f'; Figure 3 at git {at}' if at else ''})")


def b_relaxed_col() -> str:
    """Sheet b's column for a pass at the relaxed threshold, named from PASS_RELAXED (D160 (6) Q18)."""
    return f"judge_pass_relaxed_{PASS_RELAXED}"


def threshold_texts() -> dict:
    """Every text that names a judge threshold, as written now (the selftest rebuilds them under other thresholds)."""
    fn = {"c": {"questions": ["q"] * 21}, "e": {"rho_all": {"answers": 1, "questions": 1}}, "b": [],
          "a": {c: {"papers": {"answers": 21, "s": None}, "pass": {"s": {"mean": i}}, "pass3": {"s": {"mean": i}}}
                for i, c in enumerate(CONFIGS)}}
    have = {"judge_failed": 0, "faith_status": {}, "papers_null_reasons": {}}
    claim = next(c for c in CLAIMS if c[0] == "F5-6")[3]
    return {"axis": pass_axis_label(), "sheet a pass": a_signal("pass"), "sheet a pass3": a_signal("pass3"),
            "sheet b relaxed column": b_relaxed_col(), "legend": legend_text(fn, "", have),
            "caption": caption_text("", ""), "claim F5-6": claim(fn)}


def check_threshold_texts() -> str:
    """D160 (6), Q18: every text that names a threshold follows PASS_T and PASS_RELAXED. Built as now, each names
    them; built again with the two set to 3 and 2, no text may still name 4 ("4 or more", "score 4", "4+") and each
    must name the new values. Refused otherwise (a threshold typed into a text)."""
    g = globals()
    saved = (g["PASS_T"], g["PASS_RELAXED"])
    try:
        now = threshold_texts()
        g["PASS_T"], g["PASS_RELAXED"] = 3, 2
        moved = threshold_texts()
    finally:
        g["PASS_T"], g["PASS_RELAXED"] = saved
    pass_k = ("axis", "sheet a pass", "legend", "caption", "claim F5-6")
    relaxed_k = ("sheet a pass3", "sheet b relaxed column", "legend", "caption", "claim F5-6")
    has = lambda t, k, v: re.search(rf"(?<![\d.]){v}(?: or more|\+)|\bscore {v}\b|\brelaxed {v}\b|_{v}$",   # noqa: E731
                                    t[k]) is not None
    bad = [f"{k} names no {saved[0]}" for k in pass_k if not has(now, k, saved[0])]
    bad += [f"{k} names no {saved[1]}" for k in relaxed_k if not has(now, k, saved[1])]
    bad += [f"{k} still names {saved[0]} with the pass threshold at 3" for k, v in moved.items()
            if re.search(rf"\b{saved[0]} or more|score {saved[0]}\b|\b{saved[0]}\+|relaxed {saved[0]}\b|_{saved[0]}$",
                         v)]
    bad += [f"{k} does not follow a pass threshold of 3" for k in pass_k if not has(moved, k, 3)]
    bad += [f"{k} does not follow a relaxed threshold of 2" for k in relaxed_k if not has(moved, k, 2)]
    if bad:
        raise Refused("threshold texts: " + "; ".join(bad) + "; nothing written")
    return (f"every threshold text (axis label, sheet a's signal names, sheet b's relaxed column, legend, caption, "
            f"claim F5-6) follows PASS_T {saved[0]} "
            f"and PASS_RELAXED {saved[1]} (rebuilt at 3 and 2, none still names {saved[0]})")


def build_sheets(fn, stamp):
    a_rows, b_rows, c_rows, d_rows, e_rows = [], [], [], [], []
    for c in CONFIGS:
        for sig, ref, unit in (("pass", "answer key", "%"), ("pass3", "answer key", "%"),
                               ("papers", "papers", "precision")):
            x = fn["a"][c][sig]
            s = x["s"]
            a_rows.append({"strategy": LABEL[c], "signal": a_signal(sig), "reference": ref, "row": "summary",
                           "question_id": None, "value": r9(s["mean"]) if s else None,
                           "ci_low": r9(s["mean_lo"]) if s else None, "ci_high": r9(s["mean_hi"]) if s else None,
                           "median": r9(s["median"]) if s else None, "q25": r9(s["quartile_25"]) if s else None,
                           "q75": r9(s["quartile_75"]) if s else None, "unit": unit,
                           "n_questions": len(x["per_q"]), "n_answers": x["answers"],
                           "draws": "1, 2, 3" if sig != "papers" else "1"})
            for q, v in x["per_q"]:
                a_rows.append({"strategy": LABEL[c], "signal": a_rows[-1]["signal"] if a_rows[-1]["row"] == "question"
                               else a_rows[-1]["signal"], "reference": ref, "row": "question", "question_id": q,
                               "value": r9(v), "ci_low": None, "ci_high": None, "median": None, "q25": None,
                               "q75": None, "unit": unit, "n_questions": None, "n_answers": None,
                               "draws": "1, 2, 3" if sig != "papers" else "1"})
    at_point = Counter(b_point(p) for p in fn["b"])          # answers drawn on one marker (the plate prints the count)
    for p in fn["b"]:
        b_rows.append({"strategy": LABEL[p["strategy"]], "question_id": p["question_id"], "draw": 1,
                       "concept_recall": r9(p["concept_recall"]), "papers_precision": r9(p["papers_precision"]),
                       "judge_correctness": p["judge_correctness"], "judge_pass": p["judge_pass"],
                       b_relaxed_col(): p[b_relaxed_col()], "labelled_example": p["example"], "answers_at_this_point": at_point[b_point(p)]})
    cc = fn["c"]
    for c in CONFIGS:
        for s in ("judge", "concept", "papers"):
            c_rows.append({"strategy": LABEL[c], "signal": SIG_LABEL[s],
                           "mean": r9(cc["means"][s][c]) if "means" in cc else None,
                           "rank_1_highest": r9(7 - cc["ranks_low1"][s][c]) if "means" in cc else None,
                           "questions": len(cc["questions"]), "W": r9(cc.get("W")), "W_P": r9(cc.get("P")),
                           "W_ci_low": r9((cc.get("W_ci") or [None])[0]), "W_ci_high": r9((cc.get("W_ci") or [None, None])[1]),
                           "mean_pairwise_rho": r9(cc.get("rho")), "pc1_share": r9(cc.get("pc1")),
                           "participation_ratio": r9(cc.get("pr"))})
    for c in CONFIGS:
        x = fn["d"][c]
        for k in range(6):
            d_rows.append({"strategy": LABEL[c], "faithfulness": k, "answers": x["counts"][k], "n": x["n"],
                           "share_pct": r9(100 * x["counts"][k] / x["n"]) if x["n"] else None,
                           # audit 27 Oct F3: the strategy's answerable answers d leaves out, by the call's status
                           "left_out_no_text": x["status"].get("no_answer", 0),
                           "left_out_unscored": x["status"].get("error", 0)})
    ea, e35 = fn["e"]["rho_all"], fn["e"]["rho_3to5"]
    for p in fn["e"]["points"]:
        e_rows.append({"strategy": LABEL[p["strategy"]], "question_id": p["question_id"], "draw": 1,
                       "faithfulness": p["faithfulness"], "papers_precision": r9(p["papers_precision"]),
                       "rho_all": r9(ea["rho"]), "rho_all_ci_low": r9(ea["lo"]), "rho_all_ci_high": r9(ea["hi"]),
                       "n_answers": ea["answers"], "n_questions": ea["questions"],
                       "rho_3to5": r9(e35["rho"]), "rho_3to5_ci_low": r9(e35["lo"]),
                       "rho_3to5_ci_high": r9(e35["hi"]), "n_answers_3to5": e35["answers"]})
    out = {}
    for L, rows in zip("abcde", (a_rows, b_rows, c_rows, d_rows, e_rows)):
        if not rows:
            raise Refused(f"panel {L}: no row to draw or to write (S448 R8 wants a data row per panel)")
        cols = list(rows[0])
        out[f"Fig. 5{L}"] = {"columns": cols, "rows": [[r.get(k) for k in cols] for r in rows]}
    return out


def write_workbook(sheets, path):
    S457.write_source_data([(n, s["columns"], s["rows"]) for n, s in sheets.items()], path)


# ---------------------------------------------------------------------------------------------------------------
# the plate
# ---------------------------------------------------------------------------------------------------------------
PLATE_H = 150.0
LINE_COL = {"single_pass": "black", "multi_hop": "orange", "verified_pass": "vermillion", "rlm_5": "sky blue",
            "rlm_10": "blue", "rlm_20": "bluish green"}
MARK = {"single_pass": "o", "multi_hop": "s", "verified_pass": "D", "rlm_5": "^", "rlm_10": "v", "rlm_20": "P"}


def cividis6():
    from matplotlib import colormaps
    cm = colormaps[S457.FLOCK["colour"]["continuous"]]
    return ["#%02X%02X%02X" % tuple(round(255 * v) for v in cm(int(round(255 * i / 5)))[:3]) for i in range(6)]


def draw(fn, sheets, paths):
    """Five panels, 183 x 150 mm. a: per strategy, the judge's pass rate against the key (86 questions, three draws)
    beside MiniCheck precision against the papers (the W questions, draw 1), each with its question dots, box and
    mean with Rule 2's interval. b: each draw-1 answer, concept recall (key) against MiniCheck precision (papers),
    its marker the judge's pass. c: each strategy's rank under the three signals, W. d: the judge with passages,
    the share of answers at each faithfulness score, per strategy. e: MiniCheck precision (papers) by faithfulness
    score, answer-level rho."""
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath
    plt.rcParams.update(S457.plate_rc("S473"))
    W, H = S457.FIG_W_MM, PLATE_H
    fig = plt.figure(figsize=(W / 25.4, H / 25.4), facecolor="#FFFFFF")
    printed = {}
    BLUE, ORANGE, GREY = S457.OKABE["blue"], S457.OKABE["vermillion"], S457.DOT_GREY
    t2p, fp = TextToPath(), FontProperties(family=S457.FONT, size=S457.PT)
    overlaps = {}
    rows_of = {name: [dict(zip(s["columns"], r)) for r in s["rows"]] for name, s in sheets.items()}

    def width(s):
        return t2p.get_text_width_height_descent(s, fp, ismath=False)[0] * S457.MM_PT

    def axes_mm(x, y, w, h):
        return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])

    def num(artist, entry):
        gid = f"s448num_{len(printed)}"
        artist.set_gid(gid)
        printed[gid] = entry
        return artist

    def fixed(artist, why):
        return num(artist, {"fixed": artist.get_text(), "why": why})

    def text_mm(x, y, s, **kw):
        return fig.text(x / W, 1 - y / H, s, **kw)

    def tied(x, y, sheet, row, fmt, **kw):
        vals = rows_of[sheet][row]
        s = S457_HALF.format(fmt, **{k: ("" if v is None else v) for k, v in vals.items()})
        t = text_mm(x, y, s, **kw)
        return num(t, {"sheet": sheet, "row": row, "format": fmt})

    def letter(ch, x, y):
        text_mm(x, y, S457.LETTER_CASE(ch), fontsize=S457.PT_LETTER, fontweight=S457.LETTER_WEIGHT,
                va="baseline", ha="left")

    def clean(ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # ---------------- a: two forests side by side
    LAB = 20.0
    A_TOP, A_H, A_W, A_GAP = 13.0, 47.0, 34.0, 5.0
    rows_y = list(range(len(CONFIGS)))
    pitch = A_H / len(CONFIGS)
    sheet_a = "Fig. 5a"
    for j, (sig, lim, ticks, xl) in enumerate((("pass", (0, 100), [0, 25, 50, 75, 100], pass_axis_label()),
                                                ("papers", (0, 1), [0, 0.25, 0.5, 0.75, 1], "MiniCheck precision"))):
        x0 = LAB + j * (A_W + A_GAP)
        ax = axes_mm(x0, A_TOP, A_W, A_H)
        span = lim[1] - lim[0]
        ax.set_xlim(lim[0] - 0.04 * span, lim[1] + 0.04 * span)
        ax.set_ylim(len(CONFIGS) - 0.5, -0.5)
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{v:g}" for v in ticks])
        ax.set_yticks(rows_y)
        ax.set_yticklabels([LABEL[c] for c in CONFIGS] if j == 0 else [])
        ax.tick_params(axis="y", length=0, pad=2)
        clean(ax)
        ax.set_xlabel(xl, labelpad=2)
        if any(ch.isdigit() for ch in xl):
            fixed(ax.xaxis.label, "the judge score a pass needs (Rule 5, D154; D151's wording)")
        mm_per = A_W / (span * 1.08)
        for i, c in enumerate(CONFIGS):
            x = fn["a"][c][sig]
            if x["s"] is None:
                continue
            vals = [v for _, v in x["per_q"]]
            S457.dot_row(ax, [(v - lim[0]) * mm_per for v in vals], vals, x["s"], i - 0.12, pitch, overlaps,
                         f"a {sig} {c}")
        ref = "Against the answer key" if sig == "pass" else "Against the papers"
        text_mm(x0, A_TOP - 6.2, ref, ha="left", va="baseline")
        first = next(k for k, r in enumerate(rows_of[sheet_a]) if r["row"] == "summary"
                     and r["signal"].startswith("judge" if sig == "pass" else "MiniCheck"))
        tied(x0, A_TOP - 2.4, sheet_a, first,
             "n = {n_questions} questions, three draws" if sig == "pass" else "n = {n_questions} questions, draw 1",
             ha="left", va="baseline")
    letter("a", 0.5, A_TOP - 6.2)

    # ---------------- b: each answer, key (x) against papers (y)
    B_X, B_W = 120.0, 58.0
    axb = axes_mm(B_X, A_TOP, B_W, A_H - 4.0)
    axb.set_xlim(-0.04, 1.04)
    axb.set_ylim(-0.04, 1.04)
    axb.set_xticks([0, 0.5, 1])
    axb.set_xticklabels(["0", "0.5", "1"])
    axb.set_yticks([0, 0.5, 1])
    axb.set_yticklabels(["0", "0.5", "1"])
    clean(axb)
    axb.set_xlabel("Concept recall (key)", labelpad=2)
    axb.set_ylabel("MiniCheck precision (papers)", labelpad=2)
    pts = fn["b"]
    for p in pts:
        if p["judge_pass"]:
            axb.plot([p["concept_recall"]], [p["papers_precision"]], ls="none", marker="o", ms=1.6 / S457.MM_PT,
                     mfc="#FFFFFF", mec=BLUE, mew=0.6, zorder=3)
        else:
            axb.plot([p["concept_recall"]], [p["papers_precision"]], ls="none", marker="^", ms=1.8 / S457.MM_PT,
                     mfc=ORANGE, mew=0, zorder=4)
    # a marker that stands for several answers carries their count, tied to the first such row of the sheet
    rows_b = rows_of["Fig. 5b"]
    seen = set()
    rend = fig.canvas.get_renderer()
    px_mm = fig.dpi / 25.4
    y_per_mm = 1.08 / (A_H - 4.0)                       # panel b's y data units per mm
    marks = [axb.transData.transform((q["concept_recall"], q["papers_precision"])) for q in pts]
    placed_bb = []                                      # count labels already placed, display units

    def clear(bb, gap_mm=0.8):
        g = gap_mm * px_mm
        if any(bb.x0 < o.x1 + g and o.x0 < bb.x1 + g and bb.y0 < o.y1 + g and o.y0 < bb.y1 + g for o in placed_bb):
            return False
        r_ = 0.8 * px_mm                                # a marker's radius
        return not any(bb.x0 - r_ < mx < bb.x1 + r_ and bb.y0 - r_ < my < bb.y1 + r_ for mx, my in marks)

    for j, r in enumerate(rows_b):
        pt = (r["concept_recall"], r["papers_precision"], r["judge_pass"])
        if r["answers_at_this_point"] > 1 and pt not in seen:
            seen.add(pt)
            # beside the marker, on the right unless another marker sits there (then on the left); when neither
            # side is clear of other labels and markers, the nearest clear height, joined to the marker by a line
            right_busy = any(0 < q["concept_recall"] - pt[0] < 0.1 and abs(q["papers_precision"] - pt[1]) < 0.04
                             for q in pts)
            sides = ("left", "right") if right_busy else ("right", "left")
            cands = [(s, 0.0) for s in sides] + [(s, k * sgn * 3.6) for k in range(1, 7) for sgn in (1, -1)
                                                 for s in sides]
            t = axb.text(0, 0, str(r["answers_at_this_point"]), va="center", clip_on=False)
            choice = None
            for side, dy in cands:
                t.set_position((pt[0] + (0.03 if side == "right" else -0.03), pt[1] + dy * y_per_mm))
                t.set_ha("left" if side == "right" else "right")
                bb = t.get_window_extent(rend)
                if clear(bb):
                    choice = (side, dy)
                    break
            if choice is None:
                choice = cands[0]
                t.set_position((pt[0] + (0.03 if choice[0] == "right" else -0.03), pt[1]))
                t.set_ha("left" if choice[0] == "right" else "right")
            placed_bb.append(t.get_window_extent(rend))
            if choice[1]:
                sx = 0.012 if choice[0] == "right" else -0.012
                axb.plot([pt[0] + sx, pt[0] + 2 * sx], [pt[1], pt[1] + choice[1] * y_per_mm], color="#000000",
                         lw=0.5, solid_capstyle="butt", clip_on=False, zorder=2)
            num(t, {"sheet": "Fig. 5b", "row": j, "format": "{answers_at_this_point}"})
    ex = [p for p in pts if p["example"]]
    if ex:
        p = ex[0]
        axb.annotate("", xy=(p["concept_recall"], p["papers_precision"]), xytext=(p["concept_recall"] + 0.15, 0.35),
                     arrowprops={"arrowstyle": "-", "lw": 0.5, "color": "#000000"})
        fixed(axb.text(p["concept_recall"] + 0.16, 0.3, "15_rabies_tanzania_FR1", ha="left", va="center"),
              "the labelled example (LIST.md Figure 5)")
    # key
    ky = A_TOP - 6.2
    kx = B_X
    k1 = axes_mm(kx, ky - 2.0, 3.0, 2.6)
    k1.set_axis_off(); k1.set_xlim(0, 3); k1.set_ylim(2.6, 0)
    k1.plot([1.5], [1.3], ls="none", marker="o", ms=1.6 / S457.MM_PT, mfc="#FFFFFF", mec=BLUE, mew=0.6)
    text_mm(kx + 3.5, ky, "judge passes", ha="left", va="baseline")
    kx2 = kx + 3.5 + width("judge passes") + 4.0
    k2 = axes_mm(kx2, ky - 2.0, 3.0, 2.6)
    k2.set_axis_off(); k2.set_xlim(0, 3); k2.set_ylim(2.6, 0)
    k2.plot([1.5], [1.3], ls="none", marker="^", ms=1.8 / S457.MM_PT, mfc=ORANGE, mew=0)
    text_mm(kx2 + 3.5, ky, "judge fails", ha="left", va="baseline")
    num(text_mm(B_X, A_TOP - 2.4, f"n = {len(pts)} answers, draw 1", ha="left", va="baseline"),
        {"sheet": "Fig. 5b", "where": {"draw": 1}, "format": "n = {count} answers, draw 1"})
    letter("b", B_X - 15.0, A_TOP - 6.2)

    # ---------------- c: ranks under each signal, W
    C_TOP, C_H = 84.0, 50.0
    C_X, C_W = LAB, 34.0
    axc = axes_mm(C_X, C_TOP, C_W, C_H)
    axc.set_xlim(-0.25, 2.25)
    axc.set_ylim(6.5, 0.5)
    axc.set_xticks([0, 1, 2])
    axc.set_xticklabels(["Judge", "Concepts", "Papers"])
    axc.set_yticks([1, 2, 3, 4, 5, 6])
    axc.set_yticklabels(["1", "2", "3", "4", "5", "6"])
    axc.set_ylabel("Rank, highest first", labelpad=2)
    clean(axc)
    axc.tick_params(axis="x", length=0, pad=3)
    cc = fn["c"]
    if "means" in cc:
        for c in CONFIGS:
            ys = [7 - cc["ranks_low1"][s][c] for s in ("judge", "concept", "papers")]
            col = S457.OKABE[LINE_COL[c]]
            axc.plot([0, 1, 2], ys, color=col, lw=0.9, marker=MARK[c], ms=1.6 / S457.MM_PT, mew=0, zorder=3)
        # direct labels on the right, at each strategy's rank under the papers (ties side by side)
        placed = defaultdict(int)
        for c in sorted(CONFIGS, key=lambda c: (7 - cc["ranks_low1"]["papers"][c], CONFIGS.index(c))):
            y = 7 - cc["ranks_low1"]["papers"][c]
            off = placed[y]
            placed[y] += 1
            t = axc.text(2.2, y + 0.42 * off, LABEL[c], ha="left", va="center", clip_on=False)
            if any(ch.isdigit() for ch in LABEL[c]):
                fixed(t, "a strategy's direct label")
        tied(C_X, C_TOP - 6.2, "Fig. 5c", 0, "W = {W:.2f}, exact P = {W_P:.3f}" if cc["P"] >= 0.001 else
             "W = {W:.2f}, exact P < 0.001", ha="left", va="baseline")
        tied(C_X, C_TOP - 2.4, "Fig. 5c", 0, "n = {questions} questions", ha="left", va="baseline")
    letter("c", 0.5, C_TOP - 6.2)

    # ---------------- d: faithfulness with passages, share at each score
    D_X, D_W = 92.0, 34.0
    axd = axes_mm(D_X, C_TOP, D_W, C_H)
    cols6 = cividis6()
    axd.set_xlim(0, 100)
    axd.set_ylim(len(CONFIGS) - 0.5, -0.5)
    axd.set_xticks([0, 50, 100])
    axd.set_xticklabels(["0", "50", "100"])
    axd.set_yticks(rows_y)
    axd.set_yticklabels([LABEL[c] for c in CONFIGS])
    axd.tick_params(axis="y", length=0, pad=2)
    clean(axd)
    axd.set_xlabel("Answers (%)", labelpad=2)
    rows_d = rows_of["Fig. 5d"]
    for i, c in enumerate(CONFIGS):
        x = fn["d"][c]
        left = 0.0
        for k in range(6):
            w_ = 100 * x["counts"][k] / x["n"] if x["n"] else 0
            if w_ > 0:
                axd.barh([i], [w_], left=[left], height=0.62, color=cols6[k], lw=0)
            left += w_
        r0 = next(j for j, r in enumerate(rows_d) if r["strategy"] == LABEL[c] and r["faithfulness"] == 0)
        tied(D_X + D_W + 1.0, C_TOP + C_H * (i + 0.5) / len(CONFIGS) + 1.0, "Fig. 5d", r0, "n = {n}",
             ha="left", va="baseline")
    # the score key above the panel
    kx = D_X
    text_mm(kx, C_TOP - 6.2, "Faithfulness score", ha="left", va="baseline")
    kx = D_X
    for k in range(6):
        kk = axes_mm(kx, C_TOP - 4.6, 2.6, 2.4)
        kk.set_axis_off(); kk.set_xlim(0, 1); kk.set_ylim(0, 1)
        kk.add_patch(plt.Rectangle((0, 0), 1, 1, color=cols6[k], lw=0))
        fixed(text_mm(kx + 3.0, C_TOP - 2.6, str(k), ha="left", va="baseline"), "the key's score")
        kx += 3.0 + width(str(k)) + 2.2
    letter("d", D_X - 18.5, C_TOP - 6.2)

    # ---------------- e: papers precision by faithfulness score
    E_X, E_W = 151.0, 28.0
    axe = axes_mm(E_X, C_TOP, E_W, C_H)
    axe.set_xlim(-0.6, 5.6)
    axe.set_ylim(-0.04, 1.04)
    axe.set_xticks(range(6))
    axe.set_xticklabels([str(k) for k in range(6)])
    axe.set_yticks([0, 0.5, 1])
    axe.set_yticklabels(["0", "0.5", "1"])
    clean(axe)
    axe.set_xlabel("Faithfulness score", labelpad=2)
    axe.set_ylabel("MiniCheck precision (papers)", labelpad=2)
    import numpy as np
    for k in range(6):
        vals = sorted(p["papers_precision"] for p in fn["e"]["points"] if p["faithfulness"] == k)
        if not vals:
            continue
        mm_x = E_W / 6.2
        ys_mm = [v * (C_H / 1.08) for v in vals]
        off, over = S457.swarm(ys_mm, half=2.0, pitch=0.5, dot=S457.DOT_MM)
        overlaps[f"e {k}"] = over
        # dots over the median line, so a score with one answer still shows its dot
        axe.plot([k + o / mm_x for o in off], vals, ls="none", marker="o", ms=S457.DOT_MM / S457.MM_PT,
                 mfc=GREY, mew=0, zorder=5)
        med = float(np.median(vals))
        axe.plot([k - 0.32, k + 0.32], [med, med], color="#000000", lw=1.0, solid_capstyle="butt", zorder=4)
    ea = fn["e"]["rho_all"]
    if ea["rho"] is not None:
        tied(E_X, C_TOP - 6.2, "Fig. 5e", 0, "rho = {rho_all:.2f}", ha="left", va="baseline")
    tied(E_X, C_TOP - 2.4, "Fig. 5e", 0, "n = {n_answers} answers, draw 1", ha="left", va="baseline")
    letter("e", E_X - 11.0, C_TOP - 6.2)

    # the key to the dots (a, e), one line under the plate
    ky = C_TOP + C_H + 11.5
    text_mm(LAB, ky, "Grey dot: one question (a) or one answer (e). Box: quartiles, line: median. Blue: mean with "
            "its 95% interval.", ha="left", va="baseline")
    fixed(fig.texts[-1], "the key: a percentage in words")
    S457.finish_plate(fig, W, H, paths, title="Figure 5")
    return W, H, printed, overlaps


class _HalfUp(__import__("string").Formatter):
    def format_field(self, value, spec):
        m = re.fullmatch(r"(\+?)\.(\d+)f", spec)
        if m and isinstance(value, (int, float)) and not isinstance(value, bool):
            return S457.half_up(value, int(m.group(2)))
        return format(value, spec)


S457_HALF = _HalfUp()


# ---------------------------------------------------------------------------------------------------------------
# texts: legend draft, Source Data caption, claims list
# ---------------------------------------------------------------------------------------------------------------
def p_txt(p):
    return "< 0.001" if p < 0.001 else S457.half_up(p, 3)


def ci_txt(lo, hi, nd=2):
    return "undefined" if lo is None or hi is None else f"{S457.half_up(lo, nd)} to {S457.half_up(hi, nd)}"


def legend_text(fn, stamp, have):
    """The figure's legend: what each panel draws, with its n (Valerio, 23 October: describe the image only, about
    120 to 250 words, as the resubmission's captions; the data stamp stays in legend_draft.md's header)."""
    cc, ea = fn["c"], fn["e"]["rho_all"]
    nq = len(cc["questions"])
    nb = len(fn["b"])
    ex = [p for p in fn["b"] if p["example"]]
    ex_txt = (f" The labelled answer is {EXAMPLE[1]} ({LABEL[EXAMPLE[0]]})." if ex else "")
    no_text = have["judge_failed"]
    d_no_text = have["faith_status"].get("no_answer", 0)   # audit 27 Oct F3: d scores no answer without text
    left_out = []
    if have["faith_status"].get("error", 0):
        left_out.append(f"unscored faithfulness calls (n = {have['faith_status']['error']})")
    nulls = sum(have["papers_null_reasons"].values())
    if nulls:
        left_out.append(f"MiniCheck nulls (n = {nulls})")
    # a box's own n where a MiniCheck null leaves a strategy one question short of the W set (exact n per box)
    short = {}
    for c in CONFIGS:
        k = fn["a"][c]["papers"]["answers"]
        if k != nq:
            short.setdefault(k, []).append(LABEL[c])
    exc = "".join(f"; {k} for " + (", ".join(v[:-1]) + " and " + v[-1] if len(v) > 1 else v[0])
                  for k, v in sorted(short.items(), reverse=True))
    return (
        "**Figure 5 | Signals measured against the answer key and against the papers.** "
        "Answers of six generation strategies (gemini-3-flash-preview) to answerable questions. "
        f"**a**, Per strategy, pass rate against the key (n = {N_ANSWERABLE} questions, "
        "three draws each) and MiniCheck precision against the papers (share of claims supported by the source papers; "
        f"draw 1, n = {nq} questions{exc}). The pass rate is the share of answers the judge scores {PASS_T} or more "
        f"for correctness; the rates at {PASS_RELAXED} or more are in the Source Data. Grey dots, one question; box, quartiles; black line, median; "
        "blue, mean with its two-sided 95% percentile interval over 10,000 question resamples. "
        "**b**, Concept recall against the key (x) and MiniCheck precision against the papers (y) for each draw-1 "
        f"answer to those questions (n = {nb} answers). Open circle, judge pass (score {PASS_T} or more); filled "
        f"triangle, judge fail; a number "
        f"beside or linked to a marker counts the answers at that point.{ex_txt} "
        "**c**, Each strategy's rank by mean judge correctness score (Judge) and concept recall (Concepts), three "
        "draws, and MiniCheck precision (Papers), draw 1, on the questions of a; ties share a rank. W, Kendall's "
        "coefficient of concordance over the three rankings, with its exact one-sided P. "
        "**d**, Share of answers at each faithfulness score (0 to 5) given by the judge reading the retrieved passages, "
        "three draws; n per strategy at right. "
        "**e**, MiniCheck precision by faithfulness score, one grey dot per draw-1 answer "
        f"(n = {ea['answers']} answers, {ea['questions']} questions); black line, median; rho, answer-level Spearman "
        "correlation. "
        f"Answers with no text (n = {no_text}) score 0 for the judge and concept recall"
        + ((" and are left out of d" if d_no_text == no_text else f"; in d, answers with no text (n = {d_no_text}) "
            "are left out") if d_no_text else "")
        + (("; " + " and ".join(left_out) + " are left out") if left_out else "") + "."
    )


def caption_text(stamp, tag):
    return (f"# Source Data Fig. 5, caption\n\n**Source Data Fig. 5 | Numerical values plotted in Figure 5.** "
            f"Provisional{tag}. Data stamp: {stamp}. One sheet per panel. Sheet Fig. 5a: per strategy and signal "
            f"(the judge's pass rate against the key at score {PASS_T} or more, drawn, and at the relaxed threshold of "
            f"{PASS_RELAXED} or more, in Source Data only; MiniCheck precision against the papers) a 'summary' row (mean, "
            "its 95% percentile interval over 10,000 question resamples, median, quartiles, questions, answers, draws) "
            "and one 'question' row per plotted dot. Sheet Fig. 5b: each plotted answer, its concept recall, "
            f"MiniCheck precision, judge correctness, pass (score {PASS_T} or more) and pass at the relaxed threshold "
            f"(score {PASS_RELAXED} or more), whether it is the labelled example, and how many answers share "
            "its marker. Sheet Fig. 5c: "
            "per strategy and signal the mean on the questions W uses, its rank (1 highest), Kendall's W with its "
            "exact P and interval, mean pairwise rho, PC1 share and participation ratio. Sheet Fig. 5d: per strategy "
            "the answers at each faithfulness score of the judge with passages and their share, and the strategy's "
            "answers left out of d (left_out_no_text: no text, so no call; left_out_unscored: a call that returned "
            "no score). Sheet Fig. 5e: each "
            "plotted answer's faithfulness score and MiniCheck precision, with the answer-level Spearman rho and its "
            "question-resample interval, over all scores and over scores of three or more. Generated by "
            f"`uv run --frozen python {SCRIPT} figure` from S3's collect output, L1's and L3's rows.\n\n"
            "Proposed Data Availability sentence: \"The source data for Figure 5 is in Supplementary Data 6.\"\n")   # D303 follow-up: Data n + 1 (D302)


# the paper's and the letter's Figure 5 numbers, as S393 and S318 locate and print them (their file:line cited)
CLAIMS = [
    ("F5-1", "Main Text, Results, 'Faithfulness scoring by the LLM judge showed a ceiling effect, with 80.3%'; "
             "Discussion, 'The judge rated 80.3% of answers as perfectly faithful' (S393 E8, "
             "findings/recompute/S393_early_claims.md:139)", "80.3% of answers at 5/5 faithfulness",
     lambda fn: f"{S457.half_up(100 * fn['d_all']['at5'] / fn['d_all']['n'], 1)}% ({fn['d_all']['at5']:,} of "
                f"{fn['d_all']['n']:,} answers, judge with passages, three draws)"),
    ("F5-2", "Main Text, Results, 'Source-grounded precision spanned 0.00 to 1.00 (median 0.57), with 38.0%' (S393 E9, "
             "S393_early_claims.md:143)", "38.0% (161 of 424) of the 5/5 answers below 0.50 precision, median 0.57",
     lambda fn: (f"{fn['e']['e9']['below_half']} of {fn['e']['e9']['rated_5']} below 0.5 "
                 f"({S457.half_up(100 * fn['e']['e9']['below_half'] / fn['e']['e9']['rated_5'], 1)}%), median "
                 f"{S457.half_up(fn['e']['e9']['median'], 2)} ({S457.half_up(100 * fn['e']['e9']['median'], 1)}%) "
                 "(draw 1 so far)") if fn['e']['e9']['rated_5'] else "none yet"),
    ("F5-3", "Main Text, Results, 'Across the top three score tiers (scores 3 to 5, 500 answers), this association "
             "disappeared' (S393 E10, S393_early_claims.md:147)", "Spearman rho 0.05, P 0.24, 500 answers",
     lambda fn: (f"rho {S457.half_up(fn['e']['rho_3to5']['rho'], 2)}, interval "
                 f"{ci_txt(fn['e']['rho_3to5']['lo'], fn['e']['rho_3to5']['hi'])}, {fn['e']['rho_3to5']['answers']} "
                 "answers (Rule 7: no plain P)") if fn['e']['rho_3to5']['rho'] is not None else "too few answers"),
    ("F5-4", "Main Text, Results, 'Despite this divergence in absolute scores'; Figure 5 legend, 'Kendall's W over the "
             "three rankings is 0.927' (scripts/s318/g3_ranking.py:259-276)", "W 0.93, exact P < 0.001",
     lambda fn: f"W {S457.half_up(fn['c']['W'], 2)}, exact P {p_txt(fn['c']['P'])} on {len(fn['c']['questions'])} "
                "questions (grounding against the papers, D35)" if "W" in fn["c"] else "not computed"),
    ("F5-5", "Main Text, Results, 'Their per-configuration scores correlated at a mean pairwise' "
             "(scripts/s318/g3_ranking.py:277-286)", "mean rho 0.90 (0.73 to 0.96), PC1 93.6%, participation ratio 1.14",
     lambda fn: (f"mean rho {S457.half_up(fn['c']['rho'], 2)} ({ci_txt(*fn['c']['rho_ci'])}), PC1 "
                 f"{S457.half_up(100 * fn['c']['pc1'], 1)}%, participation ratio {S457.half_up(fn['c']['pr'], 2)}")
     if "W" in fn["c"] else "not computed"),
    ("F5-6", "experiments/LIST.md 'Figure 5', Found (computed by scripts/S487_kendall_grounded.py; A6): verified pass worst by "
             "correctness and best by grounding against the papers", "verified pass last by correctness, first by "
             "grounding (+0.22)",
     lambda fn: "pass rate rank of verified pass " + str(1 + sorted(CONFIGS, key=lambda c: -fn['a'][c]['pass']['s']['mean']).index('verified_pass'))
                + f" of 6 at score {PASS_T} (" + str(1 + sorted(CONFIGS, key=lambda c: -fn['a'][c]['pass3']['s']['mean']).index('verified_pass'))
                + f" at the relaxed {PASS_RELAXED}); papers rank " + (str(1 + sorted([c for c in CONFIGS if fn['a'][c]['papers']['s']],
                                                          key=lambda c: -fn['a'][c]['papers']['s']['mean']).index('verified_pass'))
                                           if fn['a']['verified_pass']['papers']['s'] else "-") + " of 6"),
]


# D304 (8 Nov): each row's anchor in the agreed text (Claude Docs rev 3688), as the live documents read with every mark
# accepted: the main text and the Supplementary Notes as S602 wrote them from the same export. (document, the words that
# must be in it, the agreed claim, the strings 'S473 gives now' must hold for the row to match), or (None, why retired):
# a retired row is one the agreed text no longer states; its value is still computed. F5-6 was a LIST.md finding until
# D304; Supplementary Note 6 now states it.
CLAIM_DOCS = {"main text": ROOT / "resubmission/04_manuscript/02_Main_Text.docx",
              "SI": ROOT / "resubmission/06_supplementary/Supplementary_Information.docx"}
ANCHORS = {
    "F5-1": ("main text", "it gave the maximum of 5/5 to 73.6% of 1,539 scored answers",
             "Results, 'The judge also scores faithfulness': 73.6% of 1,539 scored answers at 5/5", ("73.6%", "1,539")),
    "F5-2": ("SI", "The 369 draw-1 answers scored 5/5 had a median of 82.4% of their verifiable claims supported by the "
                   "papers, against 54.5% for the 133 scored below 5, yet 8.7% of the 5/5 answers had fewer than half "
                   "of their claims supported",
             "Supplementary Note 6, 'Checked against the source papers': of the 369 draw-1 answers at 5/5, median "
             "82.4% supported, 8.7% below half", ("of 369", "(8.7%)", "(82.4%)")),
    "F5-3": (None, "the agreed text gives no rank correlation over scores 3 to 5; Supplementary Note 6 sets the supported "
                   "share of the 5/5 answers against the rest (F5-2)"),
    "F5-4": ("SI", "Kendall's W over the three rankings, 0.30; exact one-sided P = 0.534; n = 86 questions",
             "Supplementary Note 6, 'Strategy-level rankings diverged' (and Results, 'Kendall's W 0.30; n = 86 "
             "questions'): W 0.30, exact one-sided P 0.534, 86 questions", ("W 0.30", "P 0.534", "86 questions")),
    "F5-5": (None, "the agreed text gives no mean pairwise correlation, PC1 share or participation ratio"),
    "F5-6": ("SI", "Claim checking ranked passage verification first and single pass retrieval second",
             "Supplementary Note 6, 'Strategy-level rankings diverged': claim checking ranks passage verification "
             "first", ("papers rank 1 of 6",)),
}


def _docx_text(p) -> str:
    """A .docx's paragraphs as text, every mark accepted (w:t runs; deleted text is w:delText and left out)."""
    import zipfile
    x = zipfile.ZipFile(p).read("word/document.xml").decode()
    return "\n".join("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", m.group()))
                     for m in re.finditer(r"<w:p[ >].*?</w:p>", x, re.S))


def claims_md(fn, stamp):
    texts = {k: _docx_text(p) for k, p in CLAIM_DOCS.items() if p.exists()}
    out = ["# Figure 5: claims list (D82)", "",
           f"Written by `{SCRIPT} figure` with the plate it sits beside. Data stamp: {stamp}.", "",
           "Every Figure 6 number S393 and S318 located in the submitted Main Text, the Figure 5 legend and the letter, "
           "against what S473 computes now. Provisional: the comparison is read again on the final run. D304 (8 "
           "November): each row is anchored on the sentence of the agreed text (Claude Docs rev 3688) that now states "
           "it, found in the live document with every mark accepted, or retired with the reason; a retired row's "
           "value is still computed. 'Submitted' gives the row's old location and value. Documents read: "
           + "; ".join(f"`{p.relative_to(ROOT)}` sha256 {hashlib.sha256(p.read_bytes()).hexdigest()[:12]}"
                       for p in CLAIM_DOCS.values() if p.exists()) + ".", "",
           "| Row | Where (search for) | Claimed | S473 gives now | Status | In the text now | Submitted |",
           "|---|---|---|---|---|---|---|"]
    for cid, where, claimed, f in CLAIMS:
        try:
            got = f(fn)
        except Exception as e:                       # noqa: BLE001  a value not computable on these rows
            got = f"not computable on these rows ({type(e).__name__})"
        an = ANCHORS[cid]
        if an[0] is None:
            out.append(f"| {cid} | {where} | {claimed} | {got} | provisional | retired: {an[1]} | as Where |")
            continue
        d, words, now, want = an
        found = "yes" if words in texts.get(d, "") else "NOT FOUND: re-read the document"
        st = "matches" if all(w in got for w in want) else "differs"
        out.append(f"| {cid} | {now} | {', '.join(want)} | {got} | {st} (provisional) | {found} | {where}; {claimed} |")
    return "\n".join(out) + "\n"

# ---------------------------------------------------------------------------------------------------------------
# figure
# ---------------------------------------------------------------------------------------------------------------
OWNED = ("Figure 5*", "Source Data Fig. 5*", "figure5_numbers.json", "figure5_provenance.json", "legend_draft.md",
         "claims.md", "fig5_data_state.json")
FIG5_S473_AT = "a16b2460"           # the last commit that changed fig5/figure5_numbers.json before D166 (S497's plate)


def figure(args):
    import tempfile
    with tempfile.TemporaryDirectory(prefix="S473_views_") as tmp:
        return _figure(args, Path(tmp))


def _figure(args, tmp: Path):
    import shutil
    if not args.out:
        raise Refused(f"D166: {OUT.relative_to(ROOT)} holds the locked Figure 5 (scripts/S497_fig5_d166.py); this "
                      "command draws S473's plate of 26 October and writes only into --out <folder>")
    out = Path(args.out).resolve()
    import lock_equiv                                       # D204: d66daa28 but for the second judge's machines
    if not lock_equiv.accepts(S463.LOCK_TOML):
        raise Refused("experiments/LOCK.toml is not D88's d66daa28: the judge rows are checked against it")
    S457.figure_lock_agreed()
    try:
        srcs = pull_sources(Path(args.src).expanduser().resolve(), tmp) if args.src else frozen_sources(tmp)
    except FR.FrozenInputError as e:
        raise Refused(f"frozen input: {e}") from None
    rep = reproduce()
    groups = S463.key_groups()
    pull_log = json.loads(srcs["pull"].read_text())
    collect = srcs["collect"]
    ans_dirs = srcs["ans_dirs"]
    answers, ans_inputs, _ = S463.read_answers(ans_dirs)
    read = S463.read_collect(collect, list(DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = read_l3(groups)
    rep.append(l3["reproduced"])
    l1 = read_l1(srcs["l1"], l3["header"], groups)
    check_same_answers(l1, l3)
    # S3 judged the same texts as L1 and L3 scored: each answer's text sha256 in the records S3 judged equals L3's
    txt = answer_text_sha(ans_dirs)
    diff = sorted(k for (c, q, d), r in l3["rows"].items()
                  for k in [f"{INDEX}|{c}|{q}|d{d}"] if txt.get(k) != r.get("answer_sha256"))
    if diff:
        raise Refused(f"{len(diff)} answers judged by S3 differ from the texts L3 and L1 scored, first {diff[0]}")
    rep.append("S3's judged answers (K1's copy with G1R15's 15 reruns over it) equal the texts L1 and L3 scored "
               "(answer sha256, all 2,430)")
    faith_rows = {}
    for x in read_jsonl(collect):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    k1 = read_k1(srcs["k1"])
    fn = compute(read, l3, l1, faith_rows, groups)
    have = fn["have"]
    side = read["side"]
    when = (side.get("_provenance") or {}).get("at")
    # s3_guard.py collect writes "at" in the local time of the machine that ran it, with no zone; the pull and the
    # collect run here, on this machine, so it is converted to UTC like the read time beside it
    if when:
        from datetime import datetime, timezone
        when = datetime.fromisoformat(when).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    n4 = fn["all4"]
    stamp = (f"PROVISIONAL: {n4} of {PLANNED['papers']} draw-1 answerable answers have a final row from all four "
             f"scorers; judge plain "
             f"call {have['judge']:,} of {PLANNED['judge']:,}, concept recall {have['concept']:,} of "
             f"{PLANNED['concept']:,}, MiniCheck against the papers {have['papers']:,} of {PLANNED['papers']:,} "
             f"(draw 1), judge with passages {have['faith']:,} of {PLANNED['faith']:,}; read "
             f"{pull_log['ended_utc']} (S3 collect {when}, run_sha256 {str(read['run_sha256'])[:12]})")
    tag = f" (provisional, {n4} of {PLANNED['papers']})"
    plate = f"Figure 5{tag}"
    sd = f"Source Data Fig. 5{tag}"
    sheets = build_sheets(fn, stamp)
    rep.append(check_threshold_texts())                       # D160 (6), Q18: refused before anything is written
    rep.append(check_fig2(sheets, sha256_file(collect)))
    stage = out.with_name(out.name + ".staging")
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    paths = {k: stage / f"{plate}.{k}" for k in ("pdf", "svg", "png")}
    W_, H_, printed, overlaps = draw(fn, sheets, paths)
    FR.check_pdf_deterministic(paths["pdf"])                    # D155: no write time in the PDF or the SVG
    FR.check_svg_deterministic(paths["svg"])
    write_workbook(sheets, stage / f"{sd}.xlsx")
    FR.deterministic_xlsx(stage / f"{sd}.xlsx")                 # D155: openpyxl's write times removed
    (stage / f"Source Data Fig. 5 caption{tag}.md").write_text(caption_text(stamp, tag))
    (stage / "figure5_numbers.json").write_text(json.dumps({
        "stamp": stamp, "what": "every number the plate draws, sheet by sheet as Source Data Fig. 5 holds them "
                                "(S448 R8 compares the workbook with this file)",
        "sheets": sheets, "printed": printed}, indent=1, ensure_ascii=False) + "\n")
    leg = legend_text(fn, stamp, have)
    (stage / "legend_draft.md").write_text(
        "# Figure 5, title and legend (draft)\n\n"
        f"Written by `{SCRIPT} figure` from the plotted numbers. Data stamp: {stamp}.\n\n" + leg + "\n")
    (stage / "claims.md").write_text(claims_md(fn, stamp))
    state = {"stamp": stamp, "planned": PLANNED, "have": have, "answers_with_all_four": n4,
             "W_questions": fn["c"]["questions"], "W_partial_blocks_left_out": fn["c"]["partial_blocks_left_out"],
             "c": {k: v for k, v in fn["c"].items() if k not in ("questions",)},
             "e": {k: v for k, v in fn["e"].items() if k != "points"}, "d_all": fn["d_all"],
             "d_status": {c: fn["d"][c]["status"] for c in CONFIGS},
             "not_drawn": {"K1 (RAGChecker, RAGAS; Supplementary per the figure story review, Q for Valerio)": k1,
                           "L1 key stage (MiniCheck against the key) rows": len(l1["stages"]["key"]),
                           "L1 overlap stage (lexical baselines) rows": len(l1["stages"]["overlap"])},
             "dots_overlapping": overlaps, "pull": pull_log}
    (stage / "fig5_data_state.json").write_text(json.dumps(state, indent=1, default=str) + "\n")
    files = {p.name: sha256_file(p) for p in sorted(stage.iterdir()) if p.name != "figure5_provenance.json"}
    (stage / "figure5_provenance.json").write_text(json.dumps({
        # D155: no build time and no HEAD (each made the file differ on every build); the code that ran is named by
        # the sha256 of the script and of the three modules it imports, the data by inputs_sha256
        "provenance": {"script": SCRIPT, "script_sha256": sha256_file(ROOT / SCRIPT),
                       "imports_sha256": {m: sha256_file(ROOT / "scripts" / m) for m in (
                           "S457_fig2_panels.py", "S463_fig2_ranking.py", "fig_repro.py")},
                       "command": f"uv run --frozen python {SCRIPT} figure"
                                  + (" --from <pull dir>" if args.src else "")},
        "stamp": stamp, "reproduced": rep, "page_mm": [W_, H_],
        "inputs": {"s3_collect": {"path": srcs["collect_name"], "sha256": sha256_file(collect),
                                  "sidecar": srcs["side"]},
                   "answers": {label_of(k, srcs["labels"]): v for k, v in ans_inputs.items()}, "l3": {"path": "findings/recompute/L3/concept_recall.jsonl",
                                                 "sha256": sha256_file(L3_DIR / "concept_recall.jsonl")},
                   "l1": {f"{s}": len(v) for s, v in l1["stages"].items()},
                   "l1_files": {f"l1/{p.relative_to(srcs['l1']).as_posix()}": sha256_file(p)
                                for p in sorted(srcs["l1"].rglob("*.jsonl"))},
                   "k1_files": k1["files"]},
        "inputs_sha256": dict(sorted(srcs["sha"].items())), "inputs_checked": srcs["checked"],
        "lock": {"path": "experiments/LOCK.toml", "sha256": sha256_file(S463.LOCK_TOML)},
        "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": sha256_file(S457.FIGURE_LOCK),
                        "status": S457.FLOCK.get("status")},
        "files": files}, indent=1, default=str) + "\n")
    # move in: earlier S473 files of --out removed only now
    out.mkdir(parents=True, exist_ok=True)
    for pat in OWNED:
        for p in out.glob(pat):
            p.unlink()
    for p in stage.iterdir():
        shutil.move(str(p), out / p.name)
    stage.rmdir()
    print("\n".join(["reproduced:"] + [f"  {x}" for x in rep]))
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {plate}; {stamp}")


def selftest() -> int:
    """D155's input checks: they pass on the frozen copies and refuse each of five altered inputs (mutants)."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="S473_selftest_") as t:
        srcs = frozen_sources(Path(t))
        print(f"  PASS    the frozen copies: {srcs['checked'][0]}")
        sha = srcs["sha"]
        tsv = identical_files(FR.frozen(FIG5_SET, "s3/IDENTICAL_FILES.tsv"))
        k_pin = next(iter(FROZEN_SHA256))
        k_tsv = next(k for k in tsv if k in sha and k not in FROZEN_SHA256)
        mutants = {f"a pinned input changed ({k_pin})": ({**sha, k_pin: "0" * 64}, tsv),
                   f"an input IDENTICAL_FILES.tsv pins changed ({k_tsv})": ({**sha, k_tsv: "0" * 64}, tsv),
                   f"a pinned input not read ({k_pin})": ({k: v for k, v in sha.items() if k != k_pin}, tsv),
                   "an input read but pinned nowhere": ({**sha, "fig5_inputs/extra.jsonl": "0" * 64}, tsv)}
        killed = 0
        for name, (s_, t_) in mutants.items():
            try:
                check_frozen(s_, t_)
                print(f"  SURVIVED {name}")
            except Refused:
                killed += 1
                print(f"  killed  {name}")
        try:
            label_of(Path(t) / "elsewhere" / "answers.jsonl", srcs["labels"])
            print("  SURVIVED an input outside every frozen set named in the provenance")
        except Refused:
            killed += 1
            print("  killed  an input outside every frozen set named in the provenance")
    n = len(mutants) + 1
    # D160 (6), Q18: the threshold texts follow PASS_T and PASS_RELAXED as written, and a typed one is refused
    try:
        check_threshold_texts()
        print("  PASS    every threshold text follows PASS_T and PASS_RELAXED (rebuilt at 3 and 2)")
        ok_texts = True
    except Refused as e:
        print(f"  FAIL    the threshold texts as written: {e}")
        ok_texts = False
    g = globals()
    for name, fname, typed in (("the axis label typed as 'Pass rate 4+ (%)'", "pass_axis_label",
                                lambda: "Pass rate 4+ (%)"),
                               ("sheet b's relaxed column typed as 'judge_pass_relaxed_3'", "b_relaxed_col",
                                lambda: "judge_pass_relaxed_3")):
        n += 1
        real = g[fname]
        g[fname] = typed
        try:
            check_threshold_texts()
            print(f"  SURVIVED {name}")
        except Refused:
            killed += 1
            print(f"  killed  {name}")
        finally:
            g[fname] = real
    # D160 (6), Q18: check_fig2 passes on this script's plate of 26 October (git FIG5_S473_AT, since D166 replaced
    # the files of fig5/) and Figure 3 at FIG3_V24_AT (D201 Q2), and refuses a changed rate and another collect
    shown = subprocess.run(["git", "show", f"{FIG5_S473_AT}:{(OUT / 'figure5_numbers.json').relative_to(ROOT)}"],
                           cwd=ROOT, capture_output=True, text=True)
    if shown.returncode:
        print(f"  FAIL    git show {FIG5_S473_AT}: {shown.stderr.strip()[:200]}")
        return 1
    fig5 = json.loads(shown.stdout)["sheets"]
    sha = FR.sha256_file(FR.frozen(FIG2_SET, "g1_collect.jsonl"))
    try:
        check_fig2(fig5, sha)
        print(f"  PASS    check_fig2 on S473's plate of 26 October (git {FIG5_S473_AT}) and Figure 3 at git "
              f"{FIG3_V24_AT}")
        ok_fig2 = True
    except Refused as e:
        print(f"  FAIL    check_fig2 on S473's plate of 26 October (git {FIG5_S473_AT}) and Figure 3: {e}")
        ok_fig2 = False
    bent = json.loads(json.dumps(fig5))
    cols = bent["Fig. 5a"]["columns"]
    row = next(r for r in bent["Fig. 5a"]["rows"] if r[cols.index("row")] == "summary"
               and r[cols.index("signal")] == a_signal("pass"))
    row[cols.index("value")] += 0.01
    for name, args in ((f"a Figure 5 pass rate at {PASS_T} moved by 0.01", (bent, sha)),
                       ("Figure 3 written from another G1 collect", (fig5, "0" * 64)),
                       ("D201 Q2: the pin dropped, Figure 3's current file (key v2.5) read", (fig5, sha, FIG2_DIR, None)),
                       ("D201 Q2: a pin that does not resolve", (fig5, sha, FIG2_DIR, "0000000"))):
        n += 1
        try:
            check_fig2(*args)
            print(f"  SURVIVED {name}")
        except Refused:
            killed += 1
            print(f"  killed  {name}")
    print(f"selftest: frozen copies pass; mutants {killed} of {n} killed")
    return 0 if killed == n and ok_fig2 and ok_texts else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--to", required=True)
    f = sub.add_parser("figure")
    f.add_argument("--from", dest="src", help="a new pull's folder; without it the frozen inputs (D155)")
    f.add_argument("--out")
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "selftest":
            return selftest()
        {"pull": pull, "figure": lambda x: figure(x)}[a.cmd](a)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
