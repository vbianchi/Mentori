#!/usr/bin/env python3
"""S470 - plan row L1: MiniCheck and the text-overlap metrics on the Figure 2 answers (G1), per answer, for Figure 5.

Why. Figure 5 compares the signals, each measured against two references (D35, experiments/LIST.md "Figure 5"): the
answer key (correctness, concepts) and the papers (grounding). The deposited MiniCheck checked each answer against the
key only (analysis_minicheck.py:131-175); S19 measured the same claims against the source papers. Both, and the
lexical baselines the reviewers asked for (S07: ROUGE-L, METEOR, BERTScore; S382 and S141: number overlap and bge-m3
similarity), were computed on the deposited exp04 answers. This script computes them on G1's re-run answers: six
strategies (single_pass, multi_hop, verified_pass, rlm_5, rlm_10, rlm_20) x 135 questions x 3 draws = 2,430 answers.
No metric is retyped: each is the deposited function, or the function an earlier script lifted and gated, called the
way that script calls it.

The answers. <inputs>/runs/exp_01__<config>__exp_v4_s20_n0/answers.jsonl, each listed with its sha256 in
<inputs>/MANIFEST.sha256 (sha256sum format, paths relative to <inputs>); a file whose sha256 differs is refused. An
answer is the last line of its answer_key (exp_01's rule, experiments/scorers/records.py WHAT A RUN IS), and the
reading is cross-checked against records.read_run. The 2,430 (config, question, draw) cells must all be there, once.
Every row records the answer's group, draw, config, stop_reason (generation.stop_reason) and status (records.py: ok,
error, no_answer).

Selection (LIST.md Rule 8, Rule 10). The group comes from the D5 key's answer type as the runner pins it
(experiments/runner/experiment.py:101-102, read through records.group_of): extractive and synthesis are answerable
(86 questions), refutation is false_premise (10), not_answerable (39). The runner's answerable flag must agree with
S373_rejudge_v2.AS_V1's on all 135 (it is the same file, ground_truth_v2_4_as_v1.json, sha256-pinned by the runner),
or the run is refused. Every one of the 2,430 answers gets a row in each stage. On the 39 every signal is null with
the reason "not applicable". On an empty answer (empty after strip) a signal not defined on empty text is null with
the reason "no answer", and a signal defined on empty text takes its value (Rule 10: "an empty answer recalled
nothing, but it makes no claim whose support could be measured"):
  key stage    precision null ("no answer": no claims to check). Recall 0.0: Rule 10's value for a recall on an empty
               text (an empty text recalls no key sentence, as concept recall is 0), which is also what the deposited
               score_faithfulness returns there (analysis_minicheck.py:120-129, a short-circuit that scores nothing).
               F1 0.0: 2PR/(P+R) is 0 whenever recall is 0, the deposited function's value. The deposited
               run_minicheck_scoring writes no row at all for an empty answer (analysis_minicheck.py:241-242). Q3.
  papers       precision null ("no answer")
  overlap      ROUGE-L 0.0 (rouge_score), METEOR 0.0 (nltk) and number overlap 0.0 (the deposited score_all's empty
               branch, analysis_deterministic_scorer.py:688-697) as those functions define them; the citation-stripped
               number overlap is the deposited compute_number_overlap on the empty text (0.0, or 1.0 when the key holds
               no number: the function's "N/A" value, analysis_deterministic_scorer.py:202-204; S141's det_record
               writes the row as unscorable instead); BERTScore null ("no answer": bert_score cannot encode an empty
               candidate with this transformers, bert_score/utils.py:192 raises) and the similarity null ("no answer":
               S141_runner.scorers.semantic_similarity returns None on an empty text).
Two more nulls the deposited code forces, counted and printed: "no claim sentence" (a non-empty answer that
decompose_to_sentences splits into nothing: it drops every fragment under 20 characters and every line that starts
with "|" or "---", analysis_minicheck.py:88-92, so a short answer such as "0.80" or an answer that is only a table
has no claim; score_faithfulness then returns 0.0 for all three without calling MiniCheck, and the deposited
run_minicheck_scoring raises on such a row, so all three are null; S19 writes no row for it, so its papers precision
is null) and "no key sentence" (a key that splits into nothing). The difference from an empty answer: a text with no
claim sentence may still hold the key's fact (an answer "0.80" to a question whose key is 0.80), and nothing measured
whether it does, so its recall is unknown; an empty text holds nothing. The six questions dropped under D7 are absent
from the key, as in S384 and S19: answers on them are skipped and counted (G1 asks none of them, so the count is 0;
the six are listed in the selection line).

MiniCheck's own cut. MiniCheck-Flan-T5 splits each document into chunks of up to 500 words (minicheck.py:148,
inference.py:102-121), builds "predict: " + chunk + "</s>" + claim and tokenizes it with max_length 2048 and
truncation (inference.py:233-246): a chunk long in tokens (repeated citations such as [11_asf_burkina_faso.pdf:p0])
pushes the claim past the cut and the model scores the chunk alone. Under LOCK.toml [text] scorer_input = "whole" no
signal is computed on a cut input, so before scoring, every (chunk, claim) input is built by MiniCheck's own code
(its score() run with the model call replaced by a recorder, mc_input_tokens) and counted by its own tokenizer. A
side with any input over 2,048 tokens is null with the reason "over the encoder's 2048-token limit" (key stage: the
precision side makes precision and F1 null, the recall side recall and F1; papers: precision, and the answer is not
scored), counted per strategy. The row's detail.minicheck_inputs holds each side's input count, cut claims and
longest input.

Errored answers. records.py gives status "error" to an answer whose generation.error is set. The number overlap
column is the deposited score_all as S382 runs it, and score_all takes its empty branch for an errored answer whether
or not it holds text (analysis_deterministic_scorer.py:688, "if not answer or error"), so an errored answer with text
gets number overlap 0.0 while every other signal scores its text. Such rows carry detail.number_overlap_branch =
"deposited empty-or-error branch"; the selection line counts them and lists the first ten.

Stages. Each runs its reproduction gate first (README.md:75-79) and exits non-zero, writing nothing, when it fails.
  key      MiniCheck-Flan-T5-Large (S384.load_minicheck: lytang checkpoint from S384.hf_cache, offline, pinned to
           --device, float32; punkt_tab required) precision, recall and F1 of each answer against the key's
           expected_answer, both directions, by the deposited score_faithfulness and decompose_to_sentences as S384
           lifts them (sha256 pinned). Gate: S384's own G2 (gate_g2): 20 deposited rows rescored with the v1 key, the
           scorer's outputs kept; then key_signals, this stage's own call, on the same 20 answers and v1 keys must
           ask MiniCheck nothing the G2 pass did not (every call found among them) and give the deposited P, R, F1
           and per-sentence probabilities.
  papers   MiniCheck precision of each answer's claims against its question's source paper(s), whole: S19's --full-doc
           path, "\\n\\n".join of the papers' texts from findings/recompute/S18_evidence_docs.jsonl (join_docs), S19.check
           (the max over MiniCheck's own chunks), called on four claims at a time so progress shows inside an answer
           (each claim is scored on its own, so the grouping changes nothing). The source files are the key's
           (S373.AS_V1 source_files): S19 read them from S18_evidence_manifest.json's sizing, which has no entry for
           OOD_041 to OOD_050 (Q56 gave the ten their v2.4 evidence paper in the key); every question where the two
           differ is printed. S19's retrieval mode (k3) is not built. Gate: the first 2 rows of
           findings/recompute/S19_minicheck_source_fulldoc.jsonl (09_seqkit_TE3 multi_hop, 09_seqkit_CO2
           single_pass; 9 claims) rescored by this stage's own papers_docs and papers_signals: the same files, claims,
           labels and precision, every probability within 1e-4. S19 scored 09_seqkit_TE3 multi_hop on an input over
           MiniCheck's cut (its one claim, a "[Max turns reached] SEARCH: ..." query, is long; S19 stores claims cut at
           300 characters), so this stage writes that row null; the gate scores it all the same (keep_cut) to
           reproduce S19's values, and requires the null.
  overlap  Against the key's expected_answer: S07's ROUGE-L F1, METEOR and BERTScore F1 (S07.rouge_l, S07.meteor,
           S07.bertscore: roberta-large, lang en, batch 32, no fallback), number overlap as S382 computes it (the
           deposited score_all's number_overlap, run through S382.score with the key's answerable flag), number
           overlap on the
           citation-stripped answer as S141's det_record computes it (the deposited compute_number_overlap on
           S141_runner.scorers.strip_citations), and bge-m3 similarity as S141's similarity stage computed it on the
           v2.4 key (S141_runner.scorers.semantic_similarity: the whole answer and key, normalised, dot product),
           with the encoder pinned to LOCK.toml [retrieval] embedding (hf_repo, revision, local_files_only, device).
           LOCK.toml [text] scorer_input = "whole": an encoder never computes on a cut text. bert_score cuts both
           texts at model_max_length (bert_score/utils.py:200-201, 512 word pieces for roberta-large, specials
           included) and SentenceTransformer at max_seq_length (8,192 for bge-m3, specials included), so a row whose
           answer or key is longer is written null with the reason "over the encoder's 512-token limit" (8,192), and
           counted per strategy; the metric is not called on it. No splitting variant is built. Gates, each through
           this stage's own OverlapFns: S07's own reproduce_v1 with S07's rouge_l, meteor and bertscore names pointed
           at OverlapFns (ROUGE-L and METEOR on all 528 v1 rows exactly, BERTScore on its 20 rows within 1e-4);
           S382's own gate (the lifted scorer on the v1 key reproduces the deposit on all 828 rows), then
           OverlapFns.number_overlap on the 528 answerable v1 rows equal to the deposit's number_overlap; S141's own
           reproduce for the similarity stage with its semantic_similarity name pointed at OverlapFns.similarity and
           the pinned encoder (20 v1 rows within 1e-4); and OverlapFns.number_overlap_stripped on every v1 row of
           S141's deterministic artefact that carries a number overlap, exactly equal.

Order and shards. --draws picks the draws (default 1 for papers, 1,2,3 for key and overlap). Within the run the
answers go draw by draw, and within a draw question by question in the key's order, all six strategies of a question
together, so a stopped run is balanced across strategies. --shard i/n keeps the answers whose question and draw (the
answer_key's last two parts) hash to i: sha256 of "<question_id>|d<draw>", its first 16 hex digits as an integer, mod
n. The split depends on nothing but the key, so it is the same in every process and on every resume, and the six
strategies of a question stay in one shard. A stage keeps the n of its first session (recorded in the header); a run
with another n is refused, and so is one started while a process with another n runs. --threads N sets
torch.set_num_threads before any model loads.

Outputs, under --outdir (default findings/recompute/L1/):
  header.json                          the provenance: identity (key, inputs, deposited code), each stage's
                                       parameters (this script's sha256, every lifted or imported file's sha256,
                                       uv.lock's, the files each gate compares with, the checkpoint, the encoders'
                                       snapshots, nltk data) and shard count, and one entry per session (git commit,
                                       device, threads, torch and package versions, LOCK.toml sha256 read from disk,
                                       each gate's message)
  <stage>/<stage>.shard<i>of<n>.jsonl  one row per answer, keyed by answer_key, each written and fsynced as it is
                                       done (the overlap stage computes 120 answers per batch, then writes them)
A run resumes: an answer_key already in any file of the stage is skipped. Before it reads which rows are done, a run
takes its shard's lock (flock, not waiting; the lock files live in the system temp folder, named from the outdir's
path, so a failed gate leaves no trace in the outdir): a second process on the same shard is refused at once, before
any model loads. Under that lock an unfinished last line of its own file (a process killed while writing) is cut off;
an unfinished last line in another shard's file is read as not done; a damaged line that ends in a newline is refused.
A run is also refused, before any model loads, when the existing header's key, inputs manifest, answers files,
deposited code or this stage's parameters (this script's sha256 included) differ from this run's, when an answer_key
is written twice, or when a written row's answer sha256 is not the answer's. Device and threads are recorded, not
part of the identity (the device on every row and session, the threads on the session): each process's gate holds
its device to the deposited values within 1e-4.

Network. HF_HUB_OFFLINE is 1 for the whole process, and nltk.download is replaced by a lookup that only finds the
package on disk and stops the run when it is missing (S07.meteor calls nltk.download on every call,
S07_baseline_metrics.py:503-507, which reached the network and could have replaced the data the header hashed).

Other modes, writing nothing: --stage verify (read the stages' rows: the Rule 8 and Rule 10 checks on each row,
counts of nulls per reason and strategy; it fails, listing them per draw and strategy, when any selected answer of
the draws asked has no row, unless --partial; --verify-stages narrows the stages) and --stage count-limits (the
tokenizers only, no model: per strategy, how many of the answers on the 96 scored questions exceed BERTScore's 512
and bge-m3's 8,192 tokens, and how many key-stage answers have a MiniCheck input over 2,048 tokens on each side).
--gate-only runs a stage's gate and stops. --limit N and --questions Q1,Q2 narrow a run, for dry runs.

Reproduce (the Beelink; clone ~/projects/mentori-runs-l1 at the commit that holds this script, inputs ~/l1_inputs).
The upstream deposit (exp04 results, analysis_minicheck.py, analysis_deterministic_scorer.py) and the MiniCheck
checkpoint are found as S384 finds them: MENTORI_PAPER (machine.py: else data/upstream, then a sibling checkout) and
MENTORI_HF_CACHE (S384.hf_cache: else <upstream>/data/hf_cache). D113's trial ran S384 and S19 in this clone on 21
October; whether it set the two is not recorded (UNVERIFIED), so the first command prints where they resolve.
roberta-large (snapshot 722cf37b, the laptop's) and bge-m3 (LOCK.toml [retrieval] revision 5617a9f6) are read from
~/.cache/huggingface/hub offline; LOCK.toml says the bge-m3 snapshot was read on the Studio and the laptop only, so
they are copied from the laptop once. Once per machine:

    # on the laptop: the two encoders, as the laptop's cache holds them
    rsync -a -e "ssh -p 2222" ~/.cache/huggingface/hub/models--roberta-large \
        ~/.cache/huggingface/hub/models--BAAI--bge-m3 valeriob@100.105.190.7:.cache/huggingface/hub/
    # on the Beelink
    cd ~/projects/mentori-runs-l1
    cat ~/.cache/huggingface/hub/models--roberta-large/refs/main     # 722cf37b1afa9454edce342e7895e588b6ff1d59
    cat ~/.cache/huggingface/hub/models--BAAI--bge-m3/refs/main      # 5617a9f61b028005a4858fdac845db406aefb181
    uv run --frozen python -c "import sys; sys.path[:0] = ['scripts', '.']; import machine, S384_exp04_minicheck_key_v22 as S; print(machine.PUB, S.hf_cache())"
    uv run --frozen python -c "import nltk; [nltk.download(p) for p in ('punkt_tab', 'wordnet', 'omw-1.4', 'punkt')]"
    uv run --frozen python scripts/check_S470.py                                           # offline checks
    uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage count-limits
    uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage key --device cpu --gate-only
    uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage papers --device cpu --gate-only
    uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage overlap --device cpu --gate-only

The stages, detached from the ssh session (one MiniCheck is a 3 to 4.7 GB float32 copy; each process runs its own
gate first; a process that stops is started again with the same command and resumes):

    cd ~/projects/mentori-runs-l1
    N=4
    for i in $(seq 0 $((N-1))); do
      nohup setsid uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage papers \
          --device cpu --draws 1 --shard $i/$N --threads 4 > ~/l1_papers_$i.log 2>&1 < /dev/null &
    done
    nohup setsid uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage key --device cpu \
        --threads 4 > ~/l1_key.log 2>&1 < /dev/null &
    nohup setsid uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage overlap --device cpu \
        --threads 4 > ~/l1_overlap.log 2>&1 < /dev/null &
    # when they have ended (every row present; papers draw 1 only):
    uv run --frozen python scripts/S470_l1_signals.py --inputs ~/l1_inputs --stage verify
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import inspect
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"              # the module docstring, Network
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TQDM_DISABLE", "1")

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from machine import RECOMPUTE, rel  # noqa: E402

SCRIPT = "scripts/S470_l1_signals.py"
OUTDIR = RECOMPUTE / "L1"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
INDEX = "exp_v4_s20_n0"
DRAWS = (1, 2, 3)
N_QUESTIONS, N_ANSWERS = 135, 2430
GROUP_COUNTS = {"answerable": 86, "false_premise": 10, "not_answerable": 39}
APPLIES = ("answerable", "false_premise")
STAGES = ("key", "papers", "overlap")
SIGNALS = {"key": ("precision", "recall", "f1"),
           "papers": ("precision",),
           "overlap": ("rouge_l_f1", "meteor", "bertscore_f1", "number_overlap", "number_overlap_citation_stripped",
                       "semantic_similarity")}
# Rule 10: the value a signal takes on an empty answer, where its own function defines one (the module docstring)
DEFINED_ON_EMPTY = {"key": ("recall", "f1"), "papers": (),
                    "overlap": ("rouge_l_f1", "meteor", "number_overlap", "number_overlap_citation_stripped")}
LIMITED = {"bertscore_f1": "bertscore", "semantic_similarity": "bge_m3"}     # signal -> encoder with a token limit
MC_SIDES = {"key": {"precision": ("precision",), "recall": ("recall",), "f1": ("precision", "recall")},
            "papers": {"precision": ("precision",)}}        # signal -> the MiniCheck sides (inputs) it is computed from
NA, NO_ANSWER, NO_CLAIM, NO_KEY_SENT = "not applicable", "no answer", "no claim sentence", "no key sentence"
OVER = "over the encoder's {n}-token limit"
LIMITS = {"bertscore": 512, "bge_m3": 8192}     # roberta-large model_max_length; bge-m3 max_seq_length (both checked)
MC_LIMIT = 2048                 # MiniCheck-Flan-T5's max_model_len (inference.py:43), checked on the loaded model
ERROR_BRANCH = "deposited empty-or-error branch"
ROBERTA_SNAPSHOT = "722cf37b1afa9454edce342e7895e588b6ff1d59"   # the laptop's roberta-large, S07's gate ran on it
NLTK_PACKAGES = {"wordnet": "corpora/wordnet", "punkt": "tokenizers/punkt", "punkt_tab": "tokenizers/punkt_tab",
                 "omw-1.4": "corpora/omw-1.4"}        # what S07.meteor downloads, and where nltk keeps each
PAPERS_STEP = 4                 # claims per S19.check call in the papers stage (a progress line after each)
PROB_TOL = 1e-4
S19_FULLDOC = RECOMPUTE / "S19_minicheck_source_fulldoc.jsonl"
S18_DOCS = RECOMPUTE / "S18_evidence_docs.jsonl"
S18_MANIFEST = RECOMPUTE / "S18_evidence_manifest.json"
PAPERS_GATE_ROWS = (("09_seqkit_TE3", "multi_hop"), ("09_seqkit_CO2", "single_pass"))
PAPERS_GATE_CLAIMS = 9
DEPOSITED_DET_SHA256 = "56b09bbc39cf58444a6c389b38d9237a1f82c713c2abd91f3c5ae97f7080689d"   # data/upstream/MANIFEST.sha256
OVERLAP_BATCH = 120            # 20 questions x 6 strategies per BERTScore call
CHARS_UNIT = 25_000            # the papers stage's speed is quoted per claim per 25k characters of paper


class Refused(Exception):
    """A refusal before anything is written (exit 2)."""


class GateFail(Exception):
    """A reproduction gate that did not reproduce (exit 1, nothing written)."""


class NltkMissing(BaseException):
    """An nltk package S07.meteor asked for is not on disk. A BaseException, so S07.meteor's own "except Exception"
    around nltk.download cannot swallow it (exit 2)."""


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def source_sha(fn) -> str:
    """sha256 of a function's source: what a lifted or imported metric executes, independent of the rest of its file."""
    return sha256_text(inspect.getsource(fn))


