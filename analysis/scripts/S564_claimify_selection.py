#!/usr/bin/env python3
"""S564 - Claimify's Selection stage on the sentences MiniCheck scores for Papers (D208).

WHY. D208 (Valerio, 2 November, O3): Papers is MiniCheck's supported sentences over its sentences, and the deposited
splitter (decompose_to_sentences) turns headings and lead-in lines into "claims". D172 A5-Q1 and Am10 take headings out
of the count, and D202 rejected choosing a heading rule by guess. D208 replaces the hand rule with the literature's
method: Claimify's Selection stage (Metropolitansky and Larson 2025, "Towards Effective Extraction and Evaluation of
Factual Claims", arXiv 2502.10855v2, section 3.2; prompts in Appendix N.1.1; hyperparameters in Appendix D) asks an LLM
whether each sentence holds at least one specific and verifiable proposition. HEADING_RULE is no_heading since D245; S560 and S563
stay as the comparison and the range.

WHAT IS SENT, AS CLAIMIFY DOES IT.
  system   SYSTEM_PROMPT below: Appendix N.1.1's "Selection System Prompt", word for word. The arXiv HTML prints it as a
           listing wrapped at the page width; the wraps are joined (four places: "e.g., a / dataset", "expand on this
           point / (e.g.,", "->" / "John is the CEO", "lead the following / sentence(s)"), LaTeX's "20\\%" is "20%", and
           the typographic quotes around the two verdict strings in the output format are straight quotes.
  user     USER_TEMPLATE below: Appendix N.1.1's "Selection User Prompt": Question, Excerpt, Sentence.
  excerpt  Section 3.1: the sentence's p preceding and f following sentences; Appendix D sets p = 5 and f = 5 for
           Selection (max_preceding_sentences, max_following_sentences). The system prompt says "[...]" means the reader
           does not see every sentence; it is put before the first sentence shown when earlier sentences are left out,
           and after the last when later ones are. Sentences are joined by one space. No metadata (footnote 5: "We did
           not use any metadata for the experiments described in this paper").
  question The question of the D5 key (S470.the_key(), the key the L1 answers were scored on), by question id.
  sentence The sentences are MiniCheck's own split, not Claimify's NLTK split (section 3.1), since D208 filters the
           sentences MiniCheck scored. L1: S560's census.jsonl (sha256 pinned below; made by tracked_decompose, which
           S560 checked against the deposited function and the stored per_claim on every used row), each answer's
           claims in claim_index order, complete from 0 to claims_in_answer - 1. Figure 2's 49: the deposited
           decompose_to_sentences (S384.deposited_code, sha256 pinned there) on S498's answers (S498.build_answers);
           each answer's sha256 must equal S498's row, its sentence count S498's n_claims, and each sentence cut at 300
           characters S498's stored claim (per_claim, or per_claim_on_cut_input for a row S498 stored as null; E029,
           stored null "over the encoder's 2048-token limit" with neither, is checked on its count only, and its
           Papers stays null whatever Selection says).
           MiniCheck's outcomes (supported, probability) are never read into a unit: only the claim text is kept.

WHERE THIS DEPARTS FROM CLAIMIFY, AND WHY. Appendix D: completions = 3 at temperature 0.2, min_successes = 2,
max_retries = 2. LOCK.toml binds every call (D53): the scorer devstral-small-2:24b ([scorers] model) at the instrument
settings ([judge]: temperature 0, think off, seed none, num_predict 16384), sent by experiments/runner/ollama_client.chat
with lock.ollama(model, role="scorer"), so one completion per sentence (Claimify's own temperature for one completion is
0, Appendix D). An output that does not parse is recorded as "unparseable" and not retried: at temperature 0 a retry
repeats it. Claimify's system prompt replaces devstral's built-in one (chat: a caller's system message replaces the
template's); the record keeps the system prompt sent.

THE OUTCOME. Parsed from the "Final submission:" and "Sentence with only verifiable information:" fields:
  none   "Does NOT contain a specific and verifiable proposition" (Claimify: labelled "No verifiable claims")
  all    "Contains ..." and "remains unchanged"
  some   "Contains ..." and a rewritten sentence (stored in rewritten, not used)
  contains  "Contains ..." with no "Sentence with only verifiable information:" line (Valerio, O-a, 2 Nov). devstral
         wrote 4 of the 100 timed this way, as "<insert 'Contains a specific and verifiable proposition'>". It stays in
         Papers, as all and some do. A verdict naming both options (the template copied) does not parse.
For Papers a sentence leaves the count only on "none". A "some" sentence stays in as written: MiniCheck scored the
original sentence, and rescoring the rewritten one would change the instrument. THIS IS CLAUDE'S CHOICE, FOR VALERIO TO
CONFIRM (D208): the other reading would score the rewritten sentences with MiniCheck again.

THE ROUTINE (experiments/runner/job.py through judge_passages.start, as S508): the server named by the lane number in the
environment (S564_LANE = n, the server 11450 + n, its log ~/ollama_logs/serve_<port>.log; the port is never on a command
line), a fresh load of the lock's judge model with the server checks (version, binary, KV cache, flash attention,
parallel 1), the after-first-call check, then the units in order. The scorer call must equal the judge call the load
checked (model, digest, options, fields) or the run refuses. Every call record goes to calls.jsonl (LOCK.toml [record]
fields, lock_sha256 among them); one row per sentence to rows.jsonl, fsynced. Resumable: a sentence whose latest row is
ok or unparseable under this run_sha256 is skipped; a row under another run_sha256 refuses the run (one folder, one
definition). One writer per folder (judge_passages.hold_writer).

SETS. timing: TIMING_N sentences of the L1 census, drawn with random.Random(TIMING_SEED): half from S560's candidate
stratum (a sentence any of S560.CANDIDATES fires on), half from the rest, each sorted by sentence id before the draw.
l1: the 13,740 L1 sentences. h49: the 1,069 sentences of Figure 2's 49. full: l1 then h49.
SHARDS. --shard k/n keeps the units whose place in the set is k modulo n, in its own folder (default
<out>/<set>/shard_k_of_n), so several servers can share a set. run_sha256 is the whole set's, so every shard of a set
carries the same one and their rows join by sentence_id. A launcher can walk the shards as a queue: a shard another
process writes exits 75 (WRITER BUSY), a finished one exits 0 at once.

    uv run --frozen python scripts/S564_claimify_selection.py --selftest
    uv run --frozen python scripts/S564_claimify_selection.py --set timing --dry-run
    S564_LANE=<n> uv run --frozen python scripts/S564_claimify_selection.py --set timing --machine macos \\
        --binary /opt/homebrew/bin/ollama --out findings/recompute/S564_claimify_selection/timing_100

Writes into --out: headers.jsonl, fresh_load_*.json, calls.jsonl, rows.jsonl and summary.json (counts by outcome and
status, seconds per call median and p90, tokens, busy servers, the ETA for ETA_SENTENCES on one server, provenance).
Model calls on answers only; no human rating is read, so the folder is committable. Exit 0 when every unit of the set
has a parsed row, 1 otherwise, 75 when another process writes the folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

SCRIPT = "scripts/S564_claimify_selection.py"
CENSUS = ROOT / "findings/recompute/heading_rule_eval/census.jsonl"
CENSUS_SHA256 = "217233221b07f2f09b0a29bbc3d4e068dcafa014400faf36e5e4c48efcc8b105"   # S560 evaluation.json input_sha256
S498_ROWS = ROOT / "findings/recompute/S498_human49_minicheck_papers.jsonl"
OUT = ROOT / "findings/recompute/S564_claimify_selection"
N_L1, N_H49 = 13740, 1069
ETA_SENTENCES = N_L1 + N_H49
P_PRECEDING, F_FOLLOWING = 5, 5             # Appendix D, Selection
STORED_CLAIM_CHARS = 300                    # S19.check stores claims[i][:300]
TIMING_N, TIMING_SEED = 100, 564
OMITTED = "[...]"
CONTAINS = "contains a specific and verifiable proposition"
NOT_CONTAINS = "does not contain a specific and verifiable proposition"
DONE = {"ok", "unparseable"}
LANE_BASE = 11450

SYSTEM_PROMPT = """You are an assistant to a fact-checker. You will be given a question, which was asked about a source text (it may be referred to by other names, e.g., a dataset). You will also be given an excerpt from a response to the question. If it contains "[...]", this means that you are NOT seeing all sentences in the response. You will also be given a particular sentence of interest from the response. Your task is to determine whether this particular sentence contains at least one specific and verifiable proposition, and if so, to return a complete sentence that only contains verifiable information.

