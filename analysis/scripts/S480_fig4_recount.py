#!/usr/bin/env python3
"""S480 - Figure 4's judged counts, recounted by plain counting in code apart from the plate's: the known numbers
S472's reproduction gate (4) checks.

WHY. O1 (Valerio, 24 October, "O1 agree"): S472's gate (4) checked its pass counts against a scratch summary.json
written by prep.py, which imports S472 and S463, so an error in that code would have reproduced itself. This script
imports nothing from S463, S472 or S457 and computes no statistic: it reads the same raw files and counts. Its output,
findings/recompute/S480_fig4_recount.json, records every input file's sha256, and S472 refuses a recount made from
files other than the ones it read.

D188 (Valerio, 31 October: every figure moves to key v2.5): the counts are made twice. "counts_v24" counts the key
v2.4 rows of the two collects, as before D188 (the anchor). "counts" counts the draw-1 rows scripts/judge_rows_v25.py
chooses, imported directly (read_v25; it imports no figure script), the rows S472 draws: RLM-10's from --s6-g1, the
frozen set of S528 (out_s6_g1 with out_s6_g1r15 after phase 3), with no key v2.4 fallback: a set that leaves one RLM-10
answer of a changed question on key v2.4 is refused. G3's from an answer's key v2.5 row (S512's re-judging of the 132
changed questions: out_s6_g3 beside --collect) where one exists, else its key v2.4 row; with no out_s6_g3 there (the
frozen collect) G3's answers of changed questions are recorded as awaiting S6 (judge_rows_v25 block). Every v2.4 row
chosen must be the row the collect gave. S472's gate (4) checks its v2.4 counts against counts_v24 and its plate's
against counts.

D163 (G9, the two stress set-ups, Figure 4's rows 9 and 10; D132's nine set-ups stay as they were): "stress_records"
counts, per stress set-up, the answers, the answers with no text, the words, the model calls, the failed and cut calls
and the out-of-scope questions sent to a direct answer, from --g9's answers.json. Once --collect holds any row of theirs
(the frozen 41d3105d holds none) each must have all its draw-1 rows, and both join counts and counts_v24. Once
out_s6_g7_g3 sits beside --collect, "draw_counts" holds {config|draw|threshold: [passed, questions]} on the answerable
questions of D98's subset, on the rows judge_rows_v25 chooses (the rule below); until then the key is absent.

WHAT IT COUNTS, per set-up (the eight G3 set-ups raw_gemini, naive_rag, full_orchestrator, orch_no_analyser,
orch_no_planner, orch_no_supervisor, orch_no_synthesiser, orch_factual_to_documents, G9's two when judged, and rlm_10),
draw 1 only (D98):
  answerable_pass_4, answerable_pass_3   answerable questions (of 86) whose judge row is (a) status "ok" with a
                                         correctness of 4 or more (3 or more)
  not_answerable_refused_3               not-answerable questions (of 39) whose row is "ok" with a refusal_accuracy of
                                         3 or more
  false_premise_pass_4, false_premise_pass_3
                                         false-premise questions (of 10) whose row is "ok" with a correctness of 4 or
                                         more (3 or more); 4 is Rule 9's pass, 3 the relaxed threshold (D160 (11))
  <group>_judged                         the group's questions whose row is "ok" with the group's score, or
                                         "no_answer" (a row with any other status, or "ok" without the score, is not
                                         judged)
  judged_no_answer                       rows with (a) status "no_answer" (of 135); each must be an answer whose record
                                         holds no text (G3: generated_answer empty or white space; RLM-10:
                                         generation.answer empty or white space, or generation.error set), and every
                                         such answer must have that status
  unscored                               rows neither "ok" with the group's score nor "no_answer", by status
  not_answerable_direct_answer           for an orchestrator set-up whose analyser is on, the not-answerable questions
                                         whose record has generation.analysis.decision "direct_answer"; null where
                                         there is no analyser (raw_gemini, naive_rag, rlm_10) or where every record
                                         carries generation.analysis.status "switched_off" (orch_no_analyser: its
                                         stored decision is a default, not a routing). A mix of switched off and on
                                         is refused.
The group of each question: experiments.runner.experiment.questions() (the D5 key) and
experiments.scorers.records.GROUP_OF_TYPE (LIST.md Rule 8), both data. The score read per group, copied (not imported)
from S463.METRIC (scripts/S463_fig2_ranking.py, the constant METRIC): answerable "correctness", false_premise
"correctness", not_answerable "refusal_accuracy". Thresholds: pass 4 (D132, D154: the pass rate; S472.PASS_T,
scripts/S472_fig4_panels.py) and 3 (the relaxed threshold, D154); refused at 3 (Rule 9; S463.REFUSAL_T,
scripts/S463_fig2_ranking.py); false premise at 4, 3 the relaxed threshold (Rule 9 as D160 (11) set it; S472.FP_T and
S472.FP_RELAXED, scripts/S472_fig4_panels.py). Cited by name, not line: the lines moved (audit 27 Oct F6).

WHAT IT READS AND CHECKS (any failure exits 1, nothing written):
  --records      <dir>/findings/runs/exp_03__<set-up>__exp_v4_s20_n0/answers.json, the eight G3 set-ups: draw 1 is
                 the 135 questions of the D5 key, each once, each with the key's answer_type.
  --g9           <dir>/runs/exp_03__<set-up>__exp_v4_s20_n0/answers.json, G9's two set-ups, the same checks.
  --s6-g1        the folder holding out_s6_g1 and out_s6_g1r15 (and SHA256SUMS, recorded as an input).
  --collect      G3's s3_guard.py collect output and its sidecar <file>.json; --rlm-collect, G1's. Each sidecar: its
                 rows count equals the file's rows, its set is G3 (G1), its run_sha256 is every row's. The two
                 collects carry one run_sha256 (one judge set-up). No (config, question, draw) twice in either file.
                 Each draw-1 row of the set-ups counted: answer_key exp_v4_s20_n0|<set-up>|<question>|d1, the group's
                 prompt (answerable_prompt false exactly for the not-answerable group), one row per answer.
  --rlm-answers  <dir>/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl, each answer key's last line (exp_01 appends),
                 the file's sha256 equal to its line in <dir>/../MANIFEST.sha256; draw 1 holds all 135 questions.
REPRODUCES FIRST (README.md:75-79; a difference exits 2, nothing written):
  (0) D188: counts_v24 equals ANCHOR_V24 (the counts this script's committed output held before D188, at 8b1a5d7a),
      field by field, on every run, the frozen defaults or inputs given by path (a pull folder holding the S6 outs
      beside its collects): the v2.4 rows of draw 1 are the locked anchor whatever folder they are read from (review
      of build 3, F1). Only the selftest's fixtures, which are not the real questions, skip it, and say so;
  (1) the D5 key holds 135 questions, 86 answerable, 10 false premise, 39 not answerable (LIST.md Rule 8);
  (2) RLM-10's draw-1 counts (counts: the rows judge_rows_v25 chose, as Figure 3 reads them since D186 (3)) equal
      Figure 3's Source Data numbers (--fig2-numbers, default
      findings/figures_provisional/fig3_strategies/figure3_numbers.json): sheet Fig. 3a, rows 'draw' of rlm_10, draw 1,
      thresholds 4 and 3 (draw_pass_rate_pct x draw_questions / 100); sheet Fig. 3b, row 'draw' of rlm_10, draw 1
      (draw_refused_pct x draw_questions / 100); row 'false premise' of rlm_10 (fp_draw_1_passed_t3 of
      fp_draw_1_answers, for false_premise_pass_3; and fp_draw_1_passed_t4 of fp_draw_1_answers for
      false_premise_pass_4 when Figure 3's sheet holds that column: on 27 October it holds the draw-1 count at 3
      only, so the count at 4 is then compared with nothing and the output says so). Each product must be a whole
      number. Figure 3 must have been written from the same G1
      collect: the figure3_provenance.json beside --fig2-numbers must list, among its provenance.inputs_sha256, the
      sha256 of the --rlm-collect file read here. Both files' paths and sha256 are recorded under known_inputs.

COMMANDS, from the repository root (uv run only; no model call; nothing outside --out is written):
  uv run --frozen python scripts/S480_fig4_recount.py
      THE ONE COMMAND (D155) that rewrites findings/recompute/S480_fig4_recount.json from the frozen inputs, byte for
      byte: every input defaults to its frozen copy through scripts/fig_repro.frozen() (FROZEN below):
        --records      fig4_records_1023.tar, folder fig4_records_1023 (S472 pull of 23 October)
        --collect      findings/recompute/fig4_g9_inputs/g3_collect.jsonl (S472 pull-judge of 3 November: G3's
                       collect with G9's 270 rows; its own SHA256SUMS. The collect of 24 October, fig4_inputs, stays
                       selftest's collect, FROZEN_41D3)
        --rlm-collect  findings/recompute/fig2_inputs/g1_collect.jsonl (G1's collect of 23 October)
        --rlm-answers  fig2_g1r15_inputs.tar, folder fig2_g1r15_inputs/runs
        --g9           findings/recompute/g9_inputs (G9's two answers.json)
        --s6-g1        findings/recompute/fig3_s6_inputs (S528, checked against its own SHA256SUMS)
      A tar is read from env FROZEN_TARS (default ~/Mentori_scratch_keep/frozen_2026-10-26; after the deposit, the
      folder its tars were downloaded to), checked against findings/recompute/frozen_inputs/SHA256SUMS and extracted
      once into the gitignored findings/recompute/frozen_inputs/extracted/. Before reading a frozen input, every file
      of its set pinned in FROZEN_PIN must have the sha256 this script's committed output of 26 October recorded
      (else exit 1, nothing written).
  uv run --frozen python scripts/S480_fig4_recount.py [--records <dir>] [--collect <g3_collect.jsonl>] \
      [--rlm-collect <g1_collect.jsonl>] [--rlm-answers <g1r15_inputs/runs>] [--g9 <g9_inputs>] [--s6-g1 <dir>] \
      [--fig2-numbers <figure3_numbers.json>] [--out findings/recompute/S480_fig4_recount.json]
      Any input given is read from that path instead (a later pull; no pin applies to it).
      Runs the selftest first (quietly) and writes nothing if a check fails.
  uv run --frozen python scripts/S480_fig4_recount.py selftest
      Built fixtures in a temporary folder (eight G3 set-ups, G9's two and RLM-10 on a six-question key: 3 answerable,
      1 false premise, 2 not answerable; counts worked by hand), read and counted through the functions above and
      through main(): the counts by hand; then every refusal on an altered copy (a repeated (config, question,
      draw) row, a sidecar's rows, set or run_sha256, an answer judged with the other group's prompt, a draw-1
      answer with no row, a judge no_answer on an answer with text and an empty answer judged ok, an analyser
      switched off on some answers only, an answers.jsonl not matching MANIFEST.sha256, a draw 1 missing a
      question, two collects under different run_sha256) and every reproduction failure (one Figure 3 value
      changed, a share that is not a whole count, a Figure 3 written from another G1 collect, a key of other
      sizes), each of the last through main() with nothing written. D188: on the fixtures read_v25 is replaced by a
      stand-in (their rows carry no key hash or header, which judge_rows_v25 refuses): counts_v24 equals counts when
      every row chosen is v2.4, and one v2.5 row chosen changes counts and not counts_v24; anchor_v24 passes the
      pre-D188 counts and names one changed count; read_v25 itself on the frozen collects (committed) chooses every
      draw-1 v2.4 row read of G3, with 480 G3 answers awaiting S6, and takes RLM-10's 60 from the frozen S6G1 set;
      read_v25 on a folder without that set is refused. Last line "selftest: <k> of <k> checks pass".
      Also D155: frozen_default() passes the pinned files and refuses a changed one; the output names no git HEAD,
      working-tree state or write time, and its command no --out.
Writes --out with provenance (script path and sha256, the command with every input given and --out left out, the
frozen defaults read, the Python version; D155: no git HEAD, working-tree state or write time, so two runs on the
same inputs write the same bytes), "inputs" (every file the counts come from, path relative to the repository and
sha256: the ten answers.json, the two collects and their sidecars, RLM-10's answers.jsonl, the SHA256SUMS of --s6-g1),
"known_inputs" (the files read only to reproduce: figure3_numbers.json, figure3_provenance.json, MANIFEST.sha256, and
rerun_d89.sh for G1's 15 rerun keys), the reproduction, "judge_rows_v25" (judge_rows_v25.py's sha256, per set the
sources read with their run_sha256 and rows, the S6 outs absent, the draw-1 answers from key v2.5 and those awaiting S6,
provisional), "counts", "counts_v24", "stress_records" and, once S6G7G3 is copied, "draw_counts".
"""
import argparse
import hashlib
import json
import platform
import shlex
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fig_repro as FR  # noqa: E402  (D155: the frozen inputs; it imports no figure script)
import judge_rows_v25 as JR  # noqa: E402  (D188: key v2.5 rows where S6 judged; it imports no figure script)

