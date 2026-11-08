#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "ragchecker==0.1.9",
#   "en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl",
# ]
# [tool.uv]
# exclude-newer = "2026-10-14T00:00:00Z"
# ///
"""RAGChecker (amazon-science/RAGChecker 0.1.9) on answers that store their passages, every model call under the lock.

    PYTHONHASHSEED=0 uv run --script experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11434 \
        --arm <results.json> --gt <ground truth json> --out <dir> [--limit N] [--rows START:END] [--order claims|passage]
    PYTHONHASHSEED=0 uv run --script experiments/scorers/ragchecker_run.py --base http://127.0.0.1:11434 \
        --run <run sink or results file> --gt <ground truth json> --out <dir> [--store <chroma dir>] [--limit N] [--rows START:END]
        [--order claims|passage]

ORDER (O1 of 16 October, D80 V10; tested in rc_order_test on 8 R0 answers: 1,668 checking calls, the same reply text
and label in both orders). RefChecker builds one checking prompt per (claim, passage), claim by claim
(refchecker/checker/checker_base.py check(): for each claim, for each passage). --order claims (the default) sends
them so, one prompt per RefChecker batch (batch_size_checker 1), exactly as before this option existed. --order
passage gives RefChecker one batch per checking step (batch_size_checker 10**9, ONE_BATCH) and sends that batch's
prompts grouped by their text up to '### Claim:' (question and passage), groups in order of first appearance and
prompts in their own order within a group, so consecutive calls share the passage and the server reuses its cached
prefix; the replies are returned to RefChecker in its own order. The prompts are the same strings in both orders;
only the order they are sent in differs. Every call record carries order, orig_index (the prompt's place in
RefChecker's batch), batch (the batch's number within the answer) and batch_len; the header carries order and
batch_size_checker. Offline checks: experiments/scorers/check_ragchecker_order.py.

STEP ORDER (D83, Q144). RAGChecker runs its four checking steps (answer2response, response2answer, retrieved2response,
retrieved2answer) in the order it iterates a Python set of their names (ragchecker/evaluator.py evaluate(),
"requirements = set()" then "for requirement in requirements"). A set of strings is iterated in the order of their
hashes, which change per process unless PYTHONHASHSEED fixes them. No label depends on that order, but which prompt
the server has cached does (K0). So the scorer refuses to start unless it was started with PYTHONHASHSEED=0 and the
interpreter applied it (sys.flags.hash_randomization 0, which also refuses python -E, -I and -R), and every header
records both as pythonhashseed and hash_randomization. Offline checks: experiments/scorers/check_ragchecker_order.py.
The R0 pilot, the 15 October scorings and K0 ran with the order left to chance (their headers have no such field).

RUN MODE (--run; audit of 16 October F5, F39, F55). The answers of one run as experiments/scorers/records.py reads
them (exp_01, exp_02, exp_03, exp_06 and the authors' RLM, G6), each with the passages its generator saw, resolved
from passage ids to text through the index the run recorded at its start. The --arm path below is unchanged; --run
differs from it only here:
  Rule 8     a question the D5 key marks not answerable (LIST.md:326-340) is written with status "not_applicable",
             metrics null and reason "not applicable", without a model call; `records.py rule8` fails any output
             that holds a number there
  passages   an answer whose record lists no passages (records.py passages_kind "not_recorded") is "unscorable"
  resume     by (run_id, config, question_id, draw); refused when --out holds a row under another lock_sha256, a
             row without run_id (an --arm output), or a row of the same answer with another item_sha256 (records.py
             resume); not_applicable counts as done. Every row carries run_id, answer_key, draw, group,
             passages_kind and item_sha256, the header the runs, their index identities and the --gt sha256

K1 (D83, Q142; findings/recompute/K1/README.md). --run takes several runs, read in one process. With --assignment
<file> --machine <name> (the file of scripts/S451_k1_assign.py, checked by experiments/scorers/assignment.py), only
that machine's answers are scored: the assignment's draws, its questions given to that machine, question by question in
the file's order and the six configs in the file's order inside each question; a missing answer, a config or question
the file does not name, or a file whose sha256 fields do not recompute is refused before anything is written. Every
row and every call record then carries "machine", and the header the assignment's path, file sha256,
assignment_sha256, rule_sha256 and machine. --stop-on-failed ends the process (exit 4) after the first answer recorded
as failed. --dry-run reads, selects and checks the resume and prints the work list, with no model call and no write.
Without these options nothing changes in what is sent or written.
D86 (two stages): with a staged assignment every row and every call record also carries "k1_stage", its question's
stage, and --stage {1,2} scores only that stage's questions (the header records it). "k1_stage", since RefChecker's
own step is already a call record's "stage" (extract, check).
Helpers (Valerio, 17 October; findings/recompute/K1/README.md "Helping K1"): with --worker <name> --amendments
<amendments.json> --amendments-head <sha256> the answers are the worker's under the amendment chain
(experiments/scorers/assignment.py for_worker: the chain verified, the worker on --machine, and its questions under
the pinned head equal to its questions under the file now, or refused); every row and call record also carries
"worker", the header the worker, the chain file's sha256, the pinned head and the number of moves. --machine stays the
physical machine. Without --worker nothing changes.
A stop between answers (D89, K1 O2; findings/recompute/K1/README.md "Stopping a worker"): with --stop-file <path>,
before each answer the process looks for that file; if it exists, it prints "RAGCHECKER STOPPED BETWEEN ANSWERS" and
exits 5 (STOP_EXIT), so the answer in flight is finished and written and no call is cut. The launcher treats exit 5 as
a clean stop; the next start resumes at the next answer. Without --stop-file nothing changes.

REFERENCE CLAIMS (D92, Q190; findings/recompute/K1/README.md "Reference claims"). RAGChecker cuts the reference
answer into claims for every answer it scores (evaluator.py extract_claims, "gt_answer"), so the six answers of one
question were each checked against their own cut: on the Beelink one cutting request gave 6 replies in 7 sends (audit of
17 October F2). With --reference-claims <file> --reference-claims-sha256 <hex> (--run only) the reference of each
question is cut once, on the Studio, by scripts/S462_k1_reference_claims.py, and those claims are passed in with every
answer of the question (RAGResult gt_answer_claims; RAGChecker 0.1.9 evaluator.py:104 then skips the cut). The answer's
own claims and every check run as before. Before anything is read or written the file is refused unless its sha256 is
the one given, the MANIFEST.sha256 beside it names that sha256, every entry's entry_sha256 recomputes, and every entry was
cut under this lock and this model; then every answer this process would score with RAGChecker is refused unless its
question has an ok entry whose reference_sha256 and question_sha256 are the sha256 of this answer's reference and
question (the cut read the same text). Each row then carries reference_claims (the file's sha256, the entry's sha256,
the cut's request and reply sha256, its machine, the claim count) and extract_calls (the answer's extraction calls,
which must be 1: the response's; anything else is recorded as failed). A row is never scored against claims RAGChecker
changed: gt_answer_claims after the run must equal the entry's, or the row is failed. Resume with the file: a prior ok
row counts as done only if it carries this entry's sha256, or carries no reference_claims and its gt_answer_claims equal
the entry's claims exactly (the Studio's rows of 17 October: its cut gave one reply in 5 sends, audit F2); a prior ok row
cut differently is refused with a pointer to S462 archive (the Beelink's rows are archived and scored again, D92), so no
output mixes two cuts. The header records the file, its sha256, its entries and the rows accepted by equal claims.
Without --reference-claims nothing changes.

Model calls. RAGChecker's own path (refchecker -> litellm batch_completion) retries an API error forever and caps
the extractor's reply at 1,000 tokens. Here every call goes through custom_llm_api_func to
experiments/runner/ollama_client.chat with the lock's scorer settings (the judge's: devstral-small-2:24b,
temperature 0, the whole context, no output limit, truncate and shift false). One claim per checking call
(LOCK.toml [scorers] ragchecker_claims_per_call = 1). RefChecker's own joint check (joint_check) is never used. A call that does not end with
"stop" (an error, a stall, an answer that fills the context) raises: the answer is recorded as failed with the
reason, never scored from a cut reply.

Two RefChecker behaviours are guarded here, since neither can be changed from outside it:
  no claims    a reply with no parseable claims gives zero claims, and RAGChecker then scores precision or
               recall 0 (ragchecker/computation.py). An answer with no response claims, no reference claims or no
               reference is recorded as status "unscorable" with the reason; what RAGChecker computed is kept
               under metrics_as_computed, never under metrics. One cause seen on 15 October: RefChecker keeps only
               the text after the first "###" of an extraction reply (refchecker/extractor/llm_extractor.py,
               parse_claims(res, '###')), so a reply that lists its triplets and then adds "### Notes:" yields
               zero claims (1 of 2 smoke answers).
  triplets     so RefChecker receives, from each extraction reply, only its lines that hold a ("subject",
               "predicate", "object") triplet, in order (O1, Valerio, 15 October). The full reply stays in
               ragchecker_calls.jsonl as text; what RefChecker received is text_to_refchecker. A reply with no
               triplet line is passed unchanged (and then gives zero claims, recorded as above).
  labels       RefChecker labels a checking reply Contradiction if that word appears anywhere in it, else
               Entailment if that word does (refchecker/checker/llm_checker.py). With no output cap a reply can
               carry more than the one word asked for. Each checking reply is classed as one clear label or
               ambiguous; an answer with any ambiguous reply is recorded as status "ok_ambiguous_labels" with the
               count, so analysis decides whether to keep it.

JOINT (D103, Valerio 20 October: "Let's try this and see if this improves the speed"). RefChecker's own joint check
(refchecker/checker/llm_checker.py, joint_check) pads a reply's missing labels with "Neutral", cuts extra ones and
matches labels to claims by position, so make_evaluator refuses it. In its place, with --claims-per-call N above 1:
RefChecker builds its one-claim prompts as always and hands each checking step to one batch (--order passage, which N
above 1 requires); the batch's prompts are grouped by (question, passage), and up to N claims of a group go to one call
whose prompt numbers them and asks one "<number>: <label>" line per claim (joint_prompt: our wording, modelled on
RefChecker's JOINT_CHECKING_PROMPT_Q and not equal to it; its rules paragraph is kept word for word, its opening is
reworded to "each claim", a form without a question is added, which RefChecker does not have, and its answer
instructions, an unnumbered list of labels, are replaced by numbered claims, "Judge each claim on its own" and exactly
one numbered label per line). The reply is used only when it gives exactly one valid label for every number and nothing
else (parse_joint); otherwise every claim of that call is asked alone with RefChecker's own one-claim prompt. A claim
alone in its chunk, and a checking prompt that does not rebuild byte for byte from RefChecker's one-claim template
(split_single), are sent as they are. RefChecker then labels each claim from the label word (joint) or from the model's
reply (alone), by its own rule. Call records: a joint call has stage "check_joint", orig_index the list of its prompts'
places, and joint {n, accepted, why, labels}; a prompt asked alone has single_why. Rows add claims_per_call, check_modes
(per checking batch, one code per prompt in RefChecker's order: J<seq> labelled by joint call seq, A alone in its chunk,
R<seq> asked alone after joint call seq was rejected, U not rebuilt) and the counts; the header claims_per_call,
guarded_joint and joint_test. The default N is the lock's ragchecker_claims_per_call (1); another N runs only with
--joint-test, until Valerio decides on the lock (D103), and at N = 1 nothing of this is reached: the one-claim path
sends what it sent before (experiments/scorers/check_ragchecker_order.py).

Output, one line per answer, resumable by (config, question_id): <out>/ragchecker.jsonl with RAGChecker's
per-answer metrics, the claims and the entailment labels it computed them from, wall time, call counts and the
lock sha256. Rows with no answer or a generation error are written with status "no_answer". On resume only rows
with status ok or ok_ambiguous_labels count as done; failed and unscorable rows are tried again (a new line, the
latest line per answer is the one that counts). D110 (Valerio, 21 October, Q25): an answer whose latest two rows are both failed by
a reply that reached num_predict (error "model call length: ...") counts as done, so a resume no longer retries it; its
latest row stays "failed", so every count shows it. Every model call: <out>/ragchecker_calls.jsonl (the D37 record,
the answer it belongs to, its stage and, for checking calls, its label class). Each start appends its settings
to <out>/ragchecker_headers.jsonl.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.runner.lock import load  # noqa: E402
from experiments.runner.ollama_client import chat  # noqa: E402

CHECK_SIGNATURE = "only a single word in ['Entailment', 'Neutral', 'Contradiction']"
TRIPLET = re.compile(r"""\(\s*["'].*["']\s*,\s*["'].*["']\s*,\s*["'].*["']\s*\)""")


def triplet_lines(text: str) -> str:
    """The lines of an extraction reply that hold a triplet, joined in order; the reply itself when it has none."""
    kept = [ln.strip() for ln in text.splitlines() if TRIPLET.search(ln)]
    return "\n".join(kept) if kept else text
LABELS = {"entailment", "neutral", "contradiction"}
DONE = {"ok", "ok_ambiguous_labels", "no_answer"}


def label_class(text: str) -> str:
    """'clear' when the reply is exactly one label (case, whitespace, quotes and a final full stop aside)."""
    t = text.strip().strip("`*'\" ").rstrip(".").strip().lower()
    return "clear" if t in LABELS else "ambiguous"


HASH_SEED = "0"                         # D83 (Q144): RAGChecker's four checking steps in one fixed order


def hash_seed_state() -> dict:
    """The PYTHONHASHSEED this process was started with and whether the interpreter applied it (STEP ORDER)."""
    return {"pythonhashseed": os.environ.get("PYTHONHASHSEED"), "hash_randomization": sys.flags.hash_randomization}


def require_hash_seed() -> dict:
    """hash_seed_state(), or SystemExit unless PYTHONHASHSEED is "0" and hash randomization is off (STEP ORDER)."""
    s = hash_seed_state()
    if s["pythonhashseed"] != HASH_SEED or s["hash_randomization"] != 0:
        raise SystemExit(
            f"REFUSED: PYTHONHASHSEED is {s['pythonhashseed']!r} (hash randomization "
            f"{'on' if s['hash_randomization'] else 'off'}); RAGChecker's four checking steps run in a fixed order only "
            f"when the scorer starts with PYTHONHASHSEED={HASH_SEED} (D83, Q144). Start it as "
            f"'PYTHONHASHSEED={HASH_SEED} uv run --script experiments/scorers/ragchecker_run.py ...', or put "
            f"'export PYTHONHASHSEED={HASH_SEED}' in the launcher, and run python without -E, -I or -R.")
    return s


ORDERS = ("claims", "passage")
ONE_BATCH = 10**9                       # --order passage: RefChecker hands each checking step to llm() as one batch
CLAIM_MARK = "### Claim:"


def batch_size_checker(order: str) -> int:
    return 1 if order == "claims" else ONE_BATCH


def group_key(p) -> str:
    """A checking prompt's text up to '### Claim:' (instructions, question, passage); the whole prompt otherwise."""
    t = p if isinstance(p, str) else json.dumps(p, ensure_ascii=False)
    i = t.find(CLAIM_MARK)
    return t[:i] if i >= 0 else t