def run_of(config: str) -> str:
    return f"exp_01__{config}__{INDEX}"


# ---------------------------------------------------------------- the key and the answers

def the_key() -> dict:
    """The D5 key as the runner pins it, checked against S373.AS_V1: path, sha256, version, questions by id."""
    from experiments.runner import experiment as ex
    import S373_rejudge_v2 as S373
    if Path(ex.KEY_D5).resolve() != Path(S373.AS_V1).resolve():
        raise Refused(f"the runner's D5 key {ex.KEY_D5} is not S373.AS_V1 {S373.AS_V1}")
    raw = Path(ex.KEY_D5).read_bytes()
    if sha256_bytes(raw) != ex.KEY_D5_SHA256:
        raise Refused(f"{rel(ex.KEY_D5)} sha256 {sha256_bytes(raw)[:12]} is not the runner's pin {ex.KEY_D5_SHA256[:12]}")
    d = json.loads(raw)
    src = Path(S373.KEY)
    kv = str(json.loads(src.read_text(encoding="utf-8"))["version"])
    if d.get(f"source_v{kv.replace('.', '')}_sha256") != sha256_file(src):
        raise Refused(f"{Path(ex.KEY_D5).name} was not built from {src.name} v{kv} (S388's check)")
    return {"path": rel(ex.KEY_D5), "file": Path(ex.KEY_D5), "sha256": ex.KEY_D5_SHA256, "version": kv,
            "source": {"path": rel(src), "sha256": sha256_file(src)},
            "dropped_d7": list(d["dropped_d7"]), "questions": {q["id"]: q for q in d["questions"]}}


