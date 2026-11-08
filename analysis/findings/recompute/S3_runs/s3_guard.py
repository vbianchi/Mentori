#!/usr/bin/env python3
"""S3 (plan row S3; D88, D92 Q189, D94): the server guard, the work list and the units of the judging, for G1
(Figure 2) and the other answer sets (D94 A1). Used by run_s3.sh and wait_s3.sh beside this file (README.md). No model
call: it reads ps, lsof (ss, netstat.exe), the server's GET /api/ps, the server log and the frozen inputs.

    uv run --frozen python findings/recompute/S3_runs/s3_guard.py survey --base <B> --ledger <own_<port>.json> [--job-pattern RE]
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py release --base <B> --ledger <file> --log <server log> --why TEXT
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py set --set <set>      (inputs, out, phases, store manifest[, S6 judge script[, G7 question scope]])
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py units --set <set> --inputs <dir> --out <dir> [--phases "1 2 3"]
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py plan --set <set> --inputs <dir> --out <dir> [--phases ...] [--unit U] [--judge main|second]
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py claim --out <dir> --unit U --worker W   (unclaim: the same)
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py same --old <inputs> --new <inputs> --keys <file> [--configs ...]
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py collect --out <dir> [<dir> ...] [--replace <dir>] --dest <file> [--set S]
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py snap --set <set> --src <runs folder> --dest <dir>
    uv run --frozen python findings/recompute/S3_runs/s3_guard.py link --set G5 --inputs <dir> [--make]

survey: experiments/runner/server_users.py survey with no model of S3's own and no K1 ledger, so any process naming
  the port, any open connection to it, anything unreadable and any loaded model is a user. One exception, the
  release: a loaded model is not a user when the ledger proves that the server has served no model request since a
  release (the server log's [GIN] lines after the release's offset, counted by server_users.model_requests) and every
  model loaded now was loaded at the release. A load is a request, so with no request since the release no model
  can have been loaded since, by anyone. The Q152 timing test (Q152_PATTERN: verifier_ports run, run_q152.sh,
  anywhere on the machine; D92 Q152, review of 18 October F1) is also a user, whatever port it uses: it needs a quiet
  Studio (all its ports share one GPU) and treats judge_passages as a job that must not run (verifier_ports.py
  JOB_PATTERN), so S3 must not start or move to its next strategy while it runs. Prints one JSON object, then FREE,
  WAIT or BUSY; exit 0 free, 3 when the Q152 test is the only user (run_s3.sh then waits for it to end instead of
  stopping), 1 busy.
release: written when the job that loaded the models now in /api/ps has ended. By wait_s3.sh when the deepseek-r1
  variant of S2 has ended (its models, deepseek-r1:70b and devstral-small-2:24b as read on 18 October at 00:40, are
  then an ended job's), and by run_s3.sh after each judge_passages process it ran has exited (devstral is then S3's
  own). It reads the log's size first, then surveys: it refuses (exit 1, nothing written) while a process names the
  port, the Q152 test runs, a connection is open or a listing cannot be read (so the waiter keeps waiting); otherwise it writes the ledger (base, log, offset, the
  models loaded, why, when). A request that ends after the size was read is counted by the next survey, which then
  finds the server busy: the guard fails closed.
set: the fields run_s3.sh reads. A whole-key set (S6W<set>, B17) prints "all" as its seventh field: run_s3.sh's scope is
  empty or "all", and S512 takes the set's cover from the out's name (S512 out_scope).
units (D94): the work of a set as units, in the order a worker takes them. A set (SETS) names its runs, its store,
  its default phases and whether it leaves out unanswered answers (a run still writing). PHASES gives each phase its
  judge_passages selection: 1 the plain call (a) on draw 1 (Figure 2's ranking needs only (a)), 2 the plain call on
  draws 2 and 3, 3 the calls with passages (b) on every draw, reusing each (a) already written (judge_passages.py
  PHASES). Unit p<phase>__<run> writes <out>/judge/<run>/; one TSV line per unit: unit, variants, draws, run, out
  folder, store, keys file, answered_only ("-" for none).
plan: the dry run of the judging, offline. For each unit, every answer read from the inputs as judge_passages run
  reads it (records.py, the store read-only), its selection (draws, keys, answered_only), both prompts built and
  verified as before any call (judge_passages.safe_prompts), and the rows already in the unit's judge_passages.jsonl
  compared as judge_passages run compares them (run_sha256 from the lock and the code; a row of the same answer under
  another item or run sha256 is a conflict, which run refuses), done counted for the unit's variants
  (judge_passages.is_done), the calls left ((a) calls, (b) calls, (a) reused) with their prompt characters (for an
  estimate of hours), and the unit's claim. Also whether <check>/repro_check.json passed and covers this lock and
  code (the server, machine and digest parts are checked by run's require_check). --judge second (D85): the rows and
  check of judge_passages --judge second, compared under its run_sha256 (default main, as before). An answer an earlier unit of the
  same plan judges is counted as that unit leaves it (review of 18 October F6): a phase-3 unit planned with phases 1
  and 2 counts their (a) as reused and their complete rows as done, so the calls add up across phases; the total
  counts each answer once. Prints one JSON line per unit and a total; exit 1 on a refusal or a conflict.
claim (requirement of D94: a second worker on disjoint rows): a unit is taken by mkdir <out>/claims/<unit> (atomic),
  its owner.json naming the worker (machine and port). Exit 0 when the unit is this worker's (new, or its own from an
  earlier start), 2 when another worker holds it. A worker never runs another's unit; two workers on one machine and
  out share the claims. On another machine (the laptop), whose out is its own, the units it is to take are claimed
  first in the Studio's out under its worker name (by hand, `claim --worker laptop_11434`), so the Studio's workers
  skip them. A claim means "in progress": run_s3.sh unclaims a unit when its run has ended done (review of 18
  October F5), so a later pass (another snapshot of G3 or G4, another port) takes it again and finds only what is
  new; a worker stopped in a unit keeps that claim for its restart (unclaim by hand when it will not restart).
same (D93 Q-c): whether two input copies hold the same answers except the keys listed, which must differ: G1's 15
  reruns of 18 October judged in their own pass, so the main pass (the copy before them) and the separate pass (the
  copy after) together judge every answer once in its latest version.
snap (snap_s3_inputs.sh calls it): a frozen copy of a set's runs from <runs folder> (the sinks) into <dest>/runs/,
  each run's answers file, index_identity.jsonl and run_identity.json; an answers.jsonl still being written is cut
  after its last whole line (an answer's line is written whole, so the cut leaves out at most the line in progress); an
  answers.json (exp_03, rewritten whole) must parse, else it is read again (3 tries, 5 s apart) or refused. Then
  MANIFEST.sha256 over the copy and COPY.json (when, from where, each run's answers). <dest> must not exist.
  A set with a subset (SETS "subset"; D175 Q3, D176: the local T2 generators' rlm_5, rlm_10 and rlm_20 on D98's 45
  questions at every draw): in those runs only the lines of the subset's questions are copied at the subset's draws
  (a line is an attempt; the last line of a key stays its answer, records.py), the others are left out and counted in
  COPY.json (subset.lines_left_out), and the subset's file is copied beside runs/, so the manifest covers it. units
  refuses such a set's copy when that file is missing or differs from the repo's, or when a subset run holds a line of
  another question at a subset draw (a copy taken without the filter).
  G5 (D104 A3; exp_06, whose answers are a results file, not a sink): <src> is the G5 clone; every results file of
  the run is read (a *_merged.json is skipped, as exp_06's resume and check_g5 skip it; a file the glob matches under
  another name exp_06 does not give a results file is refused), an answer key with two different rows is refused,
  the file holding the whole union is copied byte for byte to results/, or, when no one file holds it (D185 (2):
  G7's 4 shares), the union is written there as one results file, each answer key once; each file read is listed
  with its sha256 in results_sources.sha256 (under the manifest) and COPY.json, and each sink the rows name gives its
  index_identity.jsonl and run_identity.json. S6G5 and S6G7G5 carry G5's snap.
link (D104 A3, G5): records.py reads a results file's sinks under the clone's findings/runs, so each sink the copy's
  rows name must be a link there to the copy's sink (<inputs>/runs/<run_id>); units refuses the set until it is.
  --make makes the missing links and repoints a link to an older copy of the same base; a real folder or a link
  elsewhere is never touched (refused).
collect: one jsonl of a set's rows for the analysis: the latest row of each answer in each judge_passages.jsonl under
  the out folders given; an answer in two of them (two workers) must agree on item_sha256 and run_sha256, and (a) in
  both final with equal scores (D46: the laptop and the Studio give equal scores), else refused; a complete row
  (both variants final) is taken over a phase-1 or phase-2 row. --replace <out>: its rows replace the others' rows of
  the same answer (G1's 15 reruns), each replaced (and each added) answer counted. Every row written, the --replace
  rows included, must carry one run_sha256 (one lock, code, options and system prompt), else refused (review of 18
  October F1). A sidecar <dest>.json records the sources, the run_sha256 and the counts; with --set, also the set's
  phases and whether its (b) "deferred" will be judged (F7: G6's will not, its phases leave out 3).

What the guard cannot see (as server_users.py): a job between two calls whose model is not loaded and whose command
line does not name the port. A request by such a job after a release is counted, so it makes the server busy.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from experiments.runner import server_users as U  # noqa: E402

CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
# D175 Q3, D176: a local T2 generator's RLM set-ups run on D98's 45 questions (S464) at every draw; ids under ROOT
LOCAL_SUBSET = {"configs": ("rlm_5", "rlm_10", "rlm_20"), "draws": (1, 2, 3),
                "ids": "findings/recompute/D98_subset/d98_subset.json"}
# D94 A1: every answer set the judge scores. runs: paths under the inputs (a "*" is globbed, sorted); store: under the
# inputs, or "~/..." (None: the store each run recorded, read only); keys: a file under the inputs; answered_only: the
# set is a snapshot of a run still writing (judge_passages --answered-only). The inputs are frozen copies, each with its
# MANIFEST.sha256 (G1: K1's ~/k1_inputs; the others: snap_s3_inputs.sh).
SETS = {
    "G1": {"inputs": "~/k1_inputs", "runs": [f"runs/exp_01__{c}__exp_v4_s20_n0" for c in CONFIGS], "store": "store",
           "out": "out", "phases": "1 2 3"},
    # D93 Q-c: the 15 answers rerun on 18 October, from a copy taken after the rerun, in their own out
    "G1R15": {"inputs": "~/s3_inputs/g1r15", "runs": [f"runs/exp_01__{c}__exp_v4_s20_n0" for c in CONFIGS[2:]],
              "store": "~/k1_inputs/store", "keys": "keys.txt", "out": "out_g1r15", "phases": "1 2 3"},
    "G2": {"inputs": "~/s3_inputs/g2", "runs": ["runs/exp_01__matched_budget__exp_v4_s20_n0"],
           "store": "~/k1_inputs/store", "out": "out_g2", "phases": "1 2 3"},
    # the authors' RLM: its passages are the whole corpus (about 1.1 million characters, above num_ctx), so a (b) call
    # fails as too long (LOCK.toml [text]: nothing is cut); phase 3 is not in its default
    "G6": {"inputs": "~/s3_inputs/g6", "runs": [f"runs/b4_rlm_ref__cap{c}__all135" for c in (5, 10, 20)],
           "store": None, "out": "out_g6", "phases": "1 2"},
    "G3": {"inputs": "~/s3_inputs/g3", "runs": ["runs/exp_03__*"], "store": "~/k1_inputs/store", "out": "out_g3",
           "phases": "1 2 3", "answered_only": True},
    "G4": {"inputs": "~/s3_inputs/g4", "runs": ["runs/exp_02_scaling_factorial__*"], "store": None, "out": "out_g4",
           "phases": "1 2 3", "answered_only": True},
    # D104 A3: Figure 3's depth sweep (exp_06; draw 1 of 860 answers, stopped by D98; the subset's draws 2 and 3 from 1
    # November). Its answers are one results file (records.py exp_06: rows naming their run_id), copied whole; each
    # row's sink is read under the clone's findings/runs (records.read_run runs_root), so the copy's sinks are linked
    # there (link below; snap_s3_inputs.sh G5 makes the links). Its index is G1's (exp_v4_s20_n0, the same
    # id_text_sha256), so the frozen store. snap: where the copy is taken from, under the G5 clone (exp_06 writes the
    # whole list into each results file; the union of the files is the answer set, as check_g5.py reads it). names
    # (D185 (2)): every file the glob matches must have the name exp_06 gives a results file of a start
    # (exp_06_depth_sweep.py:610-614: <prefix>_<model>_<host>-<port>[_part<k>of<n>]_<YYYYmmdd_HHMMSS or latest>.json),
    # else snap refuses.
    "G5": {"inputs": "~/s3_inputs/g5", "runs": ["results/exp_06_depth_sweep__depthsweep86.json"],
           "store": "~/k1_inputs/store", "out": "out_g5", "phases": "1 2 3", "answered_only": False, "linked_sinks": True,
           "snap": {"results": "experiments/mentori/publication/scripts/results_v4/"
                               "v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview*.json",
                    "names": r"v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview_[A-Za-z0-9.-]+-\d+"
                             r"(?:_part\d+of\d+)?_(?:\d{8}_\d{6}|latest)\.json",
                    "sinks": "findings/runs"}},
    # D157 (2), Q13 O-a: T2, claude-haiku-4-5's arm of Figure 2 panel f (exp_01 --generator, T2_runs/README.md): G1's
    # six strategies, 135 questions, 3 draws and index, each run id with "+claude-haiku-4-5" (its answer keys are G1's
    # strings; rows are told apart by run_id, judge_passages.ident). G1's phases; G1's frozen store (T2's Studio stores
    # hold G1's whole index identity, T2_runs/README.md). Still generating: snapshots of the stored answers into one
    # out, answered only (an answer stored with an error waits for the last pass, S3_ANSWERED_ONLY=0); a later
    # snapshot's answers already judged are skipped (same item_sha256), as G3's and G4's.
    "T2": {"inputs": "~/s3_inputs/t2", "runs": [f"runs/exp_01__{c}__exp_v4_s20_n0+claude-haiku-4-5" for c in CONFIGS],
           "store": "~/k1_inputs/store", "out": "out_t2", "phases": "1 2 3", "answered_only": True},
    # W8 (Valerio, 28 Oct, "go for it"): T2's gemini-2.5-pro arm, as T2 (D157 (2)) with its own run-id suffix, inputs
    # and out, judged from its own clone at the commit that added it (main's judge code, as T2's). Its draws 2 and 3
    # cover the fixed third only (D98), so phase 2 judges what is stored; answered only until its generation ends.
    "T2G": {"inputs": "~/s3_inputs/t2g", "runs": [f"runs/exp_01__{c}__exp_v4_s20_n0+gemini-2.5-pro" for c in CONFIGS],
            "store": "~/k1_inputs/store", "out": "out_t2g", "phases": "1 2 3", "answered_only": True},
    # D177 (3), Q7: each local T2 generator is its own set with its own out, as T2G (an answer key holds no generator,
    # so in one out with Haiku's its rows would meet Haiku's keys). T2L<model>: T2's local lane (T2_runs/README.md
    # "local lane"), named by its generator, so neither name begins with T2G. T2's phases, store and answered only;
    # inputs a copy of the generator's runs in its Studio clone (snap_s3_inputs.sh). The subset (D175 Q3, D176): their
    # rlm_5, rlm_10 and rlm_20 on D98's 45 questions at every draw; answers those runs stored for other questions
    # before the rule are left out of the copy, so never judged (T2_runs check_t2.py subset_draws, the same rule).
    "T2LGEMMA": {"inputs": "~/s3_inputs/t2lgemma", "runs": [f"runs/exp_01__{c}__exp_v4_s20_n0+gemma3-27b" for c in CONFIGS],
                 "store": "~/k1_inputs/store", "out": "out_t2lgemma", "phases": "1 2 3", "answered_only": True,
                 "subset": LOCAL_SUBSET},
    "T2LQCODER": {"inputs": "~/s3_inputs/t2lqcoder",
                  "runs": [f"runs/exp_01__{c}__exp_v4_s20_n0+qwen3-coder-30b" for c in CONFIGS],
                  "store": "~/k1_inputs/store", "out": "out_t2lqcoder", "phases": "1 2 3", "answered_only": True,
                  "subset": LOCAL_SUBSET},
}
# S6 (D182; README "S6, key v2.5"): the answers to the 132 questions whose judge prompt key v2.5 changed, judged again
# on v2.5 by scripts/S512_s6_rejudge_v25.py (S3's judge with the key and the question list changed). Each S6 set is its
# v2.4 set's runs, store and phases, with its own out (out_s6_<set>, which S512 requires); "judge_script" names the
# script it needs: `set` prints it as a sixth field and run_s3.sh refuses another S3_JP, and plan reads its answers and
# run identity through it. G9's answers are in G3's runs (exp_03), G4R38's are judged as S6G4 with its own inputs
# and out, as G4R38 was judged as G4.
S6_JUDGE = "scripts/S512_s6_rejudge_v25.py"
for _p in ("G1", "G1R15", "T2", "T2G", "G2", "G4", "G5", "G6", "G3"):
    SETS["S6" + _p] = {**SETS[_p], "out": "out_s6_" + _p.lower(), "judge_script": S6_JUDGE, "s6_of": _p}
# D184 (1): G7's new answers (draws 2 and 3 of G3, G4 and G5, on D98's subset) judged once on key v2.5 complete. Each
# S6G7<set> is its v2.4 set's runs (S6G7G3: G7's eight set-ups, below), inputs, store, answered_only, linked_sinks
# and snap, with its own out (out_s6_g7_<set>, which S512 --questions all requires and its default refuses), phases
# 2 and 3, and two fields:
# "questions" ("all": `set` prints it as a seventh field, run_s3.sh passes it as S512 --questions, plan reads the
# answers and run identity with it) and "draws" (units keeps only these draws in every phase, so phase 1 is refused
# and phase 3 selects draws 2 and 3, not every draw).
for _p in ("G3", "G4", "G5"):
    SETS["S6G7" + _p] = {**SETS[_p], "out": "out_s6_g7_" + _p.lower(), "phases": "2 3", "judge_script": S6_JUDGE,
                         "s6_of": _p, "questions": "all", "draws": [2, 3]}
# S6G7G3's runs are G7's eight exp_03 set-ups only (D173 G7-Q2: the six wave-1 ablations and the two stress set-ups,
# preflight.sh WAVE1 without the baselines, and STRESS_SETUPS), not G3's runs/exp_03__*: raw_gemini and naive_rag
# stored all three draws on all 135 questions on 19 October (G3_runs/README.md), so their draws 2 and 3 are not G7's.
G7_G3_SETUPS = ("full_orchestrator", "orch_no_analyser", "orch_no_planner", "orch_no_supervisor", "orch_no_synthesiser",
                "orch_factual_to_documents", "orch_distil_every_step", "orch_distil_every_step_f1")
SETS["S6G7G3"]["runs"] = [f"runs/exp_03__{c}__exp_v4_s20_n0" for c in G7_G3_SETUPS]
# B17 (plan rows S8, S10; run plan newRuns.md F1, Runs 1, 2, 3, 5, 6, 7): answers with no devstral row on key v2.4, judged
# once on key v2.5 by S512's whole-key scope, plain call only. Each S6W<set> names its own out (out_s6_w_<set>, which
# gives S512 the set's cover, S512 WHOLE; the two tables' runs are held equal by S512's test), phases 1 and 2 at most
# ("plain_only": units refuses phase 3), and "questions": "whole:<set>" with its "draws" (as D184's: units keeps only
# these draws). No S6W set is an S6<set> or S6G7<set>, so S482's maps and judge_rows_v25 are not touched by them.
#   S6WG10, S6WG11 (D196): the runs in ~/projects/mentori-runs-g10 on the Studio, copied by `snap --set` into
#     ~/s3_inputs/g10, g11. G10's stores are each arm's own clone of G4's (recorded in its identity, None here, as G4);
#     G11's index is G1's, so G1's frozen store. S6WG10's exp_01__matched_budget__exp_v4_s20_n0 has G2's run id and answer
#     keys, on other answers, so its rows must never be read beside out_g2's by run id alone.
#   S6WT2LGEMMA, S6WT2LQCODER (Run 6): T2LGEMMA's and T2LQCODER's runs, inputs (snap_s3_inputs.sh, the same copies),
#     store, answered_only and subset. They never had a v2.4 row, so every answer is judged here.
#   S6WG12 (D200), S6WG13 (PA3): reruns, read from a copy holding the rerun lines only (s6/s6w_inputs.py rerun), judged
#     as G4 and G2 are read: G4's recorded stores, G1's frozen store. Their answers replace failed or stale ones; how a
#     reader takes them is the reader's (they carry their own run_sha256).
#   S6WS12B (D200, held, newRuns.md Run 7): the 194 April answers in an exp_01-like sink (s6/s6w_inputs.py april).
#   S6WT2G (D202, D198 O4): T2G's inputs, runs and store, for the second judge only ("judge": plan refuses another, and so
#     does S512), from the Beelink's own clone; its out is out_s6_w_t2g_second (run_s3.sh S3_JUDGE=second). Generation has
#     ended, so an answer with no text gets its no_answer row (no call). s6/start_s6w_second_beelink.sh runs its first
#     three runs, 3f's; the other three are inside D198 O4's held 2,025.
_W = {"judge_script": S6_JUDGE, "phases": "1 2", "draws": [1, 2, 3], "plain_only": True}
SETS["S6WG10"] = {**_W, "inputs": "~/s3_inputs/g10", "store": None, "out": "out_s6_w_g10", "questions": "whole:g10",
                  "runs": [f"runs/exp_01__matched_budget__exp_v4_{i}" for i in ("s20_n3", "s50_n3", "s20_n0")]}
SETS["S6WG11"] = {**_W, "inputs": "~/s3_inputs/g11", "store": "~/k1_inputs/store", "out": "out_s6_w_g11",
                  "questions": "whole:g11", "runs": ["runs/exp_01__single_pass_cut800__exp_v4_s20_n0"]}
SETS["S6WT2LGEMMA"] = {**SETS["T2LGEMMA"], **_W, "out": "out_s6_w_t2lgemma", "questions": "whole:t2lgemma"}
SETS["S6WT2LQCODER"] = {**SETS["T2LQCODER"], **_W, "out": "out_s6_w_t2lqcoder", "questions": "whole:t2lqcoder"}
SETS["S6WG12"] = {**_W, "inputs": "~/s3_inputs/g12", "runs": SETS["G4"]["runs"], "store": None, "out": "out_s6_w_g12",
                  "phases": "2", "draws": [2], "questions": "whole:g12"}
SETS["S6WG13"] = {**_W, "inputs": "~/s3_inputs/g13", "runs": SETS["G2"]["runs"], "store": SETS["G2"]["store"],
                  "out": "out_s6_w_g13", "questions": "whole:g13"}
SETS["S6WS12B"] = {**_W, "inputs": "~/s3_inputs/s12b", "runs": ["runs/s12b_april"], "store": None, "out": "out_s6_w_s12b",
                   "phases": "1", "draws": [1], "questions": "whole:s12b"}
SETS["S6WT2G"] = {**SETS["T2G"], **_W, "out": "out_s6_w_t2g", "questions": "whole:t2g", "answered_only": False,
                   "judge": "second"}
for _k, _v in SETS.items():                             # a question scope or a draw list is S512's (D184), never alone
    assert ("questions" in _v) == ("draws" in _v) and (
        "questions" not in _v or _v["judge_script"] == S6_JUDGE and (_v["questions"] == "all"
                                                                     or _v["questions"].startswith("whole:"))), _k
PHASES = {"1": ("a", [1]), "2": ("a", [2, 3]), "3": ("ab", None)}   # D94: variants and draws of each phase
# The Q152 timing test (D83, D92 Q152): run_q152.sh and the verifier_ports run it starts (uv and python). Its select
# and analyse steps send no call and are not matched; nor is a command that only reads its files (tail of its log).
Q152_PATTERN = r"(?:experiments\.runner\.verifier_ports|verifier_ports\.py)\s+run\b|run_q152\.sh"


def run_dir(inputs: Path, config: str) -> Path:
    return inputs / "runs" / f"exp_01__{config}__exp_v4_s20_n0"


def names(models: list[dict]) -> list[str]:
    return sorted(m.get("name") or m.get("model") for m in models)


def released(ledger: Path | None, base: str, loaded_now: list[str]) -> dict:
    """Whether the ledger proves that every model loaded now was loaded at a release with no request since."""
    if ledger is None or not ledger.exists():
        return {"proved": False, "why": "no release recorded for this server"}
    try:
        led = json.loads(ledger.read_text())
        if U.norm(led.get("base")) != U.norm(base):
            return {"proved": False, "why": f"the ledger {ledger} is for {led.get('base')}, not {base}"}
        n = U.model_requests(Path(led["log"]), int(led["log_offset"]))
    except (OSError, ValueError, KeyError, TypeError) as e:
        return {"proved": False, "why": f"the ledger cannot be read: {type(e).__name__}: {e}"}
    extra = sorted(set(loaded_now) - set(led.get("loaded_at_release") or []))
    out = {"since": led.get("at"), "release_why": led.get("why"), "model_requests_since": n, "not_loaded_at_release": extra,
           "proved": n == 0 and not extra}
    if not out["proved"]:
        out["why"] = (f"{n} model request(s) in the server log since the release of {led.get('at')}" if n else
                      f"loaded now but not at the release of {led.get('at')}: {extra}")
    return out


def with_q152(pattern: str | None) -> str:
    return Q152_PATTERN + (f"|{pattern}" if pattern else "")


def mark_q152(out: dict) -> list[dict]:
    """The survey's processes that are the Q152 test, relabelled so the summary names it."""
    q = [u for u in out["processes"] if re.search(Q152_PATTERN, u["args"])]
    for u in q:
        u["why"] = "is the Q152 timing test"
    out["q152"] = [u["pid"] for u in q]
    return q