def send_order(prompts: list, order: str) -> list[int]:
    """The indices of one batch's prompts in the order they are sent: as given for claims; for passage, grouped by
    group_key, groups in order of first appearance, stable within a group."""
    idx = list(range(len(prompts)))
    if order == "passage" and len(prompts) > 1:
        first: dict = {}
        for i, p in enumerate(prompts):
            first.setdefault(group_key(p), i)
        idx.sort(key=lambda i: (first[group_key(prompts[i])], i))
    return idx


def make_llm(base: str, call, order: str, calls_log: Path, current: dict, per_call: int = 1):
    """RefChecker's custom_llm_api_func: every prompt of a batch through ollama_client.chat under the lock, sent in
    send_order(), one record per call in calls_log, the replies returned in RefChecker's order. per_call above 1 (D103,
    JOINT in the docstring): the guarded joint check, joint_llm(); at 1 nothing of it is reached."""
    if per_call > 1:
        return make_joint_llm(base, call, order, calls_log, current, per_call)

    def llm(prompts):
        current["batch"] = current.get("batch", 0) + 1
        texts = [None] * len(prompts)
        for i in send_order(prompts, order):
            p = prompts[i]
            msgs = [{"role": "user", "content": p}] if isinstance(p, str) else p
            rec = chat(base, call, msgs)
            current["n"] += 1
            stage = "check" if any(CHECK_SIGNATURE in (m.get("content") or "") for m in msgs) else "extract"
            rec.update(answer=current["key"], seq=current["n"], stage=stage, order=order, orig_index=i,
                       batch=current["batch"], batch_len=len(prompts))
            if current.get("machine"):                   # K1 (D83, Q142): the machine in every record
                rec["machine"] = current["machine"]
            if current.get("k1_stage"):                  # K1 (D86): the question's stage in every record
                rec["k1_stage"] = current["k1_stage"]
            if current.get("worker"):                    # K1 helpers: the worker in every record
                rec["worker"] = current["worker"]
            current["extracts"] = current.get("extracts", 0) + (stage == "extract")   # D92 Q190: 1 per answer
            if stage == "check" and rec["status"] == "ok":
                rec["label_class"] = label_class(rec["text"])
                current["checks"] += 1
                current["ambiguous"] += rec["label_class"] == "ambiguous"
            given = triplet_lines(rec["text"]) if stage == "extract" else rec["text"]
            if stage == "extract":
                rec["text_to_refchecker"] = given
            with calls_log.open("a") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if rec["status"] != "ok":
                raise RuntimeError(f"model call {rec['status']}: {rec['error'] or rec['stop_reason']}")
            texts[i] = given
        return texts
    return llm


