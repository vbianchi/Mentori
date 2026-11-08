#!/usr/bin/env python3
"""judged_ledger - one read path to a deposit answer joined to its judge scores on the current answer key.

WHY. S388 writes the merged ledgers of the S373 re-judge. S393_early_claims.py:288-454 has its own merge, Resolver
and tables, and S392_supervisor_labels_v22.py:206-228, S390_status_board.py:91-107,
S08_human_eval_analysis.py:1283-1293 and S18e_judge_evidence_devstral.py:645 each glob the raw S373 ledgers with
their own code. The analysis scripts that move to the re-judged scores read through this module, so that the group
of a question, the arm of a row, the Q55 scope and the D7 drop are each decided in one place. S393 is not imported
by the load path: it stays the second implementation the self-test compares with. The module is not named
judged_rows: 13 scripts define a function of that name and S78_rlm_draw_spread.py:47 imports it, so a line
"import judged_rows" would rebind the name in any of them.

SOURCE. The merged ledgers findings/recompute/S388_rejudge_v22/<folder>/<judge>.jsonl, which S388 writes and git
does not hold (Q58, notes/DECISIONS_2026-10-12.md:59-60). Before any ledger is read (_context):
  - S373.KEY and S373.AS_V1 exist; key_scope.KEY is S373.AS_V1 and key_scope.Scope() accepts its sha256
    (key_scope.KEY_SHA256; another sha256 is key_scope's own refusal, which starts "key_scope REFUSED:"); AS_V1's
    source_v<version>_sha256 is the sha256 of S373.KEY (S388's check, :259-263)
  - findings/recompute/S388_rejudge_v22.json is JSON and holds the blocks _provenance, inputs, experiments, outputs
    and final; every output it lists is "<folder>/<judge>.jsonl" for a folder of S388.LABEL_TO_SLUG and a judge of
    S373.JUDGES, with a sha256, a row count and, under experiments, the expected, rows and scored counts of that
    folder and judge (_check_record)
  - that json records the two key files' sha256 as the key its ledgers were merged under, and final.passes true
    (S388:453-461: every expected answer has a scored main-judge row, none of them unattributed, every S380 status
    file finished), with the scored count of every main-judge folder equal to its expected count
  - every file that json lists under "outputs" is in the folder with the listed sha256 (_check_tree). A file in
    the folder that the json does not list is not read
When a ledger is parsed (_ledger) its bytes are hashed again, and its rows and its scored rows must be the counts
that json gives for it (outputs: rows; experiments: rows and scored).

STOPS. A check that fails, a file that is missing and a file that is not what its reader expects (a key file,
S388's record, the manifest, a result file, a ledger line that is not JSON) are each a SystemExit of one sentence
that starts "judged_ledger REFUSED:" (key_scope's refusal of AS_V1's sha256, above, is the one that does not) and
names the file or the ledger key; a sentence about the merged folder, a whole ledger or S388's record ends with
the command REBUILD. A wrong argument is a ValueError of one sentence: an unknown experiment or judge, a judge with
no ledger for the experiment, a partial ledger without partial=True, an arm the experiment has no row in, and
load_all for a judge with no merged ledger or, without partial=True, with a partial ledger for any experiment.

JUDGES. The judges of an experiment are the ones that json lists a ledger for: on 13 October devstral (the main
judge, D8) for every experiment and gptoss for the two replications. A ledger with fewer scored rows than expected
answers in that json (the qwen ledgers) is partial and is read only with partial=True. For a ledger that is not
partial, load() also refuses unless (_check_complete, once per experiment and judge) the answers the experiment's
result files hold on a question of the key that is not a D7 question, per arm (deposit_counts(experiment).expected),
are the ledger's rows of the experiment per arm, and unless those answers, summed over the experiments the ledger
holds rows of (four experiments share the folder reanalysis_arms), are the expected count that json gives the
folder and judge (it gives one expected count per folder and judge, none per arm).

RESULT FILES. Read through S374's reader, each once per process (_file); a file that is missing, or that S374's
reader cannot read row by row, is a refusal that names it. data/upstream/MANIFEST.sha256, which git holds, lists
the deposit's files as "<sha256>  publication/<part>/<file>": the path under the deposit root
(bootstrap_upstream.py, collect and write_manifest). machine.py resolves that root on each machine (UPSTREAM:
MENTORI_PAPER, then data/upstream, then a sibling checkout), so the manifest name of a result file is its path
under UPSTREAM. A result file the manifest lists must have the listed sha256, compared once per process on the
bytes read just before S374's reader opens the file (_check_pin); another sha256 is a refusal that names the file
and both hashes. On 13 October the manifest lists the 32 result files under the deposit root and none of the 29
under findings/recompute (the S141 folders, S357 and the S314 rerun): git tracks those 29 and the load path hashes
none of them, so a changed copy of one of them loads without a message. The self-test's J15 tests that each of the
29 is its blob at HEAD.

JOIN (_resolve, _row). A ledger key is "<S374 label>|<file tag>|<row index>" (S373_rejudge_v2.py:170). The tag is
the result file's name, or its folder's name when the path holds "S141" (:163); the index is the row's position in
S374's load_rows(file) (:164), as a decimal number without leading zeros. The key is resolved to that row through
S374's reader. The row's question (s374 qid) and the length of its answer (s374 answer) must equal the ledger
row's question_id and answer_chars (S388 rule 5); the ledger row's source and row must be the key's tag and index;
its config must be what S373 stores for that row (:171); its judge must be the model S373.JUDGES gives the
ledger's judge; its key_hash must be S373.key_hash of its question under S373.KEY (S388 rule 3). A key that
resolves to no row, to another question or to another answer length is a SystemExit that names the key. So is a
row with another key hash, and a ledger row on a D7 question (S388 rule 2 drops them).

ROW. One Row per judged answer. A Row is frozen, and it compares and hashes by identity: load() returns the same
objects on every call, so Rows can be put in a set or used as dict keys. Fields, and where each applies (None
elsewhere):
  experiment   the short name used here (EXPERIMENTS); slug, label: S388's folder and the S374 label
  key          the ledger key; tag and row are its file tag and row index
  judge        devstral, gptoss or qwen (S373.JUDGES); judge_model is the ledger's model name
  question_id, answer_chars, status
  scores       the ledger's scores as a read-only view (types.MappingProxyType; dict(row.scores) is a copy that
               can be changed or written as JSON); None on a row without a score. A view cannot be copied or
               pickled, so dataclasses.asdict, copy.deepcopy, pickle and pandas.DataFrame(rows) raise TypeError on
               a scored Row: row.as_dict() gives the 26 fields with scores as a dict of its own, for
               pandas.DataFrame([r.as_dict() for r in rows])
  answer_type  S373.KEY's answer_type of the question; group: see GROUP
  config       the deposit row's config: the strategy in exp04, exp05, rep2, rep5, s141_mini, s141_timing and
               s357; the pipeline configuration in exp06; "naive_baseline" in naive. exp07: the row's model_key
               (the benchmark's name for a generator and its thinking setting). s314: S314_CONFIG, since the file
               holds the verified_pass rows of exp05 only and its rows carry no config (exp05_final.py:46-52; J13
               checks the questions per index against the deposit). None in exp09 and exp00
  generator    the model that wrote the answer, under the name the result file stores, as S374's genmodel reads it
               from the row or the file. It is not mapped to another name: for rep2's
               reviewer_strategy_replication.json it is ollama::qwen3-coder:latest, the generator S393.TWO_FILES
               (S393_early_claims.py:171) names qwen3-coder:30b. s314: the gen_model of the file's "_header" lines
               (genmodel returns a fixed text for that file, s374/rows.py:57)
  draw         rep5: the <d> of its folder name <generator>__draw<d>. rep2: REP2_DRAW (one run per generator;
               the files hold no draw, S393_early_claims.py:397 and S320_replication_two_tidy.csv name it 1)
  index, core, noise   exp05 and s314: the index name exp_v4_s<core>_n<noise> (noise is the ratio of noise papers
               to core papers, create_indexes.py:110-121)
  depth        exp09: the row's retrieval depth
  arm          see ARM;  in_scope: see SCOPE
  dimension, score, passed   see SCORE

GROUP. From S373.KEY's answer_type, never from the ledger's "answerable", which records the prompt used and is
true for the ten (S373_rejudge_v2.py:18-21; D5 and Q51, notes/DECISIONS_2026-10-11.md:36-74):
  answerable       answer_type extractive or synthesis
  refutation       answer_type refutation: the ten false-premise questions OOD_041 to OOD_050, answered by
                   refuting the premise
  not_answerable   answer_type not_answerable: no answer in the corpus
_context refuses a key with any other answer_type, a record whose question_answerable is not
(answer_type != not_answerable), a refutation set that is not key_scope's Scope.ten, and an AS_V1 record whose
answerable differs from question_answerable.

SCORE. dimension is correctness for the groups answerable and refutation (the ten are scored against the
refutation) and refusal_accuracy for not_answerable. score is scores[dimension]; passed is score >= PASS_AT
(S393_early_claims.py:450). A scored row (status ok or ok_output_limit) whose scores lack that dimension, or hold
there something other than an integer from 0 to 5 (a bool, a float and NaN are refused too), is a SystemExit that
names the key and the value. Every other value in scores must be null or an integer from 0 to 5, or the row is
refused the same way; a null stays None, so a consumer of another dimension handles None itself (J10 counts the
nulls per judge and dimension: on 13 October hallucination_avoidance on 15 devstral rows and completeness on 1
gptoss row). A row with no status is refused. A row with any other status has scores, score and passed None;
reported() leaves it out and counts it.

ARM. A mark; no row is removed. Devstral rows on 13 October 2026 (v1-format key e971de522df6), recounted by J7:
  reported               26,847   every row not named below
  deposit_verified_pass   1,629   exp05 rows whose config is verified_pass: the deposit's own rows of that
                                  strategy. The paper's verified_pass rows of corpus scaling are the S314 rerun's
                                  (exp05_final.py:1-8: Valerio adopted the rerun on 28 September), which here are
                                  s314's rows of the arm reported
  thinking_off              932   rep5 folders named <generator>__draw<d> plus the suffix S141_campaign.SIDE_ARMS
                                  gives its thinking-off arm ("__thinkoff", S141_campaign.py:67). SIDE_ARMS lists
                                  the glm-4.7-flash arm; the gemini-3-flash-preview draw 1 folder carries the same
                                  suffix, and J7 checks both folders against think_off or gemini_think_off in
                                  arm_header.json. 932 gptoss rows too
  smoke                      18   s314 rows of phase smoke, 9 of mode separate and 9 of mode inline, all at 50
                                  core papers. The reported s314 rows are phase repro or full with mode separate
                                  (exp05_final.py:51): 1,629
  mini                    2,390   every s141_mini row
  timing                    298   every s141_timing row
  gemini                    180   every s357 row
An S314 phase and mode outside these, or a rep5 folder name outside that grammar, is a SystemExit.

CORPUS SCALING. reported("exp05") keeps rows of the arm reported, so it holds every strategy but verified_pass and
its statement counts the 1,629 deposit_verified_pass rows among the rows left out. corpus_scaling_reported()
returns in one call what the paper reports for the experiment: those rows followed by reported("s314").rows, with
the statement of both selections. It refuses unless s314's rows of the arm reported and exp05's rows of the arm
deposit_verified_pass are on the same (index, question) pairs, one row each (1,629 pairs; J13 compares them with
the deposit file as well).

SCOPE (Q55, notes/DECISIONS_2026-10-12.md:5-13). in_scope is key_scope.Scope.row_in_scope(question, index) for
exp05 and s314, None for every other experiment. False on 144 exp05 rows (90 at 5 core papers, 54 at 10; 120 of
the arm reported and 24 of the arm deposit_verified_pass) and 24 s314 rows (15 and 9), all on the ten (J8). No
scope rule is applied in the other experiments; the self-test's table counts their rows on the ten as the group
refutation. Among them exp07 holds 70 devstral rows on five of the ten, and neither its result files nor its
dataset file (exp07_bench_synthesizer_dataset.json, which S374's list leaves out) hold an index name.

D7. The six questions whose text changed are absent from the merged ledgers (S388 rule 2). deposit_counts(experiment)
counts, from the result files, the key's question list and AS_V1's dropped_d7, the deposit answers on those
questions per arm, next to the rows with no answer and the answers on the key's other questions (expected). The
set comes from the key file, and no count is held in the load path. S373 leaves the changed questions out by its
own rule, which compares each question's text in S373.KEY with the v1 key and does not read dropped_d7
(S373_rejudge_v2.py:231-233): the two sets are the same six questions on 13 October (J9), and emptying dropped_d7
does not by itself make S373 judge them. With dropped_d7 emptied (D9) and the ledgers as they are, load() refuses
(JUDGES) for every experiment whose S388 folder holds deposit answers on those questions (12 of the 13 on
13 October; exp00 holds none and loads), because those answers are then expected and no ledger holds them.

    import judged_ledger as jl
    rows = jl.load("exp05")                  # every devstral row of the exp05 file, every arm: a tuple of Row
    sel = jl.reported("exp05")               # arm reported (every strategy but verified_pass), in scope, scored
    print(sel.statement())                   # rows kept, rows each rule left out, D7 answers not in the ledger
    cs = jl.corpus_scaling_reported()        # sel.rows and reported("s314").rows; cs.statement() states both
    pairs = jl.paired("rep5").pairs          # (devstral Row, gptoss Row) per ledger key both judges hold
    jl.deposit_counts("exp05").d7            # arm -> deposit answers on D7 questions, a read-only view
    jl.load("exp04", "qwen", partial=True)   # a partial ledger, on request only

The checks, the ledgers and the result files are cached within a process: the checks run once, each ledger is
parsed once, each result file is loaded once through S374's reader (the S314 file is read once more for its header
lines), and a second load of the same experiment and judge returns the same tuple. reported(), paired() and
corpus_scaling_reported() build their result on each call. Importing the module imports machine.py, which looks
for the harness checkout with git rev-parse (machine.py:106-120). No function of the load path starts a process,
calls a model or opens a connection.

SELF-TEST. Reads the two key files and the v1 key (S373.V1), S388's record and its blob at HEAD, the merged
ledgers, the result files and the manifest, the question files data/ground_truth_v2/inputs_v2_1/<question>.json
(through S373.SOURCES, S373_rejudge_v2.py:172), the S373 ledgers S393 reads,
findings/recompute/S141_phase5_tidy_corrected.csv (through S393.Resolver, S393_early_claims.py:335-337) and the
S141 arm headers; runs git ls-tree, hash-object, show and ls-files, which write nothing; writes nothing; exits 1
if a gate fails. A gate line prints what the gate tested, each test with its own True or False, and counts.

    uv run python scripts/judged_ledger.py

  J1   the two key files' sha256 against key_scope.KEY_SHA256, AS_V1's header and S388_rejudge_v22.json
  J2   every merged ledger's sha256 and row count against that json; that json against its blob at HEAD, both
       parsed and compared block by block without _provenance["generated"], the time S388 writes on every run
       (S388:493), with the blocks that differ printed. A record that a rebuild changed in that time alone passes
  J3   refusals, on altered copies held in memory: a missing folder, a missing ledger, a ledger with another hash
       or other counts than the record's, a ledger line that is not JSON; a record that is not JSON or lacks a
       block or an output's counts; a key file without its records; a manifest that is not one; a missing result
       file and one with another sha256 than the manifest's; a key with no row, another question, another answer
       length, another key hash; a row without a status; a scored row without its group's dimension or with a
       score that is not an integer 0 to 5, in that dimension or another; a record whose final.passes is true
       with a main-judge folder short of its expected count; deposit answers that differ from the ledger's rows
       or the record's expected count; rerun rows off the deposit's pairs. Wrong arguments: a partial or absent
       ledger, an unknown experiment, an arm the experiment lacks, load_all with an unknown judge or a judge with
       a partial ledger. And a row without a score, read as None
  J4   the group field: answer_type's values and records, against AS_V1's questions, Scope.ten and
       key_scope.D5_TEN; the ledgers' answerable flag on the ten
  J5   the join against S373's own item builder (S373.SOURCES, as S388 builds its expected set): the same keys,
       questions and answer lengths for both judges; each source's answers off D7 against S388.KNOWN_SOURCE
  J6   rows per experiment and judge against S388.KNOWN_LABEL and the expected totals; the exp04 groups
  J7   rows per arm; the s314 smoke rows' core size; each rep5 folder's arm_header.json against tag, generator,
       draw and arm
  J8   in_scope against key_scope's partition of the deposit rows; None outside exp05 and s314
  J9   D7: deposit rows = rows with no answer + answers on D7 questions + ledger rows, per experiment and arm; the
       questions S373's own rule leaves out against dropped_d7
  J10  the score dimension and pass rule on every scored row; every value of every dimension an integer 0 to 5
       or null, with the nulls counted; PASS_AT against exp05_final.PASS_AT
  J11  reported(): rows kept plus rows left out is every row, per experiment
  J12  paired(): the two replications, devstral with gptoss, and the rows each rule left out on each side
  J13  corpus scaling: s314's rows of the arm reported, exp05's rows of the arm deposit_verified_pass and the
       deposit file's verified_pass answers off D7 are on the same (index, question) pairs, one row each; the
       verified_pass rows corpus_scaling_reported() returns are s314's, on the pairs the deposit's arm keeps under
       the same scope and score rules; the generator in the file's headers
  J14  the cache: the same objects on a second call; scores, d7 and expected are read-only views; Rows hash
  J15  the result files: the sha256 of every file the manifest lists against the manifest, and the manifest
       against its blob at HEAD; every file it does not list is tracked in git and its blob at HEAD (not tested
       when git gives no answer)
  S0 to S9  the comparison with S393 (the one place S393 is imported). S393 reads this machine's S373 ledgers with
       its own ledgers(judge, remote=False): that path returns before its ssh and scp calls
       (S393_early_claims.py:262-264), so no other machine is contacted. S0: those ledgers are the files S388
       merged (sha256) and the blobs at HEAD. S1: S393.merge gives the same keys and scores as the loader for
       both judges. S2 to S8: S393's Resolver and new_tables against the rows of reported() and paired() mapped
       to S393's unit names, per experiment, with every other loader row counted by the reason S393's table does
       not hold it; in S2 to S5 the pass flag on S393's side is S393's score at S393's threshold. S9: S393's
       count of the rows it maps to no table, bucket by bucket
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "s374"))
import bootstrap_upstream  # noqa: E402
import key_scope  # noqa: E402
import S141_campaign  # noqa: E402
import S388_merge_rejudge_v22 as S388  # noqa: E402
from machine import RECOMPUTE, ROOT, UPSTREAM, VENDOR  # noqa: E402
from rows import answer as s374_answer, genmodel as s374_genmodel, load_rows as s374_load_rows  # noqa: E402
from rows import qid as s374_qid  # noqa: E402


def _s374_files() -> list:
    """S374's list of result files (s374/files.py). That module globs the upstream results when it is imported, so
    it is imported on first use, not when this module is (D155: a figure build that imports judged_ledger must not
    list a sibling checkout). `judged_ledger.S374_FILES` still works, through the module __getattr__ below."""
    from files import FILES
    return FILES


def __getattr__(name: str):
    if name == "S374_FILES":
        return _s374_files()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

S373 = S388.S373                                     # KEY, AS_V1, JUDGES, SOURCES: imported, never retyped
TREE = RECOMPUTE / "S388_rejudge_v22"                # S388's merged ledgers (S388:464); not in git (Q58)
PROVENANCE = RECOMPUTE / "S388_rejudge_v22.json"     # S388's committed record of them (S388:516)
RECORD_BLOCKS = ("_provenance", "inputs", "experiments", "outputs", "final")     # of that record (S388:490-515)
MANIFEST = VENDOR / bootstrap_upstream.MANIFEST_NAME  # data/upstream/MANIFEST.sha256: the deposit's files, in git
REBUILD = "uv run python scripts/S388_merge_rejudge_v22.py --final"
MAIN_JUDGE = S388.MAIN_JUDGE                         # devstral (D8, notes/DECISIONS_2026-10-13.md:5-8)
SECOND_JUDGE = "gptoss"                              # the replications' second judge (Q57); a key of S373.JUDGES
OK = S388.OK                                         # the statuses that carry scores
PASS_AT = 3                                          # S393_early_claims.py:450; J10 checks exp05_final.PASS_AT
SCORE_MIN, SCORE_MAX = 0, 5                          # the judge's scale; J10 counts the values the ledgers hold

ANSWERABLE, REFUTATION, NOT_ANSWERABLE = "answerable", "refutation", "not_answerable"
GROUP_OF = {"extractive": ANSWERABLE, "synthesis": ANSWERABLE,       # S373.KEY's answer_type -> group
            "refutation": REFUTATION, "not_answerable": NOT_ANSWERABLE}
DIMENSION = {ANSWERABLE: "correctness", REFUTATION: "correctness", NOT_ANSWERABLE: "refusal_accuracy"}   # D5

REPORTED, THINKING_OFF, SMOKE, MINI, TIMING, GEMINI = "reported", "thinking_off", "smoke", "mini", "timing", "gemini"
DEPOSIT_VP = "deposit_verified_pass"                 # exp05's own verified_pass rows (exp05_final.py:1-8)
S314_REPORTED = frozenset({("repro", "separate"), ("full", "separate")})     # (phase, mode), exp05_final.py:51
S314_SMOKE = "smoke"                                 # the phase of S314's two 50-paper smoke tests (S316:226-236)
S314_CONFIG = "verified_pass"                        # the strategy S314 reran (exp05_final.py:46-52)
REP2_DRAW = 1                                        # S393_early_claims.py:397
THINKOFF_SUFFIXES = frozenset(a["suffix"] for a in S141_campaign.SIDE_ARMS if a.get("think_off"))   # :65-68

_INDEX = re.compile(r"exp_v4_s(\d+)_n(\d+)")         # create_indexes.py:110-112
_DRAW = re.compile(r"(.+)__draw(\d+)")               # S141_campaign.arm_id, :95-96
_ROW_INDEX = re.compile(r"0|[1-9][0-9]*", re.ASCII)  # a row index as S373 writes it (:170): no leading zeros
_OUTPUT = re.compile(r"([^/]+)/([^/]+)\.jsonl")      # an output of S388's record: <folder>/<judge>.jsonl (S388:478)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ABSENT = object()
OUT_OF_SCOPE = "out of scope (Q55)"                  # the rules of reported(), as its left_out names them
NOT_SCORED = "judged without a score"


def _refuse(msg: str):
    raise SystemExit("judged_ledger REFUSED: " + msg)


def _label(fragment: str) -> str:
    """The one S374 label in S388.LABEL_TO_SLUG that holds fragment, so that no label is spelled out here."""
    hits = [lab for lab in S388.LABEL_TO_SLUG if fragment in lab]
    if len(hits) != 1:
        _refuse(f"{len(hits)} labels of S388.LABEL_TO_SLUG hold {fragment!r}, expected one")
    return hits[0]


# short name -> S374 label. The first five names are S393.LABELS' own; exp00 and exp07 are the deposit's file prefixes.
EXPERIMENTS = {short: _label(fragment) for short, fragment in (
    ("exp04", "(exp04)"),              # generation strategies
    ("exp05", "(exp05)"),              # corpus scaling: the deposit's file (the paper's verified_pass rows: s314)
    ("exp06", "(exp06)"),              # orchestration (pipeline ablation)
    ("naive", "Naive RAG"),            # naive RAG baseline
    ("exp09", "(exp09)"),              # retrieval depth: nine depth files, six with judged answers
    ("exp00", "(exp00"),               # generator selection
    ("exp07", "(exp07)"),              # component benchmark: synthesizer
    ("rep2", "(published)"),           # strategy replication, two models
    ("rep5", "S141 campaign"),         # strategy replication, five models, three draws
    ("s141_mini", "S141 mini"),        # the S141 small-model arm at 50 core papers
    ("s141_timing", "S141 timing"),    # the S141 timing pass
    ("s314", "S314"),                  # the verified_pass rerun on the exp05 indexes
    ("s357", "S357"))}                 # the S357 Gemini arm
_SHORT = {label: short for short, label in EXPERIMENTS.items()}
if set(_SHORT) != set(S388.LABEL_TO_SLUG) or SECOND_JUDGE not in S373.JUDGES or MAIN_JUDGE not in S373.JUDGES:
    _refuse("EXPERIMENTS does not name every label of S388.LABEL_TO_SLUG once, or a judge is not in S373.JUDGES")
WITH_SCOPE = ("exp05", "s314")                       # the experiments run on several indexes (Q55)
INDEX_FIELD = {"exp05": "index_name", "s314": "index"}   # the deposit row's field that holds the index name
WITH_CONFIG = ("exp04", "exp05", "exp06", "naive", "rep2", "rep5", "s141_mini", "s141_timing", "s357")
ARM_OF = {"s141_mini": MINI, "s141_timing": TIMING, "s357": GEMINI}      # experiments that are one arm


@dataclass(frozen=True, slots=True, eq=False)
class Row:
    """One judged answer: a merged ledger row joined to the deposit row it scores (module docstring, ROW). Two Rows
    are equal only when they are one object, and a Row hashes by identity."""
    experiment: str
    slug: str
    label: str
    key: str
    judge: str
    judge_model: str
    question_id: str
    answer_type: str
    group: str
    config: str | None
    generator: str
    draw: int | None
    index: str | None
    core: int | None
    noise: int | None
    depth: int | None
    arm: str
    in_scope: bool | None
    tag: str
    row: int
    answer_chars: int
    status: str
    scores: MappingProxyType | None
    dimension: str
    score: int | None
    passed: bool | None

    def as_dict(self) -> dict:
        """The 26 fields as a dict, scores as a dict of its own (None on a row without a score)."""
        d = {name: getattr(self, name) for name in self.__slots__}
        d["scores"] = None if self.scores is None else dict(self.scores)
        return d


def _counts(left_out: dict) -> str:
    return ", ".join(f"{n:,} {rule}" for rule, n in left_out.items()) or "none"


@dataclass(frozen=True)
class Selection:
    """What reported() returns: the rows kept, and how many rows each rule left out.

    total is every row of the experiment and judge; left_out maps a rule to its rows, each row counted under the
    first rule that leaves it out, in the order: "arm <name>" for each other arm, OUT_OF_SCOPE (exp05 and s314),
    NOT_SCORED. len(rows) + sum(left_out.values()) == total. d7_answers is the number of deposit answers of this
    arm on D7 questions, which no ledger holds. partial_coverage is None for a ledger S388's record gives as
    complete; for a partial ledger it is (scored, expected), the record's counts for the ledger's folder and
    judge."""
    experiment: str
    judge: str
    arm: str
    rows: tuple[Row, ...]
    total: int
    left_out: dict[str, int]
    d7_answers: int
    partial_coverage: tuple[int, int] | None = None

    def statement(self) -> str:
        """One sentence: rows kept of the total, the count each rule left out, the D7 answers and, for a partial
        ledger, the record's scored and expected counts."""
        partial = "" if self.partial_coverage is None else (
            f"; the ledger is partial: S388's record gives {self.partial_coverage[0]:,} of the "
            f"{self.partial_coverage[1]:,} expected answers of its folder as scored")
        return (f"{self.experiment}, judge {self.judge}, arm {self.arm}: {len(self.rows):,} of {self.total:,} judged "
                f"rows kept; left out: {_counts(self.left_out)}; {self.d7_answers:,} deposit answers of this arm on "
                f"the {len(d7_questions())} D7 questions are in no ledger (S388 rule 2){partial}")