def survey(base: str, ledger: Path | None, pattern: str | None, **canned) -> dict:
    """canned: server_users.survey's runner, get, me and platform, set only by check_s3_guard.py."""
    base = U.norm(base)
    out = U.survey(base, [], None, with_q152(pattern), Path(U.NETSTAT).exists(), **canned)
    q152 = mark_q152(out)
    loaded_now = [u["model"] for u in out["loaded"]]
    out["release"] = released(ledger, base, loaded_now) if loaded_now else None
    others = bool(len(out["processes"]) > len(q152) or out["connections"] or out["unreadable"])
    busy_but_q152 = others or bool(loaded_now and not out["release"]["proved"])
    out["busy"] = busy_but_q152 or bool(q152)
    out["wait_q152"] = bool(q152) and not busy_but_q152
    return out


def summary(out: dict) -> str:
    bits = [f"pid {u['pid']} {u['why']}: {u['args'][:80]}" for u in out["processes"]]
    bits += [f"{len(out['connections'])} open connection(s) to port {out['port']}"] if out["connections"] else []
    bits += [f"cannot read {x}" for x in out["unreadable"]]
    if out["loaded"]:
        loaded = ", ".join(u["model"] for u in out["loaded"])
        rel = out.get("release")
        bits += [f"loaded {loaded}" + ("" if rel is None else ": released, no request since" if rel["proved"]
                                       else f": {rel['why']}")]
    return "; ".join(bits) if bits else "free, nothing loaded"