def read_manifest(inputs: Path) -> tuple[dict, str]:
    mf = inputs / "MANIFEST.sha256"
    if not mf.exists():
        raise Refused(f"{mf} does not exist")
    out = {}
    for n, line in enumerate(mf.read_text().splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise Refused(f"{mf}:{n} is not a sha256sum line")
        out[parts[1].strip().lstrip("*")] = parts[0]
    return out, sha256_file(mf)


def verify_inputs(inputs: Path) -> dict:
    """Every manifest entry under the six G1 runs is checked; each run's answers.jsonl must be listed."""
    man, man_sha = read_manifest(inputs)
    answers = {}
    for c in CONFIGS:
        prefix = f"runs/{run_of(c)}/"
        a = prefix + "answers.jsonl"
        if a not in man:
            raise Refused(f"{a} is not in {inputs}/MANIFEST.sha256")
        for path, want in man.items():
            if path.startswith(prefix):
                got = sha256_file(inputs / path) if (inputs / path).exists() else "missing"
                if got != want:
                    raise Refused(f"{inputs / path}: sha256 {got[:12]}, the manifest says {want[:12]}")
        answers[run_of(c)] = man[a]
    return {"manifest_sha256": man_sha, "answers_sha256": answers}


def read_answers(inputs: Path, key: dict) -> tuple[list[dict], dict]:
    """The 2,430 G1 answers (the module docstring, The answers), and what the selection found."""
    from experiments.runner import experiment as ex
    from experiments.scorers import records as R
    qorder = [q["id"] for q in ex.questions()]
    if len(qorder) != N_QUESTIONS:
        raise Refused(f"the runner gives {len(qorder)} questions, not {N_QUESTIONS}")
    dropped = set(key["dropped_d7"])
    out, d7 = [], []
    for c in CONFIGS:
        run = run_of(c)
        path = inputs / "runs" / run / "answers.jsonl"
        last: dict = {}
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            rec = json.loads(raw)
            k = rec["answer_key"]
            if rec["question_id"] in dropped:
                d7.append(k)
                continue
            if k in last and not (last[k][1].get("generation") or {}).get("error"):
                raise Refused(f"{path}:{n} stores {k} again after its answer at line {last[k][0]}")
            last[k] = (n, rec)
        for k, (n, rec) in last.items():
            gen = rec.get("generation") or {}
            qid, draw = rec["question_id"], rec["draw"]
            if k != ex.answer_key(c, qid, draw, index=INDEX) or rec.get("config") != c \
                    or (rec.get("run_id") or run) != run or rec.get("index_name") != INDEX:
                raise Refused(f"{path}:{n}: {k} is not a G1 {c} answer on {INDEX}")
            ans = gen.get("answer") or ""
            out.append({"answer_key": k, "run_id": run, "config": c, "question_id": qid, "draw": draw,
                        "group": R.group_of(qid), "status": R._status(ans, gen.get("error")),
                        "error": gen.get("error"), "stop_reason": gen.get("stop_reason"), "answer": ans,
                        "answer_sha256": sha256_text(ans), "source": f"runs/{run}/answers.jsonl:{n}"})
        if not d7:                      # the shared reader agrees (it refuses a question outside the key)
            mine = {(x["answer_key"], x["answer"], x["status"], x["group"], x["draw"], x["config"])
                    for x in out if x["config"] == c}
            theirs = {(x["answer_key"], x["answer"], x["status"], x["group"], x["draw"], x["config"])
                      for x in R.read_run(path.parent, resolve=False)}
            if mine != theirs:
                raise Refused(f"{run}: this reading and records.read_run differ on {len(mine ^ theirs)} answers")
    require_complete(out, qorder)
    groups = {}
    for q in qorder:
        g = R.group_of(q)
        flag = key["questions"][q].get("answerable")
        if flag is not (g != "not_answerable"):
            raise Refused(f"{q}: group {g} (the runner's answer type) but S373.AS_V1 answerable {flag!r}")
        if g in APPLIES and not (key["questions"][q].get("expected_answer") or "").strip():
            raise Refused(f"{q}: no expected_answer in the key")
        groups[q] = g
    count = {g: sum(1 for v in groups.values() if v == g) for g in GROUP_COUNTS}
    if count != GROUP_COUNTS:
        raise Refused(f"groups {count}, not {GROUP_COUNTS} (Rule 8)")
    pos = {q: i for i, q in enumerate(qorder)}
    out.sort(key=lambda x: (x["draw"], pos[x["question_id"]], CONFIGS.index(x["config"])))
    info = {"answers": len(out), "questions": count, "d7_dropped": sorted(dropped), "d7_answers": len(d7),
            "empty": sum(1 for x in out if not x["answer"].strip()),
            "empty_scored": sum(1 for x in out if not x["answer"].strip() and x["group"] in APPLIES),
            "status": {s: sum(1 for x in out if x["status"] == s) for s in ("ok", "error", "no_answer")}}
    ewt = [x for x in out if x["error"] and x["answer"].strip() and x["group"] in APPLIES]
    info["error_with_text"] = {"n": len(ewt), "by_strategy": {c: sum(1 for x in ewt if x["config"] == c) for c in CONFIGS},
                               "first": [x["answer_key"] for x in ewt[:10]]}
    return out, info


def require_complete(out: list[dict], qorder: list[str]) -> None:
    """The 2,430 G1 cells, each once: six strategies x the runner's 135 questions x three draws."""
    cells = {(x["config"], x["question_id"], x["draw"]) for x in out}
    want = {(c, q, d) for c in CONFIGS for q in qorder for d in DRAWS}
    if cells != want or len(out) != N_ANSWERS:
        raise Refused(f"{len(out)} answers on {len(cells & want)} of the {len(want)} G1 cells; "
                      f"{len(want - cells)} missing, {len(cells - want)} not G1's")


def ordered(answers: list[dict], draws, shard=(0, 1), questions=None) -> list[dict]:
    """The answers of the draws asked, draw by draw, question by question in the key's order, the six strategies of a
    question together (read_answers sorted them), in shard i of n."""
    i, n = shard
    pos = {a["answer_key"]: k for k, a in enumerate(answers)}
    keep = [a for a in answers if a["draw"] in draws and shard_of(a, n) == i
            and (questions is None or a["question_id"] in questions)]
    return sorted(keep, key=lambda a: (list(draws).index(a["draw"]), pos[a["answer_key"]]))


def shard_of(a: dict, n: int) -> int:
    return int(sha256_text(f"{a['question_id']}|d{a['draw']}")[:16], 16) % n


# ---------------------------------------------------------------- MiniCheck's inputs, counted before its cut

def mc_input_tokens(scorer, docs: list, claims: list) -> tuple[list[list[int]], int]:
    """For MiniCheck's score(docs, claims): per claim, the token count of each input MiniCheck builds for it, before its
    cut, and the cut (max_model_len). The inputs are built by MiniCheck's own code: its score() runs with the model
    call (Inferencer.inference) replaced by a recorder, so the sentence split, the 500-word chunker and the chunk
    choice are the library's (minicheck.py:143-150, inference.py:95-153); each input is then the text batch_tokenize
    tokenizes ("predict: " + chunk + eos + claim, inference.py:233-241), counted by the same tokenizer with no cut."""
    import numpy as np
    from minicheck.inference import Inferencer
    from minicheck.minicheck import MiniCheck
    mc = getattr(scorer, "minicheck", scorer)
    inf = mc.model
    if not isinstance(inf, Inferencer) or inf.model_name != "flan-t5-large":
        raise Refused(f"MiniCheck's model is {type(inf).__name__} {getattr(inf, 'model_name', None)}, not flan-t5-large")
    seen: list[list[tuple[str, str]]] = []

    def record(doc, claim):
        seen.append(list(zip(doc, claim)))
        return {"max_support_prob": 0.0, "used_chunks": [], "support_prob_per_chunk": np.zeros(0)}

    inf.inference = record                       # an instance attribute: the class's method is untouched
    try:
        MiniCheck.score(mc, docs=list(docs), claims=list(claims))
    finally:
        del inf.inference
    if len(seen) != len(claims):
        raise Refused(f"MiniCheck built inputs for {len(seen)} of {len(claims)} claims")
    tok = inf.tokenizer
    flat = ["predict: " + tok.eos_token.join([d, c]) for pairs in seen for d, c in pairs]
    import transformers
    level = transformers.logging.get_verbosity()
    transformers.logging.set_verbosity_error()   # "longer than the specified maximum": counting it is the point
    try:
        lens = [len(x) for x in tok(flat, truncation=False)["input_ids"]] if flat else []
    finally:
        transformers.logging.set_verbosity(level)
    out, i = [], 0
    for pairs in seen:
        out.append(lens[i:i + len(pairs)])
        i += len(pairs)
    return out, inf.max_model_len


class MeteredScorer:
    """MiniCheck's score(), each call's inputs counted first by mc_input_tokens. dry: count only, score nothing (labels
    0, probabilities 0.0)."""

    def __init__(self, scorer, dry: bool = False):
        self.scorer, self.dry, self.calls, self.limit = scorer, dry, [], None

    def score(self, docs, claims):
        counts, self.limit = mc_input_tokens(self.scorer, docs, claims)
        self.calls.append({"docs": list(docs), "claims": list(claims), "counts": counts})
        if self.dry:
            return [0] * len(claims), [0.0] * len(claims), None, None
        return self.scorer.score(docs=docs, claims=claims)

    def side(self, call: dict) -> dict:
        """inputs: (chunk, claim) inputs built; cut_claims: claims with an input over the limit; max_tokens."""
        c = call["counts"]
        return {"claims": len(c), "inputs": sum(len(x) for x in c),
                "cut_claims": sum(1 for x in c if any(n > self.limit for n in x)),
                "max_tokens": max((n for x in c for n in x), default=0)}


class MemoScorer:
    """MiniCheck's score() with its outputs kept by input. While open it scores and keeps; once frozen, an input it has
    not seen is counted as a miss and scored (the key gate: key_signals must ask what the deposited path asked)."""

    def __init__(self, minicheck):
        self.minicheck, self.memo, self.frozen, self.misses = minicheck, {}, False, 0

    def score(self, docs, claims):
        k = (tuple(docs), tuple(claims))
        if k not in self.memo:
            self.misses += self.frozen
            self.memo[k] = self.minicheck.score(docs=list(docs), claims=list(claims))
        return self.memo[k]


# ---------------------------------------------------------------- rows and the rules they obey

def base_row(a: dict, stage: str) -> dict:
    return {"answer_key": a["answer_key"], "run_id": a["run_id"], "config": a["config"], "question_id": a["question_id"],
            "draw": a["draw"], "group": a["group"], "status": a["status"], "stop_reason": a["stop_reason"],
            "answer_chars": len(a["answer"]), "answer_blank": not a["answer"].strip(),
            "answer_sha256": a["answer_sha256"], "stage": stage}


def finish(row: dict, values: dict, reasons: dict, detail: dict | None = None) -> dict:
    row["signals"] = {s: values.get(s) for s in SIGNALS[row["stage"]]}
    row["null_reasons"] = {s: reasons[s] for s in SIGNALS[row["stage"]] if row["signals"][s] is None}
    row["detail"] = detail or {}
    return row


def not_applicable(a: dict, stage: str) -> dict:
    return finish(base_row(a, stage), {}, {s: NA for s in SIGNALS[stage]})


def key_signals(a: dict, expected: str, ns: dict, scorer) -> dict:
    """MiniCheck against the key, one answer: the deposited score_faithfulness, its inputs counted (a side with an input
    over MiniCheck's cut is null), then Rule 8 and Rule 10."""
    if a["group"] not in APPLIES:
        return not_applicable(a, "key")
    m = MeteredScorer(scorer)
    res = ns["score_faithfulness"](a["answer"], expected, m)
    sides = {}
    if m.calls:                 # the deposited order: precision (docs = the key), then recall (docs = the answer)
        if len(m.calls) != 2 or set(m.calls[0]["docs"]) != {expected} or set(m.calls[1]["docs"]) != {a["answer"]}:
            raise Refused(f"{a['answer_key']}: score_faithfulness called MiniCheck in an order this script does not know")
        sides = {"precision": m.side(m.calls[0]), "recall": m.side(m.calls[1])}
    dep = {s: res[s] for s in SIGNALS["key"]}
    detail = {"deposited_returned": dict(dep), "n_gen_sentences": res["n_gen_sentences"],
              "n_exp_sentences": res["n_exp_sentences"], "mean_precision_prob": res.get("mean_precision_prob"),
              "mean_recall_prob": res.get("mean_recall_prob"), "precision_details": res["precision_details"],
              "recall_details": res["recall_details"],
              "minicheck_inputs": {"limit": m.limit, **sides} if sides else None}
    row = base_row(a, "key")
    if row["answer_blank"]:
        if res["n_exp_sentences"] == 0:
            return finish(row, {}, {"precision": NO_ANSWER, "recall": NO_KEY_SENT, "f1": NO_KEY_SENT}, detail)
        return finish(row, {"recall": dep["recall"], "f1": dep["f1"]}, {"precision": NO_ANSWER}, detail)
    if res["n_exp_sentences"] == 0:
        return finish(row, {}, {s: NO_KEY_SENT for s in SIGNALS["key"]}, detail)
    if res["n_gen_sentences"] == 0:
        return finish(row, {}, {s: NO_CLAIM for s in SIGNALS["key"]}, detail)
    values, reasons = dict(dep), {}
    for side, sig_cut in (("precision", ("precision", "f1")), ("recall", ("recall", "f1"))):
        if sides[side]["cut_claims"]:
            for s in sig_cut:
                values.pop(s, None)
                reasons[s] = OVER.format(n=m.limit)
                detail["deposited_returned"][s] = None          # computed on a cut input: not kept
            detail[f"{side}_details"] = None
            detail[f"mean_{side}_prob"] = None
    return finish(row, values, reasons, detail)


def join_docs(docs: dict, files: list) -> str:
    """S19's --full-doc document: the papers' texts joined by a blank line (S19_minicheck_regrounded.py:309)."""
    return "\n\n".join(docs[f] for f in files)


def papers_signals(a: dict, doc: dict, decompose, check, scorer, progress=None, keep_cut: bool = False) -> dict:
    """MiniCheck against the source papers, one answer: S19's full-doc path (one whole document per claim, S19.check),
    its inputs counted first (an answer with a claim over MiniCheck's cut is null and not scored), then scored
    PAPERS_STEP claims per check call, progress(claims done, claims, seconds) after each. keep_cut (the papers gate
    only): an answer over the cut is scored all the same, its values kept in the detail beside the null signal, so
    the gate can reproduce an S19 row that was computed on a cut input."""
    if a["group"] not in APPLIES:
        return not_applicable(a, "papers")
    row = base_row(a, "papers")
    detail = {"doc_files": doc["files"], "doc_chars": len(doc["text"]), "doc_sha256": doc["sha256"]}
    if row["answer_blank"]:
        return finish(row, {}, {"precision": NO_ANSWER}, {**detail, "n_claims": 0})
    claims = decompose(a["answer"])
    if not claims:
        return finish(row, {}, {"precision": NO_CLAIM}, {**detail, "n_claims": 0})
    t = time.time()
    dry = MeteredScorer(scorer, dry=True)
    check(dry, claims, [[doc["text"]]] * len(claims))
    if len(dry.calls) != 1 or len(dry.calls[0]["claims"]) != len(claims):
        raise Refused(f"{a['answer_key']}: S19.check called MiniCheck in a way this script does not know")
    side = dry.side(dry.calls[0])
    detail.update(n_claims=len(claims), minicheck_inputs={"limit": dry.limit, "precision": side},
                  count_seconds=round(time.time() - t, 2))
    if side["cut_claims"] and not keep_cut:
        return finish(row, {}, {"precision": OVER.format(n=dry.limit)}, detail)
    t = time.time()
    per = []
    for s in range(0, len(claims), PAPERS_STEP):
        part = claims[s:s + PAPERS_STEP]
        per += check(scorer, part, [[doc["text"]]] * len(part))
        if progress:
            progress(len(per), len(claims), time.time() - t)
    prec = round(sum(1 for x in per if x["supported"]) / len(per), 4)
    if side["cut_claims"]:          # keep_cut: never a signal, only the gate's reproduction of an S19 row
        return finish(row, {}, {"precision": OVER.format(n=dry.limit)},
                      {**detail, "per_claim_on_cut_input": per, "precision_on_cut_input": prec})
    return finish(row, {"precision": prec}, {}, {**detail, "per_claim": per, "seconds": round(time.time() - t, 2)})


def overlap_rows(batch: list[dict], key_q: dict, fns) -> list[dict]:
    """The overlap signals for a batch of answers. fns holds the metric calls (OverlapFns, or a stub in check_S470);
    an encoder's metric is called only on the rows whose answer and key fit its limit."""
    rows, todo = {}, []
    for a in batch:
        if a["group"] not in APPLIES:
            rows[a["answer_key"]] = not_applicable(a, "overlap")
        else:
            todo.append(a)
    if not todo:
        return [rows[a["answer_key"]] for a in batch]
    exp = [key_q[a["question_id"]]["expected_answer"] for a in todo]
    ans = [a["answer"] for a in todo]
    rouge = fns.rouge(ans, exp)
    meteor = fns.meteor(ans, exp)
    numov = fns.number_overlap(todo)
    tokens, fit = [], {"bertscore": [], "bge_m3": []}
    for a, e in zip(todo, exp):
        blank = not a["answer"].strip()
        t = {}
        for enc in ("bertscore", "bge_m3"):
            na = None if blank else fns.tokens(enc, a["answer"])
            nk = fns.tokens(enc, e)
            t[enc] = {"answer": na, "key": nk, "limit": fns.limit(enc)}
            fit[enc].append(not blank and na <= fns.limit(enc) and nk <= fns.limit(enc))
        tokens.append(t)
    idx = [i for i, ok in enumerate(fit["bertscore"]) if ok]
    bert = dict(zip(idx, fns.bertscore([ans[i] for i in idx], [exp[i] for i in idx]))) if idx else {}
    for i, (a, e) in enumerate(zip(todo, exp)):
        row = base_row(a, "overlap")
        blank = row["answer_blank"]
        values = {"rouge_l_f1": float(rouge[i]), "meteor": float(meteor[i]), "number_overlap": float(numov[i]),
                  "number_overlap_citation_stripped": float(fns.number_overlap_stripped(e, a["answer"]))}
        reasons = {}
        detail = {"tokens": tokens[i]}
        if blank or a["error"]:
            detail["number_overlap_branch"] = ERROR_BRANCH
        if blank:
            reasons.update({"bertscore_f1": NO_ANSWER, "semantic_similarity": NO_ANSWER})
        else:
            if fit["bertscore"][i]:
                values["bertscore_f1"] = float(bert[i])
            else:
                reasons["bertscore_f1"] = OVER.format(n=fns.limit("bertscore"))
            if fit["bge_m3"][i]:
                sim, _cost, meta = fns.similarity(e, a["answer"])
                values["semantic_similarity"] = sim
                detail["similarity_meta"] = meta
            else:
                reasons["semantic_similarity"] = OVER.format(n=fns.limit("bge_m3"))
        detail["key_numbers"] = fns.key_numbers(e)
        rows[a["answer_key"]] = finish(row, values, reasons, detail)
    return [rows[a["answer_key"]] for a in batch]


def row_violations(row: dict) -> list[str]:
    """Rule 8 and Rule 10, and the encoders' cuts, on one written row; [] when it obeys them."""
    st = row.get("stage")
    if st not in SIGNALS:
        return [f"stage {st!r}"]
    sig, why = row.get("signals") or {}, row.get("null_reasons") or {}
    det = row.get("detail") or {}
    bad = []
    if set(sig) != set(SIGNALS[st]):
        bad.append(f"signals {sorted(sig)}")
    for s in SIGNALS[st]:
        v, r = sig.get(s), why.get(s)
        if v is None and not r:
            bad.append(f"{s}: null with no reason")
        if v is not None and r:
            bad.append(f"{s}: a value and a reason")
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))
                              or not (-1.0 if s == "semantic_similarity" else 0.0) <= v <= 1.0 + 1e-6):
            bad.append(f"{s}: {v!r} is not a number in range")
        if row.get("group") not in APPLIES:
            if v is not None or r != NA:
                bad.append(f"{s}: {row.get('group')} must be null '{NA}' (Rule 8), is {v!r} {r!r}")
            continue
        if r == NA:
            bad.append(f"{s}: '{NA}' on a {row.get('group')} question")
        if row.get("answer_blank"):
            if s in DEFINED_ON_EMPTY[st]:
                if v is None and r != NO_KEY_SENT:
                    bad.append(f"{s}: its function defines a value on an empty answer, written null {r!r}")
            elif v is not None or r != NO_ANSWER:
                bad.append(f"{s}: an empty answer must be null '{NO_ANSWER}' (Rule 10), is {v!r} {r!r}")
        elif r == NO_ANSWER:
            bad.append(f"{s}: '{NO_ANSWER}' on a non-empty answer")
        if st in MC_SIDES:                                   # MiniCheck's 2,048-token cut
            mi = det.get("minicheck_inputs") or {}
            sides = [mi.get(x) for x in MC_SIDES[st][s]]
            cut = any(x and x.get("cut_claims") for x in sides)
            if r and r.startswith("over the encoder") and (not cut or r != OVER.format(n=mi.get("limit"))):
                bad.append(f"{s}: '{r}' without a MiniCheck input over the limit")
            if v is not None and not row.get("answer_blank") and (not all(sides) or cut):
                bad.append(f"{s}: a value computed on a MiniCheck input over the limit, or with no input count")
            continue
        if r and r.startswith("over the encoder"):
            enc = LIMITED.get(s)
            t = (det.get("tokens") or {}).get(enc) if enc else None
            if not t or not (max(t["answer"] or 0, t["key"] or 0) > t["limit"]) or r != OVER.format(n=t["limit"]):
                bad.append(f"{s}: '{r}' without a text over the limit")
        if v is not None and s in LIMITED:
            t = (det.get("tokens") or {}).get(LIMITED[s])
            if not t or t["answer"] is None or max(t["answer"], t["key"]) > t["limit"]:
                bad.append(f"{s}: a value computed on a text over the encoder's limit, or with no token count")
    if st == "overlap" and row.get("group") in APPLIES and (row.get("answer_blank") or row.get("status") == "error") \
            and det.get("number_overlap_branch") != ERROR_BRANCH:
        bad.append("number_overlap: an empty or errored answer without the deposited branch's mark")
    return bad