@dataclass(frozen=True)
class Pairs:
    """What paired() returns: (first judge's Row, second judge's Row) per ledger key both judges hold, and the rows
    only one of them holds. With an arm named, left_out_first and left_out_second are the rows reported() left
    out on each side before pairing, rule by rule (Selection.left_out); None with arm=None, where no rule runs."""
    experiment: str
    first: str
    second: str
    arm: str | None
    pairs: tuple[tuple[Row, Row], ...]
    only_first: tuple[Row, ...]
    only_second: tuple[Row, ...]
    left_out_first: dict[str, int] | None = None
    left_out_second: dict[str, int] | None = None

    def statement(self) -> str:
        """One sentence: the pairs, the rows one judge alone holds and, with an arm named, the rows each rule left
        out on each side before pairing."""
        arm = "every arm" if self.arm is None else f"arm {self.arm}, in scope, scored"
        left = "" if self.arm is None else (f"; left out before pairing: {self.first} {_counts(self.left_out_first)}; "
                                            f"{self.second} {_counts(self.left_out_second)}")
        return (f"{self.experiment}, {self.first} with {self.second}, {arm}: {len(self.pairs):,} pairs on the ledger "
                f"key; {len(self.only_first):,} rows of {self.first} alone, {len(self.only_second):,} of "
                f"{self.second} alone{left}")