def release(base: str, ledger: Path, log: Path, why: str, pattern: str | None = None, **canned) -> dict:
    base = U.norm(base)
    offset = log.stat().st_size                        # first: a request ending after this is counted later
    out = U.survey(base, [], None, with_q152(pattern), Path(U.NETSTAT).exists(), **canned)
    mark_q152(out)
    if out["processes"] or out["connections"] or out["unreadable"]:
        out["busy"] = True
        out["release"] = None
        return {"released": False, "survey": out, "why": summary(out)}
    rec = {"state": "released", "base": base, "port": out["port"], "log": str(log.resolve()), "log_offset": offset,
           "loaded_at_release": [u["model"] for u in out["loaded"]], "why": why,
           "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    ledger.parent.mkdir(parents=True, exist_ok=True)
    U.write_json(ledger, rec)
    return {"released": True, "ledger": rec}


def home(p: str) -> Path:
    return Path(p).expanduser()


def store_manifest(st: dict) -> tuple[str, str]:
    """A store outside the set's inputs ("~/k1_inputs/store", shared with G1) is covered by the MANIFEST.sha256 of the
    folder that holds it: (that folder, the store's prefix in it), which run_s3.sh checks (review of 18 October F9).
    ("-", "-"): the store is under the inputs (their own manifest covers it) or is each run's recorded one (G4, G6:
    not frozen, read only)."""
    if st["store"] is None or not st["store"].startswith("~"):
        return "-", "-"
    s = home(st["store"])
    return str(s.parent), s.name + "/"


def units(set_name: str, inputs: Path, out_root: Path, phases: str, answered_only: bool | None = None) -> list[dict]:
    """The set's units in the order a worker takes them: phase by phase, each run in the set's order."""
    if set_name not in SETS:
        raise SystemExit(f"REFUSED: no set {set_name!r} (SETS: {', '.join(SETS)})")
    st = SETS[set_name]
    runs = []
    for r in st["runs"]:
        hits = sorted(inputs.glob(r)) if "*" in r else [inputs / r]
        if not hits:
            raise SystemExit(f"REFUSED: {set_name}: no run matches {inputs / r}")
        runs += hits
    store = None if st["store"] is None else home(st["store"]) if st["store"].startswith("~") else inputs / st["store"]
    keys = inputs / st["keys"] if st.get("keys") else None
    ao = st.get("answered_only", False) if answered_only is None else answered_only
    if st.get("linked_sinks"):                           # G5: every row's sink must be the copy's (link)
        bad = link(set_name, inputs)
        if bad:
            raise SystemExit(f"REFUSED: {set_name}: {bad[0]}" + (f" (and {len(bad) - 1} more)" if len(bad) > 1 else "")
                             + "; snap_s3_inputs.sh " + set_name + " makes the links (s3_guard.py link --make)")
    bad = subset_problems(set_name, inputs)              # D175 Q3, D176: a copy taken with the set's subset filter
    if bad:
        raise SystemExit(f"REFUSED: {set_name}: {bad[0]}" + (f" (and {len(bad) - 1} more)" if len(bad) > 1 else "")
                         + "; take a new copy with snap_s3_inputs.sh " + set_name)
    if "plain_only" in st and not out_root.name.startswith(st["out"]):   # B17: the out's name gives S512 the set's cover
        raise SystemExit(f"REFUSED: {set_name}'s out is {st['out']} (or its _second), not {out_root.name}")
    out = []
    for p in phases.split():
        if p not in PHASES:
            raise SystemExit(f"REFUSED: no phase {p!r} (1, 2, 3)")
        variants, draws = PHASES[p]
        if st.get("plain_only") and variants != "a":     # B17
            raise SystemExit(f"REFUSED: {set_name} makes the plain call only (B17); phase {p} is the calls with passages")
        if "draws" in st:                                # D184: the set's draws only, in every phase
            draws = [d for d in (draws or st["draws"]) if d in st["draws"]]
            if not draws:
                raise SystemExit(f"REFUSED: {set_name} judges draws {','.join(map(str, st['draws']))} only (D184); "
                                 f"phase {p} selects none of them")
        for r in runs:
            name = run_name(r)
            out.append({"unit": f"p{p}__{name}", "phase": p, "variants": variants, "draws": draws, "run": r,
                        "out": out_root / "judge" / name, "store": store, "keys": keys, "answered_only": ao})
    return out


def subset_of(set_name: str, run: str) -> tuple[set, set] | None:
    """(question ids, draws) a run of the set is held to (SETS "subset"; its config is the run name's second part),
    or None when the run has no subset."""
    sub = SETS[set_name].get("subset")
    if not sub or run.split("__")[1] not in sub["configs"]:
        return None
    return set(json.loads((ROOT / sub["ids"]).read_text(encoding="utf-8"))["ids"]), set(sub["draws"])


def subset_lines(raw: bytes, ids: set, draws: set, where: Path) -> tuple[bytes, int]:
    """The lines of an answers.jsonl kept under a subset: a line at a subset draw only when its question is one of the
    ids; a line at another draw always. Returns the kept bytes and the number of lines left out."""
    keep, out = [], 0
    for n, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            q, d = rec["question_id"], rec["draw"]
        except (ValueError, KeyError, TypeError) as e:
            raise SystemExit(f"REFUSED: {where}:{n} has no question_id and draw ({type(e).__name__}); the subset "
                             "filter reads each line") from None
        if d in draws and q not in ids:
            out += 1
            continue
        keep.append(line)
    return b"".join(keep), out


def subset_problems(set_name: str, inputs: Path) -> list[str]:
    """A copy of a set with a subset must hold the subset's file as the repo has it and, in each subset run, no line
    of another question at a subset draw (a copy taken without the filter)."""
    sub = SETS[set_name].get("subset")
    if not sub:
        return []
    want = json.loads((ROOT / sub["ids"]).read_text(encoding="utf-8"))["ids"]
    f = inputs / Path(sub["ids"]).name
    try:
        have = json.loads(f.read_text(encoding="utf-8"))["ids"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        return [f"no subset file {f} ({type(e).__name__}): the copy was not taken with {set_name}'s filter"]
    if have != want:
        return [f"{f} differs from the repo's {sub['ids']}: the copy was taken under another subset"]
    bad = []
    for r in SETS[set_name]["runs"]:
        held = subset_of(set_name, r.rsplit("/", 1)[-1])
        a = inputs / r / "answers.jsonl"
        if held is None or not a.exists():
            continue
        _, out = subset_lines(a.read_bytes(), *held, a)
        if out:
            bad.append(f"{a} holds {out} lines of questions outside the subset at its draws {sorted(held[1])}: a copy "
                       "taken without the filter")
    return bad


def run_name(r: Path) -> str:
    """A run's name in its unit and out folder: a sink's folder name, or a results file's name without .json (G5)."""
    return r.name[:-len(".json")] if r.name.endswith(".json") else r.name


def runs_root() -> Path:
    """Where records.read_run looks for a results file's sinks (its runs_root default: the clone's findings/runs)."""
    from experiments.scorers import records as R
    return Path(R.read_run.__kwdefaults__["runs_root"])


def sink_ids(results: Path) -> list[str]:
    rows = json.loads(results.read_text(encoding="utf-8")).get("results") or []
    return sorted({r.get("run_id") for r in rows if r.get("run_id")})


def link(set_name: str, inputs: Path, make: bool = False, root: Path | None = None) -> list[str]:
    """D104 A3 (G5): each sink a results file's rows name must be, under the runs root records.read_run reads, a link
    to that sink in the copy (<inputs>/runs/<run_id>, the identity files snap copied), so the judge reads the copy's
    index identity. make: missing links are made, and a link to the same sink in an older copy of the same base is
    pointed at this one; a real folder there (another job's sink) or a link elsewhere is never touched. Returns the
    problems (none: every link in place)."""
    st = SETS[set_name]
    root = runs_root() if root is None else root
    inputs = inputs.resolve()
    bad = []
    for r in st["runs"]:
        f = inputs / r
        try:
            ids = sink_ids(f)
        except (OSError, ValueError) as e:
            bad.append(f"cannot read {f}: {type(e).__name__}: {e}")
            continue
        if not ids:
            bad.append(f"{f} names no run_id")
        for rid in ids:
            want, dst = inputs / "runs" / rid, root / rid
            if not (want / "index_identity.jsonl").is_file():
                bad.append(f"the copy has no sink identity {want / 'index_identity.jsonl'}")
                continue
            if dst.is_symlink() and dst.resolve() == want:
                continue
            if dst.is_symlink():
                old = Path(os.readlink(dst))
                ours = old.name == rid and old.parent.name == "runs" and old.parent.parent.parent == inputs.parent
                if make and ours:
                    dst.unlink()
                    dst.symlink_to(want)
                    print(f"LINKED: {dst} -> {want} (was {old})")
                    continue
                bad.append(f"{dst} links to {old}, not to {want}")
            elif dst.exists():
                bad.append(f"{dst} is a real folder (another job's sink?), not a link to {want}; S3 does not touch it")
            elif make:
                root.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(want)
                print(f"LINKED: {dst} -> {want}")
            else:
                bad.append(f"no link {dst} -> {want}")
    return bad


def owner(out_root: Path, unit: str) -> dict | None:
    f = out_root / "claims" / unit / "owner.json"
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return {"worker": "?", "why": f"{f} unreadable"} if f.parent.exists() else None


def claim(out_root: Path, unit: str, worker: str) -> int:
    d = out_root / "claims" / unit
    d.parent.mkdir(parents=True, exist_ok=True)
    try:
        d.mkdir()
    except FileExistsError:
        o = owner(out_root, unit)
        if o and o.get("worker") == worker:
            print(f"MINE: {unit} (claimed {o.get('at')})")
            return 0
        print(f"TAKEN: {unit} by {(o or {}).get('worker')} ({(o or {}).get('at')})")
        return 2
    U.write_json(d / "owner.json", {"worker": worker, "unit": unit, "host": socket.gethostname(),
                                    "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    print(f"CLAIMED: {unit} for {worker}")
    return 0


def unclaim(out_root: Path, unit: str, worker: str) -> int:
    o = owner(out_root, unit)
    if o is None:
        print(f"NOT CLAIMED: {unit}")
        return 1
    if o.get("worker") != worker:
        print(f"REFUSED: {unit} is {o.get('worker')}'s, not {worker}'s")
        return 1
    (out_root / "claims" / unit / "owner.json").unlink(missing_ok=True)
    (out_root / "claims" / unit).rmdir()
    print(f"UNCLAIMED: {unit} ({worker})")
    return 0


def judge_module(set_name: str):
    """The module whose run_answers, select, run_identity and code_identity a set's work list is read with: S512 for
    an S6 set (SETS "judge_script"), judge_passages for every other set (as before)."""
    if (SETS.get(set_name) or {}).get("judge_script") == S6_JUDGE:
        import S512_s6_rejudge_v25 as S6
        return S6
    from experiments.scorers import judge_passages as JP
    return JP


def plan(set_name: str, inputs: Path, out_root: Path, phases: str, check_dir: Path, only: str | None = None,
         answered_only: bool | None = None, judge: str = "main") -> int:
    """judge (D85, D112 Q5): judge_passages --judge, "main" ([judge] model) or "second" ([judge] second_model); the
    rows are compared under that judge's run_sha256, as its run compares them (a second judge's rows are otherwise
    another run's: a conflict)."""
    if (SETS.get(set_name) or {}).get("judge", judge) != judge:   # D202: a set named for one judge
        raise SystemExit(f"REFUSED: {set_name} is judged by the {SETS[set_name]['judge']} judge only, not the {judge}")
    from experiments.runner.lock import load
    from experiments.scorers import judge_passages as JP
    M = judge_module(set_name)                           # S6 sets: S512 (key v2.5, the 132); every other set: JP
    lock = load()
    call = lock.ollama(JP.judge_of(lock, judge), role="judge")
    kw = {"questions": SETS[set_name]["questions"]} if (SETS.get(set_name) or {}).get("questions") else {}   # D184
    run_sha = M.run_identity(lock, call, **kw)
    code = M.code_identity()
    chk_f = check_dir / "repro_check.json"
    chk = json.loads(chk_f.read_text()) if chk_f.exists() else None
    check = {"file": str(chk_f), "exists": chk is not None}
    if chk is not None:
        check.update(passed=chk.get("passed"), n=chk.get("n"), equal_scores=chk.get("equal_scores"),
                     same_lock=chk.get("lock_sha256") == lock.sha256, same_code=chk.get("code") == code,
                     server=chk.get("server"), at=(chk.get("_provenance") or {}).get("at"))
        if judge != "main":                            # the main judge's plan line as before
            check["same_judge"] = chk.get("model") == call.model
    us = units(set_name, inputs, out_root, phases, answered_only)
    if only:
        us = [u for u in us if u["unit"] == only]
        if not us:
            raise SystemExit(f"REFUSED: no unit {only!r} in {set_name} phases {phases}")
    print(json.dumps({"set": set_name, "inputs": str(inputs), "lock_sha256": lock.sha256, "judge": call.model,
                      "run_sha256": run_sha, "check": check}))
    tot = {"answers": 0, "done": 0, "to_do": 0, "a_calls": 0, "b_calls": 0, "a_reused": 0, "a_prompt_chars": 0,
           "b_prompt_chars": 0, "no_answer": 0, "conflicts": 0}
    bad, read, by_phase = [], {}, {}
    # review of 18 October F6: an answer an earlier unit of this plan judges is counted as that unit leaves it: its
    # row then complete (no (b) call to make: done for phase 3), or (a) written with (b) deferred (reused in phase 3)
    earlier: dict = {}                                   # (run, ident) -> "done" or "reuse", by the units counted so far
    seen, left = set(), set()                            # every answer of the plan, and those with a call left
    for u in us:
        k = (str(u["run"]), str(u["store"]))
        try:
            if k not in read:
                read[k] = M.run_answers(u["run"], None, u["store"])
            keys = [x for x in u["keys"].read_text().splitlines() if x.strip()] if u["keys"] else None
            items = M.select(read[k], u["draws"], keys, u["answered_only"], **kw)
            prompts = {JP.ident(x): JP.safe_prompts(x) for x in items if JP.answered(x)}
            latest = JP.latest_rows(u["out"] / "judge_passages.jsonl", {JP.ident(x): x["item_sha256"] for x in items},
                                    run_sha, u["out"])
        except SystemExit as e:                         # run_answers, select and latest_rows refuse with SystemExit
            print(json.dumps({"unit": u["unit"], "refused": str(e)}))
            bad.append(f"{u['unit']}: {e}")
            continue
        row = {"unit": u["unit"], "variants": u["variants"], "draws": u["draws"], "answers": len(items), "done": 0,
               "to_do": 0, "a_calls": 0, "b_calls": 0, "a_reused": 0, "a_prompt_chars": 0, "b_prompt_chars": 0,
               "no_answer": sum(1 for x in items if not JP.answered(x)), "conflicts": 0,
               "claim": (owner(out_root, u["unit"]) or {}).get("worker")}
        for x in items:
            prev, key = latest.get(JP.ident(x)), (str(u["run"]), JP.ident(x))
            seen.add(key)
            if prev is not None and JP.is_done(prev, u["variants"]) or earlier.get(key) == "done" or (
                    u["variants"] == "a" and key in earlier):
                row["done"] += 1
                continue
            row["to_do"] += 1
            left.add(key)
            if not JP.answered(x):
                earlier[key] = "done"                    # a no_answer row, complete in any phase
                continue
            pa, pb, _, _ = prompts[JP.ident(x)]
            if u["variants"] == "ab" and (JP.reusable_a(prev) or earlier.get(key) == "reuse"):
                row["a_reused"] += 1
            else:
                row["a_calls"] += 1
                row["a_prompt_chars"] += len(pa)
            if u["variants"] == "ab" and pb is not None:  # (a) differing from a stored score withholds (b): not known yet
                row["b_calls"] += 1
                row["b_prompt_chars"] += len(pb)
            earlier[key] = "reuse" if u["variants"] == "a" and pb is not None else "done"
        print(json.dumps(row))
        ph = by_phase.setdefault(u["phase"], dict.fromkeys(tot, 0))
        for t in tot:
            tot[t] += row[t]
            ph[t] += row[t]
    # the total counts each answer once (a phase-3 unit holds the answers of phases 1 and 2 again); calls are summed
    tot.update(answers=len(seen), to_do=len(left), done=len(seen) - len(left))
    print(json.dumps({"total": tot, "by_phase": by_phase}))
    if bad:
        print("S3 PLAN REFUSED: " + "; ".join(bad))
        return 1
    # a phase-3 unit counted after this plan's phases 1 and 2 counts what they will leave (earlier, above)
    print(f"S3 PLAN: {set_name}, {len(us)} units; "
          + "; ".join(f"phase {p} {v['to_do']} of {v['answers']} answers to judge, {v['a_calls']} (a) calls, "
                      f"{v['b_calls']} (b) calls, {v['a_reused']} (a) reused" for p, v in by_phase.items())
          + f"; in all {tot['to_do']} of {tot['answers']} answers to judge, {tot['a_calls']} (a) and {tot['b_calls']} (b) calls"
          + "; check " + ("passed" if chk and chk.get("passed") else "not passed" if chk else "not run yet"))
    return 0


def same(old: Path, new: Path, keys_f: Path, runs: list[str], store: Path | None) -> int:
    """D93 Q-c: every answer of the runs equal in the two copies (answer, status, error, passages) except the keys
    listed, each of which must be in both and differ."""
    from experiments.scorers import records as R
    keys = {k for k in keys_f.read_text().splitlines() if k.strip()}
    seen, bad, n = set(), [], 0
    for r in runs:
        a = {x["answer_key"]: x for x in R.read_run(old / r, store=store, resolve=False)}
        b = {x["answer_key"]: x for x in R.read_run(new / r, store=store, resolve=False)}
        if set(a) != set(b):
            bad.append(f"{r}: answer keys differ ({len(set(a) ^ set(b))})")
            continue
        for k in a:
            fa, fb = ([x[f] for f in ("answer", "status", "error", "passages_kind")] + [
                [p["id"] for p in x["passages"] or []]] for x in (a[k], b[k]))
            n += 1
            if k in keys:
                seen.add(k)
                if fa == fb:
                    bad.append(f"{r}: {k} is listed as rerun but equal in both copies")
            elif fa != fb:
                bad.append(f"{r}: {k} differs and is not listed")
    if keys - seen:
        bad.append(f"listed keys in no run: {sorted(keys - seen)[:3]}")
    print(json.dumps({"answers": n, "listed": len(keys), "listed_found": len(seen), "problems": bad[:20]}))
    print(("SAME: " if not bad else "NOT SAME: ") + f"{n} answers, {len(seen)} of {len(keys)} listed keys differ"
          + ("" if not bad else f"; {len(bad)} problems, first: {bad[0]}") + " (D93 Q-c)")
    return 0 if not bad else 1


def collect(outs: list[Path], replace: Path | None, dest: Path, set_name: str | None = None) -> int:
    from experiments.scorers import judge_passages as JP

    def rows_of(o: Path) -> dict:
        got = {}
        for f in sorted(o.glob("judge/*/judge_passages.jsonl")):
            for d in JP.read_rows(f):
                got[JP.ident(d)] = (d, str(f))                    # the latest row of an answer in a file
        return got

    merged, src, bad = {}, {}, []
    for o in outs:
        for k, (d, f) in rows_of(o).items():
            if k not in merged:
                merged[k], src[k] = d, f
                continue
            m = merged[k]
            if (m.get("item_sha256"), m.get("run_sha256")) != (d.get("item_sha256"), d.get("run_sha256")):
                bad.append(f"{k}: two definitions ({src[k]}, {f})")
            elif m["a"]["status"] in JP.FINAL and d["a"]["status"] in JP.FINAL and m["a"].get("scores") != d["a"].get("scores"):
                bad.append(f"{k}: (a) scores differ ({src[k]}, {f})")
            elif JP.is_done(d, "ab") and not JP.is_done(m, "ab"):
                merged[k], src[k] = d, f
    replaced = added = 0
    if replace is not None:
        for k, (d, f) in rows_of(replace).items():
            replaced, added = replaced + (k in merged), added + (k not in merged)
            merged[k], src[k] = d, f
    from collections import Counter
    # one file, one definition (judge_passages.py's own rule; review of 18 October F1): every row, the --replace rows
    # included, under one run_sha256 (lock, code, options, system prompt); two answers differ in item_sha256 by design
    runs = Counter(d.get("run_sha256") for d in merged.values())
    if len(runs) > 1:
        by = {}
        for k, d in merged.items():
            by.setdefault(d.get("run_sha256"), set()).add(src[k])
        bad.append("the rows carry " + str(len(runs)) + " run_sha256 values (another lock or code; keep each clone at "
                   "one commit for the whole set): " + "; ".join(f"{str(r)[:12]} {n} rows from {sorted(by[r])[:2]}"
                                                            for r, n in runs.most_common()))
    if bad:
        print(json.dumps({"problems": bad[:20]}))
        print(f"COLLECT REFUSED: {len(bad)} problems, first: {bad[0]}")
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w") as fh:
        for k in sorted(merged, key=lambda t: tuple(map(str, t))):
            fh.write(json.dumps(merged[k], ensure_ascii=False) + "\n")
    side = {"_provenance": {"script": "findings/recompute/S3_runs/s3_guard.py collect", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "inputs": [str(o) for o in outs] + ([str(replace)] if replace else [])},
            "rows": len(merged), "run_sha256": next(iter(runs), None), "replaced": replaced,
            "added_by_replace": added, "from": dict(Counter(src.values())),
            "status_a": dict(Counter(d["a"]["status"] for d in merged.values())),
            "status_b": dict(Counter(d["b"]["status"] for d in merged.values()))}
    if set_name is not None:
        # review of 18 October F7: whether a (b) "deferred" will be judged is the set's plan, not the row's; G6's
        # phases leave out 3 (its passages are longer than the context), so its deferred (b) is not asked by decision
        ph = SETS[set_name]["phases"].split()
        side.update(set=set_name, set_phases=ph, b_deferred_will_be_judged="3" in ph,
                    b_deferred_means="not judged yet: the set's phase 3 makes the call" if "3" in ph else
                    "not asked: phase 3 is not in the set's phases (D94; whether it runs is Valerio's call)")
    U.write_json(dest.with_name(dest.name + ".json"), side)
    print(f"COLLECTED: {len(merged)} answers into {dest} ({replaced} replaced, {added} added from {replace}); "
          f"run_sha256 {str(side['run_sha256'])[:12]}; (b) {side['status_b']}")
    return 0


def snap(set_name: str, src: Path, dest: Path) -> int:
    import hashlib
    import shutil
    if set_name not in SETS:
        raise SystemExit(f"REFUSED: no set {set_name!r}")
    if dest.exists():
        raise SystemExit(f"REFUSED: {dest} exists (a copy is taken once; take another into a new folder)")
    part = dest.with_name(dest.name + ".partial")
    shutil.rmtree(part, ignore_errors=True)
    if "snap" in SETS[set_name]:
        counts, extra = snap_results(set_name, src, part)
        return finish_snap(set_name, src, dest, part, counts, extra)
    names = []
    for r in SETS[set_name]["runs"]:
        pat = r.split("/", 1)[1]
        hits = sorted(src.glob(pat)) if "*" in pat else [src / pat]
        if not hits or not all(h.is_dir() for h in hits):
            raise SystemExit(f"REFUSED: no run {src / pat}")
        names += [h.name for h in hits]
    counts, left_out = {}, {}
    sub = SETS[set_name].get("subset")
    for n in names:
        s_dir, d_dir = src / n, part / "runs" / n
        d_dir.mkdir(parents=True)
        for f in ("index_identity.jsonl", "run_identity.json"):
            if (s_dir / f).exists():
                shutil.copy2(s_dir / f, d_dir / f)
        held = subset_of(set_name, n)
        if (s_dir / "answers.jsonl").exists():
            raw = (s_dir / "answers.jsonl").read_bytes()
            raw = raw[:raw.rfind(b"\n") + 1]                 # the line still being written, if any, is left out
            if held is not None:                             # D175 Q3, D176: only the subset's questions at its draws
                raw, left_out[n] = subset_lines(raw, *held, s_dir / "answers.jsonl")
            (d_dir / "answers.jsonl").write_bytes(raw)
            counts[n] = raw.count(b"\n")
        elif held is not None:
            raise SystemExit(f"REFUSED: {s_dir} holds no answers.jsonl; the subset filter reads exp_01's lines only")
        elif (s_dir / "answers.json").exists():
            for t in range(3):
                raw = (s_dir / "answers.json").read_bytes()
                try:
                    counts[n] = len(json.loads(raw).get("results") or [])
                    break
                except ValueError:
                    time.sleep(5)
            else:
                raise SystemExit(f"REFUSED: {s_dir / 'answers.json'} did not parse in 3 reads (being rewritten?)")
            (d_dir / "answers.json").write_bytes(raw)
        else:
            raise SystemExit(f"REFUSED: {s_dir} holds no answers.jsonl or answers.json")
    extra = {}
    if sub:                                                  # the subset's file beside runs/, under the manifest
        ids_raw = (ROOT / sub["ids"]).read_bytes()
        (part / Path(sub["ids"]).name).write_bytes(ids_raw)
        extra = {"subset": {"ids_file": sub["ids"], "ids_sha256": hashlib.sha256(ids_raw).hexdigest(),
                            "ids": len(json.loads(ids_raw)["ids"]), "configs": list(sub["configs"]),
                            "draws": list(sub["draws"]), "lines_left_out": left_out,
                            "why": "D175 Q3, D176: a local T2 generator's RLM set-ups on D98's 45 questions at "
                                   "every draw; lines of other questions at those draws are not copied"}}
    return finish_snap(set_name, src, dest, part, counts, extra)


def finish_snap(set_name: str, src: Path, dest: Path, part: Path, counts: dict, extra: dict) -> int:
    import hashlib
    files = sorted(f for f in part.rglob("*") if f.is_file())
    (part / "MANIFEST.sha256").write_text("".join(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(part)}\n"
                                                  for f in files))
    U.write_json(part / "COPY.json", {"copied": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "set": set_name,
                                      "from": f"{socket.gethostname()}:{src.resolve()}",
                                      "script": "findings/recompute/S3_runs/s3_guard.py snap", "answer_lines": counts,
                                      **extra})
    part.rename(dest)
    lo = (extra.get("subset") or {}).get("lines_left_out")
    un = extra.get("results_union")
    print(f"SNAPPED: {set_name}, {len(counts)} runs, {sum(counts.values())} answer lines (records) into {dest}"
          + ("" if lo is None else f"; {sum(lo.values())} lines of questions outside the subset left out ({lo})")
          + ("" if not un else f"; the union of {un['files']} results files ({un['rows_read']} rows read)"))
    return 0


def read_results(f: Path) -> tuple[bytes, dict]:
    """A results file exp_06 rewrites whole after each answer: read until it parses (3 tries, 5 s apart). Returns the
    bytes read and the parsed file, whose "results" is a list."""
    for _ in range(3):
        raw = f.read_bytes()
        try:
            data = json.loads(raw)
            if isinstance(data.get("results"), list):
                return raw, data
        except (ValueError, AttributeError):
            pass
        time.sleep(5)
    raise SystemExit(f"REFUSED: {f} did not parse in 3 reads (being rewritten?)")


# D185 (2): the top-level fields of exp_06's results files (exp_06 _save_results) that the union file carries; every
# file that has one must give it the same value. records.py checks a row's sink against "index" (_results_file).
UNION_HEAD = ("experiment", "model", "index", "question_set")


def snap_results(set_name: str, src: Path, part: Path) -> tuple[dict, dict]:
    """G5 (D104 A3): src is the G5 clone. Every file the set's glob matches is read (exp_06's resume reads their
    union), but a *_merged.json (exp_06 --merge's output), which exp_06's resume and check_g5 also skip (listed in
    COPY.json results_skipped_merged); a file whose name is not one exp_06 gives a results file (SETS snap "names")
    is refused; one answer key
    with two different rows is refused. When one file holds the whole union, that file is copied byte for byte (as
    before D185). When none does (D185 (2): G7's draws 2 and 3 ran as 4 shares, D95 Q213, each share's files holding
    its own questions' rows), the union is written as one results file: each answer key once (rows equal in several
    files are one answer), ordered as exp_06 --merge orders them (question, depth, draw), with the top-level fields
    UNION_HEAD that every file agrees on (two files with different values: refused). Each file read is listed with
    its sha256 in results_sources.sha256 at the copy's root (paths under the clone; MANIFEST.sha256 covers that file)
    and in COPY.json. Then each sink the rows name: index_identity.jsonl (required: records.py reads the passage ids
    through it) and run_identity.json. The calls are not copied (the judge does not read them)."""
    import hashlib
    import shutil
    st = SETS[set_name]
    files = sorted(src.glob(st["snap"]["results"]))
    merged = [f.name for f in files if f.name.endswith("_merged.json")]   # exp_06 --merge's output: skipped, as exp_06's
    files = [f for f in files if not f.name.endswith("_merged.json")]     # resume (:623) and check_g5.answers skip it
    if not files:
        raise SystemExit(f"REFUSED: no results file {src / st['snap']['results']}"
                         + (f" (only {merged}, skipped)" if merged else ""))
    odd = [f.name for f in files if not re.fullmatch(st["snap"]["names"], f.name)]
    if odd:
        raise SystemExit(f"REFUSED: {len(odd)} file(s) the glob matches are not named as exp_06 names a results file "
                         f"({st['snap']['names']}), first {odd[0]}; nothing copied")
    union: dict = {}
    read, sha, heads = {}, {}, {}
    for f in files:
        raw, data = read_results(f)
        rows = data["results"]
        keys = [r.get("answer_key") for r in rows]
        if None in keys or len(set(keys)) != len(keys):
            raise SystemExit(f"REFUSED: {f}: a row without answer_key, or one answer key twice")
        for r in rows:
            k, v = r["answer_key"], json.dumps(r, sort_keys=True, ensure_ascii=False)
            if union.setdefault(k, (v, f.name, r))[0] != v:
                raise SystemExit(f"REFUSED: answer {k} differs between {union[k][1]} and {f.name}")
        read[f.name] = (raw, rows, set(keys))
        sha[f.name] = (hashlib.sha256(raw).hexdigest(), f.relative_to(src).as_posix())
        for h in UNION_HEAD:
            if h in data:
                heads.setdefault(h, {}).setdefault(json.dumps(data[h], sort_keys=True), f.name)
    whole = [n for n, (_, _, ks) in read.items() if ks == set(union)]
    (target := part / st["runs"][0]).parent.mkdir(parents=True)
    made = None
    if whole:                                                   # one file holds every answer: copied byte for byte
        latest = [n for n in whole if n.endswith("_latest.json")]   # exp_06 keeps a _latest twin of its timestamped file
        name = (latest or whole)[0]
        raw, rows, _ = read[name]
    else:                                                       # D185 (2): the shares' union, each answer once
        split = {h: sorted(vs.values()) for h, vs in heads.items() if len(vs) > 1}
        if split:
            h, ns = next(iter(split.items()))
            raise SystemExit(f"REFUSED: the results files disagree on {h!r} ({', '.join(ns)}); no union written")
        name = None
        rows = sorted((u[2] for u in union.values()), key=lambda r: (str(r.get("question_id")), r.get("depth") or 0,
                                                                     r.get("draw") or 0, r["answer_key"]))
        head = {h: json.loads(next(iter(vs))) for h, vs in heads.items()}
        raw = json.dumps({**head, "n_results": len(rows), "results": rows, "union_of": sorted(read)}, indent=2).encode()
        made = {"rows": len(rows), "sha256": hashlib.sha256(raw).hexdigest(), "files": len(read),
                "rows_read": sum(len(r) for _, r, _ in read.values()),
                "why": "D185 (2): no one results file held every answer (G7's shares, D95 Q213); the union of the "
                       "files, each answer key once, rows equal in several files taken once"}
    target.write_bytes(raw)
    (part / "results_sources.sha256").write_text("".join(f"{h}  {p}\n" for h, p in (sha[n] for n in sorted(sha))))
    for rid in sorted({r["run_id"] for r in rows}):
        s_dir, d_dir = src / st["snap"]["sinks"] / rid, part / "runs" / rid
        if not (s_dir / "index_identity.jsonl").is_file():
            raise SystemExit(f"REFUSED: {s_dir} holds no index_identity.jsonl")
        d_dir.mkdir(parents=True)
        for f in ("index_identity.jsonl", "run_identity.json"):
            if (s_dir / f).exists():
                shutil.copy2(s_dir / f, d_dir / f)
    return ({st["runs"][0].rsplit("/", 1)[-1]: len(rows)},
            {"results_copied": name, "results_union": made,
             "results_read": {n: len(r) for n, (_, r, _) in read.items()},
             "results_sha256": {n: sha[n][0] for n in sorted(sha)}, "results_skipped_merged": merged,
             "sinks": sorted({r["run_id"] for r in rows})})


def main(argv: list[str] | None = None, **canned) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("survey")
    s.add_argument("--base", required=True)
    s.add_argument("--ledger", type=Path)
    s.add_argument("--job-pattern")
    r = sub.add_parser("release")
    r.add_argument("--base", required=True)
    r.add_argument("--ledger", required=True, type=Path)
    r.add_argument("--log", required=True, type=Path)
    r.add_argument("--why", required=True)
    r.add_argument("--job-pattern")
    sub.add_parser("set").add_argument("--set", required=True)
    for name in ("units", "plan"):
        p = sub.add_parser(name)
        p.add_argument("--set", default="G1")
        p.add_argument("--inputs", type=Path, help="default: the set's (SETS)")
        p.add_argument("--out", required=True, type=Path)
        p.add_argument("--phases", help="default: the set's")
        p.add_argument("--answered-only", choices=["0", "1"], help="default: the set's")
    sub.choices["plan"].add_argument("--check-dir", type=Path, help="default: <out>/check")
    sub.choices["plan"].add_argument("--unit")
    sub.choices["plan"].add_argument("--judge", choices=["main", "second"], default="main",
                                     help="judge_passages --judge whose rows and check are read (D85)")
    for name in ("claim", "unclaim"):
        c = sub.add_parser(name)
        c.add_argument("--out", required=True, type=Path)
        c.add_argument("--unit", required=True)
        c.add_argument("--worker", required=True)
    m = sub.add_parser("same")
    m.add_argument("--old", required=True, type=Path)
    m.add_argument("--new", required=True, type=Path)
    m.add_argument("--keys", required=True, type=Path)
    m.add_argument("--configs", nargs="+", default=list(CONFIGS[2:]))
    m.add_argument("--store", type=Path)
    k = sub.add_parser("collect")
    k.add_argument("--out", required=True, type=Path, nargs="+")
    k.add_argument("--replace", type=Path)
    k.add_argument("--dest", required=True, type=Path)
    k.add_argument("--set", choices=list(SETS), help="the set the outs hold: its phases go into the sidecar (F7)")
    n = sub.add_parser("snap")
    n.add_argument("--set", required=True)
    n.add_argument("--src", required=True, type=Path)
    n.add_argument("--dest", required=True, type=Path)
    k = sub.add_parser("link")
    k.add_argument("--set", required=True)
    k.add_argument("--inputs", required=True, type=Path)
    k.add_argument("--make", action="store_true")
    k.add_argument("--runs-root", type=Path, help="default: records.read_run's (the clone's findings/runs)")
    a = ap.parse_args(argv)
    if a.cmd == "snap":
        return snap(a.set, a.src, a.dest)
    if a.cmd == "link":
        if not SETS.get(a.set, {}).get("linked_sinks"):
            print(f"REFUSED: {a.set} has no linked sinks (SETS)")
            return 1
        bad = link(a.set, a.inputs, a.make, a.runs_root)
        print("LINKS " + ("IN PLACE" if not bad else f"MISSING OR WRONG: {len(bad)}; first: {bad[0]}"))
        return 0 if not bad else 1
    if a.cmd == "set":         # run_s3.sh's defaults: inputs, out folder (beside this file), phases; the store's manifest
        if a.set not in SETS:
            print(f"REFUSED: no set {a.set!r} (SETS: {', '.join(SETS)})")
            return 1
        st = SETS[a.set]
        if "plain_only" in st:   # B17: run_s3.sh's seventh field is empty or "all"; S512 reads the set from the out's name
            st = {**st, "questions": "all"}
        # an S6 set adds a sixth field, the judge script run_s3.sh must run for it; a G7 set (D184) a seventh, its
        # question scope (S512 --questions); every other set's line as before
        print("\t".join([str(home(st["inputs"])), st["out"], st["phases"], *store_manifest(st)]
                        + ([st["judge_script"]] if st.get("judge_script") else [])
                        + ([st["questions"]] if st.get("questions") else [])))
        return 0
    if a.cmd in ("units", "plan"):
        st = SETS.get(a.set) or {}
        inputs = (a.inputs or home(st.get("inputs", "?"))).resolve()
        phases = a.phases or st.get("phases", "1 2 3")
        ao = None if a.answered_only is None else a.answered_only == "1"
        if a.cmd == "plan":
            return plan(a.set, inputs, a.out, phases, a.check_dir or a.out / "check", a.unit, ao, a.judge)
        for u in units(a.set, inputs, a.out, phases, ao):
            print("\t".join([u["unit"], u["variants"], ",".join(map(str, u["draws"])) if u["draws"] else "-",
                             str(u["run"]), str(u["out"]), str(u["store"] or "-"), str(u["keys"] or "-"),
                             "1" if u["answered_only"] else "0"]))
        return 0
    if a.cmd == "claim":
        return claim(a.out, a.unit, a.worker)
    if a.cmd == "unclaim":
        return unclaim(a.out, a.unit, a.worker)
    if a.cmd == "same":
        return same(a.old, a.new, a.keys, [f"runs/exp_01__{c}__exp_v4_s20_n0" for c in a.configs], a.store)
    if a.cmd == "collect":
        return collect(a.out, a.replace, a.dest, a.set)
    if a.cmd == "release":
        res = release(a.base, a.ledger, a.log, a.why, pattern=a.job_pattern, **canned)
        print(json.dumps(res))
        print("RELEASED: " + (", ".join(res["ledger"]["loaded_at_release"]) or "nothing loaded") if res["released"]
              else "NOT RELEASED: " + res["why"])
        return 0 if res["released"] else 1
    out = survey(a.base, a.ledger, a.job_pattern, **canned)
    print(json.dumps(out))
    print(("WAIT: " if out["wait_q152"] else "BUSY: " if out["busy"] else "FREE: ") + summary(out))
    return 3 if out["wait_q152"] else 1 if out["busy"] else 0


if __name__ == "__main__":
    sys.exit(main())
