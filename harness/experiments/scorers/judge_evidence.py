#!/usr/bin/env python3
"""S18f (D96 Q211 O1): S18e's three arms judged again under the lock, on G1's draw-1 answers to the 86 answerable
questions, with whole papers.

D96 (Valerio, 18 October): "S18e's three arms (no paper, whole paper, wrong paper) are run again on G1's draw-1
answerable answers under the lock, with whole papers up to the lock's context, before the abstract's judge sentence is
rewritten; a result that contradicts the submitted one is reported as it is."

WHAT S18e WAS (scripts/S18e_judge_evidence_devstral.py, findings/recompute/S18e_results.md). The judge,
devstral-small-2:24b, scored exp04's answers in five arms: A and B2 controls, B no paper, C the question's source
paper(s) in a "## Source Material" section before "## Generated Answer" (scripts/S18b_rejudge.py build_prompt), D the
same section holding a size-matched wrong paper (S18b.mismatch_partner: the nearest question in S18's evidence-size
order with no source file in common). A paper was sent whole when the question's papers fitted 28,000 tokens, else as
bge-m3-ranked excerpts. S18e judged 71 questions, 426 calls per arm (its ledger, S18e_devstral.jsonl), and analysed
61 questions, 366 answers per arm (S18's frozen set less D7, S18e_results.json analysis_set).

WHAT THIS RUNS. The answers: G1's draw 1 (~/k1_inputs, K1's frozen copy, checked against its MANIFEST.sha256), six
strategies, the 86 answerable questions (Rule 8, LIST.md), 516 answers; an answer G1R15 lists (~/s3_inputs/g1r15,
keys.txt, the 15 reruns of 18 October, D93 Q-c) is taken from that copy, as S3's collect --replace takes it. Each
answer is read by judge_passages.run_answers (records.py), so its question, key, answer and item_sha256 are S3's.
  B  no paper: S18b.build_prompt with no evidence. For every answer it is checked byte for byte to equal S3's call
     (a) (judge_passages.safe_prompts), so B is NOT judged here: `analyze` takes S3's (a) row of the same answer,
     after checking that row's item_sha256, its (a) prompt_sha256 and its run_sha256 (lock, judge code, options,
     system prompt) are what this code computes.
  C  whole paper: S18b.build_prompt with the question's own papers, every paper whole (S18b.build_evidence's "full"
     layout for every question, S18's whole extracted text, findings/recompute/S18_evidence_docs.jsonl).
  D  wrong paper: the same with the papers of S18b.mismatch_partner(question), on S18's sizing and order, exactly as
     S18e chose its donors (checked against S18e's ledger for every question S18e judged).
No arm is cut (LOCK.toml [text]): a prompt longer than the lock's num_ctx is sent and fails visibly (truncate false).
`count` gives each prompt's exact devstral token count offline, so how many fit is known before any call.
Every call goes through experiments/runner/ollama_client.generate with lock.ollama([judge] model, role="judge"),
by judge_passages.judge_call (retried once on an unparseable or failed call, never on an HTTP 4xx), after
judge_passages.start (fresh load, server checks, the check again after the first call: D80 V6).

GATES (every command but `count`'s token part runs them first; nothing is planned, judged or written unless all pass):
  G1  the 516 answers: 86 answerable questions x 6 strategies, draw 1, each once, the 86 those of the runner's key;
      G1R15's listed draw-1 keys found and different from G1's.
  G2  every paper's text is S18's: its PDF sha256 and length equal S18_evidence_manifest.json's; every question's
      source files in the D5 key equal S18's sizing.
  G3  every whole-paper block that S18e also sent whole has S18e's evidence_sha256; every donor equals S18e's for
      each question S18e judged in arm D.
  G4  per answer: B equals S3's (a); C and D equal B with one section inserted at the template's "## Generated
      Answer" (removing it gives B byte for byte); the section is the evidence whole.

REPRODUCE BEFORE WRITING (README.md:75-79). `count` builds devstral's tokenizer from the GGUF of the locked model
(LOCK.toml [models] digest -> the manifest blob, sha256 checked -> its model layer), with llama.cpp's "default"
pre-tokenizer (the GGUF's tokenizer.ggml.pre), and writes no count unless it reproduces Ollama's prompt_eval_count on
every stored devstral row it can rebuild: S440's 214 calibration calls (prompt + one constant, the system prompt and
the chat wrapping) and S18e's 1,086 arm B, C and D calls whose prompts S18e's own code rebuilds (C and D with whole
papers), with the same constant. The judge run itself never uses the tokenizer.

    uv run python experiments/scorers/judge_evidence.py count            [--g1 DIR] [--g1r15 DIR] [--store DIR]
    uv run python experiments/scorers/judge_evidence.py plan --out DIR --check-dir DIR [--report] [--unit U]
    uv run python experiments/scorers/judge_evidence.py units --out DIR
    uv run python experiments/scorers/judge_evidence.py run --base URL --log LOG --binary BIN --machine macos \
        --check-dir DIR --out DIR --unit U [--limit N] [--no-recheck]
    uv run python experiments/scorers/judge_evidence.py collect --out DIR [DIR ...] --dest FILE
    uv run python experiments/scorers/judge_evidence.py analyze --collect FILE --s3 FILE [--partial]

UNITS. The 86 questions in id order, UNIT_Q per unit (u01 to u09); a unit judges, per question, arm C on the six
strategies and then arm D on the six, so the six calls of an arm share the prompt up to the answer (the evidence
comes before "## Generated Answer"; S18e's warm calls took a median 58 s against 272 s cold). A unit writes
<out>/judge/<unit>/judge_evidence.jsonl, one row per call (latest row per ident wins), with judge_passages's statuses;
a row is done when its status is ok or no_answer under the same item_sha256 and run_sha256, and a row of the same
ident under another item or run sha256 makes `run` refuse (one file, one definition). A row's item_sha256 holds its
answer, arm, paper block and prompt sha256; its run_sha256 the lock, options, system prompt and call_code_identity
(judge_passages, S18b, S18's papers), not this file, so editing the analysis does not orphan judged rows. One writer per unit
(judge_passages.hold_writer, exit 75). A unit that judged answers ends with a recheck: another fresh load, its first
RECHECK_N judged rows judged again, any difference exits 1.

Outputs: `count` findings/recompute/S18f_tokens.{json,md}; `plan --report` findings/recompute/S18f_plan.{json,md};
`analyze` findings/recompute/S18f_results.{json,md}; it refuses while any answer lacks its B, C or D row (each
counted), unless --partial, which marks the output PARTIAL. `run` has no default --base. `count`, `plan`, `units`,
`collect` and `analyze` make no network call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import struct
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from experiments.runner import experiment as E  # noqa: E402
from experiments.runner.lock import load  # noqa: E402
from experiments.scorers import judge_passages as JP  # noqa: E402
from experiments.scorers import records as R  # noqa: E402
import S141_runner.judge as J  # noqa: E402
import S18b_rejudge as S18b  # noqa: E402

RECOMPUTE = ROOT / "findings/recompute"
DOCS = RECOMPUTE / "S18_evidence_docs.jsonl"
MANIFEST = RECOMPUTE / "S18_evidence_manifest.json"
S18E_LEDGER = RECOMPUTE / "S18e_devstral.jsonl"
S18E_RESULTS = RECOMPUTE / "S18e_results.json"
S440_LEDGER = RECOMPUTE / "S440_judge_lock_check.jsonl"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
RUN = "exp_01__{c}__exp_v4_s20_n0"
DRAW = 1
N_QUESTIONS = 86                       # Rule 8's answerable group (LIST.md: extractive 60, synthesis 26)
ARMS = ("C", "D")                      # B is S3's (a): see the docstring
KIND = {"C": "correct", "D": "mismatch"}
UNIT_Q = 10
RECHECK_N = 10
FINAL = {"ok", "no_answer"}
ANCHOR = JP.ANCHOR                     # "## Generated Answer\n", where S18b inserts its section
G1_DEFAULT = Path("~/k1_inputs").expanduser()
G1R15_DEFAULT = Path("~/s3_inputs/g1r15").expanduser()
STORE_DEFAULT = Path("~/k1_inputs/store").expanduser()
SENTINEL = "\x00S18f\x00"


class GateError(SystemExit):
    pass


def sha(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8", "surrogatepass") if isinstance(b, str) else b).hexdigest()


def num(v: float) -> str:
    """A count with thousands separators; a half (the median of an even count) keeps its .5."""
    return f"{int(v):,}" if float(v).is_integer() else f"{v:,.1f}"


def inputs_identity(a) -> dict:
    """The inputs by content, not by where they sat (review defect 6): each frozen copy by its MANIFEST.sha256's
    sha256 and its lasting source, so any copy of the same source regenerates the output in one command."""
    out = {"g1": {"source": "K1's frozen copy ~/k1_inputs (laptop and Studio)",
                  "manifest_sha256": file_sha(a.g1 / "MANIFEST.sha256")},
           "store": {"source": "~/k1_inputs/store", "path_is_default": a.store == STORE_DEFAULT},
           "s18_docs": file_sha(DOCS), "s18_manifest": file_sha(MANIFEST)}
    if a.g1r15 is not None:
        out["g1r15"] = {"source": "the Studio's ~/s3_inputs/g1r15 (snap_s3_inputs.sh G1R15), or a copy of it",
                        "manifest_sha256": file_sha(a.g1r15 / "MANIFEST.sha256")}
    return out


def file_sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def call_code_identity() -> dict:
    """The code and data that define a judged call: judge_passages's code identity (the judge call, its parser, key
    and reader), S18b (the evidence prompt and the donor rule) and S18's papers and sizing. This file is not in it
    (review defect 3, 18 October): what this file adds to a call is its prompt, and every row's item_sha256 holds the
    prompt's sha256 (work), so an edit here that changes a prompt is refused per row, and an edit that does not (the
    analysis, a docstring) leaves the judged rows usable."""
    return {**JP.code_identity(), "s18b_rejudge_py": sha(Path(S18b.__file__).read_bytes()), "s18_docs": file_sha(DOCS),
            "s18_manifest": file_sha(MANIFEST)}


def code_identity() -> dict:
    """call_code_identity plus this file's own sha256: the provenance of every output, never a row's identity."""
    return {**call_code_identity(), "judge_evidence_py": sha(Path(__file__).read_bytes())}


def run_identity(lock, call) -> str:
    return sha(json.dumps({"lock": lock.sha256, "code": call_code_identity(), "options": call.options,
                           "fields": call.fields, "system": call.system and sha(call.system)}, sort_keys=True))


# ---------------------------------------------------------------- the answers (G1)

def answerable_ids() -> list[str]:
    """The runner's 86 answerable questions (Rule 8: the D5 key's answer type extractive or synthesis)."""
    return sorted(q["id"] for q in E.questions() if q["answer_type"] in ("extractive", "synthesis"))


def manifest_ok(copy: Path, prefixes: tuple[str, ...]) -> tuple[bool, str]:
    """The copy's MANIFEST.sha256 lines under these prefixes: at least one, every file present with that sha256."""
    try:
        lines = [ln.split("  ", 1) for ln in (copy / "MANIFEST.sha256").read_text().splitlines() if ln.strip()]
    except OSError as e:
        return False, f"no manifest: {e}"
    mine = [(h, p) for h, p in lines if p.startswith(prefixes)]
    bad = [p for h, p in mine if not (copy / p).is_file() or file_sha(copy / p) != h]
    return bool(mine) and not bad, f"{len(mine)} files, differing {bad[:3]}"     # no path: outputs name inputs by content (defect 6)