SCRIPT = "scripts/S480_fig4_recount.py"
INDEX = "exp_v4_s20_n0"
G3 = ["raw_gemini", "naive_rag", "full_orchestrator", "orch_no_analyser", "orch_no_planner", "orch_no_supervisor",
      "orch_no_synthesiser", "orch_factual_to_documents"]
STRESS = ["orch_distil_every_step", "orch_distil_every_step_f1"]   # G9 (D163)
ORCH = G3[2:] + STRESS                 # the set-ups with an analyser, on or switched off
RLM = "rlm_10"
ALL = G3 + [RLM]                       # D132's nine set-ups: the anchor's
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"
# copied from S463.METRIC, scripts/S463_fig2_ranking.py (written out here, not imported)
SCORE_OF_GROUP = {"answerable": "correctness", "false_premise": "correctness", "not_answerable": "refusal_accuracy"}
PASS_T = (4, 3)            # D132, D154: 4 the pass rate (S472.PASS_T), 3 the relaxed threshold
REFUSED_T = 3              # Rule 9 (S463.REFUSAL_T)
FP_T = (4, 3)              # Rule 9 (D160 (11)): 4 the false-premise pass (S472.FP_T), 3 the relaxed threshold
GROUP_N = {"answerable": 86, "false_premise": 10, "not_answerable": 39}   # LIST.md Rule 8
N_Q = 135
FIG2_NUMBERS = ROOT / "findings" / "figures_provisional" / "fig3_strategies" / "figure3_numbers.json"
RERUN_SH = ROOT / "findings" / "recompute" / "G1_runs" / "rerun_d89.sh"   # G1's 15 reruns (D93 Q-c), S463.RERUN_SH
# D188: the v2.4 recount of the frozen inputs, as this script's committed output held it before D188 (the "counts" of
# findings/recompute/S480_fig4_recount.json at 8b1a5d7a, written on the frozen G3 and G1 collects). With every input
# its frozen default, counts_v24 must equal these (reproduce (0)); fields as ANCHOR_FIELDS, None where no analyser.
ANCHOR_FIELDS = ("answerable_pass_4", "answerable_pass_3", "not_answerable_refused_3", "false_premise_pass_4",
                 "false_premise_pass_3", "answerable_judged", "false_premise_judged", "not_answerable_judged",
                 "judged_no_answer", "unscored", "not_answerable_direct_answer")
ANCHOR_V24 = {"raw_gemini": (32, 62, 0, 8, 8, 86, 10, 39, 0, 0, None),
              "naive_rag": (73, 82, 39, 10, 10, 86, 10, 39, 0, 0, None),
              "full_orchestrator": (65, 84, 2, 8, 8, 86, 10, 39, 0, 0, 37),
              "orch_no_analyser": (66, 82, 37, 8, 8, 86, 10, 39, 0, 0, None),
              "orch_no_planner": (63, 80, 1, 9, 9, 86, 10, 39, 0, 0, 37),
              "orch_no_supervisor": (65, 81, 1, 9, 10, 86, 10, 39, 0, 0, 38),
              "orch_no_synthesiser": (68, 81, 2, 10, 10, 86, 10, 39, 0, 0, 37),
              "orch_factual_to_documents": (60, 79, 38, 9, 10, 86, 10, 39, 0, 0, 0),
              RLM: (66, 80, 39, 10, 10, 86, 10, 39, 1, 0, None)}
OUT = ROOT / "findings" / "recompute" / "S480_fig4_recount.json"
# D155: the frozen copies read when no input path is given (fig_repro.frozen(set, rel); findings/recompute/
# frozen_inputs/README.md), the inputs S472's plate of 26 October read.
FROZEN = {"records": ("fig4_records_1023", "fig4_records_1023"),
          "collect": ("fig4_g9", "g3_collect.jsonl"),
          "rlm_collect": ("fig2", "g1_collect.jsonl"),
          "rlm_answers": ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs"),
          "g9": ("g9", "."),
          "s6_g1": ("fig3_s6", ".")}
FROZEN_41D3 = ("fig4", "g3_collect.jsonl")   # selftest's collect, which stays when FROZEN["collect"] moves to a later set
# The sha256 this script's committed output of 26 October (61a3f303) recorded for each file it counts (its "inputs")
# and for the MANIFEST it checks (known_inputs.rlm_manifest). A frozen input with another sha256 is refused.
_RUNS = "fig4_records_1023/findings/runs/exp_03__{}__exp_v4_s20_n0/answers.json"
FROZEN_PIN = {
    ("fig4_records_1023", _RUNS.format("raw_gemini")): "afa5aa7eca967a07d3098c3bb53159c6114948b185e06aab85274123bd6f87ee",
    ("fig4_records_1023", _RUNS.format("naive_rag")): "544d3cb4174ec1c9649d2bc436ddcfadc42e6c3d0da5a82612db9ad3d42d21b1",
    ("fig4_records_1023", _RUNS.format("full_orchestrator")):
        "3a91380cf2b620fdc573ec78a2f91b824a3ceac811d62e430fe48041729c812c",
    ("fig4_records_1023", _RUNS.format("orch_no_analyser")):
        "6c54402ea3fec29f9f89bd0b5c3c6d892b2ddff5ca5e27fd034ee67b0e0f426c",
    ("fig4_records_1023", _RUNS.format("orch_no_planner")):
        "4ac955d8a012b7cd5fd103736d5868fc0bb2e1682937b8f780433de685067d1d",
    ("fig4_records_1023", _RUNS.format("orch_no_supervisor")):
        "0a7a955ffd36f332905366829a04621530271c093af9617127e51c4fd3d3ab04",
    ("fig4_records_1023", _RUNS.format("orch_no_synthesiser")):
        "a5d82c4b338548759ea32aa26415b368f37da0e67960844c68d3f51c44cf7bdc",
    ("fig4_records_1023", _RUNS.format("orch_factual_to_documents")):
        "126eeda5385dafc2414eb24ea7171d4633d0ab02a833ce0b9de10a540240e152",
    ("fig4", "g3_collect.jsonl"): "41d3105db493fa05fe6fc702ce315c4c4417f528699dc51b05da5b9240e7ec37",
    ("fig4", "g3_collect.jsonl.json"): "8ad99ba4071eb289166ca16b9ff48c541f7208cc55f2bbf151d893ec9b1451c7",
    ("fig2", "g1_collect.jsonl"): "f5ff75bc244cda492a48e7e11f54f2007ed7d586a8f49e78921edd7244b28965",
    ("fig2", "g1_collect.jsonl.json"): "04996e9dd9c3cca49177068f0143fbe0d1c7fa265a4eb6f617d24551f501f895",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/runs/exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl"):
        "ecb6de5343d172894fd56d57997e3301d70ca3fb509ae2cd65f8e47eb8c268b7",
    ("fig2_g1r15_inputs", "fig2_g1r15_inputs/MANIFEST.sha256"):
        "60c1f703d7b5853ec7bd5aebaecec9ac50ea3cb078b1f44741c5964427635b2e",
    ("g9", "PULL.json"): "e7f9abed14cee406c3c1934af3ea0257bfc06da9d1401213ce5fd913384f61f9",   # SHA256SUMS' line
    # 3 November: FROZEN["collect"] moved to S472 pull-judge's collect with G9's rows (S472's FROZEN_PIN, the same)
    ("fig4_g9", "g3_collect.jsonl"): "527fd71e53f30ca77f6ca050be58206a08e99b55b87e8d58887f5486bbdd4bae",
    ("fig4_g9", "g3_collect.jsonl.json"): "047a84919456d72557d581d83d6584ac8440158201a1ebec067be6b26d03b297",
}