@dataclass(frozen=True)
class CorpusScaling:
    """What corpus_scaling_reported() returns: rows is exp05.rows followed by s314.rows; exp05 and s314 are the two
    Selections; verified_pass_pairs is the number of (index, question) pairs that the judged rows of the rerun and
    of the deposit's own arm share, one row each, before the scope and score rules."""
    judge: str
    rows: tuple[Row, ...]
    exp05: Selection
    s314: Selection
    verified_pass_pairs: int

    def statement(self) -> str:
        """The rows of each source in one sentence, then the statement of each Selection."""
        return (f"corpus scaling, judge {self.judge}: {len(self.rows):,} rows = {len(self.exp05.rows):,} of exp05 "
                f"(every strategy but {S314_CONFIG}) + {len(self.s314.rows):,} of s314 ({S314_CONFIG}, from the S314 "
                f"rerun: exp05_final.py:1-8); the rerun's {self.verified_pass_pairs:,} judged rows of the arm "
                f"{REPORTED} are on the (index, question) pairs of the deposit's {self.verified_pass_pairs:,} judged "
                f"{S314_CONFIG} rows, one row each. {self.exp05.statement()}. {self.s314.statement()}")


@dataclass(frozen=True)
class DepositCount:
    """Counts over the rows of one experiment's result files, without any ledger (deposit_counts). d7 and expected
    are read-only views."""
    experiment: str
    rows: int                        # rows S374's reader yields
    no_answer: int                   # rows with no answer text: never judged (S373_rejudge_v2.py:166)
    not_in_key: int                  # answers on a question S373.KEY does not hold
    d7: MappingProxyType             # arm -> answers on a D7 question: absent from the merged ledgers
    expected: MappingProxyType       # arm -> answers on a question of the key that is not a D7 question


@dataclass(frozen=True)
class _Context:
    provenance: dict                 # S388_rejudge_v22.json
    key_sha256: str                  # of S373.KEY
    scope: key_scope.Scope           # AS_V1's records and the Q55 rule
    d7: frozenset                    # AS_V1's dropped_d7
    answer_type: dict                # question -> S373.KEY's answer_type, every record (the D7 ones too)
    key_hash: dict                   # question -> S373.key_hash under S373.KEY (S388 rule 3)


# ---- the checks that run once, before any ledger is read --------------------------------------------------

def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _shown(p: Path) -> str:
    try:
        return str(Path(p).relative_to(ROOT))
    except ValueError:
        return str(p)


def _parse_json(raw: bytes, path: Path, what: str, hint: str = ""):
    """raw parsed as JSON; bytes that are not JSON are a refusal that names path."""
    try:
        return json.loads(raw)
    except ValueError as e:
        _refuse(f"{_shown(path)} is not readable as {what} ({type(e).__name__}: {e}){hint}")


def _read_json(path: Path, what: str, hint: str = ""):
    """The parsed JSON of path; a file that cannot be read or is not JSON is a refusal that names it."""
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        _refuse(f"{_shown(path)} is not readable as {what} ({type(e).__name__}: {e}){hint}")
    return _parse_json(raw, path, what, hint)


def _check_record(prov) -> dict:
    """prov (S388's record, parsed), refused unless it holds RECORD_BLOCKS and, for every output, the fields this
    module reads: a "<folder>/<judge>.jsonl" name whose folder S388.LABEL_TO_SLUG holds and whose judge S373.JUDGES
    holds, a sha256, a row count and the folder and judge's expected, rows and scored counts under experiments.
    Refused too when final.passes is true and a main-judge folder's scored count is not its expected count: S388
    sets passes only when the two are equal for every folder (S388:434-461), so such a record was not written by
    S388 as it stands."""
    hint = f"; run: {REBUILD}"
    lacks = [b for b in RECORD_BLOCKS if not isinstance(prov, dict) or not isinstance(prov.get(b), dict)]
    if lacks:
        _refuse(f"{_shown(PROVENANCE)} is not S388's record: it holds no block {', '.join(lacks)}{hint}")
    folders = set(S388.LABEL_TO_SLUG.values())
    for name, meta in prov["outputs"].items():
        m = _OUTPUT.fullmatch(name)
        folder = prov["experiments"].get(m.group(1)) if m else None
        cov = folder.get(m.group(2)) if isinstance(folder, dict) else None
        if (not m or m.group(1) not in folders or m.group(2) not in S373.JUDGES or not isinstance(meta, dict)
                or not isinstance(meta.get("sha256"), str) or not _is_int(meta.get("rows"))
                or not isinstance(cov, dict) or not all(_is_int(cov.get(k)) for k in ("expected", "rows", "scored"))):
            _refuse(f"{_shown(PROVENANCE)} is not S388's record: its output {name!r} is not a ledger of a folder of "
                    f"S388.LABEL_TO_SLUG and a judge of S373.JUDGES with a sha256, a row count and, under "
                    f"experiments, expected, rows and scored counts{hint}")
    if not all(isinstance(v, dict) for v in prov["experiments"].values()):
        _refuse(f"{_shown(PROVENANCE)} is not S388's record: an entry of its experiments block holds no judges{hint}")
    off = sorted(s for s, v in prov["experiments"].items() if isinstance(v.get(MAIN_JUDGE), dict)
                 and v[MAIN_JUDGE].get("scored") != v[MAIN_JUDGE].get("expected"))
    if prov["final"].get("passes") is True and off:
        _refuse(f"{_shown(PROVENANCE)} contradicts itself: final.passes is true and the {MAIN_JUDGE} ledger of "
                f"{', '.join(off)} has a scored count that is not its expected count{hint}")
    return prov


def _check_tree(tree: Path, outputs: dict) -> None:
    """Refuse unless tree holds every file of outputs ({"<slug>/<judge>.jsonl": {"rows", "sha256"}}) with the
    listed sha256. The first missing folder, missing file or other hash is the refusal."""
    if not Path(tree).is_dir():
        _refuse(f"the merged ledger folder {_shown(tree)} is missing; run: {REBUILD}")
    for name, meta in outputs.items():
        p = Path(tree) / name
        if not p.is_file():
            _refuse(f"the merged ledger {_shown(p)} is missing; run: {REBUILD}")
        try:
            got = _sha256(p.read_bytes())
        except OSError as e:
            _refuse(f"the merged ledger {_shown(p)} cannot be read ({type(e).__name__}); run: {REBUILD}")
        want = str(meta.get("sha256"))
        if got != want:
            _refuse(f"the merged ledger {_shown(p)} has sha256 {got[:12]}, {PROVENANCE.name} records "
                    f"{want[:12]}; run: {REBUILD}")


def _key_tables(key_doc) -> tuple:
    """(the header field AS_V1 holds for this key version, question -> answer_type, question -> question_answerable,
    question -> S373.key_hash, the questions S373.refutation names) of S373.KEY as parsed. A document without the
    fields S373 and this module read is a refusal that names the key file."""
    try:
        field = f"source_v{str(key_doc['version']).replace('.', '')}_sha256"     # the field S381 writes (S388:259)
        v2 = {r["id"]: r for r in key_doc["records"]}
        answer_type = {q: r["answer_type"] for q, r in v2.items()}
        answerable = {q: r["question_answerable"] for q, r in v2.items()}
        key_hash = {q: S373.key_hash(q, v2) for q in v2}
        refutes = frozenset(q for q in v2 if S373.refutation(q, v2))
    except (KeyError, TypeError, AttributeError, ValueError) as e:
        _refuse(f"{_shown(S373.KEY)} is not an answer key S373 reads: it lacks version, records or a field of a "
                f"record ({type(e).__name__}: {e})")
    return field, answer_type, answerable, key_hash, refutes


@lru_cache(maxsize=1)
def _context() -> _Context:
    """The keys, S388's record and the merged folder, checked as the module docstring's SOURCE and GROUP say."""
    for p in (S373.KEY, S373.AS_V1, PROVENANCE):
        if not p.is_file():
            _refuse(f"{_shown(p)} is missing" + (f"; run: {REBUILD}" if p == PROVENANCE else ""))
    if key_scope.KEY.resolve() != S373.AS_V1.resolve():
        _refuse(f"key_scope reads {_shown(key_scope.KEY)} and S373 judges on {_shown(S373.AS_V1)}: two key files")
    try:
        scope = key_scope.Scope()                        # refuses unless AS_V1's sha256 is key_scope.KEY_SHA256
    except (KeyError, TypeError, AttributeError, ValueError) as e:
        _refuse(f"{_shown(S373.AS_V1)} is not a key key_scope reads ({type(e).__name__}: {e})")
    key_raw = S373.KEY.read_bytes()
    key_sha = _sha256(key_raw)
    field, answer_type, answerable, key_hash, refutes = _key_tables(_parse_json(key_raw, S373.KEY, "an answer key"))
    as_v1 = _read_json(S373.AS_V1, "the v1-format key")
    header = as_v1.get(field) if isinstance(as_v1, dict) else None
    if header != key_sha:
        _refuse(f"{_shown(S373.AS_V1)} was built from another key ({field} {str(header)[:12]}), not "
                f"{S373.KEY.name} ({key_sha[:12]})")
    prov = _check_record(_read_json(PROVENANCE, "S388's record", f"; run: {REBUILD}"))
    head = prov["_provenance"]
    if head.get("key_sha256") != key_sha or head.get("as_v1_sha256") != scope.sha256:
        _refuse(f"{_shown(PROVENANCE)} records ledgers merged under another key ({str(head.get('key_sha256'))[:12]} "
                f"and {str(head.get('as_v1_sha256'))[:12]}; the key files are {key_sha[:12]} and "
                f"{scope.sha256[:12]}); run: {REBUILD}")
    if prov["final"].get("passes") is not True:
        _refuse(f"{_shown(PROVENANCE)} does not record a passed final check ({prov['final']}); run: {REBUILD}")
    _check_tree(TREE, prov["outputs"])

    for q, t in answer_type.items():
        if not isinstance(t, str) or t not in GROUP_OF:
            _refuse(f"{S373.KEY.name} gives {q} the answer_type {t!r}, which GROUP_OF does not hold")
        if answerable[q] is not (GROUP_OF[t] != NOT_ANSWERABLE):
            _refuse(f"{S373.KEY.name}: {q} has answer_type {t} and question_answerable {answerable[q]!r}")
        rec = scope.records.get(q)
        if rec is None and q not in scope.dropped_d7:
            _refuse(f"{q} is in {S373.KEY.name} and neither a question nor a D7 drop of {S373.AS_V1.name}")
        if rec is not None and rec["answerable"] is not answerable[q]:
            _refuse(f"{q}: answerable {rec['answerable']} in {S373.AS_V1.name}, question_answerable "
                    f"{answerable[q]} in {S373.KEY.name}")
    ten = {q for q, t in answer_type.items() if GROUP_OF[t] == REFUTATION}
    if ten != set(scope.ten) or ten != refutes:
        _refuse(f"the refutation questions of {S373.KEY.name} ({len(ten)}) are not key_scope's Scope.ten "
                f"({len(scope.ten)}) or not the questions S373.refutation names")
    return _Context(provenance=prov, key_sha256=key_sha, scope=scope, d7=frozenset(scope.dropped_d7),
                    answer_type=answer_type, key_hash=key_hash)


# ---- the result files, through S374's reader --------------------------------------------------------------

def _tag(path: str) -> str:
    """The file tag of a ledger key, as S373 builds it (S373_rejudge_v2.py:163)."""
    return Path(path).name if "S141" not in path else Path(path).parent.name


@lru_cache(maxsize=1)
def _paths() -> dict:
    """(S374 label, file tag) -> result file, for the labels S388 files under an experiment."""
    out: dict = {}
    for label, path in _s374_files():
        if label not in S388.LABEL_TO_SLUG:
            continue
        if (label, _tag(path)) in out:
            _refuse(f"two result files of {label!r} share the tag {_tag(path)!r}")
        out[(label, _tag(path))] = path
    return out


def _read_manifest(path: Path) -> MappingProxyType:
    """name -> sha256 of a manifest file, through bootstrap_upstream.read_manifest (the reader its --verify uses).
    A file that is missing, that the reader cannot split into "<sha256>  <name>" lines, that lists no file or that
    holds something other than 64 hexadecimal digits as a sha256 is a refusal that names it."""
    if not Path(path).is_file():
        _refuse(f"{_shown(path)} is missing: git holds it, and it lists the sha256 of the deposit's files")
    try:
        rows = bootstrap_upstream.read_manifest(Path(path))
    except (OSError, ValueError) as e:
        _refuse(f"{_shown(path)} is not a manifest of lines '<sha256>  <path>' ({type(e).__name__}: {e})")
    bad = [name for name, sha in rows.items() if not _SHA256.fullmatch(sha)]
    if bad or not rows:
        _refuse(f"{_shown(path)} is not a manifest of lines '<sha256>  <path>': "
                + (f"{len(bad)} of its lines hold no sha256, the first for {bad[0]!r}" if bad else "it lists no file"))
    return MappingProxyType(rows)


@lru_cache(maxsize=1)
def _manifest() -> MappingProxyType:
    """name -> sha256 of MANIFEST (data/upstream/MANIFEST.sha256), read once per process."""
    return _read_manifest(MANIFEST)


def _manifest_name(path) -> str | None:
    """The name the manifest gives a file: its posix path under the deposit root machine.py resolved (UPSTREAM), as
    bootstrap_upstream.collect writes it ("publication/<part>/<file>"). None for a file outside that root. The
    path is compared as written: no link is followed."""
    try:
        return Path(os.path.abspath(path)).relative_to(os.path.abspath(UPSTREAM)).as_posix()
    except ValueError:
        return None


def _check_pin(path: str, raw: bytes) -> None:
    """Refuse when the manifest lists this result file with another sha256 than that of raw, the file's bytes. A
    file outside the deposit root, or one the manifest does not list, has no pin and passes."""
    name = _manifest_name(path)
    want = _manifest().get(name) if name is not None else None
    got = _sha256(raw)
    if want is not None and got != want:
        _refuse(f"the result file {_shown(Path(path))} has sha256 {got} and {_shown(MANIFEST)} lists {want} for "
                f"{name}: it is not the deposit's file")


@lru_cache(maxsize=None)
def _file(path: str) -> tuple:
    """(document, rows) of one result file from S374's load_rows; a row's position in rows is the index of its
    ledger key. Refused when the file is missing, when the manifest lists it with another sha256 (_check_pin), and
    when S374's reader cannot load it or cannot read the question and the answer of one of its rows."""
    p = Path(path)
    if not p.is_file():
        _refuse(f"the result file {_shown(p)} is missing (a deposit that is not on this machine: "
                f"uv run python scripts/bootstrap_upstream.py)")
    name = _manifest_name(path)
    try:
        if name is not None and name in _manifest():
            _check_pin(path, p.read_bytes())
        doc, rows = s374_load_rows(path)
        for dep in rows:                                 # question and answer read here, so that no later read raises
            if not isinstance(s374_qid(dep), str):
                raise TypeError("a row's question id is not text")
            s374_answer(dep)
    except (OSError, KeyError, TypeError, AttributeError, ValueError, RecursionError) as e:
        _refuse(f"the result file {_shown(p)} cannot be read by S374's reader ({type(e).__name__}: {e})")
    return doc, rows