# ---------------------------------------------------------------- header, identity and resume

def identity(key: dict, inputs_info: dict) -> dict:
    from S384_exp04_minicheck_key_v22 import DEPOSITED, DEPOSITED_SHA256, HARNESS_COMMON
    from machine import PUB_SCRIPTS
    det = PUB_SCRIPTS / "analysis_deterministic_scorer.py"
    dep = {"analysis_minicheck.py": sha256_file(DEPOSITED), "analysis_deterministic_scorer.py": sha256_file(det),
           "exp_common.py": sha256_file(HARNESS_COMMON)}
    if dep["analysis_minicheck.py"] != DEPOSITED_SHA256 or dep["analysis_deterministic_scorer.py"] != DEPOSITED_DET_SHA256:
        raise Refused(f"the deposited scripts are not the pinned ones: {dep}")
    return {"key": {k: key[k] for k in ("path", "sha256", "version", "source")},
            "inputs": inputs_info, "deposited": dep}


def hf_snapshot(repo: str, want: str | None = None) -> dict:
    """The snapshot the offline loader resolves for a repo in the default Hugging Face cache, and its weights blob;
    refused when it is not want."""
    from huggingface_hub import constants
    root = Path(constants.HF_HUB_CACHE) / f"models--{repo.replace('/', '--')}"
    if not (root / "refs" / "main").exists():
        raise Refused(f"{repo} is not in the Hugging Face cache {constants.HF_HUB_CACHE} (the module docstring, "
                      f"Reproduce, copies it from the laptop)")
    snap = (root / "refs" / "main").read_text().strip()
    if want and snap != want:
        raise Refused(f"{repo}: the cache resolves snapshot {snap[:12]}, not {want[:12]}")
    out = {"repo": repo, "snapshot": snap}
    for f in ("model.safetensors", "pytorch_model.bin"):
        p = root / "snapshots" / snap / f
        if p.exists():
            out.update(weights=f, weights_blob=p.resolve().name)
            break
    return out


def nltk_offline() -> None:
    """nltk.download replaced, for this process, by a lookup on disk that never fetches (the module docstring,
    Network). A package that is not on disk stops the run (NltkMissing)."""
    import nltk
    if getattr(nltk.download, "s470_offline", False):
        return

    def find_only(info_or_id=None, *a, **k):
        name = NLTK_PACKAGES.get(info_or_id)
        if name is None:
            raise NltkMissing(f"nltk.download({info_or_id!r}) asked for a package this script does not know; nothing "
                              f"is downloaded")
        for cand in (name, name + ".zip"):
            try:
                nltk.data.find(cand)
                return True
            except LookupError:
                pass
        raise NltkMissing(f"nltk's {info_or_id} ({name}) is not on disk; download it once (the module docstring, "
                          f"Reproduce)")

    find_only.s470_offline = True
    nltk.download = find_only


def nltk_data() -> dict:
    """sha256 of the nltk data the metrics read: punkt_tab's English tables (MiniCheck's sent_tokenize, METEOR's
    word_tokenize) and the WordNet archives METEOR matches synonyms with."""
    import nltk
    out = {"nltk": nltk.__version__}
    try:
        d = Path(str(nltk.data.find("tokenizers/punkt_tab/english/")))
        h = hashlib.sha256()
        for f in sorted(p for p in d.iterdir() if p.is_file()):
            h.update(f.name.encode() + b"\0" + f.read_bytes())
        out["punkt_tab_english_sha256"] = h.hexdigest()
    except LookupError:
        out["punkt_tab_english_sha256"] = None
    for name in ("corpora/wordnet.zip", "corpora/omw-1.4.zip"):
        try:
            out[name] = sha256_file(Path(str(nltk.data.find(name))))
        except (LookupError, OSError):
            out[name] = None
    return out


def lock_info() -> dict:
    from experiments.runner.lock import LOCK, load
    spec = load().retrieval()["embedding"]
    return {"path": rel(LOCK), "sha256": sha256_file(LOCK), "embedding": spec}


def digest(paths) -> dict:
    """sha256 of each file, and one over the list when it is long (a folder of artefacts)."""
    paths = sorted(Path(p) for p in paths)
    shas = {rel(p): sha256_file(p) for p in paths}
    if len(shas) <= 12:
        return shas
    return {"files": len(shas), "sha256_of_sorted_list": sha256_text(json.dumps(shas, sort_keys=True))}


def gate_files(stage: str) -> dict:
    """sha256 of the files a stage's gate reads and compares with (README.md:75-79: the evidence a gate passed on)."""
    from machine import PUB, require
    if stage == "key":
        import S384_exp04_minicheck_key_v22 as S384
        files = [S384.ARTEFACT, S384.GENERATION, S384.KEY_V1]
        require(*files)
        return digest(files)
    if stage == "papers":
        files = [S19_FULLDOC, PUB / "results/exp04_generation_latest.json", S18_MANIFEST, S18_DOCS]
        require(*files)
        return digest(files)
    import S07_baseline_metrics as S07
    import S141_scorers_4_2b as S141
    import S382_exp04_objective_v22 as S382
    files = [S07.MASTER, S07.GEN, S07.GT, S07.V1_SCORES, S382.GEN, S382.DET, S382.KEY_V1, S141.V1_KEY]
    require(*files)
    art = [p for p in Path(S141.V1_SIGNALS).glob("*.jsonl") if p.name.endswith((".similarity.jsonl", ".deterministic.jsonl"))]
    camp = [p for arm in S141.arms() for p in (arm / "results.json", arm / "intermediate.json") if p.exists()]
    return {**digest(files), "S141 v1 similarity and deterministic artefacts": digest(art),
            "S141 campaign answers": digest(camp)}