def make_evaluator(RAGChecker, model: str, order: str, joint: bool, llm):
    """RAGChecker as this scorer builds it (main; S462 cuts the references with the same construction). RefChecker's
    own joint check is refused (D103: it pads missing labels with "Neutral", cuts extra ones and matches by position,
    refchecker/checker/llm_checker.py); more than one claim per call is the guarded joint check in make_llm."""
    if joint:
        raise SystemExit("REFUSED: RefChecker's own joint check (joint_check=True) is never used (D103); more than one "
                         "claim per checking call is this scorer's guarded joint check (--claims-per-call, JOINT)")
    return RAGChecker(extractor_name=f"ollama/{model}", checker_name=f"ollama/{model}",
                      batch_size_extractor=1, batch_size_checker=batch_size_checker(order), joint_check=joint,
                      custom_llm_api_func=llm)


# ---------------------------------------------------------------- the guarded joint check (D103)

JOINT_HEAD_Q = ("I have a list of claims that made by a language model to a question, please help me for checking "
                "whether each claim can be entailed according to the provided reference which is related to the "
                "question. \nThe reference is a list of passages, and each claim is represented as a triplet formatted "
                "with (\"subject\", \"predicate\", \"object\").\n\n")
JOINT_HEAD = ("I have a list of claims that made by a language model, please help me for checking whether each claim "
              "can be entailed according to the provided reference. \nThe reference is a list of passages, and each "
              "claim is represented as a triplet formatted with (\"subject\", \"predicate\", \"object\").\n\n")
JOINT_RULES = ("If the claim is supported by ANY passage in the reference, answer 'Entailment'. \n"
               "If NO passage in the reference entail the claim, and the claim is contradicted with some passage in the "
               "reference, answer 'Contradiction'.\n"
               "If NO passage entail or contradict with claim, or DOES NOT contain information to verify the claim, "
               "answer 'Neutral'. \n\n"
               "Please DO NOT use your own knowledge for the judgement, just compare the reference and the claim to get "
               "the answer.\n\n")
JOINT_TAIL = ("### Claims:\n{claims}\n\nThere are {k} claims, numbered 1 to {k}. Judge each claim on its own. Your "
              "answer should always be exactly {k} lines, one per claim in the order given: the claim's number, a "
              "colon, and a single word in ['Entailment', 'Neutral', 'Contradiction']. For example, for 2 claims:\n"
              "1: Entailment\n2: Neutral\n\nDO NOT add explanations or you own reasoning to the output.\n")
JOINT_LINE = re.compile(r"(\d+)\s*[:.)]\s*(entailment|neutral|contradiction)\.?", re.I)


def single_templates() -> dict:
    """RefChecker's own one-claim checking prompts (refchecker/checker/checker_prompts.py), by whether they hold a
    question: the prompts a joint prompt is built from, and whose exact rebuild decides whether one can be."""
    from refchecker.checker.checker_prompts import LLM_CHECKING_PROMPT, LLM_CHECKING_PROMPT_Q
    return {"q": LLM_CHECKING_PROMPT_Q, "plain": LLM_CHECKING_PROMPT}


def split_single(prompt: str) -> tuple | None:
    """(template, question or None, reference, claim) of one of RefChecker's one-claim checking prompts, only when
    the template filled with them gives the prompt back byte for byte; else None (the prompt is then checked alone)."""
    import string
    for name, t in single_templates().items():
        lits = [lit for lit, *_ in string.Formatter().parse(t)]
        fields = [f for _, f, *_ in string.Formatter().parse(t) if f]
        if fields != (["question", "reference", "claim"] if name == "q" else ["reference", "claim"]):
            continue
        if not (prompt.startswith(lits[0]) and prompt.endswith(lits[-1])):
            continue
        mid = prompt[len(lits[0]):len(prompt) - len(lits[-1])]
        if name == "q":
            q, sep, rest = mid.partition(lits[1])
            if not sep:
                continue
        else:
            q, rest = None, mid
        ref, sep, claim = rest.rpartition(lits[-2])
        if not sep:
            continue
        got = t.format(question=q, reference=ref, claim=claim) if name == "q" else t.format(reference=ref, claim=claim)
        if got == prompt:
            return name, q, ref, claim
    return None


def joint_prompt(name: str, question: str | None, reference: str, claims: list[str]) -> str:
    """The joint checking prompt for k claims of one (question, passage), in our wording modelled on RefChecker's
    JOINT_CHECKING_PROMPT_Q but not equal to it: JOINT_RULES is RefChecker's rules paragraph word for word; JOINT_HEAD_Q
    rewords its opening ("whether each claim", "each claim is represented"); JOINT_HEAD is a form without a question,
    which RefChecker does not have (from its one-claim LLM_CHECKING_PROMPT); JOINT_TAIL replaces its answer
    instructions (an unnumbered list of labels) with numbered claims, "Judge each claim on its own" and exactly one
    "<number>: <label>" line per claim. Each claim is as in its one-claim prompt."""
    head = JOINT_HEAD_Q if name == "q" else JOINT_HEAD
    body = (f"### Question:\n{question}\n\n" if name == "q" else "") + f"### Reference:\n{reference}\n\n"
    lines = "\n".join(f"{n}. {c}" for n, c in enumerate(claims, 1))
    return head + JOINT_RULES + body + JOINT_TAIL.format(claims=lines, k=len(claims))