@lru_cache(maxsize=None)
def _header_generator(path: str) -> str:
    """The gen_model of a JSONL result file's "_header" lines, which load_rows skips (s374/rows.py:14); refused
    unless every header names the same model."""
    models = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    d = json.loads(line)
                    if "_header" in d:
                        models.add(d["_header"].get("gen_model"))
    except (OSError, KeyError, TypeError, AttributeError, ValueError) as e:
        _refuse(f"the header lines of {_shown(Path(path))} cannot be read ({type(e).__name__}: {e})")
    if len(models) != 1 or not all(isinstance(m, str) for m in models):
        _refuse(f"{_shown(Path(path))}: its header lines name {sorted(map(str, models))} as gen_model, expected "
                f"one model")
    return next(iter(models))


def _answered(dep: dict) -> bool:
    """Whether the row's answer is text that is not blank: the text half of S373's test (S373_rejudge_v2.py:166),
    whose other half is that S373.KEY holds the question."""
    text = s374_answer(dep)
    return isinstance(text, str) and bool(text.strip())


def _item_config(dep: dict):
    """The config S373 stores in a ledger row for this deposit row (S373_rejudge_v2.py:168, :171)."""
    g = dep.get("generation") if isinstance(dep.get("generation"), dict) else {}
    return dep.get("config") or g.get("config") or dep.get("depth")


def _fields(exp: str, tag: str, path: str, doc, dep: dict) -> dict:
    """config, generator, draw, index, core, noise, depth and arm of one deposit row, by experiment (module
    docstring, ROW and ARM). where names the row in a refusal."""
    where = f"{tag} of {exp}, question {s374_qid(dep)}"
    f = {"config": None, "generator": s374_genmodel(dep, doc, path), "draw": None, "index": None, "core": None,
         "noise": None, "depth": None, "arm": ARM_OF.get(exp, REPORTED)}
    if exp in WITH_CONFIG:
        g = dep.get("generation") if isinstance(dep.get("generation"), dict) else {}
        f["config"] = dep.get("config") or g.get("config")
        if not isinstance(f["config"], str):
            _refuse(f"{where}: the row holds no config")
    elif exp == "exp07":
        f["config"] = dep.get("model_key")
        if not isinstance(f["config"], str):
            _refuse(f"{where}: the row holds no model_key")
    elif exp == "exp09":
        f["depth"] = dep.get("depth")
        if isinstance(f["depth"], bool) or not isinstance(f["depth"], int):
            _refuse(f"{where}: the row's depth is {f['depth']!r}, expected an integer")
    if exp in WITH_SCOPE:
        f["index"] = dep.get(INDEX_FIELD[exp])
        m = _INDEX.fullmatch(f["index"]) if isinstance(f["index"], str) else None
        if not m or int(m.group(1)) != key_scope.index_core_size(f["index"], strict=True):
            _refuse(f"{where}: the index name {f['index']!r} is not exp_v4_s<core>_n<noise>")
        f["core"], f["noise"] = int(m.group(1)), int(m.group(2))
    if exp == "exp05" and f["config"] == S314_CONFIG:
        f["arm"] = DEPOSIT_VP                            # the paper's rows of this strategy are s314's
    elif exp == "rep2":
        f["draw"] = REP2_DRAW
    elif exp == "rep5":
        base = tag
        for suffix in THINKOFF_SUFFIXES:
            if tag.endswith(suffix):
                base, f["arm"] = tag[:-len(suffix)], THINKING_OFF
        m = _DRAW.fullmatch(base)
        if not m or S141_campaign.arm_id(str(f["generator"]), int(m.group(2))) != base:
            _refuse(f"{where}: the folder name is not <generator>__draw<d> with or without a thinking-off suffix "
                    f"{sorted(THINKOFF_SUFFIXES)} for the generator {f['generator']!r}")
        f["draw"] = int(m.group(2))
    elif exp == "s314":
        f["config"], f["generator"] = S314_CONFIG, _header_generator(path)
        phase_mode = (dep.get("phase"), dep.get("mode"))
        if all(isinstance(x, str) for x in phase_mode) and phase_mode in S314_REPORTED:
            f["arm"] = REPORTED
        elif phase_mode[0] == S314_SMOKE:
            f["arm"] = SMOKE
        else:
            _refuse(f"{where}: phase and mode {phase_mode} are neither the reported run {sorted(S314_REPORTED)} "
                    f"nor a smoke test")
    if not isinstance(f["generator"], str) or not f["generator"]:
        _refuse(f"{where}: no generator in the row or its file")
    return f


# ---- the join ---------------------------------------------------------------------------------------------

def _resolve(key: str, question_id, answer_chars) -> tuple:
    """(label, tag, row index, result file, document, deposit row) of a ledger key, checked against the ledger
    row's question_id and answer_chars (module docstring, JOIN)."""
    parts = key.split("|")
    if len(parts) != 3 or not _ROW_INDEX.fullmatch(parts[2]):
        _refuse(f"key {key!r} resolves to no row: it is not <label>|<file tag>|<row index> (S373_rejudge_v2.py:170)")
    label, tag, i = parts[0], parts[1], int(parts[2])
    if label not in S388.LABEL_TO_SLUG:
        _refuse(f"key {key!r} resolves to no row: S388.LABEL_TO_SLUG does not hold its label")
    path = _paths().get((label, tag))
    if path is None:
        _refuse(f"key {key!r} resolves to no row: S374's file list holds no result file {tag!r} under that label "
                f"(a deposit that is not on this machine: uv run python scripts/bootstrap_upstream.py)")
    doc, rows = _file(path)
    if i >= len(rows):
        _refuse(f"key {key!r} resolves to no row: {tag} has {len(rows):,} rows")
    dep = rows[i]
    if s374_qid(dep) != question_id:
        _refuse(f"key {key!r} resolves to another question: the ledger row is on {question_id}, row {i} of {tag} "
                f"is on {s374_qid(dep)}")
    n = len(s374_answer(dep)) if _answered(dep) else 0
    if not _is_int(answer_chars) or n != answer_chars or not n:
        _refuse(f"key {key!r} resolves to another answer length: the ledger row scores {answer_chars} characters, "
                f"row {i} of {tag} holds {n}")
    return label, tag, i, path, doc, dep


def _score(key: str, group: str, status: str, scores, prompt_answerable) -> tuple:
    """(dimension, score, passed) of a ledger row by its group (module docstring, SCORE)."""
    dim = DIMENSION[group]
    if status not in OK:
        return dim, None, None
    if not isinstance(scores, dict):
        _refuse(f"key {key!r} has status {status} and no scores")
    v = scores.get(dim)
    if not _is_int(v) or not SCORE_MIN <= v <= SCORE_MAX:
        _refuse(f"key {key!r} is in the group {group} and needs {dim} as an integer {SCORE_MIN} to {SCORE_MAX}: its "
                f"scores hold {sorted(scores)} with {dim} {v!r} (judged with the "
                f"{'answerable' if prompt_answerable else 'decline'} prompt)")
    off = {k: x for k, x in scores.items() if x is not None and (not _is_int(x) or not SCORE_MIN <= x <= SCORE_MAX)}
    if off:
        _refuse(f"key {key!r}: its scores hold {off}, and a score is an integer {SCORE_MIN} to {SCORE_MAX} or null")
    return dim, v, v >= PASS_AT


def _row(r, slug: str, judge: str, ctx: _Context) -> Row:
    """The Row of one merged ledger row r, read from <slug>/<judge>.jsonl."""
    where = f"{slug}/{judge}.jsonl"
    if not isinstance(r, dict):
        _refuse(f"a row of the merged ledger {where} is not a JSON object; run: {REBUILD}")
    key = r.get("key")
    if not isinstance(key, str):
        _refuse(f"a row of the merged ledger {where} has no key; run: {REBUILD}")
    label, tag, i, path, doc, dep = _resolve(key, r.get("question_id"), r.get("answer_chars"))
    q, status = r["question_id"], r.get("status")
    if S388.LABEL_TO_SLUG[label] != slug:
        _refuse(f"key {key!r} is in {where} and its label belongs to {S388.LABEL_TO_SLUG[label]}")
    if (r.get("source") != tag or not _is_int(r.get("row")) or r.get("row") != i
            or r.get("config") != _item_config(dep)):
        _refuse(f"key {key!r}: the ledger row's source, row and config "
                f"{(r.get('source'), r.get('row'), r.get('config'))} are not the key's {(tag, i, _item_config(dep))}")
    if r.get("judge") != S373.JUDGES[judge]["model"]:
        _refuse(f"key {key!r} in {where} was judged by {r.get('judge')!r}, not {S373.JUDGES[judge]['model']!r}")
    if not isinstance(status, str):
        _refuse(f"key {key!r} in {where} has no status")
    if q in ctx.d7:
        _refuse(f"key {key!r} is on the D7 question {q}, which S388 rule 2 drops; run: {REBUILD}")
    if q not in ctx.answer_type:
        _refuse(f"key {key!r} is on {q}, which {S373.KEY.name} does not hold")
    if r.get("key_hash") != ctx.key_hash[q]:
        _refuse(f"key {key!r} was judged under another key hash of {q} ({r.get('key_hash')!r}, where "
                f"{S373.KEY.name} gives {ctx.key_hash[q]!r}), which S388 rule 3 drops; run: {REBUILD}")
    exp = _SHORT[label]
    f = _fields(exp, tag, path, doc, dep)
    group = GROUP_OF[ctx.answer_type[q]]
    dim, score, passed = _score(key, group, status, r.get("scores"), r.get("answerable"))
    return Row(experiment=exp, slug=slug, label=label, key=key, judge=judge, judge_model=r["judge"], question_id=q,
               answer_type=ctx.answer_type[q], group=group, config=f["config"], generator=f["generator"],
               draw=f["draw"], index=f["index"], core=f["core"], noise=f["noise"], depth=f["depth"], arm=f["arm"],
               in_scope=ctx.scope.row_in_scope(q, f["index"]) if exp in WITH_SCOPE else None,
               tag=tag, row=i, answer_chars=r["answer_chars"], status=status,
               scores=MappingProxyType(r["scores"]) if status in OK else None, dimension=dim, score=score,
               passed=passed)


def _parse_ledger(raw: bytes, name: str, slug: str, judge: str, meta: dict, rec: dict, ctx: _Context) -> dict:
    """S374 label -> the Rows of one merged ledger's bytes, in the file's order (sorted by key, S388:476). meta and
    rec are what S388's record gives the ledger under outputs and under experiments. Refused unless raw has meta's
    sha256 and row count, every line with text is a JSON object _row accepts, no key is on two rows, and the rows
    and the rows with a scoring status are rec's rows and scored."""
    shown = _shown(TREE / name)
    got = _sha256(raw)
    if got != meta["sha256"]:
        _refuse(f"the merged ledger {shown} changed after the folder was checked (sha256 {got[:12]}, "
                f"{PROVENANCE.name} records {meta['sha256'][:12]}); run: {REBUILD}")
    lines = [(at, x) for at, x in enumerate(raw.split(b"\n"), 1) if x.strip()]
    if len(lines) != meta["rows"]:
        _refuse(f"the merged ledger {shown} holds {len(lines):,} rows and {PROVENANCE.name} lists {meta['rows']:,} "
                f"for it; run: {REBUILD}")
    by_label: dict = defaultdict(list)
    seen: set = set()
    scored = 0
    for at, line in lines:
        try:
            r = json.loads(line)
        except (ValueError, RecursionError) as e:
            _refuse(f"line {at} of the merged ledger {shown} is not JSON ({type(e).__name__}: {e}); run: {REBUILD}")
        if not isinstance(r, dict):
            _refuse(f"line {at} of the merged ledger {shown} is not a JSON object; run: {REBUILD}")
        row = _row(r, slug, judge, ctx)
        if row.key in seen:
            _refuse(f"key {row.key!r} is on two rows of {name}; run: {REBUILD}")
        seen.add(row.key)
        by_label[row.label].append(row)
        scored += row.status in OK
    if (len(lines), scored) != (rec["rows"], rec["scored"]):
        _refuse(f"the merged ledger {shown} holds {len(lines):,} rows, {scored:,} of them scored, and "
                f"{PROVENANCE.name} records {rec['rows']:,} rows and {rec['scored']:,} scored answers for it under "
                f"experiments; run: {REBUILD}")
    return {label: tuple(rows) for label, rows in by_label.items()}


@lru_cache(maxsize=None)
def _ledger(slug: str, judge: str) -> dict:
    """S374 label -> the Rows of one merged ledger (_parse_ledger), on the bytes read here, parsed once per
    process."""
    ctx = _context()
    name = f"{slug}/{judge}.jsonl"
    try:
        raw = (TREE / name).read_bytes()
    except OSError as e:
        _refuse(f"the merged ledger {_shown(TREE / name)} cannot be read ({type(e).__name__}); run: {REBUILD}")
    return _parse_ledger(raw, name, slug, judge, ctx.provenance["outputs"][name],
                         ctx.provenance["experiments"][slug][judge], ctx)


# ---- the interface ----------------------------------------------------------------------------------------

def _label_of(experiment: str) -> str:
    if experiment in EXPERIMENTS:
        return EXPERIMENTS[experiment]
    if experiment in _SHORT:
        return experiment
    raise ValueError(f"no experiment {experiment!r}: the names are {', '.join(EXPERIMENTS)} (or an S374 label)")


def judges(experiment: str, partial: bool = False) -> tuple[str, ...]:
    """The judges with a merged ledger in the experiment's S388 folder whose every expected answer of that folder
    is scored in S388's record; with partial=True also the judges with a partial ledger. The record counts per
    folder: s141_mini, s141_timing, s314 and s357 share one."""
    ctx = _context()
    slug = S388.LABEL_TO_SLUG[_label_of(experiment)]
    cov = ctx.provenance["experiments"].get(slug, {})
    return tuple(j for j in sorted(cov) if f"{slug}/{j}.jsonl" in ctx.provenance["outputs"]
                 and (partial or cov[j]["scored"] == cov[j]["expected"]))


def _check_expected(exp: str, judge: str, name: str, folder: tuple, deposit: dict, ledger: dict,
                    folder_deposit: int, folder_expected: int) -> None:
    """Refuse unless deposit == ledger and folder_deposit == folder_expected. deposit: arm -> the answers the
    result files of exp hold on a question of the key that is not a D7 question. ledger: arm -> the rows of exp in
    the ledger name. folder_deposit: those answers summed over folder, the experiments the ledger holds rows of.
    folder_expected: the expected count S388's record gives the ledger's folder and judge. Every count is an
    argument, so the self-test calls it with altered counts."""
    if deposit != ledger:
        _refuse(f"the result files of {exp} hold {deposit or 'no'} answers per arm on the key's questions that are "
                f"not D7 questions, and the {judge} ledger {name}, which {PROVENANCE.name} gives as complete, holds "
                f"{ledger or 'no'} rows of {exp} per arm; run: {REBUILD}")
    if folder_deposit != folder_expected:
        _refuse(f"the result files of {', '.join(folder)} hold {folder_deposit:,} answers on the key's questions "
                f"that are not D7 questions, and {PROVENANCE.name} expects {folder_expected:,} for the {judge} "
                f"ledger {name}; run: {REBUILD}")