def read_answers(g1: Path, g1r15: Path | None, store: Path) -> tuple[list[dict], list]:
    """G1's draw-1 answers to the 86, six strategies, each in its latest version (G1R15 replaces what keys.txt lists)."""
    qids = answerable_ids()
    ok, note = manifest_ok(g1, tuple(f"runs/{RUN.format(c=c)}/" for c in CONFIGS))
    checks = [("G0 G1's runs equal their MANIFEST.sha256 lines", ok, note)]
    if g1r15 is not None:
        ok, note = manifest_ok(g1r15, ("runs/", "keys.txt", "same.log"))
        same = (g1r15 / "same.log").exists() and any(ln.startswith("SAME: ") for ln in  # run_s3.sh's grep '^SAME: '
                                                      (g1r15 / "same.log").read_text().splitlines())
        checks.append(("G0 G1R15's copy equals its MANIFEST.sha256 and its same.log says SAME (D93 Q-c)", ok and same, note))
    want = set(qids)
    by: dict[tuple, dict] = {}
    for c in CONFIGS:
        for x in JP.run_answers(g1 / "runs" / RUN.format(c=c), None, store):
            if x["draw"] == DRAW and x["question_id"] in want:
                if R.group_of(x["question_id"]) != "answerable":
                    raise GateError(f"G1 REFUSED: {x['question_id']} is in the 86 but Rule 8 groups it "
                                    f"{R.group_of(x['question_id'])}")
                if (c, x["question_id"]) in by:
                    raise GateError(f"G1 REFUSED: two draw-1 answers to {x['question_id']} in {c}")
                by[(c, x["question_id"])] = {**x, "from": "G1"}
    replaced, identical = [], []
    if g1r15 is not None:
        keys = {k for k in (g1r15 / "keys.txt").read_text().splitlines() if k.strip()}
        d1 = {k for k in keys if k.endswith(f"|d{DRAW}")}
        found = set()
        for c in CONFIGS:
            run = g1r15 / "runs" / RUN.format(c=c)
            if not run.exists():
                continue
            for x in JP.run_answers(run, None, store):
                if x["answer_key"] not in d1:
                    continue
                found.add(x["answer_key"])
                if x["question_id"] not in want:
                    continue
                old = by.get((c, x["question_id"]))
                if old is None or old["answer_key"] != x["answer_key"]:
                    raise GateError(f"G1 REFUSED: G1R15's {x['answer_key']} replaces no G1 answer of the same key")
                if old["item_sha256"] == x["item_sha256"]:     # a rerun that reproduced its answer: the same answer
                    identical.append(x["answer_key"])          # (review defect 11), taken from G1R15 all the same
                by[(c, x["question_id"])] = {**x, "from": "G1R15"}
                replaced.append(x["answer_key"])
        checks.append(("G1 G1R15's draw-1 keys all found in its copy", found == d1,
                       f"{len(found)} of {len(d1)} draw-1 keys; {len(replaced)} answerable replaced: {sorted(replaced)}"
                       f"; of them identical to G1's: {sorted(identical) or 'none'}"))
    items = [by[k] for k in sorted(by, key=lambda k: (k[1], CONFIGS.index(k[0])))]
    got_q = {x["question_id"] for x in items}
    checks.append(("G1 516 answers: 86 answerable questions x 6 strategies, draw 1",
                   len(qids) == N_QUESTIONS and got_q == want and len(items) == N_QUESTIONS * len(CONFIGS),
                   f"{len(items)} answers, {len(got_q)} questions, {N_QUESTIONS} expected"))
    return items, checks


# ---------------------------------------------------------------- papers and donors (G2, G3)