def parse_joint(text: str, k: int) -> tuple[list | None, str | None]:
    """(labels in claim order, None) when the reply gives exactly one valid label for each of the k numbered claims
    and nothing else (blank lines, and a line of only backticks or asterisks, aside); else (None, why)."""
    got: dict = {}
    for raw in text.splitlines():
        t = raw.strip().strip("`*").strip()
        if not t:
            continue
        m = JOINT_LINE.fullmatch(t)
        if not m:
            return None, f"a line that is not '<number>: <label>': {t[:60]!r}"
        n = int(m[1])
        if not 1 <= n <= k:
            return None, f"number {n} names no claim (1 to {k})"
        if n in got:
            return None, f"claim {n} labelled twice"
        got[n] = m[2].title()
    missing = [n for n in range(1, k + 1) if n not in got]
    if missing:
        return None, f"no label for claim {', '.join(map(str, missing))}"
    return [got[n] for n in range(1, k + 1)], None


def make_joint_llm(base: str, call, order: str, calls_log: Path, current: dict, per_call: int):
    """D103 (JOINT in the docstring). One batch is one RefChecker checking step (one batch per step, --order passage).
    Its one-claim prompts are grouped by (question, passage), groups in order of first appearance; each group's claims,
    in RefChecker's order, go up to per_call to a numbered joint call. A joint reply is used only when it gives exactly
    one valid label for every numbered claim (parse_joint); otherwise each of those claims is asked alone with
    RefChecker's own one-claim prompt. A claim alone in its chunk, an extraction prompt and a checking prompt that does
    not rebuild exactly are sent as they are. RefChecker gets back, in its own order, the joint label word for a claim
    checked jointly and the model's reply for one checked alone. Per batch, current["modes"] gets one code per prompt
    in RefChecker's order: J<seq> (labelled by joint call seq), A (alone in its chunk), R<seq> (asked alone after joint
    call seq was rejected), U (a checking prompt that did not rebuild), X (extraction)."""
    def stamp(rec: dict) -> dict:
        for f in ("machine", "k1_stage", "worker"):
            if current.get(f):
                rec[f] = current[f]
        return rec

    def write(rec: dict) -> None:
        with calls_log.open("a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def one(prompts, i: int, why: str | None) -> str:
        """prompts[i] sent as it is, recorded as the one-claim path records it (plus why it went alone)."""
        p = prompts[i]
        msgs = [{"role": "user", "content": p}] if isinstance(p, str) else p
        rec = chat(base, call, msgs)
        current["n"] += 1
        stage = "check" if any(CHECK_SIGNATURE in (m.get("content") or "") for m in msgs) else "extract"
        rec.update(answer=current["key"], seq=current["n"], stage=stage, orig_index=i, order=order,
                   batch=current["batch"], batch_len=len(prompts), claims_per_call=per_call)
        stamp(rec)
        if why:
            rec["single_why"] = why
        current["extracts"] = current.get("extracts", 0) + (stage == "extract")
        if stage == "check" and rec["status"] == "ok":
            rec["label_class"] = label_class(rec["text"])
            current["checks"] += 1
            current["ambiguous"] += rec["label_class"] == "ambiguous"
        reply = triplet_lines(rec["text"]) if stage == "extract" else rec["text"]
        if stage == "extract":
            rec["text_to_refchecker"] = reply
        write(rec)
        if rec["status"] != "ok":
            raise RuntimeError(f"model call {rec['status']}: {rec['error'] or rec['stop_reason']}")
        return reply

    def llm(prompts):
        current["batch"] = current.get("batch", 0) + 1
        back, modes = [None] * len(prompts), [None] * len(prompts)
        units, groups = [], {}
        for i, p in enumerate(prompts):
            content = p if isinstance(p, str) else json.dumps(p, ensure_ascii=False)
            parts = split_single(p) if isinstance(p, str) and CHECK_SIGNATURE in content else None
            if parts is None:
                units.append(("one", [i], "X" if CHECK_SIGNATURE not in content else "U"))
                continue
            key = parts[:3]
            if key not in groups:
                groups[key] = []
                units.append(("group", key, None))
            groups[key].append((i, parts[3]))
        for kind, what, code in units:
            if kind == "one":
                i = what[0]
                back[i] = one(prompts, i, None if code == "X" else "its prompt does not rebuild from RefChecker's "
                                                                    "one-claim template")
                modes[i] = code
                continue
            members = groups[what]
            for c0 in range(0, len(members), per_call):
                chunk = members[c0:c0 + per_call]
                if len(chunk) == 1:
                    i = chunk[0][0]
                    back[i], modes[i] = one(prompts, i, "alone in its chunk (the only claim, or the last one, of its "
                                                        "passage in this step)"), "A"
                    continue
                text = joint_prompt(what[0], what[1], what[2], [c for _, c in chunk])
                msgs = [{"role": "user", "content": text}]
                rec = chat(base, call, msgs)
                current["n"] += 1
                seq = current["n"]
                rec.update(answer=current["key"], seq=seq, stage="check_joint", order=order,
                           orig_index=[i for i, _ in chunk], batch=current["batch"], batch_len=len(prompts),
                           claims_per_call=per_call)
                stamp(rec)
                current["checks"] += 1
                current["joint_calls"] = current.get("joint_calls", 0) + 1
                if rec["status"] != "ok":
                    write(rec)
                    raise RuntimeError(f"model call {rec['status']}: {rec['error'] or rec['stop_reason']}")
                labels, why = parse_joint(rec["text"], len(chunk))
                rec["joint"] = {"n": len(chunk), "accepted": labels is not None, "why": why, "labels": labels}
                write(rec)
                if labels is not None:
                    for (i, _), lab in zip(chunk, labels):
                        back[i], modes[i] = lab, f"J{seq}"
                    continue
                current["joint_rejected"] = current.get("joint_rejected", 0) + 1
                for i, _ in chunk:
                    back[i], modes[i] = one(prompts, i, f"joint call {seq} rejected: {why}"), f"R{seq}"
        if any(m != "X" for m in modes):
            current.setdefault("modes", []).append({"batch": current["batch"], "modes": modes})
        return back
    return llm


def joint_summary(current: dict, per_call: int) -> dict:
    """What a row records of the guarded joint check (D103): per batch the code of each prompt (make_joint_llm), and
    counts: prompts labelled jointly, asked alone in their chunk, asked alone after a rejected joint reply, not
    rebuilt; joint calls made and rejected."""
    codes = [m for b in current.get("modes", []) for m in b["modes"]]
    return {"claims_per_call": per_call, "check_modes": current.get("modes", []),
            "checked_jointly": sum(m.startswith("J") for m in codes), "checked_alone": codes.count("A"),
            "checked_alone_after_rejection": sum(m.startswith("R") for m in codes), "not_rebuilt": codes.count("U"),
            "joint_calls": current.get("joint_calls", 0), "joint_rejected": current.get("joint_rejected", 0)}


def claims_per_call(a, lock) -> int:
    """D103: the claims per checking call, --claims-per-call or the lock's [scorers] ragchecker_claims_per_call. A
    value other than the lock's runs only with --joint-test (until Valerio decides); above 1 it needs --order passage
    (RefChecker hands a whole checking step to one batch only then). SystemExit on a refusal."""
    want = lock.d["scorers"]["ragchecker_claims_per_call"]
    n = want if getattr(a, "claims_per_call", None) is None else a.claims_per_call
    if not isinstance(n, int) or n < 1:
        raise SystemExit(f"REFUSED: claims per checking call {n!r}: a whole number, 1 or more")
    if n != want and not getattr(a, "joint_test", False):
        raise SystemExit(f"REFUSED: --claims-per-call {n} differs from the lock's ragchecker_claims_per_call {want}: "
                         f"only with --joint-test (D103: the lock decides, after Valerio reads the sample test)")
    if getattr(a, "joint_test", False) and n == 1:
        raise SystemExit("REFUSED: --joint-test with one claim per call tests nothing (give --claims-per-call N, N > 1)")
    if n > 1 and a.order != "passage":
        raise SystemExit(f"REFUSED: {n} claims per checking call needs --order passage (one batch per checking step)")
    return n


# ---------------------------------------------------------------- reference claims (D92, Q190)

CLAIMS_FILE = "reference_claims.jsonl"
CLAIMS_MANIFEST = "MANIFEST.sha256"
SCORED = ("ok", "ok_ambiguous_labels")


def text_sha256(s: str | None) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def entry_sha256(e: dict) -> str:
    """sha256 of an S462 entry: canonical JSON (sorted keys, no spaces, UTF-8) of every field but entry_sha256."""
    from experiments.runner.ollama_client import canonical_sha256
    return canonical_sha256({k: v for k, v in e.items() if k != "entry_sha256"})


def manifest_sums(path: Path) -> dict:
    """{file name: sha256} of a MANIFEST.sha256 in shasum's format ("<64 hex>  <name>")."""
    out = {}
    for ln in path.read_text().splitlines():
        if ln.strip():
            h, _, name = ln.partition("  ")
            out[name.strip()] = h.strip()
    return out


def digest_matches(lock_digest: str, digest: str | None) -> bool:
    """D91's rule: at least 12 lowercase hex characters, a prefix of the lock's digest, exact at 64."""
    d = digest or ""
    return len(d) >= 12 and all(c in "0123456789abcdef" for c in d) and lock_digest.startswith(d)


def load_reference_claims(path: Path, pinned: str | None, lock_sha256: str, model: str, lock_digest: str) -> dict:
    """The S462 file, checked (REFERENCE CLAIMS in the docstring): {"path", "file_sha256", "entries": {qid: entry}}.
    Raises ValueError with the reason."""
    path = Path(path)
    if not pinned:
        raise ValueError("--reference-claims needs --reference-claims-sha256 (the sha256 its MANIFEST.sha256 gives)")
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise ValueError(f"cannot read {path}: {e}") from None
    got = hashlib.sha256(raw).hexdigest()
    if got != pinned:
        raise ValueError(f"{path} has sha256 {got[:12]}, not the {pinned[:12]} given")
    man = path.parent / CLAIMS_MANIFEST
    try:
        listed = manifest_sums(man).get(path.name)
    except OSError:
        listed = None
    if listed != got:
        raise ValueError(f"{man} does not list {path.name} with sha256 {got[:12]} (it lists {str(listed)[:12]})")
    entries = {}
    for n, ln in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        e = json.loads(ln)
        q = e.get("question_id")
        if e.get("entry_sha256") != entry_sha256(e):
            raise ValueError(f"{path} line {n} ({q}): entry_sha256 does not recompute (the entry was changed)")
        if q in entries:
            raise ValueError(f"{path} line {n}: a second entry for {q}")
        if e.get("lock_sha256") != lock_sha256:
            raise ValueError(f"{path} line {n} ({q}): cut under lock {str(e.get('lock_sha256'))[:12]}, this run is "
                             f"under {lock_sha256[:12]}")
        if e.get("status") == "ok" and (e.get("model") != model or not digest_matches(lock_digest, e.get("model_digest"))):
            raise ValueError(f"{path} line {n} ({q}): cut by {e.get('model')} {str(e.get('model_digest'))[:12]}, "
                             f"the lock's scorer is {model} {lock_digest[:12]}")
        entries[q] = e
    return {"path": str(path), "file_sha256": got, "entries": entries}


def needs_ragchecker(x: dict, ref: str) -> bool:
    """The answer reaches RAGChecker in score_run (not Rule 8, an answer, passages recorded, a reference)."""
    from experiments.scorers import records as R
    return (x["group"] in R.APPLIES["ragchecker"] and x["status"] == "ok" and x["passages_kind"] != "not_recorded"
            and bool(ref.strip()))


def check_claims_for(items: list, refs: dict, rc: dict) -> None:
    """Every answer that reaches RAGChecker has an ok entry cut from its own question and reference, or ValueError."""
    for x in items:
        ref = refs.get(x["question_id"], "")
        if not needs_ragchecker(x, ref):
            continue
        e = rc["entries"].get(x["question_id"])
        where = f"{x['question_id']} ({x['config']}, d{x['draw']})"
        if e is None:
            raise ValueError(f"{where}: no entry in the reference claims {rc['path']}")
        if e.get("status") != "ok":
            raise ValueError(f"{where}: its entry has status {e.get('status')!r}, not ok")
        if e.get("reference_sha256") != text_sha256(ref):
            raise ValueError(f"{where}: the entry was cut from another reference (sha256 {e['reference_sha256'][:12]}, "
                             f"this reference {text_sha256(ref)[:12]})")
        if e.get("question_sha256") != text_sha256(x["question"]):
            raise ValueError(f"{where}: the entry was cut with another question text (sha256 "
                             f"{e['question_sha256'][:12]}, this answer's {text_sha256(x['question'])[:12]})")


LENGTH_STOP = "model call length:"   # the error of a call that reached num_predict (status and stop_reason "length")


def length_twice(prior: list) -> set:
    """D110 (Q25): the idents (records.py's (run_id, config, question_id, draw)) whose latest two rows are both failed by
    a length stop. One such stop is retried, since the same answer's extraction has ended normally on another try (21
    October, rlm_10 OOD_046 d1); a second shows the loop repeats, and a 16,384-token reply is never a usable one."""
    hist: dict = {}
    for d in prior:
        hist.setdefault((d["run_id"], d["config"], d["question_id"], d["draw"]), []).append(d)
    return {k for k, rows in hist.items() if len(rows) >= 2 and all(
        r.get("status") == "failed" and LENGTH_STOP in str(r.get("error")) for r in rows[-2:])}


def claims_resume(prior: list, done: set, rc: dict) -> tuple[set, int]:
    """(done, rows accepted by equal claims) under the reference claims (REFERENCE CLAIMS, resume), or ValueError for a
    prior scored row cut differently. The ident is records.py's (run_id, config, question_id, draw); the latest row of
    an answer counts, as in records.resume."""
    latest = {}
    for d in prior:
        latest[(d["run_id"], d["config"], d["question_id"], d["draw"])] = d
    accepted = 0
    for k in done:
        row = latest.get(k)
        if row is None or row.get("status") not in SCORED:
            continue
        e = rc["entries"].get(row["question_id"])
        if e is None:
            raise ValueError(f"a prior row of {row['question_id']} ({row['config']}) was scored, and the reference "
                             f"claims have no entry for its question")
        tag = row.get("reference_claims")
        if tag is not None:
            if tag.get("entry_sha256") != e["entry_sha256"]:
                raise ValueError(f"a prior row of {row['question_id']} ({row['config']}) was scored with another "
                                 f"reference claims entry ({str(tag.get('entry_sha256'))[:12]}, now "
                                 f"{e['entry_sha256'][:12]}); archive the output first (S462 archive)")
        elif row.get("gt_answer_claims") == e["claims"]:
            accepted += 1
        else:
            raise ValueError(f"a prior row of {row['question_id']} ({row['config']}) was scored against "
                             f"{len(row.get('gt_answer_claims') or [])} reference claims cut for that answer, not the "
                             f"{len(e['claims'])} of the reference claims file; archive the worker's ragchecker output "
                             f"first (scripts/S462_k1_reference_claims.py archive; D92 Q190: those rows are scored again)")
    return done, accepted


def claims_tag(rc: dict, e: dict) -> dict:
    """What a row records about the reference claims it was scored against."""
    return {"file_sha256": rc["file_sha256"], "entry_sha256": e["entry_sha256"], "request_sha256": e["request_sha256"],
            "reply_sha256": e["reply_sha256"], "cut_machine": e["cut_machine"], "n_claims": e["n_claims"]}


def reference_claims_arg(a, lock, model: str, digest: str) -> dict | None:
    """--reference-claims, loaded and checked (load_reference_claims), or None without it; SystemExit on a refusal."""
    p = getattr(a, "reference_claims", None)
    if p is None:
        return None
    try:
        return load_reference_claims(p, getattr(a, "reference_claims_sha256", None), lock.sha256, model, digest)
    except ValueError as e:
        raise SystemExit(f"REFUSED: reference claims: {e}") from None


STOP_EXIT = 5                    # D89 K1 O2: stopped between answers on request (--stop-file)


def stop_requested(a) -> bool:
    """--stop-file names a file that exists: stop before the next answer (D89, K1 O2)."""
    f = getattr(a, "stop_file", None)
    return f is not None and Path(f).exists()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:11434")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--arm", type=Path)
    src.add_argument("--run", type=Path, nargs="+", help="a run's sink or results file, read by "
                     "experiments/scorers/records.py (F5); scored as RUN MODE in the docstring says. K1: the six runs "
                     "the --assignment names, in one process")
    ap.add_argument("--store", type=Path, help="--run: the Chroma directory to resolve passage ids against "
                    "(default: the store the run recorded)")
    ap.add_argument("--gt", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--rows", help="START:END (0-based, END excluded) of the arm's answers in its fixed order, so two "
                    "machines can split one job; the selection is written into the header")
    ap.add_argument("--order", choices=ORDERS, default="claims", help="the order checking prompts are sent in (ORDER "
                    "in the docstring): claims, RefChecker's own (default), or passage, grouped by passage")
    ap.add_argument("--assignment", type=Path, help="--run, K1 (D83, Q142): the assignment file of "
                    "scripts/S451_k1_assign.py; only --machine's answers are scored, question by question")
    ap.add_argument("--machine", help="--assignment: the machine this process scores for, written in every record")
    ap.add_argument("--stage", type=int, choices=[1, 2], help="--assignment, K1 (D86): score only this stage's "
                    "questions of a staged assignment")
    ap.add_argument("--worker", help="--assignment, K1 helpers: the worker this process scores for (with --amendments "
                    "and --amendments-head), written in every record")
    ap.add_argument("--amendments", type=Path, help="--worker: K1's amendment chain (findings/recompute/K1/amendments.json)")
    ap.add_argument("--amendments-head", help="--worker: the chain head the launcher pinned")
    ap.add_argument("--stop-on-failed", action="store_true", help="--run: stop (exit 4) after the first answer "
                    "recorded as failed (a model call that did not end with 'stop')")
    ap.add_argument("--dry-run", action="store_true", help="--run: read, select and check the resume, print the work "
                    "list; no model call, nothing written")
    ap.add_argument("--stop-file", type=Path, help="--run (D89, K1 O2): before each answer, exit 5 if this file exists "
                    "(a stop between answers; the launcher treats it as clean)")
    ap.add_argument("--reference-claims", type=Path, help="--run (D92, Q190): the reference claims of "
                    "scripts/S462_k1_reference_claims.py, passed in for every answer of each question (REFERENCE CLAIMS "
                    "in the docstring)")
    ap.add_argument("--reference-claims-sha256", help="--reference-claims: the file's sha256, as its MANIFEST.sha256 "
                    "gives it")
    ap.add_argument("--claims-per-call", type=int, help="D103: claims per checking call (JOINT in the docstring); "
                    "default the lock's [scorers] ragchecker_claims_per_call; another value only with --joint-test")
    ap.add_argument("--joint-test", action="store_true", help="D103: allow --claims-per-call other than the lock's, "
                    "for the sample test only (scripts/S466_k1_joint_test.py), until Valerio decides")
    a = ap.parse_args()
    require_hash_seed()                                  # D83 (Q144), before anything is read, loaded or written
    k1_args(a)
    per_call = claims_per_call(a, load())                # D103, before anything is read or written
    if a.dry_run:
        return dry_run(a)

    from ragchecker import RAGChecker, RAGResults
    from ragchecker.metrics import all_metrics

    lock = load()
    model = lock.d["scorers"]["model"]
    call = lock.ollama(model, role="scorer")
    joint = False                                        # RefChecker's own joint check: never (D103, make_evaluator)
    a.out.mkdir(parents=True, exist_ok=True)
    out, calls_log = a.out / "ragchecker.jsonl", a.out / "ragchecker_calls.jsonl"
    current = {"key": None, "n": 0, "checks": 0, "ambiguous": 0, "batch": 0}
    llm = make_llm(a.base, call, a.order, calls_log, current, per_call)

    evaluator = make_evaluator(RAGChecker, model, a.order, joint, llm)
    refs = {q["id"]: q.get("expected_answer", "") for q in json.loads(a.gt.read_text())["questions"]}
    if a.run is not None:
        return score_run(a, evaluator, current, lock, model, call, joint, out, refs, per_call)
    rows = json.loads(a.arm.read_text())["per_question_results"]
    latest = {}
    if out.exists():
        for d in map(json.loads, out.read_text().splitlines()):
            latest[(d["config"], d["question_id"])] = d["status"]
    done = {k for k, v in latest.items() if v in DONE}
    if a.rows:
        start, end = (int(x) if x else None for x in a.rows.split(":"))
        rows = rows[start:end]
    todo = [r for r in rows if (r["config"], r["question_id"]) not in done][: a.limit]
    header = {"_provenance": {"script": "experiments/scorers/ragchecker_run.py", "inputs": [str(a.arm), str(a.gt)],
                              "started": time.strftime("%Y-%m-%dT%H:%M:%S")},
              "ragchecker": "0.1.9", "model": model, "model_digest": call.digest, "lock_sha256": lock.sha256,
              "options": call.options, "fields": call.fields, "joint_check": joint, "base": a.base,
              "row_range": a.rows, "order": a.order, "batch_size_checker": batch_size_checker(a.order),
              **hash_seed_state(), "rows": len(rows), "already_done": len(done), "to_do": len(todo)}
    if per_call > 1:                                     # D103: the guarded joint check
        header.update(claims_per_call=per_call, guarded_joint=True, joint_test=bool(a.joint_test))
    with (a.out / "ragchecker_headers.jsonl").open("a") as fh:
        fh.write(json.dumps(header) + "\n")
    print(f"ragchecker 0.1.9: {len(rows)} rows, {len(done)} done, {len(todo)} to score with {model}", flush=True)

    for r in todo:
        key = f"{r['config']}|{r['question_id']}"
        current.update(key=key, n=0, checks=0, ambiguous=0, batch=0)
        if per_call > 1:
            current.update(modes=[], joint_calls=0, joint_rejected=0)
        ctx = [{"doc_id": f"{c.get('source')}#{c.get('chunk_idx')}", "text": c["text"]} for c in r.get("contexts") or []]
        ref = refs.get(r["question_id"], "")
        gen = r.get("generation") or {}
        t0 = time.time()
        row = {"question_id": r["question_id"], "config": r["config"], "n_contexts": len(ctx),
               "context_chars": sum(len(c["text"]) for c in ctx), "lock_sha256": lock.sha256, "metrics": None}
        if not gen.get("answer") or gen.get("error"):
            row.update(status="no_answer", error=gen.get("error") or "no answer stored")
        elif not ref.strip():
            row.update(status="unscorable", error="no reference answer for this question")
        else:
            res = RAGResults.from_dict({"results": [{"query_id": key, "query": r["question"], "gt_answer": ref,
                                                     "response": gen["answer"], "retrieved_context": ctx}]})
            try:
                evaluator.evaluate(res, all_metrics)
                x = res.results[0]
                row.update(response_claims=x.response_claims, gt_answer_claims=x.gt_answer_claims,
                           answer2response=x.answer2response, response2answer=x.response2answer,
                           retrieved2response=x.retrieved2response, retrieved2answer=x.retrieved2answer, error=None)
                missing = [n for n, c in (("response", x.response_claims), ("reference", x.gt_answer_claims)) if not c]
                if missing:
                    row.update(status="unscorable", metrics_as_computed=x.metrics,
                               error="no claims extracted from the " + " and the ".join(missing))
                else:
                    row.update(status="ok" if current["ambiguous"] == 0 else "ok_ambiguous_labels", metrics=x.metrics)
            except Exception as e:                               # noqa: BLE001 - recorded, never scored
                row.update(status="failed", error=f"{type(e).__name__}: {e}")
        row.update(calls=current["n"], checking_calls=current["checks"], ambiguous_labels=current["ambiguous"],
                   wall_s=round(time.time() - t0, 1), at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        if per_call > 1:
            row.update(joint_summary(current, per_call))
        with out.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['at']} {r['config']:13s} {r['question_id']:28s} {row['status']} {row['calls']} calls "
              f"{row['wall_s']} s", flush=True)
    print("RAGCHECKER DONE", flush=True)
    return 0