class Fail(Exception):
    pass


class NotReproduced(Exception):
    pass


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frozen_default(name: str, frozen=None) -> Path:
    """D155: the frozen copy of input name (a key of FROZEN), after every pinned file of its set has the sha256 of
    FROZEN_PIN (else Fail: not the input the committed recount was made from)."""
    frozen = frozen or FR.frozen
    s, r = FROZEN[name]
    try:
        for (ps, pr), want in FROZEN_PIN.items():
            if ps == s:
                got = sha256_file(frozen(ps, pr))
                if got != want:
                    raise Fail(f"frozen input {ps}:{pr} has sha256 {got[:12]}, the committed recount recorded "
                               f"{want[:12]}")
        return frozen(s, r)
    except FR.FrozenInputError as e:
        raise Fail(str(e)) from None


def rel(p: Path) -> str:
    p = Path(p).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def key_groups():
    from experiments.runner.experiment import questions
    from experiments.scorers.records import GROUP_OF_TYPE
    qs = questions()
    return [q["id"] for q in qs], {q["id"]: GROUP_OF_TYPE[q["answer_type"]] for q in qs}, \
        {q["id"]: q["answer_type"] for q in qs}


def read_g3_records(rec: Path, order, types):
    """{(config, question): {"no_text", "decision", "analysis_status"}} for the eight G3 set-ups' draw 1."""
    out, files = {}, {}
    for c in G3:
        p = rec / "findings" / "runs" / f"exp_03__{c}__{INDEX}" / "answers.json"
        files[c] = p
        R = [r for r in json.loads(p.read_text())["results"] if r["draw"] == 1]
        ids = [r["question_id"] for r in R]
        if sorted(ids) != sorted(order) or len(set(ids)) != len(ids):
            raise Fail(f"{p}: draw 1 is not the {N_Q} questions of the D5 key, each once")
        for r in R:
            q = r["question_id"]
            if r.get("answer_type") != types[q] or r.get("answer_key") != f"{INDEX}|{c}|{q}|d1":
                raise Fail(f"{p}: {q}: answer_type {r.get('answer_type')!r} or answer_key {r.get('answer_key')!r}")
            a = (r.get("generation") or {}).get("analysis") or {}
            out[(c, q)] = {"no_text": not (r.get("generated_answer") or "").strip(),
                           "decision": a.get("decision"), "analysis_status": a.get("status")}
    return out, files


def read_g9_records(g9: Path, order, types, groups):
    """G9's two set-ups' draw 1: ({(config, question): the record fields count reads}, {config: path}, stress_records:
    per set-up the answers, the answers with no text, the words of the stored answers, the model calls (the entries of
    generation.calls), the failed calls (a status other than ok and length), the cut calls (length) and the
    not-answerable questions whose analyser, on, chose direct_answer)."""
    out, files, stress = {}, {}, {}
    for c in STRESS:
        p = g9 / "runs" / f"exp_03__{c}__{INDEX}" / "answers.json"
        files[c] = p
        R = [r for r in json.loads(p.read_text())["results"] if r["draw"] == 1]
        ids = [r["question_id"] for r in R]
        if sorted(ids) != sorted(order) or len(set(ids)) != len(ids):
            raise Fail(f"{p}: draw 1 is not the {N_Q} questions of the D5 key, each once")
        row = Counter(answers=0, no_text=0, words=0, model_calls=0, failed_calls=0, cut_calls=0,
                      not_answerable_direct_answer=0)
        for r in R:
            q = r["question_id"]
            if r.get("answer_type") != types[q] or r.get("answer_key") != f"{INDEX}|{c}|{q}|d1":
                raise Fail(f"{p}: {q}: answer_type {r.get('answer_type')!r} or answer_key {r.get('answer_key')!r}")
            g = r.get("generation") or {}
            a = g.get("analysis") or {}
            text = r.get("generated_answer") or ""
            st = Counter(x.get("status") for x in g.get("calls") or [])
            on = a.get("status") != "switched_off"
            out[(c, q)] = {"no_text": not text.strip(), "decision": a.get("decision"), "analysis_status": a.get("status")}
            row.update(answers=1, no_text=int(not text.strip()), words=len(text.split()), model_calls=sum(st.values()),
                       failed_calls=sum(v for k, v in st.items() if k not in ("ok", "length")), cut_calls=st["length"],
                       not_answerable_direct_answer=int(on and groups[q] == "not_answerable"
                                                        and a.get("decision") == "direct_answer"))
        stress[c] = dict(row)
    return out, files, stress


def read_rlm_records(runs: Path, order):
    p = runs / f"exp_01__{RLM}__{INDEX}" / "answers.jsonl"
    man = runs.parent / "MANIFEST.sha256"
    want = {}
    for ln in man.read_text().splitlines():
        if ln.strip():
            h, f = ln.split(None, 1)
            want[f.strip()] = h
    h = sha256_file(p)
    if want.get(f"runs/exp_01__{RLM}__{INDEX}/answers.jsonl") != h:
        raise Fail(f"{p}: sha256 {h[:12]} is not its line in {man}")
    last = {}
    for ln in p.read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            last[r["answer_key"]] = r
    out = {}
    for q in order:
        r = last.get(f"{INDEX}|{RLM}|{q}|d1")
        if r is None:
            raise Fail(f"{p}: no draw-1 record of {q}")
        g = r.get("generation") or {}
        out[(RLM, q)] = {"no_text": bool(g.get("error")) or not (g.get("answer") or "").strip(),
                         "decision": None, "analysis_status": None}
    return out, p, man


def read_collect(p: Path, want_set: str, configs, groups):
    """{(config, question): (a) dict} of the draw-1 rows of configs; the sidecar's checks; one run_sha256."""
    side_p = p.with_name(p.name + ".json")
    side = json.loads(side_p.read_text())
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    if side.get("rows") != len(rows):
        raise Fail(f"{side_p}: {side.get('rows')} rows, {p} holds {len(rows)}")
    if side.get("set") != want_set:
        raise Fail(f"{side_p}: set {side.get('set')!r}, want {want_set!r}")
    runs = Counter(r.get("run_sha256") for r in rows)
    if len(runs) != 1 or side.get("run_sha256") not in runs:
        raise Fail(f"{p}: run_sha256 values {dict(runs)}, sidecar {side.get('run_sha256')}")
    seen, out = set(), {}
    for i, r in enumerate(rows, 1):
        k = (r.get("config"), r.get("question_id"), r.get("draw"))
        if k in seen:
            raise Fail(f"{p}: row {i} repeats {k}")
        seen.add(k)
        c, q, d = k
        if c not in configs or d != 1:
            continue
        if q not in groups or r.get("answer_key") != f"{INDEX}|{c}|{q}|d1":
            raise Fail(f"{p}: row {i} {k}: answer_key {r.get('answer_key')!r}")
        if bool(r.get("answerable_prompt")) != (groups[q] != "not_answerable"):
            raise Fail(f"{p}: row {i} {k}: judged with the other group's prompt")
        out[(c, q)] = r.get("a") or {}
    missing = [(c, q) for c in configs for q in groups if (c, q) not in out]
    if missing:
        raise Fail(f"{p}: {len(missing)} draw-1 answers have no row, first {missing[0]}")
    return out, side_p, side["run_sha256"]


def kind_of(a: dict, group: str):
    """('scored', score) | ('no_answer', None) | ('unscored', status)."""
    st = a.get("status")
    if st == "ok":
        v = (a.get("scores") or {}).get(SCORE_OF_GROUP[group])
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return "scored", v
        return "unscored", "ok without its score"
    if st == "no_answer":
        return "no_answer", None
    return "unscored", str(st)


def count(order, groups, recs, judged, setups=None):
    by = {g: [q for q in order if groups[q] == g] for g in GROUP_N}
    out = {}
    for c in ALL if setups is None else setups:
        k = {q: kind_of(judged[(c, q)], groups[q]) for q in order}
        hit = lambda q, t: k[q][0] == "scored" and k[q][1] >= t            # noqa: E731
        bad = [q for q in order if (k[q][0] == "no_answer") != recs[(c, q)]["no_text"]]
        if bad:
            raise Fail(f"{c} {bad[0]}: judge {k[bad[0]][0]}, record no_text {recs[(c, bad[0])]['no_text']}")
        row = {f"answerable_pass_{t}": sum(hit(q, t) for q in by["answerable"]) for t in PASS_T}
        row.update(
            not_answerable_refused_3=sum(hit(q, REFUSED_T) for q in by["not_answerable"]),
            **{f"false_premise_pass_{t}": sum(hit(q, t) for q in by["false_premise"]) for t in FP_T},
            **{f"{g}_judged": sum(k[q][0] in ("scored", "no_answer") for q in by[g]) for g in GROUP_N},
            judged_no_answer=sum(k[q][0] == "no_answer" for q in order),
            unscored=sum(k[q][0] == "unscored" for q in order),
            unscored_by_status=dict(Counter(k[q][1] for q in order if k[q][0] == "unscored")))
        offs = Counter(recs[(c, q)]["analysis_status"] == "switched_off" for q in order)
        if c in ORCH and len(offs) > 1:
            raise Fail(f"{c}: the analyser is switched off on {offs[True]} answers and on for {offs[False]}")
        if c in ORCH and not offs[True]:
            row["analyser"] = "on"
            row["not_answerable_direct_answer"] = sum(recs[(c, q)]["decision"] == "direct_answer"
                                                      for q in by["not_answerable"])
        else:
            row["analyser"] = "switched off" if c in ORCH else "none"
            row["not_answerable_direct_answer"] = None
        out[c] = row
    return out