Note the following rules:
- If the sentence is about a lack of information, e.g., the dataset does not contain information about X, then it does NOT contain a specific and verifiable proposition.
- It does NOT matter whether the proposition is true or false.
- It does NOT matter whether the proposition is relevant to the question.
- It does NOT matter whether the proposition contains ambiguous terms, e.g., a pronoun without a clear antecedent. Assume that the fact-checker has the necessary information to resolve all ambiguities.
- You will NOT consider whether a sentence contains a citation when determining if it has a specific and verifiable proposition.

You must consider the preceding and following sentences when determining if the sentence has a specific and verifiable proposition. For example:
- if preceding sentence = "Who is the CEO of Company X?" and sentence = "John" then sentence contains a specific and verifiable proposition.
- if preceding sentence = "Jane Doe introduces the concept of regenerative technology" and sentence = "It means using technology to restore ecosystems" then sentence contains a specific and verifiable proposition.
- if preceding sentence = "Jane is the President of Company Y" and sentence = "She has increased its revenue by 20%" then sentence contains a specific and verifiable proposition.
- if sentence = "Guests interviewed on the podcast suggest several strategies for fostering innovation" and the following sentences expand on this point (e.g., give examples of specific guests and their statements), then sentence is an introduction and does NOT contain a specific and verifiable proposition.
- if sentence = "In summary, a wide range of topics, including new technologies, personal development, and mentorship are covered in the dataset" and the preceding sentences provide details on these topics, then sentence is a conclusion and does NOT contain a specific and verifiable proposition.