def work_list(a, lock, refs: dict, out: Path, rc: dict | None) -> tuple:
    """(items, assignment or None, done idents, to do, rows accepted by equal claims): the answers read and selected,
    the resume, and with reference claims (D92 Q190) their checks and claims_resume; SystemExit on a refusal."""
    from experiments.scorers import records as R
    accepted = 0
    try:
        items, asg = read_items(a)
        for x in items:
            x["item_sha256"] = R.item_sha256(x, refs.get(x["question_id"], ""))
        prior = [json.loads(ln) for ln in out.read_text().splitlines() if ln.strip()] if out.exists() else []
        done = R.resume(prior, lock.sha256, DONE | {"not_applicable"}, {R.ident(x): x["item_sha256"] for x in items})
        if rc is not None:
            check_claims_for(items, refs, rc)
            done, accepted = claims_resume(prior, done, rc)
        twice = length_twice(prior) & {R.ident(x) for x in items}
        if twice:
            print(f"D110: {len(twice)} answer(s) failed twice by a length stop, counted as done (failed rows kept): "
                  + ", ".join("|".join(map(str, k[1:])) for k in sorted(twice, key=str)), file=sys.stderr, flush=True)
        done = done | twice
    except (R.RecordsError, ValueError) as e:
        raise SystemExit(f"REFUSED: {e}") from None
    todo = [x for x in items if R.ident(x) not in done][: a.limit]
    return items, asg, done, todo, accepted