def papers(qids: list[str]) -> tuple[dict, dict, dict, list]:
    """S18's whole papers, one block per question used (its own, or as a donor), and the donors."""
    man = json.loads(MANIFEST.read_text())
    sizing = man["sizing"]
    order = sorted(sizing, key=lambda k: (sizing[k]["est_tokens"], k))     # S18b.main's donor order (S18e load())
    docs, bad = {}, []
    for d in map(json.loads, DOCS.open()):
        m = man["documents"].get(d["file"]) or {}
        if d["sha256"] != m.get("sha256") or len(d["text"]) != m.get("chars"):
            bad.append(d["file"])
        docs[d["file"]] = d["text"]
    key = {q["id"]: q for q in json.loads(E.KEY_D5.read_text())["questions"]}
    diff = [q for q in qids if q not in sizing or key[q]["source_files"] != sizing[q]["source_files"]]
    checks = [("G2 every paper is S18's (PDF sha256 and length, S18_evidence_manifest.json)", not bad and len(docs) == len(man["documents"]),
               f"{len(docs)} papers; differing {bad}"),
              ("G2 every question's source files in the D5 key equal S18's sizing", not diff, f"differing {diff}")]
    donors = {q: S18b.mismatch_partner(q, sizing, order) for q in qids}
    full = {q: {**sizing[q], "mode": "full"} for q in sizing}             # every paper whole
    blocks = {}
    for src in sorted(set(qids) | set(donors.values())):
        text, mode, chars = S18b.build_evidence(src, full, docs, [], None, 0)
        files = full[src]["source_files"]
        if mode != "full" or any(docs[f] not in text for f in files):
            raise GateError(f"G2 REFUSED: {src}'s block is not its papers whole")
        blocks[src] = {"text": text, "sha256": sha(text), "files": files, "chars": len(text),
                       "s18_mode": sizing[src]["mode"]}
    # G3: S18e's own ledger
    seen_ev, bad_ev, seen_d, bad_d = 0, [], 0, []
    for r in map(json.loads, S18E_LEDGER.open()):
        if r["arm"] in ("C", "D") and r.get("evidence_mode") == "full" and r["evidence_source_qid"] in blocks:
            seen_ev += 1
            if blocks[r["evidence_source_qid"]]["sha256"] != r["evidence_sha256"]:
                bad_ev.append(r["evidence_source_qid"])
        if r["arm"] == "D" and r["question_id"] in donors:
            seen_d += 1
            if donors[r["question_id"]] != r["evidence_source_qid"]:
                bad_d.append(r["question_id"])
    checks.append(("G3 whole-paper blocks equal S18e's evidence_sha256 where S18e sent them whole", seen_ev > 0 and not bad_ev,
                   f"{seen_ev} S18e rows compared; differing {sorted(set(bad_ev))}"))
    checks.append(("G3 every donor equals S18e's for the questions S18e judged in arm D", seen_d > 0 and not bad_d,
                   f"{seen_d} S18e rows compared; differing {sorted(set(bad_d))}"))
    in86 = set(qids)
    order86 = [q for q in order if q in in86]
    other = {q: S18b.mismatch_partner(q, {k: sizing[k] for k in order86}, order86) for q in qids}
    notes = {"donors_outside_the_86": sorted(q for q in qids if donors[q] not in in86),
             "donor_differs_if_chosen_among_the_86": sorted(q for q in qids if other[q] != donors[q])}
    return blocks, donors, notes, checks


# ---------------------------------------------------------------- prompts (G4)

def section_head(template: str) -> str:
    """The text S18b.build_prompt puts before the evidence, cut out of its own output (not restated)."""
    p = S18b.build_prompt(template, {"question": "q", "expected_answer": "e", "expected_concepts": []}, "a", SENTINEL, None)
    head = p.split(SENTINEL)[0]
    return head[head.index("## Source Material"):]


def anchor_at(template: str, x: dict) -> int:
    """Where the template's "## Generated Answer" lands in x's prompt (as judge_passages.prompts finds it)."""
    head = template[:template.index(ANCHOR)]
    text = ", ".join(x["concepts"]) if x["concepts"] else "N/A"
    return len(head.replace("{question}", x["question"]).replace("{expected_answer}", x["expected"])
               .replace("{expected_concepts}", text))


def arm_prompts(template: str, head: str, x: dict, blocks: dict, donors: dict) -> dict:
    """{"B": S3's (a), "C": ..., "D": ...} for one answered answer; raises GateError on any layout difference."""
    q = {"question": x["question"], "expected_answer": x["expected"], "expected_concepts": x["concepts"]}
    b = S18b.build_prompt(template, q, x["answer"], "", None)
    a = JP.safe_prompts(x)[0]
    if b != a:
        raise GateError(f"G4 REFUSED: {x['answer_key']}: arm B is not S3's (a)")
    k = anchor_at(template, x)
    if b[k:k + len(ANCHOR)] != ANCHOR:
        raise GateError(f"G4 REFUSED: {x['answer_key']}: the template's anchor is not where it should be")
    out = {"B": b}
    for arm in ARMS:
        src = x["question_id"] if arm == "C" else donors[x["question_id"]]
        ev = blocks[src]["text"]
        p = S18b.build_prompt(template, q, x["answer"], ev, None)
        section = head + ev + "\n\n"
        if p != b[:k] + section + b[k:] or p[:k] + p[k + len(section):] != b:
            raise GateError(f"G4 REFUSED: {x['answer_key']}: arm {arm} is not B with one section at the anchor")
        out[arm] = p
    return out


def work(g1: Path, g1r15: Path | None, store: Path) -> dict:
    """Every gate, then every call of the job in unit order, with its prompt."""
    t0 = time.time()
    items, checks = read_answers(g1, g1r15, store)
    qids = answerable_ids()
    blocks, donors, notes, c2 = papers(qids)
    checks += c2
    template = S18b.load_harness()[0]
    if template != J._template("ANSWERABLE_JUDGE_PROMPT"):
        raise GateError("G4 REFUSED: S18b's template is not the archived one judge_passages sends")
    head = section_head(template)
    calls, b_same = [], 0
    for x in items:
        ok = JP.answered(x)
        pr = arm_prompts(template, head, x, blocks, donors) if ok else {}
        b_same += ok
        for arm in ARMS:
            src = x["question_id"] if arm == "C" else donors[x["question_id"]]
            p = pr.get(arm)
            calls.append({"arm": arm, "x": x, "src": src, "prompt": p,     # the prompt's sha256 in the item (defect 3)
                          "item_sha256": sha(json.dumps([x["item_sha256"], arm, src, blocks[src]["sha256"],
                                                         p and sha(p)])),
                          "b_prompt_sha256": sha(pr["B"]) if ok else None})
    n_ans = sum(JP.answered(x) for x in items)
    checks.append(("G4 every answered answer: B equals S3's (a); C and D are B plus one whole section at the anchor",
                   b_same == n_ans, f"{b_same} answered answers; {len(items) - n_ans} with no answer (no call)"))
    order = {q: i for i, q in enumerate(qids)}
    calls.sort(key=lambda c: (order[c["x"]["question_id"]], ARMS.index(c["arm"]), CONFIGS.index(c["x"]["config"])))
    for c in calls:
        c["unit"] = unit_of(c["x"]["question_id"], qids)
    return {"items": items, "calls": calls, "blocks": blocks, "donors": donors, "notes": notes, "checks": checks,
            "qids": qids, "template_sha256": sha(template), "s": round(time.time() - t0, 1)}


def unit_of(qid: str, qids: list[str]) -> str:
    return f"u{qids.index(qid) // UNIT_Q + 1:02d}"


def ident(d: dict) -> tuple:
    return d["arm"], d["run_id"], d["config"], d["question_id"], d["draw"]


def call_ident(c: dict) -> tuple:
    return c["arm"], c["x"]["run_id"], c["x"]["config"], c["x"]["question_id"], c["x"]["draw"]


def gate(w: dict) -> None:
    for name, ok, note in w["checks"]:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {note}", flush=True)
    if not all(ok for _, ok, _ in w["checks"]):
        raise GateError("GATE FAILED: nothing planned, judged or written")
    print(f"GATE PASSED ({len(w['checks'])} checks, {w['s']} s)", flush=True)


# ---------------------------------------------------------------- the token count (offline)

def _rd(f, fmt):
    return struct.unpack("<" + fmt, f.read(struct.calcsize(fmt)))[0]


def _rstr(f):
    return f.read(_rd(f, "Q")).decode("utf-8", "surrogateescape")


_SCALAR = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}


def _val(f, t):
    if t == 8:
        return _rstr(f)
    if t == 9:
        it, n = _rd(f, "I"), _rd(f, "Q")
        return [_val(f, it) for _ in range(n)]
    return _rd(f, _SCALAR[t])


def gguf_kv(path: Path) -> dict:
    """The key-value header of a GGUF file (version 2 or 3); the tensors are not read."""
    kv = {}
    with open(path, "rb") as f:
        if f.read(4) != b"GGUF":
            raise SystemExit(f"REFUSED: {path} is not a GGUF file")
        if _rd(f, "I") not in (2, 3):
            raise SystemExit(f"REFUSED: {path}: GGUF version not 2 or 3")
        _rd(f, "Q")
        for _ in range(_rd(f, "Q")):
            k = _rstr(f)
            kv[k] = _val(f, _rd(f, "I"))
    return kv