Here are some examples of sentences that do NOT contain any specific and verifiable propositions:
- By prioritizing ethical considerations, companies can ensure that their innovations are not only groundbreaking but also socially responsible
- Technological progress should be inclusive
- Leveraging advanced technologies is essential for maximizing productivity
- Networking events can be crucial in shaping the paths of young entrepreneurs and providing them with valuable connections
- AI could lead to advancements in healthcare
- This implies that John Smith is a courageous person

Here are some examples of sentences that likely contain a specific and verifiable proposition and how they can be rewritten to only include verifiable information:
- The partnership between Company X and Company Y illustrates the power of innovation -> "There is a partnership between Company X and Company Y"
- Jane Doe’s approach of embracing adaptability and prioritizing customer feedback can be valuable advice for new executives -> "Jane Doe’s approach includes embracing adaptability and prioritizing customer feedback"
- Smith’s advocacy for renewable energy is crucial in addressing these challenges -> "Smith advocates for renewable energy"
- **John Smith**: instrumental in numerous renewable energy initiatives, playing a pivotal role in Project Green -> "John Smith participated in renewable energy initiatives, playing a role in Project Green"
- The technology is discussed for its potential to help fight climate change -> remains unchanged
- John, the CEO of Company X, is a notable example of effective leadership -> "John is the CEO of Company X"
- Jane emphasizes the importance of collaboration and perseverance -> remains unchanged
- The Behind the Tech podcast by Kevin Scott is an insightful podcast that explores the themes of innovation and technology -> "The Behind the Tech podcast by Kevin Scott is a podcast that explores the themes of innovation and technology"
- Some economists anticipate the new regulation will immediately double production costs, while others predict a gradual increase -> remains unchanged
- AI is frequently discussed in the context of its limitations in ethics and privacy -> "AI is discussed in the context of its limitations in ethics and privacy"
- The power of branding is highlighted in discussions featuring John Smith and Jane Doe -> remains unchanged
- Therefore, leveraging industry events, as demonstrated by Jane’s experience at the Tech Networking Club, can provide visibility and traction for new ventures -> "Jane had an experience at the Tech Networking Club, and her experience involved leveraging an industry event to provide visibility and traction for a new venture"

Your output must adhere to the following format exactly. Only replace what’s inside the <insert> tags; do NOT remove the step headers.
Sentence:
<insert>

4-step stream of consciousness thought process (1. reflect on criteria at a high-level -> 2. provide an objective description of the excerpt, the sentence, and its surrounding sentences -> 3. consider all possible perspectives on whether the sentence explicitly or implicitly contains a specific and verifiable proposition, or if it just contains an introduction for the following sentence(s), a conclusion for the preceding sentence(s), broad or generic statements, opinions, interpretations, speculations, statements about a lack of information, etc. -> 4. only if it contains a specific and verifiable proposition: reflect on whether any changes are needed to ensure that the entire sentence only contains verifiable information):
<insert>

Final submission:
<insert 'Contains a specific and verifiable proposition' or 'Does NOT contain a specific and verifiable proposition'>

Sentence with only verifiable information:
<insert changed sentence, or 'remains unchanged' if no changes, or 'None' if the sentence does NOT contain a specific and verifiable proposition>"""

USER_TEMPLATE = """Question:
{question}

Excerpt:
{excerpt}