@lru_cache(maxsize=None)
def _check_complete(label: str, judge: str) -> None:
    """For a ledger S388's record gives as complete: the deposit's expected answers of the experiment per arm
    against the ledger's rows of it, and the same answers over the ledger's experiments against the record's
    expected count (_check_expected). Run once per experiment and judge."""
    slug = S388.LABEL_TO_SLUG[label]
    by_label = _ledger(slug, judge)
    held = [lab for lab in EXPERIMENTS.values() if lab in by_label]
    _check_expected(exp=_SHORT[label], judge=judge, name=f"{slug}/{judge}.jsonl",
                    folder=tuple(_SHORT[lab] for lab in held),
                    deposit=dict(_deposit_counts(label).expected),
                    ledger=dict(Counter(r.arm for r in by_label.get(label, ()))),
                    folder_deposit=sum(sum(_deposit_counts(lab).expected.values()) for lab in held),
                    folder_expected=_context().provenance["experiments"][slug][judge]["expected"])


def load(experiment: str, judge: str = MAIN_JUDGE, partial: bool = False) -> tuple[Row, ...]:
    """Every Row of one experiment (a name of EXPERIMENTS or its S374 label) and judge, every arm, in and out of
    scope, in the ledger's order. ValueError for an unknown experiment, for a judge with no ledger for it, and
    for a ledger with fewer scored rows than expected answers unless partial=True. For a ledger that is not
    partial, a SystemExit when the deposit's expected answers differ from the ledger's rows per arm or from the
    record's expected count (_check_complete). The tuple is cached: a second call returns the same object."""
    label = _label_of(experiment)
    slug = S388.LABEL_TO_SLUG[label]
    have = judges(experiment, partial=True)
    if judge not in have:
        raise ValueError(f"no merged ledger of judge {judge!r} for {_SHORT[label]}: its judges are {', '.join(have) or 'none'}")
    complete = judge in judges(experiment)
    if not complete and not partial:
        cov = _context().provenance["experiments"][slug][judge]
        raise ValueError(f"the {judge} ledger of {slug} is partial ({cov['scored']:,} of {cov['expected']:,} expected "
                         f"answers scored); pass partial=True to read it")
    rows = _ledger(slug, judge).get(label, ())
    if complete:
        _check_complete(label, judge)
    return rows


def load_all(judge: str = MAIN_JUDGE, partial: bool = False) -> tuple[Row, ...]:
    """The Rows of every experiment this judge has a ledger for, every arm, in the order of EXPERIMENTS.
    ValueError for a judge S373.JUDGES does not hold, for a judge with no merged ledger, and, without
    partial=True, for a judge with a partial ledger for any experiment (the message names them): the call returns
    every experiment the judge has a ledger for, or none."""
    if judge not in S373.JUDGES:
        raise ValueError(f"no judge {judge!r}: the judges are {', '.join(S373.JUDGES)}")
    have = [exp for exp in EXPERIMENTS if judge in judges(exp, partial=True)]
    if not have:
        raise ValueError(f"judge {judge!r} has no merged ledger")
    part = [exp for exp in have if judge not in judges(exp)]
    if part and not partial:
        raise ValueError(f"judge {judge!r} has a partial ledger for {', '.join(part)}; pass partial=True to read "
                         f"them, or call load() for the other experiments")
    return tuple(r for exp in have for r in load(exp, judge, partial=partial))


def reported(experiment: str, judge: str = MAIN_JUDGE, arm: str = REPORTED, partial: bool = False) -> Selection:
    """The rows of one arm (REPORTED unless named) that are not out of scope under Q55 and carry a score, with the
    count each rule left out (Selection). In exp05 the arm REPORTED holds every strategy but verified_pass:
    corpus_scaling_reported() adds the rows the paper reports for that strategy. ValueError when the experiment
    has no row in that arm; the message lists its arms (s141_mini, s141_timing and s357 are one arm each: mini,
    timing, gemini)."""
    rows = load(experiment, judge, partial=partial)
    label = _label_of(experiment)
    exp = _SHORT[label]
    arms = Counter(r.arm for r in rows)
    if arm not in arms:
        raise ValueError(f"{exp} has no row in the arm {arm!r}: its arms are {dict(arms)}")
    left = {f"arm {a}": n for a, n in sorted(arms.items()) if a != arm}
    if exp in WITH_SCOPE:
        left[OUT_OF_SCOPE] = 0
    left[NOT_SCORED] = 0
    kept = []
    for r in rows:
        if r.arm != arm:
            continue
        if r.in_scope is False:
            left[OUT_OF_SCOPE] += 1
        elif r.status not in OK:
            left[NOT_SCORED] += 1
        else:
            kept.append(r)
    cov = _context().provenance["experiments"][S388.LABEL_TO_SLUG[label]][judge]
    return Selection(experiment=exp, judge=judge, arm=arm, rows=tuple(kept), total=len(rows), left_out=left,
                     d7_answers=deposit_counts(exp).d7.get(arm, 0),
                     partial_coverage=None if cov["scored"] == cov["expected"] else (cov["scored"], cov["expected"]))


def paired(experiment: str, first: str = MAIN_JUDGE, second: str = SECOND_JUDGE, arm: str | None = REPORTED,
           partial: bool = False) -> Pairs:
    """The rows of two judges on the same ledger key, for the two replications (rep2, rep5; any experiment both
    judges have a ledger for). With arm named, each side is reported(experiment, judge, arm).rows, so the arm,
    scope and score rules apply to both, and the rows those rules left out on each side are carried in
    left_out_first and left_out_second; with arm=None each side is load(experiment, judge). Both rows of a
    pair come from one deposit row; a pair with two questions or two answer lengths is a SystemExit."""
    def side(judge: str) -> tuple:
        if arm is None:
            return {r.key: r for r in load(experiment, judge, partial)}, None
        sel = reported(experiment, judge, arm, partial)
        return {r.key: r for r in sel.rows}, dict(sel.left_out)
    (a, left_a), (b, left_b) = side(first), side(second)
    for k in a.keys() & b.keys():
        if (a[k].question_id, a[k].answer_chars) != (b[k].question_id, b[k].answer_chars):
            _refuse(f"key {k!r} names two answers: {first} {(a[k].question_id, a[k].answer_chars)}, {second} "
                    f"{(b[k].question_id, b[k].answer_chars)}")
    return Pairs(experiment=_SHORT[_label_of(experiment)], first=first, second=second, arm=arm,
                 pairs=tuple((a[k], b[k]) for k in a if k in b),
                 only_first=tuple(r for k, r in a.items() if k not in b),
                 only_second=tuple(r for k, r in b.items() if k not in a),
                 left_out_first=left_a, left_out_second=left_b)


def _check_same_pairs(deposit: Counter, rerun: Counter, judge: str) -> None:
    """Refuse unless the two counters of (index, question) pairs hold the same pairs, each once. deposit: the
    judged exp05 rows of the arm DEPOSIT_VP. rerun: the judged s314 rows of the arm REPORTED."""
    off = sum(1 for k in deposit.keys() | rerun.keys() if (deposit[k], rerun[k]) != (1, 1))
    if off:
        _refuse(f"corpus scaling, judge {judge}: the S314 rerun's judged rows of the arm {REPORTED} are on "
                f"{len(rerun):,} (index, question) pairs ({sum(rerun.values()):,} rows) and the deposit's judged "
                f"{S314_CONFIG} rows of exp05 on {len(deposit):,} ({sum(deposit.values()):,} rows); {off:,} pairs "
                f"are not on one row of each, so the rerun does not stand in for the deposit's arm pair by pair")


def corpus_scaling_reported(judge: str = MAIN_JUDGE) -> CorpusScaling:
    """What the paper reports for corpus scaling, in one call: reported("exp05", judge).rows, which hold every
    strategy but verified_pass, followed by reported("s314", judge).rows, with both Selections and one statement
    of the two. The verified_pass rows come from the S314 rerun and not from the deposit's exp05 file
    (exp05_final.py:1-8: Valerio adopted the rerun on 28 September). A SystemExit unless the rerun's judged rows of
    the arm REPORTED and the deposit's judged verified_pass rows (exp05, arm DEPOSIT_VP) are on the same
    (index, question) pairs, one row each (_check_same_pairs); the scope and score rules of reported() then apply
    to the rerun's rows. ValueError when the judge has no complete ledger for one of the two experiments."""
    exp05, s314 = reported("exp05", judge), reported("s314", judge)
    deposit = Counter((r.index, r.question_id) for r in load("exp05", judge) if r.arm == DEPOSIT_VP)
    rerun = Counter((r.index, r.question_id) for r in load("s314", judge) if r.arm == REPORTED)
    _check_same_pairs(deposit, rerun, judge)
    return CorpusScaling(judge=judge, rows=exp05.rows + s314.rows, exp05=exp05, s314=s314,
                         verified_pass_pairs=len(rerun))


def d7_questions() -> frozenset:
    """The questions dropped under D7: AS_V1's dropped_d7 (empty once D9 reverses D7 in the key file)."""
    return _context().d7


@lru_cache(maxsize=None)
def _deposit_counts(label: str) -> DepositCount:
    ctx = _context()
    exp = _SHORT[label]
    n = no_answer = not_in_key = 0
    d7: Counter = Counter()
    expected: Counter = Counter()
    for (lab, tag), path in _paths().items():
        if lab != label:
            continue
        doc, rows = _file(path)
        for dep in rows:
            n += 1
            q = s374_qid(dep)
            if not _answered(dep):
                no_answer += 1
            elif q not in ctx.answer_type:
                not_in_key += 1
            else:
                (d7 if q in ctx.d7 else expected)[_fields(exp, tag, path, doc, dep)["arm"]] += 1
    return DepositCount(experiment=exp, rows=n, no_answer=no_answer, not_in_key=not_in_key,
                        d7=MappingProxyType(dict(d7)), expected=MappingProxyType(dict(expected)))


def deposit_counts(experiment: str) -> DepositCount:
    """Counts over one experiment's result files, read through S374's reader and no ledger: the rows, the rows
    with no answer, the answers on a question the key lacks, the answers on D7 questions per arm (what the merged
    ledgers leave out under S388 rule 2) and, per arm, the answers on the key's other questions (expected: the
    answers a complete ledger holds one row for). The fields d7 and expected are read-only views of cached dicts;
    dict(view) is a copy."""
    return _deposit_counts(_label_of(experiment))


# ---- self-test --------------------------------------------------------------------------------------------

# Expected values, valid under the key whose v1-format file (S373.AS_V1) has this sha256 and with D7 in force
# (13 October 2026). Under another key the gates that use them fail with that reason, and they are recounted.
# Per-experiment totals are not typed here: they are S388.KNOWN_LABEL.
EXPECTED_UNDER_KEY = "e971de522df6fab54a070e44736b6cb28a5ebd26bab07ca9e1513230bb86f4ef"
EXPECTED = {
    "devstral_rows": 32294,
    "exp04_groups": {ANSWERABLE: 516, NOT_ANSWERABLE: 231, REFUTATION: 60},
    "gptoss": {"rep2": 809, "rep5": 12878},
    "arms": {"exp05": {REPORTED: 8067, DEPOSIT_VP: 1629}, "rep5": {REPORTED: 11946, THINKING_OFF: 932},
             "s314": {REPORTED: 1629, SMOKE: 18}, "s141_mini": {MINI: 2390}, "s141_timing": {TIMING: 298},
             "s357": {GEMINI: 180}},
    "smoke_core": {50: 18},
    "out_of_scope": {"exp05": {5: 90, 10: 54}, "s314": {5: 15, 10: 9}},   # notes/DECISIONS_2026-10-12.md:35-36
    "d7_answers": {"exp05": 198, "s314": 33},                             # key_scope.py K7 and K8
    "d7_answers_total": 693,                                              # notes/DECISIONS_2026-10-12.md:53
}
SEVERAL_ARMS = ("exp05", "rep5", "s314")             # the experiments of EXPECTED["arms"] with two arms


def _gate(fails: list, name: str, ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<4}{msg}")
    if not ok:
        fails.append(name)


def _refusal(fn, *needles: str, exc=SystemExit) -> bool:
    """True when fn() raises exc with every needle in its message."""
    try:
        fn()
    except exc as e:
        return all(n in str(e) for n in needles)
    return False


def _git(*args: str):
    """A git command on this repository that writes nothing: the finished process, or the reason git gave no
    answer."""
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, timeout=120,
                              stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"git gave no answer ({type(e).__name__})"


def _rel(paths: list) -> list | None:
    """The paths relative to the repository, or None when one of them is outside it."""
    try:
        return [Path(os.path.abspath(p)).relative_to(ROOT).as_posix() for p in paths]
    except ValueError:
        return None


def _at_head(paths: list) -> tuple:
    """(True, False or None, text): whether each working-tree file is its blob at HEAD, by git ls-tree and
    git hash-object, which write nothing. None when git gives no answer or a file is outside the repository."""
    rel = _rel(paths)
    if rel is None:
        return None, "a file is outside the repository"
    tree, work = _git("ls-tree", "-r", "HEAD", "--", *rel), _git("hash-object", "--", *rel)
    for r in (tree, work):
        if isinstance(r, str) or r.returncode:
            return None, r if isinstance(r, str) else f"git gave no answer (exit {r.returncode})"
    head = {ln.split("\t", 1)[1]: ln.split()[2] for ln in tree.stdout.decode().splitlines() if "\t" in ln}
    mine = dict(zip(rel, work.stdout.decode().split()))
    differ = sorted(p for p in rel if head.get(p) != mine.get(p))
    return not differ, f"{len(rel) - len(differ)} of {len(rel)} files are their blob at HEAD" + (
        f"; not: {differ[:3]}" if differ else "")