def model_blob(model: str, digest: str, models_dir: Path) -> tuple[Path, dict]:
    """The locked model's GGUF: blobs/sha256-<lock digest> is the model's manifest (its sha256 checked), whose
    application/vnd.ollama.image.model layer is the weights file."""
    man = models_dir / "blobs" / f"sha256-{digest}"
    if not man.exists() or file_sha(man) != digest:
        raise SystemExit(f"REFUSED: no manifest blob of {model} with the lock's digest {digest[:12]} in {models_dir}")
    layer = [x for x in json.loads(man.read_text())["layers"] if x["mediaType"] == "application/vnd.ollama.image.model"]
    if len(layer) != 1:
        raise SystemExit(f"REFUSED: {man} names {len(layer)} model layers")
    blob = models_dir / "blobs" / layer[0]["digest"].replace(":", "-")
    if not blob.exists() or blob.stat().st_size != layer[0]["size"]:
        raise SystemExit(f"REFUSED: {blob} missing or not {layer[0]['size']} bytes")
    return blob, {"manifest_blob": str(man), "manifest_sha256": digest, "model_layer": layer[0]["digest"],
                  "model_layer_size": layer[0]["size"]}


# llama.cpp's pre-tokenizer for tokenizer.ggml.pre "default" (LLAMA_VOCAB_PRE_TYPE_DEFAULT, BPE): these four
# expressions applied in turn, then the byte-level map. It is checked, not trusted: `count` refuses unless the
# tokenizer reproduces Ollama's counts on every stored row it rebuilds.
DEFAULT_PRE = (r"[\p{P}\$\+<=>\^~\|]+",
               r"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)",
               r"\p{N}+",
               r"[0-9][0-9][0-9]")


def tokenizer(kv: dict):
    from tokenizers import Regex, Tokenizer, models, pre_tokenizers
    if kv.get("tokenizer.ggml.model") != "gpt2" or kv.get("tokenizer.ggml.pre") != "default":
        raise SystemExit(f"REFUSED: tokenizer {kv.get('tokenizer.ggml.model')}/{kv.get('tokenizer.ggml.pre')}, "
                         "not the gpt2/default this counter rebuilds")
    vocab = {t: i for i, t in enumerate(kv["tokenizer.ggml.tokens"])}
    merges = [tuple(m.split(" ", 1)) for m in kv["tokenizer.ggml.merges"]]
    tk = Tokenizer(models.BPE(vocab=vocab, merges=merges, ignore_merges=False))
    tk.pre_tokenizer = pre_tokenizers.Sequence([pre_tokenizers.Split(Regex(r), behavior="isolated") for r in DEFAULT_PRE]
                                               + [pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False)])
    return tk


def validate(tk, limit: int | None = None) -> dict:
    """Ollama's prompt_eval_count minus this tokenizer's count, on S440's 214 calls and on every S18e arm B, C and D
    call whose prompt S18e's own code rebuilds (C and D: the whole-paper blocks). Exactly one value is allowed."""
    import S18e_judge_evidence_devstral as X
    import S376_judge_calibration as S376
    n = lambda p: len(tk.encode(p, add_special_tokens=False).ids)   # noqa: E731
    items = {x["answer_key"]: x for x in S376.answers_and_key()}
    s440 = Counter()
    for r in map(json.loads, S440_LEDGER.open()):
        x = items[r["answer_key"]]
        s440[r["prompt_tokens"] - n(J.build_prompt(x["question"], x["expected"], x["concepts"], x["answer"],
                                                   x["answerable"], None))] += 1
    S = X.load()
    rows = [json.loads(line) for line in S18E_LEDGER.open()][:limit]
    blocks = X.build_blocks(S, {r["evidence_source_qid"] for r in rows if r.get("evidence_mode") == "full"}, 0, None)
    s18e, skipped = Counter(), Counter()
    for r in rows:
        if r["arm"] not in ("B", "C", "D") or (r["arm"] != "B" and r.get("evidence_mode") != "full"):
            skipped["not rebuilt (arm A or B2, or excerpts)"] += 1
            continue
        p = X.prompt(S, X.v22(r["question_id"], S["v2"]), S["answers"][(r["question_id"], r["config"])],
                     "" if r["arm"] == "B" else blocks[r["evidence_source_qid"]]["text"])
        if sha(p) != r["prompt_sha256"]:
            skipped["prompt not rebuilt byte for byte (key changed since)"] += 1
            continue
        s18e[r["prompt_tokens"] - n(p)] += 1
    offsets = set(s440) | set(s18e)
    out = {"s440": {str(k): v for k, v in s440.items()}, "s18e": {str(k): v for k, v in s18e.items()},
           "s18e_skipped": dict(skipped), "rows": sum(s440.values()) + sum(s18e.values()),
           "offset": offsets.pop() if len(offsets) == 1 else None}
    out["passed"] = out["offset"] is not None and sum(s440.values()) == 214 and sum(s18e.values()) >= 1000
    return out


