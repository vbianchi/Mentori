#!/usr/bin/env python3
"""S18e - the judge-evidence experiment (S18) re-judged by devstral-small-2:24b against the judge's current key
(S373.KEY: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45); v2.2 when this script was written).

WHY. The abstract's headline judge finding rests on S18 (phase-3 worklist AB-03, MT-44, MT-49a to MT-52,
ME-21; F3 and Q4): shown the source paper, the judge gave 5/5 faithfulness to 81.7% of answers against 82.5%
without it (-0.8 points, 95% CI -6.5 to +4.8, 372 answers), and to 26.1% when shown a size-matched wrong
paper (right minus wrong 55.6 points, 47.6 to 63.7). S18 was judged by qwen3-coder:30b against the v1 key.
The judge is now devstral-small-2:24b and the key S373.KEY (ground truth v2.4 since 11 October, Q50), and no S373 source re-runs S18. This
script is that re-run (Q28), prepared and not yet run.

WHAT S18 IS (S18a builds the evidence, S18b judges, S18c analyses, S18d verifies; design and readings in
findings/S18_PREREGISTRATION.md). The 528 answerable exp04 answers (88 questions x 6 configurations), read
unchanged, judged with the harness prompt in six arms, one change at a time:
  A   the published call (answer cut at 3,000 characters, num_ctx 16384, num_predict 8192), gated against
      the deposited scores
  A2  A at num_ctx 40960, num_predict 1024 (the runtime options)
  B   A2 with the complete answer: no evidence
  B2  B again, byte-identical, as a final pass: the noise floor
  C   B plus a "## Source Material" section before "## Generated Answer" (S18b.build_prompt) holding the
      question's source paper(s): the whole text when it fits 28,000 tokens ("full"), else bge-m3-ranked
      chunks up to that budget ("selected")
  D   B plus the block of a size-matched wrong paper (S18b.mismatch_partner: the nearest question in
      evidence-size order with no source file in common)
The analysis (S18c) is the share scored faithfulness 5 on the 62 "full" questions frozen by name before any
result (S18_frozen_analysis_set.json, 372 answers), with a question-cluster bootstrap (2,000 resamples, seed
42) and a TOST at 5 points. C vs D is the primary contrast.

THE RE-RUN keeps the answers, the evidence blocks byte for byte, the donors, the frozen set and S18c's
analysis code. It changes the judge to devstral as S373 calls it and the key to S373.KEY as S373 builds it
(reports name the version read from that file's "version" field). D7 (S373.AS_V1 "dropped_d7", the same six
questions in v2.2 and v2.3) drops CD_015, which is in the frozen set: 61 questions and 366 answers per arm.
  A   S373's own call: the current-key prompt, the complete answer, S373's devstral options (num_ctx 32768,
      num_predict 8192). After the run it must reproduce S373's exp04 devstral scores, as S18's arm A had to
      reproduce the deposited ones.
  B   A at the evidence arms' context (num_ctx EV_NUM_CTX). A vs B is the runtime-options control (S18's
      A vs A2).
  C   B plus the question's own block.     D   B plus S18's wrong-paper block.
  B2  B again, last: the noise floor, and MT-44's repeatability sentence.
S18's A2 also isolated the 3,000-character cut. S373 cuts nothing, so that arm has no counterpart here.
EV_NUM_CTX is raised from 32768 because the largest evidence prompt is about 36,000 devstral tokens
(--dry-run estimates it), and S18's probe measured Ollama truncating a prompt silently at num_ctx minus
num_predict (S18_PREREGISTRATION.md section 3): 32768 - 8192 leaves 24,576. The GGUF header gives
devstral-small-2 a 393,216-token context; its f16 KV cache is 160 KiB per token, about 10 GiB at 65536.

GATE, first in every mode, no model call. Nothing is planned, judged or written unless:
  G1  the frozen set hashes to its recorded sha256 and is S18c's 62 "full" questions
  G2  S18c.compare, on the deposited rows, reproduces S18_results_full.json exactly (six contrasts, four
      dimensions), and the printed numbers at their printed precision (PRINTED below)
  G3  every deposited prompt of arms B, B2, C and D rebuilds byte for byte (sha256) from the v1 key with this
      script's builder and blocks, and every D donor is S18b.mismatch_partner's. The one "selected" block the
      primary set needs (15_rabies_tanzania_CO2, donor to 08_deseq2_FR1 and _TE3) is recovered without
      bge-m3: a depth-first search over its paper's chunks finds the chunk subset whose prompt has the
      deposited sha256, and exactly one subset must
  G4  every no-evidence current-key prompt is the one S373 sends (S141_runner.judge.build_prompt), and the D7
      list is the six questions S373 leaves out as reworded
After the run, --analyze applies S18's own gate to arm A (S18c.GATE_EXACT, S18c.GATE_MAD) against S373's
exp04 devstral rows, then S18's resolvability rule (B vs B2 within 3 points), then the contrasts.

    uv run python scripts/S18e_judge_evidence_devstral.py --dry-run
    uv run python scripts/S18e_judge_evidence_devstral.py --ports 11441 11454 11455
    uv run python scripts/S18e_judge_evidence_devstral.py --ports 11434 --questions 08_deseq2_FR1 --arms C,D   # smoke, 12 calls
    uv run python scripts/S18e_judge_evidence_devstral.py --analyze [--ledgers ...] [--s373 ...]

Writes findings/recompute/S18e_plan[_all].{json,md} (--dry-run); S18e_devstral[_all][_<out>][_shard<k>of<n>].{jsonl,md}
(the run: one row per call, appended, resumable; a row counts when its status is ok or ok_output_limit and
its key_hash is the question's current S373 key hash, and resume skips only such rows); and
S18e_results[_all].{json,md} (--analyze; "_all" marks --set all). --dry-run and --analyze make no network call.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import queue
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import S18b_rejudge as S18b  # noqa: E402  evidence blocks, donors, the evidence prompt
import S18c_analyze as S18c  # noqa: E402  the pre-registered contrasts and the replication gate's criterion
import S373_rejudge_v2 as S373  # noqa: E402  the current key, its hash, the devstral settings, the server check
from machine import PUB, RECOMPUTE, rel  # noqa: E402
from S141_runner.judge import ANSWERABLE_DIMS, parse_scores  # noqa: E402
from S141_runner.judge import build_prompt as s373_prompt  # noqa: E402
from S141_runner.providers import OllamaProvider  # noqa: E402

RAW = RECOMPUTE / "S18_rejudge_raw.jsonl"
FROZEN = RECOMPUTE / "S18_frozen_analysis_set.json"
FROZEN_SHA = "75c9b8fe0a2cc1335f1e0d03bf65d748ac009c8d8073b9af792768e4a03ca85d"  # S18_PREREGISTRATION.md, A2
RESULTS_FULL = RECOMPUTE / "S18_results_full.json"
DOCS = RECOMPUTE / "S18_evidence_docs.jsonl"
CHUNKS = RECOMPUTE / "S18_evidence_chunks.jsonl"
MANIFEST = RECOMPUTE / "S18_evidence_manifest.json"
V1 = PUB / "data/ground_truth.json"  # the key S18b read; byte-identical to S373.V1
EXP04 = PUB / "results/exp04_generation_latest.json"
D7 = S373.AS_V1  # its "dropped_d7" (ground_truth_v2_4_as_v1.json since 11 October, Q50; the same six as v2.2's)
BUDGET_CHARS = int(28000 * 3.82)  # S18b.main: budget_chars = int(a.budget_tokens * 3.82), default 28,000

# What the paper prints from S18 (worklist AB-03, MT-44, MT-50 to MT-52, ME-21; S318 judge_evidence_total
# and judge_evidence_content).
PRINTED = {"share5_C": "81.7", "share5_B": "82.5", "share5_D": "26.1",
           "C vs B": ("-0.8", "-6.5", "4.8"), "C vs D": ("55.6", "47.6", "63.7"),
           "n_answers": 372, "n_questions": 62, "d_selected_questions": 2, "b_b2_identical_answers": 528}

DEV = S373.JUDGES["devstral"]
EV_NUM_CTX = 65536
ORDER = ("A", "B", "C", "D", "B2")  # arm-major (one model load per arm), B2 last so it cannot replay B's cache
EVIDENCE = {"A": None, "B": None, "C": "correct", "D": "mismatch", "B2": None}
CONTRASTS = (("B", "B2", "noise floor: identical inputs, two runs"),
             ("A", "B", "runtime options: num_ctx 32768 against the evidence arms' num_ctx"),
             ("C", "B", "evidence effect, total"),
             ("D", "B", "irrelevant-text effect: same bulk, wrong paper"),
             ("C", "D", "PRIMARY: evidence content effect"))
OK = ("ok", "ok_output_limit")
CEIL_MARGIN = 8  # S18b guard 8.1: prompt_eval_count >= num_ctx - num_predict - 8 stops the run
SENTINEL = "\x00S18e\x00"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def file_sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def arm_options(ev_num_ctx: int) -> dict[str, dict]:
    a = dict(DEV["options"])
    return {arm: (dict(a) if arm == "A" else {**a, "num_ctx": ev_num_ctx}) for arm in ORDER}


def ceiling(opts: dict) -> int:
    return opts["num_ctx"] - opts["num_predict"] - CEIL_MARGIN


# ───────────────────────────────────────────────────────────────────────────── inputs and prompts
def load() -> dict:
    gen = json.loads(EXP04.read_text())
    S = {"v1": {q["id"]: q for q in json.loads(V1.read_text())["questions"]},
         "v2": {r["id"]: r for r in json.loads(S373.KEY.read_text())["records"]},
         "key_version": str(json.loads(S373.KEY.read_text())["version"]),
         "dropped": sorted(json.loads(D7.read_text())["dropped_d7"]),
         # S18b's reading of the answers
         "answers": {(r["question_id"], r["config"]): (r["generation"] or {}).get("answer", "")
                     for r in gen["per_question_results"] if r.get("answerable")},
         "deposited": [json.loads(line) for line in RAW.open()],
         "frozen": json.loads(FROZEN.read_text()),
         "sizing": json.loads(MANIFEST.read_text())["sizing"],
         "docs": {d["file"]: d["text"] for d in map(json.loads, DOCS.open())},
         "chunks": [json.loads(line) for line in CHUNKS.open()],
         "template": S18b.load_harness()[0]}
    S["order"] = sorted(S["sizing"], key=lambda k: (S["sizing"][k]["est_tokens"], k))  # S18b.main's donor order
    S["configs"] = sorted({c for _, c in S["answers"]})
    S["B"] = {(r["question_id"], r["config"]): r for r in S["deposited"] if r["arm"] == "B"}
    return S


def v22(qid: str, v2: dict) -> dict:
    """The question and key exactly as S373 gives them to the judge."""
    ea, ec = S373.key_of(qid, v2)
    q = json.loads((S373.V2_INPUTS / f"{qid}.json").read_text())["question"]
    return {"question": q, "expected_answer": ea, "expected_concepts": ec}


def prompt(S: dict, q: dict, answer: str, evidence: str) -> str:
    """S18b.build_prompt: the harness prompt filled as exp_common fills it, the complete answer, and the
    Source Material section when there is evidence."""
    return S18b.build_prompt(S["template"], q, answer, evidence, None)


def frame(S: dict, q: dict, answer: str) -> tuple[str, str]:
    """The evidence prompt around its evidence, (before, after), cut out of S18b.build_prompt itself."""
    parts = prompt(S, q, answer, SENTINEL).split(SENTINEL)
    assert len(parts) == 2, "the evidence marker occurs more than once"
    return parts[0], parts[1]


def donor(S: dict, qid: str, kind: str) -> str:
    return qid if kind == "correct" else S18b.mismatch_partner(qid, S["sizing"], S["order"])


# ───────────────────────────────────────────────────────────────────────────── evidence blocks
def part(c: dict) -> str:
    """One excerpt as S18b.build_evidence lays out a 'selected' block (verified by G3's sha256)."""
    return f"--- SOURCE: {c['file']} (excerpt {c['idx']}) ---\n{c['text']}"


def users(S: dict, src: str) -> list[dict]:
    """Deposited rows that carry src's block: arm C of src, and arm D with src as the donor."""
    return [r for r in S["deposited"] if (r["arm"] == "C" and r["question_id"] == src)
            or (r["arm"] == "D" and r["evidence_source_qid"] == src)]


def recover(S: dict, src: str, limit: int) -> tuple[list[str] | None, int, str]:
    """The chunks S18b's bge-m3 ranking put in src's 'selected' block, recovered without the embedding.

    The block is the picked chunks joined in (file, idx) order, and the deposited rows record its character
    total and the sha256 of each prompt that carried it. A depth-first search over the chunks of src's
    source files, hashing incrementally and pruning on the character total, finds every subset whose prompt
    has that sha256. Exactly one must; anything else returns None."""
    r = users(S, src)[0]
    target = r["evidence_chars"]
    files = set(S["sizing"][src]["source_files"])
    cand = sorted((c for c in S["chunks"] if c["file"] in files), key=lambda c: (c["file"], c["idx"]))
    lens = [len(c["text"]) for c in cand]
    full = max(lens)
    if math.comb(len(cand), max(1, round(target / full))) > limit:
        return None, 0, f"not searched: about {math.comb(len(cand), round(target / full)):,} subsets"
    head, tail = frame(S, S["v1"][r["question_id"]], S["answers"][(r["question_id"], r["config"])])
    blobs = [part(c).encode() for c in cand]
    rest = [0] * (len(cand) + 1)
    for j in range(len(cand) - 1, -1, -1):
        rest[j] = rest[j + 1] + lens[j]
    tail_b, found, nodes = tail.encode(), [], [0]

    def dfs(j: int, tot: int, h, first: bool, picked: list[int]) -> None:
        nodes[0] += 1
        if nodes[0] > limit:
            return
        if tot == target:
            g = h.copy()
            g.update(tail_b)
            if g.hexdigest() == r["prompt_sha256"]:
                found.append(list(picked))
            return
        if j == len(cand) or tot + rest[j] < target:
            return
        if tot + lens[j] <= target:
            g = h.copy()
            g.update((b"" if first else b"\n\n") + blobs[j])
            picked.append(j)
            dfs(j + 1, tot + lens[j], g, False, picked)
            picked.pop()
        dfs(j + 1, tot, h, first, picked)

    dfs(0, 0, hashlib.sha256(head.encode()), True, [])
    if nodes[0] > limit:
        return None, nodes[0], f"search stopped at {limit:,} nodes"
    if len(found) != 1:
        return None, nodes[0], f"{len(found)} subsets match the deposited sha256"
    return [cand[j]["chunk_id"] for j in found[0]], nodes[0], "one subset matches"


def build_blocks(S: dict, srcs: set[str], limit: int, embed_url: str | None) -> dict:
    """S18's evidence block for each question in srcs, with how it was obtained."""
    by_id = {c["chunk_id"]: c for c in S["chunks"]}
    out = {}
    for src in sorted(srcs):
        mode, ids = S["sizing"][src]["mode"], None
        if mode == "full":
            text, _, chars = S18b.build_evidence(src, S["sizing"], S["docs"], [], None, BUDGET_CHARS)
            how = "whole text (S18b.build_evidence)"
        else:
            ids, nodes, note = recover(S, src, limit)
            if ids is not None:
                picked = sorted(map(by_id.get, ids), key=lambda c: (c["file"], c["idx"]))
                text, chars = "\n\n".join(map(part, picked)), sum(len(c["text"]) for c in picked)
                how = f"recovered from the deposited prompt sha256 ({nodes:,} search nodes, {note})"
            elif embed_url:
                S18b.OLLAMA = embed_url  # S18b.embed_one posts to S18b.OLLAMA + "/api/embed"
                text, _, chars = S18b.build_evidence(src, S["sizing"], S["docs"], S["chunks"],
                                                     S["v1"][src]["question"], BUDGET_CHARS)
                how = f"bge-m3 ranking at {embed_url} (S18b.build_evidence); {note}"
            else:
                text, chars, how = None, None, f"needs bge-m3 at run time (--embed-port); {note}"
        u = users(S, src)[0]
        out[src] = {"mode": mode, "text": text, "how": how, "chunk_ids": ids, "chars": chars,
                    "deposited_chars": u["evidence_chars"],
                    # the Source Material section's length, header included, from the deposited prompt sizes
                    "section_chars": u["prompt_chars"] - S["B"][(u["question_id"], u["config"])]["prompt_chars"],
                    "sha256": sha(text) if text else None}
    return out


# ───────────────────────────────────────────────────────────────────────────── the gate
def boot_share5(by: dict, ax: str, ay: str, keys: list, n: int = 2000) -> tuple[float, float]:
    """S18c.cluster_boot_diff on the share scored 5, without its rounding (as S318's g2_judge copies it), so
    the interval can be compared with the printed one at the printed precision."""
    x, y, qids = S18c.paired(by, ax, ay, "faithfulness", keys)
    rng = np.random.default_rng(S18c.SEED)
    idx = defaultdict(list)
    for i, q in enumerate(qids):
        idx[q].append(i)
    qs = list(idx)
    out = []
    for _ in range(n):
        pick = rng.choice(len(qs), len(qs), replace=True)
        sel = [i for k in pick for i in idx[qs[k]]]
        out.append(float((x[sel] == 5).mean()) - float((y[sel] == 5).mean()))
    lo, hi = np.percentile(out, [2.5, 97.5])
    return float(lo), float(hi)


def share5(by: dict, arm: str, keys: list) -> tuple[float, int]:
    xs = [by[(arm,) + k]["parsed"]["faithfulness"] for k in keys if (arm,) + k in by]
    return (sum(x == 5 for x in xs) / len(xs), len(xs)) if xs else (float("nan"), 0)


def pp(v: float) -> str:
    return f"{100 * v:.1f}"


def gate_numbers(S: dict) -> list[tuple[str, bool, str]]:
    """G1 and G2."""
    checks = []
    P = S["frozen"]["primary_set_full"]
    h = sha("\n".join(sorted(P)))
    checks.append(("G1 frozen set sha256", h == FROZEN_SHA == S["frozen"]["sha256_primary"], h[:16]))
    _, by = S18c.load(RAW)
    mode = {r["question_id"]: r["evidence_mode"].split(":")[-1]
            for r in S["deposited"] if r["arm"] == "C" and r.get("evidence_mode")}
    keys = [k for k in sorted({(q, c) for (_, q, c) in by}) if mode.get(k[0]) == "full"]
    full_q = {q for q, _ in keys}
    checks.append(("G1 frozen set is S18c's 'full' questions", full_q == set(P) and len(P) == 62,
                   f"{len(full_q)} 'full', {len(P)} frozen"))

    dep = json.loads(RESULTS_FULL.read_text())
    for con in dep["contrasts"]:
        ax, ay = con["contrast"].split(" vs ")
        mine = S18c.compare(by, ax, ay, keys, con["label"])
        checks.append((f"G2 S18c.compare reproduces S18_results_full.json, {con['contrast']}",
                       mine["dims"] == con["dims"], "all four dimensions, every statistic"))
        if con["contrast"] == "C vs B":
            tost = mine["dims"]["faithfulness"]["tost"]
            checks.append(("G2 no equivalence at the 5-point margin (MT-51)", not tost["equivalent"],
                           f"TOST CI {tost['ci95_pp']}"))
    for arm in ("C", "B", "D"):
        v, n = share5(by, arm, keys)
        checks.append((f"G2 printed 5/5 share, arm {arm}", pp(v) == PRINTED[f"share5_{arm}"] and n == 372,
                       f"{pp(v)}% of {n}"))
    for ax, ay in (("C", "B"), ("C", "D")):
        d = share5(by, ax, keys)[0] - share5(by, ay, keys)[0]
        lo, hi = boot_share5(by, ax, ay, keys)
        got = (pp(d), pp(lo), pp(hi))
        rec = next(c for c in dep["contrasts"] if c["contrast"] == f"{ax} vs {ay}")["dims"]["faithfulness"]
        same_as_s18c = [round(100 * round(lo, 4), 2), round(100 * round(hi, 4), 2)] == rec["share5_diff_ci95_pp"]
        checks.append((f"G2 printed difference and 95% CI, {ax} vs {ay}", got == PRINTED[f"{ax} vs {ay}"] and same_as_s18c,
                       f"{got[0]} points [{got[1]}, {got[2]}]"))
    checks.append(("G2 printed n", len(keys) == PRINTED["n_answers"] and len(full_q) == PRINTED["n_questions"],
                   f"{len(keys)} answers, {len(full_q)} questions"))
    sel = {r["question_id"] for r in S["deposited"]
           if r["arm"] == "D" and r["question_id"] in full_q and r["evidence_mode"].endswith(":selected")}
    checks.append(("G2 retrieved passages for 2 of the 62 questions (ME-21)",
                   len(sel) == PRINTED["d_selected_questions"], ", ".join(sorted(sel))))
    same = sum(1 for (arm, q, c), r in by.items() if arm == "B" and ("B2", q, c) in by
               and all(r["parsed"][d] == by[("B2", q, c)]["parsed"][d] for d in S18c.DIMS))
    checks.append(("G2 B and B2 identical on all four dimensions (MT-44)", same == PRINTED["b_b2_identical_answers"],
                   f"{same} answers"))
    return checks


def gate_prompts(S: dict, qids: set[str], blocks: dict) -> tuple[list, dict]:
    """G3: rebuild every deposited prompt of arms B, B2, C and D for qids, byte for byte."""
    n = Counter()
    bad = []
    for r in S["deposited"]:
        if r["arm"] not in ("B", "B2", "C", "D") or r["question_id"] not in qids:
            continue
        ev = ""
        if r["arm"] in ("C", "D"):
            src = donor(S, r["question_id"], "correct" if r["arm"] == "C" else "mismatch")
            if src != r["evidence_source_qid"]:
                bad.append(("donor", r["arm"], r["question_id"], r["config"]))
                continue
            b = blocks[src]
            if b["text"] is None:
                n["not built"] += 1
                continue
            if b["chars"] is not None and b["chars"] != r["evidence_chars"]:
                bad.append(("evidence_chars", r["arm"], r["question_id"], r["config"]))
                continue
            ev = b["text"]
        p = prompt(S, S["v1"][r["question_id"]], S["answers"][(r["question_id"], r["config"])], ev)
        if sha(p) == r["prompt_sha256"]:
            n[r["arm"]] += 1
        else:
            bad.append(("prompt sha256", r["arm"], r["question_id"], r["config"]))
    checks = [("G3 deposited prompts rebuilt byte for byte", not bad,
               f"{dict(n)}; mismatches {len(bad)}" + (f", first {bad[:3]}" if bad else ""))]
    return checks, dict(n)


# ───────────────────────────────────────────────────────────────────────────── plan
def plan(S: dict, qids: list[str], arms: list[str], opts: dict, blocks: dict) -> tuple[list[dict], list]:
    """Every call: its prompt (None only for a block that needs bge-m3), sizes and guards. Also G4."""
    items, g4_bad = [], []
    for arm in arms:
        for qid in qids:
            q = v22(qid, S["v2"])
            kh = S373.key_hash(qid, S["v2"])
            for cfg in S["configs"]:
                ans = S["answers"][(qid, cfg)]
                noev = prompt(S, q, ans, "")
                if arm == arms[0] and noev != s373_prompt(q["question"], q["expected_answer"], q["expected_concepts"],
                                                          ans, True, None):
                    g4_bad.append((qid, cfg))
                kind = EVIDENCE[arm]
                src = donor(S, qid, kind) if kind else None
                b = blocks[src] if src else None
                p = noev if b is None else (prompt(S, q, ans, b["text"]) if b["text"] is not None else None)
                section = 0 if b is None else (len(p) - len(noev) if p is not None else b["section_chars"])
                tail = frame(S, q, ans)[1]
                items.append({"key": f"S18e|{arm}|exp04|{cfg}|{qid}", "arm": arm, "question_id": qid, "config": cfg,
                              "key_hash": kh, "answer_chars": len(ans), "evidence": kind, "evidence_source_qid": src,
                              "evidence_mode": b["mode"] if b else None, "evidence_sha256": b["sha256"] if b else None,
                              "evidence_chars": b["deposited_chars"] if b else 0, "prompt": p,
                              "prompt_sha256": sha(p) if p is not None else None,
                              "prompt_chars": len(noev) + section, "noev_chars": len(noev), "section_chars": section,
                              "tail_chars": len(tail), "options": opts[arm], "ceiling": ceiling(opts[arm])})
    return items, g4_bad


def calibrate(S: dict, paths: list[str]) -> dict:
    """Characters to devstral prompt tokens, and seconds per call, measured on files, not assumed.

    Prompt text: a line fitted on S373's devstral rows (answerable answers; each prompt rebuilt as S373 built
    it, tokens as Ollama counted them). Its intercept is mostly the system prompt devstral's Ollama template
    adds. PDF text tokenizes denser than prompt text; the factor is measured on S18's qwen3-coder rows
    (evidence characters per token over no-evidence characters per token): its median for the estimate, its
    5th percentile with three residual standard deviations for the conservative bound. Seconds per call: a
    plane through the same rows' wall time, prompt tokens and output tokens."""
    srcs = sorted(S373.SOURCES, key=len, reverse=True)
    cache: dict[str, dict] = {}
    X, Y, T, used = [], [], [], {}
    for p in paths:
        name = Path(p).name
        src = next((s for s in srcs if name.startswith(f"S373_devstral_{s}")), None)
        if src is None:
            continue
        if src not in cache:
            cache[src] = {x["key"]: x for x in S373.SOURCES[src](S["v1"], S["v2"])}
        n0 = len(X)
        for line in open(p):
            if not line.strip():
                continue
            r = json.loads(line)
            x = cache[src].get(r["key"])
            if (x is None or not x["answerable"] or r.get("status") not in OK or not r.get("prompt_tokens")
                    or r.get("key_hash") != S373.key_hash(x["question_id"], S["v2"]) or r.get("answer_chars") != len(x["answer"])):
                continue
            X.append(len(s373_prompt(x["question"], x["expected"], x["concepts"], x["answer"], True, None)))
            Y.append(r["prompt_tokens"])
            if r.get("output_tokens") and r.get("wall_s"):
                T.append((r["prompt_tokens"], r["output_tokens"], r["wall_s"], r.get("port"), r.get("ollama")))
        used[rel(p)] = {"sha256": file_sha(p), "rows_used": len(X) - n0}
    if len(X) < 50:
        raise SystemExit(f"FATAL: {len(X)} S373 devstral rows to calibrate on; pass --calib with S373 devstral ledgers")
    Xa, Ya = np.array(X, float), np.array(Y, float)
    slope, icpt = np.polyfit(Xa, Ya, 1)
    sd = float(np.std(Ya - (icpt + slope * Xa)))
    ev, nb = [], []
    for r in S["deposited"]:
        b = S["B"][(r["question_id"], r["config"])]
        if r["arm"] in ("C", "D"):
            ev.append((r["prompt_chars"] - b["prompt_chars"]) / (r["prompt_eval_count"] - b["prompt_eval_count"]))
        elif r["arm"] == "B":
            nb.append(r["prompt_chars"] / r["prompt_eval_count"])
    Tm = np.array([[1, t[0], t[1]] for t in T], float)
    coef = np.linalg.lstsq(Tm, np.array([t[2] for t in T], float), rcond=None)[0]
    return {"n_rows": len(X), "intercept_tokens": float(icpt), "chars_per_token": float(1 / slope), "resid_sd": sd,
            "ev_factor": float(np.median(ev) / np.median(nb)), "ev_factor_p5": float(np.percentile(ev, 5) / np.median(nb)),
            "qwen_chars_per_token_evidence": float(np.median(ev)), "qwen_chars_per_token_noevidence": float(np.median(nb)),
            "time": {"n": len(T), "s_intercept": float(coef[0]), "s_per_prompt_token": float(coef[1]),
                     "s_per_output_token": float(coef[2]), "output_tokens_median": float(np.median([t[1] for t in T])),
                     "ports": sorted({str(t[3]) for t in T}), "ollama": sorted({str(t[4]) for t in T})},
            "ledgers": used}


def estimate(it: dict, cal: dict) -> tuple[float, float]:
    r = cal["chars_per_token"]
    base = cal["intercept_tokens"] + it["noev_chars"] / r
    return (base + it["section_chars"] / (r * cal["ev_factor"]),
            base + it["section_chars"] / (r * cal["ev_factor_p5"]) + 3 * cal["resid_sd"])


def timing(items: list[dict], cal: dict, n_servers: int) -> dict:
    """Hours: the assignment's 6 to 12 s per call, and the fitted plane with and without prefix reuse (the
    six answers of a question share everything up to the answer, so in C and D five of six are warm)."""
    t = cal["time"]

    def wall(tokens: float) -> float:
        return max(t["s_intercept"] + t["s_per_prompt_token"] * tokens + t["s_per_output_token"] * t["output_tokens_median"], 1.0)

    warm = cold = 0.0
    seen = set()
    for it in items:
        cold += wall(it["est_tokens"])
        g = (it["arm"], it["question_id"])
        if it["evidence"] and g in seen:
            warm += wall(it["tail_chars"] / cal["chars_per_token"])
        else:
            warm += wall(it["est_tokens"])
        seen.add(g)
    n = len(items)
    return {"calls": n, "servers": n_servers, "band_h": [round(n * 6 / 3600 / n_servers, 1), round(n * 12 / 3600 / n_servers, 1)],
            "fitted_prefix_reuse_h": round(warm / 3600 / n_servers, 1), "fitted_all_cold_h": round(cold / 3600 / n_servers, 1)}


# ───────────────────────────────────────────────────────────────────────────── the run
def judge_call(prov: OllamaProvider, prompt_text: str, opts: dict):
    """S141_runner.judge.Judge.score's loop for a prompt built here: retried once, never zero-filled."""
    last = None
    for attempt in (1, 2):
        call = prov.generate(DEV["model"], prompt_text, dict(opts), think=DEV["think"], timeout=3600)
        last = call
        if not call.ok:
            if attempt == 2:
                return "error", None, call, attempt
            continue
        scores, _ = parse_scores(call.text or "", True)
        if any(scores.get(d) is not None for d in ANSWERABLE_DIMS):
            return "ok", {d: scores.get(d) for d in ANSWERABLE_DIMS}, call, attempt
        if attempt == 2:
            return "unparseable", None, call, attempt
    return "error", None, last, 2


def run(a, items: list[dict], stem: str) -> int:
    jl, md = RECOMPUTE / f"{stem}.jsonl", RECOMPUTE / f"{stem}.md"
    servers = [S373.server(p, DEV["model"]) for p in a.ports]
    digests = {s["model_digest"] for s in servers}
    if None in digests or len(digests) != 1:
        raise SystemExit(f"FATAL: {DEV['model']} digests across the servers are {digests}; one is required")
    key_sha = file_sha(S373.KEY)
    done = set()
    if jl.exists():
        done = {(r["key"], r["key_hash"]) for r in map(json.loads, filter(str.strip, jl.read_text().splitlines()))
                if r.get("status") in OK}
    todo = [x for x in items if (x["key"], x["key_hash"]) not in done]
    groups: dict[tuple, list] = {}
    for x in todo:  # items are arm-major with B2 last; a group keeps a question's six answers on one server
        groups.setdefault((x["arm"], x["question_id"]), []).append(x)
    print(f"devstral on S18: {len(items)} calls, {len(items) - len(todo)} done, {len(todo)} to judge in "
          f"{len(groups)} groups; servers {servers}", flush=True)
    q: queue.Queue = queue.Queue()
    for g in groups.values():
        q.put(g)
    lock, stop = threading.Lock(), threading.Event()
    by_port = {s["port"]: s for s in servers}

    def worker(port: int) -> None:
        prov = OllamaProvider(f"http://127.0.0.1:{port}")
        while not stop.is_set():
            try:
                g = q.get_nowait()
            except queue.Empty:
                return
            for x in g:
                if stop.is_set():
                    return
                t0 = time.time()
                status, scores, call, attempts = judge_call(prov, x["prompt"], x["options"])
                tok = (call.tokens if call else {}) or {}
                if (tok.get("prompt") or 0) >= x["ceiling"]:
                    status = "out_of_context"
                elif call is not None and call.length_capped:
                    status = "ok_output_limit" if status == "ok" else "output_limit"
                rec = {k: x[k] for k in ("key", "arm", "question_id", "config", "key_hash", "answer_chars", "evidence",
                                         "evidence_source_qid", "evidence_mode", "evidence_sha256", "evidence_chars",
                                         "prompt_sha256", "prompt_chars", "options", "ceiling")}
                rec.update({"source": EXP04.name, "answerable": True, "est_prompt_tokens": round(x["est_tokens"]),
                            "judge": DEV["model"], "think": DEV["think"], "truncate_chars": None, "port": port,
                            "ollama": by_port[port]["ollama"], "model_digest": by_port[port]["model_digest"],
                            "key_sha256": key_sha, "status": status, "scores": scores if status in OK else None,
                            "prompt_tokens": tok.get("prompt"), "output_tokens": tok.get("completion"),
                            "finish_reason": call.finish_reason if call else None, "attempts": attempts,
                            "error": call.error if call else None, "raw_text": call.text if call else None,
                            "wall_s": round(time.time() - t0, 2), "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                with lock:
                    with jl.open("a") as fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"{port} {x['key']} {rec['wall_s']}s {status} prompt {rec['prompt_tokens']}", flush=True)
                # S18b's two stops: a prompt at the context ceiling, and any output cut at num_predict, scored or
                # not (devstral's longest S373 output is a few hundred tokens of 8,192, so a cut is a runaway)
                if status in ("out_of_context", "output_limit", "ok_output_limit"):
                    stop.set()
                    print(f"FATAL {x['key']}: {status} (prompt {rec['prompt_tokens']} of ceiling {x['ceiling']}, "
                          f"finish {rec['finish_reason']}); every server stops after its current call", flush=True)
                    return

    t0 = time.time()
    ths = [threading.Thread(target=worker, args=(p,)) for p in a.ports]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    el = time.time() - t0
    recs = [json.loads(line) for line in jl.read_text().splitlines() if line.strip()] if jl.exists() else []
    lines = [f"# S18e devstral on the judge-evidence experiment ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Judge {DEV['model']}, think {DEV['think']}, complete answers; key {rel(S373.KEY)} sha256 {key_sha[:12]}.",
             "Servers: " + ", ".join(f"{s['port']} Ollama {s['ollama']} digest {s['model_digest']}" for s in servers), "",
             "| arm | rows | statuses | max prompt tokens | ceiling |", "|---|---|---|---|---|"]
    for arm in ORDER:
        rs = [r for r in recs if r["arm"] == arm]
        if rs:
            lines.append(f"| {arm} | {len(rs)} | {dict(Counter(r['status'] for r in rs))} | "
                         f"{max((r['prompt_tokens'] or 0) for r in rs)} | {rs[0]['ceiling']} |")
    if todo:
        lines += ["", f"This run: {el / 60:.1f} min on {len(a.ports)} servers; stopped early: {stop.is_set()}."]
    md.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if stop.is_set() else 0


# ───────────────────────────────────────────────────────────────────────────── analysis
def analyze(a, S: dict, qids: list[str], opts: dict, prov: dict) -> int:
    paths = a.ledgers or sorted(glob.glob(str(RECOMPUTE / "S18e_devstral*.jsonl")))
    cur = {q: S373.key_hash(q, S["v2"]) for q in qids}
    rows = [json.loads(line) for p in paths for line in open(p) if line.strip()]
    by, dup, partial = {}, 0, 0
    for r in sorted(rows, key=lambda r: r.get("at", "")):
        if r.get("status") not in OK or r.get("key_hash") != cur.get(r.get("question_id")):
            continue
        sc = r.get("scores") or {}
        if not all(isinstance(sc.get(d), int) for d in ANSWERABLE_DIMS):
            partial += 1
            continue
        k = (r["arm"], r["question_id"], r["config"])
        if k in by:
            dup += 1
            continue
        by[k] = {"parsed": sc, "row": r}
    keys = [(q, c) for q in qids for c in S["configs"]]
    health = {}
    for arm in ORDER:
        rs = [r for r in rows if r.get("arm") == arm]
        health[arm] = {"expected": len(keys), "counted": sum(1 for k in keys if (arm,) + k in by),
                       "statuses": dict(Counter(r.get("status") for r in rs)),
                       "max_prompt_tokens": max([r.get("prompt_tokens") or 0 for r in rs], default=None),
                       "ceiling": ceiling(opts[arm]), "dates": dict(Counter(str(r.get("at", ""))[:10] for r in rs))}

    s373 = {}
    for p in (a.s373 or sorted(glob.glob(str(RECOMPUTE / "S373_devstral_*.jsonl")))):
        for line in open(p):
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("source") == EXP04.name and r.get("status") in OK and r.get("key_hash") == cur.get(r.get("question_id"))
                    and isinstance((r.get("scores") or {}).get("faithfulness"), int)):
                s373.setdefault((r["question_id"], r["config"]), r["scores"])
    pairs = [(by[("A",) + k]["parsed"]["faithfulness"], s373[k]["faithfulness"]) for k in keys if ("A",) + k in by and k in s373]
    gate = {"n": len(pairs), "criterion_exact": S18c.GATE_EXACT, "criterion_mad": S18c.GATE_MAD}
    if pairs:
        d = np.array([x - y for x, y in pairs], float)
        gate.update(exact_agreement=round(float((d == 0).mean()), 4), mean_abs_diff=round(float(np.abs(d).mean()), 4))
        gate["pass"] = bool(gate["exact_agreement"] >= S18c.GATE_EXACT and gate["mean_abs_diff"] <= S18c.GATE_MAD)
    else:
        gate["pass"] = None

    contrasts = [S18c.compare(by, ax, ay, keys, lab) for ax, ay, lab in CONTRASTS
                 if any((ax,) + k in by for k in keys) and any((ay,) + k in by for k in keys)]
    nf = next((c["dims"]["faithfulness"] for c in contrasts if c["contrast"] == "B vs B2"), None)
    resolvable = None if not nf or not nf.get("n") else abs(nf["share5_diff_pp"]) <= 3.0
    bb2 = [k for k in keys if ("B",) + k in by and ("B2",) + k in by]
    same = sum(1 for k in bb2 if all(by[("B",) + k]["parsed"][d] == by[("B2",) + k]["parsed"][d] for d in S18c.DIMS))
    shares = {arm: dict(zip(("share5", "n"), share5(by, arm, keys))) for arm in ORDER}
    res = {"_provenance": {**prov, "ledgers": {rel(p): file_sha(p) for p in paths}, "rows": len(rows),
                           "duplicates_skipped": dup, "partial_scores_skipped": partial},
           "analysis_set": {"questions": len(qids), "answers": len(keys), "frozen_set_sha256": FROZEN_SHA,
                            "dropped_d7": sorted(set(S["frozen"]["primary_set_full"]) & set(S["dropped"]))},
           "health": health, "replication_gate_arm_A_vs_S373_exp04": gate, "resolvable_noise_under_3pp": resolvable,
           "b_b2_identical_all_four_dims": {"answers": len(bb2), "identical": same},
           "share5_faithfulness": shares, "contrasts": contrasts,
           "s18_printed_qwen_v1": PRINTED}
    out = RECOMPUTE / f"S18e_results{a.suffix}.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    L = [f"# S18e results: devstral-small-2:24b on ground truth v{S['key_version']} "
         f"({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"{len(qids)} questions, {len(keys)} answers per arm (S18's frozen set less D7). Ledgers: {len(paths)}, "
         f"{len(rows)} rows; {dup} duplicates and {partial} partial scores not counted.", "",
         f"Replication gate (arm A against S373's exp04 devstral rows, S18's criterion): n {gate['n']}, "
         f"exact {gate.get('exact_agreement')}, mean |diff| {gate.get('mean_abs_diff')}, pass {gate['pass']}.",
         f"Noise floor within 3 points: {resolvable}. B and B2 identical on all four dimensions: {same} of {len(bb2)}.", "",
         "| arm | counted | 5/5 faithfulness | max prompt tokens | ceiling |", "|---|---|---|---|---|"]
    for arm in ORDER:
        h = health[arm]
        L.append(f"| {arm} | {h['counted']} of {h['expected']} | {100 * shares[arm]['share5']:.2f}% | "
                 f"{h['max_prompt_tokens']} | {h['ceiling']} |")
    L += ["", "| contrast | n | 5/5 x | 5/5 y | difference, points | 95% CI | TOST equivalent at 5 |", "|---|---|---|---|---|---|---|"]
    for c in contrasts:
        f = c["dims"]["faithfulness"]
        if f.get("n"):
            L.append(f"| {c['contrast']} ({c['label']}) | {f['n']} | {100 * f['share5_x']:.2f}% | {100 * f['share5_y']:.2f}% | "
                     f"{f['share5_diff_pp']} | {f['share5_diff_ci95_pp']} | {(f.get('tost') or {}).get('equivalent')} |")
    L += ["", "S18 as printed (qwen3-coder:30b, v1 key, 372 answers): C 81.7%, B 82.5%, D 26.1%; C vs B -0.8 [-6.5, 4.8]; "
          "C vs D 55.6 [47.6, 63.7].", f"Full statistics: {rel(out)}."]
    if gate["pass"] is False:
        L.append("\nThe replication gate failed: per S18's pre-registration the contrasts are not a controlled "
                 "comparison against the scores S373 reports for exp04.")
    (RECOMPUTE / f"S18e_results{a.suffix}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


# ───────────────────────────────────────────────────────────────────────────── main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="gate, build every prompt, report sizes and time; no model")
    ap.add_argument("--analyze", action="store_true", help="gate, then the contrasts on the ledgers; no model")
    ap.add_argument("--ports", nargs="+", type=int, help="judge on these Ollama ports")
    ap.add_argument("--arms", default=",".join(ORDER))
    ap.add_argument("--set", choices=("primary", "all"), default="primary",
                    help="primary: S18's frozen 62 questions less D7; all: its 88 less D7 (needs --embed-port to run)")
    ap.add_argument("--questions", default=None, help="comma-separated question ids, for a smoke test")
    ap.add_argument("--shard", default=None, help="k[,k...]/n: only the questions whose id hashes to these shards")
    ap.add_argument("--out", default=None, help="a tag for the ledger name")
    ap.add_argument("--num-ctx", type=int, default=EV_NUM_CTX, help="num_ctx of arms B, B2, C and D")
    ap.add_argument("--embed-port", type=int, default=None, help="--set all: the Ollama port serving bge-m3")
    ap.add_argument("--recover-limit", type=int, default=20_000_000, help="search nodes allowed per 'selected' block")
    ap.add_argument("--calib", nargs="+", default=None, help="S373 devstral ledgers for the token calibration")
    ap.add_argument("--ledgers", nargs="+", default=None, help="--analyze: S18e ledgers (default: all local)")
    ap.add_argument("--s373", nargs="+", default=None, help="--analyze: S373 devstral ledgers for arm A's gate")
    a = ap.parse_args()
    a.suffix = "" if a.set == "primary" else f"_{a.set}"
    if sum(map(bool, (a.dry_run, a.analyze, a.ports))) != 1:
        ap.error("give exactly one of --dry-run, --analyze, --ports")
    arms = [x for x in ORDER if x in a.arms.split(",")]
    if not arms or len(arms) != len(a.arms.split(",")):
        ap.error(f"--arms takes {','.join(ORDER)}")
    if a.ports and a.set == "all" and not a.embed_port:
        ap.error("--set all needs --embed-port (bge-m3 ranks the chunks of the 'selected' questions)")
    t0 = time.time()
    S = load()
    opts = arm_options(a.num_ctx)

    # ── G1, G2
    checks = gate_numbers(S)
    # ── the question sets: S18's (for G3) and the re-run's (less D7)
    s18_set = set(S["frozen"]["primary_set_full"]) if a.set == "primary" else set(S["sizing"])
    qids = sorted(s18_set - set(S["dropped"]))
    if a.questions:
        want = a.questions.split(",")
        if set(want) - set(qids):
            ap.error(f"not in the {a.set} set less D7: {sorted(set(want) - set(qids))}")
        qids = [q for q in qids if q in want]
    if a.shard:
        ks, n = a.shard.split("/")
        ks, n = {int(k) for k in ks.split(",")}, int(n)
        qids = [q for q in qids if int(hashlib.sha256(q.encode()).hexdigest(), 16) % n in ks]
    srcs = {donor(S, q, kind) for q in s18_set for kind in ("correct", "mismatch")}
    embed = f"http://127.0.0.1:{a.embed_port}" if (a.ports and a.embed_port) else None
    blocks = build_blocks(S, srcs, a.recover_limit, embed)
    # ── G3
    g3, g3n = gate_prompts(S, s18_set, blocks)
    checks += g3
    # ── G4
    v1s = {q["id"]: q for q in json.loads(S373.V1.read_text())["questions"]}
    changed = sorted(q for q, r in S["v2"].items() if r.get("question") and r["question"] != v1s[q]["question"])
    checks.append(("G4 D7 is the six questions S373 leaves out as reworded", changed == S["dropped"], ", ".join(changed)))
    items, g4_bad = plan(S, qids, arms, opts, blocks)
    checks.append((f"G4 no-evidence v{S['key_version']} prompts are S373's", not g4_bad,
                   f"{len(qids) * len(S['configs']) - len(g4_bad)} of {len(qids) * len(S['configs'])}"))
    for name, ok, note in checks:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {note}")
    if not all(ok for _, ok, _ in checks):
        print("GATE FAILED: nothing planned, judged or written")
        return 1
    print(f"GATE PASSED ({len(checks)} checks, {time.time() - t0:.0f} s)", flush=True)

    inputs = [RAW, FROZEN, RESULTS_FULL, DOCS, CHUNKS, MANIFEST, V1, EXP04, S373.KEY, D7, S18b.HARNESS]
    prov = {"script": "scripts/S18e_judge_evidence_devstral.py", "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "inputs": {rel(p): file_sha(p) for p in inputs}, "params": {k: v for k, v in vars(a).items()},
            "key": rel(S373.KEY), "key_sha256": file_sha(S373.KEY), "key_version": S["key_version"],
            "gate": [{"check": n, "pass": ok, "note": note} for n, ok, note in checks]}
    if a.analyze:
        return analyze(a, S, qids, opts, prov)

    cal = calibrate(S, a.calib or sorted(glob.glob(str(RECOMPUTE / "S373_devstral_*.jsonl"))))
    for it in items:
        it["est_tokens"], it["est_tokens_conservative"] = estimate(it, cal)
    over = [it["key"] for it in items if it["est_tokens_conservative"] >= it["ceiling"]]
    unbuilt = sorted({it["evidence_source_qid"] for it in items if it["prompt"] is None})
    if a.ports:
        if over:
            raise SystemExit(f"FATAL: {len(over)} prompts may not fit their ceiling (conservative estimate), "
                             f"first {over[:3]}; raise --num-ctx")
        if unbuilt:
            raise SystemExit(f"FATAL: evidence blocks not built: {unbuilt}")
        stem = f"S18e_devstral{a.suffix}" + (f"_{a.out}" if a.out else "") + (f"_shard{a.shard.replace('/', 'of').replace(',', '-')}" if a.shard else "")
        return run(a, items, stem)

    # ── the dry run's report
    per_arm = {}
    for arm in arms:
        xs = [it for it in items if it["arm"] == arm]
        top = max(xs, key=lambda it: it["prompt_chars"])
        per_arm[arm] = {"calls": len(xs), "options": opts[arm], "ceiling": ceiling(opts[arm]),
                        "max_prompt_chars": top["prompt_chars"], "max_prompt_at": top["key"],
                        "max_est_tokens": round(max(it["est_tokens"] for it in xs)),
                        "max_est_tokens_conservative": round(max(it["est_tokens_conservative"] for it in xs)),
                        "over_ceiling_conservative": sum(1 for it in xs if it["est_tokens_conservative"] >= it["ceiling"]),
                        "over_s373_num_ctx_32768_less_num_predict": sum(1 for it in xs if it["est_tokens"] >= ceiling(DEV["options"])),
                        "prompts_built": sum(1 for it in xs if it["prompt"] is not None)}
    used = {it["evidence_source_qid"] for it in items if it["evidence_source_qid"]}
    report = {"_provenance": {**prov, "wall_s": round(time.time() - t0, 1)},
              "set": a.set, "questions": len(qids), "answers_per_arm": len(qids) * len(S["configs"]),
              "dropped_from_s18_set": sorted(s18_set & set(S["dropped"])), "arms": arms, "per_arm": per_arm,
              "g3_rebuilt_by_arm": g3n, "calibration": cal,
              "time": {"one_server": timing(items, cal, 1), "three_servers": timing(items, cal, 3)},
              "blocks": {k: {kk: vv for kk, vv in v.items() if kk != "text"} for k, v in blocks.items() if k in used},
              "prompts_needing_bge_m3": sum(1 for it in items if it["prompt"] is None),
              "commands": {"mac_studio": "uv run python scripts/S18e_judge_evidence_devstral.py --ports 11441 11454 11455",
                           "laptop": "uv run python scripts/S18e_judge_evidence_devstral.py --ports 11434",
                           "both": ["mac studio: ... --ports 11441 11454 11455 --shard 0,1,2/4 --out studio",
                                    "laptop: ... --ports 11434 --shard 3/4 --out laptop"],
                           "analyze": "uv run python scripts/S18e_judge_evidence_devstral.py --analyze"},
              "items": [{k: v for k, v in it.items() if k not in ("prompt", "options")} for it in items]}
    (RECOMPUTE / f"S18e_plan{a.suffix}.json").write_text(json.dumps(report, indent=1) + "\n")
    c, tm1, tm3 = cal, report["time"]["one_server"], report["time"]["three_servers"]
    L = [f"# S18e plan: S18 re-judged by devstral-small-2:24b on ground truth v{S['key_version']} "
         f"({time.strftime('%Y-%m-%d %H:%M')})", "",
         f"Gate passed ({len(checks)} checks; no model call). Set {a.set}: {len(qids)} questions, "
         f"{len(qids) * len(S['configs'])} answers per arm; dropped by D7 from S18's set: {report['dropped_from_s18_set']}.", "",
         "| arm | calls | num_ctx | ceiling | max prompt chars | est. tokens | conservative | over S373's 24,568 |",
         "|---|---|---|---|---|---|---|---|"]
    for arm, v in per_arm.items():
        L.append(f"| {arm} | {v['calls']} | {v['options']['num_ctx']} | {v['ceiling']} | {v['max_prompt_chars']:,} | "
                 f"{v['max_est_tokens']:,} | {v['max_est_tokens_conservative']:,} | {v['over_s373_num_ctx_32768_less_num_predict']} |")
    L += ["", f"Tokens = {c['intercept_tokens']:.0f} + characters / {c['chars_per_token']:.2f} (fitted on {c['n_rows']} S373 "
          f"devstral rows, residual sd {c['resid_sd']:.0f}); PDF text at {c['ev_factor']:.3f} of that ratio "
          f"(5th percentile {c['ev_factor_p5']:.3f}), measured on S18's qwen3-coder rows.",
          f"Calls: {tm1['calls']}. One server: {tm1['band_h'][0]} to {tm1['band_h'][1]} h at 6 to 12 s per call; fitted "
          f"{tm1['fitted_prefix_reuse_h']} h with prefix reuse, {tm1['fitted_all_cold_h']} h all cold. Three servers: "
          f"{tm3['band_h'][0]} to {tm3['band_h'][1]} h; fitted {tm3['fitted_prefix_reuse_h']} h, {tm3['fitted_all_cold_h']} h.",
          f"Prompts needing bge-m3 at run time: {report['prompts_needing_bge_m3']}.", "",
          "Commands: " + "; ".join(f"`{v}`" for k, v in report["commands"].items() if isinstance(v, str))]
    (RECOMPUTE / f"S18e_plan{a.suffix}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