def rerun_keys(path: Path = RERUN_SH) -> list[str]:
    """G1's 15 rerun answer keys, read from rerun_d89.sh's KEYS as S463.rerun_keys reads them (copied, not imported):
    lines of six fields whose first is an exp_01 run, the answer key fields 2 to 5."""
    keys = []
    for ln in path.read_text().splitlines():
        f = ln.strip().split("|")
        if len(f) == 6 and f[0].startswith("exp_01__"):
            keys.append("|".join(f[1:5]))
    if len(keys) != 15 or len(set(keys)) != 15:
        raise Fail(f"{rel(path)}: {len(keys)} rerun keys, want 15 distinct")
    return keys


def _s6_loaded(src: dict, tmp: Path, replace_keys=None):
    """An S6 source present on disk: s3_guard.py collect on its outs (and --replace) into tmp, then read_source."""
    import contextlib
    import io
    dest = tmp / f"{src['name']}_collect.jsonl"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = JR.guard().collect(src["outs"], src.get("replace"), dest, src["set"])
    if rc:
        raise Fail(f"s3_guard collect refused {src['name']}: {buf.getvalue().strip()[-300:]}")
    return JR.read_source(src, dest, replace_keys=replace_keys)


def read_v25(g3c: Path, g1c: Path, groups: dict, j3: dict, j1: dict, s6_g1: Path, g3_sets=None):
    """D188: the draw-1 judge rows of the set-ups counted as scripts/judge_rows_v25.py chooses them: an answer's key
    v2.5 row (S512) where one exists, else its key v2.4 row. G3 and G9 (g3_sets, default the eight): out_g3 beside
    --collect (v2.4) and out_s6_g3 beside it when present (the 132), choose with G3's per-configuration rule reading
    draw 1 of those set-ups only. G1: out and out_g1r15 beside --rlm-collect (v2.4, the 15 reruns held to out_g1r15) and
    out_s6_g1 with out_s6_g1r15 under s6_g1, which must be present, choose at every draw (G1's rule), then RLM-10's draw
    1, with every answer of a changed question from key v2.5 (no v2.4 fallback). Every v2.4 row chosen must be the row
    read_collect read (its (a) equal). Returns ({(config, question): (a) dict}, the record: sources, answers from v2.5,
    answers awaiting S6, and the 'draw' rows' cells {(config, question, draw): (a) dict} or None until out_s6_g7_g3 is
    beside --collect)."""
    import tempfile
    judged, rec = {}, {}
    g3_sets = G3 if g3_sets is None else g3_sets
    try:
        with tempfile.TemporaryDirectory(prefix="S480_s6_") as td:
            td = Path(td)
            s3 = JR.sources(g3c.parent, "G3")
            s3_frozen = JR.sources(s6_g1, "G3")[1]     # D203: out_s6_g3 frozen beside S6G1 (S528 --add)
            if not s3[1]["present"] and s3_frozen["present"]:
                s3 = [s3[0], s3_frozen, s3[2]]
            L3 = [JR.read_source(s3[0], g3c)] + ([_s6_loaded(s3[1], td)] if s3[1]["present"] else [])
            a3 = [{"run_id": f"exp_03__{c}__{INDEX}", "config": c, "question_id": q, "draw": 1,
                   "answer_key": f"{INDEX}|{c}|{q}|d1"} for c in g3_sets for q in sorted(groups)]
            ch3 = JR.choose(a3, L3, g7_configs=JR.g7_configs("G3"),
                            read_only=lambda d: d.get("draw") == 1 and d.get("config") in g3_sets)
            keys = rerun_keys()
            s1 = JR.sources(g1c.parent, "G1")
            s1_25 = JR.sources(s6_g1, "G1")[1]
            if not s1_25["present"]:
                raise Fail(f"judge_rows_v25 G1: {s1_25['missing']} not under {s6_g1}: RLM-10 is read on key v2.5 only")
            L1 = [JR.read_source(s1[0], g1c, replace_keys=keys), _s6_loaded(s1_25, td, replace_keys=keys)]
            a1 = [{k: d[k] for k in ("run_id", "config", "question_id", "draw", "answer_key")}
                  for d in L1[0].rows.values()]
            ch1 = JR.choose(a1, L1, all_draws=True)
            draws = draw_cells(s3, L3, ch1, groups, g3_sets, td) if s3[2]["present"] else None
    except JR.Refused as e:
        raise Fail(f"judge_rows_v25: {e}") from None
    for name, ch, want, old in (("G3", ch3, [(c, q) for c in g3_sets for q in sorted(groups)], j3),
                                ("G1", ch1, [(RLM, q) for q in sorted(groups)], j1)):
        n25 = n_await = 0
        for c, q in want:
            v = ch[(f"exp_0{3 if name == 'G3' else 1}__{c}__{INDEX}", c, q, 1)]
            if v["row"] is None:
                raise Fail(f"judge_rows_v25 {name}: {c} {q} draw 1: no judge row chosen ({v['status']})")
            if v["status"] != "v2.5" and (v["row"].get("a") or {}) != old[(c, q)]:
                raise Fail(f"judge_rows_v25 {name}: {c} {q} draw 1: the v2.4 row chosen is not the row read")
            judged[(c, q)] = v["row"].get("a") or {}
            n25 += v["status"] == "v2.5"
            n_await += v["status"] == "v2.4 awaiting S6"
        if name == "G1" and n_await:
            raise Fail(f"judge_rows_v25 G1: {n_await} RLM-10 answers of changed questions have no key v2.5 row under "
                       f"{s6_g1}: no key v2.4 fallback")
        rec[name] = {"sources": {n: {"kind": x["kind"], "run_sha256": x["run_sha256"], "rows": x["rows"],
                                     **({"set_aside": x["set_aside"]} if "set_aside" in x else {})}
                                 for n, x in ch["_sources"].items()},
                     "s6_absent": [Path(m).name for m in (s3 if name == "G3" else [None, s1_25])[1]["missing"]],
                     "draw_1_answers": len(want), "from_v25": n25, "awaiting_s6": n_await}
    rec["provisional"] = any(rec[n]["awaiting_s6"] for n in ("G3", "G1"))
    rec["draws"] = draws
    return judged, rec


def draw_keep(d: dict, subset, g7) -> bool:
    """Which rows the 'draw' rows read (the rule of S472.draw_rows_keep, written out here, not imported): a G3 or G9
    set-up on a question of D98's subset; of a row at draw 2 or 3 of a G7 set-up, only an S6G7G3 row (questions "all")."""
    if d.get("config") not in G3 + STRESS or d.get("question_id") not in subset:
        return False
    return not ("a" in d and d.get("config") in g7 and d.get("draw") in (2, 3) and d.get("questions") != "all")


def draw_cells(s3: list, L3: list, ch1: dict, groups: dict, g3_sets, tmp: Path) -> dict:
    """The (a) dicts of the 'draw' rows, {(config, question, draw): (a) dict}: every set-up on D98's subset, draws 1 to 3,
    through judge_rows_v25.choose with draw_keep; RLM-10 from ch1, its G1 choice at every draw."""
    sub = json.loads(D98_SUBSET.read_text())["ids"]
    g7 = set(JR.g7_configs("G3"))
    ans = [{"run_id": f"exp_03__{c}__{INDEX}", "config": c, "question_id": q, "draw": d,
            "answer_key": f"{INDEX}|{c}|{q}|d{d}"} for c in G3 + STRESS for q in sub for d in (1, 2, 3)]
    if not s3[1]["present"]:
        raise Fail("judge_rows_v25: out_s6_g7_g3 is beside --collect and out_s6_g3 is not")
    loaded = L3 + [_s6_loaded(s3[2], tmp)]
    ch = JR.choose(ans, loaded, g7_configs=g7, read_only=lambda d: draw_keep(d, sub, g7))
    out = {(a["config"], a["question_id"], a["draw"]): ch[(a["run_id"], a["config"], a["question_id"], a["draw"])]["row"]
           for a in ans}
    out = {k: v.get("a") or {} for k, v in out.items() if v is not None}
    for q in sub:
        for d in (1, 2, 3):
            r = ch1[(f"exp_01__{RLM}__{INDEX}", RLM, q, d)]["row"]
            if r is not None:
                out[(RLM, q, d)] = r.get("a") or {}
    return {"cells": out, "subset": sub}


def count_draws(cells: dict, groups: dict, subset: list) -> dict:
    """{config|draw|threshold: [passed, questions]} on the answerable questions of subset: passed, a score of the
    threshold or more; questions, the answers with a row that is not unscored (a no_answer counts and fails)."""
    aq = [q for q in subset if groups[q] == "answerable"]
    out = {}
    for c in G3 + STRESS + [RLM]:
        for d in (1, 2, 3):
            for t in PASS_T:
                k = n = 0
                for q in aq:
                    if (c, q, d) not in cells:
                        continue
                    kind, v = kind_of(cells[(c, q, d)], "answerable")
                    if kind != "unscored":
                        n += 1
                        k += kind == "scored" and v >= t
                out[f"{c}|{d}|{t}"] = [k, n]
    return out


def anchor_v24(counts: dict) -> list[str]:
    """Reproduce (0): counts_v24 against ANCHOR_V24, field by field; the differences (empty when equal)."""
    probs = []
    for c in ALL:
        for f, v in zip(ANCHOR_FIELDS, ANCHOR_V24[c]):
            if counts[c].get(f, "absent") != v:
                probs.append(f"{c} {f}: {counts[c].get(f, 'absent')} here, the pre-D188 recount {v}")
    return probs