def cmd_count(a) -> int:
    lock = load()
    model = lock.d["judge"]["model"]
    call = lock.ollama(model, role="judge")
    num_ctx, num_predict = call.options["num_ctx"], call.options["num_predict"]
    blob, prov = model_blob(model, lock.d["models"][model]["digest"], a.models_dir)
    t0 = time.time()
    tk = tokenizer(gguf_kv(blob))
    v = validate(tk)
    print(f"TOKENIZER CHECK: {v['rows']} stored devstral calls; Ollama's count minus this tokenizer's: S440 {v['s440']}, "
          f"S18e {v['s18e']}; {'PASSED' if v['passed'] else 'NOT PASSED'}", flush=True)
    if not v["passed"]:
        print("COUNT REFUSED: the tokenizer does not reproduce Ollama's counts; nothing written")
        return 1
    w = work(a.g1, a.g1r15, a.store)
    gate(w)
    off = v["offset"]
    n = lambda p: len(tk.encode(p, add_special_tokens=False).ids) + off   # noqa: E731
    btok, rows = {}, []
    for c in w["calls"]:
        x = c["x"]
        if c["prompt"] is None:
            rows.append({"arm": c["arm"], "answer_key": x["answer_key"], "unit": c["unit"], "status": "no_answer"})
            continue
        if x["answer_key"] not in btok:
            btok[x["answer_key"]] = n(JP.safe_prompts(x)[0])
        t = n(c["prompt"])
        fit = "fits" if t + num_predict <= num_ctx else "fits_context_only" if t < num_ctx else "too_long"
        rows.append({"arm": c["arm"], "answer_key": x["answer_key"], "question_id": x["question_id"],
                     "config": x["config"], "unit": c["unit"], "evidence_source_qid": c["src"],
                     "prompt_sha256": sha(c["prompt"]), "prompt_chars": len(c["prompt"]), "tokens": t,
                     "b_tokens": btok[x["answer_key"]], "fit": fit})
    called = [r for r in rows if r.get("tokens")]
    per_arm = {}
    for arm in ARMS:
        rs = [r for r in called if r["arm"] == arm]
        top = max(rs, key=lambda r: r["tokens"])
        per_arm[arm] = {"calls": len(rs), "fit": dict(Counter(r["fit"] for r in rs)), "max_tokens": top["tokens"],
                        "max_at": top["answer_key"],    # the median of an even count is the mean of the two middle values (defect 7)
                        "median_tokens": statistics.median(r["tokens"] for r in rs)}
    answers_all = defaultdict(set)
    for r in called:
        answers_all[r["answer_key"]].add(r["fit"])
    both = sum(1 for v_ in answers_all.values() if v_ == {"fits"})
    q_over = sorted({r["question_id"] for r in called if r["fit"] != "fits"})
    res = {"_provenance": {"script": "experiments/scorers/judge_evidence.py count", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "lock_sha256": lock.sha256, "model": model, "tokenizer_source": prov,
                           "code": code_identity(), "template_sha256": w["template_sha256"],
                           "inputs": {**inputs_identity(a), "s18e_ledger": file_sha(S18E_LEDGER),
                                      "s440_ledger": file_sha(S440_LEDGER)},
                           "wall_s": round(time.time() - t0, 1)},
           "tokenizer_check": v, "num_ctx": num_ctx, "num_predict": num_predict,
           "fit_rule": "fits: tokens + num_predict <= num_ctx; fits_context_only: tokens < num_ctx; too_long: otherwise",
           "answers": len(w["items"]), "no_answer": sum(1 for x in w["items"] if not JP.answered(x)),
           "answers_both_arms_fit": both, "per_arm": per_arm, "questions_with_a_prompt_over": q_over,
           "donors": w["donors"], "donor_notes": w["notes"],
           "gate": [{"check": c0, "pass": ok, "note": nt} for c0, ok, nt in w["checks"]], "rows": rows}
    (a.dest_dir / "S18f_tokens.json").write_text(json.dumps(res, indent=1) + "\n")
    L = [f"# S18f token count: S18e's arms C and D on G1's draw-1 answerable answers, whole papers ({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"Tokenizer: the locked {model} GGUF ({prov['model_layer'][:19]}), llama.cpp's default pre-tokenizer. It reproduces "
         f"Ollama's prompt_eval_count on {v['rows']} stored calls with one constant, {off} tokens (S440 {v['s440']}; "
         f"S18e {v['s18e']}).", "",
         f"{res['answers']} answers, {res['no_answer']} with no answer (no call). Lock: num_ctx {num_ctx:,}, num_predict "
         f"{num_predict:,}. {res['fit_rule']}.", "",
         "| arm | calls | fits | fits context only | too long | median tokens | max tokens | at (strategy, question) |", "|---|---|---|---|---|---|---|---|"]
    for arm, p in per_arm.items():
        L.append(f"| {arm} | {p['calls']} | {p['fit'].get('fits', 0)} | {p['fit'].get('fits_context_only', 0)} | "
                 f"{p['fit'].get('too_long', 0)} | {num(p['median_tokens'])} | {p['max_tokens']:,} | "
                 f"{' '.join(p['max_at'].split('|')[1:3])} |")
    L += ["", f"Answers whose C and D prompts both fit: {both} of {len(answers_all)} answered. Questions with a prompt "
          f"that does not fit: {q_over or 'none'}.",
          f"Donors outside the 86 (S18's order holds 88 questions): {w['notes']['donors_outside_the_86'] or 'none'}; "
          f"donors that would differ if chosen among the 86 only: {w['notes']['donor_differs_if_chosen_among_the_86'] or 'none'}.",
          "", "Full rows: findings/recompute/S18f_tokens.json."]
    (a.dest_dir / "S18f_tokens.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


# ---------------------------------------------------------------- units, plan

def units(qids: list[str]) -> list[tuple[str, list[str]]]:
    out = defaultdict(list)
    for q in qids:
        out[unit_of(q, qids)].append(q)
    return sorted(out.items())


def latest_rows(f: Path, mine: dict, run_sha: str) -> dict:
    """ident -> the latest row of each call in mine (ident -> item_sha256); a row of one of them under another item
    or run sha256 refuses (one file, one definition)."""
    latest = {}
    for d in JP.read_rows(f):
        k = ident(d)
        if k not in mine:
            continue
        if d.get("item_sha256") != mine[k] or d.get("run_sha256") != run_sha:
            raise SystemExit(f"REFUSED: {f} already holds {k} judged on another answer, paper, lock or code; use a new --out")
        latest[k] = d
    return latest


def check_state(check_dir: Path, lock) -> dict:
    f = check_dir / "repro_check.json"
    if not f.exists():
        return {"file": str(f), "exists": False}
    c = json.loads(f.read_text())
    return {"file": str(f), "exists": True, "passed": c.get("passed"), "n": c.get("n"),
            "same_lock": c.get("lock_sha256") == lock.sha256, "same_judge_code": c.get("code") == JP.code_identity(),
            "server": c.get("server")}


def estimate(calls: list[dict], tok: dict | None) -> dict | None:
    """Hours, UNVERIFIED: S18e's measured wall times (10 and 11 October, four devstral servers sharing the Studio,
    num_ctx 65,536, prompts up to 36,000 tokens) fitted as cold s = a + b * tokens (the first call of a question and
    arm) and warm s (the next five, the prefix reused), applied to this job's exact token counts (`count`)."""
    if not tok:
        return None
    import numpy as np
    rs = sorted((json.loads(line) for line in S18E_LEDGER.open()), key=lambda r: (r["port"], r["at"]))
    prev, cold, warm = {}, [], []
    for r in rs:
        if r["arm"] in ("C", "D"):
            g = (r["arm"], r["question_id"])
            (warm if prev.get(r["port"]) == g else cold).append((r["prompt_tokens"], r["wall_s"]))
            prev[r["port"]] = g
    cb = np.polyfit([t for t, _ in cold], [s for _, s in cold], 1)
    warm_s = float(np.median([s for _, s in warm]))
    by = {(r["arm"], r["answer_key"]): r["tokens"] for r in tok["rows"] if r.get("tokens")}

    def seconds(cs: list[dict]) -> tuple[float, int]:
        """cs in the order judged after one fresh load: the first call of a (question, arm) cold, the rest warm."""
        total, seen, n = 0.0, set(), 0
        for c in cs:
            t = by.get((c["arm"], c["x"]["answer_key"]))
            if t is None:
                continue
            g = (c["arm"], c["x"]["question_id"])
            total += warm_s if g in seen else float(cb[1] + cb[0] * t)
            seen.add(g)
            n += 1
        return total, n
    main_s, n = seconds(calls)
    # Each unit that judges ends with its recheck (cmd_run, recheck): a second fresh load, then the unit's first
    # RECHECK_N calls with a prompt judged again, in unit order (review defect 5).
    rc_s, rc_n, loads = 0.0, 0, 0
    for u in sorted({c["unit"] for c in calls}):
        picked = [c for c in calls if c["unit"] == u and c["prompt"] is not None][:RECHECK_N]
        if picked:
            s, k = seconds(picked)
            rc_s, rc_n, loads = rc_s + s, rc_n + k, loads + 2
    return {"calls": n, "recheck_calls": rc_n, "fresh_loads": loads,
            "hours_one_server": round((main_s + rc_s) / 3600, 1), "hours_without_rechecks": round(main_s / 3600, 1),
            "cold_fit_s": [round(float(cb[1]), 1), round(float(cb[0]), 5)], "warm_median_s": round(warm_s, 1),
            "basis": "S18e_devstral.jsonl wall_s (four servers sharing the Studio, 10-11 October), applied to the judged "
            "calls and the rechecks; the fresh loads' seconds are not counted; prompts here reach further than S18e's "
            f"{max(t for t, _ in cold + warm):,} tokens, so the cold fit is extrapolated: UNVERIFIED"}


def cmd_units(a) -> int:
    for u, qs in units(answerable_ids()):
        print(f"{u}\t{len(qs)}\t{','.join(qs)}")
    return 0


def cmd_plan(a) -> int:
    lock = load()
    call = lock.ollama(lock.d["judge"]["model"], role="judge")
    run_sha = run_identity(lock, call)
    w = work(a.g1, a.g1r15, a.store)
    gate(w)
    chk = check_state(a.check_dir, lock)
    print(json.dumps({"job": "S18f", "lock_sha256": lock.sha256, "judge": call.model, "run_sha256": run_sha,
                      "options": call.options, "check": chk}), flush=True)
    tot = Counter()
    rows_out = []
    for u, qs in units(w["qids"]):
        if a.unit and u != a.unit:
            continue
        cs = [c for c in w["calls"] if c["unit"] == u]
        f = a.out / "judge" / u / "judge_evidence.jsonl"
        latest = latest_rows(f, {call_ident(c): c["item_sha256"] for c in cs}, run_sha)
        done = sum(1 for c in cs if (latest.get(call_ident(c)) or {}).get("status") in FINAL)
        todo = [c for c in cs if (latest.get(call_ident(c)) or {}).get("status") not in FINAL]
        row = {"unit": u, "questions": len(qs), "calls_planned": len(cs), "done": done, "to_do": len(todo),
               "model_calls": sum(1 for c in todo if c["prompt"] is not None),
               "no_answer": sum(1 for c in todo if c["prompt"] is None),
               "prompt_chars": sum(len(c["prompt"]) for c in todo if c["prompt"] is not None),
               "claim": (owner(a.out, u) or {}).get("worker")}
        print(json.dumps(row), flush=True)
        rows_out.append(row)
        for k in ("calls_planned", "done", "to_do", "model_calls", "no_answer", "prompt_chars"):
            tot[k] += row[k]
    print(json.dumps({"total": dict(tot)}))
    tok_f = a.dest_dir / "S18f_tokens.json"
    tok = json.loads(tok_f.read_text()) if tok_f.exists() else None
    if tok is not None:
        cur = {(c["arm"], c["x"]["answer_key"]): sha(c["prompt"]) for c in w["calls"] if c["prompt"] is not None}
        old = {(r["arm"], r["answer_key"]): r["prompt_sha256"] for r in tok["rows"] if r.get("tokens")}
        if cur != old:
            print(f"NOTE: {tok_f} counts other prompts than these (run `count` again); its counts are not used")
            tok = None
    est = estimate(w["calls"], tok)
    if a.report:
        res = {"_provenance": {"script": "experiments/scorers/judge_evidence.py plan --report", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                               "lock_sha256": lock.sha256, "run_sha256": run_sha, "code": code_identity(),
                               "template_sha256": w["template_sha256"], "inputs": inputs_identity(a)},
               "gate": [{"check": c0, "pass": ok, "note": nt} for c0, ok, nt in w["checks"]],
               "answers": len(w["items"]), "from_g1r15": sorted(x["answer_key"] for x in w["items"] if x["from"] == "G1R15"),
               "arm_B": "S3's call (a), reused: the prompt equals it byte for byte for every answered answer (G4)",
               "units": rows_out, "total": dict(tot), "check": chk, "estimate": est,
               "donors": w["donors"], "donor_notes": w["notes"],
               "blocks": {k: {kk: vv for kk, vv in v.items() if kk != "text"} for k, v in w["blocks"].items()}}
        (a.dest_dir / "S18f_plan.json").write_text(json.dumps(res, indent=1) + "\n")
        L = [f"# S18f plan: arms C and D on G1's draw-1 answerable answers, whole papers, under the lock ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Gate passed ({len(w['checks'])} checks; no model call). {len(w['items'])} answers; {tot['model_calls']} model "
             f"calls to make in {len(rows_out)} units ({tot['done']} done); {tot['no_answer']} no-answer rows (no call). "
             f"Arm B is S3's (a), not judged here.", "",
             "| unit | questions | calls to make | done | prompt characters |", "|---|---|---|---|---|"]
        L += [f"| {r['unit']} | {r['questions']} | {r['model_calls']} | {r['done']} | {r['prompt_chars']:,} |" for r in rows_out]
        L += ["", f"Estimate (UNVERIFIED): {est['hours_one_server']} h on one server for {est['calls']} judged calls and "
              f"{est['recheck_calls']} recheck calls after {est['fresh_loads']} fresh loads ({est['hours_without_rechecks']} h "
              f"without the rechecks; {est['basis']})." if est else
              "No estimate: run `count` first.", f"Check: {chk}."]
        (a.dest_dir / "S18f_plan.md").write_text("\n".join(L) + "\n")
        print("\n".join(L))
    print(f"S18F PLAN: {len(rows_out)} units; {tot['model_calls']} model calls and {tot['no_answer']} no-answer rows to "
          f"write, {tot['done']} done; check " + ("passed" if chk.get("passed") else "not passed" if chk["exists"] else "not run yet")
          + (f"; {est['recheck_calls']} recheck calls after {est['fresh_loads']} fresh loads; about "
             f"{est['hours_one_server']} h on one server (UNVERIFIED)" if est else ""))
    return 0


def owner(out: Path, unit: str) -> dict | None:
    f = out / "claims" / unit / "owner.json"
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return {"worker": "?"} if f.parent.exists() else None


# ---------------------------------------------------------------- run

def judge_row(base: str, call, c: dict, log: Path, blocks: dict) -> dict:
    x = c["x"]
    b = blocks[c["src"]]
    row = {"arm": c["arm"], "run_id": x["run_id"], "config": x["config"], "question_id": x["question_id"],
           "draw": x["draw"], "answer_key": x["answer_key"], "from": x["from"], "key_hash": x["key_hash"],
           "item_sha256": c["item_sha256"], "b_item_sha256": x["item_sha256"], "b_prompt_sha256": c["b_prompt_sha256"],
           "evidence": KIND[c["arm"]], "evidence_source_qid": c["src"], "evidence_files": b["files"],
           "evidence_sha256": b["sha256"], "evidence_chars": b["chars"]}
    t0 = time.time()
    if c["prompt"] is None:
        row.update(status="no_answer", error=x["gen_error"] or "no answer stored", scores=None)
    else:
        ids = [{"source": f, "chunk_idx": None, "whole_paper": True} for f in b["files"]]
        res = JP.judge_call(base, call, c["prompt"], True, ids, log,
                            {"answer": x["answer_key"], "variant": f"S18f_{c['arm']}", "item_sha256": c["item_sha256"]})
        row.update(res)
    row["faithfulness"] = (row.get("scores") or {}).get("faithfulness")
    row["wall_s"] = round(time.time() - t0, 1)
    row["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return row


def cmd_run(a) -> int:
    base = a.base.rstrip("/")
    lock0 = load()
    check = JP.require_check(a.check_dir, lock0, base, a.machine, a.binary)
    call0 = lock0.ollama(lock0.d["judge"]["model"], role="judge")
    run_sha = run_identity(lock0, call0)
    w = work(a.g1, a.g1r15, a.store)
    gate(w)
    cs = [c for c in w["calls"] if c["unit"] == a.unit]
    if not cs:
        raise SystemExit(f"REFUSED: no unit {a.unit!r} (units: {', '.join(u for u, _ in units(w['qids']))})")
    out = a.out / "judge" / a.unit
    out.mkdir(parents=True, exist_ok=True)
    JP.hold_writer(out)
    res_f, log = out / "judge_evidence.jsonl", out / "judge_evidence_calls.jsonl"
    mine = {call_ident(c): c["item_sha256"] for c in cs}
    latest = latest_rows(res_f, mine, run_sha)
    todo = [c for c in cs if (latest.get(call_ident(c)) or {}).get("status") not in FINAL][: a.limit]
    if not todo:
        return finish(out, res_f, mine, run_sha, None)
    lock, model, call, fl = JP.start(a, out, "run")
    if lock.sha256 != lock0.sha256 or run_identity(lock, call) != run_sha:
        raise SystemExit("REFUSED: the lock or the code changed while the run started")
    header = {"_provenance": {"script": "experiments/scorers/judge_evidence.py run", "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "inputs": [str(a.g1), str(a.g1r15), str(a.store), str(DOCS), str(MANIFEST)]},
              "unit": a.unit, "model": model, "model_digest": call.digest, "lock_sha256": lock.sha256,
              "options": call.options, "fields": call.fields, "system_prompt_sha256": call.system and sha(call.system),
              "base": base, "machine_identity": fl["machine_identity"], "run_sha256": run_sha, "code": code_identity(),
              "check": {k: check[k] for k in ("n", "equal_scores", "identical_text", "lock_sha256", "model_digest")},
              "calls": len(cs), "to_do": len(todo), "template_sha256": w["template_sha256"]}
    with (out / "judge_evidence_headers.jsonl").open("a") as fh:
        fh.write(json.dumps(header) + "\n")
    print(f"S18f {a.unit}: {len(cs)} calls, {len(cs) - len(todo)} done, {len(todo)} to judge with {model}", flush=True)
    for c in todo:
        row = judge_row(base, call, c, log, w["blocks"])
        row["lock_sha256"], row["run_sha256"] = lock.sha256, run_sha
        with res_f.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['at']} {row['arm']} {row['config']:13s} {row['question_id']:28s} {row['status']} "
              f"F={row['faithfulness']} prompt {row.get('prompt_tokens')} {row['wall_s']} s", flush=True)
    rechecked = None if a.no_recheck else recheck(a, base, cs, res_f, out, run_sha, w["blocks"])
    return finish(out, res_f, mine, run_sha, rechecked)


def recheck(a, base: str, cs: list[dict], res_f: Path, out: Path, run_sha: str, blocks: dict) -> dict:
    """judge_passages.recheck's rule for this unit: another fresh load, the first RECHECK_N rows that reached the
    model judged again; passes only if every status and score is the same."""
    lock, model, call, fl = JP.start(a, out, "recheck")
    latest = {ident(d): d for d in JP.read_rows(res_f) if d.get("run_sha256") == run_sha}
    picked = [c for c in cs if c["prompt"] is not None and call_ident(c) in latest][:RECHECK_N]
    n = eq = 0
    for c in picked:
        prev = latest[call_ident(c)]
        row = judge_row(base, call, c, out / "judge_evidence_recheck_calls.jsonl", blocks)
        same = row["status"] == prev["status"] and row.get("scores") == prev.get("scores")
        n, eq = n + 1, eq + same
        with (out / "judge_evidence_recheck.jsonl").open("a") as fh:
            fh.write(json.dumps({"ident": list(call_ident(c)), "item_sha256": c["item_sha256"], "run_sha256": run_sha,
                                 "equal": same, "now": row.get("scores"), "written": prev.get("scores"),
                                 "at": row["at"]}) + "\n")
    res = {"n": n, "equal": eq, "passed": (eq == n) if n else None, "run_sha256": run_sha, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (out / "judge_evidence_recheck_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"RECHECK: {eq} of {n} calls give the same status and scores after a fresh load; "
          f"{ {True: 'PASSED', False: 'NOT PASSED', None: 'nothing to recheck'}[res['passed']] }", flush=True)
    return res


def finish(out: Path, res_f: Path, mine: dict, run_sha: str, rechecked: dict | None) -> int:
    rows = {ident(d): d for d in JP.read_rows(res_f) if d.get("run_sha256") == run_sha and ident(d) in mine}
    summary = {"_provenance": {"script": "experiments/scorers/judge_evidence.py run", "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
               "run_sha256": run_sha, "calls": len(mine), "rows": len(rows),
               "to_do": sum(1 for k in mine if (rows.get(k) or {}).get("status") not in FINAL),
               "status": {arm: dict(Counter(d["status"] for k, d in rows.items() if k[0] == arm)) for arm in ARMS},
               "recheck": rechecked}
    (out / "judge_evidence_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"SUMMARY: {summary['status']}; {summary['to_do']} of {len(mine)} calls not final", flush=True)
    if rechecked is not None and rechecked["passed"] is False:
        print(f"S18F UNIT NOT PASSED: the recheck ({rechecked['equal']} of {rechecked['n']} equal)", flush=True)
        return 1
    print("S18F UNIT DONE" if summary["to_do"] == 0 else f"S18F UNIT ENDED: {summary['to_do']} calls not final "
          "(errors, length, unparseable: tried again on resume)", flush=True)
    return 0


# ---------------------------------------------------------------- collect, analyze

def cmd_collect(a) -> int:
    merged, src, bad = {}, {}, []
    for o in a.out:
        for f in sorted(o.glob("judge/*/judge_evidence.jsonl")):
            for d in JP.read_rows(f):
                k = ident(d)
                if k in merged and (merged[k]["item_sha256"], merged[k]["run_sha256"]) != (d["item_sha256"], d["run_sha256"]):
                    bad.append(f"{k}: two definitions ({src[k]}, {f})")
                    continue
                if k in merged and merged[k]["status"] in FINAL and d["status"] in FINAL and merged[k].get("scores") != d.get("scores") and src[k] != str(f):
                    bad.append(f"{k}: scores differ between {src[k]} and {f}")
                    continue
                if k not in merged or src[k] == str(f) or (d["status"] in FINAL and merged[k]["status"] not in FINAL):
                    merged[k], src[k] = d, str(f)
    runs = Counter(d["run_sha256"] for d in merged.values())
    if len(runs) > 1:
        bad.append(f"the rows carry {len(runs)} run_sha256 values (another lock or code)")
    if bad:
        print(json.dumps({"problems": bad[:20]}))
        print(f"COLLECT REFUSED: {len(bad)} problems, first: {bad[0]}")
        return 1
    a.dest.parent.mkdir(parents=True, exist_ok=True)
    with a.dest.open("w") as fh:
        for k in sorted(merged, key=lambda t: tuple(map(str, t))):
            fh.write(json.dumps(merged[k], ensure_ascii=False) + "\n")
    st = {arm: dict(Counter(d["status"] for k, d in merged.items() if k[0] == arm)) for arm in ARMS}
    side = {"_provenance": {"script": "experiments/scorers/judge_evidence.py collect", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "inputs": [str(o) for o in a.out]}, "rows": len(merged), "run_sha256": next(iter(runs), None),
            "status": st}
    a.dest.with_name(a.dest.name + ".json").write_text(json.dumps(side, indent=1) + "\n")
    print(f"COLLECTED: {len(merged)} rows into {a.dest}; run_sha256 {str(side['run_sha256'])[:12]}; {st}")
    return 0


def b_rows(w: dict, s3_file: Path, s3_run: str) -> tuple[dict, list, Counter, Counter]:
    """Arm B from S3's rows: for each of this job's answers, S3's latest row of the same (run_id, config, question,
    draw) must carry the same item_sha256, judge_passages's run_sha256 under this lock (lock, judge code, options,
    system prompt) and, for (a), the prompt_sha256 of this job's arm B. Returns (by, problems, left out, counts)."""
    want = {(x["run_id"], x["config"], x["question_id"], x["draw"]): x for x in w["items"]}
    b_sha = {(c["x"]["run_id"], c["x"]["config"], c["x"]["question_id"], c["x"]["draw"]): c["b_prompt_sha256"]
             for c in w["calls"]}
    latest = {}
    for d in JP.read_rows(s3_file):
        if JP.ident(d) in want:
            latest[JP.ident(d)] = d
    by, bad, why, n = {}, [], Counter(), Counter()
    for k, d in latest.items():
        x = want[k]
        n["rows"] += 1
        if d.get("item_sha256") != x["item_sha256"] or d.get("run_sha256") != s3_run:
            bad.append(f"S3 row {k}: another answer, lock or judge code")
            continue
        if d["a"]["status"] != "ok":
            why[f"B {d['a']['status']}"] += 1
            continue
        if d["a"].get("prompt_sha256") != b_sha[k]:
            bad.append(f"S3 row {k}: its (a) prompt is not arm B's")
            continue
        n["same_prompt"] += 1
        by[("B", x["question_id"], x["config"])] = {"parsed": d["a"]["scores"]}
    n["missing"] = len(want) - n["rows"]
    n["missing_keys"] = sorted(set(want) - set(latest))
    return by, bad, why, n


def cmd_reuse(a) -> int:
    """Whether S3's rows can stand as arm B: every S3 row of this job's answers checked as b_rows checks it."""
    lock = load()
    call = lock.ollama(lock.d["judge"]["model"], role="judge")
    w = work(a.g1, a.g1r15, a.store)
    gate(w)
    by, bad, why, n = b_rows(w, a.s3, JP.run_identity(lock, call))
    print(json.dumps({"s3_rows": n["rows"], "same_prompt_and_run": n["same_prompt"], "not_yet_judged": n["missing"],
                      "left_out": dict(why), "problems": bad[:20]}))
    print(("REUSE " + ("REFUSED" if bad else "PASSED")) + f": {n['same_prompt']} of {n['rows']} S3 rows of this job's "
          f"{len(w['items'])} answers carry arm B's prompt, item and run sha256; {n['missing']} not judged by S3 yet; "
          f"{len(bad)} problems")
    return 1 if bad else 0


def cmd_analyze(a) -> int:
    """B from S3's collect (G1 out with out_g1r15 replacing, s3_guard.py collect), C and D from this job's collect;
    S18c's contrasts on the answers judged ok in all three arms with all four scores."""
    import S18c_analyze as S18c
    lock = load()
    call = lock.ollama(lock.d["judge"]["model"], role="judge")
    w = work(a.g1, a.g1r15, a.store)
    gate(w)
    s3_run = JP.run_identity(lock, call)
    s18f_run = run_identity(lock, call)
    by, bad, why, nb = b_rows(w, a.s3, s3_run)
    # An answer with no row in an arm leaves the analysed set; it is counted, and analyze refuses unless --partial
    # (review defect 4): a partial look says so in its counts, never "left out: none".
    if nb["missing"]:
        why["B not judged by S3"] += nb["missing"]
    want = {call_ident(c): c for c in w["calls"]}
    seen = set()
    for d in JP.read_rows(a.collect):
        k = ident(d)
        if k not in want:
            continue
        if d["item_sha256"] != want[k]["item_sha256"] or d["run_sha256"] != s18f_run:
            bad.append(f"S18f row {k}: another answer, paper, lock or code")
            continue
        seen.add(k)
        if d["status"] != "ok":
            why[f"{d['arm']} {d['status']}"] += 1
            continue
        by[(d["arm"], d["question_id"], d["config"])] = {"parsed": d["scores"]}
    for k in set(want) - seen:
        why[f"{k[0]} not judged by S18f"] += 1
    missing = sum(v for k, v in why.items() if k.endswith("not judged by S3") or k.endswith("not judged by S18f"))
    if missing and not a.partial:
        bad.append(f"{missing} rows missing ({ {k: v for k, v in why.items() if 'not judged' in k} }); "
                   "collect them, or pass --partial for an interim look")
    if bad:
        print(json.dumps({"problems": bad[:20]}))
        print(f"ANALYZE REFUSED: {len(bad)} problems, first: {bad[0]}")
        return 1
    full = lambda v: all(isinstance(v["parsed"].get(dim), int) for dim in S18c.DIMS)   # noqa: E731
    keys = [(x["question_id"], x["config"]) for x in w["items"]
            if all(((arm, x["question_id"], x["config"]) in by and full(by[(arm, x["question_id"], x["config"])]))
                   for arm in ("B", "C", "D"))]
    contrasts = [S18c.compare(by, ax, ay, keys, lab) for ax, ay, lab in
                 (("C", "B", "evidence effect, total"), ("D", "B", "irrelevant-text effect: same bulk, wrong paper"),
                  ("C", "D", "PRIMARY: evidence content effect"))]
    share = {arm: round(sum(by[(arm,) + k]["parsed"]["faithfulness"] == 5 for k in keys) / len(keys), 4) if keys else None
             for arm in ("B", "C", "D")}
    prior = json.loads(S18E_RESULTS.read_text())      # S18 as printed and S18e, read, not typed (review defect 8)
    res = {"_provenance": {"script": "experiments/scorers/judge_evidence.py analyze", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "inputs": {"s3": [str(a.s3), file_sha(a.s3)], "collect": [str(a.collect), file_sha(a.collect)],
                                      "s18e_results": [str(S18E_RESULTS.relative_to(ROOT)), file_sha(S18E_RESULTS)],
                                      **inputs_identity(a)},
                           "code": code_identity(), "lock_sha256": lock.sha256, "s3_run_sha256": s3_run,
                           "s18f_run_sha256": s18f_run},
           "partial": bool(missing), "answers": len(w["items"]), "analysed": len(keys), "questions": len({q for q, _ in keys}),
           "left_out": dict(why), "share5_faithfulness": share, "contrasts": contrasts}
    (a.dest_dir / "S18f_results.json").write_text(json.dumps(res, indent=1) + "\n")
    L = [f"# S18f results: devstral-small-2:24b under the lock, G1 draw 1, whole papers ({time.strftime('%Y-%m-%d %H:%M')})", "",
         *([f"PARTIAL (--partial): {missing} rows not judged yet; not a result."] if missing else []),
         f"{len(keys)} answers of {len(w['items'])} judged ok with four scores in all three arms ({res['questions']} questions); "
         f"left out by arm and status: {dict(why) or 'none'}. B is S3's (a).", "",
         "| contrast | n | 5/5 x | 5/5 y | difference, points | 95% CI (question bootstrap) | TOST equivalent at 5 |",
         "|---|---|---|---|---|---|---|"]
    for c in contrasts:
        f = c["dims"]["faithfulness"]
        if f.get("n"):
            L.append(f"| {c['contrast']} ({c['label']}) | {f['n']} | {100 * f['share5_x']:.2f}% | {100 * f['share5_y']:.2f}% | "
                     f"{f['share5_diff_pp']} | {f['share5_diff_ci95_pp']} | {(f.get('tost') or {}).get('equivalent')} |")
    p18, s5, aset = prior["s18_printed_qwen_v1"], prior["share5_faithfulness"], prior["analysis_set"]
    ce = {c["contrast"]: c["dims"]["faithfulness"] for c in prior["contrasts"]}
    L += ["", f"From {S18E_RESULTS.relative_to(ROOT)}: S18 as printed (qwen3-coder:30b, v1 key, {p18['n_answers']} answers): "
          f"C {p18['share5_C']}%, B {p18['share5_B']}%, D {p18['share5_D']}%; C vs B {p18['C vs B'][0]} "
          f"[{p18['C vs B'][1]}, {p18['C vs B'][2]}]; C vs D {p18['C vs D'][0]} [{p18['C vs D'][1]}, {p18['C vs D'][2]}]. "
          f"S18e (devstral, {aset['answers']} answers of {aset['questions']} questions, excerpts above 28,000 tokens): "
          + ", ".join(f"{arm} {100 * s5[arm]['share5']:.2f}%" for arm in ("C", "B", "D"))
          + "; " + "; ".join(f"{k} {ce[k]['share5_diff_pp']} {ce[k]['share5_diff_ci95_pp']}" for k in ("C vs B", "C vs D")
                              if k in ce) + ".",
          "", "Full statistics: findings/recompute/S18f_results.json."]
    (a.dest_dir / "S18f_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = {n: sub.add_parser(n) for n in ("count", "plan", "units", "run", "collect", "reuse", "analyze")}
    for n in ("count", "plan", "run", "reuse", "analyze"):
        ps[n].add_argument("--g1", type=Path, default=G1_DEFAULT, help="G1's frozen copy (K1's ~/k1_inputs)")
        ps[n].add_argument("--g1r15", type=Path, default=G1R15_DEFAULT, help="G1R15's copy (snap_s3_inputs.sh)")
        ps[n].add_argument("--store", type=Path, default=STORE_DEFAULT, help="the store G1's passages resolve through")
    ps["count"].add_argument("--models-dir", type=Path, default=Path("~/.ollama/models").expanduser())
    for n in ("count", "plan", "analyze"):
        ps[n].add_argument("--dest-dir", type=Path, default=RECOMPUTE, help="where its S18f_* files go (the checks: a temp dir)")
    for n in ("plan", "units", "run"):
        ps[n].add_argument("--out", type=Path, default=ROOT / "findings/recompute/S18f_runs/out")
    ps["plan"].add_argument("--check-dir", type=Path, required=True)
    ps["plan"].add_argument("--unit")
    ps["plan"].add_argument("--report", action="store_true", help="also write findings/recompute/S18f_plan.{json,md}")
    r = ps["run"]
    r.add_argument("--base", required=True, help="the judge's server; no default, as run_s18f.sh has no default port "
                   "(review defect 2: 11434 is the Mentori app's Ollama)")
    r.add_argument("--log", required=True, type=Path)
    r.add_argument("--binary", required=True, type=Path)
    r.add_argument("--machine", required=True, choices=["macos", "beelink"])
    r.add_argument("--check-dir", required=True, type=Path)
    r.add_argument("--unit", required=True)
    r.add_argument("--limit", type=int)
    r.add_argument("--no-recheck", action="store_true")
    ps["collect"].add_argument("--out", type=Path, nargs="+", required=True)
    ps["collect"].add_argument("--dest", type=Path, required=True)
    ps["analyze"].add_argument("--collect", type=Path, required=True, help="this job's collect")
    ps["analyze"].add_argument("--partial", action="store_true", help="analyse while rows are missing (counted, marked PARTIAL)")
    for n in ("reuse", "analyze"):
        ps[n].add_argument("--s3", type=Path, required=True, help="S3's G1 collect (s3_guard.py collect --replace out_g1r15)")
    a = ap.parse_args(argv)
    return {"count": cmd_count, "plan": cmd_plan, "units": cmd_units, "run": cmd_run, "collect": cmd_collect,
            "reuse": cmd_reuse, "analyze": cmd_analyze}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