def stage_params(stage: str) -> dict:
    """What a stage's numbers depend on besides the key, the inputs, the deposit and the code: a resume needs the same."""
    import S384_exp04_minicheck_key_v22 as S384
    ck = {k: v for k, v in S384.checkpoint_identity(S384.hf_cache()).items() if k != "hf_cache"}   # where: the session
    mc = {"checker": "lytang/MiniCheck-Flan-T5-Large", **ck, "max_model_len": MC_LIMIT, "cut_rule": "null, never cut",
          "dtype": "torch.float32", "punkt_tab_english_sha256": S384.punkt_tab()["punkt_tab_english_sha256"],
          "lifted": {"S384.load_minicheck": source_sha(S384.load_minicheck)}}
    if stage == "key":
        return {**mc, "reference": "the key's expected_answer (S373.AS_V1)",
                "function": "analysis_minicheck.score_faithfulness, decompose_to_sentences (S384.deposited_code)",
                "gate_files": gate_files(stage)}
    if stage == "papers":
        import S19_minicheck_regrounded as S19
        return {**mc, "reference": "the source papers, whole", "mode": "full-doc", "join": "\\n\\n",
                "source_files": "the key's (S373.AS_V1 source_files)", "docs": rel(S18_DOCS),
                "docs_sha256": sha256_file(S18_DOCS), "aggregation": "S19.check: max over documents",
                "claims_per_check_call": PAPERS_STEP, "gate_files": gate_files(stage),
                "lifted": {**mc["lifted"], "S19.check": source_sha(S19.check)}}
    import S07_baseline_metrics as S07
    import S141_scorers_4_2b as S141
    import S382_exp04_objective_v22 as S382
    from S141_runner import scorers as sc
    lk = lock_info()
    return {"reference": "the key's expected_answer (S373.AS_V1)",
            "bertscore": {"model_type": "roberta-large", "lang": "en", "batch_size": 32, "idf": False,
                          "rescale_with_baseline": False, **hf_snapshot("roberta-large", ROBERTA_SNAPSHOT)},
            "similarity": {**lk["embedding"], "normalize_embeddings": True},
            "limits": {"bertscore": LIMITS["bertscore"], "bge_m3": LIMITS["bge_m3"], "rule": "null, never cut"},
            "nltk_data": nltk_data(), "gate_files": gate_files(stage),
            "lifted": {"S07.rouge_l": source_sha(S07.rouge_l), "S07.meteor": source_sha(S07.meteor),
                       "S07.bertscore": source_sha(S07.bertscore), "S382.score": source_sha(S382.score),
                       "S382.deposited_scorer": source_sha(S382.deposited_scorer),
                       "S141_runner.scorers.semantic_similarity": source_sha(sc.semantic_similarity),
                       "S141_runner.scorers.strip_citations": source_sha(sc.strip_citations),
                       "S141.det_record": source_sha(S141.det_record)}}


def code_shas() -> dict:
    """This script, every file it lifts or imports a metric from, and uv.lock (the package versions): part of every
    stage's parameters, so a resume under edited code is refused."""
    return {SCRIPT: sha256_file(Path(__file__)), **lifted_shas(), "uv.lock": sha256_file(ROOT / "uv.lock")}