def reproduce(order, groups, counts, fig2: Path, g1_sha: str):
    """(1) the D5 key's sizes; (2) RLM-10's draw-1 counts against Figure 3's Source Data, written from the G1 collect
    whose sha256 is g1_sha (figure3_provenance.json beside fig2)."""
    got = Counter(groups.values())
    if len(order) != N_Q or dict(got) != GROUP_N:
        raise NotReproduced(f"the D5 key gives {len(order)} questions {dict(got)}, want {N_Q} {GROUP_N}")
    prov = json.loads((fig2.parent / "figure3_provenance.json").read_text())
    if g1_sha not in ((prov.get("provenance") or {}).get("inputs_sha256") or {}).values():
        raise NotReproduced(f"{fig2.parent / 'figure3_provenance.json'} lists no input with the G1 collect's sha256 "
                            f"{g1_sha[:12]}: Figure 3 was not written from this G1 collect")
    sh = json.loads(fig2.read_text())["sheets"]

    def rows(name):
        s = sh[name]
        return [dict(zip(s["columns"], r)) if isinstance(r, list) else r for r in s["rows"]]

    def whole(pct, n, what):
        x = pct * n / 100
        if abs(x - round(x)) > 1e-6:
            raise NotReproduced(f"Figure 3 {what}: {pct}% of {n} is not a whole count")
        return int(round(x))
    want, probs = {}, []
    for r in rows("Fig. 3a"):
        if r.get("row_kind") == "draw" and r.get("strategy") == RLM and r.get("draw") == 1:
            want[f"answerable_pass_{r['threshold']}"] = (whole(r["draw_pass_rate_pct"], r["draw_questions"],
                                                               f"Fig. 3a draw 1 at {r['threshold']}"),
                                                         r["draw_questions"])
    for r in rows("Fig. 3b"):
        if r.get("strategy") != RLM:
            continue
        if r.get("row_kind") == "draw" and r.get("draw") == 1:
            want["not_answerable_refused_3"] = (whole(r["draw_refused_pct"], r["draw_questions"], "Fig. 3b draw 1"),
                                                r["draw_questions"])
        if r.get("row_kind") == "false premise":
            for t in FP_T:
                if r.get(f"fp_draw_1_passed_t{t}") is not None:
                    want[f"false_premise_pass_{t}"] = (r[f"fp_draw_1_passed_t{t}"], r["fp_draw_1_answers"])
    need = ["answerable_pass_4", "answerable_pass_3", "not_answerable_refused_3", "false_premise_pass_3"]
    # D160 (11): the false-premise count at 4 is compared when Figure 3's Source Data holds its draw-1 value
    optional = ["false_premise_pass_4"]
    den = {"answerable_pass_4": "answerable_judged", "answerable_pass_3": "answerable_judged",
           "not_answerable_refused_3": "not_answerable_judged", "false_premise_pass_3": "false_premise_judged",
           "false_premise_pass_4": "false_premise_judged"}
    for k in need + optional:
        if k not in want:
            if k in need:
                probs.append(f"Figure 3's Source Data has no RLM-10 draw-1 value for {k}")
            continue
        g = (counts[RLM][k], counts[RLM][den[k]])
        if g != want[k]:
            probs.append(f"RLM-10 {k}: {g[0]} of {g[1]} here, Figure 3 {want[k][0]} of {want[k][1]}")
    if probs:
        raise NotReproduced("; ".join(probs))
    return {"d5_key": {"questions": len(order), **GROUP_N},
            "rlm_10_draw_1_vs_figure_2": {k: {"here": counts[RLM][k], "figure_2": want[k][0], "of": want[k][1]}
                                          for k in need + optional if k in want},
            "not_compared": {k: "Figure 3's Source Data holds no RLM-10 draw-1 value for it"
                             for k in optional if k not in want}}


# ---------------------------------------------------------------------------------------------------------------
# selftest: built fixtures, counts worked by hand, every refusal on an altered copy
# ---------------------------------------------------------------------------------------------------------------
FX_ORDER = ["qa1", "qa2", "qa3", "qf1", "qn1", "qn2"]
FX_GROUPS = {"qa1": "answerable", "qa2": "answerable", "qa3": "answerable", "qf1": "false_premise",
             "qn1": "not_answerable", "qn2": "not_answerable"}
FX_TYPES = {q: f"type_{g}" for q, g in FX_GROUPS.items()}
FX_N = {"answerable": 3, "false_premise": 1, "not_answerable": 2}
FX_RUN = "f" * 64
# G3 set-ups: correctness qa1 5, qa2 3, qa3 2; qf1 3; refusal qn1 4, qn2 1. Planner off: qa3's judge call "error".
# RLM-10: qa1 has no text (judge no_answer), qa2 4, qa3 4; qf1 2; refusal qn1 3, qn2 3.
FX_G3_SCORE = {"qa1": 5, "qa2": 3, "qa3": 2, "qf1": 3, "qn1": 4, "qn2": 1}
FX_RLM_SCORE = {"qa1": None, "qa2": 4, "qa3": 4, "qf1": 2, "qn1": 3, "qn2": 3}


def fx_write(d: Path, g3_rows=None, g1_rows=None, side3=None, recs=None, rlm_lines=None, fig2a=None, prov_sha=None,
             fig2fp=None, g9_recs=None):
    """Writes the fixture under d and returns the main() arguments; each keyword replaces one part with an altered
    copy (a function of the default)."""
    def ans_row(c, q, draw=1, text="an answer", analysis=None):
        return {"draw": draw, "question_id": q, "answer_type": FX_TYPES[q], "answer_key": f"{INDEX}|{c}|{q}|d{draw}",
                "generated_answer": text, "generation": {"analysis": analysis} if analysis is not None else {}}
    g9 = {c: [ans_row(c, q, text="two words", analysis={"status": "ok", "decision": "direct_answer" if q == "qn1" else
                                                        "plan"}) for q in FX_ORDER] for c in STRESS}
    g9[STRESS[0]][0]["generation"]["calls"] = [{"status": "ok"}, {"status": "length"}, {"status": "error"}]
    g9 = g9_recs(g9) if g9_recs else g9
    for c in STRESS:
        f = d / "g9" / "runs" / f"exp_03__{c}__{INDEX}" / "answers.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"results": g9[c]}))
    (d / "s6").mkdir(exist_ok=True)
    (d / "s6" / "SHA256SUMS").write_text("fixture\n")
    rec = {}
    for c in G3:
        an = (lambda q: {"status": "switched_off", "decision": "direct_answer"}) if c == "orch_no_analyser" else \
            (lambda q: {"status": "ok", "decision": "direct_answer" if FX_GROUPS[q] == "not_answerable" else
                        "plan"}) if c == "full_orchestrator" else \
            (lambda q: {"status": "ok", "decision": "plan"}) if c in ORCH else (lambda q: None)
        rec[c] = [ans_row(c, q, analysis=an(q)) for q in FX_ORDER] + [ans_row(c, "qa1", draw=2)]
    rec = recs(rec) if recs else rec
    for c in G3:
        f = d / "rec" / "findings" / "runs" / f"exp_03__{c}__{INDEX}" / "answers.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"results": rec[c]}))

    def jrow(c, q, sc, draw=1):
        g = FX_GROUPS[q]
        a = ({"status": "no_answer"} if sc is None else {"status": "error"} if sc == "error" else
             {"status": "ok", "scores": {SCORE_OF_GROUP[g]: sc}})
        return {"config": c, "question_id": q, "draw": draw, "answer_key": f"{INDEX}|{c}|{q}|d{draw}",
                "answerable_prompt": g != "not_answerable", "run_sha256": FX_RUN, "a": a}
    r3 = [jrow(c, q, "error" if (c, q) == ("orch_no_planner", "qa3") else FX_G3_SCORE[q])
          for c in G3 for q in FX_ORDER] + [jrow("raw_gemini", "qa1", 1, draw=2)]
    r1 = [jrow(RLM, q, FX_RLM_SCORE[q]) for q in FX_ORDER] + [jrow("single_pass", "qa1", 5)]
    r3, r1 = (g3_rows(r3) if g3_rows else r3), (g1_rows(r1) if g1_rows else r1)
    for name, rows, st in (("g3_collect.jsonl", r3, "G3"), ("g1_collect.jsonl", r1, "G1")):
        (d / name).write_text("".join(json.dumps(r) + "\n" for r in rows))
        side = {"rows": len(rows), "set": st, "run_sha256": FX_RUN}
        if side3 and st == "G3":
            side = side3(side)
        (d / (name + ".json")).write_text(json.dumps(side))
    lines = [{"answer_key": f"{INDEX}|{RLM}|qa2|d1", "generation": {"answer": ""}}]          # superseded
    lines += [{"answer_key": f"{INDEX}|{RLM}|{q}|d1",
               "generation": {"answer": "" if FX_RLM_SCORE[q] is None else "an answer"}} for q in FX_ORDER]
    lines = rlm_lines(lines) if rlm_lines else lines
    jl = d / "g1" / "runs" / f"exp_01__{RLM}__{INDEX}" / "answers.jsonl"
    jl.parent.mkdir(parents=True, exist_ok=True)
    jl.write_text("".join(json.dumps(x) + "\n" for x in lines))
    (d / "g1" / "MANIFEST.sha256").write_text(f"{sha256_file(jl)}  runs/exp_01__{RLM}__{INDEX}/answers.jsonl\n")
    a_rows = [{"row_kind": "draw", "strategy": RLM, "draw": 1, "threshold": t, "draw_pass_rate_pct": 200 / 3,
               "draw_questions": 3} for t in (4, 3)]
    a_rows = fig2a(a_rows) if fig2a else a_rows
    sheets = {"Fig. 3a": {"columns": [], "rows": a_rows},
              "Fig. 3b": {"columns": [], "rows": [
                  {"row_kind": "draw", "strategy": RLM, "draw": 1, "draw_refused_pct": 100.0, "draw_questions": 2},
                  {"row_kind": "false premise", "strategy": RLM, "fp_draw_1_passed_t3": 0, "fp_draw_1_answers": 1,
                   **(fig2fp or {})}]}}
    (d / "fig2").mkdir(exist_ok=True)
    (d / "fig2" / "figure3_numbers.json").write_text(json.dumps({"sheets": sheets}))
    sha1 = sha256_file(d / "g1_collect.jsonl")
    (d / "fig2" / "figure3_provenance.json").write_text(json.dumps(
        {"provenance": {"inputs_sha256": {"g1": prov_sha or sha1}}}))
    return ["--records", str(d / "rec"), "--collect", str(d / "g3_collect.jsonl"), "--rlm-collect",
            str(d / "g1_collect.jsonl"), "--rlm-answers", str(d / "g1" / "runs"), "--g9", str(d / "g9"), "--s6-g1",
            str(d / "s6"), "--fig2-numbers",
            str(d / "fig2" / "figure3_numbers.json"), "--out", str(d / "out.json")]