def score_run(a, evaluator, current, lock, model, call, joint, out, refs, per_call: int = 1) -> int:
    """RUN MODE (F5, F39, F55; the docstring): the answers of one run, read by experiments/scorers/records.py."""
    from ragchecker import RAGResults
    from ragchecker.metrics import all_metrics
    from experiments.scorers import records as R
    from experiments.scorers import assignment as A

    rc = reference_claims_arg(a, lock, model, call.digest)          # D92 Q190: before anything is read or written
    items, asg, done, todo, accepted = work_list(a, lock, refs, out, rc)
    header = {"_provenance": {"script": "experiments/scorers/ragchecker_run.py --run",
                              "inputs": [*map(str, run_paths(a)), str(a.gt)],
                              "started": time.strftime("%Y-%m-%dT%H:%M:%S")},
              "ragchecker": "0.1.9", "model": model, "model_digest": call.digest, "lock_sha256": lock.sha256,
              "options": call.options, "fields": call.fields, "joint_check": joint, "base": a.base,
              "gt_sha256": hashlib.sha256(a.gt.read_bytes()).hexdigest(), "store": str(a.store) if a.store else None,
              "runs": sorted({x["run_id"] for x in items}),
              "indexes": sorted({json.dumps(x["index"], sort_keys=True) for x in items if x["index"]}),
              "row_range": a.rows, "order": a.order, "batch_size_checker": batch_size_checker(a.order),
              **hash_seed_state(), "rows": len(items), "already_done": len(done), "to_do": len(todo)}
    if rc is not None:                                   # D92 Q190: the reference claims every answer is scored against
        header["reference_claims"] = {"path": rc["path"], "file_sha256": rc["file_sha256"],
                                      "entries": len(rc["entries"]), "accepted_by_equal_claims": accepted}
    if per_call > 1:                                     # D103: the guarded joint check
        header.update(claims_per_call=per_call, guarded_joint=True, joint_test=bool(getattr(a, "joint_test", False)))
    if asg is not None:                                  # K1 (D83, Q142): the assignment and the machine
        header.update(A.stamp(asg, a.machine, a.assignment, getattr(a, "stage", None), worker=getattr(a, "worker", None)),
                      stop_on_failed=a.stop_on_failed)
    with (a.out / "ragchecker_headers.jsonl").open("a") as fh:
        fh.write(json.dumps(header) + "\n")
    print(f"ragchecker 0.1.9 --run: {len(items)} answers, {len(done)} done, {len(todo)} to score with {model}", flush=True)

    scored = 0
    for x in todo:
        if stop_requested(a):                            # D89 K1 O2: between answers, never inside one
            print(f"RAGCHECKER STOPPED BETWEEN ANSWERS: {a.stop_file} exists; {scored} answers scored in this session, "
                  f"{len(todo) - scored} left (the next session resumes)", flush=True)
            return STOP_EXIT
        scored += 1
        key = f"{x['run_id']}|{x['answer_key']}"
        current.update(key=key, n=0, checks=0, ambiguous=0, batch=0, extracts=0, machine=getattr(a, "machine", None),
                       k1_stage=x.get("k1_stage"), worker=getattr(a, "worker", None))
        if per_call > 1:
            current.update(modes=[], joint_calls=0, joint_rejected=0)
        ctx = [{"doc_id": f"{p['source']}#{p['chunk_idx']}", "text": p["text"]} for p in x["passages"] or []]
        ref = refs.get(x["question_id"], "")
        t0 = time.time()
        row = {"run_id": x["run_id"], "answer_key": x["answer_key"], "question_id": x["question_id"],
               "config": x["config"], "draw": x["draw"], "group": x["group"], "passages_kind": x["passages_kind"],
               "n_contexts": len(ctx), "context_chars": sum(len(c["text"]) for c in ctx),
               "item_sha256": x["item_sha256"], "lock_sha256": lock.sha256, "metrics": None}
        if getattr(a, "machine", None):                  # K1 (D83, Q142): the machine in every record
            row["machine"] = a.machine
        if x.get("k1_stage"):                            # K1 (D86): the question's stage in every record
            row["k1_stage"] = x["k1_stage"]
        if getattr(a, "worker", None):                   # K1 helpers: the worker in every record
            row["worker"] = a.worker
        if x["group"] not in R.APPLIES["ragchecker"]:
            # Rule 8 (LIST.md:337; F39): RAGChecker does not apply to a not-answerable question; null, never a number
            row.update(status="not_applicable", reason=R.NOT_APPLICABLE, error=None)
        elif x["status"] != "ok":
            row.update(status="no_answer", error=x["error"] or "no answer stored")
        elif x["passages_kind"] == "not_recorded":
            row.update(status="unscorable", error="the run's record lists no passages for this answer")
        elif not ref.strip():
            row.update(status="unscorable", error="no reference answer for this question")
        else:
            given = {}
            if rc is not None:                           # D92 Q190: the question's claims, cut once on the Studio
                e = rc["entries"][x["question_id"]]
                given = {"gt_answer_claims": [list(c) for c in e["claims"]]}
                row["reference_claims"] = claims_tag(rc, e)
            res = RAGResults.from_dict({"results": [{"query_id": key, "query": x["question"], "gt_answer": ref,
                                                     "response": x["answer"], "retrieved_context": ctx, **given}]})
            try:
                evaluator.evaluate(res, all_metrics)
                y = res.results[0]
                row.update(response_claims=y.response_claims, gt_answer_claims=y.gt_answer_claims,
                           answer2response=y.answer2response, response2answer=y.response2answer,
                           retrieved2response=y.retrieved2response, retrieved2answer=y.retrieved2answer, error=None)
                missing = [n for n, c in (("response", y.response_claims), ("reference", y.gt_answer_claims)) if not c]
                if rc is not None:
                    row["extract_calls"] = current.get("extracts", 0)
                if rc is not None and (y.gt_answer_claims != given["gt_answer_claims"] or row["extract_calls"] != 1):
                    row.update(status="failed", metrics_as_computed=y.metrics,
                               error=f"the reference claims were not used as passed (claims "
                                     f"{'equal' if y.gt_answer_claims == given['gt_answer_claims'] else 'changed'}, "
                                     f"{row['extract_calls']} extraction calls, 1 expected: the response's)")
                elif missing:
                    row.update(status="unscorable", metrics_as_computed=y.metrics,
                               error="no claims extracted from the " + " and the ".join(missing))
                else:
                    row.update(status="ok" if current["ambiguous"] == 0 else "ok_ambiguous_labels", metrics=y.metrics)
            except Exception as e:                               # noqa: BLE001 - recorded, never scored
                row.update(status="failed", error=f"{type(e).__name__}: {e}")
        row.update(calls=current["n"], checking_calls=current["checks"], ambiguous_labels=current["ambiguous"],
                   wall_s=round(time.time() - t0, 1), at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        if per_call > 1:
            row.update(joint_summary(current, per_call))
        with out.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['at']} {x['config']:13s} {x['question_id']:28s} d{x['draw']} {row['status']} {row['calls']} calls "
              f"{row['wall_s']} s", flush=True)
        if row["status"] == "failed" and getattr(a, "stop_on_failed", False):
            print(f"RAGCHECKER STOPPED: {key} failed ({row['error']}); --stop-on-failed", flush=True)
            return 4
    print("RAGCHECKER DONE", flush=True)
    return 0