def _record_at_head(prov: dict) -> tuple:
    """(True, False or None, text): S388's record as parsed against its blob at HEAD as parsed (git show), block by
    block, without _provenance["generated"], the time S388 writes on every run (S388:493). False when a block
    differs or HEAD holds no blob for the file; None when git gives no answer."""
    rel = _rel([PROVENANCE])
    if rel is None:
        return None, "the record is outside the repository"
    listed, shown = _git("ls-tree", "HEAD", "--", rel[0]), _git("show", f"HEAD:{rel[0]}")
    if isinstance(listed, str) or listed.returncode:
        return None, listed if isinstance(listed, str) else f"git gave no answer (exit {listed.returncode})"
    if not listed.stdout.strip() or isinstance(shown, str) or shown.returncode:
        return False, "HEAD holds no blob for it"
    try:
        head = json.loads(shown.stdout)
    except ValueError:
        return False, "its blob at HEAD is not JSON"

    def blocks(doc) -> dict:
        return {k: ({a: b for a, b in v.items() if a != "generated"} if k == "_provenance" and isinstance(v, dict)
                    else v) for k, v in doc.items()} if isinstance(doc, dict) else {}
    mine, theirs = blocks(prov), blocks(head)
    names = sorted(mine.keys() | theirs.keys())
    differ = [k for k in names if mine.get(k, _ABSENT) != theirs.get(k, _ABSENT)]
    return not differ, f"{len(names) - len(differ)} of {len(names)} blocks equal; blocks that differ: {differ or 'none'}"


def _tracked(paths: list) -> set | None:
    """The paths git tracks (git ls-files, which writes nothing), relative to the repository; None when git gives
    no answer."""
    rel = _rel(paths)
    if not paths:
        return set()
    if rel is None:
        return None
    r = _git("ls-files", "-z", "--", *rel)
    if isinstance(r, str) or r.returncode:
        return None
    return {p for p in r.stdout.decode().split("\0") if p}


def _s393_gates(fails: list) -> None:
    """S0 to S9: S393's merge, Resolver and new_tables on this machine's committed S373 ledgers, against the
    loader. S393 is imported here and nowhere else in this module."""
    import inspect
    import S393_early_claims as S393
    ctx = _context()
    hashes = dict(ctx.key_hash)
    unused = TREE / "not_created"       # S393.ledgers uses its tmp argument on the scp path only (:265-284)
    files = {j: S393.ledgers(j, False, unused)[0] for j in (MAIN_JUDGE, SECOND_JUDGE)}
    read = {Path(f["file"]).name: f["sha256"] for fs in files.values() for f in fs}
    merged_in = {n: rec["sha256"] for n, rec in ctx.provenance["inputs"].items() if rec["role"] == "production"
                 and rec["judge"] in files}
    head_ok, head_msg = _at_head([RECOMPUTE / n for n in sorted(read)])
    _gate(fails, "S0", read == merged_in and head_ok is not False,
          f"S393.ledgers(judge, remote=False) read {len(read)} production ledgers of {MAIN_JUDGE} and "
          f"{SECOND_JUDGE} on this machine: the same files and sha256 as S388's inputs: {read == merged_in}; "
          f"{head_msg}")

    scored = {j: {r.key: r for r in load_all(j) if r.status in OK} for j in files}
    best, s1_ok, s1_msg = {}, True, []
    for j in files:
        best[j], _counts_by_rule, conflicts = S393.merge(files[j], hashes, set(ctx.d7))
        mine = scored[j]
        both = best[j].keys() & mine.keys()
        equal = sum(1 for k in both if best[j][k]["scores"] == mine[k].scores
                    and best[j][k]["question_id"] == mine[k].question_id
                    and best[j][k]["answer_chars"] == mine[k].answer_chars)
        s1_ok &= set(best[j]) == set(mine) and equal == len(both) and not conflicts
        s1_msg.append(f"{j}: {len(best[j]):,} scored answers, loader {len(mine):,} scored rows, the same keys: "
                      f"{set(best[j]) == set(mine)}, scores, question and answer length equal on {equal:,} of "
                      f"{len(both):,}, {len(conflicts)} conflicts")
    _gate(fails, "S1", s1_ok, "S393.merge against every scored loader row. " + "; ".join(s1_msg))

    res = S393.Resolver()
    T, drop, G = S393.new_tables(best[MAIN_JUDGE], best[SECOND_JUDGE], res)
    thr = inspect.signature(S393._pmap).parameters["thr"].default      # S393's pass threshold, read from its code
    derived = "pass flag (S393's score at S393's threshold)"            # S393's tables of S2 to S5 hold no flag

    def theirs_passed(e: dict) -> bool:
        return (e["cor"] if e["ans"] else e["ref"]) >= thr

    def compare(name: str, sel: Selection, theirs: dict, mine: dict, twice: int, outside: Counter, what: str) -> None:
        """One gate: S393's units against the loader's, and every other loader row counted by its reason."""
        both = theirs.keys() & mine.keys()
        differ = [u for u in theirs.keys() ^ mine.keys()] + [u for u in both if theirs[u] != mine[u]]
        outside = Counter({rule: n for rule, n in sel.left_out.items() if n}) + outside
        every = len(mine) + sum(outside.values()) == sel.total
        ok = not differ and not twice and every
        _gate(fails, name, ok,
              f"{sel.experiment}: units S393 {len(theirs):,}, loader {len(mine):,}, in both {len(both):,}, equal "
              f"{len(both) - sum(1 for u in differ if u in both):,} ({what}); {twice} units named twice; "
              f"{sum(outside.values()):,} loader rows are in no S393 table: {dict(outside) or 'none'}; units and "
              f"these rows are the loader's {sel.total:,} rows: {every}"
              + ("" if not differ else f"; first units that differ: {differ[:3]}"))

    # exp04 and exp06: every group; the ten in S393's own group G for the configurations of its TEN_CFG
    for name, exp in (("S2", "exp04"), ("S3", "exp06")):
        sel = reported(exp)
        theirs = {("table", u): {**e, "passed": theirs_passed(e)} for u, e in T[exp].items()}
        theirs.update({("ten", u): {**e, "passed": theirs_passed(e)} for u, e in G[exp].items()})
        mine, twice, outside = {}, 0, Counter()
        for r in sel.rows:
            if r.group == REFUTATION and r.config not in S393.TEN_CFG[exp]:
                outside[f"the ten, {r.config} (used by no claim of S393)"] += 1
                continue
            ans = r.group != NOT_ANSWERABLE
            u = ("ten" if r.group == REFUTATION else "table", (r.config, r.question_id))
            twice += u in mine
            mine[u] = {"ans": ans, "chars": r.answer_chars, "cor": r.score if ans else None,
                       "fai": r.scores.get("faithfulness") if ans else None,
                       "ref": None if ans else r.score, "passed": r.passed}
        compare(name, sel, theirs, mine, twice, outside,
                f"correctness, faithfulness, refusal score, answer length, {derived}; the ten in S393's own group")

    # exp05: S393 keeps the answerable rows off the ten of every strategy but verified_pass, correctness only.
    # reported("exp05") holds no verified_pass row: the deposit's arm is among the rows it left out
    sel = reported("exp05")
    theirs = {u: {**e, "passed": e["cor"] >= thr} for u, e in T["exp05"].items()}
    mine, twice, outside = {}, 0, Counter()
    for r in sel.rows:
        if r.group != ANSWERABLE:
            outside[f"group {r.group}"] += 1
        else:
            u = (str(r.core), str(r.noise), r.config, r.question_id)
            twice += u in mine
            mine[u] = {"ans": True, "cor": r.score, "passed": r.passed}
    compare("S4", sel, theirs, mine, twice, outside, f"correctness, {derived}")

    sel = reported("naive")
    theirs = {u: {**e, "passed": e["cor"] >= thr} for u, e in T["naive"].items()}
    mine, twice, outside = {}, 0, Counter()
    for r in sel.rows:
        if r.group != ANSWERABLE:
            outside[f"group {r.group}"] += 1
        else:
            twice += r.question_id in mine
            mine[r.question_id] = {"ans": True, "chars": r.answer_chars, "cor": r.score, "passed": r.passed}
    compare("S5", sel, theirs, mine, twice, outside, f"correctness, answer length, {derived}")

    # exp09: S393 keeps the gemini-3-flash file at the depths of its DEPTHS, as a pass flag
    sel = reported("exp09")
    mine, twice, outside = {}, 0, Counter()
    for r in sel.rows:
        if r.generator.split("::")[-1] != S393.REF:
            outside["another generator's depth file"] += 1
        elif r.group != ANSWERABLE:
            outside[f"group {r.group}"] += 1
        elif r.depth not in S393.DEPTHS:
            outside[f"{S393.REF} at a depth outside S393.DEPTHS"] += 1
        else:
            twice += (r.depth, r.question_id) in mine
            mine[(r.depth, r.question_id)] = {"ans": True, "chars": r.answer_chars, "p3": int(r.passed)}
    compare("S6", sel, dict(T["exp09"]), mine, twice, outside, f"pass flag, answer length; {S393.REF} file")

    # the two replications: S393 keeps the answerable rows off the ten, both judges' pass flags per unit
    two = set(S393.TWO_FILES.values())
    for name, exp in (("S7", "rep2"), ("S8", "rep5")):
        sel = reported(exp)
        second = {a.key: b for a, b in paired(exp).pairs}
        theirs = {u: e for u, e in T["rep"].items() if (u[0] in two) == (exp == "rep2")}
        mine, twice, outside = {}, 0, Counter()
        for r in sel.rows:
            if r.group != ANSWERABLE:
                outside[f"group {r.group}"] += 1
                continue
            gen = S393.TWO_FILES[r.tag] if exp == "rep2" else res.arm2gen[r.tag.rsplit("__draw", 1)[0]]
            u = (gen, r.draw, r.config, r.question_id)
            twice += u in mine
            b = second.get(r.key)                    # a unit the second judge has no scored row for holds None
            mine[u] = {"ans": True, "chars": r.answer_chars, "main": int(r.passed),
                       "second": None if b is None else int(b.passed)}
        compare(name, sel, theirs, mine, twice, outside,
                f"pass flag of {MAIN_JUDGE} and of {SECOND_JUDGE}, answer length")

    # S9: the scored rows S393 maps to no table, in its own buckets, predicted from the loader's fields
    want: Counter = Counter()
    for j, tag in ((MAIN_JUDGE, "main"), (SECOND_JUDGE, "second")):
        for r in scored[j].values():
            if r.label not in S393.LABELS:
                want[f"{tag}: source not used here: {r.label}"] += 1
            elif r.experiment == "exp09" and r.generator.split("::")[-1] != S393.REF:
                want[f"{tag}: depth sweep, not gemini-3-flash"] += 1
            elif r.arm == THINKING_OFF:
                want[f"{tag}: replication side arm (thinking off)"] += 1
            elif r.group == REFUTATION:
                grouped = r.experiment in S393.TEN_CFG and r.config in S393.TEN_CFG[r.experiment]
                want[f"{tag}: on one of the ten (Q51), " + ("their own group" if grouped else "used by no claim")] += 1
    _gate(fails, "S9", dict(want) == dict(drop),
          f"S393's rows mapped to no table, {sum(drop.values()):,} in {len(drop)} buckets, equal the loader's "
          f"prediction bucket by bucket: {dict(want) == dict(drop)}"
          + ("" if dict(want) == dict(drop) else f"; S393 {dict(drop)}; loader {dict(want)}"))