def selftest(quiet=False) -> bool:
    import contextlib
    import io
    import tempfile
    res = []

    def check(name, ok, detail=""):
        res.append(bool(ok))
        if not quiet or not ok:
            print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail)[:300] if detail and not ok else ''}")

    g = globals()
    saved = {k: g[k] for k in ("key_groups", "N_Q", "GROUP_N")}
    g.update(key_groups=lambda: (list(FX_ORDER), dict(FX_GROUPS), dict(FX_TYPES)), N_Q=len(FX_ORDER),
             GROUP_N=dict(FX_N))
    tmp = Path(tempfile.mkdtemp(prefix="s480_selftest_"))
    k = 0

    def same(g3c, g1c, groups, j3, j1, s6_g1, g3_sets):
        """read_v25's stand-in on fixtures (their rows carry no key hash or header for judge_rows_v25): every row
        chosen is the v2.4 row read."""
        return {**j3, **j1}, {"stand_in": "selftest: the v2.4 rows", "provisional": False}

    def one_v25(g3c, g1c, groups, j3, j1, s6_g1, g3_sets):
        """A stand-in whose choice replaces naive RAG's qa1 row (correctness 5) with a v2.5 row scoring 2."""
        j = {**j3, **j1}
        j[("naive_rag", "qa1")] = {"status": "ok", "scores": {"correctness": 2}}
        return j, {"stand_in": "selftest: one v2.5 row", "provisional": False}

    def run(reader=same, **alter):
        """main() on a fixture with one part altered: (rc, stderr, whether --out was written)."""
        nonlocal k
        k += 1
        d = tmp / f"f{k}"
        d.mkdir()
        argv = fx_write(d, **alter)
        err, out = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            rc = main(argv, check_first=False, v25_reader=reader, anchor=False)
        return rc, err.getvalue(), (d / "out.json").is_file(), d
    try:
        rc, err, wrote, d = run()
        check("the fixture: main() exits 0 and writes its recount", rc == 0 and wrote, err)
        if wrote:
            doc = json.loads((d / "out.json").read_text())
            cn = doc["counts"]
            base = {"answerable_judged": 3, "false_premise_judged": 1, "not_answerable_judged": 2,
                    "judged_no_answer": 0, "unscored": 0, "unscored_by_status": {}}
            want = {"raw_gemini": {**base, "answerable_pass_4": 1, "answerable_pass_3": 2,
                                   "not_answerable_refused_3": 1, "false_premise_pass_4": 0, "false_premise_pass_3": 1, "analyser": "none",
                                   "not_answerable_direct_answer": None},
                    "full_orchestrator": {**base, "answerable_pass_4": 1, "answerable_pass_3": 2,
                                          "not_answerable_refused_3": 1, "false_premise_pass_4": 0, "false_premise_pass_3": 1, "analyser": "on",
                                          "not_answerable_direct_answer": 2},
                    "orch_no_analyser": {**base, "answerable_pass_4": 1, "answerable_pass_3": 2,
                                         "not_answerable_refused_3": 1, "false_premise_pass_4": 0, "false_premise_pass_3": 1,
                                         "analyser": "switched off", "not_answerable_direct_answer": None},
                    "orch_no_planner": {**base, "answerable_pass_4": 1, "answerable_pass_3": 2,
                                        "answerable_judged": 2, "unscored": 1, "unscored_by_status": {"error": 1},
                                        "not_answerable_refused_3": 1, "false_premise_pass_4": 0, "false_premise_pass_3": 1, "analyser": "on",
                                        "not_answerable_direct_answer": 0},
                    RLM: {**base, "answerable_pass_4": 2, "answerable_pass_3": 2, "judged_no_answer": 1,
                          "not_answerable_refused_3": 2, "false_premise_pass_4": 0, "false_premise_pass_3": 0, "analyser": "none",
                          "not_answerable_direct_answer": None}}
            for c, w in want.items():
                check(f"counts by hand: {c}", cn[c] == w, f"{cn[c]} want {w}")
            check("the recount records every input (ten answers.json, two collects and sidecars, answers.jsonl, the "
                  "S6 set's SHA256SUMS) with its sha256", len(doc["inputs"]) == 16 and all(
                      v["sha256"] == sha256_file(Path(v["path"])) for v in doc["inputs"].values()))
            check("stress_records by hand: 6 answers, 12 words, 8 calls of which 1 failed and 1 cut, 1 direct answer; "
                  "no G9 row in the collect, so none in counts; no draw_counts",
                  doc["stress_records"][STRESS[0]] == {"answers": 6, "no_text": 0, "words": 12, "model_calls": 3,
                                                       "failed_calls": 1, "cut_calls": 1,
                                                       "not_answerable_direct_answer": 1}
                  and doc["stress_records"][STRESS[1]]["model_calls"] == 0
                  and not set(STRESS) & set(cn) and "draw_counts" not in doc, str(doc.get("stress_records")))
            check("reproduction recorded: RLM-10 2 of 3 at 4 and 3, 2 of 2 refused, 0 of 1 false premise",
                  {kk: (v["here"], v["of"]) for kk, v in doc["reproduced"]["rlm_10_draw_1_vs_figure_2"].items()}
                  == {"answerable_pass_4": (2, 3), "answerable_pass_3": (2, 3), "not_answerable_refused_3": (2, 2),
                      "false_premise_pass_3": (0, 1)})
            check("D160 (11): false premise counted at 4 and at 3 (G3 qf1 scored 3 passes at 3 only); with no "
                  "draw-1 count at 4 in Figure 3, the count at 4 is recorded as not compared",
                  cn["naive_rag"]["false_premise_pass_4"] == 0 and cn["naive_rag"]["false_premise_pass_3"] == 1
                  and "false_premise_pass_4" in doc["reproduced"].get("not_compared", {}))
            check("D188: counts_v24 written beside counts; with every row v2.4 they are equal",
                  doc.get("counts_v24") == cn and doc["reproduced"]["v24_anchor"]["compared"] is False)
        rc, err, wrote, d = run(g3_rows=lambda rows: rows + [
            {**r, "config": c, "answer_key": r["answer_key"].replace("|raw_gemini|", f"|{c}|")} for c in STRESS
            for r in rows if r["config"] == "raw_gemini" and r["draw"] == 1])
        doc = json.loads((d / "out.json").read_text()) if wrote else {}
        check("a collect holding G9's rows: both set-ups join counts and counts_v24",
              rc == 0 and wrote and set(STRESS) <= set(doc["counts"]) and set(STRESS) <= set(doc["counts_v24"])
              and doc["counts"][STRESS[0]]["not_answerable_direct_answer"] == 1, err)
        rc, err, wrote, d = run(g3_rows=lambda rows: rows + [
            {**r, "config": STRESS[0], "answer_key": r["answer_key"].replace("|raw_gemini|", f"|{STRESS[0]}|")}
            for r in rows if r["config"] == "raw_gemini" and r["draw"] == 1 and r["question_id"] != "qa2"])
        check("refused, nothing written: a collect holding part of G9's rows", rc == 1 and "have no row" in err
              and not wrote, err)
        cd = {("full_orchestrator", "qa1", 1): {"status": "ok", "scores": {"correctness": 5}},
              ("full_orchestrator", "qa2", 1): {"status": "ok", "scores": {"correctness": 3}},
              ("full_orchestrator", "qa3", 1): {"status": "no_answer"},
              ("full_orchestrator", "qa1", 2): {"status": "error"}, (RLM, "qa1", 3): {"status": "ok", "scores": {"correctness": 4}}}
        got = count_draws(cd, FX_GROUPS, ["qa1", "qa2", "qa3", "qf1"])
        check("count_draws by hand: a no_answer counts and fails, an unscored row and no row are left out",
              got["full_orchestrator|1|4"] == [1, 3] and got["full_orchestrator|1|3"] == [2, 3]
              and got["full_orchestrator|2|4"] == [0, 0] and got[f"{RLM}|3|4"] == [1, 1]
              and len(got) == 11 * 3 * 2, str(got))
        keep = lambda **k: draw_keep({"question_id": "qa1", **k}, ["qa1"], {"full_orchestrator"})   # noqa: E731
        check("draw_keep: S6G7G3's rows at draws 2 and 3 of a G7 set-up, no other row there; baselines at every draw",
              keep(config="full_orchestrator", draw=2, a={}, questions="all")
              and not keep(config="full_orchestrator", draw=3, a={}) and keep(config="full_orchestrator", draw=2)
              and keep(config="naive_rag", draw=2, a={}) and not keep(config=RLM, draw=1))
        rc, err, wrote, d = run(reader=one_v25)
        doc = json.loads((d / "out.json").read_text()) if wrote else {}
        check("D188: a v2.5 row chosen changes counts (naive RAG passes 0 of 3 at 4, 1 at 3), not counts_v24",
              rc == 0 and wrote and (doc["counts"]["naive_rag"]["answerable_pass_4"],
                                     doc["counts"]["naive_rag"]["answerable_pass_3"],
                                     doc["counts_v24"]["naive_rag"]["answerable_pass_4"],
                                     doc["counts_v24"]["naive_rag"]["answerable_pass_3"]) == (0, 1, 1, 2), err)
        anc = {c: dict(zip(ANCHOR_FIELDS, v)) for c, v in ANCHOR_V24.items()}
        moved = json.loads(json.dumps(anc))
        moved["orch_no_planner"]["not_answerable_refused_3"] += 1
        check("D188 anchor_v24: the pre-D188 counts pass; one count changed is named",
              anchor_v24(anc) == [] and anchor_v24(moved) == [
                  "orch_no_planner not_answerable_refused_3: 2 here, the pre-D188 recount 1"], str(anchor_v24(moved)))
        k += 1
        d = tmp / f"f{k}"
        d.mkdir()
        argv = fx_write(d)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = main(argv, check_first=False, v25_reader=same)
        check("D188 (review of build 3, F1): with the inputs given by path ANCHOR_V24 is still compared: the "
              "fixture's counts are not the pre-D188 recount, so the run exits 2 and writes nothing",
              rc == 2 and "ANCHOR_V24" in err.getvalue() and not (d / "out.json").is_file(), err.getvalue()[:200])
        rc, err, wrote, d = run(fig2fp={"fp_draw_1_passed_t4": 0})
        rep4 = json.loads((d / "out.json").read_text())["reproduced"] if wrote else {}
        check("D160 (11): a Figure 3 draw-1 count at 4 is compared when present (0 of 1 equal: written)",
              rc == 0 and wrote and rep4["rlm_10_draw_1_vs_figure_2"].get("false_premise_pass_4") ==
              {"here": 0, "figure_2": 0, "of": 1} and not rep4.get("not_compared"), err)

        def first(rows, pred, **ch):
            """rows with the first row matching pred changed by ch."""
            rows = [dict(r) for r in rows]
            r = next(r for r in rows if pred(r))
            r.update(ch)
            return rows
        nr = lambda r: r["config"] == "naive_rag" and r["question_id"] == "qn1"            # noqa: E731
        refusals = [
            ("a (config, question, draw) row repeated", 1, "repeats",
             dict(g3_rows=lambda rows: rows + [rows[0]])),
            ("a sidecar's rows not the file's", 1, "rows,", dict(side3=lambda s: {**s, "rows": s["rows"] + 1})),
            ("a sidecar's set not G3", 1, "set 'G1'", dict(side3=lambda s: {**s, "set": "G1"})),
            ("a sidecar's run_sha256 not its rows'", 1, "run_sha256 values",
             dict(side3=lambda s: {**s, "run_sha256": "e" * 64})),
            ("an answer judged with the other group's prompt", 1, "other group's prompt",
             dict(g3_rows=lambda rows: first(rows, nr, answerable_prompt=True))),
            ("a draw-1 answer with no judge row", 1, "have no row",
             dict(g3_rows=lambda rows: [r for r in rows if not nr(r)])),
            ("a judge no_answer on an answer with text", 1, "judge no_answer, record no_text False",
             dict(g3_rows=lambda rows: first(rows, nr, a={"status": "no_answer"}))),
            ("an answer with no text judged ok", 1, "judge scored, record no_text True",
             dict(recs=lambda rec: {**rec, "naive_rag": first(rec["naive_rag"], lambda r: r["question_id"] == "qn1",
                                                               generated_answer="  ")})),
            ("the analyser switched off on some answers only", 1, "switched off on 1 answers",
             dict(recs=lambda rec: {**rec, "orch_no_planner": first(
                 rec["orch_no_planner"], lambda r: r["question_id"] == "qa1",
                 generation={"analysis": {"status": "switched_off"}})})),
            ("an answers.jsonl not matching MANIFEST.sha256", 1, "is not its line",
             dict(rlm_lines=lambda ls: ls)),          # MANIFEST rewritten below for this case
            ("a G9 draw 1 missing a question", 1, "is not the",
             dict(g9_recs=lambda g: {**g, STRESS[1]: [r for r in g[STRESS[1]] if r["question_id"] != "qf1"]})),
            ("a draw 1 missing a question", 1, "is not the",
             dict(recs=lambda rec: {**rec, "raw_gemini": [r for r in rec["raw_gemini"] if r["question_id"] != "qf1"]})),
            ("the two collects under different run_sha256", 1, "the G3 collect is under run_sha256",
             dict(g3_rows=lambda rows: [{**r, "run_sha256": "e" * 64} for r in rows],
                  side3=lambda s: {**s, "run_sha256": "e" * 64})),
            ("Figure 3's RLM-10 pass at 4 changed to 1 of 3", 2, "RLM-10 answerable_pass_4: 2 of 3 here, Figure 3 1 of 3",
             dict(fig2a=lambda rows: [{**r, "draw_pass_rate_pct": 100 / 3} if r["threshold"] == 4 else r
                                      for r in rows])),
            ("a Figure 3 share that is not a whole count", 2, "is not a whole count",
             dict(fig2a=lambda rows: [{**r, "draw_pass_rate_pct": 50.0} if r["threshold"] == 3 else r
                                      for r in rows])),
            ("a Figure 3 written from another G1 collect", 2, "Figure 3 was not written from this G1 collect",
             dict(prov_sha="0" * 64)),
            ("Figure 3's RLM-10 false premise at 4 on draw 1 changed to 1 of 1", 2,
             "RLM-10 false_premise_pass_4: 0 of 1 here, Figure 3 1 of 1", dict(fig2fp={"fp_draw_1_passed_t4": 1})),
        ]
        for name, want_rc, want_msg, alter in refusals:
            if name.startswith("an answers.jsonl"):
                k += 1
                d = tmp / f"f{k}"
                d.mkdir()
                argv = fx_write(d)
                (d / "g1" / "MANIFEST.sha256").write_text(f"{'0' * 64}  runs/exp_01__{RLM}__{INDEX}/answers.jsonl\n")
                err = io.StringIO()
                with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                    rc = main(argv, check_first=False, v25_reader=same, anchor=False)
                rc, err, wrote = rc, err.getvalue(), (d / "out.json").is_file()
            else:
                rc, err, wrote, _ = run(**alter)
            check(f"refused, nothing written: {name}", rc == want_rc and want_msg in err and not wrote,
                  f"rc {rc}, wrote {wrote}: {err.strip()}")
        g["GROUP_N"] = {"answerable": 2, "false_premise": 2, "not_answerable": 2}
        rc, err, wrote, _ = run()
        check("refused, nothing written: a key of other sizes than the known ones", rc == 2 and "the D5 key gives"
              in err and not wrote, f"rc {rc}: {err.strip()}")
        # D155: frozen_default() returns a frozen input only when every pinned file of its set has its pinned sha256
        fz = tmp / "frozen"
        pins = {}
        for i, (s, r) in enumerate(FROZEN.values()):
            f = fz / s / r / "pinned.txt"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"frozen {i}\n")
            pins[(s, f"{r}/pinned.txt")] = sha256_file(f)
        fake = lambda s, r=".": fz / s / r                                   # noqa: E731
        saved_pin = g["FROZEN_PIN"]
        try:
            g["FROZEN_PIN"] = pins
            ok = all(frozen_default(k, fake) == fz / s / r for k, (s, r) in FROZEN.items())
            (fz / FROZEN["collect"][0] / FROZEN["collect"][1] / "pinned.txt").write_text("changed\n")
            try:
                frozen_default("collect", fake)
                refused = ""
            except Fail as e:
                refused = str(e)
            check("D155 frozen_default: the pinned files pass; a changed frozen file is refused",
                  ok and "the committed recount recorded" in refused, refused)
        finally:
            g["FROZEN_PIN"] = saved_pin
        # D155: the output names no time, HEAD or working-tree state, and its command names no --out
        g["GROUP_N"] = dict(FX_N)
        rc, err, wrote, d = run()
        doc = json.loads((d / "out.json").read_text()) if wrote else {}
        pv = doc.get("provenance") or {}
        check("D155 output: no git_head, written_utc or script_dirty_vs_head; the command names no --out",
              rc == 0 and not {"git_head", "written_utc", "script_dirty_vs_head"} & set(pv)
              and "--out" not in pv.get("command", "--out"), f"rc {rc}: {sorted(pv)} {pv.get('command')}")
    finally:
        g.update(saved)
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    # D188: read_v25 itself on the frozen collects (committed, findings/recompute/fig4_inputs and fig2_inputs) and the
    # frozen S6G1 set, with the D5 key restored: every G3 draw-1 row chosen is the row read_collect read (no out_s6_g3
    # beside it, so G3's 480 answers of changed questions await S6), and RLM-10's 60 come from key v2.5
    try:
        order, groups, _ = key_groups()
        g3c, g1c, s6 = FR.frozen(*FROZEN_41D3), FR.frozen(*FROZEN["rlm_collect"]), FR.frozen(*FROZEN["s6_g1"])
        j3, _, _ = read_collect(g3c, "G3", G3, groups)
        j1, _, _ = read_collect(g1c, "G1", [RLM], groups)
        judged, rec = read_v25(g3c, g1c, groups, j3, j1, s6)
        # D203 (2 Nov): out_s6_g3 is frozen in the S6G1 set, so G3's 480 answers of changed questions come from key v2.5
        # and every other G3 row chosen is the v2.4 row read
        n25 = sum(1 for k, v in judged.items() if k[0] != RLM and v != j3.get(k))
        check("D203 read_v25 on the frozen collects and the S6 set: G3's 480 answers of changed questions and RLM-10's "
              "60 from key v2.5, none awaiting; every other G3 row the v2.4 row read; not provisional; no 'draw' rows",
              set(judged) - {k for k in judged if k[0] == RLM} == set(j3) and n25 <= 480
              and (rec["G3"]["awaiting_s6"], rec["G1"]["awaiting_s6"], rec["G1"]["from_v25"]) == (0, 0, 60)
              and rec["G3"]["from_v25"] == 480 and not rec["provisional"] and rec["G3"]["s6_absent"] == []
              and rec["draws"] is None,
              json.dumps({n: {k: v for k, v in rec[n].items() if k != "sources"} for n in ("G3", "G1")}))
        try:
            read_v25(g3c, g1c, groups, j3, j1, g3c.parent)
            refused = ""
        except Fail as e:
            refused = str(e)
        check("read_v25: a folder without out_s6_g1 is refused (no key v2.4 fallback)", "key v2.5 only" in refused,
              refused)
    except (Fail, FR.FrozenInputError) as e:
        check("D188 read_v25 on the frozen collects", False, str(e))
    n = sum(res)
    print(f"selftest: {n} of {len(res)} checks pass")
    return n == len(res)