def run_paths(a) -> list:
    """--run as a list (one path or several; a caller may pass one Path)."""
    return list(a.run) if isinstance(a.run, (list, tuple)) else [a.run]


def k1_args(a) -> None:
    """The K1 options (D83, Q142), checked before anything is read: --assignment and --machine together and only with
    --run; --rows only with one --run and no --assignment; --dry-run and --stop-on-failed only with --run."""
    if (a.assignment is None) != (a.machine is None):
        raise SystemExit("REFUSED: --assignment and --machine go together")
    if getattr(a, "stage", None) is not None and a.assignment is None:
        raise SystemExit("REFUSED: --stage selects from a staged --assignment")
    if a.run is None and (a.assignment or a.dry_run or a.stop_on_failed or getattr(a, "stop_file", None)):
        raise SystemExit("REFUSED: --assignment, --dry-run, --stop-on-failed and --stop-file are --run options")
    if a.run is not None and a.rows and (len(a.run) > 1 or a.assignment):
        raise SystemExit("REFUSED: --rows selects from one run's answers; with several runs or an --assignment use "
                         "the assignment")
    k = [getattr(a, n, None) is None for n in ("worker", "amendments", "amendments_head")]
    if any(k) and not all(k):
        raise SystemExit("REFUSED: --worker, --amendments and --amendments-head go together")
    if getattr(a, "worker", None) is not None and a.assignment is None:
        raise SystemExit("REFUSED: --worker selects from an --assignment and its --amendments")
    if (getattr(a, "reference_claims", None) is None) != (getattr(a, "reference_claims_sha256", None) is None):
        raise SystemExit("REFUSED: --reference-claims and --reference-claims-sha256 go together (D92 Q190)")
    if getattr(a, "reference_claims", None) is not None and a.run is None:
        raise SystemExit("REFUSED: --reference-claims is a --run option")