def self_test() -> int:
    fails: list = []
    ctx = _context()
    prov, outputs, sc = ctx.provenance, ctx.provenance["outputs"], ctx.scope
    current = sc.sha256 == EXPECTED_UNDER_KEY
    version = prov["_provenance"].get("key_version")
    print(f"judged_ledger self-test: key {_shown(S373.KEY)} v{version} ({ctx.key_sha256[:12]}), v1 format "
          f"{sc.sha256[:12]}; merged ledgers {_shown(TREE)}")
    if not current:
        print(f"  the expected values below were written under key {EXPECTED_UNDER_KEY[:12]}: the gates that use "
              f"them fail until they are recounted")
    print("  experiments (name = S388 folder, S374 label): "
          + "; ".join(f"{e} = {S388.LABEL_TO_SLUG[lab]}, {lab}" for e, lab in EXPERIMENTS.items()))

    as_v1 = _read_json(S373.AS_V1, "the v1-format key")
    field = f"source_v{str(version).replace('.', '')}_sha256"
    v1_ok = sc.sha256 == key_scope.KEY_SHA256 == prov["_provenance"].get("as_v1_sha256")
    key_ok = as_v1.get(field) == ctx.key_sha256 == prov["_provenance"].get("key_sha256")
    one_file = key_scope.KEY.resolve() == S373.AS_V1.resolve()
    _gate(fails, "J1", v1_ok and key_ok and one_file,
          f"{S373.AS_V1.name} sha256 {sc.sha256[:12]} = key_scope.KEY_SHA256 = S388's record: {v1_ok}; "
          f"{S373.KEY.name} {ctx.key_sha256[:12]} = AS_V1's {field} = S388's record: {key_ok}; key_scope and S373 "
          f"read one v1-format file: {one_file}; its D7 set holds {len(ctx.d7)} questions")

    n_rows = {name: sum(1 for x in (TREE / name).read_bytes().split(b"\n") if x.strip()) for name in outputs}
    sha_ok = all(_sha256((TREE / name).read_bytes()) == meta["sha256"] for name, meta in outputs.items())
    rows_ok = all(n_rows[n] == m["rows"] for n, m in outputs.items())
    head_ok, head_msg = _record_at_head(prov)
    passes = prov["final"].get("passes") is True
    _gate(fails, "J2", sha_ok and rows_ok and head_ok is not False and passes,
          f"{len(outputs)} merged ledgers, {sum(n_rows.values()):,} rows: sha256 equal {PROVENANCE.name}: {sha_ok}; "
          f"row counts equal it: {rows_ok}; that json against its blob at HEAD, both parsed, without "
          f"_provenance.generated: {head_msg}; final.passes is true: {passes}")

    # J3: refusals. Altered copies of S388's record, of a ledger and of its rows, in memory; nothing is written
    slug, judge = S388.LABEL_TO_SLUG[EXPERIMENTS["naive"]], MAIN_JUDGE      # a small ledger with every group
    small = f"{slug}/{judge}.jsonl"
    small_raw = (TREE / small).read_bytes()
    lines = [json.loads(x) for x in small_raw.split(b"\n") if x.strip()]
    raw = next(r for r in lines if GROUP_OF[ctx.answer_type[r["question_id"]]] == ANSWERABLE)
    na = next(r for r in lines if GROUP_OF[ctx.answer_type[r["question_id"]]] == NOT_ANSWERABLE)
    label, tag, i = raw["key"].split("|")
    other_q = next(q for q in sc.records if q != raw["question_id"])
    dim = DIMENSION[ANSWERABLE]
    meta, rec = outputs[small], prov["experiments"][slug][judge]
    partial_name = f"{S388.LABEL_TO_SLUG[EXPERIMENTS['exp04']]}/qwen.jsonl"
    this = Path(__file__)                                                    # a file that is neither JSON nor a manifest
    absent = TREE.with_name(TREE.name + "_absent")
    exp05_file = next(p for (lab, _t), p in _paths().items() if lab == EXPERIMENTS["exp05"])
    exp05_pin = _manifest().get(_manifest_name(exp05_file) or "", "no pin")
    other_bytes = b"not the deposit's bytes"
    not_json = small_raw.replace(b"\n", b"\n{ not json\n", 1)               # its second line is not JSON
    bad_scores = (7, -1, 2.9, float("nan"), True)

    def row(**change):
        return lambda: _row({**raw, **change}, slug, judge, ctx)

    def parse(data: bytes, meta_change: dict | None = None, rec_change: dict | None = None):
        return lambda: _parse_ledger(data, small, slug, judge, {**meta, "sha256": _sha256(data), **(meta_change or {})},
                                     {**rec, **(rec_change or {})}, ctx)

    def expected(**change):
        counts = {"deposit": {REPORTED: 10}, "ledger": {REPORTED: 10}, "folder_deposit": 10, "folder_expected": 10}
        return lambda: _check_expected("naive", judge, small, ("naive",), **{**counts, **change})

    refusals = {
        "missing folder": _refusal(lambda: _check_tree(absent, outputs), absent.name, REBUILD),
        "missing ledger": _refusal(lambda: _check_tree(TREE, {**outputs, f"{slug}/absent.jsonl": outputs[small]}),
                                   f"{slug}/absent.jsonl", REBUILD),
        "ledger with another hash": _refusal(lambda: _check_tree(TREE, {small: {**meta, "sha256": "0" * 64}}),
                                             small, REBUILD),
        "ledger changed after the folder check": _refusal(
            lambda: _parse_ledger(small_raw + b"\n", small, slug, judge, meta, rec, ctx), small, "changed"),
        "ledger rows off the record's": _refusal(parse(small_raw, {"rows": meta["rows"] + 1}), small,
                                                 f"lists {meta['rows'] + 1:,}"),
        "ledger scored rows off the record's": _refusal(parse(small_raw, None, {"scored": rec["scored"] - 1}), small,
                                                        f"{rec['scored'] - 1:,} scored"),
        "ledger line that is not JSON": _refusal(parse(not_json, {"rows": meta["rows"] + 1}), small, "line 2",
                                                 "not JSON"),
        "record that is not JSON": _refusal(lambda: _read_json(this, "S388's record"), this.name, "not readable"),
        "record without a block": _refusal(lambda: _check_record({k: v for k, v in prov.items() if k != "final"}),
                                           PROVENANCE.name, "final"),
        "record output without its counts": _refusal(
            lambda: _check_record({**prov, "experiments": {k: v for k, v in prov["experiments"].items() if k != slug}}),
            PROVENANCE.name, small),
        "key file without its records": _refusal(lambda: _key_tables({"version": "0"}), S373.KEY.name, "records"),
        "manifest that is not one": _refusal(lambda: _read_manifest(this), this.name, "not a manifest"),
        "missing result file": _refusal(lambda: _file(str(absent / "results.json")), "results.json", "missing"),
        "result file with another sha256": _refusal(lambda: _check_pin(exp05_file, other_bytes),
                                                    Path(exp05_file).name, _sha256(other_bytes), exp05_pin),
        "key beyond the file": _refusal(row(key=f"{label}|{tag}|99999999", row=99999999),
                                        f"{label}|{tag}|99999999", "no row"),
        "key of no file": _refusal(row(key=f"{label}|absent.json|{i}"), f"{label}|absent.json|{i}", "no row"),
        "key index with a leading zero": _refusal(row(key=f"{label}|{tag}|0{i}"), f"{label}|{tag}|0{i}", "no row"),
        "another question": _refusal(row(question_id=other_q), raw["key"], "another question"),
        "another answer length": _refusal(row(answer_chars=raw["answer_chars"] + 1), raw["key"],
                                          "another answer length"),
        "another key hash": _refusal(row(key_hash="0" * 16), raw["key"], "another key hash"),
        "row without a status": _refusal(lambda: _row({k: v for k, v in raw.items() if k != "status"}, slug, judge,
                                                      ctx), raw["key"], "no status"),
        "dimension absent": _refusal(row(scores={k: v for k, v in raw["scores"].items() if k != dim}), raw["key"],
                                     dim),
        "dimension null": _refusal(row(scores={**raw["scores"], dim: None}), raw["key"], dim),
        "the other prompt's scores": _refusal(lambda: _row({**na, "scores": raw["scores"]}, slug, judge, ctx),
                                              na["key"], DIMENSION[NOT_ANSWERABLE]),
        f"score that is not an integer {SCORE_MIN} to {SCORE_MAX} ({len(bad_scores)} values)": all(
            _refusal(row(scores={**raw["scores"], dim: v}), raw["key"], f"{dim} {v!r}") for v in bad_scores),
        "another dimension that is not an integer or null": all(
            _refusal(row(scores={**raw["scores"], "faithfulness": v}), raw["key"], "faithfulness")
            for v in (9, "high", 2.5, True)),
        "row index that is not an integer": _refusal(row(row=float(raw["row"])), raw["key"],
                                                     "source, row and config"),
        "record that contradicts itself": _refusal(
            lambda: _check_record({**prov, "experiments": {**prov["experiments"], slug: {
                **prov["experiments"][slug], judge: {**rec, "expected": rec["expected"] + 1}}}}),
            PROVENANCE.name, "contradicts itself", slug),
        "deposit answers off the ledger's rows": _refusal(expected(deposit={REPORTED: 11}), small, "11"),
        "deposit answers off the record's expected": _refusal(expected(folder_expected=11), PROVENANCE.name, "11"),
        "rerun rows off the deposit's pairs": _refusal(
            lambda: _check_same_pairs(Counter({("exp_v4_s5_n0", "a"): 1}), Counter({("exp_v4_s5_n0", "b"): 1}), judge),
            "S314", "2 pairs"),
    }
    errors = {
        "partial ledger without partial=True": _refusal(lambda: load("exp04", "qwen"), "partial=True", exc=ValueError)
        and len(load("exp04", "qwen", partial=True)) == outputs[partial_name]["rows"],
        "judge with no ledger": _refusal(lambda: load("exp04", SECOND_JUDGE), "no merged ledger", exc=ValueError),
        "unknown experiment": _refusal(lambda: load("exp99"), "no experiment", exc=ValueError),
        "arm an experiment lacks": _refusal(lambda: reported("s141_mini"), "its arms are", exc=ValueError),
        "load_all of an unknown judge": _refusal(lambda: load_all("nobody"), "no judge 'nobody'", exc=ValueError),
        "load_all of a judge with a partial ledger": _refusal(lambda: load_all("qwen"), "'qwen'", "partial=True",
                                                              exc=ValueError),
    }
    unscored = _row({**raw, "status": "error", "scores": None}, slug, judge, ctx)       # no refusal: a row to count
    no_score = (unscored.scores, unscored.score, unscored.passed) == (None, None, None)
    _gate(fails, "J3", all(refusals.values()) and all(errors.values()) and no_score,
          f"{sum(refusals.values())} of {len(refusals)} refusals raised as a SystemExit holding the file, key, count "
          f"or value looked for"
          + ("" if all(refusals.values()) else f" (not: {[k for k, v in refusals.items() if not v]})")
          + f"; {sum(errors.values())} of {len(errors)} wrong arguments raised a ValueError holding its text"
          + ("" if all(errors.values()) else f" (not: {[k for k, v in errors.items() if not v]})")
          + f"; a row with status error is read with scores, score and passed None: {no_score}")

    # J4: the group field
    v24 = {r["id"]: r for r in json.loads(S373.KEY.read_text(encoding="utf-8"))["records"]}
    types = Counter(r["answer_type"] for r in v24.values())
    in_as = Counter(GROUP_OF[v24[q]["answer_type"]] for q in sc.records)
    ten = {q for q, r in v24.items() if r["answer_type"] == "refutation"}
    allrows = {j: load_all(j) for j in (MAIN_JUDGE, SECOND_JUDGE)}
    flags: Counter = Counter()
    for j in allrows:
        for name in outputs:
            if name.endswith(f"/{j}.jsonl"):
                for x in (TREE / name).read_bytes().split(b"\n"):
                    if x.strip():
                        r = json.loads(x)
                        flags[(GROUP_OF[v24[r["question_id"]]["answer_type"]], bool(r["answerable"]))] += 1
    flag_ok = set(flags) == {(ANSWERABLE, True), (REFUTATION, True), (NOT_ANSWERABLE, False)}
    types_ok = set(types) == set(GROUP_OF)
    ten_ok = ten == set(sc.ten) == set(key_scope.D5_TEN)
    records_ok = set(sc.records) | ctx.d7 == set(v24)
    _gate(fails, "J4", types_ok and ten_ok and flag_ok and records_ok,
          f"group from {S373.KEY.name} answer_type: {dict(sorted(types.items()))} over {len(v24)} records, the "
          f"types GROUP_OF holds: {types_ok}; AS_V1's questions and the {len(ctx.d7)} D7 questions are those "
          f"records: {records_ok}; AS_V1's questions by group {dict(sorted(in_as.items()))}; refutation = Scope.ten "
          f"= key_scope.D5_TEN: {ten_ok}; the ledgers' answerable flag is true on {flags[(REFUTATION, True)]:,} "
          f"rows on the ten; flag = (group is not {NOT_ANSWERABLE}) on every row: {flag_ok}")

    # J5: S373's own item builder
    v1 = {q["id"]: q for q in json.loads(S373.V1.read_text(encoding="utf-8"))["questions"]}
    items_d7: Counter = Counter()
    j5 = []
    for j in allrows:
        sources = sorted({rec["source"] for rec in prov["inputs"].values() if rec["role"] == "production"
                          and rec["judge"] == j})
        want, per_source = {}, {}
        for src in sources:
            n0 = len(want)
            for x in S373.SOURCES[src](v1, v24):
                if x["question_id"] in ctx.d7:
                    items_d7[(j, x["key"].split("|")[0])] += 1
                else:
                    want[x["key"]] = (x["question_id"], len(x["answer"]))
            per_source[src] = len(want) - n0
        got = {r.key: (r.question_id, r.answer_chars) for r in allrows[j]}
        known_src = current and all(n == S388.KNOWN_SOURCE[src] for src, n in per_source.items())
        j5.append((j, per_source, len(got), known_src, want == got))
    _gate(fails, "J5", all(known and same for _j, _ps, _ng, known, same in j5),
          "; ".join(f"{j}: S373.SOURCES give {sum(ps.values()):,} answers off D7 ("
                    + ", ".join(f"{s} {n:,}" for s, n in ps.items()) + f"), = S388.KNOWN_SOURCE under the expected "
                    f"key: {known}; the loader {ng:,} rows; keys, questions and answer lengths equal: {same}"
                    for j, ps, ng, known, same in j5))

    # J6: totals
    per = {exp: len(load(exp)) for exp in EXPERIMENTS}
    known = {_SHORT[label]: n for label, n in S388.KNOWN_LABEL.items()}
    g04 = dict(Counter(r.group for r in load("exp04")))
    second = {exp: len(load(exp, SECOND_JUDGE)) for exp in EXPERIMENTS if SECOND_JUDGE in judges(exp)}
    total_ok = sum(per.values()) == len(allrows[MAIN_JUDGE]) == EXPECTED["devstral_rows"]
    _gate(fails, "J6", current and per == known and g04 == EXPECTED["exp04_groups"] and second == EXPECTED["gptoss"]
          and total_ok,
          f"{MAIN_JUDGE} {sum(per.values()):,} rows: " + ", ".join(f"{e} {n:,}" for e, n in per.items())
          + f"; = S388.KNOWN_LABEL: {per == known}; the total = load_all() = the expected total: {total_ok}; exp04 "
          f"{per['exp04']} = {g04.get(ANSWERABLE)} answerable + {g04.get(NOT_ANSWERABLE)} with no answer in the "
          f"corpus + {g04.get(REFUTATION)} on the ten, the expected groups: {g04 == EXPECTED['exp04_groups']}; "
          f"{SECOND_JUDGE} " + ", ".join(f"{e} {n:,}" for e, n in second.items())
          + f", the expected rows: {second == EXPECTED['gptoss']}; under the expected key: {current}")

    # J7: arms
    arms = {exp: dict(Counter(r.arm for r in load(exp))) for exp in EXPERIMENTS}
    arms2 = {exp: dict(Counter(r.arm for r in load(exp, SECOND_JUDGE))) for exp in second}
    total_arms = Counter(r.arm for r in allrows[MAIN_JUDGE])
    smoke_core = dict(Counter(r.core for r in load("s314") if r.arm == SMOKE))
    smoke_mode = dict(Counter(_file(_paths()[(r.label, r.tag)])[1][r.row]["mode"] for r in load("s314")
                              if r.arm == SMOKE))
    head_bad = []
    by_tag = defaultdict(list)
    for r in load("rep5"):
        by_tag[r.tag].append(r)
    for tag5, rs in sorted(by_tag.items()):
        folder = Path(_paths()[(EXPERIMENTS["rep5"], tag5)]).parent
        h = json.loads((folder / "arm_header.json").read_text(encoding="utf-8"))
        off = bool(h.get("think_off") or h.get("gemini_think_off"))
        if not all((h["arm"], h["generator"], h["draw"], off) == (tag5, r.generator, r.draw, r.arm == THINKING_OFF)
                   for r in rs):
            head_bad.append(tag5)
    want_arms = {exp: EXPECTED["arms"].get(exp, {REPORTED: per[exp]}) for exp in EXPERIMENTS}
    one_arm_ok = all(len(a) == 1 for e, a in arms.items() if e not in SEVERAL_ARMS)
    _gate(fails, "J7", current and arms == want_arms and smoke_core == EXPECTED["smoke_core"] and not head_bad
          and arms2.get("rep5") == EXPECTED["arms"]["rep5"],
          f"arms, {MAIN_JUDGE}: " + ", ".join(f"{a} {n:,}" for a, n in sorted(total_arms.items()))
          + "; " + "; ".join(f"{e} {arms[e]}" for e in SEVERAL_ARMS) + f"; every other experiment one arm: "
          f"{one_arm_ok}; all = the expected arms: {arms == want_arms}; rep5 under {SECOND_JUDGE} {arms2.get('rep5')}"
          f", the expected arms: {arms2.get('rep5') == EXPECTED['arms']['rep5']}; s314 smoke rows by core size "
          f"{smoke_core}, the expected sizes: {smoke_core == EXPECTED['smoke_core']}, and by mode {smoke_mode}; "
          f"{len(by_tag)} rep5 folders, arm_header.json differs from tag, generator, draw or arm on {len(head_bad)}; "
          f"under the expected key: {current}")

    # J8: scope, against key_scope's partition of the deposit rows themselves
    scope_msg, scope_ok, none_ok = [], True, True
    for exp in EXPERIMENTS:
        rows = load(exp)
        if exp not in WITH_SCOPE:
            none_ok &= all(r.in_scope is None and r.core is None and r.index is None for r in rows)
            continue
        out = [r for r in rows if r.in_scope is False]
        by_core = dict(sorted(Counter(r.core for r in out).items()))
        dep = [(t, n, d) for (lab, t), path in _paths().items() if lab == EXPERIMENTS[exp]
               for n, d in enumerate(_file(path)[1]) if s374_qid(d) not in ctx.d7 and _answered(d)]
        _, left = sc.partition(dep, lambda x: s374_qid(x[2]), lambda x, f=INDEX_FIELD[exp]: x[2][f])
        same = {(t, n) for t, n, _ in left} == {(r.tag, r.row) for r in out}
        counts_ok = current and by_core == EXPECTED["out_of_scope"][exp]
        on_ten = all(r.group == REFUTATION for r in out)
        flagged = all(isinstance(r.in_scope, bool) for r in rows)
        scope_ok &= counts_ok and same and on_ten and flagged
        scope_msg.append(f"{exp} {len(out)} of {len(rows):,} rows out of scope {by_core}, the expected counts under "
                         f"the expected key: {counts_ok}; by arm {dict(Counter(r.arm for r in out))}; all on the "
                         f"ten: {on_ten}; = key_scope's partition of the deposit rows: {same}; in_scope True or "
                         f"False on every row: {flagged}")
    _gate(fails, "J8", scope_ok and none_ok, "; ".join(scope_msg) + f"; in_scope, core and index None on every row "
          f"of the other {len(EXPERIMENTS) - len(WITH_SCOPE)} experiments: {none_ok}")

    # J9: D7 and the deposit rows
    dc = {exp: deposit_counts(exp) for exp in EXPERIMENTS}
    d7_tot = {exp: sum(c.d7.values()) for exp, c in dc.items()}
    acct = all(c.rows == c.no_answer + c.not_in_key + sum(c.d7.values()) + sum(c.expected.values())
               and c.expected == arms[exp] and c.not_in_key == 0 for exp, c in dc.items())
    items_ok = all(items_d7[(MAIN_JUDGE, EXPERIMENTS[exp])] == d7_tot[exp] for exp in EXPERIMENTS)
    changed = {q for q, r in v24.items() if r.get("question") and r["question"] != v1[q]["question"]}   # S373:231
    d7_ok = current and sum(d7_tot.values()) == EXPECTED["d7_answers_total"] \
        and all(d7_tot[e] == n for e, n in EXPECTED["d7_answers"].items())
    _gate(fails, "J9", d7_ok and acct and items_ok and changed == set(ctx.d7),
          f"deposit answers on the {len(ctx.d7)} D7 questions, absent from the ledgers: "
          + ", ".join(f"{e} {n}" for e, n in d7_tot.items()) + f"; total {sum(d7_tot.values())}; the expected counts "
          f"under the expected key: {d7_ok}; by arm where an experiment has two: "
          + ", ".join(f"{e} {dict(dc[e].d7)}" for e in SEVERAL_ARMS) + "; per experiment and arm, deposit rows = no "
          f"answer ({sum(c.no_answer for c in dc.values()):,}) + D7 answers + ledger rows: {acct}; = S373's items "
          f"on D7 questions: {items_ok}; the {len(changed)} questions whose text differs from the v1 key (S373's "
          f"own rule, S373_rejudge_v2.py:231) are dropped_d7: {changed == set(ctx.d7)}")

    # J10: scores
    import exp05_final                                   # the earlier holder of the pass threshold, read only for it
    every = [r for rs in allrows.values() for r in rs]
    scored_rows = [r for r in every if r.status in OK]
    bad_dim = [r.key for r in scored_rows
               if r.scores.get(r.dimension) != r.score or r.passed is not (r.score >= PASS_AT)
               or r.dimension != ("refusal_accuracy" if r.group == NOT_ANSWERABLE else "correctness")]
    bad_none = [r.key for r in every if r.status not in OK and (r.scores, r.score, r.passed) != (None, None, None)]
    ints = all(_is_int(r.score) and SCORE_MIN <= r.score <= SCORE_MAX for r in scored_rows)
    values = dict(sorted(Counter(r.score for r in scored_rows).items()))
    others = all(x is None or (_is_int(x) and SCORE_MIN <= x <= SCORE_MAX) for r in scored_rows
                 for x in r.scores.values())
    nulls = {f"{j} {k}": n for (j, k), n in sorted(Counter(
        (r.judge, k) for r in scored_rows for k, x in r.scores.items() if x is None).items())}
    statuses = dict(Counter(r.status for r in every))
    passed = {j: sum(1 for r in rs if r.passed) for j, rs in allrows.items()}
    _gate(fails, "J10", not bad_dim and not bad_none and ints and others and exp05_final.PASS_AT == PASS_AT,
          f"{len(every):,} rows of the two judges, statuses {statuses}: on the {len(scored_rows):,} scored rows score "
          f"is the group's dimension and passed is score >= {PASS_AT} on all but {len(bad_dim)}; every score an "
          f"integer {SCORE_MIN} to {SCORE_MAX}: {ints}, by value {values}; every value of every dimension such an integer "
          f"or null: {others}, nulls {nulls or 'none'}; rows without a scoring status that hold "
          f"a score: {len(bad_none)}; passed " + ", ".join(f"{j} {n:,} of {len(allrows[j]):,}" for j, n in passed.items())
          + f"; PASS_AT = exp05_final.PASS_AT: {exp05_final.PASS_AT == PASS_AT}")

    # J11: reported()
    sels = {exp: reported(exp, arm=ARM_OF.get(exp, REPORTED)) for exp in EXPERIMENTS}
    sums = all(len(s.rows) + sum(s.left_out.values()) == s.total == per[exp] for exp, s in sels.items())
    kept = sum(len(s.rows) for exp, s in sels.items() if exp not in ARM_OF)
    left: Counter = Counter()
    for exp, s in sels.items():
        if exp not in ARM_OF:
            left.update(s.left_out)
    one_arm = all(len(sels[exp].rows) == per[exp] for exp in ARM_OF)
    kept_ok = kept == total_arms[REPORTED] - left[OUT_OF_SCOPE] - left[NOT_SCORED]
    _gate(fails, "J11", sums and one_arm and kept_ok,
          f"reported(), arm {REPORTED}, {MAIN_JUDGE}: {kept:,} rows kept in {len(EXPERIMENTS) - len(ARM_OF)} "
          f"experiments; left out {dict(left)}; kept + left out = every row in each experiment: {sums}; kept = the "
          f"{total_arms[REPORTED]:,} rows of the arm less those out of scope and without a score: {kept_ok}; the "
          f"{len(ARM_OF)} one-arm experiments keep every row under their own arm: {one_arm}; each statement is "
          f"printed below")

    # J12: paired()
    prs = {exp: paired(exp) for exp in second}
    prs_all = {exp: paired(exp, arm=None) for exp in second}
    alone = sum(len(p.only_first) + len(p.only_second) for p in list(prs.values()) + list(prs_all.values()))
    every_arm_ok = {e: len(p.pairs) for e, p in prs_all.items()} == second
    keys_ok = all(a.key == b.key and a.judge == MAIN_JUDGE and b.judge == SECOND_JUDGE for p in prs.values()
                  for a, b in p.pairs)
    left_ok = all(p.left_out_first == reported(e).left_out and p.left_out_second == reported(e, SECOND_JUDGE).left_out
                  and len(p.pairs) + sum(p.left_out_first.values()) == per[e] for e, p in prs.items()) \
        and all(p.left_out_first is None and p.left_out_second is None for p in prs_all.values())
    _gate(fails, "J12", not alone and every_arm_ok and keys_ok and left_ok,
          f"paired(), {MAIN_JUDGE} with {SECOND_JUDGE}, pairs on the ledger key: "
          + ", ".join(f"{e} {len(prs[e].pairs):,} in the arm {REPORTED} and {len(prs_all[e].pairs):,} in every arm"
                      for e in prs)
          + f"; pairs in every arm = the {SECOND_JUDGE} rows: {every_arm_ok}; both rows of a pair on one key, "
          f"{MAIN_JUDGE} first: {keys_ok}; rows one judge alone holds: {alone}; the rows left out on each side are "
          f"reported()'s and, with the pairs, every row: {left_ok}; each statement is printed below")

    # J13: corpus scaling. The S314 rerun stands in for the deposit's verified_pass rows of exp05
    def pair(r: Row) -> tuple:
        return r.index, r.question_id
    want314 = Counter((d[INDEX_FIELD["exp05"]], s374_qid(d)) for (lab, _t), path in _paths().items()
                      if lab == EXPERIMENTS["exp05"] for d in _file(path)[1]
                      if d["config"] == S314_CONFIG and s374_qid(d) not in ctx.d7 and _answered(d))
    dep_vp = Counter(pair(r) for r in load("exp05") if r.arm == DEPOSIT_VP)
    got314 = Counter(pair(r) for r in load("s314") if r.arm == REPORTED)
    cs = corpus_scaling_reported()
    cs_vp = [r for r in cs.rows if r.config == S314_CONFIG]
    kept_vp = Counter(pair(r) for r in reported("exp05", arm=DEPOSIT_VP).rows)
    same_judged = want314 == dep_vp == got314
    once = all(n == 1 for n in got314.values())
    from_rerun = all(r.experiment == "s314" and r.arm == REPORTED for r in cs_vp) \
        and not any(r.arm == DEPOSIT_VP for r in cs.rows)
    same_kept = Counter(pair(r) for r in cs_vp) == kept_vp
    two = sels["exp05"].rows + sels["s314"].rows
    both = len(cs.rows) == len(two) and all(a is b for a, b in zip(cs.rows, two)) \
        and cs.verified_pass_pairs == len(got314)
    units = Counter((r.index, r.config, r.question_id) for r in cs.rows)
    s314_path = next(p for (lab, _t), p in _paths().items() if lab == EXPERIMENTS["s314"])
    gens = {r.generator for r in load("s314")}
    gen_ok = all(s374_genmodel({}, None, s314_path).startswith(g) for g in gens) and len(gens) == 1
    _gate(fails, "J13", same_judged and once and from_rerun and same_kept and both
          and all(n == 1 for n in units.values()) and gen_ok,
          f"s314 arm {REPORTED}: {sum(got314.values()):,} rows on {len(got314):,} (index, question) pairs, one row "
          f"each: {once}; = the pairs of exp05's {sum(dep_vp.values()):,} rows of the arm {DEPOSIT_VP} = the deposit "
          f"file's {S314_CONFIG} answers off D7 ({sum(want314.values()):,}): {same_judged}; "
          f"corpus_scaling_reported(): {len(cs.rows):,} rows = reported('exp05').rows + reported('s314').rows: "
          f"{both}; its {len(cs_vp):,} {S314_CONFIG} rows are s314's and none is of the arm {DEPOSIT_VP}: "
          f"{from_rerun}; they are on the pairs of the {sum(kept_vp.values()):,} rows the deposit's arm keeps under "
          f"the same rules: {same_kept}; one row per (index, strategy, question): "
          f"{all(n == 1 for n in units.values())}; one generator, the one S374 reads from the file's headers "
          f"{sorted(gens)}: {gen_ok}")

    # J14: the cache, and the objects every caller shares
    again = {j: load_all(j) for j in allrows}
    same = all(a is b for j in allrows for a, b in zip(allrows[j], again[j])) and load("exp05") is load("exp05") \
        and _context() is ctx and deposit_counts("exp05") is dc["exp05"]
    views = all(isinstance(r.scores, MappingProxyType) for r in scored_rows) \
        and all(isinstance(m, MappingProxyType) for c in dc.values() for m in (c.d7, c.expected))
    hashed = len(set(allrows[MAIN_JUDGE])) == len(allrows[MAIN_JUDGE])
    _gate(fails, "J14", same and views and hashed, f"a second load of every experiment returns the same objects "
          f"({sum(len(v) for v in again.values()):,} rows), and so do load('exp05'), the checks and "
          f"deposit_counts('exp05'): {same}; scores on every scored row and d7 and expected of every experiment are "
          f"read-only views (types.MappingProxyType): {views}; the {len(allrows[MAIN_JUDGE]):,} {MAIN_JUDGE} Rows "
          f"are as many members of a set: {hashed}")

    # J15: the result files and what pins them
    files = list(dict.fromkeys(_paths().values()))
    man = _manifest()
    listed = [p for p in files if _manifest_name(p) in man]
    pin_ok = all(_sha256(Path(p).read_bytes()) == man[_manifest_name(p)] for p in listed)
    man_head, man_msg = _at_head([MANIFEST])
    rest = [p for p in files if p not in listed]
    tracked = _tracked([p for p in rest if _rel([p]) is not None])
    in_git = [p for p in rest if tracked is not None and _rel([p]) is not None and _rel([p])[0] in tracked]
    neither = [p for p in rest if p not in in_git]
    rest_head, at_head_msg = _at_head(in_git) if in_git else (True, "none to compare")
    _gate(fails, "J15", pin_ok and man_head is not False and rest_head is not False and (tracked is None or not neither),
          f"{len(files)} result files in S374's list for these experiments; {_shown(MANIFEST)} ({len(man)} files; "
          f"{man_msg}) lists {len(listed)} of them under the deposit root, each with the manifest's sha256: {pin_ok}; "
          f"not listed {len(rest)}: "
          + ("git gave no answer, so not tested" if tracked is None else
             f"{len(in_git)} tracked in git ({at_head_msg}), {len(neither)} neither, each tracked and its blob at "
             f"HEAD: {rest_head is not False and not neither}"
             + (f": {[_shown(Path(p)) for p in neither]}" if neither else "")))

    _s393_gates(fails)

    print("\n  rows per experiment and judge: group / arm / in_scope")
    for j in (MAIN_JUDGE, SECOND_JUDGE):
        for exp in EXPERIMENTS:
            if j in judges(exp):
                rows = load(exp, j)
                g, a, s = (Counter(getattr(r, f) for r in rows) for f in ("group", "arm", "in_scope"))
                print(f"    {j:<9}{exp:<12}{len(rows):>6,}  " + ", ".join(f"{k} {g[k]:,}" for k in sorted(g))
                      + "  /  " + ", ".join(f"{k} {a[k]:,}" for k in sorted(a))
                      + "  /  " + ", ".join(f"{k} {s[k]:,}" for k in sorted(s, key=str)))
    print("\n  reported(), one statement per experiment")
    for sel in sels.values():
        print("    " + sel.statement())
    print("\n  corpus_scaling_reported()")
    print("    " + cs.statement())
    print("\n  paired(), one statement per replication")
    for p in prs.values():
        print("    " + p.statement())
    print(f"\n{'PASSED' if not fails else 'FAILED ' + ' '.join(fails)}; nothing written")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(self_test())