def diff(a, b, at="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        return [x for k in sorted(set(a) | set(b)) for x in diff(a.get(k), b.get(k), f"{at}.{k}")]
    return [] if a == b else [f"{at.lstrip('.')}: {str(a)[:60]} -> {str(b)[:60]}"]


def header_problems(hdr: dict, ident: dict, stage: str, params: dict, n: int | None = None) -> list[str]:
    out = diff(hdr.get("identity"), ident)
    if stage in (hdr.get("stages") or {}):
        out += [f"stages.{stage}.{x}" for x in diff(hdr["stages"][stage], params)]
    have = (hdr.get("shards") or {}).get(stage)
    if n is not None and have is not None and have != n:
        out.append(f"shards.{stage}: this stage runs as {have} shards, this run asks for {n}")
    return out


def check_header(outdir: Path, ident: dict, stage: str, params: dict, n: int | None = None) -> dict | None:
    hp = outdir / "header.json"
    if not hp.exists():
        if (outdir / stage).is_dir() and any((outdir / stage).glob("*.jsonl")):
            raise Refused(f"{outdir / stage} holds rows and {hp} does not exist; move the folder aside")
        return None
    hdr = json.loads(hp.read_text())
    bad = header_problems(hdr, ident, stage, params, n)
    if bad:
        raise Refused(f"{hp} records another key, inputs, deposited code, shard count or {stage} parameters; resuming "
                      f"would mix them. Use another --outdir. Differences: " + "; ".join(bad[:8]))
    return hdr


@contextlib.contextmanager
def flocked(path: Path, wait: bool = True):
    fh = open(path, "a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
    except BlockingIOError:
        fh.close()
        raise Refused(f"{path} is held by another process (a second process on the same shard)") from None
    try:
        yield fh
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def lock_dir(outdir: Path) -> Path:
    """The run locks of one outdir, in the system temp folder (named from the outdir's resolved path), so a run that
    stops at its gate leaves nothing in the outdir."""
    return Path(tempfile.gettempdir()) / f"S470_locks_{sha256_text(str(Path(outdir).resolve()))[:16]}"


def take_locks(outdir: Path, stage: str, shard: tuple[int, int]) -> contextlib.ExitStack:
    """This run's locks, held until the returned stack closes: a shared lock on the stage's shard count n (refused
    while a process holds another n of the stage) and an exclusive lock on its shard (refused while another process
    holds it). Neither waits."""
    i, n = shard
    d = lock_dir(outdir)
    d.mkdir(parents=True, exist_ok=True)
    stack = contextlib.ExitStack()
    try:
        with flocked(d / f"{stage}.mutex"):           # the n check and the n lock, one process at a time
            for f in sorted(d.glob(f"{stage}.n*.lock")):
                other = f.name[len(stage) + 2:-len(".lock")]
                if other == str(n):
                    continue
                with open(f, "a") as fh:
                    try:
                        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        raise Refused(f"a process with --shard i/{other} runs the {stage} stage of {outdir}; a stage "
                                      f"keeps one shard count") from None
                    fcntl.flock(fh, fcntl.LOCK_UN)
            fh = stack.enter_context(open(d / f"{stage}.n{n}.lock", "a"))
            fcntl.flock(fh, fcntl.LOCK_SH)             # released when the file closes
        stack.enter_context(flocked(d / f"{stage}.shard{i}of{n}.lock", wait=False))
    except BaseException:
        stack.close()
        raise
    return stack


def write_header(outdir: Path, ident: dict, stage: str, params: dict, session: dict, n: int | None = None) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    hp = outdir / "header.json"
    with flocked(outdir / ".header.lock"):
        hdr = json.loads(hp.read_text()) if hp.exists() else {
            "script": SCRIPT, "created": utc(), "plan_row": "L1", "identity": ident, "stages": {}, "shards": {},
            "sessions": []}
        bad = header_problems(hdr, ident, stage, params, n)
        if bad:
            raise Refused(f"{hp} changed under this run: " + "; ".join(bad[:8]))
        hdr["stages"].setdefault(stage, params)
        if n is not None:
            hdr.setdefault("shards", {}).setdefault(stage, n)
        hdr["sessions"].append(session)
        tmp = hp.with_suffix(f".tmp{os.getpid()}")
        with open(tmp, "w") as fh:
            fh.write(json.dumps(hdr, indent=1, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, hp)


def cut_unfinished_tail(path: Path) -> int:
    """Under this shard's lock: an unfinished last line of its own file (a process killed while writing it) is cut
    off, so the next row does not join it. Returns the bytes cut."""
    if not path.exists():
        return 0
    data = path.read_bytes()
    if not data or data.endswith(b"\n"):
        return 0
    keep = data.rfind(b"\n") + 1
    with open(path, "r+b") as fh:
        fh.truncate(keep)
        fh.flush()
        os.fsync(fh.fileno())
    return len(data) - keep


def read_done(stage_dir: Path, answers: dict, unfinished: list | None = None) -> dict:
    """answer_key -> row, over every file of the stage. A last line with no newline is being written (another shard)
    or was cut by a kill: it is not done, and is listed in unfinished. A key written twice, a damaged line, a key that
    is not one of the answers, or a row whose answer sha256 is not the answer's is refused."""
    done, where = {}, {}
    if not stage_dir.is_dir():
        return done
    for f in sorted(stage_dir.glob("*.jsonl")):
        parts = f.read_bytes().split(b"\n")
        if parts[-1].strip():
            if unfinished is not None:
                unfinished.append(f"{f.name}:{len(parts)} ({len(parts[-1])} bytes, no newline)")
        for n, raw in enumerate(parts[:-1], 1):
            if not raw.strip():
                continue
            try:
                r = json.loads(raw)
                k = r["answer_key"]
            except (ValueError, KeyError, TypeError) as e:
                raise Refused(f"{f}:{n} is a damaged row ({type(e).__name__}: {str(e)[:80]}); it ends in a newline, "
                              f"so it was not cut by a kill: look at it by hand") from None
            if k in done:
                raise Refused(f"{k} is written twice: {where[k]} and {f.name}:{n}")
            if k not in answers:
                raise Refused(f"{f.name}:{n}: {k} is not one of the input answers")
            if r.get("answer_sha256") != answers[k]["answer_sha256"]:
                raise Refused(f"{f.name}:{n}: {k} was scored on another answer text")
            done[k], where[k] = r, f"{f.name}:{n}"
    return done


# ---------------------------------------------------------------- gates

@contextlib.contextmanager
def swapped(obj, **attrs):
    """Module names pointed elsewhere for the duration (a gate runs a script's own code through this stage's calls)."""
    old = {k: getattr(obj, k) for k in attrs}
    for k, v in attrs.items():
        setattr(obj, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(obj, k, v)


def gate_answer(q: str, c: str, text: str, error=None) -> dict:
    """A deposited answer in the shape the stages read, for a gate."""
    return {"answer_key": f"gate|{c}|{q}|d0", "run_id": "gate", "config": c, "question_id": q, "draw": 0,
            "group": "answerable", "status": "ok", "error": error, "stop_reason": None, "answer": text,
            "answer_sha256": sha256_text(text)}


def check_mc_limit(scorer) -> None:
    got = scorer.model.max_model_len
    if got != MC_LIMIT:
        raise Refused(f"MiniCheck's max_model_len is {got}, not {MC_LIMIT}")


def gate_key(device: str):
    """S384's own G2 (20 deposited exp04 rows rescored with the v1 key on this device; it exits on a mismatch), the
    scorer's outputs kept; then key_signals on the same 20 answers and v1 keys, which must ask MiniCheck nothing the G2
    pass did not and give the deposited values (gate_key_own)."""
    import S384_exp04_minicheck_key_v22 as S384
    from machine import require
    require(S384.ARTEFACT, S384.GENERATION, S384.DEPOSITED, S384.KEY_V1)
    S384.require_as_v1_from_key()
    ns, shas = S384.deposited_code()
    dep = json.loads(S384.ARTEFACT.read_text())["per_result"]
    results = json.loads(S384.GENERATION.read_text())["per_question_results"]
    by_key = {(r["question_id"], r.get("config", "unknown")): r for r in results}
    scorer, info = S384.load_minicheck(device)
    check_mc_limit(scorer)
    memo = MemoScorer(scorer)
    ev = S384.gate_g2(ns, memo, by_key, dep, device)
    msg = (f"key gate pass (S384 G2) on {device}: {ev['rows_matched']}/{ev['rows_compared']} deposited rows, P, R, F1, "
           f"counts and labels exact, {ev['probabilities_identical_4dp']}/{ev['sentences_compared']} probabilities "
           f"identical at 4 dp, max |diff| {ev['max_abs_probability_diff']}")
    print(msg, flush=True)
    own = gate_key_own(ns, memo, by_key, dep, ev["rows"], S384.KEY_V1)
    return ns, scorer, info, [{"gate": "S384 G2", "message": msg, "evidence": ev, "shas": shas}, own]


def details_match(got: list, dep: list, tol: float, label: str) -> bool:
    """Per-sentence details against the deposit as S384's G2 compares them (S384_exp04_minicheck_key_v22.py, PROB_TOL):
    the same sentences in order, labels exact (label: "supported" on the precision side, "covered" on the recall side,
    as G2 reads them), each probability within tol (the artefact rounds to 4 dp, and the
    Beelink's CPU gives one of 440 probabilities 0.0001 away from the laptop's, 21 October)."""
    if len(got) != len(dep):
        return False
    for x, y in zip(got, dep):
        if x["sentence"] != y["sentence"] or x[label] != y[label]:
            return False
        if abs(x["probability"] - y["probability"]) > tol + 1e-12:
            return False
    return True


def gate_key_own(ns: dict, memo: MemoScorer, by_key: dict, dep: list, rows: list, key_v1: Path) -> dict:
    """key_signals, this stage's call, on S384 G2's rows: every MiniCheck call it makes was made by the deposited
    path (memo frozen: a call with other documents or claims is a miss), and its P, R, F1 and per-sentence details
    are the deposited ones (sentences and labels exact, probabilities within S384's PROB_TOL, as G2; details_match);
    a side over MiniCheck's cut must be null with that reason. Raises GateFail."""
    import S384_exp04_minicheck_key_v22 as S384
    gt = {q["id"]: q for q in ns["load_ground_truth"](key_v1, answerable_only=False)}
    deposited = {(d["question_id"], d["config"]): d for d in dep}
    memo.frozen, memo.misses = True, 0
    bad, cut, n = [], 0, 0
    for k in rows:
        q, c = k.split("|", 1)
        d, r = deposited[(q, c)], by_key[(q, c)]
        row = key_signals(gate_answer(q, c, (r.get("generation") or {}).get("answer", "")),
                          gt[q].get("expected_answer", ""), ns, memo)
        n += 1
        for s in SIGNALS["key"]:
            v, why = row["signals"][s], row["null_reasons"].get(s)
            if v is None and why == OVER.format(n=MC_LIMIT):
                cut += 1
            elif v != d["minicheck"][s]:
                bad.append((q, c, s, d["minicheck"][s], v, why))
        for side, lab in (("precision", "supported"), ("recall", "covered")):
            got = row["detail"][f"{side}_details"]
            if got is not None and not details_match(got, d["minicheck_details"][f"{side}_details"], S384.PROB_TOL, lab):
                bad.append((q, c, f"{side}_details differ"))
    if memo.misses:
        bad.append(f"{memo.misses} MiniCheck calls the deposited path never made")
    if bad or n != len(rows) or not n:
        raise GateFail(f"key gate (key_signals) FAIL: {len(bad)} mismatches over {n} rows; first {bad[:3]}")
    msg = (f"key gate pass (key_signals on S384 G2's rows): {n}/{len(rows)} rows, P, R, F1 and per-sentence details "
           f"equal to the deposit, every MiniCheck call one the deposited path made (0 misses); {cut} signals null over "
           f"MiniCheck's {MC_LIMIT}-token cut")
    print(msg, flush=True)
    return {"gate": "key_signals on the G2 rows", "message": msg, "rows": n, "cut_signals": cut}


def papers_gate_inputs():
    """The S19 rows and the deposited answers the papers gate reads, as S19's main() reads them."""
    from machine import PUB, require
    gen_path = PUB / "results/exp04_generation_latest.json"
    require(gen_path, S19_FULLDOC, S18_DOCS, S18_MANIFEST)
    ref = [json.loads(x) for x in S19_FULLDOC.read_text().splitlines() if x.strip()][:len(PAPERS_GATE_ROWS)]
    gen = json.loads(gen_path.read_text())
    answers = {(r["question_id"], r["config"]): (r["generation"] or {}).get("answer", "")
               for r in gen["per_question_results"] if r.get("answerable")}
    return ref, answers


def gate_papers(scorer, decompose, check, ref, answers, docs_prod, device) -> dict:
    """The first rows of S19_minicheck_source_fulldoc.jsonl rescored by this stage's papers_signals on this stage's
    documents (papers_docs: the key's files, join_docs): the same files, claims, labels and precision, every
    probability within PROB_TOL. Raises GateFail."""
    got_rows = [(r["question_id"], r["config"]) for r in ref]
    if tuple(got_rows) != PAPERS_GATE_ROWS:
        raise GateFail(f"papers gate: the first rows of {S19_FULLDOC.name} are {got_rows}, not {PAPERS_GATE_ROWS}")
    bad, n, exact, worst, t0, cut = [], 0, 0, 0.0, time.time(), []
    for r in ref:
        q, c = r["question_id"], r["config"]
        if r.get("condition") != "source" or r.get("mode") != "full-doc":
            raise GateFail(f"papers gate: {q} {c} is not a full-doc source row")
        doc = docs_prod.get(q)
        if not doc or doc["files"] != r["doc_files"]:
            raise GateFail(f"papers gate: this stage's papers for {q} are {doc and doc['files']}, S19's {r['doc_files']}")
        row = papers_signals(gate_answer(q, c, answers[(q, c)]), doc, decompose, check, scorer, keep_cut=True)
        det = row["detail"]
        if "per_claim_on_cut_input" in det:     # S19 scored this row on a cut input: null here, its values reproduced
            lim = det["minicheck_inputs"]["limit"]
            if row["signals"]["precision"] is not None or row["null_reasons"].get("precision") != OVER.format(n=lim):
                bad.append((q, c, "a cut input not null", row["signals"], row["null_reasons"]))
            cut.append(f"{q} {c} ({det['minicheck_inputs']['precision']['cut_claims']} of {det['n_claims']} claims, "
                       f"longest input {det['minicheck_inputs']['precision']['max_tokens']} tokens)")
            per, prec = det["per_claim_on_cut_input"], det["precision_on_cut_input"]
        else:
            per, prec = det.get("per_claim") or [], row["signals"]["precision"]
        if len(per) != r["n_claims"] or prec != r["precision"]:
            bad.append((q, c, "n_claims/precision", (r["n_claims"], r["precision"]), (len(per), prec),
                        row["null_reasons"]))
        for x, y in zip(per, r["per_claim"]):
            n += 1
            d = abs(x["probability"] - y["probability"])
            worst, exact = max(worst, d), exact + (d == 0)
            if x["claim"] != y["claim"] or x["supported"] != y["supported"] or d > PROB_TOL + 1e-12:
                bad.append((q, c, y["claim"][:40], y["supported"], y["probability"], x["supported"], x["probability"]))
    if bad or n != PAPERS_GATE_CLAIMS:
        raise GateFail(f"papers gate FAIL on {device}: {len(bad)} mismatches, {n} claims (want {PAPERS_GATE_CLAIMS}); "
                       f"first {bad[:3]}")
    msg = (f"papers gate pass on {device} (papers_docs, papers_signals): {len(ref)}/{len(ref)} rows of "
           f"{S19_FULLDOC.name} ({', '.join(f'{q} {c}' for q, c in got_rows)}), {n} claims, files, n_claims, precision, "
           f"claims and labels exact, {exact}/{n} probabilities identical at 4 dp, max |diff| {worst:.4f} "
           f"(tolerance {PROB_TOL}); {len(cut)} of the rows S19 scored on an input over MiniCheck's {MC_LIMIT}-token "
           f"cut, null in this stage{': ' + '; '.join(cut) if cut else ''}; {time.time() - t0:.0f} s")
    print(msg, flush=True)
    return {"gate": "S19 full-doc rows", "message": msg, "claims": n, "max_abs_probability_diff": round(worst, 6),
            "rows_over_the_cut": cut, "seconds": round(time.time() - t0, 1)}


def gate_papers_stage(device: str, docs_prod: dict):
    """MiniCheck as S384 loads it, the deposited decomposer as S384 lifts it, then the papers gate."""
    import S384_exp04_minicheck_key_v22 as S384
    import S19_minicheck_regrounded as S19
    ns, _ = S384.deposited_code()
    scorer, info = S384.load_minicheck(device)
    check_mc_limit(scorer)
    return ns, scorer, info, [gate_papers(scorer, ns["decompose_to_sentences"], S19.check, *papers_gate_inputs(),
                                          docs_prod, device)]


def load_bge():
    """bge-m3 as LOCK.toml [retrieval] embedding names it: that revision, from the local cache only, on that device."""
    from sentence_transformers import SentenceTransformer
    spec = lock_info()["embedding"]
    if spec["hf_repo"] != "BAAI/bge-m3" or not spec["local_files_only"]:
        raise Refused(f"LOCK.toml [retrieval] embedding is {spec}, not a local BAAI/bge-m3")
    hf_snapshot(spec["hf_repo"], spec["revision"])
    enc = SentenceTransformer(spec["hf_repo"], device=spec["device"], revision=spec["revision"],
                              local_files_only=True)
    got = getattr(enc[0].auto_model.config, "_commit_hash", None)
    if got != spec["revision"]:
        raise Refused(f"bge-m3 loaded revision {got}, the lock names {spec['revision']}")
    if enc.max_seq_length != LIMITS["bge_m3"]:
        raise Refused(f"bge-m3 max_seq_length {enc.max_seq_length}, not {LIMITS['bge_m3']}")
    return enc, spec


def bert_tokenizer():
    from bert_score.utils import get_tokenizer
    hf_snapshot("roberta-large", ROBERTA_SNAPSHOT)
    tok = get_tokenizer("roberta-large", False)        # bert_score.score's own call (score.py:97)
    if tok.model_max_length != LIMITS["bertscore"]:
        raise Refused(f"roberta-large model_max_length {tok.model_max_length}, not {LIMITS['bertscore']}")
    return tok


def bert_count(tok, text: str) -> int:
    """Word pieces bert_score would feed for text before its cut: sent_encode's call (bert_score/utils.py:194-201)
    without truncation, checked against sent_encode itself."""
    from bert_score.utils import sent_encode
    s = text.strip()
    n = len(tok.encode(s, add_special_tokens=True, add_prefix_space=True))
    if len(sent_encode(tok, text)) != min(n, tok.model_max_length):
        raise Refused("this token count is not bert_score's sent_encode")
    return n


def bge_count(enc, text: str) -> int:
    return len(enc.tokenizer.encode(text, add_special_tokens=True))


def key_flags(key_path: Path) -> dict:
    return {q["id"]: q.get("answerable") for q in json.loads(Path(key_path).read_text())["questions"]}


class OverlapFns:
    """The real metric calls of the overlap stage (overlap_rows takes them through this object, and gate_overlap runs
    the earlier scripts' gates through them)."""

    def __init__(self, device: str, key_path: Path):
        import S07_baseline_metrics as S07
        import S382_exp04_objective_v22 as S382
        from S141_runner import scorers as sc
        self.S07, self.S382, self.sc, self.device, self.key_path = S07, S382, sc, device, key_path
        self.s07_fns = {"rouge_l": S07.rouge_l, "meteor": S07.meteor, "bertscore": S07.bertscore}   # S07's own
        self.versions: dict = {}
        self.ns, self.sources, self.sink = S382.deposited_scorer()
        self.flags = key_flags(key_path)
        self.bert_tok = bert_tokenizer()
        self.enc, self.spec = load_bge()

    def limit(self, enc):
        return LIMITS[enc]

    def tokens(self, enc, text):
        return bert_count(self.bert_tok, text) if enc == "bertscore" else bge_count(self.enc, text)

    def rouge(self, ans, exp):
        return self.s07_fns["rouge_l"](ans, exp, self.versions)

    def meteor(self, ans, exp):
        return self.s07_fns["meteor"](ans, exp, self.versions)

    def bertscore(self, ans, exp):
        return self.s07_fns["bertscore"](ans, exp, self.device, self.versions)

    def number_overlap(self, batch, key_path: Path | None = None):
        """S382's path: the deposited score_all on rows carrying the key's answerable flag and the answer's error (its
        empty branch also takes an errored answer, the module docstring); config is the answer_key, so two draws of a
        question and strategy stay apart."""
        kp, flags = (self.key_path, self.flags) if key_path is None else (key_path, key_flags(key_path))
        rows = [{"question_id": a["question_id"], "config": a["answer_key"], "answerable": flags[a["question_id"]],
                 "generation": {"answer": a["answer"], "error": a["error"]}} for a in batch]
        scored, skipped = self.S382.score(self.ns, rows, kp, None, self.sink)
        by = {r["config"]: r["objective_metrics"].get("number_overlap") for r in scored}
        if skipped or len(by) != len(batch) or any(v is None for v in by.values()):
            raise Refused(f"score_all skipped {skipped} of {len(batch)} rows, or scored one as unanswerable")
        return [by[a["answer_key"]] for a in batch]

    def number_overlap_stripped(self, expected, answer):
        return self.ns["compute_number_overlap"](expected, self.sc.strip_citations(answer))   # S141 det_record

    def key_numbers(self, expected):
        return len(self.ns["extract_numbers"](expected))

    def similarity(self, expected, answer):
        """(similarity, cost, meta): S141_runner.scorers.semantic_similarity on the whole texts, the pinned encoder."""
        return self.sc.semantic_similarity(expected, answer, self.enc, None)


def gate_overlap(fns: OverlapFns, device: str) -> list[dict]:
    """The earlier scripts' gates, each run through OverlapFns (each exits, raises GateFail or returns a failed
    verdict on a mismatch): S07's reproduce_v1, S382's gate and then OverlapFns.number_overlap on its 528 rows, S141's
    similarity reproduce, and OverlapFns.number_overlap_stripped on S141's deterministic artefact."""
    import argparse as ap
    import S141_scorers_4_2b as S141
    from machine import require
    S07, S382 = fns.S07, fns.S382
    require(S07.MASTER, S07.GEN, S07.GT, S07.V1_SCORES, S382.GEN, S382.DET, S382.KEY_V1, S141.V1_KEY)
    S07.require_as_v1_from_key()
    out = []

    def bert_here(preds, refs, dev, versions):
        if dev != fns.device:
            raise GateFail(f"S07's gate asked BERTScore on {dev}, this stage runs it on {fns.device}")
        return fns.bertscore(preds, refs)

    with swapped(S07, rouge_l=lambda p, r, v: fns.rouge(p, r), meteor=lambda p, r, v: fns.meteor(p, r),
                 bertscore=bert_here):
        g07 = S07.reproduce_v1(device, True, fns.versions)
    out.append({"gate": "S07 reproduce_v1 through OverlapFns", "evidence": g07, "message": (
        f"overlap gate S07 pass (OverlapFns.rouge, .meteor, .bertscore): ROUGE-L {g07['rouge_l_f1']['n_exactly_equal']}/"
        f"{g07['rouge_l_f1']['of']} and METEOR {g07['meteor']['n_exactly_equal']}/{g07['meteor']['of']} v1 rows exact, "
        f"BERTScore {g07['bertscore_f1']['n_within_tolerance']}/{g07['bertscore_f1']['of']} within "
        f"{g07['bertscore_f1']['tolerance']} on {device} (max |delta| {g07['bertscore_f1']['max_abs_delta']:.2e})")})
    print(out[-1]["message"], flush=True)

    gen = json.loads(S382.GEN.read_text())["per_question_results"]
    det = json.loads(S382.DET.read_text())
    g382 = S382.gate(fns.ns, gen, det, fns.sink)
    dep = {(r["question_id"], r["config"]): r for r in det["per_result"] if r["answerable"]}
    gen_by = {(r["question_id"], r["config"]): r for r in gen}
    batch = [{"question_id": q, "answer_key": f"{q}|{c}",
              "answer": ((gen_by[(q, c)].get("generation") or {}).get("answer") or ""),
              "error": (gen_by[(q, c)].get("generation") or {}).get("error")} for q, c in sorted(dep)]
    mine = fns.number_overlap(batch, key_path=S382.KEY_V1)
    diffs = [abs(float(v) - float(dep[(a["question_id"], a["answer_key"].split("|", 1)[1])]["objective_metrics"]
                                   ["number_overlap"])) for a, v in zip(batch, mine)]
    n_eq = sum(d == 0 for d in diffs)
    if n_eq != len(batch) or len(batch) != 528:
        raise GateFail(f"overlap gate OverlapFns.number_overlap FAIL: {n_eq} of {len(batch)} v1 rows equal, max "
                       f"|diff| {max(diffs):.2e}")
    msg = (f"overlap gate S382 pass: S382's own gate on all {g382['answerable']} answerable and {g382['unanswerable']} "
           f"unanswerable v1 rows, then OverlapFns.number_overlap {n_eq}/{len(batch)} answerable v1 rows equal to the "
           f"deposit")
    print(msg, flush=True)
    out.append({"gate": "S382 gate, then OverlapFns.number_overlap", "evidence": {**g382, "overlapfns_equal": n_eq},
                "message": msg})

    def sim_here(expected, generated, encoder, truncate_chars=None):
        if encoder is not fns.enc or truncate_chars is not None:
            raise GateFail("S141's reproduce asked for another encoder or a cut")
        return fns.similarity(expected, generated)

    with swapped(S141, load_encoder=lambda dev: fns.enc, semantic_similarity=sim_here):
        g141 = S141.reproduce("similarity", S141.V1_SIGNALS, S141.Key(S141.V1_KEY),
                              ap.Namespace(reproduce_n=20, device=fns.spec["device"]))
    if not g141["passed"]:
        for m in g141["mismatches"][:10]:
            print("   ", m[:300])
        raise GateFail(f"overlap gate S141 similarity FAIL: {g141['rows_matched']} of {g141['rows_compared']} rows")
    msg = (f"overlap gate S141 similarity pass (OverlapFns.similarity): {g141['rows_matched']}/{g141['rows_compared']} "
           f"v1 rows within {g141['tolerance']} on {g141['device']} with bge-m3 at {fns.spec['revision'][:12]} (max gap "
           f"{g141['max_abs_float_gap']:.2e})")
    print(msg, flush=True)
    out.append({"gate": "S141 reproduce similarity through OverlapFns", "evidence": g141, "message": msg})

    campaign = {(arm.name, row.get("config"), row.get("question_id")): row
                for arm in S141.arms() for row in S141.rows_of(arm)}
    key1 = S141.Key(S141.V1_KEY)
    n = n_eq = 0
    bad = []
    for f in sorted(Path(S141.V1_SIGNALS).glob("*.deterministic.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            if "number_overlap" not in r:
                continue
            row = campaign.get((r["arm"], r["config"], r["question_id"]))
            if row is None or r["question_id"] not in key1.questions:
                bad.append((r["arm"], r["config"], r["question_id"], "not in the campaign or the v1 key"))
                continue
            got = fns.number_overlap_stripped(key1.questions[r["question_id"]].get("expected_answer", ""),
                                              S141.answer_of(row))
            n += 1
            if got == r["number_overlap"]:
                n_eq += 1
            else:
                bad.append((r["arm"], r["config"], r["question_id"], r["number_overlap"], got))
    if bad or not n:
        raise GateFail(f"overlap gate OverlapFns.number_overlap_stripped FAIL: {n_eq} of {n} rows equal; first {bad[:3]}")
    msg = (f"overlap gate S141 deterministic pass (OverlapFns.number_overlap_stripped): {n_eq}/{n} v1 rows of S141's "
           f"deterministic artefact equal")
    print(msg, flush=True)
    out.append({"gate": "S141 deterministic number overlap through OverlapFns", "message": msg, "rows": n})
    return out


# ---------------------------------------------------------------- the stages

def load_docs() -> dict:
    return {d["file"]: d["text"] for d in (json.loads(x) for x in S18_DOCS.read_text().splitlines() if x.strip())}


def papers_docs(key: dict, answers: list[dict]) -> tuple[dict, list[str]]:
    """question -> its papers, from the key's source_files (join_docs); and every question where the key and S18's
    sizing differ."""
    docs = load_docs()
    sizing = json.loads(S18_MANIFEST.read_text())["sizing"]
    out, differ = {}, []
    for q in sorted({a["question_id"] for a in answers if a["group"] in APPLIES}):
        files = key["questions"][q].get("source_files") or []
        if not files or any(f not in docs for f in files):
            raise Refused(f"{q}: source_files {files} are not all in {S18_DOCS.name}")
        s = (sizing.get(q) or {}).get("source_files")
        if s != files:
            differ.append(f"{q}: key {files}, S18 sizing {s}")
        text = join_docs(docs, files)
        out[q] = {"files": files, "text": text, "sha256": sha256_text(text)}
    return out, differ


def versions() -> dict:
    import importlib.metadata as md
    v = {"python": sys.version.split()[0], "platform": f"{platform.system()} {platform.machine()}"}
    for p in ("torch", "transformers", "sentence-transformers", "bert-score", "rouge-score", "nltk", "minicheck",
              "numpy", "pandas", "huggingface-hub", "tokenizers"):
        try:
            v[p] = md.version(p)
        except md.PackageNotFoundError:
            v[p] = None
    return v


def git_state() -> dict:
    def run(*a):
        r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    st = run("status", "--porcelain", "--", "scripts", "experiments")
    return {"commit": run("rev-parse", "HEAD"), "dirty_scripts_or_experiments": bool(st) if st is not None else None}


def lifted_shas() -> dict:
    out = {}
    for name in ("S384_exp04_minicheck_key_v22", "S19_minicheck_regrounded", "S07_baseline_metrics",
                 "S382_exp04_objective_v22", "S141_scorers_4_2b", "S141_runner/scorers", "S373_rejudge_v2", "machine"):
        out[f"scripts/{name}.py"] = sha256_file(SCRIPTS / f"{name}.py")
    for p in ("experiments/scorers/records.py", "experiments/runner/experiment.py", "experiments/runner/lock.py"):
        out[p] = sha256_file(ROOT / p)
    return out


def emit(fh, row: dict) -> None:
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def end_at(seconds_left: float) -> str:
    return f"{(datetime.now() + timedelta(seconds=seconds_left)):%d %b %H:%M}"


def run_stage(a, key: dict, answers: list[dict], info: dict, inputs_info: dict) -> int:
    stage, outdir = a.stage, Path(a.outdir)
    by_key = {x["answer_key"]: x for x in answers}
    ident = identity(key, inputs_info)
    params = {**stage_params(stage), "code": code_shas()}
    i, n = a.shard_t
    check_header(outdir, ident, stage, params, n)
    out = outdir / stage / f"{stage}.shard{i}of{n}.jsonl"
    with (contextlib.ExitStack() if a.gate_only else take_locks(outdir, stage, a.shard_t)):
        if not a.gate_only:
            cut = cut_unfinished_tail(out)
            if cut:
                print(f"cut an unfinished last line ({cut} bytes) off {out}: a process stopped while writing it")
        unfinished: list = []
        done = read_done(outdir / stage, by_key, unfinished)
        for u in unfinished:
            print(f"  {u}: being written by another shard, or cut by a kill; read as not done")
        sel = ordered(answers, a.draws, a.shard_t, a.question_set)
        todo = [x for x in sel if x["answer_key"] not in done]
        n_done = len(sel) - len(todo)
        if a.limit:
            todo = todo[:a.limit]
        print(f"{stage}: draws {list(a.draws)}, shard {a.shard}: {len(sel)} answers selected, {n_done} already written, "
              f"{len(todo)} to do", flush=True)
        docs = None
        if stage == "papers":
            docs, differ = papers_docs(key, answers)
            print(f"papers: source files from the key; {len(differ)} questions where the key and S18's sizing differ:")
            for d in differ:
                print(f"    {d}")
        if not todo and not a.gate_only:
            print("nothing to do; no model loaded, nothing written")
            return 0
        if a.threads:
            import torch
            torch.set_num_threads(a.threads)
        t_load = time.time()
        if stage == "key":
            ns, scorer, mcinfo, gates = gate_key(a.device)
        elif stage == "papers":
            ns, scorer, mcinfo, gates = gate_papers_stage(a.device, docs)
        else:
            fns = OverlapFns(a.device, key["file"])
            gates = gate_overlap(fns, a.device)
            mcinfo = {"bertscore_device": a.device, "similarity": fns.spec}
        print(f"gates passed in {time.time() - t_load:.0f} s (models loaded)", flush=True)
        if a.gate_only:
            print("--gate-only: nothing written")
            return 0
        session = {"session": uuid.uuid4().hex, "stage": stage, "started": utc(), "host": platform.node(),
                   "git": git_state(), "script_sha256": sha256_file(Path(__file__)), "files_sha256": lifted_shas(),
                   "lock": {k: v for k, v in lock_info().items()}, "device": a.device, "threads": a.threads,
                   "torch_threads": __import__("torch").get_num_threads(), "shard": a.shard, "draws": list(a.draws),
                   "limit": a.limit, "questions": sorted(a.question_set) if a.question_set else None,
                   "inputs_dir": str(a.inputs), "versions": versions(), "model": mcinfo, "selection": info,
                   "gates": gates, "to_do": len(todo), "nltk_data": nltk_data()}
        write_header(outdir, ident, stage, params, session, n)
        out.parent.mkdir(parents=True, exist_ok=True)
        stamp = {"device": a.device, "session": session["session"]}
        t0 = time.time()
        over = {c: 0 for c in CONFIGS}
        with open(out, "a", encoding="utf-8") as fh:
            if stage == "key":
                for k, x in enumerate(todo, 1):
                    t = time.time()
                    row = key_signals(x, key["questions"][x["question_id"]].get("expected_answer") or "", ns, scorer)
                    emit(fh, {**row, **stamp, "seconds": round(time.time() - t, 2), "ts": utc()})
                    over[x["config"]] += any(r.startswith("over the encoder") for r in row["null_reasons"].values())
                    if k % 20 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)} answers, {el / 60:.1f} min, {el / k:.2f} s/answer, end about "
                              f"{end_at(el / k * (len(todo) - k))}", flush=True)
            elif stage == "papers":
                import S19_minicheck_regrounded as S19
                dec = ns["decompose_to_sentences"]
                n_cl = {x["answer_key"]: (len(dec(x["answer"])) if x["group"] in APPLIES and x["answer"].strip() else 0)
                        for x in todo}
                units = {x["answer_key"]: n_cl[x["answer_key"]] * (len(docs[x["question_id"]]["text"])
                                                                  if x["group"] in APPLIES else 0) for x in todo}
                total_u, claims_total = sum(units.values()), sum(n_cl.values())
                print(f"  {claims_total} claims to check, {total_u / CHARS_UNIT:.0f} claim x 25k-character units", flush=True)
                done_u = done_c = 0
                for k, x in enumerate(todo, 1):
                    def beat(c_done, c_all, sec, x=x):
                        print(f"    {x['answer_key']}: {c_done}/{c_all} claims, {sec / max(c_done, 1):.1f} s/claim",
                              flush=True)
                    row = papers_signals(x, docs.get(x["question_id"]) or {}, dec, S19.check, scorer, beat) \
                        if x["group"] in APPLIES else not_applicable(x, "papers")
                    emit(fh, {**row, **stamp, "ts": utc()})
                    over[x["config"]] += any(r.startswith("over the encoder") for r in row["null_reasons"].values())
                    done_u += units[x["answer_key"]]
                    done_c += n_cl[x["answer_key"]]
                    el = time.time() - t0
                    rate = el / max(done_u, 1)
                    print(f"  {k}/{len(todo)} answers ({x['answer_key']}), {done_c}/{claims_total} claims, "
                          f"{el / 60:.1f} min, {el / max(done_c, 1):.1f} s/claim, {rate * CHARS_UNIT:.1f} s/claim per "
                          f"25k chars, end about {end_at(rate * (total_u - done_u))}", flush=True)
            else:
                key_q = key["questions"]
                for s in range(0, len(todo), OVERLAP_BATCH):
                    batch = todo[s:s + OVERLAP_BATCH]
                    t = time.time()
                    rows = overlap_rows(batch, key_q, fns)
                    for row in rows:
                        emit(fh, {**row, **stamp, "ts": utc()})
                    el = time.time() - t0
                    print(f"  {s + len(batch)}/{len(todo)} answers, batch {time.time() - t:.0f} s, "
                          f"{el / (s + len(batch)):.2f} s/answer", flush=True)
        el = time.time() - t0
        print(f"{stage}: wrote {len(todo)} rows to {out} in {el / 60:.1f} min ({el / max(len(todo), 1):.2f} s/answer)")
        if stage != "overlap":
            print(f"{stage}: answers with a signal null over MiniCheck's {MC_LIMIT}-token cut, by strategy: {over}")
    return 0


def missing_rows(done: dict, answers: list[dict], draws) -> list[dict]:
    """The answers of the draws asked that have no row."""
    return [x for x in answers if x["draw"] in draws and x["answer_key"] not in done]


def verify(a, answers: list[dict]) -> int:
    """The stages' rows against Rule 8, Rule 10 and the encoders' cuts, and whether every selected answer has a row."""
    outdir = Path(a.outdir)
    by_key = {x["answer_key"]: x for x in answers}
    bad_all = missing_all = 0
    for stage in a.verify_stages:
        draws = a.draws_arg or ((1,) if stage == "papers" else DRAWS)
        unfinished: list = []
        done = read_done(outdir / stage, by_key, unfinished)
        sel = [x for x in answers if x["draw"] in draws]
        missing = missing_rows(done, answers, draws)
        missing_all += len(missing)
        bad = [(k, v) for k, r in done.items() for v in row_violations(r)]
        bad_all += len(bad)
        by_draw = {d: sum(1 for r in done.values() if r["draw"] == d) for d in DRAWS}
        print(f"{stage}: {len(done)} rows (by draw {by_draw}); draws {list(draws)}: {len(sel) - len(missing)} of "
              f"{len(sel)} answers written, {len(missing)} missing; {len(bad)} rule violations")
        for u in unfinished:
            print(f"    unfinished line {u}")
        if missing:
            for d in draws:
                per = {c: sum(1 for x in missing if x["draw"] == d and x["config"] == c) for c in CONFIGS}
                if any(per.values()):
                    print(f"    missing, draw {d}: " + ", ".join(f"{c} {v}" for c, v in per.items()))
            print("    first missing: " + ", ".join(x["answer_key"] for x in missing[:5]))
        for k, v in bad[:10]:
            print(f"    {k}: {v}")
        for s in SIGNALS[stage]:
            reasons = {}
            for r in done.values():
                why = r["null_reasons"].get(s)
                if why and why != NA:
                    reasons.setdefault(why, {}).setdefault(r["config"], 0)
                    reasons[why][r["config"]] += 1
            for why, per in sorted(reasons.items()):
                print(f"    {s} null '{why}': " + ", ".join(f"{c} {per.get(c, 0)}" for c in CONFIGS))
        if stage == "overlap":
            ewt = {c: sum(1 for r in done.values() if r["config"] == c and r["status"] == "error"
                          and not r["answer_blank"] and r["group"] in APPLIES) for c in CONFIGS}
            print("    number_overlap on errored answers with text (the deposited branch's 0.0): "
                  + ", ".join(f"{c} {v}" for c, v in ewt.items()))
    failed = bad_all or (missing_all and not a.partial)
    print("VERIFY " + ("FAILED" if failed else "PASSED")
          + (f" (--partial: {missing_all} selected answers have no row)" if a.partial and missing_all else ""))
    return 1 if failed else 0


def weightless_minicheck():
    """MiniCheck-Flan-T5 with its tokenizer and chunking settings but no weights (count-limits and check_S470 count
    inputs with it; mc_input_tokens never reaches the model): MiniCheck's Inferencer with model_name flan-t5-large,
    max_model_len 2048 and the checkpoint's own tokenizer (inference.py:38-44)."""
    import S384_exp04_minicheck_key_v22 as S384
    from minicheck.inference import Inferencer
    from minicheck.minicheck import MiniCheck
    from transformers import AutoTokenizer
    inf = Inferencer.__new__(Inferencer)
    inf.model_name, inf.max_model_len, inf.batch_size = "flan-t5-large", MC_LIMIT, 16
    inf.tokenizer = AutoTokenizer.from_pretrained("lytang/MiniCheck-Flan-T5-Large", cache_dir=str(S384.hf_cache()))
    mc = MiniCheck.__new__(MiniCheck)
    mc.model = inf
    return mc


def count_limits(answers: list[dict], key: dict) -> int:
    """Per strategy (and draw), the answers on the 96 scored questions whose answer or key exceeds each limit, and
    the answers whose key-stage MiniCheck inputs exceed MiniCheck's cut on each side."""
    import S384_exp04_minicheck_key_v22 as S384
    tok = bert_tokenizer()
    enc, spec = load_bge()
    mc = weightless_minicheck()
    ns, _ = S384.deposited_code()
    t0 = time.time()
    rows = {}
    for x in answers:
        if x["group"] not in APPLIES or not x["answer"].strip():
            continue
        e = key["questions"][x["question_id"]]["expected_answer"]
        r = rows.setdefault((x["config"], x["draw"]), {"n": 0, "bertscore": 0, "bge_m3": 0, "bert_key": 0, "bge_key": 0,
                                                       "max_bert": 0, "max_bge": 0, "mc_p": 0, "mc_r": 0, "mc_max": 0})
        r["n"] += 1
        ba, be = bert_count(tok, x["answer"]), bert_count(tok, e)
        ga, ge = bge_count(enc, x["answer"]), bge_count(enc, e)
        r["bertscore"] += max(ba, be) > LIMITS["bertscore"]
        r["bge_m3"] += max(ga, ge) > LIMITS["bge_m3"]
        r["bert_key"] += be > LIMITS["bertscore"]
        r["bge_key"] += ge > LIMITS["bge_m3"]
        r["max_bert"], r["max_bge"] = max(r["max_bert"], ba), max(r["max_bge"], ga)
        m = MeteredScorer(mc, dry=True)
        ns["score_faithfulness"](x["answer"], e, m)
        if m.calls:
            p, rc = m.side(m.calls[0]), m.side(m.calls[1])
            r["mc_p"] += bool(p["cut_claims"])
            r["mc_r"] += bool(rc["cut_claims"])
            r["mc_max"] = max(r["mc_max"], p["max_tokens"], rc["max_tokens"])
    print(f"answers on the 96 scored questions with text, by strategy and draw: over BERTScore's {LIMITS['bertscore']} "
          f"and bge-m3's {LIMITS['bge_m3']} tokens (answer or key, specials included; bge-m3 {spec['revision'][:12]}), "
          f"and key-stage MiniCheck inputs over {MC_LIMIT} tokens (precision side: answer sentences against the key; "
          f"recall side: key sentences against the answer); {time.time() - t0:.0f} s")
    print(f"| strategy | draw | answers | over {LIMITS['bertscore']} | of them the key | over {LIMITS['bge_m3']} | "
          f"of them the key | MiniCheck cut, precision | MiniCheck cut, recall | longest answer (roberta / bge-m3) | "
          f"longest MiniCheck input |")
    tot = {"n": 0, "bertscore": 0, "bge_m3": 0, "mc_p": 0, "mc_r": 0}
    for c in CONFIGS:
        for d in DRAWS:
            r = rows.get((c, d))
            if not r:
                continue
            print(f"| {c} | {d} | {r['n']} | {r['bertscore']} | {r['bert_key']} | {r['bge_m3']} | {r['bge_key']} | "
                  f"{r['mc_p']} | {r['mc_r']} | {r['max_bert']} / {r['max_bge']} | {r['mc_max']} |")
            for k in tot:
                tot[k] += r[k]
        s = {k: sum(rows[(c, d)][k] for d in DRAWS if (c, d) in rows) for k in tot}
        print(f"| {c} | all | {s['n']} | {s['bertscore']} | | {s['bge_m3']} | | {s['mc_p']} | {s['mc_r']} | | |")
    print(f"| all | all | {tot['n']} | {tot['bertscore']} | | {tot['bge_m3']} | | {tot['mc_p']} | {tot['mc_r']} | | |")
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--inputs", required=True, type=Path, help="the folder holding runs/ and MANIFEST.sha256")
    ap.add_argument("--stage", required=True, choices=[*STAGES, "verify", "count-limits"])
    ap.add_argument("--outdir", default=str(OUTDIR))
    ap.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"],
                    help="MiniCheck's device (key, papers) and BERTScore's (overlap); bge-m3 runs on the lock's")
    ap.add_argument("--threads", type=int, default=0, help="torch.set_num_threads (0 = torch's default)")
    ap.add_argument("--draws", default=None, help="comma list; default 1 for papers, 1,2,3 otherwise")
    ap.add_argument("--shard", default="0/1", help="i/n: the questions and draws that hash to i (0-based)")
    ap.add_argument("--limit", type=int, default=0, help="at most this many answers (dry runs)")
    ap.add_argument("--questions", default=None, help="comma list of question ids (dry runs)")
    ap.add_argument("--gate-only", action="store_true", help="run the stage's gate, write nothing")
    ap.add_argument("--partial", action="store_true", help="verify: missing rows do not fail it")
    ap.add_argument("--verify-stages", default=",".join(STAGES), help="verify: comma list of stages")
    a = ap.parse_args(argv)
    try:
        i, n = (int(x) for x in a.shard.split("/"))
        assert 0 <= i < n
    except (ValueError, AssertionError):
        ap.error(f"--shard {a.shard}: i/n with 0 <= i < n")
    a.shard_t = (i, n)
    a.draws_arg = tuple(int(x) for x in a.draws.split(",")) if a.draws else None
    a.draws = a.draws_arg or tuple(int(x) for x in ("1" if a.stage == "papers" else "1,2,3").split(","))
    if not set(a.draws) <= set(DRAWS) or len(set(a.draws)) != len(a.draws):
        ap.error(f"--draws {a.draws}: distinct values of {DRAWS}")
    a.verify_stages = tuple(a.verify_stages.split(","))
    if not set(a.verify_stages) <= set(STAGES):
        ap.error(f"--verify-stages {a.verify_stages}: stages of {STAGES}")
    a.question_set = set(a.questions.split(",")) if a.questions else None
    a.inputs = a.inputs.expanduser().resolve()
    return a


def main(argv=None) -> int:
    a = parse_args(argv)
    try:
        nltk_offline()
        key = the_key()
        inputs_info = verify_inputs(a.inputs)
        answers, info = read_answers(a.inputs, key)
        if a.question_set and not a.question_set <= {x["question_id"] for x in answers}:
            raise Refused(f"--questions names ids that are not G1's: {sorted(a.question_set - {x['question_id'] for x in answers})}")
        ewt = info["error_with_text"]
        print(f"selection: {info['answers']} answers, questions {info['questions']} (Rule 8, the runner's D5 key, "
              f"agreeing with S373.AS_V1); D7's dropped {', '.join(info['d7_dropped'])}: {info['d7_answers']} answers "
              f"skipped; empty answers {info['empty']} ({info['empty_scored']} on the 96 scored); status {info['status']}; "
              f"errored answers with text on the 96 {ewt['n']} {ewt['by_strategy'] if ewt['n'] else ''}"
              f"{' first ' + ', '.join(ewt['first']) if ewt['n'] else ''}; inputs manifest "
              f"{inputs_info['manifest_sha256'][:12]}", flush=True)
        if a.stage == "verify":
            return verify(a, answers)
        if a.stage == "count-limits":
            return count_limits(answers, key)
        return run_stage(a, key, answers, info, inputs_info)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    except NltkMissing as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    except GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