def read_items(a) -> tuple:
    """(answers to score in their order, the assignment or None). Every --run read by records.py; with --assignment,
    assignment.select() keeps --machine's answers question by question; else --rows of the one run."""
    from experiments.scorers import records as R
    from experiments.scorers import assignment as A
    items = []
    for p in run_paths(a):
        items += R.read_run(p, store=a.store)
    asg = None
    if getattr(a, "assignment", None):
        try:
            if getattr(a, "worker", None):              # K1 helpers: the worker's answers under the chain
                asg = A.for_worker(a.assignment, a.amendments, a.worker, a.machine, a.amendments_head)
                items = A.select(items, asg, a.worker, stage=getattr(a, "stage", None))
            else:
                asg = A.load(a.assignment)
                items = A.select(items, asg, a.machine, stage=getattr(a, "stage", None))
        except (A.AssignmentError, OSError) as e:
            raise R.RecordsError(f"assignment: {e}") from None
    elif a.rows:
        start, end = (int(x) if x else None for x in a.rows.split(":"))
        items = items[start:end]
    return items, asg


def dry_run(a) -> int:
    """--dry-run: what this process would score, in order, and what a resume would skip; no model call, no write."""
    from experiments.scorers import assignment as A
    lock = load()
    refs = {q["id"]: q.get("expected_answer", "") for q in json.loads(a.gt.read_text())["questions"]}
    out = a.out / "ragchecker.jsonl"
    model = lock.d["scorers"]["model"]
    rc = reference_claims_arg(a, lock, model, lock.ollama(model, role="scorer").digest)     # D92 Q190
    items, asg, done, todo, accepted = work_list(a, lock, refs, out, rc)
    from collections import Counter
    print(json.dumps({"dry_run": True, "lock_sha256": lock.sha256, "order": a.order, **hash_seed_state(),
                      "runs": [str(p) for p in run_paths(a)], "out": str(a.out),
                      **(A.stamp(asg, a.machine, a.assignment, getattr(a, "stage", None),
                                 worker=getattr(a, "worker", None)) if asg else {}),
                      "answers": len(items), "already_done": len(done), "to_do": len(todo),
                      "status": dict(Counter(x["status"] for x in todo)),
                      "passages_kind": dict(Counter(x["passages_kind"] for x in todo)),
                      "no_reference": sum(not refs.get(x["question_id"], "").strip() for x in todo),
                      **({"reference_claims": {"path": rc["path"], "file_sha256": rc["file_sha256"],
                                               "entries": len(rc["entries"]), "accepted_by_equal_claims": accepted}}
                         if rc is not None else {})}, indent=1))
    for x in todo[:12]:
        print(f"  {x['question_id']:28s} {x['config']:13s} d{x['draw']} {x['status']:9s} {len(x['passages'] or []):4d} passages")
    if len(todo) > 12:
        print(f"  ... {len(todo) - 12} more")
    print("RAGCHECKER DRY RUN: no model call, nothing written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