def main(argv=None, check_first=True, v25_reader=None, anchor=True):
    """v25_reader (selftest only): a stand-in for read_v25, for fixtures whose rows judge_rows_v25 would refuse.
    anchor False (selftest only): the fixtures are not the real questions, so ANCHOR_V24 is not compared."""
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["selftest"]:
        return 0 if selftest() else 1
    if check_first and not selftest(quiet=True):
        print("REFUSED: the selftest fails, nothing written (run `selftest` to see which check)", file=sys.stderr)
        return 1
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--records", help="the folder S472 pull wrote (PULL.json, findings/runs/...); default the "
                                      "frozen copy (fig4_records_1023.tar)")
    ap.add_argument("--collect", help="G3's s3_guard.py collect output (sidecar beside it); default the frozen "
                                      "findings/recompute/fig4_g9_inputs/g3_collect.jsonl (G9 judged)")
    ap.add_argument("--rlm-collect", help="G1's s3_guard.py collect output (sidecar beside it); default the frozen "
                                          "findings/recompute/fig2_inputs/g1_collect.jsonl")
    ap.add_argument("--rlm-answers", help="a runs folder holding exp_01__rlm_10__exp_v4_s20_n0/answers.jsonl, "
                                          "MANIFEST.sha256 beside it; default the frozen copy (fig2_g1r15_inputs.tar)")
    ap.add_argument("--g9", help="G9's answers (runs/<run>/answers.json); default the frozen findings/recompute/"
                                 "g9_inputs")
    ap.add_argument("--s6-g1", help="the folder holding out_s6_g1 and out_s6_g1r15, RLM-10's key v2.5 rows; default "
                                    "the frozen findings/recompute/fig3_s6_inputs (S528)")
    ap.add_argument("--fig2-numbers", default=str(FIG2_NUMBERS), help="Figure 3's numbers (the known values)")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    given = {"records": a.records, "collect": a.collect, "rlm_collect": a.rlm_collect, "rlm_answers": a.rlm_answers,
             "g9": a.g9, "s6_g1": a.s6_g1}
    try:
        ins = {k: Path(v).expanduser().resolve() if v is not None else frozen_default(k) for k, v in given.items()}
    except Fail as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    rec, g3c, g1c, runs, g9, s6_g1 = (ins[k] for k in ("records", "collect", "rlm_collect", "rlm_answers", "g9",
                                                       "s6_g1"))
    fig2, out = (Path(x).expanduser().resolve() for x in (a.fig2_numbers, a.out))
    # D155: the command that writes this output (--out, where it is written, left out), with every input as given
    command = ["uv", "run", "--frozen", "python", SCRIPT]
    for k, flag in (("records", "--records"), ("collect", "--collect"), ("rlm_collect", "--rlm-collect"),
                    ("rlm_answers", "--rlm-answers"), ("g9", "--g9"), ("s6_g1", "--s6-g1")):
        if given[k] is not None:
            command += [flag, rel(ins[k])]
    if fig2 != FIG2_NUMBERS.resolve():
        command += ["--fig2-numbers", rel(fig2)]
    try:
        order, groups, types = key_groups()
        recs, files = read_g3_records(rec, order, types)
        rr, rlm_p, man = read_rlm_records(runs, order)
        recs.update(rr)
        rg9, g9_files, stress = read_g9_records(g9, order, types, groups)
        recs.update(rg9)
        g9_judged = any(json.loads(x).get("config") in STRESS for x in g3c.read_text().splitlines() if x.strip())
        g3_sets = G3 + STRESS if g9_judged else G3
        setups = G3 + (STRESS if g9_judged else []) + [RLM]
        j3, side3, run3 = read_collect(g3c, "G3", g3_sets, groups)
        j1, side1, run1 = read_collect(g1c, "G1", [RLM], groups)
        if run3 != run1:
            raise Fail(f"the G3 collect is under run_sha256 {run3[:12]}, the G1 collect under {run1[:12]}")
        counts_v24 = count(order, groups, recs, {**j3, **j1}, setups)
        judged, jrec = (v25_reader or read_v25)(g3c, g1c, groups, j3, j1, s6_g1, g3_sets)
        counts = count(order, groups, recs, judged, setups)
        draws = jrec.pop("draws", None)
        draw_counts = count_draws(draws["cells"], groups, draws["subset"]) if draws else None
    except Fail as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    try:
        if anchor:
            probs = anchor_v24(counts_v24)
            if probs:
                raise NotReproduced("the v2.4 recount of the inputs read is not the pre-D188 recount (ANCHOR_V24): "
                                    + "; ".join(probs))
            anchor = {"compared": True, "set_ups": len(ANCHOR_V24), "fields": list(ANCHOR_FIELDS), "equal": True,
                      "inputs": "frozen defaults" if all(v is None for v in given.values()) else "given by path"}
        else:
            anchor = {"compared": False, "why": "selftest fixture, not the real questions"}
        reproduced = reproduce(order, groups, counts, fig2, sha256_file(g1c))
        reproduced["v24_anchor"] = anchor
    except NotReproduced as e:
        print(f"REPRODUCTION FAILED, nothing written: {e}", file=sys.stderr)
        return 2
    inputs = {f"answers_json:{c}": files[c] for c in G3}
    inputs.update({f"answers_json:{c}": g9_files[c] for c in STRESS})
    inputs.update({"g3_collect": g3c, "g3_collect_sidecar": side3, "g1_collect": g1c, "g1_collect_sidecar": side1,
                   "rlm_answers_jsonl": rlm_p, "s6_g1_sums": s6_g1 / "SHA256SUMS"})
    doc = {"what": "Figure 4's judged counts per set-up on draw 1, counted apart from S472 and S463 (O1, 24 October); "
                   "S472's reproduction gate (4) checks its counts against these",
           # D155: no git HEAD, working-tree state or write time (two runs on the same inputs gave two files);
           # the script and every input are named by sha256, every path relative to the repository
           "provenance": {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
                          "command": shlex.join(command),
                          "frozen_defaults": {k: f"{FROZEN[k][0]}:{FROZEN[k][1]}" for k, v in given.items()
                                              if v is None},
                          "python": platform.python_version(), "model_calls": 0},
           "inputs": {k: {"path": rel(p), "sha256": sha256_file(p)} for k, p in inputs.items()},
           "known_inputs": {"figure3_numbers": {"path": rel(fig2), "sha256": sha256_file(fig2)},
                            "rerun_keys": {"path": rel(RERUN_SH), "sha256": sha256_file(RERUN_SH)},
                            "figure3_provenance": {"path": rel(fig2.parent / "figure3_provenance.json"),
                                                   "sha256": sha256_file(fig2.parent / "figure3_provenance.json")},
                            "rlm_manifest": {"path": rel(man), "sha256": sha256_file(man)}},
           "rules": {"score_of_group": SCORE_OF_GROUP,
                     "score_of_group_source": "S463.METRIC, scripts/S463_fig2_ranking.py (copied, not imported)",
                     "pass_thresholds": list(PASS_T), "refused_threshold": REFUSED_T,
                     "false_premise_thresholds": list(FP_T),
                     "draw": 1, "group_n": GROUP_N},
           "reproduced": reproduced,
           "judge_rows_v25": {"what": "D188: counts is on the draw-1 rows scripts/judge_rows_v25.py chooses (an "
                                      "answer's key v2.5 row where S6 judged it, else its key v2.4 row); counts_v24 on "
                                      "the collects' key v2.4 rows",
                              "script_sha256": sha256_file(ROOT / "scripts" / "judge_rows_v25.py"), **jrec},
           "counts": counts,
           "counts_v24": counts_v24,
           "stress_records": stress,
           **({} if draw_counts is None else {"draw_counts": draw_counts})}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"reproduced: D5 key {N_Q} ({', '.join(str(v) for v in GROUP_N.values())}); "
          + ("v2.4 recount equal to ANCHOR_V24; " if anchor["compared"] else "v2.4 anchor not compared (fixture); ")
          + f"RLM-10 draw 1 equal to Figure 3's Source Data: "
          + ", ".join(f"{k} {v['here']} of {v['of']}" for k, v in reproduced["rlm_10_draw_1_vs_figure_2"].items()))
    if "G3" in jrec:
        print(f"judge rows (D188): G3 {jrec['G3']['from_v25']} from key v2.5, {jrec['G3']['awaiting_s6']} awaiting S6; "
              f"RLM-10 {jrec['G1']['from_v25']} from key v2.5, {jrec['G1']['awaiting_s6']} awaiting S6; "
              f"counts that differ from the v2.4 recount: "
              f"{sum(1 for c in ALL for k in counts[c] if counts[c][k] != counts_v24[c][k])}")
    for c in setups:
        r = counts[c]
        print(f"{c:26s} pass4 {r['answerable_pass_4']:2d} pass3 {r['answerable_pass_3']:2d} of "
              f"{r['answerable_judged']}  refused {r['not_answerable_refused_3']:2d} of {r['not_answerable_judged']}  "
              f"fp4 {r['false_premise_pass_4']:2d} fp3 {r['false_premise_pass_3']:2d} of {r['false_premise_judged']}  "
              f"no_answer {r['judged_no_answer']}  "
              f"unscored {r['unscored']}  direct {r['not_answerable_direct_answer']}")
    print(f"wrote {rel(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