Sentence:
{sentence}"""


class Refused(Exception):
    pass


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


# ---------------------------------------------------------------- units

def excerpt(sentences: list[str], i: int, p: int = P_PRECEDING, f: int = F_FOLLOWING) -> str:
    """Section 3.1 and Appendix D: p sentences before i, i, f after, "[...]" where sentences are left out."""
    lo, hi = max(0, i - p), min(len(sentences), i + f + 1)
    parts = ([OMITTED] if lo > 0 else []) + sentences[lo:hi] + ([OMITTED] if hi < len(sentences) else [])
    return " ".join(parts)


def messages(u: dict) -> list[dict]:
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(question=u["question"],
                                                             excerpt=excerpt(u["sentences"], u["i"]),
                                                             sentence=u["sentences"][u["i"]])}]


def answer_units(set_name: str, answer_key: str, question_id: str, config: str, question: str,
                 sentences: list[str]) -> list[dict]:
    return [{"sentence_id": f"{answer_key}#{i}", "set": set_name, "answer_key": answer_key, "claim_index": i,
             "question_id": question_id, "config": config, "question": question, "sentences": sentences, "i": i}
            for i in range(len(sentences))]


def key_questions() -> tuple[dict, dict]:
    import S470_l1_signals as S470
    k = S470.the_key()
    return {q: v["question"] for q, v in k["questions"].items()}, {"path": k["path"], "sha256": k["sha256"]}


def l1_units(census: Path = CENSUS, want_sha: str | None = CENSUS_SHA256, questions: dict | None = None) -> list[dict]:
    """The L1 census in answer order, gated: pinned file, every answer complete from 0 to claims_in_answer - 1."""
    raw = census.read_bytes()
    if want_sha is not None and sha(raw) != want_sha:
        raise Refused(f"{census} sha256 {sha(raw)[:12]} is not S560's {want_sha[:12]}")
    by: dict[str, list[dict]] = {}
    for line in raw.decode().splitlines():
        r = json.loads(line)
        by.setdefault(r["answer_key"], []).append(r)
    out = []
    for k in sorted(by):
        rows = sorted(by[k], key=lambda r: r["claim_index"])
        if [r["claim_index"] for r in rows] != list(range(rows[0]["claims_in_answer"])):
            raise Refused(f"{k}: census claims are not 0 to {rows[0]['claims_in_answer'] - 1}")
        qid = rows[0]["question_id"]
        if questions is not None and qid not in questions:
            raise Refused(f"{k}: question {qid} is not in the D5 key")
        out += answer_units("l1", k, qid, rows[0]["config"], questions[qid] if questions else "",
                            [r["claim"] for r in rows])
    return out


def h49_units(questions: dict) -> list[dict]:
    """Figure 2's 49 answers, re-split by the deposited function and gated against S498's stored rows."""
    import S384_exp04_minicheck_key_v22 as S384
    import S498_human49_minicheck_papers as S498
    ns, _ = S384.deposited_code()
    dec = ns["decompose_to_sentences"]
    rows = {d["eval_id"]: d for d in map(json.loads, S498_ROWS.read_text().splitlines())}
    out = []
    for a in S498.build_answers(S498.read_items()):
        r = rows.get(a["eval_id"])
        if r is None or r["answer_sha256"] != a["answer_sha256"]:
            raise Refused(f"{a['eval_id']}: the answer is not the one S498 scored")
        s = dec(a["answer"]) if a["answer"].strip() else []
        stored = r.get("per_claim") or r.get("per_claim_on_cut_input")
        texts_differ = stored is not None and [x[:STORED_CLAIM_CHARS] for x in s] != [c["claim"] for c in stored]
        if len(s) != r["n_claims"] or texts_differ:
            raise Refused(f"{a['eval_id']}: {len(s)} sentences, S498 stored {r['n_claims']}, or their text differs")
        if a["question_id"] not in questions:
            raise Refused(f"{a['eval_id']}: question {a['question_id']} is not in the D5 key")
        out += answer_units("h49", a["answer_key"], a["question_id"], a["config"], questions[a["question_id"]], s)
    return out


def timing_units(l1: list[dict], census: Path = CENSUS, n: int = TIMING_N, seed: int = TIMING_SEED) -> list[dict]:
    """n L1 sentences, half from S560's candidate stratum and half from the rest, one random.Random(seed)."""
    import S560_heading_rule_eval as S560
    cand = set()
    for line in census.read_text().splitlines():
        r = json.loads(line)
        if S560.candidates_of(r):
            cand.add(f"{r['answer_key']}#{r['claim_index']}")
    rng = random.Random(seed)
    a = sorted((u for u in l1 if u["sentence_id"] in cand), key=lambda u: u["sentence_id"])
    b = sorted((u for u in l1 if u["sentence_id"] not in cand), key=lambda u: u["sentence_id"])
    pick = rng.sample(a, n // 2) + rng.sample(b, n - n // 2)
    return [dict(u, set="timing", stratum="candidate" if u["sentence_id"] in cand else "rest") for u in pick]


# ---------------------------------------------------------------- the answer

def _clean(s: str) -> str:
    return re.sub(r"[*_`#]+", "", s).strip().strip("'\"‘’“”<>").strip()


def parse(text: str) -> dict | None:
    """The outcome of one Selection output, or None when it does not parse."""
    t = text.replace("\r\n", "\n")
    # a template line copied back (its options joined by " or ") and bare <insert> tags are not the answer: before this,
    # a copied "<insert 'Contains ...' or 'Does NOT contain ...'>" line was read as the verdict (11 of the 100 timed)
    t = re.sub(r"(?m)^\s*<insert\b[^>\n]*\bor\b[^>\n]*>\s*$\n?", "", t)
    t = re.sub(r"(?m)^\s*</?insert>\s*$\n?", "", t)
    # the last "final submission": the reasoning may name it first ("... omitted in the final submission."; 1 of the
    # first 816 rows of the full run, read as no verdict)
    ms = list(re.finditer(r"final\s+submission\s*:?\s*\**\s*\n?(.*?)(?:\n\s*\n|\n\s*[*#]*\s*sentence with only "
                          r"verifiable|\Z)", t, re.I | re.S))
    m = ms[-1] if ms else None
    if not m:
        return None
    verdict = _clean(m.group(1)).lower()
    if NOT_CONTAINS in verdict and CONTAINS in verdict.replace(NOT_CONTAINS, ""):
        return None   # both options copied from the template: no verdict
    if NOT_CONTAINS in verdict:
        contains = False
    elif CONTAINS in verdict:
        contains = True
    else:
        return None
    m2 = re.search(r"sentence\s+with\s+only\s+verifiable\s+information\s*:?\s*\**\s*\n?(.*)\Z", t, re.I | re.S)
    rewritten = _clean(m2.group(1)) if m2 else None
    reasoning = t[:m.start()].strip()
    if not contains:
        outcome = "none"
    elif m2 is None:
        outcome = "contains"   # D209 O-a: the verdict without its rewrite line (devstral, 4 of the 100 timed)
    elif rewritten.lower().rstrip(".") == "remains unchanged":
        outcome = "all"
    elif rewritten.lower() in ("none", ""):
        return None
    else:
        outcome = "some"
    return {"outcome": outcome, "verdict": "contains" if contains else "does_not_contain",
            "rewritten": rewritten if outcome == "some" else None, "reasoning": reasoning}


def leaves_papers(outcome: str) -> bool:
    """D208: only "no verifiable claims" leaves the Papers count; a partial verdict keeps the original sentence."""
    return outcome == "none"


# ---------------------------------------------------------------- run

def run_identity(lock, call, units_sha: str) -> str:
    return sha(json.dumps({"script": sha((ROOT / SCRIPT).read_bytes()), "system": sha(SYSTEM_PROMPT),
                           "user": sha(USER_TEMPLATE), "p": P_PRECEDING, "f": F_FOLLOWING, "lock": lock.sha256,
                           "model": call.model, "digest": call.digest, "options": call.options,
                           "fields": call.fields, "units": units_sha}, sort_keys=True))


def units_sha(units: list[dict]) -> str:
    return sha(json.dumps([[u["sentence_id"], u["question"], u["sentences"][u["i"]], excerpt(u["sentences"], u["i"])]
                           for u in units], ensure_ascii=False))


def read_rows(f: Path) -> list[dict]:
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def done_ids(rows_f: Path, ids: set, run_sha: str) -> set:
    out = set()
    for d in read_rows(rows_f):
        if d["run_sha256"] != run_sha:
            raise Refused(f"{rows_f} holds {d['sentence_id']} under run {d['run_sha256'][:12]}, not {run_sha[:12]}; "
                          f"use a new --out")
        if d["sentence_id"] not in ids:
            raise Refused(f"{rows_f} holds {d['sentence_id']}, not a unit of this set")
        if d["status"] in DONE:
            out.add(d["sentence_id"])
    return out


def append(f: Path, d: dict) -> None:
    with f.open("a") as fh:
        fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def select_one(base: str, call, u: dict, calls_f: Path, chat, after_first) -> dict:
    msgs = messages(u)
    rec = chat(base, call, msgs)
    parsed = parse(rec["text"]) if rec["status"] == "ok" else None
    status = rec["status"] if rec["status"] != "ok" else ("ok" if parsed else "unparseable")
    rec.update(sentence_id=u["sentence_id"], set=u["set"], prompt_sha256=sha(json.dumps(msgs, ensure_ascii=False)),
               selection_status=status)
    append(calls_f, rec)
    after_first(rec)
    return {"sentence_id": u["sentence_id"], "set": u["set"], "answer_key": u["answer_key"],
            "claim_index": u["claim_index"], "question_id": u["question_id"], "config": u["config"],
            "stratum": u.get("stratum"), "sentence": u["sentences"][u["i"]], "status": status,
            "outcome": parsed and parsed["outcome"], "leaves_papers": bool(parsed) and leaves_papers(parsed["outcome"]),
            "verdict": parsed and parsed["verdict"], "rewritten": parsed and parsed["rewritten"],
            "reasoning": parsed and parsed["reasoning"], "text": rec["text"], "error": rec["error"],
            "stop_reason": rec["stop_reason"], "prompt_tokens": rec["prompt_tokens"],
            "output_tokens": rec["output_tokens"], "wall_s": rec["wall_s"], "prompt_eval_s": rec["prompt_eval_s"],
            "eval_s": rec["eval_s"], "busy_servers_on_machine": rec.get("busy_servers_on_machine"),
            "model_digest": rec["model_digest"], "server": rec["server"], "lock_sha256": rec["lock_sha256"],
            "at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def summarise(out: Path, units: list[dict], run_sha: str, inputs: dict, argv: list[str]) -> dict:
    latest = {}
    for d in read_rows(out / "rows.jsonl"):
        latest[d["sentence_id"]] = d
    rows = [latest[u["sentence_id"]] for u in units if u["sentence_id"] in latest]
    walls = sorted(d["wall_s"] for d in rows if d.get("wall_s") is not None)

    def q(p):
        return walls[min(len(walls) - 1, int(round(p * (len(walls) - 1))))] if walls else None
    med = statistics.median(walls) if walls else None
    mean = statistics.mean(walls) if walls else None
    s = {"_provenance": {"script": SCRIPT, "script_sha256": sha((ROOT / SCRIPT).read_bytes()),
                         "command": "uv run --frozen python " + " ".join([SCRIPT] + argv), "inputs": inputs,
                         "written": time.strftime("%Y-%m-%dT%H:%M:%S"), "decision": "D208",
                         "method": "Claimify Selection (arXiv 2502.10855v2, section 3.2, Appendix N.1.1, D)"},
         "run_sha256": run_sha, "units": len(units), "rows": len(rows),
         "status": dict(Counter(d["status"] for d in rows)),
         "outcome": dict(Counter(d["outcome"] for d in rows if d["outcome"])),
         "leaves_papers": sum(d["leaves_papers"] for d in rows),
         "by_stratum": {k: dict(Counter(d["outcome"] for d in rows if d.get("stratum") == k))
                        for k in sorted({d.get("stratum") for d in rows if d.get("stratum")})},
         "parse_failures": sum(d["status"] == "unparseable" for d in rows),
         "errors": sum(d["status"] not in DONE for d in rows),
         "wall_s": {"median": med, "mean": mean, "p90": q(0.9), "min": walls[0] if walls else None,
                    "max": walls[-1] if walls else None},
         "prompt_tokens_mean": statistics.mean(d["prompt_tokens"] for d in rows if d["prompt_tokens"]) if rows else None,
         "output_tokens_mean": statistics.mean(d["output_tokens"] for d in rows if d["output_tokens"]) if rows else None,
         "stop_reasons": dict(Counter(d["stop_reason"] for d in rows)),
         "busy_servers_on_machine": dict(Counter(str(d["busy_servers_on_machine"]) for d in rows)),
         "eta_one_server_h": {"sentences": ETA_SENTENCES, "at_median": med and round(ETA_SENTENCES * med / 3600, 1),
                              "at_mean": mean and round(ETA_SENTENCES * mean / 3600, 1)},
         "partial_verdict": "a 'some' verdict keeps the original sentence in Papers (MiniCheck scored it); the rewritten "
                            "sentence is stored, not used. Claude's choice, for Valerio to confirm (D208)",
         "complete": len(rows) == len(units) and all(d["status"] == "ok" for d in rows)}
    (out / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n")
    return s


def build(set_name: str) -> tuple[list[dict], dict]:
    questions, key = key_questions()
    inputs = {"key": key, "census": {"path": str(CENSUS.relative_to(ROOT)), "sha256": CENSUS_SHA256}}
    l1 = l1_units(questions=questions)
    if len(l1) != N_L1:
        raise Refused(f"{len(l1)} L1 sentences, not {N_L1}")
    if set_name == "timing":
        return timing_units(l1), inputs
    if set_name == "l1":
        return l1, inputs
    h49 = h49_units(questions)
    inputs["s498"] = {"path": str(S498_ROWS.relative_to(ROOT)), "sha256": sha(S498_ROWS.read_bytes())}
    if len(h49) != N_H49:
        raise Refused(f"{len(h49)} sentences in the 49, not {N_H49}")
    return (h49 if set_name == "h49" else l1 + h49), inputs


def run(a, argv: list[str]) -> int:
    from experiments.runner import ollama_client as OC
    from experiments.scorers import judge_passages as JP
    units, inputs = build(a.set)
    if a.limit:
        units = units[: a.limit]
    whole_sha = units_sha(units)
    if a.shard:
        k, n = a.shard
        units = [u for j, u in enumerate(units) if j % n == k]
        inputs = dict(inputs, shard={"k": k, "n": n, "units": len(units)})
    if a.dry_run:
        sizes = [len(json.dumps(messages(u), ensure_ascii=False)) for u in units]
        print(f"S564 dry run: set {a.set}, {len(units)} sentences, prompt {min(sizes):,} to {max(sizes):,} characters, "
              f"mean {statistics.mean(sizes):,.0f}; no server contacted")
        return 0
    lane = os.environ.get("S564_LANE")
    if not lane or not lane.isdigit():
        raise Refused("S564_LANE (the lane number n of the server 11450 + n) is not set")
    port = LANE_BASE + int(lane)
    a.base, a.log, a.judge = f"http://127.0.0.1:{port}", Path.home() / "ollama_logs" / f"serve_{port}.log", "main"
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    JP.hold_writer(out)
    from experiments.runner.lock import load
    lock0 = load()
    call0 = lock0.ollama(lock0.d["scorers"]["model"], role="scorer")
    run_sha = run_identity(lock0, call0, whole_sha)
    rows_f, calls_f = out / "rows.jsonl", out / "calls.jsonl"
    done = done_ids(rows_f, {u["sentence_id"] for u in units}, run_sha)
    todo = [u for u in units if u["sentence_id"] not in done]
    if not todo:
        s = summarise(out, units, run_sha, inputs, argv)
        print(f"S564: all {len(units)} sentences done; {s['status']}")
        return 0 if s["complete"] else 1
    lock, model, jcall, fl = JP.start(a, out, "S564")
    call = lock.ollama(lock.d["scorers"]["model"], role="scorer")
    if (lock.sha256 != lock0.sha256 or call.model != jcall.model or call.digest != jcall.digest
            or call.options != jcall.options or call.fields != jcall.fields or call.options != call0.options):
        raise Refused("the scorer call differs from the judge call the fresh load checked, or the lock changed")
    append(out / "headers.jsonl", {"script": SCRIPT, "script_sha256": sha((ROOT / SCRIPT).read_bytes()),
                                   "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "set": a.set, "units": len(units),
                                   "done": len(done), "to_do": len(todo), "lane": int(lane), "model": call.model,
                                   "model_digest": call.digest, "lock_sha256": lock.sha256, "options": call.options,
                                   "fields": call.fields, "run_sha256": run_sha, "inputs": inputs,
                                   "machine_identity": fl.get("machine_identity"),
                                   "system_prompt_sha256": sha(SYSTEM_PROMPT), "user_template_sha256": sha(USER_TEMPLATE)})

    def after_first(rec):
        if JP._AFTER_FIRST:
            JP.certify_first_call(rec)
    print(f"S564: set {a.set}, {len(units)} sentences, {len(done)} done, {len(todo)} to do, {call.model} "
          f"(lock {lock.sha256[:12]}, run {run_sha[:12]})", flush=True)
    for k, u in enumerate(todo, 1):
        row = select_one(a.base, call, u, calls_f, OC.chat, after_first)
        if row["lock_sha256"] != lock.sha256 or row["model_digest"] != call.digest:
            raise Refused(f"{u['sentence_id']}: the call ran under lock {row['lock_sha256']} digest {row['model_digest']}")
        row["run_sha256"] = run_sha
        append(rows_f, row)
        if k % 25 == 0 or k == len(todo):
            print(f"{row['at']} {k}/{len(todo)} last {row['status']} {row['outcome']} {row['wall_s']} s", flush=True)
    s = summarise(out, units, run_sha, inputs, argv)
    print(f"S564 SUMMARY: {s['rows']} of {s['units']}; status {s['status']}; outcome {s['outcome']}; wall median "
          f"{s['wall_s']['median']} s, p90 {s['wall_s']['p90']} s; ETA {s['eta_one_server_h']} h", flush=True)
    return 0 if s["complete"] else 1


def selftest() -> int:
    """No model call: the excerpt, the prompt and the parser on fixed cases."""
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'ok  ' if cond else 'FAIL'} {name}")
    s = [f"S{i}." for i in range(12)]
    check("excerpt at 0: no leading marker, trailing marker", excerpt(s, 0) == " ".join(s[:6] + [OMITTED]))
    check("excerpt at 6: both markers", excerpt(s, 6) == " ".join([OMITTED] + s[1:12]))
    check("excerpt at 11: leading marker only", excerpt(s, 11) == " ".join([OMITTED] + s[6:12]))
    check("excerpt of a short answer: no marker", excerpt(s[:3], 1) == " ".join(s[:3]))
    u = answer_units("x", "k", "q", "c", "What?", s)[3]
    m = messages(u)
    check("system prompt is Claimify's", m[0]["content"] == SYSTEM_PROMPT and "20%" in SYSTEM_PROMPT)
    check("user prompt fields", m[1]["content"] == f"Question:\nWhat?\n\nExcerpt:\n{excerpt(s, 3)}\n\nSentence:\nS3.")
    out = "Sentence:\nX\n\n4-step ...:\nthinking\n\nFinal submission:\n{v}\n\nSentence with only verifiable information:\n{r}"
    cases = [("Contains a specific and verifiable proposition", "remains unchanged", "all"),
             ("Does NOT contain a specific and verifiable proposition", "None", "none"),
             ("Contains a specific and verifiable proposition", "A shorter sentence.", "some"),
             ("**Contains a specific and verifiable proposition**", "'remains unchanged'", "all")]
    for v, r, want in cases:
        p = parse(out.format(v=v, r=r))
        check(f"parse {want}: {v[:20]} / {r[:20]}", p and p["outcome"] == want)
    check("no final submission: None", parse("Sentence:\nX\nthinking") is None)
    check("contains with None rewritten: None", parse(out.format(v=CONTAINS.capitalize(), r="None")) is None)
    check("other verdict word: None", parse(out.format(v="Maybe", r="None")) is None)
    seen = "Sentence:\n<insert>X</insert>\n\nthinking\n\nFinal submission:\n<insert 'Contains a specific and verifiable proposition'>"
    check("verdict without rewrite line: contains", (parse(seen) or {}).get("outcome") == "contains")
    echo = ("Final submission:\n<insert 'Contains a specific and verifiable proposition' or 'Does NOT contain a specific "
            "and verifiable proposition'>\nContains a specific and verifiable proposition\n</insert>\n\nSentence with only "
            "verifiable information:\n<insert changed sentence, or 'remains unchanged' if no changes, or 'None' if the "
            "sentence does NOT contain a specific and verifiable proposition>\nremains unchanged")
    check("template lines copied, then the answer: all", (parse(echo) or {}).get("outcome") == "all")
    check("both options copied: None", parse("Final submission:\n<insert 'Contains a specific and verifiable proposition' "
                                             "or 'Does NOT contain a specific and verifiable proposition'>") is None)
    check("bold headers", (parse("**Final submission:**\nDoes NOT contain a specific and verifiable proposition\n\n"
                                 "**Sentence with only verifiable information:**\nNone") or {}).get("outcome") == "none")
    check("the reasoning names the final submission first: the last one is read",
          (parse("4. The note can be omitted in the final submission.\n\nFinal submission:\nContains a specific and "
                 "verifiable proposition\n\nSentence with only verifiable information:\nremains unchanged") or {})
          .get("outcome") == "all")
    check("only none leaves Papers", leaves_papers("none") and not leaves_papers("some") and not leaves_papers("all"))
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--set", choices=["timing", "l1", "h49", "full"])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--machine", choices=["macos", "beelink"])
    ap.add_argument("--binary", type=Path)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--shard", help="k/n: only the units whose place in the set is k modulo n (0 <= k < n)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.set:
        ap.error("--set is needed")
    if a.shard:
        m = re.fullmatch(r"(\d+)/(\d+)", a.shard)
        if not m or not int(m.group(1)) < int(m.group(2)):
            ap.error("--shard is k/n with 0 <= k < n")
        a.shard = (int(m.group(1)), int(m.group(2)))
    a.out = a.out or (OUT / a.set / (f"shard_{a.shard[0]}_of_{a.shard[1]}" if a.shard else "all"))
    if not a.dry_run and (a.machine is None or a.binary is None):
        ap.error("a run needs --machine and --binary (or --dry-run)")
    try:
        return run(a, argv)
    except Refused as e:
        print(f"REFUSED: {e}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
